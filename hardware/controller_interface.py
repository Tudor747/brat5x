"""Abstract interface owned by a future MCU transport adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from numpy.typing import NDArray
import numpy as np


class ControllerError(RuntimeError):
    pass


class ControllerInterface(ABC):
    @abstractmethod
    def home(self) -> None: ...

    @abstractmethod
    def move_joint_positions(self, q_target: Sequence[float]) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def emergency_stop(self) -> None: ...

    @abstractmethod
    def reset_emergency_stop(self) -> None: ...

    @abstractmethod
    def get_joint_positions(self) -> NDArray[np.float64]: ...

    @abstractmethod
    def is_motion_complete(self) -> bool: ...

    @property
    @abstractmethod
    def emergency_stop_latched(self) -> bool: ...
