"""Receive-only live DBPSK decoder; finite session, original packet forwarding.

Four-second windows advance once per second. A bounded worker queue keeps DSP
out of the radio receive loop. Overrun stops the session instead of silently
losing samples. Raw complex64 IQ and per-packet evidence are retained on disk.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import queue
import socket
import threading
import time
import numpy as np
from modem import decode

RATE = 192000
WINDOW = 4 * RATE
HOP = RATE
FPGA_SHA = '7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99'

def utc():
    return datetime.now(timezone.utc).isoformat()

class Windows:
    """Preallocated overlap buffer; no growing-array copy on each USB read."""
    def __init__(self):
        self.buffer = np.empty(WINDOW, np.complex64)
        self.used = 0
        self.start = 0
    def feed(self, samples):
        at = 0
        while at < len(samples):
            n = min(WINDOW-self.used, len(samples)-at)
            self.buffer[self.used:self.used+n] = samples[at:at+n]
            self.used += n; at += n
            if self.used == WINDOW:
                yield self.start, self.buffer.copy()
                self.buffer[:WINDOW-HOP] = self.buffer[HOP:].copy()
                self.used -= HOP
                self.start += HOP
    def finish(self):
        if self.used:
            return self.start, self.buffer[:self.used].copy()

def downsample(raw):
    n = np.arange(129) - 64
    taps = 2*(18000/RATE)*np.sinc(2*(18000/RATE)*n)*np.hamming(129)
    taps /= taps.sum()
    return np.convolve(raw, taps, mode='same')[::4].astype(np.complex64)

class Decoder:
    def __init__(self, output, forward):
        self.output = output
        self.forward = forward
        self.seen = set()
        self.packets = []
        self.forwarded = 0
    def process(self, start, raw):
        begun = time.monotonic()
        packets = decode(downsample(raw), single_window=True)
        for packet in packets:
            key = (packet['sequence'], packet['hex'])
            if key in self.seen:
                continue
            self.seen.add(key)
            packet.update(window_start=start//4, received_utc=utc(),
                          capture_window_end_s=(start+len(raw))/RATE,
                          decode_seconds=time.monotonic()-begun)
            # Persist validated original bytes before forwarding; never regenerate.
            with (self.output/'packets.jsonl').open('a') as f:
                f.write(json.dumps(packet)+'\n')
            if self.forward:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(bytes.fromhex(packet['hex']), ('127.0.0.1', 10019))
                self.forwarded += 1
            self.packets.append(packet)
            print('BPSK_RX_PACKET '+json.dumps(dict(
                request=packet['sequence'], name=packet['decoded']['name'],
                utc=packet['received_utc'], forwarded=self.forward,
                total=len(self.packets))), flush=True)

def run(args):
    fpga = args.images/'usrp_b210_fpga.bin'
    if hashlib.sha256(fpga.read_bytes()).hexdigest() != FPGA_SHA:
        raise ValueError('FPGA hash mismatch')
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ['UHD_IMAGES_DIR'] = str(args.images)
    import uhd
    radio = uhd.usrp.MultiUSRP(f'type=b200,fpga={fpga}')
    radio.set_rx_rate(RATE, args.channel)
    radio.set_rx_freq(uhd.types.TuneRequest(args.frequency), args.channel)
    radio.set_rx_gain(args.gain, args.channel)
    radio.set_rx_antenna('RX2', args.channel)
    if abs(radio.get_rx_rate(args.channel)-RATE)>1:
        raise ValueError('unexpected sample rate')
    report = dict(receiver_version=2, utc=utc(), frequency_hz=radio.get_rx_freq(args.channel),
                  channel=args.channel, antenna='RX2', rate=radio.get_rx_rate(args.channel),
                  gain=radio.get_rx_gain(args.channel), fpga_sha256=FPGA_SHA,
                  raw_format='little-endian complex64, 192000 samples/s', errors=[])
    (args.output/'session.json').write_text(json.dumps(report, indent=2)+'\n')
    sa = uhd.usrp.StreamArgs('fc32', 'sc16'); sa.channels=[args.channel]
    stream = radio.get_rx_stream(sa); md=uhd.types.RXMetadata()
    buf=np.empty((1,8192),np.complex64)
    jobs=queue.Queue(maxsize=4); failed=threading.Event()
    decoder=Decoder(args.output,args.forward)
    def worker():
        while True:
            job=jobs.get()
            try:
                if job is None:return
                if not failed.is_set():decoder.process(*job)
            except Exception as exc:
                report['errors'].append('decoder: '+repr(exc));failed.set()
            finally:jobs.task_done()
    thread=threading.Thread(target=worker,daemon=True);thread.start()
    # Keep SD-card writes and window construction out of the USB receive loop.
    # 64 chunks provide about 2.7 seconds of bounded scheduling/storage headroom.
    chunks=queue.Queue(maxsize=64)
    metrics=dict(chunk_queue_peak=0, decode_queue_peak=0, max_recv_gap_s=0.0,
                 max_storage_chunk_s=0.0)
    def storage_worker():
        windows=Windows()
        try:
            with (args.output/'raw-192k.cf32').open('wb') as rawfile:
                while True:
                    chunk=chunks.get()
                    try:
                        if chunk is None:break
                        if failed.is_set():continue
                        begun=time.monotonic()
                        rawfile.write(chunk.astype('<c8',copy=False).tobytes())
                        for job in windows.feed(chunk):
                            try:jobs.put_nowait(job)
                            except queue.Full:
                                report['errors'].append('decoder backlog exceeded four windows')
                                failed.set();break
                        metrics['decode_queue_peak']=max(metrics['decode_queue_peak'],jobs.qsize())
                        metrics['max_storage_chunk_s']=max(metrics['max_storage_chunk_s'],time.monotonic()-begun)
                    finally:chunks.task_done()
                if not failed.is_set():
                    tail=windows.finish()
                    if tail is not None:jobs.put(tail)
        except Exception as exc:
            report['errors'].append('storage: '+repr(exc));failed.set()
        finally:
            # Drain any already queued chunks if disk failed, unblocking shutdown.
            while True:
                try:chunks.get_nowait();chunks.task_done()
                except queue.Empty:break
    storage=threading.Thread(target=storage_worker,daemon=True);storage.start()
    samples=0
    command=uhd.types.StreamCMD(uhd.types.StreamMode.start_cont);command.stream_now=True
    stream.issue_stream_cmd(command)
    print('BPSK_RX_READY '+json.dumps(report),flush=True)
    end=time.monotonic()+args.seconds
    next_status=time.monotonic()+10
    last_recv=time.monotonic()
    try:
        while time.monotonic()<end and not failed.is_set():
            if time.monotonic()>=next_status:
                print('BPSK_RX_STATUS '+json.dumps(dict(
                    captured_s=round(samples/RATE,1), packets=len(decoder.packets),
                    forwarded=decoder.forwarded, queued_windows=jobs.qsize(),
                    queued_chunks=chunks.qsize())),flush=True)
                next_status=time.monotonic()+10
            before=time.monotonic()
            metrics['max_recv_gap_s']=max(metrics['max_recv_gap_s'],before-last_recv)
            n=stream.recv(buf,md,.5);last_recv=time.monotonic()
            if md.error_code!=uhd.types.RXMetadataErrorCode.none:
                report['errors'].append(md.strerror());failed.set();break
            if not n:continue
            try:chunks.put_nowait(buf[0,:n].copy())
            except queue.Full:
                report['errors'].append('storage backlog exceeded 64 chunks');failed.set();break
            samples+=n
            metrics['chunk_queue_peak']=max(metrics['chunk_queue_peak'],chunks.qsize())
    except KeyboardInterrupt:
        report['stopped_by_user']=True
    except Exception as exc:
        report['errors'].append('capture: '+repr(exc));failed.set()
    finally:
        stream.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
        if storage.is_alive():chunks.put(None)
        storage.join()
        jobs.put(None);thread.join()
        report['pipeline_metrics']=metrics
        report.update(samples=samples,packets=decoder.packets,forwarded=decoder.forwarded,ended_utc=utc())
        (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print('BPSK_RX_RESULT '+json.dumps(dict(samples=samples,packets=len(decoder.packets),
              forwarded=decoder.forwarded,errors=report['errors'])),flush=True)
    return 1 if report['errors'] else 0

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seconds',type=int,default=600)
    p.add_argument('--frequency',type=float,default=437000000)
    p.add_argument('--gain',type=float,default=0)
    p.add_argument('--channel',type=int,choices=(0,1),default=0)
    p.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--forward',action='store_true')
    args=p.parse_args()
    if not 1<=args.seconds<=3600 or not 430e6<=args.frequency<=440e6 or not 0<=args.gain<=40:
        p.error('bench range exceeded (duration 1..3600 s)')
    raise SystemExit(run(args))
