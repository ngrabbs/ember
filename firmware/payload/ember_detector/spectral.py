"""Baseline spectral excess detector. No acquisition or transport dependencies."""
import cv2
import numpy as np
from .model import Decision, Result, Scene


class SpectralExcess:
    algorithm_id = 'spectral_excess_v1'

    @staticmethod
    def validate(settings):
        from .pipeline import bounded
        if set(settings)!={'continuum_min','k_threshold','excess_min','min_area_px','connectivity','min_valid_fraction','max_saturated_fraction'}:
            raise ValueError('Spectral detector settings')
        for key in ('continuum_min','k_threshold','excess_min'):bounded(settings[key],.000001 if key=='continuum_min' else 0,1e9,key)
        bounded(settings['min_area_px'],1,2000000,'min_area_px',True)
        bounded(settings['connectivity'],4,8,'connectivity',True)
        if settings['connectivity'] not in (4,8):raise ValueError('Connectivity')
        bounded(settings['min_valid_fraction'],.000001,1,'min_valid_fraction')
        bounded(settings['max_saturated_fraction'],0,1,'max_saturated_fraction')

    def detect(self, scene: Scene, settings: dict) -> Result:
        lo, on, hi = scene.wavelengths
        weight = (on-lo)/(hi-lo)
        continuum = (1-weight)*scene.low + weight*scene.high
        excess = scene.on - continuum
        valid = scene.valid & np.isfinite(continuum) & np.isfinite(excess)
        valid &= continuum >= settings['continuum_min']
        k = np.full(continuum.shape, np.nan, dtype=np.float32)
        np.divide(excess, continuum, out=k, where=valid)
        metrics = dict(valid_fraction=float(valid.sum()/max(1,scene.evaluation_pixels or valid.size)), saturated_fraction=scene.saturated_fraction,
                       interpolation_weight=weight)
        maps = dict(k=k, valid=valid)
        if metrics['valid_fraction'] < settings['min_valid_fraction']:
            return Result(Decision.UNKNOWN, 'INSUFFICIENT_VALID_SIGNAL', metrics, maps=maps)
        candidates = valid & (k >= settings['k_threshold']) & (excess >= settings['excess_min'])
        count, labels, stats, _ = cv2.connectedComponentsWithStats(candidates.astype('uint8'),
                                                                 connectivity=settings['connectivity'])
        regions = []
        for label in range(1, count):
            x,y,w,h,area = map(int,stats[label])
            if area < settings['min_area_px']:continue
            mask = labels == label
            regions.append(dict(area_px=area,bbox=[x,y,w,h],peak_k=float(k[mask].max()),
                                median_k=float(np.median(k[mask])),mean_excess=float(excess[mask].mean())))
        regions.sort(key=lambda r:r['area_px'],reverse=True)
        metrics.update(candidate_pixels=int(candidates.sum()), region_count=len(regions))
        maps['candidates'] = candidates
        if scene.saturated_fraction > settings['max_saturated_fraction']:
            return Result(Decision.UNKNOWN,'EXCESSIVE_CLIPPING',metrics,regions[:32],maps)
        if regions:return Result(Decision.FIRE,'SPECTRAL_REGION',metrics,regions[:32],maps)
        return Result(Decision.NO_FIRE,'NO_QUALIFYING_REGION',metrics,maps=maps)
