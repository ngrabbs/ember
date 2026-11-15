"""Development score producers with explicit, opt-in decision thresholds."""
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


def net_brightness(image, valid, source, background):
    windows = []
    for x0, y0, x1, y1 in (source, background):
        sl = np.s_[y0:y1, x0:x1]
        if x1 > image.shape[1] or y1 > image.shape[0] or not valid[sl].all():
            return None
        windows.append(sl)
    src, bg = windows
    return float(image[src].sum(dtype=np.float64) - image[src].size * image[bg].mean(dtype=np.float64))


class JacobINative(JacobI):
    algorithm_id = 'jacob_i_native_v1'
    requires_native = True

    def validate(self, settings):
        if settings.keys() != self.defaults.keys():
            raise ValueError('Detector settings do not match profile')
        source, background = settings['source'], settings['background']
        if source is None and background is None:
            return super().validate(settings)
        if not all(isinstance(boxes, list) and len(boxes) == 3 for boxes in (source, background)):
            raise ValueError('Expected three native rectangles per setting in wavelength order')
        for a, b in zip(source, background):
            if a is None or b is None:
                raise ValueError('Native rectangles must be configured for all bands')
            super().validate(dict(settings, source=a, background=b))

    def detect(self, scene, settings):
        if settings['source'] is None:
            return self.result(None, settings['score_threshold'])
        sums = [net_brightness(image, valid, src, bg)
                for image, valid, src, bg in zip(scene.native_signals, scene.native_valid,
                                                settings['source'], settings['background'])]
        if any(value is None for value in sums):
            return self.result(None, settings['score_threshold'])
        return integrated(self, sums, settings['score_threshold'])


def integrated(detector, sums, threshold):
    low, on, high = sums
    continuum = (low + 2 * high) / 3
    score = (on - continuum) / continuum if continuum > 0 else None
    return detector.result(score, threshold, dict(band_sums=sums, continuum=continuum))


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


class Koenig(JacobGross):
    algorithm_id = 'koenig_cutoff_v1'
    defaults = dict(cutoff_dn=16, score_threshold=None)
    bounds = dict(cutoff_dn=(0, 65535, True), score_threshold=THRESHOLD)

    def detect(self, scene, settings):
        cutoff = settings['cutoff_dn']
        sums = [float(a[a >= cutoff].sum(dtype=np.float64)) for a in scene.native_signals]
        return integrated(self, sums, settings['score_threshold'])
