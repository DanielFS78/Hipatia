# -*- coding: utf-8 -*-
from .base import *

class WorkersWidget(QWidget):
    """Widget para gestionar la base de datos de trabajadores (CRUD)."""
    save_signal = pyqtSignal()
    delete_signal = pyqtSignal(int)
    add_annotation_signal = pyqtSignal(int)
    change_password_signal = pyqtSignal(int)
    product_search_signal = pyqtSignal(str)
    of_search_signal = pyqtSignal(str)
    assign_task_signal = pyqtSignal()
    cancel_task_signal = pyqtSignal(int)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_worker_id = None
        self.form_widgets = {}

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)

        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Trabajadores Actuales</b>"))
        self.workers_list = QListWidget()
        left_layout.addWidget(self.workers_list)
        self.add_button = QPushButton("Añadir Nuevo Trabajador")
        left_layout.addWidget(self.add_button)

        right_panel = QFrame()
        self.details_container_layout = QVBoxLayout(right_panel)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        self.clear_details_area()

    def populate_list(self, workers_data):
        self.workers_list.blockSignals(True)
        self.workers_list.clear()
        for worker in workers_data:
            worker_id = worker.id
            nombre = worker.nombre_completo
            activo = worker.activo
            
            item_text = f"{nombre} {'(Activo)' if activo else '(Inactivo)'}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, worker_id)
            if not activo:
                item.setForeground(QColor("gray"))
            self.workers_list.addItem(item)
        self.workers_list.blockSignals(False)
        self.clear_details_area()

    def clear_details_area(self):
        while self.details_container_layout.count():
            child = self.details_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.form_widgets = {}
        self.current_worker_id = None

        placeholder = QLabel("Seleccione un trabajador de la lista para ver sus detalles o añada uno nuevo.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        self.details_container_layout.addWidget(placeholder)

    def _create_form_widgets(self):
        self.clear_details_area()

        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)

        self.form_widgets['title'] = QLabel()
        font = self.form_widgets['title'].font()
        font.setBold(True)
        font.setPointSize(14)
        self.form_widgets['title'].setFont(font)
        container_layout.addWidget(self.form_widgets['title'])

        tab_widget = QTabWidget()
        container_layout.addWidget(tab_widget, 1)
        self.form_widgets['tab_widget'] = tab_widget

        details_tab = QWidget()
        form_layout = QFormLayout(details_tab)

        self.form_widgets['nombre'] = QLineEdit()
        self.form_widgets['tipo_trabajador'] = QComboBox()
        self.form_widgets['tipo_trabajador'].addItems(
            ["Tipo 1 (Polivalente)", "Tipo 2 (Intermedio)", "Tipo 3 (Especialista)"])
        self.form_widgets['activo'] = QCheckBox("Trabajador en activo")
        self.form_widgets['notas'] = QTextEdit()

        self.form_widgets['username'] = QLineEdit()
        self.form_widgets['username'].setPlaceholderText("Dejar vacío si no necesita acceso al sistema")
        self.form_widgets['password'] = QLineEdit()
        self.form_widgets['password'].setEchoMode(QLineEdit.EchoMode.Password)
        self.form_widgets['password'].setPlaceholderText("Dejar vacío para no cambiar")
        self.form_widgets['confirm_password'] = QLineEdit()
        self.form_widgets['confirm_password'].setEchoMode(QLineEdit.EchoMode.Password)
        self.form_widgets['confirm_password'].setPlaceholderText("Confirmar contraseña")
        self.form_widgets['role'] = QComboBox()
        self.form_widgets['role'].addItems(["(Sin acceso)", "Trabajador", "Responsable"])

        form_layout.addRow("Nombre Completo:", self.form_widgets['nombre'])
        form_layout.addRow("Nivel de Habilidad:", self.form_widgets['tipo_trabajador'])
        form_layout.addRow(self.form_widgets['activo'])
        form_layout.addRow(QLabel("<hr>"))
        form_layout.addRow(QLabel("<b>Acceso al Sistema:</b>"))
        form_layout.addRow("Usuario:", self.form_widgets['username'])
        form_layout.addRow("Contraseña:", self.form_widgets['password'])
        form_layout.addRow("Confirmar Contraseña:", self.form_widgets['confirm_password'])
        form_layout.addRow("Rol:", self.form_widgets['role'])
        
        info_label = QLabel("<i>Solo configure usuario/contraseña si el trabajador necesita acceder al sistema.</i>")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        form_layout.addRow(info_label)

        self.form_widgets['assign_group'] = QGroupBox("Asignar Nueva Tarea")
        assign_layout = QFormLayout()
        assign_layout.setContentsMargins(10, 15, 10, 15)

        self.form_widgets['product_search'] = QLineEdit()
        self.form_widgets['product_search'].setPlaceholderText("Buscar producto por código o descripción...")
        assign_layout.addRow("Buscar Producto:", self.form_widgets['product_search'])
        self.form_widgets['product_results'] = QListWidget()
        self.form_widgets['product_results'].setFixedHeight(120)
        assign_layout.addRow(self.form_widgets['product_results'])

        self.form_widgets['of_search'] = QLineEdit()
        self.form_widgets['of_search'].setPlaceholderText("Escribir Orden de Fabricación (Pedido)...")
        assign_layout.addRow("Orden de Fabricación:", self.form_widgets['of_search'])

        of_info_label = QLabel("<i>💡 Si existe, se mostrará para seleccionar. Si no existe, se creará automáticamente.</i>")
        of_info_label.setWordWrap(True)
        of_info_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        assign_layout.addRow(of_info_label)

        self.form_widgets['quantity_spinbox'] = QSpinBox()
        self.form_widgets['quantity_spinbox'].setRange(1, 9999)
        self.form_widgets['quantity_spinbox'].setValue(1)
        assign_layout.addRow("Cantidad a Producir:", self.form_widgets['quantity_spinbox'])
        self.form_widgets['assign_button'] = QPushButton("➕ Asignar Tarea al Trabajador")
        self.form_widgets['assign_button'].setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        assign_layout.addRow(self.form_widgets['assign_button'])
        self.form_widgets['assign_group'].setLayout(assign_layout)
        form_layout.addRow(self.form_widgets['assign_group'])

        self.form_widgets['product_search'].textChanged.connect(self.product_search_signal)
        self.form_widgets['of_search'].textChanged.connect(self.of_search_signal)
        self.form_widgets['assign_button'].clicked.connect(self.assign_task_signal)

        form_layout.addRow(QLabel("<hr>"))
        form_layout.addRow("Notas Generales:", self.form_widgets['notas'])

        tab_widget.addTab(details_tab, "Detalles y Asignación")

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.addWidget(QLabel("<b>Tareas Asignadas al Trabajador</b>"))
        
        self.form_widgets['history_table'] = QTableWidget()
        self.form_widgets['history_table'].setColumnCount(6)
        self.form_widgets['history_table'].setHorizontalHeaderLabels([
            "Fecha Asignación", "Código Fabricación", "Producto", "Cantidad", "Estado", "Acciones"
        ])
        header = self.form_widgets['history_table'].horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.form_widgets['history_table'].setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.form_widgets['history_table'].setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        history_layout.addWidget(self.form_widgets['history_table'])

        tab_widget.addTab(history_tab, "Tareas Asignadas")

        activity_log_tab = QWidget()
        activity_log_layout = QVBoxLayout(activity_log_tab)
        activity_log_layout.addWidget(QLabel("<b>Log de Actividad del Trabajador (Fichajes)</b>"))
        
        self.form_widgets['activity_log_table'] = QTableWidget()
        self.form_widgets['activity_log_table'].setColumnCount(7)
        self.form_widgets['activity_log_table'].setHorizontalHeaderLabels([
            "Fecha Inicio", "Fecha Fin", "Duración (seg)", "Producto", "QR", "Incidencias", "Estado"
        ])
        log_header = self.form_widgets['activity_log_table'].horizontalHeader()
        log_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        log_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.form_widgets['activity_log_table'].setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.form_widgets['activity_log_table'].setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        activity_log_layout.addWidget(self.form_widgets['activity_log_table'])

        tab_widget.addTab(activity_log_tab, "Log de Actividad")

        button_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar Cambios")
        delete_btn = QPushButton("Eliminar")
        change_pass_btn = QPushButton("Cambiar Contraseña")
        change_pass_btn.clicked.connect(lambda: self.change_password_signal.emit(self.current_worker_id))
        self.form_widgets['change_password_button'] = change_pass_btn
        save_btn.clicked.connect(self.save_signal.emit)
        delete_btn.clicked.connect(lambda: self.delete_signal.emit(self.current_worker_id))
        self.form_widgets['delete_button'] = delete_btn

        button_layout.addStretch()
        button_layout.addWidget(change_pass_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(save_btn)

        container_layout.addLayout(button_layout)
        self.details_container_layout.addWidget(container_widget)

    def show_worker_details(self, worker_data: dict):
        self._create_form_widgets()
        self.current_worker_id = worker_data.get('id')
        self.form_widgets['title'].setText("Editar Trabajador")
        self.form_widgets['nombre'].setText(worker_data.get('nombre_completo', ''))
        self.form_widgets['activo'].setChecked(bool(worker_data.get('activo', True)))
        self.form_widgets['notas'].setPlainText(worker_data.get('notas') or "")

        tipo_trabajador = worker_data.get('tipo_trabajador', 1)
        self.form_widgets['tipo_trabajador'].setCurrentIndex(tipo_trabajador - 1)

        self.form_widgets['username'].setText(worker_data.get('username') or '')
        role = worker_data.get('role') or ''
        if role == 'Trabajador': self.form_widgets['role'].setCurrentIndex(1)
        elif role == 'Responsable': self.form_widgets['role'].setCurrentIndex(2)
        else: self.form_widgets['role'].setCurrentIndex(0)

        self.form_widgets['password'].clear()
        self.form_widgets['confirm_password'].clear()
        self.form_widgets['delete_button'].setVisible(True)
        self.form_widgets['change_password_button'].setVisible(bool(self.current_worker_id))
        self.form_widgets['assign_group'].setVisible(True)

        if self.current_worker_id and self.controller:
            fabrication_history, _ = self.controller.model.get_worker_history(self.current_worker_id)
            self.populate_history_tables(fabrication_history, [])
            activity_logs = self.controller.model.get_worker_activity_log(self.current_worker_id)
            self.populate_activity_log_table(activity_logs)

    def show_add_new_form(self):
        self._create_form_widgets()
        self.current_worker_id = None
        self.form_widgets['title'].setText("Añadir Nuevo Trabajador")
        self.form_widgets['activo'].setChecked(True)
        self.form_widgets['username'].clear()
        self.form_widgets['password'].clear()
        self.form_widgets['confirm_password'].clear()
        self.form_widgets['role'].setCurrentIndex(0)
        self.form_widgets['tab_widget'].setTabVisible(1, False)
        self.form_widgets['delete_button'].setVisible(False)
        self.form_widgets['change_password_button'].setVisible(False)
        self.form_widgets['nombre'].setFocus()
        self.form_widgets['assign_group'].setVisible(False)

    def get_form_data(self):
        if not self.form_widgets: return None
        username = self.form_widgets['username'].text().strip()
        role_index = self.form_widgets['role'].currentIndex()
        role = 'Trabajador' if role_index == 1 else 'Responsable' if role_index == 2 else None

        return {
            "nombre_completo": self.form_widgets['nombre'].text().strip(),
            "activo": self.form_widgets['activo'].isChecked(),
            "notas": self.form_widgets['notas'].toPlainText().strip(),
            "tipo_trabajador": self.form_widgets['tipo_trabajador'].currentIndex() + 1,
            "username": username if username else None,
            "password": self.form_widgets['password'].text() if self.form_widgets['password'].text() else None,
            "confirm_password": self.form_widgets['confirm_password'].text() if self.form_widgets['confirm_password'].text() else None,
            "role": role
        }

    def populate_history_tables(self, fabrication_history, annotations):
        table = self.form_widgets.get('history_table')
        if not table: return
        table.setRowCount(0)
        for task_data in fabrication_history:
            row = table.rowCount()
            table.insertRow(row)
            fab_id = task_data.get('id')
            fecha = task_data.get('fecha_asignacion')
            fecha_str = fecha.strftime('%d/%m/%Y %H:%M') if isinstance(fecha, datetime) else str(fecha) if fecha else 'N/A'
            
            productos = task_data.get('productos', [])
            prod_text, qty_text = ('Sin producto', '-') if not productos else (f"{productos[0].get('codigo', '')} - {productos[0].get('descripcion', 'N/A')}", str(productos[0].get('cantidad', 0)))

            estado = task_data.get('estado', 'activo')
            estado_label = QLabel(estado.capitalize())
            if estado == 'activo': estado_label.setStyleSheet("color: green; font-weight: bold;")
            elif estado == 'completado': estado_label.setStyleSheet("color: blue; font-weight: bold;")
            elif estado == 'cancelado': estado_label.setStyleSheet("color: red; font-weight: bold;")

            table.setItem(row, 0, QTableWidgetItem(fecha_str))
            table.setItem(row, 1, QTableWidgetItem(task_data.get('codigo', '')))
            table.setItem(row, 2, QTableWidgetItem(prod_text))
            table.setItem(row, 3, QTableWidgetItem(qty_text))
            table.setCellWidget(row, 4, estado_label)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            if estado == 'activo':
                cancel_btn = QPushButton("Cancelar")
                cancel_btn.clicked.connect(lambda checked, fid=fab_id: self.cancel_task_signal.emit(fid))
                btn_layout.addWidget(cancel_btn)
            table.setCellWidget(row, 5, btn_widget)

    def populate_activity_log_table(self, activity_logs: list):
        table = self.form_widgets.get('activity_log_table')
        if not table: return
        table.setRowCount(0)
        table.setSortingEnabled(False)
        for log in activity_logs:
            row = table.rowCount()
            table.insertRow(row)
            start = log.get('tiempo_inicio')
            end = log.get('tiempo_fin')
            table.setItem(row, 0, QTableWidgetItem(start.strftime('%d/%m/%Y %H:%M:%S') if start else "En Proceso"))
            table.setItem(row, 1, QTableWidgetItem(end.strftime('%d/%m/%Y %H:%M:%S') if end else "---"))
            table.setItem(row, 2, QTableWidgetItem(str(log.get('duracion_segundos', '---'))))
            table.setItem(row, 3, QTableWidgetItem(log.get('producto_descripcion', 'N/A')))
            table.setItem(row, 4, QTableWidgetItem(log.get('qr_code', 'N/A')))
            
            # --- INCIDENCIAS (Corregido) ---
            incidencias = log.get('incidencias', [])
            incidencias_count = len(incidencias)
            
            if incidencias_count > 0:
                # Mostrar botón para ver detalles
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(4, 2, 4, 2)
                
                view_btn = QPushButton(f"Ver ({incidencias_count}) ⚠️")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f39c12; 
                        color: white; 
                        font-weight: bold;
                        border-radius: 4px;
                        padding: 2px 8px;
                    }
                    QPushButton:hover {
                        background-color: #e67e22;
                    }
                """)
                # Usamos functools.partial o lambda con variable capturada correctamente
                view_btn.clicked.connect(lambda checked, incs=incidencias: self.show_incidences_dialog(incs))
                
                btn_layout.addWidget(view_btn)
                btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setCellWidget(row, 5, btn_widget)
            else:
                # Mostrar texto simple si no hay incidencias
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 5, item)

            estado_item = QTableWidgetItem(log.get('estado', 'desconocido'))
            if log.get('estado') == 'completado': estado_item.setForeground(QColor("blue"))
            elif log.get('estado') == 'en_proceso': estado_item.setForeground(QColor("orange"))
            table.setItem(row, 6, estado_item)
        table.setSortingEnabled(True)

    def show_incidences_dialog(self, incidences: list):
        """Muestra un diálogo con el detalle de las incidencias."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Detalle de Incidencias")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel(f"Historial de Incidencias ({len(incidences)})")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Lista detallada
        list_widget = QListWidget()
        list_widget.setAlternatingRowColors(True)
        
        for inc in incidences:
            # inc es un diccionario porque get_worker_activity_log devuelve dicts
            fecha = inc.get('fecha_reporte')
            # Asegurar que fecha sea string formateado
            if isinstance(fecha, (datetime, date)):
                fecha_str = fecha.strftime('%d/%m/%Y %H:%M')
            else:
                fecha_str = str(fecha)
                
            tipo = inc.get('tipo_incidencia', 'N/A')
            desc = inc.get('descripcion', 'Sin descripción')
            estado = inc.get('estado', 'Abierta')
            adjuntos = inc.get('adjuntos', [])
            
            item_text = f"[{fecha_str}] - TIPO: {tipo} ({estado})\n{desc}"
            
            if adjuntos:
                item_text += f"\n📎 {len(adjuntos)} Adjunto(s)"
                
            item = QListWidgetItem(item_text)
            
            # Estilo condicional según estado
            font = QFont()
            if estado.lower() != 'completada' and estado.lower() != 'resuelta':
                 # Resaltar incidencias no resueltas
                item.setForeground(QColor("#c0392b"))
            
            item.setFont(font)
            list_widget.addItem(item)
            
        layout.addWidget(list_widget)
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)
        
        dialog.exec()

    def get_assignment_data(self):
        if 'product_results' not in self.form_widgets or not self.form_widgets['product_results'].currentItem(): return None
        return {
            "worker_id": self.current_worker_id,
            "product_code": self.form_widgets['product_results'].currentItem().data(Qt.ItemDataRole.UserRole),
            "quantity": self.form_widgets['quantity_spinbox'].value(),
            "orden_fabricacion": self.form_widgets['of_search'].text().strip().upper() if self.form_widgets.get('of_search') else None
        }

    def update_product_search_results(self, results):
        if 'product_results' not in self.form_widgets: return
        self.form_widgets['product_results'].clear()
        for product in results:
            item = QListWidgetItem(f"{product.codigo} | {product.descripcion}")
            item.setData(Qt.ItemDataRole.UserRole, product.codigo)
            self.form_widgets['product_results'].addItem(item)

    def setup_of_completer(self, of_list):
        if 'of_search' not in self.form_widgets: return
        completer = QCompleter(of_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.form_widgets['of_search'].setCompleter(completer)
