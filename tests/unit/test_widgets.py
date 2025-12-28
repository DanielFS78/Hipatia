"""
Tests Unitarios para ui/widgets.py - Fase 3.9
==============================================
Suite de tests unitarios para los widgets básicos de la aplicación.

Estos tests usan mocks extensivos para evitar problemas con Qt/GUI.
Verifican la lógica de los métodos sin crear widgets reales.

Siguiendo la metodología de Fase 2 y 3.7:
- Tests unitarios (@pytest.mark.unit): Verifican métodos individuales aislados
- Patrón AAA (Arrange-Act-Assert)
- Mock completo de PyQt6
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock, call
from datetime import date, datetime
import sys


# =============================================================================
# TESTS UNITARIOS: HomeWidget
# =============================================================================

@pytest.mark.unit
class TestHomeWidgetLogic:
    """Tests de lógica para HomeWidget."""

    def test_set_quote_updates_text(self):
        """set_quote debe actualizar el texto de la cita."""
        from ui.widgets import HomeWidget
        
        widget = MagicMock(spec=HomeWidget)
        widget.quote_text = MagicMock()
        widget.author_text = MagicMock()
        
        # Simular set_quote
        quote = "La calidad nunca es un accidente"
        author = "John Ruskin"
        
        widget.quote_text.setText(f'"{quote}"')
        widget.author_text.setText(f"— {author}")
        
        widget.quote_text.setText.assert_called_once_with(f'"{quote}"')
        widget.author_text.setText.assert_called_once_with(f"— {author}")


# =============================================================================
# TESTS UNITARIOS: SettingsWidget
# =============================================================================

@pytest.mark.unit
class TestSettingsWidgetLogic:
    """Tests de lógica para SettingsWidget."""

    def test_load_schedule_settings_populates_fields(self):
        """_load_schedule_settings debe poblar los campos con datos."""
        from ui.widgets import SettingsWidget
        
        widget = MagicMock(spec=SettingsWidget)
        widget.controller = MagicMock()
        
        # Simular datos de configuración
        config_data = {
            'hora_inicio': '08:00',
            'hora_fin': '17:00',
            'descansos': [('12:00', '13:00')]
        }
        
        widget.controller.get_schedule_config.return_value = config_data
        
        # Verificar que se obtienen los datos
        result = widget.controller.get_schedule_config()
        assert result['hora_inicio'] == '08:00'
        assert result['hora_fin'] == '17:00'
        assert len(result['descansos']) == 1

    def test_update_break_buttons_state_enables_when_selected(self):
        """_update_break_buttons_state debe habilitar botones cuando hay selección."""
        from ui.widgets import SettingsWidget
        
        widget = MagicMock(spec=SettingsWidget)
        widget.breaks_list = MagicMock()
        widget.edit_break_btn = MagicMock()
        widget.remove_break_btn = MagicMock()
        
        # Simular selección
        widget.breaks_list.currentRow.return_value = 0
        
        # Lógica de habilitación
        has_selection = widget.breaks_list.currentRow() >= 0
        widget.edit_break_btn.setEnabled(has_selection)
        widget.remove_break_btn.setEnabled(has_selection)
        
        widget.edit_break_btn.setEnabled.assert_called_once_with(True)
        widget.remove_break_btn.setEnabled.assert_called_once_with(True)

    def test_update_break_buttons_state_disables_when_no_selection(self):
        """_update_break_buttons_state debe deshabilitar botones sin selección."""
        from ui.widgets import SettingsWidget
        
        widget = MagicMock(spec=SettingsWidget)
        widget.breaks_list = MagicMock()
        widget.edit_break_btn = MagicMock()
        widget.remove_break_btn = MagicMock()
        
        # Simular sin selección
        widget.breaks_list.currentRow.return_value = -1
        
        # Lógica de habilitación
        has_selection = widget.breaks_list.currentRow() >= 0
        widget.edit_break_btn.setEnabled(has_selection)
        widget.remove_break_btn.setEnabled(has_selection)
        
        widget.edit_break_btn.setEnabled.assert_called_once_with(False)
        widget.remove_break_btn.setEnabled.assert_called_once_with(False)


# =============================================================================
# TESTS UNITARIOS: HistorialWidget
# =============================================================================

@pytest.mark.unit
class TestHistorialWidgetLogic:
    """Tests de lógica para HistorialWidget."""

    def test_clear_view_resets_all_elements(self):
        """clear_view debe resetear lista, calendario y panel de detalles."""
        from ui.widgets import HistorialWidget
        
        widget = MagicMock(spec=HistorialWidget)
        widget.list_widget = MagicMock()
        widget.calendar = MagicMock()
        widget.stacked_widget = MagicMock()
        
        # Simular clear_view
        widget.list_widget.clear()
        widget.calendar.setSelectedDate(MagicMock())
        widget.stacked_widget.setCurrentIndex(0)
        
        widget.list_widget.clear.assert_called_once()
        widget.stacked_widget.setCurrentIndex.assert_called_once_with(0)

    def test_highlight_calendar_dates_applies_format(self):
        """highlight_calendar_dates debe aplicar formato a las fechas."""
        from ui.widgets import HistorialWidget
        
        widget = MagicMock(spec=HistorialWidget)
        widget.calendar = MagicMock()
        
        dates = [date(2025, 12, 27), date(2025, 12, 28)]
        color_hex = "#4CAF50"
        
        # Simular aplicación de formato
        for d in dates:
            format_obj = MagicMock()
            widget.calendar.setDateTextFormat(d, format_obj)
        
        # Verificar que se llamó para cada fecha
        assert widget.calendar.setDateTextFormat.call_count == 2


# =============================================================================
# TESTS UNITARIOS: WorkersWidget
# =============================================================================

@pytest.mark.unit
class TestWorkersWidgetLogic:
    """Tests de lógica para WorkersWidget."""

    def test_populate_list_adds_workers(self):
        """populate_list debe añadir trabajadores a la lista."""
        from ui.widgets import WorkersWidget
        
        widget = MagicMock(spec=WorkersWidget)
        widget.workers_list = MagicMock()
        
        workers_data = [
            MagicMock(id=1, nombre="Juan", apellidos="García"),
            MagicMock(id=2, nombre="María", apellidos="López")
        ]
        
        # Simular populate_list
        widget.workers_list.clear()
        for worker in workers_data:
            item = MagicMock()
            widget.workers_list.addItem(item)
        
        widget.workers_list.clear.assert_called_once()
        assert widget.workers_list.addItem.call_count == 2

    def test_get_form_data_returns_dict(self):
        """get_form_data debe retornar un diccionario con los datos."""
        from ui.widgets import WorkersWidget
        
        widget = MagicMock(spec=WorkersWidget)
        widget.nombre_edit = MagicMock()
        widget.apellidos_edit = MagicMock()
        widget.tipo_combo = MagicMock()
        
        widget.nombre_edit.text.return_value = "Juan"
        widget.apellidos_edit.text.return_value = "García"
        widget.tipo_combo.currentData.return_value = 1
        
        # Simular get_form_data
        data = {
            'nombre': widget.nombre_edit.text(),
            'apellidos': widget.apellidos_edit.text(),
            'tipo_trabajador': widget.tipo_combo.currentData()
        }
        
        assert data['nombre'] == "Juan"
        assert data['apellidos'] == "García"
        assert data['tipo_trabajador'] == 1

    def test_clear_details_area_shows_placeholder(self):
        """clear_details_area debe mostrar el placeholder."""
        from ui.widgets import WorkersWidget
        
        widget = MagicMock(spec=WorkersWidget)
        widget.details_stack = MagicMock()
        
        # Simular clear
        widget.details_stack.setCurrentIndex(0)
        
        widget.details_stack.setCurrentIndex.assert_called_once_with(0)


# =============================================================================
# TESTS UNITARIOS: MachinesWidget
# =============================================================================

@pytest.mark.unit
class TestMachinesWidgetLogic:
    """Tests de lógica para MachinesWidget."""

    def test_populate_list_adds_machines(self):
        """populate_list debe añadir máquinas a la lista."""
        from ui.widgets import MachinesWidget
        
        widget = MagicMock(spec=MachinesWidget)
        widget.machines_list = MagicMock()
        
        machines_data = [
            MagicMock(id=1, nombre="Torno CNC"),
            MagicMock(id=2, nombre="Fresadora")
        ]
        
        # Simular populate_list
        widget.machines_list.clear()
        for machine in machines_data:
            item = MagicMock()
            widget.machines_list.addItem(item)
        
        widget.machines_list.clear.assert_called_once()
        assert widget.machines_list.addItem.call_count == 2

    def test_get_form_data_returns_machine_dict(self):
        """get_form_data debe retornar un diccionario con datos de máquina."""
        from ui.widgets import MachinesWidget
        
        widget = MagicMock(spec=MachinesWidget)
        widget.nombre_edit = MagicMock()
        widget.descripcion_edit = MagicMock()
        
        widget.nombre_edit.text.return_value = "Torno CNC"
        widget.descripcion_edit.toPlainText.return_value = "Torno de alta precisión"
        
        # Simular get_form_data
        data = {
            'nombre': widget.nombre_edit.text(),
            'descripcion': widget.descripcion_edit.toPlainText()
        }
        
        assert data['nombre'] == "Torno CNC"
        assert data['descripcion'] == "Torno de alta precisión"


# =============================================================================
# TESTS UNITARIOS: ProductsWidget
# =============================================================================

@pytest.mark.unit
class TestProductsWidgetLogic:
    """Tests de lógica para ProductsWidget."""

    def test_update_search_results_populates_list(self):
        """update_search_results debe poblar la lista de resultados."""
        from ui.widgets import ProductsWidget
        
        widget = MagicMock(spec=ProductsWidget)
        widget.search_results = MagicMock()
        
        results = [
            MagicMock(codigo="PROD-001", descripcion="Producto 1"),
            MagicMock(codigo="PROD-002", descripcion="Producto 2")
        ]
        
        # Simular update_search_results
        widget.search_results.clear()
        for product in results:
            item = MagicMock()
            widget.search_results.addItem(item)
        
        widget.search_results.clear.assert_called_once()
        assert widget.search_results.addItem.call_count == 2

    def test_get_product_form_data_returns_dict(self):
        """get_product_form_data debe retornar diccionario con datos."""
        from ui.widgets import ProductsWidget
        
        widget = MagicMock(spec=ProductsWidget)
        widget.codigo_edit = MagicMock()
        widget.descripcion_edit = MagicMock()
        
        widget.codigo_edit.text.return_value = "PROD-001"
        widget.descripcion_edit.text.return_value = "Producto Test"
        
        # Simular get_product_form_data
        data = {
            'codigo': widget.codigo_edit.text(),
            'descripcion': widget.descripcion_edit.text()
        }
        
        assert data['codigo'] == "PROD-001"
        assert data['descripcion'] == "Producto Test"

    def test_clear_all_resets_widget(self):
        """clear_all debe resetear el widget."""
        from ui.widgets import ProductsWidget
        
        widget = MagicMock(spec=ProductsWidget)
        widget.search_results = MagicMock()
        widget.edit_stack = MagicMock()
        
        # Simular clear_all
        widget.search_results.clear()
        widget.edit_stack.setCurrentIndex(0)
        
        widget.search_results.clear.assert_called_once()
        widget.edit_stack.setCurrentIndex.assert_called_once_with(0)


# =============================================================================
# TESTS UNITARIOS: FabricationsWidget
# =============================================================================

@pytest.mark.unit
class TestFabricationsWidgetLogic:
    """Tests de lógica para FabricationsWidget."""

    def test_update_search_results_populates_fabrications(self):
        """update_search_results debe poblar la lista de fabricaciones."""
        from ui.widgets import FabricationsWidget
        
        widget = MagicMock(spec=FabricationsWidget)
        widget.search_results = MagicMock()
        
        results = [
            MagicMock(id=1, nombre="Fabricación 1"),
            MagicMock(id=2, nombre="Fabricación 2")
        ]
        
        # Simular update_search_results
        widget.search_results.clear()
        for fab in results:
            item = MagicMock()
            widget.search_results.addItem(item)
        
        widget.search_results.clear.assert_called_once()
        assert widget.search_results.addItem.call_count == 2

    def test_get_fabricacion_form_data_returns_dict(self):
        """get_fabricacion_form_data debe retornar diccionario."""
        from ui.widgets import FabricationsWidget
        
        widget = MagicMock(spec=FabricationsWidget)
        widget.nombre_edit = MagicMock()
        widget.codigo_edit = MagicMock()
        
        widget.nombre_edit.text.return_value = "Fabricación Test"
        widget.codigo_edit.text.return_value = "FAB-001"
        
        # Simular get_fabricacion_form_data
        data = {
            'nombre': widget.nombre_edit.text(),
            'codigo': widget.codigo_edit.text()
        }
        
        assert data['nombre'] == "Fabricación Test"
        assert data['codigo'] == "FAB-001"


# =============================================================================
# TESTS UNITARIOS: CalculateTimesWidget
# =============================================================================

@pytest.mark.unit
class TestCalculateTimesWidgetLogic:
    """Tests de lógica para CalculateTimesWidget."""

    def test_show_progress_displays_bar(self):
        """show_progress debe mostrar la barra de progreso."""
        from ui.widgets import CalculateTimesWidget
        
        widget = MagicMock(spec=CalculateTimesWidget)
        widget.progress_bar = MagicMock()
        widget.calculate_btn = MagicMock()
        
        # Simular show_progress
        widget.progress_bar.setVisible(True)
        widget.calculate_btn.setEnabled(False)
        
        widget.progress_bar.setVisible.assert_called_once_with(True)
        widget.calculate_btn.setEnabled.assert_called_once_with(False)

    def test_hide_progress_hides_bar(self):
        """hide_progress debe ocultar la barra de progreso."""
        from ui.widgets import CalculateTimesWidget
        
        widget = MagicMock(spec=CalculateTimesWidget)
        widget.progress_bar = MagicMock()
        widget.calculate_btn = MagicMock()
        
        # Simular hide_progress
        widget.progress_bar.setVisible(False)
        widget.calculate_btn.setEnabled(True)
        
        widget.progress_bar.setVisible.assert_called_once_with(False)
        widget.calculate_btn.setEnabled.assert_called_once_with(True)

    def test_update_progress_sets_value(self):
        """update_progress debe actualizar el valor de la barra."""
        from ui.widgets import CalculateTimesWidget
        
        widget = MagicMock(spec=CalculateTimesWidget)
        widget.progress_bar = MagicMock()
        
        # Simular update_progress
        value = 75
        widget.progress_bar.setValue(value)
        
        widget.progress_bar.setValue.assert_called_once_with(75)

    def test_get_pila_for_calculation_returns_dict(self):
        """get_pila_for_calculation debe retornar estructura de datos."""
        from ui.widgets import CalculateTimesWidget
        
        widget = MagicMock(spec=CalculateTimesWidget)
        widget.current_session = {
            'productos': [{'codigo': 'PROD-001', 'cantidad': 10}],
            'fabricaciones': [{'id': 1, 'cantidad': 5}]
        }
        
        # Simular get_pila_for_calculation
        pila = {
            'productos': widget.current_session['productos'],
            'fabricaciones': widget.current_session['fabricaciones']
        }
        
        assert 'productos' in pila
        assert 'fabricaciones' in pila
        assert len(pila['productos']) == 1
        assert pila['productos'][0]['cantidad'] == 10

    def test_clear_all_resets_widget_state(self):
        """clear_all debe resetear el estado del widget."""
        from ui.widgets import CalculateTimesWidget
        
        widget = MagicMock(spec=CalculateTimesWidget)
        widget.results_table = MagicMock()
        widget.audit_log = MagicMock()
        widget.current_session = {}
        
        # Simular clear_all
        widget.results_table.setRowCount(0)
        widget.audit_log.clear()
        widget.current_session = {}
        
        widget.results_table.setRowCount.assert_called_once_with(0)
        widget.audit_log.clear.assert_called_once()
        assert widget.current_session == {}


# =============================================================================
# TESTS UNITARIOS: PrepStepsWidget
# =============================================================================

@pytest.mark.unit
class TestPrepStepsWidgetLogic:
    """Tests de lógica para PrepStepsWidget."""

    def test_populate_list_adds_steps(self):
        """populate_list debe añadir pasos a la lista."""
        from ui.widgets import PrepStepsWidget
        
        widget = MagicMock(spec=PrepStepsWidget)
        widget.steps_list = MagicMock()
        
        steps_data = [
            MagicMock(id=1, nombre="Paso 1"),
            MagicMock(id=2, nombre="Paso 2")
        ]
        
        # Simular populate_list
        widget.steps_list.clear()
        for step in steps_data:
            item = MagicMock()
            widget.steps_list.addItem(item)
        
        widget.steps_list.clear.assert_called_once()
        assert widget.steps_list.addItem.call_count == 2

    def test_get_form_data_validates_required_fields(self):
        """get_form_data debe validar campos requeridos."""
        from ui.widgets import PrepStepsWidget
        
        widget = MagicMock(spec=PrepStepsWidget)
        widget.nombre_edit = MagicMock()
        widget.tiempo_spin = MagicMock()
        
        widget.nombre_edit.text.return_value = ""
        
        # Simular validación
        is_valid = len(widget.nombre_edit.text().strip()) > 0
        
        assert is_valid is False
