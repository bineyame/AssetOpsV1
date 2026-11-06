"""DD-1a1 (DD1a1-R3 Q2, L2, own `*_test` DB): the Kobo scenarios of the v2 day list drafted on the registered demo
Kobo Site, and the night probes S and O re-run on it.

The Site is made the way the demo prepare makes it (`tools/demo_combined_kobo.py` `build`): import, convert, then
`configure_at` (S3 generator values, roles-3, supply uses, roles-4). Every draft uses the prepare's model profile and
publication profile (`d-verification-window-v3.json`, mini-grid v6 at 5 min).

- `test_every_v2_kobo_scenario_drafts_on_the_registered_site`: READY or BLOCKED (with reasons) per file; the test fails
  on any BLOCKED. It prints the table the packet quotes, including the profile `mill-midday` runs on.
- `test_night_probes_on_the_registered_site_equal_the_handover`: probes S and O through the registered drafter equal
  the committed `kobo-night-handover-v1.json` (ids and intervals aside: the registered runs sit after the Site's
  install, so the drafter shifts the probe day by `SHIFT`). It prints the frozen policy facts that differ between
  the template Site and the registered Site, if any.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
CONVERSIONS = ROOT / "backend" / "conversions"
SCENARIOS = ROOT / "config" / "scenarios"
MANIFEST = json.loads((CONVERSIONS / "d-verification-window-v3.json").read_text(encoding="utf-8"))
IMPORT_AT = datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc)
INSTALL_AT = IMPORT_AT + timedelta(hours=1)
KNOWN_AT = "2026-10-08T00:00:00Z"
SHIFT = timedelta(days=28)  # the probe day 2026-09-22 -> 2026-10-20, after the registered Site's install
DAY = "2026-10-20"
#: DD1a1-R2/R3 files with their UTC hours on a local day D (UTC+3): (start, end, end on the next day).
NEW_FILES = {
    "kobo-steady-day": ("03:00", "15:00", False), "kobo-steady-afternoon": ("11:00", "17:00", False),
    "kobo-steady-dusk": ("15:00", "17:00", False), "kobo-night-late": ("17:00", "21:00", False),
    "kobo-night-early": ("21:00", "03:00", True), "kobo-night-late-after-overcast": ("17:00", "21:00", False),
    "kobo-night-early-after-overcast": ("21:00", "03:00", True),
}

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


@pytest.fixture(scope="module")
def registered():
    import pg_harness
    import test_s1_bindings_postgres as pgb

    import demo_combined_kobo as dk
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    pg_harness.fresh_database()
    store = PostgresFoundationStore(URL)
    result = pgb.imported(store, when=IMPORT_AT)
    pgb.convert(store, pgb.BindingService(store, pgb.Clock(INSTALL_AT)), result.tenant, result.site, pgb.FIXTURE)
    dk.configure_at(store, result, INSTALL_AT)
    yield store


def _draft(store, doc: dict, start: str, end: str):
    """`test_s6_verification_replay._draft` with a scenario document instead of a shipped id, and no READY assert."""
    import test_s6_verification_publication as pub
    import test_s6_verification_replay as rp
    from assetops_backend.runs.profiles import REGISTERED_KOBO_PUBLICATION_PROFILE_V5

    reg = pub.registered
    scenario = reg.parse_scenario_document(copy.deepcopy(doc), source=doc["scenario_id"], origin="SHIPPED")
    known = reg.Clock(rp._at(KNOWN_AT))
    service = reg.RunSetupService(
        reg.FakeRuns(), reg.FakeSites(()), reg.FakeScenarios((scenario,)),
        model_profiles=(rp._model(MANIFEST),),
        publication_profiles=(pub.REGISTERED_KOBO_PUBLICATION_PROFILE_V3, pub.V4, REGISTERED_KOBO_PUBLICATION_PROFILE_V5),
        now=lambda: KNOWN_AT, registered_bases=reg.RegisteredLabBasis(reg.ImportedSiteRegistry(
            reg.FoundationService(store, "demo", known))))
    foundation = reg.FoundationService(store, "demo", known)
    tenant = foundation.tenant()
    view = foundation.read(foundation.site(tenant, MANIFEST["site_code"]), tenant, rp._at(start), None)
    return service.create_draft_run(reg.request(
        foundation_version=view.revision.version, scenario_id=scenario.scenario_id,
        scenario_version=scenario.version.scenario_version, interval={"start_time": start, "end_time": end},
        timestep_minutes=MANIFEST["timestep_minutes"], seed=MANIFEST["runs"]["baseline"]["seed"],
        model_profile=MANIFEST["model_profile"], publication_profile=MANIFEST["publication_profile"]))


def _shifted(store):
    def draft(doc: dict, start: str, end: str):
        move = lambda t: (datetime.fromisoformat(t.replace("Z", "+00:00")) + SHIFT).strftime("%Y-%m-%dT%H:%M:%SZ")
        return _draft(store, doc, move(start), move(end))
    return draft


def _v2_kobo_files() -> dict:
    """scenario id -> (version, start, end) for every Kobo kind of the day list plus the DD-1a1 files."""
    days = json.loads((CONVERSIONS / "demo-story-days-v2.json").read_text(encoding="utf-8"))
    files = {}
    for kind, k in days["kinds"]["kobo"].items():
        if "scenario_id" in k:
            def at(text):
                day, hhmm = text.split()
                d = datetime.fromisoformat(DAY) + timedelta(days=int(day[1:-1]))
                return f"{d:%Y-%m-%d}T{hhmm}:00Z"
            files.setdefault((k["scenario_id"], k["scenario_version"], kind), (at(k["start"]), at(k["end"])))
    for sid, (lo, hi, nxt) in NEW_FILES.items():
        files[(sid, 1, sid)] = (f"{DAY}T{lo}:00Z", f"{'2026-10-21' if nxt else DAY}T{hi}:00Z")
    return files


def test_every_v2_kobo_scenario_drafts_on_the_registered_site(registered) -> None:
    profile = MANIFEST["model_profile"]
    rows, blocked = [], []
    for (sid, version, kind), (start, end) in sorted(_v2_kobo_files().items()):
        doc = yaml.safe_load((SCENARIOS / f"{sid}.yaml").read_text(encoding="utf-8"))
        assert doc["version"]["scenario_version"] == version, (sid, version)
        run = _draft(registered, doc, start, end)
        reasons = [(r.kind, r.subject) for r in run.blocking_reasons]
        rows.append(f"{kind:32} {sid}@{version} {start[11:16]}-{end[11:16]}Z "
                    f"{profile['profile_id']} v{profile['profile_version']}: "
                    f"{'READY' if run.execution_status == 'READY' else 'BLOCKED ' + str(reasons)}")
        if run.execution_status != "READY":
            blocked.append(rows[-1])
    print("\nDD1a1-R3 registered-Site dry run (prepare day_manifest uses MANIFEST_V3 model_profile for every kind):")
    print("\n".join(rows))
    assert any(kind == "mill-midday" for _, _, kind in _v2_kobo_files()), "the v1 Kobo kinds were not read"
    assert not blocked, blocked


def _facts(run) -> dict:
    from execution_adapter import frozen_world_inputs

    inputs = frozen_world_inputs(run)
    out = {}
    for f in dataclasses.fields(inputs):
        if f.name in ("run_id", "site_id", "foundation_version"):
            continue
        out[f.name] = repr(getattr(inputs, f.name))
    return out


def test_night_probes_on_the_registered_site_equal_the_handover(registered) -> None:
    import probe_kobo_nights as probe

    draft = _shifted(registered)
    measured = probe.build(draft)
    committed = json.loads(probe.derive.HANDOVER.read_text(encoding="utf-8"))
    strip = lambda d: {k: v for k, v in d.items() if k not in ("probe_id", "interval")}
    got = {k: strip(v) for k, v in measured["probes"].items()}
    want = {k: strip(v) for k, v in committed["probes"].items()}
    got_h = {k: strip(v) for k, v in measured["handover"].items()}
    want_h = {k: strip(v) for k, v in committed["handover"].items()}
    template = probe.template_draft(probe.probe_s(), "2026-09-22T03:00:00Z", "2026-09-22T17:00:00Z")
    on_site = draft(probe.probe_s(), "2026-09-22T03:00:00Z", "2026-09-22T17:00:00Z")
    a, b = _facts(template), _facts(on_site)
    differ = {k: (a[k][:300], b[k][:300]) for k in a if a[k] != b.get(k)}
    print("\nDD1a1-R3 registered probes:", json.dumps(got, indent=1, default=str))
    print("frozen world inputs differing (template, registered):", json.dumps(differ, indent=1))
    assert got == want and got_h == want_h, (got, got_h)
