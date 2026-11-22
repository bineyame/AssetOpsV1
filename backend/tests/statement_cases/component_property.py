"""DD3.2 (spec `specs/DD-demo-data/spec.md` §6, D-DD.17): the three cases of `component_property.basis`.
The English is the ruling's, written by hand (W2), never computed."""
from __future__ import annotations

from assetops_backend.i18n import Name, State

from statement_cases import Case

MAKER, MODEL = Name("FG Wilson", "datasheet.maker"), Name("P50-3", "datasheet.model")

CASES = [
    Case("component_property.basis", "declared",
         {"basis": State("MANUFACTURER_DATASHEET"), "maker": MAKER, "model": MODEL,
          "revision": Name("P50-3/4PP/0414/GB", "datasheet.revision")},
         "Declared, from the manufacturer data sheet (FG Wilson P50-3, P50-3/4PP/0414/GB)"),
    Case("component_property.basis", "fit", {"basis": State("DATASHEET_FIT"), "maker": MAKER, "model": MODEL},
         "Assumed: fitted to the data sheet's stated points (FG Wilson P50-3); the sheet states no value"),
    Case("component_property.basis", "generic",
         {"basis": State("GENERIC_DEFAULT"),
          "reason": Name("not stated by Pylontech; a typical LFP taper start", "datasheet.basis")},
         "Assumed: not stated by Pylontech; a typical LFP taper start"),
]
