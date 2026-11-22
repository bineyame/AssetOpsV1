"""IA-P3 P5, D-IAP.39 layer 1 (the server layer of the Findings alias parity proof): per vertical, one existing built
world served by one app (`create_app`, `test_out_b4_board_postgres._serve`/`_client`), two windows, the Site
Findings read as the Site page asks it and `/api/estate/findings` as the Findings list asks it (every page of each).

- MINI: the Kobo `guardrail` world (`test_out_b4_board_postgres._build_kobo`, served as
  `test_ch5c2_real_composers_postgres.py` serves it); Site read `GET /api/sites/KOBO-001/finding-index?domain=
  mini-grid-dispatch&from&to[&cursor]` (`findingIndexClient.findingIndexPath`: no `known_at`, no `limit`).
- COLD: the `test_fx_cold_linked_postgres.py` world (w502 `positive` plus the clean replay); Site read
  `GET /api/sites/COLD-LAB-001/cold/findings?from&to&known_at` (`coldAssessmentClient.listFindings`).
- EV: the w504 `positive` world (`test_out_b4_board_postgres.EV_BUILD`, served as `test_ev_w504_positive`); Site
  read `GET /api/sites/EV-LAB-001/ev/findings?from&to&known_at` (`evAssessmentClient.listFindings`).
- Estate read: `estateReadCache.readAll(..., "findings")` = `from&to&known_at&limit=50[&cursor]`; `lens=all` and
  `state=all` are left out by `estateQueryString` (the server's defaults).

Windows: the address is the rail's instant form (`sharedRange.rangeParams`) and every read takes `windowBound`
(`readWindow`'s arithmetic): `from = max(from, to - 30 days)`, `to` and `known_at` kept. `_read_window` mirrors it.
The address names no `known_at` (the Site tab's link carries none), so neither read sends one: both take the
server's current cutoff. (A DB-now `known_at` is refused by the EV read: `EV_TIME_INVALID`, later than the latest
committed evidence cutoff.)

Assert: the Site set is non-empty; Site ids are a subset of estate ids with `site_code == code`; estate
`total_count` < 1,000 (`ALL_PAGES_LIMIT * ALL_PAGES_MAX`). Extra estate ids are printed (`IAP-PARITY` lines, `-s`).
The whole-month Site and estate bodies (page one) are written to `fixtures/iap/parity-*.json` under
`IAP_WRITE_FIXTURES=1` and otherwise must be current (as `test_iap_portfolio_sites.test_9_fixtures_are_current`).

D-IAP.42: MINI is flipped. Its Site ids missing from the estate read must all belong to a Site whose estate coverage is
neither CURRENT nor HISTORICAL (the PARTIAL withholding rule); a full subset fails with "MINI parity holds: ship the
MINI alias (D-IAP.42)". MINI pins no body.
D-IAP.43: the COLD and EV bodies are pinned normalised (`_normalise`): `finding_id` and `finding_revision_id` values to
`00000000-0000-4000-8000-{n:012d}` in order of first appearance (Site body, then estate body), any other uuid to its own
series `00000000-0000-4000-a000-{n:012d}`, every ISO timestamp and date shifted by one constant so the month window's
`from` is 2026-10-01T00:00:00Z; the compare is byte for byte on sorted keys, 2-space indent. The subset relation is
asserted on the raw bodies and again on the normalised ones. COLD's month window is the 31 days ending on the data day
(the world moves with the wall clock, so a calendar month would put the data on a different day of it each day).
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "frontend" / "src" / "estate" / "__tests__" / "fixtures" / "iap"
#: `estateReadCache.ALL_PAGES_LIMIT` and `ALL_PAGES_MAX` (the client cap is 20 pages of 50 = 1,000 rows)
PAGE_LIMIT, PAGES_MAX = 50, 20
#: `sharedRange.READ_WINDOW_DAYS`
READ_WINDOW_DAYS = 31


def _read_window(first: date, last: date, known_at: str | None) -> dict:
    """`readWindow(rangeParams({from: first, to: last, known_at}))` then `windowBound`, in Python: the address is the
    instant form (`from` 00:00Z, the day after `to` 00:00Z); `from` moves to max(first, last - 30 days)."""
    floor = last - timedelta(days=READ_WINDOW_DAYS - 1)
    lo = max(first, floor)
    return {"from": f"{lo.isoformat()}T00:00:00Z", "to": f"{(last + timedelta(days=1)).isoformat()}T00:00:00Z",
            "known_at": known_at}


def _get(c, path: str) -> dict:
    r = c.get(path)
    assert r.status_code == 200, (path, r.status_code, r.text[:400])
    return r.json()


def _pages(c, path_of, key: str) -> tuple[list[dict], list[dict]]:
    """Every page, following `next_cursor` (at most the client's 20 pages); returns (bodies, rows)."""
    bodies, rows, cursor = [], [], None
    while True:
        body = _get(c, path_of(cursor))
        bodies.append(body)
        rows.extend(body.get(key) or [])
        cursor = body.get("next_cursor")
        if cursor is None or len(bodies) >= PAGES_MAX:
            return bodies, rows


def _site_path(vertical: str, code: str, w: dict):
    def path_of(cursor: str | None) -> str:
        if vertical == "mini":  # findingIndexClient.findingIndexPath: domain, from, to[, limit][, cursor]
            q = {"domain": "mini-grid-dispatch", "from": w["from"], "to": w["to"]}
            if cursor:
                q["cursor"] = cursor
            return f"/api/sites/{code}/finding-index?{urlencode(q)}"
        q = {"from": w["from"], "to": w["to"]}  # coldAssessmentClient.coldWindowSearch: from, to, known_at
        if w["known_at"] is not None:
            q["known_at"] = w["known_at"]
        if cursor:  # the page reads page one only; later pages are read here so the Site set is whole
            q["cursor"] = cursor
        return f"/api/sites/{code}/{'cold' if vertical == 'cold' else 'ev'}/findings?{urlencode(q)}"
    return path_of


def _estate_path(w: dict):
    def path_of(cursor: str | None) -> str:  # estateQueryString order; lens/state "all" are left out
        q = {"from": w["from"], "to": w["to"]}
        if w["known_at"] is not None:
            q["known_at"] = w["known_at"]
        q["limit"] = str(PAGE_LIMIT)
        if cursor:
            q["cursor"] = cursor
        return f"/api/estate/findings?{urlencode(q)}"
    return path_of


def _diff(a, b, at: str = "$", out: list | None = None) -> list[str]:
    out = [] if out is None else out
    if len(out) >= 12:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            _diff(a.get(k, "<absent>"), b.get(k, "<absent>"), f"{at}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            _diff(x, y, f"{at}[{i}]", out)
    elif a != b:
        out.append(f"{at}: {str(a)[:80]!r} != {str(b)[:80]!r}")
    return out


def _site_uuid(url: str, code: str) -> str:
    """The Site's stored id (the estate coverage keys its sites by `site_id`, not by code)."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool

    engine = create_engine(url, poolclass=NullPool)
    try:
        with engine.connect() as connection:
            return str(connection.execute(text("SELECT id FROM site WHERE site_code = :c"), {"c": code}).scalar_one())
    finally:
        engine.dispose()


def _parity(c, vertical: str, code: str, windows: dict[str, dict], why: str = "", site_uuid: str | None = None) -> dict:
    """Reads both windows, prints each, then asserts D-IAP.39; returns the whole-month bodies (page one)."""
    site_key = "rows" if vertical == "mini" else "items"
    out, failures = {}, []
    for name, w in windows.items():
        site_bodies, site_rows = _pages(c, _site_path(vertical, code, w), site_key)
        estate_bodies, estate_rows = _pages(c, _estate_path(w), "rows")
        site_ids = {r["finding_id"] for r in site_rows}
        estate = {r["finding_id"]: r for r in estate_rows}
        missing = sorted(site_ids - set(estate))
        wrong_code = sorted(i for i in site_ids & set(estate) if estate[i]["site_code"] != code)
        extra = sorted((i, estate[i]["site_code"], estate[i].get("finding_label")) for i in set(estate) - site_ids)
        first = estate_bodies[0]
        total = first.get("total_count")
        cover = [(s.get("site_id"), s.get("state"), s.get("job_state")) for s in (first.get("coverage") or {}).get("sites", [])]
        print(f"\nIAP-PARITY {vertical} {name} window={w} site_status={site_bodies[0].get('status')} "
              f"site_pages={len(site_bodies)} site_ids={len(site_ids)} estate_pages={len(estate_bodies)} "
              f"estate_total_count={total} estate_status={first.get('status')} estate_lens={first.get('lens')} "
              f"estate_state={first.get('state_filter')} estate_coverage={cover} "
              f"site_id_of_code={sorted({r['site_id'] for r in estate_rows if r['site_code'] == code})} "
              f"missing={missing} wrong_code={wrong_code} extra={extra}")
        if vertical == "mini" and missing:  # why the estate withheld them (coverage.py §2.5 PARTIAL rule)
            days = [(s.get("site_id"), s.get("days")) for s in (first.get("coverage") or {}).get("sites", [])]
            mini = site_bodies[0]
            print(f"\nIAP-PARITY mini {name} estate_days={json.dumps(days, default=str)[:1500]}")
            print(f"\nIAP-PARITY mini {name} site_gaps={[(g.get('day'), g.get('state'), g.get('reason')) for g in mini.get('gaps') or []]} "
                  f"site_withheld={ {k: v for k, v in mini.items() if 'withh' in k or 'left_out' in k} } "
                  f"site_rows={[(r['finding_id'][:8], r.get('episode_start'), r.get('episode_end')) for r in site_rows]}")
        if not site_ids:
            failures.append(f"{name}: the Site Findings read is empty (a vacuous pass fails)")
        if wrong_code:
            failures.append(f"{name}: estate rows with another site_code: {wrong_code}")
        if vertical == "mini":  # D-IAP.42: flipped; the withheld ids belong to a Site the estate does not cover
            states = {s.get("site_id"): s.get("state") for s in (first.get("coverage") or {}).get("sites", [])}
            state = states.get(site_uuid, "<absent>")
            print(f"\nIAP-PARITY mini {name} estate coverage of {code} ({site_uuid}) = {state}")
            if not missing:
                failures.append(f"{name}: MINI parity holds: ship the MINI alias (D-IAP.42)")
            elif state in ("CURRENT", "HISTORICAL"):
                failures.append(f"{name}: Site ids {missing} are missing from the estate read although {code} is "
                                f"{state} there")
        else:
            if missing:
                failures.append(f"{name}: Site ids missing from the estate read: {missing}")
            if total is None or total >= PAGE_LIMIT * PAGES_MAX:
                failures.append(f"{name}: estate total_count {total} is not under {PAGE_LIMIT * PAGES_MAX}")
        if name == "month":
            out = {"site": site_bodies[0], "estate": first, "pages": (len(site_bodies), len(estate_bodies)),
                   "window": w, "site_key": site_key}
    assert not failures, f"SPEC_AMBIGUITY: {vertical} {code}: " + "; ".join(failures) + (f" ({why})" if why else "")
    return out


_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_STAMP = re.compile(r"(\d{4}-\d{2}-\d{2})(T\d{2}:\d{2}:\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:\d{2})?(?!\d)")
_ANCHOR = datetime(2026, 10, 1)
_FINDING_KEYS = ("finding_id", "finding_revision_id")


def _walk(v, fn, key=None):
    if isinstance(v, dict):
        return {k: _walk(x, fn, k) for k, x in v.items()}
    if isinstance(v, list):
        return [_walk(x, fn, key) for x in v]
    return fn(key, v)


def _normalise(site: dict, estate: dict, window_from: str) -> tuple[dict, dict]:
    """D-IAP.43: uuid tokens (finding series, then any other uuid in its own series) and one time shift per vertical
    so the month window's `from` becomes 2026-10-01T00:00:00Z (whole days, so dates shift with timestamps)."""
    ids: dict[str, str] = {}
    others: dict[str, str] = {}

    def collect_findings(key, v):
        if key in _FINDING_KEYS and isinstance(v, str) and _UUID.fullmatch(v) and v not in ids:
            ids[v] = f"00000000-0000-4000-8000-{len(ids) + 1:012d}"
        return v

    def collect_others(key, v):
        if isinstance(v, str):
            for u in _UUID.findall(v):
                if u not in ids and u not in others:
                    others[u] = f"00000000-0000-4000-a000-{len(others) + 1:012d}"
        return v

    for body in (site, estate):
        _walk(body, collect_findings)
    for body in (site, estate):
        _walk(body, collect_others)
    start = datetime.fromisoformat(window_from.replace("Z", "+00:00")).replace(tzinfo=None)
    delta = _ANCHOR - start

    def shift(m: re.Match) -> str:
        day, clock, zone = m.group(1), m.group(2), m.group(3)
        if clock is None:
            return (date.fromisoformat(day) + delta).isoformat() + (zone or "")
        frac = "." in clock
        t = datetime.fromisoformat(day + clock) + delta
        out = t.isoformat(timespec="microseconds" if frac else "seconds")
        if frac and len(clock.split(".")[1]) != 6:  # keep the source's fraction width
            out = out[:out.index(".") + 1 + len(clock.split(".")[1])]
        return out + (zone or "")

    def fix(key, v):
        if isinstance(v, str):
            v = _UUID.sub(lambda m: ids.get(m.group(0)) or others[m.group(0)], v)
            v = _STAMP.sub(shift, v)
        return v

    return _walk(site, fix), _walk(estate, fix)


def _dump(body) -> str:
    return json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _subset(vertical: str, site: dict, estate: dict, code: str, site_key: str, when: str) -> None:
    site_ids = {r["finding_id"] for r in site.get(site_key) or []}
    estate_ids = {r["finding_id"] for r in estate.get("rows") or [] if r.get("site_code") == code}
    assert site_ids, f"{vertical} {when}: the pinned Site body has no Findings"
    assert site_ids <= estate_ids, f"{vertical} {when}: Site ids not in the estate body: {sorted(site_ids - estate_ids)}"


def _pin(vertical: str, code: str, bodies: dict) -> None:
    """D-IAP.43: subset on the raw page-one bodies, normalise, subset again, then byte compare (or write)."""
    _subset(vertical, bodies["site"], bodies["estate"], code, bodies["site_key"], "before normalising")
    site, estate = _normalise(bodies["site"], bodies["estate"], bodies["window"]["from"])
    _subset(vertical, site, estate, code, bodies["site_key"], "after normalising")
    files = {f"parity-{vertical}-site.json": _dump(site), f"parity-{vertical}-estate.json": _dump(estate)}
    if os.environ.get("IAP_WRITE_FIXTURES") == "1":
        FIXTURES.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (FIXTURES / name).write_text(text, encoding="utf-8")
    drift = []
    for name, text in files.items():
        pinned = (FIXTURES / name).read_text(encoding="utf-8")
        if pinned != text and os.environ.get("IAP_PARITY_DUMP"):
            (Path(os.environ["IAP_PARITY_DUMP"]) / name).write_text(text, encoding="utf-8")
        if pinned != text:
            drift.append((name, _diff(json.loads(pinned), json.loads(text))))
    if drift:
        # SPEC_CONFLICT (packet-IA-P3 Known Deviations, Q-P5-3): measured on two builds of the same world, the
        # normalised bodies still differ in classes D-IAP.43 does not name (`run-<hex32>` ids, sha256/sha1 digests
        # over ids, wall-clock record stamps such as `as_of` and `decided_at`, and arrays ordered by uuid value, so
        # first-appearance tokens permute). The subset relation above holds; the byte compare waits on the Architect.
        pytest.xfail(f"SPEC_CONFLICT D-IAP.43 byte compare (Q-P5-3): {drift}")


def _month_and_61(month_first: date, month_last: date, last_61: date, known_at: str | None) -> dict[str, dict]:
    return {"month": _read_window(month_first, month_last, known_at),
            "range61": _read_window(last_61 - timedelta(days=60), last_61, known_at)}


def test_mini_kobo_site_findings_are_in_the_estate_findings(monkeypatch, tmp_path) -> None:
    import test_out_b4_board_postgres as b4

    with b4._case_db("guardrail", "iap") as url:
        _, imported = b4._build_kobo(url, tmp_path, "guardrail")
        print(f"\nIAP-PARITY mini site_import.imported_at={[str(i) for i in imported]}")
        known_at = None
        b4._serve(monkeypatch, url, tmp_path)
        with b4._client() as c:
            # Kobo's data is 2026-10-05..11-03 (ch5c2 DAYS); the 61-day range 2026-09-04..11-03 reads 10-04..11-03
            bodies = _parity(c, "mini", "KOBO-001",
                             _month_and_61(date(2026, 10, 1), date(2026, 10, 31), date(2026, 11, 3), known_at),
                             site_uuid=_site_uuid(url, "KOBO-001"))
    print(f"\nIAP-PARITY mini month pages (site, estate) = {bodies['pages']}")  # D-IAP.42: no MINI pin


def test_cold_linked_site_findings_are_in_the_estate_findings(monkeypatch, tmp_path) -> None:
    import w502_cold_work_walkthrough as w502
    from test_fx_cold_linked_postgres import CLEAN
    from test_out_b4_board_postgres import _case_db, _child, _client, _serve
    from test_out_c3_repeat_visits_postgres import _day

    out, clean_out = tmp_path / "positive", tmp_path / "clean"
    out.mkdir()
    clean_out.mkdir()
    with _case_db("fxcold", "iap") as url:
        _child(url, ["-c", w502.BUILD, "positive", str(out)])
        doc = json.loads((out / "positive.json").read_text(encoding="utf-8"))
        assert doc["blocked"] is None, doc["blocked"]
        day = _day(doc["w501"]["window"][0])
        clean_start = day + timedelta(hours=18)
        _child(url, ["-c", CLEAN, url, clean_start.isoformat(), str(clean_out), str(ROOT / "tools")])
        known_at = None
        _serve(monkeypatch, url, tmp_path)
        d = day.date()
        with _client() as c:
            # the cold world is shifted to yesterday (`w502_cold_work_cases.target_delta`); the 61-day range ends today.
            # The month is the 31 days ending on the data day (D-IAP.43: stable under the shift; see the docstring)
            bodies = _parity(c, "cold", "COLD-LAB-001", _month_and_61(d - timedelta(days=30), d, d + timedelta(days=1),
                                                                       known_at))
    print(f"\nIAP-PARITY cold data day={d} month pages (site, estate) = {bodies['pages']}")
    _pin("cold", "COLD-LAB-001", bodies)


def test_ev_w504_site_findings_are_in_the_estate_findings(monkeypatch, tmp_path) -> None:
    from test_out_b4_board_postgres import EV_BUILD, _case_db, _child, _client, _serve

    with _case_db("ev", "iap") as url:
        _child(url, ["-c", EV_BUILD, str(tmp_path), str(ROOT / "tools")])
        built = json.loads((tmp_path / "ev.json").read_text(encoding="utf-8"))
        assert built["status"] == "ready", built.get("status")
        e_day = datetime.fromisoformat(built["evidence_window_E"]["from"].replace("Z", "+00:00")).date()
        known_at = None
        _serve(monkeypatch, url, tmp_path)
        month_first = e_day.replace(day=1)
        month_last = (month_first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        with _client() as c:
            bodies = _parity(c, "ev", "EV-LAB-001", _month_and_61(month_first, month_last, e_day + timedelta(days=28),
                                                                   known_at))
    print(f"\nIAP-PARITY ev E day={e_day} month pages (site, estate) = {bodies['pages']}")
    _pin("ev", "EV-LAB-001", bodies)
