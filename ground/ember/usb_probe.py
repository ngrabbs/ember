"""Direct Pico acceptance checks. Stop the USB bridge before running."""
import argparse
import secrets
import subprocess
import time
import serial
from codec import crc16, decode, encode
from framing import FrameReader, encode_frame


class Probe:
    def __init__(self, device):
        self.device = device
        self.epoch = secrets.randbelow(0x7fffffff) + 1
        self.sequence = 0
        self.port = serial.Serial(device, 115200, timeout=.05, write_timeout=.5, exclusive=True)
        self.reader = FrameReader()

    def read(self):
        return [decode(packet) for packet in self.reader.feed(self.port.read(4096))]

    def wire(self, name, transaction, payload):
        packet = encode(name, sequence=self.sequence, source=1, target=2,
                        transaction_epoch=self.epoch, transaction_id=transaction,
                        source_boot_id=self.epoch, uptime_ms=1, payload=payload)
        self.sequence = (self.sequence + 1) & 0x3fff
        return packet

    def transact(self, packet, transaction, timeout=3):
        self.port.write(encode_frame(packet))
        reports = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for report in self.read():
                h = report["header"]
                if (h["transaction_epoch"], h["transaction_id"]) != (self.epoch, transaction):
                    continue
                reports.append(report)
                if report["name"] == "COMMAND_RESPONSE" and report["payload"]["stage"] in (1, 2, 3):
                    return reports
        return reports

    def command(self, name, transaction, **payload):
        reports = self.transact(self.wire(name, transaction, payload), transaction)
        assert reports, "No hardware command result"
        return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--reset-test", action="store_true", help="Reboot this sole attached Pico using sudo picotool")
    args = parser.parse_args()
    p = Probe(args.device)
    try:
        first = p.command("SET_PARAMETER", 1, parameter_id=1, value=2000)
        assert [r["payload"]["stage"] for r in first] == [0, 2]
        boot = first[0]["header"]["source_boot_id"]
        assert first[-1]["payload"]["value"] == 2000
        repeat = p.command("SET_PARAMETER", 1, parameter_id=1, value=2000)
        assert [r["payload"] for r in first] == [r["payload"] for r in repeat]
        conflict = p.command("SET_PARAMETER", 1, parameter_id=1, value=3000)
        assert conflict[0]["payload"]["reason"] == 9
        status = p.command("REQUEST_STATUS", 2)[1]["payload"]
        assert status["telemetry_period_ms"] == 2000 and status["accepted_commands"] == 2
        print(f"PASS: hardware boot={boot}, duplicate did not execute, conflict rejected, period retained", flush=True)
        invalid = p.command("SET_PARAMETER", 3, parameter_id=1, value=99)
        assert invalid[0]["payload"]["reason"] == 2
        unknown = bytearray(p.wire("PING", 4, {}))
        unknown[8:10] = b"\x00\xff"
        unknown[-2:] = crc16(unknown[:-2]).to_bytes(2, "big")
        assert p.transact(bytes(unknown), 4)[0]["payload"]["reason"] == 1
        bad = bytearray(p.wire("PING", 5, {}))
        bad[-1] ^= 1
        assert not p.transact(bytes(bad), 5, .7)
        p.port.write(b"x" * 300 + b"\x00")
        ping = p.command("PING", 6)
        assert ping[-1]["payload"]["stage"] == 2
        p.port.write(encode_frame(p.wire("PING", 9, {}))[:-1])
        time.sleep(.7)
        p.port.write(b"\x00")
        assert p.command("PING", 10)[-1]["payload"]["stage"] == 2
        comms = p.command("REQUEST_TELEMETRY", 7, data_group=48)[1]["payload"]
        assert comms["crc_errors"] >= 1 and comms["dropped_packets"] >= 3
        print("PASS: hardware invalid/unknown rejection, corrupt CRC discard, oversized/truncated-frame recovery", flush=True)
        if args.reset_test:
            p.port.close()
            subprocess.run(["sudo", "-n", "picotool", "reboot", "-f"], check=True)
            deadline = time.monotonic() + 15
            while True:
                try:
                    replacement = Probe(args.device)
                    break
                except (OSError, serial.SerialException):
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.25)
            p = replacement
            status = p.command("REQUEST_STATUS", 1)[1]
            assert status["header"]["source_boot_id"] != boot
            assert status["payload"]["telemetry_period_ms"] == 1000
            assert status["payload"]["accepted_commands"] == 1
            print("PASS: hardware reboot changes boot ID, clears counters/cache and restores default period", flush=True)
        else:
            p.command("SET_PARAMETER", 8, parameter_id=1, value=1000)
    finally:
        p.port.close()


if __name__ == "__main__":
    main()
