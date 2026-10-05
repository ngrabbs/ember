#!/usr/bin/env python3
"""Bounded two-frequency RF uplink proof using the ground radio's free TX port.

A single UHD owner receives the translated downlink and telemetry while sending
5kHz / silence /11kHz / silence in6second slots above the uplink center.
This is optional bench instrumentation, not an operational uplink protocol.
"""
import argparse,json,math,signal,threading,time
from pathlib import Path
import numpy as np
from libresdr_live_rx import run

TONES=(0,5000,0,11000)
SLOT_SECONDS=6


def spectral_measurement(samples,rate):
    n=8192
    if len(samples)<n:return None
    f=np.fft.fftfreq(n,1/rate)
    power=abs(np.fft.fft(samples[:n]*np.hanning(n)))**2
    noise=(abs(f)>2000)&(abs(f)<25000)
    for tone in (5000,11000):noise&=abs(f-tone)>2000
    floor=max(float(np.median(power[noise])),1e-20)
    result={}
    for tone in (5000,11000):
        indices=np.flatnonzero(abs(f-tone)<1500)
        peak=indices[np.argmax(power[indices])]
        result[str(tone)]=dict(peak_hz=float(f[peak]),power=float(power[peak]),snr_db=float(10*np.log10(max(power[peak],1e-20)/floor)))
    return dict(tones=result,noise_power=floor,rms=float(np.sqrt(np.mean(abs(samples)**2))),peak=float(np.max(abs(samples))))


class Probe:
    def __init__(self,a):
        self.a=a;self.stop=threading.Event();self.thread=None;self.error=None
        self.samples=0;self.events={};self.last_bin=None;self.tx_start=None
    def configure(self,radio,rate):
        import uhd
        self.radio=radio;self.rate=rate
        radio.set_tx_rate(rate,self.a.tx_channel)
        radio.set_tx_freq(uhd.types.TuneRequest(self.a.uplink_frequency),self.a.tx_channel)
        radio.set_tx_antenna('TX/RX',self.a.tx_channel);radio.set_tx_gain(self.a.uplink_gain,self.a.tx_channel)
        radio.set_tx_bandwidth(rate,self.a.tx_channel)
        if not math.isclose(radio.get_tx_rate(self.a.tx_channel),rate,abs_tol=1):raise ValueError('Unexpected probe TX rate')
        sa=uhd.usrp.StreamArgs('fc32','sc16');sa.channels=[self.a.tx_channel]
        self.stream=radio.get_tx_stream(sa)
        self.actual=dict(tx_rate=radio.get_tx_rate(self.a.tx_channel),master_clock=radio.get_master_clock_rate(),
            frequency=radio.get_tx_freq(self.a.tx_channel),gain=radio.get_tx_gain(self.a.tx_channel),
            antenna=radio.get_tx_antenna(self.a.tx_channel),channel=self.a.tx_channel)
    def start(self):
        self.log=(self.a.output/'repeater-spectrum.jsonl').open('w')
        self.tx_start=self.radio.get_time_now().get_real_secs()+.25
        self.thread=threading.Thread(target=self.send,daemon=True);self.thread.start()
        print('UPLINK_PROBE_READY '+json.dumps(dict(actual=self.actual,tx_start=self.tx_start,slot_seconds=SLOT_SECONDS,tones=TONES)),flush=True)
    def send(self):
        import uhd
        count=100000 #50ms, integer cycles for both tones; continuous tone phase.
        waves={tone:(self.a.uplink_peak*np.exp(2j*np.pi*tone*np.arange(count)/self.rate)).astype(np.complex64).reshape(1,-1) for tone in (5000,11000)}
        waves[0]=np.zeros((1,count),np.complex64)
        md=uhd.types.TXMetadata();md.start_of_burst=True;md.has_time_spec=True
        md.time_spec=uhd.types.TimeSpec(self.tx_start)
        try:
            while not self.stop.is_set():
                tone=TONES[int(self.samples/self.rate)//SLOT_SECONDS%len(TONES)]
                wave=waves[tone];offset=0
                while offset<count and not self.stop.is_set():
                    n=self.stream.send(wave[:,offset:],md,1)
                    if n==0:raise RuntimeError('Probe TX made no progress')
                    self.samples+=n;offset+=n;md.start_of_burst=False;md.has_time_spec=False
                event=self.stream.recv_async_msg(0.0)
                if event is not None:
                    key=str(event.event_code);self.events[key]=self.events.get(key,0)+1
        except Exception as exc:self.error=str(exc)
        finally:
            md.end_of_burst=True;md.has_time_spec=False;md.start_of_burst=False
            try:self.stream.send(np.zeros((1,0),np.complex64),md,1)
            except Exception as exc:self.error=self.error or str(exc)
    def observe(self,samples,hardware_time):
        if self.error:raise RuntimeError(self.error)
        t=hardware_time-self.tx_start
        bucket=int(t*4)
        if bucket==self.last_bin:return
        self.last_bin=bucket
        row=spectral_measurement(samples,self.rate)
        if row is None:return
        row.update(rx_hardware_time=hardware_time,tx_relative_seconds=t,
            expected_tone_hz=0 if t<0 else TONES[int(t)//SLOT_SECONDS%len(TONES)],
            received_unix=time.time())
        self.log.write(json.dumps(row)+'\n');self.log.flush()
    def close(self):
        self.stop.set()
        if self.thread is not None:self.thread.join(timeout=3)
        if self.thread is not None and self.thread.is_alive():self.error=self.error or 'Probe TX did not stop'
        self.radio.set_tx_gain(0,self.a.tx_channel)
        if hasattr(self,'log'):self.log.close()
        result=dict(actual=self.actual,tx_samples=self.samples,tx_async_events=self.events,error=self.error,
            tx_start_hardware_time=self.tx_start,slot_seconds=SLOT_SECONDS,tones=TONES)
        (self.a.output/'uplink-probe.json').write_text(json.dumps(result,indent=2)+'\n')
        print('UPLINK_PROBE_STOPPED '+json.dumps(result),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frequency',type=float,default=434200000);p.add_argument('--gain',type=float,default=40)
    p.add_argument('--channel',type=int,choices=(0,1),default=0)
    p.add_argument('--tx-channel',type=int,choices=(0,1),default=0)
    p.add_argument('--uplink-frequency',type=float,default=435100000)
    p.add_argument('--uplink-gain',type=float,default=0);p.add_argument('--uplink-peak',type=float,default=.1)
    p.add_argument('--seconds',type=int,default=80,choices=range(1,121))
    p.add_argument('--images',type=Path,default=Path.home()/'work/ember-lte/images')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--forward',action='store_true')
    p.add_argument('--transmit',action='store_true');p.add_argument('--direct-check',action='store_true',help='Receive the uplink locally; no Yamcs forwarding');a=p.parse_args()
    if not a.transmit:p.error('Explicit --transmit required')
    if not all(math.isfinite(x) for x in (a.frequency,a.gain,a.uplink_frequency,a.uplink_gain,a.uplink_peak)):p.error('Finite settings required')
    if not 430e6<=a.frequency<=440e6 or not 430e6<=a.uplink_frequency<=440e6:p.error('Invalid bench frequencies')
    if a.direct_check:
        if a.forward or a.frequency!=a.uplink_frequency:p.error('Direct check requires equal centers and no Yamcs forwarding')
    elif abs(a.frequency-a.uplink_frequency)<300000:p.error('Invalid separated bench frequencies')
    if not 0<=a.gain<=76 or not 0<=a.uplink_gain<=30 or not .01<=a.uplink_peak<=.15:p.error('Outside bench gain/amplitude range')
    def terminate(*_):raise KeyboardInterrupt('Termination requested')
    signal.signal(signal.SIGTERM,terminate)
    probe=Probe(a)
    try:run(a,probe)
    except KeyboardInterrupt:raise SystemExit(130)
if __name__=='__main__':main()
