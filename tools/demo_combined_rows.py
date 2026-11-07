"""DD-1b2b O4-O6 (DD1b2-R6, R7): the pure parts of the new finish rows, so they are tested without a database.

Nothing here reads the served app; `demo_combined_finish.py` feeds these functions what it read. Nothing is tuned: the
expected figures (42.00, 110.00, the WK-2c sentence) are the rulings' own, quoted from the build sheet."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

MILL_BEFORE, MILL_AFTER = Decimal("42.00"), Decimal("110.00")
LIMITED_TEXT = "Limited evidence: readings come from mixed sources, so the size is not worked out yet"
NO_POTENTIAL = "No potential found yet"
HEADROOM = "PRODUCTIVE_USE_HEADROOM"


def drain_summary(record: dict) -> dict:
    """F-DRAIN: a drain record (`<work>/drain-N.json`) must end with every count 0 on every Site. Recounted here from
    the record's own `end` counts, not from its verdict. Reports `over_n`."""
    fields = ("dirty", "snapshots_pending", "threads_pending", "mini_deferred", "opportunity_live")
    assert record.get("verdict", "done") != "fail", ("the drain failed (R8 C1)", record.get("name"), record.get("reason"))
    assert record.get("end"), ("drain record has no end counts", record.get("name"))
    left = {site: {f: int(c[f]) for f in fields if int(c[f])} for site, c in record["end"].items()}
    left = {s: v for s, v in left.items() if v}
    assert not left, ("not drained", record.get("name"), left)
    return {"name": record.get("name"), "ticks": record["ticks"], "N": record["N"], "over_n": record["over_n"],
            "seconds": record.get("seconds"), "sites": sorted(record["end"])}


def build_expected_threads(kobo: dict, cold: dict, portfolio_rows: list[dict], mill: dict | None,
                           unplaced: list | None = None) -> list[dict]:
    """F-COH: the expected threads, generated from the build's own documents. A Finding id comes from `kobo.json` /
    `cold.json` (`days[].findings`, which is where the build recorded them); EV records none (`ev.json` has no
    `findings`), so EV's come from the served Portfolio rows of its Site (declared limit, packet). Findings are grouped
    by (Site, mechanism) in episode order, the mechanism read from the Portfolio row, never guessed. The mill thread is
    an opportunity-only thread whose entries are the stored study (`mill.json` `study.opportunity_id`)."""
    by_id = {str(r["finding_id"]).lower(): r for r in portfolio_rows if r.get("finding_id")}
    declared: dict[str, list[str]] = {
        "KOBO-001": [str(f).lower() for d in kobo.get("days", []) for f in d.get("findings", [])],
        "COLD-LAB-001": [str(f).lower() for d in cold.get("days", []) for f in d.get("findings", [])],
        "EV-LAB-001": [fid for fid, r in by_id.items() if r.get("site_code") == "EV-LAB-001"],
    }
    if kobo.get("finding"):
        declared["KOBO-001"].append(str(kobo["finding"]).lower())
    out: list[dict] = []
    for site, ids in declared.items():
        groups: dict[str, list[str]] = {}
        for fid in dict.fromkeys(ids):
            row = by_id.get(fid)
            if row is None:  # recorded by the build but on no Portfolio row of the windows read: not asserted
                if unplaced is not None:  # R8 B3(b): returned so the packet lists each id
                    unplaced.append({"site_code": site, "finding_id": fid})
                continue
            groups.setdefault(row["mechanism"], []).append(fid)
        for mech, fids in sorted(groups.items()):
            fids.sort(key=lambda f: (by_id[f].get("episode_start") or "", f))
            out.append({"name": f"{site.split('-')[0].lower()}-{mech.lower().replace('_', '-')}", "site_code": site,
                        "mechanism": mech, "findings": fids})
    if mill and (mill.get("study") or {}).get("opportunity_id"):
        out.append({"name": "kobo-headroom", "site_code": "KOBO-001", "mechanism": HEADROOM,
                    "opportunities": [str(mill["study"]["opportunity_id"])]})
    return out


def coh_split(findings: list[dict], recurs: bool) -> tuple[list[dict], list[dict]]:
    """F-COH: (faults, allowed). The only allowed finding is COH-17 on Kobo's mill thread, and only when the thread
    recurs (R6 O4, Q7 entry: an older row reads Verified, the thread now reads RECURRED). Everything else is a fault."""
    faults, allowed = [], []
    for f in findings:
        (allowed if recurs and f["rule"] == "COH-17" and f.get("site_code") in (None, "KOBO-001") else faults).append(f)
    return faults, allowed


def local_days(first: date, today: date) -> list[date]:
    return [first + timedelta(days=n) for n in range((today - first).days + 1)]


def calendar_expectations(first: date, today: date, built: set[date]) -> dict[str, str | None]:
    """F-CAL (Q11, R8 B2): every local day from first evidence to today. A day with no built run is asserted NO_DATA
    only BEFORE the Site-local today (S-10, S-4, S-2, ...); today's open day may hold a PENDING row, so it is read and
    recorded but not asserted. A built day carries no asserted grade (None)."""
    return {d.isoformat(): (None if d in built or d >= today else "NO_DATA") for d in local_days(first, today)}


def mill_page(page: dict) -> dict:
    """MILL-3 on the verification page wire (`summary_wire`): VERIFIED, and the first metric reads 42.00 -> 110.00."""
    assert page.get("state") == "VERIFIED", ("mill verdict", page.get("state"), page.get("reasons"))
    m = (page.get("metrics") or [None])[0]
    assert m, "no metric on the verification page"
    before, after = Decimal(str(m["before"])).quantize(Decimal("0.01")), Decimal(str(m["after"])).quantize(Decimal("0.01"))
    assert (before, after) == (MILL_BEFORE, MILL_AFTER), (str(before), str(after))
    return {"before": str(before), "after": str(after), "line": page.get("line"), "days_before": m.get("days_before"),
            "days_after": m.get("days_after")}


def action_ref_kind(action: dict) -> str | None:
    ref = action.get("ref")
    return ref.get("kind") if isinstance(ref, dict) else None


def wk2b(grow: dict, kw_pattern) -> dict:
    """WK-2b restated (R6 O6; DD1b2-R Q10): on S no headline money, the headline is not the kW pattern, the sales
    contributor starts "0 kWh used by Grain mill", the potential reads "No potential found yet"."""
    assert not grow.get("headline_money"), grow.get("headline_money")
    assert not kw_pattern.fullmatch(grow["headline"]), grow["headline"]
    sales = next(c for c in grow["contributors"] if c["key"] == "productive_sales")
    assert sales["text"].startswith("0 kWh used by Grain mill"), sales["text"]
    assert NO_POTENTIAL in potential_text(grow.get("potential")), grow.get("potential")
    return {"headline": grow["headline"], "sales": sales["text"], "potential": grow.get("potential")}


def potential_text(potential) -> str:
    if isinstance(potential, dict):
        return " ".join(str(potential.get(k) or "") for k in ("text", "label", "headline", "line", "value_line"))
    return str(potential or "")


def wk2c(grow: dict, study: dict | None = None) -> dict:
    """WK-2c on S-11 (R3 under "Leave it"): the potential equals the limited-evidence sentence; FAILS if any kW figure
    or money shows for it (a `value_line`, a money object, a digit-and-kW text)."""
    import re

    potential = grow.get("potential")
    assert potential, "no potential on the S-11 Grow row"
    text = potential_text(potential).strip()
    assert LIMITED_TEXT in text, text
    assert not re.search(r"\d\s*(–|-|to)?\s*\d*\s*kW", text), ("a kW figure shows", text)
    if isinstance(potential, dict):
        assert not potential.get("value_line"), ("a value line shows", potential.get("value_line"))
        assert not any(k for k in potential if "money" in k and potential[k]), ("money shows", potential)
    assert not re.search(r"(USD|\$)\s*\d|\d\s*(USD|\$)", text), ("money shows", text)
    out = {"potential": potential}
    if study is not None:
        out["status"], out["eligible_days"] = study.get("status"), study.get("eligible_days")
        assert study.get("status") == "LIMITED" and study.get("eligible_days") == 5, study
    return out


def board_faults(board: dict) -> list[str]:
    """Every story board (DD1b2-R8 B1): no PRODUCER_NOT_SETTLED anywhere, and the board's `read_state` must be
    AVAILABLE (a PARTIAL `read_state` means a producer port failed; a row is never in state PARTIAL). The failed port
    names are listed if the wire carries them."""
    import json

    bad = []
    if "PRODUCER_NOT_SETTLED" in json.dumps(board):
        bad.append("PRODUCER_NOT_SETTLED")
    if board.get("read_state") != "AVAILABLE":
        failed = board.get("failed")
        bad.append(f"read_state {board.get('read_state')}" + (f" (failed: {failed})" if failed else ""))
    return bad


def require_ev_group(threads: list[dict]) -> None:
    """DD1b2-R8 B3(a): EV's expected threads come from the served Portfolio rows, so an empty EV group would make
    COH-10 vacuous for EV. The fault Tuesday must yield at least one thread."""
    assert any(t.get("site_code") == "EV-LAB-001" for t in threads), "no expected EV thread: the EV group is empty"
