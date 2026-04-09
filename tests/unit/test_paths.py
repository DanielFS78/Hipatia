# -*- coding: utf-8 -*-
"""Tests para ``core.paths`` (raíz escribible y config usuario en frozen)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

from core.paths import get_writable_app_root, resolve_user_config_ini

pytestmark = pytest.mark.unit


def test_get_writable_app_root_not_frozen():
    root = get_writable_app_root()
    assert (root / "core" / "paths.py").is_file()


def test_get_writable_app_root_frozen(monkeypatch, tmp_path):
    exe = tmp_path / "App.exe"
    exe.write_text("x", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    assert get_writable_app_root() == exe.parent.resolve()


def test_resolve_user_config_ini_dev_uses_bundle_fn(tmp_path, monkeypatch):
    def fake_rp(rel: str) -> str:
        return str(tmp_path / rel.replace("/", os.sep))

    ini = tmp_path / "config" / "config.ini"
    ini.parent.mkdir(parents=True, exist_ok=True)
    ini.write_text("[Connection]\n", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", False, raising=False)
    out = resolve_user_config_ini(fake_rp)
    assert out == str(ini)


def test_resolve_user_config_ini_frozen_copies_once(monkeypatch, tmp_path):
    bundle_dir = tmp_path / "meipass"
    bundled = bundle_dir / "config" / "config.ini"
    bundled.parent.mkdir(parents=True, exist_ok=True)
    bundled.write_text("[Connection]\nmode=sqlite\n", encoding="utf-8")

    exe_dir = tmp_path / "dist"
    exe_dir.mkdir(parents=True, exist_ok=True)
    exe = exe_dir / "Hipatia.exe"
    exe.write_text("", encoding="utf-8")

    def fake_rp(rel: str) -> str:
        return str(bundle_dir / rel.replace("/", os.sep))

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))

    out1 = resolve_user_config_ini(fake_rp)
    user_ini = Path(out1)
    assert user_ini.is_file()
    assert user_ini.read_text(encoding="utf-8") == bundled.read_text(encoding="utf-8")

    bundled.write_text("[Connection]\nmode=postgresql\n", encoding="utf-8")
    out2 = resolve_user_config_ini(fake_rp)
    assert out2 == out1
    assert user_ini.read_text(encoding="utf-8") == "[Connection]\nmode=sqlite\n"
