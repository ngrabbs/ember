"""Keep simulator DNS available during server boot, then begin sample traffic."""
import os
import time
from urllib.error import URLError
from urllib.request import urlopen

deadline = time.monotonic() + 600
while True:
    try:
        with urlopen("http://yamcs:8090/api/instances/myproject", timeout=3) as response:
            if response.status == 200:
                break
    except (URLError, TimeoutError):
        pass
    if time.monotonic() >= deadline:
        raise SystemExit("Yamcs did not become ready within 10 minutes; check server logs.")
    time.sleep(1)

os.execvp("python", ["python", "-u", "simulator.py", "--tm_host", "yamcs", "--tc_host", "0.0.0.0"])
