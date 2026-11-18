# W5-04 readiness refresh: open points (V1a-V5)

Read-only pre-flight, 2026-10-24, worktree `AssetOpsV1-review6` on `task/W5-04-ev-work-a` at main `48b0bf84`. The K4 branch `task/W5-02c-K4-cold-action` (head `de57ee51`, merge-base `48b0bf84`) was read with `git show`. Inputs: the task, the build spec, preflight rulings 1-46 (made against `8884d86b`), E5 rulings A1-A6/M1/L1-L3, E4/E6 UI rulings 1-29, K4 rulings 1-22, the mock measurements, the register, and v69 `SITE_WORK.ev`/`siteWorkScreen`/`add('ev-action'...)` (index.html:334-342, 701-703, 710-713). No code was run and nothing outside this file was changed. The list includes only points that are new or still open. Each point gives options and recommends the first one unless it says otherwise.

## A. Gate and migration

1. **K4 is not merged, but rulings 1-2 make every unit, V1a included, wait for K5.** K4 also edits `backend/tests/test_w502_domain_intent_postgres.py` (+85 lines). V1a owns that same file for the sole-head update and the cold three-criteria rejection.
   - (a) Hold all of W5-04 until K4a/K4b/K5 merge, as the rulings say.
   - (b) Waive the gate for V1a/V1b only. V1a would then rebase over K4's test edits, and V2a would still wait for K5.
   - Recommend (a) unless the schedule needs (b). Under (b), V1a must not touch the K4 hunks.

2. **0035 parent and head pin.** The 0034 parent is confirmed: `revision="0034_w5_ev_scenarios"`, `down_revision="0033_w5_cold_work"` (0034:16-17). No 0035 exists.
   - The ruling-3 grep finds about 20 test files that hard-code the current head `0034_w5_ev_scenarios`:
     - Head constants in `mini_depth_probe.py`, test_w203, w204, w205a, w206, w207, w401, w402, w403, w501, w503 and w502_domain_intent.
     - Direct version checks in test_s2_evidence_ledger, s1_bindings, s405, s4_consequence_store, s4_evidence_consequence_work (two), w200 (three) and w201 (two).
     - `get_heads()==[HEAD]` in w207, w401, w402, w403, w501 (two) and w503 (two).
   - The parent-chain checks are test_w501:137 and test_w503:50 (`PREVIOUS = "0033_w5_cold_work"`). Keep them and add a 0035→0034 parent assertion.
   - `pg_harness.py:144-157` reads heads dynamically and needs no change.
   - `host/tests` has no matches.
   - Ruling 3 holds. The only open question is whether `mini_depth_probe.py`, which is not a `test_` file, counts as a "sole-head test". Recommend yes: include it in V1a's handoff list.

3. **The name of the generated domain CHECK.** 0033:43 has an inline unnamed `domain text NOT NULL CHECK (domain = 'COLDCHAIN')`. Rulings 5/8 assume the generated name is `domain_action_domain_check`, which is the Postgres default but has not been verified.
   - (a) Upgrade looks up the constraint by `pg_constraint` (conrelid `domain_action`, contype `c`, def `domain = 'COLDCHAIN'`). It asserts exactly one match and drops it. Tests assert that only `domain_action_domain_chk` remains afterwards.
   - (b) Use the literal `DROP CONSTRAINT domain_action_domain_check`.
   - Recommend (a), or (b) plus a schema test that pins the pre-0035 name.

4. **Downgrade message style.** 0033's message ends with a period; 0034's does not (0033:137, 0034:88). Ruling 8's literal `...EV domain Action rows exist.` has a period. This is a confirmation only: keep the period as ruled. 0033 locks the tables child-first, as `("domain_action_case_link","domain_action_intent","domain_action")`. Recommend copying that order.

## B. E5 and backend API mismatches

5. **Stale wording: `LinkReadPorts` lives in `work/adapters/postgres_work_read.py:79-95`, not in `composition.py`.** Composition only wires it (composition.py:56-63, `ev_snapshot=build_ev_read_service(None)._snapshot`). Ruling 15 and the spec's V1 section say "add to `LinkReadPorts` in `work/composition.py`". Both files are on V1a's list. Correct the wording: add the fields in `postgres_work_read.py` and bind them in `composition.py`.

6. **There are no Finding "citations" separate from provenance (rulings 14 and 16; spec "accepted_evidence_ids is a sorted subset of the exact Finding revision's citations").**
   - `EvReadService.findings_on(c, snap)` (postgres_assessment_store.py:3008) returns `finding_id, revision_id, session_id, lifecycle, source_provenance`. Evidence IDs are folded into `source_provenance`; there is no `evidence_ids` field.
   - `selected_provenance_on(c, snap, ids)` (:3054-3060) intersects with the selected *assessment head's* `evidence_ids`, not the Finding's.
   - Options:
     - (a) Define "Finding citations" as the evidence ID list inside the Finding revision's `source_provenance`, with the exact key named by the Architect after V1a reads it.
     - (b) Add an explicit `evidence_ids` to `findings_on` rows. This edits analytics, which is outside V1a's file list.
     - (c) Use the assessment head's `evidence_ids`. This contradicts ruling 14's "cannot widen".
   - Recommend (a).

7. **A6 analogue: refuse rather than intersect.** `selected_provenance_on` silently intersects the supplied IDs (:3060). E5 ruling A6 made a declared ID outside the selected set refuse with zero writes rather than persist a smaller list. Ruling 14 says only "subset". Recommend stating it explicitly: any declared `accepted_evidence_ids` or `session_ids` member outside the selected set gives 422 `DOMAIN_INTENT_LINK_INVALID`, writes no root or intent, and never intersects. Test one foreign evidence ID and one foreign session ID.

8. **`decision_clock` is not public (ruling 19: "Expose a decision_clock result from the public replay response"; ruling 21's K0).**
   - `Chain.decision_clock()` exists only in `backend/tests/test_w205b_ev_replay_postgres.py:235`.
   - `ev_replay.py` and `ev_replay_api.py` return no watermark.
   - The production snapshot has `watermark = max(decided_at) FROM ingestion_disposition` (:2681). E5 calls the same value `committed_watermark` (ev_scenarios/service.py:257, 271).
   - Options:
     - (a) K0 = the `watermark`/`committed_watermark` returned by an existing public EV read after replay, for example the E5 scenario list `window.committed_watermark` or the EV session list envelope. Neither replay file changes.
     - (b) Add a field to the replay response. That needs `ev_replay*.py` on V1a's list.
   - Recommend (a), and name the exact read in the ruling.

9. **The EV session root versus its revision.** `ev_session` has `id`; revisions live in `ev_session_revision(id, session_id)` (0025:82, :108). `sessions_on` returns both `session_id` (root) and `revision_id` (:2939-2955). Rulings 12/16 hold. Fix the stale spec wording "`ev_session.revision_id` UUIDs" (ruling 12) to "`ev_session_revision.id`".

10. **The Finding pin window (ruling 13: "the Finding pin's exact `[window_start,window_end)` and pinned selection cutoff").** `findings_on` rows expose no window fields; the window comes from `snap` (`selected.cutoff`, window bounds). Recommend confirming that the "pin" means the EV `_snapshot` selection the Finding was read under: the window and cutoff the POST supplies and the server re-selects. Name the stored keys, so V1a does not invent a pin structure.

11. **Rulings 10/11 change cold behaviour, but the cold test files are not on V1b's list.**
    - Today a non-`COLDCHAIN` domain returns 422 with the *cold* literal `The cold Action declaration is incomplete or invalid.` (domain_action.py:138, :42).
    - No `site_type` comparison exists anywhere in `work/`.
    - Ruling 10's neutral message (`The Action domain is missing or unsupported.`) and ruling 11's Site-type check therefore both change the observable cold refusals.
    - Neither neutral literal exists in code yet.
    - Options:
      - (a) Add `backend/tests/test_w502_domain_intent_{model,postgres}.py` and any cold API test to V1b's file list for those vectors.
      - (b) Move rulings 10/11 to V1a, which already owns the cold test files.
    - Recommend (a).

12. **The literal spellings across the three layers need a closed mapping.** Site `site_type` is `EV_CHARGING` (0001:66); Finding domain is `ev_charging` (analytics/ev.py:31; cold `cold_chain`); `domain_action.domain` uses the Site spelling. Ruling 9's `DOMAINS` mapping must carry both literals per domain. Ruling 17's `_domain_links` widening must replace the literal `fr.domain = 'cold_chain'` filter and the fallback `{"pinned": None, "domain": "cold_chain"}` (postgres_work_read.py:214, :220). Confirm that the fallback becomes domain-specific from the Action row, not `cold_chain`.

13. **E5 null semantics that W5-04 inherits.**
    - (a) `foundation_revision_on` can return `None` (:3035; E5 ruling 7). Ruling 39's asset fallback ("selected Foundation connector label/code") then has no source. It must fall back to `No asset linked`, never to an unselected Foundation. The W4 Maintenance row carries `asset_label` and asset ID but no Foundation read. Which read supplies the connector label is unspecified: V3a has only `workClient.ts`, and no EV Foundation client is on its list. Recommend: show the W4 `asset_label` or `No asset linked` only, and drop the Foundation-label middle tier from ruling 39 unless the Architect names the read and adds it to V3a.
    - (b) E5's currency (A5) and money (A1) do not touch W5-04, since W5-04 calls no money method. Confirm, so no builder adds `scenario_money_on`.

## C. Contradictions with merged frontend code or the K4 branch

14. **The topbar range slot does not exist (rulings 29 and 77; spec V2a "topbar range/cutoff"; V4a "Preserve selected topbar range/cutoff").** K2a shipped a page-local `ColdWorkWindow` after the subtabs (SiteWorkActions.tsx:613-660), registered as **R88** (D1: "The app has no topbar or range-picker slot"). Mock `ev-work` and `ev-action` both show the topbar range picker. R77 (EAT→UTC) assumes a topbar.
    - (a) Extend R88 to `ev-work`, `ev-work-incidents`, `ev-work-maintenance` and `ev-action`, using the same compact `Window` control. Rewrite R77 as the zone label inside that control.
    - (b) Build a real topbar slot. This is shell work outside W5-04.
    - Recommend (a). For `ev-action`, state whether the window control appears there at all. Cold K4 shows none; only the range/cutoff query is preserved.

15. **K4 `DomainActionVerification.tsx` is cold-only, and its status line conflicts with ruling 44.**
    - The cold-only parts are `COLD_CRITERIA_TITLE`, `COLD_RELATED_TITLE`, `COLD_INSPECT` and `COLD_RESULT_LABELS` (:17-34). It always renders Related activity with the Inspect button.
    - The K4 status line is `{owner} · {shortName(display_name) || display_name} · {finding label}` (frames diff, near :1439; K4 ruling 9). EV ruling 44 and the mock (index.html:711, `Charging operations · Depot Charging Hub`) need the *full* display name and no Finding label.
    - Options:
      - (a) V4a adds a per-domain presentation input to `DomainActionVerification`: title, Related panel on or off, status-name rule and literals, selected by `action.domain`. The cold output stays byte-identical, proven by K4's existing tests.
      - (b) A separate EV component.
    - Recommend (a). Also confirm that the EV status line carries no `Finding version` disclosure. The mock has none, which also keeps the strip cap achievable; see 25.

16. **The EV refusal and non-loaded state shape versus K4 ruling 4 / R101.** K4 renders one untitled state panel for loading, 404 and 403/422/503. The W5-04 spec says `Refused page heading 'EV work unavailable', server message, Retry`, and `Loading the EV Action declaration.`
    - (a) EV reuses K4's untitled state panel, holding `EV work unavailable` plus the message and Retry as its content, not as a page heading. Extend R101 to `ev-action`.
    - (b) A literal page-level heading.
    - Recommend (a). Also name the EV not-found literal: K4 uses `Action was not found at this site.`

17. **`SCREEN_LEADING` ownership.** K4 ruling 3 let K4a alone add `"cold-action"` to `frontend/src/test/panelStructure.ts`. R80 adds currentness notices to all four EV screens, but `panelStructure.ts` is on no V2a/V3a/V4a file list.
    - (a) V2a adds `ev-work`, V3a adds `ev-work-incidents`/`ev-work-maintenance`, and V4a adds `ev-action`, each with `[data-domain-action-currentness]` or the case equivalent.
    - (b) No `SCREEN_LEADING` entries, with notices asserted ad hoc.
    - Recommend (a). Add the file to the three cards.

18. **EV currently falls into the W1/mini-grid paths silently, so the cards must name the branch points.**
    - `SiteWorkFrame` branches only on `COLDCHAIN` (SiteAnalyticsFrames.tsx:1807).
    - `SiteWorkCasesFrame` passes `windowForm={site.site_type !== "COLDCHAIN"}` (:2104).
    - `siteWorkCases.tsx` gates `cold` on `siteType === "COLDCHAIN"` (:1001), with the attribute `data-cold-cases` (:980).
    - `SiteActionFrame` gates on `COLDCHAIN` (:1579-1595).
    - `domainActionClient.ts` treats every non-COLDCHAIN index row as W1 (`title===null`, :221), so an EV row is malformed today. Its detail accepts COLDCHAIN only (:270).
    - The cards list the right files. The open questions:
      - (i) Is the V3a case-cell gate renamed to a domain gate, for example `data-domain-cases`? Or does EV reuse `data-cold-cases`, which K5's test asserts is absent on MINIGRID?
      - (ii) Does EV get `windowForm=false`, using the R88 control from point 14?
    - Recommend a domain-neutral attribute added alongside `data-cold-cases`, which is kept for cold, and `windowForm=false` for EV.

19. **The cold strip keeps `1 actions`, but EV gets `1 action` (R79).** `coldActionCount` deliberately keeps `1 actions` (coldWorkPresentation.ts:49-52, "U3"). EV ruling 33 corrects it. Confirm that the domains are intentionally inconsistent until the UI/UX pass (V2a puts its own counter in `evWorkPresentation.ts` and leaves cold untouched), or align cold now. Recommend the first, with no cold edit in W5-04.

20. **Site subtitle: no field exists (rulings 22 and 32, R78).** There is no Site subtitle field in the backend or frontend. R90 says so for cold, and `SiteFoundationChange.tsx:101` confirms it. So ruling 22's producer subtitle `2 × 60 kW connectors · ...` cannot be stored. Ruling 32's "when stored subtitle is null" is always true, and R103 (E4) withheld the same literal on Health as false for other Foundations. Recommend: drop the subtitle from ruling 22 and the spec's producer paragraph. EV Work always shows `EV charging operations at this site.`, and R78's wording becomes "always, since the Site read has no subtitle", matching R90.

21. **Ledger `follow_on` precedent (ruling 43).** Ruling 43 clears `follow_on` to null. Every earlier W5 promotion kept it: cold-work×3 kept `post-S7 cold-chain domain`, and availability/energy (W5-03a) kept `post-S7 EV domain`. The checker requires `follow_on` only for `deferred` (check_v69_ledger.py:113-116), so either value passes. Recommend following the ruling (null), or confirm the precedent instead. This matters only for consistency.

22. **The registry outcome is already known (ruling 41).** At `48b0bf84`, `A-ev-session-rules` is still `open` despite W5-03a's merge, and so are `A-maintenance-index` and `A-work-cases`. So V4b must leave `A-ev-work-projections` open and name those three predecessors, the same disposition as K4 ruling 11 for cold. This is a confirmation only. State it in the V4b card so no builder tries to close the node.

## D. Mock departures without a D-label

23. **The cold case-tab departures that EV reuses are registered for cold screens only.** V3a reuses K3a/K3b cells on `ev-work-incidents` and `ev-work-maintenance`, but these rows name cold screens only:
    - R91: currentness tone, blue for Historical/Unknown, amber for Pending. R80 gives EV the notices but no tone.
    - R92: the `What this list is based on` disclosure at the panel foot. The EV spec says "retain W4 basis disclosure" with no row.
    - R93: the `Showing a–b of N` pager block.
    - R94: two-line previews with `Read full text`.
    - V2a's four-row fold and `Show all {n} Actions` button reuse the K2 behaviour; check which R-row covers it on cold.
    - Options:
      - (a) Extend R91-R94 and the fold row to the EV screens, as was done with R69/R91 for `cold-action`.
      - (b) New R104+ rows.
    - Recommend (a). R81/R82 duplicate cold R70/R71 for the EV screen and are fine as they stand.

24. **`ev-action` reuse of K4 departures.** R99 (long title/owner wrap) and R101 (untitled state panel; see 16) will be visible on `ev-action` but name `cold-action` only. R100/R102 (Related activity) do not apply because EV has no Related panel. Recommend extending R99 and R101 to `ev-action` in V4a.

## E. Caps (lesson 15)

25. **Every W5-04 cap is still the pre-K2 number, the same numbers K2, K3 and K4 had to raise.** Final merged or ruled caps for the equivalent cold surfaces at 1440/390:
    - `WORK_CAPS` main 1600/2000, panel 650/850 (K2 ruling 2).
    - `CASE_CAPS` main 1400/1800, panel 650/650, with 680 at 390 for one open (K3 rulings 17/25).
    - `ACTION_CAPS` main 1500/1900, strip 140/200, criteria 500/760, notice 110/160 (K4 ruling 7; branch `w502-cold-work-evidence.mjs:54`).

    | W5-04 cap (spec "Measurements") | Value | Worst-case content | Likely result | Cold precedent |
    | --- | --- | --- | --- | --- |
    | Work page (Actions) | 1400/1800 | 5 rows, 36-character IDs, 160-character text, notice | **fail** | 1600/2000 |
    | Positive Actions panel | 440/650 | 5 rows, 160-character title/owner, fold | **fail** | 650/850 |
    | Positive case panels (Incidents/Maintenance) | 440/650, or not separately stated | 5 rows with `Read full text` previews and pager | **fail at 1440** | 650/650 (680 one-open) |
    | Empty panel | 430/520 | Empty card plus R92 basis disclosure (mock 316/336, no disclosure) | at risk at 390 | none for zero |
    | Work strip | 100/150 | `Scoped to` plus 160-character? Strip text is fixed | likely pass | 100/150 |
    | Work notice | 110/160 | 160-character cutoff sentence | likely pass | 110/160 |
    | Action page | 1250/1600 | 160-character title and owner, 3 criteria, notice | **fail at 390** | 1500/1900 |
    | Action strip | 100/120 | 160-character owner plus full Site name, wrapped (R99) | **fail** | 140/200 |
    | Criteria panel | 360/590 | 3 fixed literal rows (mock 243/401); text is fixed, not user data | likely pass | 500/760 for 4 rows |
    | Action notice | 100/140 | Fixed literal | pass | 110/160 |

    Options:
    - (a) Adopt the cold final caps for the matching EV surfaces now, as in the precedent column. For the EV criteria panel keep 360/590, since it holds three fixed rows. Rule the empty-panel cap after including R92's disclosure (proposal 460/560).
    - (b) Keep the spec numbers and accept round-trips.
    - Recommend (a). Also state up front what happens if a remeasure still exceeds a cap. K4 ruling 7's wording would do: report the fixture, width and height to the Architect before review; never clip, drop content or silently enlarge.

26. **User-expanded states that need an exemption ruled up front.** None of these is named in the W5-04 spec:
    - `ev-work` Actions:
      - the open `Finding version` / revision disclosure in the Source cell (R75);
      - the `Show all {n} Actions` fold expanded;
      - long-text disclosures, if V2a reuses K2's.
    - `ev-work-incidents`:
      - `Read full text` with one open and with all open (K3 ruling 18/25 pattern);
      - `UTC and IDs` and `Finding version` disclosures (K4 ruling 14, one-line UUID scroller);
      - the basis disclosure.
    - `ev-work-maintenance`:
      - the Activity and Outcome note disclosures (R81/R82);
      - `Read full text`;
      - `UTC and IDs`;
      - the basis disclosure.
    - `ev-action`: there is no disclosure in the mock. If V4a adds a `Finding version` to the strip, it is height-exempt (K4 ruling 6/17); recommend not adding one (see 15).

    Recommend one sentence that mirrors K4 ruling 7: any user-opened disclosure or fold is exempt from page, panel and strip height caps but keeps full text, containment, one-line UUIDs in their own scroller, row count, panel order and zero document overflow. Its measured height is reported, not gated.

## F. Status of rulings 1-46

**Hold as written:** 4, 6, 7, 8, 16, 18, 20, 23, 24, 25, 26, 27, 28, 30, 31, 34 (plus point 17), 35, 36, 37, 38, 40, 42, 45 and 46.

**Hold with a confirmation or minor wording fix:**
- 1 and 2: the order and ownership hold; the gate is open while K4 is unmerged (point 1).
- 3: about 20 files (point 2).
- 5: the generated name is unverified (point 3).
- 9: no mapping exists yet; carry both literals (point 12).
- 10 and 11: their cold test impact is not on V1b's list (point 11).
- 12: wording `ev_session_revision.id` (point 9).
- 17: the exact lines are :214/:220 (point 12).
- 21: depends on the K0 source (point 8).
- 33: cold stays `1 actions` (point 19).
- 41: the outcome is "leave open" (point 22).
- 43: `follow_on` precedent (point 21).

**Need an Architect amendment:**
- 13: the pin structure (point 10).
- 14: the citation source (points 6/7).
- 15: the location (point 5).
- 19: `decision_clock` (point 8).
- 22: the subtitle (point 20).
- 29: no topbar; R88 instead (point 14).
- 32: always the fallback (point 20).
- 39: no Foundation read on V3a (point 13).
- 44: conflicts with K4's shortName status line (point 15).
- The spec's cap table (points 25/26).

**Total: 26 points.** The likely blockers before V1a are 1, 3, 6, 8 and 11; before V2a, 14, 17, 18, 23 and 25; before V4a, 15, 16, 24 and 25.
