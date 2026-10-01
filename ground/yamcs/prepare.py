#!/usr/bin/env python3
"""Prepare an isolated, pinned upstream Yamcs starter; never edit flight files."""
from pathlib import Path
import secrets
import subprocess

REVISION = "61e94169687f8729832c754e0813bf90271e4800"
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / ".runtime" / "quickstart"


def prepare():
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
    config.write_text(text)
    instance = SOURCE / "src/main/yamcs/etc/yamcs.myproject.yaml"
    instance.write_text(instance.read_text().replace("host: simulator", "host: localhost"))
    print(f"Prepared Yamcs 5.13.0 upstream starter at {REVISION}.")
    print("Run: docker compose up -d")


if __name__ == "__main__":
    prepare()
