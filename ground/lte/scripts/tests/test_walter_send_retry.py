"""Exercise production retry logic without opening Walter's serial port."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


class WalterSendRetryTest(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / 'walter-radio-check.py'
        tree = ast.parse(source.read_text())
        # Load the real helper/class while excluding the script's hardware startup.
        selected = ast.Module(body=[node for node in tree.body
            if getattr(node, 'name', None) in ('ModemRejected', 'send_packet')], type_ignores=[])
        self.now = 0
        self.calls = []
        self.payload = b'x' * 128
        self.ns = dict(args=SimpleNamespace(send_retries=3), emit=lambda message: None,
            time=SimpleNamespace(monotonic=lambda: self.now, sleep=self.sleep))
        exec(compile(selected, str(source), 'exec'), self.ns)
        self.error = self.ns['ModemRejected']

    def sleep(self, seconds):
        self.now += seconds

    def run_send(self, effects, deadline=30):
        def command(cmd, timeout, payload):
            self.calls.append((cmd, timeout, payload))
            effect = effects.pop(0)
            if isinstance(effect, Exception):
                raise effect
            return effect
        self.ns['command'] = command
        return self.ns['send_packet'](self.payload, deadline)

    def rejected(self, started=False, response=b'+CME ERROR: operation not supported'):
        return self.error('send', response, started)

    def test_pre_prompt_error_then_success_preserves_payload(self):
        self.assertEqual(self.run_send([self.rejected(), b'OK']), b'OK')
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.now, 2)
        self.assertTrue(all(call[2] is self.payload for call in self.calls))

    def test_retry_limit(self):
        with self.assertRaises(self.error):
            self.run_send([self.rejected() for _ in range(4)])
        self.assertEqual(len(self.calls), 4)
        self.assertEqual(self.now, 6)

    def test_never_retry_after_payload(self):
        with self.assertRaises(self.error):
            self.run_send([self.rejected(started=True)])
        self.assertEqual(len(self.calls), 1)

    def test_never_retry_other_error(self):
        with self.assertRaises(self.error):
            self.run_send([self.rejected(response=b'ERROR')])
        self.assertEqual(len(self.calls), 1)

    def test_never_retry_pending_command(self):
        with self.assertRaises(TimeoutError):
            self.run_send([TimeoutError('pending')])
        self.assertEqual(len(self.calls), 1)

    def test_deadline_during_backoff_prevents_next_command(self):
        with self.assertRaises(TimeoutError):
            self.run_send([self.rejected()], deadline=1)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.now, 1)


if __name__ == '__main__':
    unittest.main()
