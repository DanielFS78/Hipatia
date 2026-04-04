"""
Interfaz PyQt6 (`assignment_dialogs`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional, TYPE_CHECKING, Any

from core.di_container import DIContainer
from core.services.fabricacion_service import FabricacionService

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget
    # Assuming AppController structure
    from controllers.app_controller import AppController

class AssignPreprocesosDialog(QDialog):
    """
    Diálogo para asignar preprocesos a fabricaciones desde el menú de Preprocesos.
    """

    def __init__(self, parent_controller: "AppController", parent: Optional["QWidget"] = None) -> None:
        super().__init__(parent)
        self.controller = parent_controller
        self.setup_ui()
        self.load_fabricaciones()

    def _fabricacion_service(self) -> Any | None:
        pc = getattr(self.controller, "product_controller", None)
        fs = getattr(pc, "fabricacion_service", None) if pc is not None else None
        if fs is not None:
            return fs
        _c = DIContainer.get_instance()
        if _c.is_registered(FabricacionService):
            return _c.resolve(FabricacionService)
        return None

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
            fabricaciones = self.controller.search_fabricaciones("")
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
            svc = self._fabricacion_service()
            if svc is not None:
                preprocesos = svc.get_preprocesos_by_fabricacion(fabricacion_id)
            else:
                preprocesos = self.controller.model.get_preprocesos_by_fabricacion(fabricacion_id)
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

        # Usar el método existente del controlador
        self.controller.show_fabricacion_preprocesos(fabricacion_id)

        # Recargar los preprocesos después de la modificación
        self.load_current_preprocesos(fabricacion_id)
