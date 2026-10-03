"""FIFO recovery policy boundary tests; these do not qualify RF delivery."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
class LTEQueue(unittest.TestCase):
    def test_backoff_retention_expiry_uncertainty_and_timer_wrap(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',
                            '-fsanitize=address,undefined',
                            '-I'+str(ROOT/'firmware/comms_transport'),
                            str(ROOT/'test/firmware/lte_queue_test.c'),'-o',str(target)],check=True)
            subprocess.run([str(target)],check=True)
