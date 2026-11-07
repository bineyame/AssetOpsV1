"""DD-1b2b step 7 (DD1b2-R8 A): the reads after the prepare. Reads only; none of it is a `CHECKS` row.

    python <tree>/tools/demo_combined_after.py <db url> <work> [--s2] [--ref <dd1b2 after.json>]  (tree form, R9 section 3)

DD1b2-R13 (B2): run with `ASSETOPS_RESPONSE_STORE=compose` so the GETs store nothing. `--s2` adds S+2 (clone half of
O8; `--ref` is the rehearsal build's after.json, against which Assure must be unchanged). It also carries O12, the
Kobo "Why?" price line, the Cold Protect "Why?", the ACT-002/003 labels, L4's action-index reads and O16's fuel-row
asserts. Each assert is recorded under `asserts`; the exit code is non-zero if any fails.

O8 (H1 measurements: renewable selections, studies, mill thread, boards, Portfolio counts), O14 (unused solar), O15
(generator energy per steady-before night; litres are NOT stored on this Site, see `litre_note`). Writes
`<work>/after.json` and prints it. Never ticks and never writes to the database."""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import demo_combined_rows as demo_rows

KOBO = "KOBO-001"
PRE, POST = (-13, -12, -11), (-8, -6, -5)  # O14's days
RENEWABLE_SQL = ("SELECT count(DISTINCT s.window_start) FROM mini_depth_selection s JOIN site st ON "
                 "st.tenant_id = s.tenant_id AND st.id = s.site_id WHERE st.site_code = %s AND s.domain = 'renewable' "
                 "AND s.window_start >= %s AND s.window_start < %s")
STUDY_SQL = ("SELECT o.id, o.first_day, o.last_day, CAST(r.result->>'eligible_days' AS int), r.result->>'status', "
             "o.public_no FROM mini_opportunity o JOIN site s ON s.tenant_id = o.tenant_id AND s.id = o.site_id "
             "JOIN LATERAL (SELECT result FROM mini_opportunity_revision x WHERE x.tenant_id = o.tenant_id AND "
             "x.site_id = o.site_id AND x.opportunity_id = o.id ORDER BY x.revision_no DESC LIMIT 1) r ON true "
             "WHERE s.site_code = %s ORDER BY o.last_day")
SERIES_SQL = ("SELECT x.device_id, x.signal_id, x.source_time, x.normalized_value_text FROM accepted_evidence x "
              "JOIN site s ON s.id = x.site_id WHERE s.site_code = %s AND x.source_time >= %s AND x.source_time < %s")


def connect(url: str):
    import psycopg

    return psycopg.connect(url.replace("+psycopg", ""))


def local_day(ts: datetime) -> date:
    return (ts.astimezone(timezone.utc) + timedelta(hours=3)).date()  # Kobo is Africa/Nairobi, no DST


def kwh_per_local_day(rows: list[tuple], pick) -> dict[str, Decimal]:
    """Sum 5-minute kW readings x 5/60 per Site-local day for the (device, signal) pairs `pick` accepts. Readings are
    deduplicated on (device, signal, source_time); a non-numeric value is skipped (dd1a2_mill3_dry_run.py:49-52)."""
    seen: set = set()
    out: dict[str, Decimal] = {}
    for device, signal, ts, value in rows:
        if not pick(device, signal) or (device, signal, ts) in seen:
            continue
        try:
            kw = Decimal(str(value))
        except Exception:  # noqa: BLE001
            continue
        seen.add((device, signal, ts))
        key = local_day(ts).isoformat()
        out[key] = out.get(key, Decimal(0)) + kw * Decimal(5) / Decimal(60)
    return out


def unused_solar(available: dict[str, Decimal], delivered: dict[str, Decimal], mill: dict[str, Decimal],
                 days: list[str]) -> dict:
    """O14: unused = available - delivered; the group means over `days`."""
    per = {d: {"available": float(available.get(d, 0)), "delivered": float(delivered.get(d, 0)),
               "unused": float(available.get(d, 0) - delivered.get(d, 0)), "mill": float(mill.get(d, 0))} for d in days}
    mean = {k: round(sum(v[k] for v in per.values()) / max(len(per), 1), 1) for k in ("available", "delivered", "unused", "mill")}
    return {"days": per, "mean": mean}


def quotable(pre_unused: float, post_unused: float) -> bool:
    """O14: "about 96 / about 22" may be quoted only if unused reads 96.4 and 22.4 (+-0.5)."""
    return abs(pre_unused - 96.4) <= 0.5 and abs(post_unused - 22.4) <= 0.5


# ---- DD1b2-R13 asserts: the pure parts (each raises AssertionError; main records pass/fail and exits non-zero) ---------

STEADY_KINDS = ("steady", "steady-before", "steady-before-first")
PRICE_LINE = re.compile(r"^(\S+) kWh × (\S+) ([A-Z]{3})/kWh$")
SPARE_SOLAR = re.compile(r"^Spare solar on (\d+) of (\d+) well-observed")
BAD_THREAD_STATES = ("WITHDRAWN", "CLOSED")


def o12_grow_nodes(grow: dict) -> dict:
    """O12: the Kobo Grow row's potential text and every contributor text. Pass: the potential reads "No potential
    found yet" and a contributor shows spare solar seen ("Spare solar on e of a well-observed ...", e >= 1)."""
    potential = demo_rows.nodes_potential_text(grow)
    texts = [str(c.get("text")) for c in grow.get("contributors", [])]
    assert demo_rows.NO_POTENTIAL in potential, ("potential", potential)
    seen = [m for m in (SPARE_SOLAR.match(t) for t in texts) if m and int(m.group(1)) >= 1]
    assert seen, ("no contributor shows spare solar seen", texts)
    return {"potential": potential, "contributors": texts}


def o12_s5_grow(grow: dict, thread_label: str | None) -> dict:
    """DD1b2-R14 section 1: on S-5 (the thread recurs) the potential starts "Not judged yet" with no kW figure and no
    money; a contributor shows spare solar seen. The thread's state label is report-only."""
    potential = demo_rows.nodes_potential_text(grow)
    node = (grow.get("nodes") or {}).get("potential")
    assert potential.startswith("Not judged yet"), ("potential", potential)
    assert not re.search(r"\bkW\b", potential), ("kW figure in the potential", potential)
    chip = grow.get("potential")
    assert not (isinstance(node, dict) and node.get("money")) and not (isinstance(chip, dict) and chip.get("money")), (
        "money on the potential", node, chip)
    texts = [str(c.get("text")) for c in grow.get("contributors", [])]
    assert any((m := SPARE_SOLAR.match(t)) and int(m.group(1)) >= 1 for t in texts), ("no spare solar seen", texts)
    return {"potential": potential, "thread_state_label": thread_label, "contributors": texts}


def why_price_line(comes_from: list[str], money: dict | None, price: Decimal, currency: str) -> dict:
    """F-THREADS "Why?" price line: any price shown equals the stored selection price; any money shown equals
    kWh x price at 2 dp. No price line and no money is recorded as LIMITED; money without a price line fails."""
    parsed = [m for m in (PRICE_LINE.match(str(t)) for t in comes_from) if m]
    amounts = {Decimal(str(money[k])) for k in ("amount_low", "amount_high", "amount") if money and money.get(k) is not None}
    if not parsed:
        assert not amounts, ("money shown with no price line", sorted(amounts), comes_from)
        return {"state": "LIMITED", "price_line": None, "money": None, "comes_from": comes_from}
    for m in parsed:
        kwh, shown, cur = Decimal(m.group(1)), Decimal(m.group(2)), m.group(3)
        assert shown == price and cur == currency, ("price shown", m.group(0), "stored", str(price), currency)
        want = (kwh * price).quantize(Decimal("0.01"))
        assert all(a.quantize(Decimal("0.01")) == want for a in amounts), ("money", sorted(amounts), "want", str(want))
    return {"state": "PRICED", "price_line": [m.group(0) for m in parsed], "money": sorted(map(str, amounts))}


def protect_names_threads(nodes: list[dict], required: str, other: list[str]) -> dict:
    """DD1b2-R14 section 2: the Cold Protect "Why?" must name ACT-000002's thread (`required`). A missing other thread
    is recorded as the BL-50 known gap, not a failure."""
    named = {str(i) for n in nodes if n.get("kind") == "thread" for i in n.get("ids", [])}
    assert str(required) in named, ("the Protect Why? does not name ACT-000002's thread", required, sorted(named))
    return {"required": required, "named": sorted(named),
            "other_threads": {t: ("named" if str(t) in named else "BL-50 known gap: not named") for t in other}}


def action_agreed(thread_states: dict[str, list[str]]) -> dict:
    """ACT-002/003: each domain Site (Cold with ACT-000002, EV with ACT-000003) has a thread reading "Action agreed"."""
    for site, labels in thread_states.items():
        assert "Action agreed" in labels, (site, labels)
    return thread_states


def fuel_rows_ok(rows_: list[tuple], kind_by_day: dict[str, str], offset_by_day: dict[str, int]) -> dict:
    """O16: `rows_` are (window_start, state, quantity_low, quantity_high). Each fuel row's Site-local day is a story
    day of days.json and is not a steady or steady-before day; S-14 and S-7 are PRICED with quantity 0."""
    by_offset: dict[int, list[tuple]] = {}
    for w0, state, lo, hi in rows_:
        d = local_day(w0).isoformat()
        assert d in kind_by_day, ("fuel row on a day that is not a story day", d)
        assert kind_by_day[d] not in STEADY_KINDS, ("fuel row on a steady day", d, kind_by_day[d])
        by_offset.setdefault(offset_by_day[d], []).append((state, lo, hi))
    for off in (-14, -7):
        got = by_offset.get(off)
        assert got, ("no fuel row on", f"S{off}")
        assert all(s == "PRICED" and Decimal(str(lo)) == 0 and Decimal(str(hi)) == 0 for s, lo, hi in got), (off, got)
    return {"rows": len(rows_), "by_offset": {f"S{k:+d}": len(v) for k, v in sorted(by_offset.items())}}


def action_index_ok(rows_: list, action_code: str, label: str) -> int:
    """L4: the Site's `domain_action_index` read holds at least one row, and it is the Site's Action."""
    assert len(rows_) >= 1, (label, "no rows")
    assert action_code in json.dumps(rows_, default=str), (label, action_code, "not in the rows")
    return len(rows_)


def recurrence_holds(events: list[tuple], s_plus_2: str, recurred_day: str = "2026-10-31") -> dict:
    """O8 clone half: still "Recurs" (one RECURRED, effective S-5 from OPP-000002), no WITHDRAWN or CLOSED, and no
    RECURRED effective on S+2."""
    states = [e[0] for e in events]
    bad = [s for s in states if s in BAD_THREAD_STATES]
    assert not bad, ("thread states", bad)
    recurred = [str(e[1]) for e in events if e[0] == "RECURRED"]
    assert recurred == [recurred_day], ("RECURRED events", recurred, "want", [recurred_day])
    assert s_plus_2 not in recurred, ("RECURRED effective on S+2", recurred)
    return {"events": events}


def known_at_links(bodies: list) -> list[str]:
    """Report only: every link or text in the given bodies that carries an explicit `known_at`."""
    out: set[str] = set()

    def visit(node: object) -> None:
        if isinstance(node, dict):
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)
        elif isinstance(node, str) and "known_at=" in node:
            out.add(node)

    for b in bodies:
        visit(b)
    return sorted(out)


def site_links(body: object, codes: tuple[str, ...]) -> list[str]:
    """Report only: the paths in a Portfolio body that name a domain Site (where Cold and EV open from Portfolio)."""
    out: set[str] = set()

    def visit(node: object) -> None:
        if isinstance(node, dict):
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)
        elif isinstance(node, str) and node.startswith("/") and any(c in node for c in codes):
            out.add(node)

    visit(body)
    return sorted(out)


PORTFOLIO_LANDING = ("Portfolio opens Cold and EV at the Site pages through the Portfolio links listed in "
                     "`portfolio_site_links` (DS-1 opens Cold and EV from the story-day links, DD1b2-R9 section 1)")


def main(url: str, work: Path, s2: bool = False, ref: Path | None = None) -> int:
    import demo_combined_finish as fin  # needs the backend on the path; imported here so the pure parts test alone

    ctx = fin.load(work, fin.app_client(url, work))
    ctx.url = url
    S = ctx.S
    day = lambda n: (S + timedelta(days=n)).date().isoformat()  # noqa: E731
    doc: dict = {"S": S.isoformat(), "s2_mode": s2, "asserts": {}}
    failed: list[str] = []

    def check(name: str, fn, *args):
        try:
            doc["asserts"][name] = {"status": "pass", "read": fn(*args)}
        except Exception as exc:  # recorded per assert; the exit code is non-zero after all ran
            doc["asserts"][name] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"[:1500]}
            failed.append(name)

    sel_days = (-3, -1, 0, 1, 2) if s2 else (-3, -1, 0, 1)
    with connect(url) as c:
        # ---- O8 (1): renewable selections per day; (2): every stored study
        doc["o8_renewable_selections"] = {f"S{n:+d} {day(n)}": c.execute(
            RENEWABLE_SQL, (KOBO, S + timedelta(days=n), S + timedelta(days=n + 1))).fetchone()[0] for n in sel_days}
        studies = c.execute(STUDY_SQL, (KOBO,)).fetchall()
        doc["o8_studies"] = [{"public_no": s[5], "first_day": str(s[1]), "last_day": str(s[2]), "eligible_days": s[3],
                              "status": s[4]} for s in studies]
        # ---- O14 / O15 from accepted_evidence
        lo, hi = S + timedelta(days=-20), S + timedelta(days=-3)
        rows = c.execute(SERIES_SQL, (KOBO, lo, hi)).fetchall()
        pairs = sorted({(r[0], r[1]) for r in rows})
        doc["evidence_pairs"] = [list(p) for p in pairs]
        avail = kwh_per_local_day(rows, lambda d, s: (d, s) == ("pv-inverter-controller", "available-power"))
        deliv = kwh_per_local_day(rows, lambda d, s: (d, s) == ("pv-inverter-controller", "ac-power"))
        mill = kwh_per_local_day(rows, lambda d, s: "mill" in d and s in ("ac-power", "active-power", "power"))
        pre = unused_solar(avail, deliv, mill, [day(n) for n in PRE])
        post = unused_solar(avail, deliv, mill, [day(n) for n in POST])
        doc["o14"] = {"pre": pre, "post": post, "quote_96_22": quotable(pre["mean"]["unused"], post["mean"]["unused"])}
        gen = kwh_per_local_day(rows, lambda d, s: d == "generator-controller" and s == "ac-power")
        steady = [d["day"] for d in ctx.site_days("kobo") if d["kind"] in ("steady-before", "steady-before-first")]
        doc["o15"] = {"generator_kwh_by_local_day": {d: round(float(gen.get(d, 0)), 3) for d in steady},
                      "litre_note": "no fuel signal reaches evidence on this Site (0 fuel_level rows): litres are not "
                                    "stored and are NOT recomputed here; the stored measure is generator kWh"}
    # ---- O8 (3): the mill thread's events; (4): boards; (5): Portfolio counts; (6) is F-COH's allowed_coh17
    thread = fin._mill_thread(ctx)
    doc["o8_mill_thread_events"] = [(e.get("state"), e.get("effective_day") or e.get("day")) for e in
                                    (thread or {}).get("events", [])]
    boards = {}
    for n in ((-5, -1, 0, 1, 2) if s2 else (-5, -1, 0, 1)):
        body = ctx.board(KOBO, S + timedelta(days=n), S + timedelta(days=n + 1))
        by = fin.rows(body)
        boards[f"S{n:+d}"] = {k: {"state": by[k]["state"], "headline": by[k].get("headline")}
                              for k in ("GROW_REVENUE", "ASSURE_PERFORMANCE") if k in by}
    doc["o8_boards"] = boards
    pf, windows = {}, [("week", -6, 1), ("month", -29, 1)] + ([("week_s2", -4, 3), ("month_s2", -27, 3)] if s2 else [])
    estate_week = None
    for name, a, b in windows:
        body, *_ = fin._estate(ctx, S + timedelta(days=a), S + timedelta(days=b))
        pf[name] = body.get("summary")
        estate_week = body if name == "week" else estate_week
    doc["o8_portfolio"] = pf

    def portfolio_grow_open() -> dict:
        out = {}
        for name, summary in pf.items():
            grow = ((summary or {}).get("category_counts") or {}).get("GROW_REVENUE") or {}
            assert grow.get("open_findings", 0) >= 1, (name, "Portfolio Grow does not count the mill thread open", grow)
            out[name] = grow
        return out

    check("portfolio_grow_counts_mill_thread_open", portfolio_grow_open)

    # ---- O8 clone half (S+2 mode): the study ending S+2, the thread, Assure unchanged
    if s2:
        def s2_study() -> dict:
            got = [s for s in doc["o8_studies"] if s["last_day"] == day(2)]
            assert got, ("no study ends on S+2", day(2), doc["o8_studies"])
            return got[0]

        check("o8_study_ending_s_plus_2", s2_study)
        check("o8_recurs_unchanged", recurrence_holds, doc["o8_mill_thread_events"], day(2))

        def assure_unchanged() -> dict:
            assert ref and ref.is_file(), "no reference after.json (--ref) to compare Assure against"
            before = json.loads(ref.read_text(encoding="utf-8"))["o8_boards"]
            diff = {k: (before[k]["ASSURE_PERFORMANCE"], boards[k]["ASSURE_PERFORMANCE"]) for k in before
                    if before[k].get("ASSURE_PERFORMANCE") != boards.get(k, {}).get("ASSURE_PERFORMANCE")}
            assert not diff, ("Assure changed against the reference", diff)
            return {"compared": sorted(before), "s_plus_2": boards["S+2"].get("ASSURE_PERFORMANCE")}

        check("o8_assure_unchanged", assure_unchanged)

    # ---- O12: the Kobo Grow row's potential and contributors on S-8 and S-5
    grow8 = fin.rows(ctx.board(KOBO, S + timedelta(days=-8), S + timedelta(days=-7)))["GROW_REVENUE"]
    check("o12_grow_nodes_S-8", o12_grow_nodes, grow8)
    grow5 = fin.rows(ctx.board(KOBO, S + timedelta(days=-5), S + timedelta(days=-4)))["GROW_REVENUE"]
    chain5 = ctx.get(f"/api/sites/{KOBO}/chain", date=day(-5))
    label5 = next((t.get("state_label") for t in chain5.get("threads", []) if t.get("mechanism") == demo_rows.HEADROOM),
                  None)
    check("o12_grow_nodes_S-5", o12_s5_grow, grow5, label5)

    # ---- F-THREADS: the Kobo Grow "Why?" price line on the pinned mill study day S-11
    def kobo_why_price() -> dict:
        mill_last = fin._mill(ctx)["study"]["last_day"]
        valid_at = fin.iso(fin.demo_rows.site_day_start(datetime.fromisoformat(mill_last).date(), fin._kobo_zone(ctx))
                           + timedelta(hours=12))
        sel = ctx.get(f"/api/sites/{KOBO}/financial-assumptions", key="productive_use_price_per_kwh", limit=1,
                      valid_at=valid_at).get("selection") or {}
        assert sel.get("state") == "PRICED", (valid_at, sel)
        price = Decimal(str(sel["price"]["value"]))
        assert price == Decimal("0.25"), ("stored selection price", str(price))
        why = ctx.get(f"/api/sites/{KOBO}/chain/why", date=day(-11), category="GROW_REVENUE")
        grow = fin.rows(ctx.board(KOBO, S + timedelta(days=-11), S + timedelta(days=-10)))["GROW_REVENUE"]
        return why_price_line((why.get("text") or {}).get("comes_from") or [], grow.get("headline_money"), price,
                              sel["price"]["currency"])

    check("kobo_why_price_line_S-11", kobo_why_price)

    # ---- F-THREADS: the Cold Protect "Why?" names both Cold threads, over the window holding Cold's story days
    from zoneinfo import ZoneInfo

    def zone(code: str) -> ZoneInfo:
        site = ctx.get(f"/api/sites/{code}")
        return ZoneInfo(next(n["timezone"] for n in fin.walk(site) if isinstance(n.get("timezone"), str)))

    def cold_protect_why() -> dict:
        # DD1b2-R14: on S's Site-local day the Protect Why? names the thread that holds ACT-000002; the other Cold
        # thread missing is the BL-50 known gap (recorded, not a failure)
        z = zone(fin.COLD)
        local = datetime.fromisoformat(ctx.site_day("cold", "failure")["day"]).date()
        win = {"from": fin.iso(fin.demo_rows.site_day_start(local, z)),
               "to": fin.iso(fin.demo_rows.site_day_start(local + timedelta(days=1), z))}
        chain = ctx.get(f"/api/sites/{fin.COLD}/chain", **win)
        required = next(str(a["thread"]) for a in chain.get("actions", []) if str(a.get("code")) == "ACT-000002")
        other = [str(t["id"]) for t in chain.get("threads", []) if str(t["id"]) != required]
        why = ctx.get(f"/api/sites/{fin.COLD}/chain/why", category="PROTECT_ASSET", **win)
        return {**protect_names_threads(why.get("nodes", []), required, other),
                "why_text": (why.get("text") or {}).get("comes_from")}

    check("cold_protect_why_names_act_002_thread", cold_protect_why)

    # ---- F-THREADS: "Action agreed" on the ACT-002/003 threads, from the stored check.json (a file read)
    def act_agreed() -> dict:
        read = json.loads((work / "check.json").read_text(encoding="utf-8"))["rows"]["F-THREADS"]["read"]["cold_ev"]
        return action_agreed({site: v["thread_states"] for site, v in read.items()})

    check("action_agreed_act_002_003", act_agreed)

    # ---- L4: domain_action_index on the Site-local story day and on its week (Cold ACT-000002, EV ACT-000003)
    def action_index(code: str, kind: str, action: str) -> dict:
        d = ctx.site_day("cold" if code == fin.COLD else "ev", kind)
        z, local = zone(code), datetime.fromisoformat(d["day"]).date()
        out = {}
        for label, a, b in (("day", 0, 1), ("week", -6, 1)):
            lo = fin.demo_rows.site_day_start(local + timedelta(days=a), z)
            hi = fin.demo_rows.site_day_start(local + timedelta(days=b), z)
            r = ctx.client.get(f"/api/sites/{code}/domain-work/action-index", params={"from": fin.iso(lo), "to": fin.iso(hi)})
            assert r.status_code == 200, (code, label, r.status_code, r.text[:200])
            out[label] = action_index_ok(r.json().get("rows", []), action, f"{code} {label}")
        return out

    check("l4_action_index_cold", action_index, fin.COLD, "failure", "ACT-000002")
    check("l4_action_index_ev", action_index, fin.EV, "fault", "ACT-000003")

    # ---- O16: the stored fuel rows against days.json (the MONEY-B gate for E3.2)
    def fuel_rows() -> dict:
        kobo = [d for d in ctx.days if d["site"] == "kobo" and d.get("day")]
        with connect(url) as c2:
            got = c2.execute(
                "SELECT r.window_start, r.state, r.quantity_low, r.quantity_high FROM financial_consequence_revision r "
                "JOIN site s ON s.id = r.site_id WHERE s.site_code = %s", (KOBO,)).fetchall()
        return fuel_rows_ok(got, {d["day"]: d["kind"] for d in kobo}, {d["day"]: d["offset"] for d in kobo})

    check("o16_fuel_rows", fuel_rows)

    # ---- report only: links with an explicit known_at, and where Portfolio lands for Cold and EV
    def known_at() -> list[str]:
        bodies = []
        for d in ctx.days:
            if d.get("has_run", True) and d["kind"] != "missing":
                code = {"kobo": KOBO, "cold": fin.COLD, "ev": fin.EV}[d["site"]]
                bodies.append(ctx.board(code, fin.at(d["start"]), fin.at(d["end"])))
        return known_at_links(bodies)

    links = known_at()
    doc["known_at_links"] = {"count": len(links), "links": links[:40]}
    doc["portfolio_site_links"] = site_links(estate_week, (fin.COLD, fin.EV))
    doc["portfolio_landing"] = PORTFOLIO_LANDING

    doc["failed"] = failed
    (work / "after.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    print(json.dumps(doc, indent=2, default=str))
    return 1 if failed else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    s2_mode = "--s2" in args
    ref_path = Path(args[args.index("--ref") + 1]) if "--ref" in args else None
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--ref")]
    raise SystemExit(main(pos[0], Path(pos[1]), s2_mode, ref_path))
