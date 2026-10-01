"""Generate firmware offsets, IDs and sizes from the bench dictionary."""
from pathlib import Path
import sys
from codec import DICTIONARY as D, layout


def generate(path):
    lines = ["/* Generated from dictionary.json; do not edit. */", "#pragma once",
             f"#define W_MAX_PACKET {D['max_packet_bytes']}u",
             f"#define W_VERSION {D['schema_version']}u",
             f"#define W_TC_IDENTITY {0x1800 | D['apids']['command']}u",
             f"#define W_TM_IDENTITY {0x800 | D['apids']['downlink']}u"]
    position = 6
    for field in D["secondary_header"]:
        lines.append(f"#define W_{field['name'].upper()} {position}u")
        position += layout([field]).size
    lines += [f"#define W_PAYLOAD {position}u", f"#define W_MAX_PAYLOAD {D['max_packet_bytes']-position-2}u"]
    for group in ("kinds", "endpoints"):
        for name, value in D[group].items():
            lines.append(f"#define W_{group.upper()}_{name.upper()} {value}u")
    for enum, values in D["enums"].items():
        for name, value in values.items():
            lines.append(f"#define W_{enum.upper()}_{name.upper()} {value}u")
    for message in D["messages"]:
        name = message["name"]
        lines.append(f"#define W_ID_{name} {message['id']}u")
        lines.append(f"#define W_SIZE_{name} {layout(message['fields']).size}u")
        position = 0
        for field in message["fields"]:
            lines.append(f"#define W_{name}_{field['name'].upper()} {position}u")
            position += layout([field]).size
    parameter = D["parameters"]["TELEMETRY_PERIOD"]
    for name in ("minimum", "maximum", "default"):
        lines.append(f"#define W_PERIOD_{name.upper()} {parameter[name]}u")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    generate(sys.argv[1])
