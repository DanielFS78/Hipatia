# -*- coding: utf-8 -*-
"""
BOMImportPreviewDialog: Diálogo de supervisión para la importación de estructuras.
==================================================================================
Muestra un árbol jerárquico (QTreeWidget) que representa la estructura A3RP.
Permite al usuario marcar/desmarcar qué nodos desea importar como subfabricaciones.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QHBoxLayout, QLabel, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from core.import_manager.dto import BOMNodeDTO


class BOMImportPreviewDialog(QDialog):
    """
    Diálogo interactivo para previsualizar y supervisar el árbol BOM antes de importar.
    """
    
    def __init__(self, root_node: BOMNodeDTO, parent=None) -> None:
        super().__init__(parent)
        self.root_node = root_node
        self.setWindowTitle("Supervisión de Importación de Estructura A3RP")
        self.resize(900, 600)
        self._init_ui()
        
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Cabecera informativa
        info_label = QLabel(
            "<b>Instrucciones:</b> Revisa la estructura del producto.<br>"
            "Los elementos marcados con el Checkbox se importarán como <b>Subfabricaciones</b> (con sus propios tiempos y procesos).<br>"
            "Los elementos no marcados se tratarán como materiales simples o se ignorarán si no tienen relevancia operativa."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Árbol de previsualización
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["Importar Subfab.", "Nivel", "Código", "Denominación", "Cant."])
        header = self.tree.header()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        root_item = self.tree.invisibleRootItem()
        if root_item is not None:
            self._populate_tree(self.root_node, root_item)
        self.tree.expandAll()
        layout.addWidget(self.tree)
        
        # Línea separadora
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        self.btn_import = QPushButton("Proceder con la Importación")
        self.btn_import.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        self.btn_import.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_import)
        layout.addLayout(btn_layout)

    def _populate_tree(self, node: BOMNodeDTO, parent_item: QTreeWidgetItem) -> None:
        """
        Rellena recursivamente el QTreeWidget con la estructura del nodo.
        
        Args:
            node: DTO del nodo BOM a visualizar.
            parent_item: Item del árbol que actuará como padre.
        """
        item = QTreeWidgetItem(parent_item)
        
        # Columna 0: Checkbox de supervisión
        # Si el adaptador dijo que era compuesto, lo marcamos por defecto
        item.setCheckState(0, Qt.CheckState.Checked if node.es_subfabricacion else Qt.CheckState.Unchecked)
        
        item.setText(1, str(node.nivel))
        item.setText(2, node.codigo_componente)
        item.setText(3, node.denominacion)
        item.setText(4, f"{node.cantidad:g}")
        
        # Guardar referencia al DTO en el item para recuperarlo luego
        item.setData(0, Qt.ItemDataRole.UserRole, node)
        
        for hijo in node.hijos:
            self._populate_tree(hijo, item)

    def get_supervised_tree(self) -> BOMNodeDTO:
        """
        Recorre el árbol de la UI y actualiza los flags 'es_subfabricacion' 
        según lo que el usuario haya marcado/desmarcado.
        """
        top_item = self.tree.topLevelItem(0)
        if top_item is not None:
            self._sync_node_from_item(top_item)
        return self.root_node

    def _sync_node_from_item(self, item: QTreeWidgetItem) -> None:
        """
        Sincroniza el estado del checkbox de la UI de vuelta al DTO de forma recursiva.
        
        Args:
            item: Item del árbol a sincronizar.
        """
        node: BOMNodeDTO = item.data(0, Qt.ItemDataRole.UserRole)
        if node:
            node.es_subfabricacion = (item.checkState(0) == Qt.CheckState.Checked)
            
        for i in range(item.childCount()):
            child = item.child(i)
            if child is not None:
                self._sync_node_from_item(child)
