"""Software-only GROUND_TEST endpoint; never opens a radio or serial device."""
import argparse
from collections import OrderedDict
import secrets
import select
import socket
import time
from urllib.error import URLError
from urllib.request import urlopen
from codec import DICTIONARY as D, PacketError, decode, encode, validate_arguments


class Endpoint:
    def __init__(self, clock=time.monotonic, boot_id=None):
        self.clock = clock
        self.start = clock()
        self.boot_id = boot_id or secrets.randbelow(0xffffffff) + 1
        self.sequence = 0
        self.period = D["parameters"]["TELEMETRY_PERIOD"]["default"]
        self.accepted = self.rejected = self.rx = self.tx = self.crc_errors = self.dropped = 0
        self.cache = OrderedDict()

    def packet(self, name, payload, transaction=(0, 0)):
        result = encode(name, sequence=self.sequence, source=D["endpoints"]["ihu"],
                        target=D["endpoints"]["ground"], transaction_epoch=transaction[0],
                        transaction_id=transaction[1], source_boot_id=self.boot_id,
                        uptime_ms=int((self.clock() - self.start) * 1000) & 0xffffffff,
                        payload=payload)
        self.sequence = (self.sequence + 1) & 0x3fff
        self.tx = (self.tx + 1) & 0xffffffff
        return result

    def telemetry(self, name):
        if name in ("SYSTEM_STATUS", "HEARTBEAT"):
            payload = dict(mode=D["enums"]["mode"]["SAFE"],
                           configuration=D["enums"]["configuration"]["GROUND_TEST"],
                           telemetry_period_ms=self.period)
            if name == "SYSTEM_STATUS":
                payload.update(accepted_commands=self.accepted, rejected_commands=self.rejected)
            return payload
        return dict(rx_packets=self.rx, tx_packets=self.tx, crc_errors=self.crc_errors,
                    dropped_packets=self.dropped, rssi_dbm=-32768)

    def periodic(self):
        return [self.packet(name, self.telemetry(name))
                for name in ("HEARTBEAT", "SYSTEM_STATUS", "COMM_STATUS")]

    def handle(self, wire):
        try:
            command = decode(wire, allow_unknown_command=True)
            if command["header"]["kind"] != D["kinds"]["command"]:
                raise PacketError("not an uplink command")
        except PacketError as error:
            self.dropped = (self.dropped + 1) & 0xffffffff
            if str(error) == "CRC mismatch":
                self.crc_errors = (self.crc_errors + 1) & 0xffffffff
            return []
        self.rx = (self.rx + 1) & 0xffffffff
        header = command["header"]
        transaction = (header["transaction_epoch"], header["transaction_id"])
        key = (header["source"], *transaction)
        fingerprint = (header["message_id"], header["target"], wire[30:-2])

        def response(stage, reason="NONE", parameter=0, value=0):
            return ("COMMAND_RESPONSE", dict(command_id=header["message_id"],
                    stage=D["enums"]["stage"][stage], reason=D["enums"]["reason"][reason],
                    parameter_id=parameter, value=value))

        if key in self.cache:
            previous, reports = self.cache[key]
            if fingerprint != previous:
                self.rejected = (self.rejected + 1) & 0xffffffff
                reports = [response("REJECTED", "TRANSACTION_CONFLICT")]
            return [self.packet(name, payload, transaction) for name, payload in reports]
        if command["name"] is None:
            reports = [response("REJECTED", "UNKNOWN_COMMAND")]
            self.rejected = (self.rejected + 1) & 0xffffffff
        else:
            try:
                validate_arguments(command)
            except PacketError:
                reports = [response("REJECTED", "INVALID_PARAMETER")]
                self.rejected = (self.rejected + 1) & 0xffffffff
            else:
                self.accepted = (self.accepted + 1) & 0xffffffff
                reports = [response("ACCEPTED")]
                name = command["name"]
                if name == "SET_PARAMETER":
                    self.period = command["payload"]["value"]
                    reports.append(response("COMPLETED", parameter=1, value=self.period))
                elif name in ("REQUEST_STATUS", "REQUEST_TELEMETRY"):
                    group = command["payload"].get("data_group", 1)
                    telemetry = "SYSTEM_STATUS" if group == 1 else "COMM_STATUS"
                    reports.append((telemetry, self.telemetry(telemetry)))
                    reports.append(response("COMPLETED"))
                else:
                    reports.append(response("COMPLETED"))
        self.cache[key] = (fingerprint, reports)
        if len(self.cache) > 64:
            self.cache.popitem(last=False)
        return [self.packet(name, payload, transaction) for name, payload in reports]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="yamcs")
    parser.add_argument("--tm-port", type=int, default=10016)
    parser.add_argument("--tc-port", type=int, default=10026)
    args = parser.parse_args()
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.bind(("0.0.0.0", args.tc_port))
    control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    control.bind(("127.0.0.1", 10027))
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    deadline = time.monotonic() + 600
    while True:
        try:
            with urlopen(f"http://{args.host}:8090/api/instances/ember", timeout=3) as response:
                if response.status == 200:
                    break
        except (URLError, TimeoutError):
            pass
        if time.monotonic() >= deadline:
            raise SystemExit("EMBER Yamcs instance did not become ready")
        time.sleep(1)
    endpoint = Endpoint()
    next_periodic = time.monotonic()
    drop_next = False
    print(f"EMBER GROUND_TEST simulator boot_id={endpoint.boot_id}", flush=True)
    while True:
        ready, _, _ = select.select([control, receiver], [], [],
                                    max(0, next_periodic - time.monotonic()))
        if control in ready:
            instruction, address = control.recvfrom(64)
            if instruction == b"drop-results-once":
                drop_next = True
                control.sendto(b"armed", address)
        if receiver in ready:
            packet, _ = receiver.recvfrom(65535)
            old_period = endpoint.period
            results = endpoint.handle(packet)
            if drop_next and results:
                results = []
                drop_next = False
                print("Fault injection: suppressed one transaction's results", flush=True)
            for result in results:
                sender.sendto(result, (args.host, args.tm_port))
            if endpoint.period != old_period:
                next_periodic = time.monotonic() + endpoint.period / 1000
        if time.monotonic() >= next_periodic:
            for packet in endpoint.periodic():
                sender.sendto(packet, (args.host, args.tm_port))
            next_periodic = time.monotonic() + endpoint.period / 1000


if __name__ == "__main__":
    main()
