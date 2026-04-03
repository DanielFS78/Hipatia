# -*- coding: utf-8 -*-
"""Tests para helpers puros de horarios (`schedule_helpers`)."""

from __future__ import annotations

import pytest

from controllers.schedule_helpers import break_display_lines_from_json, load_breaks_list

pytestmark = pytest.mark.unit


def test_break_display_lines_from_json_valid() -> None:
    raw = '[{"start": "12:00", "end": "13:00"}, {"start": "09:30", "end": "09:45"}]'
    assert break_display_lines_from_json(raw) == ["12:00 - 13:00", "09:30 - 09:45"]


def test_break_display_lines_from_json_invalid_json() -> None:
    assert break_display_lines_from_json("not json") == []


def test_break_display_lines_from_json_skips_bad_entries() -> None:
    raw = '[{"start": "10:00", "end": "10:15"}, {"foo": 1}, "x"]'
    assert break_display_lines_from_json(raw) == ["10:00 - 10:15"]


def test_load_breaks_list_strips_strings() -> None:
    raw = '[{"start": " 08:00 ", "end": "08:30"}]'
    assert load_breaks_list(raw) == [{"start": "08:00", "end": "08:30"}]
