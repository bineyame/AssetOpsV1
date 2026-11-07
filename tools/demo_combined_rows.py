"""DD-1b2b O4-O6 (DD1b2-R6, R7): the pure parts of the new finish rows, so they are tested without a database.

Nothing here reads the served app; `demo_combined_finish.py` feeds these functions what it read. Nothing is tuned: the
expected figures (42.00, 110.00, the WK-2c sentence) are the rulings' own, quoted from the build sheet."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
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
                           unplaced: list | None = None, headroom: list[str] | None = None) -> list[dict]:
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
    if headroom:  # DD1b2-R10: the stored studies with eligible days (recurrence), not only the pinned one
        out.append({"name": "kobo-headroom", "site_code": "KOBO-001", "mechanism": HEADROOM,
                    "opportunities": [str(o) for o in headroom]})
    elif mill and (mill.get("study") or {}).get("opportunity_id"):
        out.append({"name": "kobo-headroom", "site_code": "KOBO-001", "mechanism": HEADROOM,
                    "opportunities": [str(mill["study"]["opportunity_id"])]})
    return out


def headroom_opportunities(stored: list[tuple]) -> list[str]:
    """DD1b2-R10 F-COH: from stored rows `(opportunity_id, last_day, eligible_days of the latest revision)`, the
    Kobo headroom occurrences: every study with at least one eligible day, ordered by `last_day`. A study with none is
    not an occurrence."""
    return [str(o) for o, _last, eligible in sorted(stored, key=lambda r: (str(r[1]), str(r[0])))
            if eligible is not None and int(eligible) >= 1]


def unknown_only_not_judged(outcomes: dict) -> list[str]:
    """DD1b2-R10 CO-5/SP-1, SP-2: `outcomes` maps key -> (state, reason). On a window with no complete reading an
    UNKNOWN outcome is acceptable only for reason OBJECTIVE_NOT_JUDGED, and NO_OBJECTIVE only for
    NO_OBJECTIVE_DECLARED. Any other reason (PRODUCER_NOT_SETTLED, OBJECTIVES_NOT_READ, ...) fails. Returns the keys
    that are UNKNOWN."""
    unknown = []
    for key, (state, reason) in outcomes.items():
        if state == "UNKNOWN":
            assert reason == "OBJECTIVE_NOT_JUDGED", ("UNKNOWN for a reason other than not-judged", key, reason)
            unknown.append(key)
        elif state == "NO_OBJECTIVE":
            assert reason == "NO_OBJECTIVE_DECLARED", ("NO_OBJECTIVE for another reason", key, reason)
    return unknown


def wk4(state: str, text: str, complete: int | None) -> str:
    """WK-4 branches: too early to judge (fewer checked days than the minimum); no fully checked day this month
    (R10: UNKNOWN, `kpi.days.complete == 0`, the line ends "sales not recorded"); otherwise on pace or behind."""
    if "too early to judge" in text:
        assert state == "UNKNOWN" and text.endswith("(needs 3 checked days)"), (state, text)
        return "TOO_EARLY"
    if complete == 0:
        assert state == "UNKNOWN" and text.endswith("sales not recorded"), (state, text)
        return "NO_FULL_DAY"
    assert state in ("ON_TRACK", "WATCH") and "so far this month" in text, (state, text, complete)
    return "JUDGED"


def expected_index_gaps(days: list[dict], lo: datetime, hi: datetime) -> list[str]:
    """DD1b2-R10 SP-4: the finding index works on UTC days. A UTC day in [lo, hi) is a gap when no built run window
    `[start, end)` touches it."""
    runs = [(_utc(d["start"]), _utc(d["end"])) for d in days
            if d.get("has_run", True) and d.get("kind") != "missing" and d.get("start") and d.get("end")]
    out = []
    day = datetime(lo.year, lo.month, lo.day, tzinfo=timezone.utc)
    while day < hi:
        nxt = day + timedelta(days=1)
        if not any(s < nxt and e > day for s, e in runs):
            out.append(day.date().isoformat())
        day = nxt
    return out


def _utc(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def site_day_start(day: date, zone) -> datetime:
    """CO-6 (CH-5a1): the Site-local midnight that opens `day`, in UTC."""
    return datetime(day.year, day.month, day.day, tzinfo=zone).astimezone(timezone.utc)


def wk1(grow: dict) -> dict:
    """WK-1 restated (R10): the earnings claim decides. With a counted day the headline carries money and the
    `charging_delivered` line is not "Not known yet"; with none, `headline_money` is absent and the line starts
    "Not known yet". Money on a day with too little data fails; so does a missing figure on a known one."""
    money = grow.get("headline_money") or {}
    line = next((c["text"] for c in grow.get("contributors", []) if c.get("key") == "charging_delivered"), None)
    assert line, ("no charging_delivered line", grow.get("contributors"))
    known = not line.startswith("Not known yet")
    if known:
        assert money.get("amount_high") and money.get("currency"), ("a known day shows no money", money, line)
        assert grow["headline"] == "estimated charging income", grow["headline"]
    else:
        assert not money, ("money shown on a day with too little data", money, line)
    return {"headline": grow["headline"], "money": money or None, "charging_delivered": line, "known": known}


def nodes_potential_text(grow: dict) -> str:
    """The Grow potential sentence: `nodes.potential.text` first, then the chip (`potential`)."""
    node = (grow.get("nodes") or {}).get("potential")
    if isinstance(node, dict) and node.get("text"):
        return str(node["text"])
    return potential_text(grow.get("potential"))


COH2_REASON = "Portfolio does not join domain-Site Actions (estate/index.py:193); known, DS-1 covers it; BL-47"
DOMAIN_SITES = ("COLD-LAB-001", "EV-LAB-001")


def recorded_action_ids(*docs: object) -> set[str]:
    """Every Action id a build record names: the `id` of any dict stored under an `action` key (ev.json fault_day,
    a Cold replay `positive.json` fixture). DD1b2-R9 item 1."""
    out: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            act = node.get("action")
            if isinstance(act, dict) and isinstance(act.get("id"), str):
                out.add(act["id"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for d in docs:
        walk(d)
    return out


def _coh2_known_gap(f: dict, action_ids: set[str]) -> bool:
    site = f.get("site_code")
    bodies = f.get("bodies") or []
    return (f["rule"] == "COH-2" and site in DOMAIN_SITES and f.get("subject") in action_ids
            and any(str(b).startswith(f"action_index.{site}") for b in bodies)
            and not any(str(b).startswith("actions.") for b in bodies))


COH17_REASON = "mill recurrence: an older row reads Verified, the thread now reads RECURRED (CH6b3-R4)"
_L3_DETAIL = re.compile(r"^(\d+) distinct Verified threads in the table, claim (\d+)$")


def _coh17_mill_recurrence(f: dict, recurs: bool) -> bool:
    """DD1b2-R13 section 1: the shape of the estate check L3 when one thread's older row reads Verified."""
    if not (recurs and f.get("rule") == "COH-17" and f.get("site_code") is None and f.get("subject") == "L3"
            and f.get("window") in ("week", "month")):
        return False
    m = _L3_DETAIL.match(str(f.get("detail")))
    return bool(m) and int(m.group(1)) - int(m.group(2)) == 1


def coh_split(findings: list[dict], recurs: bool, action_ids: set[str] | frozenset[str] = frozenset()
              ) -> tuple[list[dict], list[dict]]:
    """F-COH: (faults, allowed). Allowed: the estate check L3 for the one recurring mill thread (DD1b2-R13 section 1:
    COH-17, no Site, window week or month, subject L3, "n distinct Verified threads in the table, claim m" with
    n - m == 1, `recurs` true, at most one per window; reason COH17_REASON, owner BL-07), and COH-2 on Cold/EV for a
    recorded Action read from that Site's domain `action_index` (DD1b2-R9 item 1; reason COH2_REASON). Everything else
    is a fault, including any COH-2 on Kobo and any other COH-17."""
    faults, allowed = [], []
    taken: set[str] = set()
    for f in findings:
        if _coh17_mill_recurrence(f, recurs) and f["window"] not in taken:
            taken.add(f["window"])
            allowed.append({**f, "reason": COH17_REASON, "owner": "BL-07"})
        elif _coh2_known_gap(f, set(action_ids)):
            allowed.append({**f, "reason": COH2_REASON})
        else:
            faults.append(f)
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
    assert NO_POTENTIAL in nodes_potential_text(grow), (grow.get("nodes", {}).get("potential"), grow.get("potential"))
    return {"headline": grow["headline"], "sales": sales["text"], "potential": nodes_potential_text(grow)}


def potential_text(potential) -> str:
    if isinstance(potential, dict):
        return " ".join(str(potential.get(k) or "") for k in ("text", "label", "headline", "line", "value_line"))
    return str(potential or "")


def wk2c(grow: dict, study: dict | None = None) -> dict:
    """WK-2c on S-11 (R3 under "Leave it"): the potential equals the limited-evidence sentence; FAILS if any kW figure
    or money shows for it (a `value_line`, a money object, a digit-and-kW text)."""
    import re

    chip, node = grow.get("potential"), (grow.get("nodes") or {}).get("potential")
    assert chip or node, "no potential on the S-11 Grow row"
    text = nodes_potential_text(grow).strip()
    assert LIMITED_TEXT in text, text
    for shown in (node, chip):  # R10: the bars apply to the node and the chip alike
        if not shown:
            continue
        t = potential_text(shown).strip()
        assert not re.search(r"\d\s*(–|-|to)?\s*\d*\s*kW", t), ("a kW figure shows", t)
        assert not re.search(r"(USD|\$)\s*\d|\d\s*(USD|\$)", t), ("money shows", t)
        if isinstance(shown, dict):
            assert not shown.get("value_line") and not shown.get("value") and not shown.get("days_line"), \
                ("a value line shows", shown)
            assert not any(k for k in shown if "money" in k and shown[k]), ("money shows", shown)
    out = {"potential": node or chip, "chip": chip}
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
