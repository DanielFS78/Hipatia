"""
Utilidades de apoyo para `SimulationExecutionManager`.

Estas funciones encapsulan bloques repetidos (construcción de scheduler,
activación de botones y arranque de hilos) para mantener el manager pequeño.
"""

from __future__ import annotations

from datetime import datetime
from dataclasses import replace
from typing import Any

from core.dtos import CalculationProductDTO, CalculationStepDTO
from core.simulation.engine.motor import MotorDeEventos


def build_scheduler(
    *,
    production_flow: list[dict[str, Any]],
    worker_service: Any,
    machine_service: Any,
    schedule_manager: Any,
    time_calculator_cls: Any,
    scheduler_cls: Any = MotorDeEventos,
    visual_dialog_reference: Any | None = None,
) -> Any:
    """Construye el motor de simulación a partir del estado actual de workers y máquinas."""
    workers_data = worker_service.get_all_workers(include_inactive=False)
    worker_names_and_skills = [(w.nombre_completo, w.tipo_trabajador) for w in workers_data]
    all_machines_data = machine_service.get_all_machines(include_inactive=False)
    machines_dict = {str(m.id): m.nombre for m in all_machines_data}
    time_calculator = time_calculator_cls(schedule_manager)

    kwargs: dict[str, Any] = {
        "production_flow": production_flow,
        "all_workers_data": worker_names_and_skills,
        "all_machines_data": machines_dict,
        "schedule_config": schedule_manager,
        "time_calculator": time_calculator,
        "start_date": datetime.now(),
    }
    if visual_dialog_reference is not None:
        kwargs["visual_dialog_reference"] = visual_dialog_reference
    return scheduler_cls(**kwargs)


def set_planning_units(planning_session: list[Any], units: int) -> None:
    """Aplica unidades de producción a cada ítem (dict o DTO)."""
    for i, item in enumerate(planning_session):
        if isinstance(item, dict):
            item["unidades"] = units
        elif isinstance(item, CalculationStepDTO):
            planning_session[i] = replace(item, unidades=units)
        elif isinstance(item, CalculationProductDTO):
            item.units_for_this_instance = units


def enable_result_actions(calc_page: Any, *, include_go_home: bool = False) -> None:
    """Habilita los botones de acciones disponibles tras resultados."""
    calc_page.save_pila_button.setEnabled(True)
    calc_page.export_button.setEnabled(True)
    calc_page.export_pdf_button.setEnabled(True)
    calc_page.export_log_button.setEnabled(True)
    calc_page.clear_button.setEnabled(True)
    if include_go_home:
        calc_page.go_home_button.setEnabled(True)


def start_optimizer_thread(
    *,
    optimizer: Any,
    start_date: Any,
    end_date: Any,
    units: int,
    thread_cls: Any,
    worker_cls: Any,
    on_finished: Any,
    controller_ref: Any,
) -> None:
    """Crea y arranca el hilo de optimización, registrándolo en controller_ref."""
    exec_thread = thread_cls()
    worker = worker_cls(optimizer, start_date, end_date, units)
    worker.moveToThread(exec_thread)

    controller_ref.execution_thread = exec_thread
    controller_ref.worker = worker

    exec_thread.started.connect(worker.run)
    worker.finished.connect(on_finished)
    worker.finished.connect(worker.deleteLater)
    exec_thread.finished.connect(exec_thread.deleteLater)
    exec_thread.start()
