# -*- coding: utf-8 -*-
"""Tests unitarios para OrderSetupDialog (tracking): init, get_data, botones accept/reject."""
import pytest
from PyQt6.QtCore import Qt
from ui.dialogs.tracking_dialogs import OrderSetupDialog

pytestmark = pytest.mark.unit


def test_order_setup_dialog_init(qtbot):
    dialog = OrderSetupDialog(default_order="TEST-001")
    qtbot.addWidget(dialog)
    
    assert dialog.windowTitle() == "Iniciar Nueva Producción"
    assert dialog.order_input.text() == "TEST-001"
    assert dialog.quantity_spin.value() == 100

def test_order_setup_dialog_get_data(qtbot):
    dialog = OrderSetupDialog()
    qtbot.addWidget(dialog)
    
    dialog.order_input.setText(" of-2024-abc  ")
    dialog.quantity_spin.setValue(550)
    
    data = dialog.get_data()
    assert data["order_number"] == "OF-2024-ABC"
    assert data["total_units"] == 550

def test_order_setup_dialog_buttons(qtbot):
    dialog = OrderSetupDialog()
    qtbot.addWidget(dialog)
    
    with qtbot.waitSignal(dialog.accepted, timeout=1000) as blocker:
        dialog.accept()
    assert blocker.signal_triggered
        
    dialog2 = OrderSetupDialog()
    qtbot.addWidget(dialog2)
    with qtbot.waitSignal(dialog2.rejected, timeout=1000) as blocker2:
        dialog2.reject()
    assert blocker2.signal_triggered
