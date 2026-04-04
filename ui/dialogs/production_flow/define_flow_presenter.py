"""
Interfaz PyQt6 (`define_flow_presenter`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

import logging
import math
from typing import List, Dict, Any, Optional, TYPE_CHECKING, cast
from datetime import datetime
from core.define_flow_presenter_io import (
    find_first_positive_duration,
    legacy_flow_list_to_production_steps,
    main_task_deadline,
    main_task_departamento,
    main_task_desc_for_library,
    main_task_descripcion_producto,
    main_task_fabricacion_id,
    main_task_iterate_sub_partes,
    main_task_product_code,
    main_task_sub_partes_sequence,
    sub_task_display_name,
    sub_task_requiere_maquina_tipo,
    sub_task_tipo_trabajador,
)
from core.dtos import (
    FlowTaskDataDTO,
    FlowTaskConfigDTO,
    ProductionFlowStepDTO,
    FlowItemDTO,
    ProductFlowLibraryProductDTO,
)

if TYPE_CHECKING:
    from core.app_model import AppModel
    from core.config import ScheduleConfig

from core.services.machine_service import MachineService
from core.services.preparation_service import PreparationService
from core.services.fabricacion_service import FabricacionService


def _normalize_prep_info_response(raw: Any) -> tuple[Optional[Any], Optional[Any]]:
    """Convierte respuesta legada (tupla o lista de al menos 2 elementos) a par (grupo, máquina)."""
    if raw is None:
        return None, None
    if isinstance(raw, tuple) and len(raw) >= 2:
        return raw[0], raw[1]
    if isinstance(raw, list) and len(raw) >= 2:
        return raw[0], raw[1]
    return None, None


class DefineFlowPresenter:
    """
    Presenter/Lógica para aislar el ensamblado de datos y configuraciones 
    de la vista (DefineProductionFlowDialog).
    """
    
    def __init__(
        self,
        model: Optional[Any] = None,
        schedule_config: Optional[Any] = None,
        default_units: int = 1,
        *,
        machine_service: MachineService | None = None,
        preparation_service: PreparationService | None = None,
        fabricacion_service: FabricacionService | None = None,
    ) -> None:
        self.logger = logging.getLogger("EvolucionTiemposApp.DefineFlowPresenter")
        self.model = model
        self.machine_service = machine_service
        self.preparation_service = preparation_service
        self.fabricacion_service = fabricacion_service
        self.schedule_config = schedule_config
        self.default_units = default_units
        self.production_flow: List[ProductionFlowStepDTO] = []

    def prepare_task_data(self, tasks_data: List[Dict[str, Any]]) -> Dict[str, ProductFlowLibraryProductDTO]:
        """
        Organiza la lista plana de tareas primarias en DTOs agrupados por producto.
        """
        structured_data: Dict[str, ProductFlowLibraryProductDTO] = {}
        for main_task in tasks_data:
            product_code = main_task_product_code(main_task)
            main_product_info = {
                "code": product_code,
                "desc": main_task_desc_for_library(main_task),
            }
            structured_data[product_code] = ProductFlowLibraryProductDTO(
                descripcion=main_task_descripcion_producto(main_task),
            )

            if main_task_iterate_sub_partes(main_task):
                for i, sub_task in enumerate(main_task_sub_partes_sequence(main_task)):
                    task_name = sub_task_display_name(sub_task)
                    duration = find_first_positive_duration(
                        sub_task, ("tiempo", "tiempo_optimo", "duration")
                    )

                    if duration <= 0:
                        self.logger.error(
                            f"Tarea '{task_name}' de {product_code} sin tiempo válido. Se usará 0.0."
                        )

                    task_id = f"{product_code}_{i}_{task_name.replace(' ', '_')}"

                    task_dto = FlowTaskDataDTO(
                        id=task_id,
                        name=task_name,
                        duration=duration,
                        duration_per_unit=duration,
                        department=main_task_departamento(main_task),
                        requiere_maquina_tipo=sub_task_requiere_maquina_tipo(sub_task),
                        tipo_trabajador=sub_task_tipo_trabajador(sub_task),
                        fabricacion_id=main_task_fabricacion_id(main_task),
                        original_product_code=product_code,
                        original_product_info=main_product_info,
                        deadline=main_task_deadline(main_task),
                    )
                    structured_data[product_code].tasks.append(task_dto)
        return structured_data

    def set_production_flow(self, flow: List[Dict[str, Any]] | List[ProductionFlowStepDTO]) -> None:
        """Inicializa el flujo de producción convirtiéndolo a DTOs si es necesario."""
        if not flow:
            self.production_flow = []
            return

        if isinstance(flow[0], ProductionFlowStepDTO):
            self.production_flow = cast(List[ProductionFlowStepDTO], flow)
            return

        self.production_flow = legacy_flow_list_to_production_steps(
            cast(List[Dict[str, Any]], flow)
        )

    def get_production_flow(self) -> List[ProductionFlowStepDTO]:
        """Retorna el flujo de producción actual."""
        return self.production_flow

    def add_step(self, step_dto: ProductionFlowStepDTO) -> None:
        """Añade un nuevo paso al flujo."""
        self.production_flow.append(step_dto)

    def update_step(self, index: int, step_dto: ProductionFlowStepDTO) -> None:
        """Actualiza un paso existente."""
        if 0 <= index < len(self.production_flow):
            self.production_flow[index] = step_dto

    def delete_step(self, index: int) -> None:
        """Elimina un paso y limpia dependencias rotas."""
        if 0 <= index < len(self.production_flow):
            self.production_flow.pop(index)
            # Ajustar índices de dependencia posteriores
            for step in self.production_flow:
                prev_idx = step.config.previous_task_index
                if prev_idx is not None:
                    if prev_idx == index:
                        step.config.previous_task_index = None  # Dependencia rota
                    elif prev_idx > index:
                        step.config.previous_task_index = prev_idx - 1

    def get_step(self, index: int) -> Optional[ProductionFlowStepDTO]:
        """Obtiene un paso por su índice."""
        if 0 <= index < len(self.production_flow):
            return self.production_flow[index]
        return None

    def get_machines_for_task(self, task_info: Optional[FlowTaskDataDTO]) -> List[Any]:
        """Obtiene las máquinas compatibles con el tipo de proceso de la tarea."""
        if task_info is None:
            return []
        process_type = task_info.requiere_maquina_tipo
        if not process_type:
            return []
        if self.machine_service is not None:
            return cast(List[Any], self.machine_service.get_machines_by_process_type(process_type))
        if self.model is not None:
            return cast(List[Any], self.model.get_machines_by_process_type(process_type))
        return []

    def get_prep_info(self, product_code: str) -> tuple[Optional[Any], Optional[Any]]:
        """Obtiene información de preparación por defecto para un producto."""
        if self.preparation_service is not None:
            return self.preparation_service.get_prep_info_for_product(product_code)
        if self.fabricacion_service is not None and hasattr(
            self.fabricacion_service, "get_prep_info_for_product"
        ):
            raw = self.fabricacion_service.get_prep_info_for_product(product_code)
            return _normalize_prep_info_response(raw)
        if self.model is not None:
            raw = self.model.get_prep_info_for_product(product_code)
            return _normalize_prep_info_response(raw)
        return None, None

    def get_prep_steps_for_machine(self, machine_id: int) -> List[Any]:
        """Obtiene todas las fases de preparación asociadas a una máquina."""
        if self.preparation_service is not None:
            groups = self.preparation_service.get_groups_for_machine(machine_id)
        elif self.model is not None:
            groups = self.model.get_groups_for_machine(machine_id)
        else:
            return []
        all_steps = []
        legacy_model = self.model
        for group in groups:
            if self.preparation_service is not None:
                steps = self.preparation_service.get_steps_for_group(group.id)
            elif legacy_model is not None:
                steps = legacy_model.get_steps_for_group(group.id)
            else:
                steps = []
            all_steps.extend(steps)
        return all_steps

    def get_default_step_ids(self, group_id: int) -> List[int]:
        """Obtiene los IDs de los pasos pertenecientes a un grupo."""
        if self.preparation_service is not None:
            return [step.id for step in self.preparation_service.get_steps_for_group(group_id)]
        if self.model is not None:
            return [step.id for step in self.model.get_steps_for_group(group_id)]
        return []

    def get_step_view_model(self, index: int) -> FlowItemDTO:
        """
        Genera un FlowItemDTO listo para la vista con strings formateados (Fase 12C).
        """
        step = self.get_step(index)
        if not step:
            return FlowItemDTO(index=index, is_group=False, title="Error: Paso no encontrado")

        if step.config.is_group:
            workers = ", ".join(step.config.workers) or "Sin asignar"
            task_count = len(step.config.group_tasks)
            
            return FlowItemDTO(
                index=index,
                is_group=True,
                title=f"Grupo Secuencial ({task_count} tareas)",
                workers=workers,
                cycle_info=f"🔄 Ciclo: {step.config.units_per_cycle} uds/ciclo",
                tasks_names=[t.task.name for t in step.config.group_tasks]
            )
        
        # Paso individual
        task = step.task
        machine_name = "Sin máquina"
        if step.config.machine_id and (self.machine_service is not None or self.model is not None):
            if self.machine_service is not None:
                all_machines = self.machine_service.get_all_machines(include_inactive=True)
            elif self.model is not None:
                all_machines = self.model.get_all_machines(include_inactive=True)
            else:
                all_machines = []
            machine_name = next((m.nombre for m in all_machines if m.id == step.config.machine_id), "Desconocida")
        elif not task.requiere_maquina_tipo:
            machine_name = "No requiere máquina"

        workers_str = ", ".join(step.config.workers) or "Sin asignar"
        
        condition = "Inicio no definido"
        if step.config.start_condition_type == "date" and step.config.start_condition_date:
            condition = f"Inicia el: {step.config.start_condition_date.strftime('%d/%m/%Y')}"
        elif step.config.previous_task_index is not None:
            prev_idx = step.config.previous_task_index
            prev_step = self.get_step(prev_idx)
            prev_name = prev_step.task.name if prev_step else "N/A"
            condition = f"Depende de '{prev_name}' (Tras {step.config.min_predecessor_units} uds.)"
        elif step.config.depends_on_worker:
            condition = f"Depende de operario: {step.config.depends_on_worker}"

        return FlowItemDTO(
            index=index,
            is_group=False,
            title=f"PASO {index + 1}: {task.name}",
            machine=machine_name,
            workers=workers_str,
            condition=condition
        )

    def group_tasks(
        self, 
        selected_indices: List[int],
        selected_workers: List[str],
        units_per_cycle: int,
        total_units: int
    ) -> List[ProductionFlowStepDTO]:
        """
        Crea un grupo secuencial a partir de las tareas seleccionadas (Fase 12C).
        """
        if len(selected_indices) < 2:
            raise ValueError("Se requieren al menos 2 tareas para agrupar.")
            
        if any(selected_indices[i] + 1 != selected_indices[i + 1] for i in range(len(selected_indices) - 1)):
            raise ValueError("Solo puede agrupar tareas que son consecutivas en el flujo.")

        tasks_to_group = [self.production_flow[i] for i in selected_indices]
        
        total_time = sum(t.task.duration for t in tasks_to_group)
        total_optimal_time = sum(t.task.duration_per_unit for t in tasks_to_group)

        group_config = FlowTaskConfigDTO(
            workers=selected_workers,
            units_per_cycle=units_per_cycle,
            total_units=total_units,
            is_group=True,
            group_tasks=tasks_to_group,
            group_metadata={
                "total_cycle_time": total_time,
                "total_optimal_time": total_optimal_time,
                "task_count": len(tasks_to_group),
                "departments": list(set(t.task.department for t in tasks_to_group))
            }
        )
        
        # El DTO de cabecera del grupo usa el primer task data como referencia visual
        group_step = ProductionFlowStepDTO(task=tasks_to_group[0].task, config=group_config)

        # Mapa de índices para ajustar el flujo externo
        old_to_new_index_map = {}
        group_insert_index = selected_indices[0]
        
        for old_index in range(len(self.production_flow)):
            if old_index < group_insert_index:
                old_to_new_index_map[old_index] = old_index
            elif old_index in selected_indices:
                old_to_new_index_map[old_index] = group_insert_index
            else:
                new_idx = old_index - (len(selected_indices) - 1)
                old_to_new_index_map[old_index] = new_idx

        # Reconstruir flujo
        new_flow = self.production_flow[:group_insert_index]
        new_flow.append(group_step)
        new_flow.extend(
            step for i, step in enumerate(self.production_flow) 
            if i not in selected_indices and i > group_insert_index
        )

        # Actualizar dependencias externas
        for step in new_flow:
            if not step.config.is_group and step.config.previous_task_index is not None:
                old_dependency_index = step.config.previous_task_index
                step.config.previous_task_index = old_to_new_index_map.get(old_dependency_index)

        self.production_flow = new_flow
        return self.production_flow
