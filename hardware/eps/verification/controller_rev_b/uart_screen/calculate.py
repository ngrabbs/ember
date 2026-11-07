"""UART static loading/leakage screen, not waveform or whole-EPS acceptance."""
from pathlib import Path
import json
VLO,VHI=3.23280,3.32439  # Inherited static essential-rail screen, not startup.
ERR=.001+25e-6*65      # 0.1%, 25 ppm/K, conservative 65 K excursion.
limits=lambda r:(r*(1-ERR),r*(1+ERR))
bleed=limits(68000);bias=limits(100000);series_rx=limits(47);series_tx=limits(330)
off=2e-6;inp=1e-6;mcu_leak=5e-6;adapter_leak=10e-6
out_load=VHI/bleed[0]
rx_high=(2.4-inp*series_rx[1])/(1+series_rx[1]/bias[0])
rx_low=(.4+inp*series_rx[1])/(1+series_rx[1]/bias[1])
tx_high=VLO-.1-adapter_leak*series_tx[1]
tx_low=.1+adapter_leak*series_tx[1]
result={
 'status':'CONDITIONAL_STATIC_INTERFACE_SCREEN_ONLY',
 'resistor_fractional_error':ERR,'supply_V':[VLO,VHI],
 'selected_buffer':'Nexperia 74LVC2G34GW,125',
 'bleed_ohm':bleed,'bias_ohm':bias,'RX_series_ohm':series_rx,'TX_series_ohm':series_tx,
 'output_high_static_load_A':{'MCU_RX':out_load+mcu_leak,'connector_TX':out_load+adapter_leak},
 '100uA_output_characterization_applies':out_load+max(mcu_leak,adapter_leak)<100e-6,
 'conditional_off_output_voltage_budget_V':off*bleed[1],
 'conditional_UART_two_terminal_off_rail_budget_V':2*off*bleed[1],
 'off_current_condition':'Ioff is specified at VCC=0 V only. Applying it at a calculated nonzero rail voltage is a screening assumption; undefined-supply and transient behavior require separate verification.',
 'static_margins_V':{'MCU_TX_high_to_buffer':VLO-.4-2.0,'MCU_TX_low_to_buffer':.8-.4,
  'adapter_RX_high_to_buffer':rx_high-2,'adapter_RX_low_to_buffer':.8-rx_low,
  'buffer_high_to_MCU_RX':VLO-.1-.7*VHI,'buffer_low_to_MCU_RX':.3*VLO-.1,
  'buffer_high_to_adapter':tx_high-2.0,'buffer_low_to_adapter':.8-tx_low},
 'connector_TX_high_low_V':[tx_high,tx_low],
 'bias_worst_low_MCU_TX_load_A':VHI/bias[0]+inp,
 'static_supply_allocation_A':1.2e-3,
 'allocation_basis':'Two 500uA intermediate-input additional-current allowances, 4uA ICC, all three 68k bleeds, one 100k pull-up and 2uA input leakage; rounded upward. Not switching current.',
 'maximum_buffer_input_slew_ns_per_V':10,
 'development_baud':115200,'adapter_output_requirements_V':{'VOH_min':2.4,'VOL_max':.4},
 'adapter_static_input_load_upper_A':adapter_leak,'connector_load_capacitance_budget_F':50e-12,
 'open_gates':['actual buffer-input slew and UART sampling/clock budget','brownout and stored-charge transients','connector ESD/abuse and mechanical clearance','combined external-interface back-power audit','hardware temperature and flight qualification']}
assert result['100uA_output_characterization_applies']
assert all(x>0 for x in result['static_margins_V'].values())
assert result['conditional_UART_two_terminal_off_rail_budget_V']<.3
Path(__file__).with_name('calculated.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
