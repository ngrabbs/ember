"""Strict EMBER bench packet codec. No transport, dispatch or authorization.

CLI: python3 ground/ember/codec.py decode HEX
     python3 ground/ember/codec.py encode packet.json
"""
import argparse
import binascii
import json
from pathlib import Path
import struct

DICTIONARY = json.loads(Path(__file__).with_name("dictionary.json").read_text())
TYPES = {"u8": "B", "u16": "H", "u32": "I", "i16": "h"}


class PacketError(ValueError):
    pass


def layout(fields):
    return struct.Struct(">" + "".join(TYPES[field["type"]] for field in fields))


HEADER = layout(DICTIONARY["secondary_header"])


def crc16(data):
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xffff, no reflect/xorout."""
    return binascii.crc_hqx(data, 0xffff)


def message_for(kind, message_id):
    for message in DICTIONARY["messages"]:
        if message["kind"] == kind and message["id"] == message_id:
            return message
    raise PacketError("unknown kind/message ID")


def pack_fields(fields, values):
    if set(values) != {field["name"] for field in fields}:
        raise PacketError("missing or unexpected fields")
    try:
        return layout(fields).pack(*(values[field["name"]] for field in fields))
    except (struct.error, TypeError) as error:
        raise PacketError(str(error)) from error


def validate_identity(header, kind):
    endpoints = DICTIONARY["endpoints"]
    if header["source"] not in endpoints.values() or header["target"] not in endpoints.values():
        raise PacketError("unknown endpoint")
    epoch, transaction = header["transaction_epoch"], header["transaction_id"]
    if bool(epoch) != bool(transaction):
        raise PacketError("transaction epoch and ID must both be zero or nonzero")
    if not header["source_boot_id"]:
        raise PacketError("source_boot_id must be nonzero")
    if kind == "command":
        if not transaction or header["source"] != endpoints["ground"] or header["target"] != endpoints["ihu"]:
            raise PacketError("bench commands require ground-to-IHU and a transaction")
    elif header["source"] == endpoints["ground"] or header["target"] != endpoints["ground"]:
        raise PacketError("downlink must target ground from a spacecraft endpoint")
    if kind == "response" and (not transaction or header["source"] != endpoints["ihu"]):
        raise PacketError("command responses require IHU source and a transaction")


def encode(name, *, sequence, source, target, transaction_epoch=0,
           transaction_id=0, source_boot_id, uptime_ms, payload):
    message = next((m for m in DICTIONARY["messages"] if m["name"] == name), None)
    if message is None:
        raise PacketError("unknown message name")
    if not isinstance(sequence, int) or not 0 <= sequence < 16384:
        raise PacketError("sequence outside 14-bit range")
    body = pack_fields(message["fields"], payload)
    header = dict(schema_version=DICTIONARY["schema_version"],
                  kind=DICTIONARY["kinds"][message["kind"]], message_id=message["id"],
                  source=source, target=target, transaction_epoch=transaction_epoch,
                  transaction_id=transaction_id, source_boot_id=source_boot_id,
                  uptime_ms=uptime_ms, payload_length=len(body))
    validate_identity(header, message["kind"])
    secondary = pack_fields(DICTIONARY["secondary_header"], header)
    command = message["kind"] == "command"
    apid = DICTIONARY["apids"]["command" if command else "downlink"]
    total_length = 6 + len(secondary) + len(body) + 2
    if total_length > DICTIONARY["max_packet_bytes"]:
        raise PacketError("packet exceeds profile limit")
    packet = struct.pack(">HHH", (int(command) << 12) | 0x800 | apid,
                         0xc000 | sequence, total_length - 7) + secondary + body
    return packet + struct.pack(">H", crc16(packet))


def decode(packet, *, allow_unknown_command=False):
    if not 6 + HEADER.size + 2 <= len(packet) <= DICTIONARY["max_packet_bytes"]:
        raise PacketError("packet size outside profile limits")
    identity, sequence, length = struct.unpack_from(">HHH", packet)
    if length + 7 != len(packet):
        raise PacketError("CCSDS length mismatch")
    if identity >> 13 or not identity & 0x800 or sequence >> 14 != 3:
        raise PacketError("unsupported CCSDS version, secondary flag or segmentation")
    if crc16(packet[:-2]) != struct.unpack_from(">H", packet, len(packet) - 2)[0]:
        raise PacketError("CRC mismatch")
    header = dict(zip((f["name"] for f in DICTIONARY["secondary_header"]),
                      HEADER.unpack_from(packet, 6)))
    if header["schema_version"] != DICTIONARY["schema_version"]:
        raise PacketError("unsupported EMBER schema version")
    kind = next((name for name, value in DICTIONARY["kinds"].items()
                 if value == header["kind"]), None)
    if kind is None:
        raise PacketError("unknown packet kind")
    command = kind == "command"
    if (identity >> 12 & 1) != int(command) or identity & 0x7ff != DICTIONARY["apids"]["command" if command else "downlink"]:
        raise PacketError("packet type/APID does not match kind")
    validate_identity(header, kind)
    body = packet[6 + HEADER.size:-2]
    if len(body) != header["payload_length"]:
        raise PacketError("payload length mismatch")
    try:
        message = message_for(kind, header["message_id"])
    except PacketError:
        if not allow_unknown_command or kind != "command":
            raise
        return {"name": None, "sequence": sequence & 0x3fff,
                "header": header, "payload": {}, "raw_payload": body}
    payload_layout = layout(message["fields"])
    if len(body) != header["payload_length"] or len(body) != payload_layout.size:
        raise PacketError("payload length mismatch")
    payload = dict(zip((f["name"] for f in message["fields"]), payload_layout.unpack(body)))
    return {"name": message["name"], "sequence": sequence & 0x3fff,
            "header": header, "payload": payload}


def validate_arguments(decoded):
    """Application validation, separate from structural decode for NACK handling."""
    message = message_for(next(k for k, v in DICTIONARY["kinds"].items()
                               if v == decoded["header"]["kind"]),
                          decoded["header"]["message_id"])
    for field in message["fields"]:
        if "enum" in field and decoded["payload"][field["name"]] not in DICTIONARY["enums"][field["enum"]].values():
            raise PacketError("invalid " + field["name"])
    if decoded["name"] == "SET_PARAMETER":
        parameter = DICTIONARY["parameters"]["TELEMETRY_PERIOD"]
        if not parameter["minimum"] <= decoded["payload"]["value"] <= parameter["maximum"]:
            raise PacketError("TELEMETRY_PERIOD outside allowed range")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode"))
    parser.add_argument("input")
    args = parser.parse_args()
    try:
        if args.operation == "decode":
            print(json.dumps(decode(bytes.fromhex(args.input)), indent=2))
        else:
            print(encode(**json.loads(Path(args.input).read_text())).hex())
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, str(error) + "\n")
