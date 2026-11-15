"""Jacob pixelwise brightness excess."""
import numpy as np
from .scoring import ScoreDetector, THRESHOLD


class JacobP(ScoreDetector):
    algorithm_id = 'jacob_p_v1'
    requires_native = False
    defaults = dict(continuum_min=4., percentile=99., score_threshold=None)
    bounds = dict(continuum_min=(1e-6, 65535, False), percentile=(0, 100, False), score_threshold=THRESHOLD)

    def detect(self, scene, settings):
        low, on, high = scene.aligned_signals
        continuum = (low + 2 * high) / 3
        valid = scene.valid & (continuum >= settings['continuum_min'])
        if not valid.any():
            return self.result(None, settings['score_threshold'])
        values = (on[valid] - continuum[valid]) / continuum[valid]
        score = float(np.percentile(values, settings['percentile']))
        return self.result(score, settings['score_threshold'], dict(valid_pixels=int(valid.sum())))
