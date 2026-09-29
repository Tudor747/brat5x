"""Named, manually taught joint configurations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import math
import yaml

from robot.robot_model import RobotModel


@dataclass(frozen=True)
class TaughtPose:
    name: str
    joint_positions: tuple[float, float, float, float, float, float]

    @property
    def rail_mm(self) -> float:
        return self.joint_positions[0]

    @property
    def joints_deg(self) -> tuple[float, float, float, float, float]:
        return tuple(math.degrees(value) for value in self.joint_positions[1:])  # type: ignore[return-value]


def load_taught_poses(path: str | Path, robot: RobotModel) -> dict[str, TaughtPose]:
    with Path(path).open("r", encoding="utf-8") as stream:
        root = yaml.safe_load(stream)
    entries = root.get("taught_poses") if isinstance(root, Mapping) else None
    if not isinstance(entries, Mapping):
        raise ValueError("taught pose file requires a 'taught_poses' mapping")
    poses: dict[str, TaughtPose] = {}
    for name, item in entries.items():
        if not isinstance(item, Mapping) or not isinstance(item.get("joints_deg"), Mapping):
            raise ValueError(f"invalid taught pose {name}")
        degrees = item["joints_deg"]
        positions = (float(item["rail_mm"]),) + tuple(
            math.radians(float(degrees[joint_name])) for joint_name in ("J1", "J2", "J3", "J4", "J5")
        )
        robot.validate_joint_positions(positions)
        poses[str(name).upper()] = TaughtPose(str(name).upper(), positions)  # type: ignore[arg-type]
    return poses
