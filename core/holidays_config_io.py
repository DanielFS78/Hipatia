# -*- coding: utf-8 -*-
"""
Nombre del Módulo: holidays_config_io
Descripcion: Normalizacion y consultas sobre la lista de festivos en configuracion,
             fuera de la capa ui (Fase 12C).
"""

from __future__ import annotations

import json
from typing import Any


def normalize_holidays_json(holidays: Any) -> list[dict[str, str]]:
    """Convierte JSON/str/lista heterogenea en lista deduplicada de dicts date/desc."""
    try:
        if isinstance(holidays, str):
            raw = json.loads(holidays)
        else:
            raw = holidays
        if not isinstance(raw, list):
            raw = []
    except Exception:
        raw = []

    normalized: list[dict[str, str]] = []
    for h in raw:
        if isinstance(h, str):
            normalized.append({"date": h, "desc": ""})
        elif isinstance(h, dict) and "date" in h:
            normalized.append(
                {"date": str(h.get("date", "")), "desc": str(h.get("desc", ""))}
            )

    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for h in normalized:
        date = h.get("date", "").strip()
        if not date or date in seen:
            continue
        seen.add(date)
        out.append({"date": date, "desc": h.get("desc", "").strip()})
    return out


def holiday_dates_set(entries: list[dict[str, str]]) -> set[str]:
    """Conjunto de fechas ISO ya normalizadas."""
    return {e["date"] for e in entries if e.get("date")}


def holidays_without_date(entries: list[dict[str, str]], date_str: str) -> list[dict[str, str]]:
    """Copia sin la entrada con la fecha dada."""
    return [e for e in entries if e.get("date") != date_str]


def iter_holiday_dates_iso(entries: list[dict[str, str]]) -> list[str]:
    """Lista ordenada de fechas para resaltar en calendario."""
    out: list[str] = []
    for e in entries:
        d = e.get("date")
        if d:
            out.append(str(d))
    return out
