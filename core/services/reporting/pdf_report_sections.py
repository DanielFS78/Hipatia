"""Secciones reutilizables para reportes PDF de planificación."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


def add_diagnostics_section(story, audit, styles) -> None:
    """Añade diagnósticos de recursos e inactividad al PDF."""
    resource_warnings = [d for d in audit if d.decision_type == "ESPERA POR RECURSO"]
    story.append(Paragraph("Cuellos de Botella de Recursos (Máquinas/Trabajadores)", styles["h3"]))

    if not resource_warnings:
        story.append(Paragraph("No se han detectado esperas significativas por recursos.", styles["BodyText"]))
    else:
        total_wait_time = sum(d.details.get("wait_minutes", 0) for d in resource_warnings)
        story.append(
            Paragraph(
                f"Tiempo total de espera por recursos: <b>{total_wait_time:.1f} minutos</b>.",
                styles["BodyText"],
            )
        )
        for decision in sorted(resource_warnings, key=lambda d: d.details.get("wait_minutes", 0), reverse=True)[:3]:
            details = decision.details
            texto = (
                f" • <b>{decision.task_name}:</b> Espera de <b>{details.get('wait_minutes', 0):.1f} min</b> "
                f"por <i>'{details.get('resource', 'N/A')}'</i>."
            )
            story.append(Paragraph(texto, styles["Bullet"]))

    story.append(Spacer(1, 0.2 * inch))
    idle_events = [d for d in audit if d.decision_type == "TIEMPO_INACTIVO"]
    story.append(Paragraph("Tiempos de Inactividad por Dependencias", styles["h3"]))

    if not idle_events:
        story.append(
            Paragraph(
                "No se han detectado parones en el flujo de trabajo por dependencias entre tareas.",
                styles["BodyText"],
            )
        )
        return

    total_idle_time = sum((d.end_date - d.start_date).total_seconds() / 60 for d in idle_events)
    story.append(
        Paragraph(
            f"El flujo de producción se detuvo por un total de <b>{total_idle_time:.1f} minutos</b> esperando que se completaran tareas previas.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    table_data = [["<b>Inicio de la Inactividad</b>", "<b>Fin de la Inactividad</b>", "<b>Duración (min)</b>"]]
    sorted_idle_events = sorted(idle_events, key=lambda d: (d.end_date - d.start_date), reverse=True)
    for event in sorted_idle_events[:5]:
        duration = (event.end_date - event.start_date).total_seconds() / 60
        table_data.append(
            [event.start_date.strftime("%d/%m %H:%M"), event.end_date.strftime("%d/%m %H:%M"), f"{duration:.1f}"]
        )

    table = Table(table_data, colWidths=[2.5 * inch, 2.5 * inch, 2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#BF2A2A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(table)


def add_sequential_group_diagnostics_section(story, audit, styles) -> None:
    """Añade diagnóstico de grupos secuenciales."""
    story.append(Paragraph("Análisis de Grupos de Trabajo Secuencial", styles["h3"]))
    group_events = [d for d in audit if "GRUPO_SECUENCIAL" in d.decision_type]
    if not group_events:
        story.append(Paragraph("No se utilizaron grupos de trabajo secuencial en esta planificación.", styles["BodyText"]))
        return

    group_summary = {}
    for decision in audit:
        if decision.decision_type == "GRUPO_SECUENCIAL_FIN":
            worker = decision.task_name.replace("Grupo (", "").replace(")", "")
            duration = decision.details.get("total_duration_min", 0)
            if worker not in group_summary:
                group_summary[worker] = {"count": 0, "total_time": 0}
            group_summary[worker]["count"] += 1
            group_summary[worker]["total_time"] += duration

    if not group_summary:
        story.append(Paragraph("Se definieron grupos, pero no pudieron ser planificados.", styles["BodyText"]))
        return

    total_time_in_groups = sum(data["total_time"] for data in group_summary.values())
    story.append(
        Paragraph(
            f"Tiempo total de trabajo en modo secuencial: <b>{total_time_in_groups:.1f} minutos</b>.",
            styles["BodyText"],
        )
    )
    table_data = [["<b>Trabajador Asignado</b>", "<b>Nº de Grupos</b>", "<b>Tiempo Total en Grupos (min)</b>"]]
    for worker, data in sorted(group_summary.items(), key=lambda item: item[1]["total_time"], reverse=True):
        table_data.append([worker, str(data["count"]), f"{data['total_time']:.1f}"])

    table = Table(table_data, colWidths=[2.5 * inch, 2 * inch, 3 * inch])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(Spacer(1, 0.1 * inch))
    story.append(table)


def add_audit_log_table_section(story, audit, styles) -> None:
    """Añade tabla detallada de auditoría."""
    data = [["Hora", "Elemento", "Evento y Detalle", "Estado"]]
    body_style = styles["BodyText"]
    body_style.fontSize = 8
    for d in sorted(audit, key=lambda x: x.timestamp):
        is_micro = d.decision_type == "MICRO_TAREA_PLANIFICADA"
        event_text = (
            f"&nbsp;&nbsp;&nbsp;↳ {d.icon} {d.user_friendly_reason}"
            if is_micro
            else f"{d.icon} {d.user_friendly_reason}"
        )
        data.append([d.timestamp.strftime("%d/%m %H:%M:%S"), Paragraph(d.task_name, body_style), Paragraph(event_text, body_style), d.status.value])
    table = Table(data, colWidths=[1.3 * inch, 1.7 * inch, 5.5 * inch, 0.8 * inch])
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]
    )
    for i, dec in enumerate(sorted(audit, key=lambda x: x.timestamp), 1):
        if "GRUPO_SECUENCIAL" in dec.decision_type:
            style.add("BACKGROUND", (0, i), (-1, i), colors.lightblue)
    table.setStyle(style)
    story.append(table)

