"""CH-0 U2 (build sheet §3.2): self-tests for the chain coherence check and the L3 clone helper.

Pure: hand-made fixture bundles under `fixtures/chain_coherence/bundles/`, no database, no app, no network.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / "backend"))

import chain_coherence as cc  # noqa: E402

BUNDLES = HERE / "fixtures" / "chain_coherence" / "bundles"
COLD, KOBO = "COLD-LAB-001", "KOBO-001"
F1, A1 = "f1000000-0000-0000-0000-000000000001", "a1000000-0000-0000-0000-000000000001"
DC = "day:cold:failure:2026-10-31"

#: bundle -> the one finding it must yield: (rule, site_code, window, subject)
FAILING = {
    "coh7b_state": ("COH-7b", COLD, "week", "PROTECT_ASSET"),
    "coh4b_board_finding": ("COH-4", COLD, DC, F1),
    "coh6_opportunity_missing": ("COH-6", KOBO, "week", "findings:opportunities"),
    "coh1_api_link": ("COH-1", COLD, DC, f"/api/sites/{COLD}/cold/findings/x"),
    "coh2_no_action": ("COH-2", COLD, "week", A1),
    "coh3_board_missing_action": ("COH-3", COLD, DC, A1),
    "coh4_missing_finding": ("COH-4", COLD, "week", F1),
    "coh5_lens": ("COH-5", COLD, DC, f"{F1}:COST"),
    "coh6_opportunity_denied": ("COH-6", KOBO, "week", "portfolio:opportunity"),
    "coh7_basis": ("COH-7a", COLD, "week", "window_basis"),
    "coh8_verified": ("COH-8", COLD, "week", A1),
    "coh9_counts": ("COH-9a", KOBO, "week", "00000000-0000-0000-0000-00000000c0b0"),
    "coh10_thread_occurrence": ("COH-10", KOBO, "week", "f3000000-0000-0000-0000-000000000003"),
    "coh11_action_unlinked": ("COH-11", COLD, "week", A1),
    "coh11_action_link_missing": ("COH-11", COLD, "week", A1),
    "coh13_lifecycle_disagree": ("COH-13", COLD, DC, F1),
    "coh14_verified_attention": ("COH-14", COLD, DC, "PROTECT_ASSET:X"),
    "coh15_earlier_segment": ("COH-15", COLD, "week", A1),
    "coh16_opportunity_disagree": ("COH-16", KOBO, "week", "07000000-0000-0000-0000-000000000004"),
    "coh17_claims_disagree": ("COH-17", None, "week", "count.open_threads"),
    "coh18_day_grades": ("COH-18", None, "week", "count.open_threads"),
}


def keys(report: dict) -> list[tuple]:
    return [cc._key(f) for f in report["findings"]]


def test_clean_bundle_passes_every_rule() -> None:
    report = cc.check(cc.Bundle(BUNDLES / "clean"))
    assert report["findings"] == [] and report["pass"] is True
    assert report["schema"] == cc.REPORT_SCHEMA and report["bundle"]["request_count"] > 0
    # COH-9(b) is info only: the clean bundle's day phrases are listed and never fail
    assert {i["phrase"] for i in report["info"]["COH-9b"]} == {"3 of 7 days", "2 of the last 5 days"}


def test_every_rule_has_a_failing_fixture() -> None:
    assert {r for r, *_ in FAILING.values()} | {"COH-0", "COH-7", "COH-9"} >= {name for name, _ in cc.RULES}


@pytest.mark.parametrize("bundle", sorted(FAILING))
def test_each_failing_bundle_yields_exactly_its_finding(bundle: str) -> None:
    report = cc.check(cc.Bundle(BUNDLES / bundle))
    assert keys(report) == [FAILING[bundle]]
    assert report["pass"] is False and report["findings"][0]["bodies"]


def test_expect_semantics() -> None:
    bundle = cc.Bundle(BUNDLES / "coh2_no_action")
    rule, site, window, subject = FAILING["coh2_no_action"]
    hit = {"rule": rule, "site_code": site, "window": window, "subject": subject, "register": "I-03"}
    gone = {"rule": "COH-5", "site_code": COLD, "window": DC, "subject": "gone", "register": "I-21"}
    expected = cc.check(bundle, [hit])
    assert expected["pass"] is True and expected["expected_unmatched"] == [] and expected["resolved"] == []
    assert cc.check(bundle, [])["pass"] is False  # a new finding fails
    assert cc.check(bundle, None)["pass"] is False  # no --expect: any finding fails
    resolved = cc.check(bundle, [hit, gone])
    assert resolved["pass"] is True and resolved["resolved"] == [gone]  # expected but absent: reported, not failing
    assert cc.check(cc.Bundle(BUNDLES / "clean"), [gone])["pass"] is True


def test_wildcard_subject_expectation_is_bounded_by_count() -> None:
    """MD0b-R: subject "*" covers `count` findings of its (rule, site, window), no more, and no other window."""
    bundle = cc.Bundle(BUNDLES / "coh2_no_action")
    rule, site, window, _ = FAILING["coh2_no_action"]
    detail = cc.check(bundle, [])["findings"][0]["detail"]
    wild = {"rule": rule, "site_code": site, "window": window, "subject": "*", "count": 1, "register": "MD0b-R:A1",
            "detail_contains": detail[:20]}
    assert cc.check(bundle, [wild])["pass"] is True  # matching detail: absorbed up to the count
    different = {**wild, "detail_contains": "a different kind of problem"}
    report = cc.check(bundle, [different])  # a finding of another kind stays unexpected
    assert report["pass"] is False and report["resolved"] == [different]
    assert cc.check(bundle, [{k: v for k, v in wild.items() if k != "detail_contains"}])["pass"] is False
    assert cc.check(bundle, [{**wild, "count": 0}])["pass"] is False  # beyond the count: unexpected
    other = {**wild, "window": "no-such-window"}
    report = cc.check(bundle, [other])
    assert report["pass"] is False and report["resolved"] == [other]  # another window does not cover it


def test_variants_gate_expected_entries() -> None:
    """MD0b-N1: a `variants` entry applies only to a run of a listed variant; one without applies to all."""
    bundle = cc.Bundle(BUNDLES / "coh2_no_action")
    rule, site, window, subject = FAILING["coh2_no_action"]
    entry = {"rule": rule, "site_code": site, "window": window, "subject": subject}
    gated = {**entry, "variants": ["close"]}
    states = cc.check(bundle, [gated], variant="states")
    assert states["pass"] is False and states["expected_unmatched"]  # a states-run finding is unexpected
    assert cc.check(bundle, [gated], variant="close")["pass"] is True  # a close run absorbs it
    assert cc.check(bundle, [gated])["pass"] is False  # no variant given: a gated entry does not apply
    for v in ("states", "close", None):
        assert cc.check(bundle, [entry], variant=v)["pass"] is True  # no `variants`: applies to all
    assert cc.main(["check", "--bundle", str(BUNDLES / "coh2_no_action"), "--variant", "close", "--expect", str(_write(entry, gated))]) == 0


def _write(entry: dict, gated: dict) -> Path:
    import tempfile
    path = Path(tempfile.mkdtemp()) / "e.json"
    path.write_text(json.dumps([gated]), encoding="utf-8")
    return path


def test_resolved_wildcard_is_printed_loudly_and_new_count_agrees(capsys) -> None:
    bundle = cc.Bundle(BUNDLES / "coh2_no_action")
    rule, site, window, _ = FAILING["coh2_no_action"]
    detail = cc.check(bundle, [])["findings"][0]["detail"]
    wild = {"rule": rule, "site_code": site, "window": window, "subject": "*", "count": 1,
            "detail_contains": detail[:20]}
    gone = {"rule": "COH-5", "site_code": COLD, "window": DC, "subject": "*", "count": 1, "detail_contains": "x"}
    report = cc.check(bundle, [wild, gone])
    cc.print_report(report, [wild, gone])
    out = capsys.readouterr().out
    assert "RESOLVED-WILDCARD" in out and "COH-5" in out.split("RESOLVED-WILDCARD")[1]
    over = cc.check(bundle, [{**wild, "count": 0}])  # beyond the count: the per-rule line says new, as `pass` does
    cc.print_report(over, [{**wild, "count": 0}])
    assert f"{rule}: 1 finding(s), 0 expected, 1 new" in capsys.readouterr().out


def test_check_cli_exit_codes(tmp_path: Path, capsys) -> None:
    bundle = BUNDLES / "coh2_no_action"
    assert cc.main(["check", "--bundle", str(bundle)]) == 1
    rule, site, window, subject = FAILING["coh2_no_action"]
    expect = tmp_path / "expect.json"
    expect.write_text(json.dumps({"expectations": [
        {"rule": rule, "site_code": site, "window": window, "subject": subject}]}), encoding="utf-8")
    report = tmp_path / "report.json"
    assert cc.main(["check", "--bundle", str(bundle), "--expect", str(expect), "--report", str(report)]) == 0
    assert json.loads(report.read_text(encoding="utf-8"))["schema"] == "chain-coherence-report/1"
    assert "self-check: 1 pass, 0 fail" in capsys.readouterr().out


ROUTES = ["/sites/:siteId", "/sites/:siteId/findings/:findingId", "/maintenance/requests/:caseId/*", "/findings"]


@pytest.mark.parametrize("href,ok", [
    ("/sites/KOBO-001", True),
    ("/sites/KOBO-001/findings/f1?from=a&to=b#top", True),  # query and fragment stripped
    ("/sites/KOBO-001/findings", False),  # `:findingId` needs one non-empty segment
    ("/sites//findings/f1", False),
    ("/sites/KOBO-001/findings/f1/extra", False),
    ("/maintenance/requests/c1/record/x", True),  # `/*` matches the rest
    ("/maintenance/requests/c1", False),
    ("/findings", True),
    ("/api/sites/KOBO-001", False),
    ("https://x", False),
    ("/sites/KOBO-001?next=https://x", False),
])
def test_link_matcher(href: str, ok: bool) -> None:
    assert (cc.link_problem(href, ROUTES) is None) is ok


def test_screen_routes_file_is_the_app_route_list() -> None:
    routes = cc.load_routes()
    assert routes == sorted(set(routes)) and "/portfolio" in routes and "*" not in routes and "/" not in routes


def test_pagination_pages_are_concatenated() -> None:
    bundle = cc.Bundle(BUNDLES / "clean")
    assert bundle.files("portfolio.week") == ["portfolio.week.p1.json", "portfolio.week.p2.json"]
    portfolio = bundle.get("portfolio.week")
    assert [r["finding_id"][:2] for r in portfolio["rows"]] == ["f3", "f1"]
    assert portfolio["opportunity"]["state"] == "FOUND"  # other keys come from page 1


def _edited(tmp_path: Path, src: str, manifest_edit=None, **files) -> cc.Bundle:
    root = tmp_path / "b"
    shutil.copytree(BUNDLES / src, root)
    if manifest_edit:
        path = root / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest_edit(manifest)
        path.write_text(json.dumps(manifest), encoding="utf-8")
    for name, edit in files.items():
        path = root / name
        body = json.loads(path.read_text(encoding="utf-8"))
        edit(body)
        path.write_text(json.dumps(body), encoding="utf-8")
    return cc.Bundle(root)


def test_a_non_200_body_fails_the_bundle_as_coh0(tmp_path: Path) -> None:
    def fail(m: dict) -> None:
        for r in m["requests"]:
            if r["name"] == "portfolio.week" and r["page"] == 2:
                r["status"] = 503

    bundle = _edited(tmp_path, "coh2_no_action", fail)
    assert bundle.get("portfolio.week") is None and bundle.bodies["portfolio.week"].status == 503
    report = cc.check(bundle)
    assert keys(report) == [("COH-0", None, "week", "portfolio.week")] and report["pass"] is False


def test_a_cut_off_paged_run_fails_the_bundle_as_coh0(tmp_path: Path) -> None:
    def cut(m: dict) -> None:
        for r in m["requests"]:
            if r["name"] == "portfolio.week" and r["page"] == 2:
                r["truncated"] = True

    report = cc.check(_edited(tmp_path, "clean", cut))
    assert keys(report) == [("COH-0", None, "week", "portfolio.week")] and report["pass"] is False


class _Pages(cc.Getter):
    def __init__(self, status: int = 200, forever: bool = False) -> None:
        self.status, self.forever, self.calls = status, forever, []

    def get(self, path: str, params: dict[str, str]) -> tuple[int, dict]:
        self.calls.append((path, dict(params)))
        return self.status, {"rows": [], "next_cursor": "more" if self.forever else None}


def test_collector_marks_a_run_cut_off_at_max_pages(tmp_path: Path) -> None:
    c = cc.Collector(_Pages(forever=True), tmp_path)
    c.fetch("x", "/api/estate/findings", {}, "week", paged=True)
    assert len(c.requests) == cc.MAX_PAGES and c.requests[-1]["truncated"] is True
    assert not any(r.get("truncated") for r in c.requests[:-1])
    ok = cc.Collector(_Pages(), tmp_path)
    ok.fetch("y", "/api/estate/findings", {}, "week", paged=True)
    assert not ok.requests[0].get("truncated")


def test_known_at_reaches_the_board_requests_too(tmp_path: Path) -> None:
    getter = _Pages()
    c = cc.Collector(getter, tmp_path, "2026-10-31T00:00:00Z")
    c.board("board.x", "KOBO-001", "w", "a", "b", None)
    c.fetch("e", "/api/estate/outcome-summary", {}, "week")
    assert all(p.get("known_at") == "2026-10-31T00:00:00Z" for _, p in getter.calls) and len(getter.calls) == 2


COLD_BOARD = f"/api/sites/{COLD}/outcome-board"


def _board_self(tmp_path: Path, value: str | None, nested: str | None = None, params: dict | None = None,
                window: dict | None = None):
    def links(body: dict) -> None:
        if window is not None:
            body["window"] = window
        if value is not None:
            body["links"] = {"self": value}
        if nested is not None:
            body.setdefault("rows", [{}])[0]["links"] = {"self": nested}

    def req(m: dict) -> None:
        for r in m["requests"]:
            if r["name"] == f"board.{DC}":
                r["params"] = params or {}

    bundle = _edited(tmp_path, "clean", req, **{"board.day_cold_failure_2026-10-31.json": links})
    return cc.coh1_links(bundle)


def test_a_root_self_link_equal_to_its_own_request_is_exempt(tmp_path: Path) -> None:
    query = {"from": "2026-10-31T16:00:00Z", "to": "2026-10-31T17:05:00Z"}
    own = f"{COLD_BOARD}?from=2026-10-31T16%3A00%3A00Z&to=2026-10-31T17%3A05%3A00Z"
    assert _board_self(tmp_path, own, params=query) == []


def test_a_root_self_link_that_is_not_its_own_request_is_a_contradiction(tmp_path: Path) -> None:
    other = f"{COLD_BOARD}?from=2026-10-30T16%3A00%3A00Z"
    found = _board_self(tmp_path, other, params={"from": "2026-10-31T16:00:00Z"})
    assert [f["subject"] for f in found] == [other]
    elsewhere = "/api/sites/KOBO-001/outcome-board"
    assert [f["subject"] for f in _board_self(tmp_path / "e", elsewhere)] == [elsewhere]


#: CH-5a1 R6: the Addis local day 2026-10-31 (UTC+3), as the board body names it.
ADDIS_31 = {"from": "2026-10-30T21:00:00Z", "to": "2026-10-31T21:00:00Z"}


def test_a_board_date_request_equals_its_one_day_range_self_link(tmp_path: Path) -> None:
    """CH-5a1 (intended, R6): `date=D` canonicalises to the body's own window (D's Site-local day)."""
    own = f"{COLD_BOARD}?from=2026-10-30T21%3A00%3A00Z&to=2026-10-31T21%3A00%3A00Z"
    assert _board_self(tmp_path, own, params={"date": "2026-10-31"}, window=ADDIS_31) == []


def test_a_board_date_request_is_not_its_utc_day_in_addis(tmp_path: Path) -> None:
    """CH-5a1 R6 (Addis): the UTC-midnight day is no longer the `date=D` read when the body's window is local."""
    utc = f"{COLD_BOARD}?from=2026-10-31T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z"
    assert len(_board_self(tmp_path / "a", utc, params={"date": "2026-10-31"}, window=ADDIS_31)) == 1
    assert len(_board_self(tmp_path / "b", utc, params={"date": "2026-10-31"})) == 1  # no window: no equivalence


def test_the_date_equivalence_does_not_widen(tmp_path: Path) -> None:
    two_days = f"{COLD_BOARD}?from=2026-10-30T21%3A00%3A00Z&to=2026-11-01T21%3A00%3A00Z"
    assert len(_board_self(tmp_path / "a", two_days, params={"date": "2026-10-31"}, window=ADDIS_31)) == 1
    other_day = f"{COLD_BOARD}?from=2026-10-29T21%3A00%3A00Z&to=2026-10-30T21%3A00%3A00Z"
    assert len(_board_self(tmp_path / "b", other_day, params={"date": "2026-10-31"}, window=ADDIS_31)) == 1
    # a different route: the same equivalence is not applied
    b = cc.Body("x", "/api/sites/X/other", "w", 200, {}, [], {"date": "2026-10-31"})
    assert not cc.is_own_self_link(
        b, "$.links.self", "/api/sites/X/other?from=2026-10-31T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z")


def test_a_nested_self_link_is_a_contradiction_even_when_equal(tmp_path: Path) -> None:
    found = _board_self(tmp_path, COLD_BOARD, nested=COLD_BOARD)
    assert [(f["subject"], "rows[0]" in f["detail"]) for f in found] == [(COLD_BOARD, True)]


def test_example_data_strings_are_listed_as_info_only(tmp_path: Path) -> None:
    root = tmp_path / "b"
    shutil.copytree(BUNDLES / "clean", root)
    page = root / "portfolio.week.p2.json"
    body = json.loads(page.read_text(encoding="utf-8"))
    body["rows"][0]["source_provenance"] = {"classification": "REGISTERED_SIMULATION"}
    body["rows"][0]["note"] = "Verified on example data"
    page.write_text(json.dumps(body), encoding="utf-8")
    report = cc.check(cc.Bundle(root))
    assert report["pass"] is True
    [item] = report["info"]["COH-12"]
    assert (item["site_code"], item["source_mode"], item["path"]) == (COLD, "REGISTERED_SIMULATION", "$.rows[1].note")  # merged pages


def test_day_windows_follow_the_board_reads() -> None:
    """CH-5a1 (intended, R6/Q8, closes MD0-R R10): Kobo and Cold days are their Addis local days; EV unchanged."""
    days = [{"site": "kobo", "kind": "normal", "day": "2026-10-30", "assess": "build",
             "start": "2026-10-30T03:00:00Z", "end": "2026-10-30T11:00:00Z"},
            {"site": "cold", "kind": "failure", "day": "2026-10-31", "assess": "build",
             "start": "2026-10-31T16:00:00Z", "end": "2026-10-31T17:05:00Z"},
            {"site": "ev", "kind": "normal", "day": "2026-10-27", "assess": "build",
             "start": "2026-10-27T08:00:00Z", "end": "2026-10-27T16:00:00Z"},
            {"site": "kobo", "kind": "missing", "day": "2026-10-21", "assess": "none", "start": None, "end": None}]
    kobo, cold, ev = cc.day_windows(days)
    assert (kobo["id"], kobo["date"], kobo["from"], kobo["to"]) == (
        "day:kobo:normal:2026-10-30", "2026-10-30", "2026-10-29T21:00:00Z", "2026-10-30T21:00:00Z")
    assert (cold["from"], cold["to"], cold["date"]) == ("2026-10-30T21:00:00Z", "2026-10-31T21:00:00Z", None)
    assert cold["estate"] == ("2026-10-30T00:00:00Z", "2026-11-01T00:00:00Z")  # estate routes need UTC midnights
    assert kobo["estate"] == ("2026-10-29T00:00:00Z", "2026-10-31T00:00:00Z")
    assert (ev["from"], ev["to"], ev["date"]) == ("2026-10-27T08:00:00Z", "2026-10-27T16:00:00Z", None)
    assert ev["estate"] == ("2026-10-27T00:00:00Z", "2026-10-28T00:00:00Z")


@pytest.mark.parametrize("site,start,day", [
    ("kobo", "2026-10-30T22:30:00Z", "2026-10-31"),   # 01:30 Addis: already the next local day
    ("cold", "2026-10-30T20:59:00Z", "2026-10-30"),   # 23:59 Addis: still the same local day
])
def test_day_windows_take_the_addis_local_day_across_utc_midnight(site: str, start: str, day: str) -> None:
    [w] = cc.day_windows([{"site": site, "kind": "k", "day": day, "assess": "build", "start": start,
                           "end": start}])
    lo = datetime.fromisoformat(f"{day}T00:00:00+03:00").astimezone(timezone.utc)
    assert (w["from"], w["to"]) == (cc.iso(lo), cc.iso(lo + timedelta(days=1)))
    assert w["date"] == (day if site == "kobo" else None)


def test_category_lens_map_is_the_outcome_map_reading() -> None:
    assert cc.CATEGORY_LENS == {"OPTIMIZE_COST": "COST", "PROTECT_ASSET": "RISK", "GROW_REVENUE": "OPPORTUNITY"}


# ---- tools/chain_clone.py (pure: the SQL builders and name refusals; no database) ------------------------------

import chain_clone  # noqa: E402


@pytest.mark.parametrize("name", ["", "CH0", "ch-0", "a" * 21, "x_test", "x; DROP DATABASE assetops", "../x"])
def test_clone_refuses_any_other_target(name: str) -> None:
    with pytest.raises(chain_clone.CloneRefused):
        chain_clone.create_sql(name)
    with pytest.raises(chain_clone.CloneRefused):
        chain_clone.drop_sql(name)


def test_clone_sql_has_the_fixed_source_and_the_pattern_target() -> None:
    assert chain_clone.create_sql("ch0") == \
        'CREATE DATABASE "assetops_chainclone_ch0_test" TEMPLATE "assetops_polish_full_test"'
    assert chain_clone.drop_sql("ch0") == 'DROP DATABASE IF EXISTS "assetops_chainclone_ch0_test" WITH (FORCE)'
    assert chain_clone.SOURCE_DB == "assetops_polish_full_test"
    assert chain_clone.clone_url("ch0").endswith("/assetops_chainclone_ch0_test")
    assert "pg_backend_pid()" in chain_clone.SESSIONS_SQL and "pg_terminate_backend" not in chain_clone.SESSIONS_SQL


def test_clone_tool_never_names_the_demo3_db_or_terminates_sessions() -> None:
    text = (HERE.parent / "chain_clone.py").read_text(encoding="utf-8")
    assert "demo3" not in text and "pg_terminate_backend" not in text
    assert "--source" not in text  # no option changes the source


def test_clone_url_is_printed_with_the_password_masked() -> None:
    import chain_clone

    url = chain_clone.clone_url("abc")
    assert chain_clone.PW in url
    shown = chain_clone.masked(url)
    assert chain_clone.PW not in shown and shown.startswith("postgresql+psycopg://assetops:***@")


def test_coh10_unobserved_and_split_threads_and_pre_ch2_bundles(tmp_path: Path) -> None:
    """CH-2: an expected thread no Portfolio row shows fails; one thread's Findings on two ids fail; a bundle with
    no `thread` key (collected before CH-2) is not judged by COH-10/COH-11."""
    bundle = cc.Bundle(BUNDLES / "coh10_thread_occurrence")
    gone = [{"name": "absent", "site_code": KOBO, "findings": ["ffffffff-0000-0000-0000-000000000000"]}]
    assert [f["subject"] for f in cc.coh10_thread_identity(bundle, gone)] == ["absent"]
    split = [{"name": "both", "site_code": KOBO, "findings": [F1, "f3000000-0000-0000-0000-000000000003"]}]
    details = [f["detail"] for f in cc.coh10_thread_identity(bundle, split)]
    assert any("split across 2 thread ids" in d for d in details)
    assert cc.coh10_thread_identity(cc.Bundle(BUNDLES / "clean"), gone) == []  # unstamped: pre-CH-2
    assert cc.coh11_actions_linked(cc.Bundle(BUNDLES / "clean")) == []


def test_expected_threads_file_names_the_l4_threads() -> None:
    names = {t["name"]: t for t in cc.load_threads()}
    assert len(names["kobo-generator"]["findings"]) == 3 and len(names["cold-start-failure"]["findings"]) == 2
    assert names["kobo-headroom"]["opportunities"] == ["OPP-000003", "OPP-000004"]  # CH-4 R1


def test_stamped_bundle_without_the_thread_keys_fails_coh10_and_coh11() -> None:
    """Review L3: the manifest stamp, not the key, decides; a dropped key fails (COH-0 style) instead of skipping."""
    bundle = cc.Bundle(BUNDLES / "coh_thread_key_missing")
    assert [f["subject"] for f in cc.coh10_thread_identity(bundle)] == ["thread"]
    assert {f["subject"] for f in cc.coh11_actions_linked(bundle)} == {"thread", "action_thread_id"}


def test_coh11_names_an_action_with_no_link_of_its_own() -> None:
    """Review L2: the origin row is threaded and shows the Action, but the Action's own link is absent."""
    found = cc.coh11_actions_linked(cc.Bundle(BUNDLES / "coh11_action_link_missing"))
    assert [f["subject"] for f in found] == [A1] and "no thread link" in found[0]["detail"]


def test_lifecycle_bundle_passes_and_compares_pairs() -> None:
    """CH-3: a lifecycle-stamped bundle with agreeing reads passes; COH-13's compared set is non-empty."""
    bundle = cc.Bundle(BUNDLES / "clean_lifecycle")
    assert cc.check(bundle)["findings"] == [] and cc.lifecycle_pairs(bundle) == 2
    assert cc.coh13_lifecycle_agreement(cc.Bundle(BUNDLES / "clean")) == []  # unstamped: pre-CH-3


@pytest.mark.parametrize("hi, lo, ok", [
    (("OPEN", "2026-10-28"), ("OPEN", "2026-10-28"), True),            # same state both days
    (("ACTION_IN_HAND", "2026-11-02"), ("OPEN", "2026-10-28"), True),  # hi changed after lo's day
    (("ACTION_IN_HAND", "2026-11-02"), ("ACTION_IN_HAND", "2026-11-02"), False),  # lo cannot see a later change
    ((None, None), ("OPEN", "2026-10-28"), False),                    # no state at hi, but one at lo
])
def test_coh13_orders_reads_by_their_day(tmp_path: Path, hi: tuple, lo: tuple, ok: bool) -> None:
    root = tmp_path / "b"
    shutil.copytree(BUNDLES / "clean_lifecycle", root)
    board, port = root / "board.day_cold_failure_2026-10-31.json", root / "portfolio.week.p2.json"
    b, p = json.loads(board.read_text(encoding="utf-8")), json.loads(port.read_text(encoding="utf-8"))
    for row in b["rows"]:
        for i in row["issues"]:
            i["ref"]["thread"].update(state=lo[0], state_effective_day=lo[1])        # board: 31 Oct (lo)
    p["rows"][0]["thread"].update(state=hi[0], state_effective_day=hi[1], state_day="2026-11-03")
    board.write_text(json.dumps(b), encoding="utf-8")
    port.write_text(json.dumps(p), encoding="utf-8")
    assert (cc.coh13_lifecycle_agreement(cc.Bundle(root)) == []) is ok


def test_stamped_bundle_without_the_lifecycle_keys_fails(tmp_path: Path) -> None:
    """CH-3: the `lifecycle` stamp decides; a dropped `state_day` or `action_segment_no` fails (COH-0 style)."""
    root = tmp_path / "b"
    shutil.copytree(BUNDLES / "clean_lifecycle", root)
    port = root / "portfolio.week.p2.json"
    p = json.loads(port.read_text(encoding="utf-8"))
    del p["rows"][0]["thread"]["state_day"], p["rows"][0]["action_segment_no"]
    port.write_text(json.dumps(p), encoding="utf-8")
    bundle = cc.Bundle(root)
    assert [f["subject"] for f in cc.coh13_lifecycle_agreement(bundle)] == ["state_day"]
    assert [f["subject"] for f in cc.coh15_action_segment(bundle)] == ["action_segment_no"]


@pytest.mark.parametrize("name", ["", "CH0", "ch-0", "a" * 21, "x_test", "x; DROP DATABASE assetops", "../x"])
def test_settle_refuses_non_clone_names_before_any_process(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """CH3-R: `settle` ticks only an `assetops_chainclone_*_test` clone; a bad name is refused before a process
    starts."""
    import subprocess

    import chain_clone

    def no_process(*_a, **_k):
        raise AssertionError("settle started a process for a refused name")

    monkeypatch.setattr(subprocess, "Popen", no_process)
    with pytest.raises(chain_clone.CloneRefused):
        chain_clone.settle(name)
    with pytest.raises(chain_clone.CloneRefused):
        chain_clone.main(["settle", name])


def test_settle_env_points_only_at_the_clone() -> None:
    import chain_clone

    env = chain_clone.settle_env("ch3")
    assert env["DATABASE_URL"].endswith("/assetops_chainclone_ch3_test")
    assert env["ASSETOPS_TEST_DATABASE_URL"] == env["DATABASE_URL"]
    assert chain_clone.TICK[:3] == ("-m", "assetops_backend.scheduling.run", "tick")
    assert not any(k in env for k in chain_clone.KEY_NAMES)


def test_settle_runs_the_comparison_first_and_records_only_the_files_it_created(tmp_path: Path) -> None:
    """CH3-R M2: settle runs the S2 comparison, then the tick and performance step; it records exactly the files the
    steps created under var/, and drop's cleanup deletes exactly those, never a file that existed before."""
    var = tmp_path / "var"
    old = var / "evidence" / "migration" / "kobo-001" / "old.json"
    old.parent.mkdir(parents=True)
    old.write_text("{}", encoding="utf-8")
    labels = []

    def run(label, argv, env, name):
        labels.append(label)
        assert env["DATABASE_URL"].endswith("/assetops_chainclone_t1_test")
        if label == "s2-comparison":
            assert argv[:2] == ("-m", "assetops_backend.evidence_migration") and "KOBO-001" in argv
            (old.parent / "new.json").write_text("{}", encoding="utf-8")
            (var / "perf" / "deep").mkdir(parents=True)
            (var / "perf" / "deep" / "x.json").write_text("{}", encoding="utf-8")
        return 0

    assert chain_clone.settle("t1", var, run) == 0
    assert labels == ["s2-comparison", "tick", "performance"]
    record = json.loads(chain_clone.created_record("t1", var).read_text(encoding="utf-8"))
    assert record["files"] == ["evidence/migration/kobo-001/new.json", "perf/deep/x.json"]
    assert record["dirs"] == ["perf", "perf/deep"]
    assert sorted(chain_clone.cleanup("t1", var)) == record["files"]
    assert old.is_file() and not (old.parent / "new.json").exists() and not (var / "perf").exists()
    assert not (var / "chainclone_t1").exists()
    assert chain_clone.cleanup("t1", var) == []


def test_cleanup_refuses_a_recorded_path_outside_var(tmp_path: Path) -> None:
    var = tmp_path / "var"
    outside = tmp_path / "keep.txt"
    outside.write_text("x", encoding="utf-8")
    rec = chain_clone.created_record("t2", var)
    rec.parent.mkdir(parents=True)
    rec.write_text(json.dumps({"files": ["../keep.txt"], "dirs": []}), encoding="utf-8")
    with pytest.raises(chain_clone.CloneRefused):
        chain_clone.cleanup("t2", var)
    assert outside.is_file()


@pytest.mark.parametrize("name", ["../x", "polish_full", "demo3_full"])
def test_settle_refuses_a_non_clone_name_before_any_step(name: str, tmp_path: Path) -> None:
    ran = []
    with pytest.raises(chain_clone.CloneRefused):
        chain_clone.settle(name, tmp_path, lambda *a: ran.append(a) or 0)
    assert ran == [] and not any(tmp_path.iterdir())


def test_coh14_verified_line_prefix_is_the_boards_thread_lines() -> None:
    from assetops_backend.site_outcomes import board
    assert board.THREAD_MONITORING.startswith(cc.VERIFIED_LINE_PREFIX)
    assert board.THREAD_CLOSED.startswith(cc.VERIFIED_LINE_PREFIX)
    assert not board.THREAD_RECURRED.startswith(cc.VERIFIED_LINE_PREFIX)
    assert not board.THREAD_BEFORE.startswith(cc.VERIFIED_LINE_PREFIX)


def _thread_level(verdict: str):
    """The clean bundle's cold PROTECT_ASSET row as a board day after the Finding left the day: no MOVES Finding, the
    verified thread-level line in the subline, and the given verdict on its primary outcome."""
    def edit(body: dict) -> None:
        row = next(r for r in body["rows"] if r["category"] == "PROTECT_ASSET")
        row["issues"] = [i for i in row["issues"] if not (i.get("kind") == "FINDING" and i.get("role") == "MOVES")]
        row["subline"] = "Fix verified, monitoring (ACT-001) · 7 more fully checked days to close"
        for o in row["outcomes"]:
            o["state"], o["reason"] = (verdict, "PRIMARY_FINDING_OPEN" if verdict == "NEEDS_ATTENTION" else None)
    return edit


def test_coh14_judges_a_row_by_its_thread_level_verified_line(tmp_path: Path) -> None:
    """Fix round 2 (CH3-R M3): a row with no MOVES Finding but a verified thread's line is in COH-14's compared set;
    NEEDS_ATTENTION for an open primary Finding there fails, ON_TRACK passes."""
    name = "board.day_cold_failure_2026-10-31.json"
    bad = _edited(tmp_path / "bad", "clean_lifecycle", **{name: _thread_level("NEEDS_ATTENTION")})
    assert len(list(cc.coh14_rows(bad))) == 1
    assert [k for k in keys(cc.check(bad)) if k[0] == "COH-14"] == [("COH-14", COLD, DC, "PROTECT_ASSET:" + k)
                                                                    for k in _protect_keys(bad)]
    good = _edited(tmp_path / "good", "clean_lifecycle", **{name: _thread_level("ON_TRACK")})
    assert len(list(cc.coh14_rows(good))) == 1
    assert [k for k in keys(cc.check(good)) if k[0] == "COH-14"] == []


def _protect_keys(bundle: cc.Bundle) -> list[str]:
    board = bundle.get(f"board.{DC}")
    row = next(r for r in board["rows"] if r["category"] == "PROTECT_ASSET")
    return [o["key"] for o in row["outcomes"]]


def test_clean_opportunity_bundle_passes_and_judges_the_headroom_thread(tmp_path: Path) -> None:
    """CH-4: the stamped opportunity bundle passes COH-6, COH-10 (opportunity leg) and COH-16; the leg is not vacuous
    (a board ref on another thread id splits the thread, a wrong occurrence count fails, no item at all fails)."""
    report = cc.check(cc.Bundle(BUNDLES / "clean_opportunity"))
    assert report["findings"] == [] and report["pass"] is True
    board = "board.day_kobo_trial-before_2026-10-31.json"

    def other_thread(body: dict) -> None:
        body["rows"][0]["issues"][0]["ref"]["thread"]["id"] = "07000000-0000-0000-0000-0000000000ff"

    split = _edited(tmp_path / "split", "clean_opportunity", **{board: other_thread})
    assert any("split across 2 thread ids" in f["detail"] for f in cc.coh10_thread_identity(split))

    def one_occurrence(body: dict) -> None:
        body["opportunities"][0]["occurrences"] = 1

    count = _edited(tmp_path / "count", "clean_opportunity", **{"findings_opp.week.p1.json": one_occurrence})
    assert any("shows 1 occurrences" in f["detail"] for f in cc.coh10_thread_identity(count))

    def none(body: dict) -> None:
        body["opportunity"] = {**body["opportunity"], "state": "NONE", "items": []}

    def empty(body: dict) -> None:
        body["opportunities"] = []

    gone = _edited(tmp_path / "gone", "clean_opportunity", **{"portfolio.week.p1.json": none,
                                                              "findings_opp.week.p1.json": empty, board: lambda b: [
                                                                  i.update(ref=None) for i in b["rows"][0]["issues"]]})
    assert [f["subject"] for f in cc.coh10_thread_identity(gone)] == ["kobo-headroom"]
    # An unstamped (pre-CH-4) bundle is not judged by COH-16 or the leg.
    assert cc.coh16_opportunity_agreement(cc.Bundle(BUNDLES / "clean")) == []


def _summary_variant(tmp_path: Path, site_code: str, domain: str, window: dict) -> cc.Bundle:
    """The clean bundle with one summary Site's `domain` and `window` replaced (CH5a1-R2 COH-7a)."""
    dst = tmp_path / "bundle"
    shutil.copytree(BUNDLES / "clean", dst)
    path = dst / "summary.week.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    for s in body["sites"]:
        if s["site_code"] == site_code:
            s["domain"], s["window"] = domain, window
            s["window_basis"] = "DAY" if domain == "mini_grid" else "PERIOD"  # CH6b1-R Q2: the domain's basis
    path.write_text(json.dumps(body), encoding="utf-8")
    return cc.Bundle(dst)


#: The clean week requests [25 Oct 00Z, 1 Nov 00Z): `window_day` rule 3 (CH5a2-R R7) = the UTC date of
#: 31 Oct 23:59:59Z = 31 Oct, read as Kobo's (Addis) local day [30 Oct 21Z, 31 Oct 21Z).
KOBO_CARD_DAY = {"from": "2026-10-30T21:00:00Z", "to": "2026-10-31T21:00:00Z"}
#: The CH-5a1 card day (the Site-local day of `to - 1 µs`, the next local day east of UTC) is no longer expected.
KOBO_OLD_CARD_DAY = {"from": "2026-10-31T21:00:00Z", "to": "2026-11-01T21:00:00Z"}
WEEK = {"from": "2026-10-25T00:00:00Z", "to": "2026-11-01T00:00:00Z"}


@pytest.mark.parametrize("site,domain,window,fails", [
    (KOBO, "mini_grid", KOBO_CARD_DAY, False),  # the mini card's one Site-local day (window_day) is expected
    (KOBO, "mini_grid", KOBO_OLD_CARD_DAY, True),  # R7: the day after the picked date is not
    (KOBO, "mini_grid", WEEK, True),            # a mini card on the requested window is not its card day
    (COLD, "cold_chain", WEEK, False),          # every other Site: the requested window
    (COLD, "cold_chain", KOBO_CARD_DAY, True),  # ... and only it
])
def test_coh7a_mini_summary_card_is_its_site_local_summary_day(tmp_path: Path, site, domain, window, fails) -> None:
    report = cc.check(_summary_variant(tmp_path, site, domain, window))
    hits = [k for k in keys(report) if k[0] == "COH-7a"]
    assert hits == ([("COH-7a", site, "week", "window")] if fails else []), report["findings"]


@pytest.mark.parametrize("site,domain,window,basis,fails", [
    (KOBO, "mini_grid", KOBO_CARD_DAY, "DAY", False),
    (KOBO, "mini_grid", KOBO_CARD_DAY, "PERIOD", True),
    (COLD, "cold_chain", WEEK, "PERIOD", False),
    (COLD, "cold_chain", WEEK, "LATEST_EVENT", True),   # CH6b1-R Q2: the deleted basis is a finding
    (COLD, "cold_chain", WEEK, "DAY", True),
])
def test_coh7a_basis_is_the_domains(tmp_path: Path, site, domain, window, basis, fails) -> None:
    """CH6b1-R Q2: mini DAY, every other Site PERIOD; two bases in one summary are not a finding."""
    _summary_variant(tmp_path, site, domain, window)
    path = tmp_path / "bundle" / "summary.week.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    for s in body["sites"]:
        if s["site_code"] == site:
            s["window_basis"] = basis
    path.write_text(json.dumps(body), encoding="utf-8")
    hits = [k for k in keys(cc.check(cc.Bundle(path.parent))) if k[0] == "COH-7a"]
    assert hits == ([("COH-7a", site, "week", "window_basis")] if fails else []), hits


# ---- MD-0: in-process collect without demo work documents (R8), `check --threads` (R9), the mechanism files ----


def test_in_process_collect_reads_only_story_and_days(tmp_path: Path, monkeypatch) -> None:
    """R8: `collect --database-url` builds the client with `app_client` and reads story.json and days.json itself;
    it never calls `demo_combined_finish.load`, so a work folder without kobo/cold/ev work documents collects."""
    import types

    story, days = {"S": "2026-10-31T00:00:00Z", "code": "mechanism-v1"}, [{"site": "kobo", "day": "2026-10-19"}]
    (tmp_path / "story.json").write_text(json.dumps(story), encoding="utf-8")
    (tmp_path / "days.json").write_text(json.dumps({"days": days}), encoding="utf-8")
    fake = types.ModuleType("demo_combined_finish")
    fake.app_client = lambda url, work: ("client", url, work)
    fake.load = lambda *a, **k: pytest.fail("collect must not load the demo work documents")
    monkeypatch.setitem(sys.modules, "demo_combined_finish", fake)
    seen = {}

    def collect(getter, s, d, out, source, known_at):
        seen.update(getter=getter, story=s, days=d, source=source)
        return {"requests": []}
    monkeypatch.setattr(cc, "collect", collect)
    assert cc.main(["collect", "--work", str(tmp_path), "--database-url", "postgresql://x/assetops_mechanism_test",
                    "--out", str(tmp_path / "b")]) == 0
    assert (seen["story"], seen["days"], seen["source"]) == (story, days, "in-process")
    assert seen["getter"].client == ("client", "postgresql://x/assetops_mechanism_test", tmp_path)


def test_check_threads_replaces_the_expected_threads(tmp_path: Path) -> None:
    """R9: `check --threads` judges COH-10 against the named file (the mechanism build's), not THREADS_FILE."""
    bundle = cc.Bundle(BUNDLES / "coh10_thread_occurrence")
    gone = [{"name": "absent", "site_code": KOBO, "findings": ["ffffffff-0000-0000-0000-000000000000"]}]
    assert [f["subject"] for f in cc.check(bundle, None, gone)["findings"] if f["rule"] == "COH-10"] == ["absent"]
    assert not [f for f in cc.check(bundle)["findings"] if f["rule"] == "COH-10" and f["subject"] == "absent"]
    path = tmp_path / "expected-threads.json"
    path.write_text(json.dumps({"schema": "chain-coherence-threads/1", "threads": gone}), encoding="utf-8")
    report = tmp_path / "r.json"
    cc.main(["check", "--bundle", str(BUNDLES / "coh10_thread_occurrence"), "--threads", str(path),
             "--report", str(report)])
    found = json.loads(report.read_text(encoding="utf-8"))["findings"]
    assert "absent" in [f["subject"] for f in found if f["rule"] == "COH-10"]


def test_expected_mechanism_loads_and_only_names_declared_gaps() -> None:
    path = HERE / "fixtures" / "chain_coherence" / "expected-mechanism.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == "chain-coherence-expected/1" and "GAP-K7" in data["rule"]
    for e in cc.load_expect(path):
        assert e["register"].startswith(("MD-0:", "MD0b-R:", "CH6b3-R4:")) and e.get("owner"), e


def test_settle_also_accepts_the_mechanism_dbs_only() -> None:
    """P7: `settle` ticks `assetops_mechanism(_close)_test` by the names `mechanism`/`mechanism_close`; create and
    drop keep the chain-clone names, so neither can reach a mechanism DB."""
    assert chain_clone.settle_db("mechanism") == "assetops_mechanism_test"
    assert chain_clone.settle_db("mechanism_close") == "assetops_mechanism_close_test"
    assert chain_clone.settle_db("ch0") == "assetops_chainclone_ch0_test"
    assert chain_clone.settle_env("mechanism")["DATABASE_URL"].endswith("/assetops_mechanism_test")
    assert "\"assetops_mechanism_test\"" not in chain_clone.create_sql("mechanism") + chain_clone.drop_sql("mechanism")
    for name in ("mechanism_x", "assetops_mechanism", "polish_full"):
        with pytest.raises(chain_clone.CloneRefused):
            chain_clone.settle_db(name)


def test_coh5_reads_only_primary_issues(tmp_path: Path) -> None:
    """CH-5a2 B5: a secondary (non-primary) appearance of a Finding on a board row is not a lens claim."""
    def secondary(body: dict) -> None:
        for row in body["rows"]:
            for issue in row.get("issues") or []:
                if issue.get("kind") == "FINDING":
                    issue["primary"] = False
    bundle = _edited(tmp_path, "coh5_lens", **{"board.day_cold_failure_2026-10-31.json": secondary})
    assert cc.coh5_lens(bundle) == []
    assert cc.coh5_lens(cc.Bundle(BUNDLES / "coh5_lens")) != []


def test_coh14_reads_structured_thread_lines(tmp_path: Path) -> None:
    """CH-5a2 B4: COH-14 reads `thread_lines` kinds where present, and the copy only on an older body."""
    assert cc._verified_line({"thread_lines": [{"kind": "MONITORING"}], "subline": None}) is True
    assert cc._verified_line({"thread_lines": [{"kind": "BEFORE_CHANGE"}], "subline": "Fix verified, x"}) is False
    assert cc._verified_line({"subline": "a · Fix verified and closed (ACT-1)"}) is True


def test_coh17_agreeing_claims_pass_and_each_break_is_named(tmp_path: Path) -> None:
    """CH-5a2b COH-17: `clean_claims` (chain, Portfolio and Findings claims equal in every window) passes; a value,
    a missing `summary.claims`, a moved chain window and a missing chain body each fail; an unequal Site set is
    not compared; an unstamped bundle is not judged."""
    assert cc.check(cc.Bundle(BUNDLES / "clean_claims"))["findings"] == []
    assert cc.coh17_count_claims(cc.Bundle(BUNDLES / "clean")) == []

    def value(b):
        b["summary"]["claims"]["count.opportunities"]["value"] = 9
    got = cc.coh17_count_claims(_edited(tmp_path / "v", "clean_claims", None, **{
        "day_findings_all.day_kobo_trial-before_2026-10-31.p1.json": value}))
    assert [(f["window"], f["subject"]) for f in got] == [("day:kobo:trial-before:2026-10-31", "count.opportunities")]
    assert "value: chain 1, day_findings_all 9" in got[0]["detail"]

    def drop(b):
        del b["summary"]["claims"]
    got = cc.coh17_count_claims(_edited(tmp_path / "d", "clean_claims", None, **{"portfolio.week.p1.json": drop}))
    assert [(f["window"], f["subject"]) for f in got] == [("week", "portfolio")]

    def moved(b):
        b["window"]["from"] = "2026-10-24T00:00:00Z"
    got = cc.coh17_count_claims(_edited(tmp_path / "w", "clean_claims", None, **{"chain_estate.week.json": moved}))
    assert [(f["window"], f["subject"]) for f in got] == [("week", "window")]

    def other_sites(b):
        b["scope_disclosure"] = {"sites": [{"site_code": "COLD-LAB-001"}]}
        b["summary"]["claims"]["count.open_threads"]["value"] = 7
    assert cc.coh17_count_claims(_edited(tmp_path / "s", "clean_claims", None,
                                         **{"portfolio.week.p1.json": other_sites})) == []

    def no_chain(m):
        m["requests"] = [r for r in m["requests"] if r["name"] != "chain_estate.week"]
    got = cc.coh17_count_claims(_edited(tmp_path / "c", "clean_claims", no_chain))
    assert [(f["window"], f["subject"]) for f in got] == [("week", "chain")]


# ---- CH6b3-R: COH-17 rows C2-L1, W1, W2, COH-18 R1-R4, the info list and the tallies (`clean_full`) -------------------

KOBO, COLD = "KOBO-001", "COLD-LAB-001"


def _site(body: dict, code: str) -> dict:
    key = "code" if "code" in body["sites"][0] else "site_code"
    return next(s for s in body["sites"] if s[key] == code)


def _chain_row(b: dict) -> dict:
    return _site(b, KOBO)["rows"]["GROW_REVENUE"]


def _second_currency(b: dict) -> None:
    _site(b, COLD)["earnings"]["estimated_income"]["value"]["currency"] = "EUR"


def _edit_card_claim(b: dict) -> None:
    b["cards"]["PROTECT_ASSET"]["claim"]["value"] = 9


def _edit_both_amounts(b: dict) -> None:
    _site(b, COLD)["earnings"]["estimated_income"]["value"]["amount"] = "11.005"


def test_clean_full_passes_and_compares_every_row() -> None:
    bundle = cc.Bundle(BUNDLES / "clean_full")
    report = cc.check(bundle)
    assert report["findings"] == []
    assert report["tallies"]["COH-17"]["compared"] > 0 and report["tallies"]["COH-18"]["compared"] > 0
    assert report["info"]["COH-17-period-nodes"] == []


@pytest.mark.parametrize("row,files", [
    ("C2", {"chain_estate.week.json": _edit_card_claim}),
    ("C3", {"summary.week.json": lambda b: b["cards"]["PROTECT_ASSET"].update(tone="red")}),
    ("M1", {"summary.week.json": lambda b: b.update(money_total={**b["money_total"], "text": "other"})}),
    # one Site's amount moves on both bodies, so M6 agrees and only the sum breaks
    ("M2", {"chain_estate.week.json": _edit_both_amounts, "summary.week.json": _edit_both_amounts}),
    ("M3", {"chain_estate.week.json": _second_currency, "summary.week.json": _second_currency}),
    ("M4", {"chain_estate.week.json": lambda b: (b["money_total"]["lines"].pop(0), b["cards"]["GROW_REVENUE"]["parts"].update(
        income=" · ".join(b["money_total"]["lines"])))}),
    ("M5", {"chain_estate.week.json": lambda b: b["cards"]["GROW_REVENUE"]["parts"].update(income="other")}),
    ("M6", {"summary.week.json": lambda b: _site(b, KOBO)["earnings"]["estimated_income"].update(text="other")}),
    ("V1", {"chain_estate.week.json": lambda b: _chain_row(b).update(state_label="other")}),
    ("V2", {f"board_summary.week.{KOBO}.json": lambda b: b["rows"][0].update(headline="other")}),
    ("V3", {"chain_estate.week.json": lambda b: _chain_row(b).update(nodes={"kpi": None})}),
    ("V4", {f"board_summary.S.{KOBO}.json": lambda b: b["rows"][0].update(nodes={"kpi": None})}),
    ("L1", {"portfolio.week.p1.json": lambda b: b["summary"].update(verified_resolution_count=9)}),
    ("L1", {"portfolio.week.p1.json": lambda b: b["progress"].update(verified_resolution_count=9)}),
    ("L1", {"portfolio.week.p1.json": lambda b: b["summary"].update(priority_site_count=1)}),
    # CH6b3-R3: L2, L3, W3, N1 and the C2 absent-key fix (a card or count key absent is a finding)
    ("L2", {"summary.week.json": lambda b: b.update(verified_result_count=9)}),
    ("L3", {"portfolio.S.p1.json": lambda b: b["rows"][0].update(workflow_label="No action agreed yet")}),
    ("W3", {"why_estate.week.PROTECT_ASSET.json": lambda b: b["text"].update(days_used="other")}),
    ("N1", {"portfolio.S.p1.json": lambda b: b["summary"].update(card_notes={"PROTECT_ASSET": "5 of 7 days checked at Kobo"})}),
    # both sides absent: the old `{} == {}` passed this
    ("C2", {"chain_estate.week.json": lambda b: (b["cards"]["ASSURE_PERFORMANCE"].pop("claim"),
                                                 b["counts"].pop("count.verified_results"))}),
])
def test_coh17_each_row_fails_on_its_planted_break(tmp_path: Path, row: str, files: dict) -> None:
    got = cc.coh17_count_claims(_edited(tmp_path, "clean_full", None, **files))
    assert row in {f["subject"] for f in got}, got


def test_coh17_mini_nodes_on_week_are_not_compared_and_unstamped_is_not_judged(tmp_path: Path) -> None:
    def other_nodes(b):
        b["rows"][0]["nodes"] = {"kpi": None}
    assert cc.coh17_count_claims(_edited(tmp_path / "w", "clean_full", None, **{f"board_summary.week.{KOBO}.json": other_nodes})) == []

    def unstamp(m):
        m["full_claims"] = False
    def wrong(b):
        b["money_total"]["text"] = "other"
    bundle = _edited(tmp_path / "u", "clean_full", unstamp, **{"chain_estate.week.json": wrong})
    assert cc.coh17_count_claims(bundle) == []
    assert cc.info_coh17_period_nodes(bundle) == []


def test_coh17_findings_compare_only_their_one_key(tmp_path: Path) -> None:
    """The trap in CH6b3-R Q1: `count.sites_disrupted` joins the Portfolio keys, not the Findings' one key."""
    def findings(b):
        b["summary"]["claims"].pop("count.sites_disrupted", None)
    assert cc.coh17_count_claims(_edited(tmp_path, "clean_full", None, **{"findings_all.week.p1.json": findings})) == []
    assert cc.FINDINGS_CLAIM_KEYS == ("count.opportunities",)


def test_period_node_difference_is_listed_not_judged_and_unequal_days_is_not_unexplained(tmp_path: Path) -> None:
    def other_frame(b):
        b["rows"][0]["nodes"]["kpi"].update(text="Band held on one event", days={"complete": 1, "expected": 1})
    bundle = _edited(tmp_path / "f", "clean_full", None, **{f"board_summary.week.{COLD}.json": other_frame})
    assert cc.coh17_count_claims(bundle) == []
    (item,) = cc.info_coh17_period_nodes(bundle)
    assert (item["site_code"], item["window"], item["part"], item["unexplained"]) == (COLD, "week", "kpi", False)

    def same_days(b):
        b["rows"][0]["nodes"]["kpi"].update(text="Different words")
    (item,) = cc.info_coh17_period_nodes(_edited(tmp_path / "s", "clean_full", None,
                                                 **{f"board_summary.week.{COLD}.json": same_days}))
    assert item["unexplained"] is True


def _why_kobo_says(b):
    _site(b, KOBO)["text"]["say"] = "other"


def test_coh17_why_rows(tmp_path: Path) -> None:
    got = cc.coh17_count_claims(_edited(tmp_path / "1", "clean_full", None,
                                        **{"why_estate.week.GROW_REVENUE.json": _why_kobo_says}))
    assert [f["subject"] for f in got] == ["W1"]

    def extra(b):
        b["text"]["comes_from"].insert(0, "GreenHarvest Cold Room: Compressor stopped")
    got = cc.coh17_count_claims(_edited(tmp_path / "2", "clean_full", None,
                                        **{"why_estate.week.PROTECT_ASSET.json": extra}))
    assert [f["subject"] for f in got] == ["W2"]

    def warning_only(b):   # the early-warning line alone names no Site: 0, against a claim of 1
        b["text"]["comes_from"] = ["2 early warnings, counted separately"]
    got = cc.coh17_count_claims(_edited(tmp_path / "3", "clean_full", None,
                                        **{"why_estate.S.PROTECT_ASSET.json": warning_only}))
    assert [(f["window"], f["subject"]) for f in got] == [("S", "W2")]
    assert "Why? names [], count.sites_disrupted is 1" in got[0]["detail"]


def _day_file(d: str) -> str:
    return f"chain_day.{KOBO}.{d}.json"


def test_coh18_sum_rule(tmp_path: Path) -> None:
    def wrong_day(b):  # the planted wrong-day mapping (CH-5a `:684`): a COMPLETE day graded from another day's NO_DATA
        b["days"][0]["grade"] = "NO_DATA"
    got = cc.coh18_day_grades(_edited(tmp_path / "1", "clean_full", None, **{_day_file("2026-10-29"): wrong_day}))
    assert {(f["site_code"], f["window"], f["subject"]) for f in got} == {(KOBO, "week", "days"),
                                                                          *[(None, "week", k) for k in cc.CLAIM_KEYS]}
    assert "complete: chain 5, day grades 4" in got[0]["detail"]

    def wrong_claim(b):
        b["counts"]["count.opportunities"]["days"]["complete"] = 1
    got = cc.coh18_day_grades(_edited(tmp_path / "2", "clean_full", None, **{"chain_estate.week.json": wrong_claim}))
    assert [(f["window"], f["subject"]) for f in got] == [("week", "count.opportunities")]

    def missing_date(b):
        b["days"] = [e for e in b["days"] if e["day"] != "2026-10-31"]
    got = cc.coh18_day_grades(_edited(tmp_path / "3", "clean_full", None, **{f"chain_span.S.{COLD}.json": missing_date}))
    assert ("S", "missing:2026-10-31") in [(f["window"], f["subject"]) for f in got]

    def null_days(b):
        _site(b, KOBO)["days"] = None
    got = cc.coh18_day_grades(_edited(tmp_path / "4", "clean_full", None, **{"chain_estate.S.json": null_days}))
    assert (KOBO, "S", "days") in [(f["site_code"], f["window"], f["subject"]) for f in got]

    def unstamp(m):
        m["day_bodies"] = False
    assert cc.coh18_day_grades(_edited(tmp_path / "5", "clean_full", unstamp, **{_day_file("2026-10-29"): wrong_day})) == []


def test_coh18_built_days_and_checked_days_basis_with_gap_days(tmp_path: Path) -> None:
    clean = cc.Bundle(BUNDLES / "clean_full")
    # Kobo's PARTIAL 26 Oct is built and not listed: R3 fails; listed it passes; with no list neither rule is judged.
    assert cc.coh18_day_grades(clean) == []
    got = cc.coh18_day_grades(clean, [])
    assert [(f["site_code"], f["window"], f["subject"]) for f in got] == [(KOBO, "week", "built:2026-10-26")]
    listed = [{"site_code": KOBO, "day": "2026-10-26", "gap": "GAP-X"}]
    assert cc.coh18_day_grades(clean, listed) == []

    def all_complete(b):
        b["days"][0]["grade"] = "COMPLETE"
    def checked_on_s(b):  # S is all COMPLETE, so no CHECKED_DAYS claim is allowed there
        b["counts"]["count.open_threads"]["basis"] = "CHECKED_DAYS"
        b["money_total"]["basis"] = "CHECKED_DAYS"
        _site(b, KOBO)["earnings"]["estimated_income"]["basis"] = "CHECKED_DAYS"
    got = cc.coh18_day_grades(_edited(tmp_path / "1", "clean_full", None, **{"chain_estate.S.json": checked_on_s}), listed)
    assert sorted((f["site_code"] or "", f["subject"]) for f in got) == [
        ("", "count.open_threads"), ("", "money_total"), (KOBO, "earnings.estimated_income")]

    def no_data_on_s(b):
        b["days"][0]["grade"] = "NO_DATA"
    def s_days(b):
        checked_on_s(b)
        _site(b, KOBO)["days"].update(complete=0, no_data=1)
        for c in b["counts"].values():
            c["days"].update(complete=1, no_data=1)
    assert cc.coh18_day_grades(_edited(tmp_path / "2", "clean_full", None, **{
        "chain_estate.S.json": s_days, _day_file("2026-10-31"): no_data_on_s,
        # 31 Oct is also in the week window: its tally moves with it
        "chain_estate.week.json": lambda b: [_site(b, KOBO)["days"].update(complete=4, no_data=2),
                                             *[c["days"].update(complete=11, no_data=2) for c in b["counts"].values()]],
    }), listed) == []


def test_gap_days_load_from_the_expectation_files(tmp_path: Path) -> None:
    fixtures = BUNDLES.parent
    assert cc.load_gap_days(fixtures / "expected-today.json") is None
    (gap,) = cc.load_gap_days(fixtures / "expected-mechanism.json")
    assert (gap["site_code"], gap["gap"]) == (KOBO, "GAP-K7")
    spec = json.loads((cc.TOOLS.parent / "backend" / "conversions" / "mechanism-v1.json").read_text(encoding="utf-8"))
    day_zero = datetime.fromisoformat(spec["story"]["day_zero"])
    assert gap["day"] == (day_zero + timedelta(days=7)).date().isoformat()


def test_a_stamped_bundle_comparing_nothing_fails_and_tallies_name_skips(tmp_path: Path) -> None:
    def nothing(m):
        m["requests"] = [r for r in m["requests"] if r["name"].startswith("chain_")
                         and not r["name"].startswith("chain_estate") or r["name"] == "chain_estate.week"]
        m["windows"] = {"S": m["windows"]["S"]}
    got = cc.coh18_day_grades(_edited(tmp_path / "e", "clean_full", nothing))
    assert ("vacuous") in {f["subject"] for f in got}
    got = cc.coh17_count_claims(_edited(tmp_path / "f", "clean_full", nothing))
    assert {f["subject"] for f in got} >= {"chain", "vacuous"}
    tally = cc.rule_tallies(cc.Bundle(BUNDLES / "clean_claims"))
    assert tally["COH-17"]["compared"] > 0 and tally["COH-18"] == {"compared": 0, "skipped": 0}
