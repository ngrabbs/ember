import contextlib
import io
import struct
import unittest
from unittest.mock import Mock

from codec import encode
from payload_bridge import Bridge, Console, UnknownOutcome, observed


class PayloadBridgeTests(unittest.TestCase):
    def test_startup_console_dispatches_after_internal_hello(self):
        boot = 42
        fire_reply = struct.pack('>BBBBIII', 2, 2, 2, 0, boot, 1234, 9)
        console = Console.__new__(Console)
        console.port = Mock()
        console.port.readline.side_effect = [
            b'FIRMWARE role=IHU_MCU boot=123\n',
            b'MODE configuration=GROUND_TEST mode=NOMINAL reason=UHF_STARTUP_LINK_ACTIVE\n',
            b'STATUS role=IHU_MCU can_ready=1 mode=00 uptime_ms=1234 pending=0\n',
            b'SUBMITTED request=7 type=1 bytes=0\n',
            b'RESULT request=7 outcome=CAN_HELLO_CONFIRMED peer=42 bytes=0 hex=\n',
            b'SUBMITTED request=8 type=152 bytes=0\n',
            f'RESULT request=8 outcome=PAYLOAD_FIRE_RESULT peer=42 bytes=16 hex={fire_reply.hex()}\n'.encode(),
        ]
        submitted = Mock()
        with contextlib.redirect_stdout(io.StringIO()):
            raw, peer, elapsed = console.execute('PAYLOAD_FIRE_CHECK', 32, submitted)
        self.assertEqual([call.args[0] for call in console.port.write.call_args_list],
                         [b'status\n', b'payload fire-check\n'])
        submitted.assert_called_once()
        name, fields = observed('PAYLOAD_FIRE_CHECK', raw, peer, elapsed, 1)
        self.assertEqual((name, fields['payload_version'], fields['result'], fields['execution_mode']),
                         ('PAYLOAD_FIRE_RESULT', 2, 2, 2))

    def test_serial_disconnect_exits_bridge_without_a_completion(self):
        console = Mock()
        console.execute.side_effect = OSError('USB disconnected')
        emit = Mock()
        bridge = Bridge(console, emit)
        command = encode('PAYLOAD_STATUS_QUERY', sequence=1, source=1, target=2,
                         transaction_epoch=12, transaction_id=1, source_boot_id=3,
                         uptime_ms=0, payload={})
        with self.assertRaises(OSError):
            bridge.handle(command)
        emit.assert_not_called()

    def test_legacy_fire_reply_cannot_report_unknown(self):
        raw = struct.pack('>BBBBIII', 1, 2, 2, 0, 42, 1234, 9)
        with self.assertRaises(UnknownOutcome):
            observed('PAYLOAD_FIRE_CHECK', raw, 42, 1, 1)


if __name__ == '__main__':
    unittest.main()
