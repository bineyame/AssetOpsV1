# PL-1 review

Verdict: REJECT until finding 1 is fixed (one-line fix). Behaviour is otherwise correct.

1. HIGH (tsc, acceptance gap vs packet claim "tsc clean"): frontend/src/estate/EstatePortfolio.tsx ~line 913, loadMore refusal branch
   `return { key, first: page, more: [], next: null }` lacks the new required Read fields `windowKey` and `lens`.
   `tsc --noEmit` fails TS2345 there. Fix: `return { ...prev, first: page, more: [], next: null }`.
   (Second tsc error, missing contract-fixtures json, is a sparse-checkout artefact, not the slice.)
2. LOW: tests do not cover a refused load-more after a lens change (the path in finding 1).
3. Info: tests file intact and well-formed (ends cleanly, diff is a pure append; the heredoc slip is noted, no damage).

Checks: vitest src/estate 5 files / 124 tests pass (node_modules junction, removed). Not run: full suite, build, layout evidence (no settled-state layout change).
Items: (1) panel-only loading, aria-busy, no held rows: verified in code+tests. (2) old rows never under new label: yes. (3) whole body from one response, scope ids use held lens: yes. (4) window change/refusal: held only when windowKey equal and held loaded: unchanged. (5) race: effect cleanup `live` guard; cost->risks test valid. (6) Tests 1,2,5 plausibly fail on main (main shows full loading screen); not re-run on main.
