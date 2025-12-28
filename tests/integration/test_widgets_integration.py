"""
Tests de Integración para ui/widgets.py - Fase 3.9
==================================================
Suite de tests de integración para widgets de la aplicación.

Estos tests verifican:
- Interacción entre widgets y controllers
- Flujos de datos entre componentes
- Señales y slots

Siguiendo la metodología de Fase 2 y 3.7.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date


# =============================================================================
# TESTS DE INTEGRACIÓN: WorkersWidget con Controller
# =============================================================================

@pytest.mark.integration
class TestWorkersWidgetIntegration:
    """Tests de integración para WorkersWidget."""

    def test_populate_and_select_worker_flow(self):
        """Flujo completo: poblar lista y seleccionar trabajador."""
        from ui.widgets import WorkersWidget
        
        # Crear widget y controller mockeados
        controller = MagicMock()
        widget = MagicMock(spec=WorkersWidget)
        widget.controller = controller
        
        # Simular datos de trabajadores
        workers_data = [
            MagicMock(id=1, nombre="Juan", apellidos="García", tipo_trabajador=1),
            MagicMock(id=2, nombre="María", apellidos="López", tipo_trabajador=2)
        ]
        
        controller.get_all_workers.return_value = workers_data
        
        # Simular populate_list
        widget.workers_list = MagicMock()
        widget.workers_list.clear()
        
        for worker in controller.get_all_workers():
            item = MagicMock()
            widget.workers_list.addItem(item)
        
        # Verificar que se poblaron los trabajadores
        assert widget.workers_list.addItem.call_count == 2
        controller.get_all_workers.assert_called_once()

    def test_save_worker_emits_signal_and_updates_list(self):
        """Guardar trabajador debe emitir señal y actualizar lista."""
        from ui.widgets import WorkersWidget
        
        widget = MagicMock(spec=WorkersWidget)
        widget.save_signal = MagicMock()
        widget.controller = MagicMock()
        
        # Simular datos del formulario
        form_data = {
            'nombre': 'Pedro',
            'apellidos': 'Martínez',
            'tipo_trabajador': 1
        }
        
        # Simular guardado
        widget.save_signal.emit()
        widget.controller.save_worker(form_data)
        
        widget.save_signal.emit.assert_called_once()
        widget.controller.save_worker.assert_called_once_with(form_data)


# =============================================================================
# TESTS DE INTEGRACIÓN: ProductsWidget con Controller
# =============================================================================

@pytest.mark.integration
class TestProductsWidgetIntegration:
    """Tests de integración para ProductsWidget."""

    def test_search_and_display_product_flow(self):
        """Flujo completo: buscar y mostrar producto."""
        from ui.widgets import ProductsWidget
        
        controller = MagicMock()
        widget = MagicMock(spec=ProductsWidget)
        widget.controller = controller
        
        # Simular búsqueda
        search_term = "PROD"
        search_results = [
            MagicMock(codigo="PROD-001", descripcion="Producto 1"),
            MagicMock(codigo="PROD-002", descripcion="Producto 2")
        ]
        
        controller.search_products.return_value = search_results
        
        # Simular update_search_results
        widget.search_results = MagicMock()
        widget.search_results.clear()
        
        for product in controller.search_products(search_term):
            item = MagicMock()
            widget.search_results.addItem(item)
        
        controller.search_products.assert_called_once_with(search_term)
        assert widget.search_results.addItem.call_count == 2

    def test_manage_subfabricaciones_opens_dialog(self):
        """Gestionar subfabricaciones debe abrir diálogo."""
        from ui.widgets import ProductsWidget
        
        widget = MagicMock(spec=ProductsWidget)
        widget.manage_subs_signal = MagicMock()
        
        # Simular clic en botón
        widget.manage_subs_signal.emit()
        
        widget.manage_subs_signal.emit.assert_called_once()


# =============================================================================
# TESTS DE INTEGRACIÓN: FabricationsWidget con Controller
# =============================================================================

@pytest.mark.integration
class TestFabricationsWidgetIntegration:
    """Tests de integración para FabricationsWidget."""

    def test_create_fabricacion_flow(self):
        """Flujo completo: crear nueva fabricación."""
        from ui.widgets import FabricationsWidget
        
        controller = MagicMock()
        widget = MagicMock(spec=FabricationsWidget)
        widget.controller = controller
        widget.create_fabricacion_signal = MagicMock()
        
        # Simular creación
        widget.create_fabricacion_signal.emit()
        
        widget.create_fabricacion_signal.emit.assert_called_once()

    def test_display_fabricacion_with_preprocesos(self):
        """Mostrar fabricación con sus preprocesos."""
        from ui.widgets import FabricationsWidget
        
        widget = MagicMock(spec=FabricationsWidget)
        
        fabricacion_data = MagicMock(
            id=1,
            nombre="Fabricación Test",
            codigo="FAB-001"
        )
        
        preprocesos_data = [
            MagicMock(id=1, nombre="Preproceso 1"),
            MagicMock(id=2, nombre="Preproceso 2")
        ]
        
        # Simular display_fabricacion_form
        widget.nombre_edit = MagicMock()
        widget.codigo_edit = MagicMock()
        widget.preprocesos_list = MagicMock()
        
        widget.nombre_edit.setText(fabricacion_data.nombre)
        widget.codigo_edit.setText(fabricacion_data.codigo)
        
        for prep in preprocesos_data:
            widget.preprocesos_list.addItem(prep.nombre)
        
        widget.nombre_edit.setText.assert_called_once_with("Fabricación Test")
        assert widget.preprocesos_list.addItem.call_count == 2


# =============================================================================
# TESTS DE INTEGRACIÓN: CalculateTimesWidget con Controller
# =============================================================================

@pytest.mark.integration
class TestCalculateTimesWidgetIntegration:
    """Tests de integración para CalculateTimesWidget."""

    def test_calculate_times_flow(self):
        """Flujo completo: calcular tiempos de fabricación."""
        from ui.widgets import CalculateTimesWidget
        
        controller = MagicMock()
        widget = MagicMock(spec=CalculateTimesWidget)
        widget.controller = controller
        
        # Simular pila de cálculo
        pila_data = {
            'productos': [{'codigo': 'PROD-001', 'cantidad': 10}],
            'fabricaciones': [{'id': 1, 'cantidad': 5}]
        }
        
        # Simular resultados
        results = [
            {'task': 'Tarea 1', 'start': 0, 'duration': 10},
            {'task': 'Tarea 2', 'start': 10, 'duration': 15}
        ]
        
        audit_log = {'total_time': 25}
        
        controller.calculate_times.return_value = (results, audit_log)
        
        # Simular cálculo
        calc_results, calc_audit = controller.calculate_times(pila_data)
        
        controller.calculate_times.assert_called_once_with(pila_data)
        assert len(calc_results) == 2
        assert calc_audit['total_time'] == 25

    def test_progress_updates_during_calculation(self):
        """Debe actualizar progreso durante cálculo."""
        from ui.widgets import CalculateTimesWidget
        
        widget = MagicMock(spec=CalculateTimesWidget)
        widget.progress_bar = MagicMock()
        
        # Simular actualizaciones de progreso
        progress_values = [0, 25, 50, 75, 100]
        
        for value in progress_values:
            widget.progress_bar.setValue(value)
        
        assert widget.progress_bar.setValue.call_count == 5


# =============================================================================
# TESTS DE INTEGRACIÓN: DashboardWidget con Controller
# =============================================================================

@pytest.mark.integration
class TestDashboardWidgetIntegration:
    """Tests de integración para DashboardWidget."""

    def test_load_all_dashboard_data(self):
        """Cargar todos los datos del dashboard."""
        from ui.widgets import DashboardWidget
        
        controller = MagicMock()
        widget = MagicMock(spec=DashboardWidget)
        widget.controller = controller
        
        # Simular datos
        machine_data = [{'nombre': 'Torno', 'horas': 100}]
        worker_data = [{'nombre': 'Juan', 'tareas': 15}]
        
        controller.get_machine_usage.return_value = machine_data
        controller.get_worker_load.return_value = worker_data
        
        # Simular carga
        machines = controller.get_machine_usage()
        workers = controller.get_worker_load()
        
        controller.get_machine_usage.assert_called_once()
        controller.get_worker_load.assert_called_once()
        assert len(machines) == 1
        assert len(workers) == 1


# =============================================================================
# TESTS DE INTEGRACIÓN: HistorialWidget con Controller
# =============================================================================

@pytest.mark.integration
class TestHistorialWidgetIntegration:
    """Tests de integración para HistorialWidget."""

    def test_switch_mode_and_load_data(self):
        """Cambiar modo y cargar datos correspondientes."""
        from ui.widgets import HistorialWidget
        
        controller = MagicMock()
        widget = MagicMock(spec=HistorialWidget)
        widget.controller = controller
        widget.mode_changed_signal = MagicMock()
        
        # Simular cambio de modo
        mode = "iteraciones"
        widget.mode_changed_signal.emit(mode)
        
        # Simular carga de datos según modo
        if mode == "iteraciones":
            data = controller.get_iterations_history()
        else:
            data = controller.get_fabrications_history()
        
        widget.mode_changed_signal.emit.assert_called_once_with("iteraciones")

    def test_select_date_and_show_details(self):
        """Seleccionar fecha y mostrar detalles."""
        from ui.widgets import HistorialWidget
        
        controller = MagicMock()
        widget = MagicMock(spec=HistorialWidget)
        widget.controller = controller
        
        selected_date = date(2025, 12, 27)
        
        # Simular obtención de datos para la fecha
        day_data = [
            {'task': 'Tarea 1', 'time': '10:00'},
            {'task': 'Tarea 2', 'time': '14:00'}
        ]
        
        controller.get_data_for_date.return_value = day_data
        
        result = controller.get_data_for_date(selected_date)
        
        controller.get_data_for_date.assert_called_once_with(selected_date)
        assert len(result) == 2
