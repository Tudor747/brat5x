"""Deterministic simulated printer."""

from __future__ import annotations

import logging

from printers.printer_base import PrinterConfig, PrinterInterface, PrinterState


LOGGER = logging.getLogger(__name__)


class MockPrinter(PrinterInterface):
    def __init__(self, config: PrinterConfig) -> None:
        self.config = config
        self._state = PrinterState.IDLE
        self._progress_percent = 0.0
        self._bed_temperature = 25.0
        self._print_name: str | None = None

    @property
    def state(self) -> PrinterState:
        return self._state

    @property
    def progress_percent(self) -> float:
        return self._progress_percent

    @property
    def bed_temperature(self) -> float:
        return self._bed_temperature

    @property
    def print_name(self) -> str | None:
        return self._print_name

    def _transition(self, state: PrinterState) -> None:
        if state is not self._state:
            LOGGER.info("[PRINTER] %s: %s -> %s", self.config.name, self._state.value, state.value)
            self._state = state

    def start_print(self, print_name: str, bed_temperature_c: float = 60.0) -> None:
        self._print_name = print_name
        self._progress_percent = 0.0
        self._bed_temperature = float(bed_temperature_c)
        self._transition(PrinterState.PRINTING)

    def set_progress(self, progress_percent: float) -> None:
        if self.state is not PrinterState.PRINTING:
            raise RuntimeError("progress can only be changed while printing")
        if not 0.0 <= progress_percent <= 100.0:
            raise ValueError("progress must be within [0, 100]")
        self._progress_percent = float(progress_percent)

    def finish_print(self, bed_temperature_c: float | None = None) -> None:
        self._progress_percent = 100.0
        if bed_temperature_c is not None:
            self._bed_temperature = float(bed_temperature_c)
        self._transition(PrinterState.FINISHED)

    def begin_cooling(self) -> None:
        if self.state not in {PrinterState.FINISHED, PrinterState.COOLING}:
            raise RuntimeError("printer must be finished before cooling")
        self._transition(PrinterState.COOLING)

    def cool_to(self, bed_temperature_c: float) -> None:
        self._bed_temperature = float(bed_temperature_c)
        if self.state is PrinterState.FINISHED:
            self._transition(PrinterState.COOLING)
        if (
            self.state is PrinterState.COOLING
            and self._bed_temperature <= self.config.safe_bed_temperature_c
        ):
            self._transition(PrinterState.READY_FOR_REMOVAL)

    def set_error(self) -> None:
        self._transition(PrinterState.ERROR)

    def refresh(self) -> None:
        LOGGER.debug("[PRINTER] Refreshed mock %s", self.config.name)

    def mark_part_removed(self) -> None:
        if not self.is_safe_for_removal():
            raise RuntimeError("cannot mark a part removed before the printer is safe")
        self._print_name = None
        self._progress_percent = 0.0
        self._transition(PrinterState.IDLE)
