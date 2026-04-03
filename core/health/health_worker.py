# -*- coding: utf-8 -*-
"""
Nombre del Módulo: health_worker
Descripción: QThread que orquesta DatabaseHealthChecker y TestRunner
             emitiendo señales de progreso a la UI.
"""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from .health_checker import DatabaseHealthChecker, HealthReport, TestResults


class HealthCheckWorker(QThread):
    """
    Hilo de verificación de salud del sistema.
    Emite señales de progreso para que la UI las consuma sin bloquearse.
    """

    # (test_name, current, total)
    test_progress = pyqtSignal(str, int, int)
    # TestResults al terminar los tests
    test_finished = pyqtSignal(object)
    # HealthReport parcial (solo BD, sin tests aún)
    db_checked = pyqtSignal(object)
    # HealthReport completo
    all_done = pyqtSignal(object)
    # Mensaje de error si algo falla
    error_occurred = pyqtSignal(str)

    def __init__(self, db_manager: object, run_tests: bool = True) -> None:
        """
        Inicializa el worker con el gestor de base de datos.

        Args:
            db_manager: Instancia de DatabaseManager.
            run_tests: Si True, ejecuta los tests unitarios tras verificar la BD.
        """
        super().__init__()
        self._db_manager = db_manager
        self._run_tests = run_tests

    def run(self) -> None:
        """Ejecuta las verificaciones en el hilo secundario."""
        try:
            checker = DatabaseHealthChecker()
            report = checker.check(self._db_manager)
            self.db_checked.emit(report)

            if self._run_tests:
                from .test_runner import TestRunner
                runner = TestRunner()
                runner.run(
                    progress_callback=lambda name, cur, tot: self.test_progress.emit(name, cur, tot),
                    finished_callback=self._on_tests_done,
                )
            else:
                self.all_done.emit(report)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def _on_tests_done(self, results: TestResults) -> None:
        """Callback interno cuando los tests terminan."""
        self.test_finished.emit(results)

        # Recalcular estado con los resultados de tests
        checker = DatabaseHealthChecker()
        report = checker.check(self._db_manager)
        report.test_results = results
        report.overall_status = checker._compute_status(report)
        self.all_done.emit(report)
