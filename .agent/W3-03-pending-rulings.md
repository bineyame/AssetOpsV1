# W3-03 pending rulings

## P-0b-1 — RESOLVED (r0b applied: `excursion` + drain, cold line assertions added) — B3 clean fixture: cold `normal` makes no POTENTIAL_PRODUCT_EXPOSURE line (run 0b, stopped variant)

Spec: closure 4 B3 names cold `normal` (via `mixed_replay` mechanics) and requires "cold `POTENTIAL_PRODUCT_EXPOSURE`
UNPRICED" in the clean four-Site fixture, plus F/E/M COMPLETE.

Producer step: `test_w303_portfolio_fixture_postgres.py::build_portfolio_fixture` — `opened("normal", cold_chain)`,
`run(cold)` (W2-03 assessment worker), then EV x2, tariffs, money, P01 PowerSite v1-v3, `rig.run()`; frozen read
`2026-10-30T09:03:00Z` (= PowerSite `runner.now + 1 min`); request `[2026-10-06,2026-10-07)`, no `known_at`.

Actual public read (cold `normal`):
- `/findings`, `/evidence`, `/financials`: `CURRENT`, `coverage.state=COMPLETE`, all four Sites `CURRENT`.
- `/findings` rows: only KOBO-001 (W1 PRICED). **No COLD-LAB-001 Finding.**
- `/financials` rows: KOBO-001 `CANDIDATE_OPERATING_COST_EXPOSURE ELIGIBLE`; EV-LAB-001/002 `GROSS_TARIFF_SCENARIO
  ELIGIBLE` (group `COMPARABLE`, 2 lines). **No cold line**; group `POTENTIAL_PRODUCT_EXPOSURE` state
  `UNKNOWN_COVERAGE`, 0 lines, while root `coverage.state` is `COMPLETE` (under closure 5 S4 this cold unit is `U`,
  so Portfolio M would be PARTIAL, not COMPLETE).
- `/evidence`: COLD-LAB-001 rows backup/cooling/temperature FULL, exposure NONE (window 19:00-20:05Z).
- Cold coverage item: selection `…017c`, watermark real DB time, job SETTLED, freshness RECENT.

Mismatched assertion: "cold POTENTIAL_PRODUCT_EXPOSURE UNPRICED" (and M COMPLETE once Portfolio reduces it).

Probes (not committed; evidence only, same DB, same composition):
- cold `excursion` without drain: two cold Findings (`UNPRICED` in `/findings`), still no cold line,
  `POTENTIAL_PRODUCT_EXPOSURE` still `UNKNOWN_COVERAGE`.
- cold `excursion` **plus the W2-04 cold consequence worker** (`test_w204_cold_consequence.drain(cold)`, the pattern of
  `test_w301_provenance_dto_postgres.py::_cold`): one cold line `POTENTIAL_PRODUCT_EXPOSURE UNPRICED`, amount null,
  `finding_revision_id` = a selected cold Finding revision; group `INELIGIBLE` (1 line); all three roots
  `CURRENT/COMPLETE`; every other assertion in the test still passes (1 passed, 83 s).

Question: should the clean fixture use cold `excursion` + W2-04 drain (builder already takes
`cold_case="excursion", cold_drain=True`), or another cold producer? Once ruled, the held assertions to add are:

```python
(cold_line,) = lines[fx.site_ids["COLD-LAB-001"]]
cold_revisions = {r["finding_revision_id"] for r in rows[fx.site_ids["COLD-LAB-001"]]}
assert (cold_line["category"], cold_line["eligibility"]) == ("POTENTIAL_PRODUCT_EXPOSURE", "UNPRICED")
assert cold_line["amount"] is None and cold_line["finding_revision_id"] in cold_revisions
assert len({line["category"] for line in financials["rows"]}) == 3
```

## Q-1a-1 — RESOLVED (r1a applied in 1b: Lane A `06acf1cf`, Lane B `f3f04ef6`) (run 1a): S9 Action tie key has no selected event time in the Action selector rows

Spec: closure 4 S6-S9 "choose for a Finding cell by latest selected Action event `recorded_at`, then `action_id`
ascending". `coverage.py::_actions` (Lane A file) selects each Action's latest event but its row carries only
`selected_event_id`, not that event's `recorded_at`; Lane B may not edit it. Built in 1a:
`estate/portfolio.py::_action_for` joins on the exact `(source_finding_id, source_finding_revision_id)` pair and, when
several match, takes the max of a private `_raw["_selected_recorded_at"]` if present, else `action_id` ascending (the
spec's second key). No fixture exercises two Actions on one origin pair (10-06 has none; the S6 chain has one per
Finding). Question: should Lane A add private `_selected_recorded_at` (the selected event's `recorded_at`) to
`coverage.py::_actions` rows, with root bytes unchanged, before 1b's workflow-label tests?

## Q-1b-1 — OPEN (run 1b, blocks r1a2 item 4): Portfolio cursor signing key has no configuration seam

r1a2 item 4: "Use a server-held cursor signing key; refuse issuance if it is unavailable. ... Lane A owns the shared
`scope.py` encode/decode seam and configuration in a pre-1b handoff; Lane B uses it for Portfolio in 1b."
That Lane A seam was not built (the 1b dispatch names only `coverage.py::_selected_recorded_at` for Lane A), and no
signing-key configuration exists in the backend (`grep hmac|signing_key|secret_key` finds only
`evidence/gateway_access.py`'s verifier compare). Unruled: the key's source (environment variable name? settings
object?), its encoding/minimum length, how the development/test server gets one, and whether the router or the
service refuses issuance when it is absent (which status/code: 503 `ESTATE_STORE_UNAVAILABLE`, or another).
Question: give the literal configuration (name, encoding, dev/test default or none), the refusal status/code when
absent, and confirm which run/lane builds the `scope.py` seam (a Lane A pre-run before 1b continues, or 1b itself).
Not built: the HMAC, the 422 tamper tests, and the signed page-one-mode assertions in
`test_w303_portfolio_api.py::test_cursor_lens_window_cutoff_and_v1_token`.

## Q-1b-2 — OPEN (run 1b): `workflow_label` for an APPLIED Action with a non-VERIFIED terminal outcome

Closure 5 S7: "The table order is precedence", and the last row "Joined Action with none of the above, including
`NONE_AT_CUTOFF` or a non-VERIFIED terminal outcome" -> `No action yet`. A RESOLVED Action with outcome other than
VERIFIED normally reduces to `application_state=APPLIED` (lifecycle: APPLIED is never reverted), so strict first
match gives `Applied`; the "non-VERIFIED terminal outcome" clause then only reaches `NONE_AT_CUTOFF` (PENDING
matches its own earlier row). Built: strict table order (`portfolio.py::workflow_label`),
so APPLIED + RESOLVED/NOT_VERIFIED reads `Applied`; the test asserts only the unambiguous `NONE_AT_CUTOFF` case.
Question: is APPLIED + RESOLVED non-VERIFIED `Applied` (strict order) or `No action yet` (terminal clause wins over
the application rows)? Same question for PENDING + non-VERIFIED terminal, if reachable.

## Q-1b-3 — OPEN (run 1b): r1a2 item 2 pending guard without a selected line is invisible to Lane B

r1a2 item 2: "Lane B uses the full selected Financials inputs, including the guard/withheld reason". The selector
(`financials.py::select_financial_scope` / `windowed_lines`, Lane A files) exposes per Site only
`_windows_covered: bool`; the guard/withheld reason survives only on a selected line (`eligibility="PENDING"`).
A cold `withheld` read with zero consequences, or an EV transient guard with no stored history (`continue` at
`windowed_lines` EV branch), yields no line, so Portfolio sees only `_windows_covered=False` and reports UNKNOWN,
not PENDING. Built: `portfolio.py::money_pending` = window uncovered and any selected line `PENDING`.
Question: should Lane A add a private per-Site `_pending_guard: bool` (cold `withheld` or EV `ERROR_PENDING`) to the
financial selector's Site coverage, root bytes unchanged, or is the line-based rule sufficient for the named
persisted variant (a)?
