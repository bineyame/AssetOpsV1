# W4-02 closure check 2 (2026-10-20)

Read-only check of "Review closure 2" in `W4-02-build-spec.md` against `W4-02-closure-check.md`. Spot-checked against merged code: `assessment_worker.py:60` and `binding_roles.py:210/224` match the spec's description of role-set registration. `authored_fixture_specs.py` has a registry and the `conversions/` dir exists, so the authored-fixture path is real. `tools/schedule-install-gate.py` exists. `pg_advisory_xact_lock(hashtextextended(...))` is an established pattern. W4-01 `0027` and W3-01 provenance remain unmerged prerequisites, not verified.

| Item | Status | Note |
| --- | --- | --- |
| Q3 | CLOSED | Functions, trigger DDL, per-hour advisory-lock coalescing, noon-only renewable and the publication-writer hook are given. The schedule installer is wired to the existing gate. |
| Q4 | CLOSED | `used_kw` is `{low,high}`; `opportunity_kwh` is headroom kW x 1 h, null when LIMITED, CONFLICT or EXCLUDED. |
| Q7 | CLOSED | Source-health dropped. `source_freshness` is an evidence-basis comparison (CURRENT/STALE/UNKNOWN) with an explicit rule. |
| Q8 | CLOSED | Three new codes plus a full code-to-copy table. EXCLUDED precedence is stated. |
| Q16 | CLOSED | Zero-to-1.10x nominal over covered generator intervals, the copy is given, tank open/close null with a stated reason. |
| Q24 | CLOSED | Value `Unavailable` and a note on 503, transport or malformed failure, no link, other cards independent. |
| Q27 | CLOSED | Authored fixture path chosen. Files, registry key and owner are named, with a stated fallback when Batch V2 cannot express the events. |
| N1 | CLOSED | roles-4 is added to both registries, Dispatch is unchanged, and an equivalence test is required. |
| N2 | CLOSED | Plain FK plus a writer-side lock and check. Functions and trigger are counted in the catalog deltas. |
| N3 | CLOSED | Same as Q27. |
| N4 | CLOSED | Renewable jobs are limited to the local 12:00 hour. |
| N5 | CLOSED | Seven units everywhere. |

OPEN count: 0 of 12.

## New questions created (all Low, none blocking)
1. The trigger fires on every `accepted_evidence` insert and filters only by role name. Several role names may also occur on non-mini Sites (for example EV or cold). State that `mini_enqueue_accepted` returns early unless the Site is a mini-grid type or has a roles-4 binding.
2. The trigger requires a matching `ingestion_disposition` row at deferred-fire time. Confirm in the build that the gateway writes the accepted and disposition rows in one transaction. The spec's "missing disposition enqueues nothing" would otherwise silently drop jobs, and no repair path is named except manual `reconcile`.
3. The Q3 trigger role list is not checked here against the roles-4 role literals. Add a unit test that the trigger's list equals the `MINIGRID_ROLES_4` role names minus `battery_reserve`.
