# W5-03 EV depth

Status: planned, closed build contract in [`.agent/W5-03-build-spec.md`](../.agent/W5-03-build-spec.md). Lane A. Decision `D-2026-10-22-w5-01-w5-03-buildspec`.

## Purpose and order

Deliver v6.9 `availability`, `energy`, `ev-health`, and `ev-scenarios` for an authorized EV_CHARGING Site. Split at the backend pipeline/page cap:

| Merge | Result | Units | Migration | Predecessor |
| --- | --- | --- | --- | --- |
| W5-03a | Selected observed connector availability and energy/site-power pages | E1–E3 | None | W5-02 reviewed/merged at `0033` |
| W5-03b | Bounded EV Health and immutable authored financial scenarios | E4–E6 | `0034_w5_ev_scenarios`, `down_revision="0033_w5_cold_work"` (the required exact head produced by W5-02) | reviewed W5-03a and merged `0033` |

W5-02 owns the exact `0033_w5_cold_work` revision ID, and W5-03b must verify one parent and one head. W5-04 (`0035`) follows W5-03b. No W4-01 case-model change is authorized.

## Observable acceptance

- Availability has two independent facts: configured scheduled connector seconds and observed connector-state seconds. A session count, successful charge, fault event alone or configured schedule cannot fill the observed numerator. Report known available, known unavailable and unknown scheduled seconds separately, with the full-schedule bounds and known-time ratio only when denominators exist. Missing status history produces Unknown, never 100% availability.
- Energy uses the W2-06/07 selected complete and partial metering states, exact accepted evidence and time-valid import-limit Foundation. Observed peak below limit does not establish that the limit never bound service. Gross tariff scenario remains distinct from collections and lost sales.
- EV Health can show an observed fault-stopped session but cannot diagnose charger condition or vehicle cause. Connector 1 physical condition is Unknown even when sessions complete. Stationary battery is `Not applicable` only when the selected Foundation confirms none installed.
- EV financial scenarios are immutable authored revisions with no observed-outcome status. A scenario tariff or what-if does not alter measured energy or the W2-07 consequence head.
- Each new route preserves tenant/Site scope, selected UTC window and `known_at`; pending, stale, historical and unknown are different states. No private Lab truth is used.

## Review and completion

E1 and E5 require per-unit independent review because they touch the selected read seam, router/schema or shared navigation. E2–E4 and E6 are reviewed before their sub-slice merge. Each unit has its own tests and 1440/390 page captures in the build spec. Run `tools/check-all.ps1` after registry/navigation changes and one real-Postgres full suite per sub-slice outside active heavy builders. Drop private `*_test` DBs and stop processes started for captures. The readiness reviewer checks every visible literal, ID, destination, DTO and producer-backed state before dispatch. No implemented positive availability/health claim may be inferred from session count or configuration alone.
