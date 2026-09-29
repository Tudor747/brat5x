"""Configured six-axis robot model."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Sequence
import numpy as np
from numpy.typing import NDArray

from robot.joint import Joint, JointType


@dataclass(frozen=True)
class JointKinematicSpec:
    """Fixed transform before a rotary joint and fixed link after it."""

    joint_name: str
    axis: str
    pre_translation_mm: tuple[float, float, float]
    pre_rpy_rad: tuple[float, float, float]
    post_translation_mm: tuple[float, float, float]
    post_rpy_rad: tuple[float, float, float]

    def __post_init__(self) -> None:
        if self.axis.lower() not in {"x", "y", "z"}:
            raise ValueError(f"unsupported axis {self.axis!r}")


@dataclass
class RobotModel:
    """Mechanical joint state and configured frame chain."""

    name: str
    joints: list[Joint]
    kinematic_chain: list[JointKinematicSpec]
    tcp_translation_mm: tuple[float, float, float]
    tcp_rpy_rad: tuple[float, float, float]
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.joints) != 6:
            raise ValueError("this prototype requires exactly six axes J0-J5")
        if self.joints[0].joint_type is not JointType.PRISMATIC:
            raise ValueError("J0 must be prismatic")
        if any(j.joint_type is not JointType.REVOLUTE for j in self.joints[1:]):
            raise ValueError("J1-J5 must be revolute")
        expected = [joint.name for joint in self.joints[1:]]
        actual = [spec.joint_name for spec in self.kinematic_chain]
        if actual != expected:
            raise ValueError(f"kinematic chain order {actual} does not match joints {expected}")

    @property
    def q(self) -> NDArray[np.float64]:
        return np.asarray([joint.current_position for joint in self.joints], dtype=float)

    @property
    def home_q(self) -> NDArray[np.float64]:
        return np.asarray([joint.home_position for joint in self.joints], dtype=float)

    def validate_joint_positions(self, positions: Sequence[float]) -> None:
        if len(positions) != len(self.joints):
            raise ValueError(f"expected {len(self.joints)} positions, got {len(positions)}")
        for joint, position in zip(self.joints, positions, strict=True):
            joint.validate_position(float(position))

    def set_joint_positions(self, positions: Sequence[float]) -> None:
        self.validate_joint_positions(positions)
        for joint, position in zip(self.joints, positions, strict=True):
            joint.current_position = float(position)
