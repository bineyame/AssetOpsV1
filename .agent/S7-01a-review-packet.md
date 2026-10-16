# S7-01a review packet - Site source-health and battery boundary reads

Task `tasks/S7-01a-health-read.md`; branch `task/S7-01a-health-read` from main `8b5d8137`. Non-UI;
USER_REVIEW_REQUIRED false (mergeable after fresh independent review). Reviewer diff:
`git diff 8b5d8137..HEAD -- ':!.agent'`. S7-01b contract: `.agent/S7-01a-handoff.md`.

## Outcome

- `D-edge-health-cases` fixture (`backend/tests/s7_health_cases.py`): one gateway per case on KOBO-001,
  credentials from the provisioning CLI, every diagnostic through the authenticated central path; six
  central cases plus never-received, a second Site with no enabled source, and wrong-Site refusal.
- Versioned two-clock read `GET /api/sites/{code}/source-health` (schema `assetops.site-source-health` v1):
  server-receipt contact separate from reported-fact age/clock trust; registration and latest diagnostic per
  gateway in one REPEATABLE READ transaction; inconsistent selection 409, store failure 503. S2
  `gateway-health` unchanged.
- Battery boundary `GET /api/sites/{code}/battery` and `/assets/{asset_id}/battery` (schema
  `assetops.asset-boundary` v1): effective Foundation/binding-set IDs, physical condition `UNKNOWN` with named
  missing causal inputs, or `NOT_CONFIGURED`; foreign/unknown/non-battery asset 404.

## Files

- `backend/assetops_backend/evidence/source_health.py` (new): snapshot types, `check_consistent`, DTO.
- `backend/assetops_backend/evidence/adapters/postgres_gateway_access.py`: read-only `source_health_snapshot`.
- `backend/assetops_backend/source_health_api.py`, `asset_boundary_api.py` (new routes); `main.py` wiring.
- `backend/assetops_backend/sites/battery_boundary.py` (new).
- `backend/tests/s7_health_cases.py`, `test_s7_source_health_postgres.py`, `test_s7_asset_boundary_postgres.py` (new).

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Six central cases via registered gateway auth + central ingestion; never received; wrong Site | Met | `test_six_cases_never_received_and_reload`, `test_no_registered_source_and_wrong_site` (KOBO-001 gateway naming KOBO-002 is 403, no row) |
| ID, sequence, server/reported times, reload | Met | same test: receipts vs read vs stored rows; second read identical |
| Contact `CURRENT/STALE/UNKNOWN` distinct from fact age/trust; fresh receipt of old facts | Met | `s7-delayed-old` CURRENT contact / OLD facts; `s7-clock-offset` UNTRUSTED -> facts UNKNOWN |
| `NO_REGISTERED_SOURCE` / never received `UNKNOWN` | Met | KOBO-002 summary; `s7-never-received` |
| Stale contact does not date outage; queue/disk last reported | Met | reason `NO_RECEIPT_WITHIN_THRESHOLD_OUTAGE_START_NOT_DATED`; `as: LAST_REPORTED` |
| Gateway contact never proves source contact | Met | per-source `reported_contact_status`, `NOT_IN_SELECTED_DIAGNOSTIC`; `not_claimed: DEVICE_CONNECTED` |
| Store failure / inconsistent selection cannot yield a current claim | Met | `test_store_failure_is_503_without_a_claim`, `test_inconsistent_selection_is_refused` (5 doctored snapshots + future receipt, route 409) |
| One repeatable-read snapshot | Met | `test_registration_and_diagnostics_share_one_snapshot` (diagnostic committed mid-transaction not selected) |
| `STALE_PROJECTION` | Not applicable (no derived projection), recorded in DTO `stale_projection.applicable=false` | |
| No join to accepted measurements | Met | no evidence table read in either read |
| Battery: effective basis IDs, `UNKNOWN` with missing causal inputs | Met | `test_configured_battery_is_unknown_with_missing_causal_inputs_and_pinned_ids` (IDs pinned after reload) |
| Unbound/absent battery `NOT_CONFIGURED`/Unknown reason | Met | `test_configured_but_unbound_battery` (`NO_BINDING_SET`), `test_absent_battery_is_not_configured_without_an_asset_id` |
| SOC/nameplate separate labels; withheld claims | Met (nameplate `DECLARED_FOUNDATION_RATING`; SOC value not selected, only bound channel ID) | |
| 401/403/404; foreign asset never an empty healthy row | Met | `test_identity_seam*`, `test_wrong_asset_and_wrong_site_are_refused` |
| Composition | Met | `TestComposition::test_create_app_serves_both_s7_reads` |

## Checks

- Focused: `test_s7_source_health_postgres.py` 8 passed; `test_s7_asset_boundary_postgres.py` 6 passed.
- Fail-closed mutations (each reverted with `git checkout`): drop the receipt-after-read check -> inconsistent
  test fails; `READ COMMITTED` isolation -> 5 of 8 fail (incl. snapshot race); battery selection accepting any
  asset -> 5 of 6 fail.
- `python tools/writer_guard_probes.py --seam`: exit 0, all probes CAUGHT/ALLOWED as expected, tree restored.
  The only writer-module change is a read method (no INSERT/UPDATE); fixture SQL is in `backend/tests` only.
- `tools/check-all.ps1`: All 9 guards passed (rev `c0bc25e1`). Registry checker: "Registry valid: 234 nodes".
- Full backend suite, rev `c0bc25e1`, PowerShell-equivalent `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml=<abs>` on private `assetops_s701a_test`, keep-awake running: **2449 passed, wall 1284 s (21:22)**; JUnit tests=2449 failures=0 errors=0 skipped=0. An earlier run on the same revision (2444 passed, 5 failed in `test_s4_finding_index_postgres.py`/`test_s4_finding_store_postgres.py`) failed only with `FATAL: sorry, too many clients already` while another worktree's pytest ran concurrently; rerun after it finished was clean. Base DB dropped afterwards.

## Known deviations

- Fixture SQL registers the eight case gateways/sources directly (an import makes exactly one gateway per
  Site); they are inserted DISABLED and enabled only through the provisioning CLI.
- `NO_REGISTERED_SOURCE` means no ENABLED gateway: every imported Site has its disabled import gateway, which
  is listed with `registration: DISABLED`.
- Clock trust tolerance 5000 ms is a W1 choice in `source_health.py` (`CLOCK_TRUST_TOLERANCE_MS`).
- No superseded-revision battery test (no Foundation revision writer exercised); selection is by effective
  revision components, so such an asset falls to 404 by construction.
- Accepted SOC values are not selected (optional in the packet).

## Residual risk / review focus

- `check_consistent` parses each selected diagnostic text on every read (bounded: one per gateway).
- Walkthrough (S7-01b) runs on the real clock: `s7-stale-cadence` (30 s cadence) is STALE 60 s after publish.
- Migration: none, so S6-02a `0019_verification_core` does not interact.
