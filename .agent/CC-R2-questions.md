# CC-R2 questions for the Architect (Lane C)

Branch `task/CC-R2-placement`. Owner rule: no isolated design decisions. Everything else in CC-R2 is built. Each
item below is built exactly as the spec says, or left unchanged, and I stopped there.

## CC-R2-Q1 Confidence reason texts trip the product vocabulary guard (same class as CC-R1-Q1)

The spec fixes the `confidence_reasons` texts as "Supported claim" / "Unconfirmed claim" and
"Registered simulation source" (build spec CC-R2 "Confidence", Q-C19/Q-C20). The Portfolio Confidence column shows
them joined by " · " (CC-R2 "Frontend"). `claim` and `simulation` are guarded terms in
`frontend/src/test/productVocabulary.json` (D-2026-10-04). CC-R1-Q1 kept `simulated` guarded and changed the
verdict label to "test data".

- **Built:** the backend sends the spec texts verbatim (`estate/placement.py:_confidence`, `_SOURCE_TEXT`), and the
  frontend shows them. No vocabulary scan runs on the Confidence cell. The placement reason lines, group headings
  and policy text contain no guarded term.
- **Needs:** the ruled texts for the two lifecycle reasons and the `REGISTERED_SIMULATION` source reason. For
  example "Supported Finding" / "Unconfirmed Finding" and "Generated test data source" (matching "Generated test
  data"). Alternatively, a ruling that the Confidence cell is exempt. Changing them touches only the texts in
  `placement.py`, `test_cc_placement.py`, `test_cc_placement_postgres.py`, and `portfolioFixtures.ts`.

## CC-R2-Q2 The W3-03 portfolio fixture has no EV Finding row

CC-00 fact, from a tier-2 run on `assetops_cc2_test`: `build_portfolio_fixture` (cold `excursion`, EV `complete`,
KOBO-001 W1) gives three Portfolio members:

- two cold Findings, `COLD_EXCURSION` and `COLD_START_FAILURE`, both with a null `episode_end`;
- the KOBO-001 W1 row.

The EV `complete` producer selects no EV Finding. The gate "the EV row is UNPRICED_RISK /
UNPRICED_SERVICE_INTERRUPTION unless CC-00 records rank 1 or 2" therefore has no row to assert.

- **Built:** `test_cc_placement_postgres.py` pins the CC-00 fact (`ev == []`). It asserts that `lens=risks` equals
  the set of cold and EV rows, which here is the two cold rows. It pins both cold rows to ACT_NOW /
  `EPISODE_OPEN` + `NO_ACTION_RECORDED`. EV placement is covered by the pure test only
  (`test_cc_placement.py::test_rule_5_unpriced_risk`, `EV_INTERRUPTION`).
- **Needs:** one of the following.
  - (a) Accept pure-only EV coverage for CC-R2.
  - (b) Name an existing producer with a selected EV interruption Finding to assert against. One possibility is a
    W3-01 golden EV case other than `complete`; I have not checked which one selects one.

## CC-R2-Q3 Panel copy now contradicts the Confidence column

`frontend/src/estate/EstatePortfolio.tsx` has a panel-bottom line, "Priority and confidence are not assessed for
these records." It is computed from `priority !== null && confidence !== null`, and `priority` is always null. The
panel subtitle `portfolioWords.ts:PRIORITY_SUBTITLE` says "...priority and confidence appear when assessed." Every
Portfolio row now carries a confidence, so the bottom line is no longer true. The spec does not cover either text.

- **Built:** both left unchanged. `estatePortfolio.test.tsx:136` still asserts the old bottom line.
- **Needs:** the replacement wording, or a ruling to remove the line. The `<details>` "How placement works" already
  sits under the table.

## CC-R2-Q4 The tier-3 capture has no estate Portfolio claim

Build spec §0.3 says tier-3 evidence uses `tools/s602b-verification-evidence.mjs` ("estate Portfolio for case
`estate`"). Adding `estate` to the walkthrough `CASES` makes that script's generic `casesSuite` check the F01
verification page (`expect.current_state` VERIFIED). The script has no Portfolio page claim, though: group
headings, reason lines and the three placements. The `.mjs` is not in the CC-R2 file list.

- **Built:** no change to the `.mjs`.
- **Needs:** confirmation that the coordinator's tier-3 step adds the Portfolio claim to the `.mjs`, or a ruling
  that CC-R2 adds it in a follow-up commit before capture.
