"""Readable supervisory state machine for the prototype workflow."""

from __future__ import annotations

from enum import Enum
import logging

from controller.safety import SafetyManager
from controller.scheduler import PrinterScheduler
from hardware.controller_interface import ControllerInterface
from motion.taught_pose import TaughtPose
from printers.printer_base import PrinterInterface
from printers.printer_manager import PrinterManager


LOGGER = logging.getLogger(__name__)


class RobotState(str, Enum):
    IDLE = "IDLE"
    WAITING_FOR_JOB = "WAITING_FOR_JOB"
    PRINT_FINISHED = "PRINT_FINISHED"
    WAITING_FOR_BED_COOLING = "WAITING_FOR_BED_COOLING"
    MOVING_TO_PRINTER = "MOVING_TO_PRINTER"
    MOVING_TO_APPROACH = "MOVING_TO_APPROACH"
    PUSHING_PRINT = "PUSHING_PRINT"
    RETRACTING = "RETRACTING"
    RETURNING_HOME = "RETURNING_HOME"
    ERROR = "ERROR"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class RobotStateMachine:
    def __init__(
        self,
        printers: PrinterManager,
        controller: ControllerInterface,
        safety: SafetyManager,
        taught_poses: dict[str, TaughtPose],
        scheduler: PrinterScheduler | None = None,
    ) -> None:
        self.printers = printers
        self.controller = controller
        self.safety = safety
        self.taught_poses = taught_poses
        self.scheduler = scheduler or PrinterScheduler()
        self.state = RobotState.IDLE
        self.active_printer: PrinterInterface | None = None
        LOGGER.info("[STATE] %s", self.state.value)

    def _transition(self, state: RobotState) -> None:
        LOGGER.info("[STATE] %s -> %s", self.state.value, state.value)
        self.state = state

    def _pose_name(self, suffix: str) -> str:
        if self.active_printer is None:
            raise RuntimeError("no active printer")
        return f"{self.active_printer.config.name.upper()}_{suffix}"

    def _move(self, pose_name: str) -> None:
        try:
            pose = self.taught_poses[pose_name]
        except KeyError as exc:
            raise RuntimeError(f"missing required taught pose {pose_name}") from exc
        self.safety.validate_motion(pose.joint_positions, self.controller)
        LOGGER.info("[MOTION] Moving to %s", pose_name)
        self.controller.move_joint_positions(pose.joint_positions)

    def tick(self) -> RobotState:
        """Perform at most one state action; mock movements complete immediately."""
        if self.state in {RobotState.ERROR, RobotState.EMERGENCY_STOP}:
            return self.state
        try:
            if self.state is RobotState.IDLE:
                self._transition(RobotState.WAITING_FOR_JOB)
            elif self.state is RobotState.WAITING_FOR_JOB:
                self.printers.refresh_all()
                selected = self.scheduler.select_next(self.printers)
                if selected is not None:
                    self.active_printer = selected
                    LOGGER.info("[PRINTER] %s finished", selected.config.name)
                    self._transition(RobotState.PRINT_FINISHED)
            elif self.state is RobotState.PRINT_FINISHED:
                assert self.active_printer is not None
                self._transition(
                    RobotState.MOVING_TO_PRINTER
                    if self.active_printer.is_safe_for_removal()
                    else RobotState.WAITING_FOR_BED_COOLING
                )
            elif self.state is RobotState.WAITING_FOR_BED_COOLING:
                assert self.active_printer is not None
                self.active_printer.refresh()
                LOGGER.info("[PRINTER] Bed = %.1f C", self.active_printer.bed_temperature)
                if self.active_printer.is_safe_for_removal():
                    self._transition(RobotState.MOVING_TO_PRINTER)
            elif self.state is RobotState.MOVING_TO_PRINTER:
                self._move(self._pose_name("RAIL"))
                self._transition(RobotState.MOVING_TO_APPROACH)
            elif self.state is RobotState.MOVING_TO_APPROACH:
                self._move(self._pose_name("APPROACH"))
                self._transition(RobotState.PUSHING_PRINT)
            elif self.state is RobotState.PUSHING_PRINT:
                assert self.active_printer is not None
                self.safety.validate_push(self.active_printer)
                self._move(self._pose_name("PUSH_START"))
                self._move(self._pose_name("PUSH_END"))
                self._transition(RobotState.RETRACTING)
            elif self.state is RobotState.RETRACTING:
                self._move(self._pose_name("APPROACH"))
                self._transition(RobotState.RETURNING_HOME)
            elif self.state is RobotState.RETURNING_HOME:
                self._move("HOME")
                assert self.active_printer is not None
                self.active_printer.mark_part_removed()
                self.active_printer = None
                self._transition(RobotState.IDLE)
        except Exception:
            LOGGER.exception("[STATE] Controller workflow failed")
            self.controller.stop()
            self._transition(RobotState.ERROR)
        return self.state

    def emergency_stop(self) -> None:
        self.controller.emergency_stop()
        self._transition(RobotState.EMERGENCY_STOP)

    def reset_emergency_stop(self) -> None:
        if self.state is not RobotState.EMERGENCY_STOP:
            raise RuntimeError("state machine is not emergency-stopped")
        self.controller.reset_emergency_stop()
        self.active_printer = None
        self._transition(RobotState.IDLE)
