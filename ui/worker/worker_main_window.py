"""
Ventana principal para trabajadores de producción.

Interfaz simplificada que muestra solo las fabricaciones asignadas
y funcionalidades de registro de tiempos e incidencias.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSpacerItem, QSizePolicy,
    QGroupBox, QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from typing import Optional

class WorkerMainWindow(QMainWindow):
    """
    Ventana principal para el rol de trabajador.

    Proporciona una interfaz simplificada con acceso únicamente a:
    - Dashboard de fabricaciones asignadas
    - Registro de trabajo mediante QR
    - Registro de incidencias

    Attributes:
        current_user (dict): Datos del trabajador autenticado
        stacked_widget (QStackedWidget): Widget apilado para cambiar entre pantallas
    """

    # Señales
    logout_requested = pyqtSignal()

    export_data_requested = pyqtSignal()


    # --- AÑADIR ESTE BLOQUE ---
    task_selected = pyqtSignal(dict)
    generate_labels_requested = pyqtSignal(dict)
    camera_config_requested = pyqtSignal()
    consult_qr_requested = pyqtSignal()
    start_task_requested = pyqtSignal(dict)
    end_task_requested = pyqtSignal(dict)
    register_incidence_requested = pyqtSignal(dict)

    def __init__(self, current_user, parent=None):
        """
        Inicializa la ventana principal del trabajador.

        Args:
            current_user (dict): Diccionario con datos del trabajador autenticado
                Debe contener: 'id', 'nombre', 'role'
            parent (QWidget, optional): Widget padre
        """
        super().__init__(parent)

        self.current_user = current_user
        self.logger = logging.getLogger("EvolucionTiemposApp.WorkerMainWindow")

        self._setup_ui()

        self.logger.info(f"WorkerMainWindow inicializada para {current_user.get('nombre', 'Usuario')}")

    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Configuración de ventana
        self.setWindowTitle(
            f"Hipatia - Trabajador: {self.current_user.get('nombre', 'Usuario')}"
        )
        self.resize(1024, 768)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Stacked widget para diferentes pantallas
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)

        # Footer
        footer = self._create_footer()
        main_layout.addWidget(footer)

        # Crear pantallas iniciales
        self._create_initial_screens()

    def _create_header(self) -> QFrame:
        """
        Crea el header de la ventana.

        Returns:
            QFrame: Frame con el header configurado
        """
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

        # Logo/Título
        title_label = QLabel("🏭 HIPATIA")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        # Espacio flexible
        header_layout.addStretch()

        # Información del usuario
        user_info_layout = QVBoxLayout()

        user_name_label = QLabel(f"👤 {self.current_user.get('nombre', 'Usuario')}")
        user_name_font = QFont()
        user_name_font.setPointSize(12)
        user_name_font.setBold(True)
        user_name_label.setFont(user_name_font)

        user_role_label = QLabel(f"Rol: {self.current_user.get('role', 'Trabajador')}")
        user_role_label.setStyleSheet("color: #bdc3c7; font-size: 10px;")

        user_info_layout.addWidget(user_name_label)
        user_info_layout.addWidget(user_role_label)

        header_layout.addLayout(user_info_layout)

        # Botón de configuración de cámara
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

        # Botón de cerrar sesión
        logout_btn = QPushButton("🚪 Cerrar Sesión")
        logout_btn.clicked.connect(self._on_logout_clicked)
        header_layout.addWidget(logout_btn)

        return header

    def _create_footer(self) -> QFrame:
        """
        Crea el footer de la ventana.
        """
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

        # --- AÑADIR ESTE BOTÓN ---
        self.export_data_btn = QPushButton("📤 Exportar Datos")
        footer_layout.addWidget(self.export_data_btn)
        # --- FIN DEL BLOQUE ---

        version_label = QLabel("Versión 1.5.0 - Interfaz Trabajador")
        footer_layout.addWidget(version_label, 0, Qt.AlignmentFlag.AlignRight)

        return footer

    def _create_initial_screens(self):
        """Crea las pantallas iniciales de la interfaz."""
        # Pantalla principal del dashboard
        dashboard_widget = self._create_dashboard_screen()
        self.add_screen("dashboard", dashboard_widget)
        self.switch_screen(0)  # Asegurarse de que se muestra

    def _create_dashboard_screen(self) -> QWidget:
        """
        Crea la pantalla principal del dashboard del trabajador.
        Muestra las tareas asignadas y los detalles/acciones.
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Panel Izquierdo: Mis Tareas ---
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        self.tasks_group = QGroupBox("Mis Tareas Asignadas")
        tasks_layout.addWidget(self.tasks_group)

        tasks_list_layout = QVBoxLayout()
        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("font-size: 14px;")
        # Conectar la señal de itemClicked
        self.tasks_list.itemClicked.connect(self._on_task_selected)
        tasks_list_layout.addWidget(self.tasks_list)
        self.tasks_group.setLayout(tasks_list_layout)

        # --- Panel Derecho: Detalles y Acciones (Modificado) ---
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        self.details_group = QGroupBox("Detalles y Acciones de Tarea")
        details_layout.addWidget(self.details_group)

        # Usamos un StackedWidget para cambiar entre el placeholder y las acciones
        self.details_stack = QStackedWidget()

        # Página 0: Placeholder
        self.details_placeholder = QLabel("Selecciona una tarea de la lista para ver sus detalles y acciones.")
        self.details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_placeholder.setWordWrap(True)
        self.details_placeholder.setStyleSheet("color: #7f8c8d; font-size: 13px; padding: 20px;")

        # Página 1: Acciones de Tarea
        self.task_actions_widget = self._create_task_actions_widget()

        self.details_stack.addWidget(self.details_placeholder)
        self.details_stack.addWidget(self.task_actions_widget)

        details_content_layout = QVBoxLayout()
        details_content_layout.addWidget(self.details_stack)
        self.details_group.setLayout(details_content_layout)

        # --- Añadir paneles al divisor ---
        splitter.addWidget(tasks_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)

        self.current_selected_task = None  # Guardar la tarea seleccionada

        return widget

    def enable_action_buttons(self, enabled: bool):
        """
        Habilita o deshabilita los botones de acción (Registrar Incidencia y Finalizar Tarea).

        Args:
            enabled (bool): True para habilitar, False para deshabilitar
        """
        self.register_incidence_btn.setEnabled(enabled)
        self.end_task_btn.setEnabled(enabled)

        # El botón de iniciar tarea se habilita/deshabilita de forma opuesta
        self.start_task_btn.setEnabled(not enabled)

        self.logger.debug(f"Botones de acción {'habilitados' if enabled else 'deshabilitados'}")

    def _create_task_actions_widget(self) -> QWidget:
        """
        Crea el widget que contiene los botones de acción para una tarea seleccionada.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        # --- Sección de Detalles ---
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

        # --- Sección de Acciones (Botones) ---
        actions_font = QFont()
        actions_font.setPointSize(12)
        actions_font.setBold(True)

        # Botón 1: Generar Etiquetas (Siempre habilitado)
        self.generate_labels_btn = QPushButton("🖨️ 1. Generar Etiquetas QR")
        self.generate_labels_btn.setFont(actions_font)
        self.generate_labels_btn.setFixedHeight(50)
        self.generate_labels_btn.setStyleSheet("background-color: #3498db; color: white;")
        layout.addWidget(self.generate_labels_btn)

        # Botón 2: Iniciar Tarea
        self.start_task_btn = QPushButton("▶️ 2. Iniciar Tarea (Escanear QR)")
        self.start_task_btn.setFont(actions_font)
        self.start_task_btn.setFixedHeight(50)
        self.start_task_btn.setStyleSheet("background-color: #2ecc71; color: white;")
        layout.addWidget(self.start_task_btn)

        # Botón 3: Registrar Incidencia
        self.register_incidence_btn = QPushButton("⚠️ 3. Registrar Incidencia")
        self.register_incidence_btn.setFont(actions_font)
        self.register_incidence_btn.setFixedHeight(50)
        self.register_incidence_btn.setStyleSheet("background-color: #f39c12; color: white;")
        layout.addWidget(self.register_incidence_btn)

        # Botón 4: Finalizar Tarea
        self.end_task_btn = QPushButton("⏹️ 4. Finalizar Tarea (Escanear QR)")
        self.end_task_btn.setFont(actions_font)
        self.end_task_btn.setFixedHeight(50)
        self.end_task_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        layout.addWidget(self.end_task_btn)

        # Botón 5: Consultar QR (Acción general)
        self.consult_qr_btn = QPushButton("🔍 Consultar QR")
        self.consult_qr_btn.setFixedHeight(40)
        layout.addWidget(self.consult_qr_btn)

        layout.addStretch()  # Empuja todo hacia arriba

        # --- Conectar botones para que emitan las señales ---
        self.generate_labels_btn.clicked.connect(self._on_generate_labels_clicked)
        self.start_task_btn.clicked.connect(self._on_start_task_clicked)

        # Conecta los botones que estaban "muertos"
        self.register_incidence_btn.clicked.connect(self._on_register_incidence_clicked)
        self.end_task_btn.clicked.connect(self._on_end_task_clicked)

        self.consult_qr_btn.clicked.connect(self.consult_qr_requested.emit)

        return widget

    def _on_logout_clicked(self):
        """Maneja el clic en el botón de cerrar sesión."""
        self.logger.info(f"Usuario {self.current_user.get('nombre', 'Usuario')} solicitó cerrar sesión")
        self.logout_requested.emit()
        self.close()

    def _on_camera_config_clicked(self):
        """Emite señal para abrir configuración de cámara."""
        self.logger.info("Usuario solicitó configuración de cámara")
        self.camera_config_requested.emit()

    def add_screen(self, name: str, widget: QWidget):
        """
        Añade una nueva pantalla al stacked widget.

        Args:
            name (str): Nombre identificador de la pantalla
            widget (QWidget): Widget de la pantalla
        """
        self.stacked_widget.addWidget(widget)
        self.logger.debug(f"Pantalla '{name}' añadida al stacked widget")

    def switch_screen(self, index: int):
        """
        Cambia a una pantalla específica.

        Args:
            index (int): Índice de la pantalla en el stacked widget
        """
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            self.logger.debug(f"Cambiado a pantalla con índice {index}")
        else:
            self.logger.warning(f"Índice de pantalla inválido: {index}")

    def show_message(self, title: str, message: str, level: str = "info"):
        """
        Muestra un mensaje en una ventana emergente.

        Args:
            title (str): Título del mensaje
            message (str): Contenido del mensaje
            level (str): Nivel del mensaje ('info', 'warning', 'error')
        """
        from PyQt6.QtWidgets import QMessageBox
        
        # Registrar en log
        if level == "info":
            self.logger.info(f"{title}: {message}")
        elif level == "warning":
            self.logger.warning(f"{title}: {message}")
        elif level == "error":
            self.logger.error(f"{title}: {message}")
        
        # Mostrar ventana emergente
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if level == "info":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif level == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif level == "error":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        
        msg_box.exec()

    def update_tasks_list(self, tasks: list):
        self.tasks_list.clear()
        if not tasks:
            self.tasks_list.addItem("No tienes tareas asignadas.")
            return

        for task in tasks:
            # task es el dict que envía el controlador

            # Intentamos obtener la información del PRODUCTO primero
            prod_codigo = task.get('producto_codigo')
            prod_desc = task.get('producto_descripcion')
            cantidad = task.get('cantidad', 0)

            display_codigo = ""
            display_desc = ""

            if prod_codigo and prod_desc:
                # ¡Éxito! Tenemos un producto. Mostramos sus datos.
                display_codigo = prod_codigo
                display_desc = f"{prod_desc} (Cantidad: {cantidad})"
            else:
                # Si no hay producto (quizás es una tarea de preproceso),
                # mostramos los datos de la fabricación como fallback.
                display_codigo = task.get('codigo', 'N/A')
                display_desc = task.get('descripcion', 'Sin descripción')

            # Creamos el item de lista con la información correcta
            item_text = f"🏭 {display_codigo}\n    {display_desc}"
            item = QListWidgetItem(item_text)

            # Guardamos el diccionario completo (esto es importante)
            item.setData(Qt.ItemDataRole.UserRole, task)
            self.tasks_list.addItem(item)

    def _on_task_selected(self, item: QListWidgetItem):
        """
        Se llama cuando el usuario selecciona una tarea de la lista.
        MODIFICADO: Ya no asume el estado, solo notifica al controlador.
        """
        try:
            self.current_selected_task = item.data(Qt.ItemDataRole.UserRole)
            if not self.current_selected_task:
                self.logger.warning("El item seleccionado no tiene datos (UserRole).")
                self.details_stack.setCurrentIndex(0)  # Mostrar placeholder
                return

            self.logger.info(f"Tarea seleccionada: {self.current_selected_task.get('codigo')}")

            # 1. Actualizar las etiquetas en el panel de acciones
            self.selected_task_code_label.setText(f"TAREA: {self.current_selected_task.get('codigo', 'N/A')}")
            self.selected_task_desc_label.setText(
                f"Descripción: {self.current_selected_task.get('descripcion', 'N/A')}")

            # 2. Poner la UI en un estado 'neutro' o de 'carga'
            self.task_status_label.setText("Estado: Comprobando...")
            self.task_status_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")

            # Deshabilitar todos los botones de acción temporalmente
            self.generate_labels_btn.setEnabled(False)
            self.start_task_btn.setEnabled(False)
            self.register_incidence_btn.setEnabled(False)
            self.end_task_btn.setEnabled(False)

            # 3. Cambiar al panel de acciones
            self.details_stack.setCurrentIndex(1)

            # 4. Emitir señal para que el controlador verifique el estado real
            # El controlador deberá recibir esta señal, consultar la BD
            # y luego llamar a self.update_task_state() con el estado correcto.
            self.task_selected.emit(self.current_selected_task)

        except Exception as e:
            self.logger.error(f"Error en _on_task_selected: {e}", exc_info=True)
            self.details_stack.setCurrentIndex(0)

    def update_task_state(self, state: str, current_step_name: Optional[str] = None):
        """
        Actualiza el estado de la UI (etiqueta y botones) según el estado de la tarea.
        El controlador llamará a este método.

        MODIFICADO: Acepta un 'current_step_name' opcional.

        Args:
            state (str): "pendiente", "en_proceso", "finalizada"
            current_step_name (str, optional): El nombre del paso que está "en_proceso".
        """
        # --- INICIO DE CORRECCIÓN ---

        # Habilitar siempre el botón de generar etiquetas
        self.generate_labels_btn.setEnabled(True)

        if state == "pendiente":
            self.task_status_label.setText("Estado: 🟢 Pendiente")
            self.task_status_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
            self.start_task_btn.setEnabled(True)
            self.register_incidence_btn.setEnabled(False)  # No se puede registrar sin iniciar
            self.end_task_btn.setEnabled(False)

        elif state == "en_proceso":
            # Si estamos en proceso, mostramos QUÉ paso está en proceso
            step_display = f"({current_step_name})" if current_step_name else ""
            self.task_status_label.setText(f"Estado: 🟡 En Proceso {step_display}")
            self.task_status_label.setStyleSheet("font-weight: bold; color: #f39c12;")

            self.start_task_btn.setEnabled(False)  # Ya iniciada
            self.register_incidence_btn.setEnabled(True)
            self.end_task_btn.setEnabled(True)

        elif state == "finalizada":
            self.task_status_label.setText("Estado: ✅ Finalizada")
            self.task_status_label.setStyleSheet("font-weight: bold; color: #3498db;")
            self.start_task_btn.setEnabled(False)
            self.register_incidence_btn.setEnabled(False)
            self.end_task_btn.setEnabled(False)

    def _on_generate_labels_clicked(self):
        if self.current_selected_task:
            self.generate_labels_requested.emit(self.current_selected_task)

    def _on_start_task_clicked(self):
        if self.current_selected_task:
            self.start_task_requested.emit(self.current_selected_task)

    def _on_register_incidence_clicked(self):
        if self.current_selected_task:
            self.register_incidence_requested.emit(self.current_selected_task)

    def _on_end_task_clicked(self):
        if self.current_selected_task:
            self.end_task_requested.emit(self.current_selected_task)