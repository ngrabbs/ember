#!/usr/bin/env python3
"""Bounded LibreSDR TX/RX self-check; does not validate LTE or calibrated power."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import threading
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--transmit', action='store_true', help='Required: enable the short RF tone test')
parser.add_argument('--tx-gain', type=float, default=0, help='UHD gain, 0..50 dB')
parser.add_argument('--duration', type=float, default=.25, help='TX measurement interval, .25..5 seconds')
args = parser.parse_args()
if not 0 <= args.tx_gain <= 50 or not .25 <= args.duration <= 5:
    parser.error('Gain/duration outside bounded test ranges')
if not args.transmit:
    parser.error('This test emits RF. Review antenna setup, then pass --transmit.')
image_dir = Path(os.environ.get('LTE_IMAGE_DIR', str(Path.home() / 'work/ember-lte/images')))
fpga = image_dir / 'usrp_b210_fpga.bin'
expected = '7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99'
if hashlib.sha256(fpga.read_bytes()).hexdigest() != expected:
    raise SystemExit('Custom FPGA checksum mismatch')
os.environ['UHD_IMAGES_DIR'] = str(image_dir)
import numpy as np
import uhd

rate = 2_000_000
frequency = 751_000_000
spacing = 125_000
u = uhd.usrp.MultiUSRP(f'type=b200,fpga={fpga},master_clock_rate=16000000')
if min(u.get_rx_num_channels(), u.get_tx_num_channels()) < 2:
    raise SystemExit('Expected a two-channel radio')
u.set_rx_rate(rate, 1)
u.set_rx_freq(uhd.types.TuneRequest(frequency), 1)
u.set_rx_gain(20, 1)
u.set_rx_antenna('RX2', 1)
u.set_tx_rate(rate, 0)
u.set_tx_freq(uhd.types.TuneRequest(frequency), 0)
u.set_tx_gain(args.tx_gain, 0)
u.set_tx_antenna('TX/RX', 0)
time.sleep(.2)
sa = uhd.usrp.StreamArgs('fc32', 'sc16'); sa.channels = [1]
rx = u.get_rx_stream(sa)
sa = uhd.usrp.StreamArgs('fc32', 'sc16'); sa.channels = [0]
tx = u.get_tx_stream(sa)
stop = threading.Event()
tx_errors = []
wave = (.1 * np.exp(2j * np.pi * spacing * np.arange(8192) / rate)).astype(np.complex64)
def transmit():
    md = uhd.types.TXMetadata(); md.start_of_burst = True; md.end_of_burst = False
    md.has_time_spec = True; md.time_spec = u.get_time_now() + uhd.types.TimeSpec(.1)
    try:
        while not stop.is_set():
            n = tx.send(wave, md, .2)
            md.start_of_burst = False; md.has_time_spec = False
            if n != wave.size:
                tx_errors.append(f'short send: {n}/{wave.size}')
        md.end_of_burst = True
        tx.send(np.zeros((1, 1), dtype=np.complex64), md, .2)
    except Exception as exc:
        tx_errors.append(str(exc))

buffer = np.zeros((1, 16384), dtype=np.complex64)
md = uhd.types.RXMetadata()
errors = {}
def capture(count):
    chunks = []; total = 0; deadline = time.monotonic() + count / rate + 3
    while total < count and time.monotonic() < deadline:
        n = rx.recv(buffer, md, .5)
        if md.error_code != uhd.types.RXMetadataErrorCode.none:
            key = str(md.error_code); errors[key] = errors.get(key, 0) + 1
        if n:
            chunks.append(buffer[0, :n].copy()); total += n
    if total < count:
        raise RuntimeError(f'Incomplete RX capture: {total}/{count}')
    return np.concatenate(chunks)[:count]

cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont); cmd.stream_now = True
rx.issue_stream_cmd(cmd)
thread = None
try:
    capture(rate // 4)
    before = capture(rate // 4)
    thread = threading.Thread(target=transmit); thread.start()
    capture(rate // 4)
    during = capture(int(rate * args.duration))
    stop.set(); thread.join(timeout=2)
    if thread.is_alive():
        raise RuntimeError('TX thread failed to stop')
    capture(rate // 4)
    after = capture(rate // 4)
finally:
    stop.set()
    if thread is not None:
        thread.join(timeout=2)
    cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
    rx.issue_stream_cmd(cmd)

def metrics(samples):
    size = 16384
    blocks = samples[:samples.size // size * size].reshape(-1, size)
    window = np.hanning(size)
    spectrum = np.mean(np.abs(np.fft.fft(blocks * window, axis=1)) ** 2, axis=0) / window.sum() ** 2
    target = round(spacing / rate * size)
    signal = float(np.sum(spectrum[target-2:target+3]))
    return {'tone_power_dbfs_relative': round(10*np.log10(max(signal, 1e-30)), 2),
            'rms_dbfs_relative': round(10*np.log10(max(float(np.mean(np.abs(samples)**2)), 1e-30)), 2),
            'peak_magnitude': round(float(np.max(np.abs(samples))), 4)}
result = {'rx_channel': 1, 'tx_channel': 0, 'rx_center_hz': frequency,
          'tone_rf_hz': frequency + spacing, 'sample_rate': rate,
          'tx_gain_db': u.get_tx_gain(0), 'rx_gain_db': u.get_rx_gain(1),
          'tx_digital_amplitude': .1, 'before': metrics(before),
          'during': metrics(during), 'after': metrics(after),
          'rx_metadata_errors': errors, 'tx_errors': tx_errors,
          'limitation': 'Same SDR: internal coupling may contribute; no LTE decode or calibrated power.'}
result['tone_rise_db'] = round(result['during']['tone_power_dbfs_relative'] - result['before']['tone_power_dbfs_relative'], 2)
result['tone_fall_db'] = round(result['during']['tone_power_dbfs_relative'] - result['after']['tone_power_dbfs_relative'], 2)
print(json.dumps(result, indent=2))
if errors or tx_errors:
    raise SystemExit(1)
