# S6-02b re-review: truth fixes F1, F3, F5 (D-2026-10-16-s602-closure)

Reviewer: fresh Claude reviewer, independent of the implementer. Branch `fix/S6-02b-truth` at `88d842fb`.
Diff reviewed: `git diff 364d7bbe..88d842fb`, which is frontend only (`SiteActionVerification.tsx`,
`verificationWords.ts`, the focused test file, and the packet).

## Verdict: ACCEPT

There are no High or Medium findings. All three Architect-required fixes are met, and the changes add no fail-open
path. The three Lows below do not block.

## F1: met

- On the Plan and Evidence views, any explicit selection (`outcome_id`, `plan_id`, `recorded_at`, `event_id`) now
  triggers a separate `/verification/history` read (`SiteActionVerification.tsx:196,200`). Its `current_state` is
  shown as "Actual current state" beside the selected state (`:394-402`). The `explicitSel` predicate (`:162`)
  matches `explicit` (`:218`).
- A historical VERIFIED cannot be read as current. Once the selection is explicit on these views, the strip is always
  labelled "State at the selected time" (`atCutoff`, `:365`). The banner covers three cases: the actual state is
  shown below, the actual state is being read and must not be treated as current, or the actual state could not be
  read and the historical state must not be treated as current (`:377-383`).
- A failed read is stated, not hidden. `read()` → `exchange()` (`actionClient.ts:461-484`) never rejects, because a
  network failure becomes a refusal. A failed history read therefore sets `currentHistory`, which leaves `actual`
  null and sets `actualMissing`. The banner then says the state "could not be read", and
  `data-verification-actual-current-unavailable` is rendered. The `active` guard in `set` stops a stale read from
  writing after the selection changes.
- Tests cover a historical VERIFIED beside a current INCONCLUSIVE for both Evidence and Plan, plus an unreadable
  history case.

## F5: met

The `sourceWords` default is now "Source not recognised (treated as unverified)" (`verificationWords.ts:222`). All
three call sites (`:627`, `:1122`, `:1248`) go through this function, and no other mapping produces "Field
readings". The source-pair PASS/FAIL comes from the backend `pair.state`, not from this label, so an unrecognised
value cannot pass that row in the UI.

## F3: met

- **Default reading.** Each window has a plain summary of assessed days, distinct registered sources, assessments
  and source records (`:1230-1236`, `:1318-1320`).
- **Dig deeper.** It shows:
  - the origin FindingRevision ID;
  - the selected assessment revision IDs, from `target.<window>.assessment_revision_ids`, which the backend sets in
    `verification_rules.py:644`;
  - the source records;
  - a per-day table with cohort status, cohort digest, run ID, model version, input digest and configuration digest.

  All of these fields exist on the wire (`_selection_pin`, `verification.py:93-100`).
- **Later-window binding is correct.** The backend evidence read (`verification.py:541-561`) takes
  `bindings[-1]` among the bindings recorded at or before `known_at`, and reports that binding's ID as
  `later_selection_binding_id`. The frontend reads the plan by exact ID with no cutoff, so it receives every
  binding. It filters to `recorded_at <= knowledge_cutoff` and selects the binding by that exact ID
  (`:1091-1094`). Both timestamps are UTC `isoformat` strings produced by `_wire`, so the string comparison agrees
  with the backend. The days shown are therefore those of the binding the target was computed from. For a pinned
  outcome, the lineage plan is read from `evidence.plan_id` (`:205`), which is correct.
- Baseline days come from `plan.baseline_selection.days`, the same frozen selection whose `target` the backend
  returns.

## Fail-open check

No new fail-open path.
- An absent or failed history read never shows a current state, and the screen says so.
- An absent or failed lineage plan read shows no days or IDs, and the summary says the plan could not be read.
- An unknown source value now reads as unrecognised.

## Findings (all Low, non-blocking)

**L1 (Low). `SiteActionVerification.tsx:1231` with `:205-207`.** While the lineage plan read is still in flight,
`planRead` is false, so for a moment the summary says the plan "could not be read". The same sentence appears on a
real refusal, which is also not shown as a typed refusal. This message is transient, it errs toward stating a
problem, and it claims nothing false about the evidence. *Fix:* keep the read result, and give the summary
separate "being read" and "could not be read" sentences, as the F1 banner already does.

**L2 (Low). `SiteActionVerification.tsx:1093-1094`.** The fallback
`?? bindings[bindings.length - 1]` is used when `later_selection_binding_id` is null or is not among the filtered
bindings. Given the backend semantics above, this fallback cannot be reached today. If it ever were reached, it
would show days from a binding the target was not computed from. *Fix:* if the ID is null, show the window as
unbound. If the ID is not found, state that rather than guessing.

**L3 (Low, conservative).** On the Plan view with an exact `plan_id` and no cutoff, the backend's
`verification_state` is the real current state (`at=None`). It is still labelled "State at the selected time". The
same value appears beside it as "Actual current state", so nothing is misrepresented. This only matters for
precision.

## Checks I ran (`88d842fb`, worktree `AssetOpsV1-gap-planning`)

- `npx.cmd tsc --noEmit` (frontend): exit 0, no errors.
- `npx.cmd vitest run src/sites/__tests__/siteActionVerification.test.tsx`: 1 file, 18/18 passed, 9.5 s. This
  includes the 4 new fix-round tests. React Router warnings were printed to stderr but caused no failures.

## Not verified

- I did not rerun the full `npm test`, the production build, or browser and layout evidence. The packet reports one
  unrelated full-suite failure under load (S4-04), which passed when rerun alone. I have not reproduced that.
- The owner visual walkthrough is still outstanding, and S6-02b stays held for it.
