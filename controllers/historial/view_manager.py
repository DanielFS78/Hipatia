# -*- coding: utf-8 -*-
"""
Nombre del Módulo: view_manager.py (Historial)
Descripción: Gestiona la lógica de presentación de los datos históricos, incluyendo 
             el filtrado de listas, resaltado de calendarios y generación de gráficos QtCharts.
"""
from __future__ import annotations
import logging
from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import Any, List, Dict
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCharts import QChart, QLineSeries, QDateTimeAxis, QValueAxis

class HistorialViewManager:
    """
    Gestor de vista para el historial.

    Sincroniza los datos crudos con la interfaz de usuario, manejando la 
    población de listas, el resaltado dinámico de fechas en el calendario 
    y la actualización del gráfico de actividad.
    """

    def __init__(self, db: Any, pila_service: Any, view: Any, controller_ref: Any = None):
        self.db = db
        self.pila_service = pila_service
        self.view = view
        self.controller_ref = controller_ref
        self.logger = logging.getLogger(__name__)
        self.historial_data: List[Any] = []

    def update_view(self) -> None:
        """Actualiza la vista completa de Historial."""
        self.logger.info("Actualizando la vista de Historial.")
        page = self.view.pages.get("historial")
        if not page or not hasattr(page, 'filter_combo'):
            return

        page.clear_view()
        mode = page.current_mode
        
        if mode == "iteraciones":
            self.historial_data = self.db.iteration_repo.get_all_iterations_with_dates()
            responsables = ["Todos los Responsables"] + sorted(list(
                set(row.nombre_responsable for row in self.historial_data if row.nombre_responsable)))
            page.filter_combo.blockSignals(True)
            page.filter_combo.clear()
            page.filter_combo.addItems(responsables)
            page.filter_combo.blockSignals(False)
        else:
            self.historial_data = self.pila_service.get_all_pilas_with_dates()
            page.filter_combo.blockSignals(True)
            page.filter_combo.clear()
            page.filter_combo.addItem("Todas las Pilas")
            page.filter_combo.blockSignals(False)
            
        self.populate_list()
        self.update_calendar_highlights()
        self.update_activity_chart()

    def populate_list(self) -> None:
        """Rellena la lista de resultados según el modo y filtros."""
        page = self.view.pages.get("historial")
        if not page or not hasattr(page, 'search_entry'):
            return
            
        search_text = page.search_entry.text().lower()
        filter_text = page.filter_combo.currentText()
        mode = page.current_mode
        page.results_list.clear()
        
        for item_data in self.historial_data:
            list_item = None
            if mode == "iteraciones":
                prod_code = item_data.producto_codigo
                prod_desc = item_data.producto_descripcion if hasattr(item_data, 'producto_descripcion') else ""
                responsable = item_data.nombre_responsable
                creation_date = item_data.fecha_creacion
                
                search_content = f"{prod_code} {prod_desc}".lower()
                if (filter_text != "Todos los Responsables" and responsable != filter_text):
                    continue
                if (search_text and search_text not in search_content):
                    continue
                
                date_str = creation_date.strftime('%d/%m/%Y') if isinstance(creation_date, (datetime, date)) else str(creation_date)
                
                display_text = f"📜 {prod_code} - {prod_desc}\n    └ {date_str} por {responsable}"
                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.ItemDataRole.UserRole, item_data)
                
            elif mode == "fabricaciones":
                fab_name = item_data.nombre
                fab_desc = item_data.descripcion
                search_content = f"{fab_name} {fab_desc}".lower()
                if search_text and search_text not in search_content:
                    continue
                    
                start_date = item_data.start_date
                end_date = item_data.end_date
                start_str = start_date.strftime('%d/%m/%Y') if isinstance(start_date, date) else 'N/A'
                end_str = end_date.strftime('%d/%m/%Y') if isinstance(end_date, date) else 'N/A'
                
                display_text = f"📋 {fab_name}\n    └── {start_str} a {end_str}"
                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.ItemDataRole.UserRole, item_data)
            
            if list_item:
                page.results_list.addItem(list_item)

    def update_calendar_highlights(self) -> None:
        """Actualiza los resaltados del calendario según los ítems listados."""
        page = self.view.pages.get("historial")
        if not page or not hasattr(page, 'results_list'):
            return
            
        page.clear_calendar_format()
        mode = page.current_mode
        dates_to_highlight = set()
        
        for i in range(page.results_list.count()):
            item = page.results_list.item(i)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            if mode == "iteraciones":
                creation_date = item_data.fecha_creacion
                if isinstance(creation_date, (datetime, date)):
                    dates_to_highlight.add(QDate(creation_date.year, creation_date.month, creation_date.day))
            else:
                start_date = item_data.start_date
                end_date = item_data.end_date
                if start_date and end_date:
                    current_date = start_date
                    while current_date <= end_date:
                        dates_to_highlight.add(QDate(current_date.year, current_date.month, current_date.day))
                        current_date += timedelta(days=1)
        
        color = "#3498db" if mode == 'iteraciones' else "#2ecc71"
        page.highlight_calendar_dates(list(dates_to_highlight), color)

    def update_activity_chart(self) -> None:
        """Actualiza el gráfico de actividad (últimos 12 meses)."""
        page = self.view.pages.get("historial")
        if not page or not hasattr(page, 'activity_chart_view'):
            return
            
        counts: Dict[float, int] = defaultdict(int)
        now = datetime.now()
        mode = page.current_mode
        
        for item_data in self.historial_data:
            item_date = None
            if mode == "iteraciones":
                item_date_obj = item_data.fecha_creacion
                if isinstance(item_date_obj, datetime):
                    item_date = item_date_obj
                elif isinstance(item_date_obj, str):
                    try:
                        item_date = datetime.strptime(item_date_obj, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        continue
            else:
                start_date_obj = item_data.start_date
                if isinstance(start_date_obj, date):
                    item_date = datetime.combine(start_date_obj, datetime.min.time())
            
            if item_date and (now - item_date).days <= 365:
                timestamp = datetime(item_date.year, item_date.month, 1).timestamp() * 1000
                counts[timestamp] += 1
                
        series = QLineSeries()
        max_val = 0
        if counts:
            max_val = max(counts.values())
            
        for ts, count in sorted(counts.items()):
            series.append(ts, count)
            
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"Actividad de {mode.capitalize()} (Últimos 12 Meses)")
        legend = chart.legend()
        if legend:
            legend.hide()
        
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MMM yyyy")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%i")
        axis_y.setRange(0, max_val + 1)
        axis_y.setTickCount(max_val + 2 if max_val < 10 else 10)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        page.activity_chart_view.setChart(chart)
