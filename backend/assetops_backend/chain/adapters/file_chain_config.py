"""File reader for the declared chain config (coverage policy, operating calendar, thread lifecycle).

The schema validation lives in ``chain/policy.py``; this adapter only reads the
JSON file. The shipped files are read once per process.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from assetops_backend.chain.policy import (
    ChainConfigError,
    CoveragePolicy,
    OperatingCalendar,
    parse_coverage_policy,
    parse_operating_calendar,
)
from assetops_backend.chain.lifecycle import LifecyclePolicy, parse_thread_lifecycle

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_POLICY_PATH = REPO_ROOT / "config" / "chain" / "coverage-policy-v1.json"
DEFAULT_CALENDAR_PATH = REPO_ROOT / "config" / "chain" / "operating-calendar-v1.json"
DEFAULT_REGISTER_PATH = REPO_ROOT / "config" / "chain" / "event-register-v1.yaml"  # CH-1b
DEFAULT_LIFECYCLE_PATH = REPO_ROOT / "config" / "chain" / "thread-lifecycle-v1.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ChainConfigError(f"{path}: cannot read: {exc}") from exc
    if not isinstance(payload, dict):
        raise ChainConfigError(f"{path}: top level must be an object")
    return payload


def load_coverage_policy(path: Path | str | None = None) -> CoveragePolicy:
    if path is None:
        return _default_policy()
    return parse_coverage_policy(_read_json(Path(path)), str(path))


def load_operating_calendar(path: Path | str | None = None) -> OperatingCalendar:
    if path is None:
        return _default_calendar()
    return parse_operating_calendar(_read_json(Path(path)), str(path))


@lru_cache(maxsize=1)
def _default_policy() -> CoveragePolicy:
    return parse_coverage_policy(_read_json(DEFAULT_POLICY_PATH), str(DEFAULT_POLICY_PATH))


@lru_cache(maxsize=1)
def _default_calendar() -> OperatingCalendar:
    return parse_operating_calendar(_read_json(DEFAULT_CALENDAR_PATH), str(DEFAULT_CALENDAR_PATH))


def load_event_register(path: Path | str | None = None):
    """CH-1b: the declared event register (YAML), validated by ``chain/events.py``."""
    if path is None:
        return _default_register()
    return _register(Path(path))


def _register(path: Path):
    import yaml

    from assetops_backend.chain.events import parse_register

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ChainConfigError(f"{path}: cannot read: {exc}") from exc
    return parse_register(payload, str(path))


@lru_cache(maxsize=1)
def _default_register():
    return _register(DEFAULT_REGISTER_PATH)


def load_thread_lifecycle(path: Path | str | None = None) -> LifecyclePolicy:
    """CH-3 §1: the declared thread-lifecycle policy (OD-2 close-after days, inconclusive expiry, clean-day measures)."""
    if path is None:
        return _default_lifecycle()
    return parse_thread_lifecycle(_read_json(Path(path)), str(path))


@lru_cache(maxsize=1)
def _default_lifecycle() -> LifecyclePolicy:
    return parse_thread_lifecycle(_read_json(DEFAULT_LIFECYCLE_PATH), str(DEFAULT_LIFECYCLE_PATH))


@lru_cache(maxsize=1)
def load_prebuilt_routes():
    """CH-5c Q8 (CH5c-R6: read below the port): `config/chain/prebuilt-routes-v1.json`, parsed by `chain.prebuilt`."""
    from assetops_backend.chain.prebuilt import CONFIG_NAME, parse

    return parse(_read_json(REPO_ROOT / "config" / "chain" / CONFIG_NAME))


@lru_cache(maxsize=None)
def read_module_source(module: str) -> str | None:
    """CH-5b1 (CH5b1-R Q1): a producer module's source text for the graph check's emitter test; None if not found."""
    import importlib.util

    spec = importlib.util.find_spec(module)
    if spec is None or not spec.origin or not spec.origin.endswith(".py"):
        return None
    return Path(spec.origin).read_text(encoding="utf-8")
