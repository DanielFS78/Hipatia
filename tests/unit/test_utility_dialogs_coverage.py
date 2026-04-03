# -*- coding: utf-8 -*-
"""Tests unitarios para diálogos de utilidad: AddBreak, Login, ChangePassword, Sync, HojasExcel, MultiWorker."""
import pytest
from PyQt6.QtCore import Qt
from ui.dialogs.utility_dialogs import (
    AddBreakDialog, LoginDialog, ChangePasswordDialog,
    SyncDialog, SeleccionarHojasExcelDialog, MultiWorkerSelectionDialog
)
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QCheckBox
from core.dtos import (
    DatabaseComparisonDTO, SyncTableDifferencesDTO, SyncRecordDTO, SyncRecordPayloadDTO
)

pytestmark = pytest.mark.unit


def test_add_break_dialog(qtbot):
    dialog = AddBreakDialog()
    qtbot.addWidget(dialog)
    dialog.start_time_edit.time().setHMS(12, 0, 0)
    dialog.end_time_edit.time().setHMS(12, 30, 0)
    times = dialog.get_times()
    assert "start" in times
    assert "end" in times
    
def test_login_dialog(qtbot):
    dialog = LoginDialog()
    qtbot.addWidget(dialog)
    dialog.username_edit.setText("testuser")
    dialog.password_edit.setText("testpass")
    creds = dialog.get_credentials()
    assert creds == ("testuser", "testpass")

def test_change_password_dialog(qtbot):
    dialog = ChangePasswordDialog(require_current_password=True)
    qtbot.addWidget(dialog)
    dialog.current_password_edit.setText("old")
    dialog.new_password_edit.setText("new")
    dialog.confirm_password_edit.setText("new")
    pwds = dialog.get_passwords()
    assert pwds["current"] == "old"
    assert pwds["new"] == "new"
    assert pwds["confirm"] == "new"
    
    dialog2 = ChangePasswordDialog(require_current_password=False)
    qtbot.addWidget(dialog2)
    assert dialog2.current_password_edit.isHidden()

def test_sync_dialog(qtbot):
    differences = DatabaseComparisonDTO(
        tables=[
            SyncTableDifferencesDTO(
                table_name="usuarios",
                differences=[
                    SyncRecordDTO(action="new", data=SyncRecordPayloadDTO(fields={"id": 1, "nombre": "User1", "rol": "admin"})),
                    SyncRecordDTO(action="new", data=SyncRecordPayloadDTO(fields={"id": 2, "nombre": "User2", "rol": "operario"}))
                ]
            )
        ]
    )
    dialog = SyncDialog(differences)
    qtbot.addWidget(dialog)
    
    # Just 1 tab for 'usuarios'
    assert dialog.tab_widget.count() == 1
    widget = dialog.tab_widget.widget(0)
    assert widget is not None
    table = widget.findChild(QTableWidget)
    assert table is not None
    assert table.rowCount() == 2
    
    # Check the first item
    item = table.item(0, 0)
    assert item is not None
    item.setCheckState(Qt.CheckState.Checked)
    
    changes = dialog.get_selected_changes()
    assert isinstance(changes, DatabaseComparisonDTO)
    assert len(changes.tables) == 1
    assert changes.tables[0].table_name == "usuarios"
    assert len(changes.tables[0].differences) == 1
    assert changes.tables[0].differences[0].data.fields["id"] == 1

def test_seleccionar_hojas_excel_dialog(qtbot):
    dialog = SeleccionarHojasExcelDialog()
    qtbot.addWidget(dialog)
    dialog.check_resumen.setChecked(True)
    dialog.check_desglose.setChecked(False)
    dialog.check_trabajador.setChecked(True)
    
    opts = dialog.get_opciones()
    assert opts["imprimir_resumen"] is True
    assert opts["imprimir_desglose"] is False
    assert opts["imprimir_trabajador"] is True

def test_multi_worker_selection_dialog(qtbot):
    workers = ["Juan", "Pedro", "Ana"]
    dialog = MultiWorkerSelectionDialog(workers, previously_selected=["Ana"])
    qtbot.addWidget(dialog)
    
    assert len(dialog.checkboxes) == 3
    # Ana should be checked
    assert dialog.checkboxes[2].isChecked()
    
    dialog.checkboxes[0].setChecked(True) # select Juan
    selected = dialog.get_selected_workers()
    assert "Juan" in selected
    assert "Ana" in selected
    assert "Pedro" not in selected
