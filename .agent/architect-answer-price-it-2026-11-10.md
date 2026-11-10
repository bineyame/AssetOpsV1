# Architect answer: the "price it" journey for unpriced items (2026-11-10)

- Architect: Claude (`assetops-architect`). Binding checked in `.ai/ROLE_CONFIG.md`: Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-walkthrough-2026-11-10.md` item 10): "FOr early warning and general unpriced items on the main page, what is the action from the user to make them priced if needed, is that specified anywhere or is it permaneltyl not supported?"
- Owner answer, item 12.4: "yes", to specifying the journey.
- **Status: specified, for the backlog as BL-68 (`.agent/backlog-post-demo.md`).** Nothing is built. It depends on sign-in (BL-54).
- No mockup is drawn yet. The price form becomes a v7.1 mockup draft for owner approval before any build (mockup-first rule).

## 1. In plain words, for the owner

- **Answer to your question: it is not permanently unsupported, but it was not specified as a user journey.**
  - Prices can be stored today. They are versioned, dated, and say whether each one is an estimate, a contract rate or a recorded purchase.
  - Only an administrator can set them, using a tool, because the app has no sign-in yet. The price route exists, but it refuses every request until sign-in exists ("Sign in to edit Site prices").
- **Two kinds of unpriced item.**
  - **One missing number** (for example "a cost per visit is not set"). The item gets a **"Set a price" link** that opens the Site's price form with that price already chosen. You enter the amount and the date it applies from, and the figure is recalculated.
  - **A missing model or data feed** (battery wear model, demand forecast, bus roster, repair and fault history). One number cannot price these. The item says what is missing, shows what is measured meanwhile, and never shows a guessed amount.
- **Who may change prices:** a named "Pricing editor" role, per Site or portfolio. Every change records who made it, when, why, and from which date it applies.
- **Back-dating is allowed, with a reason.** Figures from that date are recalculated as new versions. The old figures are kept, so "as known at" an earlier time still shows what was known then, and the new figure carries "restated on {date}, was X" (BL-67c).
- **Which model or integration would matter most to a client:** first, **repair and work-order history with repair costs** (it prices four of the seven warnings and is data clients already have). Then the battery wear model, the demand-charge tariff and forecast, the bus roster, and the cold-room stock record (§5).
- **Size: about 2.75 units** after sign-in exists (BL-54), plus 0.5 units for roles if BL-54 delivers sign-in without roles. Not before the client session, apart from one optional honest step (§6).

## 2. What exists today (verified in code)

**Price store.**
- `financials/assumptions.py` holds one series per Site and price key.
- Keys: `diesel_price_per_litre`, `ev_gross_tariff_per_kwh` and `productive_use_price_per_kwh`.
- Each price has a basis: `AUTHORED_ESTIMATE`, `CONTRACT_RATE` or `RECORDED_PURCHASE`.
- Three change kinds, with overlap rules already enforced:
  - `INITIAL`: may be back-dated;
  - `SUCCESSION`: from now on;
  - `CORRECTION`: back-dated or bounded, needs a reason, supersedes what it overlaps, and keeps the old revisions.

**Write route.**
- `POST /api/sites/{site}/financial-assumptions` (`financial_api.py`).
- Refusal order: 401 without a principal; 422 if the body names an actor (the server derives the actor); 403/404 by Site scope; 401 `HUMAN_PRINCIPAL_REQUIRED`.
- The only publisher today is `SYSTEM_PUBLISHER`, through `publish_assumption.py`.

**Unpriced items.**
- Early warnings (`outcomes/warnings.py` `PRICE_NEEDS`):

  | Warning | What it says it needs |
  |---|---|
  | REPEATED | a cost per visit |
  | PLAN_OVERDUE, PLAN_DUE_SOON | repair cost and wear history |
  | BATTERY | a tested battery wear model |
  | CHARGER_FAULT | repair cost and fault history |
  | CONNECTOR_OUT | the bus roster |
  | PEAK | a demand forecast |

- Finding consequences (`estate/placement.py` `_UNPRICED_REASON`):
  - `UNPRICED_PRODUCT_EXPOSURE` (cold excursion);
  - `UNPRICED_START_FAILURE`;
  - `UNPRICED_SERVICE_INTERRUPTION` (EV);
  - `UNPRICED_OTHER`.
- Money lines read `UNPRICED` wherever the needed price key has no current revision. This covers estate Financials (`estate/financials.py`), the Portfolio ("Price not established", `estate/portfolio.py:395`) and verification value (`actions/verification_families.py:246`).

## 3. Classification: which items one price can fix

| Item | Kind | What prices it | Price key (new keys marked +) |
|---|---|---|---|
| Any line that is unpriced only because the diesel price, EV tariff or productive price is missing | **Simple** | the existing key | existing |
| REPEATED (visits without a result) | **Simple** | a cost per visit (call-out plus labour) | + `repair_visit_cost` (currency/visit) |
| EV service interruption (Finding) | **Simple** (lower bound) | a declared cost per interrupted session (penalty, goodwill or lost fee) | + `interrupted_session_cost` (currency/session) |
| PLAN_OVERDUE, PLAN_DUE_SOON | **Half simple** | a planned-repair cost (simple); the risk of the delay needs wear or failure history (data) | + `planned_service_cost` (currency/job); the history comes from Work records |
| CHARGER_FAULT | **Half simple** | a repair cost (simple); how often faults recur needs fault history (data) | + `charger_repair_cost` (currency/repair) |
| Cold excursion (product exposure) | **Data** | the stock in the chamber at the time (inventory record); a declared stock value gives "value at risk", never "loss" | + `stock_value_at_risk` (currency/load), shown as an upper bound only |
| Backup start failure (Cold) | **Data** | the outage consequence: stock record plus excursion | none (follows the cold excursion) |
| BATTERY | **Model** | a tested wear model for that battery chemistry and product, plus a replacement cost | none until the model exists |
| PEAK | **Model / tariff** | a demand-charge tariff (BL-67b, structured tariffs) and a demand forecast | BL-67b |
| CONNECTOR_OUT | **Integration** | the bus roster (which departures depended on that connector) | none until the integration exists |

**Rules.**
- **Server-side keys only.** New keys are a migration plus a units entry, like `productive_use_price_per_kwh` (WALK1-3, migration 0040).
- **Half-simple items show the simple part as priced, and keep the rest open.** For example: "Planned repair: 120 USD (your price) · cost of the delay: needs wear history". The two parts are never added into one figure.
- **A declared "value at risk" is never labelled a loss or a saving.** The same rule as "not billed or collected" applies.

## 4. The journey

### 4.1 From the item to the form

- **Where the link appears:** every unpriced item carries a server-built `price_action` in its read body:
  - early-warning rows on the Portfolio and boards;
  - money cells reading "Price not established" or "Unpriced";
  - Finding "Cost exposure: Not available" tiles;
  - verification "No sales estimate".
- **Two shapes of `price_action`:**
  - `{kind: "SET_PRICE", key, label, href}` for a simple or half-simple item;
  - `{kind: "NEEDS_MODEL", need_key, text, href}` for a model, data or integration item.
- **The words come from the server** (CH-6b2 rule). The frontend renders the link and never decides which items are priceable, so the hard-wiring ratchet is not raised.
- **Link words:**
  - "Set a cost per visit for GreenHarvest →" (simple);
  - "What is needed to price this →" (model).
- **Address:** `/sites/:code/financials/prices?key=repair_visit_cost&from=&to=&known_at=&return=<encoded current address>`. The shared range travels with it (SR); `return` brings the user back.
- **Without the role:** the link still opens the price page, read-only. It shows the current price and its history, and "Prices for this site are set by {role holders}. Ask them to set a cost per visit." The link is never hidden.

### 4.2 The Site price page (`/sites/:code/financials/prices`)

The page lists the Site's prices, one row per key. Each row shows:
- the current value, currency, basis and "applies from";
- who set it, and when;
- a History disclosure: every revision, with its change kind in plain words ("first price", "new price from 1 Dec", "correction from 1 Oct: {reason}"), the person, and the time it was recorded.

The form (opened at `key`) has these fields:
- **Amount**, in the key's unit.
- **Currency** (ISO 4217; defaults to the Site's existing currency for that key).
- **Basis:** "An estimate", "A contract rate" or "A recorded purchase". These are the three stored bases; for a contract rate or recorded purchase, a reference field (contract number or receipt) is suggested.
- **Applies from:** a date, defaulting to today.
  - An earlier date is back-dating, and the form says so.
  - The server, not the user, decides the change kind from the date and the existing series: INITIAL, SUCCESSION or CORRECTION.
- **Reason:** required when back-dating or correcting.

Before saving, a **preview** shows what will change, for example: "This price applies from 1 Oct. 14 figures at GreenHarvest change: 3 early warnings get a cost; Financials 1-31 Oct is restated." The preview comes from a server dry run and writes nothing.

**Save, then return.**
- The user goes back to `return`.
- Affected figures read "Updating…" (the existing `PENDING_RECOMPUTE` state) until they are rebuilt, then read as priced.
- "Why?" shows the price, its version, who set it, and the date.

### 4.3 Who may change prices (roles)

These need BL-54, which provides sign-in and real principals; roles come with it or are added (+0.5).

| Role | Prices |
|---|---|
| Viewer, Operator, Site technician | read only; may ask a pricing editor (the read-only page names them) |
| **Pricing editor** (finance or commercial), scoped per Site or portfolio | publish initial and succession prices for Sites in scope |
| Pricing editor, for a **correction or back-date** | allowed, with a reason. Optional second approval ("four eyes") is a per-portfolio setting, **off** for the first clients |
| Tenant administrator | assigns roles; does not publish prices unless also a pricing editor |

**Server rules.**
- The actor always comes from the verified principal. A body naming an actor stays a 422 (today's rule).
- The `SYSTEM_PUBLISHER` tool path stays for onboarding (BL-55). It is labelled "set by the AssetOps administrator" in the history.

### 4.4 Audit trail

**What every revision stores, append-only (most of it is already in the store):**
- key, value, currency, basis and reference;
- `valid_from` and `valid_to`;
- change kind and reason;
- the revisions it supersedes;
- actor id, the actor's display name at the time, and the authorization basis (role and scope);
- `recorded_at` (the server time).

**Rules.**
- Nothing is edited in place and nothing is deleted. A mistaken price is corrected by a new CORRECTION revision.
- The History disclosure, "Why?" and an export (CSV of the series) all read this one trail.

### 4.5 Effective date, back-dating and restatement

These follow the money rulings, D-MONEY.1-5 and BL-67.
- **From today on (SUCCESSION).** Only future figures change. Nothing is restated.
- **Back-dated (INITIAL over an unpriced past, or CORRECTION over a priced past).**
  - The affected days or periods are rebuilt as **new revisions** through the event register (BL-66, AR rows). The receipts name the new price version (MN-1).
  - The old revisions stay, so "as known at" a time before the change still shows the old figure, or "unpriced".
- **How a restated figure is shown** follows owner question Q2 (BL-67, still open). The Architect's recommendation is (i): the restated figure with "Restated on {date}, was {X}" (BL-67c).
  - An INITIAL over an unpriced past is not a restatement. It reads "Priced on {date}", because there was no earlier amount.
- **Limits.**
  - "Applies from" cannot be before the Site's first readings, because there is nothing to price there.
  - A future-dated correction is refused (that is a SUCCESSION), as the store already rules.
  - Back-dating past a period the client has marked as reported ("closed") needs that period reopened. That is a later feature, and it is listed but not sized here.
- **Before ANY-2 lands:** figures composed on read simply read the new price, and the old figure survives only through `known_at`. That is correct, but slow, and the "was X" note is missing. So restatement notes depend on BL-66 and BL-67c.

## 5. What the screen says for model- or data-dependent items

**Pattern (one block, the same everywhere):**
1. What is measured, which stays shown.
2. What pricing it needs.
3. What AssetOps shows meanwhile.
4. A link "What is needed to price this →", which opens a short page with the list below and "Tell your AssetOps contact you want this". That records interest; it is not a fake form.

There is never an amount, a range or a "≈" until the model exists.

| Item | On-screen words (server text) |
|---|---|
| BATTERY | "Battery wear is measured, not priced. Pricing it needs a tested wear model for this battery type and its replacement cost. Meanwhile: cycles, depth of discharge and time at low charge." |
| PEAK | "The peak is measured, not priced. Pricing it needs your demand-charge tariff and a demand forecast. Meanwhile: the peak, its time, and how close it came to the limit." |
| CONNECTOR_OUT | "Time out of service is measured. What it cost depends on which buses needed this connector, which needs the bus roster. Meanwhile: minutes out of service and sessions affected." |
| CHARGER_FAULT, PLAN_* (half simple) | "Repair cost: {set price or 'Set a repair cost →'}. The cost of the fault coming back needs fault and repair history, which builds up from Work records as repairs are recorded." |
| Cold excursion and start failure | "Time above the limit is measured. The product loss needs the stock in the chamber at the time. {If stock_value_at_risk is set: 'Up to {value} of stock was at risk (your declared value); this is not a loss.'}" |

## 6. Ranked: which models or integrations matter most to a client

Ranked by how many items they price across Site types, how much money is usually at stake, whether clients already hold the data, and the cost to build.

| Rank | Model or integration | Prices | Why this rank | Rough size |
|---|---|---|---|---|
| 1 | **Repair and work-order history with costs** (import from the client's maintenance system, or AssetOps Work records with a cost field) | REPEATED, PLAN_*, CHARGER_FAULT, and the "fault coming back" half | All Site types. Operations and maintenance is the largest controllable cost after fuel. Clients already keep this data. Mostly an import plus a cost field | 1.5-2.5 |
| 2 | **Battery wear model** (per chemistry, validated against field data) | BATTERY; later, the capital side of the Protect outcome | The battery is the most expensive part of a mini-grid that has to be replaced, so the money is large. But the model must be tested before any figure is defensible | 3-5, plus validation |
| 3 | **Demand-charge tariff plus a demand forecast** (BL-67b, then a forecast) | PEAK, and EV depot energy cost | Large for EV depots and grid-tied Sites. The tariff part is BL-67b. The forecast needs history | 1.5-2.0 (tariff), +2 (forecast) |
| 4 | **Bus roster / fleet schedule integration** | CONNECTOR_OUT, the EV service interruption consequence | Very valuable for fleet operators, but one Site type only, and each client's system differs | 1.5-2.5 per system |
| 5 | **Cold-room stock record** (inventory or load log) | cold excursion and start failure | Turns "value at risk" into exposure. Clients rarely record stock per load digitally | 1.0-1.5 |

## 7. Size, dependencies and timing (BL-68)

| Card | Scope | Size |
|---|---|---|
| **PR-1** `price_action` on unpriced items | server field and words on early warnings, money cells, Finding cost tiles and verification value; the frontend link; `return` handling | 0.5 |
| **PR-2** Site price page | read-only view and history for everyone; the form, preview and save for pricing editors; phone and accessibility; mockup first | 0.75 |
| **PR-3** Server write path | admit a signed-in pricing editor (replacing `HUMAN_PRINCIPAL_REQUIRED`); actor fields; dry-run preview route; new keys `repair_visit_cost`, `planned_service_cost`, `charger_repair_cost`, `interrupted_session_cost` and `stock_value_at_risk` (migration and units) | 0.75 |
| **PR-4** Recalculation on publish | a publish marks affected rows for rebuilding in the event register; "Updating…" until rebuilt; "Priced on" and "Restated on" notes read from revisions | 0.25 (on top of BL-66 and BL-67c) |
| **PR-5** "What is needed" blocks | server words for model and data items, the explainer page, and the "tell your contact" record | 0.5 |
| Roles, only if BL-54 has none | pricing editor role, scope per Site or portfolio, optional four-eyes setting | +0.5 |

- **Total: 2.75 units (3.25 if roles are added).**
- **Dependencies:**
  - **BL-54 sign-in (hard).** Without it, the write path stays refused.
  - **BL-66 ANY-2 (soft).** Without it, recalculation is on read, which is correct but slow, and there are no restatement notes.
  - **BL-67c restatement note,** for back-dated prices. Its policy waits on owner Q2.
  - **BL-55 onboarding,** for the administrator path.
- **Before the client session:** only an optional honest step, **PR-1 plus the read-only half of PR-2 (about 0.75 units).**
  - Each unpriced item links to the Site's price page.
  - The page shows the current prices and their history, and "Prices are set by your AssetOps administrator until sign-in is available".
  - It answers "how do I price this?" truthfully, with no write path.
  - The Architect recommends it only if the client session is far enough after ANY-2; otherwise the presenter says it.
- **Mockup:** a v7.1 price-page draft goes to the owner before PR-2 is built.
