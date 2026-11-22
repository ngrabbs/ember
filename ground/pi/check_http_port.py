#!/usr/bin/env python3
"""Reject Tailscale Serve rules that compete with Yamcs's published HTTP port."""
import json
import os
import shutil
import subprocess


def check():
    if not shutil.which('tailscale'):
        return
    result = subprocess.run(['tailscale', 'serve', 'status', '--json'],
                            capture_output=True, text=True, timeout=10)
    if result.returncode:
        # An inactive Tailscale daemon has no listening Serve sockets.
        print('Tailscale Serve status unavailable; Docker will check port availability.')
        return
    port = os.environ.get('EMBER_HTTP_PORT', '8090')
    if port in json.loads(result.stdout).get('TCP', {}):
        raise SystemExit(
            f'Tailscale Serve owns Yamcs port {port}. Back up its configuration, then run '
            f'sudo tailscale serve --tcp={port} off. Yamcs is served directly on the '
            'Pi LAN and Tailscale addresses through Docker.')


if __name__ == '__main__':
    check()
