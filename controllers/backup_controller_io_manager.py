# -*- coding: utf-8 -*-
"""
Operaciones I/O de importación, exportación y sincronización para backups.

``BackupController`` instancia ``BackupIOManager`` y delega en ``on_import_databases`` /
``on_export_databases`` / ``on_sync_databases``; sin herencia múltiple.
"""

from __future__ import annotations

import logging
import os
import zipfile
from datetime import datetime
from typing import Any, Callable, Protocol

from core.services.audit_logger import AuditLogger
from ui.main_window import MainView


class BackupControllerIOContext(Protocol):
    """Contrato mínimo que el I/O manager necesita del controlador (solo composición)."""

    view: MainView
    db: Any
    logger: logging.Logger
    audit_logger: AuditLogger | None

    def _get_db_path(self) -> str: ...


class BackupIOManager:
    """Colaborador de composición para operaciones I/O de backup."""

    def __init__(self, controller: BackupControllerIOContext) -> None:
        self.controller = controller

    def on_import_databases(self, on_success_callback: Callable[[], None] | None = None) -> None:
        import controllers.backup_controller as backup_controller_module
        controller = self.controller

        file_path, _ = backup_controller_module.QFileDialog.getOpenFileName(
            controller.view, "Seleccionar Copia de Seguridad", "", "Archivos ZIP (*.zip)"
        )
        if not file_path:
            return

        if controller.view.show_confirmation_dialog(
            "Confirmar", "<b>¡ADVERTENCIA!</b> Esto sobrescribirá los datos actuales. ¿Continuar?"
        ):
            sb = controller.view.statusBar()
            if sb is not None:
                sb.showMessage("Importando datos, por favor espere...")
            backup_controller_module.QApplication.processEvents()
            controller.db.close()
            current_user = "Unknown"
            user_id = None

            try:
                db_path = controller._get_db_path()
                extract_path = os.path.dirname(db_path) if db_path else os.getcwd()
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(extract_path)
                    controller.logger.info(f"Archivos del ZIP extraídos en: {extract_path}")

                from database.database_manager import DatabaseManager

                controller.db = DatabaseManager()
                controller.view.show_message(
                    "Éxito", "Datos importados correctamente. Los cambios ya están disponibles.", "info"
                )
                controller.logger.info("Importación de bases de datos completada exitosamente")

                if controller.audit_logger:
                    controller.audit_logger.log_import(
                        username=current_user,
                        description=f"Importación desde ZIP: {os.path.basename(file_path)}",
                        user_id=user_id,
                    )

                if on_success_callback:
                    on_success_callback()
            except Exception as e:
                controller.logger.error(f"Error durante la importación: {e}", exc_info=True)
                controller.view.show_message("Error", f"No se pudo importar: {e}", "critical")
                if controller.audit_logger:
                    controller.audit_logger.log(
                        username=current_user,
                        action="IMPORT",
                        description=f"Fallo al importar {os.path.basename(file_path)}",
                        success=False,
                        error_message=str(e),
                        user_id=user_id,
                    )
                try:
                    from database.database_manager import DatabaseManager

                    controller.db = DatabaseManager()
                except Exception as recon_e:
                    controller.logger.critical(
                        f"No se pudo reconectar a la base de datos tras el fallo de importación: {recon_e}"
                    )

    def on_export_databases(self) -> None:
        import controllers.backup_controller as backup_controller_module
        controller = self.controller

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        file_path, _ = backup_controller_module.QFileDialog.getSaveFileName(
            controller.view, "Guardar Copia de Seguridad", f"backup_{timestamp}.zip", "Archivos ZIP (*.zip)"
        )
        if not file_path:
            return

        try:
            db_files = [backup_controller_module.resource_path(controller.db.db_path)]
            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in db_files:
                    if os.path.exists(file):
                        zipf.write(file, os.path.basename(file))
                    else:
                        controller.logger.warning(
                            f"No se encontró el archivo de base de datos '{file}' para exportar."
                        )
            controller.view.show_message("Éxito", f"Copia de seguridad guardada en:\n{file_path}", "info")

            if controller.audit_logger:
                controller.audit_logger.log_export(
                    username="User",
                    description=f"Exportación manual a ZIP: {os.path.basename(file_path)}",
                )
        except Exception as e:
            controller.view.show_message("Error", f"No se pudo crear la copia: {e}", "critical")
            if controller.audit_logger:
                controller.audit_logger.log(
                    username="User",
                    action="EXPORT",
                    description="Fallo en exportación manual",
                    success=False,
                    error_message=str(e),
                )

    def on_sync_databases(self, on_success_callback: Callable[[], None] | None = None) -> None:
        import controllers.backup_controller as backup_controller_module
        controller = self.controller

        controller.logger.info("Iniciando proceso de sincronización de bases de datos.")
        foreign_db_path, _ = backup_controller_module.QFileDialog.getOpenFileName(
            controller.view, "Seleccionar Base de Datos a Sincronizar", "", "Archivos de Base de Datos (*.db)"
        )
        if not foreign_db_path:
            return
        differences = controller.db.compare_with_db(foreign_db_path)
        if not any(differences.values()):
            controller.view.show_message("Sincronización", "No se encontraron diferencias entre las bases de datos.", "info")
            return

        from ui.dialogs import SyncDialog

        dialog = SyncDialog(differences, controller.view)
        if dialog.exec() == backup_controller_module.QDialog.DialogCode.Accepted:
            selected_changes = dialog.get_selected_changes()
            if not selected_changes:
                controller.view.show_message("Sincronización", "No se seleccionó ningún cambio para importar.", "warning")
                return
            count = controller.db.apply_sync_changes(selected_changes)
            controller.view.show_message(
                "Sincronización Completa", f"Se han importado/actualizado {count} registros.", "info"
            )

            if controller.audit_logger:
                controller.audit_logger.log(
                    username="User",
                    action="SYNC_DB",
                    description=(
                        f"Sincronización parcial: {count} registros importados desde "
                        f"{os.path.basename(foreign_db_path)}"
                    ),
                )

            if on_success_callback:
                on_success_callback()
