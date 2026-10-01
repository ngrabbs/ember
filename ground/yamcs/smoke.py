#!/usr/bin/env python3
"""Check ONLY the isolated upstream starter; send one harmless simulator command."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8090")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent

    def api(path, body=None):
        payload = None if body is None else json.dumps(body).encode()
        request = Request(args.url.rstrip("/") + path, data=payload,
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=10) as response:
            return json.load(response)

    def links():
        return {link["name"]: link for link in api("/api/links/myproject")["links"]}

    # Refuse to exercise a different deployment/dictionary/transport. The
    # Compose receiver counter proves delivery, not merely UDP transmission.
    info = links()
    destination = info["udp-out"]["detailedStatus"]
    if "simulator:10025" not in destination:
        raise SystemExit("This smoke check requires the isolated Compose starter simulator.")
    before_tm = int(info["udp-in"]["dataInCount"])
    time.sleep(3)
    after = links()
    if int(after["udp-in"]["dataInCount"]) <= before_tm:
        raise SystemExit("Telemetry count did not grow.")
    print("PASS: inbound telemetry count grows.")

    archived = api("/api/archive/myproject/packets?limit=1").get("packets", [])
    if not archived:
        raise SystemExit("No archived packet found.")
    print("PASS: packet archived; generation time " + archived[0]["generationTime"])

    def received_count():
        log = subprocess.check_output(["docker", "compose", "logs", "--no-color", "simulator"],
                                      cwd=root, text=True)
        counts = re.findall(r"Received: (\d+) commands", log)
        if not counts:
            raise SystemExit("Simulator counter unavailable; ensure it is running.")
        return int(counts[-1])

    before_rx = received_count()
    before_tx = int(after["udp-out"]["dataOutCount"])
    result = api("/api/processors/myproject/realtime/commands/myproject/SwitchVoltageOn",
                 {"args": {"Battery": 1}, "origin": "ember-starter-smoke",
                  "sequenceNumber": int(time.time()), "comment": "Isolated software simulator smoke check"})
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if received_count() > before_rx:
            break
        time.sleep(0.5)
    else:
        raise SystemExit("Simulator did not receive the command.")
    if int(links()["udp-out"]["dataOutCount"]) <= before_tx:
        raise SystemExit("Outbound command count did not grow.")
    print("PASS: sample command transmitted and received by software simulator.")
    print("Command history ID: " + result["id"])
    print("EMBER ACK/completion, hardware actions, and RF are not tested by this starter.")


if __name__ == "__main__":
    main()
