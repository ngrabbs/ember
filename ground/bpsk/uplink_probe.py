"""One bounded, explicitly triggered LibreSDR bench burst. No automatic retries.

Default is waveform generation only. --transmit additionally requires GO on stdin
within 30 seconds of READY. Fixture packets must never be forwarded to Yamcs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import sys
import time
import numpy as np
from modem import frame
from codec import encode

RATE = 192000
DIGITAL_OFFSET = 20000
FPGA_SHA = '7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99'


def waveform(kind, amplitude, sequence):
    if kind not in ('tone', 'packet') or not 0 < amplitude <= 0.05:
        raise ValueError('invalid kind or amplitude; maximum 0.05 full scale')
    if not 0 <= sequence <= 0xffffffff:
        raise ValueError('sequence out of range')
    packet = b''
    if kind == 'tone':
        a = np.ones(RATE, dtype=float)
    else:
        # Synthetic, recognizable bench fixture, never live system telemetry.
        packet = encode('HEARTBEAT', sequence=sequence & 0x3fff, source=3,
                        target=1, source_boot_id=0x52585453, uptime_ms=0,
                        payload=dict(mode=2, configuration=1, telemetry_period_ms=0))
        bits = np.unpackbits(np.frombuffer(frame(packet, sequence), np.uint8))
        a = np.r_[np.zeros(RATE//20),
                  np.repeat(1-2*(np.cumsum(bits) % 2).astype(float), RATE//1200),
                  np.zeros(RATE//20)]
    a = (a*amplitude*np.exp(2j*np.pi*DIGITAL_OFFSET*np.arange(len(a))/RATE)).astype(np.complex64)
    if len(a) > RATE*2 or not np.isfinite(a).all():
        raise ValueError('burst exceeds bounds')
    return a, packet


def run(args):
    if not 434e6 <= args.frequency <= 436e6:
        raise ValueError('frequency outside RX bench range')
    a, packet = waveform(args.kind, args.amplitude, args.sequence)
    args.output.mkdir(parents=True, exist_ok=False)
    np.save(args.output/'tx-iq.npy', a)
    report = dict(kind=args.kind, synthetic_fixture=True, packet_hex=packet.hex(),
                  rf_sequence=args.sequence, requested_signal_hz=args.frequency,
                  digital_offset_hz=DIGITAL_OFFSET, sample_rate_hz=RATE,
                  amplitude=args.amplitude, samples=len(a), duration_s=len(a)/RATE,
                  samples_sent=0, errors=[], transmitted=False)
    path = args.output/'result.json'
    path.write_text(json.dumps(report, indent=2)+'\n')
    if not args.transmit:
        print(json.dumps(report)); return
    fpga = args.images/'usrp_b210_fpga.bin'
    if hashlib.sha256(fpga.read_bytes()).hexdigest() != FPGA_SHA:
        raise ValueError('FPGA hash mismatch')
    os.environ['UHD_IMAGES_DIR'] = str(args.images)
    import uhd
    radio = uhd.usrp.MultiUSRP(f'type=b200,fpga={fpga}')
    radio.set_master_clock_rate(49152000)
    radio.set_tx_rate(RATE, 0)
    radio.set_tx_gain(0, 0)
    radio.set_tx_antenna('TX/RX', 0)
    radio.set_tx_freq(uhd.types.TuneRequest(args.frequency-DIGITAL_OFFSET), 0)
    if abs(radio.get_tx_rate(0)-RATE)>1 or abs(radio.get_tx_gain(0))>0.01:
        raise ValueError('unexpected rate/gain')
    report.update(actual_tune_hz=radio.get_tx_freq(0), actual_rate=radio.get_tx_rate(0),
                  gain=radio.get_tx_gain(0), antenna=radio.get_tx_antenna(0), fpga_sha256=FPGA_SHA)
    sa = uhd.usrp.StreamArgs('fc32', 'sc16'); sa.channels = [0]
    stream = radio.get_tx_stream(sa)
    print('UPLINK_PROBE_READY '+json.dumps(report), flush=True)
    try:
        if not select.select([sys.stdin], [], [], 30)[0] or sys.stdin.readline().strip() != 'GO':
            raise RuntimeError('no explicit GO within 30 seconds')
        md = uhd.types.TXMetadata()
        md.start_of_burst = True; md.end_of_burst = True
        md.has_time_spec = True
        md.time_spec = uhd.types.TimeSpec(radio.get_time_now().get_real_secs()+0.25)
        sent = stream.send(a.reshape(1, -1), md, 3.0)
        report['samples_sent'] = int(sent)
        if sent != len(a):
            raise RuntimeError('short TX send; no retry')
        am = uhd.types.TXAsyncMetadata(); end = time.monotonic()+3; ack = False
        while time.monotonic()<end:
            if stream.recv_async_msg(am, 0.1):
                if am.event_code == uhd.types.TXMetadataEventCode.burst_ack:
                    ack = True; break
                raise RuntimeError('TX event: '+str(am.event_code))
        if not ack:
            raise RuntimeError('no burst acknowledgment')
        report['transmitted'] = True
    except BaseException as exc:
        report['errors'].append(str(exc)); raise
    finally:
        try:
            stop = uhd.types.TXMetadata(); stop.end_of_burst = True
            stream.send(np.zeros((1, 0), np.complex64), stop, 0.5)
        finally:
            radio.set_tx_gain(0, 0)
            path.write_text(json.dumps(report, indent=2)+'\n')
            print('UPLINK_PROBE_RESULT '+json.dumps(report), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind', choices=('tone', 'packet'), required=True)
    p.add_argument('--frequency', type=float, required=True)
    p.add_argument('--amplitude', type=float, default=0.01)
    p.add_argument('--sequence', type=int, default=901)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--images', type=Path, default=Path.home()/'work/ember-lte/images')
    p.add_argument('--transmit', action='store_true')
    run(p.parse_args())
