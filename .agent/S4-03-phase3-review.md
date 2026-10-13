# S4-03 phase 3 + closeout - fresh Claude review

Reviewer: fresh Claude (did not author phases 1-3 or the closeout). Branch `task/S4-03-finding-evidence-history`, HEAD `37212de`, diff `26b5e7a..37212de`. No code was edited.

## Verdict: ACCEPT (carries below; no finding blocks the owner walkthrough)

I found no expensive-to-reverse defect, no misleading packet claim that changes acceptance, and no owner-only decision beyond the ones the packet already lists (History block layout vs mock table, late-note wording). The items below are Low carries.

## Checks I ran (one at a time)

| Check | Result |
| --- | --- |
| `npx.cmd vitest run` (frontend) | 61 files, **1439 passed**. Matches the packet. |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npm.cmd run build` | exit 0, chunk-size warning only |
| `tools/check-all.ps1` | **All 9 guards passed**; missing-claim scan "3 tagged, 15 baselined"; ledger valid (110 screens) |
| Full backend `pytest backend -q` on `assetops_test` (127.0.0.1:55432) | **1908 passed**, 0 failed, 0 skipped, 21 deprecation warnings, 11m28s. No connection-exhaustion errors. |

Not run by me: `tools/s4-finding-evidence.mjs` (needs servers, Chrome, private DB; I was told to start no servers) and `tools/layout-evidence.mjs`. So the browser claims (110/110, closed 8/8, overflow 1425/390, F04 v1 42 / v2-v3 78 cited, late note on v2 only, F01 102/263 and roles summing to 102) are **unverified by me**; I checked that the suite code asserts what the packet says. The packet records `layout-evidence.mjs` as `not run` with its precondition (it never visits Finding child views), which is the honest form.

## Item by item

1. **History.**
   - Exhaustive paging: `SiteFindingHistory.tsx:76-108` follows `next_after_revision_no` at 100/request until null; backend `finding_read.py:587-601` returns `next_after_revision_no` only while the last page row is below the final `revision_no`. Vitest walks 205 versions in 3 requests; the browser suite compares app rows to the API walked in 2-row pages.
   - Completeness statement: "All N recorded versions are listed" only when every page loaded and `rows.length === page.total` (`:264`); a failed later page reads "incomplete" (tested). Drift: see C1.
   - Selected vs latest: separate `is_selected`/`is_latest` from the backend (`finding_read.py:578`), separate marks and data hooks (`:319-326`); a mutation that used `is_latest` for selection was reported failing.
   - `accepted_rows`: rendered as "N cited; R of N found as accepted records" plus a link to that version's Evidence (`:350-358`); no verdict word (test asserts no "lineage/verified/fully traced").
   - Late-acceptance note: `accepted_at` is `max(ingestion_disposition.decided_at)` over the version's cited rows (`postgres_finding_store.py:381`), compared with the previous version's stored `recorded_at` (`:309-311`). The rule is computed only from stored times, and the sentence ("Cites readings accepted after version N-1 was recorded. Version N-1 keeps the records it cited.") is literally true under that rule. A BASIS_REFRESHED successor that cites the same set does not get the note, which is correct.
   - No `knowledge_at` replay: no replay parameter in the client or UI; copy says times "are not a way to view the Finding as of an earlier moment"; tests and the browser suite reject "knowledge".
   - Refusals: 401/403/404/409/503 in plain words; 404 on a pinned ID keeps the address and offers latest only as a link (tested).
2. **Q3 proof.** The vitest Q3 test drives real router history through `SiteFindingFrame`: old -> new (select link) -> Evidence (section link) -> Back x2 -> old, Forward, then a remount on the old address after an append still reads `rid(1)` and says "version 4 replaces it". The omitted-ID test shows "latest at read time" moving from v2 to v3 after an append. The browser suite adds keyboard Tab+Enter, `Page.reload` and Forward-to-Evidence. Genuine.
3. **N1-N4.**
   - N1: `cited_evidence_by_role` is built from the whole `rows` (the full cited set), before `page = rows[offset:offset+limit]` (`finding_read.py:507-516, 546-548`). The Postgres test compares per-role counts and source-ID sets to the stored `finding_revision_evidence`/accepted rows, and the broken fixture asserts the sum equals resolved count (len-1). The reported 7-row-slice mutation would fail that test. Real. UI renders it with "Counted over all N cited records" and states unresolved ones separately.
   - N2: `EVIDENCE_LIFECYCLE_SENTENCE.UNCONFIRMED` now says "stay available in this Finding's history". Fixed.
   - N3: heading and link label switch to "these days"/"overlapping day" when the window spans days. Fixed.
   - N4: `refuse_foreign_work()` runs in `prepare` after prerequisite checks and before any write; it refuses an existing non-empty (or non-directory) `--work` without the marker. Fixed.
4. **Placeholder retirement and baseline 16 -> 15.** The removed S4-01 sentence said "a full history view, fuel and money estimates and actions come later". The history part is now delivered (the History link replaces it). Money and actions are still stated as not available elsewhere on the same page (`SiteFinding.tsx:119-120` "Recommendations and actions, with fuel and money estimates, come later"; `:331` Fuel and cost card). So nothing becomes silently unstated, and the baseline shrink is legitimate. `UNAVAILABLE.history_tab` removal: no remaining references; full backend suite passes.
5. **Closeout docs.**
   - Registry rewording: the three "current text" quotes match `v69-dependency-registry-pilot.json` lines 184, 216 and 316 exactly, and each proposed text removes "knowledge cutoff" consistent with `D-2026-10-11-s3-phase-2-selection-and-read`. The packet notes `finding-history:1#a` is a reviewed mapping. Good.
   - Promotion: proposal is "not applied", gated on review plus owner checkpoint, and promotes only the three named core portions while keeping G-04/Coverage/Use gaps. Not over-promoted. See C3 for one wording slip.
   - Owner walkthrough: uses ports 8866/5366 (open copy) and 8867/5367 (closed copy), private DB names (`assetops_s403_owner_walk`, `assetops_s403_owner_closed`, neither on the protected list nor matching protected markers), and `drop` with `--db` and `--work` for both copies. Commands match the tool's argparse (`links --web-port`, `serve --port --web-port`, `close-gate`, `drop`). See C4 for a usability gap.
   - Packet claims vs evidence: frontend counts, guard counts and the 17 History tests (11 + 4 `it.each` + 2 Q3) match what I saw.

## Carries (Low; none blocks)

- **C1 - drift path untested and its count sentence can read wrongly.** `SiteFindingHistory.tsx:264-278`. If a version is appended between pages, `rows.length` can exceed the first page's `total`. The view then shows "Only 101 of 100 recorded versions could be read, so this list is incomplete" next to the drift note. No test covers the drift branch (`grep drift` finds none). This needs more than 100 versions plus a concurrent append, and the drift note is shown, so it is not misleading in practice. Fix later: when `drift` is set, suppress the "Only X of Y" sentence, and add one vitest case.
- **C2 - `frontend/src/test/settled.ts:22`.** The edit changed the trailing `\.` to `.`, so the loading regex now matches any final character. This is a test-helper looseness only; restore `\.`.
- **C3 - packet "Panels stay partial".** `finding-history:1` is currently `panel_status: "gap"`, not partial. When the coordinator applies the proposal it should set it to partial (ActionEvent still G-04), not complete. Also add `66d001f` (browser suite) to the evidence commit list.
- **C4 - owner walkthrough window/variable scoping.** `$db/$work/$db2/$work2` are set in the windows whose `serve` then blocks. The closed copy and the mock-comparison command need another window where those variables are not defined, and the drop step does not say which window to use. This fails safe (argparse rejects a missing `--db`/`--work` value, and the default DB needs `--include-default`), but the owner may be confused. Fix: tell the owner to re-set the variables in each new window, or inline the literal names.
- **C5 - `aria-current` appears on both the selected `<li>` and its "Select version" link** (`SiteFindingHistory.tsx:321, 384`), so screen readers announce it twice. Minor a11y.
- Carried unchanged from earlier phases: phase-1 C1 `ASSESSMENT_CITATION`; R1/Q4 M4 shape (now whole-set, awaiting Architect); refusal panels print the backend `message`; legacy tab is not browser-captured; ActionEvent/Recommendation/Alternatives are G-04 omissions (task-permitted fail-closed default).

## Residual risk not named in the packet

- The late note relies on `ingestion_disposition.decided_at` as "accepted" time. That is the stored acceptance decision, so it is correct, but a cited record whose disposition row is missing gives `accepted_at = NULL` for that record. `max` ignores it, so the note could be missed (never invented) for such a version. This fails safe.
