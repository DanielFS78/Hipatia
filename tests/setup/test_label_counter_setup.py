# tests/setup/test_label_counter_setup.py
# -*- coding: utf-8 -*-
"""Tests de setup para LabelCounterRepository y modelo FabricacionContador."""
import pytest
from sqlalchemy.orm import Session
from unittest.mock import create_autospec
from typing import Callable, cast
from database.repositories.label_counter_repository import LabelCounterRepository

pytestmark = pytest.mark.setup


class TestLabelCounterSetup:
    
    def test_repository_instantiation(self):
        # Just verify we can instantiate it
        session_factory: Callable[[], Session] = lambda: cast(Session, create_autospec(Session, instance=True))
        repo = LabelCounterRepository(session_factory)
        assert repo is not None
        assert hasattr(repo, 'get_next_unit_range')

    def test_model_exists(self):
        from database.models import FabricacionContador
        assert FabricacionContador.__tablename__ == 'fabricacion_contadores'
