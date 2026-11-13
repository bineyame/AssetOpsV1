# UQ-FI-3 packet (lane D, branch task/UQ-FI-3, stacked on task/UQ-FI-1-2 at c66937b97)

Spec: rev 7, 7.2 UQ-FI-3 row (`architect-sequence-client-scope-2026-11-11.md`); D-UQFI.1-10 (`build-sheet-OWN-GAPS-2026-11-08.md`). Owner go: `owner-proceed-waiting-items-2026-11-13.md` (provisional). Visual targets: v72 `foundation-sheet.html` (Outcome card, reading-state chips), `portfolio-hifi.html` (`.kpi` card, state chips).
Commits: `fc838d529` build; `4ba7cff0d` main merged (bd4c0086e); `499e9245a` type codemod rerun after the merge (D-UQFI.10).

## Delivered
- **Figure size: 30 px.** `--text-figure: var(--font-size-800)` (+ `--leading-figure` 38 px) in `ui/tokens.css`, a single token. Per D-UQFI.7 only the Portfolio card figure uses it (`.oc-pfcard .value-number.oc-pffig`); every other figure stays at 20 px. To change: edit the one token.
- **One-figure Portfolio card** (`estate/PortfolioOutcomes.tsx` `CategoryCards`): top line = icon + name link + "Why?"; one figure (server `value`); one sentence (server `detail`); basis line (server `basis_text`). No new words.
- **Qualifiers behind "Why?"** (`CardQualifiers`, passed to `EvidenceTrace` as new optional `more`, shown under the server words in every read state): definition, "Different days:" line, Grow parts, fuel lines + note, value lines + note, body note, per-Site states. Same server text and data hooks, same order.
- **`ui/StatusPill.tsx`** + `ui/status-pill.css`: state code -> sheet look (colour + symbol), word = caller's (server `state_label`); no `site_type` branch. Light tokens `--color-status-{complete,partial,noreadings,notanalysed,neutral,accent}-{bg,text,border}` + `--chip-height` in `tokens.css` (sheet palette values). Used by: Site board outcome rows (`sites/OutcomeBoard.tsx`, both state chips), Portfolio matrix cells, matrix key, per-Site states behind "Why?".
- Matrix cells are now neutral (the pill carries the state colour); dead `.oc-cell.tone-*`, `.oc-key i`, `.oc-sitedots i` rules removed. `OutcomeCardValue` (now unused) removed from `blocks/OutcomeRow.tsx`.

## Mapping (Q1 below)
NEEDS_ATTENTION partial+alert, OPPORTUNITY accent+trend, WATCH neutral, NOT_MEASURED notanalysed (dashed) - as portfolio-hifi draws them. Provisional (not drawn anywhere): ON_TRACK complete+check, UNKNOWN noreadings+ring, NO_OBJECTIVE neutral, NOT_APPLICABLE notanalysed; unrecognised -> neutral.

## Tests and checks (revision 499e9245a unless noted)
- `npx tsc --noEmit`: exit 0.
- New: `ui/__tests__/statusPill.test.tsx` (10: one per state x8, unknown code, tokens/CSS); `estatePortfolio.test.tsx` `uqfi3OneFigureOneSentenceTheBasisAndTheQualifiersBehindWhy` (one figure per card, card hook set exact, Why? hook set per card exact, 30 px token); `outcomeBoard.test.tsx` `uqfi3EveryRowStateIsTheOneStatusPill`.
- Changed: Portfolio card qualifier assertions now read behind "Why?" (`whyOf` helper); `lines()` ignores svg; key asserts pill codes; board chip selectors -> `[data-status-pill]`.
- Non-vacuous: days line put back on the card + NEEDS_ATTENTION look changed -> 2 failures; reverted by `git checkout`.
- vitest at fc838d529: 92 files (every `/sites/[A-Z]|from=20` file + CSS/EvidenceTrace/OutcomeRow readers) 92 passed, 2443 tests. After the merge: the 5 test files main changed + Portfolio/board/StatusPill: 8 files, 212 passed.
- Guards alone: style ratchet pass (rawHex 458; failed after the merge on SR-6b `0.85em` until the codemod rerun); mock-deviation labels OK (174 files); hard-wiring pass; missing-claim pass. check-all: for coordinator. Layout evidence / captures: not run (no serve/DB per lane rules) - card fit at 1280/390 with a 30 px figure is unverified.
- React `act()` warnings from EvidenceTrace's async load in the Portfolio test (warnings only).

## Known deviations
- "Why?" was a server-chain dialog; it now also carries the card's qualifiers below the chain text (rev 7: "Anything else moves behind the existing Why? disclosure").
- Portfolio card has no state pill in its foot (hifi shows one): the server card has a tone, not a state code; inventing one would be new semantics.
- Board "potential" chip (`oc-chip tone-green`) unchanged: it is not a state code.
- hifi per-card charts not built (out of scope; hifi's own MOCK DEVIATION).

## Questions for the Architect
1. Rev 7 says "the six reading states (on the sheet)", but the sheet's reading words are eight readings-coverage states (Complete ... Not analysed yet) and neither call site shows a reading state. Built on the six outcome states (the Portfolio key: Needs attention, Watch, Opportunity, On track, Unknown, Not measured yet), which both call sites show. Confirm, and rule the looks for On track / Unknown / No objective / N/A (not drawn), and whether Watch / Not measured get a symbol (hifi draws none).
2. Should the estate card carry an estate-level state pill (hifi foot)? Needs a server state on `EstatePortfolioCard`.
