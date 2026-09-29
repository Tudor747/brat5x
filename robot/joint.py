"""Joint representation independent of geometric kinematics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from robot.limits import JointLimits


class JointType(str, Enum):
    REVOLUTE = "revolute"
    PRISMATIC = "prismatic"


@dataclass
class Joint:
    """A commanded axis.

    Revolute positions are radians; prismatic positions are millimetres.
    Motor fields are metadata only and are deliberately unused by FK.
    """

    name: str
    joint_type: JointType
    limits: JointLimits
    current_position: float = 0.0
    home_position: float = 0.0
    gear_ratio: float | None = None
    steps_per_revolution: int | None = None
    microstepping: int | None = None

    def __post_init__(self) -> None:
        self.limits.validate(self.home_position, self.name)
        self.limits.validate(self.current_position, self.name)
        if self.gear_ratio is not None and self.gear_ratio <= 0:
            raise ValueError(f"{self.name} gear_ratio must be positive")
        if self.steps_per_revolution is not None and self.steps_per_revolution <= 0:
            raise ValueError(f"{self.name} steps_per_revolution must be positive")
        if self.microstepping is not None and self.microstepping <= 0:
            raise ValueError(f"{self.name} microstepping must be positive")

    def validate_position(self, position: float) -> None:
        self.limits.validate(float(position), self.name)

    def set_position(self, position: float) -> None:
        self.validate_position(position)
        self.current_position = float(position)

    @property
    def current_degrees(self) -> float:
        if self.joint_type is not JointType.REVOLUTE:
            raise TypeError("degree conversion is only valid for revolute joints")
        return math.degrees(self.current_position)

    def set_degrees(self, degrees: float) -> None:
        if self.joint_type is not JointType.REVOLUTE:
            raise TypeError("degree conversion is only valid for revolute joints")
        self.set_position(math.radians(degrees))
