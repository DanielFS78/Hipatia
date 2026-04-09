"""
Tests para ui/dialogs/fabrication/bitacora_dialog.py — Subfase 6.D.1
"""
import pytest
from unittest.mock import ANY, MagicMock, create_autospec, patch
from datetime import date, datetime, timedelta
from typing import Any
from PyQt6.QtCore import Qt
from ui.dialogs.fabrication.bitacora_dialog import FabricacionBitacoraDialog
from ui.dialogs.fabrication.ui_dialog_protocols import ShowsUserMessage
from core.dtos import SimulationResultTaskDTO

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def mock_qtextcharformat(monkeypatch):
    monkeypatch.setattr("PyQt6.QtGui.QTextCharFormat.setBackground", MagicMock(spec=[]))

@pytest.fixture
def mock_dependencies():
    ctrl = MagicMock(spec=['model', 'view', 'pila_controller'])
    pf = MagicMock(spec=['get_diario_bitacora', 'add_diario_evento'])
    pf.get_diario_bitacora.return_value = ([], [])
    pf.add_diario_evento.return_value = True
    ctrl.model = MagicMock(spec=['planning_facade'])
    ctrl.model.planning_facade = pf
    ctrl.pila_controller = None
    ctrl.view = MagicMock(spec=['show_message'])
    
    calc = MagicMock(spec=['find_next_workday'])
    calc.find_next_workday.side_effect = lambda d: d + timedelta(days=1)
    
    return ctrl, calc

@pytest.fixture
def dialog_and_data(mock_dependencies):
    ctrl, calc = mock_dependencies
    sim_data = [
        SimulationResultTaskDTO(
            Inicio=datetime.now() + timedelta(days=1),
            Fin=datetime.now() + timedelta(days=2),
            Tarea="T",
        )
    ]
    # PilaDTO mock data
    pila_data = {
        "pila": [1, "Nombre", "Desc", {}, [], [], date.today()] # 6 is start_date
    }
    dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
    return dialog, pila_data

class TestFabricacionBitacoraDialog:
    def test_init_no_sim_data(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        dialog = FabricacionBitacoraDialog(1, "Pila 1", [], ctrl, calc)
        qtbot.addWidget(dialog)
        assert dialog.pila_id == 1
        assert dialog.history_table.rowCount() == 0

    def test_uses_model_pila_service_when_present(self, qtbot):
        """Sin PilaService en DI ni en pila_controller, usar model.pila_service antes que planning_facade."""
        ctrl = MagicMock(spec=['model', 'view', 'pila_controller'])
        ps = MagicMock(spec=['get_diario_bitacora', 'add_diario_evento'])
        ps.get_diario_bitacora.return_value = ([], [])
        pf = MagicMock(spec=['get_diario_bitacora', 'add_diario_evento'])
        ctrl.model = MagicMock(spec=['pila_service', 'planning_facade'])
        ctrl.model.pila_service = ps
        ctrl.model.planning_facade = pf
        ctrl.pila_controller = None
        ctrl.view = MagicMock(spec=['show_message'])
        calc = MagicMock(spec=['find_next_workday'])
        calc.find_next_workday.side_effect = lambda d: d + timedelta(days=1)
        dialog = FabricacionBitacoraDialog(1, "Pila 1", [], ctrl, calc)
        qtbot.addWidget(dialog)
        ps.get_diario_bitacora.assert_called_once_with(1)
        pf.get_diario_bitacora.assert_not_called()

    def test_explicit_pila_service_skips_resolve(self, qtbot):
        ctrl = MagicMock(spec=["model", "view", "pila_controller"])
        pf = MagicMock(spec=["get_diario_bitacora", "add_diario_evento"])
        ctrl.model = MagicMock(spec=["planning_facade"])
        ctrl.model.planning_facade = pf
        ctrl.pila_controller = None
        ctrl.view = MagicMock(spec=["show_message"])
        calc = MagicMock(spec=["find_next_workday"])
        calc.find_next_workday.side_effect = lambda d: d + timedelta(days=1)
        ps = MagicMock(spec=["get_diario_bitacora", "add_diario_evento"])
        ps.get_diario_bitacora.return_value = ([], [])
        with patch(
            "ui.dialogs.fabrication.bitacora_dialog.resolve_pila_service",
            autospec=True,
        ) as mock_resolve:
            dialog = FabricacionBitacoraDialog(
                1, "Pila 1", [], ctrl, calc, pila_service=ps
            )
            qtbot.addWidget(dialog)
            mock_resolve.assert_not_called()
        ps.get_diario_bitacora.assert_called_once_with(1)

    def test_init_with_sim_data(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        sim_data = [
            SimulationResultTaskDTO(
                Inicio=datetime(2023, 10, 1, 8, 0),
                Fin=datetime(2023, 10, 1, 12, 0),
                Tarea="Task 1",
            )
        ]
        dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
        qtbot.addWidget(dialog)
        assert dialog.pila_id == 1
        
    def test_load_existing_entries(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        ctrl.model.planning_facade.get_diario_bitacora.return_value = ([], [
            ["2023-10-01", 1, "Plan 1", "Real 1", "Notas 1"],
            [date(2023, 10, 2), 2, "Plan 2", "Real 2", "Notas 2"]
        ])
        sim_data = [
            SimulationResultTaskDTO(
                Inicio=datetime(2023, 10, 1, 8, 0),
                Fin=datetime(2023, 10, 1, 12, 0),
                Tarea="Task 1",
            )
        ]
        dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
        qtbot.addWidget(dialog)
        assert len(dialog.bitacora_entries) == 2
        assert dialog.history_table.rowCount() == 2
        
    def test_on_calendar_date_selected(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        ctrl.model.planning_facade.get_diario_bitacora.return_value = ([], [
            [date(2023, 10, 1), 1, "Plan 1", "Real 1", "Notas 1"]
        ])
        sim_data = [
            SimulationResultTaskDTO(
                Inicio=datetime(2023, 10, 1, 8, 0),
                Fin=datetime(2023, 10, 1, 12, 0),
                Tarea="Task 1",
            )
        ]
        dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
        qtbot.addWidget(dialog)
        
        # Select completed date
        dialog.calendar.setSelectedDate(datetime(2023, 10, 1).date())
        dialog._on_calendar_date_selected()
        assert dialog.real_entry.toPlainText() == "Real 1"
        assert dialog.notes_entry.toPlainText() == "Notas 1"
        assert dialog.save_entry_button.text() == "Actualizar Entrada del Día"
        
        # Select empty date in future
        future_date = date.today() + timedelta(days=10)
        dialog.calendar.setSelectedDate(future_date)
        dialog._on_calendar_date_selected()
        assert dialog.real_entry.toPlainText() == ""
        assert dialog.save_entry_button.isEnabled() == False
        
        # Select empty date in past
        past_date = date.today() - timedelta(days=10)
        dialog.calendar.setSelectedDate(past_date)
        dialog._on_calendar_date_selected()
        assert dialog.real_entry.toPlainText() == ""
        assert dialog.save_entry_button.isEnabled() == True

    def test_user_messaging_injected_skips_controller_view(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        msg = create_autospec(ShowsUserMessage, instance=True)
        dialog = FabricacionBitacoraDialog(
            1, "Pila 1", [], ctrl, calc, user_messaging=msg
        )
        qtbot.addWidget(dialog)
        dialog.real_entry.setPlainText("")
        dialog._add_diario_evento()
        msg.show_message.assert_called_once_with(
            "Campo Requerido",
            "El campo 'Trabajo Realizado' no puede estar vacío.",
            "warning",
        )
        ctrl.view.show_message.assert_not_called()

    def test_add_diario_evento_empty_realizado(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        sim_data: list[SimulationResultTaskDTO] = []
        dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
        qtbot.addWidget(dialog)
        
        dialog.real_entry.setPlainText("")
        dialog._add_diario_evento()
        assert ctrl.view.show_message.call_count >= 1
        ctrl.view.show_message.assert_called_with("Campo Requerido", "El campo 'Trabajo Realizado' no puede estar vacío.", "warning")

    def test_add_diario_evento_success(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        sim_data: list[SimulationResultTaskDTO] = []
        dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
        qtbot.addWidget(dialog)
        
        dialog.calendar.setSelectedDate(date(2023, 10, 1))
        dialog._on_calendar_date_selected()
        dialog.plan_entry.setPlainText("Test Plan")
        dialog.real_entry.setPlainText("Test Real")
        dialog.notes_entry.setPlainText("Test Notas")
        
        dialog._add_diario_evento()
        assert ctrl.model.planning_facade.add_diario_evento.call_count == 1
        ctrl.model.planning_facade.add_diario_evento.assert_called_once_with(
            1, date(2023, 10, 1), ANY, "Test Plan", "Test Real", "Test Notas"
        )
        assert ctrl.view.show_message.call_count >= 1
        ctrl.view.show_message.assert_called_with("Éxito", "La entrada del día se ha guardado correctamente.", "info")

    def test_add_diario_evento_failure(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        ctrl.model.planning_facade.add_diario_evento.return_value = False
        sim_data: list[SimulationResultTaskDTO] = []
        dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
        qtbot.addWidget(dialog)
        
        dialog.real_entry.setPlainText("Test Real")
        dialog._add_diario_evento()
        assert ctrl.view.show_message.call_count >= 1
        ctrl.view.show_message.assert_called_with("Error", "No se pudo guardar la entrada en la base de datos.", "critical")

    def test_get_planned_work_for_day(self, qtbot, mock_dependencies):
        ctrl, calc = mock_dependencies
        sim_data = [
            SimulationResultTaskDTO(Inicio=datetime(2023, 10, 1, 8, 0), Fin=datetime(2023, 10, 1, 10, 0), Tarea="Task A"),
            SimulationResultTaskDTO(Inicio=datetime(2023, 10, 1, 10, 0), Fin=datetime(2023, 10, 1, 12, 0), Tarea="Task B"),
            SimulationResultTaskDTO(Inicio=datetime(2023, 10, 2, 8, 0), Fin=datetime(2023, 10, 2, 10, 0), Tarea="Task C"),
        ]
        dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
        qtbot.addWidget(dialog)
        
        work_day_1 = dialog._get_planned_work_for_day(date(2023, 10, 1))
        assert "Task A" in work_day_1
        assert "Task B" in work_day_1
        assert "Task C" not in work_day_1
        
        work_day_other = dialog._get_planned_work_for_day(date(2023, 10, 5))
        assert work_day_other == "No hay trabajo planificado para esta fecha."
    def test_init_with_far_future_date(self, mock_dependencies, qtbot):
        """Test break in date selection if too far in future."""
        ctrl, calc = mock_dependencies
        far_date = date.today() + timedelta(days=400)
        # Mock bitacora entry so it hits the break in __init__
        ctrl.model.planning_facade.get_diario_bitacora.return_value = ([], [
            [far_date, 1, "Plan", "Real", "Note"]
        ])
        sim_data = [
            SimulationResultTaskDTO(
                Inicio=datetime.combine(far_date, datetime.min.time()),
                Fin=datetime.combine(far_date, datetime.min.time()),
                Tarea="T",
            )
        ]
        dialog = FabricacionBitacoraDialog(1, "Pila 1", sim_data, ctrl, calc)
        qtbot.addWidget(dialog)
        assert dialog.calendar.selectedDate().toPyDate() == far_date
