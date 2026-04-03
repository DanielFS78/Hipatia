# -*- coding: utf-8 -*-
"""Cableado de señales Qt entre vista y controladores (composición; sin herencia múltiple)."""

from __future__ import annotations

from typing import Any, Callable

from PyQt6.QtWidgets import QFileDialog


class UISignalsWiring:
    """Encapsula la conexión de widgets y slots; recibe app, vista y logger del controlador."""

    def __init__(
        self,
        app: Any,
        view: Any,
        logger: Any,
        import_tasks_slot: Callable[[], None],
    ) -> None:
        self.app = app
        self.view = view
        self.logger = logger
        self._import_tasks_slot = import_tasks_slot

    def connect_navigation_signals(self) -> None:
        try:
            settings_page = self.view.pages.get("settings")
            if settings_page:
                def _connect_signal(attr_name: str, target: Any) -> None:
                    sig = getattr(settings_page, attr_name, None)
                    if sig is not None and hasattr(sig, "connect"):
                        sig.connect(target)

                def _connect_button_clicked(candidates: list[str], target: Any) -> None:
                    for name in candidates:
                        btn = getattr(settings_page, name, None)
                        if btn is not None and hasattr(btn, "clicked"):
                            btn.clicked.connect(target)
                            return

                _connect_button_clicked(
                    ["add_holiday_button", "btn_add_holiday"],
                    self.app.schedule_controller.on_add_holiday,
                )
                _connect_button_clicked(
                    ["remove_holiday_button", "btn_remove_holiday"],
                    self.app.schedule_controller.on_remove_holiday,
                )

                _connect_signal("import_signal", self.app.backup_controller.on_import_databases)
                _connect_signal("export_signal", self.app.backup_controller.on_export_databases)
                _connect_signal("sync_signal", self.app.backup_controller.on_sync_databases)
                _connect_signal("manage_backups_signal", self.app.backup_controller.show_backup_restore_dialog)

                _connect_signal("save_schedule_signal", self.app.schedule_controller.save_schedule_settings)
                _connect_signal("add_break_signal", self.app.schedule_controller.on_add_break)
                _connect_signal("edit_break_signal", self.app.schedule_controller.on_edit_break_clicked)
                _connect_signal("remove_break_signal", self.app.schedule_controller.on_remove_break_clicked)

                _connect_signal("detect_cameras_signal", self.app.hardware_controller.detect_cameras)
                _connect_signal("save_hardware_signal", self.app.hardware_controller.save_hardware_settings)
                _connect_signal("test_camera_signal", self.app.hardware_controller.test_camera)

                if hasattr(self.app, "import_tasks_from_csv"):
                    _connect_signal("import_tasks_signal", self._import_tasks_slot)
                elif hasattr(self.app, "tracking_repo") and hasattr(
                    self.app.tracking_repo, "import_tasks_from_csv"
                ):
                    _connect_signal("import_tasks_signal", self._import_tasks_slot)
                else:
                    self.logger.warning("TrackingRepository.import_tasks_from_csv no encontrado.")

            self.logger.debug("Señales de navegación y configuración conectadas.")
        except Exception as e:
            self.logger.error(f"Error conectando señales de navegación: {e}")

    def run_import_tasks_from_csv_dialog(self) -> None:
        """Abre diálogo CSV y delega la importación en AppModel o TrackingRepository."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self.view,
                "Importar Datos de Tareas (CSV)",
                "",
                "CSV Files (*.csv);;All Files (*)",
            )
            if not file_path:
                return

            if hasattr(self.app, "import_tasks_from_csv"):
                self.app.import_tasks_from_csv(file_path)
            elif hasattr(self.app, "tracking_repo") and hasattr(
                self.app.tracking_repo, "import_tasks_from_csv"
            ):
                success = self.app.tracking_repo.import_tasks_from_csv(file_path)
                if success:
                    self.view.show_message("Éxito", "Tareas importadas correctamente de CSV", "info")
                else:
                    self.view.show_message("Error", "Ocurrió un error al importar las tareas", "critical")
        except Exception as e:
            self.logger.error(f"Error importando tareas CSV: {e}", exc_info=True)
            self.view.show_message("Error", f"Fallo al importar CSV: {e}", "critical")

    def connect_preprocesos_signals(self) -> None:
        try:
            preprocesos_widget = self.view.pages.get("preprocesos")
            if hasattr(preprocesos_widget, "set_controller"):
                preprocesos_widget.set_controller(self.app.product_controller)

                if preprocesos_widget.add_button:
                    preprocesos_widget.add_button.clicked.connect(
                        self.app.product_controller.show_add_preproceso_dialog
                    )
                if preprocesos_widget.edit_button:
                    preprocesos_widget.edit_button.clicked.connect(preprocesos_widget._on_edit_clicked)
                if preprocesos_widget.delete_button:
                    preprocesos_widget.delete_button.clicked.connect(preprocesos_widget._on_delete_clicked)

                if self.app.preproceso_controller:
                    self.app.preproceso_controller.load_preprocesos_data()
        except Exception as e:
            self.logger.error(f"Error crítico al conectar las señales de preprocesos: {e}", exc_info=True)

    def connect_products_signals(self) -> None:
        self.app.product_controller._connect_products_signals()

    def connect_fabrications_signals(self) -> None:
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if gestion_datos_page and hasattr(gestion_datos_page, "fabricaciones_tab"):
            fabrications_page = gestion_datos_page.fabricaciones_tab
            if hasattr(fabrications_page, "search_entry"):
                fabrications_page.search_entry.textChanged.connect(
                    self.app.product_controller._on_fabrication_search_changed
                )
                fabrications_page.results_list.itemClicked.connect(
                    self.app.product_controller._on_fabrication_result_selected
                )
                fabrications_page.create_fabricacion_signal.connect(
                    self.app.product_controller.show_create_fabricacion_dialog
                )
                fabrications_page.save_fabricacion_signal.connect(
                    self.app.product_controller._on_update_fabricacion
                )
                fabrications_page.delete_fabricacion_signal.connect(
                    self.app.product_controller._on_delete_fabricacion
                )
                fabrications_page.edit_preprocesos_signal.connect(
                    self.app.product_controller.show_fabricacion_preprocesos
                )
                fabrications_page.edit_products_signal.connect(
                    self.app.product_controller.show_fabricacion_products
                )

    def connect_add_product_signals(self) -> None:
        add_prod_page = self.view.pages.get("add_product")
        if hasattr(add_prod_page, "save_button"):
            if hasattr(add_prod_page, "save_button"):
                add_prod_page.save_button.clicked.connect(self.app.product_controller._on_save_product_clicked)
                add_prod_page.manage_subs_signal.connect(
                    self.app.product_controller._on_manage_subs_for_new_product
                )
                add_prod_page.manage_procesos_signal.connect(
                    self.app.product_controller._on_manage_procesos_for_new_product
                )

    def connect_calculate_signals(self) -> None:
        self.app.calculation_controller.connect_calculate_signals()

    def connect_historial_signals(self) -> None:
        historial_page = self.view.pages.get("historial")
        if historial_page:
            self.app.historial_controller.connect_signals(historial_page)

    def connect_definir_lote_signals(self) -> None:
        lote_page = self.view.pages.get("definir_lote")
        if not lote_page:
            return

        lote_page.product_search.textChanged.connect(self.app.pila_controller._on_lote_def_product_search_changed)
        lote_page.fab_search.textChanged.connect(self.app.pila_controller._on_lote_def_fab_search_changed)
        lote_page.add_product_button.clicked.connect(self.app.pila_controller._on_add_product_to_lote_template)
        lote_page.add_fab_button.clicked.connect(self.app.pila_controller._on_add_fab_to_lote_template)
        lote_page.remove_item_button.clicked.connect(
            self.app.pila_controller._on_remove_item_from_lote_template
        )
        lote_page.new_button.clicked.connect(lote_page.clear_form)
        lote_page.save_button.clicked.connect(self.app.pila_controller._on_save_lote_template_clicked)

    def connect_lotes_management_signals(self) -> None:
        self.app.pila_controller._connect_lotes_management_signals()

    def connect_reportes_signals(self) -> None:
        reportes_page = self.view.pages.get("reportes")
        if reportes_page:
            if self.app.report_controller:
                if hasattr(reportes_page, "set_controller") and (
                    not hasattr(reportes_page, "controller") or reportes_page.controller is None
                ):
                    reportes_page.set_controller(self.app.report_controller)

    def connect_workers_signals(self) -> None:
        self.app.worker_controller._connect_workers_signals()

    def connect_machines_signals(self) -> None:
        gestion_page = self.view.pages.get("gestion_datos")
        if gestion_page and getattr(gestion_page, "maquinas_tab", None):
            machines_page = gestion_page.maquinas_tab
            if machines_page:
                machines_page.delete_signal.connect(self.app.machine_controller._on_delete_machine_clicked)
                machines_page.machines_list.itemClicked.connect(
                    self.app.machine_controller._on_machine_selected_in_list
                )
                machines_page.add_button.clicked.connect(machines_page.show_add_new_form)
                machines_page.save_signal.connect(self.app.machine_controller._on_save_machine_clicked)
                machines_page.manage_groups_signal.connect(
                    self.app.machine_controller._on_manage_prep_groups_clicked
                )
                machines_page.add_maintenance_signal.connect(
                    self.app.machine_controller._on_add_maintenance_clicked
                )
                self.app.model.machines_changed_signal.connect(self.app.machine_controller.update_machines_view)
