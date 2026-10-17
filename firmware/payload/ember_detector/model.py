"""The detector boundary: prepared arrays in, decision and evidence out."""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Protocol
import numpy as np


class Decision(IntEnum):
    NO_FIRE = 0
    FIRE = 1
    UNKNOWN = 2


@dataclass
class Scene:
    low: np.ndarray
    on: np.ndarray
    high: np.ndarray
    valid: np.ndarray
    wavelengths: tuple[float, float, float]
    saturated_fraction: float = 0.0
    evaluation_pixels: int | None = None


@dataclass
class Result:
    decision: Decision
    reason: str
    metrics: dict = field(default_factory=dict)
    regions: list = field(default_factory=list)
    maps: dict = field(default_factory=dict, repr=False)


class Detector(Protocol):
    """An implementation must not load files, select fixtures, or touch CAN."""
    algorithm_id: str
    def validate(self, settings: dict) -> None: ...
    def detect(self, scene: Scene, settings: dict) -> Result: ...
