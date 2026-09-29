"""Forward kinematics for the configured rail-mounted arm."""

from __future__ import annotations

from collections.abc import Sequence
import numpy as np
from numpy.typing import NDArray

from kinematics.transforms import axis_rotation, fixed_transform, translation_x
from robot.pose import Pose
from robot.robot_model import RobotModel


class ForwardKinematics:
    """Evaluate T_world_tcp from explicit configured frame transforms."""

    def __init__(self, robot: RobotModel) -> None:
        self.robot = robot

    def transform(self, q: Sequence[float] | None = None) -> NDArray[np.float64]:
        positions = self.robot.q if q is None else np.asarray(q, dtype=float)
        self.robot.validate_joint_positions(positions)
        transform = translation_x(float(positions[0]))
        for angle, spec in zip(positions[1:], self.robot.kinematic_chain, strict=True):
            transform = (
                transform
                @ fixed_transform(spec.pre_translation_mm, spec.pre_rpy_rad)
                @ axis_rotation(spec.axis, float(angle))
                @ fixed_transform(spec.post_translation_mm, spec.post_rpy_rad)
            )
        return transform @ fixed_transform(self.robot.tcp_translation_mm, self.robot.tcp_rpy_rad)

    def pose(self, q: Sequence[float] | None = None) -> Pose:
        return Pose.from_transform(self.transform(q))
