"""SC-1 spec section 5.3: the cases of the shipped `common.*` statements (hand literals)."""
from __future__ import annotations

from assetops_backend.i18n import Flag, Items, Word

from statement_cases import Case

CASES = [
    Case("common.not_available", "analysing", {"pending": Flag(True)}, "Not analysed yet."),  # N1
    Case("common.not_available", "needs",  # N2: vocabulary order puts BILLING first
         {"pending": Flag(False), "needs": Items((Word("record", "FUEL_INVOICES"), Word("record", "BILLING")))},
         "Not available yet: it needs the billing export with each line's kWh and tariff and fuel invoices with litres."),
    Case("common.not_available", "plain", {"pending": Flag(False)}, "Not available yet."),  # N3
    Case("common.budget_lines", "one", {"factors": Items((Word("factor", "om"),))}, "a budget line for O&M"),  # B1
    Case("common.budget_lines", "many",  # B2: 5c section 2.2 order, `om` before `staff`
         {"factors": Items((Word("factor", "staff"), Word("factor", "om")))}, "budget lines for O&M and staff"),
]
