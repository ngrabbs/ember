# Isolated BMS supply: development schematic integration

2026-10-24. Carry the permitted essential+3V3 source forward for **development schematic integration**, with TPS2553DBVR-1/UCC33020RAQR/LT3014IS5#TRPBF. This is authorization within the operator's existing complete-EPS scope to draw and verify the candidate, not electrical/PCB/hardware release. It supersedes the earlier blanket native hold in the read-only readiness note only for this bounded development drawing. All physical qualification gates remain. The goal continuation explicitly permits temporary rough edges while progressing the complete EPS; retaining the known gauging-error path indefinitely would not implement the intended design.

The [seven switch-model cases](../verification/bms/tps2553_transient/results.json) now exercise nominal ramp, current limit, timer/latch and reset behavior with imposed converter loads. They support the115k setting and larger primary bank as a development candidate; they do not supply a self-consistent UCC startup or worst-case source/fault model. Keep the protected+5V alternative unselected: it has voltage headroom but makes pack telemetry dependent on the recovery rail. Essential3V3 preserves that independence. The [endpoint/reset handoff](../verification/bms/isolated_supply_readiness/README.md) remains the exact pre-build boundary authority.

## One complete new functional sheet

Target `hardware/eps/rev_b/eps_rev_b.kicad_pro` / root `eps_rev_b.kicad_sch`. Add one unique landscape ANSI B child `bms_isolated_power.kicad_sch`. Preserve all ten existing sheets,243 physical component UUIDs, unrelated metadata and interfaces. No real PCB synchronization. Sole native mutation owner is the existing schematic-build agent; every native/library/project-setting write uses Konnect.

| Ref | Exact component/value | Connection intent |
|---|---|---|
| U900 | TPS2553DBVR-1, approved project symbol/footprint |1IN essential+3V3;2GND systemGND;3EN local control node;4FAULT local diagnostic node;5ILIM toR900;6OUT toR901 |
| U901 | UCC33020RAQR, approved project symbol/footprint |2VINP `3V3_BMS_PRI`;3/4/5/6 systemGND;1EN/FLT viaR904;8VCC `5V0_BMS_ISO`;7SEL to8;9/10/11/12 RAWground |
| U902 | LT3014IS5#TRPBF, accepted stock symbol/footprint |1IN and3SHDN `5V0_BMS_ISO`;2GND RAW;5OUT `3V3_BMS_ISO`;4ADJ divider |
| R900 |115k,TNPW0603115KBEEA |TPS ILIM toGND; conditional202.81–266.30mA range |
| R901 |1ohm,CRCW12061R00FKEAHP |TPS OUT toprimary reservoir;1%,100ppm/K,0.75W P70 |
| R902/R903 |22k/1k,TNPW060322K0BEEA/TNPW06031K00BEEA |22k essential+3V3 toTPS EN;1k fromEN toPD3 command |
| R904 |20k,TNPW060320K0BEEA |primary rail toUCC EN/FLT; not an MCU net |
| R905/R906 |16.9k/10k,TNPW060316K9BEEA/TNPW060310K0BEEA |LDO OUT–ADJ–RAW divider |
| R907/R908 |10k/1k,TNPW060310K0BEEA/TNPW06031K00BEEA |FAULT pull-up toessential+3V3;1k FAULT toPD0 |
| R909 |4.7k,TNPW06034K70BEEA |isolated5V discharge toRAW |
| R910 |3.9k,TNPW06033K90BEEA |primary reservoir discharge tosystemGND |
| R911 |4.7k,TNPW06034K70BEEA |LDO output discharge toRAW, parallel tofeedback divider |
| C900/C916 |100nF each,GRM188R72A104KA35D |TPS input local bypasses tosystemGND; nominal200nF total |
| C901–C908 |8×10uF,CGA5L1X7R1H106K160AC |primary reservoir tosystemGND |
| C909 |15nF,CGA3E2X7R1H153K080AA |UCC primary HF bypass tosystemGND |
| C910–C912 |3×10uF,CGA5L1X7R1H106K160AC |isolated5V reservoir toRAW |
| C913 |15nF,CGA3E2X7R1H153K080AA |UCC secondary HF bypass toRAW |
| C914 |100nF,GRM188R72A104KA35D |LDO local input bypass toRAW |
| C915 |10uF,CGA5L1X7R1H106K160AC |LDO output reservoir toRAW |

TNPW0603 parts use the previously screened0.1%/25ppm/K/0.110W general P70 family; verify order codes and metadata from manufacturer rules before placement. Bulk caps10uF/10%/50V/X7R/1206;15nF bypasses10%/50V/X7R/0603;Murata100nF10%/100V/X7R/0603. The capacitor bounds remain conditional reference-curve/temperature/aging screens. This inventory adds32 physical parts; confirm actual counts rather than hard-coding acceptance from this estimate.

Only existing U201.8/R218.1/R219.1/C210.1 move from+3V3 to`3V3_BMS_ISO`. All raw returns and signal names remain exact. New upward power symbols carry exact rail Values; use existing accepted downward raw/system ground symbols. Never bridge returns. Use actual local wires and exposed pin stubs, meaningful primary/module/LDO grouping and bright-green custom review callouts. Add a legitimate source flag afterR901 only if ERC needs the driven passive-filter node. Exact POWER-class assignments cover all new rails; control/feedback classes follow existing project intent. Verify full hierarchy and every rendered sheet separately.

## MCU and recovery semantics

Allocate PD3 physical29 to global `EPS_BMS_PRI_EN`, open drain: released/high enables; LOW disables TPS. Allocate PD0 physical26 to global `EPS_BMS_PRI_FAULT_N`, diagnostic input only. Local switch-side signal segments remain local names. Both globals cross between Controller and new child. No existing interface name changes. Preserve VDDIO2 onessential+3V3.

At startup mark BMS telemetry invalid, enable SYSCFG and strobe the relevant UCPD dead-battery disables before reading affected inputs. Preload PD3 HIGH before selecting open-drain output/no internal pull. PD0 input/no internal pull; mask its reset-time false fault. Pulled-high PD3 also affects PD2 reset behavior; interlock authority remains independent hardware. These are design/firmware requirements, not an implemented firmware claim.

A LOW hold of2s is a **commanded latch-clear/discharge attempt**. It is not a guaranteed fully discharged UCC reset. Release, allow supply settling and bus recovery, then require fresh BMS identity/configuration/valid telemetry before using readings. If recovery fails, retain invalid/fault status and stop autonomous repeated retries pending a qualified policy or explicit supervisor request. A microcontroller reset releases the external default-on network; do not claim the LOW hold persists through reset. Hardware TPS/BQ protection operates independently of telemetry and firmware. Neither IHU nor EPS commands bypass RBF, source or pack protection.

Normal added bleed current is approximately0.85mA primary,1.11mA isolated5V and0.73mA at3V3 output at the screened upper voltages. The previous12mA LDO output allocation still covers the computed ISO/pullup/divider/bleeder static load, but the intermediate allocation becomes at least14.11mA including1mA reserved LDO ground current and the5V bleeder. Dynamic/startup currents remain separate. Update the exact screen and TI-calculator inputs with actual assembled capacitor/load values before electrical acceptance.

## Acceptance still open

No worst-case initial TPS short response is guaranteed by the nominal model; no shared3V3/healthy CAN survival claim follows. Retain source-loop/weak-source/UVLO, essential OV barrier, full coupled UCC/LDO startup/prebias/repeated faults, off-state all-path feeds, effective capacitance/ESR, resistor pulse/thermal, EMC, gauging calibration and physical fit gates. The UCC encrypted SIMPLIS model cannot run in the installed LTspice environment. A real UCC simulation/measurement remains necessary for those model gaps. Do not call native connectivity or a successful latch model hardware/flight acceptance.
