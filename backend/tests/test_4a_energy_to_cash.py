"""4a: energy to cash, where the kWh went (spec §6.1, tests 1 to 9; D-4A.1 to D-4A.26). No database.

Every expected figure is a literal of spec §5 (W2); none is computed with `month_energy`, `feeder_month` or the
evaluator. Run with `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` unset.
"""

from __future__ import annotations

import ast
import dataclasses
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from uuid import UUID

import pytest

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure import sources as _sources
from assetops_backend.structure.check import check
from assetops_backend.structure.energy import rules
from assetops_backend.structure.energy.rules import (
    Adjustment,
    Assignment,
    Charge,
    EnergyInputs,
    FeederInput,
    FeederMonth,
    MeterRead,
    month_energy,
)
from assetops_backend.structure.energy.source import NAMES, EnergyLeafSource
from assetops_backend.structure.evaluate import Coverage, LeafValue, Missing, evaluate
from assetops_backend.structure.registry import REGISTRIES, FilledBy
from assetops_backend.structure.sources import ENERGY_LEAVES, ENERGY_STATED, ReadContext
from test_3b3_structure_evaluate import _plant, _raises

MG = REGISTRIES["MINI_GRID"]
D = Decimal
FIRST, NEXT = date(2026, 10, 1), date(2026, 11, 1)
HELD = frozenset({"CHARGE", "ADJUSTMENT", "CUSTOMER_METER_READ", "METER_ASSIGNMENT"})
EMU, SIM = "source-emulated", "demo-simulated"
BILLING, MDM = "lakeside-billing", "lakeside-mdm"
NR, NC, NCY = "NOT_RECEIVED", "NOT_CONNECTED", "NOT_CALCULATED_YET"
METERED_FB = FilledBy("COMMERCIAL_RECORD", "CUSTOMER_METER_READ", "Customer meter reads for the month")
BILLED_FB = FilledBy("COMMERCIAL_RECORD", "CHARGE (USAGE kWh)", "Billing export: the month's billed kWh")
FEEDER_ID = UUID("00000000-0000-0000-0000-00000000f001")


def d(month: int, day: int, year: int = 2026) -> date:
    return date(year, month, day)


def feeder(code: str, days: tuple[D | None, ...], band: str = "DECLARED", pct: D | None = D(5),
           origins: tuple[str, ...] = (SIM,), n: int = 1) -> FeederInput:
    return FeederInput(UUID(int=n), code, days, origins, band, pct if band == "DECLARED" else None)


def usage(meter: str | None, account: str, kwh: str | None, amount: str, cls: str | None = "STANDARD",
          currency: str = "USD", line_type: str = "USAGE", subject_kind: str = "METER") -> Charge:
    subject = None if meter is None else (subject_kind, meter)
    return Charge(line_type, cls, None if kwh is None else D(kwh), D(amount), currency, subject, account, EMU, BILLING)


def read(meter: str, start: date, end: date, kwh: str, body: str | None = None) -> MeterRead:
    return MeterRead(meter, body or meter, start, end, D(kwh), EMU, MDM)


def assign(meter: str, customer: str, start: date, end: date | None = None, body: str | None = None) -> Assignment:
    return Assignment(meter, body or meter, customer, start, end)


OLD = [f"M-OLD-{k}" for k in range(1, 7)]
NEW = [f"M-220{k}" for k in range(1, 7)]
CUST = [f"C-04{k}" for k in range(12, 18)]
NEW_KWH = ["31", "27", "22", "25", "18", "17"]


def mto() -> EnergyInputs:
    """Spec §5.1."""
    f = feeder("mto-feeder", tuple([D(194)] * 30 + [D(180)]))
    assignments = ((assign("M-0001", "C-3001", d(1, 1)), assign("M-0099", "C-0099", d(1, 1)))
                   + tuple(assign(m, c, d(5, 1, 2023), d(10, 3)) for m, c in zip(OLD, CUST))
                   + tuple(assign(m, c, d(10, 3)) for m, c in zip(NEW, CUST)))
    reads = ((read("M-0001", FIRST, NEXT, "5400"), read("M-0099", FIRST, NEXT, "40"))
             + tuple(read(m, FIRST, d(10, 3), "0") for m in OLD)
             + tuple(read(m, d(10, 3), NEXT, k) for m, k in zip(NEW, NEW_KWH)))
    charges = ((usage("M-0001", "C-3001", "5400", "2160.00"), usage("M-0099", "C-0099", "0", "0.00"))
               + tuple(usage(m, c, "0", "0.00") for m, c in zip(OLD, CUST)))
    return EnergyInputs("2026-10", FIRST, NEXT, True, FeederMonth("ONE_SET", (f,), 31), HELD, charges,
                        (Adjustment(D(40), EMU, BILLING),), reads, assignments)


def kobo() -> EnergyInputs:
    """Spec §5.2."""
    feeders = (feeder("clinic-meter", tuple([D(50)] * 31), "NOT_DECLARED", n=1),
               feeder("mill-meter", tuple([D(94)] * 30 + [D(80)]), "NOT_DECLARED", n=2),
               feeder("residential-meter", tuple([D(150)] * 31), "NOT_DECLARED", n=3))
    return EnergyInputs(
        "2026-10", FIRST, NEXT, True, FeederMonth("ONE_SET", feeders, 31), HELD,
        (usage(None, "C-1001", "5000", "2000.00"), usage(None, "C-1002", "3645", "1458.00", cls=None)),
        (Adjustment(D(45), EMU, BILLING),),
        (read("M-1", FIRST, NEXT, "5045"), read("M-2", FIRST, NEXT, "3645")),
        (assign("M-1", "C-1001", d(1, 1)), assign("M-2", "C-1002", d(1, 1))))


def run(inputs: EnergyInputs) -> dict[str, LeafValue]:
    return dict(month_energy(inputs, NAMES).values)


def valued(lv: LeafValue, value: str, evidence: str, sources: tuple[str, ...], origins: tuple[str, ...],
           currency: str | None = None, coverage: Coverage | None = None) -> None:
    assert lv.value == D(value) and str(lv.value) != "-0", lv
    assert (lv.evidence, lv.sources, lv.origins, lv.currency, lv.missing, lv.coverage) == \
        (evidence, sources, origins, currency, None, coverage), lv


def absent(lv: LeafValue, fb: FilledBy, cause: str, note: str | None, coverage: Coverage | None = None) -> None:
    assert lv == LeafValue(None, "NOT_AVAILABLE", (), coverage,
                           Missing(fb.kind, fb.family, cause, None, (), fb.words, None, note), None), lv


def cov(covered: int, days: int = 31) -> Coverage:
    return Coverage(covered, days, {"COMPLETE": covered, "NO_DATA": days - covered})


FB = {f: MG.row(f).filled_by for f in rules.ENERGY_ORDER if f not in ("metered_kwh", "billed_kwh")}
FB.update(metered_kwh=METERED_FB, billed_kwh=BILLED_FB)
FEED = ("readings:feeder_demand",)
BAND = ("readings:feeder_demand", "foundation:technical-loss-band")
CBILL, CMDM = (f"commercial:{BILLING}",), (f"commercial:{MDM}",)


def other_leaves() -> dict[str, LeafValue]:
    """Every non-energy leaf absent, so the evaluated nodes rest on the energy figures alone."""
    out = {}
    for row in MG.rows:
        if row.is_leaf and row.factor_id not in ENERGY_LEAVES:
            fb = row.filled_by
            out[row.factor_id] = LeafValue(None, "NOT_AVAILABLE", (), None,
                                           Missing(fb.kind, fb.family, NC, None, (), fb.words, None, None), None)
    return out


def evaluated(values: dict[str, LeafValue]):
    leaves = {**other_leaves(), **{f: values[f] for f in ENERGY_LEAVES}}
    return evaluate(MG, leaves, {f: values[f] for f in ENERGY_STATED})


# ---------------------------------------------------------------- test 1: §5.1 and §5.2 field by field


def test_1_mto_chain():
    v = run(mto())
    valued(v["delivered_kwh"], "6000", "MEASURED", FEED, (SIM,), coverage=cov(31))
    valued(v["technical_loss_kwh"], "300", "MODELLED", BAND, (SIM,))
    valued(v["metered_kwh"], "5580", "RECORDED", CMDM, (EMU,))
    valued(v["unexplained_loss_kwh"], "120", "MODELLED", tuple(sorted(BAND + CMDM)), (EMU, SIM))
    valued(v["adjustments_kwh"], "40", "RECORDED", CBILL, (EMU,))
    valued(v["unmapped_kwh"], "140", "DERIVED", tuple(sorted(CBILL + CMDM)), (EMU,))
    valued(v["billed_kwh"], "5400", "RECORDED", CBILL, (EMU,))
    valued(v["tariff"], "0.4", "DERIVED", CBILL, (EMU,), currency="USD")
    out = evaluated(v)
    assert (out["metered_kwh"].value, out["metered_kwh"].stated, out["metered_kwh"].computed) == (D(5580), True,
                                                                                                    D(5580))
    assert (out["billed_kwh"].value, out["billed_kwh"].stated, out["billed_kwh"].computed) == (D(5400), True, D(5400))


def test_1_kobo_no_band_customer_billing():
    v = run(kobo())
    valued(v["delivered_kwh"], "9100", "MEASURED", FEED, (SIM,), coverage=cov(31))
    absent(v["technical_loss_kwh"], FB["technical_loss_kwh"], NC, "LOSS_BAND_NOT_DECLARED")
    absent(v["unexplained_loss_kwh"], FB["unexplained_loss_kwh"], NC, "LOSS_BAND_NOT_DECLARED")
    valued(v["metered_kwh"], "8690", "RECORDED", CMDM, (EMU,))
    valued(v["adjustments_kwh"], "45", "RECORDED", CBILL, (EMU,))
    valued(v["unmapped_kwh"], "0", "DERIVED", tuple(sorted(CBILL + CMDM)), (EMU,))
    valued(v["billed_kwh"], "8645", "RECORDED", CBILL, (EMU,))
    valued(v["tariff"], "0.4", "DERIVED", CBILL, (EMU,), currency="USD")
    out = evaluated(v)
    assert (out["billed_kwh"].value, out["billed_kwh"].computed) == (D(8645), D(8645))
    assert (out["metered_kwh"].value, out["metered_kwh"].stated, out["metered_kwh"].computed) == (D(8690), True, None)


# ---------------------------------------------------------------- test 2: the variants of §5.4


def _r(inputs: EnergyInputs, **kw) -> EnergyInputs:
    return dataclasses.replace(inputs, **kw)


def _feeders(inputs: EnergyInputs, **kw) -> EnergyInputs:
    fm = inputs.feeders
    return _r(inputs, feeders=FeederMonth(fm.state, tuple(dataclasses.replace(f, **kw) for f in fm.feeders),
                                          fm.days))


def _reads(inputs: EnergyInputs, keep=lambda r: True, add=()) -> EnergyInputs:
    return _r(inputs, reads=tuple(r for r in inputs.reads if keep(r)) + tuple(add))


def _assignments(inputs: EnergyInputs, drop: str) -> EnergyInputs:
    return _r(inputs, assignments=tuple(a for a in inputs.assignments if a.meter_ref != drop))


V9B_CHARGE = usage(None, "C-0415", "25", "10.00")
V10_CHARGE = usage("M-2201", "C-0412", "31", "12.40")


def _v3() -> EnergyInputs:
    days = list(mto().feeders.feeders[0].day_kwh)
    days[16] = None
    return _feeders(mto(), day_kwh=tuple(days))


def _v15() -> EnergyInputs:
    return _reads(mto(), keep=lambda r: r.meter_ref != "M-0001", add=[read("M-0001", FIRST, NEXT, "5400")])


def _v21() -> EnergyInputs:
    k = kobo()
    a, b, c = k.feeders.feeders
    fs = (dataclasses.replace(a, band_state="NOT_DECLARED", band_pct=None),
          dataclasses.replace(b, band_state="CHANGED", band_pct=None),
          dataclasses.replace(c, band_state="DECLARED", band_pct=D(5)))
    return _r(k, feeders=FeederMonth("ONE_SET", fs, 31))


VARIANTS = {
    "V1": lambda: _r(mto(), closed=False),
    "V2": lambda: _r(mto(), feeders=FeederMonth("NOT_BOUND", (), 31)),
    "V3": _v3,
    "V4": lambda: _feeders(mto(), band_state="CHANGED", band_pct=None),
    "V5": lambda: _r(mto(), held=HELD - {"METER_ASSIGNMENT"}, assignments=()),
    "V6": lambda: _reads(mto(), keep=lambda r: r.meter_ref != "M-0001",
                         add=[read("M-0001", d(9, 28), d(10, 28), "5400")]),
    "V7": lambda: _reads(mto(), add=[read("M-0099", d(10, 15), NEXT, "10")]),
    "V8": lambda: _reads(mto(), keep=lambda r: r.meter_ref != "M-0099"),
    "V9": lambda: _assignments(mto(), "M-2203"),
    "V9b": lambda: _r(mto(), charges=mto().charges + (V9B_CHARGE,)),
    "V9c": lambda: _assignments(_r(mto(), charges=mto().charges + (V9B_CHARGE,)), "M-2204"),
    "V9d": lambda: _r(_r(mto(), charges=mto().charges + (V9B_CHARGE,)),
                      assignments=mto().assignments + (assign("M-2204", "C-0415", d(10, 3)),)),
    "V10": lambda: _r(mto(), charges=mto().charges + (V10_CHARGE,)),
    "V11": lambda: _assignments(_r(mto(), charges=mto().charges + (V10_CHARGE,)), "M-2201"),
    "V12": lambda: _reads(mto(), keep=lambda r: r.meter_ref != "M-0001", add=[read("M-0001", FIRST, NEXT, "5570")]),
    "V13": lambda: _r(mto(), charges=mto().charges + (usage("M-0001", "C-3001", "100", "30.00", cls="PRODUCTIVE"),)),
    "V14": lambda: _r(mto(), charges=(dataclasses.replace(mto().charges[0], currency="KES"),) + mto().charges[1:]),
    "V15": _v15,
    "V16": lambda: _r(mto(), charges=tuple(dataclasses.replace(c, kwh=D(0), amount=D("0.00"))
                                           for c in mto().charges)),
    "V17": lambda: _r(mto(), held=HELD - {"CHARGE"}, charges=()),
    "V18": lambda: _reads(mto(), keep=lambda r: r.meter_ref != "M-0099",
                          add=[read("M-0099", FIRST, NEXT, "40", body="M-0098")]),
    "V18b": lambda: _r(mto(), assignments=tuple(
        dataclasses.replace(a, body_meter_ref="M-0098") if a.meter_ref == "M-0001" else a for a in mto().assignments)),
    "V19": lambda: _r(mto(), feeders=FeederMonth("BINDINGS_CHANGED", (), 31)),
    "V20": lambda: _feeders(mto(), band_state="NOT_DECLARED", band_pct=None),
    "V21": _v21,
    "V22": lambda: _r(mto(), held=HELD - {"CUSTOMER_METER_READ"}, reads=()),
    "V23": lambda: _r(mto(), reads=(), assignments=(assign("M-OLD-1", "C-0412", d(5, 1, 2023), d(9, 1)),)),
    "V24": lambda: _r(mto(), charges=(), adjustments=()),
    "V25": lambda: _r(mto(), charges=tuple(dataclasses.replace(c, line_type="FIXED", kwh=None)
                                           for c in mto().charges)),
    "V26": lambda: _r(mto(), feeders=FeederMonth("BINDINGS_CHANGED", (), 31), closed=False),
}


A = "absent"
#: Variant -> factor -> ("absent", cause, note[, coverage]) or (value[, currency]). Only the named factors (§5.4).
EXPECT = {
    "V1": {**{f: (A, NR, "MONTH_OPEN") for f in ("technical_loss_kwh", "metered_kwh", "unexplained_loss_kwh",
                                                  "adjustments_kwh", "unmapped_kwh", "billed_kwh", "tariff")},
           "delivered_kwh": (A, NR, "MONTH_OPEN", cov(31))},
    "V2": {**{f: (A, NC, "FEEDER_NOT_BOUND") for f in ("delivered_kwh", "technical_loss_kwh",
                                                        "unexplained_loss_kwh")},
           "metered_kwh": ("5580",), "adjustments_kwh": ("40",), "unmapped_kwh": ("140",), "billed_kwh": ("5400",),
           "tariff": ("0.4", "USD")},
    "V3": {"delivered_kwh": (A, NR, "FEEDER_READINGS_GAP", cov(30)),
           "technical_loss_kwh": (A, NR, "FEEDER_READINGS_GAP"), "unexplained_loss_kwh": (A, NR, "FEEDER_READINGS_GAP")},
    "V4": {"technical_loss_kwh": (A, NCY, "LOSS_BAND_CHANGED"), "unexplained_loss_kwh": (A, NCY, "LOSS_BAND_CHANGED"),
           "delivered_kwh": ("6000",)},
    "V5": {"metered_kwh": (A, NC, "NEEDS:METER_ASSIGNMENT"), "unmapped_kwh": (A, NC, "NEEDS:METER_ASSIGNMENT"),
           "unexplained_loss_kwh": (A, NC, "NEEDS:METER_ASSIGNMENT"), "billed_kwh": ("5400",),
           "tariff": ("0.4", "USD"), "adjustments_kwh": ("40",)},
    "V6": {f: (A, NCY, "METER_READ_STRADDLES") for f in ("metered_kwh", "unmapped_kwh", "unexplained_loss_kwh")},
    "V7": {f: (A, NCY, "METER_READS_OVERLAP") for f in ("metered_kwh", "unmapped_kwh", "unexplained_loss_kwh")},
    "V8": {f: (A, NR, "METER_READS_INCOMPLETE") for f in ("metered_kwh", "unmapped_kwh", "unexplained_loss_kwh")},
    "V9": {"unmapped_kwh": ("140",)},
    "V9b": {"unmapped_kwh": ("115",), "billed_kwh": ("5425",), "tariff": ("0.4", "USD")},
    "V9c": {"unmapped_kwh": ("140",), "billed_kwh": ("5425",)},
    "V9d": {"unmapped_kwh": ("140",), "billed_kwh": ("5425",)},
    "V10": {"unmapped_kwh": ("109",), "billed_kwh": ("5431",), "tariff": ("0.4", "USD")},
    "V11": {"unmapped_kwh": ("109",)},
    "V12": {"metered_kwh": ("5750",), "unexplained_loss_kwh": ("-50",), "unmapped_kwh": ("140",)},
    "V13": {"billed_kwh": ("5400",), "tariff": ("0.4", "USD")},
    "V14": {"tariff": (A, NCY, "CURRENCY_MISMATCH:KES,USD"), "billed_kwh": ("5400",)},
    "V15": {"metered_kwh": ("5580",)},
    "V16": {"billed_kwh": ("0",), "tariff": (A, NCY, "ZERO_DENOMINATOR:billed_kwh")},
    "V17": {"billed_kwh": (A, NC, None), "tariff": (A, NC, "NEEDS:CHARGE"), "adjustments_kwh": (A, NC, "NEEDS:CHARGE"),
            "unmapped_kwh": (A, NC, "NEEDS:CHARGE")},
    "V18": {**{f: (A, NCY, "METER_REF_CONFLICT") for f in ("metered_kwh", "unmapped_kwh", "unexplained_loss_kwh")},
            "billed_kwh": ("5400",)},
    "V18b": {**{f: (A, NCY, "METER_REF_CONFLICT") for f in ("metered_kwh", "unmapped_kwh", "unexplained_loss_kwh")},
             "billed_kwh": ("5400",)},
    "V19": {f: (A, NCY, "FEEDER_BINDINGS_CHANGED") for f in ("delivered_kwh", "technical_loss_kwh",
                                                              "unexplained_loss_kwh")},
    "V20": {"technical_loss_kwh": (A, NC, "LOSS_BAND_NOT_DECLARED"),
            "unexplained_loss_kwh": (A, NC, "LOSS_BAND_NOT_DECLARED"), "delivered_kwh": ("6000",),
            "metered_kwh": ("5580",)},
    "V21": {"technical_loss_kwh": (A, NC, "LOSS_BAND_NOT_DECLARED"),
            "unexplained_loss_kwh": (A, NC, "LOSS_BAND_NOT_DECLARED")},
    "V22": {"metered_kwh": (A, NC, None), "unmapped_kwh": (A, NC, "NEEDS:CUSTOMER_METER_READ"),
            "unexplained_loss_kwh": (A, NC, None), "technical_loss_kwh": ("300",), "billed_kwh": ("5400",)},
    "V23": {f: (A, NR, None) for f in ("metered_kwh", "unmapped_kwh", "unexplained_loss_kwh")},
    "V24": {"adjustments_kwh": (A, NR, "NEEDS:CHARGE"), "tariff": (A, NR, "NEEDS:CHARGE"),
            "unmapped_kwh": (A, NR, "NEEDS:CHARGE"), "billed_kwh": (A, NR, None), "metered_kwh": ("5580",)},
    "V25": {"billed_kwh": ("0",), "tariff": (A, NR, "NEEDS:CHARGE"), "unmapped_kwh": ("5580",),
            "adjustments_kwh": ("40",)},
    "V26": {"delivered_kwh": (A, NR, "MONTH_OPEN", None)},
}


def _check(lv: LeafValue, factor: str, want: tuple) -> None:
    if want[0] == A:
        absent(lv, FB[factor], want[1], want[2], want[3] if len(want) > 3 else None)
    else:
        assert lv.value == D(want[0]) and lv.missing is None and str(lv.value) != "-0", (factor, lv)
        assert lv.currency == (want[1] if len(want) > 1 else None), (factor, lv)


@pytest.mark.parametrize("variant", sorted(EXPECT))
def test_2_variant(variant):
    assert set(EXPECT) == set(VARIANTS)
    v = run(VARIANTS[variant]())
    for factor, want in EXPECT[variant].items():
        _check(v[factor], factor, want)


def test_2_v12_unexplained_is_modelled_and_unclamped():
    v = run(VARIANTS["V12"]())
    assert v["unexplained_loss_kwh"].evidence == "MODELLED" and v["unexplained_loss_kwh"].value == D(-50)


def test_2_v3_coverage_and_v19_none():
    assert run(VARIANTS["V3"]())["delivered_kwh"].coverage == cov(30)
    assert run(VARIANTS["V19"]())["delivered_kwh"].coverage is None


# ---------------------------------------------------------------- test 2b: the step map (§5.4b, D-4A.16)

#: Every step of spec §2.4's table once, hand-written: (factor, step) -> (cause, note) the step gives on its variant.
STEPS = {
    ("delivered_kwh", "1"): (NC, "FEEDER_NOT_BOUND"),
    ("delivered_kwh", "2"): (NR, "MONTH_OPEN"),
    ("delivered_kwh", "3"): (NCY, "FEEDER_BINDINGS_CHANGED"),
    ("delivered_kwh", "4"): (NR, "FEEDER_READINGS_GAP"),
    ("delivered_kwh", "2<3"): (NR, "MONTH_OPEN"),
    ("technical_loss_kwh", "1"): (NC, "FEEDER_NOT_BOUND"),
    ("technical_loss_kwh", "2"): (NC, "LOSS_BAND_NOT_DECLARED"),
    ("technical_loss_kwh", "3"): (NCY, "LOSS_BAND_CHANGED"),
    ("technical_loss_kwh", "4"): (NR, "FEEDER_READINGS_GAP"),
    ("technical_loss_kwh", "2<3"): (NC, "LOSS_BAND_NOT_DECLARED"),
    ("metered_kwh", "1"): (NC, None),
    ("metered_kwh", "2"): (NR, "MONTH_OPEN"),
    ("metered_kwh", "3"): (NC, "NEEDS:METER_ASSIGNMENT"),
    ("metered_kwh", "4"): (NCY, "METER_REF_CONFLICT"),
    ("metered_kwh", "5"): (NCY, "METER_READ_STRADDLES"),
    ("metered_kwh", "6"): (NCY, "METER_READS_OVERLAP"),
    ("metered_kwh", "7"): (NR, "METER_READS_INCOMPLETE"),
    ("metered_kwh", "8"): (NR, None),
    ("unexplained_loss_kwh", "1"): (NR, "FEEDER_READINGS_GAP"),
    ("unexplained_loss_kwh", "2"): (NCY, "LOSS_BAND_CHANGED"),
    ("unexplained_loss_kwh", "3"): (NC, "NEEDS:METER_ASSIGNMENT"),
    ("adjustments_kwh", "1"): (NC, "NEEDS:CHARGE"),
    ("adjustments_kwh", "2"): (NR, "MONTH_OPEN"),
    ("adjustments_kwh", "3"): (NR, "NEEDS:CHARGE"),
    ("unmapped_kwh", "1"): (NC, "NEEDS:METER_ASSIGNMENT"),
    ("unmapped_kwh", "2"): (NC, "NEEDS:CUSTOMER_METER_READ"),
    ("unmapped_kwh", "3"): (NC, "NEEDS:CHARGE"),
    ("unmapped_kwh", "4"): (NR, "MONTH_OPEN"),
    ("unmapped_kwh", "5"): (NCY, "METER_READ_STRADDLES"),
    ("unmapped_kwh", "6"): (NR, "NEEDS:CHARGE"),
    ("billed_kwh", "1"): (NC, None),
    ("billed_kwh", "2"): (NR, "MONTH_OPEN"),
    ("billed_kwh", "3"): (NR, None),
    ("tariff", "1"): (NC, "NEEDS:CHARGE"),
    ("tariff", "2"): (NR, "MONTH_OPEN"),
    ("tariff", "3"): (NR, "NEEDS:CHARGE"),
    ("tariff", "4"): (NCY, "CURRENCY_MISMATCH:KES,USD"),
    ("tariff", "5"): (NCY, "ZERO_DENOMINATOR:billed_kwh"),
}

#: Spec §5.4b: (factor, step) -> the variant that reaches it.
STEP_MAP = {
    ("delivered_kwh", "1"): "V2", ("delivered_kwh", "2"): "V1", ("delivered_kwh", "3"): "V19",
    ("delivered_kwh", "4"): "V3", ("delivered_kwh", "2<3"): "V26",
    ("technical_loss_kwh", "1"): "V2", ("technical_loss_kwh", "2"): "V20", ("technical_loss_kwh", "3"): "V4",
    ("technical_loss_kwh", "4"): "V3", ("technical_loss_kwh", "2<3"): "V21",
    ("metered_kwh", "1"): "V22", ("metered_kwh", "2"): "V1", ("metered_kwh", "3"): "V5",
    ("metered_kwh", "4"): "V18", ("metered_kwh", "5"): "V6", ("metered_kwh", "6"): "V7",
    ("metered_kwh", "7"): "V8", ("metered_kwh", "8"): "V23",
    ("unexplained_loss_kwh", "1"): "V3", ("unexplained_loss_kwh", "2"): "V4", ("unexplained_loss_kwh", "3"): "V5",
    ("adjustments_kwh", "1"): "V17", ("adjustments_kwh", "2"): "V1", ("adjustments_kwh", "3"): "V24",
    ("unmapped_kwh", "1"): "V5", ("unmapped_kwh", "2"): "V22", ("unmapped_kwh", "3"): "V17",
    ("unmapped_kwh", "4"): "V1", ("unmapped_kwh", "5"): "V6", ("unmapped_kwh", "6"): "V24",
    ("billed_kwh", "1"): "V17", ("billed_kwh", "2"): "V1", ("billed_kwh", "3"): "V24",
    ("tariff", "1"): "V17", ("tariff", "2"): "V1", ("tariff", "3"): "V25", ("tariff", "4"): "V14",
    ("tariff", "5"): "V16",
}


def test_2b_the_step_map_is_whole():
    assert set(STEP_MAP) == set(STEPS)
    assert {f for f, _ in STEPS} == set(rules.ENERGY_ORDER)


@pytest.mark.parametrize("factor, step", sorted(STEP_MAP))
def test_2b_each_step_is_reached(factor, step):
    lv = run(VARIANTS[STEP_MAP[(factor, step)]]())[factor]
    cause, note = STEPS[(factor, step)]
    assert lv.value is None and lv.evidence == "NOT_AVAILABLE"
    assert (lv.missing.cause, lv.missing.note) == (cause, note), lv


def test_2_v27_kobo_feeders_at_bands_4_5_6():
    k = kobo()
    fs = tuple(dataclasses.replace(f, band_state="DECLARED", band_pct=D(p))
               for f, p in zip(k.feeders.feeders, (4, 5, 6)))
    v = run(_r(k, feeders=FeederMonth("ONE_SET", fs, 31)))
    assert v["technical_loss_kwh"].value == D(486) and v["technical_loss_kwh"].evidence == "MODELLED"


def test_2b_the_kobo_band_is_step_2():
    v = run(kobo())
    assert (v["technical_loss_kwh"].missing.cause, v["technical_loss_kwh"].missing.note) == STEPS[
        ("technical_loss_kwh", "2")]


def test_2b_notes_list():
    assert rules.NOTES == (
        "FEEDER_NOT_BOUND", "FEEDER_BINDINGS_CHANGED", "FEEDER_READINGS_GAP", "LOSS_BAND_NOT_DECLARED",
        "LOSS_BAND_CHANGED", "METER_REF_CONFLICT", "METER_READ_STRADDLES", "METER_READS_OVERLAP",
        "METER_READS_INCOMPLETE", "NEEDS:METER_ASSIGNMENT", "NEEDS:CUSTOMER_METER_READ", "NEEDS:CHARGE", "MONTH_OPEN",
        "CURRENCY_MISMATCH:", "ZERO_DENOMINATOR:billed_kwh")
    assert rules.OBSERVER == "energy-to-cash@1"


# ---------------------------------------------------------------- test 4: the registry (D-4A.1)


def test_4_registry_v4_and_stated_rows():
    assert MG.version == 4
    stated = {r.factor_id: r.stated_by for r in MG.rows if r.stated_by is not None}
    assert stated == {
        "metered_kwh": METERED_FB,
        "billed_kwh": BILLED_FB,
        "revenue": FilledBy("COMMERCIAL_RECORD", "CHARGE", "Billing export: the month's charges"),
        "fuel_cost": FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", "Fuel invoices for the month"),
    }
    check(MG)


@pytest.mark.parametrize("target, changes", [
    ("diesel_l", {"stated_by": FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", None)}),  # litres stay refused
    ("delivered_kwh", {"stated_by": FilledBy("COMMERCIAL_RECORD", "CHARGE", None)}),  # a leaf
])
def test_4_stated_plants_refuse(target, changes):
    error = _raises("STRUCTURE_STATED", check, _plant(MG, target, **changes))
    assert error.factor_id == target


# ---------------------------------------------------------------- test 5: read alone


SITE = SiteRef(UUID(int=7), UUID(int=8), "MTO-001", "MINIGRID", "Africa/Nairobi")
NOW = datetime(2026, 11, 20, tzinfo=timezone.utc)


def test_5_product_source_alone_names_filled_by():
    src = _sources.ProductLeafSource(None, None, lambda: NOW)
    ctx = ReadContext(SITE, "2026-10", None)
    assert ENERGY_LEAVES == {"delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh",
                             "unmapped_kwh", "tariff"}
    for f in sorted(ENERGY_LEAVES):
        absent(src.leaf(ctx, f), MG.row(f).filled_by, NC, None)


def test_5_commercial_stated_alone_is_not_connected():
    from assetops_backend.structure.money import CommercialLeafSource
    src = CommercialLeafSource(None, None, None)  # nothing is read for the two kWh nodes
    ctx = ReadContext(SITE, "2026-10", None)
    absent(src.stated(ctx, "metered_kwh"), METERED_FB, NC, None)
    absent(src.stated(ctx, "billed_kwh"), BILLED_FB, NC, None)


# ---------------------------------------------------------------- test 6: one read per ReadContext object


class _Port:
    def __init__(self, inputs: EnergyInputs) -> None:
        self.inputs, self.calls = inputs, []

    def read(self, site, month, known_at, now):
        self.calls.append((site, month, known_at, now))
        return self.inputs


class _Fallback:
    def __init__(self) -> None:
        self.calls = []

    def leaf(self, ctx, factor_id):
        self.calls.append(("leaf", factor_id))
        return "fallback"

    def stated(self, ctx, factor_id):
        self.calls.append(("stated", factor_id))
        return "fallback"


def test_6_one_read_per_context_object():
    port, fallback = _Port(mto()), _Fallback()
    src = EnergyLeafSource(port, fallback, lambda: NOW)
    ctx = ReadContext(SITE, "2026-10", None)
    got = {f: src.leaf(ctx, f) for f in sorted(ENERGY_LEAVES)}
    got.update({f: src.stated(ctx, f) for f in sorted(ENERGY_STATED)})
    assert src.leaf(ctx, "om") == "fallback" and src.stated(ctx, "revenue") == "fallback"
    assert len(port.calls) == 1 and port.calls[0] == (SITE, "2026-10", None, NOW)
    assert fallback.calls == [("leaf", "om"), ("stated", "revenue")]
    assert got["metered_kwh"].value == D(5580) and got["tariff"].value == D("0.4")
    src.leaf(ReadContext(SITE, "2026-10", None), "tariff")  # an equal but different object reads again
    assert len(port.calls) == 2
    pinned = datetime(2026, 11, 2, tzinfo=timezone.utc)
    src.leaf(ReadContext(SITE, "2026-10", pinned), "tariff")
    assert port.calls[-1][2] == pinned


# ---------------------------------------------------------------- test 7: 5a's main factor heading (D-4A.9)


def test_7_main_of():
    from assetops_backend.structure.targets import rules as target_rules
    assert dict(target_rules.MAIN_OF["MINI_GRID"]) == {"delivered_kwh": ("billed_kwh", "revenue"),
                                                        "necessary_l": ("fuel_cost",)}


def test_7_delivered_is_solved_under_the_nearest_heading_with_a_target():
    import test_5a_targets as t5a
    w = t5a.lakeside()  # no billed-kWh line: neither heading has a target without prices
    v = t5a.read_site(w, "KOBO-001").structure.values
    assert v["delivered_kwh"].value is None and v["delivered_kwh"].missing.note == "MAIN_FACTOR_UNSOLVED:revenue"
    v = t5a.read_site(w, "KOBO-001", t5a.PRICED).structure.values  # revenue's target only
    assert (v["delivered_kwh"].value, v["delivered_kwh"].sources) == (D("8550"), ("assumption:main-factor:revenue",))
    line = t5a.budget_line("KOBO-001", "BUD-2026-10:KOBO-001:billed_kwh", "billed_kwh", "8550", currency=None)
    t5a.ingest(w, "2026-11-08T10:00:00+00:00", t5a.LOADER, t5a.budget_batch([line]))
    v = t5a.read_site(w, "KOBO-001").structure.values  # billed kWh's target: solved without any price
    assert (v["delivered_kwh"].value, v["delivered_kwh"].sources) == (D("8550"),
                                                                       ("assumption:main-factor:billed_kwh",))
    assert (v["billed_kwh"].value, v["billed_kwh"].stated, v["billed_kwh"].evidence) == (D("8550"), True, "DECLARED")


# ---------------------------------------------------------------- test 8: seams (ast)

ENERGY = Path(__file__).resolve().parents[1] / "assetops_backend" / "structure" / "energy"


def _imports(path: Path) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            out.add(node.module or "")
    return out


def test_8_seams():
    files = sorted(ENERGY.glob("*.py"))
    assert {p.name for p in files} >= {"__init__.py", "rules.py", "source.py"}
    for p in files:
        for mod in _imports(p):
            assert not mod.startswith(("assetops_simulator", "host", "assetops_backend.host")), (p, mod)
            assert "commercial.adapters" not in mod and not mod.split(".")[-1].endswith("_api"), (p, mod)
        tree = ast.parse(p.read_text(encoding="utf-8"))
        assert not any(isinstance(n, ast.Attribute) and n.attr == "absent" for n in ast.walk(tree)), p
        assert not any(isinstance(n, ast.ExceptHandler) for n in ast.walk(tree)), p  # D-4A.23
    allowed = ("assetops_backend.structure.evaluate", "assetops_backend.structure.registry", "assetops_contracts")
    std = {"__future__", "collections", "collections.abc", "dataclasses", "datetime", "decimal", "types", "uuid",
           "typing"}
    for mod in _imports(ENERGY / "rules.py"):
        assert mod in std or mod.startswith(allowed), mod


# ---------------------------------------------------------------- test 9: the Foundation property (D-4A.3, D-4A.18)


@pytest.mark.parametrize("component, value, refused", [
    ("load-mill", 5, None),
    ("load-clinic", 99.9, None),
    ("generator", 5, "technical-loss-band belongs on a LOAD"),
    ("load-mill", 100, "technical-loss-band on load-mill must be below 100"),
])
def test_9_the_band_property(component, value, refused):
    import test_w402_roles_properties as w402
    from assetops_backend.sites.ports import SiteConfigurationInvalid
    doc = w402._with(component, "technical-loss-band", value)
    if refused:
        with pytest.raises(SiteConfigurationInvalid, match=refused):
            w402._parse(doc)
    else:
        site = w402._parse(doc)
        props = {(c.component_id, p.property_key): p.value for c in site.foundation.components
                 for p in (c.properties or ())}
        assert props[(component, "technical-loss-band")] == value


def test_9_no_basis_property():
    from assetops_backend.sites.models import COMPONENT_PROPERTY_DEFINITIONS
    assert "technical-loss-band-basis" not in COMPONENT_PROPERTY_DEFINITIONS
    assert COMPONENT_PROPERTY_DEFINITIONS["technical-loss-band"].unit == "%"
def test_v15_is_a_register_read():
    """V15's read kWh is register_end − register_start (1,000 → 6,400), computed by the input adapter (§4.2)."""
    from assetops_backend.structure.energy.inputs import read_kwh
    assert read_kwh({"read_type": "REGISTER", "register_start": D(1000), "register_end": D(6400)}, None) == D(5400)


# ---------------------------------------------------------------- test 3: feeder_month (pure)

UTC = timezone.utc
LO, HI = datetime(2026, 9, 30, 21, tzinfo=UTC), datetime(2026, 10, 31, 21, tzinfo=UTC)  # Nairobi, UTC+3
SET_A, SET_B = UUID(int=101), UUID(int=102)
F1, F2 = UUID(int=201), UUID(int=202)


class Rows:
    def __init__(self, sets=None, bindings=None, foundations=None, readings=None) -> None:
        self.binding_sets = ((SET_A, LO - timedelta(days=30), None),) if sets is None else sets
        self.feeder_bindings = ((SET_A, F1, LO - timedelta(days=30), None),) if bindings is None else bindings
        self.assets = (("load-clinic", F1), ("load-res", F2), ("generator", UUID(int=203)))
        self.foundations = (_foundation({"load-clinic": 5}),) if foundations is None else foundations
        self.readings = tuple(_hourly(F1)) if readings is None else readings


def _foundation(bands: dict, comp_type: str = "LOAD") -> tuple:
    comps = [{"component_id": code, "component_type": comp_type,
              "properties": [{"property_key": "technical-loss-band", "value": v, "unit": "%"}]}
             for code, v in bands.items()]
    comps.append({"component_id": "load-res", "component_type": "LOAD", "properties": []})
    return (UUID(int=301), LO - timedelta(days=30), None, {"components": comps})


def _hourly(asset, kw="2", mode="SIMULATED", skip=None):
    for h in range(31 * 24):
        start = LO + timedelta(hours=h)
        if skip is not None and skip(start):
            continue
        yield {"evidence_id": UUID(int=h + 10_000), "asset_id": asset, "start": start,
               "end": start + timedelta(hours=1), "value_kw": D(kw), "quality": "GOOD", "source_mode": mode}


def fm(rows: Rows) -> FeederMonth:
    from assetops_backend.structure.energy.inputs import feeder_month
    return feeder_month(rows, LO, HI, FIRST, d(10, 31), "Africa/Nairobi")


def test_3_feeder_month_states():
    assert fm(Rows(sets=())) == FeederMonth("NOT_BOUND", (), 31)
    assert fm(Rows(bindings=())) == FeederMonth("NOT_BOUND", (), 31)
    two = ((SET_A, LO - timedelta(days=30), LO + timedelta(days=9)), (SET_B, LO + timedelta(days=9), None))
    assert fm(Rows(sets=two)).state == "BINDINGS_CHANGED"
    late = ((SET_A, F1, datetime(2026, 10, 14, 21, tzinfo=UTC), None),)  # from 10-15 local
    assert fm(Rows(bindings=late)) == FeederMonth("BINDINGS_CHANGED", (), 31)


def test_3_feeder_month_days_origins_and_band():
    whole = fm(Rows())
    assert whole.state == "ONE_SET" and len(whole.feeders) == 1
    f = whole.feeders[0]
    assert (f.asset_id, f.asset_code, f.origins, f.band_state, f.band_pct) == (F1, "load-clinic", (SIM,), "DECLARED",
                                                                                D(5))
    assert f.day_kwh == tuple([D(48)] * 31)
    day5 = datetime(2026, 10, 4, 21, tzinfo=UTC)  # 10-05 local midnight
    gap = list(_hourly(F1, skip=lambda s: s == day5 + timedelta(hours=3)))
    gap.append({"evidence_id": UUID(int=1), "asset_id": F1, "start": day5 + timedelta(hours=3),
                "end": day5 + timedelta(hours=3, minutes=45), "value_kw": D(2), "quality": "GOOD",
                "source_mode": "SIMULATED"})  # 15 minutes missing on day 5
    days = fm(Rows(readings=tuple(gap))).feeders[0].day_kwh
    assert days[4] is None and days[3] == D(48) and days[5] == D(48)
    day6 = day5 + timedelta(days=1)
    twice = list(_hourly(F1)) + [{"evidence_id": UUID(int=2), "asset_id": F1, "start": day6 + timedelta(hours=1),
                                  "end": day6 + timedelta(hours=2), "value_kw": D(2), "quality": "GOOD",
                                  "source_mode": "SIMULATED"}]
    days = fm(Rows(readings=tuple(twice))).feeders[0].day_kwh
    assert days[5] is None and days[4] == D(48)  # overlapping readings of one feeder: conflict
    live = fm(Rows(readings=tuple(_hourly(F1, mode="LIVE")))).feeders[0]
    assert live.origins == ("unknown",)


@pytest.mark.parametrize("foundations, state, pct", [
    ((_foundation({"load-clinic": 5}), _foundation({"load-clinic": 5})), "DECLARED", D(5)),
    ((_foundation({"load-clinic": 5}), _foundation({"load-clinic": 6})), "CHANGED", None),
    ((_foundation({"load-clinic": 5}), _foundation({})), "NOT_DECLARED", None),
    ((_foundation({"load-clinic": 5}, comp_type="GENERATOR"),), "NOT_DECLARED", None),  # no LOAD of that code
    ((), "NOT_DECLARED", None),
])
def test_3_band(foundations, state, pct):
    f = fm(Rows(foundations=foundations)).feeders[0]
    assert (f.band_state, f.band_pct) == (state, pct)


# ---------------------------------------------------------------- test 6b: live reads and failures (D-4A.23)


class _Mini:
    def __init__(self, error=None) -> None:
        self.known, self.error = [], error

    def feeder_month(self, *, tenant_id, site_id, lo, hi, known_at):
        self.known.append(known_at)
        if self.error is not None:
            raise self.error
        return Rows(sets=())


class _Store:
    def __init__(self) -> None:
        self.known = []

    def latest_revisions(self, tenant_id, *, site_id=None, kind=None, recognition_period=None, known_at=None):
        self.known.append(known_at)
        return ()


def test_6b_live_reads_pass_no_cutoff():
    from assetops_backend.structure.energy.inputs import StoreEnergyInputs
    mini, store = _Mini(), _Store()
    src = EnergyLeafSource(StoreEnergyInputs(mini, store), _Fallback(), lambda: NOW)
    lv = src.leaf(ReadContext(SITE, "2026-10", None), "delivered_kwh")
    assert mini.known == [None] and store.known == [None]
    assert lv.missing.note == "FEEDER_NOT_BOUND"
    early = datetime(2026, 10, 20, tzinfo=UTC)
    assert StoreEnergyInputs(mini, store).read(SITE, "2026-10", None, early).closed is False  # closed follows now
    assert mini.known[-1] is None and store.known[-1] is None
    pinned = datetime(2026, 11, 2, tzinfo=UTC)
    inputs = StoreEnergyInputs(mini, store).read(SITE, "2026-10", pinned, early)
    assert mini.known[-1] == pinned and store.known[-1] == pinned and inputs.closed is True


@pytest.mark.parametrize("error", ["MiniReadUnavailable", "MiniReadRefused"])
def test_6b_a_refusal_or_outage_propagates(error):
    from assetops_backend.mini_depth import read as mini_read
    from assetops_backend.structure.energy.inputs import StoreEnergyInputs
    cls = getattr(mini_read, error)
    src = EnergyLeafSource(StoreEnergyInputs(_Mini(cls("INVALID_KNOWN_AT")), _Store()), _Fallback(), lambda: NOW)
    with pytest.raises(cls):
        src.leaf(ReadContext(SITE, "2026-10", None), "technical_loss_kwh")


# ---------------------------------------------------------------- the composition (spec §4.3, L1)


def _builders(monkeypatch, log):
    from types import SimpleNamespace
    import assetops_backend.chain.composition as chain_composition
    import assetops_backend.commercial.composition as commercial_composition
    import assetops_backend.financials.composition as fin_composition
    import assetops_backend.structure.litres.composition as litre_composition
    store = object()
    monkeypatch.setattr(chain_composition, "build_snapshot_store",
                        lambda url: SimpleNamespace(dispose=lambda: log.append("snapshots")))
    monkeypatch.setattr(fin_composition, "build_window_price_selection",
                        lambda url: SimpleNamespace(select=None, dispose=lambda: log.append("prices")))
    monkeypatch.setattr(commercial_composition, "build_commercial_reads",
                        lambda url: SimpleNamespace(months=None, store=store, dispose=lambda: log.append("commercial")))
    monkeypatch.setattr(litre_composition, "build_litre_inputs",
                        lambda url: SimpleNamespace(inputs=None, dispose=lambda: log.append("litres")))
    return store


def test_composition_fifth_builder(monkeypatch):
    from types import SimpleNamespace
    import assetops_backend.structure.energy.composition as energy_composition
    from assetops_backend.structure.composition import build_structure_read
    from assetops_backend.structure.money import CommercialLeafSource
    log: list[str] = []
    store = _builders(monkeypatch, log)
    seen = []
    monkeypatch.setattr(energy_composition, "build_energy_inputs", lambda url, s: seen.append(s) or SimpleNamespace(
        inputs="inputs", dispose=lambda: log.append("energy")))
    service = build_structure_read("postgresql://x")
    assert seen == [store] and log == []  # the commercial store is shared, no second engine
    src = service.read._sources
    assert isinstance(src, EnergyLeafSource) and service.read._stated is src and src._inputs == "inputs"
    assert isinstance(src._fallback, CommercialLeafSource)
    service.dispose()
    assert sorted(log) == ["commercial", "energy", "litres", "prices", "snapshots"]


def test_composition_failing_fifth_builder_disposes_the_four(monkeypatch):
    import assetops_backend.structure.energy.composition as energy_composition
    from assetops_backend.structure.composition import build_structure_read
    log: list[str] = []
    _builders(monkeypatch, log)

    def boom(url, store):
        raise RuntimeError("energy builder failed")

    monkeypatch.setattr(energy_composition, "build_energy_inputs", boom)
    with pytest.raises(RuntimeError, match="energy builder failed"):
        build_structure_read("postgresql://x")
    assert sorted(log) == ["commercial", "litres", "prices", "snapshots"]
