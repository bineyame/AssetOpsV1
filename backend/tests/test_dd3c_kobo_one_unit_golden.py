"""DD3c (D-DD.113, D-DD.117, D-DD.118): one-unit Sites stay byte-identical to main through every reader DD3c
changes. The golden `fixtures/dd3c/kobo-one-unit-golden.json` was captured by `capture()` below running on main's
code (detached worktree at the commit named in `captured_on`) BEFORE DD3c parts 3 and 4 changed the cost check and
the litres split. The cases are the Kobo-shape pure fixtures the existing tests already pin (one generator, one PV,
one fuel tank): dispatch_v3 (S3's feed), verification's window evidence and modelled cost check (S6's window), the
night text (K5's F0 nights), and Kobo's October litres month (4d's `kobo()` world).

Capture: `PYTHONPATH=<main>/backend:<main>/backend/tests python -c "import runpy;
runpy.run_path('<this file>')['write']('<golden path>', '<main sha>')"`.
"""

from __future__ import annotations

import dataclasses
import enum
import itertools
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from uuid import UUID

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "dd3c" / "kobo-one-unit-golden.json"


def _plain(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, (dict, MappingProxyType)):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_plain(v) for v in value]
        return sorted(items, key=json.dumps) if isinstance(value, (set, frozenset)) else items
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (Fraction, Decimal, datetime, date, UUID, timedelta)):
        return f"{type(value).__name__}:{value}"
    return value


def _ids(*modules):
    """Deterministic uuid4 in the fixture modules (their ids enter the outputs)."""
    counter = itertools.count(1000)
    for m in modules:
        m.uuid4 = lambda: UUID(int=next(counter))


def _dispatch() -> dict:
    import test_s3_dispatch_v3_analytic as s3
    _ids(s3)
    out = {}
    for name, feed in (("pv_alone", s3.run_interval(s3.Feed(), 5, 6, pv=s3.PV_ALONE)),
                       ("default_run", s3.run_interval(s3.Feed(), 5, 6)),
                       ("near_reserve", s3.run_interval(s3.Feed(), 5, 6, soc="31"))):
        inputs, result = s3.run(feed)
        out[name] = {"input_sha256": inputs.input_sha256, "result": _plain(result)}
    return out


def _cost_check(baseline_kw: str, later_kw: str) -> dict:
    """`VerificationService._cost_check` over S6 windows, one generator, through fakes of its ports."""
    import test_s6_verification_rules as s6
    from assetops_backend.actions import verification_rules as vr
    from assetops_backend.actions.verification import VerificationService
    from assetops_backend.financials.fuel_cost import PriceSelection
    from assetops_backend.financials.trial_fuel_comparison import NoLoadValue
    from assetops_backend.mini_depth.rules import SfcValue

    t0, t1 = s6.T0, s6.T0 + timedelta(days=1)
    windows = {"baseline": vr.window_evidence(t0, s6.full_window(t0, gen_kw=baseline_kw), load_asset_ids=[
        "load-a", "load-b"], critical_load_asset_id="crit", reserves=s6.RESERVE),
        "later": vr.window_evidence(t1, s6.full_window(t1, gen_kw=later_kw), load_asset_ids=[
            "load-a", "load-b"], critical_load_asset_id="crit", reserves=s6.RESERVE)}
    since = t0 - timedelta(days=30)
    sfc = [SfcValue(UUID(int=51), Decimal("0.355"), since, None)]
    rates = [NoLoadValue(UUID(int=52), Decimal("3.3"), since, None, "GENERIC_DEFAULT")]
    appended = []
    store = SimpleNamespace(append=lambda row: (appended.append(row), (row, True))[1])
    price = PriceSelection("PRICED", None, "price-1", Decimal("1.25"), "USD")
    trial = SimpleNamespace(store=store, price_selection=lambda *a: price)
    action_store = SimpleNamespace(sfc_history=lambda t, s, g, lo, hi, now: sfc if g == "gen" else [],
                                   no_load_history=lambda t, s, g, lo, hi, now: rates if g == "gen" else [])
    actions = SimpleNamespace(store=action_store, clock=lambda: t1 + timedelta(days=2),
                              verification_ports=SimpleNamespace(trial_comparison=trial, provenance=None))
    svc = VerificationService(actions)
    svc._window_replay = lambda *a: (windows, {"state": "PASS"}, {"state": "PASS"})
    plan = {"id": UUID(int=61), "baseline_start": t0, "baseline_end": t0 + vr.WINDOW, "later_start": t1,
            "later_end": t1 + vr.WINDOW, "basis": {"baseline_bindings": {"role_assets": {"generator_power": ["gen"]}}}}
    outcome = {"id": UUID(int=62), "action_id": UUID(int=63), "outcome": "VERIFIED",
               "basis": {"origin_finding_revision_id": UUID(int=64),
                         "evidence_ids": {n: windows[n]["evidence_ids"] for n in ("baseline", "later")}}}
    request = {k: None for k in ("actor_kind", "actor_id", "source_channel", "authorization_basis",
                                 "triggering_service", "triggering_fixture")}
    svc._cost_check(UUID(int=65), UUID(int=66), plan, outcome, request)
    [row] = appended
    return {"windows": _plain(windows), "row": _plain({k: v for k, v in row.items() if k != "recorded_at"})}


def _verification() -> dict:
    return {"improvement": _cost_check("20", "10"), "no_improvement": _cost_check("10", "20"),
            "idle": _cost_check("0", "10")}


def _night_text() -> dict:
    import test_k5_fuel_night_text as k5
    from assetops_backend.fuel_balance import night_text as nt
    _ids(k5)
    out = {}
    for i in range(4):
        out[f"night{i + 1}"] = _plain(nt.night_view(k5.probe_window(i), [], k5.TZ))
    out["night4_gap_idle"] = _plain(nt.night_view(k5.probe_window(3, spans=k5.GAP, limitations=("REPORTING_GAP",),
                                                                   idle_seconds=1800), [], k5.TZ))
    return out


def _litres() -> dict:
    import test_4d_litre_split as d4
    month = d4.run(d4.kobo())
    idle = d4.kobo()
    idle.idle = {d4.local(2026, 10, 3, 6, 0).astimezone(d4.UTC) + d4.SLOT * i for i in range(6)}
    return {"kobo_october": _plain(month), "kobo_october_idle": _plain(d4.run(idle))}


def capture() -> dict:
    return {"dispatch": _dispatch(), "verification": _verification(), "night_text": _night_text(),
            "litres": _litres()}


def write(path: str, captured_on: str) -> None:
    Path(path).write_text(json.dumps({"captured_on": captured_on, "cases": capture()}, indent=1, sort_keys=True)
                          + "\n", encoding="utf-8")


def test_one_unit_kobo_outputs_are_byte_identical_to_main() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    now = capture()
    for part in ("dispatch", "verification", "night_text", "litres"):
        assert json.dumps(now[part], sort_keys=True) == json.dumps(golden["cases"][part], sort_keys=True), part
