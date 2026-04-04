# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`calculate_times_widget`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""
from __future__ import annotations

from .base import *
from .timeline_widget import TimelineVisualizationWidget, TaskAnalysisPanel
from typing import Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from controllers.simulation.controller import SimulationController
    from controllers.ui_signals_controller import UISignalsController
    from core.dtos import LoteDTO, CalculationProductDTO, CalculationStepDTO


class CalculateTimesWidget(QWidget):
    """Widget para la pantalla de cálculo de tiempos de fabricación."""
    fabricacion_search_changed = pyqtSignal(str)
    product_search_changed = pyqtSignal(str)
    export_log_signal = pyqtSignal()
    clear_simulation_signal = pyqtSignal()
    go_home_signal = pyqtSignal()

    def __init__(self, controller: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        from core.di_container import DIContainer
        from controllers.simulation.controller import SimulationController
        from controllers.ui_signals_controller import UISignalsController
        self.simulation_controller: "SimulationController" = DIContainer.get_instance().resolve(SimulationController)
        self.ui_signals_controller: "UISignalsController" = DIContainer.get_instance().resolve(UISignalsController)
        self.planning_session: list[Any] = []
        self.last_pila_id: Any = None
        self.last_results: list[Any] = []
        self.last_audit: list[Any] = []

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        if not hasattr(self, '_ui_setup_complete'):
            try:
                self.setup_ui()
                self._ui_setup_complete = True
                self.logger.info("✅ UI de CalculateTimesWidget inicializada correctamente")
                if hasattr(self, '_pending_signal_connection') and self.ui_signals_controller:
                    if not hasattr(self, '_signals_connected'):
                        self.ui_signals_controller.connect_calculate_signals()
            except Exception as e:
                self.logger.error(f"Error crítico en setup_ui: {e}", exc_info=True)

    def set_controller(self, controller: Any) -> None:
        pass # Ignored, DI injected

    def setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        left_panel = QFrame(self); left_layout = QVBoxLayout(left_panel); left_panel.setMaximumWidth(450)

        lote_group = QGroupBox("1. Añadir Lote al Plan de Producción", self); lote_layout = QVBoxLayout(lote_group)
        self.lote_search_entry = QLineEdit(self); self.lote_search_entry.setPlaceholderText("Buscar plantilla de lote...")
        self.lote_search_results = QListWidget(self)
        self.add_lote_button = QPushButton("Añadir Lote Seleccionado a la Pila", self)
        lote_layout.addWidget(self.lote_search_entry); lote_layout.addWidget(self.lote_search_results); lote_layout.addWidget(self.add_lote_button)
        left_layout.addWidget(lote_group)

        content_group = QGroupBox("2. Pila de Producción Actual", self); content_layout = QVBoxLayout(content_group)
        self.pila_content_table = QTableWidget(self); self.pila_content_table.setColumnCount(4)
        self.pila_content_table.setHorizontalHeaderLabels(["Identificador", "Plantilla Base", "Unidades", "Fecha Límite"])
        header = self.pila_content_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch); header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.pila_content_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.remove_item_button = QPushButton("Quitar Seleccionado", self)
        content_layout.addWidget(self.pila_content_table); content_layout.addWidget(self.remove_item_button, alignment=Qt.AlignmentFlag.AlignRight)
        left_layout.addWidget(content_group, 1)

        actions_group = QGroupBox("3. Acciones de Planificación", self); actions_layout = QVBoxLayout(actions_group)
        self.define_flow_button = QPushButton("Definir Flujo de Producción", self)
        self.define_flow_button.setStyleSheet("background-color: #ffc107; color: black; padding: 10px; font-weight: bold;")
        self.define_flow_button.setEnabled(False); actions_layout.addWidget(self.define_flow_button)
        

        # Botones de ejecución manual y optimizador eliminados

        left_layout.addWidget(actions_group); left_layout.addStretch(); main_layout.addWidget(left_panel)

        right_panel = QFrame(self); right_layout = QVBoxLayout(right_panel)
        self.progress_bar = QProgressBar(self); self.progress_bar.setVisible(False); right_layout.addWidget(self.progress_bar)
        self.results_tabs = QTabWidget(self)
        gantt_widget = QWidget(self); gantt_layout = QVBoxLayout(gantt_widget)
        self.results_table = QTableWidget(self); self._setup_table()
        self.timeline_label = QLabel("<b>Cronograma Visual (Gantt)</b>", self)
        self.timeline_widget = TimelineVisualizationWidget(self); self.task_analysis_panel = TaskAnalysisPanel(self)
        top_splitter = QSplitter(Qt.Orientation.Vertical, self); top_splitter.addWidget(self.results_table); top_splitter.addWidget(self.timeline_label); top_splitter.addWidget(self.timeline_widget); top_splitter.setSizes([200, 20, 200])
        main_splitter = QSplitter(Qt.Orientation.Vertical, self); main_splitter.addWidget(top_splitter); main_splitter.addWidget(self.task_analysis_panel); main_splitter.setSizes([400, 200])
        gantt_layout.addWidget(main_splitter); self.results_tabs.addTab(gantt_widget, "Cronograma y Resultados")

        audit_widget = QWidget(self); audit_layout = QVBoxLayout(audit_widget)
        self.export_log_button = QPushButton("Exportar Log...", self)
        al = QHBoxLayout(); al.addStretch(); al.addWidget(self.export_log_button); audit_layout.addLayout(al)
        self.audit_log_display = QTextEdit(self); self.audit_log_display.setReadOnly(True); audit_layout.addWidget(self.audit_log_display)
        self.results_tabs.addTab(audit_widget, "Log de Auditoría")
        right_layout.addWidget(self.results_tabs)

        res_actions = QHBoxLayout()
        self.clear_button = QPushButton("Nuevo Plan", self); self.go_home_button = QPushButton("Volver a Inicio", self)
        self.save_pila_button = QPushButton("Guardar Pila", self); self.load_pila_button = QPushButton("Cargar Pila", self)
        self.manage_bitacora_button = QPushButton("Ver Bitácora", self); self.export_button = QPushButton("Exportar a Excel", self); self.export_pdf_button = QPushButton("Exportar Gráfico", self)
        res_actions.addWidget(self.clear_button); res_actions.addWidget(self.go_home_button); res_actions.addStretch()
        for b in [self.save_pila_button, self.load_pila_button, self.manage_bitacora_button, self.export_button, self.export_pdf_button]: res_actions.addWidget(b)
        for b in [self.save_pila_button, self.manage_bitacora_button, self.export_button, self.export_pdf_button, self.export_log_button, self.clear_button, self.go_home_button]: b.setEnabled(False)
        right_layout.addLayout(res_actions); main_layout.addWidget(right_panel, 1)

        if hasattr(self.timeline_widget, 'task_selected'): self.timeline_widget.task_selected.connect(self.task_analysis_panel.displayTask)

    def _setup_table(self) -> None:
        self.results_table.setColumnCount(8); self.results_table.setHorizontalHeaderLabels(["Tarea", "Departamento", "Inicio", "Fin", "Duración (min)", "Días Lab.", "Trabajador", "Máquina"])
        header = self.results_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch); header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def show_progress(self) -> None:
        self.progress_bar.setValue(0); self.progress_bar.setVisible(True)


    def hide_progress(self) -> None:
        self.progress_bar.setVisible(False)


    def update_progress(self, value: int) -> None: self.progress_bar.setValue(value)

    def set_progress_status(self, message: str, value: int | None = None) -> None:
        self.progress_bar.setFormat(message)
        if value is not None: self.progress_bar.setValue(value)

    def enable_result_actions(self) -> None:
        for b in [self.save_pila_button, self.export_button, self.export_pdf_button, self.export_log_button, self.clear_button, self.go_home_button]: b.setEnabled(True)

    def get_pila_for_calculation(self) -> dict[str, dict[str, Any]]:
        from core.dtos import CalculationProductDTO, CalculationStepDTO
        pila_data: dict[str, dict[str, Any]] = {"productos": {}, "fabricaciones": {}}
        for item in self.planning_session:
            if isinstance(item, CalculationProductDTO):
                # Es un preproceso o producto directo añadido a la pila
                if item.codigo not in pila_data["productos"]:
                    pila_data["productos"][item.codigo] = {"codigo": item.codigo, "descripcion": item.descripcion}
            elif isinstance(item, CalculationStepDTO):
                if item.pila_de_calculo_directa:
                    pd = item.pila_de_calculo_directa
                    pila_data["productos"].update(pd.get("productos", {})); pila_data["fabricaciones"].update(pd.get("fabricaciones", {}))
                elif item.lote_template_id:
                    lid = item.lote_template_id
                    try:
                        sc = self.simulation_controller
                        if not sc:
                            continue
                        det: Optional["LoteDTO"] = None
                        if getattr(sc, "db", None) and getattr(sc.db, "lote_repo", None) is not None:
                            det = sc.db.lote_repo.get_lote_details(lid)
                        elif getattr(sc, "model", None) is not None:
                            det = getattr(sc, "model").get_lote_details(lid)
                        if det:
                            if det.productos is not None:
                                for p in det.productos:
                                    if p.codigo not in pila_data["productos"]: pila_data["productos"][p.codigo] = {"codigo": p.codigo, "descripcion": p.descripcion}
                            if det.fabricaciones is not None:
                                for f in det.fabricaciones:
                                    if str(f.id) not in pila_data["fabricaciones"]:
                                        fi = None
                                        app = getattr(sc, "app", None)
                                        pc = getattr(app, "product_controller", None) if app else None
                                        fs = getattr(pc, "fabricacion_service", None) if pc else None
                                        if fs is not None:
                                            fi = fs.get_fabricacion_by_id(f.id)
                                        elif getattr(sc, "model", None) is not None:
                                            fi = getattr(sc, "model").get_fabricacion_by_id(f.id)
                                        fd = fi.descripcion if fi else ''
                                        pila_data["fabricaciones"][str(f.id)] = {"id": f.id, "codigo": f.codigo, "descripcion": fd}
                    except Exception as e: self.logger.error(f"Error detalles lote {lid}: {e}")
        return pila_data

    def _display_audit_log(self, audit_log: list[Any]) -> None:
        self.audit_log_display.clear(); self.audit_log_display.setUpdatesEnabled(False)
        cursor = self.audit_log_display.textCursor()
        for i, decision in enumerate(audit_log):
            status_color = {"POSITIVE": "#2ecc71", "WARNING": "#f39c12", "NEUTRAL": "#bdc3c7"}.get(str(decision.status.value), "#ecf0f1")
            html = (f'<div style="border-left: 3px solid {status_color}; padding-left: 8px; margin-bottom: 10px;">'
                    f'<p style="margin: 0; font-size: 9pt;"><b>{decision.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</b> | <span style="color: {status_color};">{decision.icon} {decision.decision_type}</span></p>'
                    f'<p style="margin: 0; font-size: 11pt; font-weight: bold;">{decision.task_name}</p>'
                    f'<p style="margin: 0; font-size: 10pt;">{decision.user_friendly_reason}</p></div>')
            cursor.movePosition(cursor.MoveOperation.End); cursor.insertHtml(html)
            if i % 200 == 0: QApplication.processEvents()
        self.audit_log_display.setUpdatesEnabled(True)

    def _update_plan_display(self) -> None:
        from core.dtos import CalculationProductDTO, CalculationStepDTO
        self.pila_content_table.blockSignals(True); self.pila_content_table.setRowCount(0)
        for i, item in enumerate(self.planning_session):
            r = self.pila_content_table.rowCount(); self.pila_content_table.insertRow(r)
            
            # Extraer datos según tipo
            if isinstance(item, CalculationProductDTO):
                identificador = item.fabricacion_id or "N/A"
                lote_codigo = item.codigo
                unidades = item.units_for_this_instance
                deadline = item.deadline
            elif isinstance(item, CalculationStepDTO):
                identificador = item.identificador
                lote_codigo = item.lote_codigo
                unidades = item.unidades
                deadline = item.deadline
            else:
                identificador = "N/A"
                lote_codigo = "N/A"
                unidades = 0
                deadline = None

            ti = QTableWidgetItem(str(identificador)); ti.setData(Qt.ItemDataRole.UserRole, i)
            dls = deadline.strftime('%d/%m/%Y') if deadline else "N/A"
            self.pila_content_table.setItem(r, 0, ti); self.pila_content_table.setItem(r, 1, QTableWidgetItem(str(lote_codigo)))
            self.pila_content_table.setItem(r, 2, QTableWidgetItem(str(unidades))); self.pila_content_table.setItem(r, 3, QTableWidgetItem(dls))
        self.pila_content_table.blockSignals(False)

    def display_simulation_results(self, results: list[Any], audit_log: list[Any]) -> None:
        self.last_results = results; self.last_audit = audit_log
        self.results_table.setRowCount(len(results))
        for row, d in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(d['Tarea'])); self.results_table.setItem(row, 1, QTableWidgetItem(d['Departamento']))
            self.results_table.setItem(row, 2, QTableWidgetItem(d['Inicio'].strftime('%d/%m/%Y %H:%M'))); self.results_table.setItem(row, 3, QTableWidgetItem(d['Fin'].strftime('%d/%m/%Y %H:%M')))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{d['Duracion (min)']:.2f}")); self.results_table.setItem(row, 5, QTableWidgetItem(f"{d['Dias Laborables']:.2f}"))
            self.results_table.setItem(row, 6, QTableWidgetItem(", ".join(d['Trabajador Asignado']))); self.results_table.setItem(row, 7, QTableWidgetItem(d.get('nombre_maquina', 'N/A')))
        self._display_audit_log(audit_log); self.export_button.setEnabled(True)
        if len(results) > MAX_TASKS_TO_RENDER:
            QMessageBox.information(self, "Visualización Omitida", f"Demasiadas tareas ({len(results)}) para mostrar el gráfico."); self.timeline_label.setVisible(False); self.timeline_widget.setVisible(False); self.timeline_widget.clear()
        else:
            self.timeline_label.setVisible(True); self.timeline_widget.setVisible(True); self.timeline_widget.setData(results, audit_log)
        for b in [self.export_pdf_button, self.save_pila_button, self.export_log_button, self.clear_button, self.go_home_button]: b.setEnabled(bool(results))

    def add_step_to_pila(self, step_data: CalculationProductDTO | CalculationStepDTO) -> bool:
        """Añade un paso (tarea/preproceso) a la pila manualmente."""
        from core.dtos import CalculationStepDTO
        if not step_data:
            return False
        self.planning_session.append(step_data)
        self._update_plan_display()
        return True

    def clear_all(self) -> None:
        self.planning_session = []; self.last_pila_id = None; self.last_results = []; self.last_audit = []
        self.lote_search_entry.clear(); self.lote_search_results.clear(); self._update_plan_display()
        self.results_table.setRowCount(0); self.timeline_widget.setData([], []); self.audit_log_display.clear()
        self.task_analysis_panel.header_label.setText("Seleccione una tarea del gráfico"); self.task_analysis_panel.header_label.setStyleSheet("")
        while self.task_analysis_panel.log_vbox.count():
            c = self.task_analysis_panel.log_vbox.takeAt(0)
            if c is not None:
                w = c.widget()
                if w is not None:
                    w.deleteLater()
        for b in [self.save_pila_button, self.manage_bitacora_button, self.export_button, self.export_pdf_button, self.export_log_button, self.clear_button, self.go_home_button]: b.setEnabled(False)
        self.load_pila_button.setEnabled(True)

