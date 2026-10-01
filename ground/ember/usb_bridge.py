"""Pi host bridge: one stable USB CDC identity, COBS frames, CCSDS over UDP."""
import argparse
import select
import socket
import time
import serial
from codec import PacketError, decode
from framing import FrameReader, encode_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True, help="Exact /dev/serial/by-id path")
    parser.add_argument("--bind", required=True, help="Docker host-gateway address, not a LAN wildcard")
    args = parser.parse_args()
    uplink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    uplink.bind((args.bind, 10026))
    control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    control.bind(("127.0.0.1", 10027))
    downlink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = None
    reader = FrameReader()
    reopen = partial_since = 0
    drop_next = False
    suppressed = set()
    counters = {"uplink": 0, "downlink": 0, "invalid": 0, "disconnected": 0}
    next_log = time.monotonic() + 30
    while True:
        now = time.monotonic()
        if port is None and now >= reopen:
            try:
                port = serial.Serial(args.device, 115200, timeout=0, write_timeout=.2, exclusive=True)
                port.reset_input_buffer()
                reader = FrameReader()
                partial_since = 0
                print("USB connected: " + args.device, flush=True)
            except (OSError, serial.SerialException):
                reopen = now + 1
        ready, _, _ = select.select([uplink, control] + ([port] if port else []), [], [], .02)
        if control in ready:
            message, address = control.recvfrom(64)
            if message == b"drop-results-once":
                drop_next = True
                control.sendto(b"armed", address)
        if uplink in ready:
            packet, _ = uplink.recvfrom(65535)
            try:
                command = decode(packet, allow_unknown_command=True)
                if command["header"]["kind"] != 0:
                    raise PacketError("not a command")
                if port is None:
                    counters["disconnected"] += 1
                else:
                    if drop_next:
                        h = command["header"]
                        if len(suppressed) >= 64:
                            suppressed.clear()
                        suppressed.add((h["transaction_epoch"], h["transaction_id"]))
                        drop_next = False
                    frame = encode_frame(packet)
                    if port.write(frame) != len(frame):
                        raise serial.SerialException("partial USB frame write")
                    counters["uplink"] += 1
            except PacketError:
                counters["invalid"] += 1
            except (OSError, serial.SerialException):
                # Never replay an uncertain write automatically.
                if port:
                    port.close()
                port = None
                reopen = now + 1
                counters["disconnected"] += 1
                print("USB write failed; outcome unknown, no retry", flush=True)
        if port and port in ready:
            try:
                data = port.read(4096)
                if not data:
                    raise serial.SerialException("USB disconnected")
                if not reader.buffer:
                    partial_since = now
                for packet in reader.feed(data):
                    try:
                        result = decode(packet)
                        if result["header"]["kind"] == 0:
                            raise PacketError("unexpected downlink command")
                        h = result["header"]
                        if (h["transaction_epoch"], h["transaction_id"]) not in suppressed:
                            downlink.sendto(packet, ("127.0.0.1", 10016))
                            counters["downlink"] += 1
                    except PacketError:
                        counters["invalid"] += 1
                if b"\x00" in data and reader.buffer:
                    # The final partial frame started after the last delimiter.
                    partial_since = now
            except (OSError, serial.SerialException):
                port.close()
                port = None
                reopen = now + 1
                print("USB disconnected; waiting for same identity", flush=True)
        if reader.buffer and now - partial_since > .5:
            reader.buffer.clear()
            reader.discard = True
            reader.errors += 1
        if now >= next_log:
            print(f"USB bridge {counters}, framing_errors={reader.errors}", flush=True)
            next_log = now + 30


if __name__ == "__main__":
    main()
