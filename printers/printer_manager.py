"""Collection management independent of printer transport."""

from __future__ import annotations

from collections.abc import Iterable

from printers.printer_base import PrinterInterface


class PrinterManager:
    def __init__(self, printers: Iterable[PrinterInterface]) -> None:
        enabled = [printer for printer in printers if printer.config.enabled]
        self._printers = {printer.config.name: printer for printer in enabled}
        if len(self._printers) != len(enabled):
            raise ValueError("printer names must be unique")

    def __iter__(self):
        return iter(self._printers.values())

    def get(self, name: str) -> PrinterInterface:
        return self._printers[name]

    def refresh_all(self) -> None:
        for printer in self._printers.values():
            printer.refresh()
