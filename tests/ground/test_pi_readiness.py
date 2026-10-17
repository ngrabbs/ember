"""Exercise long-lived packet delivery and physical device detection."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ground/ember'))
from codec import DICTIONARY, encode

spec = importlib.util.spec_from_file_location('readiness', ROOT / 'ground/pi/readiness.py')
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)


class PiReadiness(unittest.TestCase):
    def test_usb_absence_attach_and_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            device = root / '4-1'
            device.mkdir()
            self.assertFalse(readiness.libresdr_present(root))
            (device / 'idVendor').write_text('2500\n')
            (device / 'idProduct').write_text('0020\n')
            self.assertTrue(readiness.libresdr_present(root))
            (device / 'idProduct').unlink()
            self.assertFalse(readiness.libresdr_present(root))

    def test_persistent_receiver_filters_duplicates_and_preserves_bytes(self):
        fields = next(m['fields'] for m in DICTIONARY['messages'] if m['name'] == 'POWER_STATUS')
        payload = {field['name']: 0 for field in fields}
        payload.update(payload_version=1, provenance=2)
        def packet(sequence):
            return encode('POWER_STATUS', sequence=sequence, source=2, target=1,
                          source_boot_id=123, uptime_ms=sequence*1000, payload=payload)
        with tempfile.TemporaryDirectory() as directory, \
                socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sink, \
                socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender, \
                socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as wrong_peer:
            sink.bind(('127.0.0.1', 10018))
            sink.settimeout(2)
            sender.bind(('127.0.0.1', 51001))
            log = Path(directory) / 'packets.jsonl'
            env = dict(os.environ, PYTHONPATH=str(ROOT / 'ground/ember'))
            proc = subprocess.Popen([sys.executable, '-u', str(ROOT / 'ground/pi/lte_listener.py'),
                                     '--peer', '127.0.0.1', '--log', str(log)],
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True)
            try:
                self.assertIn('Listening UDP', proc.stdout.readline())
                address = ('127.0.0.1', 51000)
                wrong_peer.sendto(packet(1), address)
                bad = bytearray(packet(1)); bad[-1] ^= 1
                sender.sendto(bad, address)
                sender.sendto(packet(1), address)
                sender.sendto(packet(1), address)
                sender.sendto(packet(2), address)
                self.assertEqual(sink.recv(4096), packet(1))
                self.assertEqual(sink.recv(4096), packet(2))
                sink.settimeout(.2)
                with self.assertRaises(socket.timeout):
                    sink.recv(4096)
                self.assertIsNone(proc.poll())  # Does not exit after its first packet.
                proc.terminate()
                output, _ = proc.communicate(timeout=3)
                self.assertEqual(proc.returncode, 0, output)
                self.assertIn('rejected=2 duplicates=1', output)
                captures = [json.loads(line) for line in log.read_text().splitlines()]
                self.assertEqual([c['hex'] for c in captures], [packet(1).hex(), packet(2).hex()])
            finally:
                if proc.poll() is None:
                    proc.kill(); proc.communicate()


if __name__ == '__main__':
    unittest.main()
