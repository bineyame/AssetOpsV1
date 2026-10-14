# S4-02b phase 2a: questions and fail-closed choices (Implementer, 2026-10-14)

The packet, the decisions and the phase-1 review did not settle the points below. For each one the Implementer took the conservative, fail-closed option and continued. None blocks phase 2b.

## Q1. Four currentness states, not one `STALE/PENDING`
The read returns `currentness.state` as one of:
- `CURRENT`: the head's consequence basis equals a fresh derivation;
- `STALE`: a head exists but its basis differs, with reasons `PRICE_SELECTION_CHANGED`, `TECHNICAL_INPUT_CHANGED` or `BASIS_CHANGED`;
- `PENDING`: no consequence yet, with reason `NOT_YET_COMPUTED` or `NOT_YET_COMPUTED_NO_WORK_RECORDED`;
- `HISTORICAL`: the FindingRevision is not the latest.

Only a `CURRENT` head is `presented_as_current`. The bridge shows an amount only for a CURRENT PRICED head.

**Ruling needed:** whether the UI should merge `STALE` and `PENDING` into the packet's single "STALE/PENDING" label. Phase 2b can map them either way.

## Q2. Currentness is a fresh derivation at read time, not a price-only comparison
The read runs `load_input` + `quantify` + the window price selection for the selected latest FindingRevision, then compares the full consequence basis with the head's. After M1, that basis holds the selected price revision, or the window-clipped price boundaries, plus the technical digest.

Price-only comparison would miss one case. A late-accepted power reading inside the window changes the technical input, yet no work row is enqueued for evidence acceptance (0011 triggers fire only on price publication and FindingRevision insert). The head is then shown `STALE (TECHNICAL_INPUT_CHANGED)`, never as current, until a recompute runs.

**Ruling needed:** whether evidence acceptance should also enqueue consequence work. That would be a new trigger on `accepted_evidence`, outside this phase.

## Q3. Replay of a non-head basis (phase-1 Q6)
An unchanged basis replays the stored ID. If an exact earlier state ever recurred (A, then B, then A), `append` would return revision 1 while the head is revision 2. The read would then report `STALE` until a different state appends.

This is fail-closed, and in practice unreachable:
- price revisions and FindingRevisions are append-only with fresh IDs;
- the M1 basis carries revision IDs, so a "return" to an earlier price is always a new revision ID.

## Q4. Pre-0011 data (review L4): both options taken
- **Bootstrap.** Migration 0011 enqueues one `FINDING_REVISION_APPENDED` work row for every FindingRevision that exists when it runs. This is the same row the trigger would have written. The test downgrades to 0010 and re-upgrades with Findings present.
- **Defence in depth.** The read reports "no consequence" as `PENDING`, never as absent or zero. If no work row exists either, the reason is `NOT_YET_COMPUTED_NO_WORK_RECORDED`.

Price revisions are not backfilled. The Finding work prices with the current timeline, which already includes them.

## Q5. Work targets
- `FINDING_REVISION_APPENDED` recomputes that exact revision, even if a later one has superseded it. Per the packet, "a new FindingRevision produces its own linked consequence."
- `ASSUMPTION_PUBLISHED` recomputes only each overlapping Finding's **latest** revision. Superseded revisions keep their consequences as history and are not repriced.

## Q6. The worker is a one-shot CLI, not a daemon
There is no in-process scheduler:
- `python -m assetops_backend.recompute_consequences run --site KOBO-001` drains the Site's work;
- `pending` lists what is left.

Between a publication and the next run, the read shows `STALE`, never the old amount as current.

Failure handling:
- A failed item records a typed attempt, one of `STORE_UNAVAILABLE`, `FINDING_REVISION_NOT_FOUND` or `RECOMPUTE_FAILED`, and stays pending.
- A concurrent worker that finds the work already SUCCEEDED records nothing (`skip_if_succeeded`).
- There is no retry cap.

**Ruling needed:** whether a deployment needs a scheduled runner. That is an operations choice.

## Q7. Bridge shape changed
`GET .../findings/{id}/financials` no longer returns the S4-02a placeholder:
- `consequence.amount` is `{low, high}` display strings, or `null`;
- new fields: `currentness`, `consequence_revision_id`, `quantity_reason`, `price_reason`;
- with no consequence store configured, `state` is `UNAVAILABLE` (typed, no amount) rather than a 503 for the whole bridge.

The S4-02a frontend types (`frontend/src/sites/financialsClient.ts`) are not updated; that is phase 2b. Until 2b lands, the S4-02a Financials screen (`SiteFinancials.tsx:481`) words every state other than `QUANTITY_UNAVAILABLE` as "No price for the whole window". That includes `PRICED`, `STALE`, `PENDING` and `UNAVAILABLE`, and it is wrong for all of them. The S4-02a UI must therefore not be shown over a 2a database before 2b.

## Q8. Display rounding
- **Minor units:** a fixed ISO 4217 table of 33 currencies.
- **Unknown currency:** gives `display.state = MINOR_UNIT_UNKNOWN` with no rounded amount, and the bridge shows no amount. The unrounded value stays in `amount`.
- **Quantity:** displayed rounded up to 0.01 L (`quantity.high_display`).
- **Text form:** the unrounded `amount.high` text is the stored numeric's text, so the scale may vary (`3.5200`). Clients compare it as a Decimal.

## Q9. Demonstration producer database
`tools/s402b_power_cases.py` runs the unchanged S4 producer plus P01-power. It runs into a database of its own, default `assetops_s402bcases`, and refuses any name that does not start with `assetops_s402b`. It never touches `assetops_s4cases`.

The demonstration day is 2026-10-23, which is clear of every S4 case day.
