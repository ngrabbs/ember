"""Jacob integrated brightness on registered images."""
from .scoring import ScoreDetector, THRESHOLD, integrated, net_brightness


class JacobI(ScoreDetector):
    algorithm_id = 'jacob_i_v1'
    requires_native = False
    defaults = dict(source=None, background=None, score_threshold=None)
    bounds = dict(score_threshold=THRESHOLD)

    def detect(self, scene, settings):
        if settings['source'] is None:
            return self.result(None, settings['score_threshold'])
        sums = [net_brightness(a, scene.valid, settings['source'], settings['background'])
                for a in scene.aligned_signals]
        if any(value is None for value in sums):
            return self.result(None, settings['score_threshold'])
        return integrated(self, sums, settings['score_threshold'])
