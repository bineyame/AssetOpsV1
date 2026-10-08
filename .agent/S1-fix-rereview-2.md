# S1 fix-round re-review 2 (R1-R3)

- **Reviewer:** a fresh Claude Reviewer (Opus). I did not write any of this code, and I did no earlier S1 review, including `.agent/S1-fix-rereview.md`.
- **What I changed:** I edited no tracked file and made no commit, push or merge. This file is my only write to the repo.
- **Reviewed:** `149f7c0..022a9d1` on `task/S1-03-foundation-organization`. That is commit `7c28b8c` (the S1-02 n6 lineage fix) and commit `022a9d1` (the S1-03 R2/R3 test and guard fix).
- **Authority:**
  - the "S1-02 n6" ruling in `.agent/architect-S1-03-questions-2026-10-08.md`;
  - R1-R3 and n1 in `.agent/S1-fix-rereview.md`.

  I treated "Fix round 2" in `.agent/S1-03-review-packet.md` as claims to verify.

## Verdict for the whole S1 branch: **accept with carries**

R1 is fixed. The fix matches the Architect's ruling: the edit carries through split descendants and stops at an explicit, separately published change. That holds in memory and on Postgres, and it survives every case I could build against it. R2 and R3 are closed for the cases named in the earlier review. The two new findings below are minor test or guard gaps, not product defects.

## Checks I ran (what I saw)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | Passed |
| `tools/check-agent-workflow.ps1` | Passed |
| `pytest backend/tests -q` with `ASSETOPS_TEST_DATABASE_URL=.../assetops_test` | **1577 passed**, 0 skipped (3m10s) |
| `npx.cmd tsc --noEmit` | Clean (exit 0) |
| `npm.cmd test` (main checkout) | **Ran.** The known sandbox failure did not occur. 49 files, **1182 passed**. |
| `npm.cmd run build` (scratch worktree at `022a9d1`) | Built; only the existing chunk-size warning |
| `tools/layout-evidence.mjs` | Not rerun. This round has no layout-affecting change (one backend loop, test assertions, a guard regex), and the packet records it as not rerun. |

**Probe environment**
- Probes ran in a detached scratch worktree, `C:\Users\assef\Bineyame\AssetOpsV1-rr2-probe`, using `PYTHONPATH=<worktree>\backend`. I confirmed that `assetops_backend` resolved to the worktree.
- `node_modules` was junctioned in. I removed the junction first, then the worktree. `git worktree list` now shows only the main checkout, and the main `node_modules` is intact.
- Postgres probes used `assetops_test` only, run after the full suite finished. The dev database `assetops` was not touched.

## Item status

| # | Item | Status |
|---|---|---|
| 1 | R1 / n1: lineage carry-through | **Closed** (test gap N1 below) |
| 2 | R2: aria-label/title "Change and effect" | **Closed** for the named case. More bypasses exist (N2). |
| 3 | R3: "Record and inventory details" pinned | **Closed** |
| 4 | Regressions S1-01/02/03 | **None found** |

### 1. R1 / n1: closed

**Code** (`backend/assetops_backend/sites/binding_service.py`)
- `_publication_root` (`:88-98`) walks `derived_from_revision_id` through `SPLIT` rows. It looks rows up in `state.binding_sets`, which includes superseded rows in both stores: the Postgres `_select_binding_sets` (`postgres_foundation_store.py:475-488`) has no `superseded_at` filter, and the in-memory fake passes every row.
- The walk has a cycle guard.
- The carry condition (`:476-480`) requires both equal `bindings_sha256` and an equal `_publication_key`.
- `stopped_by` is now the root's version (`:483`).

**Stops**
- The branch tests pass for the explicit identical reinstatement: v4 with `origin=PUBLISH` at 10-08, then an SOC removal from 10-04. The in-memory test is `test_s1_bindings.py:651` and the Postgres test is `test_s1_bindings_postgres.py:376`. They show `applies_until` = 10-08 and `stopped_by` = v4, v4 stays current with its note, and SOC is bound after 10-08.
- **My probe P3 (in memory and Postgres):** the same reinstatement, then a reserve change at 10-10. That realigns v4 into `SPLIT` copies, and v4 itself becomes superseded; I asserted that the row current at 10-08 is a `SPLIT` with a different version. The edit still stops at 10-08, and `stopped_by_binding_version` is **v4**, the original publication, not the split copy. n1 is satisfied.
- **My probe P4:** an explicit identical reinstatement, with null notes on every publication and a fixed clock. It stops correctly.

**Carries**
- **P1:** a reserve split at 10-05, then "fuel off" from 10-02. That produces two `PUBLISH` pieces, and I asserted both exist. An SOC removal from 10-03 then carries through both pieces: `applies_until` is null and SOC is absent at 10-06.
- **P1b:** the same with `note=None` on both publications, under the fixed test clock, so `recorded_at` is identical across all publications. It still carries correctly, and no wrong publication matched.
- **P2 (in memory and Postgres):** P1, then reserve changes at 10-07 and 10-09. This leaves a current `SPLIT` of a superseded `SPLIT`, which I asserted. The edit from 10-03 carries through all four periods with no end. On Postgres it leaves 4 contiguous aligned rows from 10-03, each anchored inside its Foundation row, each snapshot hash matching its bytes.

**Can two publications share the identity tuple?** I found no reachable case.
- A non-SPLIT root's `derived_from_revision_id` is the `replaced` row (`:578`). That publication supersedes `replaced`, and rows are never un-superseded, so no later publication can derive from it.
- `derived_from=None` occurs only on a Site's first set: the conversion, or a first publish with no current sets.
- `recorded_at` and `note` are therefore redundant. My mutations M5/M6 dropped them and nothing changed.
- I could not build a same-`recorded_at` and null-note collision: P1b tried and did not collide, because `derived_from` differed.

**Can one publication's pieces fail to match?**
- `split()` in `binding_alignment.py` copies origin, `derived_from`, `recorded_at` and note into every piece.
- A later re-split makes `SPLIT` rows whose walk reaches back to a piece of that publication.
- A binding edit's "earlier segment" is a `SPLIT` that walks to `replaced`.
- P2 exercises the re-split chain. I found no mismatch.

**Earlier n6 behaviour** (branch tests, plus my Postgres probe of the original fixture). These hold:
- 10-04 removal across the 10-05 split: absent at 10-04T12, at 10-05 and at 12-01, present at 10-03.
- An earlier `knowledge_at` recovers SOC at 10-06.
- The edit stops at a later change with different content (branch test).
- Atomicity: one `publish_configuration` transaction.
- One aligned row and pinned snapshot per Foundation period: 2 rows from 10-04, and the byte hashes match on Postgres.

**Mutation probes (mine, reverted)**

| Mutation | Branch tests (memory + PG) | My probes |
|---|---|---|
| M1: content-only (lineage clause removed) | **Both new tests fail** | P3, P4 fail |
| M2: key = root row id (not publication) | **all pass** | P1, P1b, P2 fail (N1) |
| M3: no walk through SPLIT | in-memory "stops at a later independent change" fails; **PG suite passes** | P2, P3 fail |
| M4: `stopped_by = following.version` (no root) | **all pass** | P3 fails (n1 unpinned) |
| M5/M6: drop `derived_from` or note from the key | all pass | all pass (redundant fields, no behaviour change) |
| M7: drop content check (lineage only) | all pass | all pass (lineage implies content; belt and braces) |

### 2. R2: closed for the named case

Results of injecting into the loaded view's `main` in `SiteFoundationFrame.tsx`. Control: a plain `<a>Changes</a>` fails both checks.

| Probe | Page test (3 views) | Guard |
|---|---|---|
| `aria-label="Change and effect"` | fail | fail |
| `title="Changes"` | fail | fail |
| `aria-label={"Change and effect"}` | fail | pass |
| `aria-label='Change & effect'` (single quotes) | fail | pass |
| `aria-labelledby` pointing at a hidden `<span>{"Change and effect"}</span>` | **pass** | **pass** |
| `<div role="button" tabIndex={0}>{"Changes"}</div>` | **pass** | **pass** |
| `<input type="button" value="Changes" />` | **pass** | **pass** |
| `<a>Change &amp; effect &rarr;</a>` | **pass** | **pass** |

The last four rows are N2.

### 3. R3: closed

`siteFoundationRevision.test.tsx:891` now lists "Record and inventory details" last. I moved the panel above the topology/identity pair, and separately between that pair and the controls. Both moves failed the Site-model order test.

### 4. Regressions: none found

- The backend change is confined to the carry loop and two helpers. There is no migration, constraint, trigger or API shape change.
- The full Postgres backend suite (1577), the frontend suite (1182), `tsc` and the build all pass.
- The `stopped_by_binding_version` field and its UI text are unchanged in form.

## New findings (ranked)

### N1 (minor, test gap): the "carries through one publication's pieces" half of R1 is unpinned

- **Where:**
  - `binding_service.py:101-107` (`_publication_key`) and `:88-98` (the walk);
  - tests `test_s1_bindings.py:567-676` and `test_s1_bindings_postgres.py:376-407`.
- **Scenario:**
  - Mutation M2 compares root row ids instead of publication identity, which is the natural "simplification". With it, an edit made inside one publication that spans a Foundation boundary stops at that boundary: `applies_until` is set and the later piece keeps the old set. The whole branch suite passes in memory and on Postgres.
  - M3 (no walk) is caught in memory only. On Postgres nothing exercises a `SPLIT`-of-`SPLIT` chain.
  - M4 (report the split copy's version) is not caught by any branch test, so n1 is implemented but not pinned.
- **Why it matters:** the carry half is half of the Architect's rule. The current failure mode is honest, because the edit reports its end, but it is wrong.
- **Fix:** add my P1/P2 scenario (a publication over a reserve split, then re-split, then an edit inside it carries with no end) and P3 (a realigned reinstatement still reports v4) to the in-memory suite, ideally also to Postgres. This is test-only. **Carry.**

### N2 (minor, carry of R2's note): other forbidden-destination shapes pass both the page test and the guard

- **Where:**
  - `frontend/src/shell/__tests__/siteFoundationRevision.test.tsx:860-866` (selector `a, button, [role='tab'], [role='link'], [aria-disabled]`, with an anchored regex over `textContent`, `aria-label` and `title`);
  - `tools/checks/navigation-truthfulness.ps1:495-496`.
- **Scenario:** any of the four shapes in the R2 table renders an enabled, named "Change & effect" or "Changes" control in `main`, and nothing fails:
  - `aria-labelledby` to hidden text;
  - a `role="button"` div;
  - `<input type="button" value>`;
  - a trailing arrow, as in "Change & effect →".
- **Fix:**
  - Use testing-library accessible names: `within(main).queryAllByRole(/^(link|button|tab|menuitem)$/, { name: /^\s*(changes|change\s*(&|and)\s*effect)\b/i })`. That covers labelledby, role and input value.
  - Relax the trailing anchor so arrows and punctuation match.

  **Carry.** No such element exists in the tree today.

### Notes

- **n1 follow-on:** `stopped_by_binding_version` now names the root publication. After a later realignment, that version is superseded, and the current rows at that boundary carry other version numbers. The UI wording ("binding vN (a later, separately published change)") stays accurate. Consumers should not expect vN among the current rows.
- **Redundant key fields:** `recorded_at` and `change_note` in the key, and the kept content check, change no reachable behaviour (M5-M7). They are harmless.

## Carries (accepted with the merge)

Unchanged from `.agent/S1-fix-rereview.md` unless noted:
- Lab phone layout at 390 px is unverified, and the Lab layout claims remain unmeasured (run-setup abort).
- m4 and m5.
- Notes n2 (`shell-overflow.ps1` media-query forms), n3 and n4.
- New: N1 and N2 above.

## Residual risk not named in the packet

- The packet says "a publication spanning several Foundation periods still carries", but no branch test proves it (N1).
- n6/R1 has one Postgres test, and it covers only the stop case. Postgres behaviour for the carry and walk paths is shown by my probes, not by the branch.
