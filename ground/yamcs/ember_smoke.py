"""Exercise only the isolated EMBER software simulator through Yamcs HTTP."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ember"))
from codec import decode


class Lab:
    def __init__(self, url):
        self.url = url.rstrip("/")
        self.sequence = int(time.time())

    def api(self, path, body=None):
        request = Request(self.url + path, data=None if body is None else json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=10) as response:
            return json.load(response)

    def parameter(self, name):
        return self.api("/api/processors/ember/realtime/parameters/ember/" + name)["engValue"]

    def history(self, ticket):
        entry = self.api("/api/archive/ember/commands/" + quote(ticket["id"], safe=""))
        return {attribute["name"]: attribute["value"] for attribute in entry.get("attr", [])}

    def issue(self, name, **arguments):
        self.sequence += 1
        ticket = self.api("/api/processors/ember/realtime/commands/ember/" + name,
                          {"args": arguments, "origin": "ember-software-smoke",
                           "sequenceNumber": self.sequence})
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            attributes = self.history(ticket)
            if "ember-transaction-id" in attributes:
                packet = decode(base64.b64decode(attributes["binary"]["binaryValue"]))
                ticket["transaction"] = (packet["header"]["transaction_epoch"], packet["header"]["transaction_id"])
                ticket["wire"] = packet
                return ticket
            time.sleep(0.1)
        raise AssertionError("Command postprocessor did not allocate a transaction")

    def packets(self, name, start=None):
        query = {"name": "/ember/" + name, "limit": 100}
        if start:
            query["start"] = start
        records = self.api("/api/archive/ember/packets?" + urlencode(query)).get("packets", [])
        return [(record, decode(base64.b64decode(record["packet"]))) for record in records]

    def correlated(self, ticket, name="COMMAND_RESPONSE"):
        return [packet for _, packet in self.packets(name, ticket["generationTime"])
                if (packet["header"]["transaction_epoch"], packet["header"]["transaction_id"]) == ticket["transaction"]]

    def outcome(self, ticket, expected):
        deadline = time.monotonic() + 16
        while time.monotonic() < deadline:
            attributes = self.history(ticket)
            result = attributes.get("ember-outcome", {}).get("stringValue")
            if result:
                assert result == expected, (result, expected)
                return attributes
            time.sleep(0.1)
        raise AssertionError("No terminal outcome in command history")

    def completed(self, ticket, data=None):
        attributes = self.outcome(ticket, "COMPLETED")
        assert attributes["CommandComplete_Status"]["stringValue"] == "OK"
        assert attributes["Acknowledge_EMBER_Acceptance_Status"]["stringValue"] == "OK"
        reports = self.correlated(ticket)
        assert sorted(r["payload"]["stage"] for r in reports) == [0, 2], reports
        if data:
            assert self.correlated(ticket, data), "Missing correlated requested telemetry"
        return next(r for r in reports if r["payload"]["stage"] == 2)

    def cadence(self, period, after):
        deadline = time.monotonic() + period / 1000 * 5 + 5
        while time.monotonic() < deadline:
            packets = [p for _, p in self.packets("HEARTBEAT", after)
                       if p["payload"]["telemetry_period_ms"] == period and p["header"]["transaction_id"] == 0]
            if len(packets) >= 3:
                packets = sorted(packets[:3], key=lambda p: p["header"]["uptime_ms"])
                assert len({p["header"]["source_boot_id"] for p in packets}) == 1
                times = [p["header"]["uptime_ms"] for p in packets]
                intervals = [b - a for a, b in zip(times, times[1:])]
                assert all(abs(delta - period) <= max(100, period * .1) for delta in intervals), intervals
                print(f"PASS: archived HEARTBEAT intervals {intervals} ms at requested {period} ms")
                return
            time.sleep(0.25)
        raise AssertionError("Not enough periodic archived packets to verify cadence")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8090")
    parser.add_argument("--fault-test", action="store_true", help="Run on Docker host to suppress one transaction's results")
    args = parser.parse_args()
    lab = Lab(args.url)
    links = {link["name"]: link for link in lab.api("/api/links/ember")["links"]}
    if "ember-simulator:10026" not in links["udp-out"]["detailedStatus"]:
        raise SystemExit("Refusing commands: destination is not isolated EMBER simulator")
    if lab.parameter("SYSTEM_STATUS_configuration").get("stringValue") != "GROUND_TEST":
        raise SystemExit("Refusing commands: endpoint not identified as GROUND_TEST")
    original = lab.parameter("HEARTBEAT_telemetry_period_ms")["uint32Value"]
    try:
        for period in (1000, 2000):
            ticket = lab.issue("SET_PARAMETER", parameter_id=1, value=period)
            report = lab.completed(ticket)
            assert report["payload"]["parameter_id"] == 1 and report["payload"]["value"] == period
            print(f"PASS: SET_PARAMETER {period} ms accepted/completed, transaction {ticket['transaction']}")
            lab.cadence(period, ticket["generationTime"])
        for name, arguments, data in (("PING", {}, None), ("REQUEST_STATUS", {}, "SYSTEM_STATUS"),
                                      ("REQUEST_TELEMETRY", {"data_group": 48}, "COMM_STATUS")):
            lab.completed(lab.issue(name, **arguments), data)
            print("PASS: " + name + " correlated results" + (" and data" if data else ""))
        rejected = lab.issue("SET_PARAMETER", parameter_id=1, value=99)
        attributes = lab.outcome(rejected, "REJECTED")
        reports = lab.correlated(rejected)
        assert len(reports) == 1 and reports[0]["payload"]["stage"] == 1 and reports[0]["payload"]["reason"] == 2
        assert attributes["CommandComplete_Status"]["stringValue"] == "NOK"
        assert lab.parameter("HEARTBEAT_telemetry_period_ms")["uint32Value"] == 2000
        print("PASS: invalid period rejected with reason INVALID_PARAMETER; valid period retained")
        if args.fault_test:
            arm = "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(3); s.sendto(b'drop-results-once',('127.0.0.1',10027)); assert s.recv(64)==b'armed'"
            subprocess.run(["docker", "compose", "exec", "-T", "ember-simulator", "python", "-c", arm],
                           cwd=Path(__file__).resolve().parent, check=True)
            ticket = lab.issue("PING")
            attributes = lab.outcome(ticket, "UNKNOWN")
            assert attributes["CommandComplete_Status"]["stringValue"] == "TIMEOUT"
            assert not lab.correlated(ticket)
            print("PASS: suppressed results produce TIMEOUT / UNKNOWN outcome, not success or rejection")
    finally:
        lab.completed(lab.issue("SET_PARAMETER", parameter_id=1, value=original))
        print(f"Restored original telemetry period: {original} ms")


if __name__ == "__main__":
    main()
