# -*- coding: utf-8 -*-
"""DTOs de flujo de producción y cámara."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Mapping


@dataclass
class FlowTaskDataDTO:
    id: str
    name: str
    duration: float
    duration_per_unit: float
    department: str
    requiere_maquina_tipo: str | None = None
    tipo_trabajador: int = 1
    fabricacion_id: int | str = "N/A"
    original_product_code: str = ""
    original_product_info: dict[str, str] = field(default_factory=dict)
    deadline: datetime | None = None
    canvas_unique_id: int | None = None
    glow_effect_widget: Any = None
    green_cycle_effect_widget: Any = None
    mixed_effect_widget: Any = None

    @classmethod
    def from_legacy_mapping(cls, m: Mapping[str, Any]) -> FlowTaskDataDTO:
        """
        Construye un DTO a partir de un dict legado (canvas / tests).

        Centraliza la conversión para que la UI no use `.get` sobre mapas crudos.
        """
        raw_id = m.get("id", "")
        id_str = str(raw_id) if raw_id is not None else ""

        def _float(key: str, default: float = 0.0) -> float:
            v = m.get(key, default)
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        duration = _float("duration", 0.0)
        duration_per_unit = _float("duration_per_unit", duration)
        try:
            tipo_trabajador = int(m.get("tipo_trabajador", 1))
        except (TypeError, ValueError):
            tipo_trabajador = 1
        opci = m.get("original_product_info") or {}
        if not isinstance(opci, dict):
            opci = {}
        return cls(
            id=id_str,
            name=str(m.get("name", "Tarea")),
            duration=duration,
            duration_per_unit=duration_per_unit,
            department=str(m.get("department", "")),
            requiere_maquina_tipo=m.get("requiere_maquina_tipo"),
            tipo_trabajador=tipo_trabajador,
            fabricacion_id=m.get("fabricacion_id", "N/A"),
            original_product_code=str(m.get("original_product_code", "")),
            original_product_info={str(k): str(v) for k, v in opci.items()},
            deadline=m.get("deadline"),
            canvas_unique_id=m.get("canvas_unique_id"),
            glow_effect_widget=m.get("glow_effect_widget"),
            green_cycle_effect_widget=m.get("green_cycle_effect_widget"),
            mixed_effect_widget=m.get("mixed_effect_widget"),
        )


@dataclass
class CanvasCyclicConnectionFlags:
    """Metadatos de pintado para aristas cíclicas en el canvas de flujo (UI)."""

    is_from_mother: bool = False
    is_to_mother: bool = False

    @classmethod
    def from_connection_mapping(cls, m: Mapping[str, Any]) -> CanvasCyclicConnectionFlags:
        """Interpreta flags desde el dict de conexión legado del canvas."""
        return cls(
            is_from_mother=bool(m.get("is_from_mother", False)),
            is_to_mother=bool(m.get("is_to_mother", False)),
        )


@dataclass
class ProductFlowLibraryProductDTO:
    """Agrupa descripción de producto y tareas (`FlowTaskDataDTO`) para biblioteca / panel de definición."""

    descripcion: str
    tasks: list[FlowTaskDataDTO] = field(default_factory=list)


@dataclass
class FlowTaskConfigDTO:
    workers: list[str] = field(default_factory=list)
    machine_id: int | None = None
    start_condition_type: str = "date"
    start_condition_date: date | None = field(default_factory=date.today)
    previous_task_index: int | None = None
    depends_on_worker: str | None = None
    total_units: int = 1
    min_predecessor_units: int = 1
    units_per_cycle: int = 1
    is_group: bool = False
    group_tasks: list["ProductionFlowStepDTO"] = field(default_factory=list)
    group_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductionFlowStepDTO:
    task: FlowTaskDataDTO
    config: FlowTaskConfigDTO


@dataclass
class FlowCanvasTaskDTO:
    step: ProductionFlowStepDTO
    position: dict[str, float] = field(default_factory=lambda: {"x": 50.0, "y": 50.0})


@dataclass
class CameraConfigDTO:
    index: int
    name: str
    is_external: bool = False


@dataclass
class CameraDetailDTO:
    index: int
    name: str
    width: int = 0
    height: int = 0
    fps: float = 0.0
    backend: str = ""
    is_working: bool = False
    error_message: str | None = None


@dataclass
class FlowItemDTO:
    """DTO para representar un ítem del flujo en la vista (Fase 12C)."""
    index: int
    is_group: bool
    title: str
    machine: str = ""
    workers: str = ""
    condition: str = ""
    cycle_info: str = ""
    tasks_names: list[str] = field(default_factory=list)

