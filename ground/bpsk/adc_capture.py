"""Offline DBPSK analysis of a bounded Pico RX capture. Never forwards or executes.

Native telemetry fixtures may be used as bench frame payloads; decoding one
is not evidence of an onboard command decoder or command execution.
"""
import argparse
import json
from pathlib import Path
import re
import numpy as np
from modem import decode


def parse_capture(text):
    matches = list(re.finditer(
        r'\[rx_test\] lo=1 complete=1 shutdown_verified=1[^\n]*\n'
        r'\[rx_adc\] n=(\d+) interval_us=(\d+) elapsed_us=(\d+) '
        r'late_gt10us=(\d+) min=(\d+) max=(\d+) sum=(\d+) hex=([0-9a-f]+)',
        text.replace('\r', '')))
    if len(matches) != 1:
        raise ValueError('require exactly one completed RX capture with verified shutdown')
    n, interval, elapsed, late, low, high, total = map(int, matches[0].groups()[:7])
    raw = matches[0].group(8)
    if n not in (4096, 32768) or interval != 125 or len(raw) != n*3:
        raise ValueError('invalid capture shape or sample interval')
    if late or abs(elapsed-(n-1)*interval) > 2000:
        raise ValueError('capture timing not qualified')
    samples = np.array([int(raw[i:i+3], 16) for i in range(0, len(raw), 3)])
    if (int(samples.min()), int(samples.max()), int(samples.sum())) != (low, high, total):
        raise ValueError('capture summary mismatch')
    if low == 0 or high == 4095:
        raise ValueError('ADC clipping')
    return samples


def analytic_adc(samples):
    a = np.asarray(samples, dtype=float)
    if a.ndim != 1 or not len(a) or not np.isfinite(a).all():
        raise ValueError('invalid ADC samples')
    # Upsample 8k to 48k for the existing integer-samples/symbol decoder.
    # Linear interpolation adds no information; timing errors are rejected above.
    a = np.interp(np.arange(len(a)*6)/6, np.arange(len(a)), a-a.mean())
    mask = np.zeros(len(a)); mask[0] = 1
    mask[1:(len(a)+1)//2] = 2
    if len(a) % 2 == 0:
        mask[len(a)//2] = 1
    return np.fft.ifft(np.fft.fft(a)*mask).astype(np.complex64)


def decode_capture(text):
    samples = parse_capture(text)
    return {'samples': len(samples), 'sample_rate_hz': 8000,
            'mode': 'offline-only; no forwarding or command execution',
            'packets': decode(analytic_adc(samples), 48000)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('console', type=Path)
    args = p.parse_args()
    print(json.dumps(decode_capture(args.console.read_text()), indent=2))
