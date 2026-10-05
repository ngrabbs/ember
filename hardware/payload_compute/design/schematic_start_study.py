"""Reproducible planning allocations, not a completed circuit/ERC qualification."""
from itertools import product
from pathlib import Path
import json
import math

BASE = Path(__file__).resolve().parent


def threshold(top, bottom, sense, tolerance=0.003, leakage=25e-9):
    corners = [v * (1 + t / b) + i * t for t, b, v, i in product(
        [top * (1 - tolerance), top * (1 + tolerance)],
        [bottom * (1 - tolerance), bottom * (1 + tolerance)],
        sense, [-leakage, leakage])]
    return [min(corners), max(corners)]


windows = {}
for name, uv, ov in [('USB', 324e3, 402e3), ('BATTERY', 143e3, 215e3)]:
    windows[name] = {
        'UV_rising_V': threshold(uv, 10e3, [.396, .404]),
        'UV_falling_V': threshold(uv, 10e3, [.387, .400]),
        'OV_rising_V': threshold(ov, 10e3, [.396, .404]),
        'OV_falling_V': threshold(ov, 10e3, [.387, .400]),
    }
assert windows['USB']['UV_rising_V'][1] < 14.25
assert windows['USB']['OV_rising_V'][0] > 15.75
assert windows['BATTERY']['OV_rising_V'][0] > 8.4

# Separate low/high/off worst-case DC calculations; no intermediate-rail guarantee.
series = [4700*.99, 4700*1.01]
pulldown = [10000*.99, 10000*1.01]
en_high = min((2.4/s-.1e-6)/(1/s+1/p) for s,p in product(series,pulldown))
en_low = max((.4/s+.1e-6)/(1/s+1/p) for s,p in product(series,pulldown))
en_off = (10e-6+.1e-6)*max(pulldown)
assert en_high > 1.223 and max(en_low,en_off) < .45

loads = {'lab_7W':14.075, 'lab_15W':22.075, 'flight_15W':18.075}
usb_limit = 1.8/1.001
battery_limit = 1.8*1650/750/1.001
current = {name: power*1.2/.85/(6 if name.startswith('flight') else 14.25)
           for name,power in loads.items()}
limit_fit = {name:value <= (battery_limit if name.startswith('flight') else usb_limit)
             for name,value in current.items()}
assert limit_fit == {'lab_7W':True, 'lab_15W':False, 'flight_15W':False}

# Resource audit uses manufacturer AF/ADC tables, not only pin-count arithmetic.
plan = json.loads((BASE/'supervisor_pin_plan.json').read_text())
rows = plan['rows']
pins = [r['pin'] for r in rows]
nets = [r['net'] for r in rows]
assert len(pins) == len(set(pins)) == plan['gpio_uses'] == 69
assert len(nets) == len(set(nets))
reserved = set(plan['clock_pins'] + [plan['reset_pin']] + plan['optional_lse_pins'])
assert not reserved.intersection(pins)
available = ({f'PA{i}' for i in range(16)} | {f'PB{i}' for i in range(16)} |
             {f'PC{i}' for i in range(16)} | {f'PD{i}' for i in range(16)} |
             {f'PE{i}' for i in range(16)} | {f'PF{i}' for i in range(14)})
assert set(pins) <= available  # DS13560 Rev 6 Figure 11, LQFP100 only.
af = {'PC4':3,'PC5':3,'PB12':3,'PB13':3,'PA9':1,'PA10':1,'PA2':1,'PA3':1,
      'PB8':6,'PB9':6,'PA0':2,'PA1':2,'PB10':2,'PB11':2,'PB4':1,'PB5':1,
      'PA13':0,'PA14':0}
assert {r['pin']:r['af'] for r in rows if r['mode']=='alternate'} == af
adc = {'PA4':4,'PA5':5,'PA6':6,'PA7':7,'PB0':8,'PB1':9,'PB2':10}
assert {r['pin']:r['adc_channel'] for r in rows if r['mode']=='analog'} == adc
assert not any(r['pin'] in {'PC0','PC1','PC2','PC3'} and r['mode']=='analog' for r in rows)

frame_bytes = 1456*1088*2*3
# RC ideal model only. Vsafe 0.2 V is an engineering example, not a vendor limit.
decay = {name: {str(c): time/(c*1e-6*math.log(v/.2))
               for c in [50,100,220,470,1000]}
         for name,v,time in [('3V3_1p5ms',3.3,.0015),('1V8_4ms',1.8,.004)]}
result = {
    'status':'PASS for planning/resource arithmetic; physical packages, dynamics and measured loads pending',
    'raw_windows_V':windows,
    'eFuse_EN_static_V':{'high_min':en_high,'low_max':en_low,'AON_zero_max':en_off},
    'input_current_with_20pct_margin_A':current,
    'current_limit_min_A':{'USB':usb_limit,'BATTERY':battery_limit},
    'current_limit_allocation_fits':limit_fit,
    'MCU_unique_roles':len(rows),'direct_ADC_channels':len(adc),
    'uncompressed_triple_bytes':frame_bytes,
    'uncompressed_triple_MiB':frame_bytes/2**20,
    'CAN_500k_zero_overhead_lower_bound_s':frame_bytes*8/500e3,
    'bootstrap_0p2W_current_before_overhead_A':.2/.8/(4.75-.4),
    'ideal_discharge_Rmax_ohm_by_C_uF':decay,
    'limits':['DC corner allocations exclude ramps/injection/ground offsets',
              'Current-limit scaling is a screen, not full load/temperature/transient acceptance',
              'GPIO names/AFs are not a physical lead-to-symbol-to-pad acceptance',
              'RC screen excludes regulator delay, residual feed and component variation',
              'Camera stride, SD speed and CAN overhead remain to measure'],
}
(BASE/'schematic_start_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
