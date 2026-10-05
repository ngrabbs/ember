"""Native timer policy checks; hardware readout and delivery are separate gates."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]

class AutoTelemetry(unittest.TestCase):
    def test_cadence_busy_disable_and_clock_wrap(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',
                            '-fsanitize=address,undefined',
                            '-I'+str(ROOT/'firmware/can_feather_bench'),
                            str(ROOT/'test/firmware/autotelem_test.c'),'-o',str(target)],check=True)
            subprocess.run([str(target)],check=True)

if __name__=='__main__':unittest.main()
