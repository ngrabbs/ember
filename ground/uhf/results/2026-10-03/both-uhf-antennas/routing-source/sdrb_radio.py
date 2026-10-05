# SPDX-License-Identifier: GPL-3.0-or-later
"""Native SDRB RFIC session. Importing performs no hardware access.

This is an internal MPM integration layer, not a streaming/discovery API.
The C++ factory calibrates the radio; callers must establish board ownership
and a terminated bench setup before invoking it on hardware.
"""
from pathlib import Path
import math
from threading import RLock
from time import sleep

RX_BAND_EDGES = (1.2e9, 2.6e9)  # Same policy as sdrb_defaults.hpp; not filter specifications.


def resolve_radio_spi(root=Path("/")):
    """Find the actual CS0 endpoint on PS SPI0, independent of Linux bus number."""
    root = Path(root)
    matches = []
    for device in (root / "sys/bus/spi/devices").glob("spi*.*"):
        if "e0006000.spi" not in device.resolve().parts:
            continue
        node = device / "of_node"
        if not (node / "compatible").exists():
            continue
        if b"amsat,sdrb-ad9361" not in (node / "compatible").read_bytes().split(b"\0"):
            continue
        if (node / "reg").read_bytes() != b"\0\0\0\0" or not device.name.endswith(".0"):
            raise RuntimeError("SDRB radio must be CS0 on physical PS SPI0")
        frequency = int.from_bytes((node / "spi-max-frequency").read_bytes(), "big")
        if frequency != 1000000:
            raise RuntimeError("SDRB native SPI client requires the 1 MHz device-tree contract")
        endpoint = root / "dev" / ("spidev" + device.name[3:])
        if not endpoint.exists():
            raise RuntimeError("SDRB spidev endpoint is missing")
        matches.append(str(endpoint))
    if len(matches) != 1:
        raise RuntimeError("Expected one SDRB AD9361 endpoint on e0006000.spi CS0")
    return matches[0]


def native_manager_factory(endpoint):
    from usrp_mpm import lib
    return lib.dboards.sdrb_db_manager(endpoint)


def _frequency(value):
    value = float(value)
    if not math.isfinite(value) or not 70e6 <= value <= 6e9:
        raise ValueError("RF frequency must be finite and within 70 MHz to 6 GHz")
    return value


def _rate(value):
    value = float(value)
    if not math.isfinite(value) or not 220e3 <= value <= 61.44e6:
        raise ValueError("Master clock rate must be finite and within 220 kHz to 61.44 MHz")
    return value


class NativeRadioSession:
    """Own a GPIO controller and native RFIC, closing both on operation failure.

    These methods refer to physical RX1/RX2/TX1/TX2, without the digital
    frontend swap that the later UHD host adaptation must reconcile.
    """
    def __init__(self, control, endpoint, master_clock_rate=18.432e6,
                 factory=native_manager_factory, delay=sleep):
        self._control = control
        self._lock = RLock()
        self._closed = False
        self._manager = self._rfic = None
        self.master_clock_rate = None
        try:
            rate = _rate(master_clock_rate)
            self._control.hold_reset()
            for route in ("rx1", "rx2", "tx"):
                self._control.set_route(route, 0)
            delay(0.010)
            self._control.release_reset()  # BoardControl enforces prior FPGA compatibility.
            delay(0.010)
            self._manager = factory(endpoint)
            self._rfic = self._manager.get_radio_ctrl()
            self._rfic.set_timing_mode("1R1T")  # Native driver rejects 2R2T timing for CMOS.
            self.master_clock_rate = self._rfic.set_clock_rate(rate)
            self._rfic.set_gain("TX1", 0.0)
            self._rfic.set_gain("TX2", 0.0)
            self._rfic.set_active_chains(False, False, False, False)
        except Exception as original:
            self._fail(original)

    def _require_open(self):
        if self._closed:
            raise RuntimeError("Native SDRB radio session is closed")

    def _fail(self, original):
        try:
            self.close()
        except Exception as cleanup:
            raise ExceptionGroup("SDRB radio operation and cleanup failed", [original, cleanup])
        raise original

    def tune_rx(self, frequency):
        frequency = _frequency(frequency)
        with self._lock:
            self._require_open()
            try:
                self._control.set_route("rx1", 0)
                self._control.set_route("rx2", 0)
                actual = self._rfic.tune("RX1", frequency)  # RX LO/input selection is shared.
                state = 3 if frequency < RX_BAND_EDGES[0] else 1 if frequency < RX_BAND_EDGES[1] else 2
                self._control.set_route("rx1", state)
                self._control.set_route("rx2", state)
                return actual
            except Exception as original:
                self._fail(original)

    def tune_tx(self, frequency):
        frequency = _frequency(frequency)
        with self._lock:
            self._require_open()
            try:
                # Direct TX A connector bypasses the shared antenna route; leave that route off.
                self._control.set_route("tx", 0)
                return self._rfic.tune("TX1", frequency)
            except Exception as original:
                self._fail(original)

    def _execute(self, method, *args):
        """Serialize a validated adapter operation and reset on native failures."""
        with self._lock:
            self._require_open()
            try:
                result = getattr(self._rfic, method)(*args)
                if method == "set_clock_rate":
                    self.master_clock_rate = result
                return result
            except Exception as original:
                self._fail(original)

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
            # Hardware reset first, without waiting for another SPI operation to complete.
            # BoardControl attempts low values, input directions, and release independently.
            try:
                self._control.close()
            finally:
                self._rfic = self._manager = None
