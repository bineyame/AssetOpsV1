# TEL-05b review (independent Claude reviewer, 2026-10-28)

Branch `task/TEL-05b-finding-money-withheld` at `4430f65c`, diff `git diff main...HEAD`. Authority: build spec section TEL-05b and sections J/K/L, `.agent/TEL-05b-questions.md` (Q1-Q3 and the Q3 addendum), rulings amendment 2 (N1 replaced, owner Q5) and amendment 3 items 8-9.

## Verdict: REJECT (one High finding: the Postgres gate did not reproduce)

The slice's content is sound. The profile, fixture, emulator tests, oracle and steps 1-6 all match the spec and rulings as written, and I found no defect in the money or provenance assertions. But my independent run of the Postgres gate failed at the read-back comparison, before the Finding steps, because of a timing race that the packet does not name. "Green twice, each on a fresh database" holds for the implementer's runs. It does not hold as a reproducible gate. Steps 1-6 (Finding, provenance, price, recompute, API reads, step 6 isolation) are therefore **not independently verified** by this review.

## Findings

### High

**H1. The gate is timing-sensitive at boundary 03:00:00Z. The first SoC state read is skipped as late, so the exact oracle fails.** Locations: `host/tests/test_field_modbus_tcp_acceptance_postgres.py:495` (assert), `:60` (`RATE = 60`), `:340` (the oracle assumes every state read lands at B+1 s), `field/assetops_field/modbus_poller.py:299-306` (the skip rule), and profile `-2` `state_skew_max_seconds: 2`.
- What happened: in run `assetops_tel5br_test`, the poller counters were `VALUE 3169, SKIPPED_LATE 1` (implementer: VALUE 3170, SKIPPED_LATE 0). The raw capture shows the generator-status read at replay `03:00:01Z`. The SoC row (`battery-pcs-controller-state-of-charge`, address 1014) was then checked at replay `03:00:03Z`, past the limit B+2 s, at wall `23:21:34.596Z`. That is 51 ms after the wall epoch (`34.545Z`). The oracle expects `('battery-pcs-controller','state-of-charge','2026-10-13T03:00:00Z'): GOOD 40`, and that report never arrived. The result: `1 failed in 547.83s`, wall 549 s.
- Why it matters: profile `-2` is the first profile with two STATE rows on the same boundary. At rate 60, 2 replay seconds is about 33 ms of wall time. The first read of the session also pays for the TCP connect, so the second state read has almost no margin. This is a race, not a product defect: the poller correctly skipped a late read. But the acceptance gate depends on machine load, and the packet's residual-risk section does not mention it. The same exposure applies to TEL-08's stretch (`-2` on the BBB), which is slower.
- What would fix it: this is an Architect decision, because rate, skew and the oracle are spec-fixed and nothing may be tuned. Candidates are: open the Modbus connection before the replay epoch (a warm-up connect in the poller or harness); a lower rate for TEL-05b; a larger `state_skew_max_seconds` in `-2`; or an oracle that accepts a counted `SKIPPED_LATE` at the first boundary. After the ruling, take one fresh-DB green run. The packet should also record this risk.

### Medium

None.

### Low

**L1. The site-wide PRICED check does not match L-Q2 (2) exactly.** At `host/tests/test_field_modbus_tcp_acceptance_postgres.py:561`, L-Q2 (2) is asserted over all revisions on the Site, not per (`fid`, `frid`). Step 6 assertion 3 enforces a PRICED head per pinned Finding, so the coverage is there. But a missing PRICED revision would then surface as `STOP 3`, whose meaning is the fallback claim wording, rather than as the L-Q2 stop with the recompute report. With one Finding per run, the effect is nil today. Fix: filter on `own`.

**L2. The claim-record wording leaves out two statements the rulings require.** In `.agent/TEL-05b-review-packet.md:94`, the text equals amendment 2 item 6 plus the L-Q3 addition, so it matches what run C proved. Two statements are missing:
- amendment 2 item 2: "each published interval mean is held constant across its span, so the poller's exact mean reproduces it; the claim record says so";
- the representability rule: the unit-100 PV row is presented at register resolution (1 W), while "served through an AssetOps illustrative register block" covers only unit 101.

These belong to TEL-07, so this does not block. Note them for TEL-07.

## Requested verifications (by reading; the run reached only the read-back stage)

- **Profile `-2`.** Status `ILLUSTRATIVE`. Unit 101 rows 1000-1014 all carry row status ILLUSTRATIVE, source "AssetOps illustrative block; not a vendor register map", `quantity.point` "...not a vendor register", int32 BIG, exponent -6, sentinel 2147483647, span/cadence 300 and period 60. The ENUM is uint16 `{0..3}` with sentinel 65535. The PV row is unchanged and UNPINNED. 817-819, 842 and 843 are absent. `test_profile_2_is_the_tel05b_table` ties the file to `gx2_rows()`. Met.
- **Unit-101 exact read-back.** `test_every_unit_101_observation_reads_back_exactly_through_profile_2` compares `Fraction` equality per observation and passes. End to end, `_arrived_2 == expected` plus the independent source check. Met in code; the run failed on the race above, not on a value.
- **Finding cites only field IDs.** Step 2 checks `cited` is non-empty and `cited <= ids`, with `ids == receipt_ids` on a fresh DB. Met in code; not run.
- **Provenance UNKNOWN / `["NO_POSITIVE_BINDING"]`.** Checked for each Finding revision, and each consequence `source_provenance.state` is checked as UNKNOWN. Met in code; not run.
- **Step 6 isolates the source gate.** It reads with `source_open=True` and `finding_revision_is_latest=True` and checks the six exact assertions with STOP / SOURCE-GATE DEFECT labels, as in the Q3 addendum. Met in code; not run.
- **Stricter stop.** Any gated Finding with no consequence revision stops the run (`assert own` per pinned Finding). Met.
- **No simulation publication.** The draft is built with `FakeRuns`, nothing is published, and UNKNOWN is asserted. Met.
- **Not vacuous.** `good > 0`, Findings non-empty, at least one revision and at least one PRICED revision, exact-list step 6, and the current-amount scan of every body. Met.
- **The path is real.** Poller subprocess → emulator over TCP on 127.0.0.1 → real `GatewayProcess` → `FakeCentral` wrapping `BatchIngestionService(PostgresEvidenceLedger)`. Met.

## Checks run (revision `4430f65c`)

- `pytest field/tests host/tests/test_field_observation_fixtures.py gateway/tests/test_wire_contracts.py host/tests/test_field_modbus_tcp_acceptance_postgres.py` without a DB URL: **184 passed, 2 skipped** in 12 s.
- The Postgres gate `-k profile_2`, alone and with keep-awake running, on a freshly created `assetops_tel5br_test` at 127.0.0.1:55432. The database was dropped afterwards. **1 failed in 547.83 s** (wall 549 s); JUnit tests=1, failure at `:495` as in H1.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. Both were run directly, without `-ExecutionPolicy Bypass`.
- Not run: the TEL-04 end-to-end file, the full backend suite and any frontend checks (no frontend change).

## Residual risk not in the packet

- H1, the first-boundary state-read race at rate 60, which also bears on the TEL-08 `-2` stretch.
- I did not observe steps 1-6. The money and provenance conclusions rest on the implementer's runs A-C and on my reading of the code.
