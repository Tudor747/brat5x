"""Stable printer interface for mock and future network/serial adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class PrinterState(str, Enum):
    IDLE = "IDLE"
    PRINTING = "PRINTING"
    FINISHED = "FINISHED"
    COOLING = "COOLING"
    READY_FOR_REMOVAL = "READY_FOR_REMOVAL"
    ERROR = "ERROR"


@dataclass(frozen=True)
class PrinterConfig:
    name: str
    enabled: bool
    host: str
    interface: str
    position_mm: tuple[float, float, float]
    safe_bed_temperature_c: float


class PrinterInterface(ABC):
    """Protocol insulated from Moonraker, OctoPrint, and Marlin details."""

    config: PrinterConfig

    @property
    @abstractmethod
    def state(self) -> PrinterState: ...

    @property
    @abstractmethod
    def progress_percent(self) -> float: ...

    @property
    @abstractmethod
    def bed_temperature(self) -> float: ...

    @property
    @abstractmethod
    def print_name(self) -> str | None: ...

    @abstractmethod
    def refresh(self) -> None:
        """Refresh state from the underlying printer transport."""

    @abstractmethod
    def mark_part_removed(self) -> None:
        """Acknowledge successful removal to the adapter."""

    def is_safe_for_removal(self) -> bool:
        return (
            self.state is PrinterState.READY_FOR_REMOVAL
            and self.bed_temperature <= self.config.safe_bed_temperature_c
        )
