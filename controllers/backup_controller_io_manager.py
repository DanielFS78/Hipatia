# -*- coding: utf-8 -*-
"""
Operaciones I/O de importación, exportación y sincronización para backups.

``BackupController`` instancia ``BackupIOManager`` y delega en ``on_import_databases`` /
``on_export_databases`` / ``on_sync_databases``; sin herencia múltiple.
"""

from __future__ import annotations

import logging
import os
import shutil
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Protocol

from core.dtos import DatabaseComparisonDTO
from core.paths import get_writable_app_root
from core.services.audit_logger import AuditLogger


def _comparison_has_differences(comparison: DatabaseComparisonDTO) -> bool:
    """True si la comparación incluye al menos un registro distinto."""
    return any(len(td.differences) > 0 for td in comparison.tables)


def _find_sqlite_under(root: Path) -> Path | None:
    """Busca un .db bajo root; prioriza montaje.db como en exportaciones típicas."""
    dbs = sorted(root.rglob("*.db"))
    if not dbs:
        return None
    for p in dbs:
        if p.name.lower() == "montaje.db":
            return p
    return dbs[0]


def _prepare_foreign_sqlite_path(chosen_path: str, logger: logging.Logger) -> tuple[str | None, str | None]:
    """
    Resuelve la ruta al fichero SQLite.

    Returns:
        (ruta_al_sqlite, directorio_temporal_a_borrar_o_None).
    """
    lower = chosen_path.lower()
    if lower.endswith((".db", ".sqlite", ".sqlite3")):
        if os.path.isfile(chosen_path):
            return chosen_path, None
        logger.warning("No existe el fichero de base de datos: %s", chosen_path)
        return None, None

    if not (lower.endswith(".zip") or lower.endswith(".tar.gz") or lower.endswith(".tgz")):
        logger.warning("Formato no soportado para sincronización: %s", chosen_path)
        return None, None

    tmp = tempfile.mkdtemp(prefix="hipatia_sync_")
    try:
        if lower.endswith(".zip"):
            with zipfile.ZipFile(chosen_path, "r") as zf:
                zf.extractall(tmp)
        else:
            with tarfile.open(chosen_path, "r:*") as tf:
                tf.extractall(tmp)
    except (zipfile.BadZipFile, OSError, tarfile.TarError) as e:
        logger.warning("Archivo comprimido inválido o ilegible: %s", e)
        shutil.rmtree(tmp, ignore_errors=True)
        return None, None

    found = _find_sqlite_under(Path(tmp))
    if not found:
        logger.warning("No se halló ningún .db dentro del archivo: %s", chosen_path)
        shutil.rmtree(tmp, ignore_errors=True)
        return None, None

    return str(found), tmp


class BackupControllerIOContext(Protocol):
    """Contrato mínimo que el I/O manager necesita del controlador (solo composición)."""

    view: Any
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
                extract_path = (
                    os.path.dirname(db_path) if db_path else str(get_writable_app_root())
                )
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
        chosen_path, _ = backup_controller_module.QFileDialog.getOpenFileName(
            controller.view,
            "Seleccionar Base de Datos a Sincronizar",
            "",
            "Base de datos y copias (*.db *.sqlite *.zip *.tar.gz);;SQLite (*.db *.sqlite);;ZIP (*.zip);;TAR.GZ (*.tar.gz)",
        )
        if not chosen_path:
            return

        source_label = os.path.basename(chosen_path)
        temp_dir: str | None = None
        try:
            foreign_db_path, temp_dir = _prepare_foreign_sqlite_path(chosen_path, controller.logger)
            if not foreign_db_path:
                controller.view.show_message(
                    "Sincronización",
                    "No se pudo usar el archivo seleccionado. Elija un .db válido o una copia ZIP/TAR.GZ "
                    "que contenga la base de datos (por ejemplo la exportada desde Configuración).",
                    "warning",
                )
                return

            differences = controller.db.compare_with_db(foreign_db_path)
            if not _comparison_has_differences(differences):
                controller.view.show_message(
                    "Sincronización", "No se encontraron diferencias entre las bases de datos.", "info"
                )
                return

            from controllers.ui_class_loader import ui_class

            SyncDialog = ui_class("ui.dialogs", "SyncDialog")

            dialog = SyncDialog(differences, controller.view)
            if dialog.exec() == backup_controller_module.QDialog.DialogCode.Accepted:
                selected_changes = dialog.get_selected_changes()
                if not selected_changes.tables:
                    controller.view.show_message(
                        "Sincronización", "No se seleccionó ningún cambio para importar.", "warning"
                    )
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
                            f"Sincronización parcial: {count} registros importados desde {source_label}"
                        ),
                    )

                if on_success_callback:
                    on_success_callback()
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
