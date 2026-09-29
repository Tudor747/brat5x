"""NumPy homogeneous-transform primitives."""

from __future__ import annotations

import math
import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]


def translation_x(distance: float) -> FloatArray:
    return translation(distance, 0.0, 0.0)


def translation_y(distance: float) -> FloatArray:
    return translation(0.0, distance, 0.0)


def translation_z(distance: float) -> FloatArray:
    return translation(0.0, 0.0, distance)


def translation(x: float, y: float, z: float) -> FloatArray:
    matrix = np.eye(4, dtype=float)
    matrix[:3, 3] = (x, y, z)
    return matrix


def rotation_x(angle_rad: float) -> FloatArray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    matrix = np.eye(4, dtype=float)
    matrix[:3, :3] = ((1, 0, 0), (0, c, -s), (0, s, c))
    return matrix


def rotation_y(angle_rad: float) -> FloatArray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    matrix = np.eye(4, dtype=float)
    matrix[:3, :3] = ((c, 0, s), (0, 1, 0), (-s, 0, c))
    return matrix


def rotation_z(angle_rad: float) -> FloatArray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    matrix = np.eye(4, dtype=float)
    matrix[:3, :3] = ((c, -s, 0), (s, c, 0), (0, 0, 1))
    return matrix


def rpy_transform(roll: float, pitch: float, yaw: float) -> FloatArray:
    """Intrinsic XYZ RPY, represented as Rz(yaw) @ Ry(pitch) @ Rx(roll)."""
    return rotation_z(yaw) @ rotation_y(pitch) @ rotation_x(roll)


def homogeneous_transform(rotation: ArrayLike, position: ArrayLike) -> FloatArray:
    rotation_array = np.asarray(rotation, dtype=float)
    position_array = np.asarray(position, dtype=float)
    if rotation_array.shape == (4, 4):
        rotation_array = rotation_array[:3, :3]
    if rotation_array.shape != (3, 3) or position_array.shape != (3,):
        raise ValueError("rotation must be 3x3 and position must have length 3")
    matrix = np.eye(4, dtype=float)
    matrix[:3, :3] = rotation_array
    matrix[:3, 3] = position_array
    return matrix


def transform_point(transform: ArrayLike, point: ArrayLike) -> FloatArray:
    transform_array = np.asarray(transform, dtype=float)
    point_array = np.asarray(point, dtype=float)
    if transform_array.shape != (4, 4) or point_array.shape != (3,):
        raise ValueError("transform must be 4x4 and point must have length 3")
    homogeneous_point = np.append(point_array, 1.0)
    return (transform_array @ homogeneous_point)[:3]


def axis_rotation(axis: str, angle_rad: float) -> FloatArray:
    rotations = {"x": rotation_x, "y": rotation_y, "z": rotation_z}
    try:
        return rotations[axis.lower()](angle_rad)
    except KeyError as exc:
        raise ValueError(f"unsupported rotation axis {axis!r}") from exc


def fixed_transform(translation_mm: ArrayLike, rpy_rad: ArrayLike) -> FloatArray:
    xyz = np.asarray(translation_mm, dtype=float)
    rpy = np.asarray(rpy_rad, dtype=float)
    if xyz.shape != (3,) or rpy.shape != (3,):
        raise ValueError("translation and RPY must each contain three values")
    result = rpy_transform(*rpy)
    result[:3, 3] = xyz
    return result
