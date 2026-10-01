"""Generate Yamcs XTCE and Java wire constants from dictionary.json."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from codec import DICTIONARY as D, encode, layout

NS = "http://www.omg.org/spec/XTCE/20180204"
ET.register_namespace("", NS)


def node(parent, tag, **attrs):
    return ET.SubElement(parent, "{" + NS + "}" + tag,
                         {k: str(v).lower() if isinstance(v, bool) else str(v)
                          for k, v in attrs.items()})


def generate(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    root = ET.Element("{" + NS + "}SpaceSystem", name="ember")
    tm = node(root, "TelemetryMetaData")
    types = node(tm, "ParameterTypeSet")
    parameters = node(tm, "ParameterSet")
    containers = node(tm, "ContainerSet")

    def parameter(name, field):
        bits = layout([field]).size * 8
        enum = field.get("enum")
        ptype = node(types, "EnumeratedParameterType" if enum else "FloatParameterType" if field.get("scale") else "IntegerParameterType",
                     name=name + "_type", **({} if enum or field.get("scale") else {"signed": field["type"].startswith("i")}))
        units = node(ptype, "UnitSet")
        if field.get("unit"):
            node(units, "Unit").text = field["unit"]
        encoding = node(ptype, "IntegerDataEncoding", sizeInBits=bits,
             encoding="twosComplement" if field["type"].startswith("i") else "unsigned")
        if field.get("scale"):
            polynomial = node(node(encoding, "DefaultCalibrator"), "PolynomialCalibrator")
            node(polynomial, "Term", coefficient=field["scale"], exponent=1)
        if enum:
            values = node(ptype, "EnumerationList")
            for label, value in D["enums"][enum].items():
                node(values, "Enumeration", value=value, label=label)
        node(parameters, "Parameter", name=name, parameterTypeRef=name + "_type")

    primary = [{"name": n, "type": "u16"} for n in
               ("packet_identity", "packet_sequence_raw", "packet_length")]
    base = node(containers, "SequenceContainer", name="Packet", abstract="true")
    entries = node(base, "EntryList")
    for field in primary + D["secondary_header"]:
        parameter(field["name"], field)
        node(entries, "ParameterRefEntry", parameterRef=field["name"])

    for message in D["messages"]:
        if message["kind"] == "command":
            continue
        container = node(containers, "SequenceContainer", name=message["name"])
        ancillary = node(container, "AncillaryDataSet")
        node(ancillary, "AncillaryData", name="Yamcs").text = "UseAsArchivingPartition"
        if message.get("expected_interval_ms"):
            node(container, "DefaultRateInStream", basis="perSecond",
                 minimumValue=1000 / message["expected_interval_ms"])
        entries = node(container, "EntryList")
        for field in message["fields"]:
            name = message["name"] + "_" + field["name"]
            parameter(name, field)
            entry = node(entries, "ParameterRefEntry", parameterRef=name)
            if field == message["fields"][0]:
                node(node(entry, "LocationInContainerInBits", referenceLocation="containerStart"),
                     "FixedValue").text = "240"
        for field_name in ("source_boot_id", "uptime_ms"):
            field = next(f for f in D["secondary_header"] if f["name"] == field_name)
            name = message["name"] + "_" + field_name
            parameter(name, field)
            entry = node(entries, "ParameterRefEntry", parameterRef=name)
            offset = 6 + sum(layout([f]).size for f in D["secondary_header"][:D["secondary_header"].index(field)])
            node(node(entry, "LocationInContainerInBits", referenceLocation="containerStart"),
                 "FixedValue").text = str(offset * 8)
        base_ref = node(container, "BaseContainer", containerRef="Packet")
        comparisons = node(node(base_ref, "RestrictionCriteria"), "ComparisonList")
        for name, value in (("kind", D["kinds"][message["kind"]]),
                            ("message_id", message["id"])):
            node(comparisons, "Comparison", parameterRef=name, value=value)

    tc = node(root, "CommandMetaData")
    argument_types = node(tc, "ArgumentTypeSet")
    commands = node(tc, "MetaCommandSet")
    for message in D["messages"]:
        if message["kind"] != "command":
            continue
        command = node(commands, "MetaCommand", name=message["name"],
                       shortDescription="EMBER software bench command; no RF endpoint")
        arguments = node(command, "ArgumentList")
        for field in message["fields"]:
            name = message["name"] + "_" + field["name"] + "_type"
            atype = node(argument_types, "IntegerArgumentType", name=name, signed="false")
            units = node(atype, "UnitSet")
            if field.get("unit"):
                node(units, "Unit").text = field["unit"]
            node(atype, "IntegerDataEncoding", sizeInBits=layout([field]).size * 8, encoding="unsigned")
            # Full integer domain permits a deliberate endpoint rejection test.
            node(arguments, "Argument", name=field["name"], argumentTypeRef=name,
                 initialValue=D["parameters"]["TELEMETRY_PERIOD"]["default"]
                 if field["name"] == "value" else 1)
        entries = node(node(command, "CommandContainer", name=message["name"]), "EntryList")
        placeholder = encode(message["name"], sequence=0, source=D["endpoints"]["ground"],
                             target=D["endpoints"]["ihu"], transaction_epoch=1,
                             transaction_id=1, source_boot_id=1, uptime_ms=0,
                             payload={field["name"]: 0 for field in message["fields"]})
        node(entries, "FixedValueEntry", name="header", binaryValue=placeholder[:30].hex(), sizeInBits=240)
        for field in message["fields"]:
            node(entries, "ArgumentRefEntry", argumentRef=field["name"])
        node(entries, "FixedValueEntry", name="crc", binaryValue="0000", sizeInBits=16)
    ET.indent(root)
    ET.ElementTree(root).write(destination / "ember.xml", encoding="utf-8", xml_declaration=True)

    constants = ["package com.example.ember;", "// Generated from dictionary.json. Do not edit.",
                 "public final class WireProfile {",
                 f"  public static final int MAX_PACKET = {D['max_packet_bytes']};",
                 f"  public static final int SCHEMA = {D['schema_version']};",
                 f"  public static final int DOWNLINK_IDENTITY = {0x800 | D['apids']['downlink']};"]
    offset = 6
    for field in D["secondary_header"]:
        constants.append(f"  public static final int {field['name'].upper()} = {offset};")
        offset += layout([field]).size
    constants.append(f"  public static final int PAYLOAD = {offset};")
    for message in D["messages"]:
        position = offset
        for field in message["fields"]:
            constants.append(f"  public static final int {message['name']}_{field['name'].upper()} = {position};")
            position += layout([field]).size
    constants += [
                  "  public static int payloadLength(int kind, int id) {",
                  "    return switch ((kind << 16) | id) {"]
    for m in D["messages"]:
        if m["kind"] != "command":
            constants.append(f"      case {(D['kinds'][m['kind']] << 16) | m['id']} -> {layout(m['fields']).size};")
    constants += ["      default -> -1;", "    };", "  }", "}"]
    (destination / "WireProfile.java").write_text("\n".join(constants) + "\n")


if __name__ == "__main__":
    generate(sys.argv[1])
