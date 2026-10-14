# S4-02a registry closeout packet

Branch `closeout/S4-02a-registry` (from main `2592c82`, which merges S4-02a). Registry/ledger metadata only; no product code. No review verdict or owner approval is written here; acceptance is cited from `.agent/owner-S4-02a-acceptance-2026-10-14.md` (CONDITIONAL). Precedent: `.agent/S4-03-closeout-packet.md`.

## Changed
- `frontend/docs/architecture/v69-dependency-registry-pilot.json`
  - Nodes `I-S4-02a`, `I-financial-assumption-store`, `I-assumption-history-read`, `I-assumption-history-ui`, `D-financial-assumption-basis`: `open` -> `resolved`, with evidence (plan reviews, phase 1 review, final review, fix re-review (M1 fixed, ACCEPT), packet, owner conditional acceptance, decision `D-2026-10-13-s4-bounded-financial-basis`, commits 28668d9, 49bedd8, 408e9e6, 293b412, 07a9685, 59c2b56, 17ae9e2, 778875d, merge 2592c82, browser evidence 69/69 at 1440/390) and anchors (`financial_api.py:56-59`, `financial_read_api.py:64,88`, `financials/assumptions.py`, `postgres_assumption_store.py publish:99`, `assumption_read.py series:63`, `SiteFinancials.tsx` SiteAssumptions/History/DisabledEdit, `StoredFoundationViews.tsx:469`).
  - `G-foundation-financial-assumptions`: stays `open`; `review_trigger` now names what closes it (a reviewer accepts the line as replaced by the price value or an accepted link treatment, plus a reviewed source for the wider assumption set or an out-of-scope declaration); `evidence.source` and `evidence.ui` name the read and the link.
  - `G-assumptions-human-edit`: stays `open` (build gap); `evidence.reviewed_by` = `.agent/S4-02a-review.md`, `evidence.visual` = `%LOCALAPPDATA%/AssetOps/evidence/s402a/s402a-assumptions-current-{desktop,narrow}.png`.
  - Not touched: `I-S4-02b`, `I-S4-02`, `I-financial-*`, `I-consequence-history-read`, `D-financial-basis`, all W1 panels and portions (no promotion).
- `frontend/docs/architecture/v69-screen-ledger.json`: `assumptions` (task `S4-02a (S4-02b pending)`, `gap_ids` G-assumptions-human-edit, bounded claim, interaction, conditional-acceptance caveat, remaining G-05 gaps) and `financials` (task string, caveat: only the Finding bridge and Site price in use; money panels partial until S4-02b). `foundation` unchanged: its caveat does not mention financial assumptions and its `G-foundation-financial-assumptions` gap id is already listed.
- `.agent/next-work-2026-10-14a.json`, this packet.

## Checks
- `check_v69_dependency_registry.cjs`: exit 0. `check_v69_ledger.py`: valid (110 screens, 88 models, 258 panels).
- `tools/check-all.ps1`: All 9 guards passed.
- `check_v69_dependency_registry.cjs --next-work --out .agent/next-work-2026-10-14a.json`: ranked. `--verify-report`: exit 0.
- Pre-existing uncommitted CRLF-only noise in three checker/catalogue files and several task files was left alone and not committed.

## Next-work decision
- `Decision: {"action":"stop_owner","top":"I-financial-store","top_score":2.229,"second":"A-S5-overview","second_score":2.148,"gap":0.036,"recommendation":"A-S5-overview","reason":"contested ranking (gap 3.63% <= 5%): owner chooses; tie-break recommends A-S5-overview"}`
- Top I-financial-store 2.229, second A-S5-overview 2.148, gap 0.036 (3.63%, within 5%): owner chooses; tie-break recommends A-S5-overview. Raw leader D-financial-basis 2.429 is technically blocked (open prerequisite I-financial-store).
- `unscored_work`: I-G-01 and I-G-02 (resolved, packet done), I-G-03, I-G-04, I-G-05 (open, not_started; deferred while ready core work exists, then W1-exit review).

## Questions for the reviewer
1. `assumptions:1#a` (versioned price, currency and author basis) was left `open`, not `delivered`: its mapping target and technical_requires name D-financial-basis, I-S4-02 and I-financial-ui. Should S4-02a's accepted price history deliver it now (owner said nothing becomes Real, panels stay partial)? `assumptions:3#a` also covers consequence revisions, so it needs S4-02b.
2. `G-foundation-financial-assumptions` trigger wording: is "price value or accepted link treatment plus wider-set source or out-of-scope" the right close condition?
3. `financials`/`assumptions` ledger `task` strings now read `S4-02a (S4-02b pending)`; confirm the validator-accepted form is the intended one.

## Closeout review fixes (coordinator, 2026-10-14)

Review `.agent/S4-02a-closeout-review.md` ACCEPT with carries; applied:
- L1: `G-foundation-financial-assumptions` review_trigger now follows the task: closes when the owner or an independent reviewer accepts the line/link treatment; any wider assumption set splits into its own gap then (no new scope rule in metadata).
- I1: its `boundary.source` names the reviewed read reachable by link.
- I2: anchor labels corrected (`financial_read_api.py` next-page link :82-85, exact revision :88; `financial_api.py` refusal :83-86).
- I3: ledger task strings restored to "S4-02a + S4-02b (S4-02 closeout)".
- Rerun: registry checker 0, ledger valid, `--next-work` regenerated (decision unchanged: I-financial-store 2.229 vs A-S5-overview 2.148, 3.63%, stop_owner), `--verify-report` 0, check-all 9/9.
