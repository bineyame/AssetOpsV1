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
    assert {r for r, *_ in FAILING.values()} | {"COH-7", "COH-9"} >= {name for name, _ in cc.RULES}


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


def test_a_non_200_body_is_kept_but_never_read(tmp_path: Path) -> None:
    root = tmp_path / "b"
    shutil.copytree(BUNDLES / "coh2_no_action", root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for r in manifest["requests"]:
        if r["name"] == "portfolio.week" and r["page"] == 2:
            r["status"] = 503
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    bundle = cc.Bundle(root)
    assert bundle.get("portfolio.week") is None and bundle.bodies["portfolio.week"].status == 503
    assert cc.check(bundle)["findings"] == []


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
