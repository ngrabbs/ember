"""Integration against the pinned upstream FreeRTOS POSIX scheduler (optional path)."""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ground/ember'))
from generate_c import generate
KERNEL=os.environ.get('EMBER_FREERTOS_KERNEL_PATH')

@unittest.skipUnless(KERNEL,'set EMBER_FREERTOS_KERNEL_PATH to pinned FreeRTOS V11.2.0 source')
class RuntimeSchedulerTests(unittest.TestCase):
    def test_workers_controls_and_watchdog(self):
        kernel=pathlib.Path(KERNEL)
        version=(kernel/'include/task.h').read_text()
        self.assertIn('"V11.2.0"',version)
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)
            for name in ['pico/stdlib.h','pico/stdio_usb.h','pico/unique_id.h','pico/rand.h',
                         'hardware/i2c.h','hardware/watchdog.h','hardware/structs/watchdog.h']:
                h=p/name;h.parent.mkdir(parents=True,exist_ok=True)
                h.write_text('#include "'+str(ROOT/'firmware/ihu/tests/pico_mock.h')+'"\n')
            (p/'build_identity.h').write_text('#define FW_VERSION "0.15.0"\n#define FW_MAJOR 0\n#define FW_MINOR 15\n#define FW_PATCH 0\n#define FW_DIRTY 0\n#define FW_GIT "0123456789012345678901234567890123456789"\n')
            generate(p/'wire.h')
            port=kernel/'portable/ThirdParty/GCC/Posix'
            binary=p/'scheduler-test'
            command=['cc','-std=c11','-D_GNU_SOURCE','-pthread','-g','-Wall','-Wextra',
                     '-I'+str(p),'-I'+str(ROOT/'firmware/ihu'),'-I'+str(ROOT/'firmware/comms_transport'),
                     '-I'+str(kernel/'include'),'-I'+str(port),
                     str(ROOT/'firmware/ihu/tests/runtime_harness.c'),str(ROOT/'firmware/ihu/app.c'),
                     str(ROOT/'firmware/shared/ember_protocol/protocol.c'),
                     *[str(kernel/name) for name in ['tasks.c','queue.c','list.c','timers.c','event_groups.c']],
                     str(port/'port.c'),str(port/'utils/wait_for_event.c'),'-o',str(binary)]
            built=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            completed=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
            self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr)
            self.assertIn('PASS: actual FreeRTOS scheduler',completed.stdout)
            # A stuck sensor must not be disguised by independent task heartbeats.
            stalled=subprocess.run([str(binary),'stall'],capture_output=True,text=True,timeout=8)
            self.assertEqual(stalled.returncode,106,stalled.stdout+stalled.stderr)
