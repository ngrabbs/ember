"""Test translated-tone measurement and fail-closed IHU cadence preflight."""
import unittest
import numpy as np
from repeater_probe import spectral_measurement
from ihu_cadence import check_status

class ProbeTests(unittest.TestCase):
    def test_tones_and_noise(self):
        rate=2000000;n=50000;rng=np.random.default_rng(4)
        for hz in (0,5000,11000):
            noise=(rng.normal(size=n)+1j*rng.normal(size=n))*.001
            iq=noise if hz==0 else noise+.05*np.exp(2j*np.pi*hz*np.arange(n)/rate)
            row=spectral_measurement(iq.astype(np.complex64),rate)
            if hz:
                self.assertLess(abs(row['tones'][str(hz)]['peak_hz']-hz),250)
                self.assertGreater(row['tones'][str(hz)]['snr_db'],40)
                other=11000 if hz==5000 else 5000
                self.assertLess(row['tones'][str(other)]['snr_db'],15)
            else:self.assertLess(max(v['snr_db'] for v in row['tones'].values()),15)
        self.assertIsNone(spectral_measurement(np.zeros(100,np.complex64),rate))
    def test_cadence_preflight_faults(self):
        status='STATUS role=IHU_MCU fw=can-bench-v2 boot=1 can_ready=1 pending=0 eflg=00 tec=0 rec=0 unknown=0 tx_fail=0 tx_timeout=0 rx_bad=0 rx_overflow=0 fragments_bad=0 fragments_timeout=0 busy_drops=0'
        baseline=check_status(status)
        for before,after in [('pending=0','pending=1'),('boot=1','boot=2'),('tx_fail=0','tx_fail=1'),('can_ready=1','can_ready=0'),('eflg=00','eflg=01')]:
            with self.assertRaises(RuntimeError):check_status(status.replace(before,after),baseline)
        self.assertEqual(check_status(status,baseline),baseline)
if __name__=='__main__':unittest.main()
