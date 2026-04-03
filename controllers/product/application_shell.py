# -*- coding: utf-8 -*-
"""
Subconjunto tipado de AppController usado por ProductManager / FabricacionManager.
Evita depender del tipo completo del hub en la capa de producto.
"""
from __future__ import annotations

from typing import Any, Protocol, Union

from core.dtos import FileOperationResultDTO


class IApplicationShell(Protocol):
    """Operaciones del hub requeridas por los gestores de producto/fabricación."""

    session_controller: Any
    ui_controller: Any

    def handle_attach_file(
        self,
        target_dir: str,
        name_prefix: Union[str, int],
        source_path: str,
        category: str = "general",
    ) -> FileOperationResultDTO: ...
