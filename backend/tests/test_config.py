"""Strict-parsing tests for the file-backed feature flag configuration."""

import json
from pathlib import Path

import pytest

from assetops_backend.config import (
    DEFAULT_CONFIG_PATH,
    ConfigurationError,
    load_feature_flags,
    parse_feature_flags,
)


def write_config(tmp_path: Path, document: object) -> Path:
    path = tmp_path / "app-config.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_repository_configuration_file_parses() -> None:
    flags = load_feature_flags()

    assert isinstance(flags.simulator_lab_enabled, bool)
    assert DEFAULT_CONFIG_PATH.is_file()


@pytest.mark.parametrize("enabled", [True, False])
def test_both_flag_states_load(tmp_path: Path, enabled: bool) -> None:
    path = write_config(tmp_path, {"simulator_lab": {"enabled": enabled}})

    assert load_feature_flags(path).simulator_lab_enabled is enabled


def test_missing_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_feature_flags(tmp_path / "absent.json")


def test_invalid_json_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "app-config.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="not valid JSON"):
        load_feature_flags(path)


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ([], "must be an object"),
        ({}, "Missing 'simulator_lab' section"),
        ({"simulator_lab": {}}, "Missing 'simulator_lab.enabled'"),
        ({"simulator_lab": True}, "must be an object"),
        ({"simulator_lab": {"enabled": "true"}}, "must be a boolean"),
        ({"simulator_lab": {"enabled": 1}}, "must be a boolean"),
        ({"simulator_lab": {"enabled": None}}, "must be a boolean"),
        ({"simulator_lab": {"enabled": False, "extra": 1}}, "Unknown 'simulator_lab' keys"),
        ({"simulator_lab": {"enabled": False}, "other": 1}, "Unknown configuration keys"),
    ],
)
def test_strict_parsing_rejects_invalid_documents(document: object, message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        parse_feature_flags(document)
