# -*- coding: utf-8 -*-
from .base import *

class HistorialWidget(QWidget):
    """Widget para la nueva sección de historial de iteraciones y fabricaciones."""
    mode_changed_signal = pyqtSignal(str)
    item_selected_signal = pyqtSignal(QListWidgetItem)
    search_text_changed_signal = pyqtSignal(str)
    filter_changed_signal = pyqtSignal(str)
    calendar_date_selected_signal = pyqtSignal(QDate)
    print_report_signal = pyqtSignal()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_mode = "iteraciones"
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(450)

        controls_frame = QFrame()
        controls_layout = QGridLayout(controls_frame)
        self.iteraciones_radio = QRadioButton("Ver Iteraciones de Producto")
        self.fabricaciones_radio = QRadioButton("Ver Fabricaciones")
        self.iteraciones_radio.setChecked(True)
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.addButton(self.iteraciones_radio, 1)
        self.mode_button_group.addButton(self.fabricaciones_radio, 2)
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Buscar por código o descripción...")
        self.filter_combo = QComboBox()
        controls_layout.addWidget(self.iteraciones_radio, 0, 0)
        controls_layout.addWidget(self.fabricaciones_radio, 0, 1)
        controls_layout.addWidget(QLabel("Buscar:"), 1, 0)
        controls_layout.addWidget(self.search_entry, 1, 1)
        controls_layout.addWidget(QLabel("Filtrar por Responsable:"), 2, 0)
        controls_layout.addWidget(self.filter_combo, 2, 1)
        left_layout.addWidget(controls_frame)

        self.results_list = QListWidget()
        left_layout.addWidget(self.results_list, 1)

        self.calendar = QCalendarWidget()
        left_layout.addWidget(self.calendar)

        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        self.details_stack = QStackedWidget()
        self._create_details_page()
        self._create_placeholder_page()
        self.details_stack.setCurrentIndex(0)
        right_layout.addWidget(self.details_stack, 1)

        self.iteraciones_radio.toggled.connect(self._on_mode_changed)
        self.search_entry.textChanged.connect(self.search_text_changed_signal.emit)
        self.filter_combo.currentTextChanged.connect(self.filter_changed_signal.emit)
        self.results_list.itemClicked.connect(self.item_selected_signal.emit)
        self.calendar.clicked.connect(self.calendar_date_selected_signal.emit)
        self.print_report_button.clicked.connect(self.print_report_signal.emit)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

    def _create_placeholder_page(self):
        placeholder_widget = QWidget()
        layout = QVBoxLayout(placeholder_widget)
        placeholder_label = QLabel("Seleccione un elemento de la lista para ver sus detalles.")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setWordWrap(True)
        font = placeholder_label.font()
        font.setPointSize(16)
        placeholder_label.setFont(font)
        layout.addWidget(placeholder_label)
        self.details_stack.insertWidget(0, placeholder_widget)

    def _create_details_page(self):
        details_widget = QWidget()
        layout = QVBoxLayout(details_widget)

        self.details_title_label = QLabel("Detalles del Elemento")
        font = self.details_title_label.font()
        font.setPointSize(18)
        font.setBold(True)
        self.details_title_label.setFont(font)
        layout.addWidget(self.details_title_label)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text, 2)

        self.activity_chart_view = self._create_chart_view("Actividad Mensual (Último Año)")
        layout.addWidget(self.activity_chart_view, 1)

        self.print_report_button = QPushButton("Imprimir Informe Detallado (PDF)")
        self.print_report_button.setMinimumHeight(40)
        layout.addWidget(self.print_report_button)

        self.details_stack.insertWidget(1, details_widget)

    def _create_chart_view(self, title):
        chart = QChart()
        chart.setTitle(title)
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        return chart_view

    def _on_mode_changed(self):
        if self.iteraciones_radio.isChecked():
            self.current_mode = "iteraciones"
            self.filter_combo.clear()
            self.filter_combo.addItem("Todos los Responsables")
            self.search_entry.setPlaceholderText("Buscar por código o descripción de producto...")
        else:
            self.current_mode = "fabricaciones"
            self.filter_combo.clear()
            self.filter_combo.addItem("Todas las Fabricaciones")
            self.search_entry.setPlaceholderText("Buscar por código o descripción de fabricación...")

        self.mode_changed_signal.emit(self.current_mode)

    def clear_view(self):
        self.results_list.clear()
        self.clear_calendar_format()
        self.details_stack.setCurrentIndex(0)

    def clear_calendar_format(self):
        default_format = QTextCharFormat()
        self.calendar.setDateTextFormat(QDate(), default_format)

    def highlight_calendar_dates(self, dates, color_hex):
        date_format = QTextCharFormat()
        date_format.setBackground(QColor(color_hex))
        date_format.setForeground(QColor("white"))
        for q_date in dates:
            self.calendar.setDateTextFormat(q_date, date_format)
