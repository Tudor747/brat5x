"""Joint-limit types and errors."""

from __future__ import annotations

from dataclasses import dataclass


class JointLimitError(ValueError):
    """Raised when a joint target is outside its configured range."""


@dataclass(frozen=True)
class JointLimits:
    """Inclusive limits in the joint's internal units (mm or radians)."""

    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        if self.minimum > self.maximum:
            raise ValueError("minimum joint limit must not exceed maximum")

    def contains(self, value: float) -> bool:
        return self.minimum <= value <= self.maximum

    def validate(self, value: float, joint_name: str = "joint") -> None:
        if not self.contains(value):
            raise JointLimitError(
                f"{joint_name} target {value:.6g} is outside "
                f"[{self.minimum:.6g}, {self.maximum:.6g}]"
            )
