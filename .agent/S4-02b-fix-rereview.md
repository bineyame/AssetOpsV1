# S4-02b fix round 1: fresh Claude re-review

Reviewer: fresh Claude. I did not build S4-02b, review it, or write the fixes. Branch `task/S4-02b-fuel-consequence`,
diff `4eb53e6..68823f30` (`6abb3f5c` code and tests, `68823f30` evidence tool, walkthrough and packet). Scope: H1 and
L1-L4 from `.agent/S4-02b-review.md` (L5 stays a carry), the packet's "Fix round 1" section, and walkthrough steps 5-6
with the Q11/Q14 notes.

## Verdict: ACCEPT

H1 and L1-L4 are fixed as asked and none of the fixes is vacuous. I reverted each fix myself and a unit test failed
every time. For H1 I also confirmed in a real browser that the reverted code puts the amount back on screen under a
closed source, where the evidence tool's new visible-text count would catch it. On my own databases the screen
matches walkthrough steps 5 and 6. Nothing blocks the owner checkpoint. Five Info notes follow; none needs a fix
before merge.

## Item checks

- **H1: fixed.**
  - `FindingConsequence.tsx` `FindingBridge`: the stored head's `BridgeTable` and "How this is worked out" render only
    when `shown` (PRICED, CURRENT and an amount). Every other state renders the headline wording plus the pointer line
    `data-financials-recorded-pointer`, so no amount and no stored price appear in the money panel.
  - Under `AUDIT_ONLY`:
    - `versionWords(r, hideAmounts)` replaces every PRICED version's amount in the list with "No cost shown: the source
      is closed, so this is audit material only";
    - an opened earlier version renders only the closed-source notice, with no `BridgeTable` or disclosure.
  - Observed on my databases (closed gate, head v2):
    - the screen shows the notice, then "For the record only: no current cost", then "No amount is shown while the
      source is closed.";
    - both versions say "No cost shown ... audit material only";
    - the only figure is "1.28 USD per litre" under Price in use (screenshot `%TEMP%\claude\s402brr-shots\s402b-audit-only-desktop.png`).
  - Pinned v1 under a closed gate (headless Chrome `--dump-dom`): the panel holds only "The source is closed, so no
    amount is shown for any version." The page's whole text, including closed disclosures, has no
    `\d+\.\d\d USD` that is not followed by "per litre".
  - With the gate open, recorded amounts remain only in two places, both labelled "kept for the record":
    - the version list;
    - an explicitly opened earlier version, which adds "It is not the current cost".
  - **Can a STALE head's recorded amount in the list bring H1 back? No, in my judgement.**
    - At STALE the list shows "Version 1 · 0.00 to 15.82 USD, at 1.25 USD per litre · kept for the record"
      (screenshot `s402b-stale-desktop.png`). It is in a separate panel and is not bold.
    - It is never called current: `data-consequence-current="false"`, because `current` now also needs the bridge
      to be CURRENT.
    - The money panel above it says "Out of date: no current cost" and points to the list.
    - This is the placement the original review's fix allowed ("version list ... labelled 'kept for the record'").
    - The task requirement is that no old amount is *presented as current*, and it is not. See I2 for the copy.
  - **Is it right to keep "Price in use N.NN USD per litre" under AUDIT_ONLY? Yes.**
    - `PriceInUse` (`SiteFinancials.tsx:498-520`) reads the Site's assumptions at today's time. It does not depend on
      the Finding, the consequence read or the S3 source gate.
    - It is an input price, not a fuel cost, and it does not depend on the Finding's closed source.
  - **Can the exclusion `\d+\.\d\d USD(?! per litre)` hide a cost? Not with the code as it is.**
    - The pattern excludes only a figure followed directly by " per litre".
    - No cost formatter produces that. `range()` output ends in the currency; the list entry ends "USD, at ..."; in
      `textContent` the table amount cell is followed by "Recorded..." or "Modelled...".
    - The money-panel claims (`panelAmounts`) and the unit tests have no exclusion at all: they count any
      `\d+\.\d\d` or any `USD`, so a stray price or cost in the panel would also fail them.
    - See I4 for the limits of the pattern.
- **L1: fixed.** There is a new test, PRICED with currentness STALE. Dropping `c.currentness === "CURRENT"` from
  `Headline` makes it fail (1 failed).
- **L2: fixed.** The AUDIT_ONLY case asserts the `audit_only.statement`. Removing the notice makes it fail (1 failed).
- **L3: fixed.**
  - In `demonstration_label.py`, `_declared` raises `SpecUnreadable`. `lru_cache` does not cache the exception.
  - `demonstration_case` catches it and returns `{"label": "Source not confirmed", "case_id": "unverified", ...}`,
    which the existing `Demonstration` component shows through `demo.label`.
  - An open episode (`end` None) is labelled by the day of its start.
  - The fail-closed result applies to every Site while the spec cannot be read. That over-labels, which is the safe
    direction.
  - The new tests are: open episode, unreadable spec (monkeypatched `_declared`), and the shipped spec parses with at
    least one case. See I1 for a residual test gap.
- **L4: fixed.**
  - A history entry is "the current fuel cost" only when the bridge currentness *and* the consequence read are both
    CURRENT.
  - The new test uses an UNAVAILABLE bridge with a loaded history.
  - Reverting the fix makes 2 tests fail, including the updated `it.each` UNAVAILABLE case, which now expects
    `"false"`.
- **L5:** left as a carry, as the packet states. Unchanged.
- **Walkthrough.**
  - Step 5 (before recompute) and step 6 match my screenshots word for word: the pointer line, the list labelled
    "kept for the record", and Price in use at 1.28.
  - The new section "Not walked, and limits of the demonstration label" says plainly that PRICE_SPANS_WINDOW is tested
    but not walked (Q14). It also gives the Q11 limits: decided by Site and day, not tenant-scoped, under-claim only,
    "Source not confirmed" when unreadable, and authorship at ingestion as an Architect item.
  - It reads plainly. The only wording issue is I2.

## Mutations I ran

Each mutation was applied to committed code, run, and restored. The tree was clean afterwards except for the
coordinator's unrelated `.agent/coordinator-handoff.md`.

| Mutation | Result |
| --- | --- |
| Money panel renders the stored head in every state (`head && body && shown` → `head && body`) | killed, 6 failed in `siteFinancials.test.tsx`. The packet says 7, from its own form of the mutation. In the browser, under a closed gate, the panel showed "0.00 to 16.20 USD" again, which the `panelAmounts` regex counts |
| `versionWords` ignores `hideAmount` | killed (2) |
| Closed-source pinned branch disabled | killed (1) |
| History ignores bridge currentness (L4) | killed (2) |
| `Headline` drops the currentness check (L1) | killed (1) |
| Closed-source notice removed (L2) | killed (1) |
| L3: unreadable spec returns None | killed (1) |
| L3: open episode never labelled | killed (1) |
| L3: `_declared` swallows read errors again (returns an empty spec) | **survived** (I1) |
| L3: drop `lo < day_end` from the open-episode check | survived (I3) |

## Info

- **I1 (test gap, not blocking).**
  - The fail-closed path is tested only by monkeypatching `_declared` to raise. If `_declared` went back to swallowing
    errors, every test would still pass.
  - The shipped-spec test does catch a missing or malformed *shipped* file, which is what the review asked for ("raise,
    *or* a test that the shipped spec parses"), so the ask is met.
  - A stronger test would point `SPEC_PATH` at a missing file with `_declared.cache_clear()` and assert the "Source not
    confirmed" label.
- **I2 (copy, owner).**
  - At STALE the pointer says "Earlier fuel cost versions are listed under Fuel cost versions, kept for the record".
  - The entry it points to is the latest recorded version, now out of date, not an earlier one.
  - This is honest, because nothing is called current, but "Recorded fuel cost versions" would be more exact. The
    owner can rule on it with the other checkpoint copy questions.
- **I3.**
  - No test protects the `lo < day_end` conjunct for an open episode.
  - Without it, an open episode starting after a declared day would be labelled as demonstration data. That is an
    under-claim, so this is Info only.
- **I4.** The evidence tool's `mainAmounts` pattern has three limits. None affects this slice, because the demo is
  USD only and every cost formatter has a fixed shape:
  - it is specific to USD and to two decimal places;
  - it reads `innerText`, so it skips closed disclosures;
  - under AUDIT_ONLY no unrounded amounts reach the page anyway.
  If a second currency is added, it should match `[A-Z]{3}`.
- **I5.** A new KOBO-001 Finding wholly inside 23 Oct 2026 UTC would still carry the "Demonstration data" label. That
  is already named in the walkthrough and is an Architect item (Q11). No change from the original review.

## Checks as observed

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npm.cmd test` (frontend) | **62 files, 1478 passed.** The sandbox esbuild block did not occur |
| `npm.cmd run build` | `✓ built in 3.01s` (chunk-size warning only) |
| `pytest backend/tests/test_s4_assumption_read_api.py -k Demonstration` | 5 passed, 16 deselected. No database needed |
| `tools/check-all.ps1` | All 9 guards passed. Orphan scan: 31 tagged, 12 baselined; ledger: 110 screens |
| Walkthrough `prepare` on `assetops_s402brr_walk` / `assetops_s402brr_empty` (work `s402b-rr`, code from `68823f30`) | Gate open on both. v1-v3 published; 34 work items, 0 failed; latest: 1 PRICED, 8 POWER_MISSING, 2 FINDING_NOT_SUPPORTED, 1 POWER_COVERAGE_GAP |
| `tools/s402b-fuel-cost-evidence.mjs` (APIs 8912/8913, web 5412/5413, CDP 9412) | **90/90 claims passed.** Includes historical/pending/stale/unpriced `panelAmounts: 0` and closed source `panelAmounts: 0, mainAmounts: 0` at 1440 and 390 px. Recompute after v4: 1 appended, 11 replayed; empty store: 31 appended |
| Pinned earlier version under a closed gate (headless Chrome `--dump-dom`) | Closed-source notice only; no cost amount in the page text |
| Full backend suite, Postgres S4 suites | Not run. The fix touches only the label module, whose tests ran. The Postgres suites are unverified by me for this round |
| `tools/layout-evidence.mjs` | Not rerun (it needs its own fixture preconditions). The slice's 1440/390 overflow claims are in the evidence tool and passed |

Clean-up:
- my servers were stopped;
- `assetops_s402brr_walk` and `assetops_s402brr_empty` were dropped, and the `s402b-rr` work folder was removed;
- the owner DBs `assetops_s402bwalk` / `assetops_s402bempty` and ports 8872/8873/5372/5373 were not touched.

## Owner-walkthrough items

- Steps 5 and 6 now describe the screen accurately and can be walked on the owner DBs.
- Ask the owner to explicitly approve two things:
  1. At STALE, the recorded (now out-of-date) figure stays visible in "Fuel cost versions", labelled "kept for the
     record", while the money panel shows no amount (I2 wording).
  2. Under a closed source, the diesel price per litre in "Price in use" stays visible.
- PRICE_SPANS_WINDOW is not walked, and the demonstration label is decided by Site and day. Both are stated in the
  walkthrough.
