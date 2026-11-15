"""Explicit registry. Add a detector here; acquisition and CAN stay unchanged."""
from .spectral import SpectralExcess
from .guarded import GuardedSpectral
from .six_sigma import SixSigma
from .jacob_p import JacobP
from .jacob_i import JacobI
from .jacob_i_native import JacobINative
from .jacob_gross import JacobGross
from .koenig import Koenig

_FACTORIES = {'spectral_excess_v1': SpectralExcess, 'spectral_guarded_v1': GuardedSpectral}

for detector in (SixSigma, JacobP, JacobI, JacobINative, JacobGross, Koenig):
    _FACTORIES[detector.algorithm_id] = detector


def register(name, factory):
    if not name or name in _FACTORIES:raise ValueError('Detector ID empty/already registered')
    _FACTORIES[name] = factory


def create(name):
    if name not in _FACTORIES:raise ValueError('Unknown detector: '+str(name))
    detector = _FACTORIES[name]()
    if detector.algorithm_id != name:raise ValueError('Detector ID mismatch')
    return detector
