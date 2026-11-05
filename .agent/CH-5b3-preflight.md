# CH-5b3 pre-flight (Implementer, lane 1, branch `task/CH-5b3-why-ui` from `417a19efb`)

Scope read: build sheet CH-5b3 entry + SCOPE-1 (binding) + CH5b2-R/R2; mock `frontend/mockups/v70/index.html:411-444`
(and the CSS it uses, :203-239, :31). Kept by SCOPE-1: `F/blocks/OutcomeRow.tsx` (3 CH-6 slots), `F/blocks/Dialog.tsx`
+ `EvidenceTrace`, Why button + dialog on the four board rows and four Portfolio cards (bottom sheet at 390 px), client
304 reuse, L3/L3m 0 new + `perf_budget.py` report mode, captures of board + Portfolio at 1440/390.
Backlogged (not built): ThreadList, Site lens routes, frame-switch removal (BL-01); MeasureTile, FindingCard,
ActionTimeline (BL-02); ratchet `--shrink`.

## Code facts (P1, P5, P6)

- P1 `chainClient`: **does not exist.** No `frontend/src/shell/chainClient.ts`; no frontend file calls any `/chain` route
  (grep `/chain|chainClient` over `frontend/src` finds only `sites/chainRef.ts`). `routeFor` is
  `frontend/src/shell/operatorSiteRoutes.ts:575`; `useLinkFor` is `frontend/src/sites/chainRef.ts:60`.
- Server routes on main: site why `backend/assetops_backend/chain_api.py:222-244` (window from `board_window`, :232,
  i.e. the board's own query keys); estate why :351-378 (window from the estate `scope`, needs the Portfolio
  `from/to/known_at`). Payload `text` = `{title, say, comes_from, days_used, would_change, evidence_ref,
  evidence_label}` (`chain/why.py:219-223`, estate :268-277). Errors: 422 `CATEGORY_UNKNOWN` (:88).
- Board rows: `F/sites/OutcomeBoard.tsx:142-239` (`Row`; headline in `.ob-head` :169). Dialog focus handling:
  `ExplainerDialog` :247-318 (native modal `<dialog>`, Tab trap, Escape, focus return). Used also by the early-warning
  list (comment :245). Board query keys: `outcomeBoardSearch`, `F/sites/outcomeBoardClient.ts:211-221`.
- Portfolio cards: `F/estate/PortfolioOutcomes.tsx:312-360`; a card with a destination is a whole-card `<Link>` (:353).
  Mock card: `div.value-card.oc-pfcard` with `a.value-label.oc-cardlink` stretched by `::after` (index.html:218-222,
  :494) and `.why-btn` lifted with `z-index:2`.
- Callers: `<OutcomeBoard>` in `EvSiteViews.tsx:581`, `SiteWindowOverview.tsx:1113`, `coldSiteViews.tsx:686`, 3 tests;
  `<CategoryCards>` only `EstatePortfolio.tsx:803`.
- P5 (old lists / frame switch consumers): not applicable; R8 is backlogged (BL-01).
- P6: `MA-1-mock-measurements.md` has no Why dialog or button widths (only page widths/heights, :10-23). The size budget
  is therefore the mock CSS: popover `width=min(360, vw-24)` placed under the button; `.sheet` at `innerWidth<=600`
  (index.html:443, :212); `.why-btn` min-height 24 px (:207).
- Ratchet baseline (CH-5b2 packet): api 12, href 24, lit 70, cmp 51, code 3. New `F/blocks/` files must be 0.

## Questions (batched; each has a default I will apply unless overruled)

1. **ThreadList.** The dispatch names it; SCOPE-1 backlogs it (BL-01). Default: not built, no ThreadList tests.
2. **Client.** `chainClient.ts` must be created. Default: `F/shell/chainClient.ts` with `getSiteWhy(code, category,
   boardQuery)` and `getEstateWhy(category, window)`, a per-URL `{etag, body}` memory map, `If-None-Match` on repeat,
   body reused on `304`. Read result union like `OutcomeBoardRead` (loaded / refused / unavailable).
3. **Client injection.** Default: `OutcomeBoard` and `CategoryCards` take an optional `why` client prop defaulting to a
   module-level `createChainClient()`, so the five callers do not change.
4. **Row day line (M1 `ob-days` under the headline, mock :461).** The board body has no days field
   (`outcomeBoardClient.ts:145-174`) and MeasureTile is backlogged. Default: no row-level day line; the days line shows
   only in the dialog's "Days used". MOCK DEVIATION MD-CH5b-4.
5. **Portfolio card markup.** A button cannot sit inside the whole-card `<Link>`. Default: follow the mock: card becomes
   a `div`, the `.value-label` becomes the `Link` with the stretched `::after`, the value sits in `.oc-pfval` with the
   Why button. Existing `estatePortfolio.test.tsx` selectors that read the card as an anchor are updated to the label
   link (no copy or href changes).
6. **Dialog form.** R9 says reuse `ExplainerDialog`'s focus handling. Default: move it to `F/blocks/Dialog.tsx` (board,
   explainer and early warnings import it from there); `EvidenceTrace` renders a modal `<dialog class="conf-pop
   why-pop">` anchored under the button above 600 px and with `.sheet` at <=600 px. The Close button is visible at all
   widths (mock hides it on desktop, :239) because the dialog is modal: MOCK DEVIATION MD-CH5b-5.
7. **Which rows get Why.** Mock shows it only where it wrote a trace (all measured rows). Default: every row except
   `NOT_MEASURED`, and all four Portfolio cards. Button label "Why?"; `aria-label` "Why? {row label}" (title is server
   text not yet loaded): MOCK DEVIATION (mock includes the site name).
8. **Dialog loading / error copy (not in mock).** Default: "Loading why…"-style plain lines: "Loading the reasons…" and
   "The reasons are not available right now" (MOCK DEVIATION, checked against guard V).
9. **L3/L3m and `perf_budget.py --database-url`** need a settled clone, which is a demo prepare under the owner rule
   ("localised tests only, NO full suite, NO demo prepare"). This unit changes no backend code. Default: not run,
   recorded as not run with the owner rule as the blocker; CH-5b2's numbers stand.
10. **Captures at 1440/390** need a running backend with demo data. Default: capture only if a stack is already up
    (read-only); otherwise `layout evidence: not run`, layout claims unverified, plus a jsdom test of the `.sheet` class
    at 390 px via `matchMedia`.
