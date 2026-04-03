# -*- coding: utf-8 -*-
"""
Coordinación y señales del subsistema «optimizer_worker»: enlaza UI, servicios y persistencia para este ámbito de la aplicación Hipatia.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, date

from PyQt6.QtCore import QObject, pyqtSignal

from core.services.flow_builder_service import FlowBuilderService
from core.services.time_calculator import CalculadorDeTiempos
from core.simulation.engine.motor import MotorDeEventos

if TYPE_CHECKING:
    from core.simulation.simulation_engine import Optimizer

class OptimizerWorker(QObject):
    """
    Worker para ejecutar el Optimizer en un hilo separado.
    """
    finished = pyqtSignal(object, object, int)

    def __init__(self, optimizer: Optimizer, start_date: datetime, end_date: date, units: int) -> None:
        super().__init__()
        self.optimizer = optimizer
        self.start_date = start_date
        self.end_date = end_date
        self.units = units
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.flow_builder = FlowBuilderService()

    def run(self) -> None:
        """Ejecuta el bucle de optimización usando `MotorDeEventos` directo."""
        flexible_workers_needed = 0
        final_results: Optional[List[Dict[str, Any]]] = None
        MAX_FLEXIBLE_WORKERS = 20

        while flexible_workers_needed <= MAX_FLEXIBLE_WORKERS + 1:
            self.logger.info(f"Probando optimización con {flexible_workers_needed} trabajadores flexibles extra...")
            
            # Resetear log de auditoría para esta iteración
            self.optimizer.audit_log = []
            
            # Construir flujo de producción usando FlowBuilderService
            override_flow = self.optimizer.production_flow_override or []
            production_flow = self.flow_builder.build_flow_from_override(
                override_flow, self.units
            )

            if not production_flow:
                self.logger.warning("No production flow available for optimization.")
                break

            scheduler = self._create_scheduler(production_flow, flexible_workers_needed)
            if hasattr(scheduler, "run_simulation"):
                results, audit = scheduler.run_simulation()
            else:
                results, audit = scheduler.ejecutar_simulacion()
            
            # Extendemos el log del optimizador con el de esta iteración
            self.optimizer.audit_log.extend(audit)

            all_deadlines_met = self.optimizer._verify_deadlines(results)

            if all_deadlines_met:
                self.logger.info(f"ÉXITO: Plazos cumplidos con {flexible_workers_needed} trabajadores flexibles.")
                final_results = results
                break
            
            flexible_workers_needed += 1
            
            if flexible_workers_needed > MAX_FLEXIBLE_WORKERS:
                self.logger.critical(f"Límite de {MAX_FLEXIBLE_WORKERS} trabajadores flexibles alcanzado. Planificación inviable.")
                final_results = results
                break

        self.finished.emit(final_results, self.optimizer.audit_log, flexible_workers_needed)

    def _create_scheduler(self, production_flow: List[Dict[str, Any]], extra_workers_count: int) -> MotorDeEventos:
        """Crea y configura una instancia de `MotorDeEventos`."""
        # 1. Configurar trabajadores disponibles (base + flexibles)
        all_workers_for_sim = self.optimizer.workers_with_skills.copy()
        for i in range(extra_workers_count):
            all_workers_for_sim.append((f"FLEX_{i+1}", 3))  # Nivel 3 (Experto)

        # 2. Configuración de máquinas
        model_like = getattr(self.optimizer, "db", None) or getattr(self.optimizer, "model", None)
        if model_like is None:
            raise RuntimeError("Optimizer sin referencia a modelo/DB para leer máquinas.")
        all_machines_data = model_like.machine_repo.get_all_machines()
        machines_dict = {str(m.id): m.nombre for m in all_machines_data}
        
        # 3. Calculadora de tiempos
        time_calculator = CalculadorDeTiempos(self.optimizer.schedule_config)

        # 4. Referencia al diálogo visual (si existe)
        dialog_ref = getattr(self.optimizer, 'visual_dialog_reference', None)

        return MotorDeEventos(
            production_flow=production_flow,
            all_workers_data=all_workers_for_sim,
            all_machines_data=machines_dict,
            schedule_config=self.optimizer.schedule_config,
            time_calculator=time_calculator,
            start_date=self.start_date,
            visual_dialog_reference=dialog_ref
        )
