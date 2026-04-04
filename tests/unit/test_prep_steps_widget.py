# -*- coding: utf-8 -*-
"""Tests unitarios para PrepStepsWidget."""
import pytest
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt

from ui.widgets.prep_steps_widget import PrepStepsWidget


@pytest.mark.unit
class TestPrepStepsWidget:
    """Tests unitarios para PrepStepsWidget."""

    @pytest.fixture
    def widget(self, qtbot):
        """Fixture para PrepStepsWidget."""
        w = PrepStepsWidget()
        qtbot.addWidget(w)
        return w

    def test_init(self, widget):
        """Widget se inicializa correctamente."""
        assert widget.current_step_id is None
        assert widget.form_widgets == {}

    def test_load_preprocesos_data(self, widget):
        """Carga datos de preprocesos en la lista."""
        data = [
            {"id": 1, "nombre": "Corte", "descripcion": "Fase de corte"},
            {"id": 2, "nombre": "Soldadura", "descripcion": "Fase de soldadura"},
        ]
        widget.load_preprocesos_data(data)
        assert widget.steps_list.count() == 2

    def test_populate_list(self, widget):
        """Llena la lista con datos de steps (formato tupla)."""
        steps = [
            (1, "Corte", "Desc", 10, None, None),
            (2, "Soldadura", "Desc", 20, None, None),
        ]
        widget.populate_list(steps)
        assert widget.steps_list.count() == 2

    def test_clear_details_area(self, widget):
        """Limpia el área de detalles."""
        widget.current_step_id = 5
        widget.clear_details_area()
        assert widget.current_step_id is None
        assert widget.form_widgets == {}

    def test_show_step_details(self, widget):
        """Muestra detalles de un paso."""
        step = {
            "id": 1,
            "nombre": "Corte",
            "tiempo_fase": 10,
            "descripcion": "Fase",
            "es_diario": 0,
            "es_verificacion": 0,
        }
        widget.show_step_details(step)
        assert widget.current_step_id == 1
        assert widget.form_widgets["nombre"].text() == "Corte"

    def test_show_add_new_form(self, widget):
        """Muestra formulario de nuevo paso."""
        widget.show_add_new_form()
        assert widget.current_step_id is None
        assert widget.form_widgets["title"].text() == "Añadir Nueva Fase de Preparación"

    def test_get_form_data_empty(self, widget):
        """get_form_data sin formulario retorna None."""
        assert widget.get_form_data() is None

    def test_get_form_data_valid(self, widget):
        """get_form_data retorna datos correctos."""
        widget.show_add_new_form()
        widget.form_widgets["nombre"].setText("Corte")
        widget.form_widgets["tiempo_fase"].setText("10")
        data = widget.get_form_data()
        assert data is not None
        assert data["nombre"] == "Corte"
        assert data["tiempo_fase"] == 10.0

    def test_get_form_data_missing_fields(self, widget, qtbot):
        """get_form_data con campos vacíos emite validation_warning y retorna None."""
        widget.show_add_new_form()
        widget.form_widgets["nombre"].setText("")
        widget.form_widgets["tiempo_fase"].setText("")
        with qtbot.waitSignal(widget.validation_warning, timeout=1000) as blocker:
            assert widget.get_form_data() is None
        assert blocker.args == ["Campos Obligatorios", "El nombre y el tiempo son obligatorios."]

    def test_get_form_data_invalid_tiempo(self, widget, qtbot):
        """get_form_data con tiempo inválido emite validation_warning."""
        widget.show_add_new_form()
        widget.form_widgets["nombre"].setText("Test")
        widget.form_widgets["tiempo_fase"].setText("abc")
        with qtbot.waitSignal(widget.validation_warning, timeout=1000):
            assert widget.get_form_data() is None

    def test_get_form_data_negative_tiempo(self, widget, qtbot):
        """get_form_data con tiempo negativo emite validation_warning."""
        widget.show_add_new_form()
        widget.form_widgets["nombre"].setText("Test")
        widget.form_widgets["tiempo_fase"].setText("-5")
        with qtbot.waitSignal(widget.validation_warning, timeout=1000):
            assert widget.get_form_data() is None

    def test_get_form_data_verificacion(self, widget):
        """get_form_data con verificación hace tiempo 0."""
        widget.show_add_new_form()
        widget.form_widgets["nombre"].setText("Check")
        widget.form_widgets["tiempo_fase"].setText("10")
        widget.form_widgets["es_verificacion"].setChecked(True)
        data = widget.get_form_data()
        assert data is not None
        assert data["tiempo_fase"] == 0
        assert data["es_verificacion"] == 1

    def test_on_save_button_add(self, widget, qtbot):
        """Guardar nuevo paso emite add_step_signal."""
        widget.show_add_new_form()
        widget.form_widgets["nombre"].setText("Corte")
        widget.form_widgets["tiempo_fase"].setText("10")
        with qtbot.waitSignal(widget.add_step_signal, timeout=1000) as blocker:
            widget._on_save_button_clicked()
        assert blocker.signal_triggered

    def test_on_save_button_update(self, widget, qtbot):
        """Guardar paso existente emite update_step_signal."""
        step = {
            "id": 1,
            "nombre": "Corte",
            "tiempo_fase": 10,
            "descripcion": "",
            "es_diario": 0,
            "es_verificacion": 0,
        }
        widget.show_step_details(step)
        widget.form_widgets["nombre"].setText("Corte Updated")
        widget.form_widgets["tiempo_fase"].setText("15")
        with qtbot.waitSignal(widget.update_step_signal, timeout=1000) as blocker:
            widget._on_save_button_clicked()
        assert blocker.signal_triggered

    def test_clear_form(self, widget):
        """clear_form limpia selección y detalles."""
        widget.show_add_new_form()
        widget.clear_form()
        assert widget.current_step_id is None

    def test_delete_signal(self, widget, qtbot):
        """delete_step_signal se emite correctamente."""
        with qtbot.waitSignal(widget.delete_step_signal, timeout=1000) as blocker:
            widget.delete_step_signal.emit(3)
        assert blocker.args == [3]
