# -*- coding: utf-8 -*-
"""
Tests para BOMImportPreviewDialog.
Valida la visualización del árbol y la sincronización de checkboxes.
"""

import pytest
from PyQt6.QtCore import Qt
from ui.dialogs.product.bom_import_preview_dialog import BOMImportPreviewDialog
from core.import_manager.dto import BOMNodeDTO

@pytest.fixture
def sample_tree() -> BOMNodeDTO:
    """Proporciona un árbol BOM de ejemplo para las pruebas."""
    raiz = BOMNodeDTO(nivel=0, codigo_componente="ROOT", es_subfabricacion=True)
    hijo = BOMNodeDTO(nivel=1, codigo_componente="SUB", es_subfabricacion=True)
    nieto = BOMNodeDTO(nivel=2, codigo_componente="MAT", es_subfabricacion=False)
    
    raiz.hijos.append(hijo)
    hijo.hijos.append(nieto)
    return raiz

@pytest.mark.ui
class TestBOMImportPreviewDialog:
    """Suite de pruebas para validar el diálogo de previsualización de importación BOM."""
    
    def test_dialog_initial_population(self, qtbot, sample_tree: BOMNodeDTO) -> None:
        """Verifica que el árbol se rellena con los datos del DTO."""
        dialog = BOMImportPreviewDialog(sample_tree)
        qtbot.add_widget(dialog)
        
        # Debe haber un item en la raíz
        assert dialog.tree.topLevelItemCount() == 1
        root_item = dialog.tree.topLevelItem(0)
        assert root_item is not None
        assert root_item.text(2) == "ROOT"
        assert root_item.checkState(0) == Qt.CheckState.Checked
        
        # Debe tener un hijo
        assert root_item.childCount() == 1
        sub_item = root_item.child(0)
        assert sub_item is not None
        assert sub_item.text(2) == "SUB"
        assert sub_item.checkState(0) == Qt.CheckState.Checked
        
        # El nieto no es subfab por defecto
        mat_item = sub_item.child(0)
        assert mat_item is not None
        assert mat_item.checkState(0) == Qt.CheckState.Unchecked

    def test_sync_supervised_changes(self, qtbot, sample_tree: BOMNodeDTO) -> None:
        """Verifica que los cambios en la UI se guardan en el DTO."""
        dialog = BOMImportPreviewDialog(sample_tree)
        qtbot.add_widget(dialog)
        
        root_item = dialog.tree.topLevelItem(0)
        assert root_item is not None
        sub_item = root_item.child(0)
        assert sub_item is not None
        
        # Desmarcar el subconjunto en la UI
        sub_item.setCheckState(0, Qt.CheckState.Unchecked)
        
        # Sincronizar
        supervised_node = dialog.get_supervised_tree()
        
        assert isinstance(supervised_node, BOMNodeDTO)
        assert supervised_node.codigo_componente == "ROOT"
        assert isinstance(supervised_node.hijos[0], BOMNodeDTO)
        assert supervised_node.hijos[0].codigo_componente == "SUB"
        assert supervised_node.hijos[0].es_subfabricacion is False # Cambiado por la UI
