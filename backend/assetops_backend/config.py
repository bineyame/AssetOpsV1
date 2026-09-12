"""File-backed application configuration for the AssetOps backend.

`config/app-config.json` at the repository root is the single source of truth
for `simulator_lab.enabled`. The backend reads it here; the frontend imports the
same file so one edit changes both serving boundaries.

Parsing is strict, matching the contract posture: unknown keys, missing keys and
non-boolean values are rejected loudly instead of being coerced. A silently
mis-parsed gate would either hide the Simulator Lab when it should be served or,
worse, serve simulator surfaces that were meant to be off.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "app-config.json"

_SIMULATOR_LAB_KEY = "simulator_lab"
_ENABLED_KEY = "enabled"


class ConfigurationError(RuntimeError):
    """Raised when application configuration is missing or invalid."""


@dataclass(frozen=True)
class FeatureFlags:
    """Serving-boundary feature flags.

    `simulator_lab_enabled` gates simulator surfaces and execution only. It must
    never be used to gate Site semantics, evidence, provenance, analytics, or
    operator routes.
    """

    simulator_lab_enabled: bool


def load_feature_flags(path: Path | None = None) -> FeatureFlags:
    """Load feature flags from the file-backed configuration."""
    config_path = DEFAULT_CONFIG_PATH if path is None else path

    if not config_path.is_file():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigurationError(
            f"Configuration file is not valid JSON: {config_path}"
        ) from error

    return parse_feature_flags(raw, source=str(config_path))


def parse_feature_flags(raw: Any, *, source: str = "<in-memory>") -> FeatureFlags:
    """Strictly parse a configuration document into feature flags."""
    if not isinstance(raw, dict):
        raise ConfigurationError(f"Configuration root must be an object: {source}")

    unknown_keys = sorted(set(raw) - {_SIMULATOR_LAB_KEY})
    if unknown_keys:
        raise ConfigurationError(
            f"Unknown configuration keys {unknown_keys} in {source}"
        )

    if _SIMULATOR_LAB_KEY not in raw:
        raise ConfigurationError(f"Missing '{_SIMULATOR_LAB_KEY}' section in {source}")

    section = raw[_SIMULATOR_LAB_KEY]
    if not isinstance(section, dict):
        raise ConfigurationError(
            f"'{_SIMULATOR_LAB_KEY}' must be an object in {source}"
        )

    unknown_section_keys = sorted(set(section) - {_ENABLED_KEY})
    if unknown_section_keys:
        raise ConfigurationError(
            f"Unknown '{_SIMULATOR_LAB_KEY}' keys {unknown_section_keys} in {source}"
        )

    if _ENABLED_KEY not in section:
        raise ConfigurationError(
            f"Missing '{_SIMULATOR_LAB_KEY}.{_ENABLED_KEY}' in {source}"
        )

    enabled = section[_ENABLED_KEY]
    # `isinstance(True, int)` is True, so compare the type directly: 0/1 and
    # "false" must not be silently accepted as a gate value.
    if type(enabled) is not bool:
        raise ConfigurationError(
            f"'{_SIMULATOR_LAB_KEY}.{_ENABLED_KEY}' must be a boolean in {source}"
        )

    return FeatureFlags(simulator_lab_enabled=enabled)
