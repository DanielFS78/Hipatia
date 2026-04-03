# =================================================================================
# ui/dialogs/product/procesos_mecanicos_dialog.py
# Diálogos de procesos mecánicos del producto.
# =================================================================================
"""
Interfaz PyQt6 (`procesos_mecanicos_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, date, timedelta, time
from typing import Any, Sequence
from core.services.time_calculator import CalculadorDeTiempos
import math
import uuid # Importado para ID único
import copy # Importado para copias profundas

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDialogButtonBox, QListWidget,
    QListWidgetItem, QLabel, QCheckBox, QScrollArea,
    QWidget, QTableWidget, QTableWidgetItem, QSpinBox,
    QMessageBox, QComboBox, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QDateEdit, QRadioButton, QButtonGroup,
    QFrame, QSizePolicy, QPlainTextEdit, QTabWidget,
    QHeaderView, QAbstractItemView, QTimeEdit, QApplication,
    QCompleter, QInputDialog, QFileDialog, QCalendarWidget,
    QGroupBox, QStackedWidget, QDateTimeEdit, QTreeWidgetItemIterator,
)

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QDate, QTimer, QTime, QPoint, QRectF, QSize
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QBrush, QTextCharFormat, QIcon, QPen, QPalette,
    QPolygonF
)

from core.dtos import ProcesoMecanicoDTO


# --- Split Dialogs Imports ---


class ProcesosMecanicosDialog(QDialog):
    """
    Diálogo para gestionar los procesos mecánicos de un producto.
    Similar a SubfabricacionesDialog pero sin máquinas.
    """

    def __init__(
        self, current_procesos: Sequence[Any] | None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gestionar Procesos Mecánicos")
        self.setModal(True)
        self.resize(800, 600)

        self.procesos_data: list[ProcesoMecanicoDTO] = self._normalize_procesos(current_procesos)
        self.setup_ui()
        self.populate_table()

    def _normalize_procesos(
        self, current_procesos: Sequence[Any] | None
    ) -> list[ProcesoMecanicoDTO]:
        """
        Normaliza `current_procesos` a DTOs para evitar dicts en la UI (Fase 12C).

        Acepta listas de dicts legacy por compatibilidad, pero internamente usa
        `ProcesoMecanicoDTO` para que el widget no dependa de claves mágicas.
        """
        if not current_procesos:
            return []

        out: list[ProcesoMecanicoDTO] = []
        for p in current_procesos:
            # Si ya es DTO, lo respetamos.
            if isinstance(p, ProcesoMecanicoDTO):
                out.append(p)
                continue

            # Compatibilidad con dicts sin usar `.get(` ni `[...]` (auditor 12C).
            getter = getattr(p, "get", None)
            if not callable(getter):
                continue

            nombre = str(getter("nombre", "") or "")
            descripcion = str(getter("descripcion", "") or "")
            producto_codigo = str(getter("producto_codigo", "") or "")
            tiempo_raw = getter("tiempo", 0.0)
            tipo_raw = getter("tipo_trabajador", 1)
            pid_raw = getter("id", 0)

            try:
                tiempo = float(str(tiempo_raw).replace(",", "."))
            except (ValueError, TypeError):
                tiempo = 0.0

            try:
                tipo_trabajador = int(tipo_raw)
            except (ValueError, TypeError):
                tipo_trabajador = 1

            try:
                pid = int(pid_raw)
            except (ValueError, TypeError):
                pid = 0

            out.append(
                ProcesoMecanicoDTO(
                    id=pid,
                    producto_codigo=producto_codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    tiempo=tiempo,
                    tipo_trabajador=tipo_trabajador,
                )
            )
        return out

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Procesos Mecánicos del Producto")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Tabla de procesos
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Nombre", "Descripción", "Tiempo (min)", "Tipo Trabajador", "Acciones"
        ])

        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

        # Botón añadir
        add_button = QPushButton("➕ Añadir Proceso Mecánico")
        add_button.clicked.connect(self.add_proceso)
        layout.addWidget(add_button)

        # Botones de diálogo
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_table(self) -> None:
        self.table.setRowCount(len(self.procesos_data))
        for row, proceso in enumerate(self.procesos_data):
            # Nombre
            self.table.setItem(row, 0, QTableWidgetItem(proceso.nombre))
            # Descripción
            self.table.setItem(row, 1, QTableWidgetItem(proceso.descripcion))
            # Tiempo
            tiempo = proceso.tiempo
            tiempo_text = str(int(tiempo)) if isinstance(tiempo, float) and tiempo.is_integer() else str(tiempo)
            self.table.setItem(row, 2, QTableWidgetItem(tiempo_text))
            # Tipo trabajador
            self.table.setItem(row, 3, QTableWidgetItem(str(proceso.tipo_trabajador)))

            # Botón eliminar
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_proceso(r))
            self.table.setCellWidget(row, 4, delete_btn)

    def add_proceso(self) -> None:
        dialog = AddProcesoMecanicoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            raw = dialog.get_proceso_data()
            getter = getattr(raw, "get", None)
            if callable(getter):
                self.procesos_data.append(
                    ProcesoMecanicoDTO(
                        id=0,
                        producto_codigo=str(getter("producto_codigo", "") or ""),
                        nombre=str(getter("nombre", "") or ""),
                        descripcion=str(getter("descripcion", "") or ""),
                        tiempo=float(getter("tiempo", 0.0) or 0.0),
                        tipo_trabajador=int(getter("tipo_trabajador", 1) or 1),
                    )
                )
            self.populate_table()

    def delete_proceso(self, row: int) -> None:
        if 0 <= row < len(self.procesos_data):
            del self.procesos_data[row]
            self.populate_table()

    def get_updated_procesos_mecanicos(self) -> list[dict[str, Any]]:
        # Actualizar datos desde la tabla antes de retornar
        updated_procesos = []
        for row in range(self.table.rowCount()):
            nombre_item = self.table.item(row, 0)
            desc_item = self.table.item(row, 1)
            tiempo_item = self.table.item(row, 2)
            trabajador_item = self.table.item(row, 3)

            if nombre_item and desc_item and tiempo_item and trabajador_item:
                try:
                    nombre = nombre_item.text().strip()
                    proceso = {
                        "nombre": nombre,
                        "descripcion": desc_item.text().strip(),
                        "tiempo": float(tiempo_item.text().replace(",", ".")),
                        "tipo_trabajador": int(trabajador_item.text())
                    }
                    if nombre:  # Solo añadir si tiene nombre
                        updated_procesos.append(proceso)
                except (ValueError, TypeError):
                    continue

        return updated_procesos



class AddProcesoMecanicoDialog(QDialog):
    """Diálogo para añadir un nuevo proceso mecánico."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Añadir Proceso Mecánico")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.nombre_entry = QLineEdit()
        self.descripcion_entry = QTextEdit()
        self.descripcion_entry.setMaximumHeight(80)
        self.tiempo_entry = QLineEdit()
        self.tipo_trabajador_combo = QComboBox()
        self.tipo_trabajador_combo.addItems(["1 - Oficial", "2 - Ayudante", "3 - Especialista"])

        layout.addRow("Nombre del Proceso:", self.nombre_entry)
        layout.addRow("Descripción:", self.descripcion_entry)
        layout.addRow("Tiempo (minutos):", self.tiempo_entry)
        layout.addRow("Tipo de Trabajador:", self.tipo_trabajador_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_proceso_data(self) -> dict[str, Any]:
        return {
            "nombre": self.nombre_entry.text().strip(),
            "descripcion": self.descripcion_entry.toPlainText().strip(),
            "tiempo": float(self.tiempo_entry.text().replace(",", ".")) if self.tiempo_entry.text() else 0.0,
            "tipo_trabajador": self.tipo_trabajador_combo.currentIndex() + 1
        }


