#!/usr/bin/env python3
"""Assess a finite series using independent TX and RF evidence (no RF generation)."""
import argparse,json
from pathlib import Path

def assess(tx,rx,capture):
    expected=tx['sequences'];rows=rx['packets']
    received=[r['sequence'] for r in rows if r['sequence'] in expected]
    mismatches=[r['sequence'] for r in rows if r['hex']!=tx['packet_hex']]
    missing=sorted(set(expected)-set(received))
    return dict(expected_sequences=expected,received_sequences=received,missing_sequences=missing,
        unexpected_sequences=sorted({r['sequence'] for r in rows}-set(expected)),
        payload_mismatches=mismatches,delivery_fraction=len(set(received))/len(expected),
        duplicate_output_count=len(received)-len(set(received)),
        overlap_detections_suppressed=rx.get('overlap_duplicates'),
        stream_errors=capture['errors'],dropped_decode_windows=capture.get('dropped_decode_windows',0),
        all_source_samples_consumed=tx.get('source_samples_emitted')==tx['samples'],
        scope='RF series delivery only; saved inner telemetry, independent Yamcs archive verification required')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tx',type=Path,required=True)
    p.add_argument('--rx',type=Path,required=True);p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Choose a new report')
    report=assess(json.loads(a.tx.read_text()),json.loads(a.rx.read_text()),json.loads(a.capture.read_text()))
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
