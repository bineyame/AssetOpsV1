# W3-03 seam re-check against merged W3-01 and W3-02 (2026-10-21)

Base: `main` at `996064c3` (worktree `AssetOpsV1-plan2`). Read-only. Spec: `.agent/W3-03-build-spec.md` (body plus closures 1-3; `Lnn` = spec line). I ran no test suites. This is a code-reading check, and every claim below cites file:line.

**Verdict:** the spec is not build-ready as written. **4 Blockers, 19 Should, 10 Nit (33 questions).** The most important point is that the aligned three-domain proof is still concrete, but only on a different window and producer from the spec's. Every domain's real fixture data falls on **2026-10-06**. The spec's `[09-30,10-07)` window, its frozen 10-07 clock and its s402c producer cannot produce the CURRENT/COMPLETE clean variant (B3).

---

## Blockers

**B1. Merged code exposes no full-scope root selector, only per-Site helpers and private functions.** The spec requires reuse of "connection-taking selectors" and says to stop at the merge gate if they are missing (L9, L163). The merged roots each assemble and page inside one body function:
- `estate/index.py:164-216` `_findings`
- `index.py:223-270` `_actions`
- `estate/evidence_money.py:428-486` `_evidence`
- `estate/financials.py:387-447` `financials_body`

None of them returns the full ordered set or the per-Site token arrays. The reusable parts are public `site_coverage` (`coverage.py:44`), `mini_grid_rows`/`windowed_rows` (`evidence_money.py:220,306`), `mini_grid_lines`/`windowed_lines`/`compare` (`financials.py:155,202,306`). The rest are private: `_coverage_state`, `_status`, `_coverage_site`, `_token_site` (`index.py:27-52`), `_groups` (`evidence_money.py:392`), and the Finding row/lens/link assembly (`index.py:170-188`). Each body also calls `_scope`, which decodes the cursor by `req.kind` (`index.py:81`).

A builder must decide alone between two options:
- re-implementing row assembly in Portfolio, which risks drift from the reviewed bytes;
- refactoring four reviewed bodies.

*Fix:* the Architect names extracted functions with frozen signatures, for example `finding_selection(snap, tenant, req, scope) -> (per_site, rows)` and its Action, Evidence and Financials equivalents. The rule would be that existing root bodies stay byte-identical, proven by the W3-01 golden manifest and the W3-02 API tests. Alternatively, the Architect explicitly allows the listed private helpers.

**B2. No owner is named for the edits W3-03 needs in W3-01/02 modules.** Task line 9 gives Lane B only *new* `estate/` files. Lane A gets `main.py`, the shell, `ui/`, the registry and `tools/checks/`. The following required changes fall in neither lane:
- `estate/scope.py`:
  - `KEYS` has no `portfolio` (`:42-46`), so `parse_request` raises `INVALID_CURSOR` for the kind (`:101`).
  - `lens` is validated only for `findings` (`:117-123`).
  - Cursor key sets cannot hold `kind` and `lens` together (`:47-49,247`).
  - The marker arity and validation have no `portfolio` entry (`:53,219-235`).
  - `cursor_after`/`cursor_marker` dispatch on kind (`:269-287`).
- `index.py`: `_fence` fences lens only for `findings` (`:117-118`), and `_cursor` emits `kind` only for non-findings (`:132-135`).
- `coverage.py` row fields (S6), and the `postgres_estate_read.py` verification read (S9).

`test_w302_estate_cursor.py:158` pins the Finding and Action cursor bytes.

*Fix:* name which lane edits each module. Add the rule that existing kinds' bytes and tests stay unchanged.

**B3. The aligned clean fixture (L232, Q9 L248-261) cannot be produced as specified.**
- **Window.** For each requested UTC day, `select_dispatch_days_on` returns one row (`analytics/adapters/postgres_assessment_store.py:804-810`). A day without a selection makes the mini-grid Site `UNKNOWN` (`coverage.py:98-101,119`), as W3-01 already proves (`test_w301_estate_index_postgres.py:553-556`, "2026-10-07 has no assessment, so the Site is UNKNOWN"). The only reviewed persisted W1 priced/eligible producer is `power_estate`. It uses the S4-03 PowerSite plus the S4-05 P01 policy (`test_w301_estate_index_postgres.py:499-510,572-594`) and has assessed days 10-06 and 10-08 only (`test_s4_consequence_store_postgres.py:49-50`). Under `[09-30,10-07)`, KOBO is therefore UNKNOWN. That makes status UNKNOWN, F PARTIAL and the operating card WITHHELD, which contradicts the clean row in L254.
- **Clock.** "Frozen 2026-10-07T00:00:00Z" (L232, L248) matches no fixture machinery:
  - S4/S6 run on fixture clocks `SETUP_AT` 2026-10-29 and `T_ACCEPT` 2026-11-01, with `pin_read_at` monkeypatching `read_at` (`test_w301_estate_index_postgres.py:392-404`; `test_s4_finding_store_postgres.py:48`).
  - Cold/EV freeze at `db_now` (`test_w301_estate_golden_postgres.py:239-243`).
  - `tools/s402c_late_power_walkthrough.py` is a live-HTTP walkthrough on real DB time, so "price and drain at or before 10-07" is impossible.
  - An explicit `known_at=2026-10-07` would label the clean read HISTORICAL (`index.py:96`), not CURRENT.
- **What is concrete.** W1 POWER_DAY, cold `COLD_DAY` and the EV replay are all **2026-10-06**:
  - `test_s4_consequence_store_postgres.py:49`
  - `test_w301_estate_golden_postgres.py:61`
  - `test_w205b_ev_replay_postgres.py:103-106`
  - The two-EV fixture reads `[day, day+1)` (`test_w302_money_comparability_postgres.py:249-273`).
  - W3-01 `mixed_replay` already puts cold normal, EV complete, an S4 case and the empty Site in one DB and tenant (`test_w301_estate_golden_postgres.py:278-312`).

  No W3-01/02 test proves all three domains CURRENT together. `assert_mixed` asserts only counts (`:315-332`). The W3-02 captures had no W1 line (`W3-02-review-packet.md:52-55`).

*Fix:* the Architect re-pins the aligned proof:
- request `[2026-10-06T00:00:00Z, 2026-10-07T00:00:00Z)`, with `known_at` omitted for the CURRENT variants;
- read clock pinned by `pin_read_at`;
- W1 producer `power_estate` (P01) instead of s402c;
- composition = `mixed_replay` pattern plus `install_second_ev_site`/`two_ev_sites` plus PowerSite in one DB.

The Architect then re-derives variant (b) (`known_at=2026-09-30` still precedes every head) and confirms that PowerSite and the S4 runner do not both import KOBO-001. If 7-day alignment is required, a reviewed 7-day W1 producer must be named first. The UI default (last 7 days) stays as it is.

**B4. The Finding↔Action join and the withdrawn-verification proof are unreachable in any aligned window.**
- W3-01 selects Actions *created* in `[from,to)` (`coverage.py:271-278`). S6 Actions are created at `T_ACCEPT` 2026-11-01, and W3-01 reads them over `[11-01,11-03)` while their Finding is on 10-06 (`test_w301_estate_index_postgres.py:647-648`).
- After APPLIED, the selected Finding revision differs from the Action's origin revision (`:685-695`). The exact (Finding, revision) join required by Q6 (L244) therefore shows "No accepted Action" for an applied Action.

The fixture's RESOLUTION_WITHDRAWN-after-VERIFIED row (L232) and the "Verified"/"Resolution withdrawn"/"Outcome pending" workflow lines have no persisted path in the aligned window.

*Fix:* the Architect decides two things:
- whether workflow and progress proof uses a separate Action-window persisted read or pure vectors;
- whether the row join stays revision-exact, with an honest label for the applied-elsewhere case, or joins by origin Finding with the revision disclosed.

## Should

S1. **The Portfolio cursor shape omits `page_one_mode`** (L173), but every estate cursor requires it (`scope.py:47-48,250`) and the basis mode comes from it (`index.py:99-100`). Add it to the L173 literal.

S2. **Page-two status.** W3-01 sets `snap.historical = k < read_at` with `k` = cursor cutoff, so a live page two is labelled HISTORICAL (`index.py:89-96`). L173 says page two is *not* historical. Rule that Portfolio `status` uses `snap.basis_historical`, as W3-02 `basis_status` does (`evidence_money.py:464`).

S3. **Status vocabulary.** `_status` emits `PENDING_RECOMPUTE` and `STALE_SOURCE` (`index.py:27-34`). Portfolio's enum is `CURRENT|HISTORICAL|PENDING|UNKNOWN|EMPTY_SCOPE` (L167). Give the literal mapping (STALE_SOURCE→UNKNOWN?). Also state which states feed it (Finding coverage only, or also Action coverage), and extend the frontend type (`estateClient.ts:50`).

S4. **F/E/M reductions are identical in code.** Evidence and Financials coverage both reduce the same `site_coverage` state (`evidence_money.py:463`, `financials.py:439`), so `money_state` equals `finding_state` unless it also folds W3-02 category coverage. That includes `applicable` and the EV guard `windows_covered` (`financials.py:403-405,242-244`). L169 says "and W3-02 category coverage". Give the exact reduction.

S5. **Token item fields.**
- Which coverage supplies `selection_id/watermark/match_state/job_state/source_freshness`: the Finding-domain `site_coverage` or the `actions` coverage (`coverage.py:318-322`; W3-01 Actions token uses domain `actions`, `index.py:247`)?
- The token `domain` is lowercase `mini_grid|cold_chain|ev_charging` (`coverage.py:25-26`, `index.py:52`), while L167 says rows carry stored `MINIGRID|COLDCHAIN|EV_CHARGING`. Name the token domain string and the row `domain` source (`site.site_type`, `postgres_estate_read.py:92-96`).

S6. **Row fields W3-01 does not select.**
- `episode_end` is dropped from rows (`coverage.py:150-153,259-262`), although heads carry it (`postgres_finding_store.py:539`; `postgres_estate_read.py:221,261`).
- No `mechanism` source exists. W1 heads hold `title/claim_level/limitations` (`postgres_finding_store.py:536-540`); "stored mechanism" (L187) is undefined.
- There is no row `domain` (`findingIndex.tsx:204-206`).
- The mini-grid sort anchor is revision `episode_start` (`coverage.py:132-133`), not the `finding.anchor_start` named in L187.

Name each field's column and where it is added.

S7. **The "Outcome pending" workflow line has no wire input.** Q6 adds only `application_state/resolution_state/verification_outcome` (L244). The plan fact is W3-01's private `_verification_window` (`coverage.py:315`). Add a wire field, or a server-built label.

S8. **`progress.rows` IDs are not read.** `verification()` returns plans without `id` and outcomes as `{id: recorded_at}` (`postgres_estate_read.py:307-320`). `verification_plan_id`, `verification_outcome_id` and `recorded_at` (L218) need new SQL. Name whether it goes in the W3-01 adapter or the new `postgres_portfolio_read.py`.

S9. **Several Actions can share one (origin Finding, revision).** There is no such uniqueness, only `recommendation_key`/`acceptance_key` (`migrations/versions/0016_action_store.py:56-80`). Q6 assumes one; give a tie rule.

S10. **Display strings: server or client.** L179/L181 make `display_value`, `detail`, `quantity_display` and `amount_display` server strings. Outward/half-even rounding, `NOT_DISPLAYABLE` and the category dictionary live only in the frontend (`estateFinancialsWords.ts:16-19,85-140`; `EstateFinancials.tsx:79-81,260`). Rule which side formats. Server-side formatting would need a new Python port of MINOR_UNITS and labels.

S11. **N2 rule 1 vs rule 4.** A lone W3-02 UNPRICED line forms an `INELIGIBLE` group (`financials.py:333-334`). If "any ineligible line" in N2(1) means the group state, the `UNPRICED` card state (N2(4)) is unreachable. Say whether rule (1) reads line `eligibility` or group `state`.

S12. **Finding links.**
- W3-01's UI links Findings only for mini-grid Sites (Run 13 ruling 3, `findingIndex.tsx:203-211`). Cold/EV `links.finding` is not a reviewed route, but L187 and "Review Finding" assume an exact Finding route for every row.
- W3-01 links interpolate the raw Site code (`index.py:182,240-243`), while W3-02 uses `quote(code, safe='')` (`evidence_money.py:135-136`) and L114 requires encoding once.

Rule which builder Portfolio uses and whether cold/EV rows are inert.

S13. **A null-`next_step` gap is unproducible.** Every typed gap has a step (`evidence_money.py:155-174`; `ev_site_reads.py:62-73`). Allow `test_evidence_prompt_null_steps_and_coverage_precedence` to use a fake snapshot, as the W3-02 API tests do (`test_w302_evidence_api.py:42`), or drop the branch.

S14. **The adapter may be redundant.** `PostgresEvidenceMoneyRead` already serves every W3-01/02 read (`postgres_evidence_money_read.py:26-118`), built by `build_estate_evidence_service` (`composition.py:55-68`). State whether `postgres_portfolio_read.py` is a subclass adding only S6/S8 SQL, or not needed. Lane A's `$pgReaders` entry depends on this answer (`configuration-persistence.ps1:816`).

S15. **Date bar copy.** L90 says `Window: {from}–{to, exclusive} · UTC`. The shared bar renders `Window {from} to {last included} (UTC days)` plus "Evidence cutoff" (`estateShared.tsx:111-139`). Rule whether to reuse the shared bar unchanged; recommendation: reuse it, since it is a Lane A primitive.

S16. **Registry shape.**
- No `portfolio` panel entries exist. Panels are `{screen_id,panel_index,...}` rows (`v69-dependency-registry-pilot.json:403-428`), not `portfolio:N` keys (L159).
- Predecessors are still open, and the W3 panels are `gap`: `A-estate-index-scope`, `I-estate-finding-root`, `I-estate-evidence-root`, `I-estate-money-root`, `A-estate-comparability`, `D-estate-comparable-sites` (`:60,107,109,110,147,150`; panels `:403-428`; W3-02 kept them gap, packet `:57`).

Give the four literal panel rows (requires, status, reason) and say whether the closure conditions in L159 apply while predecessors are open.

S17. **Lane A patch list misses existing pins of an unavailable Portfolio:**
- `operatorRailInventory.test.tsx:28,79,236,248`
- `operatorRouteFrames.test.tsx:261`
- `tools/checks/navigation-truthfulness.ps1:545`
- `navigation-rail-fixtures.ps1:52-53,93,97`. The dead-link mutation fixture uses Portfolio as its unavailable subject and needs a new subject, for example Assets.

S18. **Layout tool.** L226/L329 require `tools/layout-evidence.mjs`. It has no estate or Portfolio harness beyond `/findings` (`layout-evidence.mjs:5267,5479`). W3-02 used custom `.agent/W3-02-evidence/capture*.mjs` and recorded the tool as "not run" (`W3-02-review-packet.md:72`). Rule "reviewed equivalent" = a custom capture script, or name the owner of a tool extension (Lane A owns `tools/`).

S19. **COST_CONTROL for cold/EV Sites.** The operating-cost category applies to mini-grid only (`financials.py:45`). Is that map "configuration proof" for `NOT_APPLICABLE` (N5 L318), or do cold/EV Sites show `UNASSESSED`?

## Nit

N1. The path is `backend/conversions/demo-diesel-price-publications.json`, not `conversions/...` (L248).

N2. L226 says the measurements file has no block rectangles and asks for re-measurement. It has them (`W3-03-mock-measurements.md:13-33,43-63`) and Q24 uses them, but L226 is missing from the N3 index. The Evidence aside has no own rectangle; it sits inside `portfolio-side`, 709/512.

N3. A null `episode_start` is unreachable. Rows need a non-null start (`coverage.py:64-69`), and cold/EV raise on a null anchor (`postgres_estate_read.py:214-215,257-258`). "nulls last" and "Episode window not recorded" are defensive only.

N4. No RISK/OPPORTUNITY producer exists. Only `COST` is emitted (`index.py:173`). The `COUNT` risk card and non-empty Risks/Opportunities lenses are unreachable; tests must assert the empty paths.

N5. L208 says "lexically first Site ID", but gap `site_ids` are ordered by `(site_code_key, site_id)` (`evidence_money.py:406`). Pick one.

N6. `CONTRADICTORY` readiness (`evidence_money.py:39,123-132`) is not named in the EVIDENCE cell mapping (L82, N5). Presumably it maps to UNKNOWN as "conflict".

N7. The W3-01 consequence wire has `amount_low/amount_high/amount` (`coverage.py:161-165`). The L36 JSON shows only `amount`; copy W3-01 verbatim (L46).

N8. Action counts include only Actions created in the window (`coverage.py:271-274`). An older Action verified in the last 30 days is not counted. This is residual and should be stated in the disclosure.

N9. `EvSiteViews.tsx:750,1125` keep `UnavailableInline` "Portfolio evidence" / "Portfolio roll-up". These are closed-multiset members; L114 says not to touch them.

N10. `dependency-direction.ps1` has no estate API rule (the W3-02 API needed none). The "top-level allowance" in L228 is probably a no-op; confirm. The migration chain skips `0028` (`0027`→`0029`); this does not affect W3-03, but Lane A's one-head check should expect it.

## Already delivered by W3-01 or W3-02 (do not rebuild)

1. **Strict shared parser and refusals.** Codes and messages including `INVALID_LENS`; window/known_at/limit rules; repeated/unknown-key rule (`scope.py:26-38,98-133`).
2. **Access basis and token.** `estate-access/1` `access_basis` and `estate-selection/2` token with all six arrays, `[]` included, sorted lowercase, six-digit times (`scope.py:157-185`).
3. **Cursor machinery.** Unsigned base64url cursor with `page_one_mode`, fence-before-marker, `resume_after` 422 on non-member, and a 5-member nullable-first marker precedent from Financials (`scope.py:190-301`; `index.py:108-136`).
4. **Snapshot.** One read-only REPEATABLE READ snapshot with retry-once then 409, and 503 mapping (`postgres_estate_read.py:62-72`; `index.py:66-74`). Extended W3-02 snapshot with pinned cold/EV facades and money reads (`postgres_evidence_money_read.py`).
5. **Authorized Site set.** Imported Sites including inactive ones, with `site_code_key`; foreign tenant excluded; unselected Site kept (`postgres_estate_read.py:88-96`; `index.py:101-103`).
6. **Coverage reductions.** Seven-key `coverage.sites` item (`index.py:44-48`); `COMPLETE|PARTIAL|UNKNOWN` plus `EMPTY`; `EMPTY_SCOPE` status (`evidence_money.py:38,461-465`).
7. **Finding rows.** Lifecycle, `finding_label`, null priority/confidence, COST-only lens flags, exact money gate (`coverage.py:168-196`; `index.py:170-188`).
8. **Action rows.** Application/resolution/verification states, `Action {code}` title, the verification-window and verified-30-day reductions (`coverage.py:271-322`).
9. **Evidence rows.** Readiness and typed gaps with `next_step`, `site_ids/codes/names`, full-scope `_groups` (`evidence_money.py:155-174,392-413`).
10. **Financials.** Lines, the ordered eligibility table, `compare` (groups, exclusions, diagnostics, `NO_LINES`/`UNKNOWN_COVERAGE` sentinel), `estate_total` null, EV guard handling (`financials.py:87-107,202-278,306-377`).
11. **Group key (N1).** The shared `group_key_for_partition`, byte rule matching L179 (`evidence_money.py:380-387`), proven by `test_w302_money_comparability_postgres.py:40-59`.
12. **Server links.** `quote`-encoded Site code with row-local cutoff or `Opens current Site view` (`evidence_money.py:135-152`; `financials.py:136-150`). The EV Evidence link for the footer is `line.links.evidence`.
13. **Refusal body pattern.** Endpoint null extras inside `detail`, and 401 `WWW-Authenticate` (`estate_evidence_money_api.py:23-53`).
14. **Frontend pieces.**
   - Last-7-complete-days default, query and href builders, `EstateDateBar`, `REFUSAL_COPY` and `FIRST_PAGE_CODES` (`estateShared.tsx`, `estateClient.ts:146-159`).
   - `moneyText` outward/even2 and `NOT_DISPLAYABLE`, `CATEGORY_LABEL` (`estateFinancialsWords.ts`).
   - `ui/Disclosure.tsx`; the frame pattern (`shell/EstateRootFrames.tsx`).
   - Live `/findings*`, `/actions`, `/evidence`, `/financials` routes (`App.tsx:423-436`).
15. **Persisted fixtures to compose (see B3).**
   - `mixed_replay` (`test_w301_estate_golden_postgres.py:278-312`)
   - `pin_read_at` (`test_w301_estate_index_postgres.py:392-404`)
   - `power_estate` priced/eligible W1 (`:499-510`)
   - S6 verification chain (`:630-739`)
   - `two_ev_sites` same-currency COMPARABLE plus mixed-currency (`test_w302_money_comparability_postgres.py:218-389`)
   - `add_empty_site`/`imported_before` (`test_w301_estate_index_postgres.py:93,155`)
16. **Guard surface.** The `$pgReaders` list (`configuration-persistence.ps1:816`); nav guard expected-rail format (`navigation-truthfulness.ps1:544-556`).
17. **Mock measurements.** I re-derived every Q24 and named-panel cap from `W3-03-mock-measurements.md` with mock + max(24, ceil 10%), and all match (780/851, 413, 247/272, 247/328, 1714/3512, the card caps, aside 780/564). The 390 card grid matches `portfolio.css:30` (`repeat(2,...)`; cards at top 510/510/702/702/878).

## Commit sizing (one builder run each) and read index

The 1a/1b/2/3 split holds only after B1-B4 are answered. Two seam runs come first so that 1a stays one run.

| Run | Content | Read only these spec sections | Code to read |
| --- | --- | --- | --- |
| **0a** seam (owner per B2) | Full-scope selector extraction (B1); `portfolio` kind in parser and cursor (B2, S1); row `episode_end/domain/mechanism` (S6); verification IDs (S8). Existing W3-01/02 tests and golden bytes unchanged, plus new pure cursor tests | L13-15, L165-173, L187 (row fields only), L218 (progress row keys), L312-314 (N3 last bullet, N4), the B1/B2/S1/S6/S8 answers | `scope.py`, `index.py`, `coverage.py`, `postgres_estate_read.py:274-320` |
| **0b** fixture | One persisted helper: the B3 composition (PowerSite P01 + cold normal + EV-LAB-001/002 + W303-EMPTY-001 + foreign tenant) proving CURRENT/COMPLETE on the existing roots before any Portfolio code | L151 (inputs only), L232-234, L246-263, L333-335, the B3/B4 answers | the fixture files in delivered item 15 |
| **1a** read/API fence | Scope, coverage, lifecycle filter + re-sort, five-member cursor, token, refusals, router (unmounted) | L5-11, L15, L23, L165-173, L206, L220-222, L230, L312-314, N6 1a row (L326), S2/S3/S5 answers | `estate_evidence_money_api.py`, `test_w302_estate_cursor.py` |
| **1b** projections | Cards, objectives, prompt, progress, money/selected_lines, footer, Q9 variants | L17-19, L46, L175-181, L187-208, L210-218, L242-244, L248-263, L295-320, N6 1b row (L327), L335, S4/S7/S9-S11/S13/S19 answers | `financials.py`, `evidence_money.py:380-486` |
| **2** main page | Context, cards, pulse, Finding table, lens buttons, matrix, prompt, 401/409/503 clearing; route test after Lane A mount | L84-109 (with the N3 supersessions), L183, L187, L189-208, L212-214, L222-224, L265-291, N6 2 row (L328), S12/S15 answers | `estateShared.tsx`, `findingIndex.tsx`, `EstateFinancials.tsx`, `estateFinancialsWords.ts`, mock `portfolio.js/css`, measurements |
| **3** lower panels/closeout | Opportunity (inert), change disclosure, scope disclosure, footer, measured hierarchy, browser proof, full suite | L110-112, L181-185, L216-218, L226-228, L265-291, N6 3 row (L329), L159, S16-S18 answers | `ui/Disclosure.tsx`, the W3-02 capture scripts |

Lane A patches: mount after 1b; rail, nav guards and the S17 test list after 2; registry rows (S16) at 3.
