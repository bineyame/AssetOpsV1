# POLISH-PB-2 Kobo board, verification page and display codes

Status: in_review
USER_REVIEW_REQUIRED: false
Lane: B (frontend and tools). Units: 6 (+0.5, Addendum 8 Q6). Branch `task/POLISH-PB-2-kobo-board`.

The spec is `.agent/build-sheet-POLISH.md`: §1.1 (frontend money panel), §3 (record codes, ids), the Kobo and
Verification rows of §3.1, §5 Lane B "PB-2", §7 (R655, R656; close R626), Addendum 3 (captures), Addendum 4 (no
run/ran/running), Addendum 5 (only `[data-technical-details]` hides ids), Addendum 7 (skip the rows done in PB-1) and
Addendum 8 (PB-2 pre-flight rulings). This file states scope only; the sheet is the contract. Pre-flight answers are
in Addendum 8 and the packet `.agent/POLISH-PB-2-packet.md`.

## Scope

- Kobo Overview §3.1 rows not done in PB-1, with the Addendum 4 swaps, and the P-06 zero money panel (§1.1).
- Technical details regions: `ui/TechnicalDetails.tsx`, `Disclosure` `technical` prop; the Kobo board,
  verification page, SiteAction History and `SourceProvenanceRecord` id lists (Addendum 8 Q5).
- Verification rows of §3.1; the claim label.
- `ui/displayCode.ts` and its use at the ~25 visible record-code render sites, PB-3 files included (Addendum 8 Q6).
- PA-2a hand-offs: `mini.FINDING_TITLE` with `findingWords.ts` `LIFECYCLE_WORDS`; `GAPS_NO_READINGS` (Q1); frontend
  fixtures aligned with the new server strings; essential-service role words (Q2).

## Not in scope

Cold/EV panel headings and the Portfolio "scenario" words (PB-3, Addendum 8 Q3/Q4); other server text (lane A);
`ExactReferences` call sites outside the PB-2 screens (PB-3).

## Checks

- Scoped vitest (`sites`, `shell`, `work`, `estate`, `ui`, `test`); `tsc --noEmit`; the backend tests that pin
  `FINDING_TITLE` and the gap text; `tools\check-all.ps1` 12/12.
- Captures (strict): `kobo-board-S`, `kobo-board-S1`, `kobo-board-S-open`, `kobo-verification`, plus
  `maintenance-preventive` and `wr-overview` for display codes.
- Full `npx vitest run` once at the end.
