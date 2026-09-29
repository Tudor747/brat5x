"""Small deterministic scheduler seam for future multi-printer policies."""

from __future__ import annotations

from printers.printer_base import PrinterInterface, PrinterState
from printers.printer_manager import PrinterManager


class PrinterScheduler:
    WAITING_STATES = {
        PrinterState.FINISHED,
        PrinterState.COOLING,
        PrinterState.READY_FOR_REMOVAL,
    }

    def select_next(self, manager: PrinterManager) -> PrinterInterface | None:
        """Select the first configured waiting printer (FIFO policy placeholder)."""
        return next((printer for printer in manager if printer.state in self.WAITING_STATES), None)
