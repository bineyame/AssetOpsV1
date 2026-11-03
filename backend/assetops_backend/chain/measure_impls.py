"""The six measure adapters of the day-snapshot chain (CH-1a §3 and the §5c rulings).

Each adapter reads through the one ``ChainInputReader`` port (injected) and calls the existing pure functions
unchanged: ``site_outcomes.productive_use.productive_energy`` and ``analytics.dispatch_read.dispatch_minutes``.
No driver, no SQL, no outcome id here (OL-1). The input ids an adapter returns are what the builder fingerprints,
so every stored basis a value depends on (readings, a price or tariff revision, a selected assessment revision)
is named among them.
"""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Iterable

from assetops_backend.analytics.dispatch_read import dispatch_minutes
from assetops_backend.site_outcomes.productive_use import GOOD, productive_energy

from .ports import ChainInputReader, DayCtx, InputSet

Span = tuple[datetime, datetime]
SITE = "SITE"
CENT = Decimal("0.01")
KWH = Decimal("0.001")

PRODUCTIVE_PRICE_KEY = "productive_use_price_per_kwh"
EXCURSION_ANALYTIC = "cold-excursion"
START_RESPONSE_ANALYTIC = "cold-start-response"
EV_SESSION_ANALYTIC = "ev-session/1"
CHAMBER_ROLE = "chamber_temperature"
#: CH1a-R D2/D3: Cold coverage counts the selected assessment window (the assessment's gap rule exists only there).
ASSESSED_WINDOW = "assessed_window"
#: §5c Q5: the backup-chain status roles whose accepted readings cover the period (grid, generator, transfer, bus).
BACKUP_ROLES = ("grid_power_event", "generator_state", "transfer_result", "backup_bus_state")


def _instant(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return d if d.is_finite() else None


def _num(d: Decimal) -> int | str:
    """An integral decimal as a JSON integer, else its plain decimal text."""
    return int(d) if d == d.to_integral_value() else f"{d.normalize():f}"


def _text(d: Decimal | None) -> str | None:
    return None if d is None else f"{d:f}"


def clip(spans: Iterable[Span], lo: datetime, hi: datetime) -> list[Span]:
    return [(max(a, lo), min(b, hi)) for a, b in spans if a is not None and b is not None and min(b, hi) > max(a, lo)]


def minus(base: Iterable[Span], holes: Iterable[Span]) -> list[Span]:
    """`base` with every `holes` span removed (half-open spans)."""
    out = list(base)
    for h0, h1 in holes:
        nxt: list[Span] = []
        for a, b in out:
            if h1 <= a or h0 >= b:
                nxt.append((a, b))
                continue
            if a < h0:
                nxt.append((a, h0))
            if h1 < b:
                nxt.append((h1, b))
        out = nxt
    return out


def _gaps(items: Iterable[dict[str, Any]], a_key: str, b_key: str) -> list[Span]:
    out = []
    for g in items or ():
        a, b = _instant(g.get(a_key)), _instant(g.get(b_key))
        if a is not None and b is not None and b > a:
            out.append((a, b))
    return out


class _Cached:
    """Values `money()` needs from `inputs()` (a price selection, a stored consequence), per subject-day."""

    def __init__(self) -> None:
        self._memo: dict[tuple, Any] = {}

    def _put(self, ctx: DayCtx, subject: str, value: Any) -> None:
        self._memo[(ctx.site_id, ctx.local_day, subject)] = value

    def _get(self, ctx: DayCtx, subject: str) -> Any:
        return self._memo.get((ctx.site_id, ctx.local_day, subject))


class ProductiveEnergy(_Cached):
    key = "mini.productive_energy@1"

    def __init__(self, reader: ChainInputReader) -> None:
        super().__init__()
        self.r = reader

    def subjects(self, ctx: DayCtx) -> list[str]:
        return sorted(str(u["asset_id"]).lower() for u in self.r.productive_assets(ctx) if u.get("asset_id"))

    def inputs(self, ctx: DayCtx, subject_ref: str) -> InputSet:
        readings = self.r.feeder_demand_readings(ctx, subject_ref)
        good = [x for x in readings if x.get("quality") == GOOD and x.get("value_kw") is not None]
        price = self.r.declared_price(ctx, PRODUCTIVE_PRICE_KEY)
        self._put(ctx, subject_ref, price)
        ids = [str(x["evidence_id"]).lower() for x in readings]
        if price and price.get("revision_id"):
            ids.append(f"price:{str(price['revision_id']).lower()}")
        return InputSet(tuple(ids), [(x["start"], x["end"]) for x in good], False, readings)

    def measure(self, ctx: DayCtx, subject_ref: str, inputs: InputSet) -> dict | None:
        e = productive_energy(inputs.payload, ctx.period_start_utc, ctx.period_end_utc)
        if e["kwh"] is None:
            return None
        self._put(ctx, subject_ref, (self._get(ctx, subject_ref), e["kwh"]))
        # stored to the watt-hour (as EV kWh); money is priced on the unrounded energy, as the board prices it
        return {"kwh": _text(e["kwh"].quantize(KWH, rounding=ROUND_HALF_UP)),
                "measured_seconds": e["measured_seconds"]}

    def money(self, ctx: DayCtx, subject_ref: str, value: dict) -> dict | None:
        sel, kwh = self._get(ctx, subject_ref)
        sel = sel or {}
        price = sel.get("price") or {}
        rate = _dec(price.get("value"))
        if sel.get("state") != "PRICED" or rate is None:
            return None
        amount = (kwh * rate).quantize(CENT, rounding=ROUND_HALF_UP)
        return {"amount": f"{amount:f}", "currency": str(price.get("currency")),
                "assumption_revision_id": str(sel["revision_id"]).lower()}


class RenewableHeadroom:
    key = "mini.renewable_headroom@1"

    def __init__(self, reader: ChainInputReader) -> None:
        self.r = reader

    def subjects(self, ctx: DayCtx) -> list[str]:
        return [SITE]

    def inputs(self, ctx: DayCtx, subject_ref: str) -> InputSet:
        pending = self.r.renewable_pending(ctx)
        head = self.r.renewable_hour(ctx)
        if head is None:
            return InputSet((), [], pending, None)
        period = [(ctx.period_start_utc, ctx.period_end_utc)]
        gaps = _gaps((head["result"].get("coverage") or {}).get("gaps"), "from", "to")
        ids = [str(x).lower() for x in head["evidence_ids"]] + [f"revision:{head['revision_id']}"]
        return InputSet(tuple(ids), minus(period, gaps), pending, head["result"])

    def measure(self, ctx: DayCtx, subject_ref: str, inputs: InputSet) -> dict | None:
        hour = (inputs.payload or {}).get("hour") or {}
        decision = hour.get("decision")
        if decision in ("ELIGIBLE", "EXCLUDED"):
            headroom = hour.get("headroom_kw") or {}
            low, high = _dec(headroom.get("low")), _dec(headroom.get("high"))
            return {"low_kw": _text(low), "high_kw": _text(high), "decision": decision}
        return {"low_kw": None, "high_kw": None, "decision": None, "result_state": decision}

    def money(self, ctx: DayCtx, subject_ref: str, value: dict) -> dict | None:
        return None


class DispatchMinutes:
    key = "mini.dispatch_minutes@1"

    def __init__(self, reader: ChainInputReader) -> None:
        self.r = reader

    def subjects(self, ctx: DayCtx) -> list[str]:
        return self.r.foundation_assets(ctx, "GENERATOR")

    def inputs(self, ctx: DayCtx, subject_ref: str) -> InputSet:
        lo, hi = ctx.period_start_utc, ctx.period_end_utc
        windows = self.r.dispatch_days(ctx)
        pending = any(w.get("status") == "PENDING" for w in windows) or self.r.pending_jobs(ctx, ["dispatch"])
        runs, mine = [], []
        for w in windows:
            if w.get("selection") is None:
                continue
            runs.append(str(w["selection"]["run_id"]))
            for iv in w.get("intervals") or ():
                res = iv.get("result") or {}
                first_on = _instant((res.get("interval") or {}).get("first_on"))
                # one local day per interval: the day its generator-on interval starts in
                if (str(res.get("generator_asset_id")).lower() == subject_ref and first_on is not None
                        and lo <= first_on < hi):
                    mine.append(iv)
        evidence = self.r.run_evidence_intervals(ctx, runs)
        ids = sorted({e[0] for e in evidence} | {f"revision:{str(iv['id']).lower()}" for iv in mine}
                     | {f"selection:{str(r).lower()}" for r in runs})
        return InputSet(tuple(ids), [(a, b) for _, a, b in evidence], bool(pending), mine)

    def measure(self, ctx: DayCtx, subject_ref: str, inputs: InputSet) -> dict | None:
        candidate, indeterminate = dispatch_minutes({"intervals": inputs.payload})
        return {"minutes": _num(candidate), "indeterminate_minutes": _num(indeterminate)}

    def money(self, ctx: DayCtx, subject_ref: str, value: dict) -> dict | None:
        return None


class ChamberTemperature:
    key = "cold.chamber_temperature@1"

    def __init__(self, reader: ChainInputReader) -> None:
        self.r = reader

    def subjects(self, ctx: DayCtx) -> list[str]:
        return self.r.foundation_assets(ctx, "COLD_ROOM")

    def inputs(self, ctx: DayCtx, subject_ref: str) -> InputSet:
        lo, hi = ctx.period_start_utc, ctx.period_end_utc
        covered: list[Span] = []
        ids: set[str] = set()
        for ws, we, run_id in self.r.selected_windows(ctx, [EXCURSION_ANALYTIC]):
            t = self.r.cold_temperature(ctx, ws, we)
            ids.add(f"run:{run_id}")  # a re-assessment over the same evidence is a changed input
            policy = t.get("policy")
            if policy is None:
                continue
            room = policy.get("room_asset_id")
            if room is not None and str(room).lower() != subject_ref:
                continue
            # §5c Q6: the assessed window minus the assessment's gaps
            covered += minus(clip([(ws, we)], lo, hi), _gaps(t.get("gaps"), "start", "end"))
            ids |= {str(p["evidence_id"]).lower() for p in t.get("points") or ()}
        raw = [x for x in self.r.readings(ctx, [CHAMBER_ROLE], lo, hi)
               if x["source_time"] is not None and lo <= x["source_time"] < hi]
        ids |= {x["evidence_id"] for x in raw}
        return InputSet(tuple(sorted(ids)), covered, self.r.pending_jobs(ctx, ["cold_chain"]), raw)

    def measure(self, ctx: DayCtx, subject_ref: str, inputs: InputSet) -> dict | None:
        values = [v for v in (_dec(x.get("value")) for x in inputs.payload or ()) if v is not None]
        # D3 (CH1a-R): the gap rule is the assessment's own, defined only inside an assessed window, so coverage
        # keeps the assessed-window basis; the value says so.
        return {"peak_c": _text(max(values)) if values else None, "basis": ASSESSED_WINDOW}

    def money(self, ctx: DayCtx, subject_ref: str, value: dict) -> dict | None:
        return None


class BackupStartChain:
    key = "cold.backup_start_chain@1"

    def __init__(self, reader: ChainInputReader) -> None:
        self.r = reader

    def subjects(self, ctx: DayCtx) -> list[str]:
        return self.r.foundation_assets(ctx, "GENERATOR")

    def inputs(self, ctx: DayCtx, subject_ref: str) -> InputSet:
        lo, hi = ctx.period_start_utc, ctx.period_end_utc
        readings = self.r.readings(ctx, BACKUP_ROLES, lo, hi)
        covered: list[Span] = []
        chains: list[dict[str, Any]] = []
        ids = {x["evidence_id"] for x in readings}
        for ws, we, run_id in self.r.selected_windows(ctx, [START_RESPONSE_ANALYTIC]):
            ids.add(f"run:{run_id}")
            inside = [x for x in readings if x["source_time"] is not None and ws <= x["source_time"] < we]
            b = self.r.cold_backup_chain(ctx, ws, we)
            if b.get("state") is None or not inside:
                continue
            # §5c Q5 (see packet deviation): the assessed window in which backup-role readings were accepted
            covered += clip([(ws, we)], lo, hi)
            chains += list(b.get("chains") or ())
            ids |= {str(e).lower() for ch in b.get("chains") or () for st in ch.get("steps") or ()
                    for e in st.get("evidence_ids") or ()}
        return InputSet(tuple(sorted(ids)), covered, self.r.pending_jobs(ctx, ["cold_chain"]), chains)

    def measure(self, ctx: DayCtx, subject_ref: str, inputs: InputSet) -> dict | None:
        chains = inputs.payload or []
        return {"starts": len(chains), "failed": sum(1 for ch in chains if ch.get("result") == "OBSERVED_FAILURE"),
                "basis": ASSESSED_WINDOW}

    def money(self, ctx: DayCtx, subject_ref: str, value: dict) -> dict | None:
        return None


class ChargingEnergy(_Cached):
    key = "ev.charging_energy@1"

    def __init__(self, reader: ChainInputReader) -> None:
        super().__init__()
        self.r = reader

    def subjects(self, ctx: DayCtx) -> list[str]:
        return [SITE]

    def inputs(self, ctx: DayCtx, subject_ref: str) -> InputSet:
        covered: list[Span] = []
        ids: set[str] = set()
        reads = []
        for ws, we, run_id in self.r.selected_windows(ctx, [EV_SESSION_ANALYTIC]):
            ids.add(f"run:{run_id}")
            w = self.r.ev_window(ctx, ws, we)
            if not w["selected"]:
                continue
            # §5c Q1: meter intervals ∪ reported known-status spans; unknown meter seconds are in neither set
            covered += list(w["meter"]) + list(w["status"])
            ids |= set(w["evidence_ids"])
            money = w.get("money") or {}
            for k in ("revision_id", "tariff_revision_id"):
                if money.get(k):
                    ids.add(f"{k}:{str(money[k]).lower()}")
            reads.append(w)
        self._put(ctx, subject_ref, [w.get("money") for w in reads])
        return InputSet(tuple(sorted(ids)), covered, self.r.pending_jobs(ctx, ["ev_charging"]), reads)

    def measure(self, ctx: DayCtx, subject_ref: str, inputs: InputSet) -> dict | None:
        reads = inputs.payload or []
        kwh = [_dec((w["energy"] or {}).get("complete_kwh")) for w in reads]
        kwh = [k for k in kwh if k is not None]
        return {"kwh": _text(sum(kwh, Decimal("0"))) if kwh else None,
                "sessions": sum(int((w["denominator"] or {}).get("started") or 0) for w in reads),
                "completed": sum(int((w["denominator"] or {}).get("completed") or 0) for w in reads)}

    def money(self, ctx: DayCtx, subject_ref: str, value: dict) -> dict | None:
        rows = [m for m in self._get(ctx, subject_ref) or () if m and _dec(m.get("amount")) is not None]
        currencies = {str(m.get("currency")).upper() for m in rows}
        if not rows or len(currencies) != 1:
            return None
        amount = sum((_dec(m["amount"]) for m in rows), Decimal("0")).quantize(CENT, rounding=ROUND_HALF_UP)
        return {"amount": f"{amount:f}", "currency": currencies.pop(),
                "tariff_revision_ids": sorted(str(m["tariff_revision_id"]).lower() for m in rows
                                              if m.get("tariff_revision_id"))}


def build_measure_set(reader: ChainInputReader) -> dict[str, Any]:
    adapters = (ProductiveEnergy(reader), RenewableHeadroom(reader), DispatchMinutes(reader),
                ChamberTemperature(reader), BackupStartChain(reader), ChargingEnergy(reader))
    return {a.key: a for a in adapters}
