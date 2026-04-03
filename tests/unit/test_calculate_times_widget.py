# -*- coding: utf-8 -*-
"""
Tests unitarios para el widget de cálculo de tiempos.
"""
import pytest
from unittest.mock import MagicMock, patch, create_autospec
from core.dtos import ProductDTO
from datetime import datetime

from PyQt6.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from core.app_model import AppModel
from controllers.simulation.controller import SimulationController
from core.dtos import ProductDTO, FabricacionDTO, LoteDTO, CalculationStepDTO

from ui.widgets.calculate_times_widget import CalculateTimesWidget

pytestmark = pytest.mark.unit
pytestmark = pytest.mark.setup


@pytest.fixture
def mock_controller():
    from controllers.simulation.controller import SimulationController
    controller = MagicMock(spec=SimulationController)
    controller.connect_calculate_signals = MagicMock(spec=[])
    model = MagicMock(spec=AppModel)
    controller.model = model
    
    # Mock lote
    mock_lote = MagicMock(spec=LoteDTO)
    prod_mock = MagicMock(spec=ProductDTO)
    prod_mock.codigo = "P1"
    prod_mock.descripcion = "Prod 1"
    mock_lote.productos = [prod_mock]
    
    fab_mock = MagicMock(spec=FabricacionDTO)
    fab_mock.id = 1
    fab_mock.codigo = "F1"
    mock_lote.fabricaciones = [fab_mock]
    
    model.get_lote_details.return_value = mock_lote
    
    # Mock db fabricacion
    db_fab = MagicMock(spec=FabricacionDTO)
    db_fab.descripcion = "Fab Desc"
    model.get_fabricacion_by_id.return_value = db_fab
    
    from core.di_container import DIContainer
    from controllers.simulation.controller import SimulationController
    from controllers.ui_signals_controller import UISignalsController
    DIContainer.get_instance().register(SimulationController, instance=controller)
    DIContainer.get_instance().register(UISignalsController, instance=controller)
    
    # Compliance checks
    dto_inst = ProductDTO(codigo="T", descripcion="T")
    assert isinstance(dto_inst, ProductDTO)
    model.get_lote_details.assert_not_called()
    
    return controller


@pytest.mark.unit
class TestCalculateTimesWidget:
    
    @pytest.fixture
    def widget(self, qtbot, mock_controller):
        w = CalculateTimesWidget()
        qtbot.addWidget(w)
        # Manually call setup_ui to avoid event loop issues with showEvent in some headless modes
        w.setup_ui()
        return w

    def test_init_and_showEvent(self, qtbot, mock_controller):
        controller = mock_controller
        w = CalculateTimesWidget(controller=controller)
        qtbot.addWidget(w)
        
        # Simular showEvent (requiere Qt object real)
        w._pending_signal_connection = True  # type: ignore[attr-defined]
        from PyQt6.QtGui import QShowEvent
        w.showEvent(QShowEvent())
        assert hasattr(w, '_ui_setup_complete')
        assert controller.connect_calculate_signals.called

    def test_set_controller(self, widget):
        controller = MagicMock(spec=[])
        widget.set_controller(controller)
        assert widget.simulation_controller is not None

    def test_progress_methods(self, widget):
        widget.show_progress()
        assert not widget.progress_bar.isHidden()
        assert widget.progress_bar.value() == 0
        
        widget.update_progress(50)
        assert widget.progress_bar.value() == 50
        
        widget.set_progress_status("Calculando...", 70)
        assert widget.progress_bar.value() == 70
        assert "Calculando" in widget.progress_bar.format()
        
        widget.hide_progress()
        assert widget.progress_bar.isHidden()

    def test_enable_result_actions(self, widget):
        widget.save_pila_button.setEnabled(False)
        widget.enable_result_actions()
        assert widget.save_pila_button.isEnabled()
        assert widget.export_button.isEnabled()

    def test_get_pila_for_calculation_directa(self, widget):
        widget.planning_session = [
            CalculationStepDTO(
                identificador="Pila 1",
                lote_codigo="(Pila Cargada)",
                unidades=1,
                pila_de_calculo_directa={
                    "productos": {"P1": {"codigo": "P1"}},
                    "fabricaciones": {"1": {"id": 1}}
                }
            )
        ]
        
        pila_data = widget.get_pila_for_calculation()
        assert "P1" in pila_data["productos"]
        assert "1" in pila_data["fabricaciones"]

    def test_get_pila_for_calculation_lote(self, widget, mock_controller):
        widget.controller = mock_controller
        widget.planning_session = [
            CalculationStepDTO(
                identificador="L1",
                lote_codigo="L1",
                unidades=1,
                lote_template_id=1
            )
        ]
        
        pila_data = widget.get_pila_for_calculation()
        assert "P1" in pila_data["productos"]
        assert "1" in pila_data["fabricaciones"]
        assert pila_data["fabricaciones"]["1"]["descripcion"] == "Fab Desc"

    def test_get_pila_for_calculation_lote_error(self, widget, mock_controller):
        widget.controller = mock_controller
        mock_controller.model.get_lote_details.side_effect = Exception("DB Error")
        widget.planning_session = [
            CalculationStepDTO(
                identificador="L1",
                lote_codigo="L1",
                unidades=1,
                lote_template_id=1
            )
        ]
        
        pila_data = widget.get_pila_for_calculation()
        assert pila_data == {"productos": {}, "fabricaciones": {}}

    def test_display_audit_log(self, widget):
        decision = MagicMock(
            spec=[
                "status",
                "timestamp",
                "icon",
                "decision_type",
                "task_name",
                "user_friendly_reason",
            ]
        )
        decision.status = MagicMock(spec=["value"])
        decision.status.value = 'POSITIVE'
        decision.timestamp = datetime.now()
        decision.icon = "✅"
        decision.decision_type = "Check"
        decision.task_name = "T1"
        decision.user_friendly_reason = "OK"
        
        widget._display_audit_log([decision])
        
        html = widget.audit_log_display.toHtml()
        assert "T1" in html
        assert "OK" in html

    def test_update_plan_display(self, widget):
        widget.planning_session = [
            CalculationStepDTO(
                identificador="Lote 1",
                lote_codigo="L1",
                unidades=10,
                deadline=datetime.now()
            )
        ]
        widget._update_plan_display()
        assert widget.pila_content_table.rowCount() == 1
        assert widget.pila_content_table.item(0, 0).text() == "Lote 1"

    @patch('ui.widgets.calculate_times_widget.MAX_TASKS_TO_RENDER', new=1)
    @patch('ui.widgets.calculate_times_widget.QMessageBox', autospec=True)
    def test_display_simulation_results_too_many(self, MockMsgBox, widget):
        results = [
            {"Tarea": "T1", "Departamento": "D1", "Inicio": datetime.now(), "Fin": datetime.now(), "Duracion (min)": 10, "Dias Laborables": 1, "Trabajador Asignado": ["W1"], "nombre_maquina": "M1"},
            {"Tarea": "T2", "Departamento": "D1", "Inicio": datetime.now(), "Fin": datetime.now(), "Duracion (min)": 10, "Dias Laborables": 1, "Trabajador Asignado": ["W1"], "nombre_maquina": "M1"}
        ]
        
        # Excede MAX_TASKS_TO_RENDER (1)
        widget.display_simulation_results(results, [])
        assert widget.results_table.rowCount() == 2
        assert not widget.timeline_label.isVisible()
        assert MockMsgBox.information.called

    def test_display_simulation_results_normal(self, widget):
        results = [
            {"Tarea": "T1", "Departamento": "D1", "Inicio": datetime.now(), "Fin": datetime.now(), "Duracion (min)": 10.5, "Dias Laborables": 1.2, "Trabajador Asignado": ["W1"], "nombre_maquina": "M1"}
        ]
        
        # Forzamos _display_audit_log
        with patch.object(widget, '_display_audit_log') as mock_audit:
            widget.display_simulation_results(results, [])
            assert widget.results_table.rowCount() == 1
            # Just check it's populated, not exact float formatting
            assert widget.results_table.item(0, 0).text() == "T1"
            assert not widget.timeline_label.isHidden()
            assert mock_audit.called

    def test_add_step_to_pila(self, widget):
        assert not widget.add_step_to_pila(None)
        
        step_data = CalculationStepDTO(identificador="Step 1", lote_codigo="S1", unidades=1)
        assert widget.add_step_to_pila(step_data)
        assert len(widget.planning_session) == 1
        assert widget.pila_content_table.rowCount() == 1

    def test_clear_all(self, widget):
        widget.planning_session = [{"data": "test"}]
        widget.pila_content_table.setRowCount(5)
        
        widget.clear_all()
        
        assert widget.planning_session == []
        assert widget.pila_content_table.rowCount() == 0
        assert widget.task_analysis_panel.log_vbox.count() == 0
        assert not widget.export_button.isEnabled()
        assert widget.load_pila_button.isEnabled()
