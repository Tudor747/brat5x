"""Scene data loading and Matplotlib drawing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

from demo_sequence import DemoFrame
from simple_robot import SimpleRobotGeometry


@dataclass(frozen=True)
class PrinterVisual:
    name: str
    x_mm: float
    y_mm: float


@dataclass(frozen=True)
class SceneData:
    rail_min_mm: float
    rail_max_mm: float
    printers: tuple[PrinterVisual, ...]
    serviced_printer: str = "printer_2"

    @classmethod
    def from_configs(cls, robot_path: Path, printers_path: Path) -> "SceneData":
        with robot_path.open("r", encoding="utf-8") as stream:
            robot = yaml.safe_load(stream)["robot"]
        with printers_path.open("r", encoding="utf-8") as stream:
            configured = yaml.safe_load(stream)["printers"]
        visuals = tuple(
            PrinterVisual(name, float(item["position"]["x_mm"]), float(item["position"]["y_mm"]))
            for name, item in configured.items()
            if item.get("enabled", True)
        )
        return cls(float(robot["rail"]["min_mm"]), float(robot["rail"]["max_mm"]), visuals)

    def printer(self, name: str) -> PrinterVisual:
        return next(printer for printer in self.printers if printer.name == name)


class SimulationScene:
    def __init__(self, axes: Axes, data: SceneData) -> None:
        self.axes = axes
        self.data = data
        self.robot_geometry = SimpleRobotGeometry()
        self._draw_static_scene()
        (self.arm_line,) = axes.plot([], [], "o-", color="#e76f51", linewidth=5, markersize=7, label="Robot arm")
        self.carriage = Rectangle((0, -35), 90, 70, color="#264653", zorder=3)
        self.end_effector = Rectangle((0, 0), 55, 22, color="#f4a261", zorder=4)
        self.part = Rectangle((0, 0), 90, 55, color="#2a9d8f", zorder=3)
        axes.add_patch(self.carriage)
        axes.add_patch(self.end_effector)
        axes.add_patch(self.part)
        self.state_text = axes.text(0.02, 0.96, "", transform=axes.transAxes, va="top", fontsize=12, weight="bold")

    def _draw_static_scene(self) -> None:
        axes = self.axes
        axes.set_title("Rail-mounted robot servicing a print farm (concept only)")
        axes.plot([self.data.rail_min_mm, self.data.rail_max_mm], [0, 0], color="#555", linewidth=8)
        axes.text(self.data.rail_max_mm / 2, -80, "Rail", ha="center")
        for printer in self.data.printers:
            axes.add_patch(Rectangle((printer.x_mm - 130, printer.y_mm - 90), 260, 180, fill=False, linewidth=2))
            axes.add_patch(Rectangle((printer.x_mm - 100, printer.y_mm - 25), 200, 50, color="#adb5bd"))
            axes.text(printer.x_mm, printer.y_mm + 120, printer.name.replace("_", " ").title(), ha="center")
            axes.text(printer.x_mm, printer.y_mm + 8, "Printer bed", ha="center", fontsize=8)
        axes.set_xlim(self.data.rail_min_mm - 150, self.data.rail_max_mm + 220)
        axes.set_ylim(-150, 650)
        axes.set_aspect("equal", adjustable="box")
        axes.set_xlabel("World X / rail position (mm)")
        axes.set_ylabel("World Y / toward printers (mm)")
        axes.grid(alpha=0.15)

    def update(self, frame: DemoFrame):
        x_points, y_points = self.robot_geometry.points(frame.carriage_x_mm, frame.arm_extension)
        self.arm_line.set_data(x_points, y_points)
        self.carriage.set_xy((frame.carriage_x_mm - 45, -35))
        tool_x, tool_y = x_points[-1], y_points[-1]
        self.end_effector.set_xy((tool_x - 27.5, tool_y - 11))
        printer = self.data.printer(self.data.serviced_printer)
        self.part.set_xy((printer.x_mm - 45 + frame.part_offset_mm, printer.y_mm - 27.5))
        self.state_text.set_text(f"State: {frame.state}")
        return self.arm_line, self.carriage, self.end_effector, self.part, self.state_text
