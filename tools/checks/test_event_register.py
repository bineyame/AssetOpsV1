"""CH-1b register guard (build sheet CH-1b §2; ruling CH1b-R D1): the event register is reviewed as code.

    python -m pytest tools/checks/test_event_register.py

`problems()` checks the declared register `config/chain/event-register-v1.yaml` against the code it mirrors:

- every `MeasureSpec` in `chain/measures.py` has an `inputs` entry, and every entry names an existing measure;
- every role is a role of a role set the measure's Site type serves (`sites/binding_roles.py`);
- every analytic id, job domain, mini-depth domain and assumption key exists in the code that writes it;
- every event type the 0044 producers write has a register rule (an unregistered event would be dropped silently);
- every register event type has a resolution fixture in `backend/tests/test_ch1b_register.py` (`EVENT_FIXTURES`).

Each rule has a failing mutation below, so the guard cannot pass vacuously. `tools/check-all.ps1` runs this file.
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
for _p in ("backend", "contracts"):
    if str(ROOT / _p) not in sys.path:
        sys.path.insert(0, str(ROOT / _p))

from assetops_backend.analytics import cold, dispatch, ev  # noqa: E402
from assetops_backend.chain.events import parse_register  # noqa: E402
from assetops_backend.chain.measures import MEASURES  # noqa: E402
from assetops_backend.financials.assumptions import ASSUMPTION_KEYS  # noqa: E402
from assetops_backend.mini_depth.store import DOMAINS as MINI_DEPTH_DOMAINS  # noqa: E402
from assetops_backend.mini_depth.store import JOB_DOMAIN as MINI_JOB_DOMAIN  # noqa: E402
from assetops_backend.sites.binding_roles import ROLES_BY_SET, SERVED_ROLE_SETS_BY_SITE_TYPE  # noqa: E402

REGISTER = ROOT / "config" / "chain" / "event-register-v1.yaml"
MIGRATION = ROOT / "backend" / "migrations" / "versions" / "0044_chain_events.py"
FIXTURES = ROOT / "backend" / "tests" / "test_ch1b_register.py"

ANALYTIC_IDS = frozenset({dispatch.ANALYTIC_ID, cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC,
                          ev.SESSION_ANALYTIC})
JOB_DOMAINS = frozenset({"dispatch", cold.DOMAIN, ev.DOMAIN, "mini_opportunity", *MINI_JOB_DOMAIN.values()})
#: The event types written outside the 0044 producers: the backfill's provenance event (ruling CH1b-R Q2).
NON_TRIGGER_TYPES = frozenset({"backfill.site@1"})


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def produced_types() -> frozenset[str]:
    migration = _module(MIGRATION, "_ch1b_migration_0044")
    return frozenset(f"{spec[0]}@1" for spec in migration.PRODUCERS.values())


def fixture_types() -> frozenset[str]:
    return frozenset(_module(FIXTURES, "_ch1b_register_fixtures").EVENT_FIXTURES)


def _roles(site_type: str) -> frozenset[str]:
    return frozenset(r.role for s in SERVED_ROLE_SETS_BY_SITE_TYPE.get(site_type, ()) for r in ROLES_BY_SET[s])


def problems(payload, measures=MEASURES, produced=None, fixtures=None) -> list[str]:
    produced = produced_types() if produced is None else produced
    fixtures = fixture_types() if fixtures is None else fixtures
    register = parse_register(payload, "event register")
    out: list[str] = []
    for key in sorted(set(measures) - set(register.inputs)):
        out.append(f"measure {key} has no inputs entry")
    for key in sorted(set(register.inputs) - set(measures)):
        out.append(f"inputs.{key} names no measure")
    for key, rule in sorted(register.inputs.items()):
        spec = measures.get(key)
        if spec is None:
            continue
        if not (rule.roles or rule.analytics or rule.mini_depth or rule.job_domains or rule.assumption_keys
                or rule.foundation):
            out.append(f"inputs.{key} names no source, so no event ever marks it dirty")
        for role in sorted(rule.roles - _roles(spec.site_type)):
            out.append(f"inputs.{key}: role {role} is not a {spec.site_type} role")
        for name in sorted(rule.analytics - ANALYTIC_IDS):
            out.append(f"inputs.{key}: analytic {name} is not an analytic id")
        for name in sorted(rule.job_domains - JOB_DOMAINS):
            out.append(f"inputs.{key}: job domain {name} is not a recompute-job domain")
        for name in sorted(rule.mini_depth - set(MINI_DEPTH_DOMAINS)):
            out.append(f"inputs.{key}: mini-depth domain {name} does not exist")
        for name in sorted(rule.assumption_keys - set(ASSUMPTION_KEYS)):
            out.append(f"inputs.{key}: assumption key {name} does not exist")
    for key in sorted(produced - set(register.events)):
        out.append(f"event {key} is written by the 0044 producers but has no register rule")
    for key in sorted(set(register.events) - produced - NON_TRIGGER_TYPES):
        out.append(f"event {key} has a register rule but no producer")
    for key in sorted(set(register.events) - fixtures):
        out.append(f"event {key} has no resolution fixture in {FIXTURES.name}")
    return out


def _payload() -> dict:
    return yaml.safe_load(REGISTER.read_text(encoding="utf-8"))


def test_live_register_is_clean() -> None:
    assert problems(_payload()) == []


def _drop_input(p: dict) -> None:
    del p["inputs"]["charging_kwh"]


def _empty_input(p: dict) -> None:
    p["inputs"]["charging_kwh"] = {}  # review L1: an entry with every key empty and foundation false


def _unknown_measure(p: dict) -> None:
    p["inputs"]["phantom_kwh"] = {"roles": ["feeder_demand"]}


def _wrong_role(p: dict) -> None:
    p["inputs"]["chamber_temp_c"]["roles"] = ["feeder_demand"]  # a mini-grid role on a cold measure


def _job_domain_as_analytic(p: dict) -> None:
    p["inputs"]["chamber_temp_c"]["analytics"] = ["cold_chain"]  # D1: a job domain is not an analytic id


def _unknown_job_domain(p: dict) -> None:
    p["inputs"]["avoidable_gen_min"]["job_domains"] = ["mini_dispatch"]


def _unknown_mini_depth(p: dict) -> None:
    p["inputs"]["daylight_headroom_kw"]["mini_depth"] = ["solar"]


def _unknown_key(p: dict) -> None:
    p["inputs"]["productive_kwh"]["assumption_keys"] = ["productive_price"]


def _unregistered_event(p: dict) -> None:
    del p["events"]["price.revised@1"]


def _unproduced_event(p: dict) -> None:
    p["events"]["meter.rotated@1"] = {"days": "none"}


@pytest.mark.parametrize("mutate, expected", [
    (_drop_input, "measure charging_kwh has no inputs entry"),
    (_empty_input, "inputs.charging_kwh names no source, so no event ever marks it dirty"),
    (_unknown_measure, "inputs.phantom_kwh names no measure"),
    (_wrong_role, "inputs.chamber_temp_c: role feeder_demand is not a COLDCHAIN role"),
    (_job_domain_as_analytic, "inputs.chamber_temp_c: analytic cold_chain is not an analytic id"),
    (_unknown_job_domain, "inputs.avoidable_gen_min: job domain mini_dispatch is not a recompute-job domain"),
    (_unknown_mini_depth, "inputs.daylight_headroom_kw: mini-depth domain solar does not exist"),
    (_unknown_key, "inputs.productive_kwh: assumption key productive_price does not exist"),
    (_unregistered_event, "event price.revised@1 is written by the 0044 producers but has no register rule"),
    (_unproduced_event, "event meter.rotated@1 has a register rule but no producer"),
])
def test_each_rule_fails_on_its_mutation(mutate, expected) -> None:
    payload = copy.deepcopy(_payload())
    mutate(payload)
    found = problems(payload)
    assert expected in found, found


def test_missing_fixture_fails() -> None:
    found = problems(_payload(), fixtures=fixture_types() - {"job.changed@1"})
    assert found == ["event job.changed@1 has no resolution fixture in test_ch1b_register.py"], found
