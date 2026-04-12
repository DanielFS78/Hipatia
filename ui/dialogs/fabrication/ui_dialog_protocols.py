# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.fabrication.ui_dialog_protocols

Descripción: Protocolos mínimos para comandos de aplicación usados desde diálogos de fabricación.
"""

from __future__ import annotations

from typing import Protocol


class OpensFabricacionPreprocesos(Protocol):
    """Abre la gestión de preprocesos para una fabricación (p. ej. `AppController`)."""

    def show_fabricacion_preprocesos(self, fabricacion_id: int) -> None:
        ...


class ShowsUserMessage(Protocol):
    """Muestra mensajes al usuario (alineado con `IView.show_message` / `MainView`)."""

    def show_message(self, title: str, message: str, level: str = "info") -> None:
        ...
