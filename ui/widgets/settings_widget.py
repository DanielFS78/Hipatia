# ui/widgets/settings_widget.py
"""
Nombre del Módulo: settings_widget.py
Descripción: Widget de configuración general para la aplicación Hipatia.
Maneja la lógica de horarios laborales, descansos, festivos y copias de seguridad.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QTimeEdit,
    QPushButton, QHBoxLayout, QListWidget, QCalendarWidget, QLabel, QFrame,
    QListWidgetItem, QSplitter, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor

if TYPE_CHECKING:
    from controllers.schedule_controller import ScheduleController

logger = logging.getLogger(__name__)


class SettingsWidget(QWidget):
    """
    Panel de configuración de la aplicación.
    Orquesta la vista de horarios, descansos y parámetros del sistema.

    La vista depende de ``ScheduleController`` (``set_schedule_controller``) y, si hace falta
    carga antes de existir ese controlador, de ``DatabaseManager`` vía ``set_config_db_fallback``;
    no mantiene referencia a ``AppController``.
    """
    # Señales para comunicación con el controlador
    import_signal = pyqtSignal()
    export_signal = pyqtSignal()
    save_schedule_signal = pyqtSignal(dict)
    add_break_signal = pyqtSignal()
    sync_signal = pyqtSignal()

    def __init__(self, schedule_controller: Optional[ScheduleController] = None, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa el widget de configuración.

        Args:
            schedule_controller: Controlador para gestión de horarios.
            parent: Widget padre opcional.
        """
        super().__init__(parent)
        self.schedule_controller = schedule_controller
        self._config_db: Any = None
        self._init_ui()
        if self.schedule_controller:
            self.load_schedule_settings()

    def set_schedule_controller(self, schedule_controller: Optional["ScheduleController"]) -> None:
        """Asigna el controlador de horarios (sin pasar por AppController)."""
        self.schedule_controller = schedule_controller
        self.load_schedule_settings()

    def set_config_db_fallback(self, db: Optional[Any]) -> None:
        """Base de datos con ``config_repo`` para carga temprana si aún no hay ScheduleController."""
        self._config_db = db
        if not self.schedule_controller:
            self.load_schedule_settings()

    def _init_ui(self) -> None:
        """Configura la estructura visual del panel."""
        layout = QVBoxLayout(self)

        # 1. Grupo de Horario General
        work_group = QGroupBox("Horario Laboral")
        work_layout = QFormLayout(work_group)
        self.work_start_time = QTimeEdit()
        self.work_end_time = QTimeEdit()
        work_layout.addRow("Inicio de Jornada:", self.work_start_time)
        work_layout.addRow("Fin de Jornada:", self.work_end_time)
        layout.addWidget(work_group)

        # 2. Grupo de Descansos
        breaks_group = QGroupBox("Descansos Configurados")
        breaks_layout = QVBoxLayout(breaks_group)
        self.breaks_list = QListWidget()
        breaks_layout.addWidget(self.breaks_list)

        btn_layout = QHBoxLayout()
        self.btn_add_break = QPushButton("Añadir")
        self.btn_remove_break = QPushButton("Eliminar")
        self.btn_edit_break = QPushButton("Editar")
        btn_layout.addWidget(self.btn_add_break)
        btn_layout.addWidget(self.btn_edit_break)
        btn_layout.addWidget(self.btn_remove_break)
        breaks_layout.addLayout(btn_layout)
        layout.addWidget(breaks_group)

        # 3. Calendario de Festivos
        holidays_group = QGroupBox("Gestión de Festivos")
        hol_layout = QHBoxLayout(holidays_group)
        self.calendar = QCalendarWidget()
        hol_layout.addWidget(self.calendar)

        hol_info_layout = QVBoxLayout()
        self.holidays_list = QListWidget()
        hol_info_layout.addWidget(QLabel("Días Festivos En DB:"))
        hol_info_layout.addWidget(self.holidays_list)

        hol_btn_layout = QHBoxLayout()
        self.btn_add_holiday = QPushButton("Marcar Festivo")
        self.btn_remove_holiday = QPushButton("Quitar Festivo")
        hol_btn_layout.addWidget(self.btn_add_holiday)
        hol_btn_layout.addWidget(self.btn_remove_holiday)
        hol_info_layout.addLayout(hol_btn_layout)
        hol_layout.addLayout(hol_info_layout)
        layout.addWidget(holidays_group)

        # 4. Configuración de Backup
        backup_group = QGroupBox("Copia de Seguridad")
        backup_layout = QFormLayout(backup_group)
        self.backup_time = QTimeEdit()
        backup_layout.addRow("Hora del Backup Automático:", self.backup_time)
        self.btn_export_db = QPushButton("Exportar base de datos…")
        self.btn_export_db.setToolTip(
            "Guarda la base de datos actual en un archivo ZIP. Para sincronizar en otro sitio, "
            "extrae el .db del ZIP o cópialo donde quieras comparar."
        )
        backup_layout.addRow("Copia manual:", self.btn_export_db)
        self.btn_sync_db = QPushButton("Sincronizar BD manualmente")
        self.btn_sync_db.setToolTip(
            "Compara la base de datos actual con otra copia SQLite y aplica los cambios seleccionados."
        )
        backup_layout.addRow("Sincronización:", self.btn_sync_db)
        layout.addWidget(backup_group)

        # Botón Guardar Todo
        self.btn_save_all = QPushButton("Guardar Toda la Configuración")
        self.btn_save_all.setStyleSheet("background-color: #2ecc71; color: white; height: 40px; font-weight: bold;")
        layout.addWidget(self.btn_save_all)

        # Conexión de Señales
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Conecta eventos de UI con las funciones del controlador."""
        self.btn_add_break.clicked.connect(self.on_add_break_clicked)
        self.btn_edit_break.clicked.connect(self.on_edit_break_clicked)
        self.btn_remove_break.clicked.connect(self.on_remove_break_clicked)
        self.btn_add_holiday.clicked.connect(self.on_add_holiday_clicked)
        self.btn_remove_holiday.clicked.connect(self.on_remove_holiday_clicked)
        self.btn_save_all.clicked.connect(self.on_save_all_clicked)
        self.btn_export_db.clicked.connect(self.export_signal.emit)
        self.btn_sync_db.clicked.connect(self.sync_signal.emit)
        self.breaks_list.itemSelectionChanged.connect(self._update_break_buttons_state)

    # =========================================================================
    # LÓGICA DE HORARIOS (ABSORBIDA)
    # =========================================================================

    def load_schedule_settings(self) -> None:
        """Solicita al controlador que cargue los ajustes en los widgets."""
        # 1. Intentar cargar vía ScheduleController (Arquitectura Final)
        if self.schedule_controller:
            self.schedule_controller.load_schedule_settings()
            # Cargar backup_time (específico de este widget)
            bt = self.schedule_controller.config_get_setting("backup_time", "03:00")
            self.backup_time.setTime(QTime.fromString(bt, "HH:mm"))
            return

        # 2. Fallback: solo lectura vía DatabaseManager (arranque o tests sin ScheduleController)
        db = self._config_db
        if db is not None and hasattr(db, "config_repo"):
            try:
                repo = db.config_repo
                start = repo.get_setting("work_start_time", "08:00")
                end = repo.get_setting("work_end_time", "15:15")
                bt = repo.get_setting("backup_time", "03:00")
                
                self.work_start_time.setTime(QTime.fromString(start, "HH:mm"))
                self.work_end_time.setTime(QTime.fromString(end, "HH:mm"))
                self.backup_time.setTime(QTime.fromString(bt, "HH:mm"))
                
                # Cargar descansos (import local evita ciclo ui.widgets → controllers → ui.widgets)
                from controllers.schedule_helpers import break_display_lines_from_json

                breaks_json = repo.get_setting("breaks", "[]")
                self.breaks_list.clear()
                for line in break_display_lines_from_json(breaks_json):
                    self.breaks_list.addItem(line)
            except Exception as e:
                logger.debug(f"Error en fallback de carga de settings: {e}")

    def on_add_break_clicked(self) -> None:
        """Evento para añadir un descanso mediante el diálogo del controlador."""
        if not self.schedule_controller:
            return
        self.schedule_controller.on_add_break_clicked()

    def on_edit_break_clicked(self) -> None:
        """Evento para editar el descanso seleccionado."""
        if not self.schedule_controller:
            return
        self.schedule_controller.on_edit_break_clicked()

    def on_remove_break_clicked(self) -> None:
        """Evento para eliminar el descanso seleccionado."""
        if not self.schedule_controller:
            return
        self.schedule_controller.on_remove_break_clicked()

    def on_add_holiday_clicked(self) -> None:
        """Marca el día del calendario como festivo."""
        if not self.schedule_controller:
            return
        self.schedule_controller.on_add_holiday()

    def on_remove_holiday_clicked(self) -> None:
        """Elimina el carácter festivo del día seleccionado."""
        if not self.schedule_controller:
            return
        self.schedule_controller.on_remove_holiday()

    def on_save_all_clicked(self) -> None:
        """Guarda la configuración completa incluyendo la hora de backup."""
        if not self.schedule_controller:
            return
        # Primero guardamos lo gestionado por ScheduleController
        self.schedule_controller.save_schedule_settings()

        # Segundo, guardamos la hora de backup (gestión directa)
        bt = self.backup_time.time().toString("HH:mm")
        self.schedule_controller.config_set_setting("backup_time", bt)
        logger.info(f"💾 Hora de backup guardada: {bt}")

    def _update_break_buttons_state(self) -> None:
        """Habilita o deshabilita botones según selección en la lista."""
        has_selection = len(self.breaks_list.selectedItems()) > 0
        self.btn_remove_break.setEnabled(has_selection)
        self.btn_edit_break.setEnabled(has_selection)

    def _highlight_holidays(self, holidays: List[Dict[str, str]]) -> None:
        """Pinta en el calendario los días definidos como festivos (visual)."""
        # TODO: Implementar resaltado visual en QCalendarWidget si se requiere
        pass
