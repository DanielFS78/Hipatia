# -*- coding: utf-8 -*-
"""
Nombre del Módulo: bom_import_preview_dialog
Descripción: Diálogo PyQt6 de supervisión previa a importar un BOM A3RP. Muestra un
             árbol (QTreeWidget) con columna «Importar» (desmarcada por defecto) y
             desplegable de ``BOMImportRole`` habilitado solo si la fila está marcada.
             Valida que exista exactamente un producto final antes de ``accept``.
"""

from __future__ import annotations

from typing import Iterator, Optional, cast

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor

from core.import_manager.dto import BOMImportRole, BOMNodeDTO


class BOMImportPreviewDialog(QDialog):
    """
    Permite al usuario decidir qué ramas del BOM se persisten y con qué rol semántico.

    Tras ``accept``, ``get_supervised_tree`` devuelve el mismo ``BOMNodeDTO`` raíz con
    ``import_selected`` e ``import_role`` rellenados para el servicio de importación.
    """

    _PLACEHOLDER_INDEX = 0

    @staticmethod
    def validate_row_selections_from_states(
        states: list[tuple[bool, Optional[BOMImportRole]]],
    ) -> Optional[str]:
        """
        Valida la selección sin depender de Qt (testeable en unit puro).

        Args:
            states: Lista de ``(marcado, rol)`` por fila. ``rol`` es None si no aplica
                o equivale al placeholder.

        Returns:
            Mensaje de error o None si la selección es válida.
        """
        finals = 0
        for checked, role in states:
            if not checked:
                continue
            if role is None:
                return (
                    "Cada fila marcada debe tener un tipo seleccionado "
                    "(no deje «— Elegir tipo —»)."
                )
            if role == BOMImportRole.FINAL_PRODUCT:
                finals += 1
        if finals == 0:
            return "Debe marcar exactamente un «Producto final»."
        if finals > 1:
            return "Solo puede haber una fila marcada como «Producto final»."
        return None

    def __init__(self, root_node: BOMNodeDTO, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            root_node: Árbol BOM (se muta al confirmar con ``get_supervised_tree``).
            parent: Ventana padre opcional de Qt.
        """
        super().__init__(parent)
        self.root_node = root_node
        self.setWindowTitle("Supervisión de Importación de Estructura A3RP")
        self.resize(980, 620)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        info_label = QLabel(
            "<b>Instrucciones:</b><br>"
            "1) Marque solo las filas que desea importar (por defecto todo está desmarcado).<br>"
            "2) Para cada fila marcada, elija el <b>tipo</b> en el desplegable.<br>"
            "3) Debe haber <b>exactamente un</b> <b>Producto final</b> (define código y descripción del producto).<br>"
            "4) Subfabricaciones, procesos mecánicos y componentes se asocian a ese producto final."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(
            ["Importar", "Tipo", "Nivel", "Código", "Denominación", "Cant."]
        )
        header = self.tree.header()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.tree.itemChanged.connect(self._on_item_changed)

        root_item = self.tree.invisibleRootItem()
        self.tree.blockSignals(True)
        try:
            if root_item is not None:
                self._populate_tree(self.root_node, root_item)
        finally:
            self.tree.blockSignals(False)

        self.tree.expandAll()
        layout.addWidget(self.tree)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        btn_layout = QHBoxLayout()
        self.btn_import = QPushButton("Proceder con la Importación")
        self.btn_import.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold; padding: 8px;"
        )
        self.btn_import.clicked.connect(self._on_accept_clicked)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_import)
        layout.addLayout(btn_layout)

    def _make_role_combo(self) -> QComboBox:
        """Crea el QComboBox de rol con ítem placeholder y estilo de error vía señal."""
        combo = QComboBox()
        combo.addItem("— Elegir tipo —", None)
        combo.addItem("Producto final", BOMImportRole.FINAL_PRODUCT)
        combo.addItem("Subfabricación", BOMImportRole.SUBFABRICATION)
        combo.addItem("Proceso mecánico", BOMImportRole.MECHANICAL_PROCESS)
        combo.addItem("Componente", BOMImportRole.COMPONENT)
        combo.setEnabled(False)
        combo.currentIndexChanged.connect(self._on_combo_changed)
        return combo

    def _on_combo_changed(self, _index: int) -> None:
        """Evita filas marcadas sin tipo válido (placeholder)."""
        combo = self.sender()
        if not isinstance(combo, QComboBox):
            return
        item = self._item_for_combo(combo)
        if item is None:
            return
        if item.checkState(0) != Qt.CheckState.Checked:
            return
        if combo.currentIndex() == self._PLACEHOLDER_INDEX:
            item.setForeground(1, QBrush(QColor(192, 57, 43)))
        else:
            item.setForeground(1, QBrush())

    def _item_for_combo(self, combo: QComboBox) -> Optional[QTreeWidgetItem]:
        """Localiza la fila del árbol que contiene el combo dado (recorrido en profundidad)."""
        it = QTreeWidgetItemIterator(self.tree)
        while it.value() is not None:
            item = it.value()
            if item is not None and self.tree.itemWidget(item, 1) is combo:
                return item
            it += 1
        return None

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0:
            return
        w = self.tree.itemWidget(item, 1)
        if w is None:
            return
        combo = cast(QComboBox, w)
        if item.checkState(0) == Qt.CheckState.Checked:
            combo.setEnabled(True)
        else:
            combo.blockSignals(True)
            try:
                combo.setCurrentIndex(self._PLACEHOLDER_INDEX)
                combo.setEnabled(False)
            finally:
                combo.blockSignals(False)
            item.setForeground(1, QBrush())

    def _populate_tree(self, node: BOMNodeDTO, parent_item: QTreeWidgetItem) -> None:
        """Crea un ``QTreeWidgetItem`` por nodo DTO, checkbox desmarcado y combo asociado."""
        item = QTreeWidgetItem(parent_item)
        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )
        # Importación consciente: nada marcado por defecto (se ignora el hint del Excel)
        item.setCheckState(0, Qt.CheckState.Unchecked)

        combo = self._make_role_combo()
        self.tree.setItemWidget(item, 1, combo)

        item.setText(2, str(node.nivel))
        item.setText(3, node.codigo_componente)
        item.setText(4, node.denominacion)
        item.setText(5, f"{node.cantidad:g}")

        item.setData(0, Qt.ItemDataRole.UserRole, node)

        for hijo in node.hijos:
            self._populate_tree(hijo, item)

    def _iter_items(self, item: Optional[QTreeWidgetItem]) -> Iterator[QTreeWidgetItem]:
        """Recorre en preorden el subárbol colgando de ``item`` (generador)."""
        if item is None:
            return
        yield item
        for i in range(item.childCount()):
            child = item.child(i)
            yield from self._iter_items(child)

    def _validation_error_message(self) -> Optional[str]:
        """Compone la lista de estados de fila y delega en ``validate_row_selections_from_states``."""
        top = self.tree.topLevelItem(0)
        states: list[tuple[bool, Optional[BOMImportRole]]] = []
        for tree_item in self._iter_items(top):
            checked = tree_item.checkState(0) == Qt.CheckState.Checked
            w = self.tree.itemWidget(tree_item, 1)
            role: Optional[BOMImportRole] = None
            if w is None:
                if checked:
                    return "Falta el desplegable de tipo en una fila marcada."
                states.append((checked, None))
                continue
            combo = cast(QComboBox, w)
            if checked and combo.currentIndex() != self._PLACEHOLDER_INDEX:
                raw = combo.currentData(Qt.ItemDataRole.UserRole)
                if isinstance(raw, BOMImportRole):
                    role = raw
            states.append((checked, role))
        return self.validate_row_selections_from_states(states)

    def _on_accept_clicked(self) -> None:
        err = self._validation_error_message()
        if err:
            QMessageBox.warning(self, "Revisar importación", err)
            return
        self.accept()

    def get_supervised_tree(self) -> BOMNodeDTO:
        """
        Recorre el árbol de la UI y escribe ``import_selected`` / ``import_role`` en cada DTO.

        Returns:
            La misma instancia ``root_node`` mutada para pasar a ``BOMImportService.import_bom_tree``.
        """
        top_item = self.tree.topLevelItem(0)
        if top_item is not None:
            self._sync_node_from_item(top_item)
        return self.root_node

    def _sync_node_from_item(self, item: QTreeWidgetItem) -> None:
        """Propaga checkbox y combo del ítem al ``BOMNodeDTO`` almacenado en ``UserRole``."""
        node: BOMNodeDTO | None = item.data(0, Qt.ItemDataRole.UserRole)
        if node:
            checked = item.checkState(0) == Qt.CheckState.Checked
            node.import_selected = checked
            w = self.tree.itemWidget(item, 1)
            if checked and w is not None:
                combo = cast(QComboBox, w)
                if combo.currentIndex() != self._PLACEHOLDER_INDEX:
                    role_raw = combo.currentData(Qt.ItemDataRole.UserRole)
                    node.import_role = role_raw if isinstance(role_raw, BOMImportRole) else None
                else:
                    node.import_role = None
            else:
                node.import_role = None
            # Compat: mantener hint legacy alineado con subfabricación explícita
            node.es_subfabricacion = node.import_role == BOMImportRole.SUBFABRICATION

        for i in range(item.childCount()):
            child = item.child(i)
            if child is not None:
                self._sync_node_from_item(child)
