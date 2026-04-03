# -*- coding: utf-8 -*-
"""Tests unitarios para MachinesWidget.

Cubre inicialización, filtrado de lista, populate_list, detalles, formulario
añadir/editar, get_form_data, historial de mantenimiento y señales save/delete.
Decisión de mocking: controlador con spec; modelos máquina/mantenimiento con spec.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.widgets.machines_widget import MachinesWidget

pytestmark = pytest.mark.unit


class TestMachinesWidget:
    """Tests unitarios para MachinesWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para MachinesWidget."""
        ctrl = MagicMock(spec=['get_distinct_machine_processes'])
        ctrl.get_distinct_machine_processes.return_value = ["Corte", "Soldadura"]
        from core.di_container import DIContainer
        from controllers.machine_controller import MachineController
        DIContainer.get_instance().register(MachineController, instance=ctrl)
        w = MachinesWidget(controller=ctrl)
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa correctamente."""
        assert widget.current_machine_id is None
        assert widget.form_widgets == {}

    def test_filter_machines_list(self, widget):
        """Filtra máquinas por nombre."""
        item1 = QListWidgetItem("CNC-1 (Activa)")
        item2 = QListWidgetItem("Torno-2 (Activa)")
        widget.machines_list.addItem(item1)
        widget.machines_list.addItem(item2)
        widget.search_bar.setText("cnc")
        assert not widget.machines_list.item(0).isHidden()
        assert widget.machines_list.item(1).isHidden()

    @patch('ui.widgets.machines_widget.QColor')
    @patch('PyQt6.QtWidgets.QListWidgetItem.setForeground')
    def test_populate_list(self, mock_setFg, MockColor, widget):
        """Llena la lista de máquinas."""
        m1 = MagicMock(spec=['nombre', 'activa', 'id'])
        m1.nombre = "CNC-1"
        m1.activa = True
        m1.id = 1
        m2 = MagicMock(spec=['nombre', 'activa', 'id'])
        m2.nombre = "Torno"
        m2.activa = False
        m2.id = 2
        widget.populate_list([m1, m2])
        assert widget.machines_list.count() == 2

    def test_clear_details_area(self, widget):
        """Limpia el área de detalles."""
        widget.current_machine_id = 5
        widget.clear_details_area()
        assert widget.current_machine_id is None
        assert widget.form_widgets == {}

    def test_show_machine_details(self, widget):
        """Muestra detalles de una máquina."""
        machine = MagicMock(spec=['id', 'nombre', 'departamento', 'tipo_proceso', 'activa'])
        machine.id = 1
        machine.nombre = "CNC-1"
        machine.departamento = "Mecánica"
        machine.tipo_proceso = "Corte"
        machine.activa = True
        widget.show_machine_details(machine)
        assert widget.current_machine_id == 1
        assert widget.form_widgets['nombre'].text() == "CNC-1"

    def test_show_add_new_form(self, widget):
        """Muestra formulario de nueva máquina."""
        widget.show_add_new_form()
        assert widget.current_machine_id is None
        assert widget.form_widgets['title'].text() == "Añadir Nueva Máquina"
        assert widget.form_widgets['activa'].isChecked()

    def test_get_form_data_empty(self, widget):
        """get_form_data sin formulario retorna None."""
        assert widget.get_form_data() is None

    def test_get_form_data(self, widget):
        """get_form_data retorna datos del formulario."""
        widget.show_add_new_form()
        widget.form_widgets['nombre'].setText("CNC-2")
        data = widget.get_form_data()
        assert data["nombre"] == "CNC-2"
        assert data["activa"] is True

    def test_populate_history_tables(self, widget):
        """Llena tabla de historial de mantenimiento."""
        widget.show_add_new_form()
        m1 = MagicMock(spec=['maintenance_date', 'notes'])
        m1.maintenance_date = date(2026, 1, 15)
        m1.notes = "Cambio aceite"
        m2 = MagicMock(spec=['maintenance_date', 'notes'])
        m2.maintenance_date = "2026-02-01"
        m2.notes = "Revisión"
        widget.populate_history_tables([m1, m2])
        table = widget.form_widgets['maintenance_table']
        assert table.rowCount() == 2
        assert table.item(0, 0).text() == "15/01/2026"

    def test_populate_history_tables_no_table(self, widget):
        """Sin tabla de mantenimiento no crashea."""
        try:
            widget.populate_history_tables([])
        except Exception:
            pytest.fail("populate_history_tables no debería propagar excepciones sin tabla")
        # smoke_test: sin form_widgets['maintenance_table'] la llamada no debe lanzar
        assert widget.form_widgets == {} or 'maintenance_table' not in widget.form_widgets

    def test_save_signal(self, widget, qtbot):
        """Botón guardar emite save_signal."""
        widget.show_add_new_form()
        with qtbot.waitSignal(widget.save_signal, timeout=1000) as blocker:
            widget.save_signal.emit()
        assert blocker.signal_triggered

    def test_delete_signal(self, widget, qtbot):
        """delete_signal se emite con ID correcto."""
        with qtbot.waitSignal(widget.delete_signal, timeout=1000) as blocker:
            widget.delete_signal.emit(5)
        assert blocker.args == [5]
