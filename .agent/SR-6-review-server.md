# SR-6a server review (fresh Claude reviewer, 2026-11-12)

Branch `task/SR-6-health-range`, head 5cf6278b7, diff `git diff $(git merge-base HEAD main) HEAD`, focused on SR-6's own files.
Spec: rev 10 §10.1-10.2, rev 10a §10a.1, rev 10d §10d.9; D-SR.9, D-SR.19-23, D-SR.49.

## Verdict: ACCEPT WITH FINDINGS FIXED ON THE BRANCH (2 Medium, 3 Low)

The read shape, cutoffs, route and guard edit are correct. Two summary/state rules in `site_health_range.py` do not match D-SR.49 / D-SR.20. Both are small and local, and both were reproduced with a probe test (not committed).

## Findings

**M1 (acceptance gap, D-SR.49 Q2). `gateways_in_contact_all_days` counts against Site-level expected days, not the gateway's own.**
`backend/assetops_backend/sites/site_health_range.py:134-139`. `expected` is the Site's with/without days. A gateway registered mid-window has NOT_EXPECTED contact on its pre-registration days, so `all(... == IN_CONTACT)` fails. Q2 says NOT_EXPECTED (before registration) and AFTER_CUTOFF days "are skipped, and they do not break the count".
Probe: edge-2 was registered on day 2 and had full diagnostics on days 2-6. Its contact read `[NOT_EXPECTED, NOT_EXPECTED, IN_CONTACT x5]`, and the result was `gateways_in_contact_all_days == 0`. The ruling requires 1.
Why it matters: the status line "Gateways in contact on every expected day: n of m" under-reports.
Fix: per gateway, take the days whose contact is not NOT_EXPECTED/AFTER_CUTOFF (intersected with the Site's expected days, if the Architect wants both). Count the gateway when that set is non-empty and all of it is IN_CONTACT.
Tests: every existing assertion of this field is `== 0` (`test_sr6_health_range_route.py:151`, `test_sr6_health_range_postgres.py:106`). Add a positive case and the mid-window registration case.

**M2 (misstated data, D-SR.20 principle and D-SR.49 Q1 "with ... as built"). A day with accepted readings can read NOT_EXPECTED, and it drops out of `days_with_readings`.**
- `site_health_range.py:68-70`: `source_state` returns NOT_EXPECTED whenever the SR-5a day state is NOT_EXPECTED, even with readings > 0.
- `site_health_range.py:132-133`: `klass` tests `not_expected` (and `after_cutoff`) before `with`.
- Before the fix round (4f450d065), `days_with_readings` counted every day with readings, and Q1 confirmed that definition "as built". The fix round narrowed it.
Probe: with day 0 in NOT_EXPECTED state and 288 readings, the source cell was `{"accepted_readings": 288, "state": "NOT_EXPECTED"}` and the summary was with=2 (was 3), not_expected=1.
`test_sr6_health_range_route.py:170-175` pins exactly this ("Before readings began" with 288 readings).
This is reachable. The day state's NOT_EXPECTED comes from the chain's Site-local day grade, looked up by UTC date (`estate/range_days.py:69,87`). Both demo Sites are UTC+3 (Addis Ababa, Dar es Salaam). If readings begin in local 00:00-03:00, they land on the UTC day whose local grade is NOT_EXPECTED.
Fix (or an Architect ruling): readings > 0 wins in `source_state` and in `klass`, so a reading day is always "with" and READINGS. This mirrors D-SR.20's gateway precedence (readings beat "before registered").

**L1 (residual risk, spec-level). A live stored body does not see new diagnostics or registration changes.**
`source_health_api.py:153-156` follows rev 10.2's key and watermark exactly. But `gateway_diagnostic`, `gateway` and `source` are not watermark input tables (`migrations/versions/0047_chain_response.py:29-50`).
So with no `known_at`, a body can show NO_CONTACT / PARTIAL_CONTACT for today, or a stale `disabled` flag, until the next local midnight (`valid_until`) or until a readings arrival moves the watermark. A diagnostics-only gateway is the case where Health matters most.
For the Architect: accept as a known limit (the point-in-time "Contact now" panel stays below), or add the tables to the watermark inputs.

**L2 (missing test, guard precedent). There is no guard self-test for the new `$pgReaders` entry.**
`tools/checks/test_estate_guard.py:14` records that each added reader comes "with its own reviewed file and guard test" (the thread and chain readers have `*_write_rejected` tests). I ran an equivalent probe on an isolated copy. An INSERT appended to `sites/adapters/postgres_health_range.py` is refused ("A second product database writer ... postgres_health_range.py:51"), and the driver import is not refused. So the guard holds today. Add the test so it stays pinned.

**L3 (merge order). The branch carries SR-5a's code at 034852bb2.**
That is `estate/site_range.py`, the range-overview route in `outcome_api.py`, SR-5 tests and a fixture. SR-5 is not on main and has D-SR.50 work pending. Merge SR-5 first and then main into SR-6, or SR-6 lands an older, partly reviewed SR-5a.

## Verified as correct
- One `read_snapshot`. `_health_registration` is called through `evidence.composition.health_registration` (it returns the staticmethod, nothing is copied), and the counts go through `sites.composition`, both on `snap._c`. Order: registration, counts, `select_finding_scope` once for coverage, `range_day_states` (D-SR.22/23).
- D-SR.19 SQL (`postgres_health_range.py:177-190`):
  - readings join `ingestion_disposition` on batch/ordinal, with ACCEPTED, `accepted_evidence_id = e.id`, `decided_at <= k` and `e.tenant_id`, bucketed and windowed on `COALESCE(interval_start, source_time)`;
  - diagnostics use `tenant_id`, `site_id` and `received_at <= k`.
- Contact precedence matches D-SR.20 (diagnostics, then readings (READINGS_ONLY), then before registration, then AFTER_CUTOFF, then NO_CONTACT). The 0.9 rule uses seconds in `[from, min(to,k))`. D-SR.21's dead branches are gone. No `battery` key, and no Foundation 409.
- AFTER_CUTOFF: a day start at or after `min(to,k)` gets it in gateway contact and source state, `days[].state` is unchanged, and the summary classes sum to `days_requested`.
- Route (`source_health_api.py:87-158`):
  - admission comes first, as source-health does (401/403, with no reads; the test asserts nothing was called);
  - registry 503/404, then Cold/EV 404 `HEALTH_RANGE_NOT_APPLICABLE` before the window, then 422 `INVALID_WINDOW` via `estate_request`;
  - 503 `SITE_HEALTH_RANGE_UNAVAILABLE` (no estate, or the store is down); out of scope is 404 `SITE_NOT_FOUND`;
  - key `{site, from, to, known_at}`, `sites` = `watermark_sites` = (Site); one `perf.route` line.
- `main.py:624-628`: included right after `estate_portfolio`, and `responses` exists by then. The source-health router is unchanged.
- Guard diff: exactly one added `$pgReaders` element, a single literal file path (no glob or directory). No other guard line changed.
- Diff hygiene: no `__pycache__`, cache or other ignored files. The `.agent/` additions are named packets.

## Checks run (this reviewer, worktree head 5cf6278b7)
- No-DB: `test_sr6_health_range_route.py` + `test_sr5_range_overview.py` + `test_s7_source_health_rules.py`: **68 passed**, 2.4 s.
- `test_sr6_health_range_postgres.py` on `assetops_sr6_test`: **5 passed**, 0 skipped, 27.8 s.
- Probe tests for M1 and M2: both failed as described (temporary file, removed). The guard write-refusal probe for L2 was refused as expected.
- Not run, per the dispatch: check-all (cited as 19/19 on head by the implementer), the full backend suite, and the frontend (no frontend change in SR-6a). Parity and timing (`SR-6-parity.json`) are still pending, as the packet states.
