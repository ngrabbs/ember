"""Conditional CAN branch static logic/reset screen; no transient/PVT acceptance."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
vmin, vmax = 3.232799137558028, 3.324392156862745
tol = .001 + 25e-6*65
r1max, r1min = 1000*(1+tol), 1000*(1-tol)
r10max, r10min = 10000*(1+tol), 10000*(1-tol)
r47max, r47min = 47000*(1+tol), 47000*(1-tol)
r100min = 100000*(1-tol)
gpio_low = .4
gpio_high = vmin-.4
gpio_leak = 5e-6
# TI's Schmitt thresholds have discrete supply test points. Bracket as a
# development guard only, rather than claiming an interpolated guarantee.
vt_high_guard, vt_low_guard = 2.74, .84
stb_reset_high = vmin-r10max*(gpio_leak+5e-6+1e-6)
en_high = ((vmin-.1)/r1max-1e-6)/(1/r1max+1/r100min)
en_low = .1+1e-6*r1max
tx_low = gpio_low+200e-6*r1max
stb_low = gpio_low+20e-6*r1max
tx_high = gpio_high-2.5e-6*r1max
rx_high = .8*3.0-gpio_leak*r1max
rx_low = .2*vmax+(vmax/r47min+gpio_leak)*r1max
rx_off = vmin-(gpio_leak+1e-6)*r47max
normal_drop_90mA = .090*(.135+1*(1+.01+100e-6*65))
rx_correlated_static_margin = .8*(vmin-normal_drop_90mA)-gpio_leak*r1max-.7*vmin
checks = {
    'standby_reset_high_above_schmitt_guard': stb_reset_high > vt_high_guard,
    'standby_asserted_low_below_schmitt_guard': gpio_low < vt_low_guard,
    'enable_high_above_TPS_threshold_max': en_high > 1.1,
    'enable_low_below_TPS_threshold_min': en_low < .66,
    'TXD_low_below_0p3_min_branch': tx_low < .3*3.0,
    'STB_low_below_0p3_min_branch': stb_low < .3*3.0,
    'TXD_high_above_0p7_max_branch': tx_high > .7*vmax,
    'RXD_high_above_MCU_0p7_max_supply': rx_high > .7*vmax,
    'RXD_low_below_MCU_0p3_min_supply': rx_low < .3*vmin,
    'RXD_unpowered_high_above_MCU_0p7_max_supply': rx_off > .7*vmax,
}
assert all(checks.values()), checks
result = {'status':'CONDITIONAL_DEVELOPMENT_STATIC_SCREEN_NOT_PVT_OR_FAULT_QUALIFICATION',
          'assumptions': {'essential_static_supply_V':[vmin,vmax],
                          'required_normal_branch_floor_V':3.0,
                          'GPIO_VOL_allocation_V':gpio_low,
                          'GPIO_VOH_allocation_V':gpio_high,
                          'configured_GPIO_abs_leak_guard_A':gpio_leak,
                          'resistor_initial_plus_TCR_fraction':tol,
                          'TI_Schmitt_bracketing_guard_VTplus_max_V':vt_high_guard,
                          'TI_Schmitt_bracketing_guard_VTminus_min_V':vt_low_guard,
                          'guard_is_not_continuous_supply_guarantee':True,
                          'TPS_EN_leak_guard_A':1e-6,
                          'TI_inverter_100uA_VOH_drop_VOL_V':.1,
                          'TCAN_TXD_low_input_current_A':200e-6,
                          'TCAN_STB_low_input_current_A':20e-6,
                          'TCAN_poweroff_logic_leak_each_A_at_zero_supplies':1e-6},
          'results_V':{'STB_floating_reset_min':stb_reset_high,'EN_high_min':en_high,'EN_low_max':en_low,
                       'TXD_low_max':tx_low,'STB_low_max':stb_low,'TXD_high_min':tx_high,
                       'RXD_high_min':rx_high,'RXD_low_max':rx_low,'RXD_off_high_min':rx_off,
                       'RXD_high_margin':rx_high-.7*vmax,
                       'RXD_correlated_static_margin_at90mA':rx_correlated_static_margin},
          'GPIO_sink_current_A':{'TXD_low_max':vmax/r10min+200e-6,
                                 'STB_low_max':vmax/r10min+20e-6+5e-6},
          'EN_output_load_max_A':vmax/r100min+1e-6,
          'logic_1k_ground_short_current_A':vmax/r1min,
          'logic_1k_ground_short_power_W':vmax**2/r1min,
          'checks':checks,
          'limits':['Schmitt threshold guard brackets discrete test points; continuous-supply/PVT confirmation remains open.',
                    'GPIO drive/leak allocations use the selected powered/configured MCU; not unknown or unpowered states.',
                    'RXD high margin is small; actual edge timing, loading, temperature and layout remain open.',
                    'Correlated static RXD margin uses common essential supply and90mA*(.135ohm TPS+1%/TCR1ohm-series bound); it does not cover transient droop/ripple.',
                    'TCAN Ioff at both supplies zero does not prove all partial-power or destructive bus-to-logic faults.',
                    '20ms disable/enable waits are firmware planning values, not guaranteed rail discharge or restart.',
                    'No new GPIO allocation; FAULT is a test diagnostic only, unavailable to MCU directly.']}
(HERE/'calculations.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['results_V'],indent=2))
