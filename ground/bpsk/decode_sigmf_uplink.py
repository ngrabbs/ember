"""Decode EMBER DBPSK uplink commands from a window of HackRF SigMF IQ."""

import argparse
import base64
import json
import math
from pathlib import Path
import sys

import numpy as np

from modem import decode


def read_baseband(metadata_path, start, end, frequency):
    metadata = json.loads(metadata_path.read_text())
    settings = metadata["global"]
    if settings["core:datatype"] != "ci8":
        raise ValueError("expected interleaved signed 8-bit IQ (ci8)")
    captures = metadata["captures"]
    if len(captures) != 1 or captures[0]["core:sample_start"] != 0:
        raise ValueError("expected one capture segment starting at sample zero")
    rate = int(settings["core:sample_rate"])
    offset = frequency - captures[0]["core:frequency"]
    if rate < 40_000 or abs(offset) + 12_000 >= rate / 2:
        raise ValueError("requested frequency must be within the recorded band")
    raw = np.memmap(metadata_path.with_suffix(".sigmf-data"), dtype=np.int8, mode="r")
    if raw.size % 2:
        raise ValueError("IQ file ends with an incomplete sample")
    if not (0 <= start < end <= raw.size / (2 * rate)):
        raise ValueError(f"window must lie within the {raw.size / (2 * rate):g} s recording")
    if end - start > 4:
        raise ValueError("select a window of up to four seconds around the burst")

    first, last = round(start * rate), round(end * rate)
    step = round(rate / 40_000)
    count = (last - first) // step * step
    if not count:
        raise ValueError("window is too short")
    pairs = raw[2 * first : 2 * (first + count)].reshape(-1, 2)
    iq = pairs[:, 0] + 1j * pairs[:, 1]
    iq *= np.exp(-2j * np.pi * offset * np.arange(count) / rate)
    decimated = iq.reshape(-1, step).mean(axis=1)
    intermediate_rate = rate / step
    positions = np.arange(math.floor(len(decimated) * 48_000 / intermediate_rate))
    return np.interp(positions * intermediate_rate / 48_000,
                     np.arange(len(decimated)), decimated)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path, help="path to the .sigmf-meta sidecar")
    parser.add_argument("--start", type=float, required=True, help="start in seconds")
    parser.add_argument("--end", type=float, required=True, help="end in seconds")
    parser.add_argument("--frequency", type=float, required=True, help="carrier in Hz")
    parser.add_argument("--history", type=Path, help="Yamcs history JSON for byte comparison")
    parser.add_argument(
        "--format", choices=("json", "hex", "hexdump"), default="json",
        help="JSON, one hex line per packet, or a hex dump with byte offsets and ASCII",
    )
    args = parser.parse_args()
    try:
        expected = None
        if args.history:
            history = json.loads(args.history.read_text())
            expected = next(
                (base64.b64decode(attr["value"]["binaryValue"], validate=True).hex()
                 for attr in history["attr"] if attr["name"] == "binary"), None
            )
            if expected is None:
                raise ValueError("Yamcs history has no processed binary entry")
        iq = read_baseband(args.metadata, args.start, args.end, args.frequency)
        packets = decode(iq, single_window=True, packet_kinds=(0,))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))

    for packet in packets:
        packet["estimated_carrier_hz"] = args.frequency + packet["carrier_offset_hz"]
        if expected is not None:
            packet["yamcs_binary_match"] = packet["hex"] == expected
    if args.format == "json":
        print(json.dumps(packets, indent=2))
    else:
        if not packets:
            print("No CRC-valid uplink packets found.", file=sys.stderr)
        for index, packet in enumerate(packets, start=1):
            data = bytes.fromhex(packet["hex"])
            summary = (
                f"Packet {index}: {packet['decoded']['name']}, "
                f"sequence {packet['sequence']}, {len(data)} bytes, CRC-32 and CRC-16 OK"
            )
            if expected is not None:
                summary += ", Yamcs " + ("MATCH" if packet["yamcs_binary_match"] else "MISMATCH")
            print(summary, file=sys.stderr)
            if args.format == "hex":
                print(data.hex().upper())
            else:
                if index > 1:
                    print()
                for offset in range(0, len(data), 16):
                    row = data[offset:offset + 16]
                    hex_bytes = row.hex(" ").upper()
                    ascii_bytes = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in row)
                    print(f"{offset:04X}  {hex_bytes:<47}  |{ascii_bytes}|")
    if expected is not None:
        return 0 if any(packet["yamcs_binary_match"] for packet in packets) else 1
    return 0 if packets else 1


if __name__ == "__main__":
    raise SystemExit(main())
