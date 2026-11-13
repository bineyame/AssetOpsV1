# DATA-10 fix packet (gate item 2)
Problem: Kisiwa Protect > Generator read "No preventive plan recorded" though the CALENDAR generator plan exists (D-DATA.4).
Fix: board.PlanFact gains asset_type (default None, last field; positional callers unaffected); mini.plan_fact passes p.get("asset_type");
mini._protect shows the first CALENDAR GENERATOR plan as "{title} due {d MMM}" / "overdue since {d MMM}" (UTC suffix without Site tz) when no RUN_HOURS plan.
Wire check: mini `plans` port = read.py select_preventive wire (global_index asset_fields -> asset_type), same wire cold.py reads.
Callers: cold.py/ev.py use plan_fact (no _protect); only mini calls _protect (new args defaulted).
Tests: 5 new in backend/tests/test_out_b2_mini.py; with b1_board, c4_mini_ev, b3_cold_ev, k4b_protect_fuel: 139 passed. No frontend test pins the text. check-all: for coordinator.
