# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui_manager
Descripción: Montaje visual de la ventana del trabajador (cabecera, pie, pestañas Tareas y Log).

``WorkerMainWindowUIManager`` construye el layout sobre ``WorkerMainWindow``: lista de tareas,
detalle, botones de acción y la terminal de log enlazada a ``QtLogHandler`` como en la vista
del responsable.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.log_terminal_widget import LogTerminalWidget


class WorkerMainWindowUIManager:
    """
    Gestor de layout y widgets iniciales de :class:`WorkerMainWindow`.

    Responsable de cabecera, pie, ``stacked_widget`` y la pantalla ``dashboard``
    con pestañas Tareas / Log.
    """

    def __init__(self, window: Any) -> None:
        self._w = window

    def setup_main_window(self) -> None:
        """Configura la interfaz de usuario principal sobre la ventana."""
        w = self._w
        w.setWindowTitle(
            f"Hipatia - Trabajador: {getattr(w.current_user, 'nombre_completo', 'Usuario')}"
        )
        w.resize(1024, 768)

        central_widget = QWidget()
        w.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = self._create_header()
        main_layout.addWidget(header)

        w.stacked_widget = QStackedWidget()
        main_layout.addWidget(w.stacked_widget, 1)

        footer = self._create_footer()
        main_layout.addWidget(footer)

        self._create_initial_screens()

    def _create_header(self) -> QFrame:
        w = self._w
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-bottom: 3px solid #3498db;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title_label = QLabel("🏭 HIPATIA")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        user_info_layout = QVBoxLayout()
        user_name_label = QLabel(f"👤 {getattr(w.current_user, 'nombre_completo', 'Usuario')}")
        user_name_font = QFont()
        user_name_font.setPointSize(12)
        user_name_font.setBold(True)
        user_name_label.setFont(user_name_font)

        user_role_label = QLabel(f"Rol: {getattr(w.current_user, 'role', 'Trabajador')}")
        user_role_label.setStyleSheet("color: #bdc3c7; font-size: 10px;")

        user_info_layout.addWidget(user_name_label)
        user_info_layout.addWidget(user_role_label)
        header_layout.addLayout(user_info_layout)

        camera_config_btn = QPushButton("⚙️ Configurar Cámara")
        camera_config_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
        camera_config_btn.clicked.connect(w._on_camera_config_clicked)
        camera_config_btn.setToolTip("Configurar cámara QR si tienes problemas de detección")
        header_layout.addWidget(camera_config_btn)

        w.btn_auto_ajustar = QPushButton("📐 Auto Ajustar UI")
        w.btn_auto_ajustar.setStyleSheet("""
            QPushButton {
                background-color: #f39c12; color: white; border: none;
                padding: 10px 20px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        w.btn_auto_ajustar.clicked.connect(w._forzar_auto_ajuste)
        w.btn_auto_ajustar.setToolTip("Recalcula el tamaño de la interfaz gráfica en pantallas pequeñas")
        header_layout.addWidget(w.btn_auto_ajustar)

        logout_btn = QPushButton("🚪 Cerrar Sesión")
        logout_btn.clicked.connect(w._on_logout_clicked)
        header_layout.addWidget(logout_btn)

        return header

    def _create_footer(self) -> QFrame:
        w = self._w
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-top: 1px solid #7f8c8d;
            }
            QLabel {
                color: #bdc3c7;
                font-size: 10px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 5, 20, 5)

        status_label = QLabel("✅ Sistema listo")
        footer_layout.addWidget(status_label)
        footer_layout.addStretch()

        w.export_data_btn = QPushButton("📤 Exportar Datos")
        footer_layout.addWidget(w.export_data_btn)

        version_label = QLabel("Versión 1.5.0 - Interfaz Trabajador")
        footer_layout.addWidget(version_label, 0, Qt.AlignmentFlag.AlignRight)

        return footer

    def _create_initial_screens(self) -> None:
        """Registra la pantalla ``dashboard`` (pestañas Tareas y Log) en el stack."""
        w = self._w
        dashboard_widget = self._create_dashboard_screen()
        w.add_screen("dashboard", dashboard_widget)
        w.switch_screen(0)

    def _create_dashboard_screen(self) -> QWidget:
        """
        Pantalla principal: ``QTabWidget`` con pestaña Tareas y pestaña Log.

        Asigna ``w.log_terminal`` al :class:`~ui.widgets.log_terminal_widget.LogTerminalWidget`
        de la segunda pestaña (para ``connect_log_handler`` en ``app.py``).
        """
        w = self._w
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        tabs = QTabWidget()
        tasks_tab = self._create_tasks_tab_content()
        tabs.addTab(tasks_tab, "Tareas")

        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(12, 12, 12, 12)
        w.log_terminal = LogTerminalWidget(log_tab)
        log_layout.addWidget(w.log_terminal, 1)
        tabs.addTab(log_tab, "Log")

        main_layout.addWidget(tabs)
        return widget

    def _create_tasks_tab_content(self) -> QWidget:
        """Contenido del panel de tareas (splitter lista + detalles)."""
        w = self._w
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(15, 15, 15, 15)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        w.tasks_group = QGroupBox("Mis Tareas Asignadas")
        tasks_layout.addWidget(w.tasks_group)

        tasks_list_layout = QVBoxLayout()
        w.tasks_list = QListWidget()
        w.tasks_list.setStyleSheet("font-size: 14px;")
        w.tasks_list.itemClicked.connect(w._on_task_selected)
        tasks_list_layout.addWidget(w.tasks_list)
        w.tasks_group.setLayout(tasks_list_layout)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        w.details_group = QGroupBox("Detalles y Acciones de Tarea")
        details_layout.addWidget(w.details_group)

        w.details_stack = QStackedWidget()
        w.details_placeholder = QLabel("Selecciona una tarea de la lista para ver sus detalles y acciones.")
        w.details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        w.details_placeholder.setWordWrap(True)
        w.details_placeholder.setStyleSheet("color: #7f8c8d; font-size: 13px; padding: 20px;")

        w.task_actions_widget = self._create_task_actions_widget()
        w.details_stack.addWidget(w.details_placeholder)
        w.details_stack.addWidget(w.task_actions_widget)

        details_content_layout = QVBoxLayout()
        details_content_layout.addWidget(w.details_stack)
        w.details_group.setLayout(details_content_layout)

        splitter.addWidget(tasks_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)

        return container

    def _create_task_actions_widget(self) -> QWidget:
        """Panel derecho: estado de la tarea y botones (etiquetas, QR, incidencia, fin)."""
        w = self._w
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        details_font = QFont()
        details_font.setPointSize(12)
        w.selected_task_code_label = QLabel("TAREA: N/A")
        details_font.setBold(True)
        w.selected_task_code_label.setFont(details_font)

        w.selected_task_desc_label = QLabel("Descripción: N/A")
        w.selected_task_desc_label.setWordWrap(True)

        w.task_status_label = QLabel("Estado: Pendiente")
        w.task_status_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")

        layout.addWidget(w.selected_task_code_label)
        layout.addWidget(w.selected_task_desc_label)
        layout.addWidget(w.task_status_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        actions_font = QFont()
        actions_font.setPointSize(12)
        actions_font.setBold(True)

        w.generate_labels_btn = QPushButton("🖨️ 1. Generar Etiquetas QR")
        w.generate_labels_btn.setFont(actions_font)
        w.generate_labels_btn.setFixedHeight(50)
        w.generate_labels_btn.setStyleSheet("background-color: #3498db; color: white;")
        layout.addWidget(w.generate_labels_btn)

        w.start_task_btn = QPushButton("▶️ 2. Iniciar Tarea (Escanear QR)")
        w.start_task_btn.setFont(actions_font)
        w.start_task_btn.setFixedHeight(50)
        w.start_task_btn.setStyleSheet("background-color: #2ecc71; color: white;")
        layout.addWidget(w.start_task_btn)

        w.register_incidence_btn = QPushButton("⚠️ 3. Registrar Incidencia")
        w.register_incidence_btn.setFont(actions_font)
        w.register_incidence_btn.setFixedHeight(50)
        w.register_incidence_btn.setStyleSheet("background-color: #f39c12; color: white;")
        layout.addWidget(w.register_incidence_btn)

        w.end_task_btn = QPushButton("⏹️ 4. Finalizar Tarea (Escanear QR)")
        w.end_task_btn.setFont(actions_font)
        w.end_task_btn.setFixedHeight(50)
        w.end_task_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        layout.addWidget(w.end_task_btn)

        w.consult_qr_btn = QPushButton("🔍 Consultar QR")
        w.consult_qr_btn.setFixedHeight(40)
        layout.addWidget(w.consult_qr_btn)

        layout.addStretch()

        w.generate_labels_btn.clicked.connect(w._on_generate_labels_clicked)
        w.start_task_btn.clicked.connect(w._on_start_task_clicked)
        w.register_incidence_btn.clicked.connect(w._on_register_incidence_clicked)
        w.end_task_btn.clicked.connect(w._on_end_task_clicked)
        w.consult_qr_btn.clicked.connect(w.consult_qr_requested.emit)

        return widget
