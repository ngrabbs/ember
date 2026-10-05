#!/usr/bin/env python3
"""DC threshold corners and executable power-control intent; not circuit timing.

Run with Python 3, standard library only. Values come from TLV6710 Rev. B
section 7.5. Resistor tolerance is a screening assumption, not a selected BOM.
The ideal digital model deliberately excludes analog delays, metastability,
rail decay, component faults and Jetson firmware behavior.
"""

from dataclasses import dataclass, replace
from itertools import product
import json


def divider_corners(top, bottom, thresholds, tolerance=0.001, bias=25e-9):
    # Positive bias flows into the sense pin: Vin=Vth*(1+Rt/Rb)+Ibias*Rt.
    values = [
        v * (1 + rt / rb) + i * rt
        for v, rt, rb, i in product(
            thresholds,
            (top * (1 - tolerance), top * (1 + tolerance)),
            (bottom * (1 - tolerance), bottom * (1 + tolerance)),
            (-bias, bias),
        )
    ]
    return [min(values), max(values)]


@dataclass(frozen=True)
class Inputs:
    aon_ok: bool = True
    source_ok: bool = True
    bench_mode: bool = False  # Latched boot mode, not a live jumper signal.
    ihu_payload_en: bool = True
    main_request: bool = False
    window_ok: bool = False
    shutdown_n: bool = True  # AFTER the required 5 V-to-AON translation.
    arm: bool = False
    sys_reset_n: bool = False
    ready: bool = False
    capture_request: bool = False
    stop_request: bool = False


class RunLatch:
    def __init__(self):
        self.q = False
        self.previous_arm = False

    def step(self, i):
        permission = i.bench_mode or i.ihu_payload_en
        main_en = i.aon_ok and i.source_ok and permission and i.main_request
        # No dependence of main_en on its own not-yet-powered window monitor.
        clear_n = main_en and i.window_ok and i.shutdown_n
        fresh_arm = i.arm and not self.previous_arm
        if not clear_n:
            self.q = False
        elif fresh_arm:
            self.q = True
        self.previous_arm = i.arm
        io_enable = self.q and i.sys_reset_n
        trigger_enable = io_enable and i.ready and not i.stop_request
        return {
            "main_en": main_en,
            "power_en": self.q,
            "module_io_enable": io_enable,
            "trigger_enable": trigger_enable,
            "capture": trigger_enable and i.capture_request,
            "linux_stop_request": self.q and i.stop_request,
        }


def check_control_contract():
    checked = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checked.append(name)

    latch = RunLatch()
    boot = Inputs(main_request=True)
    o = latch.step(boot)
    check("buck starts while 5 V window is not yet valid", o["main_en"] and not o["power_en"])
    good = replace(boot, window_ok=True)
    check("voltage recovery alone cannot boot module", not latch.step(good)["power_en"])
    armed = replace(good, arm=True)
    o = latch.step(armed)
    check("fresh arm edge powers module but holds I/O and capture off", o["power_en"] and not o["module_io_enable"] and not o["capture"])
    running = replace(armed, sys_reset_n=True, ready=True, capture_request=True)
    check("ready module accepts captures", latch.step(running)["capture"])
    stopping = replace(running, stop_request=True)
    o = latch.step(stopping)
    check("normal stop inhibits capture while retaining shutdown power", not o["capture"] and o["linux_stop_request"] and o["main_en"] and o["power_en"])
    o = latch.step(replace(stopping, shutdown_n=False))
    check("module shutdown clears run latch with MCU arm stuck high", not o["power_en"])
    check("module releasing shutdown cannot reboot with stale arm", not latch.step(running)["power_en"])
    latch.step(replace(running, arm=False))
    check("deliberate new arm edge can rearm", latch.step(running)["power_en"])

    for field in ("window_ok", "source_ok", "aon_ok", "ihu_payload_en", "main_request"):
        fault_latch = RunLatch()
        fault_latch.step(replace(running, arm=False))
        fault_latch.step(running)
        o = fault_latch.step(replace(running, **{field: False}))
        check(f"{field} loss clears run latch", not o["power_en"] and not o["capture"])
        check(f"{field} recovery cannot rearm a stale arm", not fault_latch.step(running)["power_en"])

    bench_latch = RunLatch()
    bench = replace(running, bench_mode=True, ihu_payload_en=False)
    check("bench mode permits standalone boot", bench_latch.step(bench)["power_en"])
    o = bench_latch.step(replace(bench, sys_reset_n=False))
    check("module reset disables carrier I/O without carrier driving reset", o["power_en"] and not o["module_io_enable"] and not o["capture"])

    # Cartesian exploration of all steady input combinations. Edge-dependent
    # rearm cases above supplement this invariant check.
    fields = list(Inputs.__dataclass_fields__)
    for bits in product((False, True), repeat=len(fields)):
        i = Inputs(**dict(zip(fields, bits)))
        machine = RunLatch()
        machine.q = True
        o = machine.step(i)
        if o["power_en"]:
            assert o["main_en"] and i.window_ok and i.shutdown_n
        if o["capture"]:
            assert o["power_en"] and i.sys_reset_n and i.ready and not i.stop_request
        if not (i.aon_ok and i.source_ok and (i.bench_mode or i.ihu_payload_en)):
            assert not o["main_en"] and not o["power_en"]
    return {"scenarios_passed": checked, "steady_combinations_checked": 2 ** len(fields)}


def main():
    windows = {
        "UV_falling_fault": divider_corners(110000, 10000, (0.397, 0.403)),
        "UV_rising_recovery": divider_corners(110000, 10000, (0.400, 0.413)),
        "OV_rising_fault": divider_corners(119000, 10000, (0.397, 0.403)),
        "OV_falling_recovery": divider_corners(119000, 10000, (0.387, 0.400)),
    }
    assert windows["UV_falling_fault"][0] > 4.75
    assert windows["OV_rising_fault"][1] < 5.25
    report = {
        "status": "DC screening and ideal logic only; not accepted hardware",
        "TLV6710_volts": windows,
        "sense_at_15_75V_max_divider_ratio": 15.75 * 10010 / (109890 + 10010),
        "control": check_control_contract(),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
