# -*- coding: utf-8 -*-
"""
Nombre del Módulo: schedule_ui_helper.py
Descripción: Helper para operaciones de interfaz de usuario del ScheduleController.
Maneja la lógica de interacción con widgets y diálogos de configuración de horarios.
"""

from __future__ import annotations
import json
import logging
from typing import TYPE_CHECKING, cast
from PyQt6.QtCore import QTime
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QTimeEdit, QWidget

from controllers.schedule_helpers import load_breaks_list, parse_break_text
import controllers.schedule_controller as schedule_controller

if TYPE_CHECKING:
    from controllers.schedule_controller import ScheduleController

from database.database_manager import DatabaseManager
from core.schedule_config import ScheduleConfig
from core.interfaces.view_interface import IView

class ScheduleUiOpsHelper:
    """
    Helper encargado de las operaciones que interactúan con la UI.
    Extraído de ScheduleController para mejorar la cohesión y reducir el tamaño del controlador.
    """

    def __init__(
        self,
        db: DatabaseManager,
        view: IView,
        schedule_manager: ScheduleConfig,
        logger: logging.Logger,
        controller: ScheduleController,
    ) -> None:
        """
        Inicializa el helper con las dependencias necesarias.

        Args:
            db: DatabaseManager para persistencia.
            view: MainView para acceso a widgets y mensajes.
            schedule_manager: Gestor de configuración de horarios.
            logger: Instancia de logger.
            controller: Referencia al controlador padre para delegación de llamadas mockeables.
        """
        self.db = db
        self.view = view
        self.schedule_manager = schedule_manager
        self.logger = logger
        self.controller = controller

    def save_schedule_settings(self) -> None:
        """Guarda la configuración completa del horario laboral desde la UI."""
        settings_page = self.view.pages["settings"]

        start_time = settings_page.work_start_time.time().toString("HH:mm")
        end_time = settings_page.work_end_time.time().toString("HH:mm")

        self.db.config_repo.set_setting("work_start_time", start_time)
        self.db.config_repo.set_setting("work_end_time", end_time)

        breaks: list[dict[str, str]] = []
        for i in range(settings_page.breaks_list.count()):
            item_text = settings_page.breaks_list.item(i).text()
            parsed = parse_break_text(item_text)
            if parsed:
                start, end = parsed
                breaks.append({"start": start, "end": end})

        self.db.config_repo.set_setting("breaks", json.dumps(breaks))
        self.schedule_manager.reload_config(self.db)

        self.logger.info(
            f"✅ Horario completo guardado: {start_time} - {end_time}, {len(breaks)} descansos"
        )
        self.view.show_message("Éxito", "Horario completo guardado y aplicado.", "info")

    def load_schedule_settings(self) -> None:
        """Carga la configuración del horario en los widgets de la UI."""
        settings_page = self.view.pages.get("settings")
        if not settings_page:
            self.logger.warning("SettingsWidget no disponible, saltando carga de horarios.")
            return

        start_time_str = self.db.config_repo.get_setting("work_start_time", "08:00")
        end_time_str = self.db.config_repo.get_setting("work_end_time", "15:15")

        settings_page.work_start_time.setTime(QTime.fromString(start_time_str, "HH:mm"))
        settings_page.work_end_time.setTime(QTime.fromString(end_time_str, "HH:mm"))

        breaks_json = self.db.config_repo.get_setting("breaks", '[{"start": "12:00", "end": "13:00"}]')
        breaks = load_breaks_list(breaks_json)
        settings_page.breaks_list.clear()
        if breaks:
            for brk in breaks:
                settings_page.breaks_list.addItem(f"{brk['start']} - {brk['end']}")
        else:
            self.logger.warning("Error cargando descansos, usando valor por defecto")
            settings_page.breaks_list.addItem("12:00 - 13:00")

    def on_add_break_clicked(self) -> None:
        """Abre el diálogo especializado para añadir un nuevo descanso horaro."""
        dialog = schedule_controller.get_add_break_dialog_class()(self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_break = dialog.get_times()
            breaks_json = self.db.config_repo.get_setting("breaks", "[]")
            breaks_list = json.loads(breaks_json)
            breaks_list.append(new_break)
            self.db.config_repo.set_setting("breaks", json.dumps(breaks_list))
            self.schedule_manager.reload_config()
            # Delegamos al controlador para que el test pueda interceptar la llamada
            self.controller.load_schedule_settings()

    def on_remove_break_clicked(self) -> None:
        """Elimina el descanso seleccionado actualmente en la lista de la UI."""
        settings_page = self.view.pages.get("settings")
        if not settings_page:
            return

        selected_items = settings_page.breaks_list.selectedItems()
        if not selected_items:
            self.view.show_message(
                "Selección Requerida",
                "Seleccione un descanso de la lista para eliminar.",
                "warning",
            )
            return

        selected_item = selected_items[0]
        break_text = selected_item.text()

        if self.view.show_confirmation_dialog(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el descanso '{break_text}'?",
        ):
            row = settings_page.breaks_list.row(selected_item)
            settings_page.breaks_list.takeItem(row)
            self.logger.info(f"Descanso '{break_text}' eliminado de la UI.")
            # Delegamos al controlador para que el test pueda interceptar la llamada
            self.controller.save_schedule_settings()
            self.view.show_message("Éxito", "Descanso eliminado correctamente.", "info")
            settings_page._update_break_buttons_state()

    def on_edit_break_clicked(self) -> None:
        """Permite editar un descanso existente abriendo el diálogo con los datos actuales."""
        settings_page = self.view.pages.get("settings")
        if not settings_page:
            return

        selected_items = settings_page.breaks_list.selectedItems()
        if not selected_items:
            self.view.show_message(
                "Selección Requerida",
                "Seleccione un descanso de la lista para editar.",
                "warning",
            )
            return

        selected_item = selected_items[0]
        original_text = selected_item.text()
        parsed = parse_break_text(original_text)
        if not parsed:
            self.logger.error(f"Error al parsear el texto del descanso: '{original_text}'")
            self.view.show_message("Error", "No se pudo leer la hora del descanso seleccionado.", "critical")
            return
        current_start_str, current_end_str = parsed
        current_start_time = QTime.fromString(current_start_str, "HH:mm")
        current_end_time = QTime.fromString(current_end_str, "HH:mm")

        dialog = schedule_controller.get_add_break_dialog_class()(self.view)
        dialog.start_time_edit.setTime(current_start_time)
        dialog.end_time_edit.setTime(current_end_time)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_times = dialog.get_times()
            new_text = f"{new_times['start']} - {new_times['end']}"
            selected_item.setText(new_text)
            self.logger.info(f"Descanso editado en la UI: '{original_text}' -> '{new_text}'")
            # Delegamos al controlador para que el test pueda interceptar la llamada
            self.controller.save_schedule_settings()
            self.view.show_message("Éxito", "Descanso actualizado correctamente.", "info")
            settings_page._update_break_buttons_state()

    def on_add_break(self) -> None:
        """Legacy helper: Abre un diálogo genérico para añadir un descanso."""
        dialog = schedule_controller.QDialog(cast(QWidget | None, self.view))
        dialog.setWindowTitle("Añadir Descanso")
        layout = schedule_controller.QFormLayout(dialog)

        start_time = schedule_controller.QTimeEdit()
        start_time.setDisplayFormat("HH:mm")
        start_time.setTime(schedule_controller.QTime(12, 0))
        end_time = schedule_controller.QTimeEdit()
        end_time.setDisplayFormat("HH:mm")
        end_time.setTime(schedule_controller.QTime(13, 0))

        layout.addRow("Hora de Inicio:", start_time)
        layout.addRow("Hora de Fin:", end_time)

        buttons = schedule_controller.QDialogButtonBox(
            schedule_controller.QDialogButtonBox.StandardButton.Ok
            | schedule_controller.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            start = start_time.time().toString("HH:mm")
            end = end_time.time().toString("HH:mm")
            settings_page = self.view.pages["settings"]
            settings_page.breaks_list.addItem(f"{start} - {end}")
            self.logger.info(f"Descanso añadido: {start} - {end}")

    # --- API programática (antes ScheduleLegacyApiHelper; composición unificada) ---

    def add_break(self, start_time: str, end_time: str, desc: str = "") -> tuple[bool, str]:
        """Añade un descanso de forma programática (API legacy / tests)."""
        try:
            breaks_json = self.db.config_repo.get_setting("breaks", "[]")
            breaks_list = json.loads(breaks_json)
            breaks_list.append({"start": start_time, "end": end_time, "desc": desc})
            self.db.config_repo.set_setting("breaks", json.dumps(breaks_list))
            self.schedule_manager.reload_config(self.db)
            return True, "Descanso añadido."
        except json.JSONDecodeError:
            return False, "Error al guardar el descanso."

    def delete_break(self, index: int) -> tuple[bool, str]:
        """Elimina un descanso por índice (API legacy / tests)."""
        try:
            breaks_json = self.db.config_repo.get_setting("breaks", "[]")
            breaks_list = json.loads(breaks_json)
            if 0 <= index < len(breaks_list):
                del breaks_list[index]
                self.db.config_repo.set_setting("breaks", json.dumps(breaks_list))
                self.schedule_manager.reload_config(self.db)
                return True, "Descanso eliminado."
            return False, "Índice inválido."
        except json.JSONDecodeError:
            return False, "Error al eliminar el descanso."

    def save_work_hours(self, start_time: str, end_time: str, breaks: list[dict[str, str]]) -> tuple[bool, str]:
        """Guarda horas laborales y descansos en configuración (API legacy)."""
        self.db.config_repo.set_setting("work_start_time", start_time)
        self.db.config_repo.set_setting("work_end_time", end_time)
        self.db.config_repo.set_setting("breaks", json.dumps(breaks))
        self.schedule_manager.reload_config(self.db)
        return True, "Horario guardado."

    def load_schedule_config(self) -> None:
        """Carga horas y descansos en la UI y delega festivos al controlador."""
        settings_page = self.view.pages.get("settings")
        if not settings_page:
            self.logger.warning("SettingsWidget no disponible, saltando carga de horarios.")
            return
        if not hasattr(settings_page, "work_start_time"):
            return

        start_time_str = self.db.config_repo.get_setting("work_start_time", "08:00")
        end_time_str = self.db.config_repo.get_setting("work_end_time", "15:15")

        settings_page.work_start_time.setTime(QTime.fromString(start_time_str, "HH:mm"))
        settings_page.work_end_time.setTime(QTime.fromString(end_time_str, "HH:mm"))

        breaks_json = self.db.config_repo.get_setting("breaks", "[]")
        try:
            breaks_list = json.loads(breaks_json)
            settings_page.breaks_list.clear()
            for brk in breaks_list:
                settings_page.breaks_list.addItem(f"{brk['start']} - {brk['end']}")
        except json.JSONDecodeError:
            settings_page.breaks_list.clear()

        self.controller.load_holidays()
