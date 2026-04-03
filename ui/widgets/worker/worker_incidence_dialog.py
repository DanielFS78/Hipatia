# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`worker_incidence_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from datetime import datetime, date
from typing import Any, List

class WorkerIncidenceDialog(QDialog):
    """Diálogo para mostrar el detalle de las incidencias de un trabajador."""
    
    def __init__(self, incidences: List[Any], parent: Any = None) -> None:
        super().__init__(parent)
        self.incidences = incidences
        self._setup_ui()
        self._populate_incidences()

    def _setup_ui(self) -> None:
        """Configura la interfaz gráfica del diálogo."""
        self.setWindowTitle("Detalle de Incidencias")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(f"Historial de Incidencias ({len(self.incidences)})")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

    def _populate_incidences(self) -> None:
        """Puebla la lista con los datos de las incidencias."""
        for inc in self.incidences:
            fecha = inc.fecha_reporte
            if isinstance(fecha, (datetime, date)):
                fecha_str = fecha.strftime('%d/%m/%Y %H:%M')
            else:
                fecha_str = str(fecha)
                
            tipo = inc.tipo_incidencia or 'N/A'
            desc = inc.descripcion or 'Sin descripción'
            estado = inc.estado or 'Abierta'
            adjuntos = inc.adjuntos or []
            
            item_text = f"[{fecha_str}] - TIPO: {tipo} ({estado})\n{desc}"
            if adjuntos:
                item_text += f"\n📎 {len(adjuntos)} Adjunto(s)"
                
            item = QListWidgetItem(item_text)
            
            # Estilo condicional según estado
            if estado.lower() not in ('completada', 'resuelta'):
                item.setForeground(QColor("#c0392b")) # Rojo para pendientes
            
            self.list_widget.addItem(item)
