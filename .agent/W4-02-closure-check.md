# W4-02 closure check (2026-10-20)

Checked at main `091aad9c` ("Merge plan/W4-02-closure"). Read-only. Inputs: `.agent/W4-02-spec-review.md` (33 questions), "Review closure (2026-10-20)" of `.agent/W4-02-build-spec.md` (cited `C:Qn`), `.agent/W4-02-mock-measurements.md`, `tasks/W4-02-mini-grid-depth.md`.

Result: 33 questions, 26 CLOSED, 7 OPEN, plus 5 new questions. W4-01 `0027` and the W3-01 `PublicProvenance` DTO are still unmerged (newest migration is `0026_w2_ev_money`), so seams that depend on them (Q18, Q23, Q26 header) are prerequisites, not verified.

## Per-item status

| Q | Status | Note |
| --- | --- | --- |
| 1 roles | CLOSED | Names, component types, units, enums and cardinality are given (C:Q1). `MINIGRID_ROLES_3` and `COLD_ROLES_1` are as cited. See N1 for the dispatch role-set registries. |
| 2 authored records | CLOSED | Null by decision: no citation of SUBMITTED records, fuel residual and test history null, with gap copy. |
| 3 job model | OPEN | The enqueue mechanism is not named. Domain values and worker separation are fixed (the existing lease query filters `domain = :d`, `assessment_store.py:320`). Still missing: a DB trigger like EV `0025` (new DDL, not in C:Q25's catalog deltas) or a change to the S2 evidence writer. Also missing: how "idempotent by hour" works (`recompute_job` has no unique key, so the advisory-lock `_coalesce_job` pattern or a new constraint), which hours a renewable job covers (all hours, or only the local 12:00 hour), and the "schedule installer" has no spec. |
| 4 windows | OPEN | Persisted unit and designated hour are fixed. Missing: whether card `used_kw` is a number (C:Q8 says measurements are number/null) or a `{low,high}` range (C:Q4 says used is summarized as min/max); how row `opportunity_kwh` is derived from hourly headroom kW. |
| 5 UTC vs local | CLOSED | Mapping rule, params and Dispatch-link rule are given. |
| 6 multi-selection | CLOSED | `windows[]`, integer `selection_id`, aggregate precedence and digest set are given. |
| 7 status/currentness | OPEN | Enums and copy are given. Missing: the source for "accepted source-health STALE" and for `basis.source_freshness` (C:Q15). No source-freshness read is defined for these domains, and the review noted W3-01's field is absent here. |
| 8 domain sub-shapes | OPEN | Most enums and code-to-copy tables are given. Missing: any renewable constraint code for a present-but-contraindicating fact (non-positive headroom, active charge obligation, critical-service deficit). The listed codes are all "missing" or conflict codes, so an EXCLUDED row (S:L41, S:L54) has no constraint text to render. |
| 9 PV capability | CLOSED | Channel plus three typed properties, with carrier component types. Property registration is in `sites/models.py` (`COMPONENT_PROPERTY_DEFINITIONS`, carrier map). `AC_BUS`, `INVERTER` exist. |
| 10 navigation | CLOSED | Capability declaration plus RENDERABLE, order and the site_type dispatch are given. |
| 11 refusals | CLOSED | Exact code and message pairs are given. |
| 12 cutover/mount | CLOSED | `build_mini_depth_router`, gate and access reuse are given. |
| 13 knowledge filter | CLOSED | Own query with `received_at` and `decided_at`; equality test required. The merged `_EVIDENCE` filters only `decided_at` (`:100-108`), as the review said. |
| 14 historical head | CLOSED | Predicate and digest reuse rule are given. |
| 15 basis/watermark | CLOSED | `result.basis` is frozen. `committed_watermark` is the latest disposition `decided_at` (NOT NULL column). Freshness input: see Q7. |
| 16 fuel quantity | OPEN | C:Q16 reuses `fuel_cost.py` bound semantics, but that model is `quantity_low = 0 L` and `high = 1.10 × …`, over Candidate time only (`fuel_cost.py:57-75`). It does not give a modelled `{low,high}` over all covered generator seconds. Also unstated: the source of "explicit bounded measurement uncertainty" for a tank reading (no property exists), so opening/closing are effectively always null. |
| 17 service calc | CLOSED | Mean, sum, interruption and unserved rules, and role label rule, are given. |
| 18 dual provenance | CLOSED | Three blocks, alias rule, adapter location. Depends on the W3-01 API being merged. |
| 19 renewable status | CLOSED | Placement, `Watch`, chip and link rules are given. |
| 20 subtitles/notes | CLOSED | Literals given. Nit: S:L53's body literal "Electrical capacity does not establish customer demand." and C:Q20's subtitle "Electrical feasibility…" overlap. Treat the body as `No productive-use scenario has been assessed.` only. |
| 21 drawers/CTA | CLOSED | Drawers are in scope with named content. |
| 22 backup tables | CLOSED | Step-to-row map, empty row and primitive reuse are given. |
| 23 Actions link | CLOSED | Global `actions` route or noninteractive `Actions unavailable`. Needs W3-01 merged. |
| 24 overview | OPEN | Reads, values and notes per status are given. Missing: the card value and note when a mini read returns 503 or fails (C:Q24 says only "no link"). |
| 25 registrations | CLOSED | Rule-8, probes, allowlists and head literals are named. Catalog counts are by snapshot. Trigger/index deltas depend on N2. |
| 26 migration literal | CLOSED | Header, jsonb shapes, lock order given. See N2 for the FK wording. |
| 27 fixture | OPEN | See N3: the positive fixture's source does not exist in the Lab model. |
| 28 phases | CLOSED | Seven units. The unmerged-seam rule is stated. |
| 29 panel paths | CLOSED | Registry paths, panelStructure assertion, nodes to close and `G-asset-battery-exposure` kept open. |
| 30 grid | CLOSED | 735/408, 4-up and 2x2. |
| 31 historical threshold | CLOSED | DB snapshot `read_time`; equality is current-eligible. |
| 32 test counts | CLOSED | Collected counts recorded at build time. See N5 for the "six-unit" typo. |
| 33 time/route tokens | CLOSED | Format and `siteId` versus `site_code` are given. |

## Checks requested

**Mock slots and honest gaps.** All kept in mock order, with gap copy for unsupported data. Renewable: status bar, 4 cards, headroom and evaluation panels, window table, notice, plus the two drawers. Service: status bar, cards, power, load table, supported and unlock panels. Fuel: status bar, cards, glance, bridge (5 fixed terms), notice, interpretation panel. Backup: status bar, cards, chains, readiness evidence, operating and next panels. Gap copy covers: `Delivery completeness unconfirmed`, `No accepted witnessed test record`, `Role not configured`, `Not assessed` (confidence), `Opportunity decision unavailable`, and the empty-chain row. No mock literal (42 kW, 200 L, 10 kW, $0.25) is retained. Not verifiable: whether the Lab can produce the data for the positive replay (N3).

**Budgets.** I recomputed all 48 heights as `ceil(mock + max(24, 10%))` from the measurements file. Every 1440 and 390 value in S:L71-74 matches, in rendered order. The row heights and the 390 table widths (379, 511, 719, 326) match the measurements. The scroll-width ceilings are 1425 and 390.

**Seam spot-checks against merged code.**
- Confirmed: `MINIGRID_ROLES_3` has no supply-loss, start-event or bus roles (those exist only in `COLD_ROLES_1`). `AC_BUS`, `INVERTER` and `FUEL_TANK` exist as component types (`sites/models.py:35-40`).
- Confirmed: `accepted_evidence.received_at` is NOT NULL; `asset_id`, `interval_start` and `interval_end` are nullable. `ingestion_disposition.decided_at` is NOT NULL. `recompute_job.cause_evidence_id` is nullable, and the dispatch path leaves it NULL (`assessment_store.py:799`). The closure does not rely on it.
- Confirmed: `analytic_run_selection.job_id` is a plain nullable `REFERENCES recompute_job(id)` (`0008:36`). `recompute_job` has no `(tenant_id, site_id, id)` unique key.
- Confirmed: `recompute_job_mutation` forbids changing identity and permits widening windows only while PENDING (`0005:349-365`). `_LIVE_JOBS` (`assessment_store.py:187`) is dispatch-specific, so a mini equivalent is needed (the closure does specify one).
- Contradicted or unspecified: the Lab mini-grid model profiles (`runs/profiles.py`) have no outage, start-request or bus-state publication (N3). `fuel_cost.py` low bound is 0 (Q16).

## New questions created by the closure

1. **N1 (dispatch role sets).** `analytics/assessment_worker.py:60` (`ROLES_BY_SET`) and `sites/binding_roles.py:296` (`roles_for`) register only minigrid roles 1 to 3. A KOBO-001 Site moved to `minigrid-roles-4` would fall out of Dispatch's role-set handling unless roles-4 is added there. Say whether roles-4 joins Dispatch and mapping-profile registries (`v4_mapping_profile`, `ROLES_BY_SET`), and that Dispatch results for the fixture Site are unchanged.
2. **N2 (selection `job_id` FK).** C:Q3 asks for a "scoped FK to `recompute_job`", but `recompute_job` has only `PK(id)` and C:Q25 forbids DDL on it. State a plain FK like `0008`, plus a writer-side tenant/Site check. Also say whether the enqueue trigger or functions are part of `0029` and counted in the catalog deltas (see Q3).
3. **N3 (positive fixture source).** C:Q27 requires publication v5 to carry storage-charge requested power, `site_supply_state`, `backup_bus_state` and a correlated start-request/result chain. The Lab mini-grid model (v4 at most) has no supply loss, start event, bus state or charge obligation. Decide: a new Lab mini-grid model version (large and out of scope), or an authored/registered fixture publication path (`authored_fixture_specs.py`). Name the file and the owner.
4. **N4 (renewable hours enqueued).** If every affected hour is enqueued per domain, `mini_renewable` jobs for non-noon hours are never read. Say whether renewable jobs are limited to the local 12:00 hour.
5. **N5 (consistency).** C:Q32 says "revised six-unit scope" but C:Q28 and the task have seven units. This is a wording fix.

## OPEN count: 7

OPEN: Q3 (enqueue mechanism, idempotency, schedule installer), Q4 (`used_kw` type, `opportunity_kwh` derivation), Q7 (source-freshness input), Q8 (no code for contraindicated renewable rows), Q16 (fuel bound vs `fuel_cost` low=0, tank uncertainty source), Q24 (overview card on 503), Q27 (positive-fixture source, N3).
