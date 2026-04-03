"""Render helpers seguros para `ReportsChartsWidget`."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QLabel


def clear_stats_layout(widget: Any) -> None:
    """Limpia el layout de estadísticas del contenedor."""
    while widget.stats_layout.count():
        child = widget.stats_layout.takeAt(0)
        if child and child.widget():
            child.widget().deleteLater()


def update_stats_cards(widget: Any, promedio_data: Any, stat_card_cls: type) -> None:
    clear_stats_layout(widget)
    if not promedio_data:
        placeholder = QLabel("No hay datos de producción")
        placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
        widget.stats_layout.addWidget(placeholder)
        return

    tiempo_min = promedio_data.promedio_segundos / 60
    widget.stats_layout.addWidget(
        stat_card_cls(
            "Tiempo Promedio",
            f"{tiempo_min:.1f} min",
            f"σ = {promedio_data.desviacion_estandar/60:.1f} min",
            "#2563eb",
        )
    )
    widget.stats_layout.addWidget(
        stat_card_cls("Total Unidades", str(promedio_data.total_unidades), "producidas", "#16a34a")
    )
    widget.stats_layout.addWidget(
        stat_card_cls("Mejor Tiempo", f"{promedio_data.minimo_segundos/60:.1f} min", "por unidad", "#0891b2")
    )
    widget.stats_layout.addWidget(
        stat_card_cls("Peor Tiempo", f"{promedio_data.maximo_segundos/60:.1f} min", "por unidad", "#dc2626")
    )
    widget.stats_layout.addStretch()

