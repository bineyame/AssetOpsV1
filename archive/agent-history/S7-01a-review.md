# S7-01a review - Site source-health and battery boundary reads

Reviewer: fresh independent Claude reviewer (did not author the slice). Reviewed `c5945e88`
(`task/S7-01a-health-read`), diff `git diff 8b5d8137..c5945e88 -- ':!.agent'`, against
`tasks/S7-01a-health-read.md` (incl. plan fix round 1), `D-2026-10-16-a-s7-health`, the S7-01 section of
`.agent/architect-W1-remaining-answers.md` and item 2 of `.agent/architect-W1-remaining-q-answers.md`.

## Verdict: ACCEPT

No High or Medium finding. Six Low findings below; none blocks merge. L1, L4 and L5 are carried to S7-01b
(they matter for the walkthrough and UI, not for the correctness of these reads); L2 and L3 are Architect
confirmations.

## Checks run (by this reviewer)

- Focused, private DB `s701a_rev_test` (created and dropped), worktree `PYTHONPATH`, main venv:
  `pytest backend/tests/test_s7_source_health_postgres.py backend/tests/test_s7_asset_boundary_postgres.py`
  -> **14 passed** (156.8 s).
- Adjacent, serial: `pytest backend/tests/test_s2_gateway_access_postgres.py` -> **29 passed** (28.8 s).
- `tools/check-architecture.ps1` -> "Architecture check passed." exit 0.
- `tools/check-agent-workflow.ps1` -> "Agent workflow check passed." exit 0.
- Full suite not rerun. Cited: implementer's run on `c0bc25e1`, 2449 passed, JUnit 0 failures/errors/skipped,
  1284 s. `git diff --stat c0bc25e1..c5945e88` touches only `.agent/S7-01a-handoff.md` and
  `.agent/S7-01a-review-packet.md`, so that run covers the reviewed code.
- Not run: `tools/writer_guard_probes.py --seam` (it mutates the tree; I cite the packet). I checked rule 8 by
  reading the diff: the only product-module change in a writer module
  (`postgres_gateway_access.py:205-250`) is SELECT-only, and the INSERTs are confined to
  `backend/tests/s7_health_cases.py:109-117`. Non-UI slice: no frontend or layout evidence needed.

## Focus points verified

- **Contact freshness from server receipt only.** `source_health.py:197` uses `freshness(received_at, ...)`;
  the reported-fact age (`fact_age`, `:166-177`) and the clock trust (`:158-163`) are separate fields. STALE
  carries the reason `NO_RECEIPT_WITHIN_THRESHOLD_OUTAGE_START_NOT_DATED` and `not_claimed` includes `OUTAGE_START`.
- **Queue and disk as last reported.** Both have `as: LAST_REPORTED` (`:251-255`), and `CURRENT_HARDWARE_STATE`
  is not claimed.
- **No green zero.** No enabled gateway gives `NO_REGISTERED_SOURCE`, and `ALL_CURRENT` needs at least one
  enabled gateway (`:265-266`). A never-received gateway is `UNKNOWN`/`NEVER_RECEIVED` with null facts.
- **409/503 with no rows.** Both refusal bodies carry `gateways: null` (`source_health_api.py:49-71`). An
  unset DATABASE_URL raises `LedgerUnavailable` from `_connect_engine` and becomes 503. `check_consistent`
  refuses a non-snapshot isolation, duplicate or foreign rows, a source not registered to its gateway, a receipt
  after the read time, and a row that disagrees with its stored text.
- **One repeatable-read snapshot.** `postgres_gateway_access.py:212-217` runs registration and the latest
  diagnostic in one `REPEATABLE READ` transaction and records the isolation. The race test commits between the
  two statements and passes.
- **S2 gateway-health unchanged.** `gateway_api.py` and `gateway_access.py` are not in the diff, and
  `test_s2_gateway_access_postgres.py` passes.
- **401/403/404.** Both reads use the `finding_api.Access` seam. An unknown or foreign Site gives 404, and a
  foreign, unknown or non-battery asset gives 404 `ASSET_NOT_IN_EFFECTIVE_BASIS` with `physical_condition: null`.
- **Battery.** Physical condition is always `UNKNOWN` with three named missing causal inputs, or
  `NOT_CONFIGURED` with no asset ID. Nothing reads gateway health or evidence tables. Nameplate carries the
  `DECLARED_FOUNDATION_RATING` label, SOC is not selected, and the withheld list is complete.
- **Deviations judged.** The fixture SQL inserts the case gateways and sources DISABLED
  (`disabled_at = registered_at`, `s7_health_cases.py:111,115`), as an import does, and only the provisioning
  CLI enables them. It is test-only, so rule 8 is clean. Treating `NO_REGISTERED_SOURCE` as "no enabled
  gateway" is the only reading under which the state can ever occur for an imported Site, and the disabled
  gateway is still listed. See L3 for the wording. The 5000 ms tolerance is covered in L2.
- **Handoff for S7-01b.** It provides one gateway per case, a `deliver()` that reloads the manifest from a fresh
  process, and the second Site (KOBO-002 via `NO_REGISTERED_SOURCE`, plus `without_battery` for an absent
  battery). The gaps are in L1 and L4.

## Findings

1. **Low - S7-01b handoff omits that the cases break S1's single-gateway binding rule on the case Site.**
   `backend/tests/s7_health_cases.py:107-117` adds eight gateways to KOBO-001. `validate_bindings` requires
   exactly one registered gateway per Site and does not filter out disabled ones
   (`backend/assetops_backend/sites/binding_service.py:232-234`; registrations are unfiltered,
   `sites/adapters/postgres_foundation_store.py:246-250`). Any later binding publish on that Site is then
   refused with `BINDING_GATEWAY_UNKNOWN`. That is harmless here, because tests convert first and register
   after, but a shared walkthrough DB that later edits KOBO-001 bindings would fail in a confusing way.
   **Fix:** add a line to `.agent/S7-01a-handoff.md` saying `register()` must run after the KOBO-001
   bindings exist, and that S7-01b should use a walkthrough DB of its own or accept that limit.
2. **Low (Architect confirmation) - the 5000 ms clock-trust tolerance is self-chosen and does two jobs.**
   It is set at `backend/assetops_backend/evidence/source_health.py:38`, decides `UNTRUSTED` and therefore
   fact `UNKNOWN` (`:161`), and is reused as the observed-after-receipt allowance (`:173`). The value is
   disclosed (`tolerance_ms`) and versioned under `rule_id ...two-clock.v1`, so this is not a correctness
   defect. It is still a product threshold that no decision records. **Fix:** ask the Architect to confirm or
   replace it, and record the value in the decision log, before S7-01b shows `UNTRUSTED` to the owner.
3. **Low (wording) - `NO_REGISTERED_SOURCE` is returned while the response lists a registered (disabled)
   gateway.** See `source_health.py:263-266`. The behaviour is right; the code name reads literally false next
   to `gateways[0].registration = DISABLED`. **Fix:** add `summary.reason` (for example
   `NO_ENABLED_GATEWAY`) or have the Architect note that "registered" in the decision means enabled. This
   does not block.
4. **Low - on the real clock, four more cases go STALE within 120 s and `deliver()` does not refresh them.**
   `s7_health_cases.py:192-200` refreshes only `s7-current` and `s7-delayed-old`. `s7-queue-growth`,
   `s7-clock-offset`, `s7-disk-stop` and `s7-disk-recovery` (60 s cadence) also show STALE contact in a
   walkthrough after about 2 minutes, yet the handoff table lists them as CURRENT and qualifies that only
   for the test clock. The read stays honest, but the owner would see the disk-recovery and clock cases
   behind a stale contact. **Fix:** let `deliver()` take keys (re-posting each case's last facts at the next
   sequence), or state the behaviour in the handoff.
5. **Low - signed ages are emitted from a clock the read itself marks untrusted.** For the `s7-clock-offset`
   case, `reported_facts.fact_age_seconds` (`source_health.py:245`) and `sources[].reported_contact_age_seconds`
   (`:214-215`) come out negative (about -85 s and -55 s), while `status` is `UNKNOWN` /
   `GATEWAY_CLOCK_UNTRUSTED`. A UI could render "-85 s old". **Fix:** null both ages when trust is
   `UNTRUSTED` (or when the observation is later than the receipt), or tell S7-01b in the handoff to suppress
   them.
6. **Low - the battery detail does not refuse a binding set that names a different Foundation revision.**
   `backend/assetops_backend/sites/battery_boundary.py:104-106` reports `BOUND` channels from
   `view.binding_set` without checking `binding_set.foundation_revision_id == view.revision.id`. The
   established basis read refuses that case as `BASIS_INCONSISTENT` (`sites/registered_basis.py:119-125`).
   S1's joint publish realigns binding sets in one transaction, so the mismatch can arise only from a race
   between the separate `revisions` and `binding_sets` reads in `FoundationService.read`. Condition stays
   `UNKNOWN` either way, so no condition claim results. **Fix:** return 409 `FOUNDATION_BASIS_UNAVAILABLE`
   (or `binding_status: BASIS_INCONSISTENT`) on a mismatch.

## Residual risk not named in the packet

- `summary.status = ALL_CURRENT` reflects contact only. With `s7-disk-stop` reporting STOP, a Site could
  still read `ALL_CURRENT`. S7-01b should label it as a contact summary, not as Site health.
- Disabled gateways still get a computed `contact.status` (a gateway disabled after receipts may show
  CURRENT). It is excluded from the counts. S7-01b should show the `registration` field next to it.
- Frontend suite, build and layout: not applicable (non-UI slice); nothing was claimed.
