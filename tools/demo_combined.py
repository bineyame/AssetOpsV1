"""DEMO-A: the combined three-Site demo dataset (KOBO-001, COLD-LAB-001, EV-LAB-001) in one private database.

    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main prepare
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main links
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main serve
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main tick
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main add-dates [--site ...] [--from D]
        [--to D|yesterday] [--kind K] [--dry-run] [--no-check]     (OWN-G1: catch the Sites up to yesterday)
    python tools/demo_combined.py --db assetops_demo3_main_test --work var/demo3_main drop

Build sheet: `AssetOpsV1-plan2/.agent/build-sheet-DEMO-COMBINED.md` (rev 1 + Addendum 1). Every story instant comes
from `backend/conversions/demo-combined-story-v1.json` resolved against one story day
S = floor_utc_day(DB now at prepare) - 2 d (written to `<work>/story.json`); nothing reads `datetime.now()` for a
story instant. The data is registered Lab simulation placed on a story calendar plus prepared example work records
(actor `service:w401-fixture`); it is never presented as live operation.

`prepare` (nothing outside the named database and work folder is written):
1. `git archive HEAD` into `<work>/tree` with `var/sites/kobo-001.yaml` only; one database, migrated to head once.
2. The Sites in increasing install instant (Addendum 1 R3): Kobo (`tools/demo_combined_kobo.py`), GreenHarvest
   (`tools/demo_combined_cold.py`), Depot (`tools/demo_combined_ev.py`), each a child process in the tree.
3. Objectives, the S2 Evidence comparison, two schedule ticks, the Performance comparison, the self-check.
`serve` runs `host/lab_app.py` on --port (default 8990) with the cursor keys from `<work>/keys.json`, plus a
walkthrough-only schedule loop (one tick every 120 s, then the Performance comparison) that stops with serve. After
the first tick it pre-warms the story-week Portfolio outcome summary once and prints "ready:" when that returns 2xx.
`drop` removes the database and work folder only when the work folder's marker records this tool made them.

Guards: `--db` must match `^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$`; `--work` must be a `var/demo3*` or
`var/polish*` folder directly under this repository's `var/` (POLISH Addendum 9 Q1). A wall cap of twice the expected time stops only the PIDs this tool started.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import demo_combined_rows as demo_rows
import demo_story_days as sd

REPO = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
PG_ADMIN = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
DB_RE = re.compile(r"^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$")
WORK_PREFIXES = ("demo3", "polish")
MARKER = ".demo3-combined-work"
STORY_FILE = REPO / "backend" / "conversions" / "demo-combined-story-v1.json"
API_PORT, WEB_PORT = 8990, 5490
TICK_EVERY_SECONDS = 120
#: DIESEL-1-R3l §9l.3 (K7): the three core Sites, and Kisiwa as the fourth (K7-F: part of the default prepare,
#: `SITES`). Every loop that means "the three Sites" iterates `CORE_SITES`.
CORE_SITES = ("kobo", "cold", "ev")
SITES = CORE_SITES + ("kisiwa",)
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001", "kisiwa": "KISIWA-001"}
#: Expected wall seconds per step; the cap is twice the sum of the selected steps. Kobo is
#: `kobo_expected_seconds` (DEMO-SPARSE U3 measured about 105 s per Kobo run: 110 s per run + 60 s).
#: DD1b2-R11 O18: `mill` is the measured 18.7 s; `drain` is drain-1 278.4 + drain-2 58.3 = 336.7 s, rounded up to 10 s.
# DIESEL-1-R3n: measured in K7-D's scratch prepare (3568 s build step)
EXPECTED_SECONDS = {"tree": 30, "kobo": 250, "cold": 300, "ev": 200, "kisiwa": 3600, "finish": 90, "mill": 20,
                    "drain": 340, "day_rows": 900}
KISIWA_STORY_FILE = REPO / "backend" / "conversions" / "demo-kisiwa-story-v1.json"
KEY_NAMES = ("ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX", "ASSETOPS_WORK_CURSOR_KEY_HEX")
#: WALK1-2 §3.1: the tariff is recorded at the configuration knowledge instant, `ev.install_at` + 30 min.
TARIFF_AFTER_INSTALL = timedelta(minutes=30)
TICK = ("-m", "assetops_backend.scheduling.run", "tick", "--environment", "default", "--max-sites", "5",
        "--s3-jobs", "10", "--consequence-items", "100")
_OFFSET = re.compile(r"^S([+-]\d+)d (\d{2}):(\d{2})$")


class StoryClockError(SystemExit):
    pass


class PrebuildRefused(SystemExit):
    """INFRA-1 fix round: a DEGRADED/FAILED prebuild. Build paths let it exit; the serve loop and the drain catch it."""


def prebuild_refusal(stdout: str) -> str | None:
    """INFRA-1 (D-E5.47) rule 5: the prebuild's last JSON line with `code` FAILED or DEGRADED gives the message the
    build exits with, naming the paths; any other code (or no JSON line) gives None."""
    lines = [x for x in (stdout or "").splitlines() if x.startswith("{")]
    if not lines:
        return None
    try:
        out = json.loads(lines[-1])
    except ValueError:
        return None
    code = out.get("code")
    if code == "DEGRADED":
        return f"PREBUILD DEGRADED: still degraded {out.get('still_degraded')}; attempts {out.get('degraded')}"
    if code == "FAILED":
        return f"PREBUILD FAILED: non-200 {out.get('non_200')}"
    return None


def kobo_expected_seconds(days_doc: dict) -> int:
    return 110 * sum(1 for e in days_doc["sites"].get("kobo", []) if e["kind"] != "missing") + 60


def say(text: str = "") -> None:
    print(text, flush=True)


def retry_until_visited(report: dict | None, tick_once, site: str = "KISIWA-001", extra: int = 2,
                        pause: float = 30.0, sleep=time.sleep) -> tuple[dict | None, int]:
    """OWN-G2 (R2-G2 Q9 addition, also G1's per-date rule R2-G1 Q6): when `report` has no `fuel_night` stage entry
    for `site`, run up to `extra` more ticks, `pause` seconds apart. Returns the last report and the extra-tick count."""
    ran = 0
    while demo_rows.fuel_night_entry(report, site) is None and ran < extra:
        sleep(pause)
        report = tick_once()
        ran += 1
    return report, ran


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def objectives_instants(story: dict) -> dict[str, datetime]:
    """DD1b1-R2 S3: each Site's objective lines are recorded at that Site's own first declared knowledge instant
    (Kobo `price_recorded_at`; Cold and EV `install_at` + `TARIFF_AFTER_INSTALL`). Each must precede that Site's first
    built day's start; otherwise the prepare stops, never a moved date.
    DATA-6: when the story builds Kisiwa, it declares MG-2 and MG-5 at its `install_at` + `TARIFF_AFTER_INSTALL`,
    which must precede its run 1."""
    instants = {"KOBO-001": at(story["kobo"]["price_recorded_at"]),
                "COLD-LAB-001": at(story["cold"]["install_at"]) + TARIFF_AFTER_INSTALL,
                "EV-LAB-001": at(story["ev"]["install_at"]) + TARIFF_AFTER_INSTALL}
    kisiwa = story.get("kisiwa") if "kisiwa" in (story.get("sites") or ()) else None
    if kisiwa:
        instant = at(kisiwa["install_at"]) + TARIFF_AFTER_INSTALL
        if instant >= at(kisiwa["run1_start"]):
            raise SystemExit(f"OBJECTIVES_INSTANT_CONFLICT: the KISIWA-001 objectives instant {iso(instant)} is not "
                             f"before its run 1 ({kisiwa['run1_start']}).")
        instants["KISIWA-001"] = instant
    for site in CORE_SITES:
        code = SITE_CODE[site]
        built = [d for d in story["days"] if d.get("site") == site and d.get("start")]
        if not built:
            continue
        first = min(built, key=lambda d: at(d["start"]))
        if instants[code] >= at(first["start"]):
            raise SystemExit(f"OBJECTIVES_INSTANT_CONFLICT: the {code} objectives instant {iso(instants[code])} is not "
                             f"before its first built day ({first['day']}, start {first['start']}).")
    return instants


def floor_day(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _resolve(node: Any, S: datetime) -> Any:
    if isinstance(node, dict):
        return {k: _resolve(v, S) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(v, S) for v in node]
    if isinstance(node, str):
        m = _OFFSET.match(node)
        if m:
            return iso(S + timedelta(days=int(m.group(1)), hours=int(m.group(2)), minutes=int(m.group(3))))
    return node


def _trial(kobo: dict, days: list, window_hour: str) -> None:
    """The trial pair's instants (the DEMO-A chain's `runs` and `windows`) from the day list's trial-* kinds."""
    hh, mm = (int(x) for x in window_hour.split(":"))
    for name, kind in (("baseline", "trial-before"), ("later", "trial-after")):
        run = next(r for r in days if r.site == "kobo" and r.kind == kind)
        kobo["runs"][name] = {"start": iso(run.start), "end": iso(run.end), "foundation_known_at": iso(run.known_at),
                              "received_at": iso(run.received_at), "sequence_epoch": run.epoch,
                              "scenario": run.scenario}
        day = at(run.day + "T00:00:00Z")
        kobo["windows"][f"{name}_start"] = iso(day + timedelta(hours=hh, minutes=mm))


def story_day(db_now: datetime, doc: dict | None = None) -> datetime:
    doc = doc or json.loads(STORY_FILE.read_text(encoding="utf-8"))
    return floor_day(db_now) + timedelta(days=doc["story_day_offset_days"])


def resolve_story(db_now: datetime, doc: dict | None = None, days_doc: dict | None = None,
                  kisiwa: bool = False, kisiwa_doc: dict | None = None) -> dict:
    """The story clock: S, every resolved instant, the install clocks and their order, and the day list in build
    order (`days`). Raises `INSTALL_CLOCK_CONFLICT` / `STORY_CLOCK_OUT_OF_RANGE` (Addendum 1 R3) and the day
    list's `StoryDaysError` codes (DEMO-SPARSE U2). With `kisiwa` (K7, opt-in) it adds `story["kisiwa"]`
    (`tools/demo_combined_kisiwa.py` `resolve`) and appends Kisiwa to `install_order`; without it the output is the
    three-Site story, byte-equal (`backend/tests/k7_story_pins.py`)."""
    doc = doc or json.loads(STORY_FILE.read_text(encoding="utf-8"))
    days_doc = days_doc or sd.load()
    S = story_day(db_now, doc)
    story = _resolve({k: v for k, v in doc.items() if k in CORE_SITES}, S)
    kobo = story["kobo"]
    kobo["import_at"] = iso(at(kobo["install_at"]) - timedelta(hours=kobo["import_before_install_hours"]))
    kobo["price_recorded_at"] = iso(at(kobo["install_at"]) + timedelta(hours=kobo["price_after_install_hours"]))
    # DD1a1-R7: the Kobo Action's effective instant is the Foundation revision boundary a complement may not span
    days = sd.resolve(days_doc, S, db_now=db_now, installs={n: at(story[n]["install_at"]) for n in CORE_SITES},
                      revision_boundaries=(at(kobo["action"]["effective_from"]),))
    kobo["runs"], kobo["windows"] = {}, {}
    _trial(kobo, days, days_doc["trial"]["window_hour"])
    kobo["trial"] = dict(days_doc["trial"])
    ev = story["ev"]
    ev["setup_at"] = iso(at(ev["install_at"]) + timedelta(hours=ev["setup_after_install_hours"]))
    ev["day_delta_days"] = (at(ev["e_start"]) - at(ev["base_e_start"])).days
    cold = story["cold"]
    failure = at(cold["failure_night_day"])
    # w502's fixed offsets from the failure night's d16 (OUT-C U3: visits wr_at - 24 d / - 11 d, WR at d16 + 20 min).
    cold["earliest_row_at"] = iso(failure + timedelta(hours=16, minutes=20) - timedelta(days=24))
    earliest = {
        "kobo": min([at(v["at"]) for v in kobo["visits"] + kobo["plans"]] +
                    [r.start for r in days if r.site == "kobo" and r.has_run]),
        "cold": min(at(cold["earliest_row_at"]), at(cold["normal_night_day"]) + timedelta(hours=16)),
        "ev": min([at(v["at"]) for v in ev["visits"] + ev["plans"]] + [at(ev["e_start"])]),
    }
    installs = {name: at(story[name]["install_at"]) for name in CORE_SITES}
    order = sorted(CORE_SITES, key=lambda n: installs[n])
    if len(set(installs.values())) != len(installs):
        raise StoryClockError(f"INSTALL_CLOCK_CONFLICT: install instants are not distinct {installs}")
    lead = timedelta(hours=doc["install_min_lead_hours"])
    for name in CORE_SITES:
        if installs[name] + lead > earliest[name]:
            raise StoryClockError(f"INSTALL_CLOCK_CONFLICT: {name} installs at {iso(installs[name])}, less than "
                                  f"{lead} before its earliest row {iso(earliest[name])}")
    floor = db_now - timedelta(days=doc["max_backdate_days"]) + timedelta(hours=doc["backdate_margin_hours"])
    work_rows = [v["at"] for v in kobo["visits"] + kobo["plans"] + ev["visits"] + ev["plans"]] + [cold["earliest_row_at"]]
    for value in work_rows:
        if at(value) < floor or at(value) > db_now + timedelta(minutes=5):
            raise StoryClockError(f"STORY_CLOCK_OUT_OF_RANGE: work occurred_at {value} is outside "
                                  f"[{iso(floor)}, {iso(db_now + timedelta(minutes=5))}]")
    if kisiwa:
        import demo_combined_kisiwa

        block = demo_combined_kisiwa.resolve(S, kisiwa_doc or json.loads(KISIWA_STORY_FILE.read_text(encoding="utf-8")))
        k_install = at(block["install_at"])
        if k_install in installs.values() or not all(k_install > v for v in installs.values()):
            raise StoryClockError(f"INSTALL_CLOCK_CONFLICT: Kisiwa installs at {iso(k_install)}; it must be distinct "
                                  f"from and after the three core installs {installs}")
        if k_install + lead > at(block["run1_start"]):
            raise StoryClockError(f"INSTALL_CLOCK_CONFLICT: kisiwa installs at {iso(k_install)}, less than {lead} "
                                  f"before its run 1 {block['run1_start']}")
        story["kisiwa"] = block
        order = order + ["kisiwa"]
    return {"schema": doc["schema"], "label": doc["label"], "db_now": iso(db_now), "S": iso(S),
            "S_date": S.date().isoformat(), "install_order": order,
            "installs": {n: iso(installs[n]) for n in order if n in CORE_SITES},
            "earliest_rows": {n: iso(v) for n, v in earliest.items()},
            "days": [r.payload() for r in days], **story}


#: POLISH §4 P-01/P-02: the route forms `story_links` prints (the board is the Site Overview; there is no
#: `/sites/{code}/outcomes` or `/sites/{code}/overview` route).
LINK_FORMS = ("/portfolio?", "/findings?", "/maintenance/preventive?", "/maintenance?", "/sites/KOBO-001?date=",
              "/sites/COLD-LAB-001?from=", "/sites/EV-LAB-001/ev?from=", "/sites/KOBO-001/actions/",
              "/sites/KOBO-001/findings/", "/sites/KISIWA-001?date=", "/sites/KISIWA-001/performance/fuel?night=",
              "/sites/KISIWA-001/fuel-findings/", "/sites/KISIWA-001/domain-actions/", "/sites/KISIWA-001/findings?",
              "/sites/KISIWA-001/performance/service?")


def story_week_query(story: dict) -> str:
    """The Portfolio and Findings week window around story day S (from S-6d to S+1d)."""
    S = at(story["S"])
    return f"from={iso(S - timedelta(days=6))}&to={iso(S + timedelta(days=1))}"


PREWARM_TIMEOUT_SECONDS = 900


def prewarm(port: int, story: dict, fetch: Any = None, clock: Any = time.monotonic) -> bool:
    """POLISH whole-diff review item 8: request the Portfolio outcome-summary for the story week once, so the first
    Portfolio a presenter opens is not the cold one. Prints "ready:" only when that request has returned a 2xx
    status (WALK1-2 L-B); any other status prints "prewarm returned {status}", and a request that never returns
    prints a warning; neither prints a "ready:" line."""
    import urllib.error
    import urllib.request

    url = f"http://127.0.0.1:{port}/api/estate/outcome-summary?{story_week_query(story)}"
    if fetch is None:
        def fetch(target: str) -> int:
            try:
                with urllib.request.urlopen(target, timeout=PREWARM_TIMEOUT_SECONDS) as response:
                    response.read()
                    return response.status
            except urllib.error.HTTPError as error:
                return error.code
    say("Pre-warming the Portfolio for the story week (outcome summary, once); wait for the ready: line.")
    started = clock()
    try:
        status = fetch(url)
    except Exception as error:  # noqa: BLE001 - any transport failure means "not warmed"
        say(f"pre-warm did not finish ({type(error).__name__}: {error}); open the Portfolio week link and wait until "
            "the outcome matrix fills before the client joins.")
        return False
    if not 200 <= int(status) < 300:
        say(f"prewarm returned {status}; open the Portfolio week link and wait until the outcome matrix fills "
            "before the client joins.")
        return False
    say(f"ready: Portfolio outcome summary for the story week answered HTTP {status} in {clock() - started:.0f} s. "
        "Do not restart serve once the client has joined.")
    return True


def story_links(story: dict, days: list[dict], kobo: dict | None, web: int,
                kisiwa: dict | None = None) -> list[tuple[str, str]]:
    """The walkthrough links (POLISH §4, Addendum 9 Q3): week and month lists around S, one board per story day (Kobo
    by `date`; cold and EV on the day's event window from `days.json`, or the whole calendar day when the day has
    no event), the Kobo Overview on S, and the Kobo Action's verification and Finding when `kobo.json` exists.
    K7: when Kisiwa is in the prepare and `kisiwa.json` exists, its two boards, its Fuel night S-6d, its
    unexplained-fuel Finding (once the build stored one) and, K7-F, its Action's fuel verification."""
    S = at(story["S"])
    base = f"http://localhost:{web}"
    week = story_week_query(story)
    month = f"from={iso(S - timedelta(days=28))}&to={iso(S + timedelta(days=3))}"
    rows = [("Portfolio, week to story day S", f"{base}/portfolio?{week}"),
            ("Findings, week to story day S", f"{base}/findings?{week}"),
            ("Maintenance, Preventive, month to S+3d", f"{base}/maintenance/preventive?{month}"),
            ("Maintenance, month to S+3d", f"{base}/maintenance?{month}")]
    for site in story["sites"]:
        code = SITE_CODE[site]
        for d in sorted((d for d in days if d["site"] == site), key=lambda d: d["offset"]):
            label = f"{code} board, {d['kind']} day S{d['offset']:+d}d ({d['day']})"
            if site == "kobo":
                rows.append((label, f"{base}/sites/{code}?date={d['day']}"))
                continue
            # DD1b1-R2 S1: a Cold or EV story day opens its whole UTC day (the board lists an Action agreed after the
            # event only over a window that reaches it); the label keeps the day's kind.
            day = datetime.fromisoformat(d["day"]).replace(tzinfo=timezone.utc)
            start, end = iso(day), iso(day + timedelta(days=1))
            if not d.get("start") or not d.get("end"):
                label += ", no event: whole day"
            path = f"/sites/{code}/ev" if site == "ev" else f"/sites/{code}"
            rows.append((label, f"{base}{path}?from={start}&to={end}"))
            # DATA-2 (D-E5.32): the exact analysed period too. Cold and EV Site reads select an analysis only when the
            # stored window contains / equals the requested one, so only this link shows the peak, the stock risk and
            # the USD estimate; the whole-day link above stays for Work and Actions.
            if d.get("start") and d.get("end"):
                t0, t1 = at(d["start"]), at(d["end"])
                rows.append((f"{code} analysed period, {d['kind']} day S{d['offset']:+d}d ({d['day']}) "
                             f"{t0:%H:%M}-{t1:%H:%M}Z", f"{base}{path}?from={iso(t0)}&to={iso(t1)}"))
    if kobo is not None:
        rows += [("KOBO-001 Overview, day S", f"{base}/sites/KOBO-001?date={story['S_date']}"),
                 (f"Action {kobo.get('action_code')} verification",
                  f"{base}/sites/KOBO-001/actions/{kobo['action']}/verification"),
                 ("Finding", f"{base}/sites/KOBO-001/findings/{kobo['finding']}")]
    if kisiwa is not None and "kisiwa" in story["sites"]:
        day = lambda n: (S + timedelta(days=n)).date().isoformat()  # noqa: E731
        rows += [("KISIWA-001 board, morning after the unexplained-fuel night (S-5d)",
                  f"{base}/sites/KISIWA-001?date={day(-5)}"),
                 ("KISIWA-001 board, day S", f"{base}/sites/KISIWA-001?date={day(0)}"),
                 ("KISIWA-001 Fuel, night S-6d", f"{base}/sites/KISIWA-001/performance/fuel?night={day(-6)}")]
        # K7-F: `kisiwa.json` carries the Finding id on its Action (`action.finding_id`); `finding.id` is read first
        action = kisiwa.get("action") or {}
        finding = (kisiwa.get("finding") or {}).get("id") or action.get("finding_id")
        if finding:
            rows.append(("KISIWA-001 unexplained-fuel finding", f"{base}/sites/KISIWA-001/fuel-findings/{finding}"))
        if action.get("id") and kisiwa.get("verdict"):  # DIESEL-1-R3m §9m.5: once the plan is frozen and judged
            rows.append(("KISIWA-001 fuel verification",
                         f"{base}/sites/KISIWA-001/domain-actions/{action['id']}/fuel-verification"))
        # OWN-GAPS R2-DS1a 1: the K5 Findings capture's and the K8 story-hour capture's windows, relative to S
        hour = S - timedelta(days=3)
        rows += [("KISIWA-001 Findings, story nights S-9d to S+1d",
                  f"{base}/sites/KISIWA-001/findings?from={iso(S - timedelta(days=9))}&to={iso(S + timedelta(days=2))}"),
                 ("KISIWA-001 Service, story hour S-3d 09:00-10:00Z",
                  f"{base}/sites/KISIWA-001/performance/service?from={iso(hour + timedelta(hours=9))}"
                  f"&to={iso(hour + timedelta(hours=10))}")]
    return rows


#: E4 D-E4.1 (C2): the product reads this file when `ASSETOPS_PREBUILT_ROUTES` names it (never part of `code_version`).
PREBUILT_ROUTES_FILE = "prebuilt-routes.json"
PERFORMANCE_MARKS_FILE = "performance-marks.json"


def read_marks(path: Path) -> dict[str, str]:
    """E4 D-E4.8 (C4): the Site -> DB-watermark marks of the last successful Performance runs; {} when absent."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): str(v) for k, v in doc.items()} if isinstance(doc, dict) else {}


def write_marks(path: Path, marks: dict[str, str]) -> None:
    """Atomic: a temp file in the same folder, then `os.replace` (as C2 writes the routes file)."""
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(marks, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(temp, path)


def performance_due(site: str, mark: str | None, marks: dict[str, str], report_dir: Path) -> bool:
    """E4 D-E4.8 (C4): rerun the Performance comparison only when the Site has no report, no recorded mark, or its
    DB watermark differs from the recorded one. A mark that could not be read (None) is always due."""
    if not report_dir.is_dir() or not any(report_dir.glob("*.json")):
        return True
    return mark is None or marks.get(site) != mark
PREBUILT_ROUTES_ENV = "ASSETOPS_PREBUILT_ROUTES"
PREBUILT_SCHEMA = "chain-prebuilt-routes-1"
#: The Sites whose board link carries `date=` (local day); the others open a whole UTC day by `from`/`to`.
DATE_BOARD_SITES = ("kobo", "kisiwa")


def _api_query(text: str, *extra: tuple[str, str]) -> str:
    """A web link's query as the frontend sends it to the API (`URLSearchParams`: `:` as `%3A`)."""
    from urllib.parse import parse_qsl, urlencode

    return urlencode(parse_qsl(text, keep_blank_values=True) + list(extra))


def _mini_board_day(to: str | None) -> str | None:
    """`frontend/src/sites/EarlyWarnings.tsx` `miniBoardDay`: the UTC day of `to`, the day before when `to` is a UTC
    midnight (an exclusive end); None without a readable `to`."""
    if not to:
        return None
    try:
        end = at(to).astimezone(timezone.utc)
    except ValueError:
        return None
    if (end.hour, end.minute, end.second, end.microsecond) == (0, 0, 0, 0):
        end -= timedelta(days=1)
    return end.date().isoformat()


def _as_date(value: Any) -> Any:
    return date.fromisoformat(value) if isinstance(value, str) else value


PORTFOLIO_LENSES = ("cost", "risks", "opportunities")  # D-E5.23: the Portfolio lens variants, pre-built too


def prebuilt_routes(story: dict, days: list[dict], kisiwa: dict | None,
                    sites_last_day: dict[str, Any]) -> list[dict[str, str]]:
    """E4 D-E4.1 (C2), pure: the pre-built route list for this build, derived from `story_links`'s own rows, so what
    is warmed is what the script opens. Each web link maps to the stored-route API request(s) its page issues, with
    the frontend's query: Portfolio -> `portfolio` (`lens=all`) and `outcome-summary`; Findings -> `findings`
    (`lens=all&state=all`); each `/sites/{code}` board (the EV page's too) -> `/api/sites/{code}/outcome-board` with
    the same `date=` or `from`/`to`. Then the S and month estate requests (the CH-5c Q8 list's), and each Site's
    board for every date from S+1 to its last added date (`sites_last_day`: Site name -> date or ISO date; Kobo and
    Kisiwa by `date`, Cold and EV on the whole UTC day). Duplicates keep the first id."""
    from urllib.parse import parse_qsl, urlsplit

    S = at(story["S"])
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(rid: str, path: str, query: str) -> None:
        if (path, query) not in seen:
            seen.add((path, query))
            out.append({"id": rid, "path": path, "query": query})

    code_site = {v: k for k, v in SITE_CODE.items()}
    for label, url in story_links(story, days, None, 0, kisiwa):
        parts = urlsplit(url)
        segs = [s for s in parts.path.split("/") if s]
        if segs == ["portfolio"]:
            add("portfolio.week", "/api/estate/portfolio", _api_query(parts.query, ("lens", "all")))
            for lens in PORTFOLIO_LENSES:
                add(f"portfolio.week.{lens}", "/api/estate/portfolio", _api_query(parts.query, ("lens", lens)))
            add("summary.week", "/api/estate/outcome-summary", _api_query(parts.query))
        elif segs == ["findings"]:
            add("findings.week", "/api/estate/findings", _api_query(parts.query, ("lens", "all"), ("state", "all")))
        elif len(segs) in (2, 3) and segs[0] == "sites" and (len(segs) == 2 or segs[2] == "ev"):
            params = dict(parse_qsl(parts.query))
            day = params.get("date") or params.get("from", "")[:10]
            if not params.get("date") and not params.get("from", "").endswith("T00:00:00Z"):
                day = params["from"]  # DATA-2: an analysed-period window; its id stays distinct from the day's
            add(f"board.day:{code_site.get(segs[1], segs[1])}:{day}", f"/api/sites/{segs[1]}/outcome-board",
                _api_query(parts.query))
        elif len(segs) == 3 and segs[0] == "sites" and segs[2] == "findings":
            # C2 review M1: a Site Findings page's warnings panel reads the Site board
            # (`frontend/src/shell/SiteAnalyticsFrames.tsx` `SiteEarlyWarnings`): a MINIGRID Site (Kobo, Kisiwa) by
            # `date=miniBoardDay(to)`; Cold and EV by the link's own `from`/`to`/`known_at` (`coldWindowFromParams`).
            site = code_site.get(segs[1], segs[1])
            params = dict(parse_qsl(parts.query))
            if site in DATE_BOARD_SITES:
                day = _mini_board_day(params.get("to"))
                if day is not None:
                    add(f"board.day:{site}:{day}", f"/api/sites/{segs[1]}/outcome-board", _api_query(f"date={day}"))
            else:
                window = [(k, params[k]) for k in ("from", "to", "known_at") if params.get(k)]
                if window:
                    add(f"board.day:{site}:{params.get('from', '')[:10]}", f"/api/sites/{segs[1]}/outcome-board",
                        _api_query("", *window))
    windows = {"S": (S, S + timedelta(days=1)), "month": (S - timedelta(days=28), S + timedelta(days=3))}
    for name, (lo, hi) in windows.items():
        q = _api_query(f"from={iso(lo)}&to={iso(hi)}")
        add(f"portfolio.{name}", "/api/estate/portfolio", _api_query(q, ("lens", "all")))
        for lens in PORTFOLIO_LENSES:
            add(f"portfolio.{name}.{lens}", "/api/estate/portfolio", _api_query(q, ("lens", lens)))
        add(f"summary.{name}", "/api/estate/outcome-summary", q)
    if "kobo" in story["sites"]:  # the "KOBO-001 Overview, day S" link (printed once `kobo.json` exists)
        add(f"board.day:kobo:{story['S_date']}", "/api/sites/KOBO-001/outcome-board",
            _api_query(f"date={story['S_date']}"))
    for site in story["sites"]:
        last = _as_date(sites_last_day.get(site))
        if last is None:
            continue
        code = SITE_CODE[site]
        for d in _days(S.date() + timedelta(days=1), last):
            if site in DATE_BOARD_SITES:
                query = _api_query(f"date={d.isoformat()}")
            else:
                day = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
                query = _api_query(f"from={iso(day)}&to={iso(day + timedelta(days=1))}")
            add(f"board.day:{site}:{d.isoformat()}", f"/api/sites/{code}/outcome-board", query)
    return out


def sites_last_day(story: dict, days: list[dict], kisiwa_entries: list[dict]) -> dict[str, Any]:
    """Each Site's latest date (its calendar and added dates): the core Sites' latest `days.json` day, Kisiwa's
    latest story or added (DONE / PUBLISHED) night."""
    out: dict[str, Any] = {}
    for site in story["sites"]:
        if site == "kisiwa":
            if story.get("kisiwa"):
                import demo_combined_kisiwa as kis

                nights = [kis.last_story_night(story["kisiwa"])]
                nights += [date.fromisoformat(e["night_date"]) for e in kisiwa_entries
                           if e.get("status") in ("DONE", "PUBLISHED")]
                out[site] = max(nights)
            continue
        mine = [date.fromisoformat(d["day"]) for d in days if d["site"] == site]
        if mine:
            out[site] = max(mine)
    return out


def prebuilt_routes_doc(requests: list[dict[str, str]], S_date: str) -> dict:
    return {"schema": PREBUILT_SCHEMA,
            "note": "E4 D-E4.1: written by tools/demo_combined.py before every prebuild and at serve start, from the "
                    f"story links and each Site's dates after S={S_date} up to its last added date.",
            "requests": requests}


def added_night_links(entries: list[dict], web: int) -> list[tuple[str, str]]:
    """OWN-G1 §4.5 `links`: one Fuel link per added Kisiwa night, then the live-dip line (owner Q2): the newest added
    night's 06:00 local dip and the litres its run read, for the on-screen beat."""
    base = f"http://localhost:{web}"
    added = sorted((e for e in entries if e.get("status") in ("DONE", "PUBLISHED")), key=lambda e: e["night_date"])
    rows = [(f"KISIWA-001 Fuel, added night {e['night_date']} ({e['kind']})",
             f"{base}/sites/KISIWA-001/performance/fuel?night={e['night_date']}") for e in added]
    if added:
        newest = added[-1]
        dip = next(a for a in newest["actions"] if a["action_id"].endswith("-dip-0600"))
        import demo_combined_kisiwa as kis

        rows.append(("Live dip: Operational records, KISIWA-001, Fuel tank dip, taken "
                     f"{kis.taken_at_local(at(dip['at']))}, value {newest['dips'][dip['action_id']]} L",
                     f"{base}/sites/KISIWA-001/performance/fuel?night={newest['night_date']}"))
    return rows


# ---- add-dates (OWN-GAPS §4, Revision 2 R2-G1): the owner's catch-up tool -------------------------------------------

ADD_DATES_ORDER = ("kobo", "cold", "ev", "kisiwa")
ALREADY_PRESENT = "already present"
NIGHT_NOT_OVER = "NIGHT_NOT_OVER"


def _days(lo: Any, hi: Any) -> list:
    return [lo + timedelta(days=n) for n in range((hi - lo).days + 1)] if lo <= hi else []


def select_sites(arg: str, story: dict) -> list[str]:
    """`--site all` = the build's Sites; any named Site the build did not prepare refuses (R2-G1 Q9 a)."""
    built = [s for s in ADD_DATES_ORDER if s in story["sites"]]
    if arg == "all":
        return built
    code_site = {v: k for k, v in SITE_CODE.items()}
    out = []
    for code in (c.strip() for c in arg.split(",") if c.strip()):
        site = code_site.get(code)
        if site is None or site not in built:
            raise sd.StoryDaysError("SITE_NOT_IN_BUILD", f"{code} is not in this build.")
        out.append(site)
    return [s for s in ADD_DATES_ORDER if s in out]


def last_story_day(days_json: dict, site: str, S: datetime) -> Any:
    """R2-G1 Q5: the max `weekday_offset` over the build's (baselined) calendar entries; `add-day` never edits it."""
    return sd.offset_date(S, max(sd.weekday_offset(site, S, sd.day_offset(e["day"]))
                                 for e in days_json["doc"]["sites"][site]))


def plan_add_dates(story: dict, days_json: dict, kisiwa_entries: list[dict], *, sites: list[str], date_from: Any,
                   date_to: Any, kind: str | None, db_now: datetime, zones: dict[str, str],
                   delivered: dict[str, set[str]]) -> dict:
    """§4.2-§4.4 and R2-G1, pure: each selected Site's dates (in its own timezone), the whole-command refusals
    (`StoryDaysError`), and what is skipped, left empty or has no EV session. `date_from` / `date_to` are dates or
    None (None: the Site's default; `--to yesterday` passes None)."""
    import demo_combined_kisiwa as kis

    S = at(story["S"])
    if date_from is not None and date_to is not None and date_from > date_to:
        raise sd.StoryDaysError("FROM_AFTER_TO", "--from is after --to.")
    plans: dict[str, dict] = {}
    for site in sites:
        code = SITE_CODE[site]
        yesterday = sd.local_yesterday(db_now, zones[code])
        if date_to is not None and date_to > yesterday:
            raise sd.StoryDaysError("DATE_NOT_PAST", f"Data can be added only up to yesterday ({yesterday.isoformat()}).")
        story_last = (kis.last_story_night(story["kisiwa"]) if site == "kisiwa"
                      else last_story_day(days_json, site, S))
        for value in (date_from, date_to):
            if value is not None and value <= story_last:
                raise sd.StoryDaysError("STORY_DAY", f"{code} {value.isoformat()} is part of the prepared story and "
                                                     "cannot be changed.")
        plan = {"dates": [], "skipped": [], "left_empty": [], "no_session": []}
        if site == "kisiwa":
            # H1: start after the last DONE night, so a PUBLISHED night (check not finished) is resumed, never skipped
            last = max([kis.last_story_night(story["kisiwa"]),
                        *[date.fromisoformat(e["night_date"]) for e in kisiwa_entries if e.get("status") == "DONE"]])
            if date_from is not None and date_from > last + timedelta(days=1):
                raise sd.StoryDaysError("GAP_NOT_ALLOWED", f"Kisiwa nights must follow on from {last.isoformat()}; "
                                                           f"start at {(last + timedelta(days=1)).isoformat()}.")
            finished = kis.latest_finished_night(story["kisiwa"], db_now)
            lo = date_from or last + timedelta(days=1)
            for d in _days(lo, date_to or finished):
                entry = kis._entry(kisiwa_entries, d)
                if entry is not None and entry.get("status") == "DONE":
                    plan["skipped"].append((d, ALREADY_PRESENT))
                elif d > finished:
                    plan["skipped"].append((d, NIGHT_NOT_OVER))
                else:
                    plan["dates"].append(d)
            new = [d for d in plan["dates"] if (kis._entry(kisiwa_entries, d) or {}).get("status") != "PUBLISHED"]
            if new and kis.date_too_old(story["kisiwa"], new[0], db_now):
                raise sd.StoryDaysError("DATE_TOO_OLD", f"Kisiwa {new[0].isoformat()} is too old to add records for; "
                                                        "prepare a fresh build.")
        else:
            mine = [d for d in days_json["days"] if d["site"] == site]
            default = sd.offset_date(S, max(d["offset"] for d in mine) + 1)
            weekday = sd.SITE_WEEKDAY.get(site)
            if weekday is not None:  # EV: the next ruled weekday (R2-G1 Q5)
                default += timedelta(days=(weekday - default.weekday()) % 7)
            lo = date_from or default
            present = {d["day"] for d in mine if d.get("received_at")} | set(delivered.get(code, ()))
            if date_from is not None and date_from > default:
                plan["left_empty"] = [d for d in _days(default, date_from - timedelta(days=1))
                                      if weekday is None or d.weekday() == weekday]
            for d in _days(lo, date_to or yesterday):
                if weekday is not None and d.weekday() != weekday:
                    plan["no_session"].append(d)
                elif d.isoformat() in present:
                    plan["skipped"].append((d, ALREADY_PRESENT))
                else:
                    plan["dates"].append(d)
        plan["kind"] = kind if kind is not None else (None if site == "kisiwa" else "normal")
        plans[site] = plan
    if kind is not None:
        span = [d for p in plans.values() for d in p["dates"] + [x for x, _ in p["skipped"]] + p["no_session"]]
        if len(sites) != 1 or len(span) != 1:
            raise sd.StoryDaysError("KIND_NEEDS_ONE_DATE", "--kind needs exactly one Site and one date.")
    order = sorted({d for p in plans.values() for d in p["dates"]})
    return {"sites": plans, "order": order}


def preflight_refusal(done_rc: int | None, line: dict | None, kisiwa: bool) -> sd.StoryDaysError | None:
    """R2-G1 Q7, in order: the tree's Kisiwa child missing or failing -> BUILD_TOO_OLD (always); then, only with
    Kisiwa selected, no `fuel_night` stage, a 403 WORK_WRITE_FORBIDDEN, anything but 422 OPREC_ENTRY_INVALID."""
    if done_rc is None or done_rc != 0 or line is None:
        return sd.StoryDaysError("BUILD_TOO_OLD", "This build predates add-dates; prepare a fresh build from current "
                                                  "main.")
    if not kisiwa:
        return None
    if not line.get("fuel_stage"):
        return sd.StoryDaysError("FUEL_STAGE_MISSING", "This build's code has no automatic diesel-night check (G2).")
    if line.get("entry_status") == 403 and line.get("entry_code") == "WORK_WRITE_FORBIDDEN":
        return sd.StoryDaysError("ENTRY_DISABLED", "Saving records is not switched on for this build "
                                                   "(ASSETOPS_OPERATIONAL_ENTRY).")
    if (line.get("entry_status"), line.get("entry_code")) != (422, "OPREC_ENTRY_INVALID"):
        return sd.StoryDaysError("ENTRY_DISABLED", "This build's code has no working record entry (G3a); prepare a "
                                                   "fresh build from current main.")
    return None


def kisiwa_stage(report: dict | None) -> tuple[bool, dict | None]:
    """R2-G2 Q9 / R2-G1 Q6: whether the tick visited KISIWA-001 (its `fuel_night` stage entry) and that entry."""
    for site in (report or {}).get("sites") or ():
        if site.get("site_code") == "KISIWA-001" and "fuel_night" in (site.get("stages") or {}):
            return True, site["stages"]["fuel_night"]
    return False, None


def failed_rows(path: Path) -> list[str]:
    """The failed row ids of a `check.json` (`demo_combined_finish.run`), or [] when it cannot be read."""
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    except (OSError, ValueError, KeyError, TypeError):
        return []
    return [k for k, v in rows.items() if isinstance(v, dict) and v.get("status") == "fail"]


def short_date(d: Any) -> str:
    return f"{d.day} {d.strftime('%b')}"


def plain_lines(added: list[dict], skipped: list[dict], no_session: list[dict], left_empty: dict) -> list[str]:
    """§4.4: one plain line per Site."""
    lines = []
    for code in [SITE_CODE[s] for s in ADD_DATES_ORDER]:
        mine = [a for a in added if a["site"] == code]
        parts = []
        if mine:
            items = []
            for a in mine:
                extra = (f", ticket {a['ticket']}" if a.get("ticket") else "")
                late = " (delivery entered after the night)" if a.get("ticket") else ""
                warn = " (a background step reported a failure; see logs)" if a.get("tick_failures") else ""
                items.append(f"{short_date(a['date'])} ({a['kind']}{extra}){late}{warn}")
            n = len(mine)
            tail = (f"{'the night' if n == 1 else 'both nights' if n == 2 else f'all {n} nights'} checked: within "
                    "margin" if code == "KISIWA-001" else "checked by the background refresh")
            parts.append(f"added {', '.join(items)}; {tail}")
        parts += [f"{short_date(s['date'])} {s.get('text') or s['reason']}" for s in skipped if s["site"] == code]
        if left_empty.get(code):
            parts.append("left empty: " + ", ".join(short_date(d) for d in left_empty[code]))
        lines += [f"{code}: " + "; ".join(parts) + "."] if parts else []
        lines += [f"{code} {d['date'].isoformat()}: no charging session (the simulated charger runs on Tuesdays)"
                  for d in no_session if d["site"] == code]
    return lines


class Demo:
    step = ""  # DD1b2-R8 C2: the label of the last child started (the manifest's `failed_at`)
    defer_drain = False  # DD1b2-R8 C1: inside `prepare` a drain failure is recorded and the prepare goes on
    drain_failures: tuple = ()

    def __init__(self, db: str, work: str) -> None:
        if not DB_RE.fullmatch(db):
            raise SystemExit(f"Refused: --db {db!r} must match {DB_RE.pattern}")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve() or not path.name.startswith(WORK_PREFIXES):
            raise SystemExit(f"Refused: --work {path} must be a var/demo3* or var/polish* folder directly under "
                             f"{REPO / 'var'}")
        self.db, self.work, self.tree = db, path, path / "tree"
        self.url = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{db}"
        self.deadline: float | None = None
        self.started: list[int] = []
        self.holds_busy = False
        self.drains: dict[str, float] = {}

    # ---- environment -------------------------------------------------------------------------------------------
    def env(self, *, keys: bool = False) -> dict[str, str]:
        out = dict(os.environ)
        parts = ["backend", "backend/tests", "contracts", "gateway", "simulator", "host", "host/tests",
                 "gateway/tests", "tools"]
        out["PYTHONPATH"] = os.pathsep.join(str(self.tree / p) for p in parts)
        out["DATABASE_URL"] = out["ASSETOPS_TEST_DATABASE_URL"] = self.url
        out["PYTHONUNBUFFERED"] = "1"
        for k in ("ASSETOPS_TEST_RUN_ID", "ASSETOPS_TEST_DATABASE_BASE_URL"):
            out.pop(k, None)
        for k in KEY_NAMES:
            out.pop(k, None)
        if keys:
            out.update(json.loads((self.work / "keys.json").read_text(encoding="utf-8")))
        return out

    def serve_env(self) -> dict[str, str]:
        """CH5c-R6: the one environment of the serve child AND the tick child, so the tick's pre-built rows carry
        the server's `code_version` (the cursor keys are hashed into it). Clone settles stay keyless
        (`chain_clone.settle_env`): they are never served. OWN-G3a (§3.2): the served app saves operational records
        typed on screen (`ASSETOPS_OPERATIONAL_ENTRY=on`, read by `host/lab_app.py`)."""
        out = self.env(keys=True)
        out["ASSETOPS_OPERATIONAL_ENTRY"] = "on"
        routes = self.work / PREBUILT_ROUTES_FILE
        if routes.is_file():  # E4 D-E4.1: the tool's and the serve loop's prebuild read the story's own list
            out[PREBUILT_ROUTES_ENV] = str(routes)
        return out

    def write_prebuilt_routes(self) -> Path | None:
        """E4 D-E4.1 (C2): (re)write `<work>/prebuilt-routes.json` from the story links and each Site's dates after S
        up to its last added date. Called before every prebuild and at `serve` start; None (nothing written) when
        the build has no story day S yet."""
        story = self.story()
        if not story.get("S"):
            return None
        import demo_combined_kisiwa as kis

        days_file = self.work / "days.json"
        days = json.loads(days_file.read_text(encoding="utf-8"))["days"] if days_file.is_file() else []
        kis_file = self.work / "kisiwa.json"
        kisiwa = json.loads(kis_file.read_text(encoding="utf-8")) if kis_file.is_file() else None
        last = sites_last_day(story, days, kis.read_days(self.work))
        doc = prebuilt_routes_doc(prebuilt_routes(story, days, kisiwa, last), story["S_date"])
        path = self.work / PREBUILT_ROUTES_FILE
        temp = path.with_name(PREBUILT_ROUTES_FILE + ".tmp")  # C2 review L3: a reader never sees a half-written file
        temp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
        os.replace(temp, path)
        return path

    def py(self, *argv: str, cwd: Path | None = None, check: bool = True, label: str = "",
           serve_env: bool = False) -> subprocess.CompletedProcess:
        """One child in the tree, bounded by the wall cap; on the cap it kills only that child's process tree."""
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        name = label or argv[0].split("/")[-1].split("\\")[-1]
        self.step = name
        log_path = logs / f"{len(list(logs.iterdir())):02d}-{re.sub(r'[^a-z0-9_.-]', '_', name.lower())[:40]}.log"
        with open(log_path, "w", encoding="utf-8") as log:
            proc = subprocess.Popen([str(PY), *argv], cwd=str(cwd or self.tree), env=self.serve_env() if serve_env else self.env(), stdout=log,
                                    stderr=subprocess.STDOUT, text=True)
            self.started.append(proc.pid)
            remaining = None if self.deadline is None else max(1.0, self.deadline - time.monotonic())
            try:
                code = proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                _kill_tree(proc.pid)
                raise SystemExit(f"WALL CAP reached during {name}; stopped PID {proc.pid} (log {log_path})")
        output = log_path.read_text(encoding="utf-8", errors="replace")
        done = subprocess.CompletedProcess(argv, code, output, "")
        if check and code != 0:
            raise SystemExit(f"FAILED: {name} (exit {code}); log {log_path}\n{output[-3000:]}")
        return done

    def owned(self) -> bool:
        return (self.work / MARKER).is_file()

    def marker_db(self) -> str | None:
        if not self.owned():
            return None
        for line in (self.work / MARKER).read_text(encoding="utf-8").splitlines():
            if line.startswith("db="):
                return line[3:].strip()
        return None

    @staticmethod
    def exists(c, db: str) -> bool:
        return c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,)).fetchone() is not None

    def story(self) -> dict:
        path = self.work / "story.json"
        if not path.is_file():
            raise SystemExit("Run prepare first.")
        return json.loads(path.read_text(encoding="utf-8"))

    # ---- prepare -----------------------------------------------------------------------------------------------
    def prepare(self, sites: tuple[str, ...] = SITES, finish: bool = True, days_file: str | None = None,
                baseline: str = "b22", cap_seconds: int | None = None) -> dict:
        import psycopg

        days_path = Path(days_file).resolve() if days_file else sd.DEFAULT_FILE
        days_doc = sd.load(days_path)
        expected = {**EXPECTED_SECONDS, "kobo": kobo_expected_seconds(days_doc)}
        # DD1b2-R6 O3: `--cap-seconds` replaces the 2x-sum cap (the whole-list rehearsal runs on 10800 s)
        cap = (cap_seconds if cap_seconds is not None
               else 2 * (expected["tree"] + sum(expected[s] for s in sites) + ((expected["finish"] + expected["day_rows"]) if finish else 0)))
        self.deadline = time.monotonic() + cap
        began = time.monotonic()
        if (self.work / ".busy").exists():
            raise SystemExit(f"Refused: another prepare/add-day holds {self.work / '.busy'}")
        if self.work.exists() and any(self.work.iterdir()) and not self.owned():
            raise SystemExit(f"Refused: {self.work} exists, is not empty and was not made by this tool")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            if self.exists(c, self.db) and self.marker_db() != self.db:
                raise SystemExit(f"Refused: database {self.db} exists and {self.work / MARKER} does not record that "
                                 "this tool made it; choose another --db")
        say(f"=== 1. Private tree (git HEAD), database {self.db}, story clock (wall cap {cap} s) ===")
        if self.work.exists():
            for child in self.work.iterdir():
                if child.name != MARKER:
                    shutil.rmtree(child) if child.is_dir() else child.unlink()
        self.work.mkdir(parents=True, exist_ok=True)
        (self.work / MARKER).write_text(f"created by tools/demo_combined.py\ndb={self.db}\n", encoding="utf-8")
        (self.work / ".busy").write_text(f"prepare pid={os.getpid()}\n", encoding="utf-8")
        self.holds_busy = True
        self.tree.mkdir()
        parts = ("backend", "gateway", "host", "simulator", "contracts", "config", "contract-fixtures", "tools")
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", *parts], cwd=REPO, capture_output=True,
                                 check=False) if shutil.which("git") else None
        if archive is not None and archive.returncode == 0:
            with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
                tar.extractall(self.tree, filter="data")
        else:  # no git here (the test container mounts the worktree without its .git): copy the checked-out files
            skip = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "node_modules")
            for part in parts:
                shutil.copytree(REPO / part, self.tree / part, ignore=skip)
        (self.tree / "var" / "sites").mkdir(parents=True)
        shutil.copy2(self.tree / "backend" / "tests" / "fixtures" / "s1" / "kobo-001.yaml",
                     self.tree / "var" / "sites" / "kobo-001.yaml")
        head = (subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True)
                if shutil.which("git") else subprocess.CompletedProcess([], 0, stdout="checked-out-copy"))
        if days_file is None:
            shipped = self.tree / sd.DEFAULT_FILE.relative_to(REPO)
            if not shipped.is_file() or sd.load(shipped) != days_doc:
                raise SystemExit(f"Refused: {sd.DEFAULT_FILE.relative_to(REPO)} differs from HEAD; commit it first")
        probe = self.py("-c", "import assetops_backend;print(assetops_backend.__file__)", label="isolation").stdout
        if str(self.tree).lower() not in probe.lower():
            raise SystemExit(f"Isolation failed: assetops_backend resolves to {probe.strip()}")
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")
            c.execute(f"CREATE DATABASE {self.db}")
        self.py("-c", "import sys, pg_harness\nfrom alembic import command\n"
                      "command.upgrade(pg_harness._alembic(sys.argv[1]), 'head')", self.url, label="migrate",
                cwd=self.tree / "backend" / "tests")
        with psycopg.connect(PG_ADMIN.rsplit("/", 1)[0] + "/" + self.db, autocommit=True) as c:
            db_now = c.execute("SELECT clock_timestamp()").fetchone()[0]
        days_doc = sd.apply_baseline(days_doc, story_day(db_now), baseline)  # DD1a2-R Q6
        for site, missing in sd.uncovered_weekdays(days_doc, story_day(db_now), baseline).items():
            if missing:
                say(f"  {SITE_CODE[site]}: ruled days in the {baseline} baseline with no entry (reported, not moved): "
                    f"{', '.join(missing)}")
        story = resolve_story(db_now, days_doc=days_doc, kisiwa="kisiwa" in sites)
        days = story.pop("days")
        (self.work / "days.json").write_text(json.dumps(
            {"schema": days_doc["schema"], "source": str(days_path), "S": story["S"], "trial": days_doc["trial"],
             "days": days, "doc": days_doc}, indent=2), encoding="utf-8")
        story["code"] = head.stdout.strip()
        story["sites"] = [s for s in story["install_order"] if s in sites]
        (self.work / "story.json").write_text(json.dumps(story, indent=2), encoding="utf-8")
        keys = {k: secrets.token_hex(32) for k in KEY_NAMES}
        (self.work / "keys.json").write_text(json.dumps(keys), encoding="utf-8")
        say(f"  tree {self.tree} (code {story['code']}); S = {story['S']}; install order {story['install_order']}")

        return self.build_and_record(story, days, finish, cap, began, time.monotonic() - began)

    def build_and_record(self, story: dict, days: list[dict], finish: bool, cap: int, began: float,
                         tree_seconds: float) -> dict:
        """The Site children and the finish, with `manifest.json` written whatever happens (DD1b2-R8 C2): a failure
        records `failed_at` (the last child's label) and the error, with the timings gathered so far."""
        timings: dict[str, float] = {}
        steps: dict[str, float] = {}
        self.defer_drain, self.drain_failures = True, ()  # DD1b2-R8 C1
        error: str | None = None
        try:
            for n, site in enumerate(story["sites"], start=2):
                install = story["installs"][site] if site in CORE_SITES else story[site]["install_at"]
                say(f"=== {n}. {SITE_CODE[site]} (installs {install}) ===")
                t0 = time.monotonic()
                done = self.py(str(self.tree / "tools" / f"demo_combined_{site}.py"), "build", self.url,
                               str(self.work), cwd=self.tree / "backend" / "tests", label=f"build-{site}")
                timings[site] = round(time.monotonic() - t0, 1)
                say("  " + (done.stdout.strip().splitlines() or ["(no output)"])[-1] + f"  [{timings[site]} s]")
            self.finish_build(story, days, finish, timings, steps)
        except BaseException as exc:  # recorded in the manifest (R8 C2), then re-raised
            error = f"{type(exc).__name__}: {exc}"[:2000]
            raise
        finally:
            steps.update(self.drains)
            manifest = {"db": self.db, "S": story["S"], "code": story["code"], "sites": story["sites"],
                        "timings_seconds": timings, "step_timings_seconds": steps,
                        "tree_seconds": round(tree_seconds, 1), "wall_seconds": round(time.monotonic() - began, 1),
                        "wall_cap_seconds": cap, "failed_at": self.step if error else None, "error": error}
            for site in story["sites"]:
                path = self.work / f"{site}.json"
                manifest[site] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
            (self.work / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        say(f"Prepared in {manifest['wall_seconds']} s (cap {cap} s). Next: links, serve.")
        return manifest

    def finish_build(self, story: dict, days: list[dict], finish: bool, timings: dict[str, float],
                     steps: dict[str, float] | None = None) -> None:
        """What follows the Site children: the mill sequence on a three-Site prepare (DD1b2-R Q4), then the finish. A
        one-Site or two-Site prepare keeps the plain finish: the mill step needs all three Sites' Action codes.
        `steps` collects the DD1b2-R6 O3 timings (mini-depth, backfill, mill, drains, finish rows)."""
        steps = steps if steps is not None else {}
        if not finish:
            return
        if set(CORE_SITES) <= set(story["sites"]):
            t0 = time.monotonic()
            out = self.after_children(story, days)
            timings["after_children"] = round(time.monotonic() - t0, 1)
            steps.update(out.get("timings_seconds", {}))
        t0 = time.monotonic()
        self.finish({**story, "days": days}, steps)
        timings["finish"] = round(time.monotonic() - t0, 1)
        steps.update(self.drains)
        self.raise_deferred_drain()

    def after_children(self, story: dict, days: list[dict], stop_before_mill: bool = False) -> dict:
        """DD1b2-R Q4 steps 2 to 5, after every Site child: `drain_mini` (the study needs the renewable heads), backfill
        step `a` (the freeze needs the snapshots), the mill step, then `b,c,d`. No tick may run before the mill step, or
        a wall-clock study opens the thread and every mill cause is skipped. Step 6, the R8 drain, is DD-1b2b's."""
        if not any(d["site"] == "kobo" and d["kind"] == "mill-midday" for d in days):
            raise SystemExit("Refused: the mill step needs the day list's Kobo mill-midday day")
        say("=== Mini-depth, snapshots, the mill step, threads ===")
        out: dict[str, Any] = {"timings_seconds": {}}

        def timed(name: str, *argv: str, **kw: Any) -> subprocess.CompletedProcess:
            t0 = time.monotonic()
            done = self.py(*argv, label=name, **kw)
            out["timings_seconds"][name] = round(time.monotonic() - t0, 1)
            say(f"  {name}: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:200]
                + f"  [{out['timings_seconds'][name]} s]")
            return done

        t0 = time.monotonic()
        self.drain_mini()
        out["timings_seconds"]["mini-depth"] = round(time.monotonic() - t0, 1)
        timed("backfill-a", "-m", "assetops_backend.chain.backfill", "--steps", "a")
        if stop_before_mill:  # development only (DD1b2-R2 section 4): the caller clones the database here
            return out
        timed("mill", str(self.tree / "tools" / "demo_combined_mill.py"), "build", self.url, str(self.work),
              cwd=self.tree / "backend" / "tests")
        done = timed("backfill-bcd", "-m", "assetops_backend.chain.backfill", "--steps", "b,c,d")
        out["threads"] = [json.loads(x) for x in done.stdout.splitlines() if x.startswith("{")]
        self.drain("drain-1")  # DD1b2-R6 O2: the R8 drain after `b,c,d`
        out["timings_seconds"]["drain-1"] = self.drains["drain-1"]
        (self.work / "after-children.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out

    def finish(self, story: dict, steps: dict[str, float] | None = None) -> None:
        steps = steps if steps is not None else {}
        say("=== Objectives, S2 comparison, two ticks, Performance comparison ===")
        if set(CORE_SITES) <= set(story["sites"]):
            lines = []
            for code, instant in objectives_instants(story).items():
                done = self.py(str(self.tree / "tools" / "demo_declare_objectives.py"), self.url,
                               str(self.tree / "backend" / "conversions" / "demo-objectives.json"), code, iso(instant),
                               label=f"objectives {code}")
                lines += [json.loads(x) for x in done.stdout.splitlines() if x.startswith("{")]
            (self.work / "objectives.json").write_text(json.dumps(lines, indent=2), encoding="utf-8")
            say(f"  objectives: {len(lines)} lines")
        if "kobo" in story["sites"]:
            done = self.py("-m", "assetops_backend.evidence_migration", "run", "--tenant", "demo", "--site", "KOBO-001",
                           label="s2-comparison")
            say("  " + (done.stdout.strip().splitlines() or ["(no output)"])[-1])
        if {"kobo", "kisiwa"} & set(story["sites"]):
            self.drain_mini()
        t0 = time.monotonic()
        report = self.tick(times=2)
        if "kisiwa" in story["sites"]:  # OWN-G2 (R2-G2 Q9 addition): a serve loop may have claimed KISIWA-001
            report, extra = retry_until_visited(report, lambda: self.tick(times=1))
            if extra:
                say(f"  tick: {extra} extra tick(s) for KISIWA-001's fuel_night stage")
        steps["finish-ticks"] = round(time.monotonic() - t0, 1)
        if set(CORE_SITES) <= set(story["sites"]):
            self.drain("drain-2")  # R8 drain 2: F-DRAIN reads after it
            self.build_period_rows(story, steps)
            self.build_day_rows(story, steps)  # D-SR.54: after the board rows, its own cap
            t0 = time.monotonic()
            done = self.py(str(self.tree / "tools" / "demo_combined_finish.py"), "check", self.url, str(self.work),
                           cwd=self.tree / "backend" / "tests", label="self-check", check=False)
            steps["finish-rows"] = round(time.monotonic() - t0, 1)
            tail = done.stdout.strip().splitlines()
            say("  " + (tail or ["(no output)"])[-1] + f"  [{steps['finish-rows']} s]")
            if done.returncode != 0:
                deferred = f" (and DRAIN FAILED (deferred): {list(self.drain_failures)})" if self.drain_failures else ""
                raise SystemExit(f"SELF-CHECK FAILED; see {self.work / 'check.json'}{deferred}")

    #: ANY-1 AR-2 (D-ANY.6): the board's stored mini depth rows are built within this many seconds.
    PERIOD_ROWS_CAP_SECONDS = 15 * 60
    #: D-SR.54: the board kinds are built with an explicit list (unchanged 15-minute cap); the two day kinds follow in
    #: their own step, 30 minutes for both Sites (about 2,100 hour reads at 0.55-0.75 s each).
    BOARD_KINDS = tuple(f"mini_depth.{d}" for d in ("renewable", "fuel", "service", "backup"))
    DAY_KINDS = ("mini_depth.fuel_day", "mini_depth.backup_day")
    DAY_ROWS_CAP_SECONDS = 30 * 60
    DAY_ROWS_RERUN = ("period_backfill build --kind mini_depth.fuel_day --kind mini_depth.backup_day")

    def build_period_rows(self, story: dict, steps: dict[str, float]) -> bool:
        """AR-2: build the `mini_depth.*` read-period rows of every mini Site after the last drain (the backfill CLI;
        an unchanged fingerprint writes nothing). Timed per Site and in total, capped at 15 minutes. Over the cap or
        on a failure it says so and the prepare goes on: the boards then need the kill switch
        `ASSETOPS_PERIOD_READ_KINDS=` (empty, today's compose) - never silent."""
        say("=== Stored board rows (AR-2: mini depth) ===")
        codes = [SITE_CODE[s] for s in ("kobo", "kisiwa") if s in story["sites"]]
        began, saved, ok = time.monotonic(), self.deadline, True
        cap = began + self.PERIOD_ROWS_CAP_SECONDS
        self.deadline = cap if saved is None else min(saved, cap)
        try:
            for code in codes:
                t0 = time.monotonic()
                done = self.py("-m", "assetops_backend.chain.period_backfill", "build", "--site", code, "--quiet",
                               *(a for k in self.BOARD_KINDS for a in ("--kind", k)),
                               label=f"period-rows {code}", check=False)
                steps[f"period-rows {code}"] = round(time.monotonic() - t0, 1)
                tail = (done.stdout.strip().splitlines() or ["(no output)"])[-1][:200]
                say(f"  period-rows {code}: {tail}  [{steps[f'period-rows {code}']} s]")
                if done.returncode != 0:
                    ok = False
                    say(f"  ROW BUILD FAILED for {code} (exit {done.returncode}): serve the boards with "
                        "ASSETOPS_PERIOD_READ_KINDS= (empty)")
        except SystemExit as stopped:  # the 15-minute cap (or the prepare's own wall cap) stopped the child
            ok = False
            say(f"  ROW BUILD INCOMPLETE ({stopped}): serve the boards with ASSETOPS_PERIOD_READ_KINDS= (empty)")
            if saved is not None and time.monotonic() >= saved:
                self.deadline = saved
                raise
        finally:
            self.deadline = saved
        steps["period-rows"] = round(time.monotonic() - began, 1)
        say(f"  period-rows total: {steps['period-rows']} s (cap {self.PERIOD_ROWS_CAP_SECONDS} s)"
            + ("" if ok else "  NOT COMPLETE"))
        (self.work / "period-rows.json").write_text(json.dumps(
            {"ok": ok, "seconds": steps["period-rows"], "sites": codes,
             "cap_seconds": self.PERIOD_ROWS_CAP_SECONDS}, indent=2), encoding="utf-8")
        return ok

    def build_day_rows(self, story: dict, steps: dict[str, float]) -> bool:
        """D-SR.54: build `mini_depth.fuel_day` / `mini_depth.backup_day` for every mini Site, after the board rows,
        under their own 30-minute cap for both Sites. Over the cap or on failure it prints the rerun command and the
        prepare goes on (the board kinds are unaffected). Records each Site's seconds and seconds per hour read."""
        say("=== Stored range rows (SR-10: fuel and backup days) ===")
        codes = [SITE_CODE[s] for s in ("kobo", "kisiwa") if s in story["sites"]]
        began, saved, ok = time.monotonic(), self.deadline, True
        cap = began + self.DAY_ROWS_CAP_SECONDS
        self.deadline = cap if saved is None else min(saved, cap)
        per_site: dict[str, dict] = {}
        rerun = f"Fuel/Backup range rows incomplete: rerun `{self.DAY_ROWS_RERUN}`"
        try:
            for code in codes:
                t0 = time.monotonic()
                done = self.py("-m", "assetops_backend.chain.period_backfill", "build", "--site", code, "--quiet",
                               *(a for k in self.DAY_KINDS for a in ("--kind", k)),
                               label=f"day-rows {code}", check=False)
                secs = round(time.monotonic() - t0, 1)
                steps[f"day-rows {code}"] = secs
                summary = demo_rows.last_json_object(done.stdout) or {}
                hours = int(summary.get("considered") or 0) * 24  # period rows (day x kind) x 24 hour reads
                per_site[code] = {"seconds": secs, "hour_reads": hours,
                                  "seconds_per_hour_read": round(secs / hours, 3) if hours else None}
                say(f"  day-rows {code}: {(done.stdout.strip().splitlines() or ['(no output)'])[-1][:200]}  [{secs} s]")
                if done.returncode != 0:
                    ok = False
                    say(f"  {rerun}")
        except SystemExit as stopped:
            ok = False
            say(f"  DAY ROW BUILD INCOMPLETE ({stopped}): {rerun}")
            if saved is not None and time.monotonic() >= saved:
                self.deadline = saved
                raise
        finally:
            self.deadline = saved
        steps["day-rows"] = round(time.monotonic() - began, 1)
        say(f"  day-rows total: {steps['day-rows']} s (cap {self.DAY_ROWS_CAP_SECONDS} s)" + ("" if ok else "  NOT COMPLETE"))
        (self.work / "day-rows.json").write_text(json.dumps(
            {"ok": ok, "seconds": steps["day-rows"], "sites": codes, "per_site": per_site,
             "cap_seconds": self.DAY_ROWS_CAP_SECONDS}, indent=2), encoding="utf-8")
        return ok

    def drain_mini(self, limit: int = 500) -> None:
        """WALK1-4 F2: the Kobo mini-depth jobs (roles-4 from commissioning) number in the hundreds and the tick's mini
        stage takes at most 10 per Site, so prepare drains them with the worker's own CLI until a pass leaves none due."""
        total = 0
        while True:
            done = self.py("-m", "assetops_backend.mini_depth.worker", "run-pending", "--limit", str(limit),
                           label="mini-depth")
            line = [x for x in done.stdout.splitlines() if x.startswith("[")]
            outcomes = json.loads(line[-1]) if line else []
            failed = [o for o in outcomes if o.get("status") == "FAILED"]
            if failed:
                raise SystemExit(f"mini-depth FAILED: {failed[:3]}")
            total += len(outcomes)
            if len(outcomes) < limit:
                break
        say(f"  mini-depth: {total} jobs processed")

    def tick(self, times: int = 1) -> dict | None:
        """CH5c-R7 F5: the tick without its pre-build stage, then the Performance comparison (a new report moves
        `F`), then the pre-build alone in the serve env, so the next request after a loop tick is a hit.
        OWN-G2 (R2-G2 Q9 c): each tick's report (the last stdout line that parses as a JSON object) is written to
        `<work>/last-tick.json`, a stale file is removed when no line parses, and the last report is returned."""
        report = None
        for _ in range(times):
            done = self.py(*TICK, "--no-prebuild", label="tick", check=False, serve_env=True)
            say("  tick: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:160])
            report = demo_rows.last_json_object(done.stdout)
            path = self.work / "last-tick.json"
            if report is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        self.performance_and_prebuild()
        return report

    def read_site_mark(self, site: str) -> str | None:
        """E4 D-E4.8 (C4): the Site's DB watermark, the predicate of `postgres_response_store.read_watermark` for one
        Site (the tenant's rows for the Site plus the tenant-wide NULL rows), on one short read-only connection."""
        import psycopg

        url = self.url.replace("postgresql+psycopg://", "postgresql://")
        try:  # review M1: an unreadable mark is "due", never an error that ends the serve loop
            with psycopg.connect(url, autocommit=True) as c:
                row = c.execute("SELECT t.id, s.id FROM site s JOIN tenant t ON t.id = s.tenant_id "
                                "WHERE t.slug = 'demo' AND s.site_code_key = lower(%s)", (site,)).fetchone()
                if row is None:
                    return None
                count = c.execute("SELECT count(*) FROM chain_input_change WHERE (tenant_id = %s OR "
                                  "tenant_id IS NULL) AND (site_id = ANY(%s) OR site_id IS NULL)",
                                  (row[0], [row[1]])).fetchone()[0]
        except psycopg.Error:
            return None
        return f"cic:{count}"

    def performance_and_prebuild(self) -> None:
        marks_path = self.work / PERFORMANCE_MARKS_FILE
        marks = read_marks(marks_path)
        for site in ("KOBO-001",) + (("KISIWA-001",) if "kisiwa" in self.story().get("sites", ()) else ()):
            report_dir = self.tree / "var" / "evidence" / "migration-performance" / site.lower()
            mark = self.read_site_mark(site)  # before the run: a write during the run forces a rerun next time
            if not performance_due(site, mark, marks, report_dir):
                say(f"  performance: skipped (no change since mark {mark})")
                continue
            done = self.py("-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", site,
                           label="performance", check=False)
            say("  performance: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:160])
            if mark is not None and done.returncode == 0:
                marks[site] = mark
                write_marks(marks_path, marks)
        self.write_prebuilt_routes()  # E4 D-E4.1: the list follows the calendar and the added dates
        done = self.py("-m", "assetops_backend.scheduling.run", "prebuild", label="prebuild", check=False,
                       serve_env=True)
        say("  prebuild: " + (done.stdout.strip().splitlines() or ["(no output)"])[-1][:160])
        refusal = prebuild_refusal(done.stdout)
        if refusal is not None:  # INFRA-1 (D-E5.47) rule 5: a DEGRADED prebuild fails the build like FAILED
            raise PrebuildRefused(refusal)

    # ---- the R8 drain (DD1b2-R6 O2, R7 Q1-Q4) -----------------------------------------------------------------
    def counts(self) -> dict:
        done = self.py(str(self.tree / "tools" / "demo_combined_drain.py"), "counts", label="drain-counts",
                       cwd=self.tree / "backend" / "tests")
        return json.loads([x for x in done.stdout.splitlines() if x.startswith("{")][-1])

    def raise_deferred_drain(self) -> None:
        """DD1b2-R8 C1: after the self-check, a deferred drain failure ends the prepare with a non-zero exit."""
        if self.drain_failures:
            self.step = "drain (deferred)"
            raise SystemExit(f"DRAIN FAILED (deferred): {list(self.drain_failures)}")

    def drain(self, name: str = "drain") -> dict:
        """Tick (raw, no pre-build) until every count is 0: dirty rows, pending `snapshots` and `threads` events, Kobo
        mini jobs still PENDING or LEASED, live opportunity jobs. N is read after the first tick, as the maximum over
        Sites of ceil((dirty + snapshots pending) / 200) + 2. Past N the drain goes on while the counts move
        (`over_n`); past 2N or on two flat ticks it fails with the counts. Performance and pre-build run once after.

        DD1b2-R8 C1: a non-zero tick is recorded per Site (the `failure` triple) and does not stop the drain. Any
        failure (a counts child that crashes or prints no JSON, a fail verdict) writes `<name>.json` with
        `verdict: "fail"`. Inside `prepare` (`defer_drain`) the prepare then goes on and ends non-zero after the
        self-check; elsewhere (`tick --until-drained`) the failure raises, so the presenter sees exit 1."""
        import demo_combined_drain as dr

        t0 = time.monotonic()
        history: list[dict] = []
        n, ticks, over_n, log, failure = None, 0, False, [], None
        try:
            history.append(self.counts())
            say(f"  {name}: start " + json.dumps({k: {f: v[f] for f in dr.FIELDS} for k, v in history[0].items()}))
            while True:
                done = self.py(*TICK, "--no-prebuild", label=f"{name}-tick", check=False, serve_env=True)
                ticks += 1
                failed = dr.tick_failures(done.stdout) if done.returncode != 0 else None
                history.append(self.counts())
                n = dr.n_for(history[-1]) if n is None else n
                verdict, reason = dr.step(history, ticks, n)
                over_n = over_n or verdict == "over_n"
                log.append({"tick": ticks, "counts": {k: {f: v[f] for f in dr.FIELDS} for k, v in history[-1].items()},
                            "total": dr.total(history[-1]), "verdict": verdict,
                            **({"tick_rc": done.returncode, "tick_failure": failed} if failed else {})})
                say(f"  {name}: tick {ticks}/N={n}: total {dr.total(history[-1])} ({verdict})"
                    + (f" [tick exited {done.returncode}: {json.dumps(failed)[:200]}]" if failed else ""))
                if verdict == "fail":
                    failure = f"{reason}; counts {json.dumps(history[-1])}"
                    break
                if verdict == "done":
                    break
        except SystemExit as exc:  # the counts child crashed (its own FAILED exit); the wall cap is not ours to absorb
            if str(exc).startswith("WALL CAP"):
                raise
            failure = f"counts failed: {str(exc)[:600]}"
        except (IndexError, ValueError, KeyError) as exc:  # the counts child printed no JSON line, or an odd one
            failure = f"counts output unreadable: {type(exc).__name__}: {exc}"
        self.drains[name] = round(time.monotonic() - t0, 1)
        record = {"name": name, "verdict": "fail" if failure else "done", "reason": failure, "ticks": ticks, "N": n,
                  "over_n": over_n, "seconds": self.drains[name], "start": history[0] if history else None,
                  "end": history[-1] if history else None, "log": log}
        (self.work / f"{name}.json").write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
        if failure and not self.defer_drain:
            raise SystemExit(f"DRAIN FAILED: {name}: {failure}")
        refused = None
        try:
            self.performance_and_prebuild()
        except PrebuildRefused as exc:  # INFRA-1 fix round: recorded, not raised mid-drain (the self-check still runs)
            refused = str(exc.code)
            say(f"  {name}: PREBUILD REFUSED (deferred): {refused[:300]}")
        if failure:
            self.drain_failures = (*self.drain_failures, f"{name}: {failure}")
            say(f"  {name}: FAILED (deferred): {failure[:300]}")
        else:
            say(f"  {name}: drained in {ticks} ticks (N={n}, over_n={over_n}) [{self.drains[name]} s]")
        if refused:
            self.drain_failures = (*self.drain_failures, f"{name}: {refused}")
            if not self.defer_drain:
                raise SystemExit(f"DRAIN FAILED: {name}: {refused}")
        return record

    # ---- add-day (DEMO-SPARSE U4) -----------------------------------------------------------------------------
    def delivered_days(self, site_code: str) -> set[str]:
        """Site-local days holding delivered (accepted) evidence for the Site: the append-only refusal basis. Local, not
        UTC: a full day's night starts at 21:00Z the day before (DD1a2-R), which is not evidence on that earlier day.
        An interval row counts on the day its span began (DD1b2-R2): a rest run's closing row has its source time at the
        next local midnight and must not make that next day "already delivered"."""
        import psycopg

        with psycopg.connect(PG_ADMIN.rsplit("/", 1)[0] + "/" + self.db, autocommit=True) as c:
            rows = c.execute(
                "SELECT DISTINCT to_char(COALESCE(e.interval_start, e.source_time) AT TIME ZONE s.timezone, 'YYYY-MM-DD') FROM accepted_evidence e "
                "JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
                "JOIN site s ON s.id = e.site_id WHERE s.site_code = %s", (site_code,)).fetchall()
        return {r[0] for r in rows}

    def db_now(self) -> datetime:
        import psycopg

        with psycopg.connect(PG_ADMIN.rsplit("/", 1)[0] + "/" + self.db, autocommit=True) as c:
            return c.execute("SELECT clock_timestamp()").fetchone()[0]

    def add_day(self, site_code: str, kind: str, day: str | None = None, as_kind: str | None = None,
                assess_now: bool = False) -> dict:
        """Append one story day, live on real time (sheet U4). Refuses with a `StoryDaysError` code. OWN-G1: a
        KISIWA-001 night (`--kind normal|delivery`, `--day S+Nd`) runs as a one-night `add-dates` without the check."""
        story = self.story()
        if site_code == "KISIWA-001":
            if as_kind is not None or assess_now:
                raise sd.StoryDaysError("OPTION_NOT_FOR_KISIWA", "--as and --assess-now do not apply to Kisiwa nights.")
            import demo_combined_kisiwa as kis

            night = (sd.offset_date(at(story["S"]), sd.day_offset(day)) if day
                     else kis.last_night(story["kisiwa"], kis.read_days(self.work)) + timedelta(days=1))
            return self.add_dates("KISIWA-001", night, night, kind, no_check=True)
        site = sd.CODE_SITE.get(site_code)
        if site is None:
            raise sd.StoryDaysError("UNKNOWN_KIND", f"--site must be one of {sorted(sd.CODE_SITE)}")
        if assess_now and kind == "late":
            raise sd.StoryDaysError("UNKNOWN_KIND", "--assess-now is for non-late kinds; a late day waits for a tick")
        busy = self.hold_busy(f"add-day {site_code} {kind}")
        try:
            return self._add_core_day(story, site_code, kind, day=day, as_kind=as_kind, assess_now=assess_now)
        finally:
            busy.unlink(missing_ok=True)

    def hold_busy(self, what: str) -> Path:
        busy = self.work / ".busy"
        try:
            fd = os.open(busy, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise SystemExit(f"Refused: another prepare/add-day holds {busy}")
        os.write(fd, f"{what} pid={os.getpid()}\n".encode())
        os.close(fd)
        return busy

    def _add_core_day(self, story: dict, site_code: str, kind: str, day: str | None = None,
                      as_kind: str | None = None, assess_now: bool = False) -> dict:
        """One Kobo / Cold / EV day under a held `.busy` (the body `add-day` always had)."""
        site = sd.CODE_SITE[site_code]
        days_path = self.work / "days.json"
        doc = json.loads(days_path.read_text(encoding="utf-8"))
        current = sd.from_payload(doc["days"])
        # DD1a2-R Q8.3: a full-day kind is several runs, delivered in source-time order
        runs = sd.plan_add_runs(doc["doc"], current, site, kind, at(story["S"]), self.db_now(), day=day,
                                as_kind=as_kind, delivered_days=self.delivered_days(site_code),
                                installs={n: at(v) for n, v in story["installs"].items()})
        if assess_now and runs[0].has_run:
            runs = [sd.DayRun(**{**r.__dict__, "assess": "build"}) for r in runs]
        planned = next(r for r in runs if not r.complement_of)
        out: dict = {"day": planned.day, "kind": planned.kind, "assess": planned.assess, "runs": len(runs)}
        if planned.has_run:
            child = self.tree / "tools" / f"demo_combined_{site}.py"
            if site != "kobo" and not child.is_file():
                raise SystemExit(f"add-day for {site_code} is not built yet")
            self.deadline = time.monotonic() + 2 * 140 * len(runs)
            payload = planned.payload() if len(runs) == 1 else [r.payload() for r in runs]
            try:
                done = self.py(str(child), "add-day", self.url, str(self.work), json.dumps(payload),
                               cwd=self.tree / "backend" / "tests", label=f"add-day-{site}")
            finally:
                self.deadline = None  # OWN-G1: the per-day cap must not bound the ticks that follow
            line = [x for x in done.stdout.splitlines() if x.startswith('{"added"')]
            out.update(json.loads(line[-1]) if line else {})
            if site == "kobo" and planned.assess == "build":
                self.drain_mini()
        # a filled `missing` day replaces its no-run entry (R4 FILL-1)
        doc["days"] = [d for d in doc["days"] if not (d["site"] == site and d["day"] == planned.day
                                                      and d["received_at"] is None)]
        doc["days"].extend(r.payload() for r in runs)
        days_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        say(f"added {site_code} {planned.day} {planned.kind}" +
            ("" if not planned.has_run else
             " (assessed now)" if planned.assess == "build" else " (not analysed yet: the next serve tick assesses it)"))
        return out

    def add_dates_line(self) -> str:
        """R2-G1 Q9 d: `serve`'s one catch-up line."""
        return f"python tools/demo_combined.py --db {self.db} --work {self.work.relative_to(REPO).as_posix()} add-dates"

    # ---- add-dates (OWN-GAPS §4, R2-G1) -------------------------------------------------------------------------
    def site_zones(self) -> dict[str, str]:
        """R2-G1 header: each Site's timezone from the build's `site` row."""
        import psycopg

        with psycopg.connect(PG_ADMIN.rsplit("/", 1)[0] + "/" + self.db, autocommit=True) as c:
            return {r[0]: r[1] for r in c.execute("SELECT site_code, timezone FROM site").fetchall()}

    def kisiwa_child(self, verb: str, *args: str, label: str, seconds: int) -> tuple[int, dict | None, str]:
        """A tree Kisiwa child in the serve env (R2-G1 header); its last JSON line, or the refusal it exited with."""
        self.deadline = time.monotonic() + seconds
        try:
            done = self.py(str(self.tree / "tools" / "demo_combined_kisiwa.py"), verb, self.url, str(self.work), *args,
                           cwd=self.tree / "backend" / "tests", label=label, check=False, serve_env=True)
        finally:
            self.deadline = None
        lines = [json.loads(x) for x in done.stdout.splitlines() if x.startswith("{")]
        return done.returncode, (lines[-1] if lines else None), done.stdout

    @staticmethod
    def child_refusal(output: str) -> sd.StoryDaysError | None:
        """A child's `StoryDaysError` exit ("CODE: detail" as its last line), re-raised in the parent."""
        tail = [x for x in output.strip().splitlines() if x.strip()]
        m = re.match(r"^([A-Z][A-Z_]+): (.*)$", tail[-1]) if tail else None
        return sd.StoryDaysError(m.group(1), m.group(2)) if m else None

    def add_dates(self, site_arg: str = "all", date_from: Any = None, date_to: Any = None, kind: str | None = None,
                  dry_run: bool = False, no_check: bool = False) -> dict:
        """OWN-G1: add the missing dates for the selected Sites, date-major (each Site one date, then one tick), then
        `finish check`. Whole-command refusals first; nothing is written before they pass."""
        import demo_combined_kisiwa as kis

        story = self.story()
        sites = select_sites(site_arg, story)
        if (self.work / ".busy").exists():
            raise SystemExit(f"Refused: another prepare/add-day holds {self.work / '.busy'}")
        days_json = json.loads((self.work / "days.json").read_text(encoding="utf-8"))
        entries = kis.read_days(self.work)
        db_now, zones = self.db_now(), self.site_zones()
        delivered = {SITE_CODE[s]: self.delivered_days(SITE_CODE[s]) for s in sites if s != "kisiwa"}
        plan = plan_add_dates(story, days_json, entries, sites=sites, date_from=date_from, date_to=date_to, kind=kind,
                              db_now=db_now, zones=zones, delivered=delivered)
        skipped = [{"site": SITE_CODE[s], "date": d, "reason": r,
                    **({"text": "the night is not over yet (it ends "
                                + kis.night_end(story["kisiwa"], d).astimezone(kis.ZoneInfo(zones["KISIWA-001"]))
                                .strftime("%H:%M") + " local)"} if r == NIGHT_NOT_OVER else {})}
                   for s, p in plan["sites"].items() for d, r in p["skipped"]]
        no_session = [{"site": SITE_CODE[s], "date": d} for s, p in plan["sites"].items() for d in p["no_session"]]
        left_empty = {SITE_CODE[s]: p["left_empty"] for s, p in plan["sites"].items() if p["left_empty"]}
        # The preflight is read-only (its one request is rejected as invalid), so a dry run runs it too: a dry run never
        # shows a plan for a request the real run would refuse.
        rc, line, _ = self.kisiwa_child("preflight", label="add-dates-preflight", seconds=600)
        refusal = preflight_refusal(rc, (line or {}).get("preflight"), "kisiwa" in sites)
        if refusal is not None:
            raise refusal
        say("add-dates plan: " + json.dumps({SITE_CODE[s]: [d.isoformat() for d in p["dates"]]
                                             for s, p in plan["sites"].items()}))
        if dry_run:
            for line in plain_lines([], skipped, no_session, left_empty):
                say(line)
            say("--dry-run: nothing added (the build checks run only on a real run).")
            return {"plan": plan}
        busy = self.hold_busy("add-dates")
        added: list[dict] = []
        check = "not run"
        try:
            for d in plan["order"]:
                today: list[dict] = []
                for site in sites:
                    p = plan["sites"][site]
                    if d not in p["dates"]:
                        continue
                    if site == "kisiwa":
                        today.append(self.add_kisiwa_night(d, p["kind"]))
                        continue
                    try:
                        out = self._add_core_day(story, SITE_CODE[site], p["kind"],
                                                 day=f"S{sd.date_offset(d, at(story['S'])):+d}d")
                    except sd.StoryDaysError as refusal:
                        if refusal.error_code not in ("DUPLICATE_DAY", "DAY_HAS_EVIDENCE"):
                            raise
                        skipped.append({"site": SITE_CODE[site], "date": d, "reason": ALREADY_PRESENT})
                        continue
                    today.append({"site": SITE_CODE[site], "date": d, "kind": out["kind"],
                                  "records": [], "checked": "tick"})
                if today:
                    codes = ", ".join(a["site"] for a in today)
                    try:
                        added += self.settled_date(d, today)
                    except SystemExit as exc:  # R5.2 item 5: earlier dates stay (append-only)
                        if not str(exc).startswith(("DRAIN FAILED", "mini-depth FAILED")):
                            raise
                        raise SystemExit(f"{codes} {d.isoformat()}: the added data did not finish processing; {exc}. "
                                         "prepare a fresh build before a demo.") from None
            import demo_combined_drain as dr

            if dr.total(self.counts()) > 0:  # R5.2 item 3: work left by a crashed or stopped earlier run
                say("settling work left from an earlier run")
                try:
                    self.settle("settle-close")
                except SystemExit as exc:
                    raise SystemExit(f"the added data did not finish processing; {exc}. "
                                     "prepare a fresh build before a demo.") from None
            if not no_check:
                report = self.tick()  # R6.1: the check reads the served state; the schedule must have just run
                if "kisiwa" in story["sites"]:
                    report, extra = retry_until_visited(report, lambda: self.tick(times=1),
                                                        sleep=lambda s: time.sleep(s))
                    if extra:
                        say(f"  tick: {extra} extra tick(s) for KISIWA-001's fuel_night stage")
                check = self.finish_check()
        except BaseException:
            if added:  # L3: the process is append-only; say what is now in the build before the error
                say("The command stopped. These dates were already added and settled:")
                for text in plain_lines(added, [], [], {}):
                    say(text)
            raise
        finally:
            busy.unlink(missing_ok=True)
        summary = {"added": [{**a, "date": a["date"].isoformat()} for a in added],
                   "skipped": [{**s, "date": s["date"].isoformat()} for s in skipped],
                   "left_empty": {k: [d.isoformat() for d in v] for k, v in left_empty.items()},
                   "no_session": [{**s, "date": s["date"].isoformat()} for s in no_session], "finish_check": check}
        say(json.dumps(summary, default=str))
        for text in plain_lines(added, skipped, no_session, left_empty):
            say(text)
        if check.startswith("FAIL"):
            raise SystemExit("This build no longer passes its checks; prepare a fresh one before a demo.")
        return summary

    def settle(self, name: str) -> dict:
        """R5.2: run the queued work of the added data through the product's own producers until nothing is due:
        the mini-depth worker (no per-tick bound), then the scheduled tick until every drain count is 0."""
        self.drain_mini()
        return self.drain(name)

    def settled_date(self, d: Any, today: list[dict]) -> list[dict]:
        """R5.2 item 2: one date's items, checked only once the product's queue for the data is empty."""
        if any(a["site"] == "KISIWA-001" for a in today):
            self.drain_mini()
            self.tick_and_verify(today)
            record = self.drain(f"settle-{d.isoformat()}")
        else:
            record = self.settle(f"settle-{d.isoformat()}")
        failures = [e["tick_failure"] for e in record["log"] if e.get("tick_failure")]
        for item in today:
            if item["site"] != "KISIWA-001":
                item["checked"] = f"settled ({record['ticks']} ticks)"
            item["tick_failures"] = failures
        return today

    def add_kisiwa_night(self, night: Any, kind: str | None) -> dict:
        """§4.5 steps 1-6 in the tree child (the entry is PUBLISHED when it returns)."""
        payload = json.dumps({"night_date": night.isoformat(), "kind": kind})
        rc, line, output = self.kisiwa_child("add-day", payload, label="add-dates-kisiwa", seconds=2 * 900)
        if rc != 0 or line is None or "added" not in line:
            raise self.child_refusal(output) or SystemExit(f"FAILED: Kisiwa add-day {night} (exit {rc})\n{output[-3000:]}")
        entry = line["added"]
        ticket = next((a["ticket"]["reference"] for a in entry["actions"] if a["kind"] == "FUEL_DELIVERY"), None)
        return {"site": "KISIWA-001", "date": night, "kind": entry["kind"], "ticket": ticket,
                "records": [r["code"] for r in entry["records"]], "checked": None}

    def tick_and_verify(self, today: list[dict]) -> list[dict]:
        """§4.4: one tick after the date; then each added Kisiwa night verified (R2-G1 Q6: up to two more ticks, 30 s
        apart, while its window is absent)."""
        import demo_combined_kisiwa as kis

        report = self.tick()  # R2-G2 Q9 c: the tick returns its parsed report (None on a build before G2)
        for item in today:
            if item["site"] != "KISIWA-001":
                continue
            for attempt in range(3):
                visited, stage = kisiwa_stage(report)
                payload = json.dumps({"night_date": item["date"].isoformat(), "fuel_night": stage if visited else None})
                rc, line, output = self.kisiwa_child("verify-day", payload, label="add-dates-verify", seconds=600)
                if rc != 0 or line is None or "verified" not in line:
                    raise self.child_refusal(output) or SystemExit(f"FAILED: Kisiwa verify-day (exit {rc})\n"
                                                                   f"{output[-3000:]}")
                result = line["verified"]
                if result["state"] == "DONE":
                    item["checked"] = f"{result['entry']['window']['state']} (revision {result['entry']['window']['revision']})"
                    break
                if result["state"] == "UNEXPECTED" or attempt == 2:
                    raise sd.StoryDaysError("ADD_NIGHT_UNEXPECTED", f"KISIWA-001 {item['date'].isoformat()}: "
                                                                    f"{result['line']}")
                time.sleep(kis.WAIT_POLL_SECONDS)
                report = self.tick()
        return today

    def finish_check(self) -> str:
        """§4.4: `finish check` on the build (writes `<work>/check.json`); "PASS" or "FAIL <rows>"."""
        done = self.py(str(self.tree / "tools" / "demo_combined_finish.py"), "check", self.url, str(self.work),
                       cwd=self.tree / "backend" / "tests", label="add-dates-check", check=False)
        if done.returncode == 0:
            return "PASS"
        return "FAIL " + (",".join(failed_rows(self.work / "check.json")) or f"exit {done.returncode}")

    # ---- reading -----------------------------------------------------------------------------------------------
    def links(self, web: int) -> None:
        story = self.story()
        days_file = self.work / "days.json"
        story_days = json.loads(days_file.read_text(encoding="utf-8"))["days"] if days_file.is_file() else []
        kobo = self.work / "kobo.json"
        k = json.loads(kobo.read_text(encoding="utf-8")) if kobo.is_file() else None
        kis = self.work / "kisiwa.json"
        kisiwa = json.loads(kis.read_text(encoding="utf-8")) if kis.is_file() else None
        rows = story_links(story, story_days, k, web, kisiwa)
        say(f"Story day S = {story['S_date']} (dates move on every rebuild; quote them from here). Code {story['code']}.")
        if kisiwa is not None and "kisiwa" in story["sites"]:
            import demo_combined_kisiwa as kis

            rows += added_night_links(kis.read_days(self.work), web)  # OWN-G1 §4.5 `links`
        for label, url in rows:
            say(f"  {label}\n    {url}")
        days_path = self.work / "days.json"
        if days_path.is_file():
            say("Story days (kind per day; missing = no run, no delivery):")
            current = sd.from_payload(json.loads(days_path.read_text(encoding="utf-8"))["days"])
            for site in story["sites"]:
                cells = [f"{r.day} S{r.offset:+d}d {r.kind}" + (f" (as {r.as_kind})" if r.as_kind else "")
                         for r in sorted((r for r in current if r.site == site), key=lambda r: r.offset)]
                say(f"  {SITE_CODE[site]}: " + "; ".join(cells))

    def serve(self, port: int, web: int) -> None:
        self.story()
        self.write_prebuilt_routes()  # E4 D-E4.1: before the serve env is built
        logs = self.work / "logs"
        logs.mkdir(exist_ok=True)
        log = open(logs / f"api-{port}.log", "w", encoding="utf-8")
        api = subprocess.Popen([str(PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                               cwd=str(self.tree / "host"), env=self.serve_env(), stdout=log,
                               stderr=subprocess.STDOUT)
        import urllib.request

        for _ in range(240):
            if api.poll() is not None:
                raise SystemExit(f"API exited; see {log.name}")
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2).read()
                break
            except Exception:
                time.sleep(0.5)
        else:
            _kill_tree(api.pid)
            raise SystemExit(f"API did not answer on port {port}")
        say(f"API on http://127.0.0.1:{port} (PID {api.pid}). Walkthrough-only schedule loop: one tick every "
            f"{TICK_EVERY_SECONDS} s, then the Performance comparison; it stops with serve.")
        say(f'Frontend, from frontend/:  $env:ASSETOPS_API_PORT="{port}"; npm.cmd run dev -- --port {web} --strictPort')
        self.links(web)
        if (self.work / "days.json").is_file():
            say("Bring every Site up to yesterday (adds the missing dates, then checks the build):")
            say(f"  {self.add_dates_line()}")
        try:
            warmed = False
            while api.poll() is None:
                try:
                    self.tick()
                except PrebuildRefused as exc:  # INFRA-1 fix round: a degraded tick is logged; the API keeps serving
                    say(f"  PREBUILD REFUSED (serving continues): {str(exc.code)[:300]}")
                if not warmed:
                    # Review item 8: after the first tick, warm the story-week Portfolio once before "ready:".
                    warmed = True
                    prewarm(port, self.story())
                for _ in range(TICK_EVERY_SECONDS):
                    if api.poll() is not None:
                        break
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            if api.poll() is None:
                _kill_tree(api.pid)

    def drop(self) -> None:
        import psycopg

        recorded = self.marker_db()
        with psycopg.connect(PG_ADMIN, autocommit=True) as c:
            if self.exists(c, self.db):
                if recorded != self.db:
                    raise SystemExit(f"Not dropping {self.db}: {self.work / MARKER} does not record that this tool "
                                     f"made it (recorded: {recorded or 'nothing'})")
                c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")
                say(f"dropped database {self.db}")
            else:
                say(f"database {self.db} does not exist")
        if self.work.exists():
            if recorded != self.db:
                raise SystemExit(f"Not removing {self.work}: its marker does not record database {self.db}")
            shutil.rmtree(self.work)
            say(f"removed {self.work}")


def _kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        return
    import signal

    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _cli_date(text: str):
    """`--from` / `--to`: a calendar date in each Site's own timezone; `yesterday` is the default (None)."""
    if text == "yesterday":
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not YYYY-MM-DD or yesterday")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tools/demo_combined.py")
    parser.add_argument("--db", required=True, help="private database, assetops_demo3_<name>_test or assetops_polish_<name>_test")
    parser.add_argument("--work", required=True, help="work folder var/demo3* or var/polish* under this repository")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--sites", default=",".join(SITES),
                   help="a subset of kobo,cold,ev,kisiwa (K7-F: the default is all four Sites)")
    p.add_argument("--no-finish", action="store_true", help="development only: skip objectives/comparisons/ticks")
    p.add_argument("--days", default=None, help="day list (default backend/conversions/demo-story-days-v4.json; "
                   "backend/conversions/demo-story-days-v3.json is the D-E5.12 rollback)")
    p.add_argument("--baseline", default="b22", choices=sorted(sd.BASELINE_FROM),
                   help="b16: the owner's fallback if the rehearsal measures the whole prepare over 3 h")
    p.add_argument("--cap-seconds", type=int, default=None,
                   help="wall cap for the whole prepare (default twice the expected sum; the rehearsal uses 10800)")
    lk = sub.add_parser("links")
    lk.add_argument("--web-port", type=int, default=WEB_PORT)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=API_PORT)
    s.add_argument("--web-port", type=int, default=WEB_PORT)
    tk = sub.add_parser("tick")
    tk.add_argument("--until-drained", action="store_true",
                    help="DD1b2-R6 O2: raw ticks until the R8 counts are 0 (a live add: run this, then show the board)")
    ac =sub.add_parser("after-children", help="development only (DD1b2-R probe): the real after_children on a prepared work folder")
    ac.add_argument("--cap-seconds", type=int, default=1800)
    ac.add_argument("--stop-before-mill", action="store_true", help="drain_mini and backfill step a only, then stop (clone here)")
    ad = sub.add_parser("add-day")
    ad.add_argument("--site", required=True, choices=sorted(SITE_CODE.values()))
    ad.add_argument("--kind", required=True, help="KISIWA-001: normal or delivery")
    ad.add_argument("--day", default=None, help="S[+-]Nd; default the day after the Site's last story day")
    ad.add_argument("--as", dest="as_kind", default=None, choices=sd.LATE_AS, help="late Kobo day: the run it carries")
    ad.add_argument("--assess-now", action="store_true", help="non-late kinds: assess and match in process")
    adds = sub.add_parser("add-dates", help="OWN-G1: add the missing dates up to yesterday, then finish check")
    adds.add_argument("--site", default="all", help="all, or a comma list of KOBO-001,COLD-LAB-001,EV-LAB-001,KISIWA-001")
    adds.add_argument("--from", dest="date_from", type=_cli_date, default=None,
                      help="YYYY-MM-DD; default per Site: the day after its last day")
    adds.add_argument("--to", dest="date_to", type=_cli_date, default=None,
                      help="YYYY-MM-DD or yesterday (default; Kisiwa: its last finished night)")
    adds.add_argument("--kind", default=None, help="only with one Site and one date")
    adds.add_argument("--dry-run", action="store_true", help="print the plan and the refusals, add nothing. It runs the read-only preflight, so the build's DB "
                                                          "and serve environment must be reachable; it writes only the child's log under <work>/logs")
    adds.add_argument("--no-check", action="store_true", help="skip the closing finish check (not for demo days)")
    sub.add_parser("drop")
    args = parser.parse_args(argv)
    demo = Demo(args.db, args.work)
    if args.cmd == "prepare":
        sites = tuple(s for s in args.sites.split(",") if s)
        if not set(sites) <= set(SITES):
            raise SystemExit(f"--sites must be a subset of {SITES}")
        try:
            demo.prepare(sites, finish=not args.no_finish, days_file=args.days, baseline=args.baseline,
                         cap_seconds=args.cap_seconds)
        finally:
            if demo.holds_busy:
                (demo.work / ".busy").unlink(missing_ok=True)
    elif args.cmd == "links":
        demo.links(args.web_port)
    elif args.cmd == "serve":
        demo.serve(args.port, args.web_port)
    elif args.cmd == "add-day":
        demo.add_day(args.site, args.kind, day=args.day, as_kind=args.as_kind, assess_now=args.assess_now)
    elif args.cmd == "add-dates":
        demo.add_dates(args.site, args.date_from, args.date_to, args.kind, dry_run=args.dry_run,
                       no_check=args.no_check)
    elif args.cmd == "tick":
        demo.story()
        if args.until_drained:
            demo.drain("tick-until-drained")
        else:
            demo.tick()
    elif args.cmd == "after-children":
        demo.deadline = time.monotonic() + args.cap_seconds
        built = json.loads((demo.work / "days.json").read_text(encoding="utf-8"))
        demo.after_children(demo.story(), built["days"], stop_before_mill=args.stop_before_mill)
    else:
        demo.drop()


if __name__ == "__main__":
    main()
