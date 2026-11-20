"""4b2 test 5, DS1b parity (spec `specs/4b-money-leaves/spec.md` §5 test 5; Known Deviation in `packet-4b2.md`).

The simulator's claim: batch E of the product's fixture `backend/tests/fixtures/money_leaves_lakeside.json` holds,
as parsed objects, the records DS1b writes for those IDs, in DS1b's envelope. It lives here, not in
`backend/tests/test_4b_money_leaves.py`, because the dependency-direction guard bans a backend import of
`assetops_simulator` (5a test 10's precedent). The fixture is read by path; no product package is loaded.
"""

from __future__ import annotations

import json

from assetops_contracts.canonical.records_v1 import parse_record
from assetops_simulator.world.history import generate_history
from assetops_simulator.world.records import batch_file_name, build_records

from .conftest import REPOSITORY_ROOT, load_fixture

MONEY_FIXTURE = REPOSITORY_ROOT / "backend" / "tests" / "fixtures" / "money_leaves_lakeside.json"
IDS = ("gen:KOBO-001:2026-10:actual:om", "gen:KOBO-001:2026-10:actual:staff", "gen:KISIWA-001:2026-10:actual:staff",
       "gen:MTO-001:2026-10:actual:om", "gen:MTO-001:2026-10:actual:staff")


def test_5_batch_e_is_ds1b_verbatim() -> None:
    step = json.loads(MONEY_FIXTURE.read_text(encoding="utf-8"))["steps"][4]["batch"]
    ours = [parse_record(r) for r in step["records"]]
    assert tuple(r.source_record_id for r in ours) == IDS
    view = load_fixture()
    (theirs,) = [b for b in build_records(view, generate_history(view)).batches
                 if batch_file_name(b) == "lakeside-power.expense_ledger.json"]
    by_id = {o.source_record_id: o for o in theirs.outcomes}
    assert ours == [by_id[i] for i in IDS]
    assert {k: step[k] for k in ("tenant_code", "source_type", "source_system", "provenance", "produced_at")} == {
        "tenant_code": theirs.batch.tenant_code, "source_type": theirs.batch.source_type,
        "source_system": theirs.batch.source_system, "provenance": theirs.batch.provenance,
        "produced_at": theirs.batch.produced_at}
