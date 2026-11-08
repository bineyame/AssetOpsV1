"""DIESEL-K6b L2 (build sheet DIESEL-1 §9m.4, ruling DIESEL-1-R3m): `fuel-residual-within-band-1` on Postgres, on its
own `assetops_k6_test`.

Item 5 (the mill path stays byte-equal): the CH-9b fixture's `freeze_domain_plan` / `evaluate_domain_plan` /
`domain_summary` outputs, normalized (ids, digests and instants made relative), equal the pins in
`fixtures/k6b_mill_pins.json`, which were captured on the branch's first commit, before any K6b code existed.
Set `K6B_CAPTURE_PINS=1` to (re)write the pins file instead of comparing (capture only on unchanged mill code).
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

UTC = timezone.utc
PINS = Path(__file__).resolve().parent / "fixtures" / "k6b_mill_pins.json"
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$")
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if URL:
    from sqlalchemy import text
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_ch9b1_opportunity_actions_postgres import mill  # noqa: F401
    from test_ch9b3_mill_verdict_postgres import _after, _close, _frozen, _later, _snap
    from test_s1_bindings_postgres import engine, store  # noqa: F401


class _Norm:
    """Ids, digests and instants made run-independent: a UUID by first-seen order, a digest as `<sha>`, an instant
    as seconds after the plan's `effective_from`, a date as days after the effective day."""

    def __init__(self, effective: datetime, eff_day: date, tz: str) -> None:
        self.effective, self.eff_day, self.ids, self.tz = effective, eff_day, {}, ZoneInfo(tz)

    def __call__(self, v):
        if isinstance(v, dict):
            return {k: self(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [self(x) for x in v]
        if isinstance(v, str):
            if _UUID.match(v):
                return self.ids.setdefault(v, f"<uuid:{len(self.ids)}>")
            if _SHA.match(v):
                return "<sha>"
            if _INSTANT.match(v):
                at = datetime.fromisoformat(v.replace("Z", "+00:00"))
                local = at.astimezone(self.tz)
                if (local.minute, local.second, local.microsecond) == (0, 0, 0):  # a calendar instant (midnight, noon)
                    return f"<d{(local.date() - self.eff_day).days:+d} {local:%H}h>"
                return f"<t{(at - self.effective).total_seconds():+.6f}s>"  # a clock instant: after effective_from
            if _DAY.match(v):
                return f"<d{(date.fromisoformat(v) - self.eff_day).days:+d}>"
            v = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                       lambda m: self.ids.setdefault(m.group(), f"<uuid:{len(self.ids)}>"), v)
            return re.sub(r"\d{4}-\d{2}-\d{2}", lambda m: f"<d{(date.fromisoformat(m.group()) - self.eff_day).days:+d}>",
                          v)
        return v


def _mill_outputs(mill) -> dict:  # noqa: F811
    """The CH-9b3 VERIFIED story (`test_verified_stores_one_domain_outcome...`) through the three mill methods."""
    svc, clock, aid, eff, tz = _frozen(mill, "k6b-mill-pin")
    try:
        replay = svc.freeze_domain_plan(mill.t, mill.s, aid)
        before = svc.domain_summary(mill.t, mill.s, aid)
        not_yet = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        _later(mill, eff, "11.5")
        _snap(mill, eff, "999")
        clock.at = _after(eff, tz, 5)
        judged = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        again = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        after = svc.domain_summary(mill.t, mill.s, aid)
        with mill.engine.connect() as c:
            effective = c.execute(text("SELECT effective_from FROM verification_plan WHERE domain_action_id = :a"),
                                  {"a": aid}).scalar_one().astimezone(UTC)
    finally:
        _close(mill)
    norm = _Norm(effective, eff, tz)
    norm(aid)
    return norm({"freeze_replay": list(replay), "summary_before": before, "evaluate_not_judged": not_yet,
                 "evaluate_judged": judged, "evaluate_replay": again, "summary_after": after})


def test_5_mill_path_outputs_equal_the_first_commit_pins(mill) -> None:  # noqa: F811
    got = json.loads(json.dumps(_mill_outputs(mill), sort_keys=True, default=str))
    if os.environ.get("K6B_CAPTURE_PINS") == "1":
        PINS.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        pytest.skip("pins captured")
    want = json.loads(PINS.read_text(encoding="utf-8"))
    assert got == want, _diff(got, want)


def _diff(a, b, path="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        return [x for k in sorted(set(a) | set(b)) for x in _diff(a.get(k), b.get(k), f"{path}.{k}")]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [x for i, (p, q) in enumerate(zip(a, b)) for x in _diff(p, q, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]
