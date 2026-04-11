# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.fabrication.assignment_dialogs
Descripción: Diálogo o presentador de fabricación: órdenes, preprocesos, productos y persistencia de pilas.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional, TYPE_CHECKING, Any

from ui.dialogs.fabrication.ui_dialog_protocols import OpensFabricacionPreprocesos
from core.di_container import DIContainer
from ui.dialogs.fabrication.dialog_dependencies import resolve_fabricacion_service

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

class AssignPreprocesosDialog(QDialog):
    """
    Diálogo para asignar preprocesos a fabricaciones desde el menú de Preprocesos.
    """

    def __init__(
        self,
        app_hub: Any | None = None,
        parent: Optional["QWidget"] = None,
        *,
        fabricacion_service: Any | None = None,
        opens_fabricacion_preprocesos: OpensFabricacionPreprocesos | None = None,
    ) -> None:
        super().__init__(parent)
        self._app_hub = app_hub
        self._fabricacion_service_override = fabricacion_service
        self._opens_fabricacion_preprocesos = opens_fabricacion_preprocesos
        self.setup_ui()
        self.load_fabricaciones()

    def _get_fabricacion_service(self) -> Any | None:
        if self._fabricacion_service_override is not None:
            return self._fabricacion_service_override
        return resolve_fabricacion_service(self._app_hub, DIContainer.get_instance())

    def setup_ui(self) -> None:
        self.setWindowTitle("Asignar Preprocesos a Fabricaciones")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Instrucciones
        instructions = QLabel(
            "<b>Gestión de Preprocesos por Fabricación</b><br>"
            "Seleccione una fabricación para ver y modificar sus preprocesos asignados."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Layout horizontal principal
        main_layout = QHBoxLayout()

        # Panel izquierdo - Lista de fabricaciones
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("<b>Fabricaciones disponibles:</b>"))

        self.fabricaciones_list = QListWidget()
        self.fabricaciones_list.itemSelectionChanged.connect(self.on_fabricacion_selected)
        left_panel.addWidget(self.fabricaciones_list)

        # Panel derecho - Preprocesos de la fabricación seleccionada
        right_panel = QVBoxLayout()

        self.fabricacion_info = QLabel("Seleccione una fabricación para ver sus preprocesos")
        self.fabricacion_info.setWordWrap(True)
        self.fabricacion_info.setStyleSheet("font-weight: bold; color: #0066CC;")
        right_panel.addWidget(self.fabricacion_info)

        # Botón para modificar preprocesos
        self.modify_button = QPushButton("Modificar Preprocesos")
        self.modify_button.clicked.connect(self.modify_selected_fabricacion)
        self.modify_button.setEnabled(False)
        right_panel.addWidget(self.modify_button)

        # Lista de preprocesos actuales
        right_panel.addWidget(QLabel("Preprocesos actuales:"))
        self.current_preprocesos_list = QListWidget()
        right_panel.addWidget(self.current_preprocesos_list)

        # Añadir paneles al layout principal
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(300)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        layout.addLayout(main_layout)

        # Botón cerrar
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def load_fabricaciones(self) -> None:
        """Carga todas las fabricaciones disponibles."""
        try:
            svc = self._get_fabricacion_service()
            if svc is not None:
                fabricaciones = svc.search_fabricaciones("")
            elif self._app_hub is not None:
                fabricaciones = self._app_hub.search_fabricaciones("")
            else:
                fabricaciones = []
            self.fabricaciones_list.clear()

            if not fabricaciones:
                item = QListWidgetItem("No hay fabricaciones disponibles")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.fabricaciones_list.addItem(item)
            else:
                for fab in fabricaciones:
                    text = f"{fab.codigo}"
                    if fab.descripcion:
                        text += f" - {fab.descripcion}"

                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, fab.id)
                    self.fabricaciones_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando fabricaciones: {e}")

    def on_fabricacion_selected(self) -> None:
        """Maneja la selección de una fabricación."""
        current_item = self.fabricaciones_list.currentItem()
        if not current_item or not current_item.data(Qt.ItemDataRole.UserRole):
            self.modify_button.setEnabled(False)
            self.fabricacion_info.setText("Seleccione una fabricación para ver sus preprocesos")
            self.current_preprocesos_list.clear()
            return

        fabricacion_id = current_item.data(Qt.ItemDataRole.UserRole)
        fabricacion_text = current_item.text()

        self.fabricacion_info.setText(f"Fabricación seleccionada: {fabricacion_text}")
        self.modify_button.setEnabled(True)

        # Cargar preprocesos actuales
        self.load_current_preprocesos(fabricacion_id)

    def load_current_preprocesos(self, fabricacion_id: int) -> None:
        """Carga los preprocesos actuales de la fabricación."""
        try:
            svc = self._get_fabricacion_service()
            if svc is not None:
                preprocesos = svc.get_preprocesos_by_fabricacion(fabricacion_id)
            else:
                mod = getattr(self._app_hub, "model", None) if self._app_hub is not None else None
                fab = getattr(mod, "fabricacion_service", None) if mod is not None else None
                preprocesos = (
                    fab.get_preprocesos_by_fabricacion(fabricacion_id) if fab is not None else []
                )
            self.current_preprocesos_list.clear()

            if not preprocesos:
                item = QListWidgetItem("Sin preprocesos asignados")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.current_preprocesos_list.addItem(item)
            else:
                for prep in preprocesos:
                    text = prep.nombre
                    if prep.descripcion:
                        text += f" - {prep.descripcion}"

                    item = QListWidgetItem(text)
                    self.current_preprocesos_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"Error cargando preprocesos de la fabricación: {e}")

    def modify_selected_fabricacion(self) -> None:
        """Abre el diálogo para modificar preprocesos de la fabricación seleccionada."""
        current_item = self.fabricaciones_list.currentItem()
        if not current_item:
            return

        fabricacion_id = current_item.data(Qt.ItemDataRole.UserRole)

        if self._opens_fabricacion_preprocesos is not None:
            self._opens_fabricacion_preprocesos.show_fabricacion_preprocesos(fabricacion_id)
        elif self._app_hub is not None:
            self._app_hub.show_fabricacion_preprocesos(fabricacion_id)
        else:
            QMessageBox.warning(
                self,
                "Configuración",
                "No hay orquestador ni apertura de preprocesos configurada.",
            )

        # Recargar los preprocesos después de la modificación
        self.load_current_preprocesos(fabricacion_id)
