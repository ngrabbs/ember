#!/usr/bin/env python3
"""Optional persistent native UHD TX or RX-forwarding + binary telemetry flow."""
import argparse,fcntl,json,math,os,signal,socket,stat,threading,time
from pathlib import Path
from binary_injector import StreamInjector
from packet_radio import waveform
from radio_control import default_socket

def udp_counters():
    lines=Path('/proc/net/snmp').read_text().splitlines()
    for header,values in zip(lines,lines[1:]):
        if header.startswith('Udp:') and values.startswith('Udp:'):
            return dict(zip(header.split()[1:],map(int,values.split()[1:])))
    raise RuntimeError('Linux UDP counters unavailable')

class ControlServer:
    def __init__(self,path,injector,status,stop):
        self.path=Path(path);self.injector=injector;self.status=status;self.stop=stop
        self.closed=threading.Event();self.ready=False
        if len(os.fsencode(self.path))>100:raise ValueError('Socket path too long')
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        info=self.path.parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:
            raise ValueError('Control directory must be owned by you and mode0700')
        self.lock=(self.path.parent/'owner.lock').open('a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:self.lock.close();raise RuntimeError('Another binary flow owns this directory')
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        try:
            if self.path.exists() or self.path.is_symlink():
                if not stat.S_ISSOCK(self.path.lstat().st_mode):raise ValueError('Refusing to replace non-socket file')
                self.path.unlink()
            self.sock.bind(str(self.path));os.chmod(self.path,0o600);self.sock.listen(2);self.sock.settimeout(.2)
        except BaseException:self.sock.close();self.lock.close();raise
        self.thread=threading.Thread(target=self.serve,daemon=True);self.thread.start()
    def serve(self):
        while not self.closed.is_set():
            try:conn,_=self.sock.accept()
            except socket.timeout:continue
            except OSError:break
            with conn:
                conn.settimeout(2)
                try:
                    data=b''
                    while b'\n' not in data:
                        part=conn.recv(2049-len(data))
                        if not part or len(data)+len(part)>2048:raise ValueError('One JSON line of at most2048bytes required')
                        data+=part
                    message=json.loads(data.split(b'\n',1)[0])
                    if not isinstance(message,dict):raise ValueError('Object required')
                    command=message.get('command')
                    if command=='status':result=dict(self.status(),ready=self.ready)
                    elif command=='stop':
                        self.injector.queue.accepting=False;self.stop.set();result=dict(state='stop_requested')
                    elif command=='enqueue' and self.ready:
                        result=self.injector.queue.enqueue(message.get('hex'),message.get('request_id'))
                    else:raise ValueError('Not ready or unknown command')
                    reply=dict(ok=True,result=result)
                except Exception as exc:reply=dict(ok=False,error=str(exc))
                try:conn.sendall((json.dumps(reply)+'\n').encode())
                except OSError:pass
    def close(self):
        self.ready=False;self.injector.queue.accepting=False;self.closed.set();self.sock.close()
        self.thread.join(timeout=20)
        if self.thread.is_alive():raise RuntimeError('Control thread did not stop')
        self.path.unlink(missing_ok=True);self.lock.close()


def build_flow(a,injector):
    from gnuradio import blocks,filter,gr,uhd
    tb=gr.top_block('Finite conducted gain probe '+a.mode)
    stream=uhd.stream_args(cpu_format='fc32',otw_format='sc16',channels=[1],args='spp=1024')
    # The deployed FPGA CHDR MTU is8192 and int0 MTU is9000. Larger frames
    # reduce per-packet CPU work; leave the master clock to the native driver.
    device='type=sdrb,mgmt_addr=127.0.0.1,recv_frame_size=8000,send_frame_size=8000'
    sink=uhd.usrp_sink(device,stream,'');tb.sdrb_sink=sink
    sink.set_gain(0,0);sink.set_samp_rate(a.rate);sink.set_center_freq(a.tx_frequency,0)
    sink.set_antenna('TX1A_Direct1',0);sink.set_bandwidth(a.rate,0)
    if abs(sink.get_samp_rate()-a.rate)>1:raise ValueError('Unexpected TX rate')
    adder=blocks.add_cc();tb.adder=adder
    if a.mode=='transponder':
        source=uhd.usrp_source(device,stream);tb.sdrb_source=source
        source.set_samp_rate(a.rate);source.set_center_freq(a.rx_frequency,0)
        source.set_antenna('RX1',0);source.set_rx_agc(False,0)
        source.set_gain(a.rx_gain,0);source.set_bandwidth(a.rate,0)
        if abs(source.get_samp_rate()-a.rate)>1:raise ValueError('Unexpected RX rate')
        taps=filter.firdes.low_pass(a.forward_scale,a.rate,a.passband,a.transition)
        repeater_filter=filter.fft_filter_ccc(1,taps,1)
        tb.connect(source,repeater_filter,(adder,0))
    else:
        zeros=blocks.vector_source_c([0j]*1024,True)
        tb.connect(zeros,(adder,0))
    tb.connect(injector.source,(adder,1));tb.connect(adder,sink)
    # The deployed radio-only RFNoC image has no DDC/DUC: stream rate and
    # radio clock must agree. Check after BOTH blocks configure the shared RFIC.
    tb.actual=dict(device_args=device,tx_rate=sink.get_samp_rate(),
        tx_clock=sink.get_clock_rate(),tx_bandwidth=sink.get_bandwidth(0),
        clock_source=sink.get_clock_source(0),samples_per_symbol=a.rate/1200)
    if a.mode=='transponder':
        tb.actual.update(rx_rate=source.get_samp_rate(),rx_clock=source.get_clock_rate(),
            rx_bandwidth=source.get_bandwidth(0))
    for key in ('tx_rate','tx_clock','rx_rate','rx_clock'):
        if key in tb.actual and not math.isclose(tb.actual[key],a.rate,rel_tol=1e-6,abs_tol=1):
            raise ValueError('Shared radio rate/clock mismatch: '+json.dumps(tb.actual))
    import pmt
    class TxEvents(gr.basic_block):
        def __init__(self):
            gr.basic_block.__init__(self,'TX async event counter',in_sig=None,out_sig=None)
            self.counts={};self.lock=threading.Lock();port=pmt.intern('events')
            self.message_port_register_in(port);self.set_msg_handler(port,self.receive)
        def receive(self,message):
            events=pmt.dict_ref(pmt.cdr(message),pmt.intern('event_code'),pmt.PMT_NIL)
            with self.lock:
                while pmt.is_pair(events):
                    name=pmt.symbol_to_string(pmt.car(events));events=pmt.cdr(events)
                    self.counts[name]=self.counts.get(name,0)+1
        def snapshot(self):
            with self.lock:return dict(self.counts)
    tb.tx_events=TxEvents();tb.msg_connect(sink,'async_msgs',tb.tx_events,'events')
    return tb


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('telemetry','transponder'),default='telemetry')
    p.add_argument('--rate',type=int,choices=(307200,614400,750000,1500000),default=614400,
        help='Default614400: 512 samples per1200-baud symbol; UHD selects RFIC clocks')
    p.add_argument('--socket',type=Path,default=default_socket());p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=120,choices=range(0,601),metavar='0..600',help='0: hold until stop command; bench runs should be bounded')
    p.add_argument('--tx-frequency',type=float,default=434200000);p.add_argument('--tx-gain',type=float,default=0)
    p.add_argument('--packet-peak',type=float,default=.12,help='Telemetry amplitude; forwarded IQ retains separate headroom')
    p.add_argument('--rx-frequency',type=float);p.add_argument('--rx-gain',type=float,default=30)
    p.add_argument('--passband',type=float,default=20000,help='Forwarded half-bandwidth in Hz')
    p.add_argument('--transition',type=float,default=20000);p.add_argument('--forward-scale',type=float,default=.5)
    p.add_argument('--transmit',action='store_true');a=p.parse_args()
    if not a.transmit:p.error('Explicit --transmit required')
    if not all(math.isfinite(x) for x in (a.tx_frequency,a.tx_gain,a.rx_gain,a.passband,a.transition,a.forward_scale,a.packet_peak)):
        p.error('Numeric settings must be finite')
    if not 430e6<=a.tx_frequency<=440e6 or not 0<=a.tx_gain<=70 or not 0<=a.rx_gain<=76:p.error('Outside bench frequency/gain bounds')
    if not 0<a.forward_scale<=16 or not 1000<=a.passband<=50000 or not 1000<=a.transition<=30000:
        p.error('Invalid forward scale/passband/transition')
    if not .01<=a.packet_peak<=.15:p.error('Packet peak must be .01..15% full scale')
    if a.passband+a.transition>=90000:p.error('Forwarded spectrum must leave clearance for telemetry at -100kHz')
    if a.mode=='transponder' and (a.rx_frequency is None or not math.isfinite(a.rx_frequency) or not 430e6<=a.rx_frequency<=440e6):
        p.error('Explicit bench RX frequency required in transponder mode')
    if a.mode=='transponder' and abs(a.rx_frequency-a.tx_frequency)<300000:p.error('Bench RX/TX centers must be at least300kHz apart')
    a.output.mkdir(parents=True,exist_ok=False);stop=threading.Event();events_lock=threading.Lock()
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
    log=(a.output/'events.jsonl').open('w')
    def event(**record):
        record['host_monotonic']=time.monotonic()
        with events_lock:log.write(json.dumps(record)+'\n');log.flush();os.fsync(log.fileno())
    injector=server=tb=None;error=None;cleanup=[];started=None;last_status={};udp_before=None
    try:
        injector=StreamInjector(event=event,prepare=lambda payload,sequence:waveform(payload,sequence,rate=a.rate,peak=a.packet_peak).tobytes())
        def status():return dict(injector.status(0 if tb is None else tb.adder.nitems_written(0)),mode=a.mode,
            tx_async_events={} if tb is None else tb.tx_events.snapshot())
        # Take IPC ownership before UHD initialization.
        server=ControlServer(a.socket,injector,status,stop)
        tb=build_flow(a,injector);tb.sdrb_sink.set_gain(a.tx_gain,0)
        from gnuradio import uhd
        # GNU Radio otherwise sends an immediate empty SOB before upstream
        # buffers fill. Start TX on hardware time after a250ms priming interval.
        tb.sdrb_sink.set_start_time(uhd.time_spec(tb.sdrb_sink.get_time_now().get_real_secs()+.25))
        udp_before=udp_counters();tb.start();started=time.monotonic();previous=0;last_progress=started
        while not stop.wait(.25):
            last_status=status();now=time.monotonic();count=last_status['output_samples']
            if count!=previous:previous=count;last_progress=now
            if last_status['writer_error']:raise RuntimeError(last_status['writer_error'])
            if now-last_progress>5:raise RuntimeError('No downstream sample progress for five seconds')
            if not server.ready and count>=a.rate:
                server.ready=True;print('BINARY_RADIO_READY '+json.dumps(dict(settings=vars(a),actual=tb.actual,status=last_status),default=str),flush=True)
            if a.seconds and now-started>=a.seconds:break
    except Exception as exc:error=str(exc);raise
    finally:
        if injector is not None:injector.queue.accepting=False
        if server is not None:
            try:server.close()
            except Exception as exc:cleanup.append('Control stop: '+str(exc))
        if tb is not None:
            try:tb.sdrb_sink.set_gain(0,0)
            except Exception as exc:cleanup.append('TX minimum gain: '+str(exc))
        if injector is not None:
            try:injector.close()
            except Exception as exc:cleanup.append('Writer stop: '+str(exc))
        if tb is not None:
            try:tb.stop();tb.wait();last_status=status()
            except Exception as exc:cleanup.append('Flow stop: '+str(exc))
        udp_after=udp_counters()
        result=dict(settings=vars(a),actual={} if tb is None else tb.actual,status=last_status,error=error,cleanup_errors=cleanup,
            udp_delta={} if udp_before is None else {key:udp_after[key]-value for key,value in udp_before.items()},
            elapsed_seconds=None if started is None else time.monotonic()-started,
            scope='Persistent bench sample submission; RF reception and repeater operation require independent proof')
        (a.output/'result.json').write_text(json.dumps(result,indent=2,default=str)+'\n');log.close()
        print('BINARY_RADIO_STOPPED '+json.dumps(result,default=str),flush=True)
        if cleanup and error is None:raise RuntimeError('; '.join(cleanup))
if __name__=='__main__':main()
