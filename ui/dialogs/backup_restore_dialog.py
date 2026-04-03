# -*- coding: utf-8 -*-
"""
Backup Restore Dialog
Permite visualizar, seleccionar y restaurar backups automáticos.
"""
import logging
from typing import List, Optional, Any
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QHeaderView, QGroupBox,
    QTextEdit, QProgressDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.services.backup_service import BackupService
from core.dtos import BackupInfoDTO


class BackupRestoreDialog(QDialog):
    """Diálogo para gestionar la restauración de backups."""
    
    def __init__(self, backup_service: BackupService, parent: Any = None, audit_logger: Any = None) -> None:
        super().__init__(parent)
        self.backup_service = backup_service
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("EvolucionTiemposApp.BackupRestore")
        self.selected_backup: BackupInfoDTO | None = None
        
        self.setWindowTitle("Gestión de Backups")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_backups()
    
    def init_ui(self) -> None:
        """Inicializa la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Backups Disponibles")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Descripción
        desc_label = QLabel(
            "Selecciona un backup para restaurar. Los archivos se extraerán a un directorio "
            "de staging para revisión antes de aplicarlos manualmente."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Tabla de backups
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(5)
        self.backups_table.setHorizontalHeaderLabels([
            "Nombre", "Fecha", "Tamaño (MB)", "Checksum", "Estado"
        ])
        header = self.backups_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.backups_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backups_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.backups_table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.backups_table)
        
        # Panel de información
        info_group = QGroupBox("Información del Backup Seleccionado")
        info_layout = QVBoxLayout(info_group)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setText("Selecciona un backup para ver detalles...")
        info_layout.addWidget(self.info_text)
        layout.addWidget(info_group)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Actualizar Lista")
        self.refresh_btn.clicked.connect(self.load_backups)
        
        self.restore_btn = QPushButton("📦 Restaurar a Staging")
        self.restore_btn.setEnabled(False)
        self.restore_btn.clicked.connect(self._on_restore_clicked)
        
        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.restore_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def load_backups(self) -> None:
        """Carga la lista de backups disponibles."""
        self.logger.info("Cargando lista de backups...")
        
        try:
            backups = self.backup_service.list_available_backups()
            
            self.backups_table.setRowCount(0)
            
            if not backups:
                self.backups_table.setRowCount(1)
                no_backups_item = QTableWidgetItem("No hay backups disponibles")
                no_backups_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.backups_table.setItem(0, 0, no_backups_item)
                self.backups_table.setSpan(0, 0, 1, 5)
                return
            
            for row, backup in enumerate(backups):
                self.backups_table.insertRow(row)
                
                # Nombre
                name_item = QTableWidgetItem(backup.name)
                name_item.setData(Qt.ItemDataRole.UserRole, backup)  # Guardar metadata
                self.backups_table.setItem(row, 0, name_item)
                
                # Fecha
                date_str = backup.date.strftime("%Y-%m-%d %H:%M:%S")
                self.backups_table.setItem(row, 1, QTableWidgetItem(date_str))
                
                # Tamaño
                size_item = QTableWidgetItem(f"{backup.size_mb:.2f}")
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.backups_table.setItem(row, 2, size_item)
                
                # Checksum
                checksum_status = "✓" if backup.has_checksum else "✗"
                checksum_item = QTableWidgetItem(checksum_status)
                checksum_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.backups_table.setItem(row, 3, checksum_item)
                
                # Estado
                status = "Íntegro" if backup.has_checksum else "Sin verificar"
                self.backups_table.setItem(row, 4, QTableWidgetItem(status))
            
            self.logger.info(f"Se cargaron {len(backups)} backups")
            
        except Exception as e:
            self.logger.error(f"Error cargando backups: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar la lista de backups:\n{e}"
            )
    
    def _on_selection_changed(self) -> None:
        """Maneja el cambio de selección en la tabla."""
        selected_items = self.backups_table.selectedItems()
        
        if not selected_items:
            self.restore_btn.setEnabled(False)
            self.info_text.setText("Selecciona un backup para ver detalles...")
            self.selected_backup = None
            return
        
        # Obtener metadata del backup seleccionado
        row = selected_items[0].row()
        name_item = self.backups_table.item(row, 0)
        
        if name_item:
            backup_data = name_item.data(Qt.ItemDataRole.UserRole)
            if backup_data and isinstance(backup_data, BackupInfoDTO):
                self.selected_backup = backup_data
                self.restore_btn.setEnabled(True)
                
                # Mostrar información detallada
                info_html = f"""
                <b>Nombre:</b> {backup_data.name}<br>
                <b>Fecha:</b> {backup_data.date.strftime("%Y-%m-%d %H:%M:%S")}<br>
                <b>Tamaño:</b> {backup_data.size_mb:.2f} MB<br>
                <b>Ruta:</b> {backup_data.path}<br>
                <b>Checksum:</b> {'Verificado ✓' if backup_data.has_checksum else 'No disponible ✗'}
                """
                self.info_text.setHtml(info_html)
    
    def _on_restore_clicked(self) -> None:
        """Maneja el clic en el botón de restaurar."""
        if not self.selected_backup:
            return
        
        backup_name = self.selected_backup.name
        
        # Confirmación con advertencia
        reply = QMessageBox.warning(
            self,
            "Confirmar Restauración",
            f"<b>¿Desea restaurar el backup '{backup_name}'?</b><br><br>"
            f"<b>⚠️ IMPORTANTE:</b><br>"
            f"• Los archivos se extraerán a <code>data/backups/staging/</code><br>"
            f"• Deberá <b>revisar manualmente</b> los archivos extraídos<br>"
            f"• Para aplicar la restauración, copie los archivos a <code>data/</code><br>"
            f"• <b>Reinicie la aplicación</b> después de copiar los archivos<br><br>"
            f"<i>Esta operación NO sobrescribirá automáticamente los datos actuales.</i>",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        
        if reply != QMessageBox.StandardButton.Ok:
            return
        
        # Crear diálogo de progreso
        progress = QProgressDialog("Restaurando backup...", "Cancelar", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        try:
            # Ejecutar restauración
            success, staging_dir = self.backup_service.restore_backup(backup_name)
            
            progress.close()
            
            if success:
                QMessageBox.information(
                    self,
                    "Restauración Completada",
                    f"<b>✓ Backup restaurado exitosamente</b><br><br>"
                    f"<b>Directorio de staging:</b><br>"
                    f"<code>{staging_dir}</code><br><br>"
                    f"<b>Próximos pasos:</b><br>"
                    f"1. Revise los archivos en el directorio de staging<br>"
                    f"2. Si todo es correcto, copie los archivos a <code>data/</code><br>"
                    f"3. Reinicie la aplicación para cargar los datos restaurados<br><br>"
                    f"<i>Nota: Esta operación no afecta los datos actuales hasta que los copie manualmente.</i>"
                )
                self.logger.info(f"Backup {backup_name} restaurado a {staging_dir}")
                
                if self.audit_logger:
                    self.audit_logger.log(
                        username="User",
                        action="RESTORE_STAGING",
                        description=f"Restauración a staging: {backup_name}",
                        success=True
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Error en Restauración",
                    f"No se pudo restaurar el backup '{backup_name}'.\n"
                    f"Revise el log para más detalles."
                )
                self.logger.error(f"Fallo al restaurar backup {backup_name}")
                if self.audit_logger:
                    self.audit_logger.log(
                        username="User",
                        action="RESTORE_STAGING",
                        description=f"Fallo al restaurar {backup_name}",
                        success=False
                    )

        except Exception as e:
            progress.close()
            self.logger.error(f"Error durante restauración: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error inesperado durante la restauración:\n{e}"
            )
            if self.audit_logger:
                    self.audit_logger.log(
                        username="User",
                        action="RESTORE_STAGING",
                        description=f"Excepción al restaurar {backup_name}",
                        success=False,
                        error_message=str(e)
                    )
