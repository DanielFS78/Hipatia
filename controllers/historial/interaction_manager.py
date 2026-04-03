"""
Nombre del Módulo: interaction_manager.py (Historial)
Descripción: Gestiona la lógica de interacción del usuario en la sección de historial,
             como la selección de elementos y filtros por calendario.
"""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Any, List, Tuple, TYPE_CHECKING
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QListWidgetItem

if TYPE_CHECKING:
    from ui.main_window import MainView

class HistorialInteractionManager:
    """
    Gestor de interacción para el historial.

    Se encarga de reaccionar a los eventos de usuario, como la selección de 
    iteraciones o fabricaciones, actualizando los detalles y resaltando fechas.
    """

    def __init__(self, db: Any, pila_service: Any, view: MainView, controller_ref: Any = None):
        self.db = db
        self.pila_service = pila_service
        self.view = view
        self.controller_ref = controller_ref
        self.logger = logging.getLogger(__name__)

    def on_item_selected(self, item: QListWidgetItem) -> None:
        """Maneja la selección de un ítem en la lista de resultados."""
        page = self.view.pages.get("historial")
        if not page or not hasattr(page, 'details_stack'):
            return

        item_data = item.data(Qt.ItemDataRole.UserRole)
        mode = page.current_mode
        page.details_stack.setCurrentIndex(1)
        
        # Necesitamos llamar a update_calendar_highlights del ViewManager o del Controller
        if self.controller_ref and hasattr(self.controller_ref, 'update_calendar_highlights'):
            self.controller_ref.update_calendar_highlights()
        
        selected_dates = []
        
        if mode == "iteraciones":
            prod_code = item_data.producto_codigo
            page.details_title_label.setText(f"Producto: {prod_code}")
            
            creation_date = item_data.fecha_creacion
            if isinstance(creation_date, (datetime, date)):
                selected_dates.append(QDate(creation_date.year, creation_date.month, creation_date.day))
            
            full_history = self.db.iteration_repo.get_product_iterations(prod_code)
            
            details_text = "HISTORIAL DE CAMBIOS DEL PRODUCTO:\n\n"
            for it in full_history:
                fecha_obj = it.fecha_creacion
                if isinstance(fecha_obj, str):
                    try:
                        fecha_obj = datetime.strptime(fecha_obj, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
                
                fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M') if isinstance(fecha_obj, (datetime, date)) else str(fecha_obj)
                
                details_text += f"--- {fecha_str} por {it.nombre_responsable} ---\n"
                details_text += f"{it.descripcion}\n\n"
                
                if it.materiales:
                     details_text += "Materiales Afectados:\n"
                     for mat in it.materiales:
                         details_text += f"  - {mat.codigo}: {mat.descripcion}\n"
                     details_text += "\n"

            page.details_text.setText(details_text)
        else:
            name = item_data.nombre
            page.details_title_label.setText(f"Fabricación: {name}")
            
            start_date = item_data.start_date
            end_date = item_data.end_date
            item_id = item_data.id

            if start_date and end_date:
                current_date = start_date
                while current_date <= end_date:
                    selected_dates.append(QDate(current_date.year, current_date.month, current_date.day))
                    current_date += timedelta(days=1)
            
            bitacora_id, entradas_raw = self.pila_service.get_diario_bitacora(int(item_id) if item_id else 0)
            entradas: List[Tuple[Any, Any, Any, Any, Any]] = entradas_raw or []
            details_text = f"BITÁCORA DE FABRICACIÓN:\n\n"
            if entradas:
                for fecha, dia, plan, real, notas in entradas:
                    fecha_str = fecha.strftime('%d/%m/%Y') if isinstance(fecha, date) else fecha
                    details_text += f"--- Día {dia} ({fecha_str}) ---\n"
                    details_text += f"PLAN: {plan}\n"
                    details_text += f"REALIZADO: {real}\n"
                    if notas:
                        details_text += f"NOTAS: {notas}\n"
                    details_text += "\n"
            else:
                details_text += "Aún no hay entradas en la bitácora para esta fabricación."
            page.details_text.setText(details_text)
            
        page.highlight_calendar_dates(selected_dates, "#e74c3c")

    def on_calendar_clicked(self, q_date: QDate) -> None:
        """Filtra la lista por la fecha seleccionada en el calendario."""
        page = self.view.pages.get("historial")
        if not page or not hasattr(page, 'results_list'):
            return
        
        py_date = q_date.toPyDate()
        mode = page.current_mode
        
        for i in range(page.results_list.count()):
            item = page.results_list.item(i)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            is_visible = False
            
            if mode == "iteraciones":
                creation_date_val = item_data.fecha_creacion
                if creation_date_val:
                    try:
                        c_date = creation_date_val
                        if isinstance(c_date, str):
                            c_date = datetime.strptime(c_date, '%Y-%m-%d %H:%M:%S')
                            
                        if isinstance(c_date, datetime):
                            if c_date.date() == py_date:
                                is_visible = True
                        elif isinstance(c_date, date):
                            if c_date == py_date:
                                is_visible = True
                    except (ValueError, TypeError):
                        pass
            else:
                start_date = item_data.start_date
                end_date = item_data.end_date
                if start_date and end_date and start_date <= py_date <= end_date:
                    is_visible = True
            
            item.setHidden(not is_visible)
