"""Exportaciones Excel/PDF desde la última simulación (composición sobre ReportController)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from PyQt6.QtWidgets import QWidget


class ReportExportHelper:
    """Delegado sin herencia múltiple; usa el controlador para estado y handle_error."""

    def __init__(self, controller: Any) -> None:
        self._c = controller

    def _extract_fab_info_from_calc_page(self, calc_page: QWidget | None) -> str:
        fab_info = "N/A"
        if calc_page and hasattr(calc_page, "pila_content_table"):
            if calc_page.pila_content_table.rowCount() > 0:
                item = calc_page.pila_content_table.item(0, 1)
                if item:
                    fab_info = item.text()
        return fab_info

    def on_export_to_excel_clicked(self, calc_page: QWidget | None = None) -> bool:
        import controllers.report_controller as report_controller_module

        if not self._c.last_simulation_results:
            self._c.view.show_message("Sin Datos", "No hay resultados de simulación para exportar.", "warning")
            return False
        try:
            file_path, _ = report_controller_module.QFileDialog.getSaveFileName(
                self._c.view,
                "Guardar Informe Excel",
                f"Informe_Detallado_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "Archivos Excel (*.xlsx)",
            )
            if not file_path:
                return False

            self._c.logger.info("Generando informe Excel con ordenación mejorada...")
            self._c.view.statusBar().showMessage("Generando informe Excel, por favor espere...")
            report_controller_module.QApplication.processEvents()

            results_with_index = []
            for index, result in enumerate(self._c.last_simulation_results):
                result["_original_sequence"] = index
                results_with_index.append(result)

            resultados_ordenados = sorted(
                results_with_index,
                key=lambda x: (x.get("Inicio", datetime.max), x.get("_original_sequence", 0)),
            )
            datos_informe = {
                "data": resultados_ordenados,
                "audit_log": self._c.last_audit_log,
                "production_flow": self._c.last_production_flow,
                "fab_info": self._extract_fab_info_from_calc_page(calc_page),
                "unidades": self._c.last_units_calculated,
            }
            estrategia = report_controller_module.ReportePilaFabricacionExcelMejorado(self._c.schedule_manager)
            generador = report_controller_module.GeneradorDeInformes(estrategia)
            if generador.generar_y_guardar(datos_informe, file_path):
                self._c.view.show_message("Éxito", f"Informe Excel guardado en:\n{file_path}", "info")
                return True
            self._c.view.show_message("Error", "No se pudo generar el informe Excel.", "critical")
            return False
        except Exception as e:
            self._c.handle_error(e, "Export to Excel")
            self._c.view.show_message("Error Crítico", f"Ocurrió un error al generar el Excel: {e}", "critical")
            return False
        finally:
            self._c.view.statusBar().clearMessage()

    def on_export_gantt_to_pdf_clicked(self, calc_page: QWidget | None = None) -> bool:
        import controllers.report_controller as report_controller_module

        try:
            if not self._c.last_simulation_results or not self._c.last_audit_log:
                self._c.view.show_message("Sin Datos", "Debe ejecutar una simulación completa primero.", "warning")
                return False

            file_path, _ = report_controller_module.QFileDialog.getSaveFileName(
                self._c.view,
                "Guardar Informe PDF",
                f"Informe_Planificacion_{datetime.now().strftime('%Y%m%d')}.pdf",
                "Archivos PDF (*.pdf)",
            )
            if not file_path:
                return False

            meta_data_code = self._extract_fab_info_from_calc_page(calc_page)
            if meta_data_code == "N/A":
                meta_data_code = "Plan"

            datos_informe = {
                "meta_data": {"code": meta_data_code},
                "planificacion": self._c.last_simulation_results,
                "audit": self._c.last_audit_log,
                "flexible_workers_needed": self._c.last_flexible_workers_needed,
                "production_flow": self._c.last_production_flow or [],
            }
            estrategia = report_controller_module.ReporteHistorialFabricacion(
                self._c.worker_service, self._c.schedule_manager
            )
            generador = report_controller_module.GeneradorDeInformes(estrategia)
            if generador.generar_y_guardar(datos_informe, file_path):
                self._c.view.show_message("Éxito", f"Informe PDF guardado en:\n{file_path}", "info")
                return True
            self._c.view.show_message("Error", "No se pudo generar el informe PDF.", "critical")
            return False
        except Exception as e:
            self._c.handle_error(e, "Export Gantt to PDF")
            return False
