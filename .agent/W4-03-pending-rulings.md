# W4-03 pending rulings

## PR-1 (raised in unit 1; does not block unit 1; needed before unit 4)

S1 asks the OPPORTUNITY stage to carry "counters", but the S4/closure-1 catalog delta for 0030 lists only the
altered stage CHECK and no `schedule_site_head` columns. W4-02 added `mini_processed/mini_deferred/mini_failed`
as new columns in 0029. Unit 1 added no counter columns.

Question: should 0030 add `opportunity_processed/opportunity_deferred/opportunity_failed` (integer NOT NULL
DEFAULT 0) to `schedule_site_head`, with the downgrade dropping them? Or should unit 4 report OPPORTUNITY
counts without persisted columns? If the answer is columns, unit 4 amends 0030 and its catalog test, which is
possible because the branch is not merged.

## PR-2 (RESOLVED by u2: narrative column landed in c351eed1; readings 1-3 confirmed)

The scenario command carries a required `narrative` (closure 1 Q1-Q3 literal request shapes; original Scenario
domain paragraph: "typed quantities/units, narrative, assumption source"). Neither the original
`mini_scenario_revision` DDL (spec lines 84-101) nor the closure 4 S4 amendment matrix has a column for it, so unit
1's 0030 cannot persist it. Unit 2b stopped before the scenario store/POST rather than hash a field it then drops.

Question: should 0030 add `narrative text NOT NULL` to `mini_scenario_revision` with
`CONSTRAINT mini_scenario_revision_narrative_check CHECK (length(btrim(narrative)) BETWEEN 1 AND 2000)` (closure 1
bound "explanation/narrative/reason 1-2000"), with the catalog test updated? Or is `narrative` hash-only (in the
payload digest, not stored)? Should the scenario row wire then expose `narrative`? (Its closure-1 row shape does not.)

Confirmations requested in the same ruling (unit 2b would otherwise take these readings):
1. A pinned tuple whose `mini_revision_id` is not a W4-02 renewable revision of this tenant/Site is 422
   `DECISION_LINK_SCOPE_INVALID`; a same-Site tuple that is not the selected head at command DB time (seq or revision
   differs) is 409 `DECISION_BASIS_CHANGED`. Pins are 0-5 distinct consecutive Site-local days.
2. Scenario `selected_source_provenance` (S20) is resolved per row for the read gate (MIXED/UNKNOWN withholds the
   calculation); the list envelope's blocks use the union over all eligible rows' pins, not the page. No per-row
   provenance key is added to the closure-1 row shape.
3. `scenario_state` is `HISTORICAL` for an explicit past `known_at`, else `DEFINED`.

## PR-3 (RESOLVED by u2b: count is 45, the 48 was an arithmetic error; no DDL change)

u1/u2 DDL is applied exactly as ruled (three `schedule_site_head` counters, `narrative` column and
`mini_scenario_revision_narrative_check`, downgrade column drop). `pg_catalog` then reports **45** named CHECKs on the
ten new tables (44 at `c3713564` plus the narrative CHECK), and the exact CHECK-name array in
`test_w403_migration_postgres.py` matches that catalog name-for-name. The u2 ruling says **48** (47 before the
narrative CHECK). Per table at head: `mini_scenario` 3 (create_key, create_payload_sha256, create_actor_id);
`mini_scenario_revision` 6 + 6 authored (revision_no, name, kind, narrative, correction_reason, chain);
`mini_alternative_revision` 8 + 6 authored; `mini_opportunity` 1 (window); `mini_opportunity_revision` 2
(revision_no, input_sha256); `mini_decision_work_link` 1 (target) + 6 authored; `mini_opportunity_scenario_link` 6
authored; the other three tables 0. `schedule_site_head` keeps 2 CHECKs at 0029 and at head (net zero, as ruled).

Question: is the count 45 (u2's 47/48 miscounted), or are three named CHECKs missing from 0030 (if so, which tables,
columns and exact names)? Everything else in commit 1 passes: 11 collected, 10 passed, the only failure is
`len(CHECKS) == 48` (actual 45). Commit 1 is on the branch with the ruled 48; unit 2b not started.

## PR-4 (RESOLVED by u2c on main 9796b0ed: 4.1/4.2 confirmed; 4.3 tightened; 4.4 decimal strings; 4.5 UNKNOWN empty-union currentness; applied in the u2c fix commit)

The spec rules the non-MINIGRID refusal only for physical reads (closure 4 S10: 200 UNKNOWN `SITE_ROLE_UNSUPPORTED`
envelope). Unit 2b took these provisional readings for scenarios (`mini_decisions_api.py`); confirm or replace:
1. `GET .../financials/scenarios` on a non-MINIGRID Site returns 200 with the `mini-scenarios-1` keys, `status`
   UNKNOWN, zero rows, the empty UNKNOWN provenance alias, `selection_token: null`, plus a `limitations` key
   `[{"code":"SITE_ROLE_UNSUPPORTED","evidence_ids":[]}]` (no store consulted).
2. A scenario POST on a non-MINIGRID Site is 422 `DECISION_LINK_SCOPE_INVALID` after the write grant and store
   check, before the principal and body.
3. Read-gate limitation codes on a scenario row: the stored calculation `reason`, then `SELECTION_CHANGED` (pinned
   revision is no longer the day's head), `RECOMPUTE_PENDING`, `SOURCE_STALE`, `SOURCE_CLASS_UNKNOWN|MIXED`
   (W4-02 codes reused), as `{code, evidence_ids: []}`.
4. `gross_sales.amount` is a JSON number on the read wire, like `energy_kwh` (stored as a decimal string).
5. Scenario list `currentness` is the W4-02 aggregate over the union of pinned days; with no pinned day it is
   `CURRENT` (or `HISTORICAL` for an explicit past cutoff) with `job_state: NONE`.

## PR-5 (raised in unit 3) - RESOLVED by u3 (build spec "Unit-3 rulings (u3)"); all eight readings confirmed, tests added

Confirm or replace these Alternatives readings:
1. A command must name the Finding revision that is latest at command DB time; an older revision is 409
   `DECISION_BASIS_CHANGED`. A version-1 command (null predecessor) for a key that already has a chain is 409
   `DECISION_CORRECTION_CONFLICT`; an unknown predecessor or a revision not of the path Finding is 422
   `DECISION_LINK_SCOPE_INVALID`.
2. Cited IDs must be accepted rows of this tenant/Site received by the command instant (else 422
   `DECISION_LINK_SCOPE_INVALID`); citations are deduplicated, no count bound. `missing_evidence_reason` is null or
   1-500 trimmed characters; at least one citation or a missing-evidence reason is required (else 422 input).
3. Row `id` is the chain root (the key's version-1 revision UUID); `revision_id` is the displayed revision.
4. A NEEDS_REVIEW row keeps its stored `disposition` and its own (earlier) `finding_revision_id`; `review_state`
   alone marks it as not current. Only heads from Finding revisions with a lower `revision_no` than the selected one
   are shown as NEEDS_REVIEW.
5. `review_state` is relative to the Finding revision only (CURRENT on the latest-at-cutoff revision, HISTORICAL on
   an older one). Envelope `currentness` is `{HISTORICAL|CURRENT, job_state: NONE}`: HISTORICAL for an explicit past
   cutoff or a pinned older revision. Pending provenance is null (no recompute job exists for authored rows).
6. S20 selected block: `selected_revision_ids = {selected Finding revision} + displayed CURRENT/HISTORICAL alternative
   revision IDs`, evidence = union of their citations; NEEDS_REVIEW rows contribute neither.
7. A malformed `revision_id` query is 422 `DECISION_INPUT_INVALID`; an unknown or not-yet-visible one is 404.
8. The command instant is bound to `mini_alternative_revision.created_at` (DB `clock_timestamp()` in production; a
   constructor-only `test_db_clock_override`, as W4-01) because the W1 fixture Findings carry future fixture times.

## PR-6 (raised in unit 4) - RESOLVED by build-spec "Unit-4 rulings (u4)"; built in c4180e15

Pieces landed: (a) `afd15193` job methods + Rule 8 coalesce allowance + 6 negative/1 positive probes; (b, partial)
`24e460d3` scan, reconcile and S5 `input_sha256` (tests 3 passed). The projection must write the stored `result`
`{status,assessed_days,eligible_days,headroom_kw,day_rows,limitations}` (closure 1 Q17-Q30 line "Files:"), and the
contract leaves these values open. Builder asks; no reading taken:

1. `headroom_kw:{low,high}|null` across the study. Which aggregate of the ELIGIBLE days' one-hour `opportunity_kwh`
   bounds: (a) `{min low, min high}` (the headroom every eligible day supports), (b) `{min low, max high}` (the
   envelope), or (c) something else? Null when zero ELIGIBLE days or any status other than SUPPORTED?
2. Stored `limitations`: which codes and when (e.g. a missing day, a LIMITED/CONFLICT day, MIXED/UNKNOWN provenance),
   each as `{code, evidence_ids}`? The wire copy "Five-day study incomplete" exists, but no stored code is named.
3. Stored claim `status` inputs (S7 + closure 1 "Opportunity"): is "W4-02 CURRENT basis at the request cutoff" a
   projection-time input (a day whose `read_selected_renewable_basis` state is PENDING_RECOMPUTE/STALE_SOURCE makes the
   stored status LIMITED), or is it only the read-time currentness axis ("status is claim-only")? And is the
   MIXED/UNKNOWN provenance test the `selected_source_provenance` block of that same reader over the five days?
4. `day_rows[].constraints`: the stored W4-02 row's `constraints` list (empty for a missing day)? Confirm.

## PR-7 (raised before unit 5 build) - RESOLVED by u5 (build spec "Unit-5..12 rulings (u5)", unit 5 rulings 1-7 and the command paragraph); built in unit 5

u4b test additions landed (ba492755). Unit 5 not started: the read contract (original API block; closure 1 Q1-Q3,
Q7-Q16; closure 4 S5/S7/S9/S14/S20; u4) leaves these values open. Builder asks; each item gives the reading the
builder would take, for confirm or replace.

1. **List envelope `status`** (`mini-opportunities-1`). Q12-Q16 says scenarios/alternatives carry UNKNOWN because they
   are authored; it does not say how the opportunity list aggregates its rows' frozen statuses. Reading: weakest over
   all eligible rows before paging, `UNKNOWN < LIMITED < SUPPORTED`; zero rows -> UNKNOWN.
2. **Opportunity `currentness.state` precedence.** Inputs per study day: the stored pin vs the S9 basis head at cutoff
   (different `mini_revision_id`, or a head now present where the pin was missing = newer selection), the basis day
   `state`, and overlapping W4-03 `mini_opportunity` jobs. Reading: (a) an overlapping opportunity job
   PENDING/LEASED/FAILED with `available_at<=known_at` not cleared by a later opportunity selection - the W4-02 `_JOBS`
   rule, so FAILED also maps to PENDING_RECOMPUTE as in W4-02 - or any basis day PENDING_RECOMPUTE (or with live job
   IDs on a missing day) -> PENDING_RECOMPUTE; (b) else a newer selection or a basis day STALE_SOURCE -> STALE_SOURCE;
   (c) else any missing pinned day -> UNKNOWN (S7); (d) else explicit past cutoff -> HISTORICAL; (e) else CURRENT. No
   revision at cutoff -> UNKNOWN, or PENDING_RECOMPUTE when (a) holds. `job_state` = W4-02 `aggregate_job` over the
   five basis days plus the opportunity job's own state (SETTLED when none). Is UNKNOWN for an unchanged missing day
   correctly placed below a newer selection/stale digest?
3. **Read-time limitation codes.** u4 names `RECOMPUTE_PENDING` and `SOURCE_STALE` as read-time only. Reading: append
   them (as the scenario row gate does) after the stored codes, plus `SELECTION_CHANGED` for a newer selection and
   `SCENARIO_BASIS_MISMATCH` (closure 1) for a stored but incompatible association, each once with `evidence_ids:[]`.
   Confirm the code for a newer selection and the order.
4. **Detail "selected revision history"** (Q12-Q16) has no shape. Reading: `history:[{revision_id,revision_no,
   input_sha256,created_at,selection_seq,selected_at,job_id,status,current}]`, one entry per selection visible at the
   cutoff, ordered `(selected_at DESC, seq DESC)`, with `current` true only on the head; revisions never selected are
   omitted. Also: are the scenario associations' history (all remain inspectable) a second `scenario_links:[...]`
   array on the detail, and with which keys?
5. **List row and detail object shape.** Reading: the original wire `opportunity` object plus S14
   `first_day,last_day,model_version`, `code` `OPP-%06d` from `public_no`, `day_rows` from the frozen result merged with
   `selected_hours` `selection_seq`/`mini_revision_id` (and the frozen `constraints`), `headroom_kw` as S8 strings; a
   list row is that object without `history`. Per-row `status`/`currentness`/limitations sit on the list row too?
6. **Opportunity list window.** Q12-Q16 says reject partial-day bounds. Reading: `from`/`to` both required (missing ->
   422 `INVALID_WINDOW`), each exactly a Site-local midnight, `from<to`; intersection on `[first_day,last_day]`.
7. **`links.site_work` route** when a `mini_decision_work_link` names the opportunity (work-link command is unit 8).
   Reading: `/sites/<site-uuid>/work` (W4-01 Site Work route); null until unit 8 lands the command. Confirm the
   literal path.

## PR-8 (raised in unit 6, after 6a) - RESOLVED by u6 (build spec "Unit-6 rulings (u6)", rulings 1-6 and the unit-6a readings paragraph); built in unit 6b

Unit 6a landed (Scenarios page). Unit 6b not started: the canonical mini Finding shell needs these values the spec
leaves open. Each item gives the reading the builder would take, for confirm or replace.

1. **`{Finding code}` source.** u5 6b and closure 2 render `Findings › {Finding code} › {section} · site: {Site}`.
   The W1 Finding detail wire (`frontend/src/sites/findingClient.ts:FindingDetailBody.finding`) carries `id` (UUID)
   and `finding_key`, and no public code; no screen shows a Finding code today (the mock's `F-104` is a mock token).
   Reading: none taken. Options: (a) `finding.finding_key`; (b) the Finding page title (`onTitle`); (c) a new W1 public
   code (out of W4-03 scope). Which field?
2. **First tab label.** The current mini row's first slot is labelled `Finding` (W1-F5b). 6b names it `Overview`.
   Reading: relabel it `Overview` for MINIGRID Sites only, same route (`siteFindingHref`), and the root view's
   breadcrumb section text is `Overview`. Confirm.
3. **Non-MINIGRID child views.** A cold/EV Finding child address (`/findings/{id}/evidence|recommendation|history`)
   falls through to the same generic frame (`SiteAnalyticsFrames.tsx:600-615`), which today renders
   `{label:"Alternatives", unavailable:true}`. The final multiset has zero `Alternatives`. Reading: on non-MINIGRID
   Sites the generic child row keeps `Finding | Evidence | Recommendation | History` with the Alternatives slot
   removed (absent, not unavailable), and the old Site-rooted breadcrumb. Confirm, or should those addresses render
   the cold/EV frames instead?
4. **Analysis helper text.** S11 puts the longer Analysis explanation in nearby helper text. Reading: the closure-2
   sentence `Analysis unavailable for this authored alternative; use the Finding overview and evidence.` on the
   Alternatives view only; other mini child views show the bare `<UnavailableTab label="Analysis" />`. Confirm.
5. **Alternatives without `revision_id`.** The live path carries `?revision_id=<exact-selected-uuid>`. Reading: the
   Alternatives tab href is built only from the frame's resolved `revision_id`; when the address has none, the page
   resolves the latest revision through the existing Finding read and redirects (replace) to the exact
   `?revision_id=`. Alternatively render `Alternatives for this Finding unavailable`. Which?
6. **Analytic CTA.** `SitePerformance.tsx:606` links `${findingHref(finding_id)}/alternatives` (no Site, no
   revision). Reading: link `/sites/{site}/findings/{finding}/alternatives?revision_id=<id>` only when the period
   summary carries the exact Finding revision ID; the summary has `finding_id` only, so today it always renders the
   noninteractive `Alternatives for this Finding unavailable`. Same for `FindingDetail.tsx:236`
   (`tabHref("alternatives")`). Confirm.

## PR-9 (raised in unit 7) - RESOLVED by u7 (build spec "Unit-7 rulings (u7)"); 9.1 breadcrumb replaced in 3ba626ba, 9.2 and 9.3 confirmed

1. **Opportunity breadcrumb shape.** u5 unit 7 says breadcrumb `Sites › {Site} › Renewable evaluation › {OPP code} ›
   Overview` "with disabled Findings root"; closure 3, B5 and N9 (and the v69 measurement `Findings›F-109›Overview·
   site: Kobo Mini-grid`) give the global shape `Findings › {OPP} › Overview · site: {Site}`. Built: one breadcrumb nav
   `[Global Findings unavailable; this opportunity is reached from Renewable evaluation.] › Sites › {Site} › Renewable
   evaluation › {OPP code} › Overview`, root noninteractive, no `· site:` suffix (the Site is in the trail). Confirm, or
   name the single shape.
2. **Proposed-load note.** Closure 1 says `{scenario name} scenario` when compatible, but the detail read carries no
   scenario name (u6 dry-read). Built: `Linked scenario; name unavailable in this read` when `scenario_id` is set, else
   `No scenario linked`; value `{proposed_load_kw} kW` (no `× 1 h`). Confirm.
3. **503 for multiple CTA matches.** Built as the u6b ruling-9 503 copy `Decisions are unavailable right now. Try
   again.` (noninteractive) for more than one exact root and for any list refusal by code. Confirm.

## PR-10 (raised in unit 8) - RESOLVED by u8 (build spec "Unit-8 rulings (u8)"); all three confirmed, no product change; unit-9 vectors in test_w403_replay_postgres.py

1. **Already-linked pair under a new key.** `UNIQUE(case_id,scenario_id)` / `UNIQUE(case_id,opportunity_id)` make a
   second association of the same case and decision impossible. Built: a new idempotency key naming an
   already-linked pair is 409 `DECISION_DUPLICATE_KEY` (checked after the decision-scope 422). Alternative: 200 with
   the existing link's original body. Which?
2. **Refused overlay copy.** Built: a refused/unavailable contexts read shows `Decision context unavailable` (no
   `Decision context:` prefix) in each row's slot; while the overlay is loading nothing is shown. Confirm.
3. **Scenario without a route.** Built: `{label} (Scenario detail unavailable)` as plain text. Confirm the
   parenthetical form.

## PR-11 (raised in unit 9a) - RESOLVED by u9 (1-3 confirmed; replay asserts the 409 against DB time, commit "W4-03 u9 PR-11")

1. **KOBO Alternative at wall-clock time.** The only W1 mini dispatch Finding on KOBO-001 comes from the S4
   `CaseRunner` (F02), whose revisions carry fixture time `SETUP_AT = 2026-10-29T12:00Z`, later than today's DB time.
   The u3 rule "selected revision visible at command time" therefore refuses the replay's HTTP Alternative POST with
   409 `DECISION_BASIS_CHANGED` (the served app has no test clock, rightly). Built: the replay records that observed
   exit and the test asserts it whenever the revision is still in the future (and the created/listed row otherwise);
   the positive Alternative lifecycle stays proved by `test_w403_alternative_postgres.py` with its test clocks.
   Alternative: a dated KOBO Finding producer whose revisions precede wall time. Which?
2. **Late contradictory branch currentness.** The late rows (an authored W4-03 variant: 8 Oct noon PV mean 25 kW,
   minute 30, accepted through public ingestion, not published under the W4-02 source) enqueue no mini job, so the
   opportunity read before the rerun is `STALE_SOURCE` with `SOURCE_STALE`, not `PENDING_RECOMPUTE`. The harness
   ingestion stamps receipt at W4-02's fixed `RECEIVED` (13 Oct), before any later cutoff, so the explicit old-cutoff
   read is also `STALE_SOURCE` (precedes HISTORICAL) while still showing the first revision and one-entry history.
   Confirm these as the fixture's semantic outcomes.
3. **Missing branch window.** Built: the W4-02 `missing-conflicting` variant (12 Oct) is published and ingested, the
   8-12 Oct days reconciled, and a second explicit reconcile `[2026-10-07T21Z, 2026-10-12T21Z)` run; the 8-12 Oct study
   is asserted not SUPPORTED. The ruled 6-10 Oct reconcile is unchanged. Confirm the second window.

## PR-12 (raised in unit 9b) - OPEN: capture defects and unproducible states

Evidence: `var/w403p/capture/evidence.json` (265 checks, 240 pass), `<state>-<width>-app.png`, `<screen>-<width>-mock.png`,
`mock-measure/mock-measure.json` (`tools/measure-mock-panels.mjs`). Panel sets and order match the mock on every produced
state (Scenarios, Opportunity, both Work screens); no missing or extra panel was observed. Heights over the u9 caps:

1. **Scenarios titled panel over cap.** Populated 645 (1440) / 436 (390) vs 348 / 391 (mock 316 / 355): each row lists
   its five pinned mini revision UUIDs in full in Physical basis (~213 px a row), and the header-plus-three-rows inner
   scroll applies only at <=600 px. Successful empty 450 / 490: the empty block carries the closure copy (three
   sentences plus the explicit no-what-if line) the unit-6a tests pin. Refused 160 is within cap. A fix needs a
   ruling on how pins are shown (count plus disclosure, abbreviated IDs, or an inner scroll cap at 1440 as well) and
   whether the empty copy may shorten. Which?
2. **Opportunity cards over cap.** 162 (1440) vs 137; 350 / 338 / 322 (390) vs 273 (mock 113 / 248-264). Text-valued
   cards ("Withheld pending evidence", "No load proposed", "Not established") wrap to two lines at the card value
   size. Options: a smaller value size for text values, shorter value copy, or a raised cap. Which?
3. **Incidents panel at 390 over cap with the W4-03 overlay.** Linked/stocked five rows 482 vs 460; refused overlay
   571 vs 460 (each row gains a `Decision context unavailable` line under Linked findings). 1440 is within cap
   (425 / 447 <= 460); Maintenance is within cap at both widths. Options: keep the overlay line in the cell and raise
   the 390 cap for overlay states, or show the refusal once for the panel instead of per row. Which?
4. **Alternatives capture blocked by the walkthrough environment (unproved at both widths).** The frame renders
   `Site unavailable`: `GET /api/sites/KOBO-001` is 503 `SITE_STORE_UNAVAILABLE` because this worktree's local,
   git-ignored `var/sites/kobo-001.yaml` differs from the document hash the S4 `CaseRunner` import recorded; and the
   W1 Finding read for KOBO is 409 `PERFORMANCE_CUTOVER_CLOSED` because `run_replay` runs the Performance comparison
   only for MG-W402-001. The Alternatives GET itself answers 404 `DECISION_NOT_FOUND` at current DB time. Should the
   tool (a) also run the Performance comparison for KOBO-001 and (b) serve with a private site-document root (or the
   CaseRunner's own document), or is the Alternatives screen evidence the component tests only?
5. **Opportunity SUPPORTED/CURRENT is not producible after replay.** The late variant's fixed 13 Oct receipt is
   visible at every cutoff (PR-11.2), so after `replay` no read of the 6-10 Oct study is SUPPORTED with CURRENT.
   Also the detail route carries no `known_at`, so the `k_before_late` capture uses a named harness rule that appends
   `known_at=<k_before_late>` to the exact detail GET (recorded per state in `evidence.json.app[].harness`; the body
   is the real backend's). The current read now shows `Source changed since selection` (the missing branch publishes
   after the late rerun). Options: split `replay` so `capture` can run between the positive and late branches, or
   accept stale/limited states as the Opportunity evidence. And is the harness `known_at` rewrite acceptable?
