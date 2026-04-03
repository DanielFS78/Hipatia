# -*- coding: utf-8 -*-
"""
Tests unitarios para ScheduleController.

Cubre: on_add_break_clicked, on_remove_break_clicked, on_edit_break_clicked,
on_add_break, save_schedule_settings, load_schedule_settings,
on_add_holiday, on_remove_holiday.
"""

from __future__ import annotations
import json
import logging
import datetime
import pytest
from typing import Any, cast
from unittest.mock import MagicMock, patch, call, create_autospec, ANY

from PyQt6.QtCore import QTime
from PyQt6.QtWidgets import QDialog

from controllers.schedule_controller import ScheduleController
from ui.widgets.settings_widget import SettingsWidget
from core.dtos import ConfigurationDTO

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers / Factories
# ---------------------------------------------------------------------------

def _make_db() -> MagicMock:
    """Crea un mock de DatabaseManager con spec minimo."""
    db = MagicMock(spec=["config_repo"])
    db.config_repo = MagicMock(spec=["get_setting", "set_setting"])
    return db


def _make_view() -> MagicMock:
    """Crea un mock de MainView con spec minimo."""
    view = MagicMock(spec=["pages", "show_message", "show_confirmation_dialog"])
    view.pages = {}
    return view


def _make_schedule_manager() -> MagicMock:
    """Crea un mock de ScheduleConfig con spec minimo."""
    return MagicMock(spec=["reload_config"])


def _make_controller() -> ScheduleController:
    """Factory para ScheduleController con dependencias mockeadas estrictamente."""
    return ScheduleController(_make_db(), _make_view(), _make_schedule_manager())


def _make_settings_page() -> MagicMock:
    """Crea un mock de SettingsWidget con __class__ forzado para isinstance."""
    page = MagicMock(spec=['breaks_list', 'work_start_time', 'work_end_time', 'calendar', '_update_break_buttons_state'])
    cast(Any, page).__class__ = SettingsWidget
    return page


# ---------------------------------------------------------------------------
# TestScheduleControllerInit
# ---------------------------------------------------------------------------

class TestScheduleControllerInit:
    """Tests de inicializacion de ScheduleController."""

    def test_init_stores_dependencies(self) -> None:
        """Verifica que todas las dependencias se almacenan correctamente."""
        db = _make_db()
        view = _make_view()
        sm = _make_schedule_manager()
        ctrl = ScheduleController(db, view, sm)
        assert ctrl.db is db
        assert ctrl.view is view
        assert ctrl.schedule_manager is sm
        assert ctrl.logger is not None

    def test_init_uses_custom_logger(self) -> None:
        """Verifica que se acepta un logger personalizado."""
        custom_log = logging.getLogger("test.schedule")
        ctrl = ScheduleController(_make_db(), _make_view(), _make_schedule_manager(), logger=custom_log)
        assert ctrl.logger is custom_log


# ---------------------------------------------------------------------------
# TestOnAddBreakClicked
# ---------------------------------------------------------------------------

class TestOnAddBreakClicked:
    """Tests para on_add_break_clicked."""

    @pytest.fixture
    def ctrl(self) -> ScheduleController:
        """ScheduleController con dependencias mockeadas."""
        return _make_controller()

    @patch("controllers.schedule_controller.AddBreakDialog")
    def test_add_break_accepted(self, MockDlg: MagicMock, ctrl: ScheduleController) -> None:
        """Aceptar el dialogo guarda el descanso y recarga la configuracion."""
        inst = MockDlg.return_value
        inst.exec.return_value = QDialog.DialogCode.Accepted
        inst.get_times.return_value = {"start": "10:00", "end": "10:30"}
        ctrl.db.config_repo.get_setting.return_value = "[]"

        with patch.object(ctrl, "load_schedule_settings", autospec=True) as mock_load:
            ctrl.on_add_break_clicked()

        assert ctrl.db.config_repo.set_setting.call_count == 1
        assert ctrl.schedule_manager.reload_config.call_count == 1
        assert mock_load.call_count == 1
        ctrl.schedule_manager.reload_config.assert_called_once_with()
        mock_load.assert_called_once_with()

    @patch("controllers.schedule_controller.AddBreakDialog")
    def test_add_break_cancelled(self, MockDlg: MagicMock, ctrl: ScheduleController) -> None:
        """Cancelar el dialogo no guarda nada."""
        inst = MockDlg.return_value
        inst.exec.return_value = QDialog.DialogCode.Rejected

        ctrl.on_add_break_clicked()

        assert ctrl.db.config_repo.set_setting.call_count == 0
        ctrl.db.config_repo.set_setting.assert_not_called()


# ---------------------------------------------------------------------------
# TestOnRemoveBreakClicked
# ---------------------------------------------------------------------------

class TestOnRemoveBreakClicked:
    """Tests para on_remove_break_clicked."""

    @pytest.fixture
    def ctrl(self) -> ScheduleController:
        """ScheduleController con dependencias mockeadas."""
        return _make_controller()

    def test_remove_break_no_settings_widget(self, ctrl: ScheduleController) -> None:
        """Retorno temprano cuando la pagina no es SettingsWidget."""
        ctrl.view.pages = {"settings": None}
        ctrl.on_remove_break_clicked()
        assert ctrl.view.show_message.call_count == 0
        ctrl.view.show_message.assert_not_called()

    def test_remove_break_no_selection(self, ctrl: ScheduleController) -> None:
        """Muestra aviso cuando no hay seleccion."""
        mock_page = _make_settings_page()
        mock_page.breaks_list.selectedItems.return_value = []
        ctrl.view.pages = {"settings": mock_page}

        ctrl.on_remove_break_clicked()

        assert ctrl.view.show_message.call_count == 1
        ctrl.view.show_message.assert_called_with(
            "Selección Requerida",
            "Seleccione un descanso de la lista para eliminar.",
            "warning"
        )

    def test_remove_break_confirmed(self, ctrl: ScheduleController) -> None:
        """Elimina el descanso cuando el usuario confirma."""
        mock_page = _make_settings_page()
        mock_item = MagicMock(spec=['text'])
        mock_item.text.return_value = "10:00 - 10:30"
        mock_page.breaks_list.selectedItems.return_value = [mock_item]
        mock_page.breaks_list.row.return_value = 0
        ctrl.view.pages = {"settings": mock_page}
        ctrl.view.show_confirmation_dialog.return_value = True

        with patch.object(ctrl, "save_schedule_settings", autospec=True) as mock_save:
            ctrl.on_remove_break_clicked()

        assert mock_page.breaks_list.takeItem.call_count == 1
        assert mock_save.call_count == 1
        assert mock_page._update_break_buttons_state.call_count == 1
        mock_page.breaks_list.takeItem.assert_called_once_with(0)
        mock_save.assert_called_once_with()
        ctrl.view.show_message.assert_called_with("Éxito", "Descanso eliminado correctamente.", "info")
        mock_page._update_break_buttons_state.assert_called_once_with()

    def test_remove_break_rejected(self, ctrl: ScheduleController) -> None:
        """No elimina el descanso cuando el usuario rechaza la confirmacion."""
        mock_page = _make_settings_page()
        mock_item = MagicMock(spec=['text'])
        mock_item.text.return_value = "10:00 - 10:30"
        mock_page.breaks_list.selectedItems.return_value = [mock_item]
        ctrl.view.pages = {"settings": mock_page}
        ctrl.view.show_confirmation_dialog.return_value = False

        ctrl.on_remove_break_clicked()

        assert mock_page.breaks_list.takeItem.call_count == 0
        mock_page.breaks_list.takeItem.assert_not_called()


# ---------------------------------------------------------------------------
# TestOnEditBreakClicked
# ---------------------------------------------------------------------------

class TestOnEditBreakClicked:
    """Tests para on_edit_break_clicked."""

    @pytest.fixture
    def ctrl(self) -> ScheduleController:
        """ScheduleController con dependencias mockeadas."""
        return _make_controller()

    def test_edit_break_no_settings_widget(self, ctrl: ScheduleController) -> None:
        """Retorno temprano cuando la pagina no es SettingsWidget."""
        ctrl.view.pages = {"settings": None}
        ctrl.on_edit_break_clicked()
        assert ctrl.view.show_message.call_count == 0
        ctrl.view.show_message.assert_not_called()

    def test_edit_break_no_selection(self, ctrl: ScheduleController) -> None:
        """Muestra aviso cuando no hay seleccion."""
        mock_page = _make_settings_page()
        mock_page.breaks_list.selectedItems.return_value = []
        ctrl.view.pages = {"settings": mock_page}

        ctrl.on_edit_break_clicked()

        assert ctrl.view.show_message.call_count == 1
        ctrl.view.show_message.assert_called_with(
            "Selección Requerida",
            "Seleccione un descanso de la lista para editar.",
            "warning"
        )

    def test_edit_break_parse_error(self, ctrl: ScheduleController) -> None:
        """Muestra error cuando el texto del descanso no se puede parsear."""
        mock_page = _make_settings_page()
        mock_item = MagicMock(spec=['text'])
        mock_item.text.return_value = "INVALID_TEXT_NO_DASH"
        mock_page.breaks_list.selectedItems.return_value = [mock_item]
        ctrl.view.pages = {"settings": mock_page}

        ctrl.on_edit_break_clicked()

        assert ctrl.view.show_message.call_count == 1
        ctrl.view.show_message.assert_called_with(
            "Error", "No se pudo leer la hora del descanso seleccionado.", "critical"
        )

    @patch("controllers.schedule_controller.AddBreakDialog")
    def test_edit_break_accepted(self, MockDlg: MagicMock, ctrl: ScheduleController) -> None:
        """Editar y confirmar actualiza el item y guarda."""
        mock_page = _make_settings_page()
        mock_item = MagicMock(spec=['text', 'setText'])
        mock_item.text.return_value = "10:00 - 10:30"
        mock_page.breaks_list.selectedItems.return_value = [mock_item]
        ctrl.view.pages = {"settings": mock_page}

        inst = MockDlg.return_value
        inst.exec.return_value = QDialog.DialogCode.Accepted
        inst.get_times.return_value = {"start": "11:00", "end": "11:30"}

        with patch.object(ctrl, "save_schedule_settings", autospec=True) as mock_save:
            ctrl.on_edit_break_clicked()

        assert mock_item.setText.call_count == 1
        assert mock_save.call_count == 1
        assert mock_page._update_break_buttons_state.call_count == 1
        mock_item.setText.assert_called_once_with("11:00 - 11:30")
        mock_save.assert_called_once_with()
        ctrl.view.show_message.assert_called_with("Éxito", "Descanso actualizado correctamente.", "info")
        mock_page._update_break_buttons_state.assert_called_once_with()

    @patch("controllers.schedule_controller.AddBreakDialog")
    def test_edit_break_cancelled(self, MockDlg: MagicMock, ctrl: ScheduleController) -> None:
        """Cancelar la edicion no modifica el item."""
        mock_page = _make_settings_page()
        mock_item = MagicMock(spec=['text', 'setText'])
        mock_item.text.return_value = "10:00 - 10:30"
        mock_page.breaks_list.selectedItems.return_value = [mock_item]
        ctrl.view.pages = {"settings": mock_page}

        inst = MockDlg.return_value
        inst.exec.return_value = QDialog.DialogCode.Rejected

        ctrl.on_edit_break_clicked()

        assert mock_item.setText.call_count == 0
        mock_item.setText.assert_not_called()


# ---------------------------------------------------------------------------
# TestOnAddBreak
# ---------------------------------------------------------------------------

class TestOnAddBreak:
    """Tests para on_add_break (dialogo inline)."""

    @pytest.fixture
    def ctrl(self) -> ScheduleController:
        """ScheduleController con dependencias mockeadas."""
        return _make_controller()

    def test_on_add_break_accepted(self, ctrl: ScheduleController) -> None:
        """Aceptar el dialogo inline anade item a la lista de descansos."""
        mock_settings = MagicMock(spec=['breaks_list'])
        ctrl.view.pages = {"settings": mock_settings}

        mock_dialog = MagicMock(spec=['exec', 'setWindowTitle', 'setLayout', 'accept', 'reject'])
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_qd_class = MagicMock(spec=['DialogCode'], return_value=mock_dialog)
        mock_qd_class.DialogCode = QDialog.DialogCode

        with patch("controllers.schedule_controller.QDialog", mock_qd_class), \
             patch("controllers.schedule_controller.QFormLayout"), \
             patch("controllers.schedule_controller.QTimeEdit"), \
             patch("controllers.schedule_controller.QDialogButtonBox"):
            ctrl.on_add_break()

        assert mock_settings.breaks_list.addItem.call_count == 1
        mock_settings.breaks_list.addItem.assert_called_once_with(ANY)

    def test_on_add_break_cancelled(self, ctrl: ScheduleController) -> None:
        """Cancelar el dialogo inline no anade ningun item."""
        mock_settings = MagicMock(spec=['breaks_list'])
        ctrl.view.pages = {"settings": mock_settings}

        mock_dialog = MagicMock(spec=['exec', 'setWindowTitle', 'setLayout', 'accept', 'reject'])
        mock_dialog.exec.return_value = QDialog.DialogCode.Rejected
        mock_qd_class = MagicMock(spec=['DialogCode'], return_value=mock_dialog)
        mock_qd_class.DialogCode = QDialog.DialogCode

        with patch("controllers.schedule_controller.QDialog", mock_qd_class), \
             patch("controllers.schedule_controller.QFormLayout"), \
             patch("controllers.schedule_controller.QTimeEdit"), \
             patch("controllers.schedule_controller.QDialogButtonBox"):
            ctrl.on_add_break()

        assert mock_settings.breaks_list.addItem.call_count == 0
        mock_settings.breaks_list.addItem.assert_not_called()


# ---------------------------------------------------------------------------
# TestSaveScheduleSettings
# ---------------------------------------------------------------------------

class TestSaveScheduleSettings:
    """Tests para save_schedule_settings."""

    @pytest.fixture
    def ctrl(self) -> ScheduleController:
        """ScheduleController con dependencias mockeadas."""
        return _make_controller()

    def test_save_schedule_settings_success(self, ctrl: ScheduleController) -> None:
        """Guarda la configuracion de horario y muestra mensaje de exito."""
        mock_page = MagicMock(spec=['work_start_time', 'work_end_time', 'breaks_list'])
        mock_page.work_start_time.time.return_value.toString.return_value = "08:00"
        mock_page.work_end_time.time.return_value.toString.return_value = "16:00"
        mock_page.breaks_list.count.return_value = 2
        mock_page.breaks_list.item.side_effect = [
            MagicMock(**{"text.return_value": "10:00 - 10:30"}),
            MagicMock(**{"text.return_value": "13:00 - 14:00"}),
        ]
        ctrl.view.pages = {"settings": mock_page}

        ctrl.save_schedule_settings()

        assert ctrl.db.config_repo.set_setting.call_count == 3
        assert ctrl.schedule_manager.reload_config.call_count == 1
        ctrl.schedule_manager.reload_config.assert_called_once_with(ctrl.db)
        ctrl.view.show_message.assert_called_with("Éxito", "Horario completo guardado y aplicado.", "info")

    def test_schedule_settings_dto_validation(self, ctrl: ScheduleController) -> None:
        """Verifica que ConfigurationDTO valida la forma de la configuracion."""
        config = ConfigurationDTO(clave="work_start_time", valor="08:00")
        assert isinstance(config, ConfigurationDTO)
        assert config.clave == "work_start_time"
        assert config.valor == "08:00"


# ---------------------------------------------------------------------------
# TestLoadScheduleSettings
# ---------------------------------------------------------------------------

class TestLoadScheduleSettings:
    """Tests para load_schedule_settings."""

    @pytest.fixture
    def ctrl(self) -> ScheduleController:
        """ScheduleController con dependencias mockeadas."""
        return _make_controller()

    def test_load_schedule_settings_no_widget(self, ctrl: ScheduleController) -> None:
        """Retorno temprano si SettingsWidget no esta presente."""
        ctrl.view.pages = {"settings": None}
        ctrl.load_schedule_settings()
        assert ctrl.db.config_repo.get_setting.call_count == 0
        ctrl.db.config_repo.get_setting.assert_not_called()

    def test_load_schedule_settings_success(self, ctrl: ScheduleController) -> None:
        """Carga la configuracion valida en la UI."""
        mock_page = _make_settings_page()
        ctrl.view.pages = {"settings": mock_page}
        ctrl.db.config_repo.get_setting.side_effect = [
            "09:00", "17:00",
            '[{"start": "12:00", "end": "13:00"}]'
        ]

        ctrl.load_schedule_settings()

        assert mock_page.work_start_time.setTime.call_count == 1
        assert mock_page.work_end_time.setTime.call_count == 1
        assert mock_page.breaks_list.clear.call_count == 1
        assert mock_page.breaks_list.addItem.call_count == 1
        mock_page.work_start_time.setTime.assert_called_once_with(ANY)
        mock_page.work_end_time.setTime.assert_called_once_with(ANY)
        mock_page.breaks_list.clear.assert_called_once_with()
        mock_page.breaks_list.addItem.assert_called_once_with("12:00 - 13:00")

    def test_load_schedule_settings_json_error(self, ctrl: ScheduleController) -> None:
        """Fallback cuando el JSON de descansos esta malformado — usa valor por defecto."""
        mock_page = _make_settings_page()
        ctrl.view.pages = {"settings": mock_page}
        ctrl.db.config_repo.get_setting.side_effect = [
            "08:00", "15:15",
            "NOT_VALID_JSON{{{{{{"
        ]

        ctrl.load_schedule_settings()

        # Con JSON invalido no se llama clear() pero si addItem con el valor por defecto
        assert mock_page.breaks_list.addItem.call_count == 1
        mock_page.breaks_list.addItem.assert_called_once_with("12:00 - 13:00")


# ---------------------------------------------------------------------------
# TestHolidayMethods
# ---------------------------------------------------------------------------

class TestHolidayMethods:
    """Tests para on_add_holiday y on_remove_holiday."""

    @pytest.fixture
    def ctrl(self) -> ScheduleController:
        """ScheduleController con dependencias mockeadas."""
        return _make_controller()

    def test_add_holiday_new_date(self, ctrl: ScheduleController) -> None:
        """Anade un nuevo festivo a la configuracion."""
        mock_page = MagicMock(spec=['calendar'])
        mock_page.calendar.selectedDate.return_value.toPyDate.return_value = datetime.date(2025, 5, 1)
        ctrl.view.pages = {"settings": mock_page}
        ctrl.db.config_repo.get_setting.return_value = "[]"

        with patch.object(ctrl, "load_schedule_settings", autospec=True) as mock_load:
            ctrl.on_add_holiday()

        assert ctrl.db.config_repo.set_setting.call_count == 1
        assert ctrl.schedule_manager.reload_config.call_count == 1
        assert mock_load.call_count == 1
        ctrl.schedule_manager.reload_config.assert_called_once_with(ctrl.db)
        mock_load.assert_called_once_with()
        ctrl.view.show_message.assert_called_with("Éxito", "Día 01/05/2025 añadido como festivo.", "info")

    def test_add_holiday_duplicate(self, ctrl: ScheduleController) -> None:
        """No re-anade un festivo duplicado."""
        mock_page = MagicMock(spec=['calendar'])
        mock_page.calendar.selectedDate.return_value.toPyDate.return_value = datetime.date(2025, 5, 1)
        ctrl.view.pages = {"settings": mock_page}
        ctrl.db.config_repo.get_setting.return_value = '["2025-05-01"]'

        ctrl.on_add_holiday()

        assert ctrl.db.config_repo.set_setting.call_count == 0
        ctrl.db.config_repo.set_setting.assert_not_called()

    def test_remove_holiday_exists(self, ctrl: ScheduleController) -> None:
        """Elimina un festivo existente de la lista."""
        mock_page = MagicMock(spec=['calendar'])
        mock_page.calendar.selectedDate.return_value.toPyDate.return_value = datetime.date(2025, 5, 1)
        ctrl.view.pages = {"settings": mock_page}
        ctrl.db.config_repo.get_setting.return_value = '["2025-04-15", "2025-05-01"]'

        with patch.object(ctrl, "load_schedule_settings", autospec=True) as mock_load:
            ctrl.on_remove_holiday()

        assert ctrl.db.config_repo.set_setting.call_count == 1
        assert ctrl.schedule_manager.reload_config.call_count == 1
        assert mock_load.call_count == 1
        ctrl.schedule_manager.reload_config.assert_called_once_with(ctrl.db)
        mock_load.assert_called_once_with()
        ctrl.view.show_message.assert_called_with("Éxito", "Día 01/05/2025 eliminado de festivos.", "info")

    def test_remove_holiday_not_in_list(self, ctrl: ScheduleController) -> None:
        """No hace nada cuando la fecha no esta en la lista."""
        mock_page = MagicMock(spec=['calendar'])
        mock_page.calendar.selectedDate.return_value.toPyDate.return_value = datetime.date(2025, 5, 1)
        ctrl.view.pages = {"settings": mock_page}
        ctrl.db.config_repo.get_setting.return_value = '["2025-04-15"]'

        ctrl.on_remove_holiday()

        assert ctrl.db.config_repo.set_setting.call_count == 0
        ctrl.db.config_repo.set_setting.assert_not_called()
