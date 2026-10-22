# W6-01 Global work cases

Status: **specified, readiness closure pending browser measurements and independent review before build**. Lane B. Architect/Planner decision `D-2026-10-22-w6-01-buildspec`. The sole implementation contract is [the build spec](../.agent/W6-01-build-spec.md). No W4-01 model change is authorized.

## Outcome and order

| Merge order | Slice and owned v6.9 screens | Observable closeout | Units |
| --- | --- | --- | --- |
| 1 | W6-01a global Incidents: `incidents` | Scoped, paginated cross-Site case list, exact Site/detail links, persisted positive and watermarked zero | A1 read, A2 page |
| 2 | W6-01b global Maintenance: `maintenance`, `maintenance-preventive` | Corrective and DRAFT preventive lists with truthful verification/due limits | B1 read, B2 corrective page, B3 preventive page |
| 3 | W6-01c request overview and record: `wr-overview`, `wr-record` | Reloadable exact request and performed records | C1 read, C2 overview, C3 record |
| 4 | W6-01d request history: `wr-history` | Ordered authored events and correction history on the reviewed C1 read | C4 history |
| 5 | W6-01e Operational records: `oprecords` | Scoped authored-record list, correction lineage and read-only manual-entry gap | E1 read, E2 page |

Each row is an independently reviewable task branch (`task/W6-01a-global-incidents` through `task/W6-01e-operational-records`). Each subsequent row consumes reviewed and merged predecessors. A read/backend unit plus at most two new pages stays within the W5/W6 size cap. The seven manifest screens retain their mock hierarchy with honest missing states; Site W4 lists and W1 Actions remain separately owned.

## Boundaries and acceptance

- Use merged `work_case`, `work_case_revision`, `work_event`, `maintenance_record`, `maintenance_plan`, and `operational_record`. Case codes and states come from `work/model.py`; no fixed mock ID, inferred incident cause, implied verification, accepted telemetry, automatic due calculation, or asset warranty claim.
- Principal-derived tenant and authorized Site set; SQL tenant/Site/Asset joins and exact selected revision/event IDs. One cutoff and repeatable-read snapshot per page; cursors bind the complete selected set and access basis. Refusals never become zero counts.
- A correction is a new immutable version; current and explicit historical selections are labelled separately. `COMPLETE` means performed activity only. `CLOSED` is an incident case state, not verified outcome. Preventive plan `DRAFT` is not an active schedule. Operational record `SUBMITTED` is not accepted evidence.
- Match every owned mock panel/column/chip or show the literal gap in the build spec; desktop 1440 and narrow 390 captures include long content and failure states. Capture the page in its owning unit. No new rail destination before a truthful route passes navigation and registry checks.
- W6-01 uses no DDL: reservation `0036` is recorded unused. Current merged Alembic head is `0030_w4_mini_decisions`; the spec does not create a second head. If a future unit proves DDL necessary, stop for an Architect amendment with literal migration, predecessor head and downgrade, before build.

## Review and gate

Per-unit independent review applies to every backend/shared-shell unit. A fresh implementer dry-read against merged main must close copy, wire, routes, fixtures and measured 1440/390 heights before A1 starts. Focused backend/frontend tests and `tools/check-all.ps1` run on the exact implementation revision; one full backend suite per slice after its units, serialized with other lanes. Owner visual review follows independent acceptance. `W6-01a` can begin after the W4 contract freeze and readiness gate; W5 delivery is not a product dependency.
