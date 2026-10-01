"""Decode an observational `eps json` line; no transport or charger control."""
import argparse
import json
import math
from pathlib import Path

D = json.loads(Path(__file__).with_name('ltc4162.json').read_text())


def decode(sample, *, cells, rsnsb_ohms, rsnsi_ohms):
    if type(cells) is not int or not 1 <= cells <= 8:
        raise ValueError('confirmed board cell count must be 1..8')
    if not all(math.isfinite(r) and r > 0 for r in (rsnsb_ohms,rsnsi_ohms)):
        raise ValueError('sense resistors must be finite positive ohms')
    if sample.get('profile') != D['profile']:
        raise ValueError('unexpected readout profile')
    raw=sample['registers']
    if set(raw) != {r['name'] for r in D['registers']}:
        raise ValueError('incomplete/unexpected register readout')
    if not all(type(v) is int and 0 <= v <= 65535 for v in raw.values()):
        raise ValueError('registers must be unsigned 16-bit words')
    chemistry=(raw['chem_cells']>>8)&15
    detected=raw['chem_cells']&15
    adc_valid=bool(raw['telemetry_status']&1)
    compatible=chemistry<=3 and (not detected or detected==cells)
    result={'raw':raw,'adc_valid':adc_valid,'chemistry':D['chemistries'].get(str(chemistry),'UNKNOWN'),
            'detected_cells':detected,'configured_cells':cells,'cells_from_board_config':not bool(detected),
            'conversion_valid':adc_valid and compatible,'engineering':None}
    if not result['conversion_valid']:
        return result
    values={r['name']:raw[r['name']]-65536 if r.get('signed') and raw[r['name']]>=32768 else raw[r['name']]
            for r in D['registers']}
    fields={r['name']:r for r in D['registers']}
    def scaled(name):
        f=fields[name]
        return values[name]*f['scale']+f.get('offset',0)
    result['engineering']={'battery_pack_v':scaled('vbat')*cells,'input_v':scaled('vin'),
                           'output_v':scaled('vout'), 'battery_ma':values['ibat']*fields['ibat']['sense_voltage_lsb_uv']/(rsnsb_ohms*1000),
                           'input_ma':values['iin']*fields['iin']['sense_voltage_lsb_uv']/(rsnsi_ohms*1000),
                           'die_temp_c':scaled('die_temp')}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample',type=Path)
    parser.add_argument('--cells',type=int,required=True)
    parser.add_argument('--rsnsb-ohms',type=float,required=True)
    parser.add_argument('--rsnsi-ohms',type=float,required=True)
    a=parser.parse_args()
    print(json.dumps(decode(json.loads(a.sample.read_text()),cells=a.cells,rsnsb_ohms=a.rsnsb_ohms,rsnsi_ohms=a.rsnsi_ohms),indent=2))
