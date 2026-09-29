"""Basic supervisory safety checks (not a hardware safety system)."""

from __future__ import annotations

from collections.abc import Sequence
import logging

from hardware.controller_interface import ControllerInterface
from printers.printer_base import PrinterInterface
from robot.robot_model import RobotModel


LOGGER = logging.getLogger(__name__)


class SafetyViolation(RuntimeError):
    pass


class SafetyManager:
    def __init__(self, robot: RobotModel) -> None:
        self.robot = robot

    def validate_motion(self, target: Sequence[float], controller: ControllerInterface) -> None:
        try:
            if controller.emergency_stop_latched:
                raise SafetyViolation("movement refused: emergency stop is latched")
            if not controller.is_motion_complete():
                raise SafetyViolation("movement refused: another movement is executing")
            self.robot.validate_joint_positions(target)
        except (ValueError, SafetyViolation) as exc:
            LOGGER.error("[SAFETY] %s", exc)
            raise

    def validate_push(self, printer: PrinterInterface) -> None:
        if not printer.is_safe_for_removal():
            message = (
                f"push refused for {printer.config.name}: state={printer.state.value}, "
                f"bed={printer.bed_temperature:.1f} C"
            )
            LOGGER.error("[SAFETY] %s", message)
            raise SafetyViolation(message)
