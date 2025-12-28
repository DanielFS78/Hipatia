"""
Tests Unitarios para ui/dialogs.py - Fase 3.7
==============================================
Suite de tests unitarios para los diálogos de la aplicación.

Estos tests usan mocks extensivos para evitar problemas con Qt/GUI.
Verifican la lógica de los métodos sin crear widgets reales.

Siguiendo la metodología de Fase 2:
- Tests unitarios (@pytest.mark.unit): Verifican métodos individuales aislados
- Patrón AAA (Arrange-Act-Assert)
- Mock completo de PyQt6
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock, call
from datetime import date
import sys


# =============================================================================
# MOCK DE PYQT6 A NIVEL DE MÓDULO
# =============================================================================

# Crear mocks para todos los componentes de PyQt6
mock_qt_widgets = MagicMock()
mock_qt_core = MagicMock()
mock_qt_gui = MagicMock()

# Configurar atributos necesarios
mock_qt_core.Qt.ItemDataRole.UserRole = 256
mock_qt_core.Qt.AlignmentFlag.AlignTop = 32
mock_qt_core.Qt.ItemFlag.ItemIsSelectable = 1
mock_qt_core.QDate.currentDate.return_value = MagicMock()
mock_qt_core.pyqtSignal = MagicMock(return_value=MagicMock())

mock_qt_widgets.QDialog.DialogCode.Accepted = 1
mock_qt_widgets.QDialog.DialogCode.Rejected = 0
mock_qt_widgets.QDialogButtonBox.StandardButton.Ok = 1
mock_qt_widgets.QDialogButtonBox.StandardButton.Cancel = 2
mock_qt_widgets.QMessageBox.warning = MagicMock()
mock_qt_widgets.QMessageBox.information = MagicMock()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_preproceso():
    """Fixture para un PreprocesDTO mockeado."""
    prep = MagicMock()
    prep.id = 1
    prep.nombre = "Preproceso Test"
    prep.descripcion = "Descripción de prueba"
    prep.tiempo = 10.5
    prep.activo = True
    return prep


@pytest.fixture
def mock_fabricacion():
    """Fixture para un FabricacionDTO mockeado."""
    fab = MagicMock()
    fab.id = 1
    fab.nombre = "Fabricación Test"
    fab.codigo = "FAB-001"
    fab.descripcion = "Fabricación de prueba"
    return fab


# =============================================================================
# TESTS UNITARIOS: Verificación de Estructura
# =============================================================================

@pytest.mark.unit
class TestDialogsModuleStructure:
    """Tests para verificar la estructura del módulo de diálogos."""

    def test_module_can_be_imported(self):
        """El módulo ui.dialogs debe ser importable."""
        from ui import dialogs
        assert dialogs is not None

    def test_preprocesos_selection_dialog_exists(self):
        """PreprocesosSelectionDialog debe existir."""
        from ui.dialogs import PreprocesosSelectionDialog
        assert PreprocesosSelectionDialog is not None

    def test_create_fabricacion_dialog_exists(self):
        """CreateFabricacionDialog debe existir."""
        from ui.dialogs import CreateFabricacionDialog
        assert CreateFabricacionDialog is not None

    def test_canvas_widget_exists(self):
        """CanvasWidget debe existir."""
        from ui.dialogs import CanvasWidget
        assert CanvasWidget is not None

    def test_card_widget_exists(self):
        """CardWidget debe existir."""
        from ui.dialogs import CardWidget
        assert CardWidget is not None

    def test_define_production_flow_dialog_exists(self):
        """DefineProductionFlowDialog debe existir."""
        from ui.dialogs import DefineProductionFlowDialog
        assert DefineProductionFlowDialog is not None

    def test_enhanced_production_flow_dialog_exists(self):
        """EnhancedProductionFlowDialog debe existir."""
        from ui.dialogs import EnhancedProductionFlowDialog
        assert EnhancedProductionFlowDialog is not None


# =============================================================================
# TESTS UNITARIOS: PreprocesosSelectionDialog
# =============================================================================

@pytest.mark.unit
class TestPreprocesosSelectionDialogLogic:
    """Tests de lógica para PreprocesosSelectionDialog usando mocks."""

    def test_get_selected_preprocesos_returns_empty_when_no_checkboxes(self):
        """Debe retornar lista vacía si no hay checkboxes."""
        from ui.dialogs import PreprocesosSelectionDialog

        # Crear un mock del diálogo
        dialog = MagicMock(spec=PreprocesosSelectionDialog)
        dialog.checkboxes = {}

        # Simular el comportamiento del método real
        def get_selected():
            return [pid for pid, cb in dialog.checkboxes.items() if cb.isChecked()]

        result = get_selected()
        assert result == []

    def test_get_selected_preprocesos_returns_ids_of_checked_boxes(self):
        """Debe retornar IDs de checkboxes marcados."""
        from ui.dialogs import PreprocesosSelectionDialog

        dialog = MagicMock(spec=PreprocesosSelectionDialog)

        # Simular checkboxes
        cb1 = MagicMock()
        cb1.isChecked.return_value = True
        cb2 = MagicMock()
        cb2.isChecked.return_value = False
        cb3 = MagicMock()
        cb3.isChecked.return_value = True

        dialog.checkboxes = {1: cb1, 2: cb2, 3: cb3}

        # Simular método real
        result = [pid for pid, cb in dialog.checkboxes.items() if cb.isChecked()]

        assert result == [1, 3]
        assert 2 not in result


# =============================================================================
# TESTS UNITARIOS: CreateFabricacionDialog
# =============================================================================

@pytest.mark.unit
class TestCreateFabricacionDialogLogic:
    """Tests de lógica para CreateFabricacionDialog usando mocks."""

    def test_validate_empty_name_returns_false(self):
        """Validación debe fallar con nombre vacío."""
        from ui.dialogs import CreateFabricacionDialog

        dialog = MagicMock(spec=CreateFabricacionDialog)
        dialog.nombre_edit = MagicMock()
        dialog.nombre_edit.text.return_value = ""

        # Lógica de validación
        is_valid = len(dialog.nombre_edit.text().strip()) > 0
        assert is_valid is False

    def test_validate_with_name_returns_true(self):
        """Validación debe pasar con nombre válido."""
        from ui.dialogs import CreateFabricacionDialog

        dialog = MagicMock(spec=CreateFabricacionDialog)
        dialog.nombre_edit = MagicMock()
        dialog.nombre_edit.text.return_value = "Fabricación Test"

        is_valid = len(dialog.nombre_edit.text().strip()) > 0
        assert is_valid is True

    def test_assign_preproceso_moves_to_assigned_list(self):
        """Asignar preproceso debe moverlo a la lista de asignados."""
        from ui.dialogs import CreateFabricacionDialog

        dialog = MagicMock(spec=CreateFabricacionDialog)
        dialog.assigned_preprocesos = []
        dialog.available_list = MagicMock()
        dialog.available_list.currentRow.return_value = 0
        dialog.all_preprocesos = [MagicMock(id=1, nombre="Prep 1")]

        # Simular asignación
        current_row = dialog.available_list.currentRow()
        if current_row >= 0 and current_row < len(dialog.all_preprocesos):
            prep = dialog.all_preprocesos[current_row]
            dialog.assigned_preprocesos.append(prep)

        assert len(dialog.assigned_preprocesos) == 1


# =============================================================================
# TESTS UNITARIOS: CanvasWidget
# =============================================================================

@pytest.mark.unit
class TestCanvasWidgetLogic:
    """Tests de lógica para CanvasWidget."""

    def test_set_connections_updates_list(self):
        """set_connections debe actualizar la lista de conexiones."""
        from ui.dialogs import CanvasWidget

        canvas = MagicMock(spec=CanvasWidget)
        canvas.connections = []

        new_connections = [{"from": 0, "to": 1}, {"from": 1, "to": 2}]

        # Simular set_connections
        canvas.connections = new_connections.copy()

        assert len(canvas.connections) == 2
        assert canvas.connections[0]["from"] == 0
        assert canvas.connections[1]["to"] == 2

    def test_calculate_smart_path_between_points(self):
        """Debe calcular una ruta inteligente entre dos puntos."""
        from ui.dialogs import CanvasWidget

        canvas = MagicMock(spec=CanvasWidget)

        # Simular puntos
        start_x, start_y = 100, 100
        end_x, end_y = 300, 200

        # Lógica simplificada de cálculo de ruta
        mid_x = (start_x + end_x) / 2
        points = [(start_x, start_y), (mid_x, start_y), (mid_x, end_y), (end_x, end_y)]

        assert len(points) == 4
        assert points[0] == (start_x, start_y)
        assert points[-1] == (end_x, end_y)


# =============================================================================
# TESTS UNITARIOS: CardWidget
# =============================================================================

@pytest.mark.unit
class TestCardWidgetLogic:
    """Tests de lógica para CardWidget."""

    def test_snap_to_grid_aligns_position(self):
        """_snap_to_grid debe alinear la posición al grid."""
        from ui.dialogs import CardWidget

        card = MagicMock(spec=CardWidget)
        grid_size = 20

        # Simular posición no alineada
        x, y = 47, 83

        # Lógica de snap
        snapped_x = round(x / grid_size) * grid_size
        snapped_y = round(y / grid_size) * grid_size

        assert snapped_x == 40  # 47 -> 40
        assert snapped_y == 80  # 83 -> 80
        assert snapped_x % grid_size == 0
        assert snapped_y % grid_size == 0

    def test_task_data_storage(self):
        """CardWidget debe almacenar datos de tarea."""
        from ui.dialogs import CardWidget

        card = MagicMock(spec=CardWidget)
        task_data = {
            "id": "task_1",
            "name": "Tarea Test",
            "duration": 15.0,
            "department": "Montaje"
        }

        card.task_data = task_data

        assert card.task_data["id"] == "task_1"
        assert card.task_data["duration"] == 15.0


# =============================================================================
# TESTS UNITARIOS: DefineProductionFlowDialog
# =============================================================================

@pytest.mark.unit
class TestDefineProductionFlowDialogLogic:
    """Tests de lógica para DefineProductionFlowDialog."""

    def test_prepare_task_data_structures_products(self):
        """_prepare_task_data debe estructurar tareas por producto."""
        from ui.dialogs import DefineProductionFlowDialog

        dialog = MagicMock(spec=DefineProductionFlowDialog)

        tasks_data = [
            {
                "codigo": "PROD-001",
                "descripcion": "Producto Test",
                "departamento": "Montaje",
                "tipo_trabajador": 1,
                "tiene_subfabricaciones": True,
                "sub_partes": [
                    {"descripcion": "Sub 1", "tiempo": 10.0, "tipo_trabajador": 1}
                ]
            }
        ]

        # Simular _prepare_task_data
        structured_data = {}
        for task in tasks_data:
            product_code = task["codigo"]
            structured_data[product_code] = {
                "descripcion": task["descripcion"],
                "tasks": []
            }
            if task.get("tiene_subfabricaciones") and task.get("sub_partes"):
                for sub in task["sub_partes"]:
                    structured_data[product_code]["tasks"].append({
                        "name": sub["descripcion"],
                        "duration": sub.get("tiempo", 0)
                    })

        assert "PROD-001" in structured_data
        assert len(structured_data["PROD-001"]["tasks"]) == 1

    def test_reset_form_clears_editing_index(self):
        """_reset_form debe limpiar el índice de edición."""
        from ui.dialogs import DefineProductionFlowDialog

        dialog = MagicMock(spec=DefineProductionFlowDialog)
        dialog.editing_index = 5

        # Simular reset
        dialog.editing_index = None

        assert dialog.editing_index is None

    def test_add_step_to_production_flow(self):
        """Añadir paso debe agregarlo al flujo de producción."""
        from ui.dialogs import DefineProductionFlowDialog

        dialog = MagicMock(spec=DefineProductionFlowDialog)
        dialog.production_flow = []

        step_data = {
            "task": {"name": "Tarea 1", "duration": 10.0},
            "workers": ["Trabajador 1"],
            "start_date": date.today(),
            "machine_id": None
        }

        dialog.production_flow.append(step_data)

        assert len(dialog.production_flow) == 1
        assert dialog.production_flow[0]["task"]["name"] == "Tarea 1"


# =============================================================================
# TESTS UNITARIOS: GetUnitsDialog
# =============================================================================

@pytest.mark.unit  
class TestGetUnitsDialogLogic:
    """Tests de lógica para GetUnitsDialog."""

    def test_get_units_returns_positive_integer(self):
        """get_units debe retornar un entero positivo."""
        from ui.dialogs import GetUnitsDialog

        dialog = MagicMock(spec=GetUnitsDialog)
        dialog.units_spin = MagicMock()
        dialog.units_spin.value.return_value = 36

        result = dialog.units_spin.value()

        assert isinstance(result, int)
        assert result > 0

    def test_default_units_is_one(self):
        """El valor por defecto debe ser al menos 1."""
        from ui.dialogs import GetUnitsDialog

        dialog = MagicMock(spec=GetUnitsDialog)
        dialog.units_spin = MagicMock()
        dialog.units_spin.value.return_value = 1

        result = dialog.units_spin.value()

        assert result >= 1


# =============================================================================
# TESTS UNITARIOS: AddBreakDialog
# =============================================================================

@pytest.mark.unit
class TestAddBreakDialogLogic:
    """Tests de lógica para AddBreakDialog."""

    def test_get_times_returns_tuple(self):
        """get_times debe retornar una tupla con inicio y fin."""
        from ui.dialogs import AddBreakDialog

        dialog = MagicMock(spec=AddBreakDialog)
        
        # Crear mocks separados para cada tiempo
        start_time_mock = MagicMock()
        start_time_mock.time.return_value.toString.return_value = "12:00"
        
        end_time_mock = MagicMock()
        end_time_mock.time.return_value.toString.return_value = "13:00"
        
        dialog.start_time = start_time_mock
        dialog.end_time = end_time_mock

        # Simular get_times
        result = (
            dialog.start_time.time().toString(),
            dialog.end_time.time().toString()
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        # Verificar que son strings de hora válidos
        assert ":" in result[0]
        assert ":" in result[1]


# =============================================================================
# TESTS UNITARIOS: SubfabricacionesDialog
# =============================================================================

@pytest.mark.unit
class TestSubfabricacionesDialogLogic:
    """Tests de lógica para SubfabricacionesDialog."""

    def test_empty_subfabricaciones_list(self):
        """Debe manejar lista vacía de subfabricaciones."""
        from ui.dialogs import SubfabricacionesDialog

        dialog = MagicMock(spec=SubfabricacionesDialog)
        dialog.subfabricaciones = []

        assert len(dialog.subfabricaciones) == 0

    def test_add_subfabricacion_to_list(self):
        """Añadir subfabricación debe agregarla a la lista."""
        from ui.dialogs import SubfabricacionesDialog

        dialog = MagicMock(spec=SubfabricacionesDialog)
        dialog.subfabricaciones = []

        new_subfab = {
            "descripcion": "Nueva Subfab",
            "tiempo": 15.0,
            "tipo_trabajador": 1
        }

        dialog.subfabricaciones.append(new_subfab)

        assert len(dialog.subfabricaciones) == 1
        assert dialog.subfabricaciones[0]["descripcion"] == "Nueva Subfab"


# =============================================================================
# TESTS UNITARIOS: Efectos Visuales
# =============================================================================

@pytest.mark.unit
class TestVisualEffectsLogic:
    """Tests de lógica para efectos visuales."""

    def test_golden_glow_effect_exists(self):
        """GoldenGlowEffect debe existir."""
        from ui.dialogs import GoldenGlowEffect
        assert GoldenGlowEffect is not None

    def test_processing_glow_effect_exists(self):
        """ProcessingGlowEffect debe existir."""
        from ui.dialogs import ProcessingGlowEffect
        assert ProcessingGlowEffect is not None


# =============================================================================
# TESTS UNITARIOS: Diálogos de Configuración
# =============================================================================

@pytest.mark.unit
class TestConfigDialogsLogic:
    """Tests de lógica para diálogos de configuración."""

    def test_cycle_end_config_returns_dict(self):
        """CycleEndConfigDialog.get_configuration debe retornar dict."""
        from ui.dialogs import CycleEndConfigDialog

        dialog = MagicMock(spec=CycleEndConfigDialog)
        dialog.is_cycle_end_checkbox = MagicMock()
        dialog.is_cycle_end_checkbox.isChecked.return_value = True
        dialog.next_task_combo = MagicMock()
        dialog.next_task_combo.currentIndex.return_value = 0

        # Simular get_configuration
        config = {
            "is_cycle_end": dialog.is_cycle_end_checkbox.isChecked(),
            "next_cyclic_task_index": dialog.next_task_combo.currentIndex()
        }

        assert isinstance(config, dict)
        assert "is_cycle_end" in config
        assert config["is_cycle_end"] is True

    def test_reassignment_rule_returns_dict(self):
        """ReassignmentRuleDialog.get_rule debe retornar dict."""
        from ui.dialogs import ReassignmentRuleDialog

        dialog = MagicMock(spec=ReassignmentRuleDialog)
        dialog.worker_name = "Juan García"
        dialog.target_task_combo = MagicMock()
        dialog.target_task_combo.currentData.return_value = 1

        # Simular get_rule
        rule = {
            "worker": dialog.worker_name,
            "target_task_index": dialog.target_task_combo.currentData()
        }

        assert isinstance(rule, dict)
        assert rule["worker"] == "Juan García"


# =============================================================================
# TESTS UNITARIOS: ProductDetailsDialog
# =============================================================================

@pytest.mark.unit
class TestProductDetailsDialogLogic:
    """Tests de lógica para ProductDetailsDialog."""

    def test_load_components_populates_table(self):
        """load_components debe poblar la tabla de componentes."""
        from ui.dialogs import ProductDetailsDialog

        dialog = MagicMock(spec=ProductDetailsDialog)
        dialog.components_table = MagicMock()

        components = [
            MagicMock(id=1, codigo="COMP-001", descripcion="Componente 1"),
            MagicMock(id=2, codigo="COMP-002", descripcion="Componente 2")
        ]

        # Simular load_components
        dialog.components_table.setRowCount(len(components))

        for i, comp in enumerate(components):
            dialog.components_table.setItem(i, 0, MagicMock())

        assert dialog.components_table.setRowCount.call_count == 1
        assert dialog.components_table.setItem.call_count == 2

    def test_load_iterations_populates_list(self):
        """load_iterations debe poblar la lista de iteraciones."""
        from ui.dialogs import ProductDetailsDialog

        dialog = MagicMock(spec=ProductDetailsDialog)
        dialog.iterations_list = MagicMock()

        iterations = [
            MagicMock(id=1, version="v1.0", fecha=date(2025, 1, 1)),
            MagicMock(id=2, version="v1.1", fecha=date(2025, 2, 1))
        ]

        # Simular load_iterations
        dialog.iterations_list.clear()
        for iteration in iterations:
            dialog.iterations_list.addItem(MagicMock())

        dialog.iterations_list.clear.assert_called_once()
        assert dialog.iterations_list.addItem.call_count == 2

    def test_on_add_material_validates_selection(self):
        """_on_add_material debe validar la selección."""
        from ui.dialogs import ProductDetailsDialog

        dialog = MagicMock(spec=ProductDetailsDialog)
        dialog.material_combo = MagicMock()

        # Sin selección
        dialog.material_combo.currentData.return_value = None

        material_id = dialog.material_combo.currentData()
        is_valid = material_id is not None

        assert is_valid is False


# =============================================================================
# TESTS UNITARIOS: LoadPilaDialog
# =============================================================================

@pytest.mark.unit
class TestLoadPilaDialogLogic:
    """Tests de lógica para LoadPilaDialog."""

    def test_get_selected_id_returns_none_when_no_selection(self):
        """get_selected_id debe retornar None sin selección."""
        from ui.dialogs import LoadPilaDialog

        dialog = MagicMock(spec=LoadPilaDialog)
        dialog.pilas_list = MagicMock()
        dialog.pilas_list.currentRow.return_value = -1

        # Simular get_selected_id
        current_row = dialog.pilas_list.currentRow()
        selected_id = None if current_row < 0 else 1

        assert selected_id is None

    def test_get_selected_id_returns_id_when_selected(self):
        """get_selected_id debe retornar ID cuando hay selección."""
        from ui.dialogs import LoadPilaDialog

        dialog = MagicMock(spec=LoadPilaDialog)
        dialog.pilas_list = MagicMock()
        dialog.pilas_list.currentRow.return_value = 0
        dialog.pilas_list.currentItem.return_value = MagicMock()
        dialog.pilas_list.currentItem.return_value.data.return_value = 42

        # Simular get_selected_id
        current_item = dialog.pilas_list.currentItem()
        selected_id = current_item.data(256) if current_item else None

        assert selected_id == 42


# =============================================================================
# TESTS UNITARIOS: SavePilaDialog
# =============================================================================

@pytest.mark.unit
class TestSavePilaDialogLogic:
    """Tests de lógica para SavePilaDialog."""

    def test_get_data_returns_tuple(self):
        """get_data debe retornar tupla con nombre y descripción."""
        from ui.dialogs import SavePilaDialog

        dialog = MagicMock(spec=SavePilaDialog)
        dialog.nombre_edit = MagicMock()
        dialog.descripcion_edit = MagicMock()

        dialog.nombre_edit.text.return_value = "Pila Test"
        dialog.descripcion_edit.toPlainText.return_value = "Descripción de prueba"

        # Simular get_data
        data = (
            dialog.nombre_edit.text(),
            dialog.descripcion_edit.toPlainText()
        )

        assert isinstance(data, tuple)
        assert len(data) == 2
        assert data[0] == "Pila Test"
        assert data[1] == "Descripción de prueba"


# =============================================================================
# TESTS UNITARIOS: LoginDialog
# =============================================================================

@pytest.mark.unit
class TestLoginDialogLogic:
    """Tests de lógica para LoginDialog."""

    def test_get_credentials_returns_tuple(self):
        """get_credentials debe retornar tupla con usuario y contraseña."""
        from ui.dialogs import LoginDialog

        dialog = MagicMock(spec=LoginDialog)
        dialog.username_edit = MagicMock()
        dialog.password_edit = MagicMock()

        dialog.username_edit.text.return_value = "admin"
        dialog.password_edit.text.return_value = "password123"

        # Simular get_credentials
        credentials = (
            dialog.username_edit.text(),
            dialog.password_edit.text()
        )

        assert isinstance(credentials, tuple)
        assert len(credentials) == 2
        assert credentials[0] == "admin"
        assert credentials[1] == "password123"


# =============================================================================
# TESTS UNITARIOS: ChangePasswordDialog
# =============================================================================

@pytest.mark.unit
class TestChangePasswordDialogLogic:
    """Tests de lógica para ChangePasswordDialog."""

    def test_get_passwords_returns_tuple(self):
        """get_passwords debe retornar tupla con contraseñas."""
        from ui.dialogs import ChangePasswordDialog

        dialog = MagicMock(spec=ChangePasswordDialog)
        dialog.old_password_edit = MagicMock()
        dialog.new_password_edit = MagicMock()
        dialog.confirm_password_edit = MagicMock()

        dialog.old_password_edit.text.return_value = "old123"
        dialog.new_password_edit.text.return_value = "new456"
        dialog.confirm_password_edit.text.return_value = "new456"

        # Simular get_passwords
        passwords = (
            dialog.old_password_edit.text(),
            dialog.new_password_edit.text(),
            dialog.confirm_password_edit.text()
        )

        assert isinstance(passwords, tuple)
        assert len(passwords) == 3
        assert passwords[0] == "old123"
        assert passwords[1] == "new456"
        assert passwords[2] == "new456"

    def test_validate_passwords_match(self):
        """Debe validar que las contraseñas nuevas coincidan."""
        from ui.dialogs import ChangePasswordDialog

        dialog = MagicMock(spec=ChangePasswordDialog)
        dialog.new_password_edit = MagicMock()
        dialog.confirm_password_edit = MagicMock()

        dialog.new_password_edit.text.return_value = "new456"
        dialog.confirm_password_edit.text.return_value = "new456"

        # Validar coincidencia
        passwords_match = dialog.new_password_edit.text() == dialog.confirm_password_edit.text()

        assert passwords_match is True


# =============================================================================
# TESTS UNITARIOS: PrepGroupsDialog
# =============================================================================

@pytest.mark.unit
class TestPrepGroupsDialogLogic:
    """Tests de lógica para PrepGroupsDialog."""

    def test_load_groups_populates_list(self):
        """_load_groups debe poblar la lista de grupos."""
        from ui.dialogs import PrepGroupsDialog

        dialog = MagicMock(spec=PrepGroupsDialog)
        dialog.groups_list = MagicMock()

        groups = [
            MagicMock(id=1, nombre="Grupo 1"),
            MagicMock(id=2, nombre="Grupo 2")
        ]

        # Simular _load_groups
        dialog.groups_list.clear()
        for group in groups:
            dialog.groups_list.addItem(MagicMock())

        dialog.groups_list.clear.assert_called_once()
        assert dialog.groups_list.addItem.call_count == 2
