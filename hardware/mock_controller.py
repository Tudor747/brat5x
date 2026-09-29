"""Synchronous controller simulation; it never emits STEP pulses."""

from __future__ import annotations

from collections.abc import Sequence
import logging
import numpy as np
from numpy.typing import NDArray

from hardware.controller_interface import ControllerError, ControllerInterface
from robot.robot_model import RobotModel


LOGGER = logging.getLogger(__name__)


class MockController(ControllerInterface):
    def __init__(self, robot: RobotModel) -> None:
        self.robot = robot
        self._moving = False
        self._emergency_stop_latched = False

    @property
    def emergency_stop_latched(self) -> bool:
        return self._emergency_stop_latched

    def home(self) -> None:
        self.move_joint_positions(self.robot.home_q)
        LOGGER.info("[MOTION] Mock homing complete")

    def move_joint_positions(self, q_target: Sequence[float]) -> None:
        if self._emergency_stop_latched:
            raise ControllerError("movement rejected: emergency stop is latched")
        if self._moving:
            raise ControllerError("movement rejected: controller is busy")
        self.robot.validate_joint_positions(q_target)
        LOGGER.info("[MOTION] MOVEJ target=%s", np.round(q_target, 4).tolist())
        self._moving = True
        try:
            # A real adapter would enqueue the target and return/poll status.
            self.robot.set_joint_positions(q_target)
        finally:
            self._moving = False
        LOGGER.info("[MOTION] Mock movement complete")

    def stop(self) -> None:
        self._moving = False
        LOGGER.warning("[SAFETY] Controlled stop requested")

    def emergency_stop(self) -> None:
        self._moving = False
        self._emergency_stop_latched = True
        LOGGER.critical("[SAFETY] EMERGENCY STOP latched")

    def reset_emergency_stop(self) -> None:
        self._emergency_stop_latched = False
        LOGGER.warning("[SAFETY] Emergency stop reset in mock controller")

    def get_joint_positions(self) -> NDArray[np.float64]:
        return self.robot.q.copy()

    def is_motion_complete(self) -> bool:
        return not self._moving

    def set_simulated_busy(self, busy: bool) -> None:
        """Test hook used to exercise the high-level interlock."""
        self._moving = bool(busy)
