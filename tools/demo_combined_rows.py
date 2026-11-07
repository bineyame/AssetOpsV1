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
    (R10: UNKNOWN, `kpi.days.complete == 0`, the line ends with `MG1_NO_DAY`); otherwise on pace or behind."""
    from assetops_backend.chain.vocabulary import MG1_NO_DAY
    if "too early to judge" in text:
        assert state == "UNKNOWN" and text.endswith("(needs 3 checked days)"), (state, text)
        return "TOO_EARLY"
    if complete == 0:
        assert state == "UNKNOWN" and text.endswith(MG1_NO_DAY), (state, text)
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


def productive_price_v1(path) -> Decimal:
    """MILL-3b: the v1 value of the productive-use price fixture (`demo-productive-price-publications.json`)."""
    import json
    from pathlib import Path

    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return Decimal(next(s for s in doc["steps"] if s["step"] == "v1")["value"])


def mill_value_page(page: dict, price: Decimal) -> dict:
    """MILL-3b (FUEL-1 §2.4): the verification page's `value` is PRICED at the declared v1 price, and its per-day figure
    and text are recomputed here from the page's own shown means (`(after - before) x price`, `money2`)."""
    from assetops_backend.actions.verification_families import VALUE_COST_TEXT, VALUE_TEXT, _price_text
    from assetops_backend.chain.vocabulary import money2

    m = (page.get("metrics") or [None])[0]
    assert m, "no metric on the verification page"
    value = page.get("value")
    assert isinstance(value, dict), ("no mill value on the verification page", value)
    assert value.get("state") == "PRICED", ("mill value", value.get("state"), value.get("reason"))
    expected = money2((Decimal(m["after"]) - Decimal(m["before"])) * price)
    assert value.get("per_day") == expected, (value.get("per_day"), expected)
    p_txt = _price_text(price)
    text = VALUE_TEXT.format(d=expected, cur=value.get("currency"), a=m["after"], b=m["before"], p=p_txt,
                             n=m["days_after"])
    assert value.get("text") == text, (value.get("text"), text)
    assert value.get("cost_text") == VALUE_COST_TEXT, value.get("cost_text")
    return {"per_day": value["per_day"], "currency": value.get("currency"), "price": p_txt,
            "revision_id": (value.get("price") or {}).get("revision_id"), "text": value["text"],
            "cost_text": value["cost_text"]}


def mill_assure(board: dict, chain: dict, mill_id: str, code: str, page: dict, site: str = "KOBO-001") -> dict:
    """MILL-5 (FUEL-1 MB-1-R §2.5): on the S+0 Kobo board the Assure row lists the mill with the DOMAIN_VERDICT link
    and the verified text (backend constants), and its headline count equals the verified entries; on the week
    `/api/estate/chain` the verified claim is Σ threads.verified + Σ threads.verified_actions, Kobo's mill counted once.
    WD-1m-R2: the mill entry's suffix is `provenance_suffix(page.outcome.source_class)` from the verdict-page body
    `page`; on the S+0 Kobo story that class must be an example class (a None means the write path did not run)."""
    import re

    from assetops_backend.chain.vocabulary import EXAMPLE_SOURCES, provenance_suffix
    from assetops_backend.outcomes.display_code import display_code
    from assetops_backend.site_outcomes.mini import NO_VERIFIED, VERIFICATION_TEXT

    assure = next((r for r in board.get("rows") or () if r.get("category") == "ASSURE_PERFORMANCE"), None)
    assert assure is not None, "no Assure row on the S+0 Kobo board"
    entries = [c for c in assure.get("contributors") or () if c.get("key") == "verified_results"]
    source_class = ((page or {}).get("outcome") or {}).get("source_class")
    if site == "KOBO-001":
        assert source_class in EXAMPLE_SOURCES, ("the S+0 Kobo mill verdict carries no example source class", source_class)
    text = VERIFICATION_TEXT["VERIFIED"].format(code=display_code(code), suffix=provenance_suffix(source_class))
    mill = [c for c in entries if (c.get("link_ref") or {}).get("kind") == "DOMAIN_VERDICT"
            and str((c.get("link_ref") or {}).get("id")) == str(mill_id)]
    assert len(mill) == 1, ("the mill entry on the Assure row", [c.get("text") for c in entries])
    assert mill[0].get("text") == text, (mill[0].get("text"), text)
    headline = assure.get("headline")
    m = re.fullmatch(r"(\d+) verified results?", str(headline or ""))
    assert headline == NO_VERIFIED or m, ("unreadable Assure headline", headline)
    shown = 0 if headline == NO_VERIFIED else int(m.group(1))
    listed = sum(1 for c in entries if re.fullmatch(r"\S+ verified\b.*", str(c.get("text") or ""))
                 and " not yet verified" not in str(c.get("text") or "") and c.get("text") != NO_VERIFIED)
    assert shown == listed, (headline, listed)
    sites = {s.get("code"): s.get("threads") or {} for s in chain.get("sites") or ()}
    claim = ((chain.get("counts") or {}).get("count.verified_results") or {}).get("value")
    total = sum(int(t.get("verified") or 0) + int(t.get("verified_actions") or 0) for t in sites.values())
    assert claim == total, ("week count.verified_results", claim, total)
    assert (sites.get(site) or {}).get("verified_actions") == 1, ("Kobo verified_actions", sites.get(site))
    return {"headline": headline, "mill_text": text, "verified_entries": listed, "week_claim": claim,
            "week_threads": sites}


def pv_values(summary: dict, page: dict, code: str, trial_code: str, trial_cost_check: dict | None,
              site: str = "KOBO-001") -> dict:
    """PV-A (FUEL-1 PV-1-R §5): on the week estate summary holding the S+0 Kobo board, the Assure card's
    `value_lines` holds the mill line built from the verdict page's own `value` (backend constants, never typed); the
    trial-fuel line is present iff `credited(trial cost check, "VERIFIED")` is not None; and no card string holds the
    sum of two same-currency entry amounts (never added)."""
    from fractions import Fraction

    from assetops_backend.chain.vocabulary import card_text
    from assetops_backend.outcomes.credit import credited
    from assetops_backend.outcomes.display_code import display_code
    from assetops_backend.site_outcomes.mini import VALUE_LINE_MILL, VALUE_LINE_TRIAL_FUEL

    card = (summary.get("cards") or {}).get("ASSURE_PERFORMANCE")
    assert isinstance(card, dict) and "value_lines" in card, ("no Assure card value_lines", card)
    lines = list(card["value_lines"])
    s = next((x for x in summary.get("sites") or () if x.get("site_code") == site), None)
    assert s is not None, ("Kobo not on the week summary", site)
    name = s.get("site_name") or site
    value = page.get("value") or {}
    assert value.get("state") == "PRICED", ("mill value", value)
    mill = card_text("assure.value_line", site=name, text=VALUE_LINE_MILL.format(
        code=display_code(code), d=value["per_day"], cur=value["currency"]))
    assert mill in lines, (mill, lines)
    got = credited(trial_cost_check, "VERIFIED")
    trial = None
    if got is not None:
        (n, d), cur = got
        pt = (trial_cost_check or {}).get("priced_total") or {}
        amount = f"{Decimal(round(Fraction(n, d) * 100)) / 100:.2f}"
        litres = f"{Decimal(round(Fraction(str(pt['fuel_change_l'])) * 10)) / 10:.1f}"
        trial = card_text("assure.value_line", site=name, text=VALUE_LINE_TRIAL_FUEL.format(
            code=display_code(trial_code), l=litres, amount=amount, cur=cur))
        assert trial in lines, (trial, lines)
    else:
        assert not any(display_code(trial_code) + ":" in x and "less diesel" in x for x in lines), lines
    entries = [e for x in summary.get("sites") or () for r in x.get("rows") or ()
               if r.get("category") == "ASSURE_PERFORMANCE" for e in (r.get("nodes") or {}).get("verified_values") or ()]
    strings: list[str] = []

    def walk(node) -> None:
        if isinstance(node, str):
            strings.append(node)
        elif isinstance(node, dict):
            for x in node.values():
                walk(x)
        elif isinstance(node, (list, tuple)):
            for x in node:
                walk(x)

    walk(card)
    sums = [f"{Decimal(str(a['amount'])) + Decimal(str(b['amount'])):.2f}" for i, a in enumerate(entries)
            for b in entries[i + 1:] if a.get("currency") == b.get("currency")]
    held = sorted({x for x in sums if any(x in t for t in strings)})
    assert not held, ("the Assure card holds a sum", held)
    return {"value_lines": lines, "mill_line": mill, "trial_line": trial,
            "trial_case": "credited" if trial else "not credited", "value_note": card.get("value_note"),
            "sums_checked": len(sums)}


def kis4(windows: dict, findings: list[dict], consequences: list[dict], prices: dict,
         dispatch_consequences: list[dict], served: list[str] = ()) -> dict:
    """KIS-4 (DIESEL-1-R3j §9j.9): the unexplained-fuel money of Kisiwa's stored fuel Findings.

    `windows`: window id -> its stored row (`residual_low`/`residual_high` exact text); `findings`: each fuel Finding's
    latest revision (`finding_id`, `revision_id`, `lifecycle`, `window_id`); `consequences`: the stored
    `fuel_residual_consequence_revision` rows; `prices`: window id -> a re-run of `select_window_price` at
    `known_at = window_end` (`state`, `revision_id`, `value`); `dispatch_consequences`: the Site's
    `financial_consequence_revision` rows (`finding_id`, `amount_low`, `amount_high`); `served`: served strings.

    - every SUPPORTED fuel Finding revision has one consequence whose litres equal its cited window's band exactly;
    - PRICED amounts equal litres x the stored price value exactly, and the stored price revision equals the re-run;
    - no `financial_consequence_revision` row has a fuel Finding's id;
    - no stored or served amount equals (two places) the sum of a fuel amount with any dispatch `amount_high`, or of
      two fuel amounts (never added)."""
    from fractions import Fraction

    from assetops_backend.actions.verification_rules import parse_exact

    by_revision = {str(c["finding_revision_id"]): c for c in consequences}
    supported = [f for f in findings if f["lifecycle"] == "SUPPORTED"]
    assert supported, ("no SUPPORTED Kisiwa fuel Finding", findings)
    fuel_amounts: list[Fraction] = []
    for f in supported:
        c = by_revision.get(str(f["revision_id"]))
        assert c is not None, ("a SUPPORTED fuel Finding revision has no consequence", f)
        w = windows[str(f["window_id"])]
        assert str(c["fuel_balance_window_id"]) == str(f["window_id"]), ("consequence cites another window", c, f)
        lo, hi = parse_exact(w["residual_low"]), parse_exact(w["residual_high"])
        assert (parse_exact(c["litres_low"]), parse_exact(c["litres_high"])) == (lo, hi), ("litres", c, w)
        if c["state"] == "PRICED":
            value = Fraction(str(c["price_value"]))
            assert parse_exact(c["amount_low"]) == lo * value and parse_exact(c["amount_high"]) == hi * value, (
                "amounts are not litres x price", c)
            again = prices[str(f["window_id"])]
            assert (again["state"], str(again["revision_id"]), Fraction(str(again["value"]))) == (
                "PRICED", str(c["price_revision_id"]), value), ("price re-run differs", again, c)
            fuel_amounts += [parse_exact(c["amount_low"]), parse_exact(c["amount_high"])]
        else:
            assert c["amount_low"] is None and c["amount_high"] is None, ("UNPRICED with an amount", c)
    fuel_ids = {str(f["finding_id"]) for f in findings}
    cited = sorted({str(d["finding_id"]) for d in dispatch_consequences} & fuel_ids)
    assert not cited, ("a financial_consequence_revision row cites a fuel Finding", cited)

    def two(x) -> str:
        return f"{Decimal(round(Fraction(x) * 100)) / 100:.2f}"

    # a zero operand is no addition (dispatch PRICED-0 days store amount_high 0), so it never makes a sum
    dispatch_high = [x for x in (parse_exact(d["amount_high"]) for d in dispatch_consequences
                                 if d.get("amount_high") is not None) if x]
    operands = [a for a in fuel_amounts if a]
    sums = {two(a + b) for a in operands for b in dispatch_high}
    sums |= {two(a + b) for i, a in enumerate(operands) for b in operands[i + 1:]}
    stored = {two(x) for x in fuel_amounts + dispatch_high}
    stored |= {two(parse_exact(d["amount_low"])) for d in dispatch_consequences if d.get("amount_low") is not None}
    held = sorted((sums & stored) | {s for s in sums for text in served if s in text})
    assert not held, ("a stored or served amount is a sum", held)
    return {"supported": len(supported), "priced": sum(c["state"] == "PRICED" for c in consequences),
            "sums_checked": len(sums), "served_strings": len(served)}


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
