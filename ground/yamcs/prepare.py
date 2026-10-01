#!/usr/bin/env python3
"""Prepare an isolated, pinned upstream Yamcs starter; never edit flight files."""
from pathlib import Path
import argparse
import secrets
import shutil
import subprocess
import sys

REVISION = "61e94169687f8729832c754e0813bf90271e4800"
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / ".runtime" / "quickstart"


def prepare(transport="simulator"):
    if not SOURCE.exists():
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "https://github.com/yamcs/quickstart.git", str(SOURCE)], check=True)
        subprocess.run(["git", "-C", str(SOURCE), "checkout", "--detach", REVISION], check=True)
    actual = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    if actual != REVISION:
        raise SystemExit(f"Unexpected starter revision {actual}; expected {REVISION}. Preserve/review the runtime directory before replacing it.")

    # Reapplying these exact substitutions is idempotent. Archive data lives
    # outside Maven's target tree and survives container/source rebuilds.
    config = SOURCE / "src/main/yamcs/etc/yamcs.yaml"
    text = config.read_text().replace("dataDir: yamcs-data", "dataDir: /yamcs-data")
    text = text.replace("secretKey: changeme", "secretKey: " + secrets.token_hex(32))
    if "  - ember\n" not in text:
        text = text.replace("  - myproject\n", "  - myproject\n  - ember\n")
    config.write_text(text)
    instance = SOURCE / "src/main/yamcs/etc/yamcs.myproject.yaml"
    instance.write_text(instance.read_text().replace("host: localhost", "host: simulator"))
    generated = ROOT / ".runtime" / "ember-generated"
    subprocess.run([sys.executable, str(ROOT.parent / "ember/generate_mdb.py"), str(generated)], check=True)
    shutil.copy2(generated / "ember.xml", SOURCE / "src/main/yamcs/mdb/ember.xml")
    java = SOURCE / "src/main/java/com/example/ember"
    java.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "ember-java").glob("*.java"):
        shutil.copy2(source, java / source.name)
    shutil.copy2(generated / "WireProfile.java", java / "WireProfile.java")
    ember = instance.read_text().replace("port: 10015", "port: 10016").replace("port: 10025", "port: 10026")
    ember = ember.replace("host: simulator", "host: ember-simulator")
    if transport == "usb":
        ember = ember.replace("host: ember-simulator", "host: host.docker.internal")
    ember = ember.replace("com.example.myproject.MyPacketPreprocessor", "com.example.ember.EmberPacketPreprocessor")
    ember = ember.replace("com.example.myproject.MyCommandPostprocessor", "com.example.ember.EmberCommandPostprocessor")
    ember = ember.replace("file: mdb/xtce.xml", "file: mdb/ember.xml")
    (instance.parent / "yamcs.ember.yaml").write_text(ember)
    print(f"Prepared Yamcs 5.13.0 at {REVISION}; EMBER transport: {transport}.")
    print("Run: docker compose up -d")


if __name__ == "__main__":
    default = "simulator"
    if (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text().splitlines():
            if line.startswith("EMBER_PACKET_TRANSPORT="):
                default = line.split("=", 1)[1].strip()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", choices=("simulator", "usb"), default=default)
    prepare(parser.parse_args().transport)
