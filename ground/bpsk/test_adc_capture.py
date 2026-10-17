import unittest
import numpy as np
from adc_capture import analytic_adc, parse_capture
from modem import decode, frame
from codec import encode


class AdcTests(unittest.TestCase):
    def test_real_if_packet(self):
        packet = encode('HEARTBEAT', sequence=901, source=3, target=1,
                        source_boot_id=123, uptime_ms=456,
                        payload=dict(mode=2, configuration=1, telemetry_period_ms=0))
        bits = np.unpackbits(np.frombuffer(frame(packet, 901), np.uint8))
        symbols = 1-2*(np.cumsum(bits) % 2).astype(float)
        base = np.r_[np.zeros(4800), np.repeat(symbols, 40), np.zeros(4800)]
        for carrier in (1000, 1391, 1700):
            with self.subTest(carrier=carrier):
                t = np.arange(len(base))/48000
                real = base*np.cos(2*np.pi*carrier*t+0.7)
                # Model the nominal equal-R/C unity-gain Sallen-Key LPF.
                freq = np.fft.fftfreq(len(real), 1/48000)
                real = np.fft.ifft(np.fft.fft(real)/(1+1j*freq/3288.3)**2).real
                a = real[::6]*30+2080
                a += np.random.default_rng(7).normal(0, 0.8, len(a))
                a = np.rint(a)
                self.assertEqual([p['hex'] for p in decode(analytic_adc(a))], [packet.hex()])
    def test_noise_rejected(self):
        a = 2080+np.random.default_rng(3).normal(0, 1, 32768)
        self.assertEqual(decode(analytic_adc(a)), [])
    def test_capture_integrity(self):
        text = ('[rx_test] lo=1 complete=1 shutdown_verified=1 status=11 TX=0 RX=0\n'
                '[rx_adc] n=4096 interval_us=125 elapsed_us=511879 late_gt10us=0 '
                'min=2080 max=2080 sum=8519680 hex='+'820'*4096+'\n')
        self.assertEqual(len(parse_capture(text)), 4096)
        for old, new in [('shutdown_verified=1', 'shutdown_verified=0'),
                         ('late_gt10us=0', 'late_gt10us=1'),
                         ('511879', '600000'), ('8519680', '8519681'),
                         ('n=4096', 'n=4095')]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                parse_capture(text.replace(old, new))
        with self.assertRaises(ValueError):
            parse_capture(text+text)


if __name__ == '__main__':
    unittest.main()
