"""Conditional GPIO and passive-discharge screen; no native circuit mutation."""
from pathlib import Path
import json, math

HERE = Path(__file__).resolve().parent

def main():
    caps = json.loads((HERE / 'capacitors.json').read_text())['banks']
    excursion = .001 + 25e-6 * 65
    lo = lambda r: r * (1 - excursion)
    hi = lambda r: r * (1 + excursion)
    vmin, vmax = 3.232799, 3.3244
    gpio_leak, en_leak, fault_leak = 5e-6, .5e-6, 1e-6
    gpio_vol, fault_vol = .4, .18
    # Open-drain low: pullup from source to EN, series resistor EN to GPIO.
    def en_low(pullup):
        rp, rs = lo(pullup), hi(1000)
        return gpio_vol + (vmax-gpio_vol)*rs/(rp+rs) + en_leak*rp*rs/(rp+rs)
    gpio = {
        'planning_gpio_leakage_A': gpio_leak,
        'EN_pullup_ohm': 22000,
        'EN_series_ohm': 1000,
        'EN_low_with10k_pullup_V': en_low(10000),
        'EN_low_with22k_pullup_V': en_low(22000),
        'TPS_EN_VIL_max_V': .66,
        'EN_high_min_V': vmin-hi(22000)*(gpio_leak+en_leak),
        'TPS_EN_VIH_min_V': 1.1,
        'GPIO_low_sink_max_A': (vmax-gpio_vol)/(lo(22000)+lo(1000))+en_leak,
        'FAULT_pullup_ohm': 10000,
        'FAULT_series_ohm': 1000,
        'FAULT_input_high_min_V': vmin-hi(10000)*(gpio_leak+fault_leak)-hi(1000)*gpio_leak,
        'MCU_VIH_conservative_max_V': .7*vmax,
        'FAULT_input_low_max_V': fault_vol+hi(1000)*gpio_leak,
        'MCU_VIL_conservative_min_V': .3*vmin,
        'FAULT_sink_max_A': vmax/lo(10000)+gpio_leak,
    }
    assert gpio['EN_low_with10k_pullup_V'] > .66
    assert gpio['EN_low_with22k_pullup_V'] < .66
    assert gpio['EN_high_min_V'] > 1.1
    assert gpio['FAULT_input_high_min_V'] > .7*vmax
    assert gpio['FAULT_input_low_max_V'] < .3*vmin
    assert gpio['FAULT_sink_max_A'] < .001
    # Upper C sensitivities inherit reference-curve/tolerance/temp assumptions.
    # Add 15nF+100nF with +10%,+15% to each converter-side bank.
    extra = .115e-6*1.1*1.15
    bank_specs = [
        ('primary', 10000, vmax, caps['primary']['zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF']*1e-6+extra),
        ('isolated_5V', 4700, 5.2, caps['isolated_5V']['zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF']*1e-6+extra),
        ('LDO_output', 26900, 3.401, caps['LDO_output']['zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF']*1e-6),
        ('primary_3k9_candidate', 3900, vmax, caps['primary']['zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF']*1e-6+extra),
        ('LDO_output_with4k7_bleeder_candidate', 1/(1/26900+1/4700), 3.401, caps['LDO_output']['zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF']*1e-6),
    ]
    rows = []
    for name, r, initial, cap in bank_specs:
        # i_feed represents ALL external feed; ignoring extra load slows decay.
        for feed in [0, 1e-6, 10e-6, 50e-6, 100e-6]:
            resistance = hi(r)
            factor = math.exp(-2/(resistance*cap))
            final = initial*factor + feed*resistance*(1-factor)
            rows.append({'node':name, 'R_max_ohm':resistance, 'C_upper_scenario_F':cap,
                         'initial_V':initial, 'assumed_total_feed_A':feed,
                         'voltage_after2s_V':final, 'below0p5V_scenario':final<.5})
    result = {
        'status':'conditional planning screen; not an accepted MCU allocation, reset guarantee or integrated circuit',
        'gpio':gpio, 'off_hold_scenario_s':2, 'discharge_scenarios':rows,
        'cautions':[
            '5uA GPIO leakage is a planning guard; exact selected-pad modes/reset restrictions require primary-source reconciliation',
            'TPS IIN_off is input supply current, not a guaranteed forward OUT leakage bound',
            'TPS IREV is the opposite direction and its published maximum test is25C; do not substitute it for forward off leakage',
            '2s is a proposed firmware hold; no all-path maximum feed or fully coupled discharge guarantee exists',
            '0.5V is a screening target, not a datasheet reset threshold',
            'The LDO divider drains its output but does not prove the isolated5V node is discharged',
            'TPS turnoff max3ms has CL1uF/RL100ohm test conditions; do not apply it to this complete reservoir',
            'GPIO high/low checks assume valid common supply and configured modes; no power-off/backfeed acceptance follows',
        ],
    }
    (HERE/'reset_screen.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(gpio,indent=2))
    print('Discharge scenarios:',len(rows))

if __name__ == '__main__':
    main()
