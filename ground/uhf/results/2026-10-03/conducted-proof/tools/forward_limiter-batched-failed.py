"""Phase-preserving amplitude bound for the optional transponder branch."""
import threading
import numpy as np

FORWARD_PEAK = .25


def limit_iq(samples, output, peak=FORWARD_PEAK):
    """Keep weak samples unchanged; scale large samples without changing phase."""
    if not np.isfinite(samples).all():
        raise ValueError('Nonfinite forwarded IQ')
    magnitude = np.abs(samples)
    maximum = float(magnitude.max(initial=0))
    clipped = int(np.count_nonzero(magnitude > peak))
    np.multiply(samples, peak / np.maximum(magnitude, peak), out=output)
    return maximum, clipped


def make_limiter():
    from gnuradio import gr

    class ForwardLimiter(gr.sync_block):
        def __init__(self):
            gr.sync_block.__init__(self, 'Forwarded IQ amplitude bound',
                                   in_sig=[np.complex64], out_sig=[np.complex64])
            # Avoid per-sample Python/GIL overhead when the adder's other
            # input is a pipe. This also bounds NumPy call frequency at600/s.
            self.set_output_multiple(1024)
            self.lock = threading.Lock()
            self.samples = self.clipped = 0
            self.maximum = 0.0
            self.error = None

        def work(self, inputs, outputs):
            try:
                maximum, clipped = limit_iq(inputs[0], outputs[0])
            except Exception as exc:
                outputs[0].fill(0)
                with self.lock:
                    self.error = str(exc)
                return len(outputs[0])
            with self.lock:
                self.samples += len(outputs[0])
                self.clipped += clipped
                self.maximum = max(self.maximum, maximum)
            return len(outputs[0])

        def snapshot(self):
            with self.lock:
                return dict(samples=self.samples, clipped_samples=self.clipped,
                            peak_before=self.maximum,
                            peak_after=min(self.maximum, FORWARD_PEAK),
                            limit=FORWARD_PEAK, error=self.error)

    return ForwardLimiter()
