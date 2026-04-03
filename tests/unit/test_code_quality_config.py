# -*- coding: utf-8 -*-
"""Tests de configuración de calidad de código: .pre-commit-config.yaml, .flake8, pyproject.toml."""
import os
import yaml  # type: ignore[import-untyped]
import pytest
import configparser

pytestmark = pytest.mark.unit


def test_pre_commit_config_exists():
    """Verify that .pre-commit-config.yaml exists and is valid YAML."""
    config_path = ".pre-commit-config.yaml"
    assert os.path.exists(config_path), f"{config_path} not found"
    
    with open(config_path, "r") as f:
        try:
            config = yaml.safe_load(f)
            assert isinstance(config, dict)
            assert "repos" in config
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {config_path}: {e}")

def test_flake8_config_exists():
    """Verify that .flake8 exists and is valid INI."""
    config_path = ".flake8"
    assert os.path.exists(config_path), f"{config_path} not found"
    
    config = configparser.ConfigParser()
    try:
        config.read(config_path)
        assert "flake8" in config
        assert config["flake8"].get("max-line-length") == "88"
    except configparser.Error as e:
        pytest.fail(f"Invalid INI in {config_path}: {e}")

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists and contains black config."""
    config_path = "pyproject.toml"
    assert os.path.exists(config_path), f"{config_path} not found"
    
    # Simple content check since tomllib is 3.11+ and toml package might not be installed in test env
    with open(config_path, "r") as f:
        content = f.read()
        assert "[tool.black]" in content
        assert "line-length = 88" in content
