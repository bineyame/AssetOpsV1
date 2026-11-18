# S4-03 phase 2 - fresh Claude review (`I-finding-evidence-ui`)

Reviewer: fresh Claude Reviewer. I did not author this phase. Date: 2026-10-13.
Branch `task/S4-03-finding-evidence-history`, HEAD `a0cb242`. Diff reviewed: `0131492..a0cb242`, five commits, 18 files.
I made no code edits.

## Verdict: RETURN (small fix round on the branch)

The Evidence child view is sound in its core:

- It reads the phase-1 read and nothing else.
- The positive lineage sentence is gated on `lineage.status == COMPLETE`. That status is computed over the whole cited set, not over one page.
- Unresolved rows are withheld rather than invented.
- Record and Dispatch links appear only when the read supplies their targets.
- An unknown pinned version is refused and the URL is kept.

Three things need fixing before acceptance:

- The legacy redirect can silently open the wrong Finding (M1).
- The view does not lead with a merged or closed Finding's status (M2).
- Raw `SIMULATED` appears on a product screen (M3).

One item needs an Architect or owner decision (M4).

## Checks I ran

The frontend suite and the build ran in this session. The usual sandbox esbuild failure did not occur.

| Check | Result |
| --- | --- |
| `npx.cmd vitest run` (frontend) | 59 files, 1412 tests passed |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npm.cmd run build` | exit 0, chunk-size warning only |
| `pytest backend/tests/test_s4_finding_evidence_history_api.py backend/tests/test_s4_finding_api.py -q` | 22 passed |
| `tools/check-all.ps1` | all 9 guards passed. Missing-claim scan: 1 tagged, 16 baselined (unchanged) |

What I did not run or verify:

- **Layout and browser evidence.** I did not rerun `tools/layout-evidence.mjs` or `tools/s4-finding-evidence.mjs`. No servers were started, and I made no visual check at 1440 or 390. The 68/68, 4/4 and 6/6 browser results, the overflow measurements and the API/row ID comparisons are the packet's claims and are unverified by me.
- **Envelope and row comparison.** I did not compare evidence ID to envelope hash/text against Postgres. That comparison belongs to the phase-2 reviewer in the task's table and is still owed, either in the fix-round re-review or in the owner walkthrough.

## Findings

### M1 - Must fix: the legacy Evidence tab can redirect silently to a Finding that does not cover the assessment

- **Where:** `frontend/src/sites/SiteFindingEvidence.tsx:703-727`. Backend: `finding_read.window_state`, which uses `findings_over` (`postgres_finding_store.py:418-430`).
- **What is wrong:**
  - The resolver reads every Finding whose latest episode overlaps the UTC day of `assessedWindow.start`. If there is exactly one, it redirects with `replace`.
  - It never checks that Finding's episode against the assessed window itself, although both are at hand (`assessedWindow`, `findings[].episode_start/episode_end`).
  - `findings_over` uses an inclusive `lo <= episode_end`. So a Finding that ends exactly at 00:00 of this day, from the previous day, counts as "on this day".
  - The resolver also ignores the window end, so a window that crosses midnight checks only its first day.
- **Example:** a T028 assessment for a 14:00-15:00 interval with no candidate. On a day whose only Finding is 10:00-11:00, the user is taken straight to that Finding's evidence.
- **Why it matters:** the target page says only "Latest version at the time of reading". Nothing tells the user it was reached by a day-level guess, so the wrong Finding opens silently. That is a misleading claim.
- **Fix (frontend only, cheap):**
  - Keep only Findings whose episode overlaps the assessed window with strict bounds: `episode_start < window.end && window.start < episode_end`.
  - Redirect only when exactly one such Finding remains. Otherwise show the existing choice or none state.
  - Add a test with one Finding on the day that does not overlap the assessed window, and one that only touches midnight.
- **For the Architect (Q1):** whether the auto-redirect should also say it was matched by period rather than by an exact assessment-to-Finding link. That is a wording decision, not a blocker once overlap is enforced.
- **"Latest version at read time" labelling:** the redirect target has no `revision_id`, and the Evidence view labels it as the latest at read time with a pin link. That is honest.

### M2 - Must fix: the Evidence view does not lead with a merged, closed or unconfirmed Finding's status

- **Where:** `SiteFindingEvidence.tsx:224-257` (`Selection`).
- **What is wrong:**
  - `body.revision.lifecycle` is in the read (`_summary`), but the view never renders it.
  - A MERGED, CLOSED or UNCONFIRMED Finding's Evidence page opens with "Latest version at the time of reading (version N)…". It does not say the Finding was joined into another Finding or is closed.
- **How you reach it:** directly from a merged Finding's root, or via the M1 redirect (`findings_over` returns MERGED Findings too).
- **Why it matters:** AC3 requires merged and closed states in plain language, and that non-current material leads with its non-current status. The earlier-version and closed-source cases are handled; the lifecycle case is not.
- **Fix:** a lead line driven by `revision.lifecycle` for the non-current lifecycles, reusing the S4-01 root's wording. It sits before the latest-at-read line and links back to the Finding root, where the merge and canonical links already live. Add a test with `lifecycle: "MERGED"`.

### M3 - Must fix: raw `SIMULATED` shown on a product screen under a `source-reference` exemption

- **Where:** `SiteFindingEvidence.tsx:313-315` (`Mode`), used at :358 (sources table) and :621 (selected record). The test pins this at `siteFindingEvidence.test.tsx:269`.
- **What is wrong:** the registered source mode is printed as the raw enum (`SIMULATED`) inside `data-vocabulary-exempt="source-reference"`.
- **Precedent:** existing product screens map the same field to plain words: `SiteEvidence.tsx:68` `provenance()` and `LedgerSiteEvidence.tsx:69` `sourceKind()`, giving "Demonstration data" or "Live data".
- **Why it matters:**
  - It breaks the owner's standing direction of no simulator language on product screens.
  - It uses the exemption for an enum rather than an identifier, which comes close to wording around the vocabulary guard.
- **Fix:**
  - Reuse the existing mapping (or move it into a shared helper).
  - Keep the exact code in a data attribute for tests.
  - Update the test assertion.

### M4 - Decision for the Architect or owner (record as a carry): mock coverage and use rows omitted rather than shown as missing

- **Where:** handoff "G-04 list". `finding-evidence:1` mock is at index.html:715-717.
- **What the app does:** it drops the mock's role summary (Input / Source / Coverage / Use) and shows the cited records and the by-source table instead.
- **Why it needs a decision:**
  - AC1 says absent roles and intervals are named gaps.
  - The owner's 2026-10-12 direction is that mock content without a source is shown in the UI as not available yet, not omitted, so that acceptance stays visibly conditional.
  - The AC4 omit-and-list default covers mock ActionEvent and recommendation content. Coverage and Use are part of core portion `finding-evidence:1#a` content, not ActionEvent or recommendation content.
  - A frontend role summary built from the paged records would be incomplete, so a real summary needs either a by-role aggregate in the read or a catalogued `<MissingClaim>` placement.
- **Why it is not counted as an Implementer defect:** the brief allowed the fail-closed omission, and nothing was reworded to dodge the scan.
- **Question to route:**
  - Option (a): a catalogued `<MissingClaim>` for "coverage and use per input" on finding-evidence:1, added in phase 3 or the fix round.
  - Option (b): a phase-3 by-role aggregate.
  - Option (c): accept the omission with a G-04 entry.
- **Same question for the tabs:** "Alternatives" and "Recommendation" in the Finding sections row are also omitted.

### L1 - Fix in the same round: "Possibly avoidable time" invents 0 on an unparsable value

- **Where:** `SiteFindingEvidence.tsx:331`, `durationText(minutes(...) ?? 0)`.
- **What is wrong:** a null or unparsable `candidate` (for example a `str(None)` from the backend) shows "0 min". That is a fabricated value.
- **Fix:** show "–" when `minutes()` returns null.

### L2 - Fix in the same round: the records table says "(does not match)" when the stored message is missing

- **Where:** `SiteFindingEvidence.tsx:518-519`.
- **What is wrong:** when the break is `ENVELOPE` (message missing), the fingerprint cell shows the recorded hash plus "(does not match)". That describes a mismatch, which is a different break. The "Record trail" column in the same row names the break correctly.
- **Fix:** pick the words by `ENVELOPE` versus `ENVELOPE_DIGEST`, as `RecordLineage` already does at :640.

### L3 - Carry: the frontend `LINK_WORDS` and backend `BROKEN_WORDS` keys are not held in parity by any test

- **Where:** `SiteFindingEvidence.tsx:69-82`.
- **Today:** the 12 frontend keys equal the 12 backend keys, so no banned word can reach the screen through the fallback.
- **Risk:** a new backend key would fall back silently to `lineage.words`. That text contains "envelope", "binding" and "cited_evidence_sha256".
  - In the per-record list, the vocabulary guard would catch it only in a test that renders that key.
  - `set_breaks` falls back further, to `b.detail`.
- **Fix:** a parity test, for example a backend test that writes the keys to a fixture the frontend test reads. Alternatively, Q2's option of rewording `BROKEN_WORDS` at the source.

### L4 - Carry (tooling): `drop` removes any non-default `--work` folder

- **Where:** `tools/s4_finding_walkthrough.py:83`, :275.
- **What is wrong:** `configure` refuses only the producer folder, `%LOCALAPPDATA%\AssetOps` and the repo. `drop` then calls `shutil.rmtree(WORK)` on any other non-default path, including one set through the environment variable. A mistyped `ASSETOPS_S4_WALK_WORK` (for example the home folder) would be deleted.
- **Fix:** require a marker file written by `prepare` before `rmtree`.

## Item-by-item answers to the dispatch

1. **Traceability.**
   - What is displayed: every displayed value comes from the read body. The page-scoped demo note says "on this page", which matches the page-scoped `_annotate`.
   - Positive "traces" sentence: shown only on COMPLETE. COMPLETE requires no broken record and no set break, and the cited-set digest is VERIFIED.
   - Unresolved rows show only the withheld sentence. Broken links are named.
   - Labels: closed source shows "Record only" first, earlier version shows the earlier-version notice first, and pinned latest is labelled correctly.
   - Refusals use plain language. "Reason given:" prints the backend message verbatim, including a 503's raw exception text. This is inherited from S4-01's `SiteFinding.tsx:158`; residual, not new.
   - Exception: lifecycle states are missing (M2).
2. **Legacy tab.** No second Evidence source remains; `FindingEvidence` is removed. It can send the user to the wrong Finding silently (M1). The latest-at-read labelling on the target is honest.
3. **Banned vocabulary.** None is reachable today: the frontend map covers every backend key. A future key would expose it (L3). Raw `SIMULATED` is a separate vocabulary issue (M3).
4. **AC4 / G-01.**
   - No new untagged phrase from the G-01 set (`not available yet`, `not yet available`, `no reviewed source`), confirmed by the scan.
   - The new "cannot be found", "Not linked" and "cannot be opened from here" strings are runtime data states, not capability gaps.
   - I found no wording changed to avoid the scan.
   - The `evidence_tab` placeholder was rendered nowhere in the frontend, so retiring it is clean.
   - The G-04 list is present. Its coverage of core content is a decision (M4).
5. **`primitives.css`.** Both new rules are scoped to `.site-finding-evidence`. A grep shows that class only on the new component's root (`SiteFindingEvidence.tsx:158`). `.site-finding` and other panels are unchanged, so there is no cross-screen effect, and no visual check was needed.
6. **Layout evidence "not run".**
   - Acceptable. `.ai/WORKFLOW.md` requires `not run` with the blocking precondition. The packet names it: `layout-evidence.mjs` uses site MG-001, which is absent from this store, creates Lab runs, and never visits the Finding Evidence path.
   - The task itself says "where its fixture supports the path".
   - The stand-in measurements in the S4 evidence script carry non-empty set counts (48/85/90).
   - The packet does not claim shell-wide coverage. The layout claim remains unverified by me.

## Carries

- C1 (phase 1) `ASSESSMENT_CITATION`: unchanged, as the packet states.
- M4: Architect/owner decision on coverage, use and role summary, and the Alternatives/Recommendation sections.
- Q1-Q3: open, with their defaults built. For Q1, also the period-match disclosure (see M1).
- L3: link-word parity test, or a backend rewording (Q2).
- L4: walkthrough `drop` guard.
- Residual: raw backend `message` text in refusal panels (inherited from S4-01).
- Residual: the WINDOW assessment row shows 0 cited records when segments cite only interval revisions. This is noted in the packet and is accurate.
- Residual: phase-2 Postgres row/envelope comparison by a reviewer is still owed (see Checks).
