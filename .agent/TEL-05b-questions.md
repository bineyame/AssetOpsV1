# TEL-05b builder questions (2026-10-28)

Items the spec does not settle. Each is built to the literal spec text or the existing contract, named here, and left for the Architect; none is a new design. None blocks the non-DB phase; Q1 and Q2 should be ruled before the two Postgres runs are taken as acceptance.

**TEL-05b-Q1. Finding-index request parameters.** Step 5 names `GET /api/sites/KOBO-001/finding-index` with no query. The route refuses that with 422 `UNSUPPORTED_DOMAIN` (`analytics/finding_index.py:131-141`: `domain`, `from` and `to` are required). Built: `domain=mini-grid-dispatch`, `from=2026-10-13T00:00:00Z`, `to=2026-10-14T00:00:00Z` (the window's UTC day). The S3 performance cutover gate may be closed for the test Site, so the test accepts either 200 (every row's `amount.state == "UNAVAILABLE"`) or 409 `PERFORMANCE_CUTOVER_CLOSED` with `rows: null`, and asserts no `current_amount_shown`/`presented_as_current` true anywhere in the body. It does not require the Finding to be listed (rows are present only for status `CURRENT`). Confirm the parameters and that both answers satisfy "the finding index shows no current amount".

**TEL-05b-Q2. Zero consequence revisions.** The gate reads "for every consequence revision that exists". Built literally: every `financial_consequence_revision` row for the Site is read pinned (`consequence_revision_id`), plus the head read for each Finding's latest revision; all must show `current_amount_shown == false` with `MIXED_OR_UNKNOWN_SOURCE` in `withheld_reasons`. If price seeding and `recompute_consequences run` produce **no** consequence revision, the test still passes on the head reads, and the withholding would then rest on the source gate of an absent head rather than on a recorded amount. Amendment 2 item 5's intent ("shown by the source gate, not by a missing price") suggests zero revisions should be a stop. Should the test assert at least one consequence revision exists?

**TEL-05b-Q3 (confirm, built).** Every Finding the Site has after `match-findings` is gated (cites only this test's accepted IDs, provenance UNKNOWN / `["NO_POSITIVE_BINDING"]`), and at least one must be anchored on 2026-10-13. The spec's `fid` is singular; the test does not assume exactly one Finding.

## Architect rulings (Claude, 2026-10-28; also in build spec section L)

**Q1. Confirmed, with one addition.** Keep `domain=mini-grid-dispatch`, `from=2026-10-13T00:00:00Z`, `to=2026-10-14T00:00:00Z`. Both answers pass, and no `current_amount_shown`/`presented_as_current` may be true anywhere: (a) 200 with every row `amount.state == "UNAVAILABLE"`, and if the body `status` is `CURRENT`, at least one row (an empty CURRENT page is a defect); (b) 409 `PERFORMANCE_CUTOVER_CLOSED` with `rows: null`. Any other status fails.

**Q2. Yes: zero is a stop.** With no head, `source_gate(None)` yields `MIXED_OR_UNKNOWN_SOURCE` without any amount being withheld. That case is vacuous, and owner Q5 and amendment 2 item 5 exclude it. Assert after step 4: (1) at least one consequence revision for (`fid`, `frid`); (2) at least one has `state == "PRICED"` with non-null `amount.low`/`amount.high`; (3) the head read and every pinned read show `presented_as_current == false`, `current_amount_shown == false`, and `MIXED_OR_UNKNOWN_SOURCE` in `withheld_reasons`; (4) each revision `source_provenance.state == "UNKNOWN"`. If (1) or (2) fails, stop and report the recompute output and the window's price selection. Do not tune anything.

**Q3. Confirmed as built.**

**Q3 (addendum). Accepted as built, plus a source-gate isolation read (2026-10-28, after gate runs A and B).**

*Stricter stop.* The reviewer accepts the builder's rule: every gated Finding must have at least one consequence revision, or the test stops. It is stricter than L-Q2 (1). It cannot hide a money-gate defect. Its only cost is a stop that goes to the Architect, and with one Finding per run it changes nothing today. L-Q2 (2), at least one PRICED revision with amounts, still applies to the 2026-10-13 Finding.

*Confound: it matters.* The API reads withhold the amount for three reasons: `AUDIT_ONLY`, `SOURCE_CLOSED` and `MIXED_OR_UNKNOWN_SOURCE`. The S3 performance cutover is closed for the test Site, and `consequence_read.py:187-190` sets `AUDIT_ONLY` before the source gate is reached. The claim record wording ruled in amendment 2, item 6 ("Money: not shown, by the existing source gate") and owner Q5 ("withheld because the source is not established") both name the source gate as the reason. Runs A and B show that this gate fails. They do not show that this gate alone withholds the amount on this revision. Opening the cutover is rejected: it needs a PASSED Performance comparison for this run's field data, which is new setup that could need tuning. A fakes-only unit test is also rejected, because it would not read this revision. That generic case is already covered by `backend/tests/test_lr01_money_eligibility_postgres.py:290-315`.

*Ruling: one read-only step 6 in `test_gx_profile_2_raises_a_finding_with_no_money_shown`, after step 5, on the same `fid`, `frid` and head.* It follows the existing pattern in `test_lr01_money_eligibility_postgres.py:290-302`. Call `build_consequence_read_service(URL).read(T, S, fid, frid, finding_revision_is_latest=True, source_open=True)` and assert exactly:
1. `currentness.state == "CURRENT"` and `currentness.reasons == []`;
2. `currentness.money_eligibility == "ELIGIBLE"`;
3. `consequence.state == "PRICED"`, `consequence.is_head is True`, and `amount.low` and `amount.high` are non-null and equal the head's stored amounts;
4. `currentness.source_gate == {"state": "UNKNOWN", "permits_current_money": False, "reason": "MIXED_OR_UNKNOWN_SOURCE"}`;
5. `currentness.withheld_reasons == ["MIXED_OR_UNKNOWN_SOURCE"]`, as an exact list;
6. `consequence.presented_as_current is False` and `currentness.current_amount_shown is False`.

Print the whole `currentness` block past capsys for the claim record. Steps 1-5 and their assertions are unchanged. No production code changes, and nothing is tuned.

*Stop.* If assertion 1, 2 or 3 fails, the amount is also withheld for a reason other than the source. Stop and report the read. Do not tune. The TEL-07 claim then uses the fallback wording below. If assertion 4, 5 or 6 fails, the source gate has a defect. Stop immediately and report it to the Architect.

*Claim record (TEL-07).* If step 6 passes, keep the wording from item 6 and add: "On the same revision with the performance cutover treated as open, the only reason the amount is withheld is `MIXED_OR_UNKNOWN_SOURCE`. Through the API, it is also withheld as `AUDIT_ONLY`/`SOURCE_CLOSED`, because the test Site has no Performance comparison." Fallback wording, used only if 1-3 fail: "Money: not shown. The amount is withheld because the source is not established, and on this test Site also because the performance cutover is closed. This run does not show the source gate as the only reason."

*Runs.* One more Postgres run on a freshly created `assetops_tel5b_test` is needed. The new step only reads, and runs A and B already showed steps 1-5 green twice, so one green run of the amended test closes the gate. (TEL-05b, TEL-07)
