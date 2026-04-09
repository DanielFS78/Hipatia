# -*- coding: utf-8 -*-
"""RegistroTemporal: vaciado del buffer en close() y modo WAL en disco."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime

import pytest

from core.services.temporal_storage import RegistroTemporal
from core.simulation.simulation_events import EventoInicioUnidad

pytestmark = pytest.mark.unit


def test_close_flushes_partial_buffer_so_events_are_queryable() -> None:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    reg: RegistroTemporal | None = None
    try:
        reg = RegistroTemporal(db_path=path, buffer_size=10_000)
        ts = datetime(2024, 1, 1, 12, 0, 0)
        reg.guardar_evento(
            EventoInicioUnidad(
                timestamp=ts,
                datos={"tarea_id": "T1", "unidad": 1, "id_instancia": "abc"},
            )
        )
        assert len(reg.buffer) == 1
        reg.close()
        assert len(reg.buffer) == 0
        events = reg.consultar_eventos()
        assert len(events) == 1
        assert events[0]["tipo_evento"] == "INICIO_UNIDAD"
    finally:
        if reg is not None:
            reg.cleanup()
