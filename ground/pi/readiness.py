#!/usr/bin/env python3
"""Ethernet-first demo access and USB-presence receiver supervision. No RF TX."""
import argparse
from pathlib import Path
import subprocess
import time


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True,
                          timeout=25).stdout.strip()


def ethernet_ready(interface):
    try:
        carrier = (Path('/sys/class/net') / interface / 'carrier').read_text().strip()
        state = command('nmcli', '-g', 'GENERAL.STATE', 'device', 'show', interface)
        return carrier == '1' and state.startswith('100 ')
    except (OSError, subprocess.SubprocessError):
        return False


def libresdr_present(root=Path('/sys/bus/usb/devices')):
    for device in root.iterdir():
        try:
            if ((device / 'idVendor').read_text().strip() == '2500' and
                    (device / 'idProduct').read_text().strip() == '0020'):
                return True
        except OSError:
            pass
    return False


def reconcile(interface, profile):
    # Separate failure domains: Wi-Fi failure must not prevent UDP reception.
    for task in ('hotspot', 'receiver'):
        try:
            if task == 'hotspot':
                active = profile in command('nmcli', '-g', 'NAME', 'connection',
                                             'show', '--active').splitlines()
                wanted = not ethernet_ready(interface)
                if wanted and not active:
                    command('nmcli', 'radio', 'wifi', 'on')
                    command('nmcli', 'connection', 'up', profile)
                    print('Hotspot enabled: Ethernet unavailable', flush=True)
                elif active and not wanted:
                    command('nmcli', 'connection', 'down', profile)
                    print('Hotspot disabled: Ethernet connected', flush=True)
            else:
                state = command('systemctl', 'show', 'ember-lte-listener.service',
                                '--property=ActiveState', '--value')
                wanted = libresdr_present()
                if wanted and state not in ('active', 'activating'):
                    command('systemctl', 'start', 'ember-lte-listener.service')
                    print('LTE listener enabled: LibreSDR present', flush=True)
                elif not wanted and state not in ('inactive', 'deactivating'):
                    command('systemctl', 'stop', 'ember-lte-listener.service')
                    print('LTE listener disabled: LibreSDR absent', flush=True)
        except (OSError, subprocess.SubprocessError) as error:
            print(f'{task} reconciliation failed: {error}', flush=True)


def recover_yamcs():
    """Docker handles process exits; recover a running but unhealthy server too."""
    try:
        health = command('docker', 'inspect', '--format',
                         '{{.State.Health.Status}}', 'ember-ground-starter-yamcs-1')
        if health == 'unhealthy':
            print('Yamcs unhealthy: restarting its existing container', flush=True)
            command('docker', 'restart', 'ember-ground-starter-yamcs-1')
    except (OSError, subprocess.SubprocessError) as error:
        print(f'Yamcs health check failed: {error}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ethernet-interface', default='eth0')
    parser.add_argument('--hotspot-profile', default='ember-demo-hotspot')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    next_health = time.monotonic() + 60
    while True:
        reconcile(args.ethernet_interface, args.hotspot_profile)
        if args.once:
            break
        if time.monotonic() >= next_health:
            recover_yamcs()
            next_health = time.monotonic() + 60
        time.sleep(5)
