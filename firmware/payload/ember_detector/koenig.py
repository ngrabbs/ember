"""Koenig whole-frame brightness above a histogram cutoff."""
import numpy as np
from .scoring import ScoreDetector, THRESHOLD, integrated


class Koenig(ScoreDetector):
    algorithm_id = 'koenig_cutoff_v1'
    requires_native = True
    defaults = dict(cutoff_dn=16, score_threshold=None)
    bounds = dict(cutoff_dn=(0, 65535, True), score_threshold=THRESHOLD)

    def detect(self, scene, settings):
        cutoff = settings['cutoff_dn']
        sums = [float(a[a >= cutoff].sum(dtype=np.float64)) for a in scene.native_signals]
        return integrated(self, sums, settings['score_threshold'])
