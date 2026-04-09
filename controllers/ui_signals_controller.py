# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui_signals_controller.py
Descripción: Centralizador de la interconexión mediante señales y slots. Desacopla
             la lógica de los widgets de los controladores principales.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QObject

from controllers.ui_signals_wiring import UISignalsWiring

if TYPE_CHECKING:
    from controllers.app_controller import AppController


class UISignalsController(QObject):
    """
    Controlador de señales y ranuras (signals & slots).

    Centraliza la conexión entre los eventos de la interfaz de usuario (clics,
    cambios de texto) y los métodos de negocio de los diversos controladores.
    """

    def __init__(self, app_controller: Any) -> None:
        """
        Inicializa el controlador de señales.

        Args:
            app_controller: Referencia al controlador principal.
        """
        super().__init__()
        self.app = app_controller
        self.view = app_controller.view
        self.logger = logging.getLogger("EvolucionTiemposApp.UISignals")
        self._wiring = UISignalsWiring(self.app, self.view, self.logger, self._on_import_tasks_requested)

    def connect_navigation_signals(self) -> None:
        self._wiring.connect_navigation_signals()

    def connect_preprocesos_signals(self) -> None:
        self._wiring.connect_preprocesos_signals()

    def connect_products_signals(self) -> None:
        self._wiring.connect_products_signals()

    def connect_fabrications_signals(self) -> None:
        self._wiring.connect_fabrications_signals()

    def connect_add_product_signals(self) -> None:
        self._wiring.connect_add_product_signals()

    def connect_calculate_signals(self) -> None:
        self._wiring.connect_calculate_signals()

    def connect_historial_signals(self) -> None:
        self._wiring.connect_historial_signals()

    def connect_definir_lote_signals(self) -> None:
        self._wiring.connect_definir_lote_signals()

    def connect_lotes_management_signals(self) -> None:
        self._wiring.connect_lotes_management_signals()

    def connect_reportes_signals(self) -> None:
        self._wiring.connect_reportes_signals()

    def connect_workers_signals(self) -> None:
        self._wiring.connect_workers_signals()

    def connect_machines_signals(self) -> None:
        self._wiring.connect_machines_signals()

    # Compatibilidad: nombres _connect_* que delegan en connect_* (API pública).
    def _connect_navigation_signals(self) -> None:
        self.connect_navigation_signals()

    def _connect_preprocesos_signals(self) -> None:
        self.connect_preprocesos_signals()

    def _connect_products_signals(self) -> None:
        self.connect_products_signals()

    def _connect_fabrications_signals(self) -> None:
        self.connect_fabrications_signals()

    def _connect_add_product_signals(self) -> None:
        self.connect_add_product_signals()

    def _connect_calculate_signals(self) -> None:
        self.connect_calculate_signals()

    def _connect_historial_signals(self) -> None:
        self.connect_historial_signals()

    def _connect_definir_lote_signals(self) -> None:
        self.connect_definir_lote_signals()

    def _connect_lotes_management_signals(self) -> None:
        self.connect_lotes_management_signals()

    def _connect_reportes_signals(self) -> None:
        self.connect_reportes_signals()

    def _connect_workers_signals(self) -> None:
        self.connect_workers_signals()

    def _connect_machines_signals(self) -> None:
        self.connect_machines_signals()

    def _on_import_tasks_requested(self) -> None:
        """Slot estable para ``import_tasks_signal`` (misma referencia que en tests)."""
        self._wiring.run_import_tasks_from_csv_dialog()

    def connect_all_signals(self) -> None:
        """Conecta todas las señales de la aplicación."""
        self.logger.debug("Iniciando conexión de señales...")
        self.connect_navigation_signals()
        self.connect_add_product_signals()
        self.connect_reportes_signals()
        self.connect_calculate_signals()
        self.connect_historial_signals()
        self.connect_workers_signals()
        self.connect_machines_signals()
        self.connect_products_signals()
        self.connect_fabrications_signals()

        try:
            self.connect_preprocesos_signals()
        except Exception as e:
            self.logger.error(f"Error conectando señales de preprocesos: {e}")

        self.connect_definir_lote_signals()
        self.connect_lotes_management_signals()

        self.app.model.product_deleted_signal.connect(self.app.ui_controller.on_data_changed)

        self.logger.info("✅ Todas las señales de la aplicación han sido conectadas exitosamente.")
