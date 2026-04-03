"""Fachada de dominio de sistema (máquinas, preparación y utilidades DB)."""

from __future__ import annotations

from typing import Any


class SystemFacade:
    """Agrupa MachineService, PreparationService y utilidades de configuración/lotes."""

    def __init__(self, machine_service: Any, preparation_service: Any, db: Any) -> None:
        self._machine_service = machine_service
        self._preparation_service = preparation_service
        self._db = db

    def __getattr__(self, name: str) -> Any:
        return getattr(self._machine_service, name)

    # --- Preparation domain ---
    def get_groups_for_machine(self, machine_id: int) -> list[Any]:
        return self._preparation_service.get_groups_for_machine(machine_id)

    def add_prep_group(self, machine_id: int, name: str, description: str, producto_codigo: str | None = None) -> int | str | None:
        return self._preparation_service.add_prep_group(machine_id, name, description, producto_codigo)

    def update_prep_group(self, group_id: int, name: str, description: str, producto_codigo: str | None = None) -> bool:
        return self._preparation_service.update_prep_group(group_id, name, description, producto_codigo)

    def delete_prep_group(self, group_id: int) -> bool:
        return self._preparation_service.delete_prep_group(group_id)

    def get_steps_for_group(self, group_id: int) -> list[Any]:
        return self._preparation_service.get_steps_for_group(group_id)

    def add_prep_step(self, group_id: int, name: str, time: float, description: str, is_daily: bool) -> int | None:
        return self._preparation_service.add_prep_step(group_id, name, time, description, is_daily)

    def update_prep_step(self, step_id: int, data: dict[str, Any]) -> bool:
        return self._preparation_service.update_prep_step(step_id, data)

    def delete_prep_step(self, step_id: int) -> bool:
        return self._preparation_service.delete_prep_step(step_id)

    def get_group_details(self, group_id: int) -> Any:
        return self._preparation_service.get_group_details(group_id)

    def get_prep_step_details(self, step_id: int) -> Any:
        return self._preparation_service.get_prep_step_details(step_id)

    def get_prep_step_details_by_ids(self, step_ids: list[int]) -> dict[int, Any]:
        return self._preparation_service.get_prep_step_details_by_ids(step_ids)

    def get_distinct_machine_processes(self) -> list[str]:
        return self._machine_service.get_distinct_machine_processes()

    def get_machine_usage_stats(self) -> dict[str, Any]:
        return self._machine_service.get_machine_usage_stats()

    def get_all_prep_steps(self) -> list[Any]:
        return self._preparation_service.get_all_prep_steps()

    def search_lotes(self, query: str) -> list[Any]:
        return self._db.lote_repo.search_lotes(query)

    def create_lote(self, data: dict[str, Any]) -> int | None:
        return self._db.lote_repo.create_lote(data)

    def get_lote_details(self, lote_id: int) -> Any:
        return self._db.lote_repo.get_lote_details(lote_id)

    def update_lote(self, lote_id: int, data: dict[str, Any]) -> bool:
        return self._db.lote_repo.update_lote(lote_id, data)

    def delete_lote(self, lote_id: int) -> bool:
        return self._db.lote_repo.delete_lote(lote_id)

    def config_get_setting(self, key: str, default: str) -> str:
        return self._db.config_repo.get_setting(key, default)

    def config_set_setting(self, key: str, value: str) -> bool:
        return self._db.config_repo.set_setting(key, value)

    def get_all_ordenes_fabricacion(self) -> list[str]:
        return self._db.tracking_repo.get_all_ordenes_fabricacion()
