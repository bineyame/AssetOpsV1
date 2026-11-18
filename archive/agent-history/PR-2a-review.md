# PR-2a review: read-only Site price page (2026-11-12)

- **Reviewer:** fresh Claude reviewer (did not author). Read-only; no Postgres run.
- **Revision:** `task/PR-2a-price-page` head `0b27e10d4`, diff vs main `49c0ca628`.
- **Verdict:** ACCEPT. No High or Medium findings. The Low findings below are optional on the branch.

## Checked and held

- **Read-only.** The router has one route, `GET /api/sites/{site_code}/prices` (`backend/assetops_backend/price_page_api.py:43`). The frontend has no form, input or Save; `sitePrices.test.tsx:134` asserts this.
- **`known_at` end to end.**
  - Client: `pricePageClient.ts` sends `known_at`.
  - API: `price_page_api.py:59-66` refuses an unzoned value with 422 and passes it as `recorded_at` to `AssumptionReadService.series`.
  - Composer: `price_page.py:215` states the cutoff, and the page renders it (`SitePrices.tsx:145`).
  - The Postgres test `test_known_at_reads_the_history_as_recorded_then` covers it. It was not rerun here.
- **Attribution matches PR-3.**
  - PR-2a keys "Entered by site admin" on actor id `service:operator-entry` (`price_page.py:28`).
  - PR-3 (`task/PR-3-price-entry` `fc67edd70`) publishes with `SITE_ADMIN_PRICE_PUBLISHER.actor_id = ENTRY_PRINCIPAL` (`financials/assumptions.py:81-82`), and `work/operational_entry.py:25` sets `ENTRY_PRINCIPAL = "service:operator-entry"`.
  - The read body maps `actor.id` from `actor_id` (`assumption_read.py:43`).
  - The values match.
- **Forward keeps the range.** `SiteAnalyticsFrames.tsx:1523-1531` keeps `from`, `to` and `known_at`, and only for an unpinned, non-cold address. `sitePrices.test.tsx:288` covers it.
- **`renderBelow(row)` seam.** It renders a full-width `<tr data-price-slot>` under the price row, before History, and nothing for null or undefined (`SitePrices.tsx:111-115`). `sitePrices.test.tsx:240` pins it.
- **Honest states.**
  - A future key reads "Not set" with the sentence and no button.
  - A stored key with no price reads "Not set" with no sentence (`price_page.py:173-175`).
  - `need` opens Part C with the server's words and no "Tell your contact" (`SitePrices.tsx:41-49`). An unknown need gives `null`.
- **Access and scope.**
  - The access and scope are the same as the price read's: `development_access` by default, `registry.imported` (which `ledger_scope` wraps), and the same 401/403/404/422/503 order.
  - One difference: the price page also maps `SiteStoreUnavailable` to 503.
- **Font sizes.** `sitePrices.css` sets them only through `var(--text-*)`.
- **Mock deviations.** D1-D4 are labelled in the packet, and the mock-deviation guard passed per the packet.

## Findings (all Low)

- **L1:** `frontend/src/sites/pricePageClient.ts`, the `case 422` beside `case 404`.
  - What is wrong: a 422 `INSTANT_NOT_ZONED` (a `known_at` with no offset) reads "No prices can be read for this site." followed by the server message.
  - Why it matters: the page reports a malformed date as a missing Site.
  - Fix: give 422 its own plain sentence.
- **L2:** `frontend/src/shell/SitePricesFrame.tsx:151`.
  - What is wrong: the subtitle hard-codes the intro sentence instead of rendering the server's `intro`. The file also keeps a copy of the sign-in sentence, `PRICES_SIGN_IN_TEXT`, for tests.
  - Why it matters: it breaks the packet's claim that "every word is the server's", and the two copies can drift apart.
- **L3:** `backend/assetops_backend/financials/price_page.py:160`.
  - What is wrong: the History reads "replaced by a later correction", but the mock says "replaced by the correction above".
  - Why it matters: this is a wording change, and the packet does not label it.
- **L4:** `backend/assetops_backend/price_page_api.py:66`.
  - What is wrong: `series` is read with the default limit of 200 revisions, but the History claims to show "every revision".
  - Why it matters: past 200 revisions the History is cut silently. That is unlikely before the demo.
- **L5:** `.agent/PR-2a-packet.md:76`.
  - What is wrong: the slice is layout-sensitive (a dense table that stacks at 760 px), and its layout evidence is "not run". The packet does not name the blocking precondition.
  - Fix: name it in the packet. The stacking stays unverified until it is run.

## Noted, not ruled (with the Architect)

- **Q1 (forwarding):**
  - Cold Sites keep the declarations screen at `/financials/assumptions`, but the subtab now says "Prices" is the current page while it shows the declarations.
  - The declarations are reachable only through "Review assumptions".
- **Q2:** EV's own subtabs still read "Assumptions".
- **Q3 (rows per Site type):**
  - The mock's GreenHarvest example lists 5 rows, including "Stock value at risk". The built MINIGRID list has 4.
  - The mock's row order differs from the built order (stored keys first).

## Checks run (this revision)

- **Backend, no database:** `test_pr2a_price_page.py`, `test_pr1_price_action.py` and `test_s4_assumption_read_api.py`: 46 passed, 0 failed, 4.4 s.
- **Typecheck:** `npx.cmd tsc --noEmit -p .`: exit 0.
- **vitest on the touched files:** `sitePrices`, `priceAction`, `siteFinancials` and `miniDecisions`: 4 files, 170 passed.
- **vitest on `simulatorLabGate` and `sitesIndexRoute`:** 4 failed. These are the same 4 the packet names, all "expected `<button>` length 0, got 1".
  - Not rerun on main: this machine has no clean main checkout, and the main worktree has local edits.
  - The diff does not touch the Sites index or the create-flow gate code, which supports the builder's "also fails on main" claim.
- **Not run:**
  - the Postgres file;
  - the guards (the packet reports 19 of 19 after the merge);
  - the production build;
  - the layout evidence.
