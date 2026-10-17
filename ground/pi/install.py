#!/usr/bin/env python3
"""Install boot readiness on an already provisioned EMBER Raspberry Pi."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess


def cmd(*args):
    subprocess.run(args, check=True, timeout=180, stdout=subprocess.DEVNULL)


def install(args):
    if os.geteuid() != 0:
        raise SystemExit('Run with sudo; prepare a private password file first.')
    password = args.hotspot_password_file.read_text().strip()
    if not 8 <= len(password) <= 63 or not password.isascii():
        raise SystemExit('Hotspot password must be 8..63 ASCII characters.')
    source = Path(__file__).resolve().parent
    repo = args.repo.resolve()
    env = repo / 'ground/yamcs/.env'
    if not env.exists():
        raise SystemExit('Provision Yamcs and its runtime first; .env is missing.')
    backup = Path('/var/backups/ember-ground') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup.mkdir(parents=True, mode=0o700)
    shutil.copy2(env, backup / 'yamcs.env')
    nm = Path('/etc/NetworkManager/system-connections')
    shutil.copytree(nm, backup / 'network-connections')
    target = Path('/opt/ember-ground')
    (target / 'ember').mkdir(parents=True, exist_ok=True)
    for name in ('readiness.py', 'lte_listener.py', 'compose.boot.yaml'):
        shutil.copy2(source / name, target / name)
    for name in ('lte_receiver.py', 'codec.py', 'dictionary.json'):
        shutil.copy2(repo / 'ground/ember' / name, target / 'ember' / name)
    # sudo may inherit a restrictive umask; services run without root privileges.
    for path in (target, target / 'ember'):
        path.chmod(0o755)
    for path in target.rglob('*'):
        if path.is_file():
            path.chmod(0o644)
    for name in ('ember-ground-readiness.service', 'ember-lte-listener.service'):
        shutil.copy2(source / name, Path('/etc/systemd/system') / name)
    dropin = Path('/etc/systemd/system/ember-ground-starter.service.d')
    dropin.mkdir(exist_ok=True)
    dropin.chmod(0o755)
    shutil.copy2(source / 'ember-ground-starter.override.conf', dropin / 'readiness.conf')
    text = env.read_text()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith('COMPOSE_FILE='):
            files = line.split('=', 1)[1].split(':')
            if '/opt/ember-ground/compose.boot.yaml' not in files:
                files.append('/opt/ember-ground/compose.boot.yaml')
            lines[index] = 'COMPOSE_FILE=' + ':'.join(files)
            break
    else:
        lines.append('COMPOSE_FILE=compose.yaml:/opt/ember-ground/compose.boot.yaml')
    env.write_text('\n'.join(lines) + '\n')
    # Do not alter the established static Ethernet profile.
    profiles = subprocess.check_output(['nmcli', '-g', 'NAME', 'connection', 'show'], text=True)
    profile = 'ember-demo-hotspot'
    if profile not in profiles.splitlines():
        cmd('nmcli', 'connection', 'add', 'type', 'wifi', 'ifname', 'wlan0',
            'con-name', profile, 'ssid', 'EMBER-Ground', 'autoconnect', 'no')
    cmd('nmcli', 'connection', 'modify', profile,
        'connection.autoconnect', 'no', '802-11-wireless.mode', 'ap',
        '802-11-wireless.band', 'bg', '802-11-wireless.channel', '6',
        '802-11-wireless-security.key-mgmt', 'wpa-psk',
        '802-11-wireless-security.proto', 'rsn',
        '802-11-wireless-security.psk', password,
        'ipv4.method', 'shared', 'ipv4.addresses', '192.168.50.1/24',
        'ipv4.never-default', 'yes', 'ipv6.method', 'disabled')
    cmd('raspi-config', 'nonint', 'do_wifi_country', args.country)
    cmd('nmcli', 'radio', 'wifi', 'on')
    cmd('systemctl', 'daemon-reload')
    cmd('systemd-analyze', 'verify', '/etc/systemd/system/ember-ground-readiness.service',
        '/etc/systemd/system/ember-lte-listener.service',
        '/etc/systemd/system/ember-ground-starter.service')
    cmd('systemctl', 'enable', 'docker', 'ember-ground-starter', 'ember-ground-readiness')
    # Recreate only Yamcs to publish HTTP on both interfaces, preserving volumes/MDB.
    cmd('systemctl', 'restart', 'ember-ground-starter')
    cmd('systemctl', 'restart', 'ember-ground-readiness')
    print(f'Installed; network/Yamcs environment backup: {backup}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--hotspot-password-file', type=Path, required=True)
    parser.add_argument('--country', default='US')
    install(parser.parse_args())
