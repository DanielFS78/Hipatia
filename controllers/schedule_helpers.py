"""
Nombre del Módulo: controllers.schedule_helpers

Descripción: Funciones puras de apoyo (sin estado de proceso): ``parse_break_text``, ``load_breaks_list``, ``break_display_lines_from_json``, ``normalize_holidays``, ``holidays_dates``, ``dump_json``. Integración típica con: ``__future__``, ``json``.
"""

from __future__ import annotations

import json
from typing import Any


def parse_break_text(break_text: str) -> tuple[str, str] | None:
    """Parsea un texto `HH:mm - HH:mm` y devuelve (start, end) o None."""
    if " - " not in break_text:
        return None
    parts = break_text.split(" - ")
    if len(parts) != 2:
        return None
    start_str, end_str = parts[0].strip(), parts[1].strip()
    if not start_str or not end_str:
        return None
    return start_str, end_str


def load_breaks_list(breaks_json: str) -> list[dict[str, str]]:
    """Convierte JSON de breaks a lista normalizada de dicts."""
    try:
        raw = json.loads(breaks_json)
        if not isinstance(raw, list):
            return []
    except json.JSONDecodeError:
        return []

    out: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict) and "start" in item and "end" in item:
            out.append({"start": str(item.get("start", "")).strip(), "end": str(item.get("end", "")).strip()})
    return [b for b in out if b["start"] and b["end"]]


def break_display_lines_from_json(breaks_json: str) -> list[str]:
    """
    Devuelve textos listos para QListWidget (capa de deserialización, sin tocar UI).

    Evita que el widget acceda con subscripts a dicts crudos del JSON.
    """
    lines: list[str] = []
    for brk in load_breaks_list(breaks_json):
        start, end = brk["start"], brk["end"]
        lines.append(f"{start} - {end}")
    return lines


def normalize_holidays(holidays_json: str) -> list[dict[str, str]]:
    """Normaliza holidays legacy (list[str] o list[dict]) a list[dict{date,desc}]."""
    from core.holidays_config_io import normalize_holidays_json

    return normalize_holidays_json(holidays_json)


def holidays_dates(normalized: list[dict[str, str]]) -> list[str]:
    """Extrae `date` de la lista normalizada."""
    from core.holidays_config_io import iter_holiday_dates_iso

    return iter_holiday_dates_iso(normalized)


def dump_json(data: Any) -> str:
    """Serializa JSON de forma consistente."""
    return json.dumps(data, ensure_ascii=False)
