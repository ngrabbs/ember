"""Real worker lifecycle, binary decisions and enforced timeout on tiny scenes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'firmware/payload'))
try:
    import numpy as np
    import cv2
except ImportError:
    raise unittest.SkipTest('Requires detector dependencies')
from live_analysis import AnalysisWorker


class LiveWorkerTests(unittest.TestCase):
    def test_reused_worker_binary_outputs_and_killed_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calibration = root/'calibration.npz'
            np.savez(calibration, **{'gain_'+str(i): np.ones((32,32), dtype='float32') for i in range(3)})
            config = json.loads((ROOT/'firmware/payload/config/stored-images.json').read_text())
            config['registration']['mode'] = 'prealigned'  # Synthetic matching grids only.
            config['calibration_sha256'] = hashlib.sha256(calibration.read_bytes()).hexdigest()
            profile = root/'config.json'; profile.write_text(json.dumps(config))
            worker = AnalysisWorker()
            try:
                pid = worker.process.pid
                for number, expected in enumerate(('NO_FIRE', 'FIRE')):
                    case = root/str(number); case.mkdir()
                    captures = []
                    for port, wave in enumerate((750,770,780)):
                        array = np.full((32,32), 100, dtype='uint8')
                        if number and port == 1: array[10:18,10:18] = 240
                        path = case/f'{port}.jpg'; cv2.imwrite(str(path), array)
                        captures.append(dict(id=path.name, bytes=path.stat().st_size, port=port, wavelength_nm=wave))
                    settings = dict(shared=dict(AeEnable=False, ExposureTime=100), per_camera={},
                                    rotations={}, wavelengths={str(i): w for i,w in enumerate((750,770,780))})
                    (case/'job.json').write_text(json.dumps(dict(captures=captures, settings=settings,
                        origin=11, request=number+1, config=str(profile), calibration=str(calibration))))
                    worker.run(case, 5)
                    self.assertEqual(json.loads((case/'result.json').read_text())['result'], expected)
                    self.assertEqual(worker.process.pid, pid)
                with self.assertRaises(TimeoutError): worker.run(case, 0)
                self.assertIsNone(worker.process)
                worker.ensure_started()
                worker.run(case, 5)
                self.assertEqual(json.loads((case/'result.json').read_text())['result'], 'FIRE')
            finally:
                worker.stop()
