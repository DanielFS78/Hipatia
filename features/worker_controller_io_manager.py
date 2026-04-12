# -*- coding: utf-8 -*-
"""
Nombre del Módulo: worker_controller_io_manager

Descripción: Colaborador de ``WorkerController`` para diálogos Qt, ficheros y flujos de E/S
             (etiquetas QR, exportaciones, mensajes y apertura de configuración de cámara).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox


class WorkerIOManager:
    """Colaborador de composición para operaciones I/O del WorkerController."""

    def __init__(
        self,
        controller: Any,
        camera_config_runner: Optional[Callable[[], None]] = None,
    ) -> None:
        self.controller = controller
        self._camera_config_runner = camera_config_runner

    def _handle_generate_labels(self, task_data: dict[str, Any]) -> None:
        controller = self.controller
        if not controller.label_manager or not controller.qr_generator:
            return
        try:
            fabricacion_id = task_data.get("id")
            producto_codigo = task_data.get("producto_codigo")
            if not fabricacion_id or not producto_codigo:
                return

            qrs_por_hoja = controller.label_manager.count_qr_placeholders("apli_1861_qr.docx", "A5")
            if qrs_por_hoja == 0:
                controller.main_window.show_message("Error", "Plantilla sin placeholders", "error")
                return

            num_hojas, ok = QInputDialog.getInt(None, "Etiquetas", "¿Cuántas HOJAS?", value=1, min=1, max=100)
            if not ok:
                return

            rango = controller.label_counter_repo.get_next_unit_range(fabricacion_id, num_hojas * qrs_por_hoja)
            if not rango:
                return

            datos_qr: list[dict[str, Any]] = []
            for unit_num in range(rango.start, rango.end + 1):
                qr_str = controller.qr_generator.generate_unique_id(fabricacion_id, producto_codigo, unit_num)
                datos_qr.append(
                    {
                        "codigo": qr_str,
                        "producto": producto_codigo,
                        "descripcion": task_data.get("descripcion", ""),
                        "qr": "placeholder",
                    }
                )

            doc_path = controller.label_manager.generate_labels("apli_1861_qr.docx", "A5", datos_qr)
            if doc_path:
                # Mantiene punto de extensión del controlador (tests y overrides).
                controller._process_label_document(doc_path)
        except Exception as e:
            controller.logger.error(f"Error generando etiquetas: {e}", exc_info=True)
            controller.main_window.show_message("Error", str(e), "error")

    def _process_label_document(self, doc_path: str) -> None:
        import shutil
        import subprocess
        controller = self.controller

        try:
            res = subprocess.run(["lpstat", "-d"], capture_output=True, text=True, timeout=2)
            if "no system default destination" not in res.stdout.lower():
                if controller.label_manager.print_document(doc_path)[0]:
                    controller.main_window.show_message("Éxito", "Enviado a impresora", "info")
                    return
        except Exception as e:
            controller.logger.debug("No se pudo verificar el estado de la impresora por defecto: %s", e)

        save_path, _ = QFileDialog.getSaveFileName(
            None,
            "Guardar Etiquetas",
            f"etiquetas_{datetime.now().strftime('%H%M%S')}.docx",
            "Word (*.docx)",
        )
        if save_path:
            shutil.copy2(doc_path, save_path)
            subprocess.run(["open", "-R", save_path])
            controller.main_window.show_message("Guardado", f"Documento en:\n{save_path}", "info")

    def _handle_export_data(self) -> None:
        import json
        controller = self.controller

        trabajador_id = controller.current_user.id
        if not trabajador_id:
            return
        try:
            last = controller.db_manager.config_repo.get_setting("last_export", "2000-01-01T00:00:00Z")
            data = controller.db_sync.get_data_for_export(trabajador_id, datetime.fromisoformat(last.replace("Z", "+00:00")))
            if not data:
                controller.main_window.show_message("Info", "Sin datos nuevos.", "info")
                return

            save_path, _ = QFileDialog.getSaveFileName(None, "Exportar", "export.json", "JSON (*.json)")
            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                controller.db_manager.config_repo.set_setting("last_export", datetime.now().isoformat())
                controller.main_window.show_message("Éxito", "Exportado.", "info")
        except Exception as e:
            controller.logger.error(f"Error export: {e}", exc_info=True)

    def _handle_camera_config(self) -> None:
        if self._camera_config_runner is not None:
            self._camera_config_runner()
            return
        self.controller.logger.warning(
            "camera_config_runner no inyectado; configuración de cámara omitida."
        )
