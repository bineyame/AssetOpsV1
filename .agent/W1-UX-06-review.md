# W1-UX-06 slice review (phase 2 and closeout)

Reviewer: a fresh, independent Claude reviewer who did not author this work. Revision under review: `4d8400de`. Diff: `28441130..4d8400de`, excluding `.agent`, with the focus on the W1-UX-06 commits: `129c1c0c`, `8b26a582`, `b7d75daf`, `88ad67a3`, `41160b19`, `2d03f626`, the capture commits, `9f0afe1a` and `4d8400de`. The review used the detached worktree `AssetOpsV1-review5`.

## Verdict: RETURN

There is one Medium finding. The code fixes, the tests and the final capture evidence are sound. The combined walkthrough is thorough and honest about what it does not cover. However, every command in it is pinned to the worktree folder `AssetOpsV1-review3`, and it never tells the owner which folder or revision to use once the slice is merged. The walkthrough is the only thing the owner will use at the gate, so this blocks.

The fix is a mechanical edit to one document. Nothing in the code needs to change.

## Findings

### 1. Medium: the walkthrough hard-codes a worktree path and does not say which folder to use after the merge

Where: `.agent/W1-UX-combined-owner-walkthrough.md:20-38`, plus every per-part `cd` and `$wt=` line (lines 87-100, 161-176, 227-236, 299-307, and so on). The literal path `C:\Users\assef\Bineyame\AssetOpsV1-review3` appears 63 times.

What goes wrong:
- **No folder or revision is named for the walk.** The document never says which folder or revision the owner should run from after the merge.
- **The review3 path will not stay valid.** `AssetOpsV1-review3` is the `task/W1-UX-06` worktree. After the merge it holds unmerged branch code, or nothing at all once the worktree is removed.
- **The main checkout is not on main either.** `C:\Users\assef\Bineyame\AssetOpsV1` is currently detached at `35509c54`, and the `main` branch itself is checked out in `AssetOpsV1-plan2`.
- **Mixing folders breaks silently.** Step 3 has the owner paste `$wt = "...review3"` into every window. If the owner `cd`s into the merged checkout but pastes these lines, `PYTHONPATH` imports the backend from review3 while the tool runs from the other folder. Nothing reports this.
- **The site-file copy fails in the main checkout.** Step 4 (line 32) copies `C:\Users\assef\Bineyame\AssetOpsV1\var\sites\*.yaml` into `var\sites\`. Run from the main checkout, that copies the folder onto itself, and PowerShell fails with "Cannot overwrite the item with itself".

Why it matters: a non-developer following the script as written will run pre-merge or mixed code, or hit an error at step 4. Either way the walkthrough does not exercise what was merged.

Fix:
1. Add one first step that names the folder the owner should use after the merge (for example the main checkout) and how to put it on the merged revision (`git switch main` / `git pull`, or the merge commit).
2. Set `$wt = (Get-Location).Path` once in that folder, and use `$wt` in place of every literal path (`cd $wt`, `cd $wt\frontend`).
3. Make the `var\sites` copy conditional: skip it when `var\sites\kobo-001.yaml` already exists, as it does in the main checkout.
4. Change "this folder" and "the main checkout" in the per-part prerequisites to match.

### 2. Low: two umbrella states that need no invented ID are recorded "not run" and are not in the owner's script

Where: `.agent/W1-UX-combined-owner-walkthrough.md` Part 5 §7 (Site Evidence labelled source, s405) and Part 16 §7 (Health, selected gateway).

- **Site Evidence, labelled source or unknown.** The recorded reason is "`links` prints no Site Evidence address". But the route is `/sites/KOBO-001/evidence`. It needs only the printed site, so `http://localhost:5520/sites/KOBO-001/evidence` works against the s405 store.
- **Health, selected gateway.** The recorded reason is "no tool prints a gateway ID". But Part 16 §4 itself says the "What to do" links open each gateway. That view is the only place the owner would see the Architect-approved Q3 lines "In contact; its latest report is old" and "...age cannot be confirmed". They are covered only by jsdom.

Both rows are honestly recorded as not run, so no claim is inflated. The owner is simply never asked to look at them.

Fix: add a "click a gateway" step to Part 16 §4, and an "open `/sites/KOBO-001/evidence`" step to Part 5 §4. Or record the true reason, which is that the evidence script cannot click through.

### 3. Low: the plain-language overview claims slightly more than was built

Where: `.agent/W1-UX-combined-owner-walkthrough.md:9` and `:13`.

- **Line 9** says "Every screen now opens with an answer card ... a small picture". That is not true everywhere:
  - Sites has no picture, by design (Part 1 §4).
  - The held and empty states draw no picture (owner note 10).
  - Foundation before any stored version, the asset refusal, and Site Work with no window chosen show no card at all.
- **Line 13** says "Money is only shown when it is current and priced". But Part 12 shows recorded historical amounts, each labelled as history.

Fix:
- Line 9: say "Most screens...", and point to note 10.
- Line 13: say "A current amount is shown only when it is current and priced. Earlier recorded amounts appear only when labelled as history."

### 4. Low: the `2d03f626` crash fix shows only the reason code and drops the reason's lineage

Where: `frontend/src/sites/SiteActionVerification.tsx:1403-1406`.

The fix is honest:
- It stops a blank page.
- It sits in the window's technical facts list, beside other exact codes (Source state, Source classes).
- The card's state line still carries the plain meaning ("Some readings are missing").
- It does not misstate anything.

What it loses:
- Each reason object's `accepted_evidence_ids` and its extra detail (`run_ids`, `fixtures`, `details`; see `source_provenance.py:157-207`).
- A plain-words gloss. `sourceProvenance.tsx:143-147` already renders the same codes through `reasonWords(r.code)` with a record count.
- A code-less object would also render the literal text "undefined" (`String(reason.code)`).

Fix (later): reuse `reasonWords`, show the record count, and fall back to a "reason not recognised" label.

### 5. Low (preference): "configuration snapshot" is broader than the "acquisition snapshot" it replaces

Where: `backend/assetops_backend/sites/registered_basis.py:116-117`.

The trigger (`binding_set is None`), the code `BINDINGS_NOT_REGISTERED` and the refusal are unchanged. "Acquisition snapshot" meant the pinned channel-link snapshot that a gateway downloads. "Configuration snapshot" could be read as the Foundation itself.

The sentence stays correct, so this is a preference. Possible fix: say "channel-link snapshot".

`READINESS_STATEMENT` (`binding_service.py:88-92`) keeps both the configuration-only meaning and the "does not mean connected, reporting or healthy" limit. It closes phase-1 L2.

## Verified

- **N1 (`SiteFinancials.tsx:133-152`).**
  - `useRead` stores the deps that each answer belongs to, and returns `null` when they differ from the current render's deps.
  - The bridge, consequences, history, series and exact reads all pass the inputs that fully identify their request (`pinnedRevision` and `consequenceRevisionId` included).
  - The new test watches every DOM insert with a MutationObserver while the bridge lands, and finds that no amount is ever drawn. The implementer showed it fails when the deps key is reverted.
- **N2 (`w1-ux-02-evidence.mjs`).** `amountShown` now uses `c.querySelector`. It is not vacuous: 12 claims in the final logs record `"amountShown":true`, and the combined rule still rejects an untimed as-of next to a drawn amount.
- **Untimed helper.** It now wraps the shared `expectStateLineVisible`, which checks the same four parts, the closed disclosures and visibility, plus `AS_OF_PATTERN`. It keeps its exact `toBe("As of: time not recorded")`. It is equivalent or stricter.
- **L1 (`healthHeadlines.tsx:33-45`).** With zero enabled gateways under `ALL_CURRENT` or `NOT_ALL_CURRENT`, the state line now reads "Gateway contact cannot be confirmed" in the limited tone, with a next step. The test asserts the state line, the sentence and the next step, and that "Every enabled gateway is in contact" is absent. `NO_REGISTERED_SOURCE` keeps its own words.
- **L3.**
  - The proximity rule removes `//` comments and ignores lines that start with `/*` or `*`.
  - Three new cases show that a commented-out guard counts as missing.
  - `layout-evidence.mjs` now prints each passing width check with both widths.
- **L4.** `knownReadiness` uses `Object.hasOwn` for both the badge and the sentence, and `it.each` covers `SOMETHING_NEW`, `constructor` and `toString`.
- **Changed tests.** I diffed every test changed in the W1-UX-06 commits and found no fail-closed assertion weakened.
  - New assertions were added in `test_s1_bindings.py`, `test_s2_registered_basis.py`, `siteHealthBoundary`, `siteFoundationRevision`, `siteActionVerification` and `siteFinancials`.
  - The fixture statement string in `siteFoundationRevision.test.tsx:228` was reworded to match.
  - The s502 tool change only follows the token to its new place in the exact references.
- **The 10 "small visual" failures.** Leaving them failed, without widening `W1_NO_VISUAL_OK` or `NO_VISUAL`, and putting the question to the owner as note 10 is correct. None of the five cards is misleading without a picture:
  - each states its held, zero or no-price condition in words;
  - none draws a zero bar.
- **Owner note 12.** For the tool's "unavailable" Finding, the server sends `PRIOR_ACTION_UNRESOLVED` (`actions/service.py:178`), so "Held: an earlier trial is still open" faithfully shows what the server sent. Only the tool's case label is misleading. The note could say so, so the owner knows the question is about the hold taking precedence on the server, not about the screen's wording.
- **Widths.**
  - All 202 narrow width records in `.agent/W1-UX-06-evidence/*.txt` read `requested 390, innerWidth 390, clientWidth 390`. Every 1440 record has a clientWidth within 1420-1440.
  - No width check failed.
  - The only failures in the final logs are the 10 no-visual claims. The others are in superseded files: `s502-s502-initial-after-tick.txt` and `s602b-w1-ux-01-inconclusive.txt`.
- **Walkthrough content.**
  - All 26 screens and S4-08 are mapped.
  - Each tool's CLI shape matches its argparse `--help`: global versus subcommand option placement, `serve`/`links` ports, s601b's defaults 8961/5461, s602b's port+1 case API, and s2demo's API on `--http-port`.
  - Ports do not collide within a part, and parts run one at a time.
  - Cleanup is given for every part, and the shared templates are left in place.
  - The 13 owner notes are clear, and the gate makes no claim of acceptance or promotion.
- **Cleanup.** No `w1ux06` database remains on the shared Postgres; I checked after dropping my own.

## Checks run (serially, by me, at `4d8400de`)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `node tools/checks/test_evidence_checks.mjs` | 9/9 pass |
| `pytest test_s1_bindings.py test_s2_registered_basis.py test_s1_cutover.py test_s1_bindings_postgres.py test_s2_registered_basis_postgres.py`, 5-path PYTHONPATH, private `assetops_w1ux06slicerev_test` (created, then dropped) | 112 passed, 26 s |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npx.cmd vitest run` siteFinancials, siteHealthBoundary, siteFoundationRevision, siteActionVerification | 4 files, 221 passed |
| Walkthrough tool CLIs (`--help` for all 16 tools and the relevant subcommands) | the shapes match the commands written |

My first pytest attempt gave 21 setup errors in `test_s2_registered_basis_postgres.py`, because that module needs the base `_test` database to exist. I created it, reran, and all 112 passed. It was then dropped.

## Not verified by me

- **Full suites.** I did not run them. I cite the implementer: backend 2590/0 skipped/0 failed in 1416 s at `b7d75daf` (`git diff b7d75daf..HEAD -- backend contracts` is empty), and frontend 1912 passed at `9f0afe1a`.
- **Browser captures.** None were rerun, because each needs Chrome, a prepared tool database and a dev server. I checked the logs, not the screenshots, which are in `%TEMP%` and not in git.
- **The `widthGuard` window-bounds fallback.** It is still unexercised in real Chrome, as the packet itself says.

## Residual risk not named in the packet

- The walkthrough's example IDs and `recorded_at` moments are tied to the final run. The document says so (line 71), but an owner may still type them.
- `AssetOpsV1` is detached, and `main` lives in `AssetOpsV1-plan2`. Finding 1's fix needs to name one of them.
