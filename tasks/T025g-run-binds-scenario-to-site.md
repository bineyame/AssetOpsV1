# T025g - The run is the only join of scenario and site (S1)

Status: planned
USER_REVIEW_REQUIRED: true

Map: A/B hardening; scenario-site contract S1. Depends on: T025f. Next: T026.
Branch: task/T025g-run-binds-scenario-to-site
Sizing: beyond one focused change (contract move, parser, run setup, seven
shipped documents, two screens, about 16 test files); two phases below.
Planner: Claude under `D-2026-09-30-planner-claude-until-reset` (Planner bound
to Claude until the Codex reset 2026-10-03 21:23).

## Outcome

From the shipped `kobo-mini-grid-prolonged` v2, open run setup: no site is
selected and Create stays disabled until the user picks one. Picking a site
built from the current Kobo template gives a READY Draft; picking one built
from the pre-T025a Kobo content gives a BLOCKED Draft whose reasons name what
the site lacks. Neither site is named anywhere but the run, and the run detail
shows the site's template lineage.

Why now: no shipped scenario is runnable on a fresh checkout, and the owner's
workaround is an untracked copy naming a different site. T026's hands-on review
should not depend on it. Rule: `D-2026-10-01-run-binds-scenario-to-site`.

## Read for detail

- `D-2026-10-01-run-binds-scenario-to-site`; `.agent/scenario-site-targeting-architect.md`
  sections 2, 3, 4 (S1), 5 and 6. Do not re-derive its findings.
- `D-2026-09-22-contract-version-scope`, `D-2026-09-20-scenario-detail-affordances`
  (amended), the "one invalid document" backlog entry; `tasks/README.md` checks.

## Phases

A fresh Implementer per phase; each ends with committed work and
`.agent/T025g-phase-N-handoff.md` (what landed, anchors, next, open risks).

1. **Contract and backend (AC1-AC6).** Observable through the API and tests.
2. **Screens and proof (AC7-AC10)**, then full suites, browser evidence and
   the packet.

## Acceptance criteria

1. **Parser.** `target_site` is no longer required. A well-formed `target_site`
   is accepted as a legacy declaration and carried as such; a malformed one is
   still rejected, and every other key stays strict. An optional
   `site_contract.description` (prose, never evaluated) is accepted. No
   template hint field is added.
2. **Run setup.** The policy and `site_id` branches of
   `_refuse_unsupported_target` go, with `resolve_target_site` and
   `TARGET_RESOLUTION_STATES`; the no-topology refusal stays. Run setup ignores
   a legacy `target_site` entirely, never chooses or defaults a site, and
   rewrites neither document. The docstring states the new rule.
3. **Lineage frozen.** The run's site binding freezes the site's
   `template_id` and `template_version`, or null for a site with no template.
   Runs persisted before this slice read back as "not recorded", never
   inferred.
4. **Contract 10.** `EXECUTION_CONTRACT_VERSION` moves 9 -> 10 under
   `D-2026-09-22-contract-version-scope` (Architect section 6). Stored Drafts
   below 10 read back whole and are refused execution with the version named,
   as today. The kernel is unchanged: the contract-9 gate
   (`host/tests/contract9_gate`) still reproduces its results.
5. **Shipped scenarios v2.** All seven `config/scenarios` documents drop
   `target_site`, move to `scenario_version: 2` with `supersedes: 1` and a new
   `version_valid_from`, and may move the requirement prose into
   `site_contract.description`. A guard fails if a shipped document carries
   `target_site`, and a pinned fingerprint per `(scenario_id, scenario_version)`
   fails on changed content at an unchanged version (same mechanism as T025f).
6. **Join proof (fixtures, not `var/`).** In process, `kobo-mini-grid-prolonged`
   v2 with the shipped profiles reaches READY on a site built from the current
   Kobo template and BLOCKED on a site built from the pre-T025a Kobo content,
   with named reasons covering the missing generator property and status
   source. A legacy document with `target_site` naming site X sets up against
   site Y. A v1 request against the v2 store is refused by the existing
   version check.
7. **Picker.** `RunSetupFrame` stops deriving the site from the scenario. It
   opens with no site selected, never auto-selects (even with one site), keeps
   Create disabled until a site is picked, and lists each site with its
   Foundation version and template lineage, including T025f's staleness note.
   Blocked sites stay selectable.
8. **Scenario detail.** `Open target Site` is gone. The screen shows what the
   scenario needs of a site: the component addresses its causes act on, its
   observation sources (`device_id`/`signal_id`), the site controls it relies
   on, and `site_contract.description` when present. A legacy `target_site`
   shows as "Legacy site declaration; not used to bind runs". No compatibility
   or "sites that can honour this" list appears there (it needs a profile).
9. **Run readback.** Run detail and the Lab run header show the frozen
   template lineage, or "not recorded" for an older run.
10. **Catalog stays alive.** The owner's `var/scenarios` copies, which carry
    `target_site`, still parse; prove it with copies of their shape in a test,
    never by touching `var/`.

## Protected seams and proof

The scenario domain resolves no site; run setup is the only component that
holds a document and a site together. Compatibility is never computed by a
second matcher (T025h dry-runs the same resolution). Persisted runs and Lab
history are not re-resolved on read (`D-2026-09-30-lab-cockpit-history`).
Run the shared checks, all five suites (serially, per T025e's C9 note) and
populated layout evidence for run setup and scenario detail at the supported
widths, against an isolated or copied `var/` holding the two fixture sites.

## Scope limits, stops and review

Not here: picker compatibility status (T025h, after T026); purpose assumptions
(T025i). No edit to `var/` data (KOBO-001, GONDAR-01, `var/scenarios`, runs).
Stop and report if the legacy acceptance cannot keep the catalog alive without
editing `var/`, or if the contract reading proves wrong in review.

First review: a discovery review that also confirms the 9 -> 10 reading. Per
the owner on 2026-10-01 it does not wait for Codex: a fresh Claude reviewer
reviews when the slice is ready, and Codex reviews it retrospectively after its
reset (see `.ai/ROLE_CONFIG.md`). The owner then checks hands-on that the
shipped prolonged scenario runs READY on a current Kobo site and BLOCKS with
named reasons on an old one, with the site chosen only at setup.
Review outcome: pending.
