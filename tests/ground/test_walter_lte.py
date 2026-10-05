"""Mock modem behavior; never represents RF or hardware qualification."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ground/ember'))
from generate_c import generate
class WalterLTE(unittest.TestCase):
    def test_bounded_window_prompt_outcomes_and_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);generate(path/'wire.h')
            subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror',
                            '-I'+str(path),'-I'+str(ROOT/'test/firmware/walter_mocks'),
                            '-I'+str(ROOT/'firmware/comms_transport'),
                            str(ROOT/'test/firmware/walter_lte_test.cpp'),'-o',str(path/'test')],check=True)
            subprocess.run([str(path/'test')],check=True)
