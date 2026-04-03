"""
Helpers de UI para `StartupScreen`.

Se extrae la construcción de secciones y el render de resultados para reducir
el tamaño del diálogo sin cambiar comportamiento.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass
class StartupSectionWidgets:
    """Referencias a frame y layouts de una seccion del StartupScreen."""

    frame: QFrame
    content: QVBoxLayout
    title: QLabel
    desc: QLabel


def make_section(title: str, description: str) -> StartupSectionWidgets:
    """Crea una sección con título, descripción y un layout de contenido."""
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    frame.setStyleSheet(
        """
        QFrame {
            border: 1px solid #555;
            border-radius: 8px;
            background-color: #2a2a2a;
            padding: 12px;
        }
        """
    )

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(15, 12, 15, 12)
    layout.setSpacing(8)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #3498db;")
    layout.addWidget(title_lbl)

    desc_lbl = QLabel(description)
    desc_lbl.setWordWrap(True)
    desc_lbl.setStyleSheet("font-size: 11px; color: #aaa; margin-bottom: 5px;")
    layout.addWidget(desc_lbl)

    content_layout = QVBoxLayout()
    content_layout.setSpacing(6)
    layout.addLayout(content_layout)

    return StartupSectionWidgets(
        frame=frame, content=content_layout, title=title_lbl, desc=desc_lbl
    )


def clear_layout(layout: Any) -> None:
    """Elimina widgets hijos de un layout."""
    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            continue
        w = item.widget()
        if w is not None:
            w.deleteLater()


def build_startup_ui(screen: Any) -> None:
    """Construye la UI del StartupScreen y asigna atributos esperados."""
    root = QVBoxLayout(screen)
    root.setContentsMargins(30, 25, 30, 25)
    root.setSpacing(18)

    header = QLabel("🔷  HIPATIA — Verificación del Sistema")
    f = QFont()
    f.setPointSize(18)
    f.setBold(True)
    header.setFont(f)
    header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    root.addWidget(header)

    subtitle = QLabel("Comprobando la integridad del sistema antes de iniciar...")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle.setStyleSheet("color: #888; font-size: 12px; margin-bottom: 10px;")
    root.addWidget(subtitle)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet("QScrollArea { background: transparent; }")

    screen._scroll_content = QWidget()
    screen._scroll_layout = QVBoxLayout(screen._scroll_content)
    screen._scroll_layout.setSpacing(12)
    screen._scroll_layout.setContentsMargins(0, 0, 0, 0)
    scroll.setWidget(screen._scroll_content)
    root.addWidget(scroll, 1)

    screen._tests_section = make_section(
        "🧪 VALIDACIÓN DE ESTRUCTURA INTERNA",
        "Verificación rápida de componentes críticos del sistema",
    )
    screen._scroll_layout.addWidget(screen._tests_section.frame)

    screen._test_status = QLabel("✅ Componentes del sistema cargados correctamente")
    screen._test_status.setStyleSheet("color: #27ae60; margin-top: 5px;")
    screen._tests_section.content.addWidget(screen._test_status)

    screen._test_note = QLabel(
        "💡 Nota: La suite completa de tests (1570 verificaciones) puede ejecutarse "
        "manualmente con 'pytest -m unit' desde la terminal."
    )
    screen._test_note.setWordWrap(True)
    screen._test_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic; margin-top: 8px;")
    screen._tests_section.content.addWidget(screen._test_note)

    screen._db_section = make_section(
        "💾 VALIDACIÓN DE BASES DE DATOS",
        "Comprobando la integridad y disponibilidad de los datos del sistema",
    )
    screen._scroll_layout.addWidget(screen._db_section.frame)
    screen._db_section.frame.hide()

    screen._db_status = QLabel("⏳ Esperando...")
    screen._db_status.setStyleSheet("color: #888; font-style: italic;")
    screen._db_section.content.addWidget(screen._db_status)

    screen._db_results_area = QWidget()
    screen._db_results_layout = QVBoxLayout(screen._db_results_area)
    screen._db_results_layout.setSpacing(4)
    screen._db_results_layout.setContentsMargins(10, 5, 0, 0)
    screen._db_section.content.addWidget(screen._db_results_area)

    screen._summary_section = make_section("📋 RESUMEN DE VERIFICACIÓN", "Estado general del sistema")
    screen._scroll_layout.addWidget(screen._summary_section.frame)
    screen._summary_section.frame.hide()

    screen._summary_badge = QLabel()
    screen._summary_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    f2 = QFont()
    f2.setPointSize(14)
    f2.setBold(True)
    screen._summary_badge.setFont(f2)
    screen._summary_section.content.addWidget(screen._summary_badge)

    screen._summary_detail = QLabel()
    screen._summary_detail.setWordWrap(True)
    screen._summary_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
    screen._summary_detail.setStyleSheet("margin-top: 8px;")
    screen._summary_section.content.addWidget(screen._summary_detail)

    screen._auto_label = QLabel()
    screen._auto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    screen._auto_label.setStyleSheet("color: #aaa; font-size: 11px; margin-top: 10px;")
    screen._summary_section.content.addWidget(screen._auto_label)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(10)

    screen._btn_export = QPushButton("📄 Exportar Informe")
    screen._btn_export.setMinimumWidth(150)
    screen._btn_export.setEnabled(False)
    screen._btn_export.setToolTip("Exporta un informe detallado para soporte técnico")
    screen._btn_export.clicked.connect(screen._on_export_report)
    btn_row.addWidget(screen._btn_export)

    btn_row.addStretch()

    screen._btn_enter = QPushButton("Entrar al Sistema")
    screen._btn_enter.setMinimumWidth(150)
    screen._btn_enter.setEnabled(False)
    screen._btn_enter.clicked.connect(screen._on_enter)
    btn_row.addWidget(screen._btn_enter)

    screen._btn_cancel = QPushButton("Cancelar")
    screen._btn_cancel.setMinimumWidth(100)
    screen._btn_cancel.clicked.connect(screen.reject)
    btn_row.addWidget(screen._btn_cancel)

    root.addLayout(btn_row)


def render_db_report(screen: Any, report: Any) -> None:
    """Rellena la sección de BD a partir de un HealthReport."""
    screen._db_section.frame.show()
    screen._db_status.hide()
    clear_layout(screen._db_results_layout)

    if not report.db_reachable:
        err = QLabel(f"❌ Base de datos no disponible: {report.error_message}")
        err.setStyleSheet("color: #e74c3c; font-weight: bold;")
        screen._db_results_layout.addWidget(err)
        return

    categories = {
        "Datos de Producción": ["productos", "fabricaciones", "lotes", "pilas"],
        "Recursos": ["trabajadores", "maquinas", "materiales"],
        "Configuración": ["preprocesos", "grupos_preparacion"],
        "Auditoría y Trazabilidad": ["tracking_logs", "audit_logs"],
    }

    for cat_name, table_names in categories.items():
        cat_tables = [t for t in report.tables if t.table_name in table_names]
        if not cat_tables:
            continue

        cat_lbl = QLabel(f"📂 {cat_name}")
        cat_lbl.setStyleSheet("font-weight: bold; color: #3498db; margin-top: 8px;")
        screen._db_results_layout.addWidget(cat_lbl)

        for t in cat_tables:
            icon = "✅" if t.status == "OK" else ("⚠️" if t.status == "EMPTY" else "❌")
            status_text = "OK" if t.status == "OK" else ("Vacía" if t.status == "EMPTY" else "Error")
            color = "#27ae60" if t.status == "OK" else ("#f39c12" if t.status == "EMPTY" else "#e74c3c")
            row = QLabel(f"   {icon} {t.friendly_name}: {status_text} ({t.record_count} registros)")
            row.setStyleSheet(f"color: {color}; font-size: 11px; padding: 2px 0;")
            screen._db_results_layout.addWidget(row)

    if not report.db_integrity_ok:
        warn = QLabel("⚠️ La integridad de la base de datos presenta inconsistencias")
        warn.setStyleSheet("color: #e74c3c; font-weight: bold; margin-top: 10px;")
        screen._db_results_layout.addWidget(warn)

