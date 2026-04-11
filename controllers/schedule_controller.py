# -*- coding: utf-8 -*-
"""
Nombre del Módulo: schedule_controller
Descripción: Controlador orquestador para la gestión de la planificación de la producción.
Gestiona la configuración de horarios laborales, descansos y festivos mediante componentes delegados.
"""
from __future__ import annotations
import logging
from typing import Any, Optional, cast
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QTimeEdit
from PyQt6.QtCore import QTime, QObject

# Nuevos Helpers por Composición
from controllers.schedule_ui_helper import ScheduleUiOpsHelper

# Helpers de utilidad existentes
from controllers.schedule_helpers import (
    dump_json,
    normalize_holidays,
)

from database.database_manager import DatabaseManager
from core.schedule_config import ScheduleConfig
from core.interfaces.view_interface import IView


def get_add_break_dialog_class() -> Any:
    """Clase del diálogo de descansos (carga diferida; sin import estático `ui`)."""
    from controllers.ui_class_loader import ui_class

    return ui_class("ui.dialogs", "AddBreakDialog")


class ScheduleController(QObject):
    """
    Controlador de horarios y descansos.
    Utiliza composición para delegar la lógica de UI y API legacy en helpers especializados.
    """

    def __init__(
        self,
        db: DatabaseManager,
        view: IView,
        schedule_manager: ScheduleConfig,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Inicializa el controlador y sus componentes delegados.

        Args:
            db: DatabaseManager con acceso a los repositorios.
            view: MainView para mostrar mensajes y acceder a widgets.
            schedule_manager: ScheduleConfig para recargar configuración.
            logger: Logger opcional para registro.
        """
        super().__init__()
        self.db: DatabaseManager = db
        self.view: IView = view
        self.schedule_manager: ScheduleConfig = schedule_manager
        self.logger = logger or logging.getLogger(__name__)

        # Composición: Instanciación de Helpers
        self.ui_helper = ScheduleUiOpsHelper(self.db, self.view, self.schedule_manager, self.logger, controller=self)

    @property
    def model(self) -> ScheduleController:
        """Propiedad puente para compatibilidad con el sistema de widgets antiguos."""
        return self

    # =========================================================================
    # API PÚBLICA (Delegación al UI Helper)
    # =========================================================================

    def save_schedule_settings(self) -> None:
        """Guarda la configuración del horario laboral persistiendo en la DB."""
        self.ui_helper.save_schedule_settings()

    def load_schedule_settings(self) -> None:
        """Carga la configuración de horarios desde la arquitectura persistente a la UI."""
        self.ui_helper.load_schedule_settings()

    def on_add_break_clicked(self) -> None:
        """Manejador del botón para añadir un nuevo descanso en la configuración."""
        self.ui_helper.on_add_break_clicked()

    def on_remove_break_clicked(self) -> None:
        """Manejador para eliminar el descanso seleccionado de la lista de UI."""
        self.ui_helper.on_remove_break_clicked()

    def on_edit_break_clicked(self) -> None:
        """Manejador para editar un descanso existente."""
        self.ui_helper.on_edit_break_clicked()

    def on_add_break(self) -> None:
        """Método de compatibilidad para el flujo legacy de añadir descansos."""
        self.ui_helper.on_add_break()

    # =========================================================================
    # API PÚBLICA (programática + carga completa; delegado al UI helper)
    # =========================================================================

    def add_break(self, start_time: str, end_time: str, desc: str = "") -> tuple[bool, str]:
        """API para añadir descansos programáticamente."""
        return self.ui_helper.add_break(start_time, end_time, desc)

    def delete_break(self, index: int) -> tuple[bool, str]:
        """API para eliminar descansos por índice."""
        return self.ui_helper.delete_break(index)

    def save_work_hours(self, start_time: str, end_time: str, breaks: list[dict[str, str]]) -> tuple[bool, str]:
        """API directa para guardar horas laborales."""
        return self.ui_helper.save_work_hours(start_time, end_time, breaks)

    def load_schedule_config(self) -> None:
        """Carga completa de la configuración (Horas, Descansos, Festivos)."""
        self.ui_helper.load_schedule_config()

    # =========================================================================
    # GESTIÓN DE FESTIVOS (Lógica central del controlador)
    # =========================================================================

    def load_holidays(self) -> None:
        """Carga la lista de festivos desde la configuración y la vuelca en la UI."""
        settings_page = self.view.pages.get("settings")
        if not settings_page or not hasattr(settings_page, "holidays_list"):
            return

        holidays_json = self.db.config_repo.get_setting("holidays", "[]")
        normalized = normalize_holidays(holidays_json)

        settings_page.holidays_list.clear()
        for h in normalized:
            settings_page.holidays_list.addItem(h["date"])

    def on_add_holiday(self) -> None:
        """Añade el día seleccionado en el calendario como festivo."""
        settings_page = self.view.pages["settings"]
        selected_date = settings_page.calendar.selectedDate().toPyDate()
        iso_date = selected_date.isoformat()

        holidays_json = self.db.config_repo.get_setting('holidays', '[]')
        normalized = normalize_holidays(holidays_json)
        dates = {h["date"] for h in normalized}
        if iso_date not in dates:
            normalized.append({"date": iso_date, "desc": ""})
            self.db.config_repo.set_setting("holidays", dump_json(normalized))
            self.schedule_manager.reload_config(self.db)
            self.load_schedule_settings()
            self.view.show_message(
                "Éxito",
                f"Día {selected_date.strftime('%d/%m/%Y')} añadido como festivo.",
                "info"
            )

    def on_remove_holiday(self) -> None:
        """Elimina el día seleccionado de la lista de festivos configurada."""
        settings_page = self.view.pages["settings"]
        selected_date = settings_page.calendar.selectedDate().toPyDate()
        iso_date = selected_date.isoformat()

        holidays_json = self.db.config_repo.get_setting('holidays', '[]')
        normalized = normalize_holidays(holidays_json)
        new_list = [h for h in normalized if h.get("date") != iso_date]
        found = len(new_list) != len(normalized)

        if found:
            self.db.config_repo.set_setting("holidays", dump_json(new_list))
            self.schedule_manager.reload_config(self.db)
            self.load_schedule_settings()
            self.view.show_message(
                "Éxito",
                f"Día {selected_date.strftime('%d/%m/%Y')} eliminado de festivos.",
                "info"
            )

    # =========================================================================
    # UTILIDADES DE CONFIGURACIÓN
    # =========================================================================

    def config_get_setting(self, key: str, default: str = "") -> str:
        """Obtiene un ajuste de configuración de la persistencia."""
        return cast(str, self.db.config_repo.get_setting(key, default))

    def config_set_setting(self, key: str, value: str) -> bool:
        """Establece o actualiza un ajuste de configuración."""
        return bool(self.db.config_repo.set_setting(key, value))

    def reload_config(self) -> None:
        """Recarga la configuración global de horarios en el sistema."""
        self.schedule_manager.reload_config(self.db)
