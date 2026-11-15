"""Jacob integrated brightness in native camera regions."""
from .jacob_i import JacobI
from .scoring import integrated, net_brightness


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
