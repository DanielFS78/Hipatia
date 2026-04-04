"""
Interfaz PyQt6 (`bitacora_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

import logging
from datetime import date, datetime, timedelta
from PyQt6.QtWidgets import (
    QDialog, QFrame, QVBoxLayout, QCalendarWidget, QLabel, 
    QTableWidget, QHeaderView, QTableWidgetItem, QFormLayout, 
    QTextEdit, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QTextCharFormat, QColor
from PyQt6.QtCore import Qt
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.services.time_calculator import CalculadorDeTiempos
    from controllers.app_controller import AppController
    from PyQt6.QtWidgets import QWidget

from core.di_container import DIContainer
from core.dtos import SimulationResultTaskDTO
from core.services.pila_service import PilaService

class BitacoraEntryDTO:
    """DTO de entrada del diario de bitácora (plan/realizado/notas)."""

    def __init__(self, plan: str, realizado: str, notas: str) -> None:
        self.plan = plan
        self.realizado = realizado
        self.notas = notas

class FabricacionBitacoraDialog(QDialog):
    """
    Diálogo para gestionar el diario de bitácora de una pila de fabricación
    con un calendario interactivo.
    """

    def __init__(self, pila_id: int, pila_nombre: str, simulation_results: List[SimulationResultTaskDTO],
                 controller: "AppController", time_calculator: "CalculadorDeTiempos", 
                 parent: Optional["QWidget"] = None) -> None:
        super().__init__(parent)
        self.time_calculator = time_calculator  # Guardamos la instancia del calculador
        self.setWindowTitle(f"Diario de Bitácora para Pila: {pila_nombre}")
        self.setMinimumSize(1200, 800)
        self.pila_id = pila_id
        self.simulation_results = simulation_results
        self.controller = controller
        self.logger = logging.getLogger("EvolucionTiemposApp")

        _c = DIContainer.get_instance()
        self._pila_service = _c.resolve(PilaService) if _c.is_registered(PilaService) else None
        if self._pila_service is None:
            mod = getattr(controller, "model", None)
            ps = getattr(mod, "pila_service", None) if mod is not None else None
            if ps is not None:
                self._pila_service = ps

        self.pila_start_date: date = self.simulation_results[0].Inicio.date() if self.simulation_results else date.today()
        self.selected_date: date = date.today()
        self.bitacora_entries: Dict[date, BitacoraEntryDTO] = {}

        # --- Layout Principal (Horizontal) ---
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- Panel Izquierdo (Calendario e Historial) ---
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self._on_calendar_date_selected)
        left_layout.addWidget(self.calendar)

        left_layout.addWidget(QLabel("<b>Historial de Entradas Guardadas</b>"))
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Fecha", "Plan", "Realizado"])
        header = self.history_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_layout.addWidget(self.history_table)

        # --- Panel Derecho (Detalle del Día y Acciones) ---
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        self.day_detail_label = QLabel("Detalles del Día")
        font = self.day_detail_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.day_detail_label.setFont(font)
        right_layout.addWidget(self.day_detail_label)

        form_layout = QFormLayout()
        self.plan_entry = QTextEdit()
        self.plan_entry.setReadOnly(True)
        self.real_entry = QTextEdit()
        self.real_entry.setPlaceholderText("Describe el trabajo que se ha realizado...")
        self.notes_entry = QTextEdit()
        self.notes_entry.setPlaceholderText("Añade notas, incidencias, etc...")
        form_layout.addRow("<b>Plan Previsto:</b>", self.plan_entry)
        form_layout.addRow("<b>Trabajo Realizado:</b>", self.real_entry)
        form_layout.addRow("<b>Notas:</b>", self.notes_entry)
        right_layout.addLayout(form_layout)

        self.save_entry_button = QPushButton("Guardar Entrada del Día")
        self.save_entry_button.clicked.connect(self._add_diario_evento)
        right_layout.addWidget(self.save_entry_button)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        self._load_and_process_data()


    def _load_and_process_data(self) -> None:
        """Carga los datos iniciales, formatea el calendario y selecciona el día actual."""

        # 1. Cargar entradas existentes desde la BD
        if self._pila_service is not None:
            _, entries = self._pila_service.get_diario_bitacora(self.pila_id)
        else:
            _, entries = self.controller.model.get_diario_bitacora(self.pila_id)
        self.bitacora_entries = {}
        for entry_data in entries:
            entry_date_source = entry_data[0]

            if isinstance(entry_date_source, str):
                entry_date = datetime.strptime(entry_date_source, '%Y-%m-%d').date()
            else:
                entry_date = entry_date_source
            
            self.bitacora_entries[entry_date] = BitacoraEntryDTO(
                plan=str(entry_data[2]),
                realizado=str(entry_data[3]),
                notas=str(entry_data[4]),
            )

        # 2. Resaltar días de trabajo en el calendario
        self._highlight_work_days()
        self._update_history_table()

        # 3. Seleccionar el primer día de trabajo pendiente
        first_pending_date = self.pila_start_date
        while first_pending_date in self.bitacora_entries:
            if first_pending_date > date.today() + timedelta(days=365):
                break
            first_pending_date = self.time_calculator.find_next_workday(first_pending_date)

        self.calendar.setSelectedDate(first_pending_date)
        self._on_calendar_date_selected()

    def _highlight_work_days(self) -> None:
        """Resalta en el calendario los días con trabajo planificado."""
        workday_format = QTextCharFormat()
        workday_format.setBackground(QColor("#E0F0FF"))

        completed_day_format = QTextCharFormat()
        completed_day_format.setBackground(QColor("#D5F5E3"))

        planned_dates = {task.Inicio.date() for task in self.simulation_results}

        for p_date in planned_dates:
            if p_date in self.bitacora_entries:
                self.calendar.setDateTextFormat(p_date, completed_day_format)
            else:
                self.calendar.setDateTextFormat(p_date, workday_format)

    def _on_calendar_date_selected(self) -> None:
        """Actualiza la vista de detalles cuando se selecciona una fecha."""
        self.selected_date = self.calendar.selectedDate().toPyDate()
        self.day_detail_label.setText(f"Detalles para el {self.selected_date.strftime('%A, %d de %B de %Y')}")

        planned_work = self._get_planned_work_for_day(self.selected_date)
        self.plan_entry.setPlainText(planned_work)

        if self.selected_date in self.bitacora_entries:
            entry = self.bitacora_entries[self.selected_date]
            self.real_entry.setPlainText(entry.realizado)
            self.notes_entry.setPlainText(entry.notas)
            self.save_entry_button.setText("Actualizar Entrada del Día")
            self.real_entry.setReadOnly(False)
            self.notes_entry.setReadOnly(False)
        else:
            self.real_entry.clear()
            self.notes_entry.clear()
            self.save_entry_button.setText("Guardar Entrada del Día")
            if self.selected_date <= date.today():
                self.real_entry.setReadOnly(False)
                self.notes_entry.setReadOnly(False)
                self.save_entry_button.setEnabled(True)
            else:
                self.real_entry.setReadOnly(True)
                self.notes_entry.setReadOnly(True)
                self.save_entry_button.setEnabled(False)

    def _update_history_table(self) -> None:
        """Rellena la tabla del historial con las entradas guardadas."""
        self.history_table.setRowCount(0)
        sorted_dates = sorted(self.bitacora_entries.keys())
        self.history_table.setRowCount(len(sorted_dates))
        for i, entry_date in enumerate(sorted_dates):
            entry = self.bitacora_entries[entry_date]
            self.history_table.setItem(i, 0, QTableWidgetItem(entry_date.strftime('%d/%m/%Y')))
            self.history_table.setItem(i, 1, QTableWidgetItem(entry.plan))
            self.history_table.setItem(i, 2, QTableWidgetItem(entry.realizado))

    def _get_planned_work_for_day(self, target_date: date) -> str:
        """Genera un resumen del trabajo planificado para una fecha específica."""
        if not self.simulation_results:
            return "No hay resultados de simulación."

        planned_tasks = []
        for task in self.simulation_results:
            t_inicio = task.Inicio
            t_fin = task.Fin
            t_nombre = task.Tarea

            if t_inicio.date() == target_date:
                start_time = t_inicio.strftime('%H:%M')
                end_time = t_fin.strftime('%H:%M')
                planned_tasks.append(f"- De {start_time} a {end_time}: {t_nombre}")

        if not planned_tasks:
            return "No hay trabajo planificado para esta fecha."

        return "\n".join(sorted(planned_tasks))

    def _add_diario_evento(self) -> None:
        """Guarda o actualiza la entrada para la fecha seleccionada."""
        plan = self.plan_entry.toPlainText().strip()
        realizado = self.real_entry.toPlainText().strip()
        notas = self.notes_entry.toPlainText().strip()

        if not realizado:
            self.controller.view.show_message("Campo Requerido",
                                                  "El campo 'Trabajo Realizado' no puede estar vacío.", "warning")
            return

        day_number = (self.selected_date - self.pila_start_date).days + 1

        # Pasamos el objeto de fecha directamente, sin convertirlo a texto
        if self._pila_service is not None:
            success = self._pila_service.add_diario_evento(
                self.pila_id, self.selected_date, day_number, plan, realizado, notas
            )
        else:
            success = self.controller.model.add_diario_evento(
                self.pila_id, self.selected_date, day_number, plan, realizado, notas
            )

        if success:
            self.controller.view.show_message("Éxito", "La entrada del día se ha guardado correctamente.", "info")
            self._load_and_process_data()
        else:
            self.controller.view.show_message("Error", "No se pudo guardar la entrada en la base de datos.",
                                                  "critical")
