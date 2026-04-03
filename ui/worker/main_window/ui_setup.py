# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`ui_setup`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QStackedWidget, QFrame, QGroupBox, QSplitter, QListWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from typing import Any

class WorkerMainWindowUISetup:
    """
    Mixin que contiene la lógica de construcción de la interfaz de usuario
    para WorkerMainWindow.
    """

    def _setup_ui(self: Any) -> None:
        """Configura la interfaz de usuario principal."""
        self.setWindowTitle(
            f"Hipatia - Trabajador: {getattr(self.current_user, 'nombre_completo', 'Usuario')}"
        )
        self.resize(1024, 768)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = self._create_header()
        main_layout.addWidget(header)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)

        footer = self._create_footer()
        main_layout.addWidget(footer)

        self._create_initial_screens()

    def _create_header(self: Any) -> QFrame:
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
        user_name_label = QLabel(f"👤 {getattr(self.current_user, 'nombre_completo', 'Usuario')}")
        user_name_font = QFont()
        user_name_font.setPointSize(12)
        user_name_font.setBold(True)
        user_name_label.setFont(user_name_font)

        user_role_label = QLabel(f"Rol: {getattr(self.current_user, 'role', 'Trabajador')}")
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
        camera_config_btn.clicked.connect(self._on_camera_config_clicked)
        camera_config_btn.setToolTip("Configurar cámara QR si tienes problemas de detección")
        header_layout.addWidget(camera_config_btn)
        
        self.btn_auto_ajustar = QPushButton("📐 Auto Ajustar UI")
        self.btn_auto_ajustar.setStyleSheet("""
            QPushButton {
                background-color: #f39c12; color: white; border: none;
                padding: 10px 20px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        self.btn_auto_ajustar.clicked.connect(self._forzar_auto_ajuste)
        self.btn_auto_ajustar.setToolTip("Recalcula el tamaño de la interfaz gráfica en pantallas pequeñas")
        header_layout.addWidget(self.btn_auto_ajustar)

        logout_btn = QPushButton("🚪 Cerrar Sesión")
        logout_btn.clicked.connect(self._on_logout_clicked)
        header_layout.addWidget(logout_btn)

        return header

    def _create_footer(self: Any) -> QFrame:
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

        self.export_data_btn = QPushButton("📤 Exportar Datos")
        footer_layout.addWidget(self.export_data_btn)

        version_label = QLabel("Versión 1.5.0 - Interfaz Trabajador")
        footer_layout.addWidget(version_label, 0, Qt.AlignmentFlag.AlignRight)

        return footer

    def _create_initial_screens(self: Any) -> None:
        dashboard_widget = self._create_dashboard_screen()
        self.add_screen("dashboard", dashboard_widget)
        self.switch_screen(0)

    def _create_dashboard_screen(self: Any) -> QWidget:
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        self.tasks_group = QGroupBox("Mis Tareas Asignadas")
        tasks_layout.addWidget(self.tasks_group)

        tasks_list_layout = QVBoxLayout()
        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("font-size: 14px;")
        self.tasks_list.itemClicked.connect(self._on_task_selected)
        tasks_list_layout.addWidget(self.tasks_list)
        self.tasks_group.setLayout(tasks_list_layout)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        self.details_group = QGroupBox("Detalles y Acciones de Tarea")
        details_layout.addWidget(self.details_group)

        self.details_stack = QStackedWidget()
        self.details_placeholder = QLabel("Selecciona una tarea de la lista para ver sus detalles y acciones.")
        self.details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_placeholder.setWordWrap(True)
        self.details_placeholder.setStyleSheet("color: #7f8c8d; font-size: 13px; padding: 20px;")

        self.task_actions_widget = self._create_task_actions_widget()
        self.details_stack.addWidget(self.details_placeholder)
        self.details_stack.addWidget(self.task_actions_widget)

        details_content_layout = QVBoxLayout()
        details_content_layout.addWidget(self.details_stack)
        self.details_group.setLayout(details_content_layout)

        splitter.addWidget(tasks_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)

        return widget

    def _create_task_actions_widget(self: Any) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        details_font = QFont()
        details_font.setPointSize(12)
        self.selected_task_code_label = QLabel("TAREA: N/A")
        details_font.setBold(True)
        self.selected_task_code_label.setFont(details_font)

        self.selected_task_desc_label = QLabel("Descripción: N/A")
        self.selected_task_desc_label.setWordWrap(True)

        self.task_status_label = QLabel("Estado: Pendiente")
        self.task_status_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")

        layout.addWidget(self.selected_task_code_label)
        layout.addWidget(self.selected_task_desc_label)
        layout.addWidget(self.task_status_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        actions_font = QFont()
        actions_font.setPointSize(12)
        actions_font.setBold(True)

        self.generate_labels_btn = QPushButton("🖨️ 1. Generar Etiquetas QR")
        self.generate_labels_btn.setFont(actions_font)
        self.generate_labels_btn.setFixedHeight(50)
        self.generate_labels_btn.setStyleSheet("background-color: #3498db; color: white;")
        layout.addWidget(self.generate_labels_btn)

        self.start_task_btn = QPushButton("▶️ 2. Iniciar Tarea (Escanear QR)")
        self.start_task_btn.setFont(actions_font)
        self.start_task_btn.setFixedHeight(50)
        self.start_task_btn.setStyleSheet("background-color: #2ecc71; color: white;")
        layout.addWidget(self.start_task_btn)

        self.register_incidence_btn = QPushButton("⚠️ 3. Registrar Incidencia")
        self.register_incidence_btn.setFont(actions_font)
        self.register_incidence_btn.setFixedHeight(50)
        self.register_incidence_btn.setStyleSheet("background-color: #f39c12; color: white;")
        layout.addWidget(self.register_incidence_btn)

        self.end_task_btn = QPushButton("⏹️ 4. Finalizar Tarea (Escanear QR)")
        self.end_task_btn.setFont(actions_font)
        self.end_task_btn.setFixedHeight(50)
        self.end_task_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        layout.addWidget(self.end_task_btn)

        self.consult_qr_btn = QPushButton("🔍 Consultar QR")
        self.consult_qr_btn.setFixedHeight(40)
        layout.addWidget(self.consult_qr_btn)

        layout.addStretch()

        self.generate_labels_btn.clicked.connect(self._on_generate_labels_clicked)
        self.start_task_btn.clicked.connect(self._on_start_task_clicked)
        self.register_incidence_btn.clicked.connect(self._on_register_incidence_clicked)
        self.end_task_btn.clicked.connect(self._on_end_task_clicked)
        self.consult_qr_btn.clicked.connect(self.consult_qr_requested.emit)

        return widget
