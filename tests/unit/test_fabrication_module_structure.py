# -*- coding: utf-8 -*-
"""Tests de estructura del paquete ui.dialogs.fabrication: exports e imports de diálogos."""
import pytest
import sys
import importlib
from ui.dialogs.fabrication import (
    create_dialog,
    selection_dialogs,
    assignment_dialogs,
    bitacora_dialog,
    input_dialogs,
    persistence_dialogs,
    products_dialog
)

pytestmark = pytest.mark.unit


def test_fabrication_package_exports():
    """Verify that ui.dialogs.fabrication exports strictly typed classes."""
    # Check modules exist
    assert create_dialog
    assert selection_dialogs
    assert assignment_dialogs
    assert bitacora_dialog
    assert input_dialogs
    assert persistence_dialogs
    assert products_dialog

def test_fabrication_dialogs_imports():
    """Verify classes are importable from their new locations."""
    from ui.dialogs.fabrication.create_dialog import CreateFabricacionDialog
    from ui.dialogs.fabrication.selection_dialogs import PreprocesosSelectionDialog
    from ui.dialogs.fabrication.assignment_dialogs import AssignPreprocesosDialog
    from ui.dialogs.fabrication.bitacora_dialog import FabricacionBitacoraDialog
    from ui.dialogs.fabrication.products_dialog import ProductsSelectionDialog
    
    assert bool(CreateFabricacionDialog)
    assert bool(PreprocesosSelectionDialog)
    assert bool(AssignPreprocesosDialog)
    assert bool(FabricacionBitacoraDialog)
    assert bool(ProductsSelectionDialog)

def test_legacy_import_compatibility():
    """Verify that ui.dialogs still exports these classes (backward compatibility)."""
    import ui.dialogs
    
    assert hasattr(ui.dialogs, 'CreateFabricacionDialog')
    assert hasattr(ui.dialogs, 'PreprocesosSelectionDialog')
    assert hasattr(ui.dialogs, 'AssignPreprocesosDialog')
    assert hasattr(ui.dialogs, 'FabricacionBitacoraDialog')
    assert hasattr(ui.dialogs, 'ProductsSelectionDialog')
