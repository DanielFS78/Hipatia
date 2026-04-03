# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`worker_activity_panel`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QHBoxLayout, QPushButton
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

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz gráfica del panel."""
        layout = QVBoxLayout(self)
        
        # --- Historial de Tareas ---
        layout.addWidget(QLabel("<b>Tareas Asignadas al Trabajador</b>"))
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Fecha Asignación", "Código Fabricación", "Producto", "Cantidad", "Estado", "Acciones"
        ])
        header = self.history_table.horizontalHeader()
        if header:
            self.history_table.setColumnWidth(2, 250)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.history_table, 1)

        # --- Log de Actividad ---
        layout.addWidget(QLabel("<b>Log de Actividad del Trabajador (Fichajes)</b>"))
        self.activity_log_table = QTableWidget()
        self.activity_log_table.setColumnCount(7)
        self.activity_log_table.setHorizontalHeaderLabels([
            "Fecha Inicio", "Fecha Fin", "Duración (seg)", "Producto", "QR", "Incidencias", "Estado"
        ])
        log_header = self.activity_log_table.horizontalHeader()
        if log_header:
            self.activity_log_table.setColumnWidth(3, 180)
            self.activity_log_table.setColumnWidth(4, 150)
        self.activity_log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.activity_log_table, 1)

    def populate_history(self, fabrication_history: List["FabricacionAsignadaDTO"]) -> None:
        """Puebla la tabla de historial de tareas."""
        self.history_table.setRowCount(0)
        for task_data in fabrication_history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            fecha = task_data.fecha_asignacion
            fecha_str = fecha.strftime('%d/%m/%Y %H:%M') if isinstance(fecha, datetime) else str(fecha) if fecha else 'N/A'
            
            productos = getattr(task_data, 'productos', [])
            prod_text, qty_text = ('Sin producto', '-') if not productos else (
                f"{productos[0].producto_codigo} - {productos[0].descripcion}", 
                str(productos[0].cantidad)
            )

            estado = task_data.estado or 'activo'
            estado_label = QLabel(estado.capitalize())
            if estado == 'activo': estado_label.setStyleSheet("color: green; font-weight: bold;")
            elif estado == 'completado': estado_label.setStyleSheet("color: blue; font-weight: bold;")
            elif estado == 'cancelado': estado_label.setStyleSheet("color: red; font-weight: bold;")

            self.history_table.setItem(row, 0, QTableWidgetItem(fecha_str))
            self.history_table.setItem(row, 1, QTableWidgetItem(task_data.codigo or ''))
            self.history_table.setItem(row, 2, QTableWidgetItem(prod_text))
            self.history_table.setItem(row, 3, QTableWidgetItem(qty_text))
            self.history_table.setCellWidget(row, 4, estado_label)

            if estado == 'activo':
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(4, 2, 4, 2)
                cancel_btn = QPushButton("Cancelar")
                cancel_btn.clicked.connect(lambda checked, fid=task_data.id: self.cancel_task_signal.emit(fid))
                btn_layout.addWidget(cancel_btn)
                self.history_table.setCellWidget(row, 5, btn_widget)

    def populate_activity_log(self, activity_logs: List["TrabajoLogDTO"]) -> None:
        """Puebla la tabla de logs de actividad."""
        self.activity_log_table.setRowCount(0)
        self.activity_log_table.setSortingEnabled(False)
        for log in activity_logs:
            row = self.activity_log_table.rowCount()
            self.activity_log_table.insertRow(row)
            
            start = log.tiempo_inicio
            end = log.tiempo_fin
            self.activity_log_table.setItem(row, 0, QTableWidgetItem(start.strftime('%d/%m/%Y %H:%M:%S') if start else "En Proceso"))
            self.activity_log_table.setItem(row, 1, QTableWidgetItem(end.strftime('%d/%m/%Y %H:%M:%S') if end else "---"))
            self.activity_log_table.setItem(row, 2, QTableWidgetItem(str(log.duracion_segundos or '---')))
            self.activity_log_table.setItem(row, 3, QTableWidgetItem(log.producto_descripcion or 'N/A'))
            self.activity_log_table.setItem(row, 4, QTableWidgetItem(log.qr_code or 'N/A'))
            
            # --- INCIDENCIAS ---
            incidencias = log.incidencias or []
            if incidencias:
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(4, 2, 4, 2)
                view_btn = QPushButton(f"Ver ({len(incidencias)}) ⚠️")
                view_btn.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; border-radius: 4px;")
                # incidencias es List[IncidenciaLogDTO], emit_signal acepta lista.
                view_btn.clicked.connect(lambda checked, incs=incidencias: self.show_incidences_signal.emit(incs))
                btn_layout.addWidget(view_btn)
                self.activity_log_table.setCellWidget(row, 5, btn_widget)
            else:
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.activity_log_table.setItem(row, 5, item)

            estado_item = QTableWidgetItem(log.estado or 'desconocido')
            if log.estado == 'completado': estado_item.setForeground(QColor("blue"))
            elif log.estado == 'en_proceso': estado_item.setForeground(QColor("orange"))
            self.activity_log_table.setItem(row, 6, estado_item)
            
        self.activity_log_table.setSortingEnabled(True)

    def clear(self) -> None:
        """Limpia las tablas."""
        self.history_table.setRowCount(0)
        self.activity_log_table.setRowCount(0)
