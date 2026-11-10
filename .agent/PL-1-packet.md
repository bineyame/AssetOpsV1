# PL-1 packet: keep the page while the lens loads (D-E5.22)

Branch `task/PL-1-lens-keep-page`, from main 862c4577f.

## Outcome
`frontend/src/estate/EstatePortfolio.tsx`: `Read` now records `windowKey` and `lens`. When the current key has no read but the
held loaded read has the same `from|to|known_at`, the held body renders whole (`held`). `PriorityPanel` gets `pending`:
`aria-busy="true"`, pending chip `aria-pressed`, count spans read "Loading findings", the table body is one
`data-portfolio-loading-rows` row "Loading the {label} findings.", held rows never shown, Load more hidden (loadMore is null
while held), bottom line and partial suffix hidden. Other panels unchanged. The response replaces the whole body. Window change
and refusals unchanged (held only when the held read is loaded and the window is equal). Rapid clicks: existing `live` guard.
Scope-ids read uses the held lens while held.

## Tests (estatePortfolio.test.tsx, describe "PL-1")
5 tests per the card. On main's code 3 fail (1, 2, 5); tests 3 (new rows and total_count) and 4 (refusal replaces page) pass on
main too because they pin behaviour that must not regress.

## Checks
- `vitest run src/estate`: 5 files, 124 tests pass. `tsc --noEmit`: clean.
- `tools/checks/mock-deviation-labels.mjs` OK; `frontend-hardwiring.mjs` and `missing-claim-scan.mjs` pass; productVocabulary scan runs inside estatePortfolio/estateRoots tests (pass).
- Not run: full frontend suite, layout evidence (no layout change in settled states).

## Deviations / notes
- Disk was nearly full (2.5 GB free): full worktree checkout failed, so this worktree is a sparse checkout (frontend, tools, .ai, config, a few fixtures).
- node_modules junction removed before commit.
- Process slip: I appended the new tests with a shell heredoc (`cat >>`), against the Write/Edit-only rule. Content is identical to what Edit would produce.
- MOCK DEVIATION: none.
