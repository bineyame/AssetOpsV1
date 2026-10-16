# S3-02b review packet: Evidence Analysis selected claim limit UI

Task `tasks/S3-02b-claim-limit-ui.md`; branch `task/S3-02b-claim-limit-ui` from main `8b5d8137` (S3-02a merged). USER_REVIEW_REQUIRED: true; owner walkthrough `.agent/S3-02b-owner-walkthrough.md` before merge or `#b` promotion. Diff: `git diff 8b5d8137..HEAD -- ':!.agent'`.

## Outcome

Evidence > Analysis has a new section, "What the selected assessment can support", beneath S2's own "How each limit is set" panel. It is on every Analysis view (ledger and legacy). The selection travels as `day=<YYYY-MM-DD>&revision=<assessment_revision_id>`. Without a day or revision the section says "No assessment selected" (UNASSESSED). With a revision it renders only the S3-02a read for that exact revision:
- a plain headline (a positive statement only when CURRENT);
- the five readings the conclusion needs, with covered minutes, gaps and per-reading accepted record links;
- "What limits it" in plain words;
- a link to the pinned revision in Performance > Dispatch;
- a closed "Technical details" disclosure with the rule, codes, revision/run/cohort, Foundation and binding IDs, source and analytic watermarks, `read_at`/`built_at` and every accepted Evidence ID as a drill-down link.

Every refusal is named on screen: 401, 403, 404 (Site and revision), 409 (closed gate and absent lineage), 422 (invalid id, outside the window, unsupported rule) and 503.

The presentation follows the owner direction of 2026-10-16. The opening paragraph is the v69 "How a claim limit is set" prose, and internals stay behind the disclosure.

## Files

- New:
  - `frontend/src/sites/claimLimitClient.ts`
  - `frontend/src/sites/EvidenceClaimLimit.tsx`
  - `frontend/src/sites/__tests__/evidenceClaimLimit.test.tsx`
  - `tools/s302_claim_limit_walkthrough.py`
- Changed:
  - `sites/LedgerSiteEvidence.tsx`: section after `ClaimLimit`
  - `sites/SiteEvidence.tsx`: legacy analysis view and `assessmentHref` prop
  - `sites/siteEvidenceClient.ts`: optional `claimLimit` client
  - `shell/SiteEvidenceFrame.tsx`: builds the Dispatch href, because sites may not import shell
  - `test/settled.ts`: two loading sentences
  - `ui/primitives.css`: `.claim-limit*`
- Closeout: task status, `tasks/README.md` row, `.ai/ACTIVE_CONTEXT.md`, `.ai/CODE_STATE.md` "S3-02b".
- No backend code, no migration and no writer.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| S2 explanation kept as its own section; S3 section on every Analysis view, UNASSESSED / "no assessment selected" without a revision | Met | Tests "sits beneath S2's own explanation…", "states 'No assessment selected'…", "reads the day without a revision…". Browser: `s2Before: true` in all 16 measured views. |
| Site, UTC day and exact revision in the URL; legacy `assessment` not reused | Met | Test "does not read the legacy `assessment` parameter"; keyboard/reload test |
| Echo the read basis and watermarks | Met | Technical details: run, model, cohort, knowledge cutoff, Foundation/binding IDs, four source watermarks, analytic/built/read times, day status and reasons, current selection |
| Ceiling only from a current S3-02a result; pending/failed/stale/historical/unassessed never positive; historical marked audit-only | Met | Tests for full / missing / poor-conflict / withdrawn / stale / withdrawn-window. Non-vacuous: mutating `data-ceiling` to show the historical ceiling failed 2 tests, then reverted. |
| Missing roles, poor quality, conflict, open bound, cohort/source/configuration limits named | Met | `reasonSentence` covers every S3-02a code. Missing, poor-quality and conflicting are proven on samples. OPEN_BOUND, COHORT and CONFIGURATION are vocabulary-only, because no sample carries them. |
| Every selected accepted ID links to exact Evidence drill-down and the pinned revision | Met | Test "links every selected accepted ID…": every `accepted_evidence_ids` entry and every role ID gets an href that keeps `record`, `day` and `revision`. In the browser the record opened, survived reload, and Back returned to the assessment. |
| Wrong Site/revision, unsupported rule and unavailable read are visible refusals | Met | Ten-case refusal test through the real client with stubbed fetch. Browser: the "revision from another day" link shows `refused`. |
| Stale response cancellation | Met | Test "drops a superseded selection's late answer": the first signal is aborted, and an out-of-order resolve does not overwrite the screen. |
| Keyboard selection and Back | Met | Unit test (links are native anchors, focusable, `aria-current`). Browser over CDP: Tab ×48 reached the 08:00–08:30 period link, Enter set `revision`, the state became CURRENT, and Back worked. |
| No physical capacity or gateway-contact substitution | Met | Only S3-02a fields are rendered; the not-inferred note is plain text, with the backend statement in the technical details |
| 1440/390 | Met (focused) | See Layout. `tools/layout-evidence.mjs` was not run (see Deviations). |
| Walkthrough `prepare/serve/late/attest/drop` | Met | Run end to end, see below |

## Checks run (final revision of the code; docs commit follows)

- `npx.cmd tsc --noEmit`: clean.
- Focused: `vitest run src/sites/__tests__/evidenceClaimLimit.test.tsx`: 28 passed.
- Full `npm.cmd test`: 69 files, 1639 passed and 1 failed. The failure was `siteFoundationChange.test.tsx` "shows old/new reserve…" at 3688 ms under full-suite load. The file passes alone (8/8), and this slice does not touch it. An earlier full sites+shell run showed the same kind of load flake once in `s404SiteFindingIndex.test.tsx`, which also passes alone (15/15).
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: valid.
- `tools/check-all.ps1`: all 9 guards passed (architecture, navigation, agent workflow, registry, delivery/mock-gap fixtures, missing-claim scan + fixtures, screen ledger).
- Backend full suite: not run, because no backend code changed (brief).

## Walkthrough (run once, end to end)

- `prepare` (`assetops_s302_owner1`, code `0090d858`):
  - builder: five cases;
  - Evidence comparison exit 0 ("Evidence cutover: permitted"), Performance comparison exit 0;
  - served route: six `ok` reads, and an unknown revision answered 404 `ASSESSMENT_REVISION_NOT_FOUND`.
- Served reads at 1440 and 390:

  | Case | Revision | Run | Cohort | Source accepted at |
  | --- | --- | --- | --- | --- |
  | Full | `4ef81a0f…` | `eeeee099…` | SELECTED_UNIQUE | 2026-10-30T08:00Z (source time 2026-10-06T08:35Z) |
  | Missing PV | `e8b2e183…` | `28cc3d76…` | | |
  | Poor/conflict | `83fdd277…` | `1880a168…` | | |
  | Late current | `8d8c5147…` | | | |
  | Withdrawn | `f76c0b25…` | | | |
  | Stale | `9320b3ba…` | | | |

- Accepted Evidence drill-down `50bf4821…` opened and survived reload; Back returned to the assessment.
- `late`: the 10-06 revision went CURRENT to STALE_PROJECTION on reload (headline "being redone", no ceiling).
- `attest` printed "ATTEST PASSED: both comparisons passed; 6 served reads match (after late)". Non-vacuous: with `gates.json` evidence `passed:false`, attest printed "ATTEST FAILED: comparison(s) did not pass: evidence" (restored afterwards).
- `drop` removed the database and the work folder.

## Layout

Focused CDP script (scratchpad, not committed). It covered 8 URLs × {1440, 390}, every one settled:
- `scrollWidth > innerWidth` was false in all 16;
- elements past the viewport outside a scroll region: 0 in all 16;
- the measured set is non-empty: 5 role rows and 41–51 accepted links on each loaded case;
- the readings table scrolls inside its own region at 390 (scroll width 314 against client width 309).

Mock `index.html#/evidence-analysis` was captured at 1440/390 for comparison. The mock has a single prose panel. The app keeps that prose and adds the selected-assessment content, with the Architect-decided S2/S3 split.

## Known deviations

1. `tools/layout-evidence.mjs` was not run. Its journeys need the registered Lab run store, which this private fixture database lacks. The focused CDP measurement above stands in for it.
2. Ports are API 8932 and web 5442, not 5432 (build brief). The task file is updated. Walkthrough URLs use `localhost`, because Vite does not answer on 127.0.0.1.
3. `late` leaves the recompute job outstanding (STALE_PROJECTION) instead of running the worker. A worker pass would also recompute the prepared stale-selection case. The withdrawn-to-HISTORICAL path is shown by the fixture's own late-revision case.
4. The packet's "Necessary" state has no ingested fixture (S3-02a gap). It is rendered from vocabulary only.

## Residual risk

- A CURRENT whole-day (WINDOW) revision's per-period list has no sample, and the walkthrough did not exercise it. It is covered by code only, plus the withdrawn-window sample for the earlier form.
- The per-role record links are labelled "Reading N". They are exact by ID, but carry no reading time.
- The full-suite load flakes named above predate this slice.

## User-review focus

- Is the headline wording right for Candidate, limited, Indeterminate and the audit-only states?
- Is the default reading free of internals?
- Does keyboard selection of a period feel natural?
- At 390, is the table scroll acceptable?

Wording polish belongs to W1 conclusion.
