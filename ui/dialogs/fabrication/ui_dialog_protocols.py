"""Protocolos mínimos para comandos de aplicación usados desde diálogos de fabricación."""

from __future__ import annotations

from typing import Protocol


class OpensFabricacionPreprocesos(Protocol):
    """Abre la gestión de preprocesos para una fabricación (p. ej. `AppController`)."""

    def show_fabricacion_preprocesos(self, fabricacion_id: int) -> None:
        ...
