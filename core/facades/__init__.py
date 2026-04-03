# -*- coding: utf-8 -*-
"""Fachadas de aplicación por dominio (encima de servicios / repos)."""

from __future__ import annotations

from core.facades.planning_facade import PlanningFacade
from core.facades.product_facade import ProductFacade

__all__ = ["PlanningFacade", "ProductFacade"]
