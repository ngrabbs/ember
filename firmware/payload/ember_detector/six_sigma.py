"""770/780 ratio with a scene-relative sigma cutoff."""
import numpy as np
from .scoring import ScoreDetector


class SixSigma(ScoreDetector):
    algorithm_id = 'six_sigma_v1'
    requires_native = False
    defaults = dict(sigma=6., denominator_min=0., min_hits=None)
    bounds = dict(sigma=(0, 100, False), denominator_min=(0, 65535, False), min_hits=(1, 20000000, True))

    def detect(self, scene, settings):
        _, on, high = scene.aligned_signals
        valid = scene.valid & (high > 0) & (high >= settings['denominator_min'])
        if not valid.any():
            return self.result(None, settings['min_hits'])
        values = on[valid].astype(np.float64) / high[valid]
        cutoff = float(values.mean() + settings['sigma'] * values.std())
        candidates = np.zeros_like(valid)
        candidates[valid] = values >= cutoff
        return self.result(int(candidates.sum()), settings['min_hits'],
                           dict(ratio_cutoff=cutoff, valid_pixels=int(valid.sum())), dict(candidates=candidates))
