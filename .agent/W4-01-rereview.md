# W4-01 re-review after fix round r1 (head fd64ebdd)

## Verdict: ACCEPT (no High, no Medium findings)

Read through git only (`afa35e79..fd64ebdd`, `git show`, `git diff main fd64ebdd`). I did not run tests, the guards,
tsc or the build in this pass, so the packet's numbers (check-all 10/10, tsc 0, 13+15 backend, frontend 2365) are
unverified by me. The merge also still needs the same-revision full backend suite (r1 ruling M5).

## Closure of r1 findings (as ruled)
- H1 closed. `WorkSubrow` + `useWorkCounts` render `Label (n)` from each list's `total_count` (limit=1, no cursor
  or known_at, same Site/window), a dash for pending/error/non-finite/no window, and clear on key change.
  `work_subtab_counts` asserts all of that. The capture shows `Actions (0) Incidents (0) Maintenance (0)` in one
  36px subrow, matching the mock's one subrow and `(n)` form.
- H2 closed. `<RailIcon name="evidence"/>` sits in an aria-hidden wrapper, and tests assert it on a zero count and
  not on refusal. The empty capture matches the mock's document icon, heading and text.
- H3 closed. CURRENT shows no word. Qualifiers sit inside the detail span, so there are 3 spans and no
  `.status-strip__state`. The empty capture shows lead, detail and Manage only.
- M1 kept per ruling and asserted: the same `known_at` is sent on Next/Previous.
- M2 closed. `w401-work.json` is added and replayed in the service test.
- M3 closed. The coverage sentences are replaced as ruled. `Reading work records`, `As of: time not recorded` and
  both `Showing` forms are asserted.
- M4 closed. The listed assertions were added or confirmed, in the backend test nodes the ruling named.
- q8-1 closed. The `WORK_MANAGE_UNAVAILABLE_STATUS` const and exactly two `REVIEWED_EXEMPTIONS` entries are
  present, and the baseline is untouched. The orphan scan and its self-check are only claimed (check-all 10/10).
- q8-2 closed. Both `registry.panels` entries are `status:gap` with the ruled `requires`. Both ledger rows carry
  `P-work-cases`, the ruled node order and `task:W4-01`. Tier and approval are not changed. `remaining_work` names
  the missing global controls and the owner tier decision.
- M5 closed. `git diff main fd64ebdd` over money code shows only `financials/composition.py`
  (`build_source_provenance` to `build_public_provenance`) and one added column, `r.finding_revision_id`, in
  `_EV_REVISION_SQL`. `select_consequence_on`/`for_finding_on` are gone (`git grep` finds none), and the money
  test module is deleted. The shared provenance port and the one column it reads are the reviewed shared port that
  q3 ruling 6 permits (it forbids only "the W3 money prerequisites or unreviewed estate core"). Neither is a money
  prerequisite. The wider diff against main in the assessment and finding stores is the reviewed shared W3
  assessment port (not money), which r1 M5 said to preserve.

## Fixer's open points
1. Extra ledger fields (`coverage:bounded`, `follow_on:null`, `to_candidate:null`): acceptable. The checker forces
   them for an S-task screen, and `bounded` is the honest value for a built bounded slice. They are not tier
   approval. No Architect needed. A one-line confirm in the next ruling is optional.
2. Action-link null-href on missing lineage, not reproduced: acceptable residual (Low). The Finding null href is
   asserted, and the Action pinned-event href and label are asserted. Record it as residual risk in the merge
   note. No Architect needed.
3. `WorkSubrow` assertions only in `siteWorkCases.test.tsx`: acceptable. That test mounts the real App on all
   three routes (Actions, Incidents, Maintenance), and the capture script re-checks counts. No Architect needed.

## Residual (Low, unchanged from r1)
L1-L6 from the first review are untouched by the ruling. L4 (raw vocabulary in the "based on" disclosure) and L5
(every KOBO mini-grid pin lists UNKNOWN) go to the owner walkthrough. L6: layout-evidence.mjs is still not
recorded as `not run`; the bespoke capture script covers it.
