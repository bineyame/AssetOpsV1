"""CH-0 U2 (build sheet §3.2): self-tests for the chain coherence check and the L3 clone helper.

Pure: hand-made fixture bundles under `fixtures/chain_coherence/bundles/`, no database, no app, no network.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import chain_coherence as cc  # noqa: E402

BUNDLES = HERE / "fixtures" / "chain_coherence" / "bundles"
COLD, KOBO = "COLD-LAB-001", "KOBO-001"
F1, A1 = "f1000000-0000-0000-0000-000000000001", "a1000000-0000-0000-0000-000000000001"
DC = "day:cold:failure:2026-10-31"

#: bundle -> the one finding it must yield: (rule, site_code, window, subject)
FAILING = {
    "coh7b_state": ("COH-7b", COLD, "week", "PROTECT_ASSET"),
    "coh4b_board_finding": ("COH-4", COLD, DC, F1),
    "coh6_opportunity_missing_row": ("COH-6", KOBO, "week", "findings:opportunities"),
    "coh1_api_link": ("COH-1", COLD, DC, f"/api/sites/{COLD}/cold/findings/x"),
    "coh2_no_action": ("COH-2", COLD, "week", A1),
    "coh3_board_missing_action": ("COH-3", COLD, DC, A1),
    "coh4_missing_finding": ("COH-4", COLD, "week", F1),
    "coh5_lens": ("COH-5", COLD, DC, f"{F1}:COST"),
    "coh6_opportunity_denied": ("COH-6", KOBO, "week", "portfolio:opportunity"),
    "coh7_basis": ("COH-7a", None, "week", "window_basis"),
    "coh8_verified": ("COH-8", COLD, "week", A1),
    "coh9_counts": ("COH-9a", KOBO, "week", "00000000-0000-0000-0000-00000000c0b0"),
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
    assert portfolio["opportunity"]["state"] == "SUPPORTED"  # other keys come from page 1


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


def _board_self(tmp_path: Path, value: str | None, nested: str | None = None, params: dict | None = None):
    def links(body: dict) -> None:
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


def test_a_board_date_request_equals_its_one_day_range_self_link(tmp_path: Path) -> None:
    own = f"{COLD_BOARD}?from=2026-10-31T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z"
    assert _board_self(tmp_path, own, params={"date": "2026-10-31"}) == []


def test_the_date_equivalence_does_not_widen(tmp_path: Path) -> None:
    two_days = f"{COLD_BOARD}?from=2026-10-31T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z"
    assert len(_board_self(tmp_path / "a", two_days, params={"date": "2026-10-31"})) == 1
    other_day = f"{COLD_BOARD}?from=2026-10-30T00%3A00%3A00Z&to=2026-10-31T00%3A00%3A00Z"
    assert len(_board_self(tmp_path / "b", other_day, params={"date": "2026-10-31"})) == 1
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
    days = [{"site": "kobo", "kind": "normal", "day": "2026-10-30", "assess": "build",
             "start": "2026-10-30T03:00:00Z", "end": "2026-10-30T11:00:00Z"},
            {"site": "cold", "kind": "failure", "day": "2026-10-31", "assess": "build",
             "start": "2026-10-31T16:00:00Z", "end": "2026-10-31T17:05:00Z"},
            {"site": "kobo", "kind": "missing", "day": "2026-10-21", "assess": "none", "start": None, "end": None}]
    kobo, cold = cc.day_windows(days)
    assert (kobo["id"], kobo["date"], kobo["from"], kobo["to"]) == (
        "day:kobo:normal:2026-10-30", "2026-10-30", "2026-10-30T00:00:00Z", "2026-10-31T00:00:00Z")
    assert (cold["from"], cold["to"], cold["date"]) == ("2026-10-31T16:00:00Z", "2026-10-31T17:05:00Z", None)
    assert cold["estate"] == ("2026-10-31T00:00:00Z", "2026-11-01T00:00:00Z")  # estate routes need UTC midnights


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
