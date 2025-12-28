"""
Tests unitarios para PilaController - Simulaciones y Optimización.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, date
from PyQt6.QtCore import QThread, QObject
from PyQt6.QtWidgets import QDialog
from ui.widgets import CalculateTimesWidget, DefinirLoteWidget
from ui.dialogs import GetOptimizationParametersDialog, LoadPilaDialog, SavePilaDialog

from controllers.pila_controller import PilaController, OptimizerWorker

@pytest.fixture
def mock_app():
    app = MagicMock()
    app.model = MagicMock()
    app.view = MagicMock()
    app.view.pages = {}
    app.schedule_manager = MagicMock()
    return app

@pytest.fixture
def controller(mock_app):
    # Usar spec=CalculateTimesWidget para que isinstance(mock_calc, CalculateTimesWidget) sea True
    mock_calc = MagicMock(spec=CalculateTimesWidget)
    # Mockear explícitamente los atributos que se usan en el controlador
    # (ya que spec= solo incluye atributos de CLASE, no los creados en __init__)
    mock_calc.save_pila_button = MagicMock()
    mock_calc.export_button = MagicMock()
    mock_calc.export_pdf_button = MagicMock()
    mock_calc.export_log_button = MagicMock()
    mock_calc.clear_button = MagicMock()
    mock_calc.go_home_button = MagicMock()
    mock_calc.execute_manual_button = MagicMock()
    mock_calc.execute_optimizer_button = MagicMock()
    mock_calc.define_flow_button = MagicMock()
    mock_calc.manage_bitacora_button = MagicMock()
    mock_calc.lote_search_results = MagicMock()
    mock_calc.pila_content_table = MagicMock()
    mock_calc.planning_session = []

    mock_app.view.pages = {"calculate": mock_calc}
    return PilaController(mock_app)

class TestPilaControllerSimulation:
    """Tests para el motor de simulación y hilos."""

    def test_on_run_manual_plan_clicked_no_flow(self, controller):
        controller.app.last_production_flow = None
        controller._on_run_manual_plan_clicked()
        controller.view.show_message.assert_called_with("Flujo no Definido", ANY, "warning")

    @patch('controllers.pila_controller.AdaptadorScheduler')
    def test_run_manual_plan_success(self, MockScheduler, controller):
        controller.app.last_production_flow = [{"step": 1}]
        
        # Simular máquinas y trabajadores
        controller.model.get_all_workers.return_value = []
        controller.model.get_all_machines.return_value = []
        
        with patch.object(controller, '_start_simulation_thread') as mock_start:
            controller._on_run_manual_plan_clicked()
            mock_start.assert_called_once()
            MockScheduler.assert_called_once()

    def test_start_simulation_thread(self, controller):
        mock_scheduler = MagicMock()
        mock_calc = controller.view.pages["calculate"]
        
        with patch('controllers.pila_controller.QThread.start'):
            controller._start_simulation_thread(mock_scheduler)
            assert controller.thread is not None
            mock_calc.show_progress.assert_called_once()

    def test_on_simulation_finished(self, controller):
        results = [{"Tarea": "T1", "Inicio": "2023-01-01T08:00:00"}]
        audit = ["Log 1"]
        mock_calc = controller.view.pages["calculate"]
        
        controller._on_simulation_finished(results, audit)
        
        # Como app es un MagicMock, last_simulation_results ahora tendrá el valor asignado
        assert controller.app.last_simulation_results == results
        mock_calc.display_simulation_results.assert_called_with(results, audit)
        mock_calc.save_pila_button.setEnabled.assert_called_with(True)

class TestPilaControllerOptimization:
    """Tests para la lógica del Optimizador."""

    @patch('controllers.pila_controller.GetOptimizationParametersDialog')
    @patch('controllers.pila_controller.Optimizer')
    def test_execute_optimizer_simulation_success(self, MockOptimizer, MockDialog, controller):
        mock_calc = controller.view.pages["calculate"]
        mock_calc.planning_session = [{"unidades": 1}]
        
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = True
        mock_dlg.get_parameters.return_value = {
            "start_date": date(2023, 1, 1),
            "end_date": date(2023, 1, 10),
            "units": 10
        }
        MockDialog.return_value = mock_dlg
        
        with patch('controllers.pila_controller.QThread.start'):
            controller._on_execute_optimizer_simulation_clicked()
            
            assert mock_calc.planning_session[0]['unidades'] == 10
            MockOptimizer.assert_called_once()

    def test_on_optimization_finished_success(self, controller):
        results = [{"id": 1}]
        audit = []
        
        controller._on_optimization_finished(results, audit, 2)
        
        assert controller.app.last_flexible_workers_needed == 2
        controller.view.show_message.assert_called_with("Resultado Optimización", ANY, "info")

class TestOptimizerWorker:
    """Tests para la clase interna OptimizerWorker."""

    def test_run(self):
        mock_optimizer = MagicMock()
        mock_optimizer.model.machine_repo.get_all_machines.return_value = []
        mock_optimizer._verify_deadlines.return_value = True
        
        with patch('controllers.pila_controller.AdaptadorScheduler') as MockSched:
            mock_sched_instance = MockSched.return_value
            mock_sched_instance.run_simulation.return_value = ([], [])
            
            worker = OptimizerWorker(mock_optimizer, datetime.now(), datetime.now(), 1)
            
            # Mockear la señal finihed.emit
            worker.finished = MagicMock()
            
            worker.run()
            
            worker.finished.emit.assert_called()

class TestPilaControllerPersistence:
    """Tests para carga y guardado de Pilas (Snapshots)."""

    @patch('controllers.pila_controller.LoadPilaDialog')
    def test_on_load_pila_clicked_success(self, MockDialog, controller):
        # Configurar repo
        controller.model.pila_repo.get_all_pilas.return_value = [{"id": 1, "nombre": "P1"}]
        
        # Configurar diálogo
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = True
        mock_dlg.get_selected_id.return_value = 1
        mock_dlg.delete_requested = False
        MockDialog.return_value = mock_dlg
        
        # Simular datos cargados
        meta = {"nombre": "Test Pila", "unidades": 5}
        controller.model.pila_repo.load_pila.return_value = (meta, [], [{"task": {}}], [])
        
        with patch.object(controller, '_open_editor_with_loaded_flow') as mock_open:
            controller._on_load_pila_clicked()
            
            assert controller.app.last_pila_id_calculated == 1
            mock_open.assert_called_with(ANY, "Test Pila", 5)

    @patch('controllers.pila_controller.SavePilaDialog')
    def test_on_save_pila_clicked_success(self, MockDialog, controller):
        # Debe haber un flujo definido
        controller.app.last_production_flow = [{"step": 1}]
        
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = QDialog.DialogCode.Accepted
        mock_dlg.get_data.return_value = ("Mi Pila", "Desc")
        MockDialog.return_value = mock_dlg
        
        controller.model.save_pila.return_value = 123
        
        controller._on_save_pila_clicked()
        
        
        controller._on_save_pila_clicked()
        
    @patch('controllers.pila_controller.FabricacionBitacoraDialog')
    def test_on_ver_bitacora_pila_clicked(self, MockDialog, controller):
        mock_calc = controller.view.pages["calculate"]
        mock_calc.last_pila_id = 999
        
        controller.model.pila_repo.load_pila.return_value = ({"nombre": "P1"}, None, [])
        
        controller._on_ver_bitacora_pila_clicked()
        MockDialog.assert_called_once()

    def test_reparse_simulation_results_dates(self, controller):
        results = [{"Tarea": "T1", "Inicio": "2023-01-01T08:00:00Z"}]
        reparsed = controller._reparse_simulation_results_dates(results)
        assert isinstance(reparsed[0]["Inicio"], datetime)

    def test_get_preprocesos_for_fabricacion(self, controller):
        mock_fab = MagicMock()
        mock_p1 = MagicMock(id=1, nombre="P1", descripcion="D1")
        mock_fab.preprocesos = [mock_p1]
        controller.model.preproceso_repo.get_fabricacion_by_id.return_value = mock_fab
        
        res = controller.get_preprocesos_for_fabricacion(1)
        assert len(res) == 1
        assert res[0]["nombre"] == "P1"

class TestPilaControllerLoteComposition:
    """Tests para la creación de plantillas de lotes."""

    def test_add_product_to_lote_template(self, controller):
        mock_page = MagicMock()
        controller.view.pages["definir_lote"] = mock_page
        mock_page.product_results.currentItem().data.return_value = ("PROD1", "Desc")
        mock_page.lote_content = {"products": set()}
        
        controller._on_add_product_to_lote_template()
        
        assert ("PROD1", "Desc") in mock_page.lote_content["products"]
        mock_page.update_content_list.assert_called_once()

    def test_save_lote_template_success(self, controller):
        mock_page = MagicMock(spec=DefinirLoteWidget)
        controller.view.pages["definir_lote"] = mock_page
        mock_page.get_data.return_value = {
            "codigo": "LOTE1",
            "product_codes": ["P1"],
            "fabricacion_ids": []
        }
        controller.model.lote_repo.create_lote.return_value = 1
        
        controller._on_save_lote_template_clicked()
        
        controller.view.show_message.assert_called_with("Éxito", ANY, "info")

class TestPilaControllerVisualEditorHandlers:
    """Tests para los handlers llamados desde el editor visual."""

    @patch('controllers.pila_controller.AdaptadorScheduler')
    def test_handle_run_manual_from_visual_editor(self, MockScheduler, controller):
        mock_dlg = MagicMock()
        mock_dlg.get_production_flow.return_value = [{"task": {"required_skill_level": 1}}]
        
        controller.model.get_all_workers.return_value = [MagicMock(nombre_completo="W1", tipo_trabajador=1)]
        controller.model.get_all_machines.return_value = []
        
        with patch.object(controller, '_start_simulation_thread'):
            controller._handle_run_manual_from_visual_editor(mock_dlg)
            MockScheduler.assert_called_once()

    @patch('controllers.pila_controller.OptimizerWorker')
    @patch('controllers.pila_controller.GetOptimizationParametersDialog')
    def test_handle_run_optimizer_from_visual_editor(self, MockDialog, MockWorker, controller):
        mock_dlg = MagicMock()
        mock_dlg.get_production_flow.return_value = [{"step": 1}]
        
        mock_calc = controller.view.pages["calculate"]
        mock_calc.planning_session = [{"unidades": 1}]
        
        mock_params = MagicMock()
        mock_params.exec.return_value = 1 # QDialog.DialogCode.Accepted
        mock_params.get_parameters.return_value = {
            "start_date": date(2023, 1, 1),
            "end_date": date(2023, 1, 10),
            "units": 10
        }
        MockDialog.return_value = mock_params
        
        with patch('controllers.pila_controller.QThread.start'):
            controller._handle_run_optimizer_from_visual_editor(mock_dlg)
            MockWorker.assert_called_once()

class TestPilaControllerFlowAndState:
    """Tests para definición de flujo y gestión de estado."""

    @patch('controllers.pila_controller.EnhancedProductionFlowDialog')
    def test_on_define_flow_clicked_success(self, MockDialog, controller):
        mock_calc = controller.view.pages["calculate"]
        mock_calc.planning_session = [{"identificador": "L1"}]
        
        controller.model.get_data_for_calculation_from_session.return_value = [{"id": 1}]
        controller.model.get_all_workers.return_value = []
        
        mock_dlg = MockDialog.return_value
        mock_dlg.exec.return_value = True
        mock_dlg.get_production_flow.return_value = [{"step": 1}]
        
        controller._on_define_flow_clicked()
        
        assert controller.app.last_production_flow == [{"step": 1}]
        controller.view.show_message.assert_called_with("Flujo Definido", ANY, "info")

    def test_on_clear_simulation(self, controller):
        mock_calc = controller.view.pages["calculate"]
        controller.app.last_production_flow = [{"step": 1}]
        
        controller._on_clear_simulation()
        
        assert controller.app.last_production_flow is None
        mock_calc.clear_all.assert_called_once()
        mock_calc.define_flow_button.setEnabled.assert_called_with(False)

class TestPilaControllerManagement:
    """Tests para la pestaña de Gestión de Lotes."""

    def test_update_lotes_view(self, controller):
        mock_gest = MagicMock()
        mock_gest.lotes_tab = MagicMock()
        mock_gest.lotes_tab.search_entry.text.return_value = "query"
        controller.view.pages["gestion_datos"] = mock_gest
        
        mock_lote = MagicMock(id=1, codigo="L1", descripcion="Desc")
        controller.model.lote_repo.search_lotes.return_value = [mock_lote]
        
        controller.update_lotes_view()
        
        mock_gest.lotes_tab.results_list.clear.assert_called()
        assert mock_gest.lotes_tab.results_list.addItem.call_count == 1

    @patch('controllers.pila_controller.QListWidgetItem')
    def test_on_lote_management_result_selected(self, MockItem, controller):
        mock_gest = MagicMock()
        controller.view.pages["gestion_datos"] = mock_gest
        
        mock_item = MagicMock()
        mock_item.data.return_value = 123
        
        controller.model.lote_repo.get_lote_details.return_value = {"id": 123, "codigo": "L1"}
        
        controller._on_lote_management_result_selected(mock_item)
        
        mock_gest.lotes_tab.display_lote_details.assert_called_with({"id": 123, "codigo": "L1"})

    def test_on_delete_lote_template_clicked(self, controller):
        controller.view.show_confirmation_dialog.return_value = True
        controller.model.lote_repo.delete_lote.return_value = True
        
        with patch.object(controller, 'update_lotes_view') as mock_update:
            controller._on_delete_lote_template_clicked(123)
            mock_update.assert_called_once()
            controller.view.show_message.assert_called_with("Éxito", ANY, "info")
