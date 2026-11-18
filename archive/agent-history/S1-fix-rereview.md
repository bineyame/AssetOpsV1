# S1 fix-round re-review (S1-03 review findings + S1-02 n6)

- **Reviewer:** a fresh Claude Reviewer (Opus). I did not write any of this code and did not do any earlier S1 review. I edited no tracked file and made no commit, push or merge. This file is my only write to the repo.
- **Reviewed:** `98a255b..149f7c0` on `task/S1-03-foundation-organization`:
  - the n6 commits `6a952ae` and `ff88ed8`;
  - the S1-03 fix commits `7e00b0c`, `776ccd7`, `7ba1ac4`, `70b7588`, `e6d097a` and `8598c58`;
  - the closeout commit `149f7c0`.
- **Authority:**
  - `.agent/architect-S1-03-questions-2026-10-08.md` (Q1-Q4 and n6);
  - `.agent/S1-03-review.md` (M1, M2, m1-m5);
  - the n6 section of `.agent/S1-02-fix-rereview.md`.

  I treated the "Fix round" section of `.agent/S1-03-review-packet.md` as claims to verify, not as findings.

## Verdict

**Changes required, narrowly: one fix, or an explicit Architect waiver of it.**

- **The rest of the fix round:** acceptable with the carries listed below.
- **Major finding R1:** the n6 implementation does not stop at a later independent, explicitly published binding change when that change has the same content as the set being edited. Instead it supersedes that change and reports the edit as having no end.
  - The fix is small and contained to the carry-through loop in `binding_service.py`.
  - If the Architect accepts the content-equality rule as written, R1 becomes a carry and the verdict becomes **accept with carries**.

## Checks I ran (what I saw)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | Passed |
| `tools/check-agent-workflow.ps1` | Passed |
| `pytest backend/tests -q` with `ASSETOPS_TEST_DATABASE_URL=.../assetops_test` | **1575 passed**, 0 skipped (4m21s) |
| `npx.cmd tsc --noEmit` | Clean |
| `npm.cmd test` | **Ran on this machine; the known sandbox failure did not occur.** 49 files, **1182 passed**. |
| `npm.cmd run build` | Built; only the existing chunk-size warning |
| `tools/layout-evidence.mjs` | Not rerun (needs Chrome plus servers). The packet records it honestly. `.agent/S1-03-fix-layout-evidence.txt` exists, with 200 PASS / 0 FAIL on the Site views at 1280/1000/640/390. It ends in an explicit abort at Lab run-setup (line 247), recorded as an abort, not as a pass. |

**Probe environment**
- All probes ran in a detached scratch worktree, `C:\Users\assef\Bineyame\AssetOpsV1-rr-probe`, with `node_modules` junctioned in. The worktree is now removed, the junction was removed first, and `git worktree list` shows only the main checkout.
- The Postgres probes used `assetops_test` only. The test fixture truncates its tables, and my probe rows remain there until the next test run. I did not touch the dev DB `assetops`.
- I started no servers. The running node/uvicorn processes (:5183, :5199, :5213, :8000, :8010) predate this review and were left alone.
- Python probes need `PYTHONPATH=<worktree>\backend`. Without it, the venv imports the main checkout's package and every mutant "passes". I caught this and reran.
- Frontend tests that use `toBeInTheDocument` fail in a junctioned worktree with "Invalid Chai property". That is a probe-environment artifact: the same test passes alone and in its file in the main checkout. The order mutants do not depend on that matcher.

## Item status

| # | Item | Status |
|---|---|---|
| 1 | n6: binding edit through Foundation splits | **Partially closed** (R1) |
| 2 | M1: "needs an imported Site" only for `migration_required` | **Closed** |
| 3 | M2(a): guard bypasses | **Closed** for the three original bypasses; one residual gap (R2, minor) |
| 4 | M2(b): panel order pinned | **Closed** for the reviewed mutations; one unpinned panel (R3, minor) |
| 5 | Q1: narrow rules scoped to `app-frame--operator`; Lab unchanged; guard | **Closed**; guard form limits (n2) |
| 6 | Q4, m2, m3 | **Closed** |
| 7 | Regressions in S1-01/S1-02 | **None found** |

### 1. n6

What I verified:

- **Fix fixture: holds.** `binding_service.py:447-460` carries the edit through contiguous current periods with the same `binding_set_id` and an equal `bindings_sha256`.
  - The 10-04 removal with a 10-05 reserve split is absent at 10-04T12, 10-05 and 12-01, and present at 10-03.
  - I reproduced this **on Postgres** (`assetops_test`, my probe). No Postgres test on the branch covers n6, and the exclusion constraints and immutability triggers accepted the plan.
- **Atomicity: yes.**
  - `publish_configuration` (`postgres_foundation_store.py:607-657`) runs the planner inside one `engine.begin()` transaction after `SELECT ... FOR UPDATE` on the Site.
  - There is no retry, so the closure's `holder` dict cannot carry stale `stopped_by` from an earlier attempt.
- **Validation and alignment: correct.**
  - `period_to` is extended before `overlapping` is computed (`:531`), so `validate_bindings` runs against every Foundation period the extended edit covers.
  - Joint `declare` also uses the extended `period_to`.
  - `finalize` (`binding_alignment.py:216-236`) splits the draft into one row per Foundation period, each with its own pinned snapshot bytes.
  - The in-memory test asserts two rows with distinct snapshot hashes after 10-04. On Postgres, every snapshot download I made verified its bytes against the stored SHA-256.
- **Earlier `knowledge_at`: recovers the old set.** The snapshot hash equals the pre-change hash, and SOC is present at 10-06. Confirmed in memory (branch test) and on Postgres (my probe).
- **Stop at an independent later change with different content: works.**
  - `applies_until` = 10-08 and `stopped_by_binding_version` = that version; the independent change is left intact.
  - Confirmed on Postgres.
- **201 fields and UI: correct.**
  - The fields are added at `foundation_api.py:608-609`.
  - The client defaults to `null` (`siteFoundationClient.ts:409-415`).
  - The form says "with no end" or "only until X, where binding vN (a later, separately published change) takes over" (`FoundationBindingsPanel.tsx:354-366`).
  - A UI test covers both messages.
- **Mutation probes (mine, reverted), all caught by `TestBindingEditThroughFoundationSplits`:**
  - loop disabled: 3/3 fail;
  - stop-on-different-content removed: 1 fails;
  - `applies_until` forced to None: 1 fails;
  - `stopped_by` not recorded: 1 fails;
  - carried periods not superseded: 3/3 fail.

**The deviation (content equality instead of split lineage) is a defect; see R1.**

### 2. M1: closed

- `SiteFoundationFrame.tsx:139-163`: `unavailable`, `not_found` and `invalid` (without `at`) now render "Stored versions unavailable" with the message and a link back.
- The "This view needs an imported Site" branch (`:165`) is now reachable only for `migration_required`, because `loaded` returns earlier.
- The new test covers 4 statuses × SLD and Readiness. Legacy Sites keep the named panel ruled in Q2.

### 3. M2(a): guard bypasses

I retried each bypass against `check-architecture.ps1` and the page test at `siteFoundationRevision.test.tsx:856`, then reverted it.

| Probe | Guard | Page test (3 views) |
|---|---|---|
| Original 1: backtick `` label: `Changes` `` in `FOUNDATION_SUBTABS` | **Fails** (row declares 4 labels) | n/a |
| Original 2: `label: CHANGE_LABEL` | **Fails** (non-literal label) | n/a |
| Original 3: `<Link aria-disabled="true">Change &amp; effect</Link>` beside the row | **Fails** (new `.tsx` scan, `navigation-truthfulness.ps1:495`) | **3 fail** |
| New: `<Link>{"Change & effect"}</Link>` (JSX expression) | Passes | **3 fail** |
| New: multi-line `<button disabled>` with `Changes` on its own line | Passes | **3 fail** |
| New: `<Link>{"Change" + " & effect"}</Link>` (concatenation) | Passes | **3 fail** |
| New: `<Link to="#" aria-label="Change and effect">&rarr;</Link>` | **Passes** | **Passes** (R2) |

### 4. M2(b): panel order

I ran each mutation against the order block, and each was caught by the right test:
- acquisition above verdict;
- bindings swapped with verdict;
- controls above topology/identity;
- gateway/sources swapped with verdict.

Moving the "Record and inventory details" audit panel above topology/identity on the Site model was **not caught** (R3).

### 5. Q1: closed

- `OperatorShellLayout.tsx:53` adds `app-frame--operator`.
- Every rule in the `max-width: 640px` block of `primitives.css` is prefixed with it.
- Rail group labels are no longer hidden, which also closes m1.
- `SimulatorLabShell` does not carry the class, and a test pins that.
- The Lab is back to its pre-S1-03 behaviour at 390 px. That is correctly carried, not claimed verified.
- `shell-overflow.ps1:211-237` fails an unscoped `.app-frame`/`.nav-rail` selector in a `(max-width: Npx)` block (probe confirmed) and fails if no such rule exists. It is sound for the form used today; see n2 for the forms it does not see.

### 6. Q4, m2, m3: closed as ruled

- **Q4:** the column is "Channels". The caption distinguishes a bound channel that describes the part from an unbound channel on an attached device. Unbound items are muted and keep "Not bound:". Placement is unchanged, and a test asserts that no bound item says "Not bound".
- **m2:** the SLD paragraphs follow the drawing (`SiteSingleLineDiagram.tsx:1079-1090`), and a test pins it.
- **m3:** `FoundationRevisionPanel.tsx:259-260` maps members through `foundation.assets`. That list is served by the Foundation API from registered assets (`foundation_api.py:256`). Each member falls back to its own code when no name exists, so it never shows an invented name. I found no mock values. The test fixture names are test data only.

### 7. Regressions: none found

- The full backend suite on Postgres passed, including the KOBO-001 `READY_TO_REPORT` gate, snapshot byte verification, reserve publication, conversion idempotence and the legacy-Site tests.
- The frontend suite (1182) and the build pass.
- The backend changes are confined to the n6 loop and two response fields. No migration, constraint or trigger changed.

## New findings

### R1 (major): an explicit later publication with unchanged content is silently superseded, and the edit is reported as having no end

- **Where:** `backend/assetops_backend/sites/binding_service.py:449-457`. A later period is carried if `following[0].bindings_sha256 == replaced.bindings_sha256`, whatever its origin.
- **Ruling:** the Architect required carry-through only for a period that is "only an unchanged Foundation-alignment/split descendant" and a stop at a later "independent, explicitly published binding change".
- **Concrete scenario** (reproduced in memory and on Postgres):
  1. v1 is the converted set.
  2. Publish "fuel off" from 10-08 (set C2).
  3. Publish the full set from 10-08 again as an explicit reinstatement. This is v4: `origin=PUBLISH`, note "fuel sensor reinstated 10-08 (explicit)". It is allowed because it differs from C2. The current rows are now `[09-29, 10-08) SPLIT C1` and `[10-08, ∞) PUBLISH C1 (v4)`.
  4. Publish an SOC removal from 10-04.
- **Observed:**
  - `applies_until: null` and `stopped_by_binding_version: null`;
  - v4 is superseded;
  - current rows are `[09-29, 10-04) SPLIT` and `[10-04, ∞) PUBLISH "SOC removed"`;
  - SOC is absent at 10-09.
- **Expected under the ruling:** stop at 10-08, report `applies_until` 10-08 and v4 (or refuse naming that boundary), and leave v4 and its note current.
- **Why it matters:**
  - A deliberate, separately published decision is overwritten without the user being told. The UI says "with no end", which hides the very boundary the ruling wanted shown "so the user can choose another edit".
  - v4's record and note leave the current configuration. They are recoverable only through `knowledge_at`.
  - S2-01a will consume these snapshots.
- **The packet's justification does not hold.** It says such a publication "cannot be told from a split copy by content". That is true, but lineage is stored:
  - every row carries `origin` and `derived_from_revision_id`;
  - a split copy is `origin=SPLIT` with `derived_from` pointing at its predecessor (`binding_alignment.py:204-214`, `binding_service.py:461-473`).
- **Fix:**
  - Carry a following period only when it descends from the same publication as `replaced`. Resolve each row's root by walking `derived_from_revision_id` through `SPLIT` rows, using all `state.binding_sets` including superseded ones, to the first non-`SPLIT` row.
  - Compare roots by publication, not by row id. One publication spanning several Foundation periods yields several non-`SPLIT` pieces that share `derived_from_revision_id`, `recorded_at` and `change_note`. For example, the n6 result itself is two `PUBLISH` pieces at 10-04 and 10-05.
  - Keep the content check as well.
  - Add my scenario as a test: in memory, and preferably also in `test_s1_bindings_postgres.py`, since n6 has no Postgres test.
  - The alternative is an explicit Architect waiver of the content-equality rule.

### R2 (minor): a Change & effect destination named only by `aria-label` passes both the guard and the page test

- **Where:** `tools/checks/navigation-truthfulness.ps1:495` (matches only `>text<` on one line) and `frontend/src/shell/__tests__/siteFoundationRevision.test.tsx:856-865` (matches `textContent` only).
- **Scenario:** `<Link to="#" aria-label="Change and effect">&rarr;</Link>` beside the view row. It is an enabled, accessibly named destination for the forbidden capability, and nothing fails.
- **Fix:** in the page test, match the accessible name (`aria-label`, `title`) as well as `textContent`. For example, `screen.queryAllByRole("link"|"button"|"tab", { name: /^(changes|change\s*(&|and)\s*effect)$/i })` within `main`.
- **Note:** the guard's single-line `>text<` scan is bypassed by JSX expressions, multi-line text and concatenation (table above). The page test catches all three, so the pair holds except for this case. The test only inspects `main`, so a destination placed in the rail is outside it. Carry this, or fold it into the same test change.

### R3 (minor): the Site-model order test does not pin the audit panel below the controls

- **Where:** `siteFoundationRevision.test.tsx:879-892`. The expected list omits "Record and inventory details".
- **Scenario:** moving that audit panel directly under the strip, above topology/identity, passes every test. Section 2 puts audit disclosures last.
- **Fix:** append "Record and inventory details" to the expected list, or assert that it is the last `h2`.
- **Note:** the gateway/sources panel and the scope note on Readiness are likewise unpinned against each other. That is lower value.

### Notes

- **n1. `stopped_by_binding_version` can name a SPLIT alignment copy.** If the independent change was later realigned by a Foundation change, the version reported is the realigned copy's, not the original publication's. The content and boundary are still correct and the UI wording is accurate enough. If R1 is fixed by lineage, consider reporting the root publication's version.
- **n2. `shell-overflow.ps1:217` sees only one media-query form.** It matches only `@media (max-width: <N>px)`. An unscoped `.app-frame` rule inside `@media (max-width: 40em)`, `@media screen and (max-width: 600px)` or `@media (width <= 600px)` passes the guard (each probed). That is acceptable for today's single block, but worth widening if more narrow rules are added.
- **n3. The unavailable wording on a `not_found` without `at`.** For example, an unknown Site on `/foundation/sld` now reads "Stored Foundation versions could not be read: …". That is honest (no false claim of absent records), though "could not be read" slightly overstates a clean 404. Cosmetic.
- **n4. 390 px captures not regenerated.** The captures in `.agent/S1-03-screens/` predate m1/m2, and the packet says so. The layout-evidence run after the fix covers the Site views at 390 px numerically.

## Carries (accepted with the merge, unchanged from the packet unless noted)

- Lab phone layout at 390 px: back to pre-S1-03 behaviour and unverified. Needs its own check (Planner: the owning Lab slice or V-01).
- Lab layout claims remain unmeasured (the run-setup abort).
- m4 (Readiness density) and m5 (topology cards follow one upstream chain per feeder).
- R2 and R3 (minor test gaps), and notes n1-n4.
- R1 only if the Architect waives the lineage requirement.

## Residual risk not named in the packet

- **Lineage claim:** the packet's own carry says "cannot be told from a split copy by content". The lineage to tell them apart is stored, so R1 is fixable rather than inherent.
- **Postgres coverage of n6:** n6 has no Postgres test. My probes show the database accepts both the carry-through and the stop plans, but nothing on the branch protects that.
