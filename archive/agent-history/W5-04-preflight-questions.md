# W5-04 EV Work pre-flight questions (V1a–V5)

Builder pre-flight, 2026-10-23, branch `task/W5-04-ev-work` from main `8884d86b`. These are read and grep findings only; no product code was written. Each question names the unit, the evidence and the options. **The builder decides none of these.** All go to the Architect as one batch.

Sources: `tasks/W5-04-ev-work.md`, `.agent/W5-04-build-spec.md` (spec), `.agent/W5-02-build-spec.md` (W5-02 spec, including the 2026-10-23 Site-screens ruling at L289+), `.agent/W5-03-build-spec.md`, `.agent/mock-departure-register.md`, `frontend/mockups/v69/index.html` (mock) and `.agent/W5-02-04-mock-measurements.md`.

## A. Gates and sequencing

**Q1 (all units, gate).** What is the earliest unit that may start?
- Evidence: there is no `0034` on main (`backend/migrations/versions/` ends at `0033_w5_cold_work.py`). W5-03b is at pre-flight only (`task/W5-03b-ev-health-scenarios` at 3aa20007). W5-03a is still building in review4 (c0f890bd).
- The task needs merged 0034 before V1a.
- Options:
  - (a) Hold all of W5-04 until W5-03b merges.
  - (b) Allow V1a to be written against a local 0034 stub, without merging.
  - (c) Re-parent 0035 onto 0033 and renumber. This breaks the ruled chain.

**Q2 (V2a, V3a, V4a, gate).** Should W5-04's UI units wait for W5-02's Site screens to merge? The task and spec do not say so.
- Evidence: none of the following is on main:
  - W5-02a-site K2a/K2b, W5-02b K3a/K3b, W5-02c K4a/K4b/K5. Only the pre-flight `task/W5-02b-cold-site-screens` ec67dfac exists.
  - `domainActionClient.ts`, `coldWorkPresentation.ts`, `DomainActionVerification.tsx`, `WORK_CONTEXT_NOTICE_DOMAIN`, `WORK_STRIP_DETAIL_DOMAIN`, `siteWindowText`, `railActiveLabel`, the `site` prop on `siteWorkCases.tsx` (its props are at `siteWorkCases.tsx:52-62`), and site-type dispatch in `SiteAnalyticsFrames.tsx` (`SiteWorkFrame` :1508).
- The V2a card says "Read W5-02 Shared Site UI" but gates only on W5-04a.
- Options:
  - (a) V2a waits for W5-02a-site, V3a for W5-02b, and V4a for W5-02c.
  - (b) V2a creates the shared modules itself. This collides with K2a ownership.
  - (c) Another order.

**Q3 (V1a/V1b, collision).** Does the V1a file list omit the Alembic sole-head tests?
- Evidence: W5-03b E5 updates "18 test files that pin the sole Alembic head" (W5-03 spec, E5 file ownership). Adding 0035 moves the head again, but V1a's card lists only three test files.
- Options:
  - (a) Add the head-pinning test files to V1a (name them, or name the grep that finds them).
  - (b) Put them in V1b.
  - (c) Some other approach.

**Q4 (V2a/V3a/V3b/V4b, collision).** How should shared-file edits be serialised against W5-03?
- Evidence:
  - W5-03a edits `SiteAnalyticsFrames.tsx`, `v69-screen-ledger.json`, `v69-dependency-registry-pilot.json`, `navigation-truthfulness.ps1`, `navigation-rail-fixtures.ps1` and `shell-overflow.ps1`.
  - W5-03b E4/E6 edit `operatorSiteRoutes.ts`, both ledger/registry JSONs, `App.tsx` and the navigation guards.
  - W5-04 V2a, V3a, V3b and V4b edit the same files.
- Confirm that W5-04 rebases on merged W5-03a and W5-03b and preserves their rows and nodes, as K3b preserves W6's. Otherwise name the merge order.

## B. V1a: migration 0035 and schema

**Q5 (V1a).** The domain CHECK is not named.
- Evidence: `0033_w5_cold_work.py:43` has `domain text NOT NULL CHECK (domain = 'COLDCHAIN')`, an inline equality with no name. Postgres auto-names it `domain_action_domain_check`. No code or test refers to that name.
- Options:
  - (a) 0035 drops `domain_action_domain_check` by that generated name and adds a named `domain_action_domain_chk CHECK (domain IN ('COLDCHAIN','EV_CHARGING'))`. Downgrade restores the named cold-only form.
  - (b) Keep the generated name.
  - (c) Look the name up from `pg_constraint` at migration time.

**Q6 (V1a).** The DB cannot reject a three-item COLDCHAIN intent after widening.
- Evidence:
  - `domain_action_intent` has no `domain` column (0033 L63-81).
  - The widened `domain_action_intent_criteria_count_chk IN (3,4)` therefore cannot tell cold from EV.
  - The spec says `test_w502_domain_intent_postgres.py` must keep "rejecting three items for COLDCHAIN … after 0035". The current test does this at the DB level through the check name (`test_w502_domain_intent_postgres.py:347-350`).
- Options:
  - (a) The cold three-item rejection moves to a service-level assertion (model test `test_w502_domain_intent_model.py:89` already covers it). The DB test asserts only that 2 and 5 items are rejected.
  - (b) 0035 adds a BEFORE INSERT trigger that joins `domain_action.domain` and enforces 4 for cold and 3 for EV at the DB, with an exact name and errcode.
  - (c) 0035 adds a denormalised `domain` column to the intent.

**Q7 (V1a).** The specified index does not match any query.
- Evidence:
  - The spec asks for an index on `(domain,site_id,recorded_at,id)`.
  - The only Site query, `postgres_domain_action_index.py:69-72 actions_in_window`, filters `tenant_id, site_id, raised_at` and orders by `raised_at DESC, id`. It has no domain filter.
  - 0033:61 already has `domain_action_site_raised (tenant_id, site_id, raised_at DESC, id)`.
- Options:
  - (a) Add the index as specified, even though no query uses it.
  - (b) Use `(tenant_id, domain, site_id, raised_at DESC, id)` and add a domain filter to the query.
  - (c) Add no index.

**Q8 (V1a).** Downgrade details.
- Evidence: 0033's downgrade (L137-164) takes ACCESS EXCLUSIVE locks and raises `'Downgrade of 0033_w5_cold_work refused: domain Action rows exist.'`
- The spec tests three EV refusals: root, intent and case-link "separately". Please give:
  - the exact 0035 refusal message;
  - whether the lock pattern is the same;
  - whether an intent or case-link row can exist without an EV root. Intent and case-link carry no domain, so "EV intent row" can only be detected by a join through `action_id`. Confirm that the refusal detects them by joining to `domain_action.domain='EV_CHARGING'`.

## C. V1a/V1b: validation, selection and read

**Q9 (V1a/V1b).** There is no per-domain validator structure.
- Evidence:
  - The spec says "Rule-8 writer remains the W5-02 adapter, now with an EV typed validator".
  - In the code, validation is plain module functions:
    - `domain_action.py:136-171`: `action_body`, `criteria`, `basis`
    - `DOMAIN = "COLDCHAIN"`, `FINDING_DOMAIN = "cold_chain"` at :23-24
    - single `CRITERIA` tuple at :34-39
  - The service writes `d.DOMAIN` (`domain_intent.py:76`) and gates on `d.FINDING_DOMAIN` (:72, :151).
  - The index uses one `INITIAL_RESULTS` tuple (`domain_action_index.py:52`) and one `CRITERION_SUMMARY` map (:54). `_Lineage` and `_source_state` hard-code cold (:171, :180).
- Options:
  - (a) A per-domain table, for example `DOMAINS = {'COLDCHAIN': (finding_domain, CRITERIA, INITIAL_RESULTS, summary, messages), 'EV_CHARGING': (...)}`, in `domain_action.py`.
  - (b) A separate `domain_action_ev.py` module. Not in the file list.
  - (c) Another named shape.

**Q10 (V1a/V1b).** How are the domain-specific refusal messages chosen?
- Evidence:
  - The current messages contain "cold" (`domain_action.py:41-47`).
  - The spec gives EV literals, but a malformed POST body may have no valid `domain`, and an intent POST learns its domain only after resolving the Action.
- Please rule:
  - which message a body with a missing or unknown `domain` gets (the cold message, a neutral message, or the EV message);
  - whether intent and case-link refusals that happen before the Action is resolved use the cold or the EV text.

**Q11 (V1b).** Should the POST reject an Action whose domain does not match the Site type?
- Evidence: there is no `site_type` check in `domain_work_api.py` or the service.
- An EV_CHARGING Action could be created on a cold Site if its Finding revision were `ev_charging`, and the reverse is also possible.
- Options:
  - (a) Add a check that `site.site_type == domain` and return 422 `DOMAIN_INTENT_LINK_INVALID`.
  - (b) Rely on the Finding domain only.

**Q12 (V1a).** Is `session_ids` made of session IDs or session revision IDs?
- Evidence:
  - The public EV session row has a `session_id` (`ev_session.id`, a UUID), a `revision_id` and an `external_session_id` (`ev-<sha>`) (`postgres_assessment_store.py` ~:2939-2955).
  - W5-03a's selection carries sorted `session_revision_ids` (`ev_depth.py:212-214`).
  - The spec says "public selected session IDs" and adds them to `source_provenance` selected IDs. Selected IDs elsewhere are revision IDs.
- Options:
  - (a) Basis holds `session_id`, and provenance adds the selected session revision IDs.
  - (b) Both hold session IDs.
  - (c) Both hold revision IDs.

**Q13 (V1a).** Which sessions may be declared?
- Evidence: the Finding row carries one `session_id` taken from its claim (`_findings` ~:3218-3227). The spec only requires "public selected sessions at the cutoff".
- Options:
  - (a) `session_ids` must include the Finding's own `session_id`.
  - (b) Any selected session at that Site within the Finding's selection window.
  - (c) Exactly the Finding's session.
- Also: is the window for "selected at the cutoff" the Finding pin's `window_start/window_end` (`postgres_work_read.py:300-304`), or the list window?

**Q14 (V1a/V1b).** Where do the EV cited accepted evidence IDs come from?
- Evidence:
  - The spec says the evidence comes "from selected public session sources only".
  - Cold `_check_basis` requires the evidence to be a subset of the Finding revision's cited accepted evidence (`domain_intent.py:144-162`, adapter `cited_evidence` `postgres_domain_intent.py:91-98`).
  - W5-03a adds `EvReadService.selected_provenance_on(c,snap,ids)` (review4 :3054), which is not on main. Main has no public EV provenance method; `_envelope` is private (:2842).
- Options:
  - (a) Use the same subset rule against the EV Finding revision's citations.
  - (b) Use the union of the accepted evidence for the declared sessions, through W5-03a's `selected_provenance_on`. This is not on main yet.
  - (c) Another source.

**Q15 (V1a).** How should the EV read port be wired?
- Evidence:
  - The spec names "the injected `EvReadService` port in `work/composition.py`" calling `_snapshot`, `sessions_on` and `findings_on`.
  - Main already passes `ev_snapshot=build_ev_read_service(None)._snapshot` into `LinkReadPorts` (`work/composition.py:44-63`, `postgres_work_read.py:84`). It has no sessions or findings port.
  - Rule 1 forbids `work/adapters/*` from importing analytics adapters (`configuration-persistence.ps1:193-243`).
- Confirm the shape: add `ev_sessions` and `ev_findings` callables (bound `sessions_on`/`findings_on`) to `LinkReadPorts`, plus a `selected_ev_basis(ports)` wrapper in `work/composition.py` that mirrors `selected_cold_envelope` (:109-126). Also give its 503 mapping (`EvReadUnavailable`?).
- Also, `findings_on` returns only "selected SUPPORTED EV Finding heads" (:3008). Is a non-SUPPORTED EV Finding a valid Action origin?

**Q16 (V1b).** What is the EV analogue of the cold detail envelope check?
- Evidence: the detail read re-checks the cold envelope through `rx.envelope(pin, …)` (`domain_action_index.py:203-211`). `build_domain_action_read` passes `envelope_of=selected_cold_envelope(ports)` (`work/composition.py:129-133`).
- For EV, please define:
  - what is re-selected at read time to produce 409 `DOMAIN_INTENT_BASIS_CHANGED` and `PENDING_RECOMPUTE`/`STALE_SOURCE`/`UNKNOWN`;
  - whether this means the declared sessions are no longer selected, or that a session revision changed.

**Q17 (V1a/V1b).** Should the W4 link selection be extended to EV?
- Evidence: `postgres_work_read.py:208-220` (`_domain_links`/`link_selections`) hard-codes `fr.domain = 'cold_chain'`. An EV domain Action case link would therefore never appear on the W4 Site or global case rows (K1c behaviour). `_pin` already has an `ev_charging` branch (:242-243).
- Should V1a or V1b widen this to `ev_charging`, which changes W4/W6 link tests? Or do EV case links stay invisible on W4 rows?
- `postgres_work_read.py` is in V1a's file list, but no instruction says to change it.

**Q18 (V1a/V1b).** A fixed intent-result and summary contract.
- Confirm:
  - EV `results` are `PENDING, PENDING, PENDING` with `evidence_ids:[]`;
  - `criterion_summary` maps only the exact three-key EV tuple to `A complete witnessed session and no repeat fault`;
  - a missing intent gives the EV message `No verification criteria have been declared for this Action.`, a different literal from cold's `No outcome criteria …`.
- I will implement this as written unless corrected.

## D. V1a/V1b: producer and clocks

**Q19 (V1a).** `EvReplayBuilder.decision_clock` does not exist.
- Evidence: the spec cites `EvReplayBuilder.decision_clock`. The real producer is the test-module `class Chain` in `backend/tests/test_w205b_ev_replay_postgres.py:214`, with `decision_clock()` at :235, `advance_late()` at :367 and fixture `chain(case)` at :418 (W5-03 spec L687 says "no EvReplayBuilder exists").
- `tools/w504_ev_work_cases.py` would have to import from `backend/tests`.
- Options:
  - (a) The tool imports `Chain` from the test module.
  - (b) The tool copies the needed steps.
  - (c) Move a shared builder into a non-test module, with its owning unit named.
- Also, the cold `tools/w502_cold_work_cases.py` is a library with no CLI (`MODES` at :52). Should w504 match that shape?

**Q20 (V1a).** Which W2 EV cases and which Finding?
- Evidence:
  - SES-011 (fault-ended) and SES-012 (incomplete) are mock-only literals; no backend fixture defines them.
  - The real cases are `complete, interrupted, fault, missing-meter, late-record, contradictory` (`test_w205b_ev_replay_postgres.py:100`), with manifests under `contract-fixtures/w2/ev/`, scenario `ev-{case}`.
  - The mock's F-130 is likewise not a real code.
- Name:
  - which case(s) the generated replay uses ("the same relative public event pattern" of which case);
  - which selected EV Finding the positive Action roots on;
  - which session(s) go into `session_ids`.

**Q21 (V1a/V1b).** The clock symbols are not defined individually.
- Evidence: the spec defines `R`, `D` and `K0` (the returned EV watermark), then "K1/K2/K3/K4 are returned DB record times". Only K4 is tied to an event (the case-link save).
- Please define K1, K2 and K3: which DB record time (Action `recorded_at`, intent `recorded_at`, INC/WR, correction) each one is.
- Also define what the "wall-clock K2 → last returned watermark ≤ K2" mapping is used for (the intent declaration selection? the browser `known_at`?).

**Q22 (V1a).** Producer clock and Site details.
- Please rule on:
  - whether the generated private EV Site keeps `timezone: Etc/UTC`, as `ev-lab-001.yaml:9` does;
  - its site code and display name, short name and subtitle, since the mock shows "Depot Charging Hub", "Depot" and "2 × 60 kW connectors · 80 kW site limit · no stationary battery";
  - whether the Foundation's effective intervals shift by the same delta as the events, as the cold producer's do.

**Q23 (V1b/V2b/V3b/V4b).** The capture producer process has no tool.
- Evidence:
  - W5-02 K2a owns `tools/w502_cold_work_walkthrough.py prepare|serve|attest|drop` (W5-02 spec P-G-5), which is not on main yet.
  - W5-04 names only `tools/w504_ev_work_cases.py` and `tools/w504-ev-work-evidence.mjs`, and neither is a serving tool.
- Options:
  - (a) Add `tools/w504_ev_work_walkthrough.py` (same modes) to V1b or V2a.
  - (b) Extend the w502 walkthrough to take a domain argument.
  - (c) The `.mjs` tool launches the API itself.
- Name the owning unit and the 403/503/pending/stale/unknown fixture separation, as P-G-5 does for cold.

## E. V2a/V2b: EV Actions tab

**Q24 (V2a, mock).** How should the Source cell's Finding link be handled?
- Evidence: the spec says `Finding {id8}` "with selected href if available". But:
  - `EvFindingFrame` (`EvAssessmentViews.tsx:772`, `SiteAnalyticsFrames.tsx:617-633`) and `evAssessmentClient.ts:217-218` ignore `revision_id`, and `evFindingHref` (:823) carries only the window.
  - This is the same condition that led W5-02 to P-K2a-37, which made the label plain text with a revision disclosure and an unavailable control (R65/R66).
- Options:
  - (a) Mirror R65/R66 for EV with new register rows (D1), applied to the Source cell and Incidents' Linked findings.
  - (b) Link to the window-only EV Finding URL.
  - (c) Extend the EV Finding frame to honour `revision_id`. This is out of the file lists.
- The mock's `F-130` link in the Source cell needs a D1 row in any case.

**Q25 (V2a, mock).** The panel subtitle and a missing register row.
- Evidence: the mock says `Due dates are not yet set in this example` (mock L342). The spec uses `Due dates are not yet set`. Cold has row R67 (D4), but there is no EV row.
- Confirm a new D4 row for `ev-work`, owned by V2a.

**Q26 (V2a, register).** Fix the register ownership.
- Evidence: R03 (Work notice, E1) is owned by "W5-04 V3a" and R04 (Actions strip, E4) by "W5-04 V3b" (`mock-departure-register.md:21-22`). But the Actions tab notice and strip ship in V2a, and the notice also appears on the case tabs in V3a.
- Proposed: R03 owned by V2a+V3a and R04 by V2a, as R01/R02 moved to K2a. Confirm.

**Q27 (V2a, mock).** The Actions empty state is not specified.
- Evidence: the mock defines `No actions at this site` / `No accepted recommendation or evidence request has been raised here yet.` (mock L339). The W5-04 spec gives no EV Actions empty copy, while cold has the same body (W5-02 spec L54).
- Confirm that EV uses both literals unchanged.

**Q28 (V2a).** How should W1 rows appear on an EV Site?
- Evidence: the union index returns W1 battery Actions plus domain rows for any Site, with no domain filter (`postgres_domain_action_index.py:69-72`). W5-02 P-K2a-33 specifies how mixed W1 rows render on cold.
- Confirm the same mixed-row rule for EV, or say that EV Sites cannot hold W1 rows and none are rendered.

**Q29 (V2a, mock).** Which topbar elements does the EV Work page need?
- Evidence:
  - The mock topbar has the site selector (L756) and the range picker `Window: Event window · 6 Oct 2026 · 08:00–16:00 EAT` (L782-785), on ev-work and also on ev-action.
  - On main there is no topbar range control; windows are in-panel `WindowForm`s.
  - W5-02 P-K2a-38 gives cold a range control "in the existing topbar date-range slot". The W5-04 spec gives no EV equivalent.
- Options:
  - (a) Use the same topbar range control on EV Work, preserving `from,to,known_at`.
  - (b) Keep the in-panel form and add a register row.
- Also: the mock shows "EAT" for EV while the fixture zone is `Etc/UTC`. Is the label formatted in the Site zone (D4 placeholder)?
- Also: does ev-action show the range picker?

**Q30 (V2a).** The V2a file list is missing two files.
- Evidence:
  - `WORK_SUBTABS` hrefs pass no query (`SiteAnalyticsFrames.tsx:1564-1567`), and `siteWorkHref` takes a raw string (`operatorSiteRoutes.ts:313`).
  - W5-02 K2a lists `operatorSiteRoutes.ts` and `operatorSiteTabs.test.tsx` to preserve `from,to,known_at` on cold subtabs. V2a lists neither, but the spec requires the "same window/cutoff across all tabs".
- Should V2a add them, or rely on K2a having made preservation type-generic?

**Q31 (V2a).** Which CSS file does the list use?
- Evidence: V2a lists `w1f4-action.css`. W5-02 P-K2a-43–47 rules that the domain Action list uses `w1f4-changes-work.css` (sticky first column, no overflow clip).
- Which file does the EV list edit?

**Q32 (V2a, mock).** What is the Work page subtitle fallback?
- Evidence: the mock subtitle is `2 × 60 kW connectors · 80 kW site limit · no stationary battery` (Site subtitle). Cold falls back to `Cold-room operations at this site.` when the stored subtitle is null (P-K2a-38). The EV spec gives no fallback.
- Give the EV fallback literal, or rule that the subtitle is omitted when null.

**Q33 (V2a, mock).** How should the strip count be pluralised?
- Evidence: the mock renders `Scoped to Depot · 1 actions` (L341). The spec template `{n} actions` reproduces that grammar slip.
- Options:
  - (a) Copy the mock exactly.
  - (b) Use the singular for 1, with a D2 row.

**Q34 (V2a/V3a, mock).** Do Work-page currentness notices need register rows?
- Evidence: the mock has no currentness or historical notice on any Work or Action screen. The spec adds `HISTORICAL`, `PENDING_RECOMPUTE`, `STALE_SOURCE` and `UNKNOWN` notices below the strip on ev-work, ev-work-incidents, ev-work-maintenance and ev-action. There is no register row for EV (or cold) Work, unlike R13/R15 for the analytics pages.
- Confirm a D2 row (R15-style) for the four EV screens and name its owner.

## F. V3a/V3b: Incidents and Maintenance

**Q35 (V3a).** Stale pre-W6 branches.
- Evidence:
  - The spec's ledger row reads "Incident/Maintenance global parity and Manage links appear only after their W6 roots mount … until then W4's unavailable text remains", and V3a reads "WR codes remain plain until W6 C2".
  - W6 A2/B2/C2 are mounted (`App.tsx:489-499`), and `siteWorkCases.tsx:272-275` already renders `Manage in {kind}` links.
  - W5-02 P-G-4 and P-K3a-1 deleted the before-W6 branch.
- Confirm EV uses:
  - `WORK_STRIP_DETAIL_DOMAIN` with the mock kind-specific muted text `Same records and states as the global Incidents list` / `… Maintenance list`, and `Manage in Incidents →` / `Manage in Maintenance →` (mock L341);
  - the client-built WR Overview href (`globalWorkRequestHref`, `globalWorkClient.ts:627`).
- I propose deleting the pre-W6 wording from the spec.

**Q36 (V3a, mock).** Is it a footer or a panel subtitle?
- Evidence: the spec calls `A case links chronology…` and `Completed work is activity…` a "Footer". In the mock these are the panel-head subtitle `<p>` (L183/L342), not a footer. Main's `w1f4-work-foot` holds the W4 Basis disclosure (`siteWorkCases.tsx:689-700`).
- Confirm the subtitle placement, which would be a D3 correction if it were built as a footer.
- Also: does the W4 `What this list is based on` disclosure stay on EV?

**Q37 (V3a, mock).** The Maintenance cells differ from cold's rulings.
- Evidence: the spec gives "state and record activity or `No activity recorded`" for Activity and "`Unverified` plus note" for Outcome. W5-02 P-K3a-4–6 instead rules:
  - a `Completed` chip only for completed requests, with the stored activity in a disclosure (R70, D2);
  - an `Unverified` badge with the note in a disclosure (R71, D2).
- Should EV use the K3a cell rules with EV register rows (D2, owner walkthrough)? Or should it follow the spec text, and if so, under what label?

**Q38 (V3a, mock).** Register rows for the case tabs.
- Evidence: the cold rows have no EV equivalents:
  - R68: WR target `workverification` → Overview
  - R72: Next evidence gap
  - R73: INC plain
- The EV mock shows only empty panels, so its row targets are defined (L338) but never rendered.
- Confirm whether EV needs D1 rows for its WR Overview target, the plain INC code and `No next evidence recorded`. Or does no departure arise because the mock never renders those cells for EV?

**Q39 (V3a).** How is the EV asset label rendered?
- Evidence: cold parses a final `GENERATOR` token as `backup generator` and shows the composite label in a disclosure (P-K3a-1–3). The EV producer's asset is "the returned EV Foundation connector ID/code".
- Give the EV asset rule: whether a connector enum token maps to a label (which literal), or whether the W4 `asset_label` is shown unchanged.

**Q40 (V3a).** The timezone formatter.
- Evidence: the spec's E5 vectors assume K3a's `siteWindowText` with the mock month table (P-K3a-7), but it is not on main. Main has `eatWindowText` (`siteWorkCases.tsx:149`).
- Confirm that V3a only reuses `siteWindowText` (covered by Q2's gate) and does not create it.

## G. V3b/V4b: registry and ledger

**Q41 (V3b).** `A-ev-work-projections` has open ancestors.
- Evidence: in `v69-dependency-registry-pilot.json`, `A-ev-work-projections` requires `A-ev-session-rules` (open), `A-action-index` (resolved) and `A-maintenance-index` (open, which requires `A-work-cases`).
- The W5-04 spec has V3b close it after V3 review. But W5-02 P-K3b rules that the cold node closes only in K4b, after the Action page, with resolved ancestors.
- Options:
  - (a) Close it in V4b once its ancestors are resolved (and name who resolves `A-ev-session-rules` and `A-maintenance-index`).
  - (b) Close it in V3b regardless of its ancestors.
  - (c) Leave it open, with a named closer.

**Q42 (V3b/V4b).** Which unit promotes `ev-action`?
- Evidence: the spec has V3 update all four rows, including `ev-action`, but `ev-action` is built only in V4a. Cold splits this: K3b promotes three rows and K4b promotes `cold-action`.
- Confirm that V3b promotes three rows and V4b promotes `ev-action`.

**Q43 (V3b/V4b).** Ledger field details.
- Evidence:
  - The current rows are `coverage:'deferred'`, `task:null`, `follow_on:'post-S7 EV domain'`, tier `Deferred`, with `unresolved_panels` holding the panel title.
  - The panel contracts have no `GAP` prefix and are "manifest candidate only; panel mapping unreviewed".
  - The spec sets `unresolved_panels:[]`. W5-02 P-K3b instead says to set the exact remaining GAP panel IDs.
- Please rule:
  - whether `follow_on` is cleared or kept;
  - whether `unresolved_panels:[]` is correct, given the panels carry no GAP prefix today;
  - whether the panel-contract `status` text changes.

## H. V4a/V4b: ev-action

**Q44 (V4a, mock).** Which Site name does the status line use?
- Evidence: the mock status line is `Charging operations · Depot Charging Hub`, the full display name (L711). Cold's K4a rule uses the stored `shortName`, falling back to the display name (P-K4a-1–4). The EV spec says `{owner ?? 'Not assigned'} · {site}`.
- Which name, the full display name or the short name?

**Q45 (V4a, mock).** The chip and result styling.
- Evidence: the mock `Open` chip is amber, and the `Pending` cells are plain text, not chips (L711-712).
- Confirm the amber tone and that the cells are plain text. The spec does not say.

**Q46 (V4a).** The `missing-claim-scan.mjs` edit is unclear.
- Evidence: V4a lists `tools/checks/missing-claim-scan.mjs` as an edit, but EV has no Related activity panel or disabled button.
- Is V4a's role to run the scan read-only, as P-K3a made it for K3a? Or must it add a rule, and if so which one?
