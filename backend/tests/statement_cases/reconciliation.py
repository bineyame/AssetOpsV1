"""3A7 (spec section 2.7 and section 6, under the rulings' "Amendment (SC-1)"): a hand-written case per variant of
the statements 3A7 adds beyond SC-1's worked shapes (the heading, gap, share and scope statements are covered by
`worked.py`'s C1 to C9 and SC1, SC2). Every English literal is written by hand (W2), never computed.

Evidence: the tolerance is `DECLARED` with origin `observed-financial` (the owner's figure or RC8's 1 in 100), so it
reads "(Declared)" inline, for every origin (D-SC1.18; D-SC1F.1, C11 and C12).
"""
from __future__ import annotations

from decimal import Decimal as D

from assetops_backend.i18n import Absent, Count, Evidence, Money, Month, Name, Percent, State, Word

from statement_cases import Case

FIN = "observed-financial"
EMU = "source-emulated"


def tol(value: str = "0.01", origin: str | None = FIN) -> Percent:
    return Percent(D(value), Evidence("DECLARED", origin))


def site(code: str) -> dict:
    return {"scope": State("SITE"), "site": Name(code, "site.code")}


ORG = {"scope": State("ORGANISATION"), "site": Absent("ORGANISATION")}
OCT = Month(2026, 10)


def refused(code: str, **facts) -> dict:
    return {"code": State(code), **facts}


def figure(origin: str, reconciled: bool | None) -> dict:
    return {"figure": Money(D("505.00"), "USD", Evidence("RECORDED", origin, reconciled))}


CASES = [
    # reconciliation.statement (spec section 6: K after E and F, S3, T2's S1, T6's S4)
    Case("reconciliation.statement", "matched", {"state": State("MATCHED"), "month": OCT, **site("KOBO-001"),
                                                 "tolerance": tol()},
         "October 2026 (KOBO-001) matches the management accounts within 1% (Declared)."),
    Case("reconciliation.statement", "matched", {"state": State("MATCHED"), "month": OCT, **site("KOBO-001"),  # C11
                                                 "tolerance": tol(origin=None)},
         "October 2026 (KOBO-001) matches the management accounts within 1% (Declared)."),
    Case("reconciliation.statement", "matched", {"state": State("MATCHED"), "month": OCT, **site("KOBO-001"),  # C12
                                                 "tolerance": tol(origin="demo-simulated")},
         "October 2026 (KOBO-001) matches the management accounts within 1% (Declared)."),
    Case("reconciliation.statement", "not_matched", {"state": State("NOT_MATCHED"), "month": OCT, **ORG,
                                                     "tolerance": tol()},
         "October 2026 (the organisation) does not match the management accounts within 1% (Declared)."),
    Case("reconciliation.statement", "not_comparable", {"state": State("NOT_COMPARABLE"), "month": OCT,
                                                        **site("MTO-001"), "tolerance": tol()},
         "October 2026 (MTO-001) cannot be compared with the management accounts yet."),
    # reconciliation.standing (T1, T3, T2, T6, T7, T8)
    Case("reconciliation.standing", "reconciled", {"reason": State("RECONCILED"), "month": OCT, **ORG,
                                                   "tolerance": tol()},
         "Reconciled: October 2026 (the organisation) matches the management accounts within 1% (Declared)."),
    Case("reconciliation.standing", "reconciled", {"reason": State("RECONCILED"), "month": OCT, **ORG,
                                                   "tolerance": tol("0.02")},
         "Reconciled: October 2026 (the organisation) matches the management accounts within 2% (Declared)."),
    Case("reconciliation.standing", "this_month_not_matched",
         {"reason": State("THIS_MONTH_NOT_MATCHED"), "month": OCT, **ORG, "tolerance": tol()},
         "Not yet reconciled: October 2026 (the organisation) does not match the management accounts within 1% "
         "(Declared)."),
    Case("reconciliation.standing", "this_month_not_comparable",
         {"reason": State("THIS_MONTH_NOT_COMPARABLE"), "month": OCT, **site("MTO-001"), "tolerance": tol()},
         "Not yet reconciled: October 2026 (MTO-001) cannot be compared with the management accounts yet."),
    Case("reconciliation.standing", "no_statement", {"reason": State("NO_STATEMENT"), **site("KOBO-001"),
                                                     "tolerance": tol()},
         "Not yet reconciled: no closed month has been compared with the management accounts."),
    Case("reconciliation.standing", "none_matched", {"reason": State("NONE_MATCHED"), **site("KOBO-001"),
                                                     "tolerance": tol()},
         "Not yet reconciled: no month's recorded revenue and fuel cost match the management accounts within 1% "
         "(Declared) yet."),
    # reconciliation.money_word (R6: the "Recorded" and "Emulated" bases, reconciled and not)
    Case("reconciliation.money_word", "word", figure(FIN, True), "Recorded"),
    Case("reconciliation.money_word", "word", figure(FIN, False), "Recorded, not yet reconciled"),
    Case("reconciliation.money_word", "word", figure(EMU, True), "Emulated"),
    Case("reconciliation.money_word", "word", figure(EMU, False), "Emulated, not yet reconciled"),
    # reconciliation.refused (spec section 2.5, R4)
    Case("reconciliation.refused", "role", refused("RECON_ROLE"),
         "Only the finance lead records the management accounts."),
    Case("reconciliation.refused", "period", refused("RECON_PERIOD"), "Write the month as YYYY-MM, like 2026-10."),
    Case("reconciliation.refused", "site_unknown", refused("RECON_SITE_UNKNOWN", site=Name("NOPE-001", "site.code")),
         "This Site is not this organisation's: NOPE-001."),
    Case("reconciliation.refused", "no_mini_grid", refused("RECON_SITE_UNKNOWN"),
         "This organisation has no mini-grid Site to compare with the management accounts."),
    Case("reconciliation.refused", "site_type", refused("RECON_SITE_TYPE", site=Name("FRZ-001", "site.code")),
         "Only mini-grid Sites are compared with the management accounts for now: FRZ-001."),
    Case("reconciliation.refused", "currency", refused("RECON_CURRENCY"),
         "Write the currency as its code in capital letters, like USD."),
    Case("reconciliation.refused", "amount", refused("RECON_AMOUNT", heading=Word("heading", "REVENUE")),
         "Write the revenue as digits with a decimal point and no separators, like 1200.00."),
    Case("reconciliation.refused", "amount", refused("RECON_AMOUNT", heading=Word("heading", "FUEL_BOUGHT")),
         "Write the fuel bought as digits with a decimal point and no separators, like 1200.00."),
    Case("reconciliation.refused", "source_ref", refused("RECON_SOURCE_REF", limit=Count(200, "character")),
         "Say where the figures come from, in at most 200 characters."),
    Case("reconciliation.refused", "month_open", refused("RECON_MONTH_OPEN", month=Month(2026, 11)),
         "November 2026 is not closed yet: record a closed month."),
]
