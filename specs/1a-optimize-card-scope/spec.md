# 1a: the Optimize card states its day and scope (implementer spec)

Status: rev 1, Architect (Claude), 2026-11-21, on the owner's delegation
(`owner/owner-away-architect-stands-in-2026-11-21b.md`; owner-away row 52 for the owner-level call). Lane A
(`two-week-build-plan.md` §0.2 days 10 to 12; §0.3 "Lands: ... `1a`"). `delivery-plan.md` §2 row `1a`: "Pin the
Optimize card's last-day behaviour, then correct it: the period's figure, or the day and scope stated" (2.5 units;
depends on none; structure page P1, approved with the pack, OD-20). Design: CH5, `economic-metric-and-effect-contracts.md`
N12 ("30-day window, lead Finding on its last day ... presented as the period's avoidable cost" must be "dated 'lead
issue now', or the window node"); `phase-plan-and-acceptance.md` §3 slice 1, PR 1a (pin, tests only) and PR 1b
(relabel). **1.75 units, two commits** (D-1A.7). **Screen unit:** reviewed now, merge held for the owner's
walkthrough. Standard review (W5): no new schema, mechanism or money figure; one SC-1 statement.
**Decisions:** `rulings.md` (D-1A.1 to D-1A.8). **Reviewer guide:** `reviewer-guide.md`.

## 0. Before you start

- Branch `task/1a-optimize-card-scope` off `main`; worktree `/opt/assetecon/AssetOpsV1-1a`; symlink
  `frontend/node_modules` from the main checkout. Start when the handshake has no open question.
- **Read:** `rulings.md`; `backend/assetops_backend/site_outcomes/read.py:595-760` (summary, `summary_window`,
  `_summary`) and `:880-970` (`_cost_claim`, `_optimize_card`, `portfolio_cards`); `site_outcomes/mini.py:507-530`,
  `:585-600`, `:640-690` (board day, `lead_finding`, `money_heads`); `chain/read.py:138-215` (`window_day`,
  `window_days`, `lead_finding`, `FindingHead`); `chain/strategies/avoided_cost.py`; `chain/vocabulary.py:426-453`
  (`money_claim`), `:570-582` (the `cost.*` card texts); `frontend/src/estate/PortfolioOutcomes.tsx:55-110`,
  `:240-300`; `frontend/src/estate/estateClient.ts:700-725`; SC-1 `specs/SC-1-statement-composer/spec.md` §3.2 to §3.6,
  §3.8.2 to §3.8.4, §5.3; `backend/assetops_backend/i18n/statements/en/agreed_action.py` and
  `backend/tests/statement_cases/agreed_action.py` (an adopter's shape); `backend/tests/test_ch5d1_optimize_card.py`;
  `backend/tests/test_out_w2_summary_window.py:1-75` (the recording fake board); mock v70
  `frontend/mockups/v70/index.html:415` (`PFDAYS`) and `:494` (`pfCard`).
- **No database, no migration, no route.** Tests are pure (backend) and vitest (frontend). Browser captures through
  the slot pool (`source /opt/assetecon/tools/pw/env.sh`; `tools/heavy-slot.sh -- ...`). Never ports 5490 or 8990,
  the walkthrough database or Docker. Evidence to `/opt/assetecon/evidence/1a/`.
- **Files.** New: `backend/assetops_backend/i18n/statements/en/portfolio_card.py`,
  `backend/tests/statement_cases/portfolio_card.py`, `backend/tests/test_1a_optimize_scope.py`,
  `tools/optimize_card_capture.cjs`, `frontend/e2e-fixtures/1a/*.json`. Edited: `site_outcomes/read.py` (one
  dataclass, one function, three call sites), `i18n/statements/en/vocabulary.py` (one noun),
  `backend/tests/test_ch5d1_optimize_card.py` (expected dicts gain `scope_text`),
  `frontend/src/estate/estateClient.ts` (one field), `frontend/src/estate/PortfolioOutcomes.tsx` (one field, one
  line of markup), `frontend/src/estate/__tests__/estatePortfolio.test.tsx`. **Not edited:** `chain/vocabulary.py`,
  `tools/checks/*` (no guard change), `tools/demo_combined_rows.py`, any legacy card text.

## 1. Outcome and why

Today the Portfolio's Optimize card on a 30-day window shows one figure, for example "3.31 USD possible extra fuel
cost", with "At Kobo · not added across sites". The figure is one Finding's stored cost: the lead Finding whose
episode touches each mini-grid Site's board day, and the board day is the window's last day (D-1A.1). Nothing on the
card says so, so an executive reads it as the month's avoidable cost. That is the one misleading figure on the first
screen (`phase-plan-and-acceptance.md` §3 slice 1).

1a keeps the one figure and states, on the card face, which issue and which day it is, and that it is not the period's
total. The period's cost figure arrives through the structure read (`7g`), not here (D-1A.2).

Gate questions (each can fail): Is today's behaviour pinned by a test before anything changes? On a 30-day window
with one priced mini-grid Site, does the card face read "One issue's cost: Kobo's lead issue on 30 October 2026, the
last of the 30 days shown, not their total"? Is the figure byte-equal to the claim as before, and no total of any kind
added? Do COH-17 O1 and the demo prepare's self-check pass unchanged? Is every new word an SC-1 statement?

## 2. Commit 1: pin today's behaviour (tests only; `backend/tests/test_1a_optimize_scope.py`)

Pure tests, green on `main` before any product edit. Each docstring cites the code line it pins.

| # | Pins | Test |
|---|---|---|
| P1 | The board day of a multi-day window is its last day (`chain/read.py` `window_day`, rule 3) | `window_day(datetime(2026,10,1,tzinfo=UTC), datetime(2026,10,31,tzinfo=UTC), "Africa/Nairobi") == date(2026,10,30)`; the same pair with `None` tz gives the same date |
| P2 | A mini-grid Site is judged on that day in the summary (`summary_window`) | With `KOBO` from `test_out_w2_summary_window.py` (copy the `SiteRef` literal), `SiteOutcomeBoardService.summary_window(None, KOBO, lo, hi, None) == ("DAY", date(2026,10,30), None, None)` (the method reads no `self`; if it ever does, construct the service as that test file does) |
| P3 | The money comes from the one lead Finding touching the board day (`lead_finding`) | Heads (`FindingHead`, all fields given): `A` episode 2 Oct 00:00 to 10 Oct 00:00 UTC, `B` episode 30 Oct 06:00 UTC, open. `lead_finding((A, B), start, end, source_open=True)` with `[start, end)` = 30 Oct local day at Nairobi is `(B.finding_id, B.revision_id, True)`; with heads `(A,)` it is `None` |
| P4 | The card carries no day or scope today | `_optimize_card([_site("K", "Kobo", _claim("3.31"))])` has exactly the keys `value, missing, detail, basis_text, days_line, tone, claim` (helpers copied from `test_ch5d1_optimize_card.py`); `days_line` is None |

Commit message: "1a commit 1: pin the Optimize card's last-day behaviour (tests only)". P4 is the one pin commit 2
changes: commit 2 edits P4 to expect the key `scope_text` as well, and says so in its message.

## 3. Commit 2: state the day and scope

### 3.1 The facts (`site_outcomes/read.py`)

```python
@dataclass(frozen=True)
class CostScope:
    """1a (D-1A.1, D-1A.5): per Site code, the day its Optimize claim is chosen on (None: the latest issue in the
    requested window) and how many days the requested window shows at that Site."""
    day: Mapping[str, date | None]
    days: Mapping[str, int]
```

In `_summary`, inside the existing per-Site loop and before the board read: `wd = window_days(lo, hi, site.timezone)`;
`scope_day[site.site_code] = b_day if basis == WINDOW_BASIS_DAY else (wd[0] if len(wd) == 1 else None)`;
`scope_days[site.site_code] = len(wd)`. After the loop, `scope = CostScope(scope_day, scope_days)`, passed as
`portfolio_cards(..., scope=scope)`. `portfolio_cards` gains the keyword-only `scope: CostScope | None = None` and
passes it to `_optimize_card(sites, counted, scope=scope)`. A failed board's Site is in `scope` but never priced, so it
is never read. No other caller changes; a call without `scope` gives `scope_text` None.

### 3.2 The statement (`i18n/statements/en/portfolio_card.py`; data only, D-SC1.3)

```python
STATEMENTS = {
    "portfolio_card.cost_scope": {
        "slots": {
            "sites": {"type": "state", "values": ["ONE", "SEVERAL"]},
            "site": {"type": "name", "absent": ["SEVERAL"]},
            "span": {"type": "state", "values": ["ONE_DAY", "RANGE"]},
            "day": {"type": "day", "absent": ["LATEST_IN_RANGE", "DAYS_DIFFER"]},
            "days": {"type": "count", "absent": ["ONE_DAY", "DAYS_DIFFER"]},
        },
        "variants": [
            {"id": "one_day", "when": {"all": [{"is": ["sites", "ONE"]}, {"is": ["span", "ONE_DAY"]}]},
             "requires": {"present": "day"},
             "text": "One issue's cost: {site}'s lead issue on {day}"},
            {"id": "one_range", "when": {"all": [{"is": ["sites", "ONE"]}, {"present": "day"}]},
             "requires": {"present": "days"},
             "text": "One issue's cost: {site}'s lead issue on {day}, the last of the {days} shown, not their total"},
            {"id": "one_latest", "when": {"is": ["sites", "ONE"]},
             "requires": {"all": [{"reason": ["day", "LATEST_IN_RANGE"]}, {"present": "days"}]},
             "text": "One issue's cost: {site}'s latest issue in the {days} shown, not their total"},
            {"id": "each_one_day", "when": {"all": [{"is": ["span", "ONE_DAY"]}, {"present": "day"}]},
             "text": "One issue's cost at each Site: its lead issue on {day}"},
            {"id": "each_range", "when": {"present": "day"}, "requires": {"present": "days"},
             "text": "One issue's cost at each Site: its lead issue on {day}, the last of the {days} shown, "
                     "not their total"},
            {"id": "each_differ", "requires": {"reason": ["day", "DAYS_DIFFER"]},
             "text": "One issue's cost at each Site: its lead issue on the last day it shows, not a total"},
        ],
        "rephrase": "never",
    },
}
```

`vocabulary.py`: append `"day"` to `VOCABULARY["noun"]["order"]` and add `"day": {"one": "day", "other": "days"}` to
its entries. No other vocabulary change. If the load check refuses any part of this literal (a slot option, an
operator form), that is a mid-build question to the Architect, not a rewording.

### 3.3 The card (`_optimize_card`)

Unchanged: `value`, `missing`, `detail`, `basis_text`, `days_line`, `tone`, `claim`, and the priced-Site rule. Added:
`"scope_text": cost_scope_text(priced, scope)`, the last key. `cost_scope_text(priced, scope) -> str | None`:

1. `None` when `scope` is None or `priced` is empty.
2. `codes` = the priced Sites' codes in Site order; `n = {scope.days[c] for c in codes}`;
   `d = {scope.day[c] for c in codes}`; `span = State("ONE_DAY") if n == {1} else State("RANGE")`.
3. One priced Site `c`, named `s.get("site_name") or s["site_code"]`: `sites = State("ONE")`,
   `site = Name(name, "site.name")`, `day = Day(scope.day[c])` if not None else `Absent("LATEST_IN_RANGE")`,
   `days = Absent("ONE_DAY")` when span is ONE_DAY else `Count(scope.days[c], "day")`.
4. Several: `sites = State("SEVERAL")`, `site = Absent("SEVERAL")`. When `len(d) == 1`, `None not in d` and
   `len(n) == 1`: `day = Day(the one day)`, `days` as in step 3. Otherwise `day = days = Absent("DAYS_DIFFER")`.
5. `render(message("portfolio_card.cost_scope", sites=..., site=..., span=..., day=..., days=...))`.

`site_outcomes/read.py` stays in the ratchet scope (no `ADOPTED` change): the new code holds only code-form strings
(the key, state values, reason codes, `"site.name"`, `"day"`), so it adds no hand-built fingerprint. If the guard
reports a `HAND_BUILT_NEW` for it, that is a mid-build question.

### 3.4 The screen

- `estateClient.ts` `EstatePortfolioCard`: `/** 1a (D-1A.3): the Optimize card's day and scope, server text. */
  scope_text?: string | null;`.
- `PortfolioOutcomes.tsx`: `CardContent` gains `scope: string | null`; `content()` sets `scope: card.scope_text ??
  null` (and `scope: null` in the not-loaded branch). In `CategoryCards`, directly after the `oc-pffig` value `div`
  and before the detail `p`: `{c.scope ? <small className="ob-days oc-pfdays" data-portfolio-card-scope>{c.scope}</small>
  : null}` with the comment `{/* 1a (D-1A.3): v70 pfCard (index.html:494) keeps the days line under the figure; the
  Optimize card's day and scope stay on the face, because its figure misleads without them. */}`. No CSS change:
  `.ob-days` is styled in `frontend/src/sites/outcomes.css:167`.
- Mock: v70 `pfCard` (`index.html:494`) order is label, figure, "Why?", `oc-pfdays` line, detail, Site dots, basis.
  The scope line sits in that `oc-pfdays` slot. **MOCK DEVIATION MD-1A-1 (format):** v70 `PFDAYS.cost` reads
  "Kobo: 6 Oct partly checked"; the live line reads the SC-1 `day` format ("30 October 2026", D-SC1.10) and the
  scope words. Register row in `.agent/mock-departure-register.md`.

### 3.5 Tests (written first; red before the edit)

`backend/tests/test_1a_optimize_scope.py` (adds to commit 1's file):

| # | Test |
|---|---|
| S1 | One priced mini-grid Site, `scope = CostScope({"K": date(2026,10,30)}, {"K": 30})`: `scope_text == "One issue's cost: Kobo's lead issue on 30 October 2026, the last of the 30 days shown, not their total"`; `value`, `detail`, `basis_text`, `claim` equal `test_ch5d1`'s expected values byte for byte |
| S2 | Same Site, `days {"K": 1}`: "One issue's cost: Kobo's lead issue on 30 October 2026" |
| S3 | One priced Site with `day None`, `days 7`, name "GreenHarvest": "One issue's cost: GreenHarvest's latest issue in the 7 days shown, not their total" |
| S4 | Two priced Sites, same day, 30 days: "One issue's cost at each Site: its lead issue on 30 October 2026, the last of the 30 days shown, not their total"; `detail` still today's per-Site list exactly; `claim` None |
| S5 | Two priced Sites, days 30 and 31 (or days 29 Oct and 30 Oct): "One issue's cost at each Site: its lead issue on the last day it shows, not a total" |
| S6 | No priced Site, and `scope=None` with one priced Site: `scope_text` None |
| S7 | No figure in `scope_text`: for S1 to S5, the text holds no digit run that also appears in any claim's `value` (the amount is never repeated; one figure, D-1A.2) |
| S8 | Summary wiring: with the recording fake board of `test_out_w2_summary_window.py` returning, for `KOBO`, an `OPTIMIZE_COST` row whose `_window` nodes carry a priced cost claim, `summary(...)` over 1 Oct to 31 Oct UTC gives `cards["OPTIMIZE_COST"]["scope_text"]` = S1's text, and over 30 Oct to 31 Oct = S2's text |
| S9 | COH-17 O1: `tools/checks/chain_coherence.coh17_optimize` returns `[]` on S1's and S4's summaries (proves no guard change is needed) |

`backend/tests/statement_cases/portfolio_card.py`: one `Case` per variant, the six English texts of S1 to S5 plus
`each_one_day` ("One issue's cost at each Site: its lead issue on 30 October 2026"), facts as listed (the guard's
coverage needs all six). `test_ch5d1_optimize_card.py`: every expected card dict gains `"scope_text": None` (its calls
pass no scope); nothing else in it changes. Sweep `grep -rn "OPTIMIZE_COST\|_optimize_card\|portfolio_cards(" backend/tests
tools/checks` and update only exact-equality expectations of the card dict; list each file touched in the packet.

`frontend/src/estate/__tests__/estatePortfolio.test.tsx`: (F1) with a summary fixture whose Optimize card has
`scope_text`, the card face shows it in `[data-portfolio-card-scope]`, after `[data-portfolio-card-value]` and before
`[data-portfolio-card-detail]` in document order; (F2) with `scope_text` null or absent, no
`[data-portfolio-card-scope]` exists; (F3) the other three cards never render one.

### 3.6 Captures (evidence, not committed; `/opt/assetecon/evidence/1a/`)

`tools/optimize_card_capture.cjs` (Playwright from `/opt/assetecon/tools/pw`): build `frontend` (`npm run build`),
serve `frontend/dist` with `npx vite preview --strictPort --port 5496 --host 127.0.0.1`, open `/portfolio` with every
request whose path starts `/api/` answered by `page.route` from `frontend/e2e-fixtures/1a/<case>/<path with / as
_>.json` (an unlisted API path answers 404 and is printed); fixtures copied from the vitest fixtures in
`estatePortfolio.test.tsx` plus the S1 and S4 cards. Two cases (one priced Site, 30 days; two priced Sites) at
1440 × 900, light; one at 390 × 844. Each capture's console errors counted and printed; 0 expected. Run once through
`tools/heavy-slot.sh --`.

### 3.7 Check-all

Fast check-all (`tools/heavy-slot.sh -- pwsh -File tools/check-all.ps1`) green, including the statement catalogue
guard with the new case module. The packet `specs/1a-optimize-card-scope/packet.md` lists both commits, every test
run with its result, the sweep's files, the captures and the register row.

## 4. Done (questions; each can fail)

1. Were P1 to P4 green on `main` before the product edit, in their own commit?
2. Does the face of a 30-day card name the issue's day and say it is not the period's total, with the figure byte-equal
   to the claim and no new figure on the card?
3. Do one-day, latest-in-range, several-Site and mixed-day windows each read their variant?
4. Is every new word an SC-1 statement, with all six variants covered, and no legacy text changed?
5. Do COH-17 O1, the demo prepare's `optimize_card` self-check and every existing card test pass with no guard edit?
6. Does each plant in the reviewer guide fail its named test?

## 5. Units

| Commit | Content | Units |
|---|---|---|
| 1 | §2 pins P1 to P4 | 0.25 |
| 2 | §3: `CostScope`, the statement, the card field, the face line, tests S1 to S9 and F1 to F3, cases, captures, packet | 1.5 |

## 6. Out of scope

The period's cost figure (`7g`, through 3B7a); the site board's Optimize row and every other field the API computes
and the screen hides (`1b`); the Grow card's money; any change to how the lead Finding is chosen; cold-chain and EV cost
claims (none is priced today; the statement covers them if one is, D-1A.5).

## 7. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Correct by a period figure or by stating day and scope | Day and scope (D-1A.2, row 52) |
| Q2 (owner) | Where the scope sits | On the face, in v70's `oc-pfdays` slot (D-1A.3, row 52) |
| Q3 | Repeat the amount inside the scope sentence | No: one figure (D-1A.2) |
| Q4 | Date format | SC-1's one `day` format, MOCK DEVIATION MD-1A-1 (D-1A.6) |
