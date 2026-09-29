"""Cartesian pose representation."""

from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class Pose:
    """Position in millimetres and orientation as a 3x3 rotation matrix."""

    position: FloatArray
    rotation: FloatArray

    def __post_init__(self) -> None:
        position = np.asarray(self.position, dtype=float)
        rotation = np.asarray(self.rotation, dtype=float)
        if position.shape != (3,):
            raise ValueError("position must have shape (3,)")
        if rotation.shape != (3, 3):
            raise ValueError("rotation must have shape (3, 3)")
        if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-7):
            raise ValueError("rotation must be orthonormal")
        if not np.isclose(np.linalg.det(rotation), 1.0, atol=1e-7):
            raise ValueError("rotation determinant must be +1")
        object.__setattr__(self, "position", position)
        object.__setattr__(self, "rotation", rotation)

    @property
    def x(self) -> float:
        return float(self.position[0])

    @property
    def y(self) -> float:
        return float(self.position[1])

    @property
    def z(self) -> float:
        return float(self.position[2])

    @classmethod
    def from_transform(cls, transform: FloatArray) -> "Pose":
        matrix = np.asarray(transform, dtype=float)
        if matrix.shape != (4, 4):
            raise ValueError("homogeneous transform must have shape (4, 4)")
        return cls(matrix[:3, 3].copy(), matrix[:3, :3].copy())

    def as_transform(self) -> FloatArray:
        transform = np.eye(4, dtype=float)
        transform[:3, :3] = self.rotation
        transform[:3, 3] = self.position
        return transform

    def as_rpy(self) -> tuple[float, float, float]:
        """Return intrinsic XYZ roll, pitch, yaw angles in radians."""
        pitch = math.atan2(-self.rotation[2, 0], math.hypot(self.rotation[0, 0], self.rotation[1, 0]))
        if abs(math.cos(pitch)) > 1e-9:
            roll = math.atan2(self.rotation[2, 1], self.rotation[2, 2])
            yaw = math.atan2(self.rotation[1, 0], self.rotation[0, 0])
        else:
            roll = math.atan2(-self.rotation[1, 2], self.rotation[1, 1])
            yaw = 0.0
        return roll, pitch, yaw
