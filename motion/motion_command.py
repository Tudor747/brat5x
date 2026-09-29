"""Future-facing MOVEJ/MOVEL command vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from robot.pose import Pose


class MotionType(str, Enum):
    MOVEJ = "MOVEJ"
    MOVEL = "MOVEL"


@dataclass(frozen=True)
class MoveJCommand:
    target: tuple[float, float, float, float, float, float]
    speed_scale: float = 1.0
    motion_type: MotionType = MotionType.MOVEJ

    def __post_init__(self) -> None:
        if not 0.0 < self.speed_scale <= 1.0:
            raise ValueError("speed_scale must be in (0, 1]")


@dataclass(frozen=True)
class MoveLCommand:
    """Declaration only; execution requires IK and Cartesian planning."""

    target: Pose
    speed_mm_s: float
    motion_type: MotionType = MotionType.MOVEL
