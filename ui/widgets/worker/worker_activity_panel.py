# -*- coding: utf-8 -*-
"""
Nombre del Módulo: worker_activity_panel

Descripción: Tabla de tareas asignadas, registro de trabajo e incidencias del trabajador seleccionado.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from datetime import datetime
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.tracking_dtos import FabricacionAsignadaDTO, TrabajoLogDTO, IncidenciaLogDTO


class WorkerActivityPanel(QWidget):
    """Panel que muestra el historial de tareas y logs de actividad de un trabajador."""

    cancel_task_signal = pyqtSignal(int)
    show_incidences_signal = pyqtSignal(list)

    # Índices columnas historial de tareas
    _H_COL_FECHA = 0
    _H_COL_CODIGO = 1
    _H_COL_PRODUCTO = 2
    _H_COL_CANT = 3
    _H_COL_ESTADO = 4
    _H_COL_ACCIONES = 5

    # Índices columnas log de actividad
    _L_COL_INI = 0
    _L_COL_FIN = 1
    _L_COL_DUR = 2
    _L_COL_PROD = 3
    _L_COL_QR = 4
    _L_COL_INC = 5
    _L_COL_EST = 6

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz gráfica del panel."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Ancho mínimo razonable para que las columnas no queden aplastadas dentro del QScrollArea
        self.setMinimumWidth(640)

        # --- Historial de Tareas ---
        layout.addWidget(QLabel("<b>Tareas asignadas al trabajador</b>"))
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            [
                "Fecha asignación",
                "Código fabricación",
                "Producto",
                "Cant.",
                "Estado",
                "Acciones",
            ]
        )
        self._configure_history_table_header()
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setWordWrap(True)
        _h_vh = self.history_table.verticalHeader()
        assert _h_vh is not None
        _h_vh.setVisible(False)
        _h_vh.setDefaultSectionSize(40)
        self.history_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.history_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.history_table, 1)

        # --- Log de Actividad ---
        layout.addWidget(QLabel("<b>Log de actividad (fichajes)</b>"))
        self.activity_log_table = QTableWidget()
        self.activity_log_table.setColumnCount(7)
        self.activity_log_table.setHorizontalHeaderLabels(
            [
                "Inicio",
                "Fin",
                "Duración (s)",
                "Producto",
                "QR",
                "Incidencias",
                "Estado",
            ]
        )
        self._configure_activity_log_header()
        self.activity_log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activity_log_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.activity_log_table.setAlternatingRowColors(True)
        self.activity_log_table.setWordWrap(True)
        _l_vh = self.activity_log_table.verticalHeader()
        assert _l_vh is not None
        _l_vh.setVisible(False)
        _l_vh.setDefaultSectionSize(40)
        self.activity_log_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.activity_log_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.activity_log_table, 1)

    def _configure_history_table_header(self) -> None:
        """Distribuye el espacio: fechas y códigos legibles; producto absorbe el resto."""
        header = self.history_table.horizontalHeader()
        assert header is not None
        header.setMinimumSectionSize(72)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # Fecha y código: contenido + mínimo cómodo
        header.setSectionResizeMode(self._H_COL_FECHA, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self._H_COL_CODIGO, QHeaderView.ResizeMode.ResizeToContents)
        # Producto: crece con la ventana
        header.setSectionResizeMode(self._H_COL_PRODUCTO, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(self._H_COL_CANT, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(self._H_COL_CANT, 64)
        header.setSectionResizeMode(self._H_COL_ESTADO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self._H_COL_ACCIONES, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(self._H_COL_ACCIONES, 118)

    def _configure_activity_log_header(self) -> None:
        """Misma idea: columnas de tiempo compactas; descripción amplia."""
        header = self.activity_log_table.horizontalHeader()
        assert header is not None
        header.setMinimumSectionSize(68)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for col in (self._L_COL_INI, self._L_COL_FIN):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self._L_COL_DUR, QHeaderView.ResizeMode.Fixed)
        self.activity_log_table.setColumnWidth(self._L_COL_DUR, 88)
        header.setSectionResizeMode(self._L_COL_PROD, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(self._L_COL_QR, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self._L_COL_INC, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self._L_COL_EST, QHeaderView.ResizeMode.ResizeToContents)

    @staticmethod
    def _set_item(row: int, col: int, table: QTableWidget, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setToolTip(text)
        table.setItem(row, col, item)

    def populate_history(self, fabrication_history: List["FabricacionAsignadaDTO"]) -> None:
        """Puebla la tabla de historial de tareas."""
        self.history_table.setRowCount(0)
        for task_data in fabrication_history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            fecha = task_data.fecha_asignacion
            fecha_str = (
                fecha.strftime("%d/%m/%Y %H:%M")
                if isinstance(fecha, datetime)
                else str(fecha)
                if fecha
                else "N/A"
            )

            productos = getattr(task_data, "productos", [])
            prod_text, qty_text = (
                ("Sin producto", "-")
                if not productos
                else (
                    f"{productos[0].producto_codigo} — {productos[0].descripcion}",
                    str(productos[0].cantidad),
                )
            )

            estado = task_data.estado or "activo"
            estado_label = QLabel(estado.capitalize())
            estado_label.setMargin(4)
            if estado == "activo":
                estado_label.setStyleSheet("color: green; font-weight: bold;")
            elif estado == "completado":
                estado_label.setStyleSheet("color: blue; font-weight: bold;")
            elif estado == "cancelado":
                estado_label.setStyleSheet("color: red; font-weight: bold;")

            self._set_item(row, self._H_COL_FECHA, self.history_table, fecha_str)
            codigo = task_data.codigo or ""
            self._set_item(row, self._H_COL_CODIGO, self.history_table, codigo)
            self._set_item(row, self._H_COL_PRODUCTO, self.history_table, prod_text)
            self._set_item(row, self._H_COL_CANT, self.history_table, qty_text)
            self.history_table.setCellWidget(row, self._H_COL_ESTADO, estado_label)

            if estado == "activo":
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(6, 4, 6, 4)
                btn_layout.setSpacing(4)
                cancel_btn = QPushButton("Cancelar")
                cancel_btn.setMinimumWidth(88)
                cancel_btn.clicked.connect(
                    lambda checked, fid=task_data.id: self.cancel_task_signal.emit(fid)
                )
                btn_layout.addWidget(cancel_btn)
                btn_layout.addStretch(1)
                self.history_table.setCellWidget(row, self._H_COL_ACCIONES, btn_widget)
            else:
                self._set_item(row, self._H_COL_ACCIONES, self.history_table, "—")

        self.history_table.resizeRowsToContents()

    def populate_activity_log(self, activity_logs: List["TrabajoLogDTO"]) -> None:
        """Puebla la tabla de logs de actividad."""
        self.activity_log_table.setRowCount(0)
        self.activity_log_table.setSortingEnabled(False)
        for log in activity_logs:
            row = self.activity_log_table.rowCount()
            self.activity_log_table.insertRow(row)

            start = log.tiempo_inicio
            end = log.tiempo_fin
            t0 = (
                start.strftime("%d/%m/%Y %H:%M:%S")
                if start
                else "En proceso"
            )
            t1 = end.strftime("%d/%m/%Y %H:%M:%S") if end else "—"
            self._set_item(row, self._L_COL_INI, self.activity_log_table, t0)
            self._set_item(row, self._L_COL_FIN, self.activity_log_table, t1)
            self._set_item(
                row, self._L_COL_DUR, self.activity_log_table, str(log.duracion_segundos or "—")
            )
            desc = log.producto_descripcion or "N/A"
            self._set_item(row, self._L_COL_PROD, self.activity_log_table, desc)
            qr = log.qr_code or "—"
            self._set_item(row, self._L_COL_QR, self.activity_log_table, qr)

            incidencias = log.incidencias or []
            if incidencias:
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(6, 4, 6, 4)
                view_btn = QPushButton(f"Ver ({len(incidencias)})")
                view_btn.setToolTip("Ver detalle de incidencias")
                view_btn.setMinimumWidth(96)
                view_btn.setStyleSheet(
                    "background-color: #f39c12; color: white; font-weight: bold; border-radius: 4px;"
                )
                view_btn.clicked.connect(
                    lambda checked, incs=incidencias: self.show_incidences_signal.emit(incs)
                )
                btn_layout.addWidget(view_btn)
                btn_layout.addStretch(1)
                self.activity_log_table.setCellWidget(row, self._L_COL_INC, btn_widget)
            else:
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.activity_log_table.setItem(row, self._L_COL_INC, item)

            estado_item = QTableWidgetItem(log.estado or "desconocido")
            estado_item.setToolTip(log.estado or "")
            if log.estado == "completado":
                estado_item.setForeground(QColor("blue"))
            elif log.estado == "en_proceso":
                estado_item.setForeground(QColor("orange"))
            self.activity_log_table.setItem(row, self._L_COL_EST, estado_item)

        self.activity_log_table.resizeRowsToContents()
        self.activity_log_table.setSortingEnabled(True)

    def clear(self) -> None:
        """Limpia las tablas."""
        self.history_table.setRowCount(0)
        self.activity_log_table.setRowCount(0)
