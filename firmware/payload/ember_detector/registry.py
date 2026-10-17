"""Explicit registry. Add a detector here; acquisition and CAN stay unchanged."""
from .spectral import SpectralExcess
from .guarded import GuardedSpectral

_FACTORIES = {'spectral_excess_v1': SpectralExcess, 'spectral_guarded_v1': GuardedSpectral}


def register(name, factory):
    if not name or name in _FACTORIES:raise ValueError('Detector ID empty/already registered')
    _FACTORIES[name] = factory


def create(name):
    if name not in _FACTORIES:raise ValueError('Unknown detector: '+str(name))
    detector = _FACTORIES[name]()
    if detector.algorithm_id != name:raise ValueError('Detector ID mismatch')
    return detector
