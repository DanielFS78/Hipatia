# -*- coding: utf-8 -*-
"""Tests unitarios para `SettingsWidget` con delegación a `ScheduleController`."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import create_autospec

import pytest

from PyQt6.QtCore import QTime

from controllers.schedule_controller import ScheduleController
from ui.widgets.settings_widget import SettingsWidget

pytestmark = pytest.mark.unit


@pytest.fixture
def schedule_controller() -> ScheduleController:
    """Mock estricto de `ScheduleController` con defaults de configuración."""
    ctrl = create_autospec(ScheduleController, instance=True)
    ctrl.config_get_setting.side_effect = lambda key, default="": {
        "backup_time": "03:00",
    }.get(key, default)
    return ctrl


@pytest.fixture
def widget(qtbot, schedule_controller: ScheduleController) -> SettingsWidget:
    """Instancia real de widget con controlador de horarios mockeado."""
    w = SettingsWidget(schedule_controller=schedule_controller)
    qtbot.addWidget(w)
    return w


@pytest.mark.unit
class TestSettingsWidget:
    """Cobertura de inicialización, delegación y comportamiento sin controlador."""

    def test_init_loads_schedule_settings(self, qtbot, schedule_controller: ScheduleController) -> None:
        """Al inicializar con controlador se delega la carga de configuración."""
        widget = SettingsWidget(schedule_controller=schedule_controller)
        qtbot.addWidget(widget)
        cast(Any, schedule_controller).load_schedule_settings.assert_called_once_with()
        cast(Any, schedule_controller).config_get_setting.assert_called_once_with("backup_time", "03:00")

    def test_update_break_buttons_state_with_and_without_selection(self, widget: SettingsWidget) -> None:
        """Los botones de descanso se habilitan solo con selección."""
        widget._update_break_buttons_state()
        assert not widget.btn_edit_break.isEnabled()
        assert not widget.btn_remove_break.isEnabled()

        widget.breaks_list.addItem("08:00 - 09:00")
        widget.breaks_list.setCurrentRow(0)
        widget._update_break_buttons_state()
        assert widget.btn_edit_break.isEnabled()
        assert widget.btn_remove_break.isEnabled()

    def test_break_actions_delegate_to_schedule_controller(
        self, widget: SettingsWidget, schedule_controller: ScheduleController
    ) -> None:
        """Las acciones de descansos delegan en el controlador de horarios."""
        widget.on_add_break_clicked()
        widget.on_edit_break_clicked()
        widget.on_remove_break_clicked()

        cast(Any, schedule_controller).on_add_break_clicked.assert_called_once_with()
        cast(Any, schedule_controller).on_edit_break_clicked.assert_called_once_with()
        cast(Any, schedule_controller).on_remove_break_clicked.assert_called_once_with()

    def test_holiday_actions_delegate_to_schedule_controller(
        self, widget: SettingsWidget, schedule_controller: ScheduleController
    ) -> None:
        """Las acciones de festivos delegan en el controlador de horarios."""
        widget.on_add_holiday_clicked()
        widget.on_remove_holiday_clicked()

        cast(Any, schedule_controller).on_add_holiday.assert_called_once_with()
        cast(Any, schedule_controller).on_remove_holiday.assert_called_once_with()

    def test_save_all_delegates_and_persists_backup_time(
        self, widget: SettingsWidget, schedule_controller: ScheduleController
    ) -> None:
        """Guardar todo delega el horario y guarda `backup_time`."""
        widget.backup_time.setTime(QTime(4, 45))

        widget.on_save_all_clicked()

        cast(Any, schedule_controller).save_schedule_settings.assert_called_once_with()
        cast(Any, schedule_controller).config_set_setting.assert_called_once_with("backup_time", "04:45")

    def test_load_schedule_settings_reads_backup_time(
        self, widget: SettingsWidget, schedule_controller: ScheduleController
    ) -> None:
        """La carga usa `config_get_setting` para `backup_time`."""
        cast(Any, schedule_controller).load_schedule_settings.reset_mock()
        cast(Any, schedule_controller).config_get_setting.reset_mock()

        widget.load_schedule_settings()

        cast(Any, schedule_controller).load_schedule_settings.assert_called_once_with()
        cast(Any, schedule_controller).config_get_setting.assert_called_once_with("backup_time", "03:00")
        assert widget.backup_time.time().toString("HH:mm") == "03:00"

    def test_set_controller_uses_schedule_controller_attribute(self, qtbot) -> None:
        """`set_controller` usa `controller.schedule_controller` cuando existe."""
        w = SettingsWidget()
        qtbot.addWidget(w)
        ctrl = create_autospec(ScheduleController, instance=True)
        ctrl.config_get_setting.return_value = "03:00"

        class DummyAppController:
            """Doble simple con atributo schedule_controller."""

            def __init__(self, schedule_controller: ScheduleController) -> None:
                self.schedule_controller = schedule_controller

        app_controller = DummyAppController(ctrl)

        w.set_controller(app_controller)

        assert w.schedule_controller is ctrl
        cast(Any, ctrl).load_schedule_settings.assert_called_once_with()

    def test_methods_are_safe_without_controller(self, qtbot) -> None:
        """Sin controlador asignado, los handlers deben retornar sin excepción."""
        w = SettingsWidget()
        qtbot.addWidget(w)

        w.on_add_break_clicked()
        w.on_edit_break_clicked()
        w.on_remove_break_clicked()
        w.on_add_holiday_clicked()
        w.on_remove_holiday_clicked()
        w.on_save_all_clicked()
        w.load_schedule_settings()

        assert w.schedule_controller is None
