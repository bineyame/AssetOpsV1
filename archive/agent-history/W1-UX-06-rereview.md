# W1-UX-06 re-review (fix round 1)

Reviewer: a fresh, independent Claude reviewer who did not author the slice or the fix. Revision under review: `85c3a9c5`. Diff: `678901f0..85c3a9c5` (5 files: the walkthrough, the packet's "Fix round 1" section, `SiteActionVerification.tsx`, its test, and `tools/checks/test_evidence_checks.mjs`). Worktree: `AssetOpsV1-review5`, detached.

## Verdict: ACCEPT

M1 is closed. L2, L3 and L4 are addressed. The new guard really fails on a review-folder path. I found no new fail-open path and no weakened assertion. Three new Lows are below. None of them blocks, but **fix N1 before the walkthrough goes to the owner**: it is a one-character edit, and it is in the "Before you start" section.

## M1: closed

I checked `.agent/W1-UX-combined-owner-walkthrough.md` against each point in the brief.

- **Runs from the main folder.** Step 1 runs `cd C:\Users\assef\Bineyame\AssetOpsV1`, then `git log --oneline -1`. The owner must match the commit the coordinator gives, and is told to "stop and ask" otherwise. The only literal paths left are this folder (lines 21 and 28).
- **No review-folder path.** No `AssetOpsV1-review*` text is left anywhere in the file.
- **`$wt` is set once per window.** There is one `$wt = (Get-Location).Path`, at line 29, right after a `cd` into the main folder. Step 3 says to paste it into every window. Every per-part line uses `cd $wt` or `cd $wt\frontend`. There is no other `$wt` assignment.
- **PYTHONPATH.** All 21 PYTHONPATH lines are the same five entries: `$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator`.
- **`var\sites`.** The `Copy-Item` is gone. Step 4 only creates the folder and warns if `kobo-001.yaml` is missing. The file is present in the main folder, and so is `.venv\Scripts\python.exe`.
- **`npm.cmd ci`.** It is in step 4, run in `$wt\frontend`, which then returns to `$wt`.

I read the walkthrough end to end as a non-developer would. Each part names its windows:
- the tool window starts with `cd $wt`;
- the web windows start with `cd $wt\frontend`;
- clean-up runs in the tool window after Ctrl+C.

Nothing in it now runs mixed or pre-merge code silently.

## Guard: works

In `tools/checks/test_evidence_checks.mjs:164-170`, I appended `cd C:\Users\assef\Bineyame\AssetOpsV1-review7\frontend` to the walkthrough. The check `the combined owner walkthrough names no review worktree path` then failed (1 failed, exit 1). I reverted with `git checkout`: 10/10 pass, exit 0, and the tree is clean. The test file is run by `tools/check-all.ps1:71`. The check is non-vacuous: it requires a length of over 1000 and the `Get-Location` line.

## L2, L3, L4

- **L2: addressed.**
  - Part 5 §4 now asks the owner to open `/sites/KOBO-001/evidence`.
  - Part 16 §4 asks the owner to click a gateway through "What to do", then look for "In contact; its latest report is old" and "...age cannot be confirmed".
  - Both §7 rows now read "owner look" instead of "not run", which is accurate.
- **L3: addressed.**
  - Line 9 now says "Most screens".
  - Line 13 now says a current amount is shown only when the current read proves it is current and priced, and that history amounts appear only labelled as history.
  - One small nit is folded into N3.
- **L4: honest.**
  - A known code shows the exact code beside `reasonWords(code)` from `sourceProvenance.tsx`.
  - An unmapped code falls back to "Another source problem was recorded.", which is non-positive.
  - A code-less object no longer renders "undefined". It shows no code and reads "Reason not recognised.", also non-positive.
  - The existing code assertion is unchanged, and a words assertion was added.
  - The record count and `accepted_evidence_ids` are still not shown. The prior review marked those "later", so that is acceptable.
- **L5:** not changed. It was a preference.

## New findings (all Low, none blocking)

### N1. Low: a broken code fence in "Before you start" swallows step 5 (introduced by this fix)

Where: `.agent/W1-UX-combined-owner-walkthrough.md:40`.

````
   cd $wt
   ```5. Each part uses **two windows**. ...
````

The closing fence of step 4 and the start of step 5 are on the same line. A fence followed by text does not close a code block. So in any Markdown preview (VS Code, GitHub), step 4's grey command box runs on to line 45. It then contains:
- the text "5. Each part uses two windows...";
- a stray "```powershell";
- the step-5 lines with their `<API port named in the part>` placeholders.

What goes wrong:
- The numbered step 5 disappears from the list.
- An owner who copies the whole step-4 box pastes junk lines and an `npm.cmd run dev -- --port <web port ...>` line. PowerShell rejects that line with "The '<' operator is reserved". It fails loudly and harms nothing, but it confuses at the very start.
- Read as raw text, the file is fine.

Fix: put a line break between the closing fence and `5.`, and indent that fence like the others.

### N2. Low: the L4 test does not prove the plain words

Where: `frontend/src/sites/__tests__/siteActionVerification.test.tsx:510`.

The test compares the rendered words against `sourceReasonWords(...)` itself, not against literal text. Neither fixture code (`SOURCE_NOT_ESTABLISHED`, `PLAIN_CODE`) is in `REASON_WORDS`, so both sides are the generic fallback. As a result:
- a mapped code's words are never checked;
- the code-less branch ("Reason not recognised.") is not exercised at all.

The production behaviour is correct by reading, and the existing code assertion is untouched, so nothing was weakened.

Fix: assert literal strings, and add one mapped code (for example `NO_POSITIVE_BINDING`) and one `{}` reason.

### N3. Low: small wording issues in the walkthrough

- **Step 3 (line 26).** It says "the first line is run from inside the folder from step 1; in a new window `cd` there first". But the first line of the snippet *is* the `cd`. Simpler: "Paste these three lines into every new window."
- **Part 5 §4 (line 393).** It says `http://localhost:<web port>/... (the web port this part prints)`. This part fixes web port 5520, so write `http://localhost:5520/sites/KOBO-001/evidence`.
- **Line 9.** It says note 10 "lists the exceptions" including Sites and the no-card states. Note 10 lists only the held and empty no-picture states. Either widen note 10 or drop the pointer's extra items.

### Guard scope (observation, not a finding)

The guard catches only the literal text `AssetOpsV1-review`. A second hard-coded `$wt = "C:\..."` line, or another worktree name (such as `AssetOpsV1-plan2`), would pass. That is enough for M1.

## Checks run (by me, at `85c3a9c5`)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run src/sites/__tests__/siteActionVerification.test.tsx` | 1 file, 25/25 passed (it ran in this worktree; stderr shows the usual React stack noise) |
| `node tools/checks/test_evidence_checks.mjs` | 10/10 pass |
| Guard plant (`AssetOpsV1-review7` path appended), then revert | 1 fail, exit 1; after the revert 10/10 pass, tree clean |
| Grep of the walkthrough | no `AssetOpsV1-review`; one `$wt =`; 21 PYTHONPATH lines, all five entries; no `Copy-Item`; one malformed fence (N1) |

## Not verified

- **Not run by me:** the full frontend and backend suites, `check-architecture`, and `check-agent-workflow`. The fix touches no backend, and only one frontend component and its test.
- **The walkthrough itself.** I did not execute it (servers, Postgres, browser). In particular:
  - the Site Evidence owner look on the s405 store;
  - the selected-gateway view on s701;
  - that `npm.cmd ci` succeeds in the main folder.

## Residual risk

- `npm.cmd ci` deletes and reinstalls `frontend\node_modules` in the main folder. If a dev server or editor process from that folder holds a file open, Windows fails with EPERM. Stop any running dev server first.
- The main checkout is detached, and its own git status shows an untracked `backend/tests/test_s3_capability_read_postgres.py`. Step 1 relies on the coordinator to put it on the merge commit first. The walkthrough correctly tells the owner to stop and ask rather than switch revisions themselves.
