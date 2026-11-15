"""Shared score thresholds and brightness calculations."""
import numpy as np
from .model import Decision, Result


class ScoreDetector:
    def validate(self, settings):
        from .pipeline import bounded
        if settings.keys() != self.defaults.keys():
            raise ValueError('Detector settings do not match profile')
        for key, value in settings.items():
            if key in ('source', 'background'):
                if value is not None and (not isinstance(value, list) or len(value) != 4
                                          or any(type(i) is not int or i < 0 for i in value)
                                          or value[0] >= value[2] or value[1] >= value[3]):
                    raise ValueError(f'Invalid {key} rectangle')
                continue
            if value is None and key in ('score_threshold', 'min_hits'):
                continue
            low, high, integer = self.bounds[key]
            bounded(value, low, high, key, integer)
        if 'source' in settings and (settings['source'] is None) != (settings['background'] is None):
            raise ValueError('Source and background rectangles must be configured together')
        if 'source' in settings and settings['source'] is not None:
            a, b = settings['source'], settings['background']
            if max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3]):
                raise ValueError('Integrated rectangles overlap')
        if 'source' in settings and settings['source'] is None and settings['score_threshold'] is not None:
            raise ValueError('Integrated decision requires source and background rectangles')

    @staticmethod
    def result(score, threshold, metrics=None, maps=None):
        metrics = dict(metrics or {}, score=score)
        if score is None:
            return Result(Decision.UNKNOWN, 'INSUFFICIENT_SCORE_SUPPORT', metrics, maps=maps or {})
        if threshold is None:
            return Result(Decision.UNKNOWN, 'DIAGNOSTIC_SCORE_ONLY', metrics, maps=maps or {})
        return Result(Decision.FIRE if score >= threshold else Decision.NO_FIRE,
                      'SCORE_THRESHOLD', metrics, maps=maps or {})


THRESHOLD = (-1e9, 1e9, False)


def net_brightness(image, valid, source, background):
    windows = []
    for x0, y0, x1, y1 in (source, background):
        sl = np.s_[y0:y1, x0:x1]
        if x1 > image.shape[1] or y1 > image.shape[0] or not valid[sl].all():
            return None
        windows.append(sl)
    src, bg = windows
    return float(image[src].sum(dtype=np.float64) - image[src].size * image[bg].mean(dtype=np.float64))


def integrated(detector, sums, threshold):
    low, on, high = sums
    continuum = (low + 2 * high) / 3
    score = (on - continuum) / continuum if continuum > 0 else None
    return detector.result(score, threshold, dict(band_sums=sums, continuum=continuum))
