# -*- coding: utf-8 -*-
"""Tests unitarios para constantes de la ventana de arranque."""
import pytest

from ui.startup_screen_constants import AUTO_ADVANCE_SECONDS, STATUS_COLORS


pytestmark = pytest.mark.unit


def test_status_colors_has_expected_keys():
    """STATUS_COLORS define los tres estados de verificación."""
    assert set(STATUS_COLORS) == {"STABLE", "WARNING", "CRITICAL"}


def test_status_colors_each_value_is_tuple_of_three():
    """Cada valor es (color_hex, icono, etiqueta)."""
    for key in ("STABLE", "WARNING", "CRITICAL"):
        val = STATUS_COLORS[key]
        assert isinstance(val, tuple)
        assert len(val) == 3
        assert val[0].startswith("#")
        assert isinstance(val[1], str)
        assert isinstance(val[2], str)


def test_auto_advance_seconds_positive():
    """AUTO_ADVANCE_SECONDS es un entero positivo."""
    assert isinstance(AUTO_ADVANCE_SECONDS, int)
    assert AUTO_ADVANCE_SECONDS == 3
