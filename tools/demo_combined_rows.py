"""DD-1b2b O4-O6 (DD1b2-R6, R7): the pure parts of the new finish rows, so they are tested without a database.

Nothing here reads the served app; `demo_combined_finish.py` feeds these functions what it read. Nothing is tuned: the
expected figures (42.00, 110.00, the WK-2c sentence) are the rulings' own, quoted from the build sheet."""
from __future__ import annotations

import json
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


#: DIESEL-1-R3p §9p.7 item 5 (K9): the Kisiwa unexplained-fuel thread's name and mechanism, as the ruling writes them.
KISIWA_FUEL_THREAD = {"name": "kisiwa-fuel", "site_code": "KISIWA-001", "mechanism": "UNEXPLAINED_FUEL"}


def kisiwa_fuel_thread(kisiwa: dict) -> dict:
    """DIESEL-1-R3p §9p.7 item 5 (K9): COH-10's Kisiwa fuel thread. Its one Finding is the night-4 Finding id from
    `kisiwa.json`, read the way `demo_combined.story_links` reads it (`finding.id`, else the Action's `finding_id`).
    A `kisiwa.json` without that id is a failure, never an empty thread."""
    fid = (kisiwa.get("finding") or {}).get("id") or (kisiwa.get("action") or {}).get("finding_id")
    assert fid, ("kisiwa.json carries no unexplained-fuel Finding id", sorted(kisiwa))
    return {**KISIWA_FUEL_THREAD, "findings": [str(fid).lower()]}


def build_expected_threads(kobo: dict, cold: dict, portfolio_rows: list[dict], mill: dict | None,
                           unplaced: list | None = None, headroom: list[str] | None = None,
                           kisiwa: dict | None = None) -> list[dict]:
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
    if kisiwa is not None:  # DIESEL-1-R3p §9p.7 item 5: only when the dataset holds Kisiwa (`kisiwa.json` exists)
        out.append(kisiwa_fuel_thread(kisiwa))
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
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
    from chain_coherence import nonzero_pair_sums

    amts = [(e.get("currency"), Decimal(str(e["amount"]))) for e in entries if e.get("amount") is not None]
    sums = sorted(nonzero_pair_sums((a, b) for i, a in enumerate(amts) for b in amts[i + 1:]))
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
    all_high = [parse_exact(d["amount_high"]) for d in dispatch_consequences if d.get("amount_high") is not None]
    dispatch_high = [x for x in all_high if x]
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
    from chain_coherence import nonzero_pair_sums

    def dec(x) -> tuple[str, Decimal]:
        return ("amount", Decimal(Fraction(x).numerator) / Decimal(Fraction(x).denominator))

    operands = [dec(a) for a in fuel_amounts]
    others = [dec(b) for b in all_high]  # zero addends are excluded by the helper
    sums = nonzero_pair_sums([(a, b) for a in operands for b in others]
                             + [(a, b) for i, a in enumerate(operands) for b in operands[i + 1:]])
    stored = {two(x) for x in fuel_amounts + dispatch_high}
    stored |= {two(parse_exact(d["amount_low"])) for d in dispatch_consequences if d.get("amount_low") is not None}
    held = sorted((sums & stored) | {s for s in sums for text in served if s in text})
    assert not held, ("a stored or served amount is a sum", held)
    return {"supported": len(supported), "priced": sum(c["state"] == "PRICED" for c in consequences),
            "sums_checked": len(sums), "served_strings": len(served)}


_MONEY_KEY = ("amount", "price", "currency", "money")


def _money_keys(node, path: str = "") -> list[str]:
    if isinstance(node, dict):
        return [p for k, v in node.items() for p in ([f"{path}.{k}"] if any(m in str(k).lower() for m in _MONEY_KEY)
                                                     else []) + _money_keys(v, f"{path}.{k}")]
    if isinstance(node, (list, tuple)):
        return [p for i, v in enumerate(node) for p in _money_keys(v, f"{path}[{i}]")]
    return []


def kis8_protect(summary: dict, night: date, site: str = "KISIWA-001") -> dict:
    """KIS-8a (DIESEL-1-R3j §9j.12, the Protect half of KIS-8): on the week estate summary holding Kisiwa's S+0 board,
    the Protect card's `fuel_lines` holds `protect.fuel_line` built from Kisiwa's Protect node entry for `night`
    (night 4), and COH-17 row UF1 passes on that summary. The wording-guard half of KIS-8 stays K9's."""
    import sys
    from pathlib import Path

    from assetops_backend.chain.vocabulary import card_text

    sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
    from chain_coherence import coh17_fuel, new_tally

    card = (summary.get("cards") or {}).get("PROTECT_ASSET")
    assert isinstance(card, dict) and "fuel_lines" in card, ("no Protect card fuel_lines", card)
    s = next((x for x in summary.get("sites") or () if x.get("site_code") == site), None)
    assert s is not None, ("Kisiwa not on the week summary", site)
    protect = next((r for r in s.get("rows") or () if r.get("category") == "PROTECT_ASSET"), None) or {}
    entries = (protect.get("nodes") or {}).get("unexplained_fuel") or []
    entry = next((e for e in entries if e.get("night_date") == night.isoformat()), None)
    assert entry is not None, ("no Kisiwa unexplained-fuel node entry for the night", night.isoformat(), entries)
    line = card_text("protect.fuel_line", site=s.get("site_name") or site, text=entry["text"])
    assert line in card["fuel_lines"], (line, card["fuel_lines"])
    tally = new_tally()
    found = coh17_fuel("week", summary, [], tally)
    assert not found and tally["compared"] == 3, ("COH-17 UF1", found, tally)
    return {"night": night.isoformat(), "line": line, "fuel_lines": len(card["fuel_lines"]), "uf1": "pass"}


def kis8_wording(bodies: dict[str, object], site: str = "KISIWA-001") -> dict:
    """KIS-8, the wording half (DIESEL-1 H4, §8.7; K9): no served body says theft, stolen, stole, siphon or pilfer
    (`tools/checks/fuel_wording.py` words, keys and values). `bodies` maps a name to a parsed served body. The check
    is not vacuous: at least one body must name `site` (the Kisiwa pages are among those read)."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
    from fuel_wording import served_hits

    hits = {name: found for name, body in bodies.items() if (found := served_hits(body))}
    assert not hits, ("H4: forbidden words in served bodies", dict(list(hits.items())[:8]))
    naming = [n for n, b in bodies.items() if site in json.dumps(b, default=str)]
    assert naming, ("KIS-8 read no served body naming the Site", site, len(bodies))
    return {"bodies": len(bodies), "naming_site": len(naming), "hits": 0}


def kisiwa_cohort(windows: list[dict]) -> dict:
    """KISIWA-COHORT (D-E5.30, DATA-1): every Kisiwa `dispatch` window whose day has readings has its latest
    selection `SELECTED_UNIQUE`. `windows`: one dict per selected window (`window_start`, `cohort_status` of the
    latest selection, `has_readings`). Not vacuous: at least one window has readings."""
    read = [w for w in windows if w.get("has_readings")]
    assert read, ("KISIWA-COHORT: no Kisiwa dispatch window with readings", len(windows))
    bad = [(str(w.get("window_start")), w.get("cohort_status")) for w in read
           if w.get("cohort_status") != "SELECTED_UNIQUE"]
    assert not bad, ("KISIWA-COHORT: Kisiwa days with readings not SELECTED_UNIQUE", bad)
    return {"windows": len(windows), "with_readings": len(read), "selected_unique": len(read)}


def kis5(plan: dict, outcome: dict, read_back: dict, windows_by_date: dict, summary: dict) -> dict:
    """KIS-5 (DIESEL-1-R3m §9m.4): the Kisiwa FUEL_BALANCE Action's stored fuel verdict reproduces.

    `plan`: the stored fuel plan; `outcome`: its stored outcome (`outcome`, `reasons`, `details`, `recorded_at`);
    `read_back`: window id -> `window(id)` read now (`revision`, `input_sha256`); `windows_by_date`: the candidate
    nights' latest windows as known at the outcome's `recorded_at`; `summary`: the served verdict page body.

    - every pinned window in `details` (baseline and later) reads back equal to its pin (revision, `input_sha256`);
    - the later pins are exactly the first 3 COMPLETE candidates as known at `recorded_at`;
    - `assess` over those windows gives the stored outcome and reasons (the verdict is recorded as computed: an
      INEFFECTIVE or INCONCLUSIVE that reproduces passes);
    - the served summary has `value` and `cost_check` null, no money key, and the fixed H1 line."""
    from assetops_backend.actions import fuel_verification as fv

    details = outcome["details"]
    pins = [details["baseline"], *details["later"]]
    for pin in pins:
        got = read_back.get(str(pin["window_id"]))
        assert got is not None, ("a pinned window cannot be read back", pin)
        assert (got["revision"], got["input_sha256"]) == (pin["revision"], pin["input_sha256"]), ("pin differs", pin, got)
    result = fv.assess(plan, windows_by_date, outcome["recorded_at"])
    chosen = [str(w.id) for w in result["chosen"]]
    assert chosen == [str(p["window_id"]) for p in details["later"]], ("later pins are not the first 3 COMPLETE", chosen)
    assert result["decided"] and (result["outcome"], list(result["reasons"])) == (
        outcome["outcome"], list(outcome["reasons"])), ("assess does not reproduce the stored verdict", result, outcome)
    assert summary.get("value") is None and summary.get("cost_check") is None, ("H2: a value on the fuel verdict",
                                                                               summary.get("value"))
    held = _money_keys(summary)
    assert not held, ("H2: a money key on the fuel verdict", held)
    assert summary.get("fixed_line") == fv.FIXED_LINE, ("H1 fixed line", summary.get("fixed_line"))
    return {"outcome": outcome["outcome"], "reasons": list(outcome["reasons"]), "pins_checked": len(pins),
            "later_nights": [p["night_date"] for p in details["later"]]}


def kis10(plan: dict, applied: dict, action: dict, claim_window_id: str, action_thread: str | None,
          finding_thread: str | None, board: dict, code: str, portfolio_lines: list[str]) -> dict:
    """KIS-10 (DIESEL-1-R3m §9m.4): fuel verification coherence.

    - the plan was recorded before the first later night began (`recorded_at < later_start`);
    - `effective_from` is the linked case's first COMPLETE `occurred_at` (`applied`);
    - the plan's origin Finding revision is the Action's; its baseline window is the one the revision's claim cites;
    - the Action's chain thread is the Finding's `UNEXPLAINED_FUEL` thread;
    - the Kisiwa board (the outcome's Site-local day + 1) lists a Verified results entry starting with the Action's
      display code whose Ref is FUEL_VERDICT;
    - no Kisiwa board `verified_values` entry and no Portfolio value line names this Action (H2)."""
    from assetops_backend.outcomes.display_code import display_code

    assert plan["recorded_at"] < plan["later_start"], ("frozen after the first later night began", plan["recorded_at"],
                                                       plan["later_start"])
    assert plan["effective_from"] == applied["occurred_at"], ("effective_from", plan["effective_from"], applied)
    assert str(plan["origin_finding_revision_id"]) == str(action["origin_finding_revision_id"]), "origin revision"
    assert str(plan["baseline_selection"]["window_id"]) == str(claim_window_id), ("baseline window", claim_window_id)
    assert action_thread is not None and action_thread == finding_thread, ("thread", action_thread, finding_thread)
    shown = display_code(code)
    assure = next((r for r in board.get("rows") or () if r.get("category") == "ASSURE_PERFORMANCE"), None)
    assert assure is not None, "no Assure row on the Kisiwa board"
    entries = [c for c in assure.get("contributors") or () if c.get("key") == "verified_results"
               and str(c.get("text") or "").startswith(shown) and (c.get("link_ref") or {}).get("kind") == "FUEL_VERDICT"
               and str((c.get("link_ref") or {}).get("id")) == str(action["id"])]
    assert len(entries) == 1, ("the fuel Action's Verified results entry", [c.get("text") for c in
                                                                           assure.get("contributors") or ()])
    values = [v for r in board.get("rows") or () for v in (r.get("nodes") or {}).get("verified_values") or ()]
    values += list(board.get("verified_values") or ())
    named = [v for v in values if str(v.get("key")) == str(action["id"]) or v.get("action_code") == code]
    assert not named, ("H2: a verified value names the fuel Action", named)
    lines = [x for x in portfolio_lines if shown in x]
    assert not lines, ("H2: a Portfolio value line names the fuel Action", lines)
    return {"entry": entries[0].get("text"), "thread": action_thread}


def action_ref_kind(action: dict) -> str | None:
    ref = action.get("ref")
    return ref.get("kind") if isinstance(ref, dict) else None


#: D-E5.13 item 3 (WK-GAP): the Kobo day measures whose week pattern the owner judged (2026-11-10).
WEEK_GAP_MEASURES = ("critical_served", "daylight_headroom_kw", "productive_kwh", "avoidable_gen_min")


def gap_gated(days_schema) -> bool:
    """D-E5.21: WK-GAP asserts the week and month patterns only when the built `days.json` schema version is 4 or
    higher (key on the version, not the file name). `days_schema` is the `schema` dict ({"id", "version"}) or the
    version itself. Fails closed: a missing or unreadable version is gated; only an explicit version below 4 is not."""
    version = days_schema.get("version") if isinstance(days_schema, dict) else days_schema
    if isinstance(version, int) and not isinstance(version, bool):
        return version >= 4
    return True


def week_day_classes(site_days: list[dict], week: list[str]) -> tuple[list[str], list[str]]:
    """WK-GAP: (missed, partial) days of `week` from the built calendar (`days.json`), never from hard-coded dates. A
    missed day has no run (a `missing` kind, or no entry at all); a partly checked day has runs but no complement
    (a story-only kind: its example hours only)."""
    ran = {d["day"] for d in site_days if d.get("kind") != "missing" and d.get("has_run", True)}
    full = {d["day"] for d in site_days if d.get("complement_of")}
    return [d for d in week if d not in ran], [d for d in week if d in ran and d not in full]


def week_gap_pattern(grades_by_measure: dict[str, dict[str, dict[str, str]]], week: list[str], missed: list[str],
                     partial: list[str]) -> dict:
    """WK-GAP (D-E5.13 item 3): the owner's week pattern, "1 missed day with 1 partly missing". `grades_by_measure`
    is {measure: {subject: {local_day: grade}}} from the latest `site_day_snapshot` revisions. The calendar must hold
    exactly one missed and one partly checked day, and for every measure and subject: NO_DATA on exactly the missed
    day, PARTIAL on exactly the partly checked day, COMPLETE on the other days of the week."""
    assert len(missed) == 1 and len(partial) == 1, ("not one missed and one partly checked day", missed, partial)
    complete = [d for d in week if d not in missed and d not in partial]
    out = {}
    for m in WEEK_GAP_MEASURES:
        subjects = grades_by_measure.get(m) or {}
        assert subjects, ("no day snapshot for the measure", m)
        for subject, by_day in sorted(subjects.items()):
            got = {g: [d for d in week if by_day.get(d) == g] for g in ("NO_DATA", "PARTIAL", "COMPLETE")}
            absent = [d for d in week if d not in by_day]
            assert not absent, (m, subject, "days with no snapshot", absent)
            assert got == {"NO_DATA": missed, "PARTIAL": partial, "COMPLETE": complete}, (
                m, subject, got, {d: by_day[d] for d in week})
            out[f"{m}|{subject}"] = got
    return {"missed": missed, "partial": partial, "complete": complete, "measures": out}


def month_day_classes(site_days: list[dict], days: list[str]) -> tuple[list[str], list[str]]:
    """WK-GAP month clause (D-E5.19 item 3): (missing-kind, story-only) days of `days` from the built calendar. Unlike
    the week, a day with no entry at all is in neither list, so if it reads NO_DATA the clause fails (an unbuilt
    stretch such as v3's S-27..S-22 is the alarm)."""
    missing = {d["day"] for d in site_days if d.get("kind") == "missing"}
    ran = {d["day"] for d in site_days if d.get("kind") != "missing" and d.get("has_run", True)}
    full = {d["day"] for d in site_days if d.get("complement_of")}
    return [d for d in days if d in missing], [d for d in days if d in ran and d not in full]


def month_gap_pattern(grades_by_measure: dict[str, dict[str, dict[str, str]]], days: list[str], missed: list[str],
                      partial: list[str]) -> dict:
    """WK-GAP month clause (D-E5.19 item 3): on [S-28, S], for every measure and subject, NO_DATA on exactly the
    `missing`-kind days and PARTIAL on exactly the story-only days. A day with no snapshot row counts as NO_DATA (no
    checked reading), so it passes only on a `missing` day. Other grades are not judged here."""
    out = {}
    for m in WEEK_GAP_MEASURES:
        subjects = grades_by_measure.get(m) or {}
        assert subjects, ("no day snapshot for the measure", m)
        for subject, by_day in sorted(subjects.items()):
            got = {g: [d for d in days if by_day.get(d, "NO_DATA") == g] for g in ("NO_DATA", "PARTIAL")}
            assert got == {"NO_DATA": missed, "PARTIAL": partial}, (m, subject, "month", got, missed, partial)
            out[f"{m}|{subject}"] = {**got, "no_snapshot": [d for d in days if d not in by_day]}
    return {"missed": missed, "partial": partial, "days": len(days), "measures": out}


def site_days_segment(line: str | None, name: str) -> str | None:
    """The "{name}: ..." part of a card days line ("{Site}: {line}" parts, " · "-joined), up to the next Site part."""
    i = (line or "").find(f"{name}: ")
    if i < 0:
        return None
    rest = line[i + len(name) + 2:]
    nxt = re.search(r" · (?=[^·:]+: )", rest)
    return rest[:nxt.start()] if nxt else rest


def not_judged_texts() -> set[str]:
    """Every `LIMIT_UNKNOWN` sentence the vocabulary can render for a 5-day study (1 to 5 days with no reading)."""
    from assetops_backend.chain import vocabulary as v

    return {v.limit_line("UNKNOWN", (), [None] * n + ["ELIGIBLE"] * (5 - n)) for n in range(1, 6)}


def wk2b(grow: dict, kw_pattern, eligible_days: int = 0) -> dict:
    """WK-2b restated (R6 O6; DD1b2-R Q10): on S no headline money, the headline is not the kW pattern, the sales
    contributor starts "0 kWh used by Grain mill".
    D-E5.13 item 4 (cause D-E5.12): the potential follows the study ending S. With `eligible_days` >= 1 (v4) it is
    the "Not judged yet: n of the 5 study days ..." sentence, with no kW and no money on the node or the chip; with 0
    (v3) it reads "No potential found yet"."""
    assert not grow.get("headline_money"), grow.get("headline_money")
    assert not kw_pattern.fullmatch(grow["headline"]), grow["headline"]
    sales = next(c for c in grow["contributors"] if c["key"] == "productive_sales")
    assert sales["text"].startswith("0 kWh used by Grain mill"), sales["text"]
    text = nodes_potential_text(grow).strip()
    if eligible_days:
        assert text in not_judged_texts(), ("the study ending S has eligible days", eligible_days, text)
        for shown in ((grow.get("nodes") or {}).get("potential"), grow.get("potential")):
            t = potential_text(shown)
            assert not re.search(r"\d\s*(–|-|to)?\s*\d*\s*kW", t), ("a kW figure shows", t)
            assert not re.search(r"(USD|\$)\s*\d|\d\s*(USD|\$)", t), ("money shows", t)
            if isinstance(shown, dict):
                assert not shown.get("value_line") and not shown.get("value"), ("a value line shows", shown)
                assert not any(k for k in shown if "money" in k and shown[k]), ("money shows", shown)
    else:
        assert NO_POTENTIAL in text, (grow.get("nodes", {}).get("potential"), grow.get("potential"))
    return {"headline": grow["headline"], "sales": sales["text"], "potential": text}


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


# ---- DIESEL-K7 (ruling DIESEL-1-R3l §9l.3): KIS-3 and KIS-9 ---------------------------------------------------------

#: Carry DIESEL-1-R3k2 L2: a combined dataset without the Kisiwa Site is a failure of every KIS row, not a skip.
KISIWA_MISSING_BODY = {"kisiwa": "missing: no KISIWA-001 Site in this dataset", "checked": 0}


class KisiwaMissing(AssertionError):
    """A KIS row ran on a dataset with no `KISIWA-001` Site. The row is marked failed and its failing body is `body`."""

    body = KISIWA_MISSING_BODY

    def __init__(self) -> None:
        super().__init__(json.dumps(self.body))


def failed_result(exc: Exception) -> dict:
    """A failed row's `check.json` entry: the error text, and the failing body when the failure carries one."""
    out = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"[:2000]}
    if isinstance(exc, KisiwaMissing):
        out["read"] = exc.body
    return out

#: K3's literal: night 4's reporting gap in the F0 world (moved by the story's `delta_days`).
KIS_F0_GAP_SPAN = ("2026-10-04T21:45:00Z", "2026-10-04T23:30:00Z")
KIS_INCIDENT_NIGHT = 4
#: K3's parity rule (§9d.6 C): power is published at 0.000001 kW, so these five terms agree within 1/100000 L.
KIS_TOLERANCE_L = "1/100000"
KIS_EXACT = {"opening_exact": "opening_l", "closing_exact": "closing_l", "deliveries_exact": "deliveries_l",
             "delivery_tolerance_exact": "delivery_tolerance_l"}
KIS_TOLERANCED_TERMS = {"loaded_litres_exact": "loaded_litres", "use_low_exact": "use_low", "use_high_exact": "use_high"}


def _kis_utc(value) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def kis3(windows: dict[int, dict], handover: dict, delta_days: int) -> dict:
    """KIS-3 (moved from K9 to K7): nights 1-10's latest stored window as known now equals the handover's night.

    `windows`: night k -> the stored row (`state`, `reason`, `gap_minutes`, `gap_spans` [[start, end]], `limitations`,
    `terms`, `residual_low`, `residual_high` exact text). Exact: state, reason (None), gap, opening, closing, D, D_tol.
    Within 1/100000 L: loaded litres, use low/high, residual low/high. The band re-computed by
    `fuel_balance.rules.balance` from the stored terms equals the stored band exactly. Night 4 UNEXPLAINED with F0's
    gap span moved by `delta_days` and `("REPORTING_GAP",)`; every other night WITHIN_MARGIN, gap 0, no limitation;
    idle seconds 0 on all ten. A pass prints `tolerance_l` and `max_diff_l` (DIESEL-1-R3n §9o.3): per toleranced
    term, the largest |stored - handover| over the ten nights, as exact `Fraction` text."""
    from fractions import Fraction

    from assetops_backend.actions.verification_rules import parse_exact
    from assetops_backend.fuel_balance.rules import balance

    tol = Fraction(KIS_TOLERANCE_L)
    states = {}
    # DIESEL-1-R3n §9o.3: the largest |stored - handover| over the ten nights, per toleranced term (the evidence)
    max_diff = {term: Fraction(0) for term in (*KIS_TOLERANCED_TERMS.values(), "residual_low", "residual_high")}
    for night in handover["nights"]:
        k, want = night["k"], night["readings"]
        w = windows.get(k)
        assert w is not None, ("no stored window", k)
        t = w["terms"]
        exact = {"state": (w["state"], want["state"]), "reason": (w["reason"], None),
                 "gap_minutes": (w["gap_minutes"], want["gap_minutes"])}
        exact |= {key: (parse_exact(t[term]), Fraction(want[key])) for key, term in KIS_EXACT.items()}
        bad = {key: pair for key, pair in exact.items() if pair[0] != pair[1]}
        assert not bad, ("night", k, "exact terms differ", bad)
        close = {key: (parse_exact(t[term]), Fraction(want[key])) for key, term in KIS_TOLERANCED_TERMS.items()}
        close |= {f"residual_{s}_exact": (parse_exact(w[f"residual_{s}"]), Fraction(want[f"residual_{s}_exact"]))
                  for s in ("low", "high")}
        far = {key: str(abs(a - b)) for key, (a, b) in close.items() if abs(a - b) > tol}
        assert not far, ("night", k, "differs by more than 1/100000 L", far)
        for key, (a, b) in close.items():
            term = key.removesuffix("_exact")
            max_diff[term] = max(max_diff[term], abs(a - b))
        assert t["idle_seconds"] == 0, ("night", k, "idle seconds", t["idle_seconds"])
        band = balance(opening=parse_exact(t["opening_l"]), closing=parse_exact(t["closing_l"]),
                       deliveries=[parse_exact(t["deliveries_l"])], loaded_litres=parse_exact(t["loaded_litres"]),
                       idle_hours=Fraction(t["idle_seconds"], 3600), accuracy_l=parse_exact(t["accuracy_l"]),
                       no_load_l_per_h=parse_exact(t["no_load_l_per_h"]))
        again = (band["state"], band["residual_low"], band["residual_high"])
        stored = (w["state"], parse_exact(w["residual_low"]), parse_exact(w["residual_high"]))
        assert again == stored, ("night", k, "band not reproduced", again, stored)
        spans = [[_kis_utc(a), _kis_utc(b)] for a, b in w["gap_spans"]]
        if k == KIS_INCIDENT_NIGHT:
            move = timedelta(days=delta_days)
            want_spans = [[_kis_utc(KIS_F0_GAP_SPAN[0]) + move, _kis_utc(KIS_F0_GAP_SPAN[1]) + move]]
            assert (w["state"], spans, list(w["limitations"])) == ("UNEXPLAINED", want_spans, ["REPORTING_GAP"]), (
                "night 4", w["state"], spans, w["limitations"])
        else:
            assert (w["state"], w["gap_minutes"], list(w["limitations"])) == ("WITHIN_MARGIN", 0, []), (
                "night", k, w["state"], w["gap_minutes"], w["limitations"])
        states[k] = w["state"]
    return {"nights": len(states), "states": states, "tolerance_l": KIS_TOLERANCE_L,
            "max_diff_l": {term: str(value) for term, value in max_diff.items()}}


def kis9(*, records: list[dict], handover: dict, calendar: dict, build: dict, actions: list[dict],
         runs: list[tuple[datetime, datetime]], windows: dict[int, dict], finding: dict | None,
         action: dict | None) -> dict:
    """KIS-9: Kisiwa story coherence (DIESEL-1-R3l §9l.3).

    `records`: the Site's operational records (`kind`, `body`, `occurred_at`, `recorded_at`, `quantity`,
    `source_document_sha256`, `case_id`); `calendar`: `story["kisiwa"]`; `build`: `kisiwa.json`; `actions`: the
    derived log's actions; `runs`: the ten runs' `[start, end)`; `windows`: night k -> the latest stored window
    (`id`, `revision`, `recorded_at`); `finding`: the fuel Finding read (`findings`: `finding_id`, `lifecycle`,
    `window_id`, `window_revision`, `thread_kinds`, `consequence_state`, `price_revision_id`, `created_at`; and
    `diesel_v1_revision_id`); `action`: the Action read (`origin_finding_id`, `case_id`, `case_state`,
    `linked_case_ids`, and K7-F's `plan_recorded_at` and `outcome_recorded_at`: the stamps of its verification plans
    and outcomes)."""
    import hashlib
    from fractions import Fraction

    import demo_combined_kisiwa as kis

    minutes = lambda r: (_kis_utc(r["recorded_at"]) - _kis_utc(r["occurred_at"])).total_seconds() / 60  # noqa: E731
    by_kind = lambda kind: [r for r in records if r["kind"] == kind]  # noqa: E731
    log = {a["action_id"]: a for a in actions}
    # (a) records
    delivery = next(a for a in actions if a["kind"] == "FUEL_DELIVERY")
    ticket = kis.TICKET_TEXT.format(reference=delivery["ticket"]["reference"], volume_l=delivery["volume_l"])
    got = by_kind("FUEL_DELIVERY")
    assert len(got) == 1, ("(a) want one FUEL_DELIVERY", got)
    d = got[0]
    assert (Fraction(str(d["quantity"])), d["source_document_sha256"], minutes(d)) == (
        Fraction(delivery["volume_l"]), hashlib.sha256(ticket.encode("ascii")).hexdigest(),
        delivery["recorded_after_minutes"]), ("(a) delivery", d)
    log_dips = {_kis_utc(a["at"]): a["action_id"] for a in actions if a["kind"] == "TANK_DIP"}
    dips = by_kind("TANK_DIP")
    assert sorted(_kis_utc(r["occurred_at"]) for r in dips) == sorted(log_dips), ("(a) dips are not the log's", dips)
    late = [r for r in dips if minutes(r) != calendar["dip_recorded_after_minutes"]]
    assert not late, ("(a) a dip is not recorded 15 min after it occurred", late)
    visits = by_kind("SITE_VISIT")
    assert len(visits) == 1 and visits[0]["body"] == calendar["action"]["site_visit"]["body"], ("(a) site visit", visits)
    removal = next(a for a in actions if a["kind"] == "FUEL_REMOVAL_UNRECORDED")
    lo = _kis_utc(removal["at"])
    hi = lo + timedelta(minutes=removal["duration_minutes"])
    named = [r for r in records if lo <= _kis_utc(r["occurred_at"]) < hi or removal["action_id"] in r["body"]
             or "remov" in r["body"].lower()]
    assert not named, ("(a) a record occurs inside the removal or names it", named)
    # (b) dip quantities: the handover's and the build's trajectory check
    want = {x["action_id"]: x["dip_l"] for x in handover["dips"]}
    built = {x["action_id"]: x["dip_l"] for r in build["runs"] for x in r["dips"]}
    for r in dips:
        action_id = log_dips[_kis_utc(r["occurred_at"])]
        assert Fraction(str(r["quantity"])) == want[action_id] == built.get(action_id), (
            "(b) dip", action_id, r["quantity"], want[action_id], built.get(action_id))
    # (c) every action of the derived log lies in exactly one run (K0's residual)
    try:
        placed = kis.straddle_check(actions, runs)
    except SystemExit as stop:
        raise AssertionError(f"(c) {stop}") from None
    # (d) the Finding
    assert finding is not None, "(d) no fuel Finding read"
    fs = finding["findings"]
    assert len(fs) == 1, ("(d) want exactly one fuel Finding", fs)
    f = fs[0]
    w4 = windows[KIS_INCIDENT_NIGHT]
    assert (f["lifecycle"], str(f["window_id"]), f["window_revision"]) == ("SUPPORTED", str(w4["id"]), 1), ("(d)", f)
    assert list(f["thread_kinds"]) == ["UNEXPLAINED_FUEL"], ("(d) threads", f["thread_kinds"])
    assert (f["consequence_state"], str(f["price_revision_id"])) == ("PRICED", str(finding["diesel_v1_revision_id"])), (
        "(d) consequence", f)
    # (e) the Action
    assert action is not None, "(e) no Action read"
    assert str(action["origin_finding_id"]) == str(f["finding_id"]), ("(e) origin", action)
    assert action["case_state"] == "COMPLETE" and str(action["case_id"]) in map(str, action["linked_case_ids"]), (
        "(e) case", action)
    assert str(visits[0]["case_id"]) == str(action["case_id"]), ("(e) the site visit does not cite the case", visits)
    # (e) K7-F: the plan is frozen at `plan.freeze_at` and one verdict is stored at `evaluate_at` (§9m.5)
    plans, outcomes = action.get("plan_recorded_at") or [], action.get("outcome_recorded_at") or []
    assert [_kis_utc(p) for p in plans] == [_kis_utc(calendar["plan"]["freeze_at"])], ("(e) plan stamp", plans)
    assert [_kis_utc(o) for o in outcomes] == [_kis_utc(calendar["evaluate_at"])], ("(e) verdict stamp", outcomes)
    # (f) every run's frozen identity names the derived log and exactly its effect-bearing actions
    assert (build["log"]["log_id"], build["log"]["log_version"]) == (calendar["story_log_id"], 1), ("(f)", build["log"])
    assert [r["k"] for r in build["runs"]] == list(range(1, len(runs) + 1)), ("(f) runs", [r["k"] for r in build["runs"]])
    for r in build["runs"]:
        mine = sorted(i for i, k in placed.items() if k == r["k"] and log[i]["kind"] in kis.EFFECT_BEARING)
        assert sorted(e.split(":")[1] for e in r["history"]) == mine, ("(f) history", r["k"], r["history"], mine)
        assert r.get("log_sha256") == build["log"]["sha256"], ("(f) run log hash", r["k"], r.get("log_sha256"))
    # (g) stamps are story instants
    by_k = {x["k"]: x for x in calendar["runs"]}
    for k, w in windows.items():
        assert _kis_utc(w["recorded_at"]) == _kis_utc(by_k[k]["assessed_at"]), ("(g) window stamp", k, w["recorded_at"])
    assert _kis_utc(f["created_at"]) == _kis_utc(by_k[KIS_INCIDENT_NIGHT]["raised_at"]), ("(g) Finding stamp", f)
    assert _kis_utc(visits[0]["recorded_at"]) == _kis_utc(calendar["site_visit_recorded_at"]), ("(g) visit", visits)
    return {"records": len(records), "dips": len(dips), "placed": len(placed), "finding": str(f["finding_id"]),
            "action_case": str(action["case_id"])}


# ---- FUEL-1 A3 (A3-R §3.9): idle fuel on Kobo, written now, run at E3 ------------------------------------------------

#: A3-R S-c: the probe's idle seconds (200 min per idle morning; 12 slots of the trial's baseline hour). A difference is
#: a data finding, never a retune.
IDLE_MORNING_SECONDS, TRIAL_BASELINE_IDLE_SECONDS = 12000, 3600


def _declared_rate() -> Decimal:
    """The Kobo declaration's own value (`demo_combined_kobo.NO_LOAD`), never retyped here."""
    from demo_combined_kobo import NO_LOAD

    return Decimal(str(next(p["value"] for p in NO_LOAD if p["property_key"] == "generator-no-load-fuel-rate")))


def idle_morning(day: str, stored: dict, cost_row: dict) -> dict:
    """A3-R §3.9 MONEY-B (O16): one idle morning. `stored` is the day's head consequence row (SQL column names);
    `cost_row` is that day's board OPTIMIZE_COST row. The row is fuel-cost-2 PRICED, idle-only and exact, its idle
    seconds are the probe's, the headline is `COST_IDLE` built through the board's own helpers from the stored fields,
    and the money prefix is the stored row's outward display (`headline_money` unchanged)."""
    from fractions import Fraction

    from assetops_backend.chain.outcomes import _litres
    from assetops_backend.financials.consequence_read import display
    from assetops_backend.site_outcomes.mini import idle_headline

    assert stored.get("model_id") == "fuel-cost-2" and stored.get("state") == "PRICED", (day, stored)
    idle = stored.get("idle_seconds")
    assert idle == IDLE_MORNING_SECONDS, ("S-c: stored idle seconds", day, idle, "want", IDLE_MORNING_SECONDS)
    rate = Decimal(str(stored["no_load_fuel_rate_l_per_h"]))
    assert rate == _declared_rate(), (day, "stored rate", rate)
    exact = Fraction(str(stored["sfc_upper_multiplier"])) * Fraction(idle, 3600) * Fraction(str(rate))
    assert Fraction(str(stored["quantity_high_exact"])) == exact, ("S-c: not idle-only", day, stored, exact)
    assert Fraction(str(stored["amount_high"])) == Fraction(str(stored["quantity_high"])) * Fraction(
        str(stored["price_value"])), (day, "amount is not upper litres x stored price", stored)
    want = idle_headline({"idle_seconds": idle, "rate": str(rate), "basis": stored.get("no_load_fuel_rate_basis"),
                          "litres_high": _litres(stored["quantity_high"])})
    assert cost_row.get("headline") == want, (day, cost_row.get("headline"), want)
    shown = display({"state": stored["state"], "currency": stored["currency"], "amount_low": stored["amount_low"],
                     "amount_high": stored["amount_high"]})
    money = cost_row.get("headline_money") or {}
    assert Decimal(str(money.get("amount_high"))) == Decimal(str(shown["amount_high"])), (day, money, shown)
    return {"day": day, "idle_seconds": idle, "high_exact": str(stored["quantity_high_exact"]),
            "amount_high": str(stored["amount_high"]), "shown_high": str(money.get("amount_high")),
            "headline": cost_row.get("headline")}


def never_summed(amounts: list[str], bodies: list[object]) -> int:
    """A3-R §3.9: no string in `bodies` holds the sum of two (or all) mornings' amounts. `amounts` are the STORED
    `amount_high` values (e.g. 15.125); each sum is searched half-even, half-up and rounded up, and as the sum of the
    outward-rounded parts (15.125 x 2 -> 30.25 and 30.26; x 3 -> 45.38 and 45.39). Returns the number of combinations
    checked (0 only when fewer than two amounts were given, which the caller asserts against)."""
    from itertools import combinations

    strings: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, str):
            strings.append(node)
        elif isinstance(node, dict):
            for x in node.values():
                walk(x)
        elif isinstance(node, (list, tuple)):
            for x in node:
                walk(x)

    for b in bodies:
        walk(b)
    from decimal import ROUND_CEILING, ROUND_HALF_EVEN, ROUND_HALF_UP

    cent = Decimal("0.01")
    combos = [combo for n in range(2, len(amounts) + 1) for combo in combinations(amounts, n)]
    sums: set[str] = set()
    for combo in combos:
        exact = sum(Decimal(a) for a in combo)
        for mode in (ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_CEILING):
            sums.add(f"{exact.quantize(cent, rounding=mode)}")
        # the sum of the outward-rounded (shown) parts, as code summing displayed amounts would give
        sums.add(f"{sum(Decimal(a).quantize(cent, rounding=ROUND_CEILING) for a in combo)}")
    hit = [(s, x) for s in sorted(sums) for x in strings if s in x]
    assert not hit, ("a sum of mornings is shown", hit[:3])
    return len(combos)


def steady_day(day: str, stored: list[dict], cost_row: dict) -> dict:
    """A3-R §3.9: a steady or steady-before day has no idle fuel: every stored head row (if any) has 0 or no idle
    seconds, and the headline is not the idle line. The headline and money are reported as shown."""
    from assetops_backend.site_outcomes.mini import COST_IDLE

    assert all(not r.get("idle_seconds") for r in stored), (day, stored)
    head = str(cost_row.get("headline") or "")
    assert not head.startswith(COST_IDLE.split(":")[0] + ":"), (day, head)
    return {"day": day, "stored_rows": len(stored), "headline": cost_row.get("headline"),
            "money": cost_row.get("headline_money")}


def trial_cost(cc: dict, result: dict) -> dict:
    """A3-R §3.9 PROBE_CHOSEN: ACT-001's stored `/2` row. MODELLED_IMPROVEMENT; the baseline idle seconds are the 12
    slots R3h kept (S-c); `fuel_change_l` = stored rate x (baseline - later idle seconds) / 3600; the priced total is
    that x the stored price; the stored basis is GENERIC_DEFAULT; the summary's price per litre is the stored price."""
    from fractions import Fraction

    assert cc.get("state") == "MODELLED_IMPROVEMENT" and result.get("state") == "MODELLED_IMPROVEMENT", (cc, result)
    assert result.get("formula") == "trial-fuel-comparison/2", result.get("formula")
    w = result.get("windows") or {}
    b, l = (w.get("baseline") or {}).get("idle_seconds"), (w.get("later") or {}).get("idle_seconds")
    assert b == TRIAL_BASELINE_IDLE_SECONDS, ("S-c: trial baseline idle seconds", b, "want", TRIAL_BASELINE_IDLE_SECONDS)
    rate = Fraction(str((result.get("no_load") or {}).get("value_l_per_h")))
    assert rate == Fraction(str(_declared_rate())), ("stored rate", rate)
    pt, price = result.get("priced_total") or {}, Fraction(str((result.get("price") or {}).get("value")))
    change = rate * Fraction(b - (l or 0), 3600)
    assert Fraction(str(pt.get("fuel_change_l"))) == change, (pt, change)
    assert Fraction(str(pt.get("amount"))) == change * price, (pt, change, price)
    assert (result.get("no_load") or {}).get("basis") == "GENERIC_DEFAULT", result.get("no_load")
    assert Fraction(str(cc.get("price_per_litre"))) == price and cc.get("priced_total") == pt, cc
    return {"baseline_idle_seconds": b, "later_idle_seconds": l, "fuel_change_l": pt.get("fuel_change_l"),
            "amount": pt.get("amount"), "price": str(result["price"]["value"]),
            "per_demand_kwh": (result.get("change_per_demand_kwh") or {}).get("nominal"),
            "basis": result["no_load"]["basis"]}


def optimize_card(summary: dict, site: str = "KOBO-001", allowed: tuple[str, ...] = ("KOBO-001",)) -> dict:
    """A3-R §3.9 CH-5d1 / O1: on the S summary `site` (Kobo, after the declaration) is priced and every priced Site is
    one of `allowed`. Exactly one priced Site: the Optimize card's value is that Site's cost claim text byte-equal,
    its `claim` that claim (replacing CH5d1-R §4's "Not known yet" forecast). DIESEL-1-R3p (A3 L3): two or more
    priced Sites (Kisiwa's dispatch Findings): the card lists each one's claim on its own, in Site order, never summed."""
    priced = []
    for s in summary.get("sites") or ():
        row = next((r for r in s.get("rows") or () if r.get("category") == "OPTIMIZE_COST"), None) or {}
        claim = (row.get("nodes") or {}).get("earnings")
        if claim is not None and claim.get("value") is not None:
            priced.append((s, claim))
    codes = [s.get("site_code") for s, _ in priced]
    assert site in codes and set(codes) <= set(allowed), ("priced Sites on S", codes, allowed)
    card = (summary.get("cards") or {}).get("OPTIMIZE_COST") or {}
    if len(priced) == 1:
        claim = priced[0][1]
        assert (card.get("value") or {}).get("text") == claim.get("text") and card.get("claim") == claim, (card, claim)
        return {"text": claim["text"]}
    from assetops_backend.chain.vocabulary import COST_SMALL, card_text, sites_text

    text = card_text("cost.sites", sites=sites_text(len(priced)))
    detail = " · ".join(card_text("cost.site", site=s.get("site_name") or s.get("site_code"), text=c["text"],
                                  small=COST_SMALL[c["key"].removeprefix("money.")]) for s, c in priced)
    card_value = (card.get("value") or {}).get("text")
    assert card_value == text and card.get("claim") is None and card.get("detail") == detail, (card, text, detail)
    return {"text": card_value, "priced": codes}


def trial_page(body: dict, result: dict) -> str:
    """A3-R §3.9 A3-PAGE: ACT-001's verification outcome body carries `fuel_value` equal to `FUEL_VALUE_PAGE` built
    from the stored row through the imported helpers."""
    from assetops_backend.chain.vocabulary import (
        FUEL_VALUE_PAGE, NO_LOAD_BASIS_WORDS, money_text, price_text, trial_litres)

    pt = result.get("priced_total") or {}
    want = FUEL_VALUE_PAGE.format(
        l=trial_litres(pt["fuel_change_l"]), amount=money_text(pt["amount"], None, pt.get("currency")),
        p=price_text(result["price"]["value"]), cur=pt.get("currency") or "",
        basis=NO_LOAD_BASIS_WORDS.get((result.get("no_load") or {}).get("basis"), NO_LOAD_BASIS_WORDS[None]))
    assert body.get("fuel_value") == want, (body.get("fuel_value"), want)
    return want


# ---- DIESEL-K9 (ruling DIESEL-1-R3q §9q.2-§9q.4): KIS-1, KIS-2, KIS-6, KIS-7 -----------------------------------------

KIS_SITE = "KISIWA-001"
KIS_ZONE = "Africa/Dar_es_Salaam"
KIS_FOUR = ("COLD-LAB-001", "EV-LAB-001", "KISIWA-001", "KOBO-001")  # sorted


def _field(row, name: str):
    return row.get(name) if isinstance(row, dict) else getattr(row, name)


# ---- OWN-G1 (OWN-GAPS R2-G1 Q3): the KIS rows read the story calendar only -----------------------------------------
# `add-dates` appends nights after the story; the KIS rows pin the prepared story, so each bounded read keeps only the
# calendar's nights and what occurred in `[run1_start, runs[-1].end)` from `story.json`.

def kis_story_range(calendar: dict) -> tuple[datetime, datetime]:
    return _kis_utc(calendar["run1_start"]), _kis_utc(calendar["runs"][-1]["end"])


def kis_story_windows(windows: list[dict], calendar: dict) -> list[dict]:
    """Stored window rows (with `night_date`) of the calendar's nights only."""
    nights = {r["night_date"] for r in calendar["runs"]}
    return [w for w in windows if str(w["night_date"])[:10] in nights]


def kis_story_records(records: list[dict], calendar: dict) -> list[dict]:
    """Operational records that occurred inside the story's runs."""
    lo, hi = kis_story_range(calendar)
    return [r for r in records if lo <= _kis_utc(r["occurred_at"]) < hi]


def kis_story_dispatch(latest: list[dict], calendar: dict) -> list[dict]:
    """Dispatch Finding revisions whose episode starts inside the story's runs."""
    lo, hi = kis_story_range(calendar)
    return [r for r in latest if lo <= _kis_utc(r["episode_start"]) < hi]


def _props(content: dict, component_id: str) -> dict[str, dict]:
    comp = next((c for c in content.get("components") or () if c.get("component_id") == component_id), None)
    return {p["property_key"]: p for p in (comp or {}).get("properties") or ()}


def kis1(revisions: list, register: dict, prices: list[dict], nights: int) -> dict:
    """KIS-1 (DIESEL-1-R3q §9q.3): Kisiwa's Foundation as known now. `revisions`: the Site's Foundation revisions
    (`RevisionRow` or dicts with `valid_from`, `superseded_at`, `content`); only current-knowledge rows count.
    `register`: `kisiwa-register.json`; `prices`: one `price_selection` per stored night window (`state`, `revision_id`,
    `value`, `currency`). Stop setting 90 % in every current revision; no-load 4.9 L/h GENERIC_DEFAULT and sensor
    accuracy 10 L GENERIC_DEFAULT in every revision from their effective instants (equal to the declarations, read);
    every window priced by one revision equal to diesel price step v1 (read from the fixture file). `nights`: the
    stored night count the story expects (`len(kisiwa.json["runs"])`); all of them are priced, not a subset."""
    import demo_combined_kisiwa as kis

    current = [r for r in revisions if _field(r, "superseded_at") is None]
    # the Site exists (the row wrapper raises KisiwaMissing without it); no current revision is a different fault
    assert current, ("Kisiwa has no current Foundation revision", len(list(revisions)))
    stops = {(Decimal(str(p.get("value"))), p.get("unit")) for r in current
             for p in [_props(_field(r, "content"), "generator").get("stop-soc-threshold") or {}]}
    assert stops == {(Decimal("90"), "%")}, ("stop setting is not 90 % in every current revision", sorted(map(str, stops)))

    def since(key: str) -> list:
        lo = _kis_utc(register[key])
        got = [r for r in current if _kis_utc(_field(r, "valid_from")) >= lo]
        assert got, ("no current revision from", key, register[key])
        return got

    def declared(props: list[dict], key: str) -> tuple:
        p = next(x for x in props if x["property_key"] == key)
        return Decimal(str(p["value"])) if p["unit"] != "state" else p["value"], p["unit"]

    no_load = (declared(kis.NO_LOAD, "generator-no-load-fuel-rate"),
               declared(kis.NO_LOAD, "generator-no-load-fuel-rate-basis"))
    assert no_load == ((Decimal("4.9"), "L/h"), ("GENERIC_DEFAULT", "state")), ("declared no-load", no_load)
    accuracy_props = kis.ROLES4["component_properties"]["properties"]
    accuracy = (declared(accuracy_props, "fuel-level-sensor-accuracy"),
                declared(accuracy_props, "fuel-level-sensor-accuracy-basis"))
    assert accuracy == ((Decimal("10"), "L"), ("GENERIC_DEFAULT", "state")), ("declared accuracy", accuracy)
    for key, component, names, want in (
            ("no_load_effective_from", "generator", ("generator-no-load-fuel-rate", "generator-no-load-fuel-rate-basis"),
             no_load),
            ("roles4_effective_from", "fuel-tank", ("fuel-level-sensor-accuracy", "fuel-level-sensor-accuracy-basis"),
             accuracy)):
        for r in since(key):
            props = _props(_field(r, "content"), component)
            missing = [n for n in names if n not in props]
            assert not missing, ("a current revision lacks", missing, str(_field(r, "valid_from")))
            assert tuple(declared(list(props.values()), n) for n in names) == want, (
                component, str(_field(r, "valid_from")), [props[n] for n in names])
    v1 = next(s for s in json.loads(kis.FIXTURE_PRICES.read_text(encoding="utf-8"))["steps"] if s["step"] == "v1")
    assert (v1["value"], v1["currency"]) == ("1.25", "USD"), v1
    assert prices and len(prices) == nights, ("not every stored night window was priced", len(prices), "expected", nights)
    assert all(p["state"] == "PRICED" for p in prices), ("an unpriced night window", prices)
    revs = sorted({str(p["revision_id"]) for p in prices})
    assert len(revs) == 1, ("the nights are priced by more than one price revision", revs)
    assert all(Decimal(str(p["value"])) == Decimal(v1["value"]) and p["currency"] == v1["currency"] for p in prices), (
        "a night is not priced at step v1", prices)
    return {"current_revisions": len(current), "stop_soc_threshold": "90 %", "no_load": "4.9 L/h GENERIC_DEFAULT",
            "sensor_accuracy": "10 L GENERIC_DEFAULT", "price": f"{v1['value']} {v1['currency']} (v1)",
            "price_revision_id": revs[0], "windows_priced": len(prices)}


def kis2(heads: dict, intervals_by_head: dict, latest_revisions: list[dict]) -> dict:
    """KIS-2 (DIESEL-1-R3q §9q.4): every Kisiwa dispatch Finding's latest revision is SUPPORTED and its head
    consequence (`heads[finding_id]`, SQL column names incl. `id`) cites it, is fuel-cost-2 PRICED at the model's
    multiplier with the declared no-load 4.9 L/h GENERIC_DEFAULT, and its `quantity_high_exact` is exactly the
    fuel-cost-2 formula over its stored power intervals (`intervals_by_head[id]`); `quantity_high` is its ceiling and
    `idle_seconds` the idle intervals' seconds. Tolerance zero."""
    from fractions import Fraction

    import demo_combined_kisiwa as kis
    from assetops_backend.financials import fuel_cost, fuel_cost_v2

    assert latest_revisions, "no Kisiwa dispatch Finding"
    declared = Decimal(str(next(p["value"] for p in kis.NO_LOAD if p["property_key"] == "generator-no-load-fuel-rate")))
    F = lambda x: Fraction(str(x))  # noqa: E731
    out = []
    for rev in latest_revisions:
        fid = str(rev["finding_id"])
        assert rev["lifecycle"] == "SUPPORTED", ("S: a latest dispatch Finding revision is not SUPPORTED", rev)
        h = heads.get(fid)
        assert h is not None, ("S: a SUPPORTED dispatch Finding has no head consequence", fid)
        assert str(h["finding_revision_id"]) == str(rev["revision_id"]), ("head cites another revision", h, rev)
        assert h["model_id"] == "fuel-cost-2" and h["state"] == "PRICED", ("S: head not fuel-cost-2 PRICED", fid,
                                                                              h["model_id"], h["state"])
        assert Decimal(str(h["sfc_upper_multiplier"])) == fuel_cost_v2.MULTIPLIER, ("multiplier", h)
        rate = Decimal(str(h["no_load_fuel_rate_l_per_h"]))
        assert rate == Decimal("4.9") == declared and h["no_load_fuel_rate_basis"] == "GENERIC_DEFAULT", (
            "no-load", rate, h["no_load_fuel_rate_basis"])
        ivs = intervals_by_head.get(str(h["id"])) or []
        assert ivs, ("a head consequence with no stored power interval", h["id"])
        loaded = sum((F(i["mean_kw"]) * Fraction(int(i["duration_seconds"]), 3600) * F(i["sfc_l_per_kwh"])
                      for i in ivs if F(i["mean_kw"]) > 0), Fraction(0))
        idle_s = sum(int(i["duration_seconds"]) for i in ivs if F(i["mean_kw"]) == 0)
        idle = Fraction(idle_s, 3600) * F(rate)
        exact = F(h["sfc_upper_multiplier"]) * (loaded + idle)
        assert exact == Fraction(str(h["quantity_high_exact"])), ("quantity_high_exact", fid, h["quantity_high_exact"],
                                                                  f"{exact.numerator}/{exact.denominator}")
        assert Decimal(str(h["quantity_high"])) == fuel_cost.to_decimal_ceiling(exact), (
            "quantity_high is not the ceiling", h["quantity_high"], fuel_cost.to_decimal_ceiling(exact))
        assert int(h["idle_seconds"] or 0) == idle_s, ("idle_seconds", h["idle_seconds"], idle_s)
        out.append({"finding_id": fid, "intervals": len(ivs), "idle_seconds": idle_s,
                    "quantity_high": str(h["quantity_high"])})
    return {"findings": len(out), "per_finding": out}


def _site_codes(items, key: str) -> list[str]:
    return sorted(str(x.get(key)) for x in items or ())


def kis6(summary: dict, chain: dict, portfolio: dict, board_s: dict, kisiwa_doc: dict, s_day: date) -> dict:
    """KIS-6 (DIESEL-1-R3q §9q.2): on the week `[S-6d, S+1d)`: four Sites from data (summary, estate chain and the
    Portfolio objectives); Kisiwa's summary cells are its S board (`window_basis` DAY from the Site-local midnight);
    the Assure line: Kisiwa's verified threads are 1 iff `kisiwa.json`'s verdict is VERIFIED (never forced), the
    Assure card claim equals the chain `count.verified_results`, and no Assure value line names Kisiwa (H2)."""
    from zoneinfo import ZoneInfo

    s = next((x for x in summary.get("sites") or () if x.get("site_code") == KIS_SITE), None)
    if s is None:
        raise KisiwaMissing()
    codes = {"summary": _site_codes(summary.get("sites"), "site_code"), "chain": _site_codes(chain.get("sites"), "code"),
             "objectives": sorted({str(o.get("site_code")) for o in portfolio.get("objectives") or ()})}
    for name, got in codes.items():
        assert got == list(KIS_FOUR), (f"{name} Sites", got)
    cells = {r["category"]: r.get("state") for r in s.get("rows") or ()}
    board = {r["category"]: r.get("state") for r in board_s.get("rows") or ()}
    assert cells == board, ("Kisiwa summary cells are not its S board", cells, board)
    start = site_day_start(s_day, ZoneInfo(KIS_ZONE)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert s.get("window_basis") == "DAY" and (s.get("window") or {}).get("from") == start, (
        "Kisiwa summary window", s.get("window_basis"), s.get("window"), start)
    verdict_state = (kisiwa_doc.get("verdict") or {}).get("state")  # R3u U5: `kisiwa.json` verdict is a dict
    want = 1 if verdict_state == "VERIFIED" else 0
    c = next(x for x in chain["sites"] if x.get("code") == KIS_SITE)
    verified = (c.get("threads") or {}).get("verified")
    assert verified == want, ("Kisiwa verified threads", verified, "verdict", verdict_state)
    card = ((summary.get("cards") or {}).get("ASSURE_PERFORMANCE") or {})
    card_value = (card.get("claim") or {}).get("value")
    count = ((chain.get("counts") or {}).get("count.verified_results") or {}).get("value")
    assert card_value is not None and card_value == count, ("Assure card claim against the chain count", card_value,
                                                            count)
    name = s.get("site_name") or KIS_SITE
    assure = next((r for r in s.get("rows") or () if r.get("category") == "ASSURE_PERFORMANCE"), None) or {}
    lines = [x for x in card.get("value_lines") or () if str(x).startswith(f"{name}:") or KIS_SITE in str(x)]
    assert not (assure.get("nodes") or {}).get("verified_values") and not lines, ("H2: a Kisiwa Assure value line",
                                                                                  lines)
    return {"sites": codes, "kisiwa_cells": cells, "verdict": verdict_state, "want_verified": want,
            "assure_card": card_value, "chain_verified_results": count}


def _optimize_priced(summary: dict) -> list[tuple[str, dict]]:
    out = []
    for s in summary.get("sites") or ():
        row = next((r for r in s.get("rows") or () if r.get("category") == "OPTIMIZE_COST"), None) or {}
        claim = (row.get("nodes") or {}).get("earnings")
        if claim is not None and claim.get("value") is not None:
            out.append((s.get("site_code"), claim))
    return out


KIS7_ITEM3_REPORT_ONLY = False  # R3u U8: True restores the R3s2 report-only form (K10 held)


def _kis7_d1_equal(money: dict, lead: dict) -> bool:
    """R3t4 §9t4: the board shows two places, so compare through the product's `money2` (half-even), never strict
    Decimal: high always, low when present; currencies equal."""
    from assetops_backend.chain.vocabulary import money2

    if money.get("currency") != lead.get("currency"):
        return False
    pairs = [(money["amount_high"], lead["amount_high"])]
    if money.get("amount_low") is not None and lead.get("amount_low") is not None:
        pairs.append((money["amount_low"], lead["amount_low"]))
    return all(money2(a) == money2(b) for a, b in pairs)


def kis7(summary_s: dict, bodies: list[object], heads: list[dict], s_day: date, board_at,
         item3_report_only: bool | None = None) -> dict:
    """KIS-7 (DIESEL-1-R3s §9s.3, replaces R3q §9q.2 KIS-7): expectations derived from stored rows, never typed.
    `heads`: each Kisiwa dispatch Finding's latest revision episode (`episode_start`, `episode_end` or None, aware
    datetimes) with its latest money head (`state`, `amount_high`, `finding_id`); `board_at(date_iso)`: the Kisiwa
    outcome board body. 1. The S summary's Optimize card is `optimize_card(..., KOBO, allowed=(KOBO, KISIWA))`.
    2. Kisiwa is priced on S iff some PRICED head's episode overlaps Kisiwa's S local day. 3. On the Kisiwa date of
    the earliest PRICED head's episode start (d1) the board's Optimize earnings has a value equal to the stored
    `amount_high` of that day's lead head (greatest episode start, smallest Finding id: `lead_finding`).
    4. `never_summed` over `bodies` for every summary with two or more priced Sites, else reported as not reached."""
    from zoneinfo import ZoneInfo

    from assetops_backend.chain.outcomes import earnings_money

    if not any(x.get("site_code") == KIS_SITE for x in summary_s.get("sites") or ()):
        raise KisiwaMissing()
    zone = ZoneInfo(KIS_ZONE)
    card = optimize_card(summary_s, "KOBO-001", allowed=("KOBO-001", KIS_SITE))

    def overlapping(day: date) -> list[dict]:
        lo, hi = site_day_start(day, zone), site_day_start(day + timedelta(days=1), zone)
        return [h for h in heads if h["episode_start"] < hi and (h.get("episode_end") is None or h["episode_end"] > lo)]

    priced_heads = [h for h in heads if h.get("state") == "PRICED"]
    expected_s = any(h in priced_heads for h in overlapping(s_day))
    codes = [c for c, _ in _optimize_priced(summary_s)]
    assert (KIS_SITE in codes) == expected_s, ("S: Kisiwa priced on S does not match its stored heads", codes,
                                              "expected priced on S:", expected_s)
    assert priced_heads, ("no PRICED Kisiwa head to price a board day from", len(heads))
    first = min(priced_heads, key=lambda h: (h["episode_start"], str(h["finding_id"])))
    d1 = first["episode_start"].astimezone(zone).date()
    board = board_at(d1.isoformat())
    row = next((r for r in board.get("rows") or () if r.get("category") == "OPTIMIZE_COST"), None) or {}
    money = earnings_money((row.get("nodes") or {}).get("earnings"))
    # Item 3 (d1 priced) asserts again (DIESEL-1-R3u U8): K10 settles d1. The R3s2 report-only form (Kisiwa has no
    # `productive_kwh` subject, so d1 earnings read "Not known yet") stays reachable with `item3_report_only=True`
    # (module `KIS7_ITEM3_REPORT_ONLY`), for a run where K10 is held.
    report_only = KIS7_ITEM3_REPORT_ONLY if item3_report_only is None else item3_report_only
    d1_report = None
    day_heads = overlapping(d1)
    latest = max(h["episode_start"] for h in day_heads)
    lead = min((h for h in day_heads if h["episode_start"] == latest), key=lambda h: str(h["finding_id"]))
    if money is None:
        d1_report = ("d1 is unsettled: no `productive_kwh` subject (R3s2)", "board earnings unpriced", d1.isoformat())
    elif lead.get("state") != "PRICED":
        d1_report = ("d1: the lead head is not PRICED", lead.get("state"), d1.isoformat())
    elif not _kis7_d1_equal(money, lead):
        d1_report = ("d1: board amount differs from the stored head", d1.isoformat(), money["amount_high"],
                     lead["amount_high"])
    if d1_report and not report_only:
        raise AssertionError(("KIS-7 item 3 (R3u)",) + d1_report)
    sums, reached = 0, 0
    for body in [summary_s] + [b for b in bodies if isinstance(b, dict) and "sites" in b]:
        got = _optimize_priced(body)
        if len(got) >= 2:
            reached += 1
            sums += never_summed([str(earnings_money(c)["amount_high"]) for _, c in got], bodies)
    return {"optimize_card": card, "kisiwa_priced_on_s": KIS_SITE in codes, "priced_on_s": codes, "d1": d1.isoformat(),
            "d1_amount_high": None if money is None else str(money["amount_high"]),
            "d1_priced": (("REPORT-ONLY (R3s2): " if report_only else "") + "; ".join(map(str, d1_report))
                          if d1_report else ("REPORT-ONLY (R3s2): " if report_only else "") + "priced and equal"),
            "sums_checked": sums,
            "multi_site_bodies": reached or "no summary prices two Sites on real data (>=2 path not reached; L0 covers it)",
            "bodies": len(bodies)}


def kis_ov(reads: list[dict], basis_rows: list[dict], board_states: dict, report: dict | None,
           s5d_board: dict | None = None, second_read=None) -> dict:
    """KIS-OV (DIESEL-1-R3r §9r.2, extended by R3s §9s.2): the Kisiwa Overview answers 200 on each read day (`reads`:
    label, status, code, body); exactly one `site_cutover_basis` row is `NO_LEGACY_EVIDENCE` for the Site's own import
    row and digest (`basis_rows`); the newest Kisiwa Performance report (`report`: `outcome`, `empty_set`) is PASSED and
    empty-set; and the S-5d and S boards (`board_states`: label -> `read_state`) read AVAILABLE."""
    for r in reads:
        assert r.get("status") == 200 and isinstance(r.get("body"), dict) and r["body"], (
            "Kisiwa Overview not served", r.get("label"), r.get("status"), r.get("code"))
    assert len(basis_rows) == 1, ("expected exactly one Kisiwa cutover basis row", basis_rows)
    b = basis_rows[0]
    assert b.get("basis") == "NO_LEGACY_EVIDENCE" and b.get("same_import") is True and b.get("same_sha") is True, (
        "Kisiwa cutover basis is not the no-legacy basis of its own import", b)
    assert report is not None, "no Kisiwa Performance comparison report"
    assert report.get("outcome") == "PASSED" and report.get("empty_set") is True, (
        "Kisiwa Performance report is not a PASSED empty-set report", report.get("outcome"), report.get("empty_set"))
    assert set(board_states) == {"S-5d", "S"} and all(v == "AVAILABLE" for v in board_states.values()), (
        "a Kisiwa board does not read AVAILABLE", board_states)
    protect_state = None
    if s5d_board is not None:
        # R3u U7 pin: the S-5d Protect row is NEEDS_ATTENTION and MG-8 is {NEEDS_ATTENTION, PRIMARY_FINDING_OPEN};
        # the lead is not asserted (K10 may settle MG-5/MG-4)
        protect = next((r for r in s5d_board.get("rows") or () if r.get("category") == "PROTECT_ASSET"), None) or {}
        mg8 = next((o for o in protect.get("outcomes") or () if o.get("key") == "MG-8"), None) or {}
        if not (protect.get("state") == "NEEDS_ATTENTION" and mg8.get("state") == "NEEDS_ATTENTION"
                and mg8.get("reason") == "PRIMARY_FINDING_OPEN"):
            second = None
            if callable(second_read):
                try:  # an error from the diagnostic read never replaces the R3u-s1 message
                    second = second_read()
                except Exception as exc:  # noqa: BLE001
                    second = {"second_read_error": f"{type(exc).__name__}: {exc}"}
            raise AssertionError(("R3u-s1: the S-5d Protect row / MG-8 is not NEEDS_ATTENTION / PRIMARY_FINDING_OPEN",
                                  {"protect_state": protect.get("state"), "mg8": mg8,
                                   "read_state": s5d_board.get("read_state"), "warnings": s5d_board.get("warnings"),
                                   "second_read": second}))
        protect_state = protect["state"]
    return {"overview_status": {r["label"]: r["status"] for r in reads}, "basis": b["basis"],
            "performance_report": {"outcome": report["outcome"], "empty_set": report["empty_set"]},
            "board_read_state": board_states, "s5d_protect": protect_state}


# ---- OWN-G2 (build sheet OWN-GAPS §2.5, R2-G2 Q9): the automatic diesel-night check ------------------------------------

def last_json_object(stdout: str) -> dict | None:
    """The last stdout line that parses as a JSON object (R2-G2 Q9 c), or None when no line does."""
    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return None


def study_ending(found: list[dict], last_day: str) -> dict:
    """WK-6 (OWN-GAPS R6.2): the one opportunity whose study ends on `last_day`; later rolling studies are ignored."""
    hits = [o for o in found if o.get("last_day") == last_day]
    assert len(hits) == 1, ("expected exactly one study ending", last_day, sorted(o.get("last_day") for o in found))
    return hits[0]


def fuel_night_entry(report: dict | None, site: str = KIS_SITE) -> dict | None:
    """The `fuel_night` stage entry for `site` in a tick report, or None when the tick did not visit it (absent,
    `SKIPPED_CLAIMED`, or retry back-off all leave no stage entry)."""
    for s in (report or {}).get("sites") or ():
        if s.get("site_code") == site and isinstance((s.get("stages") or {}).get("fuel_night"), dict):
            return s["stages"]["fuel_night"]
    return None


def kis11(report: dict | None, story_revisions: dict, fuel_findings: int, kobo_windows: int) -> dict:
    """KIS-11 (OWN-GAPS §2.5): the last tick visited KISIWA-001's `fuel_night` stage with code OK and `eligible: true`;
    every story night's latest window is revision 1 (`story_revisions`: night -> revision); Kisiwa holds exactly one
    fuel Finding; KOBO-001 has no `fuel_balance_window` row."""
    entry = fuel_night_entry(report)
    assert entry is not None, "KISIWA-001 was not visited by the last tick"
    assert entry.get("code") == "OK" and entry.get("eligible") is True, (
        "KISIWA-001's fuel_night stage is not OK and eligible", {k: entry.get(k) for k in ("code", "eligible", "error")})
    assert story_revisions, "no Kisiwa story night has a window"
    moved = {str(n): r for n, r in story_revisions.items() if r != 1}
    assert not moved, ("a story night's latest window is not revision 1", moved)
    assert fuel_findings == 1, ("want exactly one Kisiwa fuel Finding", fuel_findings)
    assert kobo_windows == 0, ("KOBO-001 has fuel_balance_window rows", kobo_windows)
    return {"fuel_night": {k: entry.get(k) for k in ("code", "eligible", "processed", "deferred")},
            "story_nights": len(story_revisions), "fuel_findings": fuel_findings, "kobo_windows": kobo_windows}
