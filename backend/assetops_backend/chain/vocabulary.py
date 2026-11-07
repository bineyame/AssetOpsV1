"""CH-4 (build sheet CH-4 §2.2): the server-rendered words of opportunity threads, the seed of the AG-29
vocabulary layer. Every client-facing literal of an opportunity item comes from here. Pure: no I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from typing import Any, Mapping, Sequence

from assetops_backend.mini_decisions.scenario_rules import decimal_text
from assetops_backend.outcomes.objectives import BEHIND_PACE, MISSED, ON_PACE, TOO_EARLY

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

OPP_TITLE = {"PRODUCTIVE_USE_HEADROOM": "Daytime solar unused at {site}"}
OPP_SHORT = {"PRODUCTIVE_USE_HEADROOM": "{site} daytime solar"}
SEEN_LINE = "Seen on {e} of {a} well-observed days · {span}"
VALUE_LINE = "{lo}–{hi} kW over {h} on every eligible day"
VALUE_LINE_ONE = "{lo} kW over {h} on every eligible day"
LIMIT_MIXED = "Limited evidence: readings come from mixed sources, so the size is not worked out yet"
LIMIT_DAYS = "Limited evidence: {n} of the 5 study days lack a reading needed to size it"
LIMIT_UNKNOWN = "Not judged yet: {n} of the 5 study days have no reading"
EVIDENCE_LABEL = {"SUPPORTED": "Supported", "LIMITED": "Limited evidence", "UNKNOWN": "Not judged yet"}
#: MA-1 M4 timeline words; CH-5a2 reuses them for Finding threads.
THREAD_STATE_WORDS = {"OPEN": "Open", "ACTION_IN_HAND": "Action agreed", "CHANGE_APPLIED": "Change made",
                      "RESOLVED_MONITORING": "Checked and working, monitoring", "CLOSED": "Closed",
                      "RECURRED": "Seen again", "REOPENED": "Reopened", "WITHDRAWN": "No longer seen"}
OPP_NONE = "No opportunity found in this period"
MIXED_SOURCE_CODES = ("SOURCE_CLASS_MIXED", "SOURCE_CLASS_UNKNOWN")


def day_text(d: date) -> str:
    """`%-d %b` without the platform's strftime: "1 Nov"."""
    return f"{d.day} {MONTHS[d.month - 1]}"


def span_text(first: date, last: date) -> str:
    """"27 Oct" for one day, "1–31 Oct" inside one month, "28 Oct–2 Nov" across months."""
    if first == last:
        return day_text(first)
    return f"{first.day}–{day_text(last)}" if first.month == last.month else f"{day_text(first)}–{day_text(last)}"


def seen_line(eligible: int, assessed: int, first: date, last: date) -> str:
    span = day_text(first) if first == last else f"{day_text(first)}–{day_text(last)}"
    return SEEN_LINE.format(e=eligible, a=assessed, span=span)


def value_line(status: str | None, headroom: Mapping[str, Any] | None, window_hours: int | None) -> str | None:
    """CH-9 §2: the headroom over the study's `window_hours` (the fewest eligible daylight hours on any eligible
    day); no line without both."""
    if status != "SUPPORTED" or not headroom or not window_hours:
        return None
    lo, hi = decimal_text(Decimal(str(headroom["low"]))), decimal_text(Decimal(str(headroom["high"])))
    h = daylight_hours_text(int(window_hours))
    return VALUE_LINE_ONE.format(lo=lo, h=h) if lo == hi else VALUE_LINE.format(lo=lo, hi=hi, h=h)


#: CH-9 (CH9-R3 Q2), MOCK DEVIATION candidate: v69 shows "kW at midday"; the headroom is over measured daylight hours.
HEADROOM_UNIT = "kW over {h}"
HEADROOM_UNIT_NONE = "kW over daylight hours"


def headroom_unit(window_hours: int | None) -> str:
    """CH6b2-R Q7c: the Portfolio opportunity unit (the browser's `opportunityHeadroomUnit` before CH-6b2)."""
    return HEADROOM_UNIT.format(h=daylight_hours_text(int(window_hours))) if window_hours else HEADROOM_UNIT_NONE


def daylight_hours_text(n: int) -> str:
    """"1 daylight hour", "12 daylight hours"."""
    return f"{n} daylight hour" if n == 1 else f"{n} daylight hours"


def limit_line(status: str | None, limitation_codes: Sequence[str], decisions: Sequence[str | None]) -> str | None:
    if status == "LIMITED":
        if any(c in MIXED_SOURCE_CODES for c in limitation_codes):
            return LIMIT_MIXED
        return LIMIT_DAYS.format(n=sum(1 for d in decisions if d in ("LIMITED", "CONFLICT")))
    if status == "UNKNOWN":
        return LIMIT_UNKNOWN.format(n=sum(1 for d in decisions if d is None))
    return None


# ---- PC-1 claims (build sheet CH-6 §S.2; CH-5a2b builds the type and the count claims, §B13 R3 / §B14) ----------

COMPLETE_BASIS, CHECKED_DAYS_BASIS, NOT_KNOWN_BASIS = "COMPLETE", "CHECKED_DAYS", "NOT_KNOWN"
CLAIM_DAY_KEYS = ("complete", "partial", "low", "no_data", "pending", "expected")
NOT_KNOWN_TEXT = "Not known yet"
#: §B13 R3 texts: (COMPLETE one, COMPLETE many, CHECKED_DAYS n >= 1, CHECKED_DAYS n = 0).
COUNT_TEXT = {
    "count.open_threads": ("{n} open finding", "{n} open findings", "{n} open on the days checked",
                           "None open on the days checked"),
    "count.verified_results": ("{n} fix confirmed", "{n} fixes confirmed", "{n} confirmed, from the days checked",
                               "None confirmed on the days checked"),
    "count.opportunities": ("{n} opportunity", "{n} opportunities", "{n} found on the days checked",
                            "None found on the days checked"),
    # MOCK DEVIATION MD-CH6-8: "{n} confirmed, from the days checked" (CH6b3-R3): no mock example of this form.
    # CH6b2-R Q2: Sites with a primary Protect thread OPEN, RECURRED or ACTION_IN_HAND (`chain/claims.py`); the
    # §B2 forms. MOCK DEVIATION MD-CH6-4: the CHECKED_DAYS forms have no mock example.
    "count.sites_disrupted": ("{n} site disrupted", "{n} sites disrupted", "{n} found on the days checked",
                              "None found on the days checked"),
}
#: CH6b2-R Q2: the COMPLETE zero form of a count, where it differs from "{n} ..." (the §B2 "No sites disrupted").
COUNT_ZERO = {"count.sites_disrupted": "No sites disrupted"}
#: B7 / R2: the source classes whose verified result is worded "on example data".
EXAMPLE_SOURCES = ("REGISTERED_SIMULATION", "AUTHORED_DEMONSTRATION")


def provenance_suffix(source_state: str | None) -> str:
    """B7 (DS-R1, COH-12): `" on example data"` for an example-data source class, else `""` (None included)."""
    return " on example data" if source_state in EXAMPLE_SOURCES else ""


@dataclass(frozen=True)
class Claim:
    key: str              # e.g. "count.open_threads", "money.estimated_income", "verdict.MG-1"
    value: Any            # int | Decimal string | verdict code | None
    basis: str            # "COMPLETE" | "CHECKED_DAYS" | "NOT_KNOWN"
    days: Mapping[str, int] | None   # {"complete", "partial", "low", "no_data", "pending", "expected"}
    text: str             # rendered once, here
    #: CH6b1-R4 SPAN: the Site-local `(first, last)` days this claim actually judged; None when it names no days.
    span: tuple[date, date] | None = None

    def to_json(self) -> dict[str, Any]:
        value = str(self.value) if isinstance(self.value, Decimal) else self.value
        out = {"key": self.key, "value": value, "basis": self.basis,
               "days": None if self.days is None else dict(self.days), "text": self.text}
        if self.span is not None:   # additive on the wire
            out["span"] = {"first": self.span[0].isoformat(), "last": self.span[1].isoformat()}
        return out


def _days_of(days: Any) -> Mapping[str, int] | None:
    if days is None:
        return None
    if isinstance(days, Mapping):
        return {k: int(days[k]) for k in CLAIM_DAY_KEYS}
    return {k: int(getattr(days, k)) for k in CLAIM_DAY_KEYS}


def count_basis(days: Any) -> str:
    """§S.2, the one basis rule: NOT_KNOWN when `days` is None, `expected == 0`, or every expected day is PENDING or
    NO_DATA; COMPLETE when `complete == expected`; else CHECKED_DAYS. `days` is a `GradeCounts` or its §S.2 subset."""
    d = _days_of(days)
    if d is None or d["expected"] == 0 or d["pending"] + d["no_data"] >= d["expected"]:
        return NOT_KNOWN_BASIS
    return COMPLETE_BASIS if d["complete"] == d["expected"] else CHECKED_DAYS_BASIS


def sum_days(per_site: Sequence[Any]) -> Mapping[str, int] | None:
    """The §S.2 subset summed over the Sites in scope; None when any Site's counts are None (the read failed)."""
    total = {k: 0 for k in CLAIM_DAY_KEYS}
    for days in per_site:
        d = _days_of(days)
        if d is None:
            return None
        for k in CLAIM_DAY_KEYS:
            total[k] += d[k]
    return total


def count_claim(key: str, value: int | None, days: Any) -> Claim:
    """A count claim (§B13 R3): a null value (the read failed) is NOT_KNOWN whatever the days."""
    d = _days_of(days)
    basis = NOT_KNOWN_BASIS if value is None else count_basis(d)
    one, many, checked, none = COUNT_TEXT[key]
    if basis == NOT_KNOWN_BASIS:
        text = NOT_KNOWN_TEXT
    elif basis == COMPLETE_BASIS:
        text = COUNT_ZERO[key] if value == 0 and key in COUNT_ZERO else (one if value == 1 else many).format(n=value)
    else:
        text = checked.format(n=value) if value else none
    return Claim(key, value, basis, d, text)


# ---- CH-5b2 "Why?" trace (build sheet CH-5b §2.3, CH5b2-R Q5-Q9) ------------------------------------------------
# Each template is a MOCK DEVIATION candidate against the MA-1 `WHY` sentences (frontend/mockups/v70/index.html:430);
# the review packet lists them mock -> new. The days lines follow the mock's `DAYS` wording (CH5b2-R Q6).

WHY_TEXT = {
    "why.title": "{site} · {category}",
    "why.from.measure": "{label} on {k} checked day{s}",
    "why.from.finding": "{title}, seen {n} time{s} since {first}",
    "why.from.action": "{code} · {label}",
    # CH6a3-R Q3: the price basis of a money claim.
    "why.from.price": "{kwh} kWh × {price} {cur}/kWh",
    "why.from.price_several": "{kwh} kWh at {n} declared prices over these days",
    "why.from.fuel_price": "{lo}–{hi} L × {price} {cur}/L",
    "why.from.fuel_price_one": "{lo} L × {price} {cur}/L",
    # MOCK DEVIATION (CH5b2-R Q7): the mock always has 2-4 lines; a trace with none says so.
    "why.from.none": "Nothing has been recorded for this yet",
    "why.change.days": "Checking {n} more day{s}",
    "why.change.action": "An agreed action",
    "why.change.verdict": "The check after the change",
    "why.change.readings": "New readings that differ",
    "why.evidence": "{site} evidence →",
    "why.days.many": "{c} of {e} day{s} checked",
    "why.days.partial": " · {p} partly checked",
    "why.days.low": " · {n} with too little data, not counted",
    # MOCK DEVIATION (CH5b2-R Q6): the mock has no pending case.
    "why.days.pending": " · {q} not in yet",
    "why.days.one.checked": "{d} checked",
    "why.days.one.partial": "{d} partly checked",
    "why.days.one.low": "{d}: too little data, not counted",
    "why.days.one.pending": "{d}: not in yet",
    # MOCK DEVIATION (CH5b2-R Q9): the estate chain carries no Portfolio headline per category, so the mock's `pf:`
    # sentences are replaced by this count.
    "why.estate.say": "{category} at {n} site{s}",
    "why.estate.from": "{site}: {say}",
    "why.estate.days": "{site}: {days}",
    # CH6b2-R Q2(b): the Protect card's "Why?" names each counted Site and its thread (mock `pf:protect` `from`).
    "why.from.disrupted": "{site}: {title}",
    # MOCK DEVIATION (CH6b2-R Q2b): a thread whose Finding has no board title is named by its state and first day.
    "why.from.disrupted_untitled": "{site}: {state}, since {first}",
    "why.from.warnings_apart": "Early warnings are counted separately and not priced",
}
#: CH5b2-R Q5: one plain label per measure (each a MOCK DEVIATION: MA-1 writes free sentences).
MEASURE_LABEL = {
    "avoidable_gen_min": "Generator time beyond need",
    "productive_kwh": "Energy for productive use",
    "daylight_headroom_kw": "Unused daytime solar",
    # CH5b2-R ruled "Critical load served"; guard V refuses "load" (productVocabulary.json "unexplained
    # abbreviations"), so the one word is swapped: Known Deviation KD-3 in the review packet, for the Architect.
    "critical_served": "Critical supply served",
    "chamber_temp_c": "Chamber temperature",
    "backup_start_chain": "Backup automatic start",
    "charging_kwh": "Energy delivered by charging",
}


def _s(n: int) -> str:
    return "" if n == 1 else "s"


def why(key: str, **fields: Any) -> str:
    """One §2.3 template, with `{s}` the plural suffix of the field named by the template's count."""
    return WHY_TEXT[key].format(**fields)


def why_days(days: Sequence[date], counts: Mapping[str, int], one: str | None) -> str:
    """CH5b2-R Q6: the days line. `counts` = {checked, partial, low, pending} over the expected days; `one` is the
    single day's class when the window is one day."""
    if len(days) == 1 and one is not None:
        return why(f"why.days.one.{one}", d=day_text(days[0]))
    c, p, n, q = (int(counts.get(k, 0)) for k in ("checked", "partial", "low", "pending"))
    e = c + p + n + q
    line = why("why.days.many", c=c, e=e, s=_s(e))
    if p:
        line += why("why.days.partial", p=p)
    if n:
        line += why("why.days.low", n=n)
    if q:
        line += why("why.days.pending", q=q)
    return line


# ---- CH-6a2 node claims (build sheet CH-6 §A4, R8, R11, R12; CH6a2-R) -------------------------------------------
# Each template is a MOCK DEVIATION candidate against MA-1 M3 unless equal (MD-CH6-2 lists them in the packet).

#: WALK1-3b §A2.2/§A2.5, moved unchanged from `site_outcomes/mini.py` (§A4 `verdict.*`; CH6a2-R Q3). `{c}` is the
#: COMPLETE-day count; `{e}` days have elapsed; `{k}` is the objective's checked-day minimum.
MG1_SO_FAR = "{mtd} kWh so far this month, on {c} of {e} days checked"
MG1_PACE = MG1_SO_FAR + " · averages {avg} kWh a day; the target needs {need} kWh a day"
MG1_TOO_EARLY = "{mtd} kWh so far this month, on {c} checked {d}; too early to judge (needs {k} checked days)"
MG1_MISSED = "{mtd} kWh this month, all {m} days checked"
#: `site_outcomes/mini.py:127` `MG1_ACTUAL`, the board's existing words for no checked day (CH6a2-R Q5).
MG1_NO_DAY = "sales not recorded"

NODE_TEXT = {
    "money.days": "{amount} over {k} of {m} days checked",
    "money.days_partial": "{amount} over {k} of {m} days checked · {p} partly checked",
    "money.income_suffix": " · not billed or collected",
    "money.not_known": NOT_KNOWN_TEXT,
    "money.currency_mixed": "Not shown · amounts in more than one currency",
    "potential.value": "{lo}–{hi} kW of daytime solar unused",
    "potential.money": "{lo}–{hi} {cur} per hour of use, at the declared price",
    "potential.none": "No potential found yet",
    "target.none": "No target set yet",
    "target.days_none": "No target, so no days are judged yet",
    "days_line.many": "{k} of {m} days checked",
    "days_line.partial": " · {p} partly checked",
    "days_line.low": " · {n} with too little data, not counted",
    "days_line.no_data_one": "No readings on {day}",
    # CH-6 R7 (design A3; MD-CH6-3: no mock place, it sits in the row subline).
    "row.target_note": "{k} of {m} outcomes have a target",
    # OWN-1104 R10 (replaced), CH6b1-R Q5: the Portfolio Grow income total and its per-Site lines (mock v70
    # `pfGrowParts`). MOCK DEVIATION MD-CH6-5: the mock's note says the Sites are not added together; OWN-1104 adds them.
    "income.total": "Estimated income from checked days: {total}",
    "income.at_least": "At least {total} estimated income, from checked days",
    "income.site": "{site}: {text}",
    "income.site_not_known": "{site}: not known yet",
}
#: §A4: the earnings labels whose money is an estimate at a declared price (MA-1 M3 suffix).
INCOME_LABELS = ("estimated_income", "estimated_charging_income")


def node_text(key: str, **fields: Any) -> str:
    """One §A4 template. CH6b2-R Q7a: "{k} of 1 days checked" reads "{k} of 1 day checked" (`m == 1`)."""
    text = NODE_TEXT[key].format(**fields)
    return text.replace(" of 1 days checked", " of 1 day checked") if fields.get("m") == 1 else text


def money2(value: Any) -> str:
    """`frontend/src/ui/money.ts` `money2`: two places, half even on the absolute value, exact; `-0.001` -> `0.00`."""
    d = Decimal(str(value))
    q = abs(d).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    text = f"{q:f}"
    return f"-{text}" if d < 0 and q != 0 else text


def money_text(low: Any, high: Any = None, currency: str | None = None) -> str | None:
    """R8: exactly `boardMoneyText` (`F/sites/OutcomeBoard.tsx`): None without an amount; `high=None` is one amount;
    equal bounds give one amount, else "{lo} to {hi}"; " {currency}" only when the currency is non-empty. Shared
    fixture `frontend/src/shell/__fixtures__/money-text.json`."""
    if low is None:
        return None
    lo = money2(low)
    hi = lo if high is None else money2(high)
    amount = lo if lo == hi else f"{lo} to {hi}"
    return f"{amount} {currency}" if currency else amount


def _one_decimal(value: Any) -> str:
    """`site_outcomes/mini.py` `num` (the MG-1 texts' number rule): integers plain, else one place half up."""
    d = Decimal(str(value))
    if d == d.to_integral_value():
        return str(int(d))
    return f"{d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP).normalize():f}"


def mg1_text(verdict: str | None, value: Any, checked: int, elapsed: int, month_days: int, target: Any,
             min_checked_days: int) -> str:
    """§A4 `verdict.*`: the MG-1 month text for `judge_month`'s verdict, by `mini.mg1_reading`'s rule; with no
    counted day, the board's "sales not recorded" (CH6a2-R Q5)."""
    if value is None or not checked:
        return MG1_NO_DAY
    words = {"mtd": _one_decimal(value), "c": checked, "e": elapsed, "m": month_days}
    if verdict in (ON_PACE, BEHIND_PACE):
        return MG1_PACE.format(**words, avg=_one_decimal(Decimal(str(value)) / checked),
                               need=_one_decimal(Decimal(str(target)) / month_days))
    if verdict == TOO_EARLY:
        return MG1_TOO_EARLY.format(**words, d="day" if checked == 1 else "days", k=min_checked_days)
    if verdict == MISSED:
        return MG1_MISSED.format(**words)
    return MG1_SO_FAR.format(**words)


def days_line(days: Any, day: date | None = None, span: Any = None, window: Any = None) -> str | None:
    """§A4 `days_line.*`: the M1 line of a node from its §S.2 days; None without days. A single expected day with no
    readings reads "No readings on {day}" when the day is given. CH6b1-R4 SPAN: the days are counted over the claim's
    `span`; the line names that span only when it differs from the Portfolio `window` ((first, last) days)."""
    d = _days_of(days)
    if d is None:
        return None
    if d["expected"] == 1 and d["no_data"] == 1 and day is not None:
        return node_text("days_line.no_data_one", day=day_text(day))
    line = node_text("days_line.many", k=d["complete"], m=d["expected"])
    if span is not None and window is not None and tuple(span) != tuple(window):
        line = f"{span_text(*span)} · " + line
    if d["partial"]:
        line += node_text("days_line.partial", p=d["partial"])
    if d["low"]:
        line += node_text("days_line.low", n=d["low"])
    return line


def verdict_claim(outcome_key: str, verdict: str | None, days: Any, text: str | None,
                  span: tuple[date, date] | None = None) -> Claim:
    """R8: the `kpi` node claim; `verdict=None` means no objective (CH6a2-R Q6: no days, NOT_KNOWN, "No target set
    yet"). The basis is the one basis rule over the measure's days."""
    key = f"verdict.{outcome_key}"
    if verdict is None:
        return Claim(key, None, NOT_KNOWN_BASIS, None, node_text("target.none"))
    d = _days_of(days)
    return Claim(key, verdict, count_basis(d), d, text or NOT_KNOWN_TEXT, None if d is None else span)


def money_claim(label: str, money: Mapping[str, Any] | None, days: Any, reason: str | None = None,
                span: tuple[date, date] | None = None) -> Claim:
    """R8/A4: an `earnings` node claim from a strategy's `Effect.money` ({"amount"} or {"low", "high"}, plus
    "currency"). With days, the text names the checked days; without (a stored consequence, CH6a2-R Q2) it is the
    amount alone. No money: `money.currency_mixed` for mixed currencies, else `money.not_known`."""
    key = f"money.{label}"
    d = _days_of(days)
    if not money:
        text = node_text("money.currency_mixed" if reason == "CURRENCY_MIXED" else "money.not_known")
        return Claim(key, None, NOT_KNOWN_BASIS, d, text, None if d is None else span)
    cur = money.get("currency")
    if "amount" in money:
        value = {"amount": str(money["amount"]), "currency": cur}
        amount = money_text(money["amount"], None, cur)
    else:
        value = {"low": str(money["low"]), "high": str(money["high"]), "currency": cur}
        amount = money_text(money["low"], money["high"], cur)
    basis = count_basis(d)
    if basis == NOT_KNOWN_BASIS:
        text = amount
    elif d["partial"]:
        text = node_text("money.days_partial", amount=amount, k=d["complete"], m=d["expected"], p=d["partial"])
    else:
        text = node_text("money.days", amount=amount, k=d["complete"], m=d["expected"])
    if label in INCOME_LABELS:
        text += node_text("money.income_suffix")
    return Claim(key, value, basis, d, text, None if d is None else span)


ESTATE_INCOME_KEY = "money.estate_income"


def estate_income(per_site: Sequence[tuple[str, Mapping[str, Any]]]) -> dict[str, Any]:
    """OWN-1104 R10 (replaced) with CH6b1-R Q5: the Portfolio income total over `(Site name, income claim JSON)` of
    every Site with an income record, in Portfolio order (a Site with none is not passed, so not named).

    - A contributor is a Site whose claim has an `amount`; its value is rounded to the minor unit by `money2` (the
      line's formatter) and the total is the sum of those rounded values, so the lines add up to the total (Q5b).
    - One currency only; otherwise value null and `money.currency_mixed`, still with the per-Site lines.
    - "At least ..." when any contributor is not COMPLETE or any named Site is NOT_KNOWN (Q5a); else the COMPLETE
      form; both end with `money.income_suffix`. No contributor: "Not known yet".
    - Lines: "{Site}: {amount} over {k} of {m} days checked[ · {p} partly checked]"; "{Site}: not known yet".
    - `days` = `sum_days` of the contributors' days (EV non-operating days are not expected, so not in `m`)."""
    lines: list[str] = []
    amounts: list[Decimal] = []
    currencies: set[str | None] = set()
    days: list[Any] = []
    partial_form = False
    for site, claim in per_site:
        value = claim.get("value") or {}
        if value.get("amount") is None:
            lines.append(node_text("income.site_not_known", site=site))
            partial_form = True
            continue
        d = _days_of(claim.get("days"))
        cur = value.get("currency")
        amount = money_text(value["amount"], None, cur)
        if d is None:
            text = amount
        elif d["partial"]:
            text = node_text("money.days_partial", amount=amount, k=d["complete"], m=d["expected"], p=d["partial"])
        else:
            text = node_text("money.days", amount=amount, k=d["complete"], m=d["expected"])
        lines.append(node_text("income.site", site=site, text=text))
        amounts.append(Decimal(money2(value["amount"])))
        currencies.add(cur)
        days.append(d)
        partial_form = partial_form or claim.get("basis") != COMPLETE_BASIS
    summed = None if not days or any(d is None for d in days) else sum_days(days)
    out: dict[str, Any] = {"key": ESTATE_INCOME_KEY, "value": None, "basis": NOT_KNOWN_BASIS, "days": summed,
                           "text": NOT_KNOWN_TEXT, "lines": lines}
    if not amounts:
        return out
    if len(currencies) != 1:
        return {**out, "text": node_text("money.currency_mixed")}
    (cur,) = currencies
    total = sum(amounts, Decimal(0))
    shown = money_text(total, None, cur)
    form = "income.at_least" if partial_form else "income.total"
    return {**out, "value": {"amount": money2(total), "currency": cur},
            "basis": CHECKED_DAYS_BASIS if partial_form else COMPLETE_BASIS,
            "text": node_text(form, total=shown) + node_text("money.income_suffix")}


def potential_claim(driver: str, value: Mapping[str, Any] | None, days: Any, lines: Sequence[str]) -> Claim:
    """A3.3 / CH6a2-R Q1: the `potential` node claim; `lines` joined by "\\n" (CH-6a3 splits them). No line is
    `potential.none`."""
    d = _days_of(days)
    text = "\n".join(lines) if lines else node_text("potential.none")
    return Claim(f"potential.{driver}", value, count_basis(d), d, text)


def potential_lines(low: Any, high: Any, money: Mapping[str, Any] | None) -> list[str]:
    """§A4 `potential.value` and, only with money (SUPPORTED and priced, R11), `potential.money`."""
    lines = [node_text("potential.value", lo=decimal_text(Decimal(str(low))), hi=decimal_text(Decimal(str(high))))]
    if money:
        lines.append(node_text("potential.money", lo=money2(money["low"]), hi=money2(money["high"]),
                               cur=money.get("currency")))
    return lines


# ---- CH-6b2 Portfolio cards (build sheet CH-6 §B2, CH6b2-R) ------------------------------------------------------
# The texts that were the browser's card rules (`F/estate/PortfolioOutcomes.tsx` before CH-6b2), moved unchanged
# unless marked; `site_outcomes/read.py` `portfolio_cards` and `estate/portfolio.py` `card_notes` render them.

CARD_TEXT = {
    # Grow (CH6b2-R Q4/Q5). The value small words; "possible" is the potential fallback, never "estimated".
    "grow.small.estimated": "estimated",
    "grow.small.possible": "possible",
    "grow.at_least": "At least {amount}",
    "grow.basis.income": "Declared price × measured kWh · not billed or collected",
    "grow.basis.none": "Opportunities · revenue not measured yet",
    # MOCK DEVIATION MD-CH6-6: per-Site targets when any Site declares one (the mock shows only the none form).
    "grow.target.none": "No target set yet at any site",
    "grow.site": "{site}: {text}",
    "grow.potential.none": "No potential found yet",
    # Protect (§B2: today's detail, from the server; CH6b2-R Q2).
    "protect.detail.none": "Service disruptions recorded as findings · loss not priced",
    "protect.detail": "Service disruptions recorded as findings · {w} early {warnings}, counted separately · "
                      "loss not priced",
    "protect.basis": "Measured events, counted separately · loss not priced",
    "protect.small.checked": "on the days checked",
    # Assure (§B2: today's `assureDetailText` words; the verified lead is the value now).
    "assure.basis": "Completed work does not establish savings",
    "assure.zero": "No verified result yet",
    "assure.targets_none": "no targets declared",
    "assure.targets": "targets declared at {sites}, for any outcome{unchecked}",
    "assure.unchecked": ", {sites} not checked",
    # The Portfolio-body clauses (`card_notes`, CH6b2-R Q1), today's `checkedDaysClause` / `evidenceGapText`.
    "note.withheld_one": " · findings next to unchecked days not shown yet",
    "note.withheld_many": " · findings next to those days not shown yet",
    "note.gap.unknown": "evidence gaps not assessed",
    "note.gap.zero": "no evidence gaps",
    "note.gap.zero_checked": "no evidence gaps on the days checked",
    "note.gap.one": "evidence gap at 1 site",
    "note.gap.all": "evidence gaps at all {sites} sites",
    "note.gap.some": "evidence gaps at {gaps} of {sites} sites",
    "note.gap.many": "evidence gaps at {gaps} sites",
    "days.site": "{site}: {line}",
}


def card_text(key: str, **fields: Any) -> str:
    return CARD_TEXT[key].format(**fields)


def sites_text(n: int) -> str:
    """"1 site", "3 sites" (the browser's `sites(n)` before CH-6b2)."""
    return f"{n} site" if n == 1 else f"{n} sites"


def evidence_gap_text(gaps: int | None, sites: int, checked_days: bool = False) -> str:
    """Rulings A-Q9 / A-Q10, moved from `evidenceGapText`: the evidence-gap clause of the Assure card."""
    if gaps is None:
        return card_text("note.gap.unknown")
    if gaps == 0:
        return card_text("note.gap.zero_checked" if checked_days else "note.gap.zero")
    if gaps == 1:
        return card_text("note.gap.one")
    if gaps == sites:
        return card_text("note.gap.all", sites=sites)
    if gaps < sites:
        return card_text("note.gap.some", gaps=gaps, sites=sites)
    return card_text("note.gap.many", gaps=gaps)


def count_card_value(claim: Mapping[str, Any], zero: str | None = None) -> dict[str, Any]:
    """CH6b2-R Q1: a count claim as the card's `{text, small}` (mock `2 <small>sites disrupted</small>`): the number
    and the claim's words after it; CHECKED_DAYS zero as "None found" + "on the days checked" (today's form)."""
    text, value, basis = claim["text"], claim.get("value"), claim["basis"]
    if basis == NOT_KNOWN_BASIS or value is None:
        return {"text": text, "small": None}
    if value == 0:
        if basis == COMPLETE_BASIS:
            return {"text": zero or text, "small": None}
        small = card_text("protect.small.checked")
        return {"text": text.removesuffix(" " + small), "small": small}
    head, _, rest = text.partition(" ")
    return {"text": head, "small": rest or None}
