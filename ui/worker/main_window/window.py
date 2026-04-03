# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`window`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

import logging
from PyQt6.QtWidgets import QMainWindow, QWidget, QMessageBox, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal

from typing import Optional, Dict, Any, List
from typing import cast
from core.interfaces.worker_view_interface import IWorkerView
from .ui_manager import WorkerMainWindowUIManager


class WorkerMainWindow(QMainWindow, IWorkerView):
    """
    Ventana principal para el rol de trabajador.
    """

    # Señales
    logout_requested = pyqtSignal()
    export_data_requested = pyqtSignal()
    task_selected = pyqtSignal(dict)
    generate_labels_requested = pyqtSignal(dict)
    camera_config_requested = pyqtSignal()
    consult_qr_requested = pyqtSignal()
    start_task_requested = pyqtSignal(dict)
    end_task_requested = pyqtSignal(dict)
    register_incidence_requested = pyqtSignal(dict)

    # Atributos UI inicializados por WorkerMainWindowUIManager.setup_main_window()
    stacked_widget: Any
    tasks_list: Any
    details_stack: Any
    register_incidence_btn: Any
    end_task_btn: Any
    start_task_btn: Any
    generate_labels_btn: Any
    task_status_label: Any

    def __init__(self, current_user: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.current_user = current_user
        self.logger = logging.getLogger("EvolucionTiemposApp.WorkerMainWindow")

        self.current_selected_task = None
        self._ui_manager = WorkerMainWindowUIManager(self)
        self._ui_manager.setup_main_window()

        self.logger.info(f"WorkerMainWindow inicializada para {getattr(current_user, 'nombre_completo', 'Usuario')}")

    def enable_action_buttons(self, enabled: bool) -> None:
        """Habilita o deshabilita los botones de control de tareas."""
        self.register_incidence_btn.setEnabled(enabled)
        self.end_task_btn.setEnabled(enabled)
        self.start_task_btn.setEnabled(not enabled)
        self.logger.debug(f"Botones de acción {'habilitados' if enabled else 'deshabilitados'}")

    def _on_logout_clicked(self) -> None:
        self.logger.info(f"Usuario {getattr(self.current_user, 'nombre_completo', 'Usuario')} solicitó cerrar sesión")
        self.logout_requested.emit()
        self.close()

    def _forzar_auto_ajuste(self) -> None:
        """
        Fuerza un recalculo dinámico del factor de escala y repinta
        toda la aplicación iterando sobre sus hijos.
        """
        from core.utils.ui_scaler import UIScaler
        from PyQt6.QtWidgets import QApplication
        
        current_height = UIScaler.get_current_screen_height(self)
        factor = UIScaler.calculate_scale_factor(current_height)
        qss = UIScaler.generate_dynamic_qss(factor)
        
        app = cast(QApplication | None, QApplication.instance())
        if app is not None:
            app.setStyleSheet(qss)
            
        for i in range(self.stacked_widget.count()):
            page = self.stacked_widget.widget(i)
            if page is None:
                continue
            if hasattr(page, 'updateGeometry'):
                page.updateGeometry()
            if hasattr(page, 'adjustSize'):
                page.adjustSize()
                
        QApplication.processEvents()
        self.update()
        self.show_message("Auto-Ajuste", f"Interfaz escalada al {int(factor*100)}% de forma manual.", "info")

    def _on_camera_config_clicked(self) -> None:
        self.logger.info("Usuario solicitó configuración de cámara")
        self.camera_config_requested.emit()

    def add_screen(self, name: str, widget: QWidget) -> None:
        """Añade una nueva vista al contenedor de pantallas de la ventana."""
        self.stacked_widget.addWidget(widget)
        self.logger.debug(f"Pantalla '{name}' añadida al stacked widget")

    def switch_screen(self, index: int) -> None:
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            self.logger.debug(f"Cambiado a pantalla con índice {index}")
        else:
            self.logger.warning(f"Índice de pantalla inválido: {index}")

    def show_message(self, title: str, message: str, level: str = "info") -> None:
        if level == "info":
            self.logger.info(f"{title}: {message}")
        elif level == "warning":
            self.logger.warning(f"{title}: {message}")
        elif level == "error":
            self.logger.error(f"{title}: {message}")
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if level == "info":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif level == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif level == "error":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        
        msg_box.exec()

    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """Muestra un diálogo de confirmación Sí/No."""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def update_tasks_list(self, tasks: List[Dict[str, Any]]) -> None:
        self.tasks_list.clear()
        if not tasks:
            self.tasks_list.addItem("No tienes tareas asignadas.")
            return

        for task in tasks:
            prod_codigo = task.get('producto_codigo')
            prod_desc = task.get('producto_descripcion')
            cantidad = task.get('cantidad', 0)

            if prod_codigo and prod_desc:
                display_codigo = prod_codigo
                display_desc = f"{prod_desc} (Cantidad: {cantidad})"
            else:
                display_codigo = task.get('codigo', 'N/A')
                display_desc = task.get('descripcion', 'Sin descripción')

            item_text = f"🏭 {display_codigo}\n    {display_desc}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, task)
            self.tasks_list.addItem(item)

    def _on_task_selected(self, item: QListWidgetItem) -> None:
        try:
            self.current_selected_task = item.data(Qt.ItemDataRole.UserRole)
            if not self.current_selected_task:
                self.logger.warning("El item seleccionado no tiene datos (UserRole).")
                self.details_stack.setCurrentIndex(0)
                return

            self.logger.info(f"Tarea seleccionada: {self.current_selected_task.get('codigo')}")

            self.selected_task_code_label.setText(f"TAREA: {self.current_selected_task.get('codigo', 'N/A')}")
            self.selected_task_desc_label.setText(
                f"Descripción: {self.current_selected_task.get('descripcion', 'N/A')}")

            self.task_status_label.setText("Estado: Comprobando...")
            self.task_status_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")

            self.generate_labels_btn.setEnabled(False)
            self.start_task_btn.setEnabled(False)
            self.register_incidence_btn.setEnabled(False)
            self.end_task_btn.setEnabled(False)

            self.details_stack.setCurrentIndex(1)
            self.task_selected.emit(self.current_selected_task)

        except Exception as e:
            self.logger.error(f"Error en _on_task_selected: {e}", exc_info=True)
            self.details_stack.setCurrentIndex(0)

    def update_task_state(self, state: str, current_step_name: Optional[str] = None) -> None:
        self.generate_labels_btn.setEnabled(True)

        if state == "pendiente":
            self.task_status_label.setText("Estado: 🟢 Pendiente")
            self.task_status_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
            self.start_task_btn.setEnabled(True)
            self.register_incidence_btn.setEnabled(False)
            self.end_task_btn.setEnabled(False)

        elif state == "en_proceso":
            step_display = f"({current_step_name})" if current_step_name else ""
            self.task_status_label.setText(f"Estado: 🟡 En Proceso {step_display}")
            self.task_status_label.setStyleSheet("font-weight: bold; color: #f39c12;")
            self.start_task_btn.setEnabled(False)
            self.register_incidence_btn.setEnabled(True)
            self.end_task_btn.setEnabled(True)

        elif state == "finalizada":
            self.task_status_label.setText("Estado: ✅ Finalizada")
            self.task_status_label.setStyleSheet("font-weight: bold; color: #3498db;")
            self.start_task_btn.setEnabled(False)
            self.register_incidence_btn.setEnabled(False)
            self.end_task_btn.setEnabled(False)

    def _on_generate_labels_clicked(self) -> None:
        if self.current_selected_task:
            self.generate_labels_requested.emit(self.current_selected_task)

    def _on_start_task_clicked(self) -> None:
        if self.current_selected_task:
            self.start_task_requested.emit(self.current_selected_task)

    def _on_register_incidence_clicked(self) -> None:
        if self.current_selected_task:
            self.register_incidence_requested.emit(self.current_selected_task)

    def _on_end_task_clicked(self) -> None:
        if self.current_selected_task:
            self.end_task_requested.emit(self.current_selected_task)
