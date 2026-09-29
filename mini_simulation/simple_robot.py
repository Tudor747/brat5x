"""Intentionally simplified top-view arm geometry."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SimpleRobotGeometry:
    retracted_reach_mm: float = 90.0
    extended_reach_mm: float = 350.0
    lateral_bend_mm: float = 85.0

    def points(self, carriage_x_mm: float, extension: float) -> tuple[list[float], list[float]]:
        """Return base/elbow/tool polyline for extension in [0, 1]."""
        amount = min(1.0, max(0.0, extension))
        reach = self.retracted_reach_mm + amount * (self.extended_reach_mm - self.retracted_reach_mm)
        elbow_x = carriage_x_mm + math.sin(amount * math.pi) * self.lateral_bend_mm
        return [carriage_x_mm, elbow_x, carriage_x_mm], [0.0, reach * 0.52, reach]
