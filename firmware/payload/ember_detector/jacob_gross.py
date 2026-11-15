"""Jacob whole-frame brightness sums."""
import numpy as np
from .scoring import ScoreDetector, THRESHOLD, integrated


class JacobGross(ScoreDetector):
    algorithm_id = 'jacob_gross_v1'
    requires_native = True
    defaults = dict(score_threshold=None)
    bounds = dict(score_threshold=THRESHOLD)

    def detect(self, scene, settings):
        if scene.native_clipped:
            return self.result(None, settings['score_threshold'])
        return integrated(self, [float(a.sum(dtype=np.float64)) for a in scene.native_signals],
                          settings['score_threshold'])
