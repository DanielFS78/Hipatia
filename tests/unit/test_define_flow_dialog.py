"""Tests para DefineProductionFlowDialog."""
import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, time
from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtCore import Qt
from types import SimpleNamespace

from core.di_container import DIContainer
from core.services.machine_service import MachineService
from core.services.preparation_service import PreparationService
from ui.dialogs.production_flow.define_flow_dialog import DefineProductionFlowDialog
from core.dtos import WorkerDTO, FlowTaskDataDTO, FlowTaskConfigDTO, ProductionFlowStepDTO
from datetime import date

@pytest.fixture
def mock_dependencies():
    with patch("ui.dialogs.production_flow.define_flow_dialog.MultiWorkerSelectionDialog", autospec=True) as mock_multi, \
         patch("ui.dialogs.production_flow.define_flow_dialog.SavePilaDialog", autospec=True) as mock_save, \
         patch("ui.dialogs.production_flow.define_flow_dialog.QInputDialog") as mock_input, \
         patch("ui.dialogs.production_flow.define_flow_dialog.QMessageBox") as mock_msg:
         mock_msg.StandardButton = QMessageBox.StandardButton
         yield {
             "multi": mock_multi,
             "save": mock_save,
             "input": mock_input,
             "msg": mock_msg
         }

@pytest.fixture
def dialog_data():
    tasks = [
        {
            "codigo": "P1", 
            "descripcion": "Prod 1", 
            "tiene_subfabricaciones": True,
            "sub_partes": [
                {"name": "main_task", "tiempo": 10}
            ]
        }
    ]
    workers = ["W1", "W2"]
    units = 10
    controller = MagicMock(spec=["model", "handle_save_flow_only"])
    controller.model = MagicMock(
        spec=[
            "get_prep_info_for_product",
            "get_machines_by_process_type",
            "get_all_machines",
            "get_groups_for_machine",
            "get_steps_for_group",
        ]
    )
    controller.model.get_prep_info_for_product.return_value = (None, None)
    controller.model.get_all_machines.return_value = []
    controller.model.get_groups_for_machine.return_value = []
    schedule_config = SimpleNamespace(WORK_START_TIME=time(8, 0))
    return tasks, workers, units, controller, schedule_config

@pytest.fixture
def dialog(qtbot, dialog_data, mock_dependencies):
    tasks, workers, units, controller, schedule_config = dialog_data
    dlg = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
    qtbot.addWidget(dlg)
    return dlg

@pytest.mark.unit
class TestDefineProductionFlowDialog:
    
    def test_init_empty(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        assert len(dialog.presenter.get_production_flow()) == 0
        assert dialog.presenter is not None
        assert "P1" in dialog.task_data_by_product

    def test_init_uses_product_controller_fabricacion_when_di_has_machine_prep_only(
        self, qtbot, dialog_data, mock_dependencies
    ):
        """Si DI tiene Machine+Preparation pero no FabricacionService, usar product_controller."""
        tasks, workers, units, controller, schedule_config = dialog_data
        container = DIContainer.get_instance()
        container.register(MachineService, instance=MagicMock(spec=MachineService))
        container.register(PreparationService, instance=MagicMock(spec=PreparationService))
        fab = MagicMock(spec=["get_prep_info_for_product"])
        pc = MagicMock(spec=["fabricacion_service"])
        pc.fabricacion_service = fab
        controller.product_controller = pc

        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        assert dialog.presenter.model is None
        assert dialog.presenter.fabricacion_service is fab

    def test_init_with_existing_flow(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        task_dto = FlowTaskDataDTO(id="T1", name="Task", duration=1.0, duration_per_unit=1.0, department="General")
        config_dto = FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")
        existing = [ProductionFlowStepDTO(task=task_dto, config=config_dto)]
        
        dialog = DefineProductionFlowDialog(
            tasks, workers, units, controller, schedule_config, existing_flow=existing
        )
        qtbot.addWidget(dialog)
        
        flow = dialog.presenter.get_production_flow()
        assert len(flow) == 1
        assert flow[0].task.id == "T1"

    def test_add_step(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        # Simular selección en el árbol (ahora en control_panel)
        root = dialog.control_panel.task_tree.topLevelItem(0)
        assert root is not None
        task_item = root.child(0)
        assert task_item is not None
        
        dialog.control_panel.task_tree.setCurrentItem(task_item)
        
        # Configurar para fecha
        dialog.control_panel.start_date_radio.setChecked(True)
        # Hack para el menu de máquinas que borra señales
        dialog.control_panel.machine_menu.currentData = MagicMock(return_value=1)  # type: ignore[method-assign]
        
        # Añadir al flujo
        dialog._add_or_update_step()
        flow = dialog.presenter.get_production_flow()
        assert len(flow) == 1
        assert flow[0].task.id == 'P1_0_main_task'

    def test_group_steps(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_0 = FlowTaskDataDTO(id="T0", name="T0", duration=1.0, duration_per_unit=1.0, department="Gen")
        task_1 = FlowTaskDataDTO(id="T1", name="T1", duration=1.0, duration_per_unit=1.0, department="Gen")
        task_2 = FlowTaskDataDTO(id="T2", name="T2", duration=1.0, duration_per_unit=1.0, department="Gen")
        
        dialog.presenter.set_production_flow([
            ProductionFlowStepDTO(task=task_0, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")),
            ProductionFlowStepDTO(task=task_1, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")),
            ProductionFlowStepDTO(task=task_2, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
        ])
        dialog._update_flow_display()
        
        # Chequear los índices 1 y 2
        dialog.flow_item_widgets[1].checkbox.setChecked(True)
        dialog.flow_item_widgets[2].checkbox.setChecked(True)
        
        # Mocks
        mock_dependencies['multi'].return_value.exec.return_value = True
        mock_dependencies['multi'].return_value.get_selected_workers.return_value = ["W1"]
        mock_dependencies['input'].getInt.return_value = (5, True) # units_per_cycle 5, approved
        
        dialog._group_selected_steps()
        
        flow = dialog.presenter.get_production_flow()
        assert len(flow) == 2
        assert flow[1].config.is_group is True
        assert flow[1].config.units_per_cycle == 5

    def test_save_flow_only(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_dto = FlowTaskDataDTO(id="T1", name="T", duration=1.0, duration_per_unit=1.0, department="General")
        config_dto = FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")
        step = ProductionFlowStepDTO(task=task_dto, config=config_dto)
        dialog.presenter.set_production_flow([step])
        
        mock_dependencies['save'].return_value.exec.return_value = True
        mock_dependencies['save'].return_value.get_data.return_value = ("Test Flow", "Desc")
        
        dialog._on_save_flow()
        assert controller.handle_save_flow_only.call_count == 1
        controller.handle_save_flow_only.assert_called_once_with(
            "Test Flow",
            "Desc",
            [step],
        )

    def test_edit_and_update_step(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_dto = FlowTaskDataDTO(id="T0", name="T0", duration=1.0, duration_per_unit=1.0, department="General")
        config_dto = FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")
        step = ProductionFlowStepDTO(task=task_dto, config=config_dto)
        dialog.presenter.set_production_flow([step])
        dialog._update_flow_display()
        
        # Iniciar edición
        dialog._edit_step(0)
        assert dialog.editing_index == 0
        assert "Actualizar Paso" in dialog.control_panel.add_update_button.text()
        
        # Simular cambio en el form (por ejemplo, fecha)
        dialog.control_panel.start_date_radio.setChecked(True)
        
        # Cancelar edición (usando el botón real)
        dialog.control_panel.cancel_edit_button.click()
        assert dialog.editing_index is None
        
        # Volver a editar y Guardar
        dialog._edit_step(0)
        dialog._add_or_update_step()
        assert dialog.editing_index is None
        assert len(dialog.presenter.get_production_flow()) == 1

    def test_delete_step_confirmation(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_dto = FlowTaskDataDTO(id="T1", name="T", duration=1.0, duration_per_unit=1.0, department="General")
        config_dto = FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")
        step = ProductionFlowStepDTO(task=task_dto, config=config_dto)
        dialog.presenter.set_production_flow([step])
        dialog._update_flow_display()
        
        # Mocking QMessageBox: Necesitamos que StandardButton.Yes sea consistente
        mock_msg = mock_dependencies['msg']
        
        # No confirmar
        mock_msg.question.return_value = QMessageBox.StandardButton.No
        dialog._delete_step(0)
        assert len(dialog.presenter.get_production_flow()) == 1
        
        # Confirmar
        mock_msg.question.return_value = QMessageBox.StandardButton.Yes
        dialog._delete_step(0)
        assert len(dialog.presenter.get_production_flow()) == 0

    def test_machine_selection_and_prep_steps(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        # Mock de máquina y pasos de prep
        mock_machine = MagicMock(id=1, nombre="M1")
        mock_step = MagicMock(id=10, nombre="Prep 1", tiempo_fase=5)
        controller.model.get_machines_by_process_type.return_value = [mock_machine]
        dialog.presenter.get_prep_steps_for_machine = MagicMock(return_value=[mock_step])  # type: ignore[method-assign]
        dialog.presenter.get_default_step_ids = MagicMock(return_value=[10])  # type: ignore[method-assign]
        
        # Seleccionar tarea que requiere máquina
        task_info = FlowTaskDataDTO(
            id="T1", name="Main", duration=1.0, duration_per_unit=1.0, 
            department="General", requiere_maquina_tipo="Tipo A",
            original_product_code="P1"
        )
        dialog._on_task_selected(task_info)
        
        # Debería haber una máquina en el menú (índice 0 es el prompt)
        assert dialog.control_panel.machine_menu.count() > 1
        
        # Asegurar que el índice 1 tiene el ID 1
        dialog.control_panel.machine_menu.setItemData(1, 1, Qt.ItemDataRole.UserRole)
        dialog.control_panel.machine_menu.setCurrentIndex(1)
        dialog._on_machine_selected()
        
        # Verificar que se añadieron checkboxes de prep_steps
        assert len(dialog.control_panel.prep_steps_checkboxes) >= 1

    def test_assign_worker_to_group(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_dto = FlowTaskDataDTO(id="T", name="T", duration=1.0, duration_per_unit=1.0, department="General")
        config_dto = FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date", is_group=True)
        step = ProductionFlowStepDTO(task=task_dto, config=config_dto)
        dialog.presenter.set_production_flow([step])
        dialog._update_flow_display()
        
        mock_dependencies['multi'].return_value.exec.return_value = True
        mock_dependencies['multi'].return_value.get_selected_workers.return_value = ["W1", "W2"]
        
        dialog._assign_worker_to_group(0)
        assert step.config.workers == ["W1", "W2"]

    def test_group_steps_errors(self, qtbot, dialog_data, mock_dependencies):
        tasks, workers, units, controller, schedule_config = dialog_data
        dialog = DefineProductionFlowDialog(tasks, workers, units, controller, schedule_config)
        qtbot.addWidget(dialog)
        
        task_0 = FlowTaskDataDTO(id="T0", name="T0", duration=1.0, duration_per_unit=1.0, department="Gen")
        task_1 = FlowTaskDataDTO(id="T1", name="T1", duration=1.0, duration_per_unit=1.0, department="Gen")
        dialog.presenter.set_production_flow([
            ProductionFlowStepDTO(task=task_0, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")),
            ProductionFlowStepDTO(task=task_1, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
        ])
        dialog._update_flow_display()
        
        # No hay suficientes seleccionados
        dialog._group_selected_steps()
        mock_dependencies['msg'].warning.assert_called_with(dialog, "Selección Insuficiente", ANY)
        
        # Error en el presenter
        dialog.flow_item_widgets[0].checkbox.setChecked(True)
        dialog.flow_item_widgets[1].checkbox.setChecked(True)
        dialog.presenter.group_tasks = MagicMock(side_effect=ValueError("Error de agrupación"))  # type: ignore[method-assign]
        
        mock_dependencies['multi'].return_value.exec.return_value = True
        mock_dependencies['multi'].return_value.get_selected_workers.return_value = ["W1"]
        mock_dependencies['input'].getInt.return_value = (10, True)
        
        dialog._group_selected_steps()
        mock_dependencies['msg'].warning.assert_called_with(dialog, "Error al agrupar", "Error de agrupación")

    def test_on_save_flow_empty(self, qtbot, dialog, mock_dependencies):
        dialog.presenter.set_production_flow([])
        dialog._on_save_flow()
        mock_dependencies['msg'].warning.assert_called_with(dialog, "Flujo Vacío", ANY)

    def test_on_save_flow_no_name(self, qtbot, dialog, mock_dependencies):
        task_dto = FlowTaskDataDTO(id="T1", name="T1", duration=1.0, duration_per_unit=1.0, department="Gen")
        step = ProductionFlowStepDTO(task=task_dto, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
        dialog.presenter.add_step(step)
        mock_dependencies['save'].return_value.exec.return_value = QDialog.DialogCode.Accepted
        mock_dependencies['save'].return_value.get_data.return_value = ("", "Desc")
        
        dialog._on_save_flow()
        mock_dependencies['msg'].warning.assert_called_with(dialog, "Nombre Requerido", ANY)

    def test_add_step_no_selection_error(self, qtbot, dialog, mock_dependencies):
        dialog.control_panel.get_selected_task = MagicMock(return_value=None)
        dialog._add_or_update_step()
        mock_dependencies['msg'].warning.assert_called_with(dialog, "Selección Requerida", ANY)

    def test_add_step_no_machine_error(self, qtbot, dialog, mock_dependencies):
        task_info = FlowTaskDataDTO(
            id="T1", name='T1', requiere_maquina_tipo='Prensa', 
            duration=1.0, duration_per_unit=1.0, department="G", original_product_code="P"
        )
        dialog.editing_index = None
        dialog.control_panel.get_selected_task = MagicMock(return_value=task_info)
        dialog.control_panel.get_form_data = MagicMock(return_value={'machine_id': None, 'workers': []})
        
        dialog._add_or_update_step()
        mock_dependencies['msg'].warning.assert_called_once_with(dialog, "Error", ANY)
        args = mock_dependencies['msg'].warning.call_args[0]
        assert "Debe asignar una máquina" in args[2]

    def test_reset_form_clears_selection(self, qtbot, dialog):
        dialog.editing_index = 5
        dialog._reset_form()
        assert dialog.editing_index is None
        
    def test_machine_selection_with_default_prep(self, qtbot, dialog):
        mock_step = MagicMock(id=50, nombre="Prep 1", tiempo_fase=10)
        dialog.presenter.get_prep_steps_for_machine = MagicMock(return_value=[mock_step])
        dialog.presenter.get_default_step_ids = MagicMock(return_value=[50])
        
        # Inyectamos datos en el combo (index 0: Seleccione, index 1: M1)
        dialog.control_panel.machine_menu.addItem("--- Seleccione ---", userData=None)
        dialog.control_panel.machine_menu.addItem("M1", userData=1)
        dialog.control_panel.machine_menu.setCurrentIndex(1)
        dialog.control_panel.machine_menu.setProperty("default_group_id", 100)
        
        # Disparamos la lógica
        dialog._on_machine_selected()
        
        # Verificamos que se creó el checkbox
        assert len(dialog.control_panel.prep_steps_checkboxes) >= 1

    def test_on_task_selected_no_machines(self, qtbot, dialog):
        task_info = FlowTaskDataDTO(
            id="T1", name='T1', requiere_maquina_tipo='Tipo Raro',
            duration=1.0, duration_per_unit=1.0, department="G", original_product_code="P"
        )
        dialog.presenter.get_machines_for_task = MagicMock(return_value=[])
        
        dialog._on_task_selected(task_info)
        
        menu = dialog.control_panel.machine_menu
        assert "¡No hay máquinas" in menu.itemText(0)
        assert not menu.isEnabled()

    def test_on_task_selected_with_default_machine(self, qtbot, dialog):
        task_info = FlowTaskDataDTO(
            id="T1", name='T1', requiere_maquina_tipo='Prensa', original_product_code='P1',
            duration=1.0, duration_per_unit=1.0, department="G"
        )
        mock_machine = MagicMock(id=1, nombre="M1")
        dialog.presenter.get_machines_for_task = MagicMock(return_value=[mock_machine])
        dialog.presenter.get_prep_info = MagicMock(return_value=(10, 1)) # group_id=10, machine_id=1
        
        dialog._on_task_selected(task_info)
        
        menu = dialog.control_panel.machine_menu
        assert menu.currentData() == 1
        assert menu.property("default_group_id") == 10

    def test_toggle_start_condition_reset(self, qtbot, dialog):
        # Escenario: no hay flujo, pero marcamos dependencia
        dialog.presenter.set_production_flow([])
        dialog.control_panel.dependency_radio.setChecked(True)
        
        dialog._toggle_start_condition()
        
        # Debe haber vuelto a fecha si no hay flujo
        assert dialog.control_panel.start_date_radio.isChecked()

    def test_update_previous_task_menu_excludes_current(self, qtbot, dialog):
        task_1 = FlowTaskDataDTO(id="P1", name="Paso 1", duration=1.0, duration_per_unit=1.0, department="G")
        task_2 = FlowTaskDataDTO(id="P2", name="Paso 2", duration=1.0, duration_per_unit=1.0, department="G")
        dialog.presenter.set_production_flow([
            ProductionFlowStepDTO(task=task_1, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")),
            ProductionFlowStepDTO(task=task_2, config=FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date"))
        ])
        dialog.editing_index = 0 # Editando el primero
        
        dialog._update_previous_task_menu()
        
        menu = dialog.control_panel.previous_task_menu
        # Solo debe haber un item (Paso 2) o ninguno si solo se permiten previos? 
        # Actualmente el código itera todo el flujo y salta el editing_index.
        assert menu.count() == 1
        assert "Paso 2" in menu.itemText(0)

    def test_get_production_flow_delegation(self, qtbot, dialog):
        # Línea 353 coverage
        assert dialog.get_production_flow() == dialog.presenter.get_production_flow()

    def test_edit_step_with_machine(self, qtbot, dialog):
        # Setup: un flujo con una máquina
        task_dto = FlowTaskDataDTO(id="T1", name="T1", requiere_maquina_tipo="Prensa", duration=1.0, duration_per_unit=1.0, department="G", original_product_code="P")
        config_dto = FlowTaskConfigDTO(workers=[], machine_id=1, start_condition_type="date")
        step = ProductionFlowStepDTO(task=task_dto, config=config_dto)
        dialog.presenter.add_step(step)
        
        # Mock para que el resource manager encuentre la máquina al editar
        mock_machine = MagicMock(id=1, nombre="M1")
        dialog.presenter.get_machines_for_task = MagicMock(return_value=[mock_machine])
        
        # Editamos
        dialog._edit_step(0)
        
        assert dialog.editing_index == 0
        assert dialog.control_panel.machine_menu.currentData() == 1

    def test_edit_step_machine_not_found(self, qtbot, dialog):
        # Setup: flujo con máquina id 99 que NO está en el combo
        task_dto = FlowTaskDataDTO(id="T1", name="T1", duration=1.0, duration_per_unit=1.0, department="G")
        config_dto = FlowTaskConfigDTO(workers=[], machine_id=99, start_condition_type="date")
        step = ProductionFlowStepDTO(task=task_dto, config=config_dto)
        dialog.presenter.add_step(step)
        
        # Editamos (findData retornará -1)
        dialog._edit_step(0)
        
        assert dialog.editing_index == 0
        # No debe haber cambiado el index si no se encontró
        
    def test_add_step_with_none_task_info(self, qtbot, dialog):
        # Forzar que _add_or_update_step llegue a la línea 230
        # Simulamos que editing_index no es None pero get_step retorna None (raro pero cubre línea)
        dialog.editing_index = 0
        dialog.presenter.get_step = MagicMock(return_value=None)
        
        dialog._add_or_update_step()
        # Debe retornar temprano sin cambiar el index (si no fallara el test)
        assert dialog.editing_index == 0
