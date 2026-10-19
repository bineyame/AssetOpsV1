# Independent spec review: W4-01 and W3-01 build specs (2026-10-20)

Reviewer: fresh Claude spec reviewer, read-only, worktree `AssetOpsV1-plan2` on main `5e45ea83`.
Inputs: `.agent/W4-01-build-spec.md`, `tasks/W4-01-work-case-core.md`, `.agent/W3-01-build-spec.md`,
`tasks/W3-01-estate-claim-action-roots.md`, `.agent/post-W2-sequence.md`, `.ai/ROLE_CONFIG.md` (Token Efficiency:
readiness gate and expanded dry-read), `D-2026-10-20-*` in `.ai/DECISIONS.md`, the merged code, and v69 `screens.js`,
`browser-review.json`.

Method: I read each spec commit by commit as the implementer would, and checked every named path:symbol, table, constraint,
route, guard and test file against the merged tree. Line refs `W4:Lnn` are to `.agent/W4-01-build-spec.md`, and
`W3:Lnn` are to `.agent/W3-01-build-spec.md`.

Verified as correct (so they are not listed below): every scoped FK target in `0027` exists with a matching UNIQUE
(`site_tenant_id_unique`, `asset_scope_unique`, `finding_revision_finding_scope_unique`, `action_site_unique`,
`action_event_site_unique`, `accepted_evidence_scope_unique`). The 11 tables, 11 triggers and 7 explicit indexes
match the stated counts, and the downgrade drop order respects the FKs. These symbols exist:
`finding_api.py:Access,Scope,development_access,ACCESS_BASIS`, `FindingIndexService.read`, `ActionIndexService.read`,
`actions/lifecycle.py:reduce`, `SourceProvenanceResolver.resolve`, `cold_reads.STATES`, `ev_reads.STATES` and
`sourceProvenance.tsx:SOURCE_WORDS`. The `browser-review.json` 1440 heights of 1101 are confirmed. Main still ends at
`0025_w2_ev_session`, so `0026_w2_ev_money` is unverified, as both specs say.

Readiness gate (ROLE_CONFIG): neither spec meets it yet. Both defer the exact fixture Site/Foundation values and
accepted IDs to "after W2 merge". W2-07 DTOs are not on main. The dry-read questions below remain open.

---

## W4-01 work-case core: questions

### Blockers

1. **Blocker** (W4:L289, L337-L339). The list row JSON is incomplete. The incident row has no `narrative` for "What
   happened", no Finding revision IDs or label for "Linked findings" (only `finding_ids`), and no Asset label. There is
   **no maintenance row shape at all**: activity, outcome, next evidence, request state and asset code/name have no keys
   or types. I need the literal row object for both kinds.
2. **Blocker** (W4:L339 vs DDL L162-L186). `Next evidence` = "authored plan criterion", but `maintenance_plan` has no
   criterion column and no request↔plan link exists (`maintenance_work_request` has no `plan_id`). Is this column a
   permanent `No next evidence recorded`, or is a column missing from the binding DDL?
3. **Blocker** (W4:L268). `GET /work/cases/{id}?known_at=` has no response body. `POST .../events` returns only "exact
   object ID, code and revision/event ID", with no literal JSON. The detail read is in the frozen surface (L351), so its
   keys must be fixed before the freeze.
4. **Blocker** (W4:L42, L279, L282). Event payload schemas per kind are undefined. Open points:
   - the ASSIGN `assignee` format and length;
   - the COMPLETE record-ID key name;
   - the COMMENT text key and its limit;
   - whether CLOSE, REOPEN and CANCEL carry a reason;
   - which keys are rejected, and with which code.

   `work_event.payload` is free jsonb.
5. **Blocker** (W4:L21 vs DDL). L21 says every mutation has `actor_kind`, `authorization_basis` and an actor-supplied
   `occurred_at`, but the binding DDL does not store them:
   - `work_case_revision` lacks `authorization_basis` and `occurred_at`;
   - `maintenance_plan`, `maintenance_record` and `operational_record` lack `actor_kind` and `authorization_basis`;
   - `maintenance_plan` has no `occurred_at` and **no `correction_reason`**, yet L286 sends one.

   Do I add columns, which the spec calls binding, or drop the request fields?
6. **Blocker** (W4:L72, L86, L94, L109, L155 vs L271). A create carries one `idempotency_key`, but the schema needs
   `work_case.create_key`, `incident.incident_key` or `request_key`, revision 1 `idempotency_key`/`payload_sha256` and
   the CREATED event key/hash. Which value goes into each? What is "canonical JSON"? I need to know:
   - which fields are hashed, and whether `actor` is included;
   - key ordering and separators;
   - how timestamps and decimals are normalised;
   - how it differs per table.
7. **Blocker** (W4:L289, L314). The fixture Sites `CR-LAB-001` and `MG-DEMO-01` do not exist. The merged codes are
   `COLD-LAB-001`, `KOBO-001` and `EV-LAB-001`, and `import_kobo.py:147` explicitly refuses the mock value `MG-DEMO-01`.
   "Ordinary accepted cold start/request/result IDs from the W2-03 replay" is not a cold-replay concept. Name the
   Site, the replay entry point and the exact accepted IDs to cite. Also, the positive Incident on a cold Site would
   render on the cold Work tab, which W5-02 owns (`cold-work-incidents`, `post-W2-sequence.md:209`). Should the
   positive case be on KOBO-001?
8. **Blocker** (W4:L289, L310). `selection_token`, the "writer fence" and the "full snapshot fence" are undefined.
   What rows are hashed, in what form, with what prefix? Which change raises 409 on page two? W3 defines its token at
   W3:L139; W4 does not.
9. **Blocker** (W4:L292). The derivation of `status` and `coverage` is undefined:
   - which job tables count as "overlapping PENDING/LEASED/FAILED work" for a pinned Finding or Action link
     (`recompute_job`, `financial_consequence_work`, `cold_consequence_work`?);
   - what "cited selected source reported stale" reads;
   - the COMPLETE/PARTIAL/UNKNOWN rule;
   - the precedence among states;
   - the value of `coverage.reason`.
10. **Blocker** (W4:L13, L335 vs code). The Work subrow is rendered in `shell/SiteAnalyticsFrames.tsx:1013-1014`
    (`<UnavailableTab label="Incidents"/>`, `"Maintenance"`), not in `operatorSiteTabs.tsx`. The spec also leaves out:
    - the two new route paths (e.g. `/sites/:siteId/work/incidents`?);
    - the URL query parameter names;
    - whether the lists reuse `SiteWorkActions`' choose-window state and its whole-UTC-day window form
      (`SiteWorkActions.tsx:113-160`);
    - the default window when the URL has none.
11. **Blocker** (W4:L40, L275 vs `D-2026-10-20-shared-provenance-dto`). The create example returns
    `basis_sha256:null` although case revision 1 is a selected revision. The decision allows null only without a
    selected revision. Open points:
    - which `selected_revision_ids` feed the derived hash for a case;
    - how a pinned Action version's cited set is read (`action_basis_evidence` is per Action, not per event);
    - whether W4 writes `evidence/public_provenance.py` itself if W3-01 commit 1 has not merged, and in which W4
      commit.

### Should

12. **Should** (W4:L32, L304). Does OPEN_VERIFICATION or a VERIFIED/INEFFECTIVE/INCONCLUSIVE attempt return
    `WORK_TRANSITION_INVALID` or `WORK_OUTCOME_NOT_SUPPORTED`?
13. **Should** (W4:L35-L37). Plan ACTIVATE/PAUSE/CANCEL and OperationalRecord ACCEPT/REJECT "return 409", but no
    route accepts those commands (L268, L286). Which endpoint and test proves the 409, or is it simply unreachable?
14. **Should** (W4:L23, L286, L303). A non-head predecessor uses `WORK_BASIS_CHANGED`, whose copy is about list
    cursors. The case-revision concurrent-successor 409 (L23) has no named code. Supply the correction-specific
    message and UI copy.
15. **Should** (W4:L21, L310). Refusal codes are missing for:
    - `occurred_at` more than 5 minutes in the future, or backdated more than 30 days;
    - a window over 31 days, missing `from`/`to`, or `from` ≥ `to`;
    - `limit` outside 1..100;
    - `known_at` after the snapshot.

    Also missing: the default for `known_at` (W3 uses DB time), and the "displayed as such" copy for backdated
    entries.
16. **Should** (W4:L282, L188-L203). COMPLETE without a record field: is that `WORK_INPUT_INVALID` or
    `WORK_LINK_SCOPE_INVALID`? Can a MaintenanceRecord be posted against an Incident case? The FK allows any kind.
    `maintenance_record.supersedes_record_id` exists, but no correction route does. Is it unreached? What is the
    "same root" rule for records?
17. **Should** (W4:L284, L314). In a correction, does omitting `cited_accepted_evidence_ids` copy the set (as links
    are copied) or clear it ("correction replaces the set")? Are asset and `occurred_at` immutable? What exactly is
    the negative branch "backdated correction" when revisions store no `occurred_at`?
18. **Should** (W4:L19). For "accepted before the command's DB time", `accepted_evidence` has `published_at` and
    `received_at` but no accepted time. Which column applies?
19. **Should** (W4:L21, L310, L82). Which rows does the maintenance list contain? Are plans included ("request/plan
    `recorded_at`")? The columns are request-only. `work_case` has `created_at`, not `recorded_at`. What does
    `total_count` count, and what is the incident `known_at` filter (`created_at <= known_at`)?
20. **Should** (W4:L339 vs `screens.js:189-191`). The mock Maintenance `Activity` column shows the request state
    badge (`Completed`, blue) next to `Unverified`. The spec maps Activity to record text and shows the request state
    nowhere. This is a user-visible mismatch, rated High by project rule. The Incident `Window` copy format
    (`6 Oct · from 19:11`) is also unspecified.
21. **Should** (W4:L345 vs `screens.js:189`). The mock Incident `Open` chip is red, but the spec says amber. Display
    labels for OPEN, IN_PROGRESS, CLOSED, CANCELLED and COMPLETED are not given.
22. **Should** (W4:L336). The `site.name` and "site short name" source is unclear, because the list body carries only
    `site_code`. The mock uses the first word of the Site name. Which field and which read supply it?
23. **Should** (W4:L331). "First 5 rows with in-panel paging" leaves open:
    - the client `limit` value against the API default of 50;
    - the paging control component and its copy;
    - how the paging interacts with `next_cursor`.
24. **Should** (W4:L337, L345). Are pinned Finding links hrefs (`siteFindingHref` with `revision_id` exists), or plain
    text? What is the label? W1 Findings have no `F-` code.
25. **Should** (W4:L316). The list of literal Alembic heads is incomplete. `0025_w2_ev_session` is also asserted in:
    - `test_s1_bindings_postgres.py:118`;
    - `test_s2_evidence_ledger_postgres.py:447`;
    - `test_s405_publication_postgres.py:492`;
    - `test_s4_consequence_store_postgres.py`;
    - `test_s4_evidence_consequence_work_postgres.py`;
    - `test_w200_source_events_postgres.py:562,611`;
    - `test_w201_cold_foundation_postgres.py:456,464`;
    - `test_w206_ev_migration_postgres.py:29`.

    The frontend tests that assert Incidents/Maintenance are unavailable are also not listed:
    `operatorSiteTabs.test.tsx`, `operatorRouteFrames.test.tsx`, `w1f4ChangesWorkStructure.test.tsx` and
    `siteWorkActions.test.tsx`. Neither is `tools/checks/navigation-rail-fixtures.ps1`.
26. **Should** (W4:L316). No named test covers the HTTP layer:
    - the 401/403/404/409/422/503 table;
    - the idempotent 200 retry;
    - the list refusal body with `rows`/`total_count` null;
    - validation order (scope before shape).

    The count "2+7+3" therefore leaves the API untested.
27. **Should** (W4:L9 vs `tools/checks/configuration-persistence.ps1:746-756`). The rule-8 writer is declared in
    commit 1, but the writer (`work/adapters/postgres_work_store.py`) arrives in commit 2. Per-table INSERT
    anti-vacuity counts would fail at commit 1. Which commit adds it, and with which `$workWriter` and table list?
28. **Should** (W4:L11, L298). `action_api.py:65` uses a separate `command_access` seam; the spec names only
    `Access`/`development_access`. Open points:
    - who may write;
    - whether a client-asserted `actor.kind=USER` is accepted when no human principal exists (W1 Action events are
      SYSTEM-only);
    - the exact SERVICE attestation format ("service, job and rule version");
    - whether the server overwrites `authorization_basis`.
29. **Should** (W4:L351 vs v69 global screens `screens.js:514-517`, OPREC, `maintenancePreventive`). The freeze fixes
    OPEN/IN_PROGRESS/CLOSED with no severity, owner, type, success criterion, plan interval or "what it proves", and
    OperationalRecord states without the mock's `Requested` or `In review`. That guarantees W6-01 amendments against
    its own mock. Confirm this is intended before ACCEPT freezes it.
30. **Should** (W4:L314). Server-generated UUIDs differ per test DB. How does a static fixture "store resolved IDs"?
    Is ID generation injectable, and how are the example IDs `1000…0101` produced?
31. **Should** (W4:L336, L343 vs `navigation-truthfulness.ps1:724-740`). `Manage in … · Not available yet` and the
    other static unavailable text cannot use `UnavailableEntry`, because the guard forbids any use outside the closed
    multiset. Which component renders them?

### Nit

32. **Nit** (W4:L13). There is no `Status` component. `ui/` has `ProductStatus.tsx` and `Disclosure.tsx`.
33. **Nit** (W4:L13). The new files are lowercase (`siteWorkIncidents.tsx`), but existing page files are PascalCase
    (`SiteWorkActions.tsx`).
34. **Nit** (W4:L81-L82). The incidents query filters on `(kind, occurred_at)`, but `work_case_site_window` has no
    `kind`. Is the extra index intended?
35. **Nit** (W4:L301). Is `WORK_EVENT_DUPLICATE_KEY` also the code for case, plan, record and OperationalRecord
    creates?
36. **Nit** (W4:L212). `'Infinity'::numeric` needs PostgreSQL 14 or later. Confirm the container version.
37. **Nit** (W4:L325). The 390 Incidents panel cap of 460 px with five 2-line rows in a table at least 720 px wide is
    tight. Confirm the budget applies to the stocked state.

**W4-01 count: 37 (Blocker 11, Should 20, Nit 6).**

---

## W3-01 estate Finding and Action roots: questions

### Blockers

1. **Blocker** (W3:L82, L85, L107 vs code). Global `/findings` is already live: `OperatorShellLayout.tsx:54`
   renders the T028 `FindingsIndex` (`sites/FindingsIndexes.tsx`, `SiteAnalyticsFrames.tsx:373`) from
   `/api/findings` (`analytics_api.py:78`). Legacy `/findings/:siteId/:assessmentId[/:findingTab]` routes also exist
   (`operatorSiteRoutes.ts:295-297`). The spec does not say:
   - whether W3 replaces the page and API or keeps them;
   - what happens to the legacy routes and their tests;
   - the app paths for the Cost, Risks and Opportunities lens tabs.
2. **Blocker** (W3:L175, L189 vs `SiteFindingIndex.tsx:70-82`, `navigation-truthfulness.ps1:724`). The guarded
   `Cost`/`Risks`/`Opportunities` unavailable chips are the **Site** Findings lens chips, not estate tabs. W3 builds
   estate lenses only. Removing those chips requires Site-level lens views that no commit builds. Which applies: keep
   the Site chips and add new estate tab links, or build Site lenses?
3. **Blocker** (W3:L101-L103, L107, L110, L176 vs `0009_finding_store.py:70-72`). The W1 `lifecycle` values are
   SUPPORTED, UNCONFIRMED, NO_LONGER_SUPPORTED and MERGED; `OPENED` is a *transition*. The following have no mapping:
   - `state=open|withdrawn|closed`;
   - "Open findings counts OPEN/OPENED";
   - the chips Open, Withdrawn and Closed;
   - the example `"lifecycle":"OPENED"`.
4. **Blocker** (W3:L103, L116 vs `actions/lifecycle.py:23-41`, `0019_verification_core.py`). The reduced Action
   states are NONE_AT_CUTOFF, PENDING and APPLIED (FAILED leaves the state unchanged), plus RESOLVED and
   RESOLUTION_WITHDRAWN events. The example `"state":"ACCEPTED"` is not a reducer output. Undefined:
   - the "nonterminal" set;
   - display labels and chip tones;
   - the "Verification window" predicate over `verification_plan.later_start/later_end`;
   - the "Verified in 30 days" rule under `verification_outcome` supersession and RESOLUTION_WITHDRAWN.
5. **Blocker** (W3:L93-L97 vs `finding_index.py:231-275`). `FindingIndexService.read` works per Site and per
   `finding_domain`/`analytic_id`. Its currentness is a per-day S3 selection with S4 match-pass gating
   (`MATCH_PENDING`), not "latest revision by (recorded_at,id)". Do I call the service per Site (its store opens its
   own connection, so there is no shared REPEATABLE READ) or reimplement its SQL? The per-Site coverage fields have
   no source and no enum per domain (mini-grid finding, `cold_episode`, `ev_session`):
   - `committed_watermark`;
   - `selection_id`;
   - `job_state` (SETTLED/NONE/…);
   - `source_freshness` (RECENT/UNKNOWN/…).
6. **Blocker** (W3:L93, L123-L129 vs `finding_api.py:35-47`). `Access` is per Site code (`(request, site_code) ->
   401|403|None`). No principal, grant enumeration, signing key or "policy version" exists. How are the authorized
   Site set and the signed `access_basis` computed in the development composition? The estate routes have no Site
   filter parameter, yet 403 `ESTATE_SCOPE_FORBIDDEN` and 404 `ESTATE_SITE_NOT_FOUND` refer to one.
7. **Blocker** (W3:L101, L110, L177-L178). The `consequence` object is undefined:
   - the `state` enum (UNPRICED and what else?);
   - the `amount` type (decimal string or number) and the currency format;
   - the source table per domain (`financial_consequence_revision`, `cold_consequence_revision`, the unmerged W2-07
     EV money);
   - the "acceptable source gate";
   - the copy for each state.
8. **Blocker** (W3:L80, L143 vs `sourceProvenance.tsx:101-104`). Renaming the public key `state` to
   `classification` makes `sourceState()` return UNKNOWN for every W1 page. That is 21 frontend consumers silently
   showing "Source unverified". The frontend fix is deferred to Lane A "after both lanes merge", so commit 1 cannot
   pass review alone. Should `state` stay as an alias, or does the frontend change land in the same merge, and who
   owns it? The backend call sites to switch are also not enumerated: `finding_read`, `consequence_read`,
   `consequence_history`, `cold_site_reads`, `cold_consequence`, the EV `_envelope` in `postgres_assessment_store`,
   `site_overview/read` and `actions/service`.
9. **Blocker** (W3:L107-L119, L177, L183). The rows lack displayed fields:
   - Site name (the `Site` column);
   - the visible Finding code (W1 has none; the mock shows `F-104`);
   - the Action title from the recommendation snapshot;
   - the snapshot key path for `success_criterion`;
   - the `lens_flags` enum values and their display.

   `GET /api/estate/scope` has no response body.
10. **Blocker** (W3:L141-L147). Provenance DTO rulings are needed before commit 1. See D1–D7 below.

### Should

11. **Should** (W3:L103 vs L174). The null copy conflicts: `Priority not recorded` and `Confidence not recorded`
    against `Not assessed`. Notes for the other cards (mock: `Accepted work`, `ACT-048`, `No closed verification yet`)
    are unmapped. In `Across {n} sites`, is n the authorized or the covered count?
12. **Should** (W3:L139). The `selection_token` input form is not exact: JSON structure and key names, the `sha256:`
    prefix, and whether cold and EV selected IDs are included.
13. **Should** (W3:L95). Is the window grain whole UTC days, as in W1 FindingIndex and SiteWorkActions, or arbitrary
    instants? How is an open episode (null end) handled? What is the `episode_start` field per domain
    (`finding.anchor_start`, `cold_episode`, `ev_session`)?
14. **Should** (W3:L95). An Action whose `created_at` is in the window but after `known_at`, or with no event at or
    before `known_at`: is it included or excluded?
15. **Should** (W3:L131). When does `ESTATE_SELECTION_INCONSISTENT` apply, as opposed to `ESTATE_BASIS_CHANGED` or
    503?
16. **Should** (W3:L82). `App.tsx` routes and the rail are Lane A files, so commit 3 is invisible without a Lane A
    patch. Who writes that patch, at which commit, and can Lane B test pages through its own router?
17. **Should** (W3:L82, L157). Which window/date-bar component is used (`periodStrip.tsx`? the SiteWorkActions
    form?), with which query parameter names and which first-load default (the API requires a window)?
18. **Should** (W3:L184 vs `screens.js:510-512`). The mock Actions panel subcopy (`Lifecycle: Open → In progress →
    Completed → Verification window → …`) is unmapped. The notice replaces the mock copy; record that as a ruled
    rewrite.
19. **Should** (W3:L176, L183, L187). Chip tones are missing for Action states, Finding lifecycle values and row
    status (PENDING_RECOMPUTE, STALE, HISTORICAL).
20. **Should** (W3:L151). The fixture is unspecified in several places:
    - which Site has an "absent selection" (a newly imported Site, and with what code?);
    - the paths of the EV manifests and the cold replay;
    - how the foreign tenant is created.

    The examples use `MG-DEMO-01`, but the merged codes are `KOBO-001`, `COLD-LAB-001` and `EV-LAB-001`.
21. **Should** (W3:L153). `test_s4_site_finding_index*` does not exist; the actual files are
    `test_s4_finding_index_postgres.py` and `test_s4_finding_index_reach.py`. The spec does not list which files'
    public-DTO assertions change.
22. **Should** (W3:L187). A static unsupported CTA or an unavailable Incident link cannot use `UnavailableEntry` (the
    closed-multiset guard). Which component renders them?
23. **Should** (W3:L81). Guard allowlists are missing: SQLAlchemy and dependency-direction entries for
    `estate/adapters/postgres_estate_read.py`, and the new top-level `estate` package. ROLE_CONFIG requires them in
    the spec.
24. **Should** (W3:L80 vs `post-W2-sequence.md:221`). `frontend/src/sites/sourceProvenance.tsx` is not on Lane A's
    shared list, yet W3 assigns it to Lane A. The W1/W2 backend read modules it changes are not Lane B domain
    modules. Rule the ownership.
25. **Should** (W3:L97). Actions exist only on mini-grid. Is a cold or EV Site `NOT_APPLICABLE` for the Actions
    coverage, and does it count toward `covered_site_count`?
26. **Should** (W3:L103). How does "Awaiting verification" join Finding to Action? Via `action.origin_finding_id`
    only, or `origin_finding_revision_id` = the selected revision?

### Nit

27. **Nit** (W3:L110). `source_ids:["source-1"]`, but `accepted_evidence.source_id` is a uuid.
28. **Nit** (W3:L132). Is a missing `from`/`to` refused as `INVALID_WINDOW`? Say so.
29. **Nit** (W3:L74). "Main ends at 0025" is correct. Name the W2-07 DTO fields to recheck, rather than "recheck at
    merge".

**W3-01 count: 29 (Blocker 10, Should 16, Nit 3).**

---

## `D-2026-10-20-shared-provenance-dto`: is it concrete enough?

**Verdict: no, not yet.** The 5-key shape, the enum, the source of `source_ids`/`evidence_ids` and the
null-without-selection rule are concrete. The following need an Architect ruling before W3-01 commit 1:

- D1 **Blocker**. "The sole class basis is `resolve` over the full cited union" conflicts with
  `SourceProvenanceResolver.consequence_revision`. That method fails closed: a Finding-revision UNKNOWN forces
  consequence UNKNOWN and adds `CONSEQUENCE_POWER_INPUT_CONFLICT` (`D-2026-10-15-s405-stored-demo-provenance`). Is
  that rule kept for consequence rows?
- D2 **Blocker**. Backward compatibility: does the public `state` key survive as an alias? The W3 spec adds an
  optional `detail` key that the decision's "exactly five keys" excludes. What are its exact contents?
- D3 **Blocker**. `basis_sha256`:
  - W1 `finding_revision` *does* store `basis_sha256` (a Finding basis, not a provenance basis). Is it used as is?
  - For a consequence row, is it the Finding or the consequence `consequence_basis_sha256`?
  - For an Action row, and for a W4 case revision, which IDs make up `selected_revision_ids`?
  - Both W3 (Action example) and W4 (create example) show `null` with a selected object, which contradicts the rule.
- D4 **Should**. The pending-EV exception in W3:L145 (classification from the current accepted set while
  `basis_sha256` names the prior head) contradicts the decision's "never … an earlier head". Which governs?
- D5 **Should**. The `SOURCE_CLASS_MISMATCH` reason has no shape: its `accepted_evidence_ids` and the field that
  carries the persisted class.
- D6 **Should**. Classifier reasons carry extra keys (`source_classes`, `fixtures`, `run_ids`, `details`). Cold and EV
  strip them to `{code, accepted_evidence_ids}`. Strip or keep? "Sorted" by what? The classifier emits in rule order.
- D7 **Nit**. `source_ids` for UNKNOWN sets with not-found or foreign IDs: only in-scope rows? Also state that the
  resolver is single-Site, so no estate-level union is ever classified.

---

## Contradictions summary

- **Merged code.**
  - Wrong Work-subrow file (W4 B10).
  - Nonexistent Site codes (W4 B7).
  - Finding lifecycle and Action state enums (W3 B3, B4).
  - The existing `/findings` page and API are ignored (W3 B1).
  - The chips being removed are Site chips, not estate chips (W3 B2).
  - Incomplete head-test list (W4 S25).
  - Nonexistent test names (W3 S21).
  - No `Status` component (W4 N32).
- **v69 mock.**
  - Maintenance Activity column versus state (W4 S20).
  - Incident Open chip tone (W4 S21).
  - Actions subcopy (W3 S18).
  - Frozen W4 states versus the global Incidents and OperationalRecord mock (W4 S29).
- **Post-W2 sequence.** Migration `0027` and Lane A ownership are consistent. Inconsistent:
  - the cold-Site positive case overlaps W5-02 (W4 B7);
  - `sourceProvenance.tsx` and the W1/W2 read modules are not on the ownership ledger (W3 S24);
  - Lane B commit 3 needs Lane A route-table integration with no stated point (W3 S16).

**Totals: W4-01 37 (11 Blocker), W3-01 29 (10 Blocker), DTO 7 (3 Blocker, counted with W3-01 B10).**
