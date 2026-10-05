"""Exercise the actual native blocks for weak-signal transparency and headroom."""
import unittest
import numpy as np
from gnuradio import blocks,gr
from forward_limiter import make_limiter,FORWARD_PEAK,COMPONENT_PEAK

class LimiterTests(unittest.TestCase):
    def test_native_headroom_and_weak_signal(self):
        samples=np.array([0j,.01+.02j,.1j,1+1j,-2j],np.complex64)
        flow=gr.top_block();source=blocks.vector_source_c(samples.tolist(),False)
        limiter=make_limiter();sink=blocks.vector_sink_c()
        flow.connect(source,limiter,sink);flow.run()
        result=np.array(sink.data(),np.complex64)
        # Native rail arithmetic can round a few float32 least-significant bits.
        np.testing.assert_allclose(result[:3],samples[:3],rtol=1e-6,atol=1e-8)
        np.testing.assert_allclose(result[3:],[COMPONENT_PEAK*(1+1j),-COMPONENT_PEAK*1j],rtol=1e-6,atol=1e-8)
        self.assertLessEqual(float(np.abs(result).max()),FORWARD_PEAK+1e-7)
        self.assertEqual(limiter.snapshot()['samples'],len(samples))
        self.assertLess(FORWARD_PEAK+.15,1)

if __name__=='__main__':unittest.main()
