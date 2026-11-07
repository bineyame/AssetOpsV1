"""OUT-E E3: the cost check a newly inserted final outcome appends, on the real stores (`.agent/build-sheet-OUT-E.md`).

Each scenario builds in a child (`out_e_trial_child.py`; the S6 builders read the database URL at import) into its
own fresh `assetops_out_e_trial_<case>_test` database, dropped afterwards (the OUT-B4 `_case_db` helper):
- `verified` -> one revision, MODELLED_IMPROVEMENT, nominal change `1/24` on SFC 0.3 L/kWh and 1.25 USD/L; the same
  evaluation re-posted is a replay and appends nothing;
- `inconclusive` -> UNAVAILABLE / OUTCOME_INCONCLUSIVE;
- `target_miss` -> MODELLED_NO_IMPROVEMENT, nominal `0`;
- `failure` (the store's append raising) -> the outcome is recorded (201) and no revision exists.
`plan_sha256` at freeze equals the stored plan's after the evaluation and the hook, and the stored outcome
`details` windows never carry `generator_kwh`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

TESTS = Path(__file__).resolve().parent
SOURCE = "Generator stop setting changed; no direct cost declared"
CASES = ("verified", "inconclusive", "target_miss", "failure")


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> dict[str, dict]:
    from test_out_b4_board_postgres import _case_db, _child

    out: dict[str, dict] = {}
    for case in CASES:
        path = tmp_path_factory.mktemp(case) / "rec.json"
        with _case_db(f"trial_{case}", "e") as url:
            _child(url, [str(TESTS / "out_e_trial_child.py"), url, str(path), case])
        out[case] = json.loads(path.read_text(encoding="utf-8"))
        print(f"OUT-E3 record {case}: " + json.dumps({k: v for k, v in out[case].items() if k != "revisions"}),
              file=sys.stderr)
        for r in out[case]["revisions"]:
            print(f"OUT-E3 record {case} revision: {r['state']} {r['reason']} "
                  f"{r['result'].get('change_per_demand_kwh')}", file=sys.stderr)
    return out


def _plan_and_details_unchanged(rec: dict) -> None:
    assert rec["plan_sha256_frozen"] == rec["plan_sha256_stored"]
    assert "generator_kwh" not in rec["details_window_keys"] and "feeder_demand_kwh" in rec["details_window_keys"]
    assert "generator_idle_seconds" not in rec["details_window_keys"]  # FUEL-1 A2: the same exclusion


def test_verified_appends_one_improvement_and_a_replay_appends_none(built) -> None:
    rec = built["verified"]
    assert rec["outcome"]["outcome"] == "VERIFIED" and rec["status"] == [201, 200] and rec["replayed"] is True
    assert rec["outcomes"] == 1 and len(rec["revisions"]) == 1
    rev = rec["revisions"][0]
    assert (rev["state"], rev["reason"], rev["revision_no"]) == ("MODELLED_IMPROVEMENT", None, 1)
    assert rev["verification_outcome_id"] == rec["outcome"]["outcome_id"]
    assert rev["idempotency_key"] == f"auto:{rec['outcome']['outcome_id']}"
    assert (rev["actor_kind"], rev["source_channel"]) == ("SYSTEM", "SYSTEM_DEMONSTRATION_API")
    result = rev["result"]
    assert result["change_per_demand_kwh"] == {"nominal": "1/24", "upper": "11/240"}
    assert result["sfc"] == {"value_l_per_kwh": "0.3"}  # pre-flight: exactly one Kobo generator fuel rate
    assert result["price"]["value"] == "1.25" and result["price"]["currency"] == "USD"
    assert rev["price_revision_id"] == result["price"]["revision_id"]
    assert result["windows"]["baseline"]["generator_kwh"] == "40" and result["windows"]["later"]["generator_kwh"] == "28"
    assert result["windows"]["baseline"]["feeder_demand_kwh"] == "120"
    assert result["windows"]["later"]["feeder_demand_kwh"] == "126"
    assert rev["intervention_cost"] == {"amount": "0", "currency": "USD", "source": SOURCE}
    # FUEL-1 A2: no no-load rate is declared here, so the stored result is `/1` and carries no priced total
    assert result["formula"] == "trial-fuel-comparison/1" and "priced_total" not in result
    _plan_and_details_unchanged(rec)


def test_inconclusive_is_not_calculated_with_its_reason(built) -> None:
    rec = built["inconclusive"]
    assert rec["outcome"]["outcome"] == "INCONCLUSIVE" and len(rec["revisions"]) == 1
    rev = rec["revisions"][0]
    assert (rev["state"], rev["reason"]) == ("UNAVAILABLE", "OUTCOME_INCONCLUSIVE")
    assert rev["result"]["change_per_demand_kwh"] is None
    _plan_and_details_unchanged(rec)


def test_target_miss_is_no_improvement(built) -> None:
    rec = built["target_miss"]
    assert rec["outcome"]["outcome"] == "INEFFECTIVE" and len(rec["revisions"]) == 1
    rev = rec["revisions"][0]
    assert rev["state"] == "MODELLED_NO_IMPROVEMENT" and rev["result"]["change_per_demand_kwh"]["nominal"] == "0"
    _plan_and_details_unchanged(rec)


def test_a_store_failure_never_removes_the_outcome(built) -> None:
    rec = built["failure"]
    assert rec["status"] == [201] and rec["outcomes"] == 1 and rec["revisions"] == []
    assert rec["outcome"]["outcome"] == "INEFFECTIVE"
    _plan_and_details_unchanged(rec)
