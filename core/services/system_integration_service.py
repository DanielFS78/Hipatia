# -*- coding: utf-8 -*-
"""Operaciones de sistema: lotes, configuración persistente y órdenes de tracking.

Centraliza el acceso que antes hacía AppModel directamente contra repositorios.
"""

from __future__ import annotations

from typing import Any, cast

from core.dtos import LoteDTO
from database.database_manager import DatabaseManager


class SystemIntegrationService:
    """Fachada delgada sobre repos de lotes, config y tracking."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    @property
    def lote_repo(self) -> Any:
        """Acceso puntual al repo (p. ej. APIs aún no envueltas)."""
        return self._db.lote_repo

    @property
    def preproceso_repo(self) -> Any:
        return self._db.preproceso_repo

    def search_lotes(self, query: str) -> list[Any]:
        return self._db.lote_repo.search_lotes(query)

    def create_lote(self, data: dict[str, Any]) -> int | None:
        return self._db.lote_repo.create_lote(data)

    def get_lote_details(self, lote_id: int) -> LoteDTO | None:
        return self._db.lote_repo.get_lote_details(lote_id)

    def update_lote(self, lote_id: int, data: dict[str, Any]) -> bool:
        return self._db.lote_repo.update_lote(lote_id, data)

    def delete_lote(self, lote_id: int) -> bool:
        return self._db.lote_repo.delete_lote(lote_id)

    def config_get_setting(self, key: str, default: str) -> str:
        return cast(str, self._db.config_repo.get_setting(key, default))

    def config_set_setting(self, key: str, value: str) -> bool:
        return self._db.config_repo.set_setting(key, value)

    def get_all_ordenes_fabricacion(self) -> list[str]:
        return self._db.tracking_repo.get_all_ordenes_fabricacion()
