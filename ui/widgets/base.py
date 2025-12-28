# -*- coding: utf-8 -*-
import logging
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QRadioButton, QButtonGroup, QGridLayout, QFrame,
    QScrollArea, QStackedWidget, QTimeEdit, QComboBox, QCheckBox,
    QTabWidget, QGroupBox, QSplitter, QMessageBox, QApplication,
    QAbstractItemView, QSpinBox, QDateEdit, QPlainTextEdit,
    QProgressBar, QSlider, QTreeWidget, QTreeWidgetItem, QMenuBar,
    QMenu, QStatusBar, QDialogButtonBox, QCompleter, QDialog, QTextEdit,
    QFormLayout, QCalendarWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QPoint, QRect
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QPainter, QTextCharFormat

# PyQt6 Charts
try:
    from PyQt6.QtCharts import (
        QChart, QChartView, QBarSeries, QBarSet, QLineSeries, QPieSeries,
        QDateTimeAxis, QValueAxis, QBarCategoryAxis, QScatterSeries
    )
except ImportError:
    logging.warning("PyQt6.QtCharts no está disponible. Los gráficos no funcionarán.")

# --- CONSTANTES DE LA APLICACIÓN ---
MAX_TASKS_TO_RENDER = 500
