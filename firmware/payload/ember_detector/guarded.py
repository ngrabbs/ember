"""Conservative spectral variant for bounded local registration uncertainty."""
import cv2
import numpy as np
from .model import Scene
from .spectral import SpectralExcess


class GuardedSpectral(SpectralExcess):
    algorithm_id='spectral_guarded_v1'

    @staticmethod
    def validate(settings):
        from .pipeline import bounded
        copy=dict(settings)
        radius=copy.pop('alignment_guard_px',None)
        bounded(radius,0,5,'alignment_guard_px',True)
        SpectralExcess.validate(copy)

    def detect(self,scene,settings):
        radius=settings['alignment_guard_px']
        kernel=np.ones((2*radius+1,2*radius+1),dtype='uint8')
        # Test against the strongest nearby reference continuum, rather than
        # declaring a displaced background edge to be on-line emission.
        guarded=Scene(cv2.dilate(scene.low,kernel),scene.on,cv2.dilate(scene.high,kernel),
                      cv2.erode(scene.valid.astype('uint8'),kernel,borderType=cv2.BORDER_CONSTANT,borderValue=0)>0,
                      scene.wavelengths,scene.saturated_fraction,scene.evaluation_pixels)
        result=super().detect(guarded,settings)
        result.metrics['alignment_guard_px']=radius
        return result
