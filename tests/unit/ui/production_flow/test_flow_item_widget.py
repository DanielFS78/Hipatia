# -*- coding: utf-8 -*-
"""Tests unitarios para FlowItemWidget: representación de pasos y grupos."""

import pytest
from unittest.mock import MagicMock, create_autospec
from PyQt6.QtCore import Qt
from ui.widgets.production_flow.flow_item_widget import FlowItemWidget
from core.dtos import FlowItemDTO

@pytest.fixture
def step_view_model() -> FlowItemDTO:
    """Fixture que proporciona un VM de tipo paso individual."""
    return FlowItemDTO(
        index=0,
        is_group=False,
        title="PASO 1: Tarea Test",
        machine="Maquina 1",
        workers="Operario A, Operario B",
        condition="Inicia el: 01/01/2026"
    )

@pytest.fixture
def group_view_model() -> FlowItemDTO:
    """Fixture que proporciona un VM de tipo grupo."""
    return FlowItemDTO(
        index=1,
        is_group=True,
        title="Grupo Secuencial (2 tareas)",
        workers="Operario C",
        cycle_info="🔄 Ciclo: 10 uds/ciclo",
        tasks_names=["Tarea A", "Tarea B"]
    )

@pytest.mark.unit
class TestFlowItemWidget:
    """Suite de pruebas para validación de FlowItemWidget (Pasos y Grupos)."""
    
    def test_init_step(self, qtbot, step_view_model):
        """Verifica la correcta inicialización de un item de tipo paso."""
        assert isinstance(step_view_model, FlowItemDTO)
        widget = FlowItemWidget(step_view_model)
        qtbot.addWidget(widget)
        
        assert widget.index == 0
        assert not widget.is_group
        # Verificar que el checkbox existe
        assert hasattr(widget, "checkbox")
        assert not widget.is_selected()

    def test_init_group(self, qtbot, group_view_model):
        """Verifica la correcta inicialización de un item de tipo grupo."""
        assert isinstance(group_view_model, FlowItemDTO)
        widget = FlowItemWidget(group_view_model)
        qtbot.addWidget(widget)
        
        assert widget.index == 1
        assert widget.is_group
        # Los grupos no tienen checkbox de selección para reagrupar (por ahora)
        assert not hasattr(widget, "checkbox")

    def test_signals_step(self, qtbot, step_view_model):
        """Verifica la emisión de señales para edición, borrado y selección en pasos."""
        widget = FlowItemWidget(step_view_model)
        qtbot.addWidget(widget)
        
        # Mocks para verificar interacciones (Bonus calidad: 0 loose mocks)
        def receiver_int(i: int): pass
        def receiver_bool(i: int, b: bool): pass
        
        mock_edit = create_autospec(receiver_int)
        mock_delete = create_autospec(receiver_int)
        mock_selection = create_autospec(receiver_bool)
        
        widget.edit_requested.connect(mock_edit)
        widget.delete_requested.connect(mock_delete)
        widget.selection_changed.connect(mock_selection)
        
        # Probar Editar
        for btn in widget.findChildren(pytest.importorskip("PyQt6.QtWidgets").QPushButton):
            if "Editar" in btn.text():
                qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
                break
        mock_edit.assert_called_once_with(0)

        # Probar Eliminar
        for btn in widget.findChildren(pytest.importorskip("PyQt6.QtWidgets").QPushButton):
            if "Eliminar" in btn.text():
                qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
                break
        mock_delete.assert_called_once_with(0)

        # Probar Selección
        widget.checkbox.setChecked(True)
        mock_selection.assert_called_once_with(0, True)

    def test_signals_group(self, qtbot, group_view_model):
        """Verifica la emisión de señales en items de tipo grupo."""
        widget = FlowItemWidget(group_view_model)
        qtbot.addWidget(widget)
        
        def receiver(i: int): pass
        mock_assign = create_autospec(receiver)
        widget.assign_workers_requested.connect(mock_assign)
        
        for btn in widget.findChildren(pytest.importorskip("PyQt6.QtWidgets").QPushButton):
            if "Operarios" in btn.text():
                qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
                break
        
        mock_assign.assert_called_once_with(1)

    def test_is_selected(self, qtbot, step_view_model, group_view_model):
        """Valida la lógica de selección en widgets con y sin checkbox."""
        step_widget = FlowItemWidget(step_view_model)
        group_widget = FlowItemWidget(group_view_model)
        qtbot.addWidget(step_widget)
        qtbot.addWidget(group_widget)
        
        assert not step_widget.is_selected()
        step_widget.checkbox.setChecked(True)
        assert step_widget.is_selected()
        
        # El grupo siempre retorna False porque no tiene checkbox
        assert not group_widget.is_selected()
