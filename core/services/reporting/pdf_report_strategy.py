"""
Lógica o utilidades del núcleo (`pdf_report_strategy`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Any, Dict, List, Set, TYPE_CHECKING, DefaultDict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, Table, TableStyle, PageBreak

from core.services.time_calculator import CalculadorDeTiempos
from .pdf_report_sections import (
    add_audit_log_table_section,
    add_diagnostics_section,
    add_sequential_group_diagnostics_section,
)
from .base import IReporteEstrategia

if TYPE_CHECKING:
    from core.models.app_model import AppModel
    from core.simulation.engine.schedule_config import ScheduleConfig

class ReporteHistorialFabricacion(IReporteEstrategia):
    """
    Estrategia para generar un informe PDF de optimización, incluyendo
    resumen ejecutivo, diagnóstico de cuellos de botella y log detallado.
    """

    def __init__(self, worker_service: Any, schedule_config: Optional[ScheduleConfig] = None) -> None:
        self.worker_service = worker_service
        self.schedule_config = schedule_config
        self.time_calculator = CalculadorDeTiempos(self.schedule_config) if schedule_config else None
        self.logger = logging.getLogger(__name__)

    def generar_reporte(self, datos_informe: Dict[str, Any], output_path: str) -> bool:
        self.logger.info(f"Generando informe PDF evolucionado en: {output_path}")

        try:
            results = datos_informe.get("planificacion", [])
            audit = datos_informe.get("audit", [])
            production_flow = datos_informe.get("production_flow", [])

            if not results:
                self.logger.error("No hay datos de planificación para el PDF.")
                return False

            doc = SimpleDocTemplate(output_path, pagesize=landscape(A4), topMargin=inch / 2, bottomMargin=inch / 2)
            styles = getSampleStyleSheet()
            story: List[Any] = []

            # 1. Portada y Resumen Ejecutivo
            self._add_executive_summary(story, datos_informe.get("meta_data", {}),
                                        datos_informe.get("flexible_workers_needed", 0), results, styles)
            story.append(PageBreak())

            # 2. Cronograma Visual (Gantt)
            story.append(Paragraph("Cronograma Visual de Planificación (Gantt)", styles['h2']))
            self._add_gantt_chart_to_pdf(story, results, styles)
            story.append(Spacer(1, 0.25 * inch))

            # 3. Análisis de Recursos y Diagnóstico
            story.append(Paragraph("Análisis y Diagnóstico de Recursos", styles['h2']))
            self._add_resource_analysis_to_pdf(story, results, self.worker_service, production_flow, styles)
            story.append(Spacer(1, 0.25 * inch))
            self._add_sequential_group_diagnostics(story, audit, styles)
            story.append(Spacer(1, 0.25 * inch))
            self._add_diagnostics(story, audit, styles)
            story.append(PageBreak())

            # 4. Log de Auditoría Detallado
            story.append(Paragraph("Log de Decisiones Detallado", styles['h2']))
            self._add_audit_log_table(story, audit, styles)

            doc.build(story)
            self.logger.info("Informe PDF evolucionado generado con éxito.")
            return True
        except Exception as e:
            self.logger.critical(f"Error al generar el informe PDF evolucionado: {e}", exc_info=True)
            return False

    def _add_executive_summary(
        self,
        story: List[Any],
        meta_data: Any,
        workers_needed: int,
        results: List[Dict[str, Any]],
        styles: Any,
    ) -> None:
        header_name = meta_data.nombre if hasattr(meta_data, 'nombre') else meta_data.get('nombre', 'N/A') if isinstance(meta_data, dict) else 'N/A'
        story.append(Paragraph(f"Informe de Planificación de Lote: {header_name}", styles['h1']))
        story.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("Resumen Ejecutivo de la Planificación", styles['h2']))
        summary_text = (
            f"Para la configuración y plazos definidos, el sistema ha determinado que se requiere un total de "
            f"<font size=12 color='blue'><b>{workers_needed} trabajador(es) flexible(s)</b></font> "
            f"adicional(es) al personal especialista existente para cumplir los objetivos."
        )
        story.append(Paragraph(summary_text, styles['BodyText']))
        story.append(Spacer(1, 0.3 * inch))
        start_time = min(r['Inicio'] for r in results)
        end_time = max(r['Fin'] for r in results)
        total_workdays = self.time_calculator.count_workdays(start_time, end_time) if self.time_calculator else 0.0
        data = [
            [Paragraph('<b>Fecha de Inicio Estimada:</b>', styles['Normal']), start_time.strftime('%d/%m/%Y %H:%M')],
            [Paragraph('<b>Fecha de Fin Estimada:</b>', styles['Normal']), end_time.strftime('%d/%m/%Y %H:%M')],
            [Paragraph('<b>Duración Total (Jornadas):</b>', styles['Normal']), f"{total_workdays:.2f}"],
            [Paragraph('<b>Número de Tareas Totales:</b>', styles['Normal']), str(len(results))],
        ]
        table = Table(data, colWidths=[2.5 * inch, 5 * inch])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(table)

    def _add_gantt_chart_to_pdf(
        self, story: List[Any], results: List[Dict[str, Any]], styles: Any
    ) -> None:
        if not results:
            return
        start_date = min(r['Inicio'] for r in results).date()
        end_date = max(r['Fin'] for r in results).date()
        total_days = (end_date - start_date).days + 1
        header = ['<b>Tarea</b>'] + [(start_date + timedelta(days=i)).strftime('%d/%m') for i in range(total_days)]
        table_data = [header]
        for task in results:
            task_start_date = task['Inicio'].date()
            task_end_date = task['Fin'].date()
            row = [Paragraph(task['Tarea'], styles['Normal'])]
            for i in range(total_days):
                current_cal_date = start_date + timedelta(days=i)
                if task_start_date <= current_cal_date <= task_end_date:
                    row.append("")
                else:
                    row.append("")
            table_data.append(row)
        col_widths = [2.5 * inch] + [0.2 * inch] * total_days
        if len(col_widths) > 50:
            col_widths = [2.5 * inch] + [0.15 * inch] * total_days
        table = Table(table_data, colWidths=col_widths)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ])
        for row_idx, task in enumerate(results, 1):
            start_offset = (task['Inicio'].date() - start_date).days
            end_offset = (task['Fin'].date() - start_date).days
            dept_color = {
                'Mecánica': colors.HexColor('#3498db'),
                'Electrónica': colors.HexColor('#2ecc71'),
                'Montaje': colors.HexColor('#f1c40f')
            }.get(str(task.get("Departamento") or ""), colors.grey)
            style.add('BACKGROUND', (start_offset + 1, row_idx), (end_offset + 1, row_idx), dept_color)
        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("<i>Nota: Las tareas con múltiples grupos de trabajadores simultáneos se detallan en el diagnóstico.</i>", styles['Normal']))

    def _add_resource_analysis_to_pdf(
        self,
        story: List[Any],
        results: List[Dict[str, Any]],
        worker_service: Any,
        production_flow: List[Dict[str, Any]],
        styles: Any,
    ) -> None:
        story.append(Paragraph("Análisis de Asignación de Habilidades", styles['h3']))
        all_workers = {w.nombre_completo: w.tipo_trabajador for w in worker_service.get_all_workers(True)}
        table_data = [['<b>Tarea</b>', '<b>Trabajador(es)</b>', '<b>Nivel Req.</b>', '<b>Nivel Asig.</b>', '<b>Diagnóstico</b>']]
        inefficiencies = 0
        for task_result in results:
            task_name = task_result['Tarea']
            assigned_workers = task_result['Trabajador Asignado']
            original_task_data = None
            for step in production_flow:
                if step.get('type') == 'sequential_group':
                    found = next((t_wrapper['task'] for t_wrapper in step.get('tasks', []) if t_wrapper.get('task', {}).get('name') == task_name), None)
                    if found:
                        original_task_data = found
                        break
                elif step.get('task', {}).get('name') == task_name:
                    original_task_data = step['task']
                    break
            if not original_task_data: continue
            required_skill = original_task_data.get('required_skill_level', 1)
            for worker_name in assigned_workers:
                worker_skill = all_workers.get(worker_name, 0)
                diagnostico = "Óptimo"
                if worker_skill > required_skill + 1:
                    diagnostico = "Sobrecalificado"
                    inefficiencies += 1
                elif worker_skill < required_skill:
                    diagnostico = "Subcalificado"
                    inefficiencies += 1
                table_data.append([Paragraph(task_name, styles['BodyText']), worker_name, str(required_skill), str(worker_skill), diagnostico])
        if len(table_data) == 1:
            story.append(Paragraph("No hay datos de asignación para analizar.", styles['BodyText']))
            return
        table = Table(table_data, colWidths=[3 * inch, 2 * inch, 1 * inch, 1 * inch, 1.5 * inch])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        for i, row in enumerate(table_data):
            if row[-1] == "Sobrecalificado":
                style.add('BACKGROUND', (0, i), (-1, i), colors.lightgoldenrodyellow)
            elif row[-1] == "Subcalificado":
                style.add('BACKGROUND', (0, i), (-1, i), colors.lightpink)
        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(f"Se detectaron <b>{inefficiencies}</b> asignaciones potencialmente ineficientes.", styles['BodyText']))
        
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Detección de Trabajo Paralelo", styles['h3']))
        tareas_con_paralelo: DefaultDict[str, Set[Any]] = defaultdict(set)
        for res in results:
            inst_id = res.get('Instancia ID')
            if inst_id and inst_id != 'N/A':
                tareas_con_paralelo[res.get('Tarea', 'Desconocida')].add(inst_id)
        tareas_paralelas_info = {t: ids for t, ids in tareas_con_paralelo.items() if len(ids) > 1}
        if not tareas_paralelas_info:
            story.append(Paragraph("No se detectó trabajo paralelo significativo.", styles['BodyText']))
        else:
            story.append(Paragraph(f"Se detectaron <b>{len(tareas_paralelas_info)} tarea(s)</b> con trabajo paralelo:", styles['BodyText']))
            data_paralelo = [[Paragraph('<b>Tarea</b>', styles['Normal']), Paragraph('<b>Nº Instancias</b>', styles['Normal']), Paragraph('<b>IDs Abreviados</b>', styles['Normal'])]]
            for tarea, instances in sorted(tareas_paralelas_info.items()):
                data_paralelo.append([Paragraph(tarea, styles['BodyText']), str(len(instances)), Paragraph(", ".join(sorted([i[:8] for i in instances])), styles['BodyText'])])
            table_paralelo = Table(data_paralelo, colWidths=[3 * inch, 1.2 * inch, 3.3 * inch])
            table_paralelo.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
            story.append(table_paralelo)

    def _add_diagnostics(self, story: List[Any], audit: List[Any], styles: Any) -> None:
        add_diagnostics_section(story, audit, styles)

    def _add_sequential_group_diagnostics(
        self, story: List[Any], audit: List[Any], styles: Any
    ) -> None:
        add_sequential_group_diagnostics_section(story, audit, styles)

    def _add_audit_log_table(self, story: List[Any], audit: List[Any], styles: Any) -> None:
        add_audit_log_table_section(story, audit, styles)

class ReporteHistorialIteracion(IReporteEstrategia):
    def generar_reporte(self, datos_informe: Dict[str, Any], output_path: str) -> bool:
        return True
