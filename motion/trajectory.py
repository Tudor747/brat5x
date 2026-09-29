"""Minimal joint-space trajectory infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class JointTrajectory:
    samples: NDArray[np.float64]

    @classmethod
    def linear(cls, start: NDArray[np.float64], end: NDArray[np.float64], sample_count: int) -> "JointTrajectory":
        if sample_count < 2:
            raise ValueError("sample_count must be at least 2")
        if np.asarray(start).shape != np.asarray(end).shape:
            raise ValueError("trajectory endpoints must have matching shapes")
        return cls(np.linspace(start, end, sample_count))
