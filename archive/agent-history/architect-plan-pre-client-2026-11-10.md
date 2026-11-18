# Architect plan: everything before the client session (2026-11-10)

- Architect: Claude (`assetops-architect`). Binding checked in `.ai/ROLE_CONFIG.md`: Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-walkthrough-2026-11-10.md`, item 13): "1. english, french and swhaili 2. lets have one, i am not sure 3.dark and white for the user to select 4.absolutely (even anything below 8 uints is ok)".
- Inputs: `architect-answer-ui-quality-2026-11-10.md` (BL-69), `architect-proposal-portfolio-layout-2026-11-10.md` (PF, SR, scale design), `architect-answer-any-range-speed-2026-11-10.md` (ANY-1/2), `architect-answer-money-snapshot-2026-11-10.md` (MN-1..3), `architect-answer-price-it-2026-11-10.md` (BL-68), `backlog-post-demo.md`, `coordinator-handoff.md`, the D-E5.25-28 Findings cards rulings in `build-sheet-OWN-GAPS-2026-11-08.md`.
- **Status:** a plan. No product code changes. The UI subset starts with a v7.2 foundation sheet that the owner approves before any build, as every UI stage does.

## 1. In plain words, for the owner

- **The UI work before the client session is 7.5 units**, inside your "below 8". It gives:
  - the quick wins (larger type, money with thousands separators, one style for empty and loading panels, no ISO dates in link text);
  - a proper design system: colour, type and spacing tokens, so the whole app has **a light theme and a dark theme that each user picks** (it follows the computer's setting until they choose);
  - **one brand font, Inter**, self-hosted, with numbers that line up in tables;
  - **the language foundation for English, French and Swahili**: every on-screen word moved into a message catalogue (on the page and on the server), dates, numbers and money formatted the way each language expects, and a language switcher in the top bar.
- **French and Swahili translations are drafted inside the 7.5 units, but they are shown to a client only after a person who reads each language well has reviewed them.** Swahili needs a native speaker. French needs a fluent reviewer. Until a language is reviewed, the switcher does not offer it. The client session is therefore safe in English whatever happens, and French or Swahili are a bonus if the reviews land in time.
- **Nothing is styled twice.** The tokens and themes land first. The shared date range, the Portfolio tabs and the scalable outcomes are then built straight onto them. The words are moved into the catalogue last, after the Portfolio wording change, so each word moves once.
- **Everything before the client session adds up to about 26 units plus FR-B**, in two lanes:
  - Lane A (server speed): FR-B, then the fixes from the non-Kobo Site audit (a placeholder), then the fast pages for boards (ANY-1) and for the Portfolio (ANY-2, with the stored money receipts and the scalable outcome rows), then the server words into the catalogue.
  - Lane B (screens): the design system, the shared date range, the Portfolio tabs and outcomes, then the page words into the catalogue and the translations.
  - Then one final demo build, checks, new pictures and the updated scripts.
- **Calendar:** the build work finishes around **Tue 24 to Fri 27 Nov**. The final build and walkthrough take 2-3 more working days. **A realistic client session is Tue 1 to Tue 8 Dec; the earliest credible date is Mon 30 Nov.**
- **What I need from you:** set the client session date; approve the v7.2 foundation sheet (about Fri 13 Nov); approve the final v7.1 Portfolio-tabs mockup with the shared date range; name a native Swahili reviewer and a fluent French reviewer (about one day each, around 25-27 Nov); approve Inter as the font.

## 2. The pre-client UI subset (UQ, 7.5 units)

### 2.1 What it contains

| Card | Scope | Size | Comes from |
|---|---|---|---|
| **UQ-0** v7.2 foundation sheet | One mockup sheet, light and dark side by side: the token tiers, the 8-step type scale (12 px floor, 14 px body), the spacing scale, Inter specimens with tabular figures, the status colours in both themes, `EmptyState`, `Skeleton`, and the top bar holding the shared date range, the language switcher and the theme control. It also redraws the v7.1 Portfolio tab row, coverage line and one outcomes-list row in the new tokens, with French and Swahili text-length samples. **The owner approves it before UQ-1.** It replaces the v6.9/v7.0 type scale and colours as the spec for **look only**; v7.1 stays the layout spec for the Portfolio and the shared date range. | 0.5 | QW sheet (0.25) widened for themes, font and switcher |
| **UQ-1** Tokens, type and font | `ui/tokens.css` becomes three tiers: primitive (colours, type scale, 4 px spacing, radii, shadows, breakpoints), semantic (surface, text, border, the six status states, focus, data series) and component. The 12 px floor and 14 px body (QW item 1). Inter self-hosted (section 3), `font-variant-numeric: tabular-nums` on numbers and tables. The **style ratchet** in `tools/checks` lands here: shrink-only counts of raw hex colours, raw `font-size` values and physical left/right properties per file outside `ui/tokens.css`, so every file written or touched from here on uses semantic tokens. | 1.25 | Stage 1 tokens (1.0) + font (0.25 of stage 3) + style ratchet (from stage 1 guards) |
| **UQ-2** Light and dark themes | The 228 raw hex values in the 35 CSS files and the ~19 inline SVGs move to semantic tokens (`currentColor` or token variables in SVG). Dark values for every semantic token, contrast-checked to WCAG AA in both themes, badge tones checked against their own backgrounds as today. Theme control in the top bar: System (default), Light, Dark. The choice is a per-browser convenience in `localStorage` (wrapped in try/catch; System if storage is blocked), applied by a small inline script in `index.html` before first paint, so the page never flashes the wrong theme. `prefers-reduced-motion` rule added with it. Client-screen captures gain a dark set. | 1.0 | Stage 1 dark values (+0.5 to ship) |
| **UQ-3** States and quick wins | `EmptyState` (cause + next step where one exists), `Skeleton`, and the rule that a panel which can only say "nothing" collapses into one "Not shown yet, and why" line on the Site boards (QW item 3). Link text never shows an ISO date (QW item 4). QW item 5 (matrix header word-break) is **dropped**: PF-O replaces the matrix. | 0.5 | QW items 3-5; part of stage 1 components |
| **UQ-4** Locale and formats | The locale model: **language** only (display time zone and reporting currency stay as today: UTC on estate pages, Site-local on Site pages, each amount in its own currency). `ui/time.ts` and `ui/money.ts` go through `Intl` (month names, grouping, currency symbol placement; QW item 2). Shown decimals stay exactly as today; only grouping and symbols change. `<html lang>` follows the language. The language switcher sits in the top bar; the choice is kept like the theme, defaulting to the browser's languages matched to en/fr/sw, else English. Every API call sends `Accept-Language`. | 0.75 | Stage 3 formats + `lang` |
| **UQ-5** Page words into the catalogue | A frontend message catalogue (keys, parameters, plurals through `Intl.PluralRules`, select), with no new dependency. The 12 `*Words.ts` files and the remaining literal strings in JSX move to the English catalogue. | 1.0 | Stage 3 catalogue, frontend part |
| **UQ-6a** Server catalogue seam | The server message contract: a word in a body is rendered from `{key, params}` for the request's locale at read time, never stored as composed text. Locale resolution from `Accept-Language`, `Content-Language` on the response. Number, date and money formatting on the server uses the same CLDR rules as the browser (Babel, BSD licence), with a parity test against fixed browser `Intl` outputs. **It must land before ANY-1's AR-1 freezes the stored-row body shape** (section 4.3). | 0.25 | Stage 3 catalogue, server part |
| **UQ-6b** Server words into the catalogue | `chain/vocabulary.py`, `site_outcomes/*`, `outcomes/warnings.py`, `estate/*` and the other composed sentences move to keyed messages with ICU-style parameters; sentence fragments joined with " · " in code become list parameters. An inventory of prose that is **stored** in rows by producers: where a client screen shows it, it is rendered from a key at read; operator-entered text is never translated. | 1.5 | Stage 3 catalogue, server part |
| **UQ-7** Pseudo-locale and string guard | A pseudo-locale (accented, 30% longer) runs over the client-screen captures to find clipped text and words that missed the catalogue. A shrink-only ratchet on literal strings in JSX and composed server text. | 0.25 | Stage 3 pseudo-locale |
| **UQ-8** French and Swahili drafts | A glossary of about 60 domain terms first (complete readings, partial readings, Finding, Action, verified, mini-grid, cold room, unexplained fuel, and so on), then drafted fr and sw catalogues for every key on the client screens, then a layout pass in both languages and both themes. **Release rule:** the switcher offers a language only when its catalogue covers every client-screen key and its reviewer has signed off. | 0.5 | New (translation drafting; human review is outside the units) |
| **Total** | | **7.5** | |

### 2.2 Do full French and Swahili translations fit?

- **The build fits; the release depends on people.** Drafting and loading both catalogues is 0.5 units of agent work (UQ-8), so the code side is inside 7.5.
- **The quality does not come from the build.** A drafted Swahili catalogue for an energy and asset product will have wrong or unnatural terms ("readings", "verified", "unexplained fuel") that only a native reader catches. French is easier to review but still needs a fluent reader who knows the domain words.
- **So the ruling is:** foundation plus English is the commitment for the client session. French and Swahili are drafted and ready, and each is switched on for clients only after its review. Showing an unreviewed language to a client is refused: a wrong word on a defensible-numbers product costs more trust than no French at all.
- **Owner actions** (section 6): a native Swahili reviewer (and which standard: Tanzanian or Kenyan usage, which matters for some terms), a fluent French reviewer, and the glossary approved by them first.

### 2.3 How it fits the shared date range and the Portfolio tabs (no restyle twice)

1. UQ-0 draws the SR top bar and the PF tab row, coverage line and outcomes row in the new tokens, so the v7.1 layout and the v7.2 look are approved together.
2. UQ-1 lands the semantic tokens and the style ratchet before SR-1, so SR and PF are written on semantic tokens from their first line.
3. SR-1 creates the top bar row. UQ-2's theme control and UQ-4's language switcher go into that row, so it is laid out once.
4. UQ-3's `EmptyState` and `Skeleton` exist before PF, so PF's tabs, tiles and lists use them from the start.
5. PF-W (the "complete readings" term family) changes the English words **before** UQ-5 and UQ-6b move them into the catalogues, so each word moves once, already in its approved form.
6. Captures are re-baselined once after PF in both themes, not once per change.

### 2.4 What stays after the client session (about 7.25-8.0 units, BL-69 remainder)

- **Stage 1 remainder (about 2.25):** the rest of the component library (`MetricCard`, `DataTable` with density and phone card mode, one-level `Tabs` with "More", `Dialog`, `Toast`, `FreshnessChip`, `ErrorState` with recovery) and the Lab catalogue page (1.25); the chart standard with table fallbacks (0.75); the axe-core pass (0.25).
- **Stage 2, the page-by-page uplift (4.5):** Portfolio cards as one figure + sentence + sparkline, Site boards, Finding detail, lists, Financials and Evidence, Work pages, depth pages; each mockup first.
- **Stage 3 remainder (0.5-1.25):** per-user language, time zone and units once sign-in exists (BL-54); a user-chosen display time zone; right-to-left (0.75) only if an Arabic, Hebrew or Persian market is planned.
- Also after: "Placement" on Findings rows for an "Act first" count on the Findings page (D-E5.25, about 1.0); the per-portfolio "complete" threshold (owner item 5.4, not sized).

## 3. Brand font

### 3.1 Recommendation: Inter (variable), fallback to the system stack

- **Licence:** SIL Open Font License 1.1. It allows bundling and embedding in commercial software, including a paid SaaS. The only limits: the font cannot be sold on its own, and the licence file must ship with it. Before shipping a **subset**, check the licence file for a Reserved Font Name; if one is declared, ship the unmodified upstream `woff2` files instead of a renamed subset.
- **Coverage:** full Latin and Latin Extended, plus Cyrillic, Greek and Vietnamese. French needs é è ê ë à â ç î ï ô û ù ü ÿ œ æ, « » and the narrow no-break space (U+202F), which `Intl` uses in French number grouping and before ; : ! ?. Swahili uses only basic Latin. UQ-1's acceptance includes a glyph check for those characters, U+00A0 and the currency symbols, so no character falls back to another font mid-word.
- **Dashboards:** tabular figures (`tnum`), slashed zero (`zero`), case-sensitive forms and fractions as OpenType features. It was designed for user interfaces at small sizes: a tall x-height and open apertures keep 12-13 px text readable. Version 4 adds an optical-size axis, so headings get tighter display spacing from the same file.
- **Weights:** one variable file covers 100-900; the product uses 400, 500, 600 and 700.
- **Self-hosted:** the `woff2` files and `OFL.txt` are vendored into the frontend assets (no CDN, no Google Fonts call), with `font-display: swap` and a preload of the roman file. Latin and Latin Extended only, roman plus italic: about 100-150 KB, cached after the first visit.
- **Fallback:** `system-ui, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, sans-serif`, keeping `tabular-nums` (Segoe UI, Roboto and SF all support it). Noto Sans in the stack also covers scripts Inter lacks if a later market needs them (Noto Sans Arabic or Ethiopic would be added then).

### 3.2 Alternatives

| Font | Licence | Strengths | Why not first |
|---|---|---|---|
| **IBM Plex Sans** | OFL 1.1 | Engineered, serious tone; good tabular figures; a matching Plex Sans Arabic exists if right-to-left is ever built | Slightly wider and more corporate; less comfortable in dense tables at 12 px |
| **Source Sans 3** | OFL 1.1 | Variable 200-900, compact, very legible, tabular figures | Narrower personality; numbers less distinct at small sizes than Inter's |
| **Noto Sans** | OFL 1.1 | Widest script coverage of any family (Latin, Ethiopic, Arabic and many more), so one family for every future market | Plainer look, larger files per script; best as the script fallback, which is its role above |

## 4. Integrated pre-client roadmap

### 4.1 Everything due before the client session

| Item | Size | Lane | Depends on |
|---|---|---|---|
| **FR-B** fix round (wrapper fixes, T6 w301 golden, `pin_read_at` patch, FR-A Lows, `OBJECTIVE_BEHIND_PACE`) | calendar block Wed 11-Fri 13 | A | the Thursday technical demo build (frozen Wednesday) |
| **FC-1/FC-2** Findings cards | merging tonight (`task/FC-findings-cards`); 0 further units | - | owner approval (given) |
| **I11** fixes from the non-Kobo Site audit (item 11) | **placeholder 1.5** (range 0.5-2.5), sized when the audit reports | A | FR-B; must land before AR-0 takes its parity baseline |
| **UQ-6a** server catalogue seam | 0.25 | A | UQ-0 spec (Architect ruling, no mockup) |
| **ANY-1** boards on stored rows: AR-0, AR-1, AR-2 | 3.0 | A | FR-B, I11, UQ-6a |
| **FCF-1** Findings cards follow-up: estate-wide "awaiting verification" for Cold and EV (D-E5.27) together with the Finding-to-domain-Action join it needs (BL-47) | 1.0 | A | FC merged; before AR-3 touches estate coverage |
| **ANY-2** Portfolio on stored rows: AR-3, AR-6, then AR-4 (with MN-1/2/3), AR-7, then AR-5 | 5.5 | A | ANY-1 (AR-1); **AR-4 and AR-7 wait for PF to merge** (both touch `site_outcomes/read.py` and the `outcome-sites` route) |
| **UQ-6b** server words into the catalogue | 1.5 | A | PF-W merged; ANY-2 AR-4 merged (so stored bodies already carry keys) |
| **UQ-0** v7.2 foundation sheet | 0.5 | B | owner approval gates UQ-1 |
| **UQ-1** tokens, type, Inter, style ratchet | 1.25 | B | UQ-0 approved |
| **SR-1** shared range bar and state | 0.5 | B | UQ-1; owner approval of the final v7.1 mockup |
| **UQ-2** light and dark themes | 1.0 | B | UQ-1, SR-1 (control goes in the top bar) |
| **UQ-4** locale, formats, switcher | 0.75 | B | SR-1 (switcher in the top bar), UQ-6a (`Accept-Language` contract) |
| **UQ-3** states and quick wins | 0.5 | B | UQ-1 |
| **SR-2, SR-3** pages onto the shared range, guard, captures | 1.25 | B | SR-1 |
| **PF** coverage once, tabs, term family, scalable outcomes, region (PF-C, PF-T, PF-W, PF-O1/2/3, region) | 4.25 | B | SR-1, UQ-2, UQ-3; lands before ANY-2's AR-4 |
| **UQ-5** page words into the catalogue | 1.0 | B | PF merged (PF-W words final, panels regrouped once) |
| **UQ-7** pseudo-locale and string guard | 0.25 | B | UQ-5 |
| **UQ-8** French and Swahili drafts and layout pass | 0.5 | B | UQ-5, UQ-6b; then the two human reviews |
| **E-final** final demo build, end-game suites, E4-style checks, recapture of client screens (light and dark), DS-1a/DS-1b updated for tabs, range and themes, owner walkthrough | 1.5 | both | everything above merged |
| **Total** | **26.0** units + FR-B | | |

Not before the client session (backlog, unchanged): BL-68 price-it (needs sign-in; its optional 0.75 read-only step is left out to keep lane B inside the date), BL-67, D-E5.25 placement, BL-69 remainder.

### 4.2 Lanes and order

```
            Wed11  Thu12  Fri13 | Mon16  Tue17  Wed18  Thu19  Fri20 | Mon23  Tue24  Wed25  Thu26  Fri27 | Mon30  Tue1  Wed2
Lane A      FR-B ............. | I11  UQ-6a ANY-1 ........  FCF-1 | ANY-2 (AR-3, AR-6 | AR-4, AR-7 after PF | AR-5) UQ-6b | E-final ..........
Lane B      UQ-0 sheet  (owner | UQ-1  SR-1  UQ-2  UQ-4  UQ-3     | SR-2/3  PF .......................... | UQ-5 UQ-7 UQ-8 | reviews  E-final
            approves Thu/Fri)  |                                  |                                      |  fr / sw
Thu 12: technical demo to close associates (no merges into its frozen build).
```

The order is causal, not just convenient:

1. **I11 before ANY-1.** AR-0 proves that stored rows equal today's compose byte for byte. If the audit's fixes change what non-Kobo boards compose after that baseline is taken, the parity cases and stored kinds are redone.
2. **UQ-6a before AR-1.** ANY stores each page fragment's body as rows. If the bodies hold composed English sentences, every stored kind has to be rebuilt and re-proved when the words become keyed. Ruled the other way round, the bodies hold `{key, params}` from day one and AR-0 proves the English rendering equal.
3. **UQ-1 before SR and PF.** They are written on semantic tokens, so UQ-2's colour migration never touches them.
4. **SR-1 before UQ-2 and UQ-4.** The top bar row exists once; the theme control and language switcher go into it.
5. **PF before AR-4 and AR-7.** Both change the Portfolio card read and the `outcome-sites` route; PF's in-memory route defines the contract that AR-7 re-sources (proposal §9.5).
6. **PF-W before UQ-5 and UQ-6b.** The term family changes about 57 strings; they are moved into the catalogues once, in their approved form.
7. **AR-4 before UQ-6b.** The money lines and receipts are stored with keys by AR-4; UQ-6b then converts the remaining read-time sentences.
8. **E-final last, once.** One demo build, one full end-game suite (test-suite policy), one recapture.

### 4.3 Seams this plan protects (Architect rulings to log)

- **D-I18N.1, words render at read.** Stored rows (`site_period_read` bodies, `site_day_snapshot`) and response bodies carry message keys and typed parameters for every word; text is rendered for the request's locale at read. The CH-6b2 rule stays: the server owns words, the browser renders them.
- **D-I18N.2, locale in every cache key.** Until AR-5 retires pre-loading, the response store key includes the locale; after AR-5, the ETag includes it. The pre-load list builds English only; other languages are composed on request (fast once ANY lands).
- **D-I18N.3, a language is offered only when complete and reviewed** (section 2.2).
- **D-UI.1, look and layout specs.** v7.2 is the spec for tokens, type, colour and states; v7.1 stays the layout spec for the Portfolio and shared range; v6.9/v7.0 stay the layout spec elsewhere. Reviewers treat a mismatch with the governing sheet as High, as today.
- **D-UI.2, the theme and language choices are per-browser conveniences** (`localStorage`), never in the address and never on the server, until sign-in exists. The date range stays address-only, as SR rules.

### 4.4 Totals and calendar

- **Units:** about **26.0 plus FR-B**: lane A about 12.75 after FR-B (I11 1.5, UQ-6a 0.25, ANY-1 3.0, FCF-1 1.0, ANY-2 5.5, UQ-6b 1.5), lane B about 11.75 (UQ 5.75 in lane B, SR 1.75, PF 4.25), and E-final 1.5 shared.
- **Pace:** about 1.25-1.75 units per lane per working day, including review and fix rounds (lower than the 3 a day of pure build time used in earlier sizing, because each slice has an Opus review and usually one fix round).
- **Build work done:** lane B around Mon 23 to Thu 26 Nov; lane A around Tue 24 to Fri 27 Nov. Counted in working days; weekend work would bring it earlier.
- **Translation reviews:** about one day each, Wed 25 to Mon 30 Nov, in parallel with E-final.
- **Client session:** **realistic Tue 1 to Tue 8 Dec; earliest credible Mon 30 Nov.** The E3 note says the demo build is not prepared on the 3rd-5th of a month: if E-final slips past Wed 2 Dec, the prepare moves to Sun 6 or Mon 7 Dec, and the session to Tue 8 Dec or later.
- **If the owner sets an earlier date, cut in this order** (each cut leaves every shown thing honest): (1) French and Swahili stay off (they are off until reviewed anyway); (2) FCF-1 (the card keeps its "mini-grid sites only" note); (3) UQ-6b and UQ-7 (English only, the catalogue seam and page catalogue stay); (4) AR-7 (the outcomes route stays in memory, correct up to about 25 Sites); (5) AR-5 (pre-loading stays). ANY-1, SR, PF and UQ-0 to UQ-4 are not cut: they carry the first impression and the speed.

## 5. Risks

| Risk | Level | Handling |
|---|---|---|
| I11 turns out large (the audit finds a product defect across Cold and EV boards) | Medium | The placeholder becomes its own slice; its UI part (panels that only say "nothing") folds into UQ-3, which already collapses them; ANY-1 waits for its data or compose part only |
| Dark theme reveals hard-coded colours in SVG charts and status visuals | Medium | UQ-2 covers inline SVGs; the style ratchet stops new raw colours; dark captures of every client screen in UQ-2 and E-final |
| Server words are used as test oracles (many tests pin English strings) | Medium | UQ-6b renders English byte-equal; tests keep their strings, plus key-level tests; AR-0 parity covers stored bodies |
| Swahili or French review not available in time | Medium | Release rule D-I18N.3: the client session runs in English |
| Owner approval of v7.2 or v7.1 slips past Fri 13 | Medium | Lane B can start SR-1 only after v7.1 approval and UQ-1 only after v7.2; every day of slip moves lane B and the session by a day |
| Two lanes edit Portfolio code at once | Low | Order rule 5 (PF before AR-4/AR-7); AR-3 and AR-6 run first in ANY-2 because they do not touch the card read |

## 6. Owner decisions and actions

1. **Set the client session date.** Recommended: Tue 1 Dec or later, with Tue 8 Dec as the safe date (section 4.4).
2. **Approve the v7.2 foundation sheet** (UQ-0), ideally Fri 13 Nov. It changes the v6.9 type scale and colours for the whole app.
3. **Approve the final v7.1 mockup** (`frontend/mockups/v71/portfolio-tabs.html` with the shared date range, Change 0b): SR is not built until it is approved.
4. **Name a native Swahili reviewer** and say which usage (Tanzanian or Kenyan), and **a fluent French reviewer** (and whether the clients are French- or Central/West African-French speakers). About one day each, around 25-27 Nov, starting with the glossary.
5. **Approve Inter** as the brand font (alternatives in section 3.2).
6. **Theme default:** follow the computer's setting (recommended) or always start light.
7. **Which language the client session is presented in** (English recommended, with a French or Swahili switch shown only if reviewed).
8. **Region values for the demo Sites** (PF's region attribute uses a declared list per tenant).

## 7. Backlog

`.agent/backlog-post-demo.md` is updated: BL-69 is split into the owner-approved pre-client subset (UQ, 7.5 units) and the post-client remainder; BL-66 reads ANY-2 5.5 with AR-7; the owner decision log has the item 13 entry.
