"""Reproduce provisional EPS sizing cases; no qualified ratings are implied."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def buck_ripple(vin, vout, inductance, frequency):
    return vout * (vin - vout) / (vin * inductance * frequency)


def generate():
    buck = []
    for label, inductance, frequency in [
        ('nominal', 5.6e-6, 400e3),
        ('initial_tolerance_and_frequency', 5.6e-6 * .8, 360e3),
        ('additional_magnetic_and_dither_sensitivity', 5.6e-6 * .8 * .7, 360e3 * .915),
    ]:
        ripple = buck_ripple(35, 3.3, inductance, frequency)
        buck.append({'case': label, 'effective_L_H': inductance, 'frequency_Hz': frequency,
                     'ripple_A_pp': ripple, 'peak_at_2A_A': 2 + ripple / 2,
                     'peak_at_3p5A_A': 3.5 + ripple / 2,
                     'ideal_load_ceiling_from_4p2A_peak_A': 4.2 - ripple / 2})
    bb = []
    for label, inductance, frequency in [('nominal', 10e-6, 400e3),
                                        ('sensitivity', 10e-6 * .8 * .7, 300e3)]:
        for vin in [4.5, 5, 8.4, 35]:
            # Equal-input/output operation uses a buck-boost transition; no zero-ripple claim.
            if vin == 5:
                bb.append({'case': label, 'input_V': vin, 'mode': 'transition: model required'})
                continue
            mode = 'boost' if vin < 5 else 'buck'
            ripple = vin * (1-vin/5)/(inductance*frequency) if mode == 'boost' else buck_ripple(vin, 5, inductance, frequency)
            avg = 5*2/(.9*vin) if mode == 'boost' else 2
            bb.append({'case': label, 'input_V': vin, 'mode': mode,
                       'effective_L_H': inductance, 'frequency_Hz': frequency,
                       'ripple_A_pp': ripple, 'estimated_average_inductor_A': avg,
                       'estimated_peak_inductor_A': avg+ripple/2})
    system = []
    for label, i33, i5 in [('illustrative_idle', .05, .1), ('illustrative_recovery', .2, .5), ('both_rails_2A', 2, 2)]:
        power = 3.3*i33 + 5*i5
        system.append({'case': label, 'I3V3_A': i33, 'I5V_A': i5, 'output_W': power,
                       'estimated_input_A_at_4p5V_90pct': power/(4.5*.9),
                       'estimated_input_A_at_7p27V_90pct': power/(7.27*.9)})
    cap = [{'step_A': step, 'unserved_duration_us': us, 'allowed_droop_V': .25,
            'ideal_capacitance_uF': step*us/.25}
           for step in [.4, 1.9] for us in [10,25,100]]
    boxes = [
        {'id':'stack','x':3,'y':12,'w':10,'h':66,'lines':['Stack H1/H2','access']},
        {'id':'solar','x':29,'y':3,'w':35,'h':7,'lines':['Solar connectors']},
        {'id':'pack','x':77,'y':3,'w':16,'h':10,'lines':['XT30','access']},
        {'id':'can','x':15,'y':14,'w':12,'h':28,'lines':['CAN A/B','336 mm²']},
        {'id':'charger','x':29,'y':14,'w':30,'h':23,'lines':['Charger / PowerPath','690 mm²']},
        {'id':'bms','x':66,'y':17,'w':25,'h':22,'lines':['Pack protection','550 mm²']},
        {'id':'mcu','x':15,'y':44,'w':20,'h':20,'lines':['STM32 core','400 mm²']},
        {'id':'buck','x':37,'y':40,'w':24,'h':18,'lines':['3.3 V buck','432 mm²']},
        {'id':'isolation','x':65,'y':42,'w':25,'h':18,'lines':['RBF + solar OV','450 mm² / open']},
        {'id':'rbf','x':92,'y':41,'w':3,'h':20,'lines':['RBF']},
        {'id':'sense','x':14,'y':68,'w':22,'h':12,'lines':['Sense harness','264 mm²']},
        {'id':'bb','x':37,'y':63,'w':32,'h':24,'lines':['5 V buck-boost','768 mm²']},
        {'id':'loads','x':71,'y':64,'w':22,'h':16,'lines':['Managed loads','352 mm²']},
    ]
    for box in boxes:
        assert box['x'] >= 0 and box['y'] >= 0 and box['x']+box['w'] <=96 and box['y']+box['h'] <=90
    for i,a in enumerate(boxes):
        for b in boxes[i+1:]:
            assert not (a['x']<b['x']+b['w'] and b['x']<a['x']+a['w'] and a['y']<b['y']+b['h'] and b['y']<a['y']+a['h']), (a['id'],b['id'])
    return {'date':'2026-10-04','status':'INCOMPLETE: sizing cases and planning rectangles; no accepted circuit/layout',
            'operator_top_standoff_mm':16,'clearance_condition':'Nominal standoff; subtract upper-board underside protrusions and tolerance. Board reference faces not established.',
            'assumptions':{'minimum_converter_input_sensitivity_V':4.5,'pack_floor_provisional_V':5,
                           'path_drop_allowance_sensitivity_V':.5,'efficiency_assumed':.9,
                           'magnetic_inductance_multiplier_sensitivity':.7,
                           'load_current_not_measured':True},
            'buck_cases':buck, 'buck_boost_2A_cases':bb,
            'peak_sense_10mOhm_1pct':{'minimum_trip_A':.0385/.0101,'maximum_trip_A':.0585/.0099,
                                    'nominal_5A_shunt_loss_W':25*.01},
            'system_cases':system, 'five_volt_load_step_capacitance':cap,
            'four_fet_gate_charge_budget':{'Qg_max_reference_C':7.3e-9,'Vgs_reference_V':4.5,'frequency_Hz':400e3,
                                         'charge_current_A':4*7.3e-9*400e3,'gate_drive_W':4*7.3e-9*4.5*400e3,
                                         'linear_bias_loss_from_35V_W':(35-4.5)*4*7.3e-9*400e3,
                                         'all_four_switching_scenario_not_actual_mode_power':True},
            'floorplan':{'nominal_board_mm':[96,90],'boxes':boxes,
                         'represented_area_mm2':sum(b['w']*b['h'] for b in boxes),
                         'converter_reservation_mm2':432+768,'previous_converter_reservation_mm2':2*24*12,
                         'additional_converter_reservation_mm2':432+768-2*24*12,
                         'checks':'rectangles within nominal board; no rectangle overlaps; not a courtyard/DRC or mechanical test'}}


def svg(data):
    from html import escape
    scale=9; ox=65; oy=110
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="1080" viewBox="0 0 1100 1080">',
         '<rect width="1100" height="1080" fill="#f8fafc"/>','<g font-family="Arial, sans-serif">',
         '<text x="65" y="45" font-size="25" fill="#162434">EPS Rev B conversion-stage reservations</text>',
         '<text x="65" y="75" font-size="15" fill="#536375">Planning only • 96 × 90 mm nominal • revised 2026-10-04</text>',
         '<rect x="65" y="110" width="864" height="810" rx="18" fill="white" stroke="#526477" stroke-width="2"/>']
    for b in data['floorplan']['boxes']:
        x=ox+b['x']*scale;y=oy+b['y']*scale;w=b['w']*scale;h=b['h']*scale
        color='#dbeafe' if b['id'] in ['mcu','can'] else '#fef3c7' if b['id'] in ['buck','bb','isolation','loads'] else '#d1fae5' if b['id'] in ['bms','sense'] else '#e2e8f0'
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{color}" stroke="#536375"/>')
        if b['id']=='rbf':
            out.append(f'<text x="{x+w/2}" y="{y+h/2}" text-anchor="middle" font-size="13" transform="rotate(-90 {x+w/2} {y+h/2})">RBF side access</text>')
        else:
            for i,line in enumerate(b['lines']):
                out.append(f'<text x="{x+w/2}" y="{y+h/2+(i-(len(b["lines"])-1)/2)*19+5}" text-anchor="middle" font-size="14" fill="#182b3c">{escape(line)}</text>')
    out += ['<text x="65" y="953" font-size="16" fill="#182b3c">16 mm top standoff reported; upper-board protrusions and tolerances still require checking.</text>',
            '<text x="65" y="982" font-size="15" fill="#536375">Converter allowance: 1200 mm² (previously 576 mm²). Rectangles are not placed components.</text>',
            '<text x="65" y="1011" font-size="15" fill="#536375">Mounting holes, holder, harness bends, heat paths and exact board outline remain unverified.</text>',
            '</g></svg>']
    return '\n'.join(out)+'\n'


if __name__ == '__main__':
    data=generate()
    (ROOT/'evidence/2026-10-04_power_stage_sizing.json').write_text(json.dumps(data,indent=2)+'\n')
    (ROOT.parent/'design/rev_b_floorplan.svg').write_text(svg(data))
    print('Sizing cases and nominal floorplan regenerated; rectangle checks passed.')
