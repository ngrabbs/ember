#!/usr/bin/env python3
"""Bring up only LC2502 CAN A, bounded retries for the boot probe timeout."""
from pathlib import Path
import subprocess
import time


def main():
    interface = Path('/sys/class/net/can0')
    spi = Path('/sys/bus/spi/devices/spi0.0')
    for attempt in range(20):
        if interface.exists():
            break
        if not spi.exists():
            raise RuntimeError('spi0.0 missing: install the LC2502 CAN A boot overlay')
        print(f'MCP2515 probe attempt {attempt + 1}/20', flush=True)
        Path('/sys/bus/spi/drivers_probe').write_text('spi0.0')
        time.sleep(.25)
    if not interface.exists():
        raise RuntimeError('CAN A did not initialize; inspect power, crystal and SPI wiring')
    # A responder must participate normally, not retain a diagnostic listen-only
    # or loopback mode. No CAN B or other network interfaces are changed.
    subprocess.run(['ip', 'link', 'set', 'can0', 'down'], check=True)
    subprocess.run(['ip', 'link', 'set', 'can0', 'type', 'can', 'bitrate', '500000',
                    'loopback', 'off', 'listen-only', 'off', 'restart-ms', '0'], check=True)
    subprocess.run(['ip', 'link', 'set', 'can0', 'up'], check=True)
    print(subprocess.check_output(['ip', '-details', 'link', 'show', 'can0'], text=True))


if __name__ == '__main__':
    main()
