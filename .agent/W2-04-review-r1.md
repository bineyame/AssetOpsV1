# W2-04 review: cold Site, evidence and unpriced money

This is an independent first review of branch `task/W2-04-cold-site-evidence-money` at head `58d2d504`. It is judged against `.agent/W2-04-build-spec.md` (`D-2026-10-18-w2-04-buildspec`, including Run-7, Run-8 and Run-9), the v69 cold screens and the `.agent/W2-04-evidence` captures.

## Verdict: CHANGES

The structure, migration and money rules look sound. Five Medium findings block: two are code or copy defects, one is a stray committed file, and two are unruled decisions that need an Architect ruling. There are no High findings.

## Findings

### Medium (blocking)

**M1. R1 is not applied to unbound source rows: their Affects cell is wrong.**
- Where: `frontend/src/sites/coldSiteViews.tsx:822-833`. When a row has no bound source (`bound.length === 0`), the Affects cell renders `Claim effect not assessed`.
- What Run-9 R1 requires: "Keep the Run-8 closed Affects summaries as capability labels, independent of whether the report was accepted." The mock agrees: Transfer switch shows `Backup chain` even when it is Not connected.
- Correct values: an unbound Transfer switch should read `Backup`, and an unbound Loading / door log should read `Temperature · cooling`.
- The test locks in the wrong behaviour. `frontend/src/sites/__tests__/coldSiteViews.test.tsx:575-582` expects `Claim effect not assessed` for rows 4-6.
- The packet's fix table says R1 is closed. That claim covers only the What cell.
- Why the captures don't show it: COLD-LAB-001 binds `transfer-1`, so the unbound path never renders there.
- Fix: use `CLOSED_SOURCE[row.label].affects` in the unbound branch and correct the test.

**M2. The line-height 1.25 lever is an unruled typography change, so it is an Architect question.**
- Where: `frontend/src/sites/w2-cold-site.css:126-129`.
- Run-8's fallback instruction for this panel: if it still exceeds its bound after the exact edits, "report the measurement and selected text in the W2-04 review packet". It does not license another lever. Run-8 and Run-9 name only 6 px padding and 6 px gaps for this panel.
- The rule also applies to every th and td in the table, header included. Only the Record cell has two lines, yet single-line rows are set at 1.25. The shared `.data-table` and the mock `td` both use 1.6.
- I viewed the 1440 capture. It is readable, and the order, content and columns are unchanged, but the rows are visibly denser than the mock.
- The rule is scoped to `min-width: 641px`, so the 390 capture is unaffected. That table scrolls and remains readable.
- The Architect should pick one:
  - (a) amend the spec to accept 1.25, preferably limited to the Record cell; or
  - (b) revert it and accept 370 px (1.39×), with the D2-ruled two-line Record cell as the stated reason.

**M3. A stray server log is committed at the repository root.**
- Where: `x`, 520 lines of uvicorn access log, added in `6177f1dc`.
- It has nothing to do with the slice and would land on main.
- Fix: `git rm x`.

**M4. The Financials Source cell uses unruled null-link copy.**
- Where: `frontend/src/sites/coldSiteViews.tsx:1225` renders `Finding link not available`.
- The spec does not contain this string. Run-8 rules that a missing destination reads `No linked page for this item`.
- Fix: use the ruled string.

**M5. Every cold chip renders in the neutral tone, while the mock colours them. This is an Architect question.**
- Mock colours: `Good` is green, and `Limited` and `Evidence limited` are amber.
- Where: `coldSiteViews.tsx:739, 768, 846, 849, 1222`, all `tone="neutral"`.
- This drift is visible to users, and no ruling covers it. W2-03 (`ColdAssessmentViews.tsx:243,511`) does the same, and `Badge.tsx` deliberately avoids colour per vocabulary.
- Fix: one W2-wide ruling, either tones mapped to mock colours or an accepted neutral deviation.

### Low

- **L1.** `coldSiteViews.tsx:1218` shows the raw unit token `degC_min` and `19–Unknown bound` to users (Financials row and card). This is plain-language drift; fold it into the UI/UX copy pass.
- **L2.** `coldSiteViews.tsx:847-850` puts `Other recorded roles` in the closed What cell when only a non-primary role has accepted facts, for example `generator_state` without `backup_start_event`. Run-8 permits that label only for overflow, so the Architect should confirm.
- **L3.** All three capture records show the same short ID, `00000002-0…`, because the capture seed IDs share a prefix. Production uses `uuid4`, so this is evidence-only, but the capture cannot show that rows are distinguishable.

## Checks D1, D2, R1 and R2 against the code

- **D1: matches.**
  - Widths are 26/16/16/23/19 (`w2-cold-site.css:96-100`).
  - The headers match, and the CSS uppercases them and wraps them on two lines.
  - The contact and quality chip maps are correct (`coldSiteViews.tsx:672-685`).
  - Nowrap applies to `.badge` only.
  - In the capture, no text collides or crosses a cell boundary.
- **D2: matches, apart from the M2 lever.**
  - The Record cell reads `Record {short id}` plus `No analysis link`.
  - The full ID, Target and the Q-R9 limitation are in Record details, and PROVED keeps its link (`:1034-1044, :1065-1086`).
- **R1: What cell correct, Affects cell wrong (M1).**
- **R2: met.** I re-measured from the 1440 captures by eye, at about ±3 px:
  - Data sources row: about 544 px against the claimed 545 (limit 569).
  - Accepted records: about 343 px against 344 (limit 345).
  - Claim limit panel: about 188 px against 191 (limit 192).
  - I did not rerun the DOM measurement, because that needs the backend, Chrome and the seed.

## Migration 0023 and backend (read, not executed)

- **Schema:**
  - Four append-only tables, with `ledger_append_only` triggers on all four.
  - Scoped composite FKs, plus the `(tenant_id,site_id,batch_id)` unique target on `batch_publication_link`.
  - The unique constraints on basis, revision number, scope, dirty key and attempt number all match the spec.
- **Money and quantity rules:**
  - The DB CHECK forces amount and currency to null.
  - `degC_min` allows null bounds only when the row is WITHHELD or carries a limitation.
- **Triggers:**
  - The FindingRevision trigger fires only for `cold_chain`.
  - Enqueue is trigger-only, with `ON CONFLICT DO NOTHING`.
  - There is no `ASSUMPTION_PUBLISHED` cause.
- **Backfill and downgrade:**
  - The backfill reuses the same dirty key, so it is idempotent.
  - Downgrade refuses while rows exist.
- I found no defect here.
- I did not run the backend tests, per the brief. I rely on the builder's run (2823 passed, skipped=0) and have not verified it.

## "Not available yet"

- The only "Not available yet" strings in the slice come from the existing `UnavailableTab` / `UnavailableEntry` (the Scenarios subtab and the rail). Those carry the reviewed exemption.
- The cold views contain no free-text "Not available yet".
- Run-8 null links are runtime states, not gaps, so they correctly have no `mock_gaps` entry.
- The orphan scan passes.

## Checks run (on this worktree, head `58d2d504`)

| Check | Result |
| --- | --- |
| `tools/check-all.ps1` | All 10 guards passed. The missing-claim scan found 39 tagged placements and 10 baselined. |
| `npx.cmd vitest run coldSiteViews.test.tsx coldRoutes.test.tsx` | 2 files, 69/69 passed |
| `npx.cmd tsc --noEmit` | exit 0 |

**Not verified:**
- the full vitest run, and the builder's single unidentified failure under load;
- the backend and host suites;
- the build;
- the live DOM height measurements.

## Residual risk

- The unbound-source path is never captured (see M1).
- The packet already names the `SOURCE_GATE_CHANGED` worker path, which has no positive test.
