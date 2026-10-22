# Decisions

## 2026-10-22

Decision: `D-2026-10-22-w5-02-w5-04-buildspec` (Codex Architect/Planner). [W5-02](../tasks/W5-02-cold-work.md) and [W5-04](../tasks/W5-04-ev-work.md) reuse merged W4 Incident/Maintenance roots and the W1 Action UI/route. The W1 database `action` row is battery-reserve-trial-only (`0016_action_store.py`), so the [cold](../.agent/W5-02-build-spec.md) and [EV](../.agent/W5-04-build-spec.md) contracts add a persisted `domain_action` root under the shared public Action code/route namespace, a union Site Action index and an explicit W4 case-link relation; no dummy battery Action is allowed. `0033_w5_cold_work` follows W5-01b's `0032_w5_cold_scenarios` and adds the Action root, immutable success intent and case link. W5-03b's reserved parent remains exactly `0033_w5_cold_work`. `0035_w5_ev_work` follows W5-03b's `0034_w5_ev_scenarios` and extends that root/intent to EV. Intent is neither the mini-grid `reserve-trial-verification-1` plan nor a verified outcome; W2 faults do not automatically create cases. Each task has three reviewed merges: root/intent/Action tab, Incident and Maintenance tabs, Action detail/closeout. W6-01 retains global Work reads and rail ownership. Labelled mock deviations cover the unsupported global create promise, live due-date copy and retained W1 Action tabs and global Actions parity that the W3 battery-only root cannot supply; no mock graphic is replaced. Planning only: independent readiness review, owner wave-start gate, per-unit review and owner visible acceptance still apply.

Amendment to `D-2026-10-22-w5-01-w5-03-buildspec` (C3 rulings Q-C3-5 and mock differences, Codex Architect, 2026-10-22): The `cold-health` mock's `Condition and evidence` Asset cells show compact asset codes and a horizontally scrolled table at 390. C3 keeps its 330/430 px panel cap and adds a scoped sticky first column with each full selected Foundation UUID on one line inside the table scroller. The three condition cards use the mock's assessment top border and 17 px body-colour value, with plain labels and separate `View detail →` links. The `(cooling,1)` and `(cooling,2)` registry reasons are fixed as literal Architect copy in `.agent/W5-01-build-spec.md` "C3 rulings (Q-C3-5, mock differences)". This is a spec ruling; implementation and review remain open.

Amendment to `D-2026-10-22-w5-01-w5-03-buildspec` (C3 rulings Q-C3-1..4, Codex Architect, 2026-10-22): The `cold-health` mock has three condition cards and one condition table under the Site-name heading. C3 extracts the existing S7 Data sources panel as a source-only export in `SiteHealth.tsx` and mounts it after the cold condition notice, without the S7 battery strip, physical battery panel or blue battery notice. **MOCK DEVIATION:** this source panel is additional to the cold Health mock, retained for the live cold Foundation Data sources link and kept separate from physical condition; the spec records the mock-faithful alternatives. The Health h1 remains the Site name. C3 also owns the now-live Health href assertion in `coldDepth.test.tsx` and the fragment-link assertion in `coldFoundation.test.tsx`. See `.agent/W5-01-build-spec.md` "C3 rulings (Q-C3-1..4)" for the exact export, render plan and tests. No implementation or owner acceptance is claimed.

Amendment to `D-2026-10-22-w5-01-w5-03-buildspec` (Codex retrospective, 2026-10-22): The appended Codex retrospectives in both W5 build specs supersede Claude's C2 `Status` heading, table-only Recovery curves and E3 table-only import-power panel. C2 restores the mock `Match` heading with `Not established` comparison cells and a selected-observation graphic through a registered graphics module; existing W2 records yield no invented recovery curve. E3 restores a selected import-sample chart and configured-limit line only with an E1b selected sample series, retaining the table and unknown/empty states. E2 keeps the mock's div-bar form but draws the selected spans in time order with window-derived axis labels; grouped duration totals remain text, not a false timeline. C3/E4 condition notices and live-selection notices are labelled `MOCK DEVIATION` with reasons and alternatives in the specs. C2 at `2812d7aa` requires rebuild/re-review; E1b and E3 need the stated wire/UI delta. No implementation or owner acceptance is claimed.

Amendment to `D-2026-10-22-w6-01-buildspec` (Codex retrospective, 2026-10-22): The appended W6 retrospective confirms the A1Q/A2Q/CL3 selected-work and mock-layout decisions, with explicit labelled mock deviations. B3 and E2 must restore the mock's live Preventive plan and Operational records Evidence-root destinations, including query-preserving links and captures. R8's unconditional dev/built request-count assertion is replaced by a manifest of observed requests and the rendered response. The W6 unit reviews remain gates; no owner acceptance is claimed.

Decision: `D-2026-10-22-w6-01-buildspec`. Codex Architect/Planner splits the seven-screen W6-01 Global work-cases row into five independently mergeable slices: [W6-01a-e](../tasks/W6-01-global-work-cases.md), ordered Incidents, Maintenance/Preventive, request Overview/Record, request History, and Operational records. The [build contract](../.agent/W6-01-build-spec.md) consumes merged W4-01 identities, event/correction order and refusal codes and W3 estate authorization/cursor patterns; it does not reinterpret Action or promote authored records to accepted equipment evidence. Existing `0027` tables suffice for read-only global projections, so reservation `0036` is unused and no Alembic revision is made; current main head is `0030_w4_mini_decisions`. Lane B owns work domain/page modules, Lane A serially integrates main/router/shell/registry/guards with per-unit review. **The readiness gate remains closed:** the seven mock screens could not be measured at 1440/390 because headless Chrome/Edge fail on this host; persisted fixtures and final literals/guard runs also require execution/closure. This decision authorizes planning order, not implementation dispatch, panel promotion or owner acceptance.

Amendment, 2026-10-22: Independent W6-01 readiness review items 1–36 are mapped to literal DTO/refusal/copy/route/producer/file/test/cap artifacts in the updated build contract. Site routes use stored Site code; global roots follow W3 silent Site omission and signed-cursor rules; manual reading remains a read-only gap. `P-work-cases` carries an Architect W6 Real-with-honest-gaps recommendation while owner status stays pending. Design caps are set, but the browser helper still stalls at `Page.enable`; the specified worst-case remeasurement and fresh readiness review remain gates before implementation dispatch. No owner acceptance or build completion is asserted.

Amendment to `D-2026-10-22-w6-01-buildspec` (2026-10-22, closure round 2): The W6-01 contract closes OI-1 through OI-10 with root-time global order and cursor ties, staged Site Work literals and test/guard ownership, six-digit nested W4 detail times, measured request-header and chip caps, explicit fixture occurrence/window and page query rules, provenance selected-ID and empty-scope precedence, route-specific detail/auth wording, capture/review ownership, and first implementation capture limits. `.agent/W6-01-mock-measure-2.md` supplies successful mock measurements; fresh independent readiness review still gates dispatch, and actual page captures gate each unit review, and the pending-owner registry rows require owner walkthrough acceptance before merge/promotion. This is a planning amendment, not an implementation or owner acceptance claim.

Amendment to `D-2026-10-22-w6-01-buildspec` (2026-10-22, OI-11): The W6-01 contract now fixes the Site Work strip global-link helper and URL query, keeps the shared unavailable status and missing-claim exemption through A2, removes both in B2, and aligns request, plan and operational example times with the frozen fixture offsets. Fresh independent closure review remains the dispatch gate; this amendment claims no build or owner acceptance.

Amendment to `D-2026-10-22-w6-01-buildspec` (2026-10-22, A1Q; produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively): The W6-01 contract (section 3.1) answers the A1 builder's Q1-Q9 literally. A1 Lane A now owns `work/composition.py` (`build_global_work_read`, `build_global_work_index_service`), the `main.py` mount and one `$pgReaders` line in `tools/checks/configuration-persistence.ps1`. The global reader reuses the W4 per-Site `_ReadTx` on one snapshot. Rulings: W4 row-provenance parity with `missing_lineage`; page-one status carried by the cursor as `page_one_mode`, with the estate wire-second page-two cutoff; estate `imported_at < to` candidates; W4 `clock_timestamp()` read time with a constructor-only test clock; W4 link labels and order; fallback links carry the response `known_at`; fixture principal `service:w401-fixture`. The guard/composition sweep assigns C1 its composition and `main.py` wiring, keeps B1/E1 wiring-free, and gives A2/B2/B3/C2/C3/C4/E2 their route constants, rail, fixture, `$expectedTabs` and screen-ledger literals. W5-01/W5-03 gaps of the same class are listed for their Architect in `.agent/W6-01-a1q-w5-sweep.md`; W5 files are unchanged here. No build, merge or owner acceptance is claimed.

Decision: `D-2026-10-22-w5-01-w5-03-buildspec`. Codex Architect/Planner publishes [W5-01](../tasks/W5-01-cold-depth.md) and its [build contract](../.agent/W5-01-build-spec.md), plus [W5-03](../tasks/W5-03-ev-depth.md) and its [build contract](../.agent/W5-03-build-spec.md). W2-F merged as `2df2a3da` and its independent re-audit closed all 14 structural findings, satisfying the W2 structural gate for these specs. W2-F Low L1 is fixed in W5-01 C5 by the refused cold Finding `Finding state` strip with `Unknown` / `Confidence: Unknown` above `PageRefusal`; L2 is evidence-manifest provenance only. W5-01a is read-only selected cooling/Health and W5-01b adds immutable authored cold scenarios with `0032_w5_cold_scenarios` depending exactly on merged `0030_w4_mini_decisions` (`0031` unused). W5-03a is read-only observed connector availability and EV energy; W5-03b adds EV Health and immutable authored scenarios with `0034_w5_ev_scenarios` depending on W5-02's reserved exact `0033_w5_cold_work`. W5-02 must publish and merge that exact head first. Each first sub-slice has at most two new pages with its selected read pipeline; each second has at most two pages with an authored store. W2 session count/configured schedule do not yield availability or charger condition, and cold what-ifs have no observed outcome. The contracts pin literal copy, selected DTO/ID sources, 1440/390 measurements, producer-backed captures, unit ownership and per-unit review. This is planning authority; the independent readiness dry-read, owner wave-start gate, implementation review and owner visible acceptance retain their stated order.
Amendment to `D-2026-10-22-w5-01-w5-03-buildspec` (2026-10-22, closure round 2): The W5-01 and W5-03 build contracts now assign exact registry nodes, panel rows and screen-ledger edits to C3/C5 and E3/E4/E6; their literal combined application passes `check_v69_dependency_registry.cjs` on a scratch copy. Both Health routes retain the S7 gateway contact panel and Foundation destination. Malformed decision attestation uses merged 422; scenario corrections retain revision-1 root windows. Cold depth names the accepted door-event read, optional ambient role and LIMITED sensing state; EV declared-empty `weekly: []` is zero scheduled seconds with null rates and explicit copy. C2/C3 and E2/E3/E4 share validated depth-client ownership. These are planning amendments, not implementation or owner acceptance.
Amendment to `D-2026-10-22-w5-01-w5-03-buildspec` (2026-10-22, C1 builder questions; produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively): W5-01 C1 Cooling (`703807cf`) stands with payload key `cooling`, context keys `label/state/evidence_ids/duration_seconds` on every row, summed door pairs, cited `accepted_evidence_ids`, a new `policy_high_deg_c`, and `recovery_state` read through a new public `cold_site_reads.cooling_response_state` (replacing the private `_capabilities` call). `/cold/health` reads the selected run's single Foundation revision (else the one known at the cutoff over the window) through a new adapter `ColdReadService.foundation_on`, identifies `GENERATOR`/`COMPRESSOR`/`TEMPERATURE_PROBE` components by Foundation `component_type` joined to `asset` on `asset_code`/`asset_type`, and returns three literal rows under `health`; `NOT_CONFIGURED` needs a resolved Foundation lacking the type. Review Lows L1, L2, I1 and I2 are fixed in the C1 follow-up; L3 is closed by citing the merged provenance test because append-only triggers make a ledger-absent cited ID unreachable. C2 gains the label/link sources, C3 the Health DTO rendering and fragment, C4 the `basis_on` basis read; C5 is unchanged. Planning amendment only.
Amendment to `D-2026-10-22-w5-01-w5-03-buildspec` (2026-10-22, A1Q sweep; produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively): The W5-01 and W5-03 contracts now state the guard and composition ownership that the W6-01 A1Q sweep found missing. C1, E1a and E1b read only through existing caller-connection read-service methods, with no SQL, driver import or `ANALYTIC_ID` above the analytics adapter layer; C1 commit `703807cf` already complies, so the in-flight C1 build changes no code. C4 and E5 register their scenario stores as rule-8 INSERT-only writers with probe corpora, and C4 resolves the C1q `basis_on` basis on its store transaction connection. C1, C4, E1b and E5 have literal `main.py` wiring, and E1b has a `financials/composition.py` builder. New HTTP modules avoid the designation tokens, and pages use the shared table and chart primitives. No build or owner acceptance is claimed.

Amendment 2026-10-22: the readiness review's 46 items are closed in the in-place W5-01/W5-03 unit cards and end tables. Cold uses DB-wall decision watermarks and a saved pre-late historical cutoff; EV uses the merged 09:00/09:05 decision clock and `[08:00,09:00)` selection. E1 is split into independently reviewed E1a/E1b. Scenario authored time (`scenario_at`) is separate from evidence `known_at`; the W5 pages retain honest unknown, pending and historical states. The amended specs still require an independent closure recheck before build dispatch.

## 2026-10-20

Decision: `D-2026-10-20-w2-f-structural`. Codex Architect/Planner publishes [W2-F](../tasks/W2-F-structural-fixes.md) and its [exact build contract](../.agent/W2-F-build-spec.md) for all 14 findings in the independent W2 structural audit. The selected cold recovery claim uses one ordered accepted-record rule in Backup, Overview and Evidence; missing resumption cannot read Full, and a thermal excursion without product identity/rule is not a supported product-exposure claim. The other fixes restore mock slots and truthful readiness, refusal, count, bound, assumption, status, source ID and unavailable-tab copy without new evidence or money. Lane A builds schema-free W2-F only after reviewed W4-01 then W3-01 merge, consuming W3-01 q1–q6/commit-1 r1 provenance changes without concurrent edits to the same views; W2-F is independently reviewed, merged and structurally re-audited before the first W5 build. The owner performs the complete product walkthrough after W6. This is planning authority, not implementation or owner acceptance.

Decision: `D-2026-10-20-w4-03-buildspec`. Codex Architect publishes the [W4-03 task packet](../tasks/W4-03-mini-decisions-work.md) and [build spec](../.agent/W4-03-build-spec.md) for mini-grid Site `scenarios`, W1 Finding `alternatives`, typed `opportunity-finding`, and deeper Site Incident/Maintenance context. `0030_w4_mini_decisions` follows W4-02's `0029` and stores immutable authored what-ifs, reviewed alternative explanations, exact renewable opportunity selections, and explicit decision/work associations. The existing W1 Finding schema requires dispatch assessment/run/minute fields and cannot honestly hold a renewable opportunity; a typed opportunity root and Site/estate lens integration avoids fabricated pins. W4-01 case identity and states remain frozen; W4-02's five individually selected local-day hours and W3-01 public provenance govern physical claims. Scenario gross sales remain labelled assumptions and never alter observed money. The contract binds every owned v69 panel/cell/CTA, measured 1440/390 budgets, wire/refusals, state precedence, migration/downgrade, fixtures and one-run commits. This is planning authority, not implementation readiness, independent review, registry resolution or owner acceptance.

Decision: `D-2026-10-20-w3-03-buildspec`. Codex Architect publishes the [W3-03 Portfolio task packet](../tasks/W3-03-portfolio-composition.md) and [build spec](../.agent/W3-03-build-spec.md). Portfolio is a read-only, authorized, one-cutoff composition of reviewed W3-01 Finding/Action and W3-02 Evidence/Financials selections across the three Site domains. It preserves exact object/revision/citation IDs, per-Site coverage and source class, declines a combined numeric measure when categories, windows, assumptions, overlap or coverage are not comparable, and keeps productive-use, asset-life and recovered-value examples honestly unestablished. The four v69 panels, every card/table/matrix cell/chip/CTA, literal copy, API/refusals, 1440/390 measured budgets, fixtures and one-run commits are specified. Existing schema is sufficient; migration reservation `0031` is unused, with no DDL, index, constraint or downgrade. Lane A owns serial shared-file integration. This is planning authority, not implementation readiness, registry approval, independent review or owner acceptance.

Decision: `D-2026-10-20-w4-02-buildspec`. Codex Architect publishes the [W4-02 task packet](../tasks/W4-02-mini-grid-depth.md) and [build spec](../.agent/W4-02-build-spec.md) for mini-grid `renewable`, `service`, `fuel` and `backup` after W4-01 and the `0028` disposition. Migration `0029` owns append-only mini-depth revisions, exact accepted-evidence links and ordered selections. Renewable opportunity needs aligned capability, PV, load, storage and critical-service evidence; service requires a requested denominator; fuel residual requires complete attested deliveries and opening/closing bounds; backup readiness requires a witnessed event-to-service chain. Missing, pending, mixed or contradictory evidence withholds positive claims. W3-01's reviewed shared provenance DTO is consumed, W1 Dispatch/Overview and W4-01 work identity remain distinct, and W4-03 owns scenario/opportunity decisions. The spec binds mock panel/copy mapping, measured 1440/390 budgets, wire/refusals, migration/downgrade, fixtures and one-run commits. This records planning authority, not implementation readiness, independent review, registry resolution or owner acceptance.

Decision: `D-2026-10-20-w3-02-buildspec`. Codex Architect publishes [W3-02 task packet](../tasks/W3-02-estate-evidence-money-basis.md) and [build spec](../.agent/W3-02-build-spec.md) for v69 `globalevidence` and `globalfinancials`. W3-02 is a read-only estate projection of exact W1/W2 Site capability and consequence selections under W3-01 authorized scope and shared provenance DTO. Missing, pending, historical, contradictory or unpriced Sites stay visible; a numeric group total requires matching category, currency, period, assumptions, complete scope and proven non-overlap of exact technical inputs. No cross-category profit/savings total or mock Action is created. Existing schema suffices for this contract, so `0028` is recorded unused; any stored projection needs a versioned amendment. Lane A owns shared route/registry/guard integration after serial branch handoff. Four one-run commits, exact wire/refusals, copy and mock panel mapping, fixture proof and 1440/390 measurement gates bind the implementer. This is planning authority, not implementation readiness, registry resolution, independent review or owner acceptance.

Review-closure-2 amendment (2026-10-20) to `D-2026-10-20-w4-01-w3-01-buildspec` and `D-2026-10-20-shared-provenance-dto`: the two specs' **Review closure 2 (2026-10-20)** sections supersede conflicting earlier examples. W3 Action snapshot has no title or success criterion: the estate Action title is `Action {action_code}` and criterion is null with `No success criterion recorded`. `detail` mirrors the resolver's exact nine keys `state,reasons,accepted_evidence_ids,problematic_accepted_evidence_ids,publication_ids,source_classes,fixtures,runs,evidence`; top-level `reasons` remains equal to `detail.reasons`, and typed reason extras/sorts are fixed in W3 closure 2. The Action selected-ID set includes its root/event, pinned origin Finding/assessment/Foundation and cited assessment IDs; its accepted citations are the exact Action basis plus pinned origin Finding evidence. A W4 case selected-ID set includes its selected revision/events/record and pinned Finding revision/Action event IDs; citations union case, linked Finding and linked Action basis/origin evidence. Neither uses a prior-head hash. W3-01 commit 1 owns the shared `evidence/public_provenance.py` patch with Lane A compatibility integration; if W4 merges first, W4-01 commit 2 carries the same reviewed patch and W3 consumes it without duplication. W3 closure 2 fixes coverage, consequence eligibility, unsupported card fields and fixture derivation; W4 closure 2 fixes link joins/fences, positive linked fixture, path-bound idempotency, SERVICE attestation, USER refusal and literal POST responses. These are planning contracts, not claims that W3/W4 code or W2-07 merge artifacts already exist.

Review-closure amendment (2026-10-20) to `D-2026-10-20-w4-01-w3-01-buildspec`: the two specs' **Review closure (2026-10-20)** sections supersede conflicting earlier illustrative wire and UI prose. W4's positive Site UI is KOBO-001; COLD-LAB-001 and EV-LAB-001 remain controls and W5-02 owns cold Work tabs. W3 keeps existing `/api/findings` and legacy Finding routes, adds estate API/routes, and retains the three unavailable *Site* Finding lens chips. Finding lifecycle is the stored SUPPORTED/UNCONFIRMED/NO_LONGER_SUPPORTED/MERGED vocabulary; Action application is the W1 reducer's NONE_AT_CUTOFF/PENDING/APPLIED with separate withdrawable resolution. The migration's added actor/authorization/occurrence columns and the closure's list/detail wire, cursor, fixture, refusal and proof rules bind W4 before implementation. No implementation, merge or owner acceptance is asserted.

Review-closure amendment (2026-10-20) to `D-2026-10-20-shared-provenance-dto`: public wire has required `{classification,state,source_ids,evidence_ids,basis_sha256,reasons}` and optional `detail`; `state` is a compatibility alias equal to `classification` for existing W1 consumers (`frontend/src/sites/sourceProvenance.tsx:101-104`). `detail` contains only existing resolver detail fields (`accepted_evidence_ids,publications,fixtures,runs,evidence`) when available; no invented values. `basis_sha256` is the SHA-256 of sorted-key compact JSON `{version:"source-provenance-basis/1",tenant_id,site_id,selected_revision_ids,accepted_evidence_ids}`, prefixed `sha256:`; it is **not** a stored Finding/economic basis or a prior selected head's hash. Sort ID arrays lexically; normalize UUIDs lowercase. With any selected revision, including an empty citation set, compute the digest; only no selection gives null. If cold/EV current accepted set is pending, emit separate `selected_source_provenance` for the prior selected row and `pending_source_provenance` for the current set; never pair a current classification with a prior basis hash. Consequence classification retains `SourceProvenanceResolver.consequence_revision`'s fail-closed Finding conflict rule. The resolver still classifies full exact cited sets per Site. Persisted EV `class` mismatch gives UNKNOWN with reason `{code:"SOURCE_CLASS_MISMATCH",accepted_evidence_ids:[...],persisted_class:"..."}`. Reasons retain typed extras when available and sort by `(code,accepted_evidence_ids,canonical extras)`; `source_ids` includes in-scope found accepted rows only, while `evidence_ids` includes missing/foreign cited IDs. Lane B owns `evidence/public_provenance.py` and domain adapters; Lane A owns the shared frontend compatibility patch, existing W1/W2 public-read integrations, `main.py`, shell and guard. Lane A integrates the compatibility patch **in W3 commit 1 before its review/merge**; if W4 merges first it carries the same reviewed patch and W3 tests it. No deferred breaking interval is authorized. This paragraph replaces the conflicting five-key/prior-head clauses above; persisted EV records remain unchanged.

Compatibility detail for the same decision: the W1 resolver's existing top-level fields `tenant_id,site_id,finding_revision_id,consequence_revision_id,cited_accepted_evidence_ids,power_accepted_evidence_ids,finding_revision_state,accepted_evidence_ids,problematic_accepted_evidence_ids,publication_ids,source_classes,fixtures,runs,evidence` remain present with their existing types on W1 Finding/consequence reads; `detail` is an additive mirror, not a move. This protects every current call to `sourceState()` and `SourceProvenance` without a same-commit migration of ~21 rendering consumers. Exact public producer files to edit/check are `analytics/finding_read.py`, `financials/consequence_read.py`, `financials/consequence_history.py`, `analytics/cold_site_reads.py`, `financials/cold_consequence.py`, `analytics/adapters/postgres_assessment_store.py` (EV envelope), `site_overview/read.py`, and `actions/service.py`; shared port files are `evidence/public_provenance.py` (new), `evidence/provenance_read.py`, and `frontend/src/sites/sourceProvenance.tsx` (type/tests only, Lane A). `sourceProvenance.tsx`'s current detail renderer reads those top-level arrays and is the compatibility proof. Existing cold/EV cursor basis fields remain their stored selection basis, separate from the new public provenance digest.

Decision: `D-2026-10-20-w4-01-w3-01-buildspec`. Codex Architect publishes the code-anchored [W4-01 work-case build spec](../.agent/W4-01-build-spec.md) and [W3-01 estate-root build spec](../.agent/W3-01-build-spec.md) against current W1/W2 seams and v6.9 screens. W4-01 owns `0027_w4_work_cases` after merged W2-07 `0026`, distinct authored work identities, immutable event order, scoped APIs and thin Site lists; its reviewed and merged identity, lifecycle, attestation, correction, links, ordering and API/refusal/read contract is frozen for W3/W5/W6. W3-01 is schema-free and independent of W4-01; it owns authorized cross-Site Finding/Action reads, exact revision/cutoff/coverage and five global roots. The specs bind literal migration or no-migration, wire examples/refusals, cursor, provenance, fixture, test, layout/copy and navigation multiset contracts, with commit-by-commit dry-read and Lane A shared-file integration. Build starts after reviewed W2-07 merges, independent spec review and applicable owner wave-start scope/core-panel gate. This is planning authority, not implementation, registry resolution or owner acceptance.

Decision: `D-2026-10-20-shared-provenance-dto`. One public `source_provenance` DTO across W1, cold and EV is `{classification,source_ids,evidence_ids,basis_sha256,reasons}`; classification is `AUTHORED_DEMONSTRATION`, `REGISTERED_SIMULATION`, `MIXED` or `UNKNOWN`. Map W1 resolver `state` and persisted EV result `class` to public `classification` at the read boundary; a mismatch with the exact-ID resolver yields UNKNOWN and a typed mismatch reason. The sole class basis is `evidence/source_provenance.py:SourceProvenanceResolver.resolve` over the sorted, deduplicated full cited accepted-evidence-ID union of exact selected revisions, never run mode, page rows, gateway credential or an earlier head. `source_ids` comes from the exact accepted rows' `source_id`; `evidence_ids` is the full sorted cited accepted-ID set. `basis_sha256` retains the selected revision's immutable basis hash already used by W2 cold/EV and their cursors; for a selected W1 revision without one, derive SHA-256 of sorted-key compact JSON `{version:"source-provenance-basis/1",tenant_id,site_id,selected_revision_ids,accepted_evidence_ids}`; without a selected revision it is null. Preserve classifier reasons and problematic IDs; empty/missing/broken/foreign is UNKNOWN, crossed/bound-unbound/incompatible fixture or multiple unproven runs is MIXED. W3-01 commit 1 implements and exact-ID-tests this mapping with Lane A integration of shared files **before W3-02 and W5**; W4-01 consumes it, and may integrate the reviewed common adapter first if its lane merges first. W1/cold/EV positive read tests assert the identical DTO on exact selected IDs; persisted EV results remain unchanged. This is a contract decision, not a claim current disparate reads are already fixed.
The merged W2 pending-read asymmetry remains binding: class/source/evidence IDs and reasons can describe the full current accepted set while `basis_sha256` names a prior selected head; `PENDING_RECOMPUTE` forbids a current claim. Estate rows keep exact selected-revision provenance separate from the per-Site pending source envelope.

Decision: `D-2026-10-20-post-w2-sequence`. Codex Architect adopts [the binding post-W2 sequence](../.agent/post-W2-sequence.md), amending the owner-approved two-lane proposal of 2026-10-18 and the 2026-10-19 decision that the W2 owner walkthrough does not block post-W2 work. It activates when independently reviewed W2-07 merges after migration `0026`: Lane A builds W4 work-case core alone, then mini-grid depth and W5 cold/EV; Lane B builds W3 estate reads, then W6 global work, Assets and Settings. OPS-01's already-merged backend test harness receives a bounded Step-1 speed/coverage follow-up, not a duplicate product task. The linked sequence fixes exact slice/screen/node order, reserves `0027`–`0039` with one migration owner and one Alembic head, assigns all shared-file ownership, freezes the reviewed W4 case contract behind Architect amendments, names the W1/W2 seams and required provenance DTO/consumer fixes, and places structural W2 walkthrough correction before W5 consumes W2 screens. No client-feedback gate precedes the work-case core; the owner-approved post-all-waves refinement remains. Every slice still requires a code-anchored full build spec, concrete-artifact pre-build closure, independent review, normal suite/guard proof and the applicable owner wave gates. This decision is planning authority, not implementation, registry-node resolution, panel promotion or W2 owner acceptance.

## 2026-10-18

Run-9 amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): `.agent/W2-04-build-spec.md` closes W2-04 review D1, D2, R1 and R2. Data sources uses revised five-column widths, wrapping headers and ordinary cells, and short one-line contact/quality chips whose full states remain in Source details; no text may clip or overlap and the 1440 paired row remains <=569 px. Unbound or unreported transfer/door roles say `No accepted report for this role` in the closed What cell. Accepted records keeps three rows and moves the exact Q-R9 unavailable-link sentence into Record details, leaving a short, noninteractive two-line Record cell and <=345 px panel target. Recheck the stocked selection at 1440/390. This is planning authority only; no code, review verdict or owner acceptance is implied.

Run-8 amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): `.agent/W2-04-build-spec.md` rules the W2-04 guard conflict, accepted-record total, date-bar copy, rule lineage and remaining closed-panel heights. Null selected destinations use the exact noninteractive `No linked page for this item` copy, and the Cooling card drops the redundant `Not available yet`; these runtime states do not create mock-gap catalogue entries or scan exemptions. `accepted_records.total_count` counts the full selected, source-gated basis before pagination. The cold Assumptions pending/historical sentence stays on the date bar's second line. Claim details point to exact accepted IDs in Record details because no rule-to-evidence ID contract exists. Route-scoped table widths, short closed cells and retained disclosures target <=1.30× mock height for the three remaining W2-04 panels; W2-03 owns its separate temperature-panel height defect. This is planning authority, not implementation, review or owner acceptance.

Run-7 layout/copy amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): the four measured cold Site outlier panels must compact to at most 1.30× their v6.9 mock height at 1440 with exactly one closed disclosure per panel. The six Data sources rows, three initially visible accepted Analysis records, two-sentence claim-limit panel and two compact money bridge rows retain their mock form; per-channel contact/fact lineage, record metadata, claim-rule details and exact consequence basis move into their panel's disclosure. The cold Evidence strip is derived from the four displayed row chips, so the excursion replay reads `Evidence limited` with three Full and one Limited row. The inverter/battery mock row remains visibly undeclared; actual grid-meter/AC-bus channels appear only as separately named power-path detail there, and ambient/manual channels appear only as separately named context detail under Chamber probe. The shared date-bar position carries selected UTC window/cutoff; exact attention/card/paging labels and UTC-versus-EAT time copy are fixed in `.agent/W2-04-build-spec.md` “Run-7 Architect ruling”. This is planning authority, not a code change, review verdict or owner acceptance.

Run-7 wording amendment to `D-2026-10-18-w2-05-buildspec` (2026-10-18): in the `ev-sld` connector disclosure use `Configured source roles:`; do not add `Configured mapping` to the four exact vocabulary exceptions. The closed charger row uses the five exact lower-case schedule states `disabled`, `no service hours`, `service hours set`, `mixed schedules`, `no schedule declared`, based solely on selected configured schedules. The What it reports cell uses `{n} configured source role(s)` for positive selected role counts, `No configured source roles` for zero on a declared charger, and `Not declared` for an undeclared charger. The predicates and non-reporting limitation are in `.agent/W2-05a-build-spec.md` “Run-7 Architect wording closure”. This is planning authority, not a code change, review verdict or owner acceptance.

Commit-3 source-contact amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): `.agent/W2-04-build-spec.md` now fixes cold Evidence source contact against the selected window end. An explicit source contact timestamp is recent through two declared gateway cadences (inclusive), otherwise stale; an explicit null source entry is NEVER, while absent source-specific history or unverifiable timing is UNKNOWN. Gateway receipt alone does not establish source contact. W2-01 cold and W2-05a EV Foundation gateway-contact null cases remain NEVER and their gateway freshness remains request-time; W2-03 assessment and W2-04 source recency use window end. The spec gives the four plain screen labels and keeps accepted fact age separate. This is planning authority only; no implementation, review verdict or owner acceptance is implied.

Commit-2 amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): An open W2-03 excursion can have two finite **observed-segment** degree-minute bounds while its duration upper bound and end remain unknown. W2-04 therefore stores the proved consequence lower bound and a null consequence upper bound, and always carries `OPEN_EPISODE_UPPER_UNKNOWN` for an eligible open excursion; it must not present the W2-03 observed-segment high as total episode exposure. `.agent/W2-04-build-spec.md` “Commit-2 Architect rulings” confirms the implementer-proposed reason, limitation and worker error codes with exact predicates, finite allowed expansions for claim/source class, and plain screen copy. The canonical open replay needs a consequence regression assertion. This is planning authority only; it changes no implementation or review status.

Decision: `D-2026-10-18-w2-06-07-buildspec`. Codex Architect/Planner publishes implementation-ready W2-06 and W2-07 packets and code-anchored specs in `tasks/W2-06-ev-assessment.md`, `tasks/W2-07-ev-site-evidence-money.md`, `.agent/W2-06-build-spec.md` and `.agent/W2-07-build-spec.md`. W2-06 follows reviewed/merged W2-05b and owns `0025_w2_ev_session`, immutable accepted-evidence session assessment, exact meter coverage, bounded fault-abort Finding, late recompute and `sessions`/`ev-finding`. W2-07 follows reviewed/merged W2-06 and owns `0026_w2_ev_money`, shared Site/evidence reads, authored time-valid gross tariff scenario with exact price/source gates and five EV Site/evidence/financial routes. The specs close the implementer dry-read against current main/W2-03 and the W2-04/05 predecessor specs: fixture identities and revision publication, identifier/UTC/Decimal formats, writer and driver guards, transactional seams, refusal/currentness, six replay assertions, mock panel/row/column/chip sources or honest gaps, and per-route visual proof. Mock content authority remains binding; no illustrated tariff, loss, billing, work, health or availability claim is seeded. Only `A-ev-session-rules`, `I-ev-assessment-store` and `A-ev-site-projections` existing registry task pointers change; status/evidence and panel promotion do not. This is planning authority, not code, independent review or owner acceptance.

Run-8 amendment to `D-2026-10-18-w2-06-07-buildspec` (2026-10-19): `.agent/W2-06-build-spec.md` “Run 8 rulings (r7)” closes P1–P8 against W2-06 commit `0dcedf16`. It confirms the selected-source copy and mock slots for P1–P4 and P6, replaces the unsupported Finding BigClaim with fixed lifecycle-aware text, and keeps pending rows while withholding their Finding link until the selection is settled. The v6.9 EV tabs remain visible as noninteractive `Not available yet` entries. The same ruling extends the exact navigation-guard inventory and fixture proof; it is design authority only, with no implementation, review verdict or owner acceptance implied.

Final Q1-Q10 and implementer dry-read amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): `.agent/W2-04-build-spec.md` now rules every W2-04 commit-1 migration question and maps each owned v6.9 status, card, panel row, column, chip and link to a selected public source or visible gap. The provisional migration needs three changes before continuation: resolve the chamber room for start-response work instead of storing the generator as room; preserve fractional UTC precision in dirty keys; constrain stored aggregate source class to the four S4-05 read states. It also needs the stated nonvacuous migration rule-8 check. A no-Finding episode creates a successful empty work attempt, never an invented consequence. `PRODUCT_EXPOSURE` remains unpriced, and no mock Action, Incident, repair, currency, stock or cold Analysis target is claimed without exact proof. The two `D-2026-10-18-w2-retro-rulings` corrections are part of the frontend review gate. This amendment is planning authority, not implementation, independent review or owner acceptance.

Decision: `D-2026-10-18-w2-retro-rulings`. Codex Architect rules every recorded W2-02/W2-03 packet deviation, interpretation and fix-round choice in `.agent/W2-retro-rulings.md` and amends both build specs. Two W2-03 user-facing choices are `CORRECT` before merge: restore the v6.9 “Loading / batch” row and repair capture settling; offer cold Evidence Analysis links only after exact-target integration proof, otherwise show labelled references and an honest unavailable gap. All other listed items are accepted within the table's stated scope, including prior q6/q1-q3 rulings. This is design authority and an implementation/review gate, not a code change, review verdict or owner acceptance.

Decision: `D-2026-10-18-w2-05-buildspec` (amended 2026-10-18, Architect W2-05 Q1 pass). Codex Architect/Planner publishes implementation-ready W2-05a/05b packets and code-anchored specs in `tasks/W2-05a-ev-foundation.md`, `tasks/W2-05b-ev-producer.md`, `.agent/W2-05a-build-spec.md` and `.agent/W2-05b-build-spec.md`. The amendment definitively answers `.agent/W2-05a-phase-handoff.md` Q1-Q8 and records a commit-by-commit implementer dry-read in both specs: distinct c1/c2 device channels and component owners without weakening S2 refusals, the blocking/nonblocking readiness split, publication refusals for missing declared-component properties, property-derived cadence ceilings, a typed UTC fixture schedule and effective-revision rule, one EV-LAB-001 fixture created in 05a with gap revisions, 0024 reserved after W2-04's 0023, and a separate EV v4 mapping profile. It maps each 05a mock panel's rows, chips and unknown slots to selected data or explicit gaps, and fixes 05b's Lab choice/replay/artifact questions. These specs bind the amended EV technical design to current main's W2-00..03 seams, preserve the v69 EV mock's layout and content authority, and require ordinary registered Lab-to-S2 replay. W2-05a assigns only `A-ev-role-set.task`; W2-05b assigns only `A-ev-world.task` and `I-ev-world.task`; no registry status/evidence promotion. OCPP physical peer remains pilot work under the amended EV decision. This is planning authority, not implementation, independent review or owner acceptance.

Further amendment to `D-2026-10-18-w2-05-buildspec` (2026-10-18, Architect W2-05a QA-QD): the EV-LAB-001 Site and connector schedules use `Etc/UTC` with offset zero because the shared Site parser accepts Area/Location names; it is not widened for bare `UTC`. The five physical EV properties are charger/connector ratings, meter resolution/error bound and clock error bound; Site import limit, status/meter cadences and connector enablement are controls. An absent feed permits publication of otherwise valid declared equipment as configuration-incomplete, but scheduled service still requires a complete feed→meter→charger→connector path. Multiple parents always refuse; with a declared feed, unfed meters or chargers refuse. An EV Foundation has at most one `AC_BUS` feed; a second feed refuses `EV_CONFIGURATION_INVALID` so the selected single-feed read cannot silently choose one. The exact implementation contract is `.agent/W2-05a-build-spec.md` “QA-QD amendment.” This is planning authority only; no code, review verdict or owner acceptance is implied.

Further amendment to `D-2026-10-18-w2-05-buildspec` (2026-10-18, Architect W2-05a QE-QG): Site import binding cadence is the minimum selected `ev-meter-cadence` across declared connectors, in seconds; a binding set requires at least one connector. The two unsuffixed W2-00 EV tuples retain role labels and global v4 compatibility but are excluded from the exact EV profile, so `ev-roles-1` publication refuses them as `BINDING_CHANNEL_V4_UNKNOWN`. EV binding publication also requires each registered source's `asset_id` to equal its requested bound asset UUID, refusing a mismatch as `BINDING_SOURCE_ASSET_MISMATCH`; S2's envelope-time `EV_CONNECTOR_MISMATCH` remains separate. The exact implementation contract is `.agent/W2-05a-build-spec.md` “QE-QG amendment.” This is planning authority only; no code, review verdict or owner acceptance is implied.

Further amendment to `D-2026-10-18-w2-05-buildspec` (2026-10-18, Architect W2-05a QH-QL): the selected connector schedule is always `{enabled,time_zone,weekly}`, with enablement from that connector's selected control property; the selected read includes each connector's declared `clock_error_bound_seconds`, shown as configuration in the existing `ev-readiness` Clock and delivery metric without claiming observed sync. The `feed` object is always present; its meter is the sole directly supplied meter or null. `SOURCE_NOT_CONTACTED` applies only to NEVER, not STALE. `at` selects configuration, while gateway contact freshness is checked at server request time and exposed as `contact.checked_at`, distinct from W2-03's assessment window-end freshness. The amended spec maps these values and gaps to the exact v6.9 `ev-foundation`, `ev-readiness` and `ev-sld` rows and diagram slots; no mock equipment or contact history is inferred. This is planning authority only; no code, review verdict or owner acceptance is implied.

Further amendment to `D-2026-10-18-w2-05-buildspec` (2026-10-18, Architect W2-05a QM-QP): retain the v6.9 Session identity mapping and load-manager labels with narrowly scoped exact-label vocabulary exceptions; use the plain gap `No tariff set for estimates` instead of a scenario exception. The EV diagram keeps its source-side meter before the bus, three feeder slots, breaker/kWh positions and monitoring rail; the declared direct import meter belongs in that upstream slot, while undeclared load manager, breakers, feeder meters and auxiliary stay visibly unknown. Neither the Foundation topology nor EV-LAB-001 fixture changes to suit the drawing. Readiness panel 1 keeps four mock rows, with meter, session-event and Site-import gaps in the existing rows; panel 4 row 2 uses the noninteractive `Investigation action · Not available yet` entry without inventing an Action. The `What each part does` table keeps four mock rows, placing connector detail inside the two charger rows. Exact wording and slots are in `.agent/W2-05a-build-spec.md` “QM-QP amendment.” This is planning authority only; no code, review verdict or owner acceptance is implied.
Final Run-5 amendment to `D-2026-10-18-w2-05-buildspec` (2026-10-18): the vocabulary scanner has no per-route scope, so its four v6.9 exceptions are global **exact phrases** only: `Session identity mapping`, `Grid supply + load manager`, `Site meter & load manager`, `Load manager · Not declared`. Other uses of mapping/load/scenario remain flagged. The 1.47× mock height of the ev-sld parts table is a fidelity defect. Retain four rows and full connector facts, but use two concise visible lines per charger and a closed, accessible in-cell `Connector details` disclosure; at 1440 its closed height must be ≤1.30× the mock and at 390 remain readable. Exact compaction and extra-charger behavior are in `.agent/W2-05a-build-spec.md` “Final Run-5 vocabulary and ev-sld density ruling.” This is planning authority, not code or acceptance.

Amendment to `D-2026-10-18-w2-03-answers` (2026-10-18, review deviations 1, 16 and 18): the confirmed commit-3 work-window bridge stands, including the six-case `[19:00,20:05)` window. On the cold Performance row show unbuilt **Cooling**, and on both cold Finding detail rows show unbuilt **Recommendation**, in mock order as visible and accessible, noninteractive `Not available yet` entries. Extend the declared in-page unavailable-entry inventory and navigation guard narrowly for these entries, following `D-2026-10-17-f5-subtabs-and-contact`; neither becomes a destination until reviewed work supports it. Approved W2-03 plain-language substitutions are `temperature:3` **How each limit is set** for mock **Claim boundary**, and the cold backup-chain columns **Power to compressor** and **Compressor response** for mock **Power to load** and **Load response**. For `REGISTERED_SIMULATION`, show **Generated test data** with adjacent text **From a registered test run; not readings from physical equipment.** Keep the exact source class and IDs in labelled deeper detail. This is a narrow title/column exception to the binding W2 mock, not a change to panel count, order, layout, evidence rules, registry tier, review status or owner acceptance. Exact implementation and proof contract: `.agent/W2-03-build-spec.md` “Review-deviation rulings.”

Decision: `D-2026-10-18-w2-mockup-authority`. Owner rules that the v6.9 mockup's W2 screens (cold-chain and EV) are built and are the binding visual and content authority like W1's; the mockup's "EV extrapolation" tags mean only that the v6.9 product spec had no EV section. This supersedes the "EV extrapolations remain references pending owner visual-authority confirmation" wording in `D-2026-10-17-w2-techdesign-ev` and closes owner item 4 of `.agent/architect-W2-design.md`. Data-unbacked mock values keep their slot with an honest gap. Record: `.agent/owner-W2-mockup-authority-2026-10-18.md`.

Decision: `D-2026-10-18-w2-03-answers`. Codex Architect closes W2-03 Q1-Q11 and the commit 3-5 contract in `.agent/W2-03-build-spec.md`. Migration `0022` restricts the existing mini-grid `financial_consequence_dirty_on_finding_revision` trigger to `NEW.domain='mini_grid'`; W2-04 `0023` separately owns cold money triggers. The built scoped cold schema and split/key rules stand. Open excursion lower duration ends at the last continuously observed out-of-band reading, so 19:15–20:00 is 45 minutes; a LOW excursion peak is the minimum observed value. The decision fixes claim and Finding gates, effective probe calibration, transfer before restoration, contradiction links, one-transaction worker projection, selected read shapes and all four exact v69 panel maps with replay-derived expectations. It is Architect planning authority, not implementation, independent review or owner acceptance.

Amendment to `D-2026-10-18-w2-03-answers` (2026-10-18): confirm the commit-3 work-window bridge and six handoff interpretations in `.agent/W2-03-build-spec.md` “Commit-3 confirmations and commit-4 freshness amendment.” A supported episode whose Finding is no longer warranted gets a `SUPPORT_CHANGED` or `BASIS_REFRESHED` revision with lifecycle `UNCONFIRMED`; an invalidated episode uses `NO_LONGER_SUPPORTED`. For commit-4 selected reads, compare the latest qualifying probe with the selected window's `to` boundary, not the wall clock, and display the actual historical window and provenance. A replay can be `CURRENT` for its selected window without claiming live contact; explicit older cutoffs remain `HISTORICAL`, pending work remains pending, and a genuinely old last probe is `STALE_SOURCE`. The detailed state precedence and proof cases are in the spec. This is design authority, not code, review or owner acceptance.

Decision: `D-2026-10-18-w2-04-buildspec`. Codex Architect fixes the W2-04 implementation packet and code-anchored spec in `tasks/W2-04-cold-site-evidence-money.md` and `.agent/W2-04-build-spec.md`. After W2-03 `0022`, cold consequence gets a separate append-only `0023` schema, trigger-only dirty work, exact Finding/episode/evidence basis and idempotent worker attempts; existing mini-grid fuel-cost and diesel assumption publication remain unchanged. Six ordinary W2-02 accepted replays drive five selected cold reads and five exact v69 panel routes. Product exposure is bounded thermal `degC_min` and unpriced; cold stock quantity/value/currency and exposure rule remain undeclared, and no repair amount is inferred. The spec fixes overlap grouping, source/currentness withholding, read shapes, guard ownership, fixtures and review gates. It assigns two existing open registry task pointers only. This is planning authority, not implementation, owner scope approval, review acceptance or panel promotion.
Readiness-gate amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): the checked spec now names the actual COLD-LAB-001 Foundation/v4 publication, W2-03 window-end probe freshness and selected-read refusal/cursor formats, exact path:symbol seams, SQL driver/writer guard ownership, and empty/pending/refused copy for all five v69 routes. `0010_financial_assumptions` enforces diesel-only keys in SQL, so `0023` has **no cold assumption-publication dirty-work arm**; the packet and earlier design's shorthand about a relevant cold assumption publication is deferred to a future coordinated schema/publisher migration. The existing `postgres_consequence_store.py` remains the sole cold consequence row writer, with work inserted only by migration triggers; Site read services stay outside the SQL driver allowlist. `batch_publication_link.batch_id` is the source-link locator. These are implementation-contract corrections, not code, owner approval or review acceptance.
Final Run-5 amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): `.agent/W2-04-build-spec.md` “Final Run-5 Architect rulings” closes Q-R1–Q-R9 and the eight implementation readings with exact response shapes, codes, source-contact limitations and mock-slot copy for all five cold routes. Pending cold work withholds money; a selected consequence may be created after its evidence cutoff; the source contact time is explicit and distinct from last accepted fact time. The cold Foundation link uses `at=to`; exact Analysis record links remain unavailable until the real Evidence target is proved by integration test. The five-screen copy ledger and retro corrections 14/17 are binding for commit 4. This is planning authority, not code, review or owner acceptance.
Q5 amendment to `D-2026-10-18-w2-04-buildspec` (2026-10-18): confirm the two Q-R1 mappings in `.agent/W2-04-build-spec.md`. Each attention item links to its own selected Finding when present; otherwise start failure and unknown transfer link to the selected backup-chain read, while pending recompute, probe gap and missing policy link to the selected Evidence read. An unavailable exact destination yields a null link. `COLD_POLICY_MISSING.limitation` uses the unresolved-policy sentence when the selected policy revision is unresolved, otherwise the selected excursion assessment limitation. This is planning authority, not code, review or owner acceptance.

## 2026-10-17

Decision: `D-2026-10-17-w2-02-buildspec`. Codex Architect resolves all nine W2-02 producer questions in `.agent/W2-02-architect-questions.md` and supplies code-anchored W2-02/W2-03 build specs. Six cases use a newly registered COLD-LAB-001 Site carrying the exact thermal/policy values, a new immutable v4 binding revision, a strict cold scenario parser and DeviceReport v2 through gateway-owned v4 sequence/envelope construction. Cold-only run identity keys are omitted for historical runs. Replay selects an explicit scoped run and persisted public lineage; W2-03 uses accepted evidence and one transactional assessment/episode/Finding projection with exact `0022` schema. **Amendment, W2-02 spec commit (2):** confirm that conversion rows remain v3-compatible and only the explicit 00:01 publication carries v4 metadata, preserving W2-01 hashes and making the new revision distinct; add a gated `GET /api/simulator-lab/cold-scenarios?site_id=COLD-LAB-001` choice read for the registered fixture while the existing unfiltered catalog and detail stay legacy-only; keep explicit model/publication profile selections in cold run requests and require exact agreement with the document before Draft, with observation identity chosen and frozen from the document. **Amendment, W2-02 spec commits (2)/(3):** `observation_sha256` hashes canonical JSON of the profile identity and parsed observation rows; frozen run identity holds IDs/digests, and execution re-reads and verifies exact Foundation and scenario inputs. The latent generator fault fails at timeout; restore transfers to GRID immediately; powered running compressor power equals cooling capacity; grid/transfer events share outage correlation; and ambient temperature publishes every five minutes. Exact hash shape, checks and transition semantics are in `.agent/W2-02-build-spec.md`. **Amendment, W2-02 cold Lab setup UI:** use a separate gated cold setup route because the legacy run setup requires a scenario detail that cold IDs do not expose. Select Site, then a Site-scoped cold choice; show the document timing, seed, one-minute step and profiles read-only before an explicit Create draft run action. Send the exact choice values and explicit model/publication selections; distinguish empty choices from unavailable stores. Freeze the effective registered binding revision?s `signal_mappings` into cold run identity as for registered runs. Exact route, request and copy are in `.agent/W2-02-build-spec.md`. **Amendment, W2-02 q5:** cold event/correlation IDs use `cold-` plus SHA-256 of the canonical arrays, preserving the existing V4 identifier grammar; report keys keep `cold:`. Cold Start verifies the frozen Foundation revision and scenario through an injected read port, runs all 61 minute boundaries, stages ordinary reports at source time +3 seconds, retains the 19:20 held report until 20:10, and writes a distinct completed cold execution artifact before Commit. Step/run-to-end thereafter refuse terminal control. The explicit run replay reads persisted publication, Batch V2 and dispositions; six canonical manifests use deterministic test fixture IDs and timestamps, while rule 8 keeps the ledger as sole evidence writer. `.agent/W2-02-build-spec.md` owns the exact commit (4) route, response, digest, manifest and six-test contract. **Amendment, W2-02 q6 (2026-10-18):** `binding_service.acquisition_snapshot` dispatches COLDCHAIN to the selected W2-01 cold configuration readiness and shared Site/registration gaps; blocking room, probe, policy, start-event and required-role gaps refuse, while optional transfer and other optional channels do not. Historical snapshots retain the current-row gap exception and pinned-byte/identity verification. Remove the test-only cold gap bypass and prove a real registered Draft. The test-only direct S2 session-conflict vector is accepted because the cold gateway has no bound session channel; it establishes ledger conflict accounting only. The V4 header dispatch in `evidence/publication.py:simulation_records` is accepted to attest sealed V4 batches. Exact seam, gap list and proof scope are in `.agent/W2-02-build-spec.md`. This amends the cold technical design and packets; it is design authority, not implementation, review or owner approval.

Decision: `D-2026-10-17-f5-subtabs-and-contact`. Codex Architect extends the owner's full-v69-menu choice to the named W1 in-page rows as a narrow exception to the absent-Site-tab rule: show live registered destinations and visibly/accessibly `Not available yet` noninteractive entries for unbuilt Foundation, Work, Finding and Financials destinations. Site Findings uses the mock lens chips; only lenses backed by a selected Site/window classification and filter become interactive, while the date/window scope control remains. Exact F5 inventory, presentation and guard proof are in `.agent/architect-W1-fidelity.md` (F5 section). W2-01 cold contact maps missing health store or unmatched gateway/diagnostic to `NEVER`, `as_of:null`, with distinct no-gateway/no-contact wording and an honest limitation; a true read failure remains explicitly unavailable. Exact contact contract is in `.agent/W2-technical-design-cold.md` (W2-01 contact null closure). This amends `D-2026-10-17-w1-rail` and refines `D-2026-10-17-w2-01-answers`; it changes no product data, backend code, registry tier or owner acceptance.

Run-8 P8 amendment to `D-2026-10-17-f5-subtabs-and-contact` (2026-10-19): add the v6.9 EV `sessions` unavailable tabs `Availability` and `Energy / site power` once each, and the EV Finding `Recommendation` once in addition to the cold Finding `Recommendation`. The exact resulting multiset and required positive/negative guard fixtures are in `.agent/W2-06-build-spec.md` “Run 8 rulings (r7)”. These entries remain text without destinations; arbitrary new entries still fail the closed inventory. No rail change, product capability, code implementation or owner acceptance is implied.

Decision: `D-2026-10-17-w2-01-answers`. Codex Architect closes W2-01 build questions A–I and the W2-02 role/copy carries in `.agent/W2-technical-design-cold.md` §3. Cold topology is typed directed Foundation connections; the single generator start-event channel binds one `backup_start_event` role for both request/result, and grid power events have their own role. EVENT bindings use the declared `event` signal unit, except quantitative manual temperature; payload units remain null except manual degC. Thirteen carrier-typed properties, per-unit bounds and cold-specific checks, selected-read commissioning/contact/cadence rules, Site-type route switching and dynamic cold title rules are exact there. The decision also names the actual Lab profile/mapping/Stage and S3/S4 worker/store/guard changes W2-02/W2-03 require. It supersedes conflicting shorthand in the earlier cold design and W2-01 packet. This is design authority, not code, review verdict or owner approval.

Decision: `D-2026-10-17-w2-00-answers`. Codex Architect resolves the eight W2-00 phase-1 questions in `.agent/W2-technical-design-cold.md` §1 and `tasks/W2-00-source-events.md`. Event equality hashes canonical source, source-time/interval timing and full payload, excluding transport/mapping/publication fields; same-message comparison keeps full-envelope SHA and wins collision precedence. Migration `0020` keys delta constraints on `measurement='INTERVAL_DELTA'`, leaving `conversion_kind` as the binding conversion. Batch V2 keeps ordinary v3 strict while a valid v4 or v3-v4-only header reaches per-ordinal parser refusal; an unusable header or cross-tenant binding selection remains a whole-batch refusal. Parser and S2 own the exact EV/correlation codes; five optional snapshot-binding keys and a closed v4 channel table define mapping compatibility. W2-00 may prove v4 with test-only injected registered binding bases; W2-01 publishes cold bindings, W2-02 registers/emits the cold runtime profile, and W2-05b registers/emits EV, an explicit W2-00 producer/profile deviation deferred to W2-02. V4 acceptance queues no dispatch work until its domain worker is introduced. The new family/kind read applies to Postgres; the legacy file route rejects those filters. This is design authority, not code, review verdict, registry promotion or owner approval.

Decision: `D-2026-10-17-mockup-layout-spec`. Codex Architect, following the owner's rejected W1 walkthrough, makes the rendered v6.9 mockup a binding layout specification for W1 rework and all W2+ UI: each named screen retains the mock panel set, order, approved titles, relative prominence, grid and visual style. An unsupported panel remains in place with an honest gap inside; app-only facts move into their owning mock panel or a named contextual destination, and no new answer card leads the page. The selected authorized read and `D-2026-10-16-w1-ux` disclosure/Analysis boundaries still govern claims. Every screen requires a route-render panel-structure test against `v69-rendered-panels.json` (or an explicit approved title map), app/mock side-by-side captures at 1440 and 390 px, and an independent review that rates any structural mismatch High. No W1 owner session occurs until all 26 Site screens pass. The screen map, title exceptions, rework slices and read gaps are in `.agent/architect-W1-fidelity.md`. This decision supersedes W1-UX's leading answer-card layout choice, changes no registry tier or backend contract, and records no owner acceptance.

Decision: `D-2026-10-17-w2-techdesign-ev` (amended 2026-10-17). Codex Architect fixes W2-05a/05b/06/07 in `.agent/W2-technical-design-ev.md` on the amended W2-00/0020-0023 cold contract: effective charger/connector roles; deterministic session pack and explicit six-case forcing; registered Lab-to-S2 path; scoped event/meter correlation; immutable session/assessment/Finding revisions and late recompute with append-only money work attempts; exact writer/trigger ownership; typed reads and supported-energy-only gross tariff scenario. The OCPP 1.6J vendor peer is deferred to the pilot gate for demonstration speed, with its format and adapter fixed in the design; the cold vendor peer is also deferred to the pilot gate. Physical-source capture and attestation remain pilot gates. Its ten W2 manifest screens use the exact v69 panel maps, shared W1-F1 layout guard/CSS, in-panel gaps and per-route structure/1440/390 review gate in the amended design; structural drift is High. This is technical authority for Planner packets, not owner approval of EV screen scope, visual authority, fixture numbers or registry promotion.

Decision: `D-2026-10-17-w2-techdesign-cold` (amended 2026-10-17). Codex Architect fixes W2-00 source-envelope v4 and W2-01..04 in `.agent/W2-technical-design-cold.md`: v4-only event and interval-delta kinds with explicit-null identity keys, byte-stable v3 and `MESSAGE_CONFLICT`, typed S2 conflict handling with message-first savepoint/reread precedence; additive migrations after 0019 and `'mini_grid'`-safe Finding generalization; effective Foundation roles and policy; standalone deterministic thermal/backup pack with explicit six-case forcing and 13-point half-open evidence window; bounded assessment and immutable revisions; exact writer/trigger ownership; typed selected reads and unpriced exposure with existing source/current-money gates and append-only work attempts. The cold vendor peer is deferred to the pilot gate for demo speed. W2-00 precedes cold and EV producers. Its twelve W2 manifest screens use the exact v69 panel maps, shared W1-F1 layout guard/CSS, in-panel gaps and per-route structure/1440/390 review gate in the amended design; structural drift is High. This is technical authority for Planner packets, not owner approval of proposed W2 screen scope, fixture values or registry promotion.

Decision: `D-2026-10-17-w2-design`. Codex Architect adopts the proposed Wave 2 domain and delivery boundaries in `.agent/architect-W2-design.md` for Planner refinement. Cold-chain excursion and backup-response claims, and EV session/energy claims, must derive from time-valid Foundation bindings and accepted public evidence through the ordinary registered Lab/gateway/S2 path; each domain gets versioned causal simulator packs, deterministic replay cases and a labelled physical-adapter contract peer. Private simulator truth cannot enter product evidence. Findings and money remain exact-revision, source-gated and fail-closed: chamber temperature does not establish spoilage; incomplete sessions are unknown; a tariff scenario is neither collections nor lost revenue. W1 plain-language, visual, deeper-analysis and honest-gap rules apply in every W2 slice. The proposed 22-screen Real-with-honest-gaps scope, core panels and demonstration values await owner confirmation; this decision does not promote registry panels, activate tasks or record owner acceptance. W3 estate and W5 work/health/scenarios remain separate.

Decision: `D-2026-10-17-w1-rail`. Codex Architect applies the owner's full-v69-menu choice as a narrow amendment to the 2026-09-13 navigation rule and `D-2026-10-02-grammar-ownership-test`. The operator rail shows all eleven roots in six v69 groups, headed `OPERATIONS`, `INTELLIGENCE`, `WORK`, `ASSURANCE`, `BUSINESS`, `ADMIN`; only Sites (`/sites`) and Findings (`/findings`) are live W1 links. Other roots are visibly and accessibly `Not available yet` text with no destination or keyboard action; site-scoped pages do not make a cross-site root live. The Simulator Lab workspace-footer link appears only with its registered gated route, and unsupported demo-workspace/count copy is omitted. The navigation guard and route/component tests must prove the full inventory, absent destinations, real live routes, gate behavior, and 390 px access while retaining the separate Site tab/subtab bans. Exact contract: `.agent/architect-W1-UX-07-answers.md`. This decision does not promote panels or record owner acceptance.

Decision: `D-2026-10-17-w1-ux-06`. Codex Architect accepts W1-UX-06 questions 1-2: the S1 `READY_TO_REPORT` badge reads `Set up to report` with its configured tone and configuration-only meaning, and the Readiness strip reads `Set-up steps` because it has no contact read. Accept question 3 for current server contact with trusted, known old reported facts: the selected gateway state line says `In contact; its latest report is old`; unknown or untrusted fact age remains explicitly unconfirmed, and neither state claims equipment health. Amend question 4: unrecognised Readiness and Health codes get non-positive headlines, and zero enabled gateways never produce `All 0 enabled gateways`; preserve the recognised no-source reason and keep readiness-dependent steps from appearing complete on an unrecognised readiness code alone. Exact words, conditions and test expectations are in `.agent/architect-W1-UX-06-answers.md`. This refines `D-2026-10-16-w1-ux`, `D-2026-10-16-a-s7-health` and `D-2026-10-16-s701-clock`; it neither promotes a panel nor records owner acceptance.

## 2026-10-16

Decision: `D-2026-10-16-s408`. Codex Architect accepts S4-08 Q1-Q3 with the display rule in `.agent/architect-S4-08-answers.md`. The Site consequence history includes unpriced versions with typed missing-price/null amount. `CURRENT_AT_CUTOFF` identifies only the latest consequence within the latest FindingRevision recorded by that cutoff; if that FindingRevision has no consequence, no row for that Finding is current at cutoff. A selected past cutoff is audit history: an eligible recorded amount is labelled historical and assumption-conditioned, never a current-money claim. Exact-version source and existing money gates still govern display, and a closed source hides amounts. Only today's separate exact-head read may claim current money after all gates pass. This implements the Site-history requirement of `D-2026-10-14-s402-post-review-follow-ons` without promoting `assumptions:3#a` or recording owner acceptance.

Decision: `D-2026-10-16-w1-ux-disclosure`. Codex Architect accepts the W1-UX-01 narrow disclosure scan as an amendment to `D-2026-10-04-plain-language-analysis-views`, with the exact banned disclosure-prose terms, permitted individually labelled references, and case-sensitive raw-code detection defined in `.agent/architect-W1-ux-disclosure-answers.md`. The closed disclosure is scanned, never exempted as a container; the existing single-value exemption rule stays. Raw IDs, versions, digests and reasons may appear only as labelled exact values, never in the collapsed summary. Raw-code matching does not flag ordinary units or acronyms including SOC, UTC, kW, kWh and PV. Plain state, material limits, scope and as-of time stay visible outside the disclosure. This does not record owner acceptance or change the W1 walkthrough gate.

Decision: `D-2026-10-16-w1-ux`. Codex Architect. For W1 product surfaces, substantive deeper analysis has a separate contextual destination, following the owner-directed T028 Analysis tabs. Compact cards and indexes link to their owning detail; a closed inline "How this was worked out" disclosure holds only small exact-reference detail and is not the sole route to method or evidence. Keep the same destination at 1440 and 390 px. Approve Site, Evidence, Finding, Action, Verification and Analysis as explained domain/navigation labels; ban raw states, codes, IDs, implementation analytics and simulator vocabulary from the default reading, with narrowly labelled exact-reference exceptions in detail. Honest selected-read states and material limits take precedence over copy or mockup fidelity. Full screen-placement and vocabulary ruling: `.agent/architect-W1-ux-answers.md`. This amends the W1-UX-01 disclosure-only proposal and preserves `D-2026-10-04-plain-language-analysis-views`; owner acceptance remains the combined W1 walkthrough.

## 2026-10-07

Decision: `D-2026-10-07-s1-foundation-import-and-cutover`. Codex Architect, responding to the S1-01 handoff review under the delegated decision authority in `.ai/ROLE_CONFIG.md`. The controlling detail is [the S1-01 Foundation contract addendum](../frontend/docs/architecture/s1-01-foundation-contract-addendum.md). This records an Architect choice, not owner acceptance of S1-01 or a new owner sign-off on the three Site-first documents. Current project routing treats those documents as implementation authority; their proposal headers remain provenance until an owner acceptance record is identified.

S1 uses PostgreSQL 16 through pinned Docker Compose, psycopg 3, SQLAlchemy Core and Alembic. A separate migrated PostgreSQL test database is required. The first migration enables `btree_gist` and applies the current-valid Foundation exclusion constraint; publication also locks the Site row. No application-only overlap fallback is silently selected. Initial Foundation may exist before bindings, but no acquisition snapshot or evidence is authorized until S1-02 publishes bindings.

Import the Kobo fixture under a configured development tenant, preserving `KOBO-001`, its timezone and v1 source values. Register all ten physical/topological components as assets; retain device inventory in Foundation content. Legacy signal mappings are comparison/candidate data until S1-02 turns them into explicit role bindings. Register one pending simulated gateway and one source per fixture device; one source owns one device report stream and all its signals share the source sequence scope. Gateway credentials remain unprovisioned until the S2 boundary. Internal database IDs are UUIDs; product routes keep the tenant-scoped stable Site code.

Until authentication is built, the backend resolves a fixed configured development tenant; client-supplied tenant identity has no authority. S1 cuts over Foundation only for explicitly imported Sites. The existing YAML Site file is the expected source of that import, identified by path and digest, not a duplicate collision. A changed source or another same-code record conflicts. Product Site index/detail reads select Postgres for registered imported codes (one row) and retain YAML for unimported codes. Legacy product Overview, Evidence and dispatch must not display or write stale file-backed state for an imported code. The Lab currently shares the Site repository and YAML store; it has no separate Site namespace. From import, new Lab Draft setup and existing Draft start/step/run-to-end/Commit for that code are blocked until Lab uses the registered snapshot. The current Stage endpoint is a read-only inspector; it may show historical staged envelopes labelled with their frozen YAML basis but cannot generate or seal more. Commit is blocked even for a stage produced before import. Evidence, Performance and Overview cut over in their later named slices. S1 publishing is battery reserve SOC only; priority controls stay read-only. The Kobo fixture has a 30-minute generator minimum-runtime property but no 35%/90% generator thresholds. An incomplete Foundation gap fixture removes reserve while remaining well-formed under the existing strict Site parser. The Planner owns the API/UI/guard details and records the fixture comparison in the S1-01 packet.

## Decision Index For Agent Context

Use this index to find only the decisions relevant to the active task. Keep
newest task-routing state in `.ai/ACTIVE_CONTEXT.md`; keep full decision
rationale in the dated entries below.

Lab cockpit decisions (owner accepted 2026-09-30):

- `D-2026-09-30-lab-cockpit-cadence`: L1a then L1b, sequentially before T026;
  conditional L2 in each owning slice and feedback-selected L3.
- `D-2026-09-30-lab-cockpit-history`: persisted host-owned history and gated
  projections; no implicit re-execution on read.
- `D-2026-09-30-lab-cockpit-presentation`: accepted timing, missingness, SLD
  reuse, playback and mockup annotations under existing seams.

Current direction correction: `D-2026-09-24-v4-roadmap-replan` supersedes the
old demo readiness/sequence and ambiguous sampling shorthand identified below.
Earlier dated entries remain history; `.ai/CODE_STATE.md` records what shipped.
Old pointers below to the feature-map execution-version ledger are historical:
the forecast was removed; relative version guidance is now in
`.ai/PLANNING_HANDOFF_T020A_T023.md`, Contract Versions And Retirements.

| ID | Date | Subject |
| --- | --- | --- |
| `D-2026-10-18-w2-05-buildspec` | 2026-10-18 | W2-05a/05b packets and code-anchored EV Foundation/producer specs. |
| `D-2026-10-18-w2-04-buildspec` | 2026-10-18 | W2-04 packet and code-anchored unpriced cold consequence/read/UI spec. |
| `D-2026-10-17-w2-02-buildspec` | 2026-10-17 | Nine W2-02 answers and code-anchored W2-02/W2-03 build specs. |
| `D-2026-10-18-w2-mockup-authority` | 2026-10-18 | Owner: v6.9 W2 cold and EV mock screens are binding visual and content authority; "extrapolation" tags mean only no v6.9 spec section. |
| `D-2026-10-17-f5-subtabs-and-contact` | 2026-10-17 | F5 mock in-page rows and Site Findings chips; W2-01 cold contact null closure. |
| `D-2026-10-17-w2-01-answers` | 2026-10-17 | W2-01 A–I closure and W2-02/W2-03 code-seam pre-check. |
| `D-2026-10-17-mockup-layout-spec` | 2026-10-17 | Binding v69 panel layout for W1 rework and W2+ UI; exact structure test, 1440/390 comparisons and High severity for structural drift. |
| `D-2026-10-17-w2-techdesign-ev` | 2026-10-17 | Amended W2-05a/05b/06/07 EV contract and exact ten-screen panel layout; OCPP peer deferred to pilot; owner EV visual and scope decisions pending. |
| `D-2026-10-17-w2-techdesign-cold` | 2026-10-17 | Amended W2-00 source format, W2-01..04 cold-chain contract and exact twelve-screen panel layout; owner scope pending. |
| `D-2026-10-17-w2-design` | 2026-10-17 | W2 cold-chain/EV architecture and simulator delivery plan; scope, core panels and demo values pending owner. |
| `D-2026-10-17-w1-rail` | 2026-10-17 | Full v69 operator rail inventory; only Sites and Findings link in W1, with gated Lab footer and route-proof guards. |
| `D-2026-10-17-w1-ux-06` | 2026-10-17 | W1 Readiness and Health labels preserve configuration, contact and fact-age boundaries. |
| `D-2026-10-16-s408` | 2026-10-16 | Site consequence history includes unpriced versions; cutoff head classification is separate from current-money authorization. |
| `D-2026-10-16-w1-ux` | 2026-10-16 | W1 separate contextual analysis, narrow reference disclosures, approved domain labels and honest-state-first plain language. |
| `D-2026-10-04-plain-language-analysis-views` | 2026-10-04 | Owner-directed plain-language defaults, assessment graphics and separate Analysis tabs in T028; amends practitioner-first presentation and the Finding tab inventory; product vocabulary guard. |
| `D-2026-10-04-practitioner-first-finding-presentation` | 2026-10-04 | Findings lead with a bounded operational explanation; provenance and method detail remain accessible through progressive disclosure. Narrow T028 correction before merge; money and prepared demo remain T029. |
| `D-2026-10-04-analytic-readiness-scope-and-gap-impact` | 2026-10-04 | Analytic readiness describes evidence sufficiency, site-wide in T028; claim-dependent gap treatment is interim, with versioned configurable impact types assigned to T028A. |
| `D-2026-10-02-demo-led-recommendation` | 2026-10-02 | Owner approved `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` at `57ea23e` ("review looks fine."); D1-D8 verbatim; section 9 outcomes are the coordinator's reading; its sequence supersedes the 2026-09-24 queue order from T027. Recorded by the Planner (Claude under the Codex exception). |
| `D-2026-10-02-rendered-tabs-per-capability` | 2026-10-02 | Rendered tabs are meaningful destinations decided per capability, not per site; "labelled in place" is not used in operator views; rendered Site tabs by milestone. Amends the 2026-09-13 canonical-fidelity and 2026-09-17 Foundation entries. |
| `D-2026-10-02-grammar-ownership-test` | 2026-10-02 | A place keeps its slot only if it owns something no other place shows; exceptions recorded; tasks citing overridden v6.9 text cite the decision; grouped rail is target, filtered to live items. |
| `D-2026-10-02-presentation-profile-and-capability-declaration` | 2026-10-02 | Presentation profile is static substrate data keyed by `site_type` (presentation only); the backend analytic capability declaration (T028) owns Finding types, evidence requirements and verification rules; three rendering rules. |
| `D-2026-10-02-demo-point-seed-rule` | 2026-10-02 | Each demo point ships an idempotent, rehearsed seed owned by the slice that creates it, checked with the Lab gate off. |
| `D-2026-10-02-delay-is-a-reporting-path-cause` | 2026-10-02 | A delayed publication is a scenario-declared reporting-path cause the publication profile answers for, like a reporting gap; it never changes value or source time, and one that would reorder publications is refused (release order is T026A). Architect ruling (Claude under the Codex exception). |
| `D-2026-10-02-scenario-states-override-issuer` | 2026-10-02 | A scenario control override is published as an operator-commanded override record only when its scenario EVENT entry declares `issued_by: OPERATOR` (optional, refused on any state but the stop-threshold and battery-reserve forcings); absent means no operator command, so no record. Who issued a change is a world fact the scenario states, not something the publication layer infers from the state key. `kobo-mini-grid-degraded-evidence` v1 declares it (re-pinned in-branch); `kobo-mini-grid-stop-60` is unchanged and publishes none. Contract stays 9. Owner signed off 2026-10-02; recommendation `.agent/T026-C1-architect-note.md`. |
| `D-2026-10-02-template-bump-record` | 2026-10-02 | A shipped template records a bump by `template_version`, pinned fingerprint and header note; `supersedes`/valid-from in `D-2026-10-01-run-binds-scenario-to-site` apply to scenarios only. A new device signal is template content: Kobo goes to v3 in T026. Owner signed off 2026-10-02. |
| `D-2026-10-01-run-binds-scenario-to-site` | 2026-10-01 | A run is the only join of a scenario version and a site version; `target_site` retired with legacy acceptance; no template hint; assumptions label; content change bumps version under a fingerprint guard. Contract clause amended 2026-10-01: no move, version stays 9 (owner signed off 2026-10-01). |
| `D-2026-09-24-v4-roadmap-replan` | 2026-09-24 | Corrected two-source basis; roadmap A-I, dispatch first, immediate component addressing; Planner recreates unfinished tasks. |
| `D-2026-09-24-task-spec-size-ceilings` | 2026-09-24 | Task-spec size bands become ceilings with no minimum, plus a cold-start test. `.ai/WORKFLOW.md` is their only owner. |
| `D-2026-09-11-stack` | 2026-09-11 | M1 uses the preferred MVP stack from the product specification. |
| `D-2026-09-11-simulator-gate` | 2026-09-11 | Simulator Lab is gated by `simulator_lab.enabled`. |
| `D-2026-09-11-workflow` | 2026-09-11 | AssetOps uses Architect/Planner, Implementer, Reviewer, and user-review workflow. |
| `D-2026-09-13-site-foundation-persistence` | 2026-09-13 | Persisted Sites, shipped templates, user-created Sites, and a swappable persistence adapter. |
| `D-2026-09-13-site-foundation-resequence` | 2026-09-13 | Site Foundation step 3 is template catalog, create from template, then read-only Site Configuration. |
| `D-2026-09-13-template-and-create-surfaces-gated` | 2026-09-13 | Template browsing and simulated Site creation are Simulator Lab surfaces behind the gate. |
| `D-2026-09-13-canonical-fidelity` | 2026-09-13 | Canonical mockup fidelity is staged after each surface has truthful content. Amended by `D-2026-10-02-rendered-tabs-per-capability`. |
| `D-2026-09-13-shared-site-substrate` | 2026-09-13 | Operator and Lab Site pages share one substrate at `frontend/src/sites/`. |
| `D-2026-09-13-provenance-status-vocabulary` | 2026-09-13 | Source mode, lifecycle, configuration origin, evidence readiness, and source health remain separate. |
| `D-2026-09-13-t006-preimplementation` | 2026-09-13 | T006 pre-implementation decisions for runtime gate proof, created Site shape, and non-loosening guard updates. |
| `D-2026-09-17-timezone-validation-timing` | 2026-09-17 | Real IANA timezone membership validation is required before timezone becomes executable behavior. |
| `D-2026-09-17-source-health-backing` | 2026-09-17 | Gateway/source health is backed by source observations, not Site lifecycle or simulator provenance. |
| `D-2026-09-17-site-foundation-fetch-seam` | 2026-09-17 | The Site Foundation frontend/backend fetch seam needs a focused integration test before expansion. |
| `D-2026-09-17-client-demo-readiness` | 2026-09-17 | Historical readiness ladder; superseded by D-2026-09-24-v4-roadmap-replan. |
| `D-2026-09-17-foundation-screen-architecture` | 2026-09-17 | The operator Site surface formerly called Site Configuration becomes Foundation, with line-cited Site tabs, filtered Foundation subtabs, route compatibility, and inventory guards. Amended by `D-2026-10-02-rendered-tabs-per-capability`. |
| `D-2026-09-20-layout-evidence-standing` | 2026-09-20 | Browser layout evidence is standing closeout evidence for layout-sensitive slices, kept outside the portable architecture runner. |
| `D-2026-09-20-no-merged-task-status-guard` | 2026-09-20 | No guard ties a merged slice's task status to branch state; closeout discipline stays manual until the drift recurs. |
| `D-2026-09-20-breaker-vocabulary` | 2026-09-20 | A breaker is topology and, when instrumented, a reported-about thing; position is evidence, not Foundation configuration. |
| `D-2026-09-20-scenario-definition-model` | 2026-09-20 | ScenarioDefinition is the saved, versioned scenario artifact; events are saved sub-artifacts inside a scenario version. |
| `D-2026-09-20-scenario-definition-storage` | 2026-09-20 | ScenarioDefinitions use composed shipped and writable stores behind a domain port, with one disjoint scenario_id space. |
| `D-2026-09-20-run-scoped-event-injection` | 2026-09-20 | Future event injection is run-scoped intervention history, not authored scenario content. |
| `D-2026-09-20-scenario-detail-affordances` | 2026-09-20 | Scenario detail renders only native controls; Run is disabled with a named prerequisite and downstream controls are absent. `Open target Site` removed by `D-2026-10-01-run-binds-scenario-to-site`. |
| `D-2026-09-21-scenario-authoring-semantics` | 2026-09-21 | The T017 checkpoint settles scenario versioning fields, the event taxonomy, and the public/private parameter boundary. |
| `D-2026-09-21-causal-runtime-before-golden-traces` | 2026-09-21 | A minimal executable causal runtime precedes authoritative golden traces; manual traces cannot establish scenario causality. |
| `D-2026-09-21-scenario-execution-contract` | 2026-09-21 | The T018 checkpoint settles execution roles, initialization and cadence ownership, timing and bound semantics, and that an unreached reading is stated rather than resolved. Amended by `D-2026-09-21-scenario-execution-contract-amendment-1`. |
| `D-2026-09-21-scenario-execution-contract-amendment-1` | 2026-09-21 | Amendment 1 to the execution contract: simultaneous causes net rather than order; the contract-version bump policy; run setup stops adjudicating cause-to-observation coupling; a scenario does not author what a device reads; `execution_requirement` is forbidden on a reported observation; a fifth `TRAJECTORY` oracle kind. |
| `D-2026-09-21-run-setup-outcome-vocabulary` | 2026-09-21 | `BLOCKED` is the shipped run-setup outcome, now on three reasons; the Fuel Loss residual splits into two scheduled decisions with different deadlines; `READY` discloses what it does not assert and T021 verifies it against the kernel. Extended 2026-09-22: the refusal line moved to who failed to answer, four location failures block as `INITIAL_VALUE_NOT_RESOLVED`, and the contradiction refuses as `INITIAL_VALUE_ANSWERS_DISAGREE` because the frozen identity can hold no answer and not two. Its one consequence about a Foundation declaring no such property at all is superseded by `D-2026-09-22-foundation-property-absent-blocks`: that case blocks. |
| `D-2026-09-21-projection-versus-composition` | 2026-09-21 | Projecting a document is static validation; composing projections into a value-at-a-time is a kernel, whatever the component is called. |
| `D-2026-09-21-specification-reference-implementation` | 2026-09-21 | A specification's reference implementation is labelled and carries a stated expiry; `reconcile_reported_observations` stops being an authority when a kernel is compared against it, and leaves the repository when its last product-path caller goes. |
| `D-2026-09-21-physical-property-ownership` | 2026-09-21 | Foundation declares what the site is, the model profile how the simulator reasons, the scenario what happens, the publication profile how the reporting installation behaves; two swap tests decide ownership, and a new slice T020A builds the missing carriers. Its template-copy consequence is corrected by `D-2026-09-22-foundation-property-absent-blocks`: a non-re-created MG-001 blocks, it does not refuse. |
| `D-2026-09-22-expiry-follows-the-condition` | 2026-09-22 | A gap-covering artifact names the condition as its expiry, never a slice number; a claim that has become false goes in the slice that falsifies it, and a thing still honest goes when someone decides to remove it. |
| `D-2026-09-22-foundation-value-declaration` | 2026-09-22 | A scenario parameter whose declared owner is Site Foundation has no value position at all. The rule is keyed on the owner, so it reaches `tank-capacity` as well as the coefficient, moves the contract version, and retires `INITIAL_VALUE_ANSWERS_DISAGREE` in T020A. Option C is a named follower. |
| `D-2026-09-22-consumption-coefficient-unit` | 2026-09-22 | The Foundation coefficient is specific fuel consumption in `L/kWh`, and `dispatched-output` is promoted to a `FORCING_INPUT` on `generator-output-power`. `L/h` is a property of machine times operating point and half that pair is the scenario's. Closes open question 4.1. |
| `D-2026-09-22-forcing-state-requirements` | 2026-09-22 | `site-load-demand` and `plane-of-array-irradiance` drop to `OPTIONAL`; reporting-path authority moves to the publication profile. The shipped Fuel Loss Event becomes able to reach `READY`. Two riders: a requirement conflict is refused rather than resolved, and `FROZEN_INPUT_ANSWERERS` gains `PUBLICATION_PROFILE`. Closes open question 3. |
| `D-2026-09-22-kernel-step-semantics` | 2026-09-22 | The four semantics the contract left open: linear ramp across a window, sampling (clarified by v4 section 6 and D-2026-09-24-v4-roadmap-replan), a forcing outside its window is unavailable, and a bounded change lets the run continue against the bounded value. Closes open question 1. |
| `D-2026-09-22-reconciliation-panel-retirement` | 2026-09-22 | The `observation_reconciliation` panel goes with (f) in T022, which completes (j) by taking the reference implementation, `declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` out of the product path. Closes open questions 5 and 11. |
| `D-2026-09-22-capacity-bound-source` | 2026-09-22 | A bound's declaration is the document's and its value is the site's. `declared_bounds` reports no upper value for `fuel-tank-volume` after T020A and that is the correct answer; the number lives in the frozen run and the first thing entitled to hold both halves is T021's kernel. |
| `D-2026-09-22-foundation-property-absent-blocks` | 2026-09-22 | A Foundation that declares no such property at all blocks with `INITIAL_VALUE_NOT_RESOLVED`. It is a fifth case of the four, not a refusal, because after T020A the binding names the property and a different profile might name another. |
| `D-2026-09-22-milestone-speed-over-purity` | 2026-09-22 | Speed over pedantic purity for the rest of the simulator milestone; a complete review, possibly a refactor, follows milestone completion and proper testing. Stop only for a defect expensive to reverse, a claim that would mislead an Implementer, or a decision only the user can take. Everything else is recorded to `.ai/MILESTONE_REVIEW_BACKLOG.md` and carried. **Governs every slice, pass and review after it.** |
| `D-2026-09-22-contract-version-scope` | 2026-09-22 | `EXECUTION_CONTRACT_VERSION` moves when a change can alter the outcome for a document that was already valid. A narrowing can; a pure widening off every executable path cannot, so the `TRAJECTORY` oracle kind does not move it. The absolute numbers are unstable and are written relatively. |

## 2026-09-11

Decision: M1 uses the preferred MVP stack from the product specification:
Python/FastAPI backend, React/TypeScript frontend, Python deterministic
simulator, modular monolith, strict boundary parsers, file-backed repositories
where sufficient, single-host container deployment, and CI-enforced architecture
guards.

Reason: The first tasks need a concrete, production-compatible but simple
technical direction before backend, frontend, simulator, parser, repository, and
CI boundaries can be planned.

Affected scope: Architecture, implementation stack, local development,
deployment, parser contracts, repository choices, CI guard planning.

## 2026-09-11

Decision: Simulator Lab is gated by `simulator_lab.enabled`, deployment-wide for
M1 and shaped for future per-tenant gating. When disabled, simulator routes,
navigation, entry points, execution actions, and truth overlays are not served,
while existing simulated Sites, SIMULATED provenance, operator routes,
analytics, and Replay remain unchanged.

Reason: Simulator execution and truth surfaces must be removable without
changing the normal AssetOps product model or leaking simulator-only capability
through hidden-but-reachable routes.

Affected scope: Simulator Lab routing, navigation, feature flags, truth overlay,
operator shell, simulated Site provenance, Replay, architecture guards,
acceptance testing.

## 2026-09-11

Decision: Start AssetOps with a lightweight Architect/Planner, Implementer,
Reviewer workflow and vertical-slice tasks.

Reason: The repository needs low context cost, frequent human review, independent
review, and protection against speculative architecture.

Affected scope: Repository governance, feature planning, task planning, review
model.

## 2026-09-11

Decision: Treat private simulator truth as separate from product-visible
evidence from the first slice.

Reason: AssetOps should learn from realistic site/device observations without
accidentally depending on privileged simulator internals.

Affected scope: Simulator, ingestion, analytics, evidence, UI claims.

## 2026-09-11

Decision: Treat UI-verifiable outcomes as the default standard for vertical
slice development.

Reason: The first useful AssetOps learning should come from screens the user can
inspect, especially the Simulator Lab and site operations screens in
`Docs/UI Design/Motivation`.

Affected scope: Task planning, backend scope, frontend scope, acceptance
criteria, review packets.

## 2026-09-11

Decision: Treat Architect, Planner, Implementer, and Reviewer as configurable
roles with default agent bindings.

Reason: Planner and Architect should default to Codex agents, Implementer should
default to a Claude agent, and future projects should be able to change those
bindings without redefining role responsibilities.

Affected scope: Role configuration, Claude Code commands, skills, workflow
handoffs.

## 2026-09-11

Decision: M1 will use a narrowed canonical Site Foundation schema with stable
Site identity plus versioned Site Foundation, stored in YAML for the initial
slice.

Reason: The first milestone needs canonical Site semantics that support
arbitrary Sites without hard-coding MG-001, while avoiding the scope of the full
future AssetOps Site schema before the simulator, gateway, and ingestion path is
proven.

Affected scope: Site configuration, Site identity, SimulatorRun references,
topology, devices, mappings, ratings, control assumptions, ingestion
provenance, UI task breakdown.

## 2026-09-11

Decision: The first Simulator Lab vertical slice will use a deterministic
recorded-run player instead of implementing the complete physical runtime.

Reason: The recorded player gives the first UI slice truthful simulation time,
world state, events, device reporting, and gateway publication while preserving
the intended runtime, ingestion, and AssetOps contracts. It is a bootstrap state
producer only, and must not introduce a demo-only ingestion path or precomputed
AssetOps conclusions.

Affected scope: Simulator runtime contract, Simulator Lab UI, recorded world
state, device reporting, gateway staging, ingestion boundary, deterministic
runtime migration, task sequencing.

## 2026-09-11

Decision: M1 will separate the canonical Source Envelope from typed AssetOps
evidence contracts.

Reason: Source envelopes should provide strict identity, timing, sequencing,
publication, provenance, and transport structure while typed evidence contracts
carry family-specific semantics. This avoids both demo-only ingestion shortcuts
and a permissive `{type, payload}` model, while supporting gateway/source
health, generator runtime, and fuel reconciliation from evidence a real device,
controller, operator, import, or external source could publish.

Affected scope: Ingestion contract, evidence contracts, telemetry, events,
alarms, operational records, controller records, validation, source health,
simulator publication, analytics, provenance, task sequencing.

## 2026-09-11

Decision: M1 Commit is a state transition that releases a completed Draft
SimulationRun's immutable staged Source Envelopes for AssetOps ingestion.

Reason: Commit must preserve the authored evidence publications exactly, avoid
copy/regeneration semantics, and keep ownership clear: Simulator Lab owns
`STAGED -> RELEASED`; AssetOps ingestion owns `RELEASED -> ACCEPTED | REJECTED`.
Commit is atomic and idempotent at the SimulationRun release scope, and it never
creates Site history, health state, findings, incidents, analytics, or other
derived product objects directly.

Affected scope: SimulationRun lifecycle, staged publication storage, release
manifest, message identity, ingestion validation, source timestamps,
`received_at`, UI task breakdown, audit and replay semantics.

## 2026-09-11

Decision: M1 will implement the Single-Line Diagram using a reusable hybrid
mini-grid archetype template with data bindings, rather than a fully automatic
topology-layout engine.

Reason: The first milestone needs a truthful diagram that can be implemented in
a reviewable slice without treating layout as canonical topology. Site
Foundation remains the source of truth for components, topology, connectivity,
ratings, devices, and signal availability; the archetype owns only presentation
and validates compatibility explicitly.

Affected scope: Site Foundation topology, SLD view model, Site Configuration,
Simulator Lab SLD, runtime overlays, evidence overlays, topology compatibility,
future graph/layout migration.

## 2026-09-11

Decision: M1 will implement product conclusions in causal order:
Gateway/Source Health, Generator Runtime Assessment, then Fuel
Reconciliation/Fuel Discrepancy.

Reason: Downstream analytics first need evidence coverage, timeliness, and
validity. Generator runtime must be established before fuel movement can be
reconciled, and a fuel discrepancy becomes a Finding only when materiality and
confidence criteria warrant operator attention. The product must use bounded
language such as unexplained fuel variance and must not infer theft or hidden
cause from discrepancy alone.

Affected scope: Source health, evidence availability, generator runtime
assessment, fuel reconciliation, findings, confidence/materiality criteria,
claim language, cold-room follow-on sequencing, UI task breakdown.

## 2026-09-11

Decision: M1 will use progressive disclosure for provenance: primary product
screens show decision-relevant provenance, while detailed technical provenance
is available through Evidence/Provenance inspection drawers and ingestion/log
views.

Reason: Operators need to see source mode, time window, freshness,
completeness, and claim limitations immediately, but low-level transport detail
should not crowd normal product screens. Provenance visibility should increase
with consequence: raw measurements need minimal provenance, assessments need
evidence sufficiency, and Findings or recommendations need inspectable evidence
basis. Scenario/private-truth causes remain outside product evidence provenance.

Affected scope: Site headers, source-mode display, evidence summaries,
Gateway/source health, Findings, recommendations, Evidence/Provenance drawer,
ingestion/log views, Simulator Lab reproducibility metadata, UI task breakdown.

## 2026-09-11

Decision: M1 allows canonical Sites to exist before they have live integrations
or SimulationRun evidence. Such Sites are valid configuration-only Sites.

Reason: A Site may be meaningfully configured before operational evidence
exists. AssetOps must show declared identity, lifecycle, location, timezone,
Foundation, topology, devices, mappings, ratings, control assumptions, and
intended source/integration configuration without fabricating operational
evidence, health, analytics, charts, or conclusions.

Affected scope: Sites List, Site Details, Site Configuration, configuration-only
Sites, source mode, lifecycle state, integration readiness, evidence
availability, gateway/source health, SLD runtime overlays, simulator exercises
of intended-live Site Foundations, UI task breakdown.

## 2026-09-11

Decision: M1 keeps canonical Site/Foundation configuration file-backed in YAML
and provides a read-only Site Configuration UI.

Reason: YAML should remain the authoritative source of truth for Site identity,
Foundation version, components, topology, devices, mappings, ratings, control
assumptions, and related configuration while the simulator, gateway, ingestion,
and evidence path is proven. The UI can render and explain configuration,
Foundation version, effective dates, SLD, and device/signal relationships, but
in-product editing, persistence, save/publish, approvals, and configuration
history management are deferred.

Affected scope: YAML Site/Foundation configuration, configuration validation,
Site Configuration UI, edit affordances, Foundation version/validity display,
SLD configuration display, device/signal relationship display, future
configuration API migration, task sequencing.

## 2026-09-11

Decision: M1 allows overlapping Draft SimulationRuns, but blocks Commit when a
Draft interval overlaps already committed simulated history for the same
`site_id`.

Reason: Simulator Lab needs Draft overlap for scenario experimentation, reruns,
and deterministic comparison, while AssetOps needs unambiguous committed Site
history until explicit branch/context selection exists. Simulation intervals use
half-open semantics `[start_time, end_time)`. Committed source evidence is
immutable; rerun creates a new Draft `run_id`, and replay inspects committed
persisted evidence without rerunning.

Affected scope: SimulationRun lifecycle, Commit eligibility, half-open interval
validation, run management UI, rerun/replay semantics, deterministic identity,
committed evidence immutability, future branch/context selection, admin reset
boundaries, task sequencing.

## 2026-09-13

Decision: Site and Site Foundation configuration is reached only through a
`SiteRepository` port defined in the product domain, with storage technology
supplied by an adapter selected in a single composition root. The port speaks
domain records and port-level errors; it never exposes files, paths, YAML text,
serialization formats, or store-specific exceptions. M1 ships two read adapters
over shipped canonical configuration and user-authored configuration, plus one
write adapter for user-authored configuration. Replacing file storage with any
other mechanism must require a new adapter module and one composition-root
change, and no change to callers.

This supersedes part of the 2026-09-11 decision "M1 keeps canonical
Site/Foundation configuration file-backed in YAML and provides a read-only Site
Configuration UI", specifically its deferral of persistence. Persistence is no
longer deferred for user-authored configuration. Everything else in that
decision still stands: YAML remains the serialization format and the
authoritative representation of Site identity and Foundation content, strict
validation on load is unchanged, and approvals and configuration history
management remain deferred. The read-only-UI clause is addressed separately
below.

Reason: The user requires the persistence mechanism to be replaceable later
without rewriting callers. A naming convention does not deliver that; a port
with a testable dependency direction does. Introducing it before any Site read
model exists is cheap, and retrofitting it after Sites, templates, SLD view
models, and evidence resolution all reach storage directly is expensive and
error-prone. Keeping the port free of file and format vocabulary is what makes
the swap real rather than nominal.

Affected scope: Site read models, Site Configuration UI data path, Site
templates, user-authored Site creation, backend module tree, composition root,
strict boundary parsers, CI architecture guard, future configuration API or
database migration, task sequencing.

## 2026-09-13

Decision: M1 distinguishes shipped canonical configuration templates from
user-created Site instances as separate concepts in separate identity spaces and
separate stores. A template has `template_id` and `template_version`, ships
read-only in the repository, and is not a Site: it has no `site_id`, no
lifecycle status, no location or timezone binding, and it cannot appear in the
Sites index, be targeted by a scenario, be simulated, or receive evidence.
Instantiating a template copies its Foundation content into a new Site document
and records `template_id` and `template_version` as origin provenance; the
created Site does not live-reference the template, and later template changes
never alter existing Sites. Shipped Sites and user-created Sites occupy one
globally unique `site_id` space with no overlay and no precedence: the same
`site_id` present in both stores is a startup-level conflict, and creation
refuses any `site_id` already present in either store. Configuration origin
(`SHIPPED` or `USER`) is provenance about the configuration document and is a
separate concept from `source.mode`, lifecycle status, integration readiness,
and source health.

This refines rather than supersedes the 2026-09-11 "YAML configuration
authority" position. YAML remains authoritative and strictly validated on load
in both stores. What changes is only who may write it: shipped configuration
stays read-only at runtime, and a second writable store holds user-authored
documents.

Reason: The distinction the user asked for only survives if it is structural. If
a user Site were created by copying a shipped Site, shipped Sites would silently
become templates and the precedence, identity, and provenance rules would have
to be retrofitted after user data exists. Overlay resolution was rejected
because a `site_id` that resolves to different content depending on store state
breaks the identity seam that every later run, envelope, evidence record, and
analytic is keyed on. Encoding origin into identity, such as prefixing
user-created `site_id` values, was rejected for the same reason the project
refuses to let a scenario label become a Site name: origin is provenance about a
configuration document and must not be readable out of the identity that
downstream history is keyed on. Copy-on-instantiate was chosen over live
reference because
a shipped template change would otherwise retroactively alter Foundations that
committed simulated history already depends on.

Affected scope: Site identity, template catalog, Site creation, configuration
origin provenance, Sites index, Site Details, Site Configuration UI, store
layout, identity validation, strict parsers, CI architecture guard, scenario
targeting, future template versioning and drift inspection, task sequencing.

## 2026-09-13

Decision: M1 makes Site creation a real product capability while keeping the
Site Configuration UI read-only. A user may create a Site by choosing a shipped
template and supplying identity and required identity-level fields; the
resulting Site is validated as a complete document and persisted through the
write adapter. In-place editing of an existing Site Foundation remains
unavailable, as do Save, Publish, approval, rename, delete, `site_id` change,
Foundation version bump in place, configuration diff, history, and rollback.
`site_id` is immutable after creation. The Site Configuration UI renders every
Site read-only regardless of origin and must state that configuration is fixed
at creation in M1, rather than implying an editing workflow that does not exist.
User-authored configuration is untrusted input: it crosses the same strict
parser as shipped configuration, with no lenient path, and the fully
materialized document is validated before anything is written.

This supersedes part of the 2026-09-11 decision "M1 keeps canonical
Site/Foundation configuration file-backed in YAML and provides a read-only Site
Configuration UI", and correspondingly narrows the "Read-only configuration UI"
enforceable seam. Superseded: the blanket deferral of in-product authoring and
of save semantics, which now exist for creation. Still standing in full:
in-place Foundation editing, Save and Publish over an existing Foundation,
approvals, configuration history and rollback are deferred; the Site
Configuration UI itself remains read-only and offers no edit affordance; strict
validation on load is unchanged; YAML remains the authoritative representation.

Reason: Creating a Site and editing a Site are different capabilities with
different risk. Creation writes a new `site_id` that no run, envelope, evidence
record, mapping version, or committed history depends on yet, so its blast
radius is bounded by validation of one new document. In-place editing mutates a
Foundation that later slices bind evidence and committed simulated history to,
and raises Foundation re-versioning, effective dating, revalidation against
existing evidence, and the question of what happens to committed history when a
mapping changes. M1 needs the first capability and has no answer for the second,
so shipping creation now and deferring editing keeps the milestone honest
instead of implying a configuration lifecycle the product does not have.

Affected scope: Site Configuration UI language and affordances, Site creation
flow, identity validation, untrusted-input handling, write-path atomicity,
Foundation versioning, deferred editing and history semantics, protected seams,
task sequencing, user-review checkpoints.

## 2026-09-13

Decision: M1 offers no user-facing way to remove a user-created Site. The
`SiteRepository` port exposes no `delete`, no archive, and no tombstone, and no
UI affordance or route removes a Site. Removing a user-created Site is a
developer action on the store for the whole of M1. If removal is wanted later it
becomes its own slice with explicit archive, tombstone, or hard-delete
semantics, and it is never folded into Site creation.

Reason: The Architect raised removal as the one product call it could not make.
Later slices key committed simulated history, envelopes, and evidence records to
`site_id`, so delete-then-recreate under the same identity would resurrect
orphaned history under a different Foundation. The cost of deferring is that
demo Sites accumulate and can only be cleared from disk, which is acceptable
while the store is file-backed and the audience is developers. The cost of
shipping removal early is an identity and history question of the same family as
in-place editing, which M1 has deliberately deferred.

Affected scope: `SiteRepository` port surface, Site creation slice scope, Sites
List affordances, user store lifecycle, future archive/tombstone semantics,
feature map open questions, task sequencing.

## 2026-09-13

Decision: The Architect's extended working notes for a feature are local-only
process material. Durable architectural context belongs in `.ai/DECISIONS.md`,
`.ai/ARCHITECTURE.md`, and `.ai/FEATURE_MAP.md`, and the tracked task files must
be sufficient on their own to implement a slice. Tracked documents must not
direct a reader to a `.agent/` file as required reading.

Reason: `.agent/` is gitignored and absent on a fresh clone, so a tracked
pointer into it is a broken dependency and contradicts the existing instruction
to normally ignore local-only files. The balance being struck is between context
bloat and provenance: promoting every line of an Architect handoff into tracked
governance would bloat the documents every session loads, while leaving the
reasoning only in a local file loses the provenance behind decisions that
supersede earlier ones. Recording the decision, its reason, what it supersedes,
and the alternatives rejected is enough provenance; the long-form derivation is
not.

Affected scope: Architect handoff artifacts, `.ai/START_HERE.md` references,
`.ai/ARTIFACT_INDEX.md` artifact states, what the Implementer is required to
read, future Architect and Planner output conventions.

## 2026-09-13

Decision: `ScreenMockups.png` renders the Simulator Lab developer shell, not the
operator product, and the canonical mockups are read that way from now on.
Consequently the mockups do not place Simulator Lab in operator navigation, and
the T003/T004 position stands unchanged: Simulator Lab is not an operator
navigation item, it is reached from workspace-level chrome, operator navigation
is structurally identical in both gate states, and no T003 or T004 boundary test
may be weakened or removed.

The evidence. v6.9 section 3.9 gives the Simulator Lab its own shell whose
navigation is "Home | Sites | Simulator Lab | Scenarios | Site Templates |
Library | Documentation | Settings". `SimulatorLab1.png` reproduces that list
exactly, and `ScreenMockups.png` reproduces it with Devices, Ingestion and
Events inserted, which v6.9 defines as Simulator Lab run tabs rather than
destinations. v6.9 section 2 fixes operator navigation at ten object classes,
Portfolio, Sites, Assets, Findings, Actions, Incidents, Maintenance, Evidence,
Financials and Reports, and not one of the mockup's rail items beyond Sites
appears in it. The screens diverge the same way: the mockup's Site tabs are
Overview, Configuration, Devices, Gateway, Ingestion, Events, Logs, while v6.9's
canonical Site tabs are Overview, Foundation, Health, Performance, Findings,
Work, Financials, Evidence; the mockup's Sites columns are Name, Type, Location,
Status, Last Data, Actions, while v6.9's are Site, Type, Mode, Assessment, Top
issue, Evidence, Last analysed. v6.9 section 3.1 is headed "Entry points (no new
operator navigation items)" and lists "Workspace utility menu: Open Simulator
Lab", which is what T004 implemented.

This supersedes nothing. It corrects a reading, and it removes the apparent
conflict rather than resolving it in either direction: read correctly, the
mockup agrees with T004.

Reason: The alternative reading, that the mockup is the operator shell and
therefore demands Simulator Lab in operator navigation, would have reversed a
merged and accepted slice whose direction came from an explicit user review at
the T003 checkpoint, on the strength of an illustration that contradicts both
the normative product document and the other mockup. Two images that disagree
with each other about the rail, and an image whose own breadcrumbs read
`Sites > MG-001 > Devices` while its rail shows Devices as a destination, are
illustrative rather than normative. Where they and v6.9 disagree, v6.9 settles
it.

The residual question is not architectural and is recorded as the one open
question in `.ai/FEATURE_MAP.md`: whether the user intends those nine screens as
a single merged shell for M1. That would be a product call the user is entitled
to make and it would supersede this entry. It is not assumed here.

Affected scope: Canonical mockup interpretation, operator navigation, Simulator
Lab shell placement, T003/T004 boundary tests, shell placement of every Site
Foundation surface, UI fidelity targets, feature map open questions.

## 2026-09-13

Decision: Causal Sequencing step 3 is resequenced. The order is now (3a) shipped
Site configuration template catalog, (3b) create a Site from a template, (3c)
read-only Site Configuration presentation. M1 ships zero canonical Sites: the
shipped read-only content is the template catalog, and every Site in the product
is one a user created. First run has a genuinely empty Sites index.

This supersedes the sequencing recorded earlier the same day in
`.ai/FEATURE_MAP.md` Causal Sequencing step 3, which ran (3a) Site repository
port and canonical read path over a shipped canonical Site fixture, (3b) shipped
templates, (3c) create. It also supersedes the slice order in that map's Site
Foundation feature-to-task guidance. It does not disturb the three 2026-09-13
persistence decisions above: the port, the two-store identity rules,
copy-on-instantiate, untrusted-input handling, create-without-edit, and no
removal all stand exactly as recorded.

Reason: The user's correction is right and the earlier ordering was wrong. A
Sites index is a view over Sites somebody configured. Shipping the index first,
populated by a canonical fixture Site, makes the view real before the capability
that fills it, and pushes the milestone's own first clause, "a user can
configure one mini-grid site", to the end of the feature. It also produces a
poor first review surface: a single row that arrived by no product action, from
which the user cannot distinguish a working configuration path from a hardcoded
row.

Where the earlier reasoning was actually wrong, specifically: it argued that the
port needed a real read consumer before it could be trusted, and then assumed
that consumer had to be a shipped Site. The template catalog is also a real read
consumer, and a better one, because it is a complete truthful screen that
requires no Site to exist. Putting a fixture Site on the critical path bought
nothing the template catalog does not buy, and cost the causal order. The one
constraint that made the earlier ordering partly right, that the template
concept must be structural before any write path or the first create copies a
shipped Site and collapses the template/instance distinction, survives untouched
and now orders the sequence on its own.

Alternatives rejected. Keeping a shipped canonical Site so that later steps and
CI have a Site without running the create flow: rejected because it restores
exactly the thing the user objected to, and because the two-store disjointness
seam it was said to protect is testable with a fixture store that is not a
product-visible Site. Shipping list, get and create in one slice so the port
arrives complete: rejected as too large for one review packet; the split is
template catalog, then create, then configuration presentation.

Consequences worth naming. `MG-001` becomes the Site the user creates from the
Hybrid Mini-Grid template rather than a Site that ships, which is also what
`SimulatorLab1.png` already shows in its run header as "Template: Hybrid
Mini-Grid (100 kW)", and what v6.9 section 3.5 setup path A describes as
template, then Foundation, then save, then run. Later steps that need a Site
create one. The two user-review checkpoints move: the first to the create slice,
the second to the configuration presentation slice.

Affected scope: Causal Sequencing step 3, Site Foundation feature-to-task
guidance, candidate vertical slices, the product spine, the shipped Site store,
first-run empty state, user-review checkpoint placement, T005-T008 task files,
and every later step that assumed a Site exists without being created.

## 2026-09-13

Decision: Authoring a simulated Site is a Simulator Lab capability and is gated
by `simulator_lab.enabled`. The Site Templates catalog and the create-a-Site
flow live in the Simulator Lab shell, behind the gate. The Sites index, Site
Details, and Site Foundation/Configuration presentation are operator
capabilities and are never gated. A Site created while the Lab was enabled stays
fully visible when the Lab is disabled, because it is product Site history and
not simulator execution. Operator navigation does not grow at all in step 3.

This supersedes the Architect's own contrary guidance, given earlier on
2026-09-13, that Site and template routes must not be gated on
`simulator_lab.enabled`. Half of that guidance stands and is now stated more
precisely: the Sites index, Site Details, and Site Configuration are never
gated, and wiring them to the simulator flag would make Sites vanish when the
Lab is switched off. The half that was wrong is template browsing and Site
creation.

Reason: v6.9 section 3.1 makes `+ Add site` an entry point whose "Create
simulated site" and "Clone site into scenario" options "open the Simulator Lab
workspace", and section 3.9 lists Site Templates in the Lab shell's navigation
and nowhere in the operator's. The only non-simulator creation path v6.9
describes is "Register live site", which depends on backend Site registration
that v6.9 explicitly defers. So a gate-off build with an empty Sites index and
no way to add one is the correct state rather than a defect.

The deciding argument is direction of risk, not only conformance. Moving a
surface out from behind the gate later is a cheap, reversible change.
Retrofitting a gate around a surface that already shipped ungated is precisely
the hidden-but-reachable failure the gate seam exists to prevent. Where a
Site-authoring surface is ambiguous, it ships gated.

Affected scope: `simulator_lab.enabled` reachability list, Site Templates and
create-flow route placement, operator navigation growth, gate-off acceptance
criteria, T003/T004 boundary tests, Site Foundation task shell placement.

## 2026-09-13

Decision: Canonical mockup fidelity is in scope from the Site Configuration
slice onward, staged per surface, and governed by three rules. First, content
before chrome: a surface adopts canonical layout only after that surface's
content is real, and no numeric value, timestamp, status, or label appears
because the mockup shows it. Second, three treatments rather than two, taken
from v6.9's own usage: a gated or decided-against capability is not rendered at
all; a canonical tab that names a real aspect of an entity but has no content
contract yet is labelled in place; a built capability that is not currently
eligible is disabled with its reason stated. Third, fidelity to the mockup is
not fidelity to its errors.

Applied to the deferred affordances the mockups show: `Edit`,
`Edit Configuration`, `Version History`, `Duplicate Site`, `Delete Site`, and
the site image `Change` control are absent from the rendered output, not
disabled. `Open in Simulator Lab`, `Start Simulation`, and `View Live Data` are
present and disabled with their named prerequisite. The Site tabs
`Configuration`, `Devices`, `Gateway`, `Ingestion`, `Events`, and `Logs` are
labelled in place until their causal step lands.

Reason: The three treatments are not invented here. v6.9 gates the Simulator Lab
by not rendering it, "not merely hidden"; it labels a deferred tab in place as
"Warranty (P1)" with "deferred, no content contract yet"; and it disables Commit
on a Draft run with the note "draft envelopes are not released to ingestion
until Commit". Adopting the document's own vocabulary keeps the product
internally consistent and avoids inventing a fourth pattern.

The absent-versus-disabled line falls where it does because disabled reads as
"soon". `Open in Simulator Lab` is genuinely soon and the feature map can name
the step that makes it true, so disabling it is informative. `Edit` is not soon:
M1 has decided configuration is fixed at creation, and greying the control would
make a promise the product has declined to make. `Version History` is worse than
a promise: no configuration-change model exists, and v6.9's eventual form for
that territory is `Foundation > Changes`, an auditable intervention record with
`Retain / Retune / Revert`, which is a different capability from version
history. Shipping the mockup's label would name a future capability wrongly. The
distinction between an action control and a tab is what makes the middle
treatment safe: a tab set describes the aspects of an entity, so naming an
aspect early is honest chrome, while a greyed button describes an action the
user cannot take and should not expect.

Two mockup errors that fidelity work must correct rather than copy. Canonical
screen 1 puts `Simulated` and `Planned` in one `Status` column, collapsing
provenance into status, which v6.9 forbids three separate times, "Mode is
provenance, not status" and "SIMULATED is neutral provenance, not an
assessment", and which the existing vocabulary-separation seam already forbids;
Mode and lifecycle are separate columns. And the mockup's `Last Data` timestamps
are evidence the product does not have; v6.9's equivalent column is `Last
analysed`, rendered `--` when there is no data in the window, and that rendering
is the target. Note also that v6.9 has no `Planned` site status and no site
lifecycle enum at all, so `lifecycle_status` is this project's extension and its
values are fixed by the M1 Site schema, not by the mockup.

Fidelity staging: shared visual vocabulary first, applied only to surfaces that
already have real content; then template catalog, create flow, Sites index, Site
Details, and Site Configuration in that order; then the configured Single Line
Diagram at causal step 4; then canonical screens 4 through 9 as their steps
land. The fidelity slices carry no user-review checkpoint of their own, because
they add no capability and no product language.

Affected scope: Site Details and Site Configuration affordances, Sites index
columns and status vocabulary, tab sets, empty and unavailable states, the new
mockup-fidelity seam and its CI guard, the read-only configuration UI seam, task
count and task shape for the Site Foundation feature.

Amended by `D-2026-10-02-rendered-tabs-per-capability`: "labelled in place" is
not used in operator views; the rest of this entry stands.

## 2026-09-13

Decision: Navigation growth is its own concern with its own rule, not a
by-product of any feature slice. A navigation destination appears only when the
route behind it renders a truthful surface. No placeholder destinations, no
disabled navigation items, no "coming soon" routes. When a Site Foundation slice
needs a new surface, whether that surface earns a navigation entry is answered
by this rule and by shell placement, never by the mockup rail.

Two immediate consequences. Operator navigation does not grow during step 3 at
all, because every new step 3 surface is a gated Simulator Lab surface in the
Lab's own shell. And the current parameterless `Site details` and
`Site configuration` operator navigation items are step-1 route placeholders
from before Site identity existed; once Sites are addressed by `site_id` they
must be removed, because a Site Details link that names no Site is not a
destination. Those surfaces are reached from a Sites row.

Reason: Navigation is a stronger claim than a button. A button says an action
exists; navigation says the product has a place. A rail of ten items where six
are dead teaches an operator a product that does not exist, and it does so on
every screen rather than in one panel. This is the same honesty posture the
project already applies to evidence, applied to information architecture. It is
also why the mockup rail is not a build target: the operator rail's real
long-run shape is v6.9 section 2's ten object classes, and nothing from the
mockup rail should be added to operator navigation on the strength of the mockup
alone.

Affected scope: Operator shell navigation, Simulator Lab shell navigation, route
placeholders from T002, navigation-related acceptance criteria in every later
slice, the mockup-fidelity seam, feature-to-task guidance.

## 2026-09-13

Decision: Simulator Lab exists to unblock product development before a real site
exists. Three consequences are now durable rules.

First, a Site the Lab produces is a normal Site. Same identity space, same
model, same repository, same store, same index, carrying simulated source mode
as provenance. It is not a second class of object, it is not Lab-owned, it lives
in no Lab-owned store, and it is never published or promoted into the product,
because it was a product object from the instant it was created. The gate covers
surfaces and execution, never objects or stores.

Second, where both shells present the same object they present it from one
substrate. The operator Site page and the Lab Site page are one presentation
core with shell-specific additions, not two implementations that happen to
agree. The substrate owns the read model, the view model that turns a record
into display, and the presentation components; neither shell may fork any of the
three. Each shell may only compose and add through named slots the substrate
declares: the Lab adds run and execution context, the operator adds a gated way
into the Lab. The substrate carries no shell, mode, or variant discriminant, and
it is a leaf that imports no shell code, no simulator code, and no feature flag.

Third, the Lab's navigation exists only to serve that purpose. It is a developer
workspace menu, not a second product information architecture, and nothing in it
is evidence that the operator product should have a matching destination.

This amends the reason given in the gating decision recorded earlier today. That
decision stands unchanged -- template browsing and Site creation are Lab
surfaces behind `simulator_lab.enabled`, and the Sites index, Site Details and
Site Configuration are never gated -- but its stated reason led with conformance
to v6.9. It should lead with purpose. The Lab is gated and self-contained
because it is a place to work before a real site exists, and that is also the
limit on what self-contained may mean: self-contained describes the workspace,
never the objects the workspace produces. v6.9's placement of Site Templates and
`Create simulated site` in the Lab is corroboration, not the reason.

Reason: The substrate rule is the expensive one to get wrong. The late failure
is not that the two shells look different; it is that they drift into two Site
models. Different labels for the same field, different unavailable states, a
value derived one way here and another there, and eventually two read models
with a translation layer between them. By then both have users and neither can
be changed alone. The cheap-looking variant of the same failure is a
`variant="lab"` branch inside the shared core: it looks shared, and its branches
drift independently anyway. That is why a discriminant inside the substrate is
banned outright and every difference must be expressible as an addition around
the core. If a difference cannot be, it is not a shell difference and belongs in
the substrate for both.

Dependency direction is what lets this coexist with the existing ban on
operator-to-simulator imports. The substrate is a leaf: both shells import it,
neither imports the other, and it imports neither. So the operator shell renders
a Site without any path to simulator code, and the substrate cannot become a
back door into simulator internals because it declares slots and never imports
what fills them. The one operator-to-Lab crossing, Open in Simulator Lab, reuses
the single gated entry-point module that T004 established rather than adding a
chokepoint or routing through the substrate.

Alternatives rejected. Build the Site page operator-first and extract a shared
core when the Lab needs one: rejected because extraction after two pages exist
is the expensive refactor and the drift has already happened by then; the whole
point of the rule is that it costs nothing before the second consumer and a
great deal after. A `variant` prop on shared components: rejected above. Letting
the Lab own its Sites and publish them to the product: rejected because it
contradicts "a normal Site with a simulator tag" and would invent a promotion
step, a second store, and a second identity moment that nothing needs.

On timing, and against the appearance of inconsistency: refusing a port with no
consumer and requiring a substrate with one consumer are not in tension. A
port's shape is unknown until a caller proves it, so shipping one early is
guesswork. The substrate's shape is already known, because it is the Site read
model the create slice must build regardless, and the user has stated a second
consumer is coming. The only decision being made early is which directory the
files go in, and the structural guards that keep them there.

Affected scope: Frontend module tree, Site read model and view model ownership,
operator and Lab Site pages, extension-slot design, the new shared-substrate
seam and its three checks, `Open in Simulator Lab` treatment under the gate,
Site Foundation feature-to-task guidance and file placement, fidelity staging,
and the reason recorded for the gating decision.

## 2026-09-13

Decision: The product has exactly two provenance concepts, not three, and six
independent provenance-and-status concepts in total.

2026-09-24 routing update: the duplicated feature-map table is retired.
This entry retains the conceptual separation; the Site model and CODE_STATE
retain the built fields. Cite this decision instead of the removed Feature Area 1.

The "simulator tag" the product shows on a Lab-produced Site *is*
`source.mode = SIMULATED`. It is not a third field. No `created_in_lab`,
`is_simulator_site`, or equivalent flag exists or may be added, because such a
field records which shell created a Site, which nothing downstream consumes and
which would fork the identity seam.

Configuration origin (`SHIPPED` / `USER`) and source mode (`LIVE` / `SIMULATED`)
are orthogonal and neither may be derived from, defaulted from, or rendered as a
proxy for the other. Configuration origin describes the document and its store;
source mode describes where evidence comes from. Lifecycle status, integration
readiness, evidence availability, and source health remain separate from both
and from each other, as already recorded.

Nothing about "a normal Site with a simulator tag" changes the two-store model.
The shipped and user-authored configuration stores, their disjoint `site_id`
space, copy-on-instantiate, and template provenance are all untouched.

Reason: The user's phrase invites a natural but wrong reading, that being
Lab-produced is a new property of a Site. It is not; it is the existing Mode
concept, which v6.9 already fixes as "provenance, not status" and which the
project's vocabulary-separation seam already protects. Naming that explicitly
now is cheaper than discovering two fields that always agree.

The specific trap worth recording: in M1 the only creation path is the Lab's, so
every `USER`-origin Site also has `source.mode = SIMULATED`. The two coincide in
every row anyone will see this milestone, which is exactly the condition under
which someone collapses them or derives one from the other. They coincide by
circumstance, not by definition. A shipped demo Site would be `SHIPPED` plus
`SIMULATED`; a Site registered for a real integration would be `USER` plus
`LIVE`. Both are meaningful and neither is reachable in M1.

Affected scope: Site model fields, Sites index columns, Site Details and Site
Configuration provenance presentation, badge vocabulary, strict parser and
validation, the vocabulary-separation seam, and every later slice that reads
provenance.

## 2026-09-13

Decision: Before T006 implementation, the disabled-bundle concern is settled as
a runtime gate seam, not a bundle-content seam. A gate-off build must serve no
Lab route, action, API, create flow, simulator URL backdoor, or operator import
path into Lab internals; it does not need to prove that Lab modules are absent
from the frontend bundle.

Decision: The T006 created Site document is not the template document. The
template contributes only a deep-copied Foundation seed. The create flow
collects `site_id`, display name, location identity fields, and timezone. The
create service defaults origin, source mode, lifecycle status, template
provenance, and any initial Foundation version/validity fields required by the
strict parser. Topology, devices, mappings, control assumptions, evidence,
source health, operational status, SLD runtime fields, and simulator/run fields
do not exist in this slice.

Decision: T006 must update architecture guards deliberately rather than making
the T005 checks pass by accident. Adapter isolation and the storage-technology
ban remain, shipped configuration roots remain read-only, writes are allowed
only through the user-store adapter, the user store root has one owner and is
gitignored, and updated checks keep non-vacuity assertions.

Reason: T006 is the first untrusted-input write boundary. The task is still a
coherent vertical slice, but it needs these decisions recorded before
implementation so the write path is strict, the feature gate stays meaningful,
and the guard changes replace prior strength instead of weakening it.

Affected scope: T006 task planning, `.ai/FEATURE_MAP.md`, Simulator Lab gate
tests, Site record shape, user store adapter, architecture guard updates, and
future Site Details/Site Configuration slices.

## 2026-09-17

Decision: T006's shape-only IANA timezone validation stands for current Site
Foundation storage and display. Real IANA timezone membership validation becomes
mandatory before any scenario, SimulationRun window, replay window, evidence
window, scheduling behavior, or analytics bucketing consumes Site timezone as
executable behavior.

Reason: Timezone is currently identity/configuration metadata. Shape validation
keeps Site records coherent without making correctness depend on host-specific
timezone database availability, especially on Windows. Once timezone affects
execution semantics, a structurally plausible but nonexistent zone can distort
run timing, local-day boundaries, evidence windows, replay, and analytics. At
that point invalid zones must be rejected early and deterministically through an
explicit dependency or bundled timezone database.

Affected scope: Site validation, Scenario and SimulationRun planning, replay
and evidence-window semantics, analytics bucketing, future dependency choices,
and task gating before timezone becomes operational.

## 2026-09-17

Decision: Gateway/source health is a separate operational evidence signal
derived from source/gateway observations, heartbeat or arrival evidence, and
expected cadence. It is not derived from Site lifecycle status, from whether a
Site exists, from whether a Site is simulated, or from simulator/run provenance.
Until backed observations exist, Site Foundation and configuration-only screens
must render source health as unknown, not backed, or not recorded rather than as
healthy, online, offline, or stale.

Reason: Site lifecycle answers whether the configured Site is managed or active.
Gateway/source health answers whether AssetOps has recently heard from the
source that claims to represent the Site. Simulation provenance answers where
the evidence came from. Those truths can diverge: an active Site may have a
stale gateway, a simulated run may emit fresh staged observations without
proving any real source is healthy, and historical observations can exist for a
Site whose lifecycle later changes. Keeping the signal separate preserves an
audit path from health badges to observation metadata.

Affected scope: Configuration-only Site UI, future source/gateway health
derivation, ingestion and heartbeat evidence, vocabulary separation, Simulator
Lab provenance, Site lifecycle presentation, and operator monitoring screens.

## 2026-09-17

Decision: The Site Foundation frontend/backend fetch seam now requires a
focused integration test binding the real frontend API clients to
representative backend responses before the shared contract is materially
expanded. The test should cover the Site Foundation clients across the Site
list/detail read path, create success, validation refusal, empty state, and
not-found or store/error envelopes where practical. It does not need to be a
broad browser end-to-end test.

Reason: T006 through T008 created multiple user-visible surfaces over the same
transport contract. Backend tests and isolated frontend rendering tests do not
prove that the real client code understands the backend payload shape, status
codes, and error envelopes. Because the seam is shared, a small mismatch can
silently affect several screens. A focused integration test gives more
confidence than adding page-local tests after visual fidelity accumulates on
top of the same unverified assumption.

Affected scope: T010/T011 planning, frontend API clients, backend response
contracts, Site Foundation regression tests, review packets, and any future
slice that changes the shared Site Foundation frontend/backend contract.

## 2026-09-17

2026-09-24 supersession: the readiness names and sequencing in this entry are
historical. D-2026-09-24-v4-roadmap-replan and PRODUCT now distinguish internal
architecture, dispatch feedback and the full client demo; evidence isolation
still applies.

Decision: Client demo readiness begins at `Demo Ready v1: Simulated Evidence
Loop`, after a simulated Site can produce staged gateway/source envelopes,
release them through ingestion, show accepted/rejected records, populate
operator evidence views from accepted evidence only, and replay committed
accepted history with provenance. Business-outcome demo readiness begins at
`Demo Ready v2: Evidence-Backed Operational Findings`, after source/gateway
health and at least one bounded operational finding are derived from accepted
evidence.

Earlier milestones are valid product walkthroughs but not client-ready AssetOps
demos: M0 Site Foundation Fidelity, M1A Topology/Devices/Signals/SLD, M1B
Scenario Catalog/Run Setup, and M1C Prototype Walkthrough Recorded Runtime.

Reason: Before the simulated evidence loop exists, the product can show
configuration, visual fidelity, scenario setup, and simulator behavior, but not
the core AssetOps promise: evidence-backed operational inspection.
Business-outcome claims require an additional conclusion chain over accepted
evidence, with confidence, claim boundaries, and provenance.

Affected scope: Roadmap planning, task sequencing, demo language, Simulator
Lab, Source Envelope, release/ingestion, evidence views, Replay, source health,
operational findings, mini-grid demo readiness, and cold-chain follow-on
planning.

## 2026-09-17

Decision: The operator Site surface previously called `Site Configuration` is
the v6.9 `Foundation` tab named at lines 464, 615 and 2117. User-visible route text, breadcrumb, page heading,
tab label, and Site Details link text become `Foundation`. The canonical route
becomes `/sites/:siteId/foundation`; `/sites/:siteId/configuration` remains only
as a compatibility redirect that preserves `siteId` and is not surfaced,
tabbed, or counted as a navigation destination. Test names, guard messages and
guard-script comments use Foundation unless deliberately asserting the legacy
redirect or the parameterless `/site-configuration` ban. Internal component and
symbol names under `frontend/src/sites/**` may lag for the rename slice if
renaming them would be mechanical churn across the shared substrate; no
user-visible string or route constant may lag.

The operator Site tab set is v6.9's `Overview | Foundation | Health |
Performance | Findings | Work | Financials | Evidence` from lines 464 and 615.
`Overview` and `Foundation` are destination tabs because their identified
routes render truthful current surfaces. The remaining tabs are labelled in
place with no link, button, route, or disabled placeholder until their content
contracts exist. The `ScreenMockups.png` screen 2 tabs `Configuration`, `Devices`, `Gateway`,
`Ingestion`, `Events`, and `Logs` are not the operator Site tab vocabulary for
M1.

The Foundation subtab row uses v6.9 line 2117 as the source:
`Definition | Topology | Controls | Changes | Readiness`. `Definition`,
`Topology`, and `Controls` render with current M1 limits; `Readiness` is
labelled in place until evidence readiness has a source contract. `Changes` is
not rendered until a reviewed configuration-change capability exists, because
v6.9 lines 2149 and 2225-2228 make it a real intervention/change-effect
capability rather than a placeholder or `ScreenMockups.png` screen 3's `Version History`.

This supersedes the forward-looking parts of the 2026-09-13 canonical-fidelity
decision that named the operator Site tabs as `Configuration`, `Devices`,
`Gateway`, `Ingestion`, `Events`, and `Logs`, and the forward-looking parts of
the 2026-09-13 navigation decision that used `Site Configuration` as the
settled surface name. It does not rewrite those dated records. Their
historical facts still stand: canonical fidelity is staged only after content
exists, absent/labelled/disabled treatments remain distinct, parameterless
routes are not destinations, and navigation growth remains governed by
truthful routes.

Sequencing: insert a dedicated Foundation naming and operator Site tab
inventory slice after T011 and before the current T012. T009 remains
chrome-only; T010 and T011 continue in order with wording changes. The inserted
slice carries the user-visible rename, `/foundation` route, `/configuration`
redirect, operator Site tab inventory guard, route-compatibility tests, and
guard-script updates. T012 then dresses Site Details against the settled tab
row, T013 dresses Foundation against the settled name and filtered subtab row,
and T014-T016 remain coherent only after their wording and structure are
updated to render into Foundation.

Guard replacement is replace-never-loosen. The frozen operator-navigation count
may remain during Site Foundation because the operator rail still does not
grow. When a rail or tab set changes, the replacement guard is a single
inventory definition consumed by rendering and tests: every rendered item must
be in the inventory, every destination item must have a real route, labelled
items must not be links/buttons/routes, gated Lab rail items must be absent
when the gate is off, and no unexpected item may render. This is stronger than
a count freeze because it checks identity, route truthfulness, and absence of
extra items rather than only a number.

Reason: v6.9 lines 464, 615 and 2117 are the operator Site vocabulary authority
where they disagree with `ScreenMockups.png` screens 2 and 3, and the accepted T008 checkpoint already settled that this surface
is the read-only Foundation/configuration presentation rather than an editable
configuration workflow. Carrying the old screen name into the canonical tab row
would leave users with two names for one surface, make the `ScreenMockups.png`
screen 2 run-tab vocabulary look like operator navigation, and weaken the audit trail around
why `Changes` and `Version History` are absent. A compatibility redirect keeps
existing addresses from breaking while preserving navigation truthfulness: the
product has one Foundation destination, not two configuration surfaces.

Affected scope: Foundation route and redirect, Site Details link, breadcrumb,
heading and tab labels, operator Site tab row, Foundation subtab row, planned
T009-T016 task wording and sequencing, navigation truthfulness guard,
architecture guard messages, frontend tests, shared Site substrate naming
cleanup, and future Planner rewrites of uncompleted task files.

Amended by `D-2026-10-02-rendered-tabs-per-capability`: Site tabs and
Foundation > Readiness are no longer labelled in place; tabs render per
capability. The rest of this entry stands.

## 2026-09-20

Decision: `tools/layout-evidence.mjs` becomes standing closeout evidence for
layout-sensitive slices, owned by the Implementer and checked by the Reviewer
from the review packet. It stays out of `tools/check-architecture.ps1`.

A slice is layout-sensitive when it changes shell layout, dense tables,
intrinsic-width drawings, SVG geometry, tab or subtab treatment, or viewport
behaviour. Such a slice names layout evidence in its checks, and its packet
carries the exact command, the base URL when non-default, and the final result
line. A packet that omits it, or records a skipped run as a pass, is a review
finding.

A missing precondition is not a pass. When Chrome, the backend or the dev
server is unavailable, the closeout records `layout evidence: not run` with the
blocking precondition, and the Reviewer treats the affected layout claim as
unverified.

Every new measured claim about overflow, visibility or rendered content must
include at least one measurement proving its set is non-empty, generalising the
640px measurement that exposed T014's dense-table claim passing on an empty
set.

Reason: the tool has found defects no suite on this project can see - T011B's
original shell overflow defect, T014's empty-set dense-table claim, and T016's
connection routed through a component, SVG text leaving its box, and a label
colliding with the name it marks. That is too much signal to leave ad hoc. But
it needs a browser, the backend and a dev server, while the architecture runner
protects seams that must hold anywhere and fails any unwired module. Putting it
in that runner would either make the portable runner non-portable or introduce
skips, and a skipped protection that reports success is the exact failure shape
this project keeps finding.

Affected scope: `.ai/WORKFLOW.md` closeout and review packet, the Implementer
and Reviewer standing briefs, task checks for layout-sensitive slices, and
review packets. No change to `tools/check-architecture.ps1` or its manifest.

## 2026-09-20

Decision: no guard is added to tie a merged slice's task status to its branch
state. Closeout discipline stays manual: before a merge, the Review Outcome is
recorded and the task status is set to complete or explicitly left open.

Reason: branch state is the wrong authority. Branches are deleted, rebased and
renamed, and a fast-forward merge leaves none at all, so a guard built on
`git branch --merged main` would miss normal workflows and overfit the one
failure already seen. `tasks/` is also empty, so a guard written now would
assert over no members - the seventh instance of the family this project keeps
shipping rather than a defence against it. The process-creep rule wants a
second occurrence or an explicit ask, and the user asked for a recommendation
rather than for the guard.

If the drift recurs, the shape to build reads task files rather than branches:
each active task carries a stable id and status, completed work moves to
`tasks/completed/` with `Status: complete` and a Review Outcome before closeout,
and a checked-in deliberately-incomplete sample task proves the guard can fail.
Without that fail-case anchor it would join the dead patterns, the unreachable
caps and the type contract no runtime test could falsify.

Affected scope: `.ai/WORKFLOW.md` closeout, the Implementer and Reviewer
standing briefs. No new tool, no change to `tools/check-agent-workflow.ps1`.

## 2026-09-20

Decision: a breaker is both a topology element and, when the site has
instrumentation for it, something a device may report about - but never both in
one record. Its position is evidence, not Foundation configuration. M1 carries
nothing beyond the declared control assumptions T014 already carries: identity,
name, optional component reference, provenance, and a statement in words.

This keeps two product claims apart:

- "This site is wired with a controllable or protective element between these
  topology nodes" - configuration and topology.
- "This breaker was open, closed, tripped, automatic or manual at this time" -
  evidence.

So `OPEN`, `CLOSED`, `TRIPPED`, `AUTO` and `MANUAL` are not Foundation schema
vocabulary, and `BREAKER` is not a Foundation `DEVICE_TYPE`. The eventual model
separates four things: a topology declaration for where the breaker is; device
and signal mappings for what can report about it; evidence records for what was
observed and when; and declared control policy or assumption for what operation
is intended, in words for M1.

T014's `frozenset` scan in
`backend/tests/test_foundation_content_parsing.py` is kept, not narrowed and not
retired, with its rationale rewritten to this decision. Retiring it would let a
later Foundation change smuggle position vocabulary into configuration before
the evidence model exists. Narrowing it to position words alone would admit
`BREAKER` as a device type and so answer half the question early. It narrows
only when a reviewed slice adds the explicit topology/evidence separation and
tests that position cannot be stored as configuration.

Reason: v6.9 gives the Simulator Lab a truthful runtime breaker state, with
loads and sources connected to the AC bus through named breakers and a legend
carrying breaker open/closed, because the simulator owns physical truth. Where
it gives Foundation control policy it defines no breaker-position schema, no
AssetOps control-state vocabulary, and no rule that configured policy equals
observed state. That silence is the finding: this seam is ours to decide, and
the causal chain the product already commits to - physical/control state
transition, device observation, gateway, source envelopes, AssetOps evidence -
puts position on the evidence side of it.

Carrying nothing more in M1 is the positive answer rather than a deferral. M1
has no evidence object, controller record, runtime overlay or breaker component
model that could truthfully hold a position. Adding the vocabulary now would
unlock no UI-verifiable value; it would teach the product to state an operating
condition without the evidence path that makes such a statement legitimate. A
screen could show a breaker open because a YAML field said so, which collapses
the simulator-truth and AssetOps-evidence boundary and makes Foundation look
like a live operations model.

Left open deliberately, for the first slice that renders or stores a breaker
state, because that slice will have the evidence contract in front of it:
whether canonical topology names breakers as components, connection equipment,
connection attributes or a distinct inline element; the accepted-evidence
vocabulary for positions and control modes; whether `tripped` is a position, an
event, a protection outcome or several of those in different records; and the
symbol set for breaker drawings. Eventually the SLD draws a breaker as an inline
topology element and may overlay an evidence-backed position on it, with
simulator runtime truth and accepted evidence staying separate overlays as
T015's slots already keep them.

Affected scope: `.ai/FEATURE_MAP.md` section 2 semantics, the `frozenset` scan's
rationale and failure message, and any future slice touching breakers, control
policy, or the Foundation control vocabulary. No schema field, model, route, or
rendered surface changes now; T014's `ControlAssumption`, T015's typed empty
slots and T016's presentation all stand as shipped.

## 2026-09-20

Decision: `ScenarioDefinition` is the saved, versioned scenario artifact for
M1B. It has scenario identity, version identity, display metadata, target-site
requirement, public timeline, public parameters, and private expectations in
separate parsed fields. `ScenarioTemplate`, if introduced later, is a reusable
recipe in a separate identity space; it is not executable by itself and does not
live-update existing definitions.

`ScenarioEvent`, authored `Intervention`, and `EvidenceCondition` are ordered
authored items inside a `ScenarioDefinition` version. They are saved
sub-artifacts because they persist inside the definition document, but they are
not top-level stored entities in M1B. Their address is
`(scenario_id, scenario_version, event_id)`. `PrivateExpectation` is
test-oracle metadata only: it is not pipeline input, public authoring data,
product evidence, operator UI, or product provenance.

The exact scenario versioning fields stay provisional until the T017 user
review checkpoint. The invariants are settled now: identity and version are
distinct; a version referenced by a run is immutable; timeline identities are
stable within a version; a future run freezes the concrete scenario version it
used and never follows latest.

Reason: A Fuel Loss Event timeline row has no useful lifecycle without the
scenario's target requirement, interval defaults, seed, public/private boundary,
evidence visibility model, and version identity. Making events a repository
root now would introduce reuse, deletion, lookup, and compatibility semantics
that M1B cannot verify. Keeping templates separate follows the Site
Template/Site distinction and prevents recipe changes from rewriting saved
definitions.

Affected scope: Scenario domain model, scenario parser, Scenario catalog and
detail payloads, future run setup, private expectation isolation, T017
checkpoint content, and T018/T019 task sequencing.

## 2026-09-20

Decision: `ScenarioDefinition` storage uses strict canonical YAML behind a
`ScenarioDefinitionRepository`-style domain port. The shipped Fuel Loss Event is
a read-only tracked definition at `config/scenarios/fuel-loss-event.yaml`, and
writable user or project definitions live under gitignored `var/scenarios/`.
Both roots compose into one repository with one globally unique `scenario_id`
space. Duplicate identities, including case variants, are configuration
conflicts within a store or across stores; there is no overlay and no
precedence.

The port speaks domain records and scenario-domain errors only: not found,
identity conflict, configuration invalid, and store unavailable. YAML, paths,
file handles, parser exceptions, duplicate-file checks, filesystem errors, and
store availability translation stay inside adapters and the composition root.

Reason: T017 has no scenario creation flow, so a fresh checkout needs a tracked
read-only scenario definition for the catalog to show. That is parallel to
shipped configured instances, not to reusable templates. The writable store
still exists because later authoring needs a place to persist user definitions,
but identity must remain disjoint from the beginning or run history will not
have a stable scenario anchor.

Affected scope: Scenario storage layout, scenario repository port, composition
root, strict parser and adapter tests, first-run catalog behavior, future
scenario authoring, and future migration away from file-backed storage.

## 2026-09-20

Decision: Future event injection is modeled as run-scoped
`InjectedRunEvent` / intervention-history records under `SimulationRun`
identity, not as authored `ScenarioEvent` rows and not as top-level scenario
artifacts. Runtime injections are addressed by a run-scoped family such as
`(run_id, injected_event_id)` or `(run_id, intervention_sequence)`. They are
never written back into the selected scenario version, never create an implicit
scenario version, and never become inherited by another run.

Reason: Authored scenario events exist before a run and define reusable
scenario content. Injected events are accepted during one run as deterministic
runtime input. Committed replay needs to save them, but under the run's ordered
intervention history so two runs can start from the same scenario version and
diverge only by run-scoped inputs. Promotion of a useful injection sequence into
authored scenario content is a future authoring capability with explicit UI and
review, not an automatic runtime side effect.

Affected scope: Scenario timeline model, SimulationRun runtime model,
intervention logs, deterministic replay, quick actions, event-log presentation,
and T020+ task planning. M1B names the seam but implements no injection models,
storage, APIs, or controls.

## 2026-09-20

Decision: On the T017 scenario detail screen, a disabled control appears only
when the action is native to the viewed `ScenarioDefinition` and the missing
prerequisite is the next named causal capability. `Run` / `Create Draft Run` is
rendered disabled with visible reason text naming the missing run setup / Draft
`SimulationRun` prerequisite. `Open target Site` is the only product bridge: it
is enabled only when the declared target Site resolves, otherwise absent or
disabled with an accessible reason.

Amended 2026-10-01: `Open target Site` is removed by
`D-2026-10-01-run-binds-scenario-to-site`; a scenario names no site.

`Commit`, `Open in AssetOps`, runtime controls, gateway output, ingestion,
Replay, Findings, and product analytics are absent from the scenario detail
screen because they belong to `SimulationRun`, ingestion, Replay, or operator
evidence/product surfaces rather than to `ScenarioDefinition`.

Reason: This is a precise application of
`D-2026-09-13-canonical-fidelity`, not an amendment to it. Disabled means "this
action belongs to the object you are viewing, but the current record or
milestone lacks the named prerequisite to perform it." Controls from another
root object or downstream lifecycle teach the wrong object model when shown as
disabled placeholders.

Affected scope: Scenario detail screen actions, accessibility reason text,
mockup-fidelity tests, run setup sequencing, and future control placement on
SimulationRun, ingestion, Replay, and operator evidence surfaces.

## 2026-09-21

Decision: the T017 user-review checkpoint settles the three scenario authoring
semantics M1B was blocked on. All three were accepted as proposed.

A scenario version carries `scenario_id`, `scenario_version`,
`version_valid_from` and `supersedes`.

The event taxonomy is three timeline entry kinds - `EVENT`, `INTERVENTION`,
`EVIDENCE_CONDITION` - and seven categories: `LOAD`, `WEATHER`, `EQUIPMENT`,
`DATA_QUALITY`, `LOSS_OR_FRAUD`, `INTERVENTION`, `MAINTENANCE`. Breaker
position and control mode are excluded by construction, and the vocabulary ban
now reaches identifier-valued schema positions so they cannot arrive as a
`parameter_id` either.

Public authoring parameters may inform future run setup and runtime behaviour.
Private expectations - `DETECTION`, `MAGNITUDE`, `TIMING`, `NO_FALSE_POSITIVE`
- are test-oracle metadata only. The boundary is a parsed-field separation with
separate payload builders, not a presentation choice, and private expectations
never reach product evidence, source envelopes, operator UI, exports or
provenance.

Reason: unlike the M1A checkpoint, each question carried a proposal on screen,
marked provisional, stating what accepting adopts and what redirecting would
mean. The user's verdict was "looks good", so accepting the screen was a
decision rather than ratification of a menu. M1A's breaker question was
presented with candidates the project had considered and not chosen and no
proposal, settled nothing, and had to go to an Architect afterwards; T017 was
planned specifically not to repeat that.

The values are settled. The on-screen provisional marking and the `provisional`
wording on `SCENARIO_VERSION_FIELDS`, `TIMELINE_ENTRY_KINDS` and
`EVENT_CATEGORIES` are not yet removed. Removing them, and the review regions
with them, is a visible product change and belongs to a slice that says so -
the same treatment T016's cold-room marker was given.

Affected scope: `.ai/FEATURE_MAP.md` section 3, T018 and T019 planning, the
scenario domain vocabularies, the scenario detail screen's review regions, and
any future slice that authors, versions, or runs a scenario.

## 2026-09-21

Decision: a minimal executable deterministic causal runtime kernel must precede
any state trace treated as authoritative simulator output. This supersedes
`D-2026-09-11`'s first-execution-mode decision that a recorded-run player would
act as the initial state producer and later be replaced by the real runtime.
The stable clock/state/event, device, gateway, ingestion, and UI seams from that
decision remain required.

`ScenarioDefinition` authors causes and conditions in time, not their resulting
state trajectory. Site Foundation, frozen run inputs, explicit initialization
inputs, and versioned simulator rules initialize private world state. The
runtime applies due events exactly once through an initialization/step contract
and computes subsequent state. For the Fuel Loss Event, the first kernel must
at least resolve the configured tank, account for declared initial fuel,
generator consumption, removal, and delivery inputs, enforce declared bounds,
and make changes to event quantity or timing produce corresponding changes in
the state trajectory.

A state trace may be retained only as a golden trace or playback fixture: it is
generated reproducibly by a named simulator version from a frozen deterministic
identity and used for regression, UI, clock, binding, or downstream contract
proof. A manually authored trace can be schema-valid and internally consistent
while still being causally circular, so it cannot certify simulation. Schema
validation, invariant/consistency validation, and causal correctness are
separate proof obligations. Causal proof requires executable transition rules
plus independent examples, boundary cases, and metamorphic checks such as
removing, retiming, or resizing an event and observing only the corresponding
consequence change.

Runtime provenance binds each result or golden trace to the exact Site and
Foundation version, scenario version and resolved public parameters, interval,
timestep, seed, simulator version, explicit initialization inputs, mappings,
and ordered intervention history. A mismatch refuses playback; it never falls
back to a trace produced for different inputs.

Reason: a fixture written to agree with a scenario proves only agreement
between two authored artifacts. Without an independently executable causal
rule it cannot show that the scenario influenced world state. A narrow real
kernel costs less than carrying that false claim through device, gateway, and
evidence work, and lets later physical realism deepen the producer without
redesigning downstream contracts.

Affected scope: M1B run-setup semantics, T018/T019 planning, M1C task sequence,
runtime initialization and step contracts, event-time semantics, trace
provenance, simulator tests, Simulator Lab claims, and golden-trace use.

## 2026-09-21

Decision: `D-2026-09-21-scenario-execution-contract`. The T018 checkpoint
settles what an authored scenario value means to an executor. The user
reviewed the Fuel Loss Event screen and accepted all four proposals.

**Execution roles: accepted as proposed.** Every public parameter and every
timeline entry carries one machine-readable execution role - `CAUSAL_INPUT`,
`FORCING_INPUT`, `REPORTED_OBSERVATION`, `NON_EXECUTABLE_CONDITION` - on an
axis orthogonal to the T017 entry kinds and categories, which are unchanged.
Only a causal input may reach initialization or a private-state transition,
and that is enforced at two independent layers rather than asserted. A
forcing input names the state it forces and is binding on a later kernel, but
may not declare a starting value: an exogenous state's value at every instant
comes from its profile, including the first, so an initial value beside it
would be a second answer to one question. A reported observation carries no
ownership and no state effect, so there is no field it could arrive in.

**Initialization and cadence ownership: accepted as proposed.** Every initial
world value has exactly one owner - Site Foundation, the scenario, a run
override, or a versioned model rule - and two owners for one value is refused
when the definition is read. The scenario owns no cadence. Foundation declares
that a signal can report and declares its unit, and declares no rate; nothing
derives a cadence from a device name, from displayed text, or from the spacing
between rows. A cadence arrives when a versioned observation profile declares
one. The prohibition is closed at the unit vocabulary rather than per
position: a duration has no authoring unit, so there is no position it can
occupy. A hand-recorded value is a real source with its own identity and no
device identity.

**Timing and bounds: accepted as proposed.** An entry is an instant, a window
with a declared length, or the whole interval, validated as three distinct
shapes; a rate may only be declared over a window. The run interval and every
step are half-open, so a boundary entry is applied by the step that begins
there and by no other, making "applied exactly once" a property of the time
model. Every bound case either refuses the definition, fails the run, or
produces a bounded change recorded with the quantity it refused. There is
deliberately no option meaning clamp quietly or drop the remainder.

**An unreached reading is stated, not resolved: accepted as proposed.** The
Fuel Loss declared causes reach 254 L where the sensor reports 155 L and the
operator records 150 L. Both readings are reported observations from a named
source, so neither prescribes tank state and the contract is coherent; what
the contract must also do is say out loud that its declared causes do not
reach either, with quantity and sign. The residual stands at -99 L and -104 L,
`NOT_ACCOUNTED_FOR`. The three honest ways out - model the missing cause,
declare a reporting behaviour that explains the difference, or accept the
readings and change the causes - remain open and are the user's to choose in a
later slice. Until one is chosen, later run setup treats an unreached reading
as a reason to block rather than as a rounding matter.

Reason: run setup cannot freeze honest inputs while a timeline row can
ambiguously prescribe both a cause and its expected result. Classifying the
values resolves that without editing any authored number, which would have
settled a product question by arithmetic rather than by review.

Affected scope: T019 Draft run setup and its `BLOCKED` computation, T021's
kernel and its initialization/step contract, T022's device observations, the
scenario parser vocabularies and payloads, and any later slice that resolves
the Fuel Loss residual.

Amended by `D-2026-09-21-scenario-execution-contract-amendment-1`, which
withdraws the closing clause about run setup blocking on an unreached reading.

## 2026-09-21

Decision: `D-2026-09-21-scenario-execution-contract-amendment-1`. Amendment 1
to `D-2026-09-21-scenario-execution-contract`. Six changes, accepted by the
user on 2026-09-21 after reading
`Docs/simulator-scenario-authoring-and-runtime.md`, which carries the full
reasoning and is committed alongside this entry. The original decision keeps
its ID and its unamended text; this entry is what it means where the two
differ. The bracketed letters are the labels that document uses.

**(c) Simultaneous causes are a group with a net effect, not a sequence.** The
original decision fixed half-open dispatch and exactly-once application but
left within-instant ordering unspecified, so two conforming kernels could
legitimately disagree at that instant. Transitions on one state completing at
the same offset now form a group with a net effect, and bounds are evaluated on
the group's net rather than between its members. Order-dependence is decided
exactly: apply all increases first to test the upper bound, all decreases first
to test the lower. If neither extreme breaches, no ordering breaches, the net
is unambiguous, and the contract answers. If one extreme breaches and the other
does not, the group is genuinely order-dependent and the contract abstains with
its own reason, saying the scenario must separate the offsets if it wants order
to decide. Order is expressed as time, never as position in a document.

A first draft of this rule declared authored `sequence` order and was reversed
inside T019 before independent review. Authored order is not physics,
serialising simultaneous causes abstains on a level the state is never in, and
declaring it would have obliged T021's kernel to serialise sub-steps inside one
instant, removing the metamorphic invariant
`D-2026-09-21-causal-runtime-before-golden-traces` asks for. Already
implemented on `task/T019-draft-run-setup` as a `DISPATCH_RULES` entry.

**(d) `EXECUTION_CONTRACT_VERSION` moves when the space of conforming
behaviours changes, including when it narrows, and never for wording.** Pinning
a previously unspecified semantic narrows the space and moves the number; a
prose edit does not. The number identifies the space, not the text. (c) moved
it from 1 to 2 because it pinned an instant the first version left open, and
rewriting (c)'s content inside the same slice did not move it again, because
both drafts narrow the same space and no implementation ever conformed to the
first draft. The policy matters because
`D-2026-09-21-causal-runtime-before-golden-traces` makes a provenance mismatch
refuse playback, so a version that moved for prose would force regeneration of
valid golden traces. Already implemented on `task/T019-draft-run-setup`.

**(e) Run setup does not adjudicate cause-to-observation coupling.** This
withdraws the original decision's closing clause, "later run setup treats an
unreached reading as a reason to block rather than as a rounding matter."
Deciding whether declared causes reach a declared reading requires composing
those causes into a value at a time, which is a transition rule, and whatever
owns a transition rule is a kernel. Run setup has no kernel, so the verdict was
never run setup's to reach. `OBSERVATION_NOT_ACCOUNTED_FOR` therefore leaves
the blocking-reason vocabulary and the observation reasons leave the run-setup
service.

The rest of the original fourth proposal stands. Both readings are still
reported observations from a named source, neither prescribes tank state, and
the residual is still real. What changes is where it is stated. Reconciliation
found a genuine defect in the document, and it was wrong only about where it
stood to look: a disagreement between an author's expectation and computed
behaviour is a test failure, not a property of a run that has not happened.
Lands in T019 before merge.

**(f) A scenario does not author what a device reads.** The original decision
left three ways out of the residual open. This takes the third and narrows it.
The authored 155 L at offset 1590 and 150 L at offset 1800 are removed. What a
run reports is generated by the observation transform from private state, at
the cadence the frozen publication profile declares, perturbed only by declared
reporting-path forcings. The 155 L value was a hand-simulation of exactly the
sample the transform will generate at 1590, and it was wrong by 99 L.

The `REPORTED_OBSERVATION` role survives unchanged and becomes more necessary,
not less: it is precisely what stops an authored reading reaching a transition.
Its meaning sharpens from "a value the contract checks the causes against" to
"an expectation about what a run should produce, which no executable path may
read." The entry at 1590 survives as an evidence condition asserting that a
reading arrives there and is materially below what dispatch accounts for; the
operator's inspection at 1800 keeps the act and loses the number. Lands in
T022, and the replacement numbers are derived during T021 from what the kernel
computes rather than chosen before it.

**(g) `execution_requirement` is forbidden on a `REPORTED_OBSERVATION`.**
Closed structurally at the parser, the way the original decision closed
duration units: there is no position the field can occupy, rather than a rule
someone has to remember. With (e) in place, `REQUIRED` on a value no executor
reads is either vacuous or a category error, and the meaning it was carrying,
"this run must produce such a reading", already has a home in the private
expectations under `DETECTION` and `TIMING`. This narrows the space of
conforming behaviours, so `EXECUTION_CONTRACT_VERSION` moves by one under (d).
(This read "2 to 3" as written, and two later narrowings now land before it;
the count is in `.ai/FEATURE_MAP.md` under *The execution-contract version
ledger*.)
It is free now and will not be once a golden trace exists. The user placed it
in its own slice, **T021A**, on 2026-09-22: T022 is the slice that first
produces a golden trace, so burying the version move inside it would make that
slice's internal ordering load-bearing and would close the free window if T022
were ever split. It sits after T021 because the kernel never reads
`execution_requirement` on a reported observation.

**(i) A fifth oracle kind, `TRAJECTORY`.** The four accepted oracle kinds are
all about analysis outcomes. None is about world trajectory, so the author's
most immediate and most confident expectation, what the tank does, had nowhere
falsifiable to go and ended up as a `REPORTED_OBSERVATION` value, which is a
load-bearing position. A `TRAJECTORY` oracle asserts a private-state value at
an offset, is checked by the kernel in tests, and is never published and never
read by any executable path.

It is not a manually authored trace under another name. A trace as input is
read and reported as the state, so being wrong causes agreement; an oracle is
compared against an independently computed value, so being wrong causes a
failure. Two guards keep it on the right side of that line. It must be sparse
and purposeful, one or two points the scenario is about, because a dense set is
a trace in the oracle position and fits the kernel to the author's arithmetic.
And it must be stated as weak proof: if the author and the kernel perform the
same arithmetic and agree, what is proven is that two implementations agree,
which catches unit, dispatch and half-open errors and does not prove the
physics. It is a regression guard, not a correctness proof. Lands in T021,
which is what can check it. Without it, (f) deletes the author's expectation
instead of relocating it.

Reason: five of the six changes withdraw or narrow a claim the contract was
making without the machinery to back it, and the sixth gives the withdrawn
expectation a position where being wrong causes a failure. The rule underneath
all of them, and the reason they are one amendment rather than six: an
expectation is legitimate when it occupies a position where being wrong causes
a failure, and circular when it occupies a position where being wrong causes
agreement.

Affected scope: `backend/assetops_backend/scenarios/execution.py` dispatch
rules and the contract-version constant, `runs/service.py` blocking reasons,
`runs/models.py` blocking vocabulary, the parser rule for
`execution_requirement`, `EXPECTATION_KINDS`,
`config/scenarios/fuel-loss-event.yaml`, the scenario detail screen's
reconciliation panel, T019's narrowing before merge, T021's oracle check and
document correction, and T022's observation transform.

## 2026-09-21

Decision: `D-2026-09-21-run-setup-outcome-vocabulary`. The T019 checkpoint
settles what a run-setup outcome asserts and when the Fuel Loss residual is
due. Accepted by the user on 2026-09-21. The first two parts were taken at the
checkpoint itself and had until now been recorded only in a local handoff note;
the third comes from the Architect read that followed.

**(a) `BLOCKED` is the shipped run-setup outcome.** Setting up a run for the
shipped Fuel Loss Event against the shipped `minimal-fuel-tank` model profile
produces a persisted Draft that cannot execute. That is accepted as correct
behaviour rather than treated as a defect to design around: a structurally
valid, fully frozen request whose executable inputs the selected profile cannot
consume is inspectable history, not a refusal. Under amendment 1's (e) the
count drops from five reasons to three, all `STATE_NOT_SUPPORTED`, for
`site-load-demand`, `plane-of-array-irradiance` and
`fuel-level-reporting-availability`. The outcome does not change; only the
reason count does. `READY` remains unreachable for the shipped document in this
build and is proved against fixtures. T019 does not widen the shipped model
profile and does not resolve the residual.

**(b) The residual is a scheduled decision, and it splits.** The checkpoint
treated it as one decision with two halves, both due before T021's task file.
It is now two decisions with different deadlines, because (e) moved one of them
out of run setup.

- The `REQUIRED` forcing states the first kernel does not model stay due
  **before T021's task file is written**, because they decide what the first
  kernel must model. Either the scenario lowers their requirement level, or the
  model profile grows to model them, or the authority for the reporting-path
  one moves to the publication profile. If `dispatched-output` is promoted to a
  forcing input, it joins this list. Deadline unchanged.
- The two unreached readings stop being a run-setup blocker under (e) and
  become a scenario-authoring question, due **before T022** and answered
  **during T021** from what the kernel computes. The right removal magnitude
  depends on what the kernel computes and on what the product can recover from
  published evidence, so deciding the number first and then building the kernel
  would fit the kernel to an authored expectation.

**(l) `READY` discloses what it does not assert, and T021 verifies it.**
`ModelProfile.supported_states` is a hand-written tuple that nothing checks
against a kernel, because no kernel exists. `READY` therefore means every
required executable input names a state that appears in that tuple with a
matching role, and every frozen value resolved. It does not mean the model can
execute them. If the shipped profile claims a state the eventual kernel does
not implement, the Draft is `READY` anyway, and being wrong causes agreement.

The remedy is disclosure now and structural closure later, not a rename. T020
states on the run record and on screen what `READY` does not assert. T021 adds
a conformance test asserting that the shipped profile's supported set equals
the set of states the kernel actually implements, derived from the kernel
rather than hand-maintained, which is the treatment this project already gives
the cadence and duration-unit prohibitions. The word becomes correct when that
test lands, and renaming it would ripple through the API payload, the
frontend, the tests and T020's screens to fix a word that is about to become
true. The disclosure becomes false at the same moment, so **T021 retires it in
the slice that lands the conformance test**, under
`D-2026-09-22-expiry-follows-the-condition`; this entry originally left the
retirement to an unnamed later slice and nothing owned it.

This is deliberately not treated the way `RUNNING` was. `RUNNING` could never
be reached in this build, so it was pure fiction and deletion was the only
honest move. `READY` is reached and does assert something true, just less than
its name suggests. Absence and overstatement warrant different remedies.

**Extended 2026-09-22 at the T019 user review: the refusal line moved.** The
user accepted the reviewer's principle and chose to align T019 to T020A rather
than the reverse. The discriminator is **who failed to answer**:

> The scenario's **declared owner** has no answer -> **refuse**, because no
> profile helps.
> The **selected profile** cannot answer -> **block**, because a different
> profile fixes it and the person gets a persisted Draft to inspect.

**Four cases moved from refusal to blocking.** A profile declaring no
`foundation_binding`; a binding matching nothing; a binding matching more than
one thing; and a binding whose unit is not the scenario's. What decides them:
a Foundation's answer is only locatable *through* the selected profile's
binding, so failing to locate it is a joint fact about the pair, and the
profile is the half a person can change on the setup form.

**A Foundation that declares no such property at all is not one of the four.**
There the declared owner itself has no answer, no binding reaches a value that
is not there, and no profile on the form would help, so it refuses. That is
the case that governs T020A's template-copy consequence, and the two must not
be collapsed: *the profile's binding could not locate an answer* blocks, *the
declared owner has no answer to locate* refuses.

> **Superseded 2026-09-22 by `D-2026-09-22-foundation-property-absent-blocks`:
> that case blocks.** This paragraph was the one part of this extension the
> code did not implement, and the discriminator above does not support it.
> `_resolve_foundation_value` reaches a refusal down one path only,
> `rating.value != declared`; every not-found blocks. For the refusal to have
> held, run setup would have had to establish that the declared owner has no
> answer without going through the profile's binding, and this entry says a
> Foundation's answer is locatable only through that binding - which after
> T020A names the property as well as the component type, so a different
> profile naming a different property may find something the Foundation does
> declare. Nothing else in this extension changes: the four blocking cases,
> the absent value on `FrozenInitializationInput` and the three invariants
> stand, and so does the structural argument for the contradiction refusal,
> whose case `D-2026-09-22-foundation-value-declaration` removes the ability
> to author at all.

**`FrozenInitializationInput` gained an absent case.** `value` and
`canonical_value` are nullable and absent together; the unit is not, because
the scenario declares it whether or not anything answers. The invariants live
on the record rather than in the service, because the service cannot produce a
violation and a hand-edited document can: a run is `READY` exactly when it
carries no blocking reason, **a `READY` run may not carry an absent value**,
and **every unresolved state must be named by a blocking reason's subject** -
the same state, not merely some reason somewhere on the same run.

**The new blocking kind is `INITIAL_VALUE_NOT_RESOLVED`.** It is named for the
state the value is left in rather than for the cause, so one name carries all
four cases, and **T020A reuses it for its `MODEL_RULE` carrier case** rather
than introducing a second kind for the same fact.

**The contradiction stays a refusal, for a structural reason worth carrying
into the record.** Foundation and scenario both answer and disagree. Every
blocking case leaves the value with **no** answer, which the frozen identity
can represent as absent; a contradiction leaves it with **two**, which the
identity has no shape for at all. A blocked Draft would have to freeze one of
the two numbers, and choosing one is the thing refusing exists to prevent.
This is not a judgement about which failure is easier to fix - the earlier
version of that argument, that a profile finding another matching component
would be shopping for a value, falls to a site declaring a second matching
component whose rating happens to equal the scenario's, and is kept only as
the intuition.

**So the contradiction is its own refusal kind,**
**`INITIAL_VALUE_ANSWERS_DISAGREE`,** split out of
`INITIALIZATION_INPUT_MISSING`, which now covers only a declared owner that did
not answer. Sharing one kind made it wrong about the case it mostly covered and
left it one word from the blocking `INITIAL_VALUE_NOT_RESOLVED` with nothing in
either name saying which side of the line it was on. The new name is the mirror of the blocking side - a run can
carry "no answer" and cannot carry "answers disagree" - so the vocabulary
carries the structural fact instead of a comment.

Reason: a persisted `BLOCKED` Draft is the honest product of a run setup that
can freeze everything and execute nothing, and it is more useful than a refusal
because it can be inspected. The residual split follows from where each half
can actually be answered. And an execution status is the one place in this
build that makes a claim about executability, so what it does not claim has to
be said in the same place.

Affected scope: T019's blocking-reason set and its fixtures, T020's run-detail
disclosure and Runs inventory language, T021's task file scope and its
`supported_states` conformance test, T022's ability to execute the shipped
scenario, `runs/profiles.py`, and the shipped Fuel Loss document. The 2026-09-22
extension adds `runs/refusals.py`, `runs/models.py`'s blocking vocabulary and
`FrozenInitializationInput`, `runs/service.py`'s freeze and blocking split,
T020A's model-rule carrier and its consequence prose, and the naming rule in
`.ai/ARCHITECTURE.md`.

## 2026-09-21

Decision: `D-2026-09-21-projection-versus-composition`. Projecting a document
is static validation. Composing projections into a value-at-a-time is a kernel.
A component that owns a transition rule is a kernel regardless of what it is
called, how narrow it is, or whether it emits a trajectory.

This is the general form of
`D-2026-09-21-causal-runtime-before-golden-traces` with one word changed. That
decision says a kernel precedes any authoritative trace; this one says a kernel
precedes any verdict that depends on composing causes. It is recorded as a
durable rule in `.ai/ARCHITECTURE.md` under Causal Runtime Authority.

Reason: the rule is what distinguishes the parts of T018's execution contract
that are sound from the part amendment 1 withdraws. `declared_bounds` reports
what a document declares and evolves nothing, so it is a projection and it
stays. The bound walk inside `reconcile_reported_observations` applies bounds to
a running value, which is a transition rule, so it was a kernel living in the
validation layer under another name. Without a stated rule that distinction has
to be rediscovered every time a validator is asked one more question, and three
review rounds on reconciliation is what rediscovering it costs.

The rule also names a live instance that predates it and is not yet fixed.
`IMPLICIT_LOWER_BOUND_DIMENSIONS` in `scenarios/execution.py` gives every
volume state a lower bound of zero whether or not the document declares one.
The asserted fact is true, but "volume is non-negative" is a model rule, not a
projection of the document, and the validation layer is injecting it. Where it
belongs is settled by `D-2026-09-21-physical-property-ownership`; when it moves
is not yet scheduled.

Affected scope: `.ai/ARCHITECTURE.md`, the scenario execution/validation layer,
run setup's blocking computation, T021's kernel boundary, and any future
component asked to decide something about a document by composing its
declarations.

## 2026-09-21

Decision: `D-2026-09-21-specification-reference-implementation`. A
specification's reference implementation belongs in the test suite, explicitly
labelled as a reference implementation and carrying a stated expiry. It does
not belong in the product path.

`reconcile_reported_observations` is the instance. Amendment 1's (e) removes
the feature it became. It does not remove the arithmetic: that moves out of the
product path rather than out of the repository, where it exercises the
execution contract against the shipped document until a kernel exists.
`declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` have exactly one
non-test caller today, which is reconciliation, so they move with it.

**Its expiry is a condition, not a slice number.** Two distinct events, and an
earlier draft of this entry collapsed them into "the expiry is T021", which the
sequence cannot deliver. It **stops being an authority** when the kernel lands:
T021 runs the two against the shipped document, compares them, and the kernel
is what survives any disagreement. It **leaves the repository** when its last
remaining caller goes, which is a different event on a different clock. See
`D-2026-09-22-expiry-follows-the-condition`.

**The removal happens in two steps, and the second is gated on an open
question.** The function has two product-path uses, not one. T019's blocking
reason is the first and it goes now. The second is the
`observation_reconciliation` payload built at
`backend/assetops_backend/simulator_lab_api.py:435` and rendered as a panel at
`frontend/src/shell/ScenarioFrame.tsx:767`, which is T018 work already merged
to `main`. The function cannot leave the repository while that caller exists,
so T019 removes the blocking use and labels the function as a reference
implementation, and removal follows the last remaining caller.

**When that caller goes is Open Question 5 in
`Docs/simulator-scenario-authoring-and-runtime.md`, it is still open, and this
decision does not settle it.** Removing a visible panel from merged work is a
product change belonging to a slice that says so, and the Architect read's
recommendation — that it goes with (f) in T022, because that is when the
authored readings disappear and the panel has nothing left to reconcile — is a
recommendation, not part of what the user accepted. Until then the panel is
honest: it describes a real property of a document that does still contain two
authored readings, so it is removed when someone decides to remove it rather
than because it has become false. No slice before that decision may treat the
removal as in scope, and T021 in particular performs the comparison and not the
removal.

Reason: `EXECUTION_CONTRACT_VERSION` versions a set of rules, and a
specification with zero implementations is under-tested. The standard remedy is
a reference implementation, and that is what reconciliation accidentally
became. The defect was never that it existed; it was that it shipped as product
behaviour, as a run-setup blocking reason and a user-facing panel. Three review
rounds on it, a simultaneity rule reversed after its first attempt, and four
still-unpinned kernel semantics are not four unrelated incidents. They are one
specification discovering it was underspecified by trying to implement itself,
and the cheap version of that discovery is a labelled spike in the test suite.

The generalisation, which is why this has its own ID: where a contract in this
project needs exercising before its real implementation exists, the exercise is
a test-suite artifact with a named expiry and a named successor, never a
product surface. A product surface acquires users, screens and acceptance
criteria, and then the throwaway cannot be thrown away.

Affected scope: `backend/assetops_backend/scenarios/execution.py`, the
`observation_reconciliation` API payload and the scenario-detail panel that
renders it, T019's narrowing before merge, T021's comparison against the
kernel, and any future contract that ships ahead of its implementation.

## 2026-09-21

Decision: `D-2026-09-21-physical-property-ownership`. Four owners are in play
for any value a simulated run needs, and two swap tests decide which one owns a
given value.

> Foundation declares what the site **is**. The model profile declares how the
> simulator **reasons** about things of that kind. The scenario declares what
> **happens** during one interval. The publication profile declares how the
> reporting installation **behaves**.
>
> Swap the asset for another of the same type and the value changes:
> **Foundation**. Swap the scenario and it changes: **scenario**. Neither, but a
> better simulator would change it: **model profile**. Neither, ever: a
> universal constant, and it belongs in code.

Fuel consumption looked ambiguous until the tests separated two things wearing
one name. *This* generator burns 14 L/h at its dispatch point changes when the
genset is swapped and not when the scenario is, so it is Foundation.
*Consumption is proportional to runtime* changes under neither swap and would
change under a better simulator, so it is a model rule. A coefficient and the
law that consumes it are different objects with different owners. The shipped
Fuel Loss document puts the coefficient in the scenario, which fails the first
test decisively: run the same scenario against a different generator and 14 L/h
would follow the story rather than the machine, which would mean the story had
replaced the asset.

**The vocabulary of owners is complete; the plumbing that carries their values
is not.** Three holes, and they must move together or not at all.
`SiteComponent` and `TemplateComponent` carry one optional scalar `rating` per
component, so Foundation cannot express a second physical property at all.
`FoundationBinding` can address only that scalar by `component_type` and
`rating_unit`, so even if Foundation grew a property no binding could reach it.
`SupportedState` carries no field a model-rule value could live in, so a
scenario may declare `owner: MODEL_RULE`, run setup will correctly name
`MODEL_PROFILE` as the answerer, and there is nowhere for the answer to come
from. That is the T019 review's L9 finding.

**A third thing was missed, and it is the subject of a decision due before
T020A's task file.** The three holes below are carriers for a *value*. None of
them declares the *need*: initialization inputs are enumerated from scenario
parameters, and this entry has the coefficient leaving the scenario. See
`Docs/simulator-scenario-authoring-and-runtime.md`, *What declares the need,
once the scenario stops declaring it*.

**A new slice, T020A, closes them, after T020 and before T021.** It is the one
change in this sequence that is an insertion rather than a narrowing: you
cannot narrow your way into a field that is not there. Nothing moves relative
to anything else and nothing in front of it is blocked. Its minimum set is the
generator's specific fuel consumption as a named property with a unit, and a
`SupportedState` carrier for model-rule values. The fuel tank's minimum usable
level is the honest home for the floor `IMPLICIT_LOWER_BOUND_DIMENSIONS`
currently invents, but it does not block T021 and can follow. Efficiency
curves, minimum load, ramp rate, tank geometry, sensor placement, battery
chemistry and PV tilt are all absent from Foundation and none of them blocks
T021, because the first kernel models none of the things they affect. The
minimum set is not a wish list.

**Templates instantiate by copy, so MG-001 must be re-created.** Adding the
consumption property to `config/site-templates/hybrid-mini-grid-100kw.yaml`
will not give it to MG-001, which was created by copy and lives in
`var/sites/mg-001.yaml`; `.ai/ARCHITECTURE.md` is explicit that a later
template change never alters an already-created instance. The demo site must be
re-created from the updated template, or the property hand-added to the
instance. Both are cheap, because it is a development fixture, but neither is
automatic, and a slice that adds the field without doing this produces a site
whose runs never resolve the coefficient.

> **Corrected 2026-09-22 by `D-2026-09-22-foundation-property-absent-blocks`:
> those runs block.** This sentence said they are refused. The code blocks,
> and this entry was written the day before the user moved the refusal line,
> so the claim was re-asserted in the 2026-09-22 extension to
> `D-2026-09-21-run-setup-outcome-vocabulary` rather than re-derived against
> the new discriminator. The obligation to re-create MG-001 is unchanged; what
> changes is the warning. Without it the slice's own UI-verifiable outcome
> never appears, which is a weaker consequence than a refusal and a sufficient
> one. Nothing else in this entry is affected.

The four failures that block are the ones where the profile's binding cannot
locate an answer that exists. See
`D-2026-09-21-run-setup-outcome-vocabulary`.

Reason: the coefficient does not merely belong somewhere tidier. The kernel
needs it at T021 to move the tank at all, and a first kernel whose physics
arrive from the scenario teaches every kernel after it to do the same. The
separation this whole sequence exists to defend would be violated at the exact
moment it first becomes testable. An earlier Architect read placed this with
the product slices T034-T038, as something only the product needs in order to
form an expectation; that was wrong by one milestone and is corrected here.

The seam that holds whatever else is decided later: the consumption coefficient
the product uses to form an expectation comes from Foundation configuration,
never from the scenario's private rate. A product reading the number the
simulator used would compute the Finding from the cause and get the right
answer for the wrong reason.

Affected scope: `backend/assetops_backend/sites/models.py` `SiteComponent` and
`TemplateComponent`, the shipped site template and the strict parser's
per-component-type property vocabulary, `runs/profiles.py` `FoundationBinding`
and `SupportedState`, run setup's frozen-inputs resolution and its blocking
reasons, `config/scenarios/fuel-loss-event.yaml`, `var/sites/mg-001.yaml`,
Site Configuration's Key Parameters panel, the M1C task sequence, and T021's
initialization.

## 2026-09-22

Decision: `D-2026-09-22-expiry-follows-the-condition`. A thing that exists only
because a condition holds names **the condition** as its expiry, never a slice
number. Two artifacts in the M1C sequence exist for exactly that reason, they
were each given a slice number, and in both cases the number was wrong.

**The rule.** When something is created to cover a gap — a reference
implementation standing in for a missing kernel, a disclosure standing in for a
missing verifier — the thing that ends it is the condition closing, not a
calendar position in a plan. A slice number is a guess about when the condition
will close, and a guess written into a record is read later as a commitment.
State the condition; let the slice that ends it be whichever slice ends it.

**And what happens then depends on whether the thing has become false.** This
is the part that separates the two instances and it is the useful half of the
rule:

- A claim that has become **false** goes in the same slice that falsifies it.
  Leaving it is not caution, it is shipping a false statement, and no
  "visible product change belongs to a slice that says so" argument applies to
  a sentence that is no longer true.
- A thing that is still **honest** but no longer needed goes when someone
  decides to remove it. That is the case the existing precedent covers — T016's
  cold-room marker, T017's provisional markings — and it is a product decision
  with its own slice.

**Instance one: the `READY` disclosure.**
`D-2026-09-21-run-setup-outcome-vocabulary` has T020 disclose that `READY` does
not assert the model can execute its inputs, and T021 close the gap with a
conformance test deriving `supported_states` from the kernel. The condition the
disclosure names is *nothing verifies the supported set against a kernel*. The
conformance test ends that condition, so the disclosure becomes false in the
slice that lands it, and **T021 retires it**. It is not a later slice's to pick
up, and until now no slice owned it at all: T020's task file said the slice
landing the conformance test would retire it and T021's said retirement
belonged to a slice that says it is doing that, which between them left it
homeless. T021 says it is doing it. `BLOCKED` never carried an equivalent claim
and nothing about it changes.

**Instance two: the reconciliation reference implementation.**
`D-2026-09-21-specification-reference-implementation` said its expiry was T021.
It cannot be. Two events, on two clocks. It stops being an **authority** when
the kernel lands and the two are compared, which is T021. It leaves the
**repository** when its last remaining product-path caller goes, and that
caller is the `observation_reconciliation` panel, whose removal is Open
Question 5 and is undecided. The reference implementation is still honest in
the meantime: it describes a real property of a document that does still
contain two authored readings. So it waits for a decision rather than for a
slice, and T021 compares without removing.

Reason: both artifacts were recorded with a slice number because the slice was
the nearest visible landmark, and in both cases the landmark was not the thing
that actually ends them. The cost is not symmetric, which is why the rule
carries the false-versus-honest distinction rather than just "name the
condition": a disclosure left past its condition is a false statement on a
screen, and a reference implementation removed before its callers is a broken
build. Erring the same way on both would be wrong in one of them.

Affected scope: `D-2026-09-21-run-setup-outcome-vocabulary`,
`D-2026-09-21-specification-reference-implementation`, T020's disclosure and
its stated expiry, T021's conformance test and its comparison against the
reference implementation, Open Question 5, `.ai/ARCHITECTURE.md` under
Presentation Honesty, and any future artifact created to cover a gap.

## 2026-09-22

Decision: `D-2026-09-22-contract-version-scope`. Adding the `TRAJECTORY`
oracle kind in T021 does **not** move `EXECUTION_CONTRACT_VERSION`. The move
that T021A carries for (g) stands, and this entry says why the two are
different rather than leaving the next reader to re-derive it. Two readers
raised the question independently within a day, which is the signal that the
policy in (d) is answerable but not yet answered in writing.

**The question.** (d) says the number moves when the space of conforming
behaviours changes, including when it narrows, and never for wording. (g)
moved it for a change that alters no executor behaviour at all:
`execution_requirement` on a `REPORTED_OBSERVATION` is read by nothing, which
is the whole argument for removing it. Adding `TRAJECTORY` to
`EXPECTATION_KINDS` also alters no executor behaviour, because no executable
path reads any oracle. If document shape alone was enough to move the number
for (g), the same reasoning reaches `TRAJECTORY`, and T021 moves it too.

**Following (g) would bump on everything, so the test has to be sharper.**
`scenarios/parsing.py` validates both vocabularies strictly. Under a strict
parser every vocabulary change alters what an executor does with *some*
document - refuse becomes run, or run becomes refuse - so "does executor
behaviour change on some document" is satisfied by every change of either
kind and separates nothing. It cannot be the test.

**The axis that does separate them is direction, measured against the
documents that already exist.**

- (g) **narrows**: a document that was valid is now refused. A run could
  already have been frozen against such a document, and after the move that
  document no longer parses, so the artifact cannot be re-derived. That is
  exactly the situation
  `D-2026-09-21-causal-runtime-before-golden-traces` makes a provenance
  mismatch refuse playback for, and it is what the number exists to signal.
- `TRAJECTORY` **widens**: every document valid before is valid now and means
  the same thing, and every artifact frozen before regenerates identically.
  Nothing that exists is affected. Only documents that could not previously
  have been written are, and no artifact was ever frozen against one.

**So the policy, stated the way it is meant to be applied: the number moves
when the change can alter the outcome for a document that was already valid.**
A narrowing can. A pure widening cannot. "Including when it narrows" in (d)
was written to catch the case a reader would otherwise forget, not to make
widening a move; this entry says so rather than leaving it to be read either
way.

**One carve-out, kept deliberately.** A widening whose new construct sits on
an executable path can change how an existing construct is interpreted beside
it, and that reaches documents that already exist. This entry does not cover
that case. `TRAJECTORY` is not it: no executable path reads any oracle, under
`D-2026-09-21-scenario-authoring-semantics`, and
`D-2026-09-21-scenario-execution-contract-amendment-1`'s (i) keeps it that
way by construction.

**Why the forward direction is not the number's job here.** A scenario
document declares no contract version; the constant lives in code and is
stamped onto a frozen run. Parser and constant ship together, so "a version-2
executor meets a version-3 document" is not a state this product can be in.
The only comparison the number ever serves is an older frozen run replayed
against a newer build, which is the backward direction, and a widening is
invisible in it.

**This is distinguishing (g), not overruling it.** (g)'s move is correct and
stays. What changes is that the reason for it is now recorded as its
direction rather than as "the document shape changed", so the next vocabulary
addition does not inherit a move it has not earned.

**What each slice leaves the number at, and why the literals should go.**
T021 leaves it at its current value. T021A moves it by one. The absolute
numbers should not be written as literals anywhere, for two reasons already
in the record and neither of them hypothetical:

- Pinning the four unpinned kernel semantics is a narrowing and moves the
  number. That declaration is due before T021's task file, so if it lands
  before T021A, T021A's move is not `2` to `3`.
- The constant's own docstring carries an unreleased-version doctrine: a
  narrowing that never leaves the branch it was made on does not spend a
  number, because nothing ever conformed to the version it would have
  replaced. Two amendments have already been absorbed that way.

`tasks/T021A-reported-observation-requirement-closure.md` hard-codes "2 to 3"
and T022's guidance says "already under version 3". Both should say the move
and the ordering rather than the values. That is the Planner's edit and it is
unblocked by this entry.

**The count itself is stated once**, in `.ai/FEATURE_MAP.md` under *The
execution-contract version ledger*, because it is a property of the sequence
and moves when the sequence does. Added 2026-09-22 once
`D-2026-09-22-foundation-value-declaration` put a third narrowing in flight.

Reason: the policy in (d) is sound and was stated against the case in front
of it. Applied literally to a widening it spends a version number to buy
nothing, which is precisely the cost (d) names when it explains why wording
must not move the number - a version that moves for a change that invalidates
nothing forces regeneration of golden traces that were never invalid. The
refinement keeps (d)'s purpose rather than its sentence.

Affected scope: `backend/assetops_backend/scenarios/execution.py`'s
`EXECUTION_CONTRACT_VERSION` and the policy comment beside it, which states
(d) correctly and is incomplete rather than wrong; T021's `TRAJECTORY` oracle;
T021A's version move and the literals in its task file; T022's statement about
which version it edits under; the slice that declares the four unpinned kernel
semantics; and the carrier decision due before T020A, whose option B is a
narrowing and would move the number if it is chosen.

## 2026-09-22

Decision: `D-2026-09-22-foundation-value-declaration`. **A scenario parameter
whose declared owner is Site Foundation has no value position at all.** It
declares the need - the state, the unit, that Foundation answers - and states
no number. Option B of the three worked up in
`Docs/simulator-scenario-authoring-and-runtime.md`, *What declares the need,
once the scenario stops declaring it*, accepted by the user on 2026-09-22.

Closed at the structure, the way
`D-2026-09-21-scenario-execution-contract-amendment-1`'s (g) closes
`execution_requirement` and T018 closed duration units: there is no position
the number can occupy, rather than a rule someone has to remember not to
break.

**Why not the other two.** Option A kept the parameter and its stated value as
a requirement Foundation is checked against, which is the `tank-capacity`
pattern already shipped. It costs least and it preserves exactly the seam (k)
exists to remove: run the same scenario against a different generator and
14 L/h still follows the story, now as a requirement that fails the run. A
scenario that cannot run against a 12 L/h genset has a machine's physical
property in it. Option C moved the need to the model profile, which is where
it conceptually belongs, and spends two protected-seam changes in one slice;
it is a follower, below.

**What this reaches, and it is more than the coefficient.** The rule is keyed
on the **owner**, because the owner is the only thing the scenario document
carries that distinguishes these parameters: the binding that addresses a
Foundation property lives in the model profile, and the scenario parser sees
no profile at all. So the rule reaches every `owner: SITE_FOUNDATION`
parameter. The shipped document has exactly one besides the coefficient -
`tank-capacity`, which states 500 L for `fuel-tank-capacity` - and **T020A
edits it too**.

That is not a widening chosen for tidiness. Exempting one parameter needs a
field invented for the exemption, which is a rule with an exception, and this
project has paid for that shape twice already - the bound guessed from a
shared prefix, and the unit case that was left a refusal while the cases
either side of it moved. It is also the better outcome: `tank-capacity` has
option A's defect today, so the seam repair lands complete rather than half.

**It moves `EXECUTION_CONTRACT_VERSION`.** Under
`D-2026-09-22-contract-version-scope` this is a narrowing that reaches a
document which already exists: the shipped Fuel Loss document as it stands is
refused by the new parser. The sequence-wide count is in `.ai/FEATURE_MAP.md`
under *The execution-contract version ledger*, which is the one place it is
stated.

**And it retires `INITIAL_VALUE_ANSWERS_DISAGREE`, in T020A rather than
later.** That refusal kind has exactly one producer, `rating.value !=
declared` in `_resolve_foundation_value`, and after this decision no document
can state a `declared` for a Foundation-owned value. Nothing can produce it.
Two ways out were identified and the first is rejected: keeping a
Foundation-owned parameter able to state a cross-check re-introduces the
number in the scenario that this decision exists to remove. So the kind is
**retired in the slice that removes its last producer**, under
`D-2026-09-22-expiry-follows-the-condition`. A refusal kind nothing can
produce is the `RUNNING` case one layer down - a vocabulary claiming a failure
mode that cannot occur - and for pure absence deletion is the honest move.

Two consequences of that worth carrying. With the contradiction gone and
`D-2026-09-22-foundation-property-absent-blocks` settling the other side,
**every failure of a Foundation-owned value now blocks and none refuses**; a
reader meeting that should not take it for an oversight. And the naming rule
in `.ai/ARCHITECTURE.md` still holds with one fewer pair to keep legible:
`INITIAL_VALUE_NOT_RESOLVED` carries the whole Foundation side, and
`INITIALIZATION_INPUT_MISSING` keeps its own producer, a `RUN_OVERRIDE` the
request did not supply.

**What does not change.** T021 reads the coefficient out of the frozen
identity exactly as it would have. The three carriers (k) names are unchanged
and still move together. MG-001 must still be re-created from the updated
template.

**Follower, with its trigger: option C.** The model profile declaring the need
is where the need belongs - *consumption is proportional to runtime* is the
model rule, and the law is the thing that knows it needs a coefficient. It was
not taken because it changes the shape of the frozen deterministic identity,
a protected seam, in the same slice that changes Foundation's schema, and
because it puts frozen rows behind no scenario parameter. **Trigger: the first
model rule that needs a Foundation value without a scenario asking for it.**
Until then the scenario declares the need and this decision is how.

Reason: the coefficient does not merely need somewhere to live, it needs
somewhere the story cannot reach. A value position that an author may fill is
a value position an author will fill, and the seam `D-2026-09-21-physical-
property-ownership` defends is exactly the one that fails quietly - the
document stays valid, the run still executes, and the physics follow the
story to whichever machine the scenario is pointed at next.

Affected scope: `backend/assetops_backend/scenarios/parsing.py` and the
`InitializationInput` shape, `scenarios/execution.py`'s
`initialization_inputs()` float filter and `EXECUTION_CONTRACT_VERSION`,
`runs/service.py` `_resolve_foundation_value`'s `declared` argument and the
retirement of `INITIAL_VALUE_ANSWERS_DISAGREE` from `runs/refusals.py`,
`config/scenarios/fuel-loss-event.yaml` for both `generator-fuel-rate` and
`tank-capacity`, T020A's scope and its task file, and the version ledger.

It also reaches a second float filter this entry did not name, in
`declared_bounds`, and that consequence is settled separately by
`D-2026-09-22-capacity-bound-source`: the `fuel-tank-volume` upper bound stops
being something the document can state. The constraint that falls out and
belongs to T020A: **the `bounds` declaration must survive the value's
removal.** A bound's `state_key` and `bound_kind` say which world state caps
which, which is a relationship between two states and not a property of a
machine, so it stays in the document when the number goes. A parser that
rejected `bounds` on a parameter stating no value would take the relationship
out with the number and leave the kernel nothing saying what caps what.

And `.ai/ARCHITECTURE.md` under Refusal And Blocking Vocabularies, which the
slice retiring the kind has to touch: the durable naming rule there uses
`INITIAL_VALUE_NOT_RESOLVED` against `INITIAL_VALUE_ANSWERS_DISAGREE` as its
worked example of *within one subject, the shape must carry it*. The rule is
general and survives; its illustration stops existing, and a rule illustrated
by a vocabulary member nobody can find reads as a rule that was not followed.
Either re-illustrate it from the pair that remains or say the example is
historical.

## 2026-09-22

Decision: `D-2026-09-22-foundation-property-absent-blocks`. **A Foundation
that declares no such property at all blocks**, with
`INITIAL_VALUE_NOT_RESOLVED`. It is a fifth case alongside the four, not a
refusal. Accepted by the user on 2026-09-22. This corrects six statements in
the record and supersedes the contrary paragraph in the 2026-09-22 extension
to `D-2026-09-21-run-setup-outcome-vocabulary`.

**Why.** The discriminator the user chose at the T019 review asks *would a
different model profile fix this?* After T020A the `FoundationBinding` names
the component type, **the property** and the unit, so the property name is as
much the profile's aim as the component type is. A different profile naming a
different property may well find something this Foundation does declare. That
is a joint fact about the pair, the profile is the half a person can change on
the setup form, and under the discriminator it blocks.

For the refusal to have held, run setup would have had to establish that the
declared owner has no answer **without** going through the profile's binding,
and the same extension that asserted the refusal also says a Foundation's
answer is locatable only through that binding. The two could not both be true.

**Where the wrong claim came from, because the shape of the mistake is worth
keeping.** It was written in `D-2026-09-21-physical-property-ownership` on
2026-09-21, one day before the refusal line moved. When the line moved it was
re-asserted in the extension rather than re-derived against the new
discriminator, and five further documents and one task file copied it. A
statement carried through a change that should have overturned it reads,
afterwards, exactly like a statement that survived review.

**What survives untouched.** The discriminator itself. The other four blocking
cases. The absent case on `FrozenInitializationInput` and its three
invariants. And the structural argument for why a contradiction could not be
blocked - absence and contradiction are different shapes, and only one of them
is something a frozen identity can hold. That argument is still correct;
`D-2026-09-22-foundation-value-declaration` simply removes the only way to
author two answers, so the case it described can no longer arise.

**MG-001 still has to be re-created.** What changes is the warning, not the
obligation: a slice that adds the property to the template without re-creating
the instance produces Drafts that **block** on the missing coefficient, so the
slice's own UI-verifiable outcome - the Key Parameters row, and the
frozen-inputs row resolving from *site foundation* - never appears. A blocked
Draft naming the missing property is also the more useful failure, because it
is inspectable, where a refusal leaves nothing behind to look at.

Reason: a persisted Draft the person can read is worth more than an error, and
the discriminator already said so. The only thing holding the refusal up was a
sentence written before the rule it was supposed to follow.

Affected scope: the 2026-09-22 extension to
`D-2026-09-21-run-setup-outcome-vocabulary`,
`D-2026-09-21-physical-property-ownership`, `.ai/FEATURE_MAP.md`'s M1C
sequencing revision, `.ai/PLANNING_HANDOFF_T019_T022.md` T020A,
`.ai/ACTIVE_CONTEXT.md`, `Docs/simulator-scenario-authoring-and-runtime.md`,
`tasks/T020A-foundation-physical-properties.md` which is the Planner's, and
T020A's blocking-reason coverage.

## 2026-09-22

Decision: `D-2026-09-22-capacity-bound-source`. **A bound's declaration is the
document's; a bound's value is the site's.** After
`D-2026-09-22-foundation-value-declaration`, `declared_bounds` reports no
upper value for `fuel-tank-volume`, and that is the correct answer rather than
a hole to be plugged.

**What was found.** `declared_bounds` skips any parameter whose value is not a
float. After option B, `tank-capacity` states no number, the loop skips it, and
the `fuel-tank-volume` bound becomes `(0.0, None)` with no error and no
refusal. `backend/tests/test_scenario_execution_contract.py` asserts
`(0.0, 500.0)` and goes red.

**Why nothing sources the value back into the document.** A projection of a
document cannot report a number the document does not carry, and after option B
the document genuinely does not know how big the tank is - that is the whole
of what option B moved. Sourcing the bound from the resolved Foundation value
would make `declared_bounds` a function of document **and** Site. That does not
make it a kernel, because it composes nothing over time, but it stops it being
a projection of the document, and the scenario domain deliberately does not
resolve a target Site: T017 split the parser from the service over exactly that.
Sourcing it from the model profile's binding is worse, because the binding is
the profile's and the scenario domain has no business reading a profile at all.
The component entitled to hold a document and a resolved Site together is run
setup, which freezes; and the component entitled to walk a bound against a
running value is the kernel. Putting the walk in run setup is
`reconcile_reported_observations` again under a different name.

**And the number does not go anywhere.** `tank-capacity` is
`owner: SITE_FOUNDATION` with `initializes: true`, so run setup already
resolves it through the profile's binding and freezes it as
`FrozenInitializationInput` for `fuel-tank-capacity`. The capacity moves from
the document to the frozen run, which is where a machine's physical property
belongs and is the same relocation option B performs for the coefficient.
T021's kernel reads it there.

**The consumer was already scheduled to leave.**
`D-2026-09-21-specification-reference-implementation` records that
`declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` have exactly one
non-test caller, reconciliation, "so they move with it". Verified: the only
non-test caller of `declared_bounds` is `reconcile_reported_observations`. A
mechanism teaching `declared_bounds` to reach Foundation would build a
cross-domain capability for a function already on its way to the test suite.
The shipped document's own comment on the `bounds` block says its purpose is
letting the contract "notice that a declared cause would take the tank past
its capacity" - which is the bound walk, the kernel that was living in the
validation layer, and the thing (h) and (j) removed.

**What is lost, priced.** Nothing can notice the shipped document's 300 L
delivery overfilling a 500 L tank from the document alone any more. That was
never a projection: knowing the tank holds 254 L at offset 2400 requires
composing the declared causes, which is a kernel. So this is (h) being
applied, not a regression introduced here.
`BOUND_CASES["fuel-tank-capacity"]` is a policy rather than a number and
survives untouched; T021's kernel applies it against the frozen capacity, so
the document correction T021 owes still has something to check against.

**What is gained, and it is not nothing.** A capacity that cannot be found
used to leave a document-level bound that might not match the site. It now
blocks the run: a binding that cannot locate the Foundation rating produces
`INITIAL_VALUE_NOT_RESOLVED`, a `READY` run may not carry an absent value, and
every absent value must be named by a blocking reason for the same state. A
silent `(0.0, None)` in a retiring validator is replaced by a run that will
not claim to be ready.

**The test, and why the cheap fix is worse than it looks.**
`test_the_declared_bound_is_declared_rather_than_guessed` proves the bound is
declared rather than inferred from two state keys sharing a prefix: it removes
the `bounds` block and watches the upper bound vanish. After option B **both
halves of that test return `(0.0, None)`**. Weakening the assertion to match
does not merely lose a number - it leaves a test whose control and whose case
are identical, passing while proving nothing. That is the failure T019 met
three times and named: an assertion that holds against a value the product
cannot make proves nothing about the product.

So the property is re-proved where the distinction still exists, and it exists
in two places, neither of them retiring. The **relationship** is in the parsed
document and in the scenario-detail payload, which publishes
`bounds: {state_key, bound_kind}` and never a number - so removing the `bounds`
block is still an observable change and still a real control. The **value** is
in the frozen identity, where run setup resolves 500 L from MG-001's Foundation
and names `SITE_FOUNDATION` as the answerer. The test splits along the same
seam the decision does, and the 500.0 keeps a home.

**And that home has to be written, not moved, because T020A removes both of
the ones the number has today.** There are exactly two assertions of 500 in
the suite. One is the bound test above. The other is
`test_run_setup.py`'s `INITIAL_VALUE_ANSWERS_DISAGREE` message assertion,
which goes with that refusal kind in the same slice - and it is over a
fixture scenario rather than the shipped tank in any case. Nothing today
asserts that MG-001's Foundation answers 500 L for `fuel-tank-capacity`;
`test_run_setup.py` names that state only in a supported-states set. So
T020A must **add** the frozen-identity assertion. Without it the slice
removes every mention of the shipped tank's capacity from the suite at the
moment that number stops being in the document and becomes something only the
profile's binding can reach.

**A rider that sharpens an existing open question.** After option B,
`declared_bounds("fuel-tank-volume")` returns `(0.0, None)` where the `0.0` is
`IMPLICIT_LOWER_BOUND_DIMENSIONS` - so the function's entire answer for that
state becomes the validation layer's own injected model rule, with the
document supplying neither number. Open Question 11 had a destination and no
slice; it now has a second reason and a sharper statement of itself.

Reason: the question looked like "where does the bound come from now" and the
answer is that it comes from where it always should have: a document says
which state caps which, and a site says how big the tank is. The only thing
that made the old arrangement look coherent was a validator composing the two,
which is the component this sequence has spent three decisions removing.

Affected scope: `backend/assetops_backend/scenarios/execution.py`
`declared_bounds` and its float filter,
`backend/tests/test_scenario_execution_contract.py`'s bound test and wherever
the 500 L assertion lands in `backend/tests/test_run_setup.py`,
`config/scenarios/fuel-loss-event.yaml`'s `tank-capacity` `bounds` block and
the parser rule that must keep accepting it without a value, T020A's criterion
for the bound, T021's kernel reading the capacity from the frozen identity,
and Open Question 11.

## 2026-09-22

Decision: `D-2026-09-22-consumption-coefficient-unit`. **The Foundation
coefficient is specific fuel consumption in `L/kWh`**, and `dispatched-output`
is promoted from `NON_EXECUTABLE_CONDITION` to a `FORCING_INPUT` on
`generator-output-power`. Accepted by the user on 2026-09-22. Closes open
question 4.1.

**The deciding argument is the project's own swap test, one notch deeper.**
*This generator burns 14 L/h at its dispatch point* changes if the dispatch
point changes, and the dispatch point is the scenario's. So `L/h` is a
property of machine **times** operating point, and half of that pair belongs
to the story. `L/kWh` is a property of the machine alone, which is why the
real engineering quantity is called *specific* fuel consumption. Writing
`L/h` into Foundation would put a scenario-dependent number into Foundation -
the same class of error as putting the coefficient in the scenario, mirrored,
in the slice whose whole purpose is repairing that class of error.

**On the promotion.** The T018 comment forbidding authored generator output
conflates *computing* it with *forcing* it. Forcing an exogenous condition the
model does not solve is what `FORCING_INPUT` is for, the same as load and
irradiance, and the comment's own reasoning - what a generator delivers
follows from the demand it is covering - argues only against computing it.

**The shipped trajectory does not change, which is what makes this cheap.**
The generator window is 240 minutes: 14 L/h over 4 h is 56 L, and 45 kW over
4 h is 180 kWh, which at 0.311 L/kWh is also 56 L. So 430 - 56 - 120 = 254 L
at offset 1590 still holds and T021's document-correction loop is undisturbed.
T021 gains one supported state and a forced constant during the declared
window: a multiplication, not a power-flow model. The kernel carries the
forced value and does not solve for it.

**What it does to `generator-fuel-rate`, and it is more than a unit change.**
The parameter leaves the scenario under
`D-2026-09-22-foundation-value-declaration` regardless. Under `L/kWh` the
coefficient is not a rate over time, so the dispatch event stops naming a rate
at all: it declares that the generator runs and at what output, and the model
rule - *consumption is specific consumption times energy delivered* - owns the
transition. That is what T020A's `SupportedState` model-rule carrier exists
for, and it removes the last place a scenario names a consumption rate.

**A consequence for the product that was not part of the argument.** The
worked example's Path B has the product computing expected consumption from
generator **run hours** times a Foundation coefficient. Under `L/kWh` it
computes from **energy delivered**, so the generator controller's `ac-power`
stops being merely something it gains the ability to publish and becomes
something the product needs it to publish. The promotion is therefore
load-bearing for T034-T038 rather than convenient for them, and it adds a
second error source - energy measurement, beside coefficient spread - to any
tolerance derived later. See open question 10.

Reason: a coefficient stored in the unit it was measured at is a number that
is false at every other load. Foundation is where a site says what it *is*,
and what this generator is does not change when the story dispatches it
differently.

Affected scope: `config/scenarios/fuel-loss-event.yaml` for
`generator-fuel-rate`, `dispatched-output` and the dispatch event's
`state_effect`; the shipped template and `var/sites/mg-001.yaml` for the
property's unit; `runs/profiles.py` for `generator-output-power` in the
shipped model profile's supported states; T020A, which carries all of it;
T021's kernel, which carries the forced state; and open questions 4.2 and 10,
both of which this sharpens.

## 2026-09-22

Decision: `D-2026-09-22-forcing-state-requirements`. **`site-load-demand` and
`plane-of-array-irradiance` drop to `OPTIONAL`, and reporting-path authority
for `fuel-level-reporting-availability` moves to the publication profile.**
Accepted by the user on 2026-09-22, with both riders below. Closes open
question 3.

**Lowering is a correction, not a dodge.** `REQUIRED` means an executor must
model this to run this scenario. To produce the Fuel Loss tank trajectory an
executor does not need irradiance or site demand: the scenario declares the
dispatch directly, so nothing computes it from load and PV. A kernel that
modelled them would be computing dispatch, which is a power-flow model and
already a T021 may-not. They were marked `REQUIRED` by an author being
careful.

**And lowering hides nothing, because the machinery already exists.**
`_support_for` in `runs/service.py` says it in one line: required and
unsupported blocks, optional and unsupported is *recorded*. An `OPTIONAL`
state the profile does not model becomes an `UnsupportedOptionalInput` on the
run rather than a blocking reason. The Draft stops being blocked and still
says what the profile does not model.

**The consequence that made this worth taking now: the shipped Fuel Loss
Event becomes able to reach `READY`.** With both states lowered, reporting
authority moved, and `generator-output-power` supported under
`D-2026-09-22-consumption-coefficient-unit`, nothing is left to block it.
That matters beyond the reason count. T021 owes *run the kernel against the
shipped document and report the trajectory*, and `BLOCKED` means everything
was frozen and the run **must not execute**; running a blocked Draft would
contradict the status this sequence spent three decisions making honest.
These three states were what stood between the sequence and its own first
executable run.

**Rider one: a requirement conflict is refused, not resolved.**
`_executable_inputs` collapses executable inputs on `(state_key, role)` and,
where two positions disagree about the requirement, takes `REQUIRED`. That
rule was invented by T019 rather than settled by T018, and it matters here
because `site-load-demand` is declared in three positions and
`plane-of-array-irradiance` in two - under the collapse, lowering one changes
nothing. **The rule is retired and the conflict is refused instead.** Two
positions disagreeing about whether one state is required is two answers to
one question, which is the shape this project already refuses as
`INITIAL_VALUE_ANSWERS_DISAGREE`; resolving it silently by taking the stricter
value is how an author's mistake becomes a behaviour. A `(state_key, role)`
pair must agree on its requirement and a document where it does not is
refused.

This is a narrowing and therefore contract-version business: a document that
was valid, because the collapse resolved it, is now refused. It shares its
version move with the four semantics - see the ledger.

**Rider two: `FROZEN_INPUT_ANSWERERS` gains `PUBLICATION_PROFILE`.** Run setup
stamps `answered_by="MODEL_PROFILE"` on the cadence row and on both
publication identity rows, beside detail text naming the publication profile.
Today that is a mislabel; once the authority moves it is a false statement
about which profile answered. **The fifth answerer and the relabel land in
T020, not in the slice that moves the authority** - corrected 2026-09-22,
after this entry was written and after T020B was named. The justification
above is that a mislabel must not reach a permanent screen, and T020 is the
slice that puts the frozen-inputs table on one. So T020 carries the relabel
and introduces the vocabulary member; T020B moves the authority and relabels
nothing, which is a scope limit in its task file. The subset assertion in
`test_the_answerers_correspond_to_the_initialization_owners` permits a fifth
member, so the cost is the wire value, the screen, and a vocabulary docstring
that says "the four".

Reason: three states the first kernel has no business modelling were holding
the shipped scenario in a state that says it must not execute, and one of them
was not a state of the world at all.

Affected scope: **T020B**, which carries all of this except rider two's
relabel - `config/scenarios/fuel-loss-event.yaml` at five positions across the
two lowered states, `runs/profiles.py` for the publication profile's
supported-reporting-states concept, `runs/service.py` `_executable_inputs`,
and the scenario parser, which is where a requirement conflict is refused;
**T020**, which carries `runs/models.py` `FROZEN_INPUT_ANSWERERS` and the
`runs/provenance.py` rows that name the answerer; T020's fixture-only `READY`
criterion, which this falsifies; and the version ledger.

## 2026-09-22

Decision: `D-2026-09-22-kernel-step-semantics`. The four semantics the
execution contract left unpinned are declared. Accepted by the user on
2026-09-22. Closes open question 1.

- **A quantity over a window ramps linearly across the steps** rather than
  landing at the completion boundary. It is what an author means by 120 L over
  45 minutes, and it is the only reading under which retiming or resizing a
  window changes the trajectory proportionally - the metamorphic invariant
  `D-2026-09-21-causal-runtime-before-golden-traces` requires. It also sits
  beside `quantity-across-a-window`, which already declares intra-step path
  independence.
- **The observation transform samples after the step's due events are
  applied.** A sensor reads the world at the sample instant and the step has
  happened by then. It is the same rule as dispatch: a boundary entry is
  applied by the step that begins there, so a sample there sees it. For the
  shipped run it makes the 2400 sample 500.0 L rather than 254.0 L.
- **A forcing outside its declared window is unavailable**, not zero and not
  held at its last value. A forcing's declared window is the whole of its
  claim; zero is a fabricated value and holding is an invented persistence
  rule, and *unavailable* is already this product's vocabulary for a value it
  does not have.
- **A bounded change lets the run continue, and later causes apply to the
  bounded value.** Otherwise a bound is a disguised run failure, and the
  policy already has a separate case for that - `insufficient-fuel` is
  `FAIL_RUN`. `BOUNDED_AND_RECORDED` records the quantity refused, and
  recording a refusal only means something if the run goes on.

Each pins a space two conforming kernels could legitimately have split on,
which is what `EXECUTION_CONTRACT_VERSION` exists to prevent. The one worth
carrying: *after* for observation means a boundary sample can never see
pre-event state, so a scenario that wants that must separate the offsets -
the same answer simultaneity got, and the same principle, that order is
expressed as time rather than as position in a document.

Two of these were free to declare and will not stay free. A forcing outside
its window is unreachable while the shipped profile does not support
irradiance and becomes reachable the moment it does; the bounded-change rule
decides everything after offset 2400 in the shipped document.

Declaring them is a narrowing and spends a version number, shared with the
requirement-conflict refusal under the unreleased-version doctrine. See the
ledger.

Reason: an unpinned semantic is a place where two implementations can both be
correct and disagree, which is the one thing a versioned contract may not
contain.

Affected scope: **T020B**, which declares them and spends the version number;
`backend/assetops_backend/scenarios/execution.py`'s `DISPATCH_RULES` and
`EXECUTION_CONTRACT_VERSION`; T021's kernel; T022's observation transform for
the sampling rule; the shipped document's trajectory after offset 2400; and
the version ledger.

## 2026-09-22

Decision: `D-2026-09-22-reconciliation-panel-retirement`. **The
`observation_reconciliation` panel and its payload go with (f) in T022.**
Accepted by the user on 2026-09-22. Closes open question 5, and with it open
question 11.

The panel is honest while the shipped document still contains two authored
readings, because that is what it describes. (f) removes them, and a panel
with nothing to reconcile is a claim that has become false, so
`D-2026-09-22-expiry-follows-the-condition` puts its removal in the slice that
falsifies it. T022 already carries a user-review checkpoint, and removing a
visible panel is a product change belonging to a slice that says so.

**The capacity-bound change does not move this, and it was checked rather than
assumed.** After T020A `declared_bounds` reports no upper bound for
`fuel-tank-volume`, which could have made the panel's arithmetic unbounded.
It does not: the panel publishes one entry per reported observation, the
shipped document's are at offsets 1590 and 1800, and the only offset where a
capacity bound could clamp is the 2400 delivery. Both reconciled offsets
precede it and the running value there is 254 L against a 500 L tank. After
T020A the panel renders exactly what it renders today; the bound walk's
upper-bound machinery simply becomes dead code for this document.

**What goes with it, which is the reason this mattered.** The panel is the
last product-path caller of `reconcile_reported_observations`, so T022
completes (j): the reference implementation, `declared_bounds` and
`IMPLICIT_LOWER_BOUND_DIMENSIONS` all leave the product path together, as
`D-2026-09-21-specification-reference-implementation` said they would when
their last caller went. That also settles open question 11's *when*: the
injected volume floor stops being a product claim in T022 and becomes a
test-suite artifact. Its *where* was already settled by
`D-2026-09-21-physical-property-ownership` - *volume is non-negative* is a
model rule and belongs to the model profile, and *this tank cannot be drawn
below its pickup* is a Foundation property and a follower. What remains is an
instruction to T021 rather than a question: the kernel takes its floor from
the model profile, never from the validation layer's constant.

Reason: this is the latest honest moment rather than the earliest possible
one, and the earliest possible one would have removed a panel that still
described something true.

Affected scope: `backend/assetops_backend/simulator_lab_api.py`'s
`observation_reconciliation` payload, `frontend/src/shell/ScenarioFrame.tsx`'s
panel, `scenarios/execution.py`'s `reconcile_reported_observations`,
`declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS`, T022's scope and its
user review, T021's kernel floor, and open questions 5 and 11.

## 2026-09-22

Decision: `D-2026-09-22-milestone-speed-over-purity`. **Speed matters more
than pedantic purity for the rest of the simulator milestone. A complete
review, including a possible refactor, happens once the milestone is complete
and the thing has been tested properly.** Directed by the user on 2026-09-22.
This governs every slice, pass and review after it.

**What still gets stopped for.** Three things, and nothing else:

- **A defect that would be expensive to reverse later.** A persisted shape, a
  contract version, an identity space, a published seam - anything where the
  cost of the fix grows with what gets built on top of it. `cadence_resolution`
  qualified while it was a rename and stopped qualifying when it became a
  deletion that costs nothing.
- **A claim that would mislead an Implementer.** A statement in the record that
  has outlived the thing it described, a criterion that points at a closed
  question, a task file that disagrees with a decision. These are cheap to fix
  and expensive to act on.
- **A decision only the user can take.** Product semantics, user-visible
  claims, evidence interpretation, demo narrative, and anything a task file
  would otherwise settle by writing a scope line.

**What now gets recorded and carried instead.** Naming that is imperfect but
honest. A declaration whose falsifier is scheduled rather than absent, as long
as it discloses that. A restatement that is redundant but not false. A
vocabulary that would be better shaped and is not wrong. An internal
inconsistency between two things that both tell the truth.

**Carried is not dropped, and that is the whole of what makes this safe.**
Everything carried goes on the list in `.ai/MILESTONE_REVIEW_BACKLOG.md` with
what it is and why it was carried. The deferred review is the thing these are
carried *to*: it is a named event with a list waiting for it, not an
intention. A thing carried without being written down is dropped, and this
decision does not authorise that.

**What this changes for a Reviewer.** A Reviewer raises the three above and
records the rest to the backlog rather than blocking a slice on it. "This
would be better named" is a backlog entry. "This name is false" is still a
finding, because a false name misleads an Implementer.

Reason: three of the last several passes were vocabulary and naming questions.
Each was individually defensible and the sequence they came in was
collectively slower than the milestone can afford. The correction is not that
those questions were wrong; it is that the milestone has a backstop and they
can wait for it, and a question that can wait should.

Affected scope: `.ai/ACTIVE_CONTEXT.md`, `.ai/WORKFLOW.md` for what a Reviewer
raises, the new `.ai/MILESTONE_REVIEW_BACKLOG.md`, and every slice, planning
pass and review for the rest of M1.

## 2026-09-24

Decision: `D-2026-09-24-v4-roadmap-replan`.

Directed by the user: re-derive planning from `Docs/simulator_design_v4.md`
and the corrected `Docs/mini-grid-demo-architecture-and-roadmap.md`, plus
canonical evidence of what is built. Do not reconcile with the superseded
roadmap, prior feature-map revamp, alignment reviews or v3 assessment.
v4 is normative for simulator mechanisms; the roadmap governs demo sequencing.

The feature map now follows roadmap section 7's A-I: credible electrical
mini-grid, source boundary/ingestion, dispatch Finding, thin economics, fuel
reconciliation, productive use, lifecycle, intervention verification, portfolio.
T001-T020 remain built. v4 sections 2.1/24 retain the unfinished starter queue,
with a carrier/addressed-binding sizing or split before implementation.
Component addressing belongs there; Site Controls wait for their controller.

Explicit supersessions:

- `D-2026-09-17-client-demo-readiness` called the evidence loop client-ready.
  It is now the internal architecture demo. The first feedback milestone is
  the dispatch Finding; the full client milestone is the portfolio/intervention
  story in roadmap section 13. Historical M0/M1A/M1B remain completed records.
  The old M1C/v1/v2/v2.5 labels no longer schedule future work.
- The former feature map's fuel-first Finding, late electrical world and late
  StateRef recommendation are withdrawn. Fuel is roadmap E, electrical runtime
  is A, and addressed binding belongs in immediate contract work.
- `D-2026-09-22-kernel-step-semantics` used "observe after the step".
  v4 section 6 supplies the precise replacement: due events, post-event sample
  at T with preceding-interval measurements, then controller/physical evolution
  for the coming interval. No initial interval measurement without declared
  historical input. Other compatible bound/window semantics remain.
- Cold-chain's scheduled Demo Ready v2.5 slot is retired. Cold-chain/e-mobility
  remain later architecture tests under roadmap sections 8/10.
- The previous handoff's backend-side kernel alternative is replaced by v4
  section 3's simulator/neutral-contract/host separation. The existing import
  guard already bans both cross-import directions.

These are planning changes, not claims that code has changed. Unimplemented
task files are deliberately untouched and await Planner recreation. No new
implementation task is activated by this record. All current runtime/evidence
gaps are named in the feature map's ownership table.

Reason: the corrected roadmap requires the first useful dispatch conclusion
from credible electrical operation through ordinary evidence; the old fuel-first
sequence could not deliver that demonstration. Protect expensive boundaries,
make progress observable and leave cheap choices to implementation.
`D-2026-09-22-milestone-speed-over-purity` continues to govern.

Affected files: FEATURE_MAP, PRODUCT, ARCHITECTURE, ACTIVE_CONTEXT, START_HERE,
the scoped Planner handoff, PLANNING_GUIDANCE, WORKFLOW, ARTIFACT_INDEX and
MILESTONE_REVIEW_BACKLOG. CODE_STATE and completed task history are unchanged.

## 2026-09-24

Decision: `D-2026-09-24-task-spec-size-ceilings`. **Task-spec size is a ceiling
with no minimum, and `.ai/WORKFLOW.md` owns the rule alone.**

The old 100-180 / 180-260 / 250-400 bands were written for specs that restated
durable mechanics. A reviewer found the six specs written to them repetitive,
explaining why past arguments were won rather than what to build. The twenty
recreated specs cite v4, the roadmap, the feature map, ARCHITECTURE and
DECISIONS instead, and average about 104 lines, below every band. That is the
bands measuring the wrong thing rather than the specs being thin, because a
lower bound on a citing spec is a quota for prose.

Ceilings are 120 / 160 / 220 lines by slice type. What replaces the lower bound
is a test a spec can fail: an implementer holding the file, the references it
names and the built state can start without asking, and any legitimate stop is
named in the file rather than left silent.

`.ai/PLANNING_GUIDANCE.md` repeated the bands and now points at WORKFLOW,
because that duplication is how a superseded rule survived in two canonical
places at once.

Reason: this was the first review of the recreated queue by anything that did
not write it, and a canonical document recommending an abandoned practice would
have misled the next Planner. `D-2026-09-22-milestone-speed-over-purity`
governs: the sizing rule is cheap to revise and expensive to leave wrong.

Decision: `D-2026-09-24-queue-resequenced-for-demo`. **The recreated queue is
resequenced so that product value is exposed before infrastructure completeness.**
Source: `Docs/queue-review-feedback-verbatim.md`, the user's review of the queue
after the Architect review merged at `c625308`. That file is the argument; this
entry records what changed.

Three headline changes, all made:

- **T026 is thinned to dispatch-essential evidence.** It keeps the PV, BMS,
  generator, load, policy and operator-commanded-record families, normal
  cadence, one reporting gap and one delayed publication. Gateway outage,
  buffering, recovery, retry, duplicate, out-of-order release, buffer
  exhaustion and numeric bias move to a new deferred `T026A`, placed after
  T035. If T023's publication path makes any of it nearly free, T026 includes
  it and reports that T026A shrank; building buffering to demonstrate it is
  what the thinning refuses. The operator-record family stays in T026: it is
  in the evidence the user kept, and it is also the forward dependency the
  `c625308` review fixed, so thinning must not undo it.
- **Verification moves ahead of analytic breadth.** The minimal immutable
  policy-intervention mechanism is extracted from T032 into a new `T029A`, and
  T034 now runs at position 15, directly after it. T034 sheds its T033
  dependency: its first guardrail set is battery reserve discipline,
  critical-load service and unserved energy, all available from T026/T027
  evidence. T033 later adds battery stress to the same versioned rule set as a
  new rule version, without re-judging earlier results. Delivery order is now
  A, B, C, D, H, then E, F, G, I. Feature-map letters are outcomes, not order.
- **T036 stops being the first client-facing milestone.** There are four demo
  points: T027 internal architecture, T028/T029 domain-expert and
  early-prospect, T034 strong product (Finding to action to verification), T036
  full polished portfolio. Roadmap 12.1's financial assumptions are therefore
  due at T029, which is real external exposure, not at T036.

Also applied from the same source: T021A is time-boxed to the narrow parser
closure and leaves the critical path if it grows; T023's stage inspector stays
utilitarian; T032 implements exactly one load-addition comparison and not a
generalized experimentation platform; T033 is named as the first major story to
defer under schedule pressure; T035 is held to the one outage -> backup
response -> unserved-energy chain with no incident-management subsystem.

Two consequences worth naming. Thinning T026 removed the case T027 used to
prove three distinct timestamps, so T027 now proves it from the delayed
publication and T026A re-proves it under full recovery. And numeric bias/noise
went to T026A even though the user asked to keep "one simple gap/delay case",
because gap and delay already give C a coverage-limited claim and bias does not.

The electrical-before-Finding order from the `c625308` review is untouched: it
is physically forced, and the user's resequencing request was downstream of it.
Nothing here changes the active task. T020A is still active and still startable.

Reason: the queue was biased toward proving infrastructure thoroughly before
exposing product value, and the cost of that bias is paid in feedback not
received. `D-2026-09-22-milestone-speed-over-purity` governs.

Affected files: `tasks/README.md`, `tasks/T021A`, `T022`, `T023`, `T026` (renamed from
`T026-dispatch-evidence-and-gateway-recovery.md`), new `T026A`, `T027`, `T028`,
`T029`, new `T029A`, `T030`, `T031`, `T032`, `T033`, `T034`, `T035`, `T036`,
`.ai/FEATURE_MAP.md`, `.ai/PRODUCT.md`, `.ai/ACTIVE_CONTEXT.md` and
`.ai/START_HERE.md`. No implementation code changed.

Decision: `D-2026-09-24-codex-spend-before-the-limit`. **Codex quota is
account-level and shared across every model, so the only lever is spending
less per call, before the limit is reached.** Exhausted twice on 2026-09-24,
the second time mid-review; `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-sol` and
`gpt-5.5` each returned the identical limit and reset time, so model choice
recovers nothing once the limit is hit.

The measured waste was repetition, not verbosity: three reviewer passes on one
slice started cold, at 145,247 / 145,568 / 25,259 tokens, and the second spent
its whole budget re-deriving what the first had established. `codex exec
resume <session-id>` continues a session with its context intact and the
session id is printed in every run header, so a second pass on the same slice
should resume rather than restart.

Also recorded: reserve `gpt-6-astra` for architecture and review judgement and
use `gpt-6-sol` for mechanical passes; never spend a full session on an
availability probe, since `model_reasoning_effort = "high"` is global while the
models default to `low`; and state in the brief what has already been run and
verified, because every such fact is work the session does not repeat.

Mechanics recorded with it, each already having failed once: pass the prompt as
an argument rather than stdin, which blocked for three hours on 2026-09-23;
background the call once rather than wrapping `nohup ... &` inside an already
backgrounded call, which reports a completion that has not happened; and merge
main into a task branch before reviewing it, because a session reads that
branch's `.ai/` rather than main's.

Full guidance in `.ai/ROLE_CONFIG.md` under "Using Codex Efficiently".


Decision: `D-2026-09-24-hardening-gates-nothing`. **A deferred hardening item
may not hold a position in the delivery order, and an order that is not
load-bearing must say so.** Follow-on to
`D-2026-09-24-queue-resequenced-for-demo`, from the "Round Two" section of
`Docs/queue-review-feedback-verbatim.md`, which accepted the resequenced queue
as a basis for starting implementation subject to these two changes.

- **T026A is unscheduled and a prerequisite of nothing, including T036.** It
  held position 21, between T035 and T036, and was named in T036's dependency
  line and T035's delivery order, so the deferral it was created to express was
  being undone by its own placement. It now has no position. T036 depends on
  T027-T035 and completed A. The portfolio demo needs a healthy site, dispatch
  loss, fuel, opportunity, battery trajectory, reliability and verification; it
  does not need a gateway outage, and T036's claim-limited Lab case is served by
  the gap and delay T026 already delivers. The one case where T026A precedes
  T036 is if that demo is deliberately built to include gateway-outage recovery
  as a proof story, which is a demo-content choice, not a standing dependency.
- **T033 and T035 are an interchangeable pair.** Neither consumes the other's
  artifacts; both depend only on T027's evidence, T029's assumptions and T034's
  rule set, so whichever runs second is unaffected. Which runs first is a
  product-priority call taken from T028/T029 feedback - backup failure and
  unserved customers may matter more to an operator than battery degradation.
  This is stated at those two rows and in those two files only. Every other
  position in `tasks/README.md` remains load-bearing; a queue in which every
  order is negotiable is not a plan.

T027 was flagged as an area to watch rather than one currently misplanned, so
nothing was removed or restructured there. Its Scope limits gained the
instruction the user wrote out: do the minimum robust implementation necessary
to prove source-envelope -> normal ingestion -> persistent Site Overview, do not
turn it into a generalized ingestion reliability project, and resumability can
be simple and correct rather than production-scale. The acceptance criteria are
untouched and none became optional; they sit on a protected seam, which is why
the slice is watched rather than trimmed.

Worth recording for the next reader: the gate was expressed by position as well
as by prose. T026A's own header carried "after T035, before T036", which a
search for the string "T026A" does not find. When a deferral is recorded, check
the deferred file's own delivery order, not only what other files say about it.

Reason: hardening deferred behind the first Finding had quietly become a gate on
the polished product demo, which contradicts the principle the previous decision
established. `D-2026-09-22-milestone-speed-over-purity` governs.

Affected files: `tasks/README.md`, `tasks/T026A`, `T027` (guidance only),
`T033`, `T035`, `T036`, `.ai/FEATURE_MAP.md` and `.ai/ACTIVE_CONTEXT.md`.
No implementation code changed. T020A remains active and unaffected.

## 2026-09-29

Decision: `D-2026-09-29-source-envelope-schema-v1`. **The canonical source
envelope is schema `assetops.source-envelope` version 1, versioned
independently of the execution contract, and compatibility is equality.**

Recorded by the T023 Implementer because the task's criterion 14 requires the
schema and its refusal behaviour to be written down, and because T027's
ingestion will parse exactly what this fixes. The schema itself lives in
`contracts/assetops_contracts/source_envelope.py`; this entry records the
choices a later slice must not reopen by accident.

- **Independent version.** `SOURCE_ENVELOPE_SCHEMA_VERSION` (1) does not move
  with `EXECUTION_CONTRACT_VERSION` (8) and vice versa. The execution contract
  says what a frozen Draft means when it runs; the envelope schema says what a
  published message looks like. The persisted stage document has its own
  `stage_schema_version` (2 since the T023 fix round added the publication
  watermark; 1 never left the branch) for the same reason.
- **Compatibility is equality.** A parser of version 1 refuses any other
  version as `SCHEMA_UNSUPPORTED` and never reads it "as close enough". A later
  version that must accept version-1 envelopes does so by an explicit reader of
  version 1, not by loosening the check.
- **Exact key sets at every level and no free-text field.** An unknown field is
  refused wherever it appears. Identities are validated identifiers, categories
  are closed vocabularies (`STATE_AT_INSTANT`/`INTERVAL_MEAN`,
  `GOOD`/`UNAVAILABLE`, `NO_COMPLETED_INTERVAL`/`NO_MEASUREMENT`), values are
  canonical exact decimal text, times are UTC instants. This is what makes the
  truth barrier structural at the boundary: a private field has nowhere to go.
- **The message id is derived, and content is not in it.** BLAKE2b-256 over
  Site, gateway, source, device, signal and source time, recomputed by the
  parser. A retry carries the same id by construction; same id with different
  content is a conflict the stage refuses rather than an overwrite.
- **`received_at` is not a field.** It is ingestion's (Evidence Loop
  Boundaries), and a document carrying one is refused as an unknown field.
- **A sample that was never published has no envelope.** A reporting gap or a
  dropped publication produces nothing; only a sample that was taken and had no
  value may produce a typed `UNAVAILABLE` envelope, and only where the mapping
  says the signal publishes unavailability. `STALE` is a consumer's conclusion
  and is not an envelope quality.
- **Mappings are versioned and frozen into the stage.** The stage persists the
  whole mapping it was staged under and is read under that mapping, never the
  current one. The shipped allowlist is the fuel level sensor alone
  (`simulator-lab-gateway-fuel` v1); T026 extends it.

Affected: `contracts/assetops_contracts/source_envelope.py` and
`source_stage.py`, `simulator/assetops_simulator/gateway/`, `host/lab_execution.py`
and `host/source_stages.py`. No execution-contract or publication-profile
version moved.

## 2026-09-29

Decision: `D-2026-09-29-run-store-libyaml`. **The run store reads its YAML
documents with PyYAML's `CSafeLoader` (libyaml), in its own slice T022B before
T024, with the C extension required.**

Decided by the owner on 2026-09-29, recorded by the coordinator, on the
Architect's recommendation (Codex as Architect,
`.agent/libyaml-architect-recommendation.md`). The owner chose each of four
points explicitly:

- **Adopt `CSafeLoader` for the run store, accepting known refusal
  differences.** Over 223 stored runs both loaders gave equal domain records,
  and the adapter's full inventory read measured 6.6x faster (medians 5.40 s
  against 0.81 s, three samples, one process - a ratio, not a budget). Of 24
  malformed probes the two loaders disagreed on 4 (a literal tab after a
  colon, a tab inside a flow sequence, a literal surrogate escape, an
  out-of-range escape). These differences are accepted, declared and tested;
  exact lexical equivalence with the pure-Python loader is **not** claimed.
  Domain validation, identity, bounds, ordering, whole-inventory failure,
  fallback, locking and atomic publication are unchanged. Only the run store's
  load point changes; Site, scenario, artifact and stage readers do not.
- **T022B comes before T024.** It owns T022A's criterion 2. T022A stays
  completed.
- **The C extension is required**, checked at install/CI and diagnosed
  clearly when absent. No machine silently reads with different refusal rules.
  Pure-Python-only installs are not supported for this path.
- **Budgets on the demo machine at its actual store size:** Runs inventory
  usable within 1 s and a successful Draft setup visible within 2 s, reported
  as median and range; the owner judges usability. If the parser change misses
  them it is a partial improvement, not criterion-2 completion.

Deferred with triggers, per the recommendation: removing `create_run`'s two
identity scans, caching/indexing/storage changes, and T023's whole-stage
rewrite (with T026). None is authorized here.

Amendment, 2026-09-29, T022B: **the owner accepts the deep-nesting process
crash as a carried risk until the run store moves to a database.** A
hand-placed run document with flow nesting past a few thousand levels overflows
libyaml's native stack and kills the process, where the pure-Python loader
raised `RecursionError`. The owner decided to add no pre-load bound. No database
is scheduled; the backlog entry names the triggers that reopen this sooner.
Setup is measured through populated run detail. T022B closed as a partial
improvement; T022A criterion 2 stays open.

## 2026-09-29

Decision: `D-2026-09-29-t024-option-c-and-reserve-override`. **T024 adopts
Option C with frozen effective Site Controls, and a scenario changes policy by
a temporary, reverting override of the battery reserve.**

Decided by the owner on 2026-09-29, recorded by the coordinator, on the
Architect's recommendation (Codex as Architect,
`.agent/T024-architect-recommendation.md`, from the Implementer's plan at
`.agent/T024-implementer-plan-phase1.md`). The owner approved each point:

- **Option C.** The new electrical profile declares the Foundation values its
  laws need; setup resolves them per addressed component and freezes each in
  the run's deterministic identity with provenance (need/profile, address,
  typed value and unit, Foundation version/valid_from, TEMPLATE/SITE source).
  Absent or ambiguous answers BLOCK with the address named. Effective Site
  Controls are frozen the same way. Foundation gains an optional typed Site
  Controls collection whose priority lists name explicit component identities;
  existing documents without controls stay readable. Execution contract
  **8 -> 9**; older Drafts read but are refused execution. Initial SOC stays
  scenario-owned. Not authorized: a generic dependency/plugin framework,
  migrating Fuel Loss to C, scenario-owned physical defaults, or a policy
  editor/history platform.
- **Policy change (criterion 5).** A scenario-authored numeric forcing on the
  battery's typed reserve CONTROL address replaces the frozen baseline inside
  `[start, end)` and the baseline applies again at `end`. Absolute replacement,
  not an increment or a Foundation edit. Genuine overlap on one address is
  refused; adjacent windows are valid. Within-step changes split evaluation, not
  averaged. A reserve above current SOC creates no energy. Priority lists stay
  baseline-only in T024, disclosed. The general "forcing outside its window is
  unavailable" rule is unchanged. Not operator evidence or a verified
  intervention.
- **Demo values** (fixture ratings, priority order, baseline reserve, override
  window and value) are proposed by the Implementer and reviewed by the owner
  at the hands-on check.
- Already settled: T024 is one slice; ship `kobo-daytime` plus overcast and
  larger-mill variants.

## 2026-09-29

Decision: `D-2026-09-29-t025-generator-policy-package`. **T025 extends contract
9 additively, takes its generator policy wholly from Site policy, and is
delivered as T025a then T025b.**

Decided by the owner on 2026-09-29, recorded by the coordinator, on the
Architect's recommendation (Codex as Architect,
`.agent/T025-architect-recommendation.md`) over the Implementer's size-gate
plan (`.agent/T025-implementer-plan.md`). The owner approved:

- **Contract 9 stays.** A new `mini-grid` v1 profile carries discrete state,
  the generator lifecycle and generator/fuel balances; `daytime-mini-grid` v1
  and the fuel model are preserved and existing v9 Drafts keep executing.
  Publication profile 4 and artifact schema 4 move only when their contracts
  change, with prior readers kept. **Merge gate:** representative pre-change
  frozen fuel and daytime inputs must parse, execute, keep their deterministic
  identities and reproduce trajectories, digests and numeric observations,
  including old reserve windows and stored artifact readback. If that cannot
  hold, return with the concrete incompatibility and a case for contract 10.
- **Q1** typed discrete (enum) values through state, trajectory, controller
  view, observation, artifact and Lab projection; no numeric noise settings on
  enums. Envelope schema 1 and the fuel-only mapping stay; generator status is
  disclosed as not yet staged (T026 owns it), never silently omitted.
- **Q2** generator CONTROL properties `start-soc-threshold` (%),
  `stop-soc-threshold` (%) and existing `minimum-runtime` (min); PHYSICAL
  `start-delay` (min) and `generator-rated-power` (kW) as the runtime
  authority; existing `specific-fuel-consumption` and tank capacity. Resolved
  and frozen as Option C model needs; an unambiguous generator-battery-tank-bus
  relationship frozen. Initial fuel, SOC and lifecycle state are
  scenario-owned.
- **Q3** the reverting override extends to profile-declared overridable
  numeric CONTROL addresses: battery reserve and generator stop threshold only.
- **Q5** lifecycle transitions at step boundaries only; start delay, policy
  windows and minimum runtime step-aligned or refused; generator fixtures step
  at 5 min. Minimum runtime counts actual RUNNING time.
- **Q6** STOPPED/STARTING/RUNNING/FAILED declared; initial FAILED is inert;
  failure causes refused until T035. Physical FAILED is not an execution
  failure.
- **Split:** T025a (criteria 1-6, 10, 14; 13 for healthy runs; balance/timing
  portions of 15) then T025b (7-9, 11-12; 13 for prolonged/changed-policy runs;
  the rest of 15; A acceptance). T025b uses `mini-grid` v2 rather than editing
  v1 in place.

**Control policy belongs to the Site, not the model.** The owner's rule: "these
are all control policies, the model should not define them itself." The model
executes only what the Site's frozen policy declares:

- The generator starts when SOC is at or below the Site's `start-soc-threshold`
  and stops when RUNNING, the Site's `minimum-runtime` has elapsed and SOC is at
  or above `stop-soc-threshold`. The model adds no trigger of its own; a
  shortfall-based start would first need to exist as a Site policy.
- Dispatch follows the Site's frozen `source-priority` Site Control (the Kobo
  template ships `[pv-array, battery, generator]`); the model never substitutes
  another order.
- Generator charging accepts only power absorbable by load and battery/PCS
  headroom; the rating is a ceiling. Fuel is checked before energy is accepted.
  The linear fuel law (no idle or start fuel) is disclosed as a simplification.

Demo values, reviewed again at T025b's hands-on check: start 35 %, stop 90 %
(prolonged) against 60 % (changed policy), minimum runtime 30 min, 40 kW,
0.3 L/kWh, tank 400 L starting at 300 L.

## 2026-09-30

Decision: `D-2026-09-30-lab-cockpit-cadence`.

Status: **ACCEPTED by the owner, 2026-09-30.** The owner requested
Architect consideration of `Docs/lab-cockpit-proposal.md` (aeb4c99) and
accepted the resulting cadence and conditional L2 rule.
It is a scoped addition to the planning basis in
`D-2026-09-24-v4-roadmap-replan`: v4 still governs mechanisms and the corrected
roadmap plus adopted queue decisions govern demo outcomes/order. Motivation
images remain Lab presentation guidance, not capability or operator-navigation
authority. The untracked technical walkthrough is explanatory context only.

Adopt L1/L2/L3 now that T025b is complete and A accepted. Split L1 into
two reviewable vertical slices: L1a durable history/charts/header (C2/C6), then
L1b runtime SLD/timeline/requested-versus-accepted/playback (C1/C3/C4/C5).
Place both before T026, sequentially. They touch the same host, observation
and projection seams as T026, and the shared checkout permits one editor.
Parallel implementation is not justified by frontend separation alone.

L2 is conditional: a slice adding runtime, reporting or intervention facts
updates their appropriate cockpit representation and persistence proof. Pure
product analytics/economics need no new private chart. C7's existing inspector
continues; its richer layout, C8 health/log breadth and C9 authoring remain
feedback-selected L3, normally after T036. T026A remains unscheduled and a
prerequisite of nothing. B/C/D/H and the four demo points keep their meanings.

Reason: SLDs and day curves make existing physics and evidence loss reviewable
before domain-expert feedback. Complete history is a real storage/readback
change, so "one presentation slice" understates L1. Deferring health/authoring
breadth protects the first Finding path.

The owner accepted the delay of T026 and conditional L2 on 2026-09-30.
The Planner's task/sequence amendment follows
`.ai/PLANNING_HANDOFF_LAB_COCKPIT.md`; implementation is not activated here.

Decision: `D-2026-09-30-lab-cockpit-history`.

Status: **ACCEPTED by the owner, 2026-09-30.** Persisted history is option (a)
for the cockpit slices; reading never re-executes an old run.

Persist complete compact Lab history with the host-owned execution artifact,
and expose it through a neutral gated Lab projection. Do not re-execute on
read. Existing T024 electrical summaries and T025 generator series/transitions
are retained; add missing per-address interval detail, stock samples, complete
observation attempts and applied-event/bound history. The capped recent-report
tail and latest-only controls/flows are not substitutes for historical data.

Use an explicit history/artifact schema, lossless numbers, typed enums,
address/time/unit provenance, recorded coverage and integrity bound to the
run/version manifest. Each fact is stored once rather than persisting a
cumulative snapshot at every boundary. COMPLETED and FAILED results reload
with their recorded extent. L1 introduces no durable resumable execution;
lost live sessions retain INTERRUPTED semantics. Old artifacts retain their
recorded series and disclose absent history rather than generating it anew.
Unknown or damaged schemas remain unreadable without overwrite.

Reason: frozen inputs and determinism cannot supply an old kernel/profile
implementation that is no longer present. A read must preserve the result
actually recorded. Private storage belongs to the composition leaf, not a
product repository or evidence schema. Single-run history must not recreate
T022A's whole-store read cost. Detailed readback/size and version-transition
guidance is in the handoff; an artifact addition alone does not move the
execution contract under `D-2026-09-22-contract-version-scope`.

Clarified 2026-09-30 (T025e Addendum B; Architect: Claude under the temporary
binding): charts read quantities the host recorded. When a chart needs a derived
total, the host records it and the chart reads it. The client never computes it.
For PV output and signed battery power, the host already records both in the
projection's electrical steps, and the gated history carries those rows as-is.

Decision: `D-2026-09-30-lab-cockpit-presentation`.

Status: **ACCEPTED by the owner with the cadence, 2026-09-30.** The underlying truth,
timing and source-health seams are already settled; no new owner domain choice
is needed to apply them.

Use one selected boundary/interval across charts, timeline, SLD and control
inspection. Preserve stock-at-T versus preceding-interval measurements and
generator state-at-T versus state-for-step. Plot reports at their actual
source time; stale retained values are labelled inspection context, never new
samples. Missingness breaks reported traces, not the physical series. Units
and addresses remain distinct and exact values remain inspectable.

Reuse the configured SLD substrate through presentation slots, with run-bound
topology and verified address/path mapping. Lab overlays are composed outside
the shared renderer; it imports no simulator, Lab contract, shell or gate.
Unknown topology or branch values remain unavailable. Arrows represent
accepted branch transfer, not invented electrical detail.

Auto-play schedules guarded Step requests sequentially in the browser.
Pacing changes wall delay only. Pause stops future requests; an in-flight
accepted step may finish. Refusal/error stops scheduling and refreshes the
authoritative position before explicit resume. No catch-up bursts, live
injection, mutable timestep, reset or server clock is added.

Record a text companion beside the Motivation images using the handoff's
annotation: replace one-second/100x promises with frozen boundary/pacing;
replace live Quick Actions with T029A's declare/freeze/new-run mechanism;
separate device quality from accepted-evidence source health; omit default
cold-room physics and all unbacked voltage/breaker/weather values. Distinguish
staging from Commit/acceptance. Screens 4-5 authoring and 8-9 dashboards remain
conditional followers. These corrections implement canonical fidelity, not
pixel fidelity to known errors.

Reason: an attractive cockpit must not silently change what its timestamps,
values, arrows or controls claim. Product conclusions continue to consume
only accepted evidence, while later gated comparison may read those product
results beside private truth without supplying truth to analytics.

## 2026-09-30

Decision: `D-2026-09-30-architect-reviewer-claude-until-reset`. Codex hit its
usage limit during the Architect review of the T025d cockpit layout and
playback flicker, with reset at 2026-10-03 21:23. The user set Architect and
Reviewer to Claude until that reset; Planner stays Codex. Passes produced under
this exception say so in their report. Revert the bindings in
`.ai/ROLE_CONFIG.md` once the reset has passed.

Affected files: `.ai/ROLE_CONFIG.md`.

Decision: `D-2026-09-30-planner-claude-until-reset`. The user extended the
temporary Claude binding to Planner until the Codex reset at 2026-10-03 21:23,
following the same planning guidance. Revert with Architect and Reviewer.

Decision: `D-2026-09-30-t025e-live-follow`. The owner accepted T025d and chose a
dedicated slice T025e before T026 for cockpit organisation and playback
smoothness (`.agent/T025e-architect-guidance.md`). The owner also decided that
T025e **includes live follow**: the SLD, interval inspection, charts and
timeline stay current during playback, with high-quality state updates and no
flicker. This replaces the T025d read-history-on-stop policy; the mechanism is
set by the Architect addendum to the guidance file.

Affected files: `.ai/ROLE_CONFIG.md`.

## 2026-10-01

Decision: `D-2026-10-01-run-binds-scenario-to-site`.

Status: **ACCEPTED by the owner, 2026-10-01**, adopting the Architect's
recommendations in `.agent/scenario-site-targeting-architect.md` (revision 2).
Recorded by the Planner, Claude under `D-2026-09-30-planner-claude-until-reset`;
the Architect advisory was also Claude under the matching exception, and its
contract-version reading goes back to Codex in T025g's first review.

**Trigger.** T025a and T025b added generator properties, a status signal and
its mapping to `kobo-mini-grid-60kw` in place at `template_version: 1`. A site
created from the earlier v1 (KOBO-001) and one created from the later v1
(GONDAR-01) carry the same lineage and different content, and the shipped
`kobo-mini-grid-prolonged` named KOBO-001, the site that cannot honour it. The
only workaround was an untracked scenario copy naming a different site.

**The rule.** A run binds a scenario version to a site version. A scenario
version declares the contract a site must honour - the addresses and sources it
acts on and reads, the site controls it relies on, and (later) checked purpose
assumptions - and never names a site, not even as a default. A site never names
a scenario. The user chooses the site at run setup. Run setup never infers,
substitutes or defaults either side; it evaluates the contract (document, the
chosen model profile's bindings, assumptions) against the chosen site, freezes
what it found, and rewrites neither document. Whether a site can honour a
scenario is asked of a (scenario version, profile version) pair.

**Retirement and legacy acceptance.** `target_site`, `DECLARED_SITE` and
`TEMPLATE_DERIVED` are retired from new and shipped documents; a guard over
`config/scenarios` keeps them out. A well-formed legacy `target_site` stays
accepted on existing documents, is no longer required, is labelled "legacy, not
used to bind runs" and is ignored by run setup. Every other key stays strict.
Without this the owner's `var/scenarios` copies would take the whole catalog
down. Acceptance continues until the owner retires those copies; no agent edits
or deletes `var/` data (KOBO-001, the scenario copies, runs).

**No template hint.** A scenario carries no template id or archetype field: a
template is the origin of a family of sites, so ranking or filtering sites by
it would choose by lineage rather than contract, and KOBO-001 had the right
lineage and the wrong content. `purpose` prose may still mention an archetype.

**Purpose assumptions label, they do not refuse.** When a later authored purpose
assumption does not hold on the chosen site, the run is labelled, not refused
or blocked. That slice (T025i) is therefore a pure widening and does not move
the execution contract.

**Versioning.** Any content change to a shipped template or shipped scenario
bumps its version (`supersedes` set, new valid-from), enforced by a pinned
fingerprint per `(id, version)`: changed content at an unchanged version fails.
`kobo-mini-grid-60kw` moves to v2 now (T025f). GONDAR-01 is left as it is: it
holds v2 content but records v1, and it is local data; the staleness label will
call it stale, which is true of its record. Removing `target_site` is a content
change, so every shipped scenario moves to v2 in T025g.

**Contract.** Removing the target refusal changes the outcome of documents that
were already valid, so T025g moves `EXECUTION_CONTRACT_VERSION` 9 -> 10 under
`D-2026-09-22-contract-version-scope`. Codex confirms the reading in T025g's
first review.

**Contract clause amended, 2026-10-01: no move. Owner signed off 2026-10-01 ("proceed").** T025g
phase 1 stopped before writing code because the clause above cannot hold
together with T025g's own acceptance criteria. The Architect (Claude under the
same exception) rules that the version stays at 9, and recommends the owner
sign the reversal.

- **The premise was false.** The Architect's revision 2 said every version-9
  run "regenerates identically" after a move.
  - In fact, `refuse_incompatible_execution` refuses any frozen version other
    than the build's, so all 15 contract-9 gate Drafts would be refused before
    they execute.
  - Re-stamping them changes `frozen_inputs_identity`, because the version is
    hashed, and the Lab artifacts embed the build version.
  - So the move would make every existing run unexecutable while the kernel is
    unchanged.
- **The reading was also wrong on its own terms.**
  `D-2026-09-22-contract-version-scope` measures the frozen artifact replayed
  against a newer build. Under that test this slice is a pure widening:
  - with legacy acceptance, no existing document stops parsing or changes
    meaning;
  - every run frozen under the old rule joined a scenario to its declared
    site, a join that is still allowed and that freezes identical world inputs;
  - `target_site` was never a kernel input.
- **"Refused becomes READY" is not a move signal.** The earlier argument relied
  on run setup now accepting requests it used to refuse. That decision already
  rejects this as a test, because under a strict parser every change flips
  refuse/run for some request.
- **Rejected alternatives:**
  - accepting both 9 and 10 empties the refusal rule;
  - re-capturing the gate at 10 destroys its baseline;
  - redesigning the gate to pin 9 in a test-only patch works, and is the
    fallback if the owner keeps the move, but it edits the contract-9 gate and
    leaves a refusal message that is false for version-9 Drafts.
- **Guardrail.** Frozen template lineage stays out of `FrozenWorldInputs` and
  `frozen_inputs_identity`. The unchanged contract-9 gate is the proof.

The purpose-assumption clause above is unaffected: labels do not move the
version. Codex still reviews this reading retrospectively.

**Sequence.** T025f (template versioning) and T025g (the run is the only join)
before T026; T025h (compatibility status in the picker, a dry-run of the same
setup resolution, never a second matcher) after T026; T025i (purpose
assumptions) after T026 and before T036, or earlier if the owner wants the label
for the C/D demo.

**Supersedes and amends.**

- The T019 run-setup site rule ("a run is not the place to retarget a
  scenario"; run setup does not choose a site for a template-derived scenario),
  which lived only in `runs/service.py` `_refuse_unsupported_target`: superseded
  by the rule above. T025g removes it and keeps the no-topology refusal.
- `D-2026-09-20-scenario-detail-affordances`: amended. `Open target Site` is
  removed because a scenario has no target; the detail screen shows what the
  scenario needs of a site instead. Compatibility is shown only in run setup,
  where a profile is chosen. The rest of that decision stands.

**Known gap, carried.** The scenario store holds one document per
`scenario_id`, so a superseded scenario version survives only in git and in the
frozen runs that used it (which freeze parameters, causes and forcings, not the
purpose text). Recorded in `.ai/MILESTONE_REVIEW_BACKLOG.md`.

Affected scope: scenario parser and models, run setup, `EXECUTION_CONTRACT_VERSION`,
shipped templates and scenarios, scenario detail and run setup screens, tasks
T025f-T025i, `tasks/README.md`.

## 2026-10-02

Decision: `D-2026-10-02-delay-is-a-reporting-path-cause`. **A delayed
publication is declared by the scenario as a reporting-path cause, and the
publication profile answers whether and how the installation can model it.**

Architect ruling for T026 (Claude under the Codex-reset exception in
`.ai/ROLE_CONFIG.md`; Codex reviews it retrospectively).

- **Why the scenario.** Ownership follows `D-2026-09-21-physical-property-ownership`:
  the scenario says what happens, the publication profile how the reporting
  installation behaves. One delay at one time is something that happens; the
  shipped precedent is the fuel-level reporting gap, a `FORCING_INPUT` window on
  a `*-reporting-availability` state that the publication profile must declare
  it can model (`D-2026-09-22-forcing-state-requirements`), else run setup
  blocks naming the profile. A delay takes the same path and the same answerer.
  Putting it in the profile alone would make a profile version mean one run.
- **What it may not do.** It changes publication time only. The value and
  source time are the observation transform's, so amendment 1 (f), "a scenario
  does not author what a device reads", holds. The world trajectory and
  controller decisions are identical with and without it.
- **Bound.** A declared delay that would release a publication after a later
  one is refused at run setup: release order, buffering and recovery are T026A.
- **Records.** Operational records (override/command) take the same seam for
  their missing and delayed cases.

Affected scope: scenario reporting-path causes, publication profiles,
`host/execution_adapter.py` `reporting_inputs`, T026, T026A.

## 2026-10-02

Decision: `D-2026-10-02-template-bump-record`. **A shipped template records a
version bump by `template_version`, its pinned fingerprint and a header note.
The `supersedes`/valid-from wording in `D-2026-10-01-run-binds-scenario-to-site`
applies to scenarios only.**

Architect ruling for T026 (Claude under the Codex-reset exception), closing the
T025f backlog item "Decision wording, routed to the Architect". **Owner
signed off 2026-10-02**: it narrows the wording of an owner-accepted clause.

- **Narrow, do not add fields.** Template versions are a linear integer per
  `template_id`; the previous version is implied, and no run reads a template
  (lineage stays out of `FrozenWorldInputs`). A `supersedes` field would repeat
  `template_version - 1` and a valid-from would claim a time the catalog never
  consults. If templates ever branch or are time-selected, that slice adds the
  fields.
- **New device signals are template content.** T026's PV available-capability
  and BMS discharge-capability signals and mappings bump
  `kobo-mini-grid-60kw` to v3. A typed `UNAVAILABLE` on v2 is not an
  alternative: a signal the site does not configure is not a reporting path,
  and publishing unavailability for it would invent one. Existing sites read
  `BEHIND`, which is true. Operational records are not template signals; the
  frozen gateway mapping declares their source against existing components.

Affected scope: `config/site-templates/kobo-mini-grid-60kw.yaml`,
`backend/tests/test_site_template_fingerprints.py`, T026.

## 2026-10-02

Decision: `D-2026-10-02-demo-led-recommendation`. **The owner approved the
Architect's demo-led recommendation, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` at
`57ea23e`, on 2026-10-02. Its near-term sequence (section 7) supersedes the
queue order of `D-2026-09-24-queue-resequenced-for-demo` from T027 onward.**

The recommendation was produced by the Architect (Claude under the Codex-reset
exception in `.ai/ROLE_CONFIG.md`); this entry was recorded by the Planner
(Claude, same exception). Codex may review both retrospectively.

**Owner records.** `.agent/owner-instruction-final-recommendation-2026-10-02.md`
(the instruction to produce the final version and then guide the Planner) and
`.agent/owner-approval-final-recommendation-2026-10-02.md`. The owner's
approval, verbatim:

> review looks fine.

**The owner's dispositions (recommendation 8.1, verbatim):**

| Decision | Owner feedback |
| --- | --- |
| D1 filtered grouped root menu | Accept, but don't promise the full v6.9 end-state can never change |
| D2 Portfolio-lite after T034 | Strong accept |
| D3 Kobo detect→verify uninterrupted | Strong accept |
| D4 opportunity before fuel; service before battery | Accept as priority intent, dependency-check before exact reorder |
| D5 static mini-grid archetype descriptor | Accept with narrower authority |
| D6 Site Evidence at T027 | Accept, but T027 = source/coverage; analytic claim readiness matures from T028 |
| D7 Action + Foundation Changes representation | Accept; very coherent |
| D8 park T025h | Accept |

Owner's summary: "Adopt the sequencing and product-surface recommendations,
but loosen unnecessary loyalty to rendered canonical navigation, narrow the
domain descriptor's authority, and distinguish source-evidence readiness at
T027 from claim-capability readiness that emerges with analytics at T028+."

**Section 9 outcomes: the coordinator's reading, not the owner's words.** The
owner said "review looks fine." and gave no different answer on any section 9
item; the coordinator read each item as taken at the recommended option (as
recorded in the approval file). The owner may correct any of these readings:

1. Global Financials stays open; decide after T036.
2. BusinessContext is site-scoped in T029, with "shared or portfolio assumption
   sets" as the trigger to revisit global Financials.
3. "Labelled in place" is not used in operator views (narrowed, not retired
   everywhere); rendered tabs are filtered per capability, not per site
   (`D-2026-10-02-rendered-tabs-per-capability`).
4. Work off the point-2 journey may move to a thin follow-on after T029.
5. Opportunity-first is accepted with its two-slice cost (T031 and T032 ahead
   of T030), subject to the Planner's dependency check (recommendation 6.3).
6. No cold-chain screens in the polished demo.

**Journey and demo story.** The recommendation's journey (5.1, "Kobo runs
uninterrupted": detect, explain, monetise, intervene and verify in one run,
breadth after, Lab last) supersedes the walk order in
`Docs/mini-grid-demo-architecture-and-roadmap.md` sections 5 and 13.3 for demo
purposes. The roadmap is an owner source document and is not edited; the
queue's demo story and demo-point table live in `tasks/README.md` and
`.ai/PRODUCT.md`. Roadmap and v6.9 text that this decision overrides are not an
acceptance oracle against it (`D-2026-10-02-grammar-ownership-test`).

**Carried rules** each have their own entry so tasks cite exactly what they
rely on: `D-2026-10-02-rendered-tabs-per-capability`,
`D-2026-10-02-grammar-ownership-test`,
`D-2026-10-02-presentation-profile-and-capability-declaration`,
`D-2026-10-02-demo-point-seed-rule`.

Affected scope: `tasks/README.md` order and demo points, T025h (parked), T027,
T028, T029, T029B (new), T029A, T034, T034A (new), T030-T033, T035, T036,
`.ai/PRODUCT.md` demo milestones, routing in `.ai/START_HERE.md` and
`.ai/ACTIVE_CONTEXT.md`.

## 2026-10-02

Decision: `D-2026-10-02-rendered-tabs-per-capability`. **The rendered tab set
holds only meaningful destinations, decided per capability, not per site; and
"labelled in place" is not used in operator views.**

Recorded by the Planner (Claude under the Codex-reset exception) from the
approved recommendation 2.4 and section 9 item 3 (coordinator's reading; see
`D-2026-10-02-demo-led-recommendation`).

The owner's rule, verbatim: "The canonical tab set defines ownership and
future placement; the rendered tab set contains only meaningful destinations
unless absence itself communicates something useful."

- **Per capability, not per site.** "Meaningful destination" means this build
  has a truthful surface for the aspect, not that this site has data for it.
  Once a capability exists, its tab renders on every applicable site, and a
  site without the evidence shows the gap inside the tab. In-page gaps are
  ordinary claim discipline, not an exception to the rule.
- **Applicability is a separate filter**, from the presentation profile and the
  backend capability declaration
  (`D-2026-10-02-presentation-profile-and-capability-declaration`), never from
  data presence.
- **"Labelled in place" is not used in operator views.** The other two
  Presentation Honesty treatments (not rendered; disabled with a stated reason)
  stand unchanged. This narrows the treatment; it is not retired everywhere.
  Checked on 2026-10-02: no non-operator surface renders it today. The only
  non-operator mentions are code comments (`frontend/src/shell/simulatorLabRoutes.tsx`,
  `frontend/src/ui/DataTable.tsx`); T027 phase 1 updates them with the
  operator code.
- **Rendered Site tabs by milestone**, one canonical inventory filtered by
  capability, in canonical order: T027 three (Overview, Foundation, Evidence);
  T028 five (+ Performance, Findings); T029 six (+ Financials); T034 seven
  (+ Work); T033 eight (+ Health, between Foundation and Performance).
- **Foundation** renders `Definition | Topology | Controls`, plus `Changes` from
  T034. `Readiness` is not rendered: claim readiness lives on Site > Evidence
  only.
- **Site > Work** renders the Actions index with no subtab row while the WORK
  group holds only Actions.
- **Other contextual sets:** Finding detail `Overview | Evidence | Alternatives`
  at T028, with Recommendation and History at T034; Action `Overview |
  Verification` at T034, the rest when they have content.

**What it amends.** `D-2026-09-13-canonical-fidelity` (the "three treatments"
rule's middle treatment, and its application of labelled-in-place to Site
tabs) and `D-2026-09-17-foundation-screen-architecture` (six Site tabs and
Foundation > Readiness labelled in place). Those entries are not rewritten.
What still stands in them: content before chrome; absent versus disabled;
parameterless routes are not destinations; replace-never-loosen guards; the
v6.9 tab vocabulary and canonical order as the ownership set.

Implementation lands in T027 phase 1 (filter changed, labels removed,
`tools/checks/navigation-truthfulness.ps1` and its tests updated without
loosening: a tab the build cannot open is not rendered, never disabled, and
never labelled in place in operator views) and T034 (Foundation > Changes).

Affected scope: `.ai/ARCHITECTURE.md` Presentation Honesty,
`frontend/src/shell/operatorSiteTabs.tsx`,
`frontend/src/sites/FoundationSubtabs.tsx`, their tests,
`tools/checks/navigation-truthfulness.ps1`, T027, T028, T029, T033, T034.

## 2026-10-02

Decision: `D-2026-10-02-grammar-ownership-test`. **A place in the navigation
grammar keeps its slot only if it owns something no other place shows; every
exception is recorded.**

Recorded by the Planner (Claude under the Codex-reset exception) from the
approved recommendation 2.2 and owner disposition D1 (8.1, 8.2).

- A place keeps its slot only if it **owns** something no other place shows:
  objects, a workflow, or site-owned content.
- A proposed exception names what would be lost by removing or moving the
  item, and what currently duplicates it.
- Every exception gets a `DECISIONS.md` entry. A task that cites v6.9 or
  roadmap text that a decision overrides cites that decision too, so v6.9 is
  not used as an acceptance oracle against an owner ruling.
- **D1's carry.** The grouped root menu (OPERATE, INTELLIGENCE, WORK,
  ASSURANCE, BUSINESS) is the target and the reference, not frozen; the
  owner's wording: "Accept, but don't promise the full v6.9 end-state can
  never change". The demo rail is filtered to live items: T027 Sites only, no
  header; headers from T028 (OPERATE: Sites; INTELLIGENCE: Findings); WORK:
  Actions at T034; Portfolio before Sites from Portfolio-lite (T034A); Assets
  after Sites at T033; ASSURANCE: Evidence at T036 only if it passes this test
  with its own entry. Layout evidence from T028 covers a one-item group.

Affected scope: rail and tab growth in T027-T036, global Evidence at T036,
global Financials (open; `D-2026-10-02-demo-led-recommendation` item 1).

## 2026-10-02

Decision: `D-2026-10-02-presentation-profile-and-capability-declaration`.
**Domain presentation is static substrate data keyed by `site_type`; which
analytics, Finding types, evidence requirements and verification rules exist
is owned by the backend through an analytic capability declaration born in
T028.**

Recorded by the Planner (Claude under the Codex-reset exception) from the
approved recommendation 4.3 and owner disposition D5.

- **`DomainPresentationProfile`** owns only: overview domains (which cards
  exist, and their order); performance views (subtab list and order); health
  emphasis; labels and vocabulary; consequence presentation. It is substrate
  data selected from the read model's `site_type`. `site_type` is domain data,
  not a shell, mode or variant discriminant.
- **The backend owns the rest.** The owner's boundary, verbatim: backend and
  domain modules remain authoritative about "what findings actually exist",
  "what evidence an analytic requires" and "what verification rules exist";
  "The descriptor can reference those capabilities, but shouldn't become the
  canonical source for them." The failure it prevents: "frontend pack says
  this Finding exists / backend analytic says something different".
- **Analytic capability declaration** (born in T028; verification rules join
  at T034): each analytic declares its id and applicable site types, the
  Finding type it may emit, required and optional evidence, and claim levels.
  The backend serves the evaluated, site-scoped version as a read model. A
  `tools/checks` guard copies the rigour of the simulator model-profile
  pattern, not its data: product analytics may not read
  `EXECUTION_REQUIREMENTS` or any private or simulator flow.
- **Three rendering rules**, applying to backend-served capability ids
  (Performance subtabs, a card's assessment slot, Evidence capability rows,
  Finding types), not to the profile's Overview domain cards: (1) a backend id
  the profile does not know still renders, with the backend's display name in
  a default position; (2) a profile id the backend does not serve renders
  nothing, and a test flags the orphan; (3) a gap is shown only from backend
  state, never from the profile.
- **Timing:** write the profile the first time a second Overview card or
  Performance subtab appears; no hard-coded card or subtab lists in shared
  frames.

Affected scope: `.ai/ARCHITECTURE.md` Shared Presentation Substrate, T027
phase 2 (profile born), T028 (declaration born), T030-T033 and T035 (each
analytic joins), T034 (verification rules join).

## 2026-10-02

Decision: `D-2026-10-02-demo-point-seed-rule`. **Each demo point ships with an
idempotent, rehearsed seed, owned by the slice that creates the point, checked
with the Lab gate off.**

Recorded by the Planner (Claude under the Codex-reset exception) from the
approved recommendation 5.2.

- Idempotent: loading the seed twice neither double-ingests nor duplicates a
  site. Data enters through normal ingestion, never hand-staged.
- Rehearsed: the owning slice walks its demo point's journey on the seed and
  documents the seed command in its packet.
- Owners: point 1 (T027) is a live run and needs no seed; point 2: T029 (Kobo
  healthy and prolonged-runtime windows); point 3: T034 (Kobo's post-action
  window) and T034A Portfolio-lite (three sites); point 4: T036 (whatever
  sites remain). Breadth slices T030, T031/T032, T033 and T035 each own the
  recipe and seed of their own site (Architect reading, planner guide
  section 5; the "never hand-staged" wording above is Planner wording).

Affected scope: T029, T034, T034A, T030-T033, T035, T036.

## 2026-10-04

Decision: `D-2026-10-04-analytic-readiness-scope-and-gap-impact`.
Decided by Codex Architect under the owner's delegated decision authority in
`.ai/ROLE_CONFIG.md`; reasoning and implementation consequences are in
`.agent/T028-architect-readiness-decisions.md`.

Analytic readiness is a backend-owned assessment of evidence sufficiency,
distinct from Site operational condition, setup progress and source health.
T028 scores all accepted Site evidence and latest active assessments, not the
Evidence page's selected window. Full describes signal availability and the
absence of claim-limiting gaps in assessed portions; it does not assert fresh,
continuous or selected-window coverage. Zero assessed intervals is disclosed.
None must respect the analytic's supported alternative reconstruction inputs.

T028 retains an explicitly interim claim-dependent coverage-gap rule: gaps
that limit a classification lower readiness; other gaps remain visible.
Required-input absence and optional-context absence remain distinct. The
permanent gap policy is deferred at the owner's request. T028A, Configurable
analytic evidence-gap impact, owns a versioned backend configuration and its
small inspection/editing surface, to be planned after T029 point-2 feedback;
it is unscheduled and gates none of the existing demo spine.

Gap impact type controls the readiness consequence of missing evidence per
analytic requirement. It cannot invent evidence or weaken prerequisites for
an actual claim. Stricter coverage requirements may lower readiness without
changing a valid assessment. Policy version and scope travel with readiness;
readiness-policy changes preserve evidence and assessment history. Actual
classification changes require analytic versioning. Presentation profiles
remain presentation only.

Reason: keep the one-analytic demo honest, distinguish coverage from its
effect on a claim, and preserve the owner's configurable-policy direction
without broadening T028. Affected scope: T028 AC20, T028A planning/backlog,
T029B coverage composition and later analytic/portfolio consumers.

## 2026-10-04

Decision: `D-2026-10-04-practitioner-first-finding-presentation`.
Decided by Codex Architect under `.ai/ROLE_CONFIG.md` delegated authority;
reasoning and bounded implementation direction are in
`.agent/T028-architect-audience.md`. This is not owner slice acceptance.

The primary audience of T028 product surfaces is mini-grid practitioners,
including operations and asset managers and technical reviewers. The first
reading of a Finding explains the operational conclusion, affected period,
supporting facts, uncertainty, bounded consequence and investigative next
step. Assessment identifiers, digests, model versions, exhaustive signal
coverage and calculation inputs remain inspectable through existing evidence
surfaces or expandable details. Material claim limitations, unavailable
bounds and missing evidence remain visible with the conclusion.

T028 receives a narrow copy and information-emphasis correction before merge,
preserving the accepted six-part Finding hierarchy and existing navigation.
Backend ownership of assessment semantics, evidence, confidence and readiness
is unchanged. Readiness remains site-wide evidence sufficiency, with the
scope and limitations established in
`D-2026-10-04-analytic-readiness-scope-and-gap-impact`; it is not operational
health or permission to act. Investigative guidance does not constitute an
operational recommendation or authorized control change.

T029 retains bounded financial translation, client-facing assumption review
and the seeded, Lab-off point-2 demo. T034 retains recommendations, action and
verification. Broader presentation changes follow practitioner feedback; no
new persona mode or navigation framework is introduced.

Reason: the first useful Finding must be understandable to its intended
reader while remaining challengeable. Technical correctness and exhaustive
provenance alone do not establish practitioner usefulness. Affected scope:
T028 presentation closeout, T029 planning and later Finding presentations.

## 2026-10-04

Decision: `D-2026-10-04-plain-language-analysis-views`.
Codex Architect, implementing the owner's direction recorded in
`.agent/owner-T028-presentation-direction-2026-10-04.md`; specification and
reasoning in `.agent/T028-architect-presentation.md`.

Amends `D-2026-10-04-practitioner-first-finding-presentation`: operator defaults
assume minimal technical knowledge and communicate operational meaning,
affected time, uncertainty, bounded consequence and investigative next steps
with plain text and labelled graphics. Deeper method, inputs, coverage and
calculation belong in a separate Analysis destination, replacing the earlier
disclosure-only correction and mandatory report-like layout. Important limits
remain visible with the default conclusion.

Amends the Finding-tab inventory in
`D-2026-10-02-rendered-tabs-per-capability` and T028 AC21 to
`Overview | Analysis | Evidence | Alternatives`. Recommendation and History
remain T034. Performance keeps Dispatch as its sole capability subtab, with
local `Overview | Analysis`; Site Evidence has local `Overview | Analysis`.
Cards and indexes link to the matching analysis rather than duplicating it.
These contextual views own interpretive detail; Evidence retains source
lineage and Alternatives retains competing explanations, satisfying
`D-2026-10-02-grammar-ownership-test`. Per-capability rendering and truthful
empty states remain unchanged.

T028 delivers a shared assessed-period timeline, bounded fuel-range graphic,
selected-period input comparison and coverage-count graphic from backend-served
assessment data only. No private simulator data, interpolated telemetry,
invented savings or new analytic conclusion enters the presentation. Backend
semantic ownership and persisted assessment history remain unchanged.

Product copy, including Analysis and Evidence, uses operational language and
excludes simulation/development terms such as run and binding. Lab vocabulary
is excluded from this restriction. A focused rendered-text guard covers the
T028 journey, with explicit exceptions only for source-owned references and
user-owned text. Stored identifiers and provenance remain intact; demonstration
data is not represented as field evidence. Remaining legacy product copy is
assigned a follow-up after T029, without allowing new jargon in the meantime.

Both presentation checkpoints land in T028 before merge. T029 retains money,
assumptions and the prepared external demo; T034 retains recommendations,
action and verification. The evidence-sufficiency scope and limits in
`D-2026-10-04-analytic-readiness-scope-and-gap-impact` are unchanged. This
decision records architecture direction, not owner slice acceptance.

## 2026-10-07

Decision: `D-2026-10-07-s2-edge-split-and-demo-source`.
Codex Architect, following the owner's S2 dependency review and source-choice reply. This is an Architect planning/contract decision, not task completion or owner acceptance of a product tier.

Split the former S2-01 outline into three reviewed tasks: **S2-01a** makes imported Kobo Lab Draft/run use the selected effective Postgres Foundation and SignalBinding snapshot and records its revision/hash; **S2-01b** makes simulated public reports pass through a separate SQLite-backed V3 gateway/outbox; **S2-01c** publishes GatewayDiagnosticsV1 locally and demonstrates disconnect/retry and disk pressure. S2-02 retains authenticated central Evidence and diagnostic receipt plus the owner checkpoint. Kobo's imported Lab Draft/run/Commit path remains deliberately blocked after S1-01 until S2-01a restores Draft/run from registered basis; Commit remains blocked until S2-02. Unimported legacy YAML Sites retain their existing boundary.

For the S2–S7 demo, the **one source in effect is simulated device input**. S2 does not claim a physical protocol parser or equivalent physical batch. The first real pilot must choose a real controller/meter/BMS capture if available, or a clearly labelled synthetic fixture built from vendor protocol documentation. That pilot gate checks frames/register scaling, units and device clocks, then compares the shared downstream path. No captured-device battery fallback is available for the current demo.

Resolve `A-edge-batch-signature` by **deferring per-batch cryptographic signatures and key rotation for this pilot**. Batch V2 keeps registered TLS gateway credentials, canonical SHA-256 payload digest and exact-byte retry. A future security requirement may activate signing only after amending the technical design, Batch V2 wire contract and test vectors. Signing implementation nodes remain open outside the S1–S7 queue; this decision does not claim they are built.

The S1-02 gateway configuration snapshot is versioned, content-hashed and delivered over an authenticated channel in this queue. Earlier "signed snapshot" wording does not require detached cryptographic signing or key rotation. A later decision to require that must define keys, verification and rotation explicitly.

Resolve `A-edge-diagnostics` with a separate authenticated GatewayDiagnosticsV1 report and append-only central `gateway_diagnostic` table. The gateway sends local sequence, observed time, source-contact and queue/disk/clock diagnostics independently of telemetry; the server records receipt time, enforces gateway/site scope and idempotent identity, and derives freshness from its receive time and declared cadence. Diagnostics are operational state, never AcceptedEvidence or an asset-health claim. Sections 1, 3 and 4 of the technical design define the table, wire and API.

Resolve `A-demo-scenarios` for the queued path: each fixture manifest separates public device reports, expected missing/contradictory/late cases and private Lab oracle. S6 verification uses **two separate runs**: a baseline under the old effective Foundation/policy and a later run under the new persisted revision. No mid-run policy change is required of the kernel. S7 battery stress stays Unknown unless a causal simulated public observation is implemented; optional producer `I-sim-battery-cases` is not counted as committed S7 work. This keeps unsupported replacement exposure withheld.

## 2026-10-08

Decision: `D-2026-10-08-s1-bindings-roles-and-snapshot`. Codex Architect, resolving the six S1-02 Implementer questions under `.ai/ROLE_CONFIG.md`. This is an Architect contract resolution, not owner slice acceptance or the combined S1 review. Detailed rationale and implementation directions are in `.agent/architect-S1-02-answers-2026-10-08.md`.

Adopt `minigrid-roles-1`: required generator_state (GENERATOR/state), generator_power (GENERATOR/kW), feeder_demand (LOAD/kW, every declared load), battery_soc (BATTERY/%) and battery_reserve (BATTERY/%, Foundation control). Other channel roles are optional: pv_power (INVERTER/kW), pv_irradiance (PV_ARRAY/W/m2), battery_power (POWER_CONVERSION_SYSTEM/kW), fuel_level (FUEL_TANK/L). Channel roles other than feeder_demand permit one binding per Site in this slice. Coverage is configuration only, never observed health or reporting.

Explicitly authorize adding generator-controller/status (state) to the registered simulated Kobo Foundation during the atomic conversion. It uses the existing device source and is recorded as a new declaration, not original YAML content or an observed capability. Preserve the original YAML, immutable import revisions and all period-specific control values. Battery reserve remains the selected Foundation's typed reserve-state-of-charge property; no POLICY channel or reserve binding is required.

S1 accepts numeric IDENTITY with equal declared/source/canonical units, and generator-state ENUM targeting STOPPED, STARTING, RUNNING and FAILED. Source unit must always match the Foundation declaration. Defer LINEAR publication until supported unit pairs, coefficients and normalization rules are decided. Kobo retains nine legacy IDENTITY mappings plus the explicitly added status ENUM mapping.

The conversion is effective from 2026-09-29T11:57:49Z and recorded at actual publication time, with Foundation-aligned binding periods through the final open period. Earlier knowledge_at reads retain the former Foundation-only basis. Backdating config does not establish historical observations, release legacy evidence or mutate accepted envelopes.

Persist the canonical combined snapshot SHA-256, schema/canonicalization version and exact registered references in the atomic publication. A separate table is optional; exact historical bytes must remain available or reproducible under a preserved versioned serializer and checked against the stored hash. Independent component hashes alone are insufficient. S1 download uses the fixed development-tenant boundary and is explicitly not authenticated gateway access. S2 adds scoped gateway credentials and consumes the same immutable snapshot contract; detached signatures remain deferred. Broad device authoring, acquisition, analytics and reopening imported Kobo Lab execution remain outside S1-02.

Decision: `D-2026-10-08-s1-foundation-organization`. Codex Architect, responding to owner UI feedback that the Foundation page was too disorganized to verify. Pull forward bounded S1-03 (Site model, Single line diagram, Readiness as three direct-linkable Foundation views at a shared selected period) before S1 merge and S2-01a. Revises the earlier S1-02 D2 ruling: the navigation guard now enforces three supported Foundation views instead of prohibiting a Readiness subtab; Evidence keeps claim/capability readiness. No new data claims or mock values; V-01 stays at its existing gate. Hold the S1-01/S1-02 merge until S1-03 lands and the owner completes the UI check. Full text: `.agent/architect-S1-ui-organization-2026-10-08.md`.

Decision: `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary`. Codex Architect, resolving the Planner's S2-01a questions under `.ai/ROLE_CONFIG.md`. Detailed directions are in `.agent/architect-S2-answers-2026-10-08.md`. This is a contract decision, not S2 implementation acceptance.

For an earlier source time, select the Foundation and binding pair effective then as recorded at `knowledge_at`; default `knowledge_at` to server now and freeze the resolved instant on the Draft. Explicit earlier `knowledge_at` may select a pair since superseded, but only if it was originally recorded at that knowledge time and its original valid periods cover the run's public source times. Persist the selected revisions and verified stored canonical snapshot bytes/hash. A pinned historical download and Lab selection use immutable publication references and stored snapshot identity, not today's mutable gateway/source names or current registration gaps. Keep current gaps visible separately; they still prevent a new/current acquisition snapshot. Missing, unregistered or hash-invalid historical snapshots fail closed. Registration identity immutability remains a separate hardening task; S2-02 authenticates gateway upload and validates original registered identity and validity without treating the development-tenant download as credential authority.

An S2-01a run freezes one registered basis. Every public report source time must lie in both selected revisions' original half-open valid periods. A run crossing a boundary is refused before Draft creation with the boundary named; multiple bases in one run are deferred. The existing kernel reaches the final `end_time` boundary and can emit a public reading there, so setup must also validate that last emitted source time. `end_time` equal to the selected basis's `valid_to` is refused. This prevents knowingly unpublishable S2 evidence. S2-01b consumes that frozen basis; S2-02 accepts later-superseded but originally time-valid references with an outdated flag rather than rejecting them as merely stale.

Amendment to `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` (S2-01a phase-1 questions, Codex Architect): snapshot schema v1 pins configuration and acquisition identities, not the Site row's name, type or timezone. S2-01a may read those valid current-row facts and freeze them on the Draft, but must not describe them as reconstructed at `knowledge_at`. Before a Draft is created, refuse a current Site type inconsistent with the selected binding role set. An unparseable current Site row remains a typed refusal. A future historical-metadata claim requires versioned Site metadata or a new snapshot contract, not a silent read of today's row.

For acquisition snapshot selection, an unsuperseded binding set whose original valid period has not ended is new/current, including a future-effective set; it remains subject to every current configuration gap. An ended period is historical even if its row remains unsuperseded, and a superseded set is historical. A historical read verifies stored bytes and original immutable references and reports today's registration gaps separately; selected Foundation-content gaps still refuse. This classification controls access to the pinned artifact, not whether the gateway is presently healthy or authorized to upload.

Imported Lab device-signal-to-component links come from the selected registered binding rows, not legacy Foundation `signal_mappings`. A bound asset UUID is resolved to a component code in the selected Foundation; an absent or nonmatching code refuses setup, while a binding with no asset stays in the snapshot but supplies no component link. The host must consume these frozen links unchanged. Asset-code mutation can still redirect a valid code before a Draft is frozen: enforce stable asset-code identity at the database boundary, with reconciliation for existing rows, before S2-02 accepts evidence. The broader registration-identity hardening remains a named prerequisite at that boundary, not a reason to invent a snapshot-v2 migration during S2-01a.

Decision: `D-2026-10-08-s2-registered-kobo-demo-configuration`. Codex Architect, resolving S2-01a phase-2 Q4/Q5 in `.agent/architect-S2-01a-answers-3.md`. This is a configuration and demo-scope decision, not S2-01a review or owner acceptance.

S2-01a keeps binding rows authoritative and its honest blocked Drafts. The original Kobo YAML has nine mapped signal links; the registered conversion has those nine plus the separately authorized generator-status declaration/binding. The two capability links (`pv-inverter-controller/available-power` and `battery-pcs-controller/discharge-capability`) belong to the newer shipped template, not the original Kobo import. A publication profile may declare an unbound optional channel; it is unconfigured and cannot yield a report or capability conclusion. Do not refuse the whole Draft solely for that declaration, silently import template links, or derive a component link from legacy mappings.

S2-02 demo setup owns any explicit, new-effective Foundation declaration and binding publication for those two channels before a registered profile-5/capability demonstration. Use typed optional inverter available-power and PCS discharge-capability roles in kW under a new role-vocabulary version, retaining `minigrid-roles-1` for historical interpretation. Until that publication is proven, withhold capability and candidate-dispatch claims. A basic S2-02 accepted-evidence demonstration using already bound channels need not wait for these optional channels; S3-01 must close the carry before claiming candidate dispatch from a registered run.

The imported Kobo Foundation also lacks the four static generator properties needed by `mini-grid` v3. S2-02 demo setup must explicitly publish a later-effective Foundation revision with generator-rated-power, start/stop SOC thresholds and start delay before relying on registered generator evidence. The newer template's 40 kW, 35%, 90% and 5 min values are authorized demo candidates, not facts imported from the old YAML or observations; record their template/demo provenance and the selected effective time. The existing 30 min minimum runtime remains as imported. Initial fuel-tank volume and generator state are scenario-owned causal inputs, not Foundation properties: choose or extend a scenario that supplies them. No historical Foundation, binding snapshot or source evidence is rewritten. S2-01b's gateway contract does not acquire this demo-fixture work.

Decision: `D-2026-10-08-s2-local-gateway-snapshot-transfer`. Codex Architect, resolving S2-01b Planner Q1 in `.agent/architect-S2-01b-answers.md`. Select option 1 for the simulated-only, separate local gateway: the authorized Lab host transfers the exact S2-01a pinned snapshot and public reports over bounded local IPC authenticated by OS peer identity or a protected local host-to-gateway credential. No public configuration endpoint or S2-02 batch-upload permission is added in S2-01b. A loopback address, path permission with indistinguishable peers, run ID, caller-supplied Site/hash or S1 development-tenant snapshot route alone is not authority.

The gateway has a locally provisioned identity and scope independent of each transfer: tenant ID, Site UUID, gateway UUID, `SIMULATED` mode and permitted source UUIDs. It verifies the peer, canonical snapshot bytes/hash/schema and immutable references, internal reference consistency, matching provisioned identities, binding/source membership and valid periods for each report before activation/sealing. The hash detects byte changes but does not authenticate the publisher: in S2-01b the authenticated Lab host is the local issuer of the pinned registered basis; the gateway cannot independently establish historical Postgres registration merely from those bytes. This protected local channel satisfies the technical design's authenticated configuration-channel requirement for this colocated simulated gateway only. A remote/physical gateway needs a separately authenticated server distribution path when introduced.

S2-02 preserves the locally sealed envelope/batch bytes and adds registered TLS gateway credentials for central upload and server-side checks of the original registered identity and validity; local IPC credentials grant neither upload nor a general snapshot-download API. A failed or unavailable local transfer leaves Stage pending/refused, never falls back to YAML or a new/current snapshot. Kobo devices are separate registered source streams, so a registered run may seal multiple Batch V2 objects; each remains homogeneous in source, Foundation and binding reference. S2-01b's acceptance is local staging, not central acceptance.

Decision: `D-2026-10-08-s2-v3-source-payload-and-period-reference`. Codex Architect, resolving S2-01b phase-1 Q1-Q3 in `.agent/architect-S2-01b-answers-2.md`. This fixes wire semantics for phase 2; it is not a review of phase 1.

SourceEnvelope V3 MEASUREMENT carries the device-published value in the registered binding's `source_unit`, after strict canonical source-text validation, not an edge-normalized value. The gateway validates unit and allowed ENUM source label without applying the binding conversion. S2-02 retains those exact envelope bytes as `original` and applies the accepted-as binding conversion centrally to persist `normalized`; it does not invert a gateway conversion to reconstruct the original. A V3 `state` source label must meet the current uppercase member grammar as well as its ENUM map. Kobo does; before another ENUM mapping with a different source-label grammar is claimed acquisition-ready, either constrain its publication or explicitly revise the wire/value contract and vectors. Never silently uppercase or rename a device label.

S2-01b's V3 producer and parser accept MEASUREMENT only. POLICY and OPERATIONAL_RECORD remain named but return `SCHEMA_UNSUPPORTED` until a versioned `record_detail`, provenance and validation contract is decided by the first slice that needs such a gateway record. S2-02 may ingest supported measurements and must not invent a policy or operator record from a Foundation change or Lab-private event. Human-attested operational records retain the separate provenance route described in technical design section 4.

Batch V2 `configuration.foundation_valid_from` preserves the exact UTC spelling in the pinned registered snapshot, including up to six fractional digits; no truncation to whole seconds or regenerated spelling is permitted. S2-02 compares the reference to the stored registered snapshot text and checks the actual half-open valid period at each envelope's source time. Whole-second SourceEnvelope V3 observation times are a separate rule. Retain the phase-1 canonical vectors and sealed bytes under these decisions.

Decision: `D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary`. Codex Architect, resolving S2-01b phase-2 Q1-Q3 in `.agent/architect-S2-01b-answers-3.md`. This directs phase-3 work, not a review or acceptance of phase 2.

For Q1 choose versioned simulated-device quantization, not permanent `INVALID_VALUE` holds or ratio-valued V3. Phase 3 adds a new immutable registered-Kobo publication profile (`registered-kobo-publication` v1) that explicitly declares a 0.000001 source-unit resolution for each numeric device signal and no numeric resolution for ENUM signals. Run setup verifies that each declared numeric unit equals the registered binding's source unit for this profile; a mismatch refuses instead of quantizing in an assumed unit. At the simulated device observation transform, after modeled bias and before `DeviceObservation` is frozen as the public reading, round the exact rational to that quantum using exact round-half-even arithmetic; serialize the result as a canonical finite decimal with insignificant trailing zeros removed. The V3 gateway still only validates and carries the published source-unit value; it never rounds or substitutes kernel truth. The prior `simulator-lab-publication` v3/v4/v5, existing Drafts, frozen observations, old artifacts, sealed envelopes and phase-1 V3/Batch V2 vectors remain unchanged. New Drafts must explicitly select the new profile; freeze its per-signal resolution in the run identity/reporting inputs and prove replay-stable bytes and that the 41 ratio holds become admitted readings without hiding other holds. This resolution is a simulated device property, not a claim about a physical Kobo instrument.

For Q2, the S2-01b direct public-observation probe through the real registered ENUM map suffices to prove adapter and gateway handling, including refusal of a lowercase label. It does not prove a registered Lab run publishes generator status. S2-02 demo setup owns a selectable registered generator-status publication path together with the explicit generator Foundation/scenario configuration already assigned there; it must show a staged and centrally accepted status from an actual registered run before making an end-to-end generator-evidence claim. Do not add an unconfigured status report to the daytime model in S2-01b.

For Q3, S2-01b keeps its explicit refusal of registered runs with publication-delay windows; no affected report is staged early. S2-01c, which owns gateway fault scenarios, adds delayed admission and local inspection from the frozen reporting-path window: retain original `source_time`, set `published_at` at actual release/sealing, and keep message identity/bytes stable on retry. S2-02 then accepts delayed reports through the same authenticated batch path and shows source/published/received times and lag. A delay never changes a measured value or silently converts an outage into a healthy report.

Amendment to `D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary` (S2-01b phase-3a defaults, Codex Architect): a resolution-declaring publication profile requires a registered Site because the binding source unit is the authority for its quantum; legacy YAML setup refuses rather than skipping that check. Freeze every declared per-signal resolution with the selected profile, but compare units only for channels actually bound in the selected registered snapshot. An unbound declaration is an unconfigured reporting path, not a basis for inventing a source unit or refusing the entire Draft solely for that optional path. A profile-selected real registered delay-window run is not yet available in S2-01b; an injected frozen-window regression proves its refusal branch only. S2-01c must provide the selectable profile/fixture and end-to-end local delay proof.

Correct the Lab interpretation of a quantized or stale reading: at the reading's own source time, `reported - bias` equals the world value only for an unquantized numeric signal under this model. With quantum `q`, it differs by at most `q/2` (including ties); it cannot recover an exact world value. A retained reading across a reporting gap describes its earlier source instant and cannot establish the current or hidden world quantity. S2-01b phase 3b corrects the misleading `ObservationView` docstring and avoids an exact-equality claim in Lab UI/copy; no existing observation, profile, or sealed wire byte changes.

Decision: `D-2026-10-09-s2-gateway-sealing-state-and-partial-progress`. Codex Architect, resolving S2-01b fix-round Q1-Q3 in `.agent/architect-S2-01b-answers-5.md`. This specifies the fail-closed sealing state; it is not a review or acceptance of the fix.

Retain `STAGED`, `SEALING_PENDING`, `SEALING_REFUSED`, `HELD`, `NOT_STAGED` and `GATEWAY_UNAVAILABLE` as ledger-derived registered Stage states. `STAGED` means every **admitted envelope for this run** belongs to a sealed local batch; it does not mean every attempted report was admitted, uploaded or accepted. Show held reports separately, including when the status is `STAGED`. An unbatched admitted envelope yields `SEALING_PENDING`, or `SEALING_REFUSED` when an active durable group refusal explains it. A holds-only run is `HELD`; no envelope and no hold is `NOT_STAGED`. These states and explanations survive a host restart.

`UNBATCHABLE` at `value` is the pre-sequence hold for a canonical report whose singleton Batch V2 exceeds the byte limit, so it consumes no sequence or outbox slot. Only a singleton size refusal gets that attribution; another batch-contract failure must retain its actual kind/field as a typed refusal, not be disguised as a bad value. Batch formation fits both count and serialized-byte limits, preserves sequence order within each source/configuration group, and does not rewrite sealed bytes.

A sealing failure in one group leaves that group's unbatched suffix and durable refusal inspectable while independent groups seal in the same committed operation. The call reports `SEAL_REFUSED` after committing that partial local progress; neither the host nor Stage may label the run fully staged. When a group later seals, clear its active refusal without changing prior batches or message IDs. S2-01c diagnostics count/report sealed, unbatched, held and refused states honestly; S2-02 may upload already sealed batches independently but must not present the run as fully released while any admitted envelope remains unbatched or an active seal refusal remains. No local state implies central acceptance.

Decision: `D-2026-10-09-s2-simulated-publication-clock`. Codex Architect, resolving S2-01c Planner Q1 in `.agent/architect-S2-01c-answers.md`. Select an explicitly advanced, persisted virtual publication clock for each registered Lab run. It is a simulated-device publication timeline, distinct from both the run's world-execution progress and the real UTC clock used for gateway diagnostics/server receipt. A world step may advance the publication clock through its reached simulation instant; after world execution completes, the operator/test harness may advance publication time further without rerunning the kernel. Pause and restart preserve the last advanced instant; neither wall-clock passage nor process restart releases a pending report. Advancing to an earlier instant refuses; repeated advancement to the same instant is idempotent.

The Lab-private scheduler persists each delayed public reading, its original source instant, scheduled release instant, stable admission key and pending/released state before gateway submission. The scheduled instant is derived from the frozen delay window and remains private Lab scheduling provenance, not V3/Batch V2/GatewayDiagnostics data. At or after the due instant, the authenticated host advances the gateway's scoped per-run virtual publication clock and submits the unchanged public reading. The gateway owns and persists that clock and stamps `published_at` with its current virtual instant at first admission/sealing; if advancement skips past the scheduled instant, the actual virtual admission instant is used rather than backdating to the schedule. Require `published_at >= source_time`. Retry/restart reuse the same report key and stored envelope/batch bytes, never re-stamp or re-sequence. A pending report has no V3 envelope or sequence; it is visible in Lab as pending with source and scheduled instants. The gateway receives no private delay cause or oracle.

`GatewayDiagnosticsV1.observed_at`, local contact/pressure observation times and central `received_at` use real UTC clocks and remain separate from the virtual publication clock. For SIMULATED evidence, `published_at - source_time` is a simulated reporting delay; `received_at - published_at` is not a physical transfer-lag measure when the clocks use different timelines. S2-02 must label these domains, display source/published/received instants with provenance and derive central diagnostic freshness from server receive time, not virtual Lab time. A future LIVE gateway uses its own real clock and does not inherit this Lab control.

Decision: `D-2026-10-09-s2-gateway-diagnostic-semantics`. Codex Architect, resolving S2-01c phase-1 Q1-Q5 in `.agent/architect-S2-01c-answers-2.md`; this is a contract clarification, not an implementation review. Keep `GatewayDiagnosticsV1` pressure provenance off the V1 wire: `disk_pressure` is the gateway's operative `OK|WARN|STOP` level, while the local read identifies `MEASURED|INJECTED_FAULT_FIXTURE|UNMEASURABLE`. A simulated gateway's central STOP is not measured hardware pressure. At STOP, all new acquisition calls, including replays, refuse before writes or sequence allocation; sealing existing admitted envelopes and emitting diagnostics may continue. A failed free-space probe is locally `UNMEASURABLE` and operatively STOP. The default 60-second cadence and 1 GiB/256 MiB free-space WARN/STOP thresholds are frozen, provisioned demo values, not universal physical safety limits.

Persist at most one immutable diagnostic per declared real-UTC cadence slot; a repeat returns its exact stored identity and bytes, and a clock earlier than the latest slot refuses. State changes within a slot are visible in the local read immediately but reach the wire in the next slot; the server uses receive time and cadence to decide central freshness. `queue_count` is the number of `STAGED|READY|IN_FLIGHT` envelopes, sealed or unbatched, excluding holds and dead letters; queue age uses their real-UTC outbox creation time and must remain real UTC when Lab V3 `published_at` becomes virtual. The local read retains sealed/unbatched/held/refused/dead-letter breakdown. `mapping_error_count` is the number of distinct `mapping_hold` rows with kind in `{NO_ACTIVE_MAPPING, UNKNOWN_CHANNEL, SOURCE_NOT_PERMITTED, OUTSIDE_VALIDITY, UNIT_INCOMPATIBLE, INVALID_ENUM}`; it is not the total held-report count. Contact is gateway real-UTC observation of a public report that resolves to a permitted source, even on replay or later hold; never-heard remains null. For a SIMULATED gateway its provenance is `OBSERVED_SIMULATED_REPORT`, never proof of physical controller contact or source health. S2-02 carries these meanings into authenticated receipt and central presentation without adding cause or private Lab fields to V1.

Decision: `D-2026-10-09-s2-publication-clock-post-run-release`. Codex Architect, resolving S2-01c phase-2 Q1-Q5 in `.agent/architect-S2-01c-answers-3.md`; this directs phase 3 and is not a phase-2 review. The run-scoped virtual clock is opt-in through an immutable registered publication profile (`RUN_VIRTUAL`); existing `GATEWAY_UTC` profiles and their old runs retain their gateway-UTC publication behavior and delay refusal. Before world completion, explicit advancement cannot pass the world's reached instant, preventing ordinary later samples from acquiring an undeclared publication delay. After completion, the virtual clock may advance beyond the world end without rerunning the kernel.

For S2-01c's registered `RUN_VIRTUAL` demo alone, a reporting-path delay WINDOW may start within the chosen world interval and end no more than one configured timestep after its end. It only schedules release of a public reading sourced within the interval; it neither extends the world execution interval nor makes a post-interval source sample. All other scenario entries and profiles retain the existing `outside-the-interval` refusal. This is an explicit narrow amendment to that dispatch rule; the selected profile and frozen run identity must establish eligibility before setup accepts the exception. Preserve the shipped scenario v1 and existing run bytes; publish a new versioned selectable fixture with a last in-interval sample still pending when the world completes, then release it on explicit post-end clock advancement. The gateway stamps actual virtual admission time, not the scheduled release instant. Its source-time Foundation/binding basis is the original in-interval basis.

The Lab-private per-run schedule remains durable outside gateway/product evidence and stores delayed report text/key before submission. Without a live host session, explicit advance may release due scheduled reports from that persisted text; it does not reconstruct or claim replay of any undelayed series that was not previously admitted. The local Stage/diagnostic read must remain honest about admitted, held and pending rows, and no no-session advance may be described as a complete rerun or central delivery. If there is no safe stored schedule, refuse rather than synthesize a report. Lab may display source, scheduled and actual publication instants with separate labels; S2-02 receives source and actual publication instants only, and does not turn simulated delay into physical transport lag.

Decision: `D-2026-10-09-s2-ordered-publication-and-closing-boundary`. Codex Architect, resolving S2-01c questions-3/-4 and first-review finding B1 in `.agent/architect-S2-01c-answers-4.md`. Amend the prior post-run-release wording: the selected post-run SOC report is the world's **closing-boundary observation** at the run end instant, not a sample strictly inside its half-open execution interval. The world produced that state at completion; the reporting-path delay window `[end-10 min,end+5 min)` covers only that one cadence reading, whereas a window also covering the preceding SOC reading would violate the existing one-reading-per-delay-window ordering rule. Preserve that refusal rule. A central consumer checks the closing sample's actual `source_time` against the original Foundation and binding half-open validity periods; the run's end boundary grants no exception to configuration validity. The delayed report keeps its value/source instant and receives the gateway's actual later virtual publication instant.

For a `RUN_VIRTUAL` profile, ordinary undelayed readings publish in source-boundary order at their own reached virtual instant, with `published_at == source_time` for the current cadence-aligned profile. A world step that spans many boundaries, including `run_to_end`, must process the same ordered boundary sequence as single-boundary steps: advance the gateway clock, admit that boundary's undelayed reports, and release delayed reports at the first reached boundary at or after due time. A later explicit post-run advance releases still-pending reports at its actual advanced instant, not a backdated due instant. Retries return prior bytes; no unadmitted earlier ordinary report may be silently stamped with a later clock merely because batching, restart or a fault skipped its boundary. If the gateway clock has already passed a required first-admission boundary and exact prior admission cannot be established, refuse or expose the missing publication rather than fabricate an undeclared delay. Pin full wire identity/bytes and publication instants across `run_to_end` versus single-step execution for the same frozen run, allowing only real-UTC local metadata to differ.

An executed `RUN_VIRTUAL` run with no durable schedule is a missing-schedule state, not a healthy empty queue; read and advance must distinguish it from a run not yet started or a profile without virtual publication. Fault injection remains a fixture-only authenticated gateway control. The Lab may place local gateway/schedule diagnostics inside a registered run's Stage disclosure, read them on page load and Stage refresh with a labelled read instant, and keep optional client methods for older fakes only if the production client implements and checks all three operations. The backend remains the canonical UTC-instant validator for free-text advance. A held delayed report is submitted to the gateway but has no V3 envelope or publication instant; Lab must call it HELD, not released evidence or an unreadable envelope. S2-02 must interpret only actual V3 source/published times, never step-batched artificial delay.

Decision: `D-2026-10-09-s2-publication-gap-and-batch-boundary`. Codex Architect, resolving S2-01c fix re-review R1 and questions-5 in `.agent/architect-S2-batch-answers-2026-10-09.md`. A completed `RUN_VIRTUAL` schedule's `admitted_through` is the last contiguous ordinary-publication boundary. If it is absent or earlier than `world_reached_instant` after a failed pass, a **stored-schedule-only** advance must refuse `PUBLICATION_GAP` before changing either Lab or gateway clock or submitting a due delayed report. The schedule read and Lab UI must show the incomplete ordinary-publication watermark and world-reached instant, not just a generic staging note; the advance answer must expose the typed refusal. A live session may re-drive the missing ordinary boundary while its gateway clock still permits its original instant. If that instant has passed, keep `PUBLICATION_INSTANT_PASSED`, stop later ordinary and delayed admissions for that run, and show the terminal gap; recovery is a new run, not late stamping or a hidden sequence jump. This strengthens, rather than replaces, the earlier rule permitting a delayed report to publish at the next actually admitted boundary or explicit post-run instant when no ordinary gap blocks it.

Seal the deterministic boundary groups as currently built. Batch V2 membership and bytes, as well as V3 identity/bytes, remain invariant under `run_to_end` versus one-boundary stepping; this may produce many small batches (the Kobo fixture currently yields 245 for 292 admitted envelopes). S2-02 must size its authenticated upload/retry/receipt path and owner evidence for that count, not assume one batch per run or step. `admit_at_run_clock` requires exact IPC body keys including `at_instant`; missing it refuses rather than falling back to stamp-at-current-clock. An executed `RUN_VIRTUAL` run with no durable schedule is `SCHEDULE_MISSING` on read and advance even if a live session remains; it must not silently regenerate missing state on a later step. Initial schedule creation during the first start, before any gateway submission, remains valid. A not-yet-started run can remain `NO_SCHEDULE`.

Decision: `D-2026-10-09-s2-pilot-gateway-upload-credential`. Codex Architect, resolving S2-02 Planner Q1 in `.agent/architect-S2-batch-answers-2026-10-09.md`. For the simulated pilot, use HTTPS/TLS plus an independently provisioned, high-entropy opaque bearer credential per registered gateway for both Batch V2 and GatewayDiagnosticsV1 upload. Issue the secret once into protected gateway configuration outside its SQLite ledger; persist only a credential selector/reference and one-way verifier in server storage, redact the secret from logs and responses, and never reuse the S2-01b local IPC credential or S1 development-tenant snapshot authority. The server authenticates before parsing or creating a Site ledger row and derives the immutable tenant/Site/gateway/mode principal from the credential and registered gateway; caller IDs and `source_mode` are claims to compare, not authority.

The credential binds the gateway identity, not a frozen per-credential source list. On **every** upload request, check current gateway enablement and immutable Site affiliation. For Batch V2, also require every declared source to be currently enabled and affiliated with that gateway; a disabled gateway/source refuses even a byte-identical upload retry before idempotency lookup. For gateway diagnostics, verify every named source's registered gateway/Site affiliation, but permit a disabled source's historical contact to remain visible as disabled; disabling one source must not silence the gateway's operational report. Separately validate each evidence envelope against its immutable originally registered Foundation/binding/source-time basis; current source authorization neither rewrites nor substitutes that accepted-as basis. A replacement credential may rotate without changing sealed bytes, batch IDs or diagnostic identities; revoking the old verifier takes effect on the next request. Phase 1 may use an injected authenticated-principal port; network endpoints remain closed until this credential and TLS boundary exists. Mutual TLS client certificates and a separate token issuer remain deferred pilot alternatives, not implicit fallbacks.

Decision: `D-2026-10-09-s2-terminal-publication-gap-closeout`. Codex Architect, resolving the merged S2-01c questions-6 in `.agent/architect-S2-batch-answers-2.md`. Keep the branch-only earlier-schedule files fail closed: if their missing boundary count leaves a started run ambiguous, read `INCOMPLETE` and refuse stored-only advancement; do not infer a complete run or migrate guessed state. Only a gateway `PUBLICATION_INSTANT_PASSED` refusal makes an ordinary-publication gap terminal; link loss, disk STOP and seal refusal remain incomplete and retryable while the original boundary is reachable. A terminal gap is terminal regardless of whether a live host session remains: reject any further publication advance **before either Lab or gateway publication clock moves**, with a typed gap refusal and the persisted admitted-through/world-reached/stopped-at facts. Do not return 200 after advancing a Lab-only clock on a terminal run. An initial start that cannot durably write a schedule leaves the run missing-schedule and requires a new run; no later step reconstructs it. A typed 409 may carry human-readable instants while the schedule read supplies the structured state. S2-02's Lab work owns the small post-merge terminal-gap correction and keeps `fully_released=false` for incomplete or terminal publication.

Decision: `D-2026-10-09-s2-ingestion-operational-semantics`. Codex Architect, resolving S2-02 phase-1 Q1-Q7 and phase-2 Q8-Q12 in `.agent/architect-S2-batch-answers-2.md`. Gateway/source external IDs remain mutable present-day names, while immutable registered UUIDs and the pinned published snapshot spelling determine accepted-as identity; asset code and tenant/Site/gateway/source affiliation remain fixed as implemented. An operator provisioning command may enable an imported gateway and only explicitly named registered sources while issuing its credential; an upload never enables either. Site/gateway/mode/disabled/source-scope mismatches are 403 without a Site-visible ledger row; wrong authenticated configuration references are whole-batch 422 refusals with an audit row, while individual source-time, binding, unit, enum, conversion and identity decisions remain per ordinal. Oversize is 413; only an authenticated request that reaches the service may create an auditable oversize refusal. Each accepted evidence row and Receipt V2 uses the batch's first server `received_at`; each ordinal's decision time remains separately recorded. New acceptances enqueue/coalesce `dispatch` recompute jobs over their source/interval window; duplicates and rejections enqueue none, and S3 expands neighboring analytic windows as needed.

Pilot bearer rotation revokes prior credential verifiers atomically when the new verifier is committed, with no overlap. The new secret must first be durably placed in a verified protected, versioned gateway file; a file/permission failure must leave the old credential active and the gateway/sources no more enabled than before. Do not overwrite the only usable old secret before successful issue; on Windows, verify an ACL restricting read to the operator and gateway process identity or refuse provisioning rather than claiming POSIX-only mode bits protected it. The central diagnostic is `CURRENT` through two declared-cadence periods from server receipt, then `STALE`, and `UNKNOWN` until a first receipt; this bounds slot-edge jitter without asserting device health. Pilot gateway upload uses direct TLS with the ASGI HTTPS scheme; forwarded scheme headers are not upload authority. A gateway diagnostic with malformed bytes or identity conflict receives an audited 422/409, while wrong path/claimed scope or foreign source receives 403 without a Site ledger row. The provisioning CLI remains development-tenant-only; its OS-user actor is labelled local operator context, not a verified tenant-user identity.

Decision: `D-2026-10-09-s2-evidence-cutover-and-credential-closeout`. Codex Architect, resolving Q13–Q20 in `.agent/architect-S2-batch-answers-3.md`. A KOBO-001 comparison with `PASSED`, explicit `empty_set: true`, matching tenant/Site UUID and a zero-count/no-replay statement permits that Site's Postgres Evidence cutover only while the compared legacy input inventory remains unchanged. This proves no historical KOBO evidence exists to migrate in this environment, not parser replay parity; retain a non-empty V1 parser fixture and demonstrate newly ingested V2 evidence for the owner. Immutable versioned JSON comparison reports are acceptable local migration artifacts, with the newest report decisive, but the gate must verify a deterministic digest of the current Site-scoped legacy inventory and compared artifacts; missing or changed input closes it. Regenerate the existing KOBO report after adding that fingerprint. No report is portable cutover authority for a different environment.

The gateway must refuse an upload credential file whose effective Windows DACL grants broader access than the operator/gateway process identity; provisioning-time verification alone is insufficient for an arbitrary configured path. Amend rotation so the verified unique versioned file is the final issued path, without a fallible post-commit rename: file/ACL failure before verifier commit leaves the old verifier and enablement intact, DB failure removes only the unissued new file, and successful commit immediately revokes the old verifier. Switch gateway configuration explicitly to the returned new path. Terminal publication uses `PUBLICATION_GAP` with schedule `TERMINAL_GAP` and refuses before either clock moves. A rejected/conflicting envelope is placed in a source-time window by its own parseable source time; unreadable-time rejections remain on the unwindowed route and are counted separately. Authenticated whole-batch refusals stay operational audit, not per-record Site Evidence. Until S3 computes dispatch, overlapping pending/leased/failed recompute jobs mean `STALE_PROJECTION`; no job means `NO_PENDING_DISPATCH`, never `CURRENT`. These decisions are Architect contracts, not owner Evidence acceptance.

## 2026-10-09

**Owner-confirmed 2026-10-09.** The owner confirmed this decision after three review rounds ("it is ready"), with two housekeeping points applied at recording: only the decision text is recorded here, and ranking notices are written to `.agent/coordinator-handoff.md`. Review trail (not authority): `.agent/owner-delivery-strategy-draft-2026-10-09.md`, `.agent/owner-delivery-strategy-review-1-2026-10-09.md`, `-review-2-`, `-review-3-`, `.agent/owner-delivery-strategy-final-2026-10-09.md`, and the Architect proposal `.agent/D-2026-10-09-owner-delivery-strategy-proposal.md` (its phased-prerequisite table and confirmation scope remain the working plan). Confirmation authorizes the strategy and the planning-only drafts during S2-02; it does not approve W1 core panels or demo values, S2 Evidence acceptance or V-01 adoption, which remain separate owner choices.

Decision: `D-2026-10-09-owner-delivery-strategy`. Owner product decision on delivery order, fidelity target, prioritisation and autonomy. It supersedes no technical decision. Product choices never satisfy a technical prerequisite, owner review, independent review, lineage proof or cutover gate.

**Goal.** Deliver a demo faithful to `frontend/mockups/v69/index.html`, from persisted source-to-claim data. Mock values do not become product data; unsupported content remains honestly unavailable.

**Story-first waves.** W1 is the S1–S7 mini-grid story, with a mock comparison on each supported screen slice. W2 adds thin cold-chain and EV spines, one Site each, on the S2–S4 backbone: Foundation, evidence, one assessment, one Finding and bounded consequence, with cold-chain excursion/backup response and EV interrupted-session simulated **data worlds and fixtures**; what-if scenario screens wait for W5. W3 builds Portfolio and global Findings (Cost/Risks/Opportunities), Actions, Evidence and Financials once, with all three domains present. W4 deepens mini-grid objectives and Site work; W5 deepens cold-chain/EV; W6 adds the broader work, Asset, onboarding and Settings roots. Each wave has owner start and exit review. The Architect proposes exact manifest IDs, core panels and demo values for each wave at its start; the owner approves them before that wave's new implementation is selected. Architecture decisions for shared FindingIndex, CapabilityReadiness, SourceHealth, money comparability, routes and actor identity may be pulled forward for all three domains; implementation stays in the active wave. The shared contracts needed by S3–S7 are decided and recorded **before S3-01 is activated**.

**Fidelity.** Each wave targets `Real with honest gaps` for owner-approved core panels. `Real` remains the eventual target for each screen not explicitly dropped: every panel real or owner-approved withheld, with interaction, navigation and V-01 acceptance. Dropped list: **none**. Indefinitely deferred list: **none**. These are proposed values, not owner approval of every manifest screen or its tier. An unassigned screen retains a planned wave or an explicit later-wave allocation before ranking; no empty route or illustrative value counts as real. The existing S1 owner UI acceptance remains evidence for S1 only; the W1 start decision is prospective for remaining W1 work, never backdated.

Candidate W1 manifest IDs represented by the current queue and V-01 are `sites`, `foundation`, `readiness`, `sld`, `lab`, `evidence`, `evidence-analysis`, `dispatch`, `analysis`, `finding`, `finding-evidence`, `financials`, `assumptions`, `mini`, `changes`, `recommendation`, `verification`, `sitework`, `action-overview`, `health` and `asset` (all exist in the manifest). This is a proposed screen set, not a claim that every panel is supported; the Architect must attach the exact core-panel IDs and owner demo values at the W1 confirmation gate. Screens outside that set still need an explicit planned wave before ranking.

Proposed allocation of the remaining **89** manifest IDs (no drop or indefinite deferral implied):

| Wave | Screen IDs | Count and reason |
| --- | --- | --- |
| W2 cold-chain thin spine | `cold`, `temperature`, `coldbackup`, `cold-foundation`, `cold-evidence`, `cold-evidence-analysis`, `cold-financials`, `cold-assumptions`, `cold-finding`, `cold-finding-excursion`, `cold-readiness`, `cold-sld` | 12; one excursion/backup source-to-consequence story, with honest gaps in adjacent panels. |
| W2 EV thin spine | `ev`, `sessions`, `ev-foundation`, `ev-evidence`, `ev-evidence-analysis`, `ev-financials`, `ev-assumptions`, `ev-finding`, `ev-readiness`, `ev-sld` | 10; one interrupted-session source-to-consequence story. |
| W3 three-domain estate | `portfolio`, `findings`, `actions`, `globalevidence`, `globalfinancials`, `findings-cost`, `findings-risks`, `findings-opportunities` | 8; shared roots only once three domain fixtures and comparable scope exist. Opportunities lists supported W1/W2 rows or an honest empty state, not an invented productive-use Finding. |
| W4 mini-grid depth | `renewable`, `service`, `fuel`, `backup`, `sitefindings`, `sitework-incidents`, `sitework-maintenance`, `scenarios`, `alternatives`, `finding-history`, `opportunity-finding`, `action-plan`, `action-execution`, `action-evidence`, `action-history` | 15; additional objectives and full Finding/Action work views. `opportunity-finding` waits for renewable assessment and lineage. |
| W5 cold/EV depth | `cooling`, `energy`, `incident`, `workverification`, `cold-health`, `cold-findings`, `cold-work`, `cold-work-incidents`, `cold-work-maintenance`, `cold-recommendation`, `cold-action`, `ev-health`, `ev-findings`, `ev-work`, `ev-work-incidents`, `ev-work-maintenance`, `ev-recommendation`, `ev-action`, `cold-scenarios`, `ev-scenarios`, `availability` | 21; additional domain assessment, availability, health, recommendations, work and what-if screens. |
| W6 work, Asset and administration | `assets`, `incidents`, `maintenance`, `assets-warranty`, `asset-register`, `asset-overview`, `site-create-form`, `site-create-template`, `site-batch-upload`, `site-setup-history`, `asset-performance`, `asset-config`, `asset-edit`, `asset-work`, `asset-evidence`, `asset-warranty`, `maintenance-preventive`, `wr-overview`, `wr-record`, `wr-history`, `oprecords`, `settings-policies`, `settings-tenant` | 23; distinct case, Asset, onboarding and policy authority. |

W2's listed screens are destinations, not a promise to fill every panel; the approved core set must fit a thin source-to-claim path. Its cold-chain/EV simulated fixture worlds remain necessary even though `cold-scenarios`/`ev-scenarios` UI waits for W5. Total allocation is 21 W1 + 22 W2 + 8 W3 + 15 W4 + 21 W5 + 23 W6 = **110 manifest IDs**; later wave-start approval may move IDs explicitly. W4, W5 and W6 each end in an owner result review rather than one 59-screen backlog exit.

**Selection within the active wave.** A candidate is an unfinished architecture decision, fixture, implementation slice or necessary delivery enabler with a named owner and reviewable closeout. Score only candidates connected by reviewed registry edges or explicit `delivery_plan.enables` edges to owner-approved active-wave screens; such `enables` edges mean planning benefit, **not** technical readiness. Publish raw `ready-now`, `closure-unlock`, reach, distance, effort, eligible screens and panel paths. First enforce wave scope, technical `requires`, owner/review stops and active-task exclusivity; ranking never bypasses those gates.

For each candidate `c`, let `D(c)` be the highest owner-set 1–5 demo value among its approved downstream screens (a direct screen task uses that screen's value). Let `d(c,p)` be the fewest **remaining closeouts after c** on a reviewed path from c to an approved core panel `p`, counting distinct architecture, data, read and UI gates needed for that panel; `d=0` means closing c makes that panel ready. Use **every distinct reachable approved core panel once**; there is no five-panel cap. Define discounted breadth `B(c)=Σ_p 1/(1+d(c,p))` and bounded panel leverage **`P(c)=5×(1−exp(−B(c)/K))`**, with **K=10 for W1**. This preserves each additional panel's contribution while keeping `0≤P<5` across waves of different size. At each later wave start, the Architect reviews the approved core-panel count and resulting score spread, proposes K (including 10 if still suitable), and the owner confirms it with that wave's IDs, core panels and demo values; a K change never occurs mid-wave without the owner's scoring-change gate. No reachable approved panel means `P=0` and no inherited demo value, so the candidate needs a documented connection before autonomous selection. Let `R(c)=min(5, distinct downstream subject areas/domains with identified approved consumers)` and `E(c)=1/3/5` for S/M/L. Then **`score(c)=0.4 D(c)+0.3 P(c)+0.2 R(c)−0.1 E(c)`** (bounded from −0.1 to below 4.4 for S/M/L). Publish uncapped reach/panel counts and the path/distance proof; a path cannot skip unresolved AND branches. `ready-now` counts `d=0` panels; `closure-unlock` counts panels that would become ready after c plus already named open upstream gates, reported separately and not added twice. Recompute after each recorded decision, accepted task or closed fixture. Exact score ties use fewer unresolved technical prerequisite gates, then lower effort, then stable node ID. Product-node `priority` is the wave ID, not the score.

Illustrative arithmetic below uses **hypothetical** owner demo values and panel mappings solely to test the proposed method; these are not approvals or measured current distances. The checker must recalculate them from approved panels and actual graph paths after prerequisite 3. For the first four rows, five illustrative panels have equal `d`; the last row shows forty direct panels and a like-for-like five-panel comparator.

| Candidate | Downstream demo D | Panels, distance / B → P | Reach R | Effort E | Score | Current eligibility |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Registry reconciliation prerequisite | 5 | 5 at d=3 / 1.25 → 0.587 | 5 | M=3 | **2.876** | Setup work, outside autonomous selection; score shows it no longer vanishes. |
| `A-S3-dispatch` decision | 5 | 5 at d=2 / 1.667 → 0.768 | 3 | M=3 | **2.530** | Selectable only after its recorded architecture prerequisites and S2 closeout. |
| `I-S3-01` task | 5 | 5 at d=0 / 5 → 1.967 | 3 | L=5 | **2.690** | Blocked until S2-02, `A-S3-dispatch` and dispatch fixture gates close. |
| `I-S7-01` task | 4 | 5 at d=0 / 5 → 1.967 | 1 | M=3 | **2.090** | Blocked until its actual Evidence, SourceHealth and fixture gates close; queue order alone will not silently block it. |
| High-fan-out shared enabler | 5 | 40 at d=0 / 40 → 4.908 | 5 | L=5 | **3.973** | Illustrative breadth case; at the same D/R/E, just five direct panels score **3.090**. |

These values make the distance/panel path, inherited demo value and technical eligibility visible separately. A real `I-S7-01` would use only its approved `health`/`asset` panels; the illustrative row is not a claim that five are approved. A candidate with no approved downstream screen cannot win by a reach-minus-effort surrogate and goes to Architect/Planner mapping review. The forty-panel row gains **0.883** score over five panels despite identical demo value, reach and effort; broad leverage now registers without making scores unbounded.

**W1 task order — recommend option (b).** After S2-02 closes, scoring may reorder S3–S7 implementation when the tasks are technically independent and the owner checkpoints still occur. The present queue and registry checker encode a linear `sequenced_after` chain, and some outline `Depends on` lines repeat it; those are currently binding until the Planner explicitly reconciles the queue, packets and checker under prerequisite 1/3. Mark each predecessor as either a real technical `requires` edge or an ordering-only edge; remove/rewrite only the latter before ranking can select around it. Keep technical `requires`, fixture and review gates even if their score is lower. This is preferable to option (a), which would make W1 scoring informational despite independent SourceHealth work and would delay the owner's requested early ranking. No task is activated on a proposed reorder while the executable queue still says otherwise.

**Shared-contract priority.** FindingIndex, CapabilityReadiness, SourceHealth, money comparability, routes and actor identity named as pre-S3 gates are mandatory Architect decisions, **outside competitive ranking**; their cross-domain value does not depend on W2/W3 screens being approved yet. Optional shared contracts are scored only against approved active-wave consumers, so the score may understate later-wave benefit. The Architect flags that limitation at each wave start and asks the owner to promote a genuinely necessary shared contract to an explicit gate; no speculative later-wave benefit is silently added to `D`, `B` or `R`.

**XL escalation.** Add `XL` as a planning estimate for work larger than one reviewable L slice; it has no autonomous score. Split an XL candidate into S/M/L reviewable slices or ask the owner to choose a bounded exception. An L candidate may proceed normally. This replaces the unreachable `>L` comparison.

**Autonomy and stops.** After wave-start owner input and S2-02 closeout, the coordinator may close out accepted work, recalculate, select an eligible top candidate, refine, build, obtain independent review, and merge under `.ai/WORKFLOW.md`. Only the coordinator records review outcomes and owner approvals after reading the underlying evidence; no Implementer commissions its own review. A `USER_REVIEW_REQUIRED` checkpoint blocks that task's acceptance/merge until owner review is recorded. Stop for owner at wave start (IDs, core panels, demo values and K), panel withholding, S2/S4/S6/S7 review checkpoints and each wave exit, screen dropping, a **≤5%** contested ranking, XL escalation, or scoring-parameter change. Also stop on checker failure, a second review rejection of the same task, or any real claim lacking lineage. Let `gap=(top score−second score)/max(abs(top score),1)` for the two eligible candidates. At **gap≤5%**, stop and present the scores, raw facts and recommended tie-break choice to the owner. At **5%<gap≤10%**, apply the published order of fewer unresolved technical gates, lower effort, then stable node ID to choose between those two, notify the owner with both scores and reasons (the notice is recorded in `.agent/coordinator-handoff.md`, so the owner sees it on resuming a session), and continue without awaiting a reply. At **gap>10%**, select the highest score without a ranking notification; with only one eligible candidate, select it without a ranking notification. Other owner gates stop regardless of gap. No silent override of a stopped gate.

**V-01 adoption gate.** Recommend that, at S2-02 independent review, S2 owner Evidence closeout and pre-S3 refinement, the owner **adopt the refined [V-01 proposal](../tasks/V-01-v69-visual-fidelity.md) as a W1 item**, with exact supported manifest IDs, core panels, mock comparison method and acceptance boundary. The Planner then makes V-01 executable; its app screenshots and checks cover only supported real data and honest missing states. Standing side-by-side comparisons remain part of each slice, but **no screen is fully `Real` until the applicable V-01 visual/interaction acceptance is actually recorded**. If adoption is withheld, keep V-01 non-executable and full `Real` blocked; do not infer approval from this strategy.

**Current review routing.** Preserve the owner's specific S2 instruction: fresh Claude independent review per slice, one Codex review of the S2-01c/S2-02 whole, and the S2 Evidence owner checkpoint. Do not infer a new Codex review per slice from this autonomy loop. Decision requests go to the active Architect under `.ai/ROLE_CONFIG.md`; owner weighing is requested with a reason when product authority is needed.

**Product-node recording.** Once W1 is confirmed, record its approved nodes as `Real with honest gaps`, `priority: W1`, with exact approved core panels, owner evidence and demo values. Other nodes remain `pending owner` with a non-authoritative planned-wave field until their wave starts. Do not pre-mark all current W1 nodes real merely because S1 is merged. A node's status describes its approved target, not completion of every panel; panel evidence and `to_real` gates remain separate.

Decision: `D-2026-10-09-s2-rotation-reconciliation-followup`. Codex Architect, resolving S2-02 Q37–Q40 and fix re-review R3 in `.agent/architect-pre-S3-answers.md` after S2 closeout; this is a follow-up contract, not a reopened S2 verdict. For the same-account pilot, `ISSUE_OUTCOME_UNKNOWN` may be a supervised operator halt without a local marker; a later successful issue on a readable DB creates a new protected file and revokes earlier selectors atomically. A marker alone is not a trusted second authority. The current fresh *unlocked* no-selector read is **not conclusive proof of rollback**: the original transaction may still finish its COMMIT. Before any non-demo/unattended rotation or real pilot, a bounded S2-02r correction must reconcile under the same gateway-row `FOR UPDATE` lock used by issuance, wait for any prior transaction to finish, then check selector/verifier, credential reference, expected source enablement and survival of the previously active credential in that locked transaction. Only proven non-commit with the old credential active permits deleting the new file; timeout or inconsistent state keeps the protected file and typed unknown outcome. `pg_stat_activity` alone does not establish this ordering. Distinguish a provably pre-transaction failure from an ambiguous COMMIT in that follow-up; the present conservative unknown result is a carry, not secret loss. The v3 store-root-bound comparison correctly closes on older servers until restart; its hash of canonical resolved Evidence/commit roots is accepted, and a moved store needs a fresh report. S2-02r is not an S3 analytic prerequisite.

Decision: `D-2026-10-09-pre-s3-claim-routes-and-actor`. Codex Architect, resolving bounded `A-claim-work-routes` and `A-actor-identity` before S3 activation under the owner-confirmed delivery strategy; detail in `.agent/architect-pre-S3-answers.md`. A Finding or Action has stable UUID identity under tenant and Site UUID across mini-grid, cold-chain and EV. Canonical Site-scoped routes are `/sites/{site_code}/findings/{finding_id}` and `/sites/{site_code}/actions/{action_id}`, with parallel `/api/sites/{site_code}/...` reads. Resolve Site code within the authenticated tenant; a global future index links to these same IDs. Finding history selects an immutable `finding_revision_id` (optional `revision_id` query) at stated `knowledge_at`; omitted revision selects latest permitted and returns its selected ID/watermark. Action state derives from ActionEvents and selects an exact event/cutoff, while plan/outcome child views select their own immutable IDs; do not invent an ActionRevision. Back-links preserve Site, window and exact claim selection. Unauthenticated is 401; unauthorized known scope is 403; foreign-tenant or nonexistent identity and foreign revision are 404. A supported but unbuilt/lagging read reports typed unavailable or pending, not a fabricated empty claim; unbuilt tabs stay hidden or honestly unavailable.

Every auditable assumption, policy or work write stores server-resolved `actor_kind`, `actor_id`, source channel, recorded time and authorization basis. A human `author_id` requires an authenticated human principal; client text, local OS username, fixed development tenant and gateway credential are not human identity. A `SYSTEM` action has stable service-principal and triggering job/command/fixture provenance, without implying a human attestation. Human attestation binds exact content/version, time and immutable proof; correction appends a new event/revision. S4-02 price edits and S6-01 Action/policy writes require a verified operator path or explicitly labelled server-authorized system demo operation; otherwise writes are unavailable. The S2 provisioning CLI's OS-user value remains local context. These bounded decisions are mandatory before S3-01 planning activation but are implementation gates of S4/S6, not dispatch inputs.

Decision: `D-2026-10-09-pre-s3-evidence-readiness-health`. Codex Architect, resolving a bounded selected-window CapabilityReadiness/SourceHealth contract for all three domains, separate from the still-open broad shared evidence projections; detail in `.agent/architect-pre-S3-answers.md`. CapabilityReadiness uses declared role/rule version, selected Foundation/bindings and **accepted** evidence for a tenant/Site/domain half-open window at `knowledge_at`. It returns per-role coverage, quality, missingness, exact revision/evidence IDs and watermark with `READY`, `LIMITED`, `UNKNOWN` or `NOT_APPLICABLE`; rejected, duplicate, held or pending gateway rows do not prove observed capability. Foundation configuration readiness remains distinct. SourceHealth separates **central contact freshness** based on server receipt and declared cadence from the **age and clock basis of reported facts** (`observed_at` and source-contact fields). A newly received old diagnostic may mean contact CURRENT while reported queue/device facts are old or Unknown. Virtual source time is not compared with real server time as physical freshness or network lag. Neither projection is asset condition; lagging read models state `STALE_PROJECTION`, and both expose source/gateway IDs, times, coverage and lineage. Cold/EV role rules and implementations wait for their waves; S7 outage/pressure fixture `D-edge-health-cases` is not required for ordinary S2 contact.

For reconciliation, bounded `A-S1-bindings` is **resolved** by `D-2026-10-08-s1-bindings-roles-and-snapshot` and `D-2026-10-08-s1-foundation-organization`. Bounded `A-S2-evidence` is **resolved** by `D-2026-10-07-s2-edge-split-and-demo-source`, `D-2026-10-08-s2-v3-source-payload-and-period-reference`, `D-2026-10-09-s2-pilot-gateway-upload-credential`, `D-2026-10-09-s2-ingestion-operational-semantics`, `D-2026-10-09-s2-evidence-cutover-and-credential-closeout` and `D-2026-10-09-s2-credential-uncertain-commit-and-evidence-demo`; this does not resolve broader projections. `A-finding-index` remains open until the S3 assessment and S4 episode contract produce Site/domain/window/revision rows; its stable root/index keys are constrained by the route decision, not implemented here. `A-money-comparability` remains open until S4 price/consequence and W3 aligned multi-Site fixtures; meanwhile no unlike currency/period aggregation, unpriced-as-zero, scenario-as-observed money or inferred recovery is authorized. S3-01 technically requires accepted S2 Evidence/ledger, time-valid S1 bindings, its typed dispatch decision and normal-ingestion dispatch fixtures, not these shared route/actor/readiness/health implementations or global indexes.

Decision: `D-2026-10-09-s2-credential-uncertain-commit-and-evidence-demo`. Codex Architect, resolving S2-02 Q21–Q36 in `.agent/architect-batch-answers-4.md`; this amends the credential closeout decision, not an S2 review verdict. An error at database COMMIT during credential issuance may be an **unknown transaction outcome**. Preserve the new protected versioned file until a fresh scoped read reconciles its selector, one-way verifier, active/revoked state and expected gateway/source enablement. If the new credential committed, report success and switch the gateway to it; if non-commit and old credential survival are proven, remove only the unissued file; if neither can be proven, return a typed unknown outcome, retain the protected file and halt operator rotation pending reconciliation. Never discard a possibly committed only-usable secret or blindly reissue. A copied legacy-comparison report is not portable to another workspace merely because it points at the same database: bind it to the canonical local Evidence/commit store-root identity as well as tenant, Site UUID, DB identity and current input digest. Absence and an empty legacy folder represent the same zero inventory; changed or unreadable legacy input closes the gate. S3 dispatch fixtures and recompute jobs are hand-off material, not Evidence cutover inputs.

The S2 owner walkthrough must show a clearly labelled authenticated fault-fixture Batch V2 with a valid and invalid sibling and the resulting accepted/rejected Site rows after reload; it must not claim the ordinary sealing gateway produced invalid input. Crash/resume 202 and an out-of-period closing reading may remain explicitly identified Postgres test evidence, without a test-only product knob. Explain the observed 246/293 versus earlier 245/292 counts by exact manifest diff before presenting them as complete. Distinct same-time readings from two simulated runs remain separate accepted Evidence by gateway sequence, but S3 must not sum overlapping epochs into a single physical series; it must select a supported basis or report limited/Indeterminate coverage. A 15:00 run-end reading is centrally valid if its original Foundation and binding periods remain open; run end alone is not a configuration-validity boundary. Gateway restart for a new protected file, isolated demo archive, and Evidence-only gateway health are acceptable pilot bounds. These rulings require S2-02 correction and independent review where named, not owner acceptance.

Decision: `D-2026-10-09-pre-s3-shared-contract-scope`. Codex Architect, resolving the delivery-planning contract batch in `.agent/architect-batch-answers-4.md` under the owner-confirmed delivery strategy. Before S3-01 activation, record bounded decisions for stable tenant/Site-scoped Finding and Action identities/routes and revision selection (`A-claim-work-routes`), authenticated actor versus attributed human author/system action and attestation (`A-actor-identity`), and selected-window CapabilityReadiness and SourceHealth with coverage, freshness, Unknown and source lineage (a bounded evidence-readiness/health architecture node). These are mandatory architecture decisions, **not** extra S3 dispatch implementation prerequisites. S3-01 technically depends on its typed dispatch contract, accepted Evidence and time-valid S1 bindings, S2-02 ledger closeout and dispatch fixtures. Site/domain/window/revision keys for future FindingIndex are constrained now, but `A-finding-index` remains open until S3 assessment and S4 episode identity exist; global index implementation is later. No cross-Site/unlike-currency aggregation or scenario-as-observed money is authorized; `A-money-comparability` remains open until the S4 consequence/assumption basis and W3 comparable fixtures exist.

The bounded `A-S1-bindings` architecture node is resolved by `D-2026-10-08-s1-bindings-roles-and-snapshot` with `D-2026-10-08-s1-foundation-organization` for the Readiness/SLD boundary. The bounded `A-S2-evidence` gateway/V3/central decision/lineage node is resolved by `D-2026-10-07-s2-edge-split-and-demo-source`, `D-2026-10-08-s2-v3-source-payload-and-period-reference`, `D-2026-10-09-s2-pilot-gateway-upload-credential`, `D-2026-10-09-s2-ingestion-operational-semantics`, `D-2026-10-09-s2-evidence-cutover-and-credential-closeout` and the uncertain-commit amendment above. Resolve these architecture nodes with citations during registry reconciliation without treating the still-reviewed S2-02 implementation as accepted; broader projections remain open separately. Foundation Readiness distinguishes configured gateway/source roles from central contact and Evidence capability; it cannot conflate registration with observed reporting. W1 panel gates are AND within a supported positive or Unknown claim variant, with distinct variants and honest missing states; owner approval of a panel requires a reviewed mapped path and does not promote unsupported alternatives, money trade-offs, onboarding or physical battery condition. The current S5-01 packet retains S4-02 as a technical prerequisite for its bounded-money panel; a future money-free Overview needs a separately scoped packet. S5-01→S6-01 and S6-02→S7-01 are ordering-only for the stated packets, while Action still needs Finding/actor/Foundation authority and Health still needs S2 diagnostics/bindings and its own fixture. Remove ordering-only edges only when queue, packets and checker agree.

Decision: `D-2026-10-11-s3-dispatch-interval-assessment`. Codex Architect resolves bounded `A-S3-dispatch` for mini-grid S3-01; Planner refinement inputs are in `.agent/architect-S3-dispatch-answers.md`. This decision uses the typed seam and Postgres revision rules in `frontend/docs/architecture/production-shaped-mvp-technical-design.md` §§3–4 and the existing `backend/tests/dispatch_decision_table.md` (`dispatch-2`) as the behavioral comparison baseline. It authorizes no file-backed product read after S3 cutover and no cold-chain/EV analytic implementation.

**Input and cohort.** `EvidenceQuery` is a tenant-authorized, Site/domain-scoped query for a UTC half-open window at `knowledge_at`; it returns typed normalized accepted readings, original interval/source times, quality, canonical role/asset/unit, exact accepted evidence IDs and content digests, as-accepted Foundation/binding revisions and source/sequence-epoch provenance. It selects by source-time or reported-interval overlap, including bracketing evidence needed to bound continuity, with the chosen knowledge cutoff applied to server acceptance/recording. `AnalyticInputSet` freezes the selected public evidence cohort, role coverage/missingness, effective public configuration, analytic/rule version, window and cutoff; its canonical SHA-256 covers sorted evidence IDs **and digests**, cohort identity, relevant Foundation/binding revision IDs and values, role coverage, window and model version. SQL rows, raw envelope JSON, gateway diagnostics, Lab world/truth, private run IDs and file-backed assessment objects stop before this boundary. `RUN_VIRTUAL` source time is a simulation clock, not real-world contact freshness.

Overlapping accepted simulated reports are separate evidence, not one physical series. The selected basis is an explicit, persisted **public report cohort**: for each required source, registered source UUID and sequence epoch, with the included batch/evidence IDs and common Site/configuration/window basis; the request/read returns that selection. A multi-source cohort must be proven coherent by its public gateway/source-epoch and sealed batch provenance. The private Lab run manifest may guide a demo operator to those public IDs but is not an analytic input or authority. S2's two overlapping runs and labelled `fault-fixture-epoch` must remain separate choices. If there is no unique/provably coherent cohort, return a limited/Indeterminate result naming the ambiguity; never prefer the latest receipt, sum epochs, use the fault fixture as ordinary output or deduplicate distinct evidence by timestamp. Within a selected cohort, same-role/time disagreements remain conflicts rather than arbitrarily choosing a value.

**Dispatch rule.** The first Postgres model is a **new version** of the mini-grid dispatch rule; it may reuse the published `dispatch-2` thresholds/decision table but must name every carried or changed rule in a versioned table and compare its results. Reconstruct generator ON/OFF intervals with observed bounds/gaps. For each segment, apply evidenced constraints in order: an authorized, supported override or effective minimum runtime; battery reserve/near-reserve; PV-plus-battery capability shortfall; then candidate headroom. A whole interval is Necessary only if every assessed segment is Necessary; any supported Candidate segment gives `CANDIDATE_AVOIDABLE` only for those bounded segments; otherwise it is Indeterminate. Missing role, poor quality, contradiction, open bound or ambiguity names the affected segment/limit. Candidate requires accepted **available PV power** and PCS **discharge capability** (the published `dispatch-2` PV-alone branch also requires evidenced PCS availability), plus the load and, for battery-supported headroom, SOC and selected Foundation reserve basis; observed `pv_power` and rated/actual `battery_power` are not substitutes. The optional available-power and discharge-capability roles require a separately published, versioned binding vocabulary and actual registered readings before S3 can make a candidate claim; `minigrid-roles-1` remains historically interpretable. The S1 Foundation's time-valid `battery_reserve` control is authoritative; S2's measurement-only V3 path supplies no accepted POLICY/OPERATIONAL_RECORD override. Do not fabricate one from a Foundation change or Lab event. Missing optional override records do not by themselves block a Candidate, but the result must say no command record was observed, not that no command occurred; any conflicting supported constraint makes the affected portion Indeterminate under the versioned rule. A supported policy/command record later needs its own versioned provenance and conflict contract before it can change this rule. Necessary policy-only claims require that supported record; otherwise classify from evidenced physical constraints or Indeterminate. Dispatch states a technical candidate, not recovered fuel/cost, physical equipment condition, causal intent or a Finding; S4 owns Finding identity and money.

**Revisions and jobs.** S3 consumes the S2 `dispatch` recompute queue transactionally with a lease/retry, expands an accepted record's affected source-time interval to continuity neighbors, and reruns at a recorded cutoff. Backdated Foundation/binding publication and analytic-model changes enqueue affected windows too. The worker persists an idempotent `AnalyticRun` keyed by Site, analytic/model version, window and input hash, its exact evidence-ID set, and append-only `AssessmentRevision` rows under a stable interval/asset assessment key. Identical input and output produce no new revision; a changed evidence/configuration/model basis appends a new revision while preserving the earlier one and its selected read URL. Projection replacement and job completion occur atomically only for the still-current input/watermark; a newly dirtied overlapping window must remain dirty for another pass, never be lost by a leased worker. Late accepted evidence may change Necessary/Candidate/Indeterminate but never rewrites an earlier revision. The Performance list/detail returns selected revision, rule version, input hash, coverage, evidence IDs, source and analytic watermarks, built time and explicit limitations.

**Projection status and cutover.** `NO_PENDING_DISPATCH` in the S2 Evidence read means only that no S2 job is outstanding; it is never a current assessment. Once S3 owns Performance, use `UNASSESSED` when no completed assessment exists, `PENDING` for a first run in progress, `CURRENT` only when a completed projection's input/source watermark matches accepted evidence and no overlapping dirty/leased/failed job remains, `STALE_PROJECTION` when a previous result exists but any such job or watermark mismatch remains, and `FAILED` when computation failed without a usable current result. Preserve prior revision links under stale/failed status and show job/error reason; no state silently means healthy, Necessary or zero. Reconcile the Evidence projection display to these truthful states after S3 activation. Before switching Performance reads to Postgres, compare representative file-backed dispatch claims against the same public evidence/configuration basis and the new model, recording matched outcomes, bounded intentional rule differences, lineage and exceptions; no private truth or stale JSON becomes product authority. If comparable baseline evidence is unavailable, record the exception and keep the affected read cutover closed rather than claim parity.

**Fixture and reuse boundary.** `I-sim-dispatch-cases` supplies a versioned, repeatable manifest of complete, missing-role/quality, contradictory same-role/time and late/out-of-order public intervals, with expected classification ceiling, selected public cohort, source/configuration revisions and exact batch/evidence IDs. Include the S2 overlapping runs and fault epoch as an ambiguity/exclusion check; prove at least one supported Candidate only after the available-PV/PCS-capability binding and accepted-report gate closes, plus Necessary and Indeterminate cases. Seal and upload every product fixture via the registered simulated gateway, Batch V2 and ordinary authenticated S2 ingestion; rejected siblings remain rejected and private oracle data stays Lab-only. The shared `EvidenceQuery`/`AnalyticInputSet`, run/revision, watermark and claim-limit contracts can be reused by later cold-chain/EV analytics, whose role sets, domain rules, fixtures and UI remain later-wave work.

Decision: `D-2026-10-11-w1-pre-loop-mapping-and-truthfulness`. Codex Architect resolves the batched PRE-S3-03 Q1–Q9, S3-01 Planner questions and reviewer carry C5; exact Planner/Implementer instructions are in `.agent/architect-batch-answers-5.md`. Owner confirmation of revised W1's 27 screens, core panels, values and K=10 is recorded in the request. These are technical/refinement rulings, so no further owner choice is needed; owner review checkpoints remain binding.

Split the owner-adopted V-01 into two reviewable L visual gates: `V-01a` for `sites`, `foundation`, `readiness`, `sld` and `V-01b` for `lab`, `evidence`, `evidence-analysis`, each with its own packet, app/mock evidence and owner checkpoint. The original V-01 is an umbrella, not a third scored gate; the S3 `dispatch` comparison remains in S3-01. A visual candidate's distance includes every unresolved technical AND branch for the same approved core panel, while technical candidates receive no credit for visual-only work. Do not score an unsized or duplicate visual gate.

The owner-confirmed `evidence-analysis:2` core includes both its S2 delivered explanation and a **positive, rule-backed selected-window claim-limit portion**. The latter remains open until a real CapabilityReadiness/dispatch-limit read, lineage and UI path is reviewed; do not drop it merely to make the checker rank. Both the honest empty/Unknown and the positive Finding-row variants of `mini:3` and `sitefindings:1` are core, with separate gates; Unknown never completes positive rows. `analysis:3` alternatives and `asset:3` positive physical condition remain non-core, visible gaps. `A-finding-index` is a mandatory W1 contract before the Site Finding list/positive Overview path, outside competitive ranking but **not** an S3 dispatch prerequisite. `A-money-comparability` remains outside W1 ranking as a later cross-option/estate contract, not a prerequisite for S4's bounded Site consequence. No other still-open architecture node is automatically outside ranking; resolved pre-S3 route, actor and readiness contracts retain their recorded status.

For the 37 proposed-only approved panel paths, Planner may perform **one coordinated registry/packet pass**, but it is a mapping review, not implementation or readiness closeout. Replace every live proposed `R-*`/`UI-*`/`D-*` token with an existing real node or a newly declared implementation/data node with one owning S3–S7 packet or bounded follow-up, effort, technical `requires`, reviewable acceptance and honest open status. Reuse accepted S1/S2 nodes for inherited seams; never manufacture a second open gate for already delivered work. Map `R` to a named read/projection closeout, `UI` to a named route/UI closeout, and `D` to an actual fixture or persisted-data closeout only when distinct from an existing producer. A whole task node may stand for an inseparable reviewed slice; if phases close independently, name real phase nodes and make the task's `requires` reflect them. Technical `requires` are AND; planning `enables` is not one. An independently reviewed mapping may become `reviewed_mapping:true` while implementation nodes remain open, but proposed IDs, unresolved positive portions and unsupported lineage must still fail closed. `A-S3-dispatch` is already resolved; S4–S7 architecture nodes close only at their own reviewed decisions. Ranking stays refused until all 51 approved core panels have reviewed paths and startup guards pass.

Preserve the single-active-task rule: any packet in `active` or `in_review`, including one without `USER_REVIEW_REQUIRED`, stops a new autonomous selection until review/closeout is recorded. Tie-break counts distinct unresolved technical gates on the candidate's reached reviewed paths, excluding the candidate, then effort and stable ID. The 14 delivered S1/S2 panel mappings may cite `.agent/PRE-S3-03-review.md` as independent verification **after F1 is fixed**; the coordinator records that review and corrects weak/stale evidence labels. Before the autonomous loop, close a small independently reviewed W1 Readiness truthfulness correction: remove hardcoded “no accepted evidence” and “awaiting credentials/not sending” assertions from the configuration view, using bounded wording or actual central reads. Until then do not promote `readiness:2/3` registered portions. This is a corrective pre-loop task, not a new capability or an excuse to defer false UI text to V-01/S7.

`delivery_plan.enables` is currently empty. The PRE-S3-03 checker must explicitly **fail closed on any non-empty `enables`** until a separately reviewed parser/scoring contract implements those planning-only edges; silently ignoring them violates the owner strategy. Add a focused non-empty fixture after the current F1 fix, without modifying scoring semantics or treating `enables` as technical readiness.

Decision: `D-2026-10-11-w1-loop-and-mapping-boundaries`. Codex Architect resolves the startup-6 coordinator loop review and W1 mapping carries C1/C5/C6; exact Planner/coordinator edits are in `.agent/architect-batch-answers-6.md`. The owner-confirmed delivery strategy remains authority: `next-work` is advice, verified against current inputs, and cannot clear owner/review gates. The S2-specific Claude-per-slice/Codex-batch review arrangement does not override the current Reviewer binding for S3–S7. Route a selected pure architecture node to the Architect, not an Implementer; route build/visual/data nodes through their owned packet and independent review. Any active or in-review packet stops another autonomous selection. The revised `.ai/COORDINATOR_LOOP.md` records this operating sequence.

**C1: split the false index gate.** Finding Evidence and History require selected FindingRevision, assessment and accepted-evidence lineage, not a Site FindingIndex. Keep S4-03 as the bounded Finding Evidence/History follow-up after S4-01; move the Site FindingIndex/list with its separate zero-row and positive-row fixtures to S4-04, gated by `A-finding-index`. `finding-evidence:1-2` and `finding-history:1` paths must lose `A-finding-index`, Site index fixtures and any combined S4-03 closeout that still requires them. Split S5's overview composition from its positive Finding-list integration: `mini:1/2/4` may close on S5-01 without the Site index; `mini:3`'s honest empty and positive variants close in a small S5-02 integration after the S4-04 Site index. This preserves both owner-approved `mini:3` variants without making unrelated Overview claims wait on a different projection. Task IDs, registry `requires`, queue and packet acceptance must agree before ranking.

**C5: scope ActionIndex to the Site list.** `A-action-index` and a Site-scoped Action index read gate `sitework:1` only. Remove `A-action-index` from the common `I-action-read` detail path and from Action Overview, Plan, Execution, Evidence, History, Recommendation, Changes and Verification paths unless a panel independently consumes an index. Keep S6-01 for the Finding-linked Action root, event/activity and controlled change; move Site Work list/index to a bounded S6-03 packet with its own `I-site-action-index-read`, `I-sitework-ui` and task closeout. Do not place S6-03 in S6-01/S6-02's technical prerequisites merely to preserve old queue order. Stable Action detail identity and event selection remain required without an index.

**C6: make the Finding closeout consistent.** S6-01's accepted Action must reference a reviewed, persisted FindingRevision under the canonical route, so `I-S6-01` technically requires the **closed `I-S4-01` task**, not only its open `I-finding-read` subnode. All Action/Recommendation/Changes/Verification panels produced by S6-01/02 inherit that same gate; S6-03 inherits it through S6-01. Remove redundant direct Finding UI/read prerequisites from individual panel paths where the S4-01 closeout already proves the exact needed basis. This does not add S5 Overview, S4-03 Evidence/History or Site FindingIndex as an Action prerequisite.

**Loop activation order.** The current `.agent/C9-rereview.md` rejects the C9 repair because labeled V-01a/b links are not discovered, so the present ranking cannot authorize selection. Fix packet discovery from actual `tasks/README.md` link targets (including labeled visual and carry packets), normalize their explicit open statuses, and independently re-review a fixture using the real labeled links before loop activation. Treat this post-acceptance C9 correction as its own bounded carry task for counting the strategy's repeated-rejection stop; another rejection of that same correction calls for owner direction. In the same pre-merge planning correction, apply C1/C5/C6, clarify incremental effort on composite task nodes, and replace placeholder/false claim-boundary labels (mapping carries C2/C3/C4/C8); obtain independent review of the changed graph and ranking. Then close the planning branch's review/status/guard gates and merge it to `main`; run the normal guards and a newly generated **verified** next-work report on merged `main`. The prior 3.018 versus 2.679 ranking is stale after these edits. Do not activate S3-01 or V-01 from it. No new owner product choice is requested now; standing owner checkpoints and any genuine ≤5% contest or repeated rejection still stop for the owner.

Decision: `D-2026-10-11-s3-phase-1-fixture-and-late-evidence`. Codex Architect resolves S3-01 phase-1 Q1–Q6 and review carries F3/F4 in `.agent/architect-S3-answers-1.md`. The phase-1 fail-closed defaults stand: the contradictory same-role values are an authenticated, explicitly labelled Batch V2 fault fixture in a separate epoch, not a gateway-sealed report; UNAVAILABLE plus reporting gaps is poor coverage, not fabricated SUSPECT; overlapping runs in one public sequence epoch remain ambiguous and cannot be separated by private run ID, sequence ranges or receipt order; demo generator values use their versioned TEMPLATE provenance and an explicit change note; the registered delayed-publication case is late only at source publication; absent fuel level is a named unused gap. This narrows the original dispatch-fixture wording to match demonstrated evidence, without changing `dispatch-3` claim semantics.

Phase 2 must add a separate, labelled authenticated fault-fixture cohort whose later-source-time record is centrally accepted before an earlier-source-time record, with exact accepted IDs and receipt/source ordering in a regenerated environment-local manifest; do not call the ordinary delayed-publication case out-of-order. It must independently assess a first accepted basis, then centrally accept a later record affecting the same selected window, consume the resulting recompute job and show a new immutable assessment revision and still-addressable old revision; publication lag before a single bulk delivery is insufficient. The typed analytic uses public accepted evidence only and never uses the fixture manifest or an epoch-name heuristic to infer trusted provenance. Phase 3 Evidence drill-down must expose actual gateway/source/epoch/batch/accepted IDs, and, where the demo manifest supplies a fixture label, visibly attribute that annotation to the manifest rather than central attestation. Default cohort selection may not silently blend or promote the fixture as ordinary output. A trusted central fixture marker or gateway-side ordering fault operation changes the S2 acquisition contract and is deferred to a separately reviewed later slice.

Owner routing amendment: the owner's 2026-10-11 instruction in `.agent/architect-S3-request-1.md` explicitly extends the S2 review arrangement to later milestones and supersedes the contrary review-routing sentence in `D-2026-10-11-w1-loop-and-mapping-boundaries`. Batch Codex Architect/Planner questions, use a fresh Claude reviewer for each slice and re-review, and conduct one batched Codex review at each milestone end; preserve all task-specific owner checkpoints and coordinator closeout authority.

Decision: `D-2026-10-11-s3-phase-2-selection-and-read`. Codex Architect resolves S3-01 phase-2 Q1–Q8 in `.agent/architect-S3-answers-2.md`, subject to the independent phase-2 review. For a run at cutoff K, selected time-valid Foundation controls and bindings known at K govern the calculation; each accepted reading retains its original as-accepted revision and accepted role as separate provenance. Backdated publication can create a new input basis and revision without rewriting accepted evidence. A configured minimum runtime blocks Candidate during the uncertain first-ON period but proves no policy-only Necessary claim. UTC-day windows, six-hour bracketing, and first-ON-report interval keys remain `dispatch-3` rules; an earlier late ON report creates a new key, while the prior revision remains addressable and is not an active duplicate.

Same-epoch overlaps remain unusable where sequence order or channel-time conflicts occur; two overlapping epochs without a defensible public selection yield `AMBIGUOUS_COHORT`. A lone manifest-labelled fixture stream may appear in the default read only as its actual limited/Indeterminate assessment with central gateway/source/epoch/batch/evidence provenance. A separate demo-manifest annotation may identify its fixture origin, explicitly attributed to that manifest; neither the analytic nor the product infers a trusted fixture flag from the epoch name. The read must never silently present a known fixture as ordinary positive output. A trusted central fixture marker is a later S2 acquisition-contract change, not an S3-01 schema shortcut.

Phase 3 may derive `UNASSESSED | PENDING | CURRENT | STALE_PROJECTION | FAILED` from immutable runs/revisions and S2 jobs instead of adding `site_window_projection`, provided a consistent scoped read proves the current accepted input basis and overlapping job state and does not select by `completed_at` alone. If it cannot prove freshness and atomic selection, it must add an atomic projection before cutover. The phase-2 worker's clock-based `knowledge_cutoff` is not a commit-ordered acceptance fence: an in-flight transaction may later commit a disposition timestamped before K. Therefore a selected historical revision is reproducible by its stored run/evidence IDs and digest, but arbitrary replay at K is not; phase 3 must not offer or describe arbitrary `knowledge_at` time travel as reproducible until a commit-ordered ledger watermark is implemented and reviewed as an S2 acquisition follow-up. Later acceptance still creates a dirty job and cannot leave a stale run marked CURRENT. No further owner product decision is requested; the S3-01 owner checkpoint remains.

Decision: `D-2026-10-11-s3-phase-3a-version-and-cutover`. Codex Architect resolves S3-01 phase-3a Q9–Q13 in `.agent/architect-S3-answers-3.md`, subject to its independent review. The stricter default cohort rule (two epochs for one source in a UTC window are ambiguous even when their spans do not overlap) and the named interval limitations lifted to the window result are material persisted assessment semantics. Name the corrected model `dispatch-3.1` before phase-3b/owner exposure, update its decision table and consumers, and automatically reconcile/reassess every stored default `dispatch-3` window under the new version. Preserve all `dispatch-3` runs/revisions/URLs unchanged as historical results; they may be shown stale or pinned, never selected as CURRENT under `dispatch-3.1`. A version change invalidates a prior comparison report, so rerun the current-environment gate after reassessment.

Performance cutover stays closed on every `MISSING_SOURCE` exception, `UNPROVEN` comparison, lineage break, stale model or changed baseline; a documented exception is not parity. An explicit empty legacy-claim set may pass only as a scoped zero-inventory statement, not proof that claim classifications match, with positive accepted-evidence/UI paths still reviewed before owner acceptance. `INTENTIONAL_DELTA` requires a claim-specific, versioned `dispatch-2` to `dispatch-3.1` rule explanation and verified comparable accepted public basis; merely finding any `INDETERMINATE` interval and any named window limitation does not prove causation and is `UNPROVEN` until demonstrated. With a matching current basis but an overlapping PENDING/LEASED job, the read remains `STALE_PROJECTION` (`RECOMPUTE_OUTSTANDING`), while `PENDING` is for no selected run. Phase-3b UI must show selected model/revision, ambiguity or limitation, stale/job reason, empty-set caveat and comparison/gate state without implying fuel or money. No new owner product choice is requested; the S3-01 owner walkthrough is still required.

Decision: `D-2026-10-12-finding-episode-and-revisions`. Codex Architect resolves `A-finding-episode` after the owner's contested-ranking choice of option A in `.agent/architect-A-finding-episode-request.md`; detailed S4-01 refinement and S3-01 Q14–Q22 rulings are in `.agent/architect-A-finding-episode-answers.md`. The first S4-01 mini-grid Finding is a **candidate generator-support episode**, not every Indeterminate assessment. Create it only from a CURRENT, coherently selected `dispatch-3.1` (or later reviewed dispatch-3.x) interval with a bounded `CANDIDATE_AVOIDABLE` segment and accepted public evidence. Indeterminate alone creates no avoidability Finding; if it replaces evidence for an existing episode, append a limited/unconfirmed revision without asserting that the issue disappeared or was fixed. Necessary-only or unassessed windows create no candidate Finding. A distinct evidence-quality Finding type would need its own later rule and fixture.

**Identity and continuity.** Persist one tenant/Site/domain/asset/mechanism-scoped Finding UUID and immutable `finding_key` when the first supported candidate span is recorded. The key is allocated from the persisted episode identity/anchor, not recomputed from a mutable first-ON timestamp, assessment key, model output hash, UTC day or private Lab run. Match later selected candidate spans to that episode across day boundaries when they overlap or are separated by at most the declared 20-minute dispatch continuity tolerance and there is no contradictory/ambiguous basis across the gap. An evidenced separation greater than 20 minutes creates a new Finding linked by `recurs_after_finding_id`; it is not revision 2 of the first. Persist the match rule version, observed bounds, anchor, cohort and selected window(s). A late earlier report can extend the episode without renaming it. If new evidence splits a previously single episode, retain the original ID for the portion containing its immutable anchor, create new linked Finding(s) for other supported portions, and append a revision explaining the changed coverage. If a later bridge joins two already persisted episodes, keep both old URLs/history, choose the earlier stable anchor (then UUID) as canonical, and record an explicit superseded/merged link on the other; never silently collapse or reuse IDs.

**Revisions and lifecycle.** Each changed selected assessment basis, supported candidate span, limitation or rule version appends an immutable FindingRevision under the same episode only when its canonical Finding basis changes; retry of the same basis is idempotent. A revision cites the exact selected interval AssessmentRevision and its AnalyticRun/model version, plus the selected window AssessmentRevision and every additional interval revision used for a cross-window episode, with exact accepted evidence IDs/digests and time-valid Foundation/binding provenance. Older `dispatch-3` results may be pinned as history but cannot create or refresh a CURRENT Finding under `dispatch-3.1`; later rules create new FindingRevisions, never relabel old ones. A CURRENT complete assessment proving the candidate span no longer supported appends a `NO_LONGER_SUPPORTED` revision and closes the active candidate claim, without asserting operational repair or savings. A stale, failed, ambiguous or Indeterminate assessment instead leaves the prior revision inspectable but marks current support unconfirmed; it does not auto-close. Reappearance after a proven separated interval creates a recurrence Finding and link. Model the close/reopen/split/merge transition as durable recorded history, not an overwritten claim.

**Read boundary.** S4-01 persists Finding/immutable FindingRevision, matching/lifecycle links, and a Site-scoped selected detail read/UI at `/sites/{site_code}/findings/{finding_id}` with optional exact `revision_id`, authenticated tenant/Site scope, selected dispatch revision/model/window/cohort, source/analytic watermark and exact lineage. The selected revision remains addressable after late evidence. Distinguish `NOT_ASSESSED`/projection lag or failed recompute, assessed `NO_FINDING`, `CURRENT` supported Finding, `UNCONFIRMED` prior Finding and closed/recurring history; a zero-row response is not proof of no issue without a current assessed basis. S4-03 owns the full Evidence/History child views, S4-04 owns Site FindingIndex/list, S4-02 owns money, and S6 owns Action/verification. The reusable cross-domain contract is stable Site-scoped episode ID, versioned matcher/transition, immutable revision-to-assessment/evidence lineage, recurrence/split/merge relationships, freshness/Unknown semantics and exact route selection; cold-chain excursion and EV session thresholds/fixtures wait for their domain slices.

S3-01 Q14–Q22 carries are ruled in the linked answer: retain only the proven capability-channel `INTENTIONAL_DELTA`, require comparable accepted evidence even for `MATCH`, and use the six-hour continuity bracket for comparison freshness. Keep today's UTC day as the honest default and the 60-row drill-down as an explicitly partial view; a bounded `S3-01u` usability carry will add assessed-day discovery and paged full evidence access without gating S4-01. Tests suffice for old-rule history; do not fabricate an obsolete-model walkthrough. The fixed fixture note and window-only FAILED/STALE result stand. Commit a stable fixture specification, keeping regenerated IDs in environment-bound run artifacts rather than presenting a stale per-run manifest as current. No further owner choice is requested; later owner review gates remain.

Decision: `D-2026-10-12-s4-finding-phase-1-clarifications`. Codex Architect rules on S4-01 Q1–Q9 in `.agent/architect-S4-01-answers-1.md`, subject to the independent phase-1 review. This amends `D-2026-10-12-finding-episode-and-revisions` where a more precise persistence rule is required. For a cross-window Finding, `UNIQUE(finding_id,assessment_revision_id)` is insufficient because another supporting assessment may change while the primary stays fixed. Keep the primary assessment FK and use unique `(finding_id,revision_no)` and `(finding_id,basis_sha256,transition)`, with an exact relation to every supporting interval/window assessment revision. The canonical basis includes selected window revision IDs as well as interval revision IDs, cited evidence, controls/bindings, claim bounds/limits and model/matcher versions; otherwise a Finding could silently continue to cite a no-longer-selected window basis. A changed selected control or window revision appends a FindingRevision even when candidate minutes stay equal. Call a provenance-only change `BASIS_REFRESHED`; reserve `SUPPORT_CHANGED` for a changed supported span, duration, claim or limitation.

The 20-minute episode bridge may cross an observed Necessary segment or an observed Indeterminate segment whose only limits are documented modelling uncertainty, provided every instant of the gap is covered by coherent observed segments and no evidence gap, contradiction or cohort ambiguity intervenes. Window coverage alone and a vacuously empty segment list cannot establish that bridge. A separated new Finding receives `recurs_after_finding_id` only when a public observed OFF establishes an actual break from the earlier generator episode; with an unobserved separation, open an unlinked Finding and show recurrence relation unknown. This narrows the earlier “evidenced separation” wording; elapsed time alone is not evidence of an OFF.

S4-01's F01 baseline Candidate must be demonstrated through the ordinary registered simulated gateway, gateway-sealed Batch V2 and central acceptance; the already reviewed S3 normal-path case may be reused if its public IDs and selected S4 fixture database are verified. Later held/contradictory/bridge cases may use separately labelled authenticated Batch V2 fault fixtures, never described as gateway-sealed or as private Lab truth. Lifecycle remains append-only in FindingRevision/relations; `finding.closed_at` is unnecessary if reads derive closure at the selected revision. A fixture-only internal FoundationService publication of generator minimum-runtime is acceptable without adding an S4 product route, but must be labelled as a fixture control and keep exact revision lineage. Spec `decided` instants are ordering labels; product acceptance uses actual server decision times. Phase-2/3 reads must expose these provenance and lifecycle distinctions. No further owner choice is required; the S4-01 owner checkpoint remains.

Decision: `D-2026-10-12-s4-finding-phase-1-fix-clarifications`. Codex Architect resolves S4-01 Q10–Q15 in `.agent/architect-S4-01-answers-2.md`, subject to the fresh phase-1 fix re-review. A current Indeterminate reassessment overlapping a previously `NO_LONGER_SUPPORTED` episode may append `UNCONFIRMED`; it does not erase the earlier closed revision or assert renewed Candidate. A supported Candidate over the same episode without a proven separated break appends `REOPENED` to that stable Finding, not a recurrence. A ≤20-minute stop between candidate spans can bridge identity only when both bounding OFF reports are accepted, ordered and no contrary report intervenes; it does not add Candidate runtime through the stop. A new episode gets an immutable recurrence link only with full assessed separation and observed OFF after the prior run and before the new one. On a later merge, preserve the earliest stable anchor/UUID as canonical even if that historical anchor is no longer in the current candidate cluster, and label the anchor as historical.

Include selected window revision/input basis in every Finding basis as already ruled, even when this yields many `BASIS_REFRESHED` revisions after same-day reassessment or backdated configuration. Keep each immutable revision and exact ID addressable; phase-2 read returns transition, prior/current selected assessment IDs, cause and unchanged-versus-changed support facts. Phase-3 detail may summarize consecutive provenance-only revisions as one “assessment basis updated” group with count and expandable exact revisions; S4-03 History owns the full chronological ledger. The normal gateway F01 proof may use 2026-10-02 with the then-effective positive template minimum runtime and roles-2, before the fixture's later zero-minute control that Lab correctly refuses. Do not conflate that ordinary case with the later fault-fixture F01 control basis or imply the two candidate starts are identical. No product route for zero-minute runtime is authorized, and no extra owner choice is requested.

Decision: `D-2026-10-12-s4-finding-phase-2-read-boundaries`. Codex Architect resolves S4-01 Q16–Q20 in `.agent/architect-S4-01-answers-3.md`, subject to the fresh phase-2 review. For this development pilot, the configured tenant/operator context may read the Finding API as S3 Performance does, with an explicit `DEVELOPMENT_TENANT_OPERATOR_CONTEXT` access basis. Injected 401/403 tests prove the access seam, not deployed human authentication or production tenant authorization; phase-3 UI and owner walkthrough must say so, and a real multi-user deployment remains gated by an authenticated principal/authorization implementation. Keep the bounded Site/UTC-day `finding-windows/{day}` read: `NO_FINDING` requires a CURRENT selected dispatch window and a completed Finding match at that basis; lag, failed or unassessed windows are not empty verdicts.

The prior bounded-stop rule explicitly forbids a contradictory report between the OFF anchors. The present interval result does not expose every intervening generator-state report, so the matcher must inspect a typed, tenant/Site-scoped view of the **selected AnalyticRun's accepted public generator-state evidence** over the stop span, under the same selection/fence. It must veto the bridge on a contradictory, non-GOOD, wrong-cohort or otherwise unaccounted intervening report; missing proof stays unbridged. Persist/cite the endpoint and checked intervening evidence IDs/digests in the Finding basis. Do not read raw SQL/Lab truth in the pure matcher or silently weaken the no-contrary rule. This is an S4 consumer/fixture correction, not a reason to mutate stored `dispatch-3.1` assessment semantics; if the typed proof cannot be delivered before phase-3 closeout, disable stop bridges and show the limitation until a reviewed follow-up. Relation facts (`claim.continuity`/`claim.recurrence`, OFF bounds and evidence) are claim lineage and must be included in the canonical Finding basis; a relation change cannot be hidden behind an unchanged hash. Preserve any already stored revisions and re-evaluate under a new matcher rule version if such rows exist.

The Finding product read has no separate file-backed Finding comparison, but a CURRENT positive Finding depends on the S3 selected assessment. For an imported Site, reuse the S3 Performance cutover gate at the product Finding route/window read before exposing a current Finding; when that gate is closed, return the typed closed/unavailable state rather than a positive claim or `NO_FINDING`. Pinned historical records may remain accessible only if clearly marked non-current and their exact source lineage is still readable. This does not add a second migration comparison. No further owner product choice is required; S4-01's owner checkpoint remains.

Decision: `D-2026-10-12-mock-gap-closure-mechanism` — **owner-confirmed 2026-10-12 for the gap catalogue and orphan guard; ranking deferred to W1 exit** (verbatim: "confirm gap catalogue and orphan guard now, defer ranking to W1 exit"; `.agent/owner-mock-gap-confirmation-2026-10-12.md`). The Codex Architect's detailed mechanism, scoring options and migration proposal are in `.agent/architect-mock-gap-mechanism-answers.md`. Add a versioned registry `mock_gaps` catalogue with one stable gap node per distinct missing non-core panel claim or on-screen missing-data element, reusing nodes for repeated placements. Each node records claim boundary, missing kind (`decision`, `data_source`, `contract`, `build`, `visual`), source status, reviewed AND prerequisites, UI placement or explicit unplaced reason, target wave or `unplanned`, owner/review trigger and evidence. Link panel portions and screen-ledger gaps to these IDs. An absent source such as gateway signal strength/firmware, commissioning records, policy documents or productive-use designation remains an unrankable data-source gap until its typed acquisition/authoring, ingestion or persistence, read and UI contracts are reviewed; simulator observations and private truth never become product evidence by implication. Add a typed UI missing-state reference and checker/`check-all` orphan guard, migrating through a dated non-expanding legacy baseline so V-01a is not blocked.

Keep W1's confirmed core scoring, K=10, technical gates and ≤5% contest unchanged. At W1 exit, ask the owner to approve a non-core ranking policy and per-screen completion mechanism; the separate lower-priority non-core lane and non-scored `complete-to-mock` audit item remain recommendations, not confirmed policy. An unplanned gap is pending allocation, not indefinite deferral; a conditional visual acceptance does not make a panel or screen Real. Planner/Implementer backfill W1 in reviewed M-size area batches plus an M schema/guard packet, reusing exact S1–S7 graph nodes where they prove the claim. The confirmed catalogue/guard mechanism did not gate V-01a's owner checkpoint or merge. No non-core scoring or product-tier change takes effect before the W1-exit owner decision and a reviewed implementation.

Decision: `D-2026-10-13-g-gap-packet-activation`. Codex Architect resolves the reviewed planning carries F1–F4 in `.agent/architect-G-activation-answers.md`. `I-G-01`–`I-G-05` are explicit unscored work, not invisible candidates and not exceptions to the single-active-task, review, owner or technical gates. Finish and merge the active V-01b first. At the next free slot, after checking the normal verified report for refusals or mandatory owner stops, activate G-01 before acting on a ranked `select`; then G-02 at the next free slot after reviewed and merged G-01 and the already merged/accepted V-01a. A ≤5% owner contest, outstanding owner checkpoint or checker refusal is never bypassed: resolve the stop first, then take the due G packet; a 5–10% notice is recorded but does not itself block that packet. G-03 through G-05 are later unscored backfills: refine and run each at the first free slot after its owning UI is merged, its packet prerequisites close, and no ready active-wave core candidate is waiting; otherwise hold it for the W1-exit backfill review. G-03 also requires accepted **and merged** V-01b, not merely S2-02. The coordinator lists all G packets and their due/deferred reasons in the verified next-work report and handoff; it does not assign a demo value or score to them. This ordering implements the owner's confirmed “now” catalogue/guard choice and reviewable migration without changing W1 scoring; no new owner ordering choice is required. G-01 validates all present `gap_ids` and UI placements, but requires complete non-core portion coverage only for explicitly enrolled batches; G-02 enrolls the four V-01a screens. G-01's first real tag is the visible Readiness gateway firmware missing state, with populated/unknown contact and 1440/390 evidence. A next-work fixture must prove the same ranked decision and score set with and without `mock_gaps` entries, including a W1-core-linked gap.

Decision: `D-2026-10-12-v01a-owner-visual-rulings`. Codex Architect rules on the V-01a owner feedback in `.agent/architect-V-01a-answers.md`, amending `tasks/V-01a-foundation-visual-fidelity.md`. `sites:1` remains the persisted Site directory portion: make Site/Type/Mode compact and keep location, lifecycle, origin and template as labelled secondary facts; do not infer Site Assessment, Top issue, Evidence limit or Last analysed from unscoped S2 records, one S3 dispatch day or S4-01 Finding detail. Positive analytical directory claims require a selected-window/freshness/aggregation contract and later Site FindingIndex/Site Summary work, so the current registry claim boundary and technical gates do not change. The owner prefers a Foundation h1, green/amber configuration Readiness and a bus-bar SLD with icons. Green means required configuration complete for the selected effective version; amber means a known configuration gap; Unknown remains neutral, with no Evidence/contact/health inference. The SLD and topology cards may use semantic icons and bus-bar geometry only for selected declared components and connections, with no invented breakers, meters, live readings or mock values. A chosen component is keyed by stable component ID in the address, survives reload and view switches, and persists across a period change only while that component remains declared; its channels always come from the newly selected effective binding set. These are V-01a visual/interaction fixes, not technical closure of deferred analytical panels. The standing independent re-review and owner visual checkpoint remain; no further owner choice is required before the fix round.

Decision: `D-2026-10-12-v01a-round3-readiness-and-organization`. Codex Architect rules on the owner's V-01a round-2 feedback in `.agent/architect-V-01a-round3-answers.md`, amending the V-01a task. Readiness leads with four selected-configuration category cards and a plain Readiness/commissioning table; category colour is derived from typed Foundation gaps, controls and required bindings, while commissioning confirmation is “Not recorded” without a commissioning source. A gateway panel may compose the existing S2 `/gateway-health` read with current registration, but labels central contact at server read time independently of the selected Foundation period, preserves Unknown/Stale/unavailable/disabled states, and makes no physical-device, accepted-Evidence or asset-health claim. This bounded read composition needs independent source/UI review before `readiness:2#a/b` or `readiness:3#a` noncore registry portions are marked delivered; `readiness:3#b`, `readiness:4#b`, `readiness:1` W1 core mapping and whole-screen partial status stay unchanged. Plain-language values and important gaps remain primary; raw binding/role/channel/version/provenance records move into explicitly labelled Advanced details. Foundation may name the first typed critical-load priority and configured loads, but cannot designate Grain mill “Productive use” from its name; financial/change/constraint-proof links require actual destinations, while Dispatch is a separately selected-window assessment. Chosen-part detail moves into a compact in-context strip with expandable channels and unchanged `component` URL semantics. No further owner choice is needed before building; independent re-review and the owner visual checkpoint remain.

Addendum to `D-2026-10-12-v01a-round3-readiness-and-organization` (owner missing-data rule): V-01a must visibly name deferred mock facts beside supported panels, as specified in `.agent/architect-V-01a-round3-answers.md` “Addendum: missing-data states and conditional acceptance.” A grouped Sites Operating view cell names the unavailable Assessment, top issue, Evidence limit and last-analysis claims without four dummy columns; nearby notes name deferred aggregate/setup claims. Foundation names absent productive-use, financial/change and constraint-proof data; Readiness names missing commissioning and unsupported gateway metrics; SLD explains absent breaker/meter/monitoring/status sources outside the drawing without drawing fictional glyphs. Any owner visual acceptance of such panels is expressly conditional on these named data gaps and covers layout/copy only. Record the condition, missing source and later trigger per panel in the review packet and existing ledger/registry caveat fields; keep partial statuses and technical gates, with no whole-screen Real promotion. A later supplying slice must replace and re-review the missing state. The owner has not yet accepted the round-3 visual result.

Decision: `D-2026-10-13-v01b-visual-and-lab-read-boundaries`. The Codex Architect's Q1–Q8 and C1 rulings are in `.agent/architect-V-01b-answers.md`. V-01b may use only supported Site Evidence and Lab reads for visible facts; missing capability, per-report disposition and Portfolio destination remain named gaps for G-03/later contracts. The registered Stage's obsolete upload/no-receipt assertion is replaced in the V-01b UI with neutral local-Stage copy (done in V-01b fix round 3, reviewed in `.agent/V-01b-fix3-rereview.md`); authoritative central receipt state comes from the Commit read, and the Stage contract is corrected separately. A historical Lab run's drawing should resolve its pinned Foundation/binding basis, never the Site's current version; this requires a later verified historical read and leaves V-01b's drawing layout assertions unverified. The Lab-specific <=640px shell selector and stricter shell-overflow guard are approved because V-01b owns the measured Lab layout. Owner visual acceptance (conditional, 2026-10-13, `.agent/owner-V-01b-walkthrough-2026-10-13.md`) does not promote unsupported mock portions to Real.

Decision: `D-2026-10-13-g01-placement-and-orphan-scan-boundary`. The Codex Architect ratifies G-01 Q1–Q4 in .agent/architect-G-01-answers.md: a bounded missing-claim phrase set, one unconditional firmware placement across gateway-contact branches, file-plus-normalized-literal baseline identity with exact counts, and a next-work refusal on an invalid gap catalogue. G-02 splits the combined gateway uptime, completeness and signal-strength copy into separate claims, IDs, rendered elements and unique placements; one element does not carry several gap IDs. G-02 extends the orphan scan with reviewed specific absent-capability cues, including “not tracked yet” and commissioning-specific “not recorded”, without globally matching ordinary runtime “not recorded” states. These are unscored migration/guard rules; W1 core scoring and the deferred W1-exit non-core policy remain unchanged. G-01's narrow re-review (ACCEPT, `e79ce8b`) and 1440/390 browser evidence (113/113) are recorded; its owner visual checkpoint remains before merge.

Decision: `D-2026-10-13-s403-legacy-evidence-and-lineage-words`. The Codex Architect's S4-03 Q1–Q6 rulings are in .agent/architect-S4-03-answers.md and .agent/architect-S4-03-answers-2.md. The assessment-keyed legacy Evidence tab may offer clearly labelled overlapping-day Finding candidates, but day-level uniqueness does not prove an exact assessment-to-Finding relation and cannot auto-redirect; an exact bridge is a later reviewed backend contract. The read retains stable broken-lineage codes and IDs with product-safe human words, and the UI never falls back to raw engineering prose or restores a positive claim on broken lineage. The selected FindingRevision ID carries its stored assessment window/evidence basis across Finding, Evidence and History; Evidence page/record and Finding analysis state remain local to their views, with no arbitrary window or knowledge-at replay. Finding Evidence may show a whole-revision by-role count for resolved cited records, naming unresolved IDs separately; per-input Coverage and analytic Use remain distinct catalogued gaps, not closed by that aggregate. History lists every stored revision with an honest incomplete/drift state; a late-accepted-reading note is version annotation, not a workflow or recommendation event. Only reviewed core portions may be marked delivered; panels remain partial, G-04 retains omitted mock content, and owner visual acceptance remains required. Owner accepted S4-03 conditionally on 2026-10-13 (`.agent/owner-S4-03-acceptance-2026-10-13.md`).

Decision: `D-2026-10-13-g02-visible-placement-and-state-boundary`. The Codex Architect's G-02 Q1–Q6 rulings are in .agent/architect-G-02-answers.md. The Site SLD must register and tag each visible missing-reading slot kind, including SVG and table placements, while its shared Lab rendering and pure configured-diagram scope captions remain separate. The G-02 orphan scan gains reviewed exact/scoped cues for its additional missing-capability wording; ordinary unavailable, undeclared and unassessed runtime/configuration states do not become gaps by blanket phrase matching. Six explicitly unplaced catalogue entries remain valid: absent policy/capability claims cannot be fabricated, and three bounded real-read portions await independent review. The five commissioning placements share one absent confirmation-source gap until a reviewed per-area confirmation contract exists. Gated Lab entry points in workspace chrome and the Sites cross-workspace create action are developer affordances, absent when the Lab gate is off; the no-simulator-language rule still governs analytical product copy. W1 core scoring, panel partial status and the W1-exit non-core policy boundary remain unchanged. G-02's fix re-review (ACCEPT) and 1440/390 browser evidence (321/322; the 390 px SLD caption is a pre-existing owner carry) are recorded; the owner accepted G-02 conditionally on 2026-10-13.

Decision: `D-2026-10-13-s4-bounded-financial-basis`. The owner selected `A-S4-financial` in the 2026-10-13 next-work contest; the Codex Architect resolves its S4-02 contract in `.agent/architect-A-S4-financial-answers.md`. A Site-scoped `FinancialAssumptionRevision` has immutable scope/key/revision, ISO currency and canonical unit, Decimal value, explicit authored/contract/recorded/scenario basis, half-open valid time and recorded/superseded time. Writes derive human `author_id` and actor/authorization metadata from a verified server principal under `A-actor-identity`; absent authentication disables human editing, while an explicitly labelled server-authorized SYSTEM fixture may publish with service/job provenance. No default price, silent tenant fallback, overlapping current validity, client-asserted author or unlabelled retroactive edit is permitted. The first key is Site diesel price per litre; maintenance needs its own rate/source and matching quantity and cannot be inferred as actual expenditure from candidate runtime.

S4-02 may derive a modelled, assumption-conditioned **potential fuel-cost exposure** only for an exact supported mini-grid FindingRevision and its selected assessment/evidence/configuration basis. `dispatch-3.1` publishes no fuel-saving quantity: a separately reviewed versioned fuel derivation must use accepted generator-power coverage for candidate segments and the selected Foundation's L/kWh consumption property, with explicit uncertainty/bounds and no private Lab truth, unsupported interpolation or pricing of Indeterminate/Necessary time. Candidate time proves no saved liters. The lower bound on potentially avoidable fuel is zero; an upper amount is shown only under a defensible stated model bound. A price valid for the entire consequence window and known at the selection cutoff multiplies unrounded compatible Decimal quantity bounds; displayed lows round down and highs up to currency minor units. No price yields `UNPRICED` with null amount, never zero; unsupported quantity, mismatched unit/currency/period/basis, stale projection and historical supersession receive distinct honest states.

Each append-only `FinancialConsequenceRevision` stores exact FindingRevision, primary and supporting assessment revisions, technical quantity bounds and source/basis digest, every assumption revision used, formula version, overlap group, half-open window, amount bounds/currency and limitations. An explicit backdated price correction valid over the old window appends a new assumption and consequence for the same FindingRevision and quantity; a future price does not reprice yesterday, and neither edit mutates the Finding or pinned old consequence. S4-02 persists and reads Site-scoped assumption/consequence current and exact history with actor, validity, lineage, pagination and typed refusal/pending states. After review it may support `financials:1#a/2#a` and `assumptions:1#a/3#a`; `mini:4#a` waits for S5 composition. Trade-offs, maintenance without a source, `financial_scenario`, FX, extrapolation and estate totals remain open. `A-money-comparability` stays outside W1 ranking and is required before cross-option/Site aggregation. Planner splits the outline into two reviewable M slices (assumption publication/history and honest unpriced bridge; then modelled quantity/consequence/repricing/UI), with the S4-02 owner checkpoint after independent review.

For G-03–G-05, `missing_kind` names the first absent authority: `contract` when record type, author/validity semantics or read rule is undefined; `data_source` when that contract exists but the producer/records are missing; `decision`, `build` and `visual` retain their distinct reviewed-choice, implementation and presentation meanings. This clarifies the commissioning example in `D-2026-10-12-mock-gap-closure-mechanism`: `G-readiness-commissioning` is now `contract/absent` because no commissioning record type exists. It remains open, unplanned and visibly “Not recorded”; the owner allocates its future contract/workflow at W1 exit. No non-core ranking or W1 core score changes here.

Addendum to `D-2026-10-13-s4-bounded-financial-basis` (S4-02b `fuel-cost-1`): The first reviewed fuel model may use immutable, dimensionless `sfc_upper_multiplier = 1.10` as an expressly conditional assumption that actual L/kWh does not exceed 1.10 times the selected Foundation SFC. Its version records the value, inequality, scope, source, reviewer/date, formula and immutable lineage; it is not a measured or calibrated physical bound. For each exact FindingRevision, quantify only observed Candidate spans fully covered by accepted, good, nonoverlapping generator-power mean intervals, each wholly contained within contiguous Candidate time and carrying one unambiguous positive SFC throughout. Count each distinct interval once: `quantity_low = 0 L`, `quantity_high = 1.10 × Σ(mean kW × full interval hours × SFC L/kWh)`. Never use dispatch interval `upper_minutes`, a segment `max mean × duration`, or prorating of an interval that crosses non-Candidate time. Any failed coverage, containment, power or SFC condition makes the whole consequence `QUANTITY_UNAVAILABLE` with no amount. The upper is a model-conditioned potential fuel-cost exposure, not measured fuel saved or a physical maximum. Independent model review and the planned owner UI checkpoint still apply. Rulings: `.agent/architect-S4-02-answers.md` (Q1, plan review C4).

Decision: `D-2026-10-14-s402-post-review-follow-ons` (addendum to `D-2026-10-13-s4-bounded-financial-basis`). The Codex Architect's S4-02 batch rulings are in .agent/architect-S4-02-batch-answers.md. A future `SUCCESSION` may replace the sole open-ended current Site price assignment at its exact `valid_from`, provided the prior revision, authorization and idempotency checks pass; preserve the previous recorded-time history and create no empty assignment. Accepted evidence that may change an exact FindingRevision's fuel technical basis must durably enqueue scoped, idempotent consequence work; a fresh `STALE` read does not replace that work. Demonstration authorship must be recorded by a server-authorized, tenant/Site-scoped ingestion publication and traced through accepted evidence before a real-Site pilot or W1 exit; Site/day matching is only a bounded fixture label. `assumptions:3#a` requires Site consequence history selectable at the same recorded cutoff as assumption history; per-Finding Overview versions alone do not close it. Existing reviewed S4-02 money claims may close independently, while this core history portion stays open until its read and UI are reviewed. Owner S4-02 checkpoint passed 2026-10-14 (`.agent/owner-S4-02b-acceptance-2026-10-14.md`); the owner settles mixed/unknown source wording at the W1 checkpoint.

Decision: `D-2026-10-14-s5-selected-window-overview`. The Codex Architect selects and resolves `A-S5-overview` under the owner's 08:40–10:40 +0300 delegation; the reviewed-input report `.agent/next-work-2026-10-14c.json` selected it at 2.198 versus `A-action-lifecycle` at 2.009 (8.60% gap, published 5–10% tie-break notice). The contract and Planner instructions are in `.agent/architect-A-S5-overview-answers.md`. S5-01 remains one bounded slice for `mini:1#a`, `mini:2#a` and `mini:4#a`; the independent Site Finding list/positive rows belong to S4-04 and S5-02 (`mini:3#a/b`).

`SiteWindowSummary` is a tenant/Site-scoped, selected half-open UTC window read/projection over committed public records. It identifies the exact selected S3 assessment revision and its source/configuration/evidence basis, eligible S4 Finding revisions and any bounded financial consequence revisions, with accepted-source and analytic watermarks, model version, built time, coverage and a typed freshness reason. A user date change selects a new window; reload preserves the requested window and pinned detail IDs. Build atomically from a consistent committed basis or derive an equivalent scoped read; late accepted evidence, analytic/model/configuration changes and consequence work invalidate/rebuild affected windows. A projection is CURRENT only when its accepted-source basis matches the ledger and relevant analytic/consequence work is complete. Preserve old exact revision links when a new result is pending or stale. `UNASSESSED`/Unknown means no completed assessment or insufficient input, `PENDING` means first computation or queued work with no current result, `STALE_PROJECTION` means an earlier result exists but its watermark/basis lags or work is dirty, and `FAILED` names failed work without a usable current result. None implies Healthy, zero cost or no Findings.

S5-01 presents the selected S3 dispatch objective/status and coverage, an evidence-backed selected-window timeline/operating context, and a bounded optional money card with exact assessment, FindingRevision, consequence/assumption and accepted evidence drill-downs. It must not copy the mock's service, battery, fuel-balance, renewable-opportunity, maintenance allowance, causal charging or recommendation claims without their own source and contract. The money card may show an amount only for a `CURRENT PRICED` consequence on the selected exact FindingRevision, compatible window and current technical/price basis; it labels the `fuel-cost-1` model-conditioned potential exposure with zero lower bound, limitation and demonstration provenance. `UNPRICED`, quantity unavailable, stale, pending, superseded, mixed/unknown source and absent consequence are separate no-amount states. Do not sum overlapping Findings, invent a Site total, or convert this to savings. Ordinary data currently has 0 of 11 qualifying Findings, so show an honest no-current-priced-consequence state and the relevant limiting Finding/Evidence links; the authored P01-power example may show its one amount only with a visible Demonstration-data label and exact lineage. Stored source provenance remains a W1-exit/real-pilot gate, not an implied property of the current date heuristic.

The S5-01 reviewer may promote `mini:1#a`, `mini:2#a` and `mini:4#a` only after selected-window, reload, stale/Unknown and exact-link evidence is reviewed. `mini:4#a` means one bounded consequence or explicit unpriced/unavailable state; the mock's blended money composition remains an open G-05/non-core gap. `mini:3#a/b` stays open until S4-04's Site FindingIndex and S5-02's Overview integration prove both scoped empty/Unknown and positive rows. The S5-01 UI may say the Finding list is unavailable while that index is missing; it may link a known selected Finding from a card without claiming a Site-wide list. S5-01 stays one reviewable read/UI slice; Planner must refine wire fields, fixture windows, projection/recompute seam, exact destinations, 1440/390 states and independent review/owner walkthrough. The durable evidence-acceptance consequence-work follow-on is a technical prerequisite of `I-site-overview-read`; it must close before S5-01 presents current money. Price equal-start SUCCESSION and stored demonstration provenance have separate follow-on packets; the latter gates W1 exit and the first real-Site pilot.

Owner-absent checkpoint rule: `USER_REVIEW_REQUIRED` remains a real owner visual checkpoint. During this and future owner-absent windows, complete implementation, fresh independent review and a reproducible walkthrough, then hold that slice's merge and acceptance until the owner performs and records the visual check. The Architect may decide delegated sequence/copy questions but cannot record an owner walkthrough on the owner's behalf. Planning and unrelated non-UI/G work may proceed under normal single-active-task and dependency rules; a dependent next slice may be prepared on a clearly stacked branch without claiming its predecessor merged or accepted. Resume merge/registry promotion only after the actual owner checkpoint.

Decision: `D-2026-10-14-action-lifecycle-and-policy-application`. Under the owner's 08:40-10:40 +0300 delegation, the Codex Architect chooses and resolves `A-action-lifecycle` in the 0.54% next-work contest (`.agent/next-work-2026-10-14d.json`: evidence-acceptance consequence work 2.020, Action lifecycle 2.009). The scores are effectively tied. This bounded architecture decision can close now and removes the common S6 Action gate across roughly fifteen W1 core portions; the evidence-acceptance consequence implementation still needs a Planner packet and remains a hard prerequisite of S5-01's money read. The next verified report, rather than this contest snapshot, routes the next work. No S6 UI owner checkpoint is waived.

S6-01 creates one immutable, tenant/Site-scoped Action identity from a reviewed persisted `FindingRevision` under the canonical Finding route. It pins the originating revision, selected assessment and accepted-evidence/configuration basis; a later Finding revision does not silently rewrite that origin. A Finding may have several Actions, but each accepted recommendation creates or idempotently returns one Action for its server-defined command key. The recommendation is a bounded proposed reserve-SOC policy trial with explicit purpose, limitation and source Finding; it is not a measured saving or verified outcome. The Action detail root is `/sites/{site}/actions/{action_id}` with stable child routes and exact `event_id` selection, and Site/Finding back-links. S6-01 may navigate from a known Finding or Action ID before the separate S6-03 Site ActionIndex exists. Hidden unsupported tabs must not masquerade as empty delivered views.

Action state is derived from an append-only, server-ordered `ActionEvent` ledger. Record stable event ID, Action and Site, event type, `occurred_at`, server `recorded_at`, idempotency key, actor kind/ID, source channel, authorization basis and triggering command/job or content revision. Idempotent identical retries return the event; conflicting reuse and cross-Site references fail. Historical reads select a recorded cutoff and then `(recorded_at,id)` order; a backdated `occurred_at` is displayed as such but never rewrites the audit order. `PROPOSED`/`ACCEPTED`, application `PENDING`/`APPLIED`/`FAILED`, and later verification status are separate dimensions. Acceptance does not assert application; an applied change or completed work does not assert benefit. A failed application preserves its attempt, error and retry relation without an effective-policy claim. No human author, approval or attestation is inferred from a gateway credential, client field, local OS user or SYSTEM fixture. Under the existing `A-actor-identity` rule, human writes need a verified operator principal; otherwise only a clearly labelled, server-authorized SYSTEM demonstration command with stable service/job provenance is allowed, or the write stays unavailable.

The supported S6-01 change is a controlled reserve-SOC edit through S1 Foundation publish, producing a new immutable effective `FoundationRevision` and an immutable change artifact that links Action, accepted recommendation, authorized command, old/new revision IDs, exact field/value/unit, validity and recorded time, and the application event. Validate the expected old revision and Site scope under the publish lock; reject stale, unauthorized or invalid edits and record a failed attempt without claiming the new setting took effect. `APPLIED` requires confirmation of the persisted new effective revision; an ActionEvent alone is insufficient. The old basis and every event/change revision remain addressable after reload. Do not mutate a Lab-only override or rewrite accepted evidence. S6-01's Execution/History and applied `changes:1#a` show policy activity with event and configuration provenance, including pending/failed cases; they do not show an effect verdict.

S6-02 owns the separate immutable `VerificationPlanRevision` and later `VerificationOutcome`. A plan pins this Action, the applied-change event and new Foundation revision, a pre-change baseline assessment/evidence basis, target, service/reserve guardrails, required coverage and later-window selection rule before evaluation. Use separate baseline and later Lab runs under their respective fixed effective Foundation revisions; commit their public reports through the ordinary gateway and central acceptance. Evaluate a closed later accepted window against the frozen plan and baseline, with exact analytic/evidence IDs. Missing or conflicting evidence yields `INCONCLUSIVE`; failed guardrail prevents `VERIFIED` even if the target improves; later results append/supersede without rewriting prior outcomes. Plan/evidence/verification child routes preserve exact plan and outcome IDs. `A-S6-verification` remains open for the full comparison rule; this lifecycle decision does not resolve it. S6-03 alone owns the Site-scoped ActionIndex/list and its watermarked empty/positive states; `A-action-index` remains open. Planner must refine S6-01's event transition table, command/API schema, actor path, race/idempotency checks, Foundation publish seam, stored fixtures and desktop/narrow Action-root states against the v6.9 Action screens and technical design before implementation.

Decision: `D-2026-10-14-s402c-late-sequence-and-s5-money`. The Architect rules that gateway admission sequence does not establish source-time order for a validated store-and-forward source. S3 must version a source-time-aware cohort rule with explicit clock/overlap/epoch limits and reassess affected windows without rewriting history. S4 must carry a material series refusal into the revised Finding and state why the episode ends. Until a reviewed reassessment resolves generator-series ambiguity, S5 withholds an amount for that affected selected Finding/window despite a `CURRENT PRICED` consequence, and shows the limitation and exact lineage. `I-late-reading-series-and-money-limit` and `I-analytic-finding-worker-schedule` are separate prerequisites of `I-site-overview-read` before S5-01; both also gate real-Site readiness. The latter schedules S3/S4 workers and makes backlog/failure visible so late evidence reaches the revised Finding without manual commands. The broader simulated/real analysis-input backlog remains for W1 exit. S4-02c acceptance is unchanged; its reviewed consequence work may close on merge. The S5 owner visual checkpoint remains required. Rulings in .agent/architect-S4-02c-answers.md; S4-02c review `.agent/S4-02c-review.md` F1.

Decision: `D-2026-10-14-s402d-schedule-storage-and-install-gate`. Ratify migration 0013's four bounded, mutable schedule tables and `scheduling/adapters/postgres_schedule_store.py` as the sole eighth PostgreSQL writer for them. Rule 8 may admit only this module's inserts and named schedule-state updates on those tables, with reverse ownership, adapter isolation and existing seven-writer protections retained. S3 jobs, Findings, evidence and financial records remain under their current writers. The environment timer may be tested privately but must not be installed on an owner-visible host until `I-late-reading-series-and-money-limit` lands; installation replaces the per-Site consequence timer. S4-02d owns DB-clock resolution of I3 for scheduled work and an independent concurrent-ingestion proof for I4; any ingestion defect belongs to a separately scoped evidence fix. No owner decision is required unless owner-facing behavior changes. Authority: `.agent/architect-S4-02d-request.md`, `tasks/S4-02d-analytic-finding-worker-schedule.md`, `.agent/S4-02d-plan-review.md` M1, and S4-02c review I3/I4. Rulings in .agent/architect-S4-02d-answers.md.

Decision: `D-2026-10-15-lr01-source-time-cohort`. Accept LR-01 Q1-Q4 as corrected by Follow-up M1 in `.agent/architect-LR-01-answers.md`. Source-time order requires a versioned, scoped clock attestation from an identified authority covering each reading with maximum UTC error no greater than 60 seconds; simulated proof stays separate from real-source proof. Order an attested channel by each reading's `placed_at` instant (measurement interval end, otherwise source time) +/- the attested error, not by the full measurement interval widened by error. Measurement intervals that only touch do not overlap; genuine measurement-interval overlap or overlapping placement-uncertainty intervals in one channel remains `REPORTS_OVERLAP`/ambiguous. Where placement-uncertainty intervals are disjoint, gateway admission sequence disagreement is a late arrival, not `SEQUENCE_ORDER_INVERTED`; sequence still resolves identity and duplicates. Retain epoch ambiguity unless the existing explicit cohort selection is used; automatic cross-epoch continuity needs separate review. Attestation changes enqueue all affected UTC-day windows through the matching six-hour query bracket and neighboring continuity windows, preserving immutable runs and selections. Proven Candidate spans may remain `SUPPORTED`, while a material refused tail produces a new FindingRevision with `GENERATOR_SERIES_AMBIGUOUS` and `SERIES_LIMIT`. A shared read-derived money eligibility gate withholds current amount during pending reassessment or material unresolved generator-series ambiguity, even if a historical consequence is `CURRENT PRICED`; eligibility alone does not replace the exact-head consequence and source/currentness checks. The Planner must add the corrected overlap rule, requeue scope, eligibility precedence and explicit-epoch boundary to the LR-01 packet before implementation. Authority: `tasks/LR-01-late-reading-series-and-money-limit.md`, `.agent/S4-02c-review.md` F1, and `D-2026-10-14-s402c-late-sequence-and-s5-money`.

Addendum to `D-2026-10-15-lr01-source-time-cohort` (LR-01 deviations, 2026-10-15): A returning A -> B -> A Finding basis may append a new immutable revision; migration 0015 removes all-history basis uniqueness, while latest-revision replay, Site locking and the matcher fence enforce idempotence. For LR-01, any same-asset generator-role series limit intersecting the episode +/- 6 h bracket withholds current money, even without Candidate-tail overlap; exact limit lineage must remain visible. The shared Finding/Financials money eligibility gate stays unchanged by schedule health. S5 keeps schedule and other upstream blockers in its separate currentness status and shows money only when that status is CURRENT, the shared gate is ELIGIBLE, and the exact-head consequence passes its existing checks. The owner-visible money view is the Financials bridge; the Finding page shows SERIES_LIMIT. An unwired or failed consequence-read gate fails closed; ELIGIBLE stubs are test-only. Required packet, docstring and proof changes are in `.agent/architect-LR-01-deviations-answers.md`. This is an Architect contract ruling, not owner acceptance or a review verdict.

Decision: `D-2026-10-15-owner-absence-work-order`. Under the owner's 2026-10-15 absence delegation, the Architect orders the single build stream: finish and freshly review LR-01; prepare and build S5-01 selected-window Overview on its reviewed head; then advance S6-01 Action store/read/UI, stored demo provenance, price equal-start succession, the S4-02d I3 evidence-owner clock fix, the F-B statement-level guard, OPS-01 Low carries, and the FindingIndex/S4-04 lane as capacity and gates allow. The 0.20% LR-01 versus Action-store contest stays with LR-01 first; if S5-01 and Action store later score within 5%, S5-01 wins because it consumes the just-reviewed money eligibility and closes the blocked Overview path. S4-04 does not gate S5-01. Planner may refine S5-01 and S6-01 in parallel with LR-01, followed by the named non-UI packets, with code-reality checks. Only one Postgres-heavy build runs at a time. Independently reviewed non-UI work may merge if it does not depend on an unmerged UI branch; all USER_REVIEW_REQUIRED merges and acceptance wait for the owner's actual walkthrough. The exact conditional order, stack and review gates are in `.agent/architect-autonomy-2026-10-15-answers.md`; this decision does not waive the schedule install, W1 exit or real-pilot gates.

Decision: `D-2026-10-15-s501-finding-choice`. Accept the S5-01 price-independent latest-episode choice with half-open intersection, canonical merged IDs only, greatest latest-revision episode start and smallest stable Finding UUID as tie-break. Do not filter by money or lifecycle. Retain the selected Finding and exact revision links through stale/withheld states; a new consistent S4 basis may change selection, while an incomplete basis cannot authorize a new current choice or amount. `ABSENT` requires complete current scoped discovery. Full implementable rule: `.agent/architect-S5-01-answers.md`.

Decision: `D-2026-10-15-s601-action-store-and-ui`. Under the owner's 2026-10-15 delegation, accept S6-01 Q2-Q5 with the transaction, scope, capability and cutoff details in `.agent/architect-S6-01-answers.md`; amend Q1 to the versioned `reserve-trial-1` rule there. Only a current, reviewed, supported pinned generator-support Finding with unambiguous numeric Candidate SOC and matching Foundation reserve may propose the bounded five-percentage-point reserve trial. It is a policy-sensitivity experiment, not a causal remedy, saving or verification claim; otherwise show a typed unavailable reason. Ratify `actions/adapters/postgres_action_store.py` as the sole ninth PostgreSQL writer for append-only Action, event, change and Action-owned child rows. The Action adapter opens the apply transaction and locks Action before calling a caller-owned-connection S1 publish that locks Site; the S1 adapter writes only Foundation and binding rows, and an Action-adapter callback writes the change artifact and APPLIED event on that same connection before the outer commit. Rule 8 must admit only this ninth writer's INSERTs to its tables, reject Action-table writes by every other module and reject mutation or DDL in the Action adapter while retaining all eight existing protections. Authorized same-Site failures remain separate durable attempts after rollback. Include the pinned FoundationRevision in recommendation identity and persist the immutable accepted-recommendation snapshot; after acceptance, recommendation read returns it with the Action link and a separate live status. A server-authorized, state-neutral SYSTEM demonstration `OBSERVED` event with fixed `DEMO_REVIEW_NOTE` code may carry an explicit `occurred_at` between ACCEPTED and server `recorded_at`, no more than 30 days earlier, to prove backdated history without changing application state. SYSTEM demonstration commands require a server-issued scoped capability and explicit label. The full M1-M3 ruling is in `.agent/architect-S6-01-answers.md` under "Follow-up (plan review M1-M3)". S6-01a/S6-01b packets must incorporate the named changes before implementation; S6-01b still waits for the owner's actual visual walkthrough before merge.

Decision: `D-2026-10-15-s405-stored-demo-provenance`. Under the owner's 2026-10-15 absence delegation, accept S4-05 Q1-Q3 as amended by Follow-up (plan review M1) in `.agent/architect-S4-05-answers.md`. A server-authorized, immutable pre-admission publication binds an exact Batch V2 commitment to tenant/Site, gateway/source, external batch ID and canonical digest. `AUTHORED_DEMONSTRATION` additionally binds fixture/spec ID and version, including authored P01 and P02. `REGISTERED_SIMULATION` binds an ordinary simulator batch to a server-recorded run identity; `SIMULATED` mode or a private manifest alone is insufficient. Publication and admission serialize on the scoped batch key; post-admission registration and mismatched commitments fail. Accepted IDs inherit immutable provenance, duplicates retain their original accepted ID, and historical unbound IDs stay unknown. Finding and consequence source state derives from each revision's exact accepted IDs, including consequence power intervals. Coherent all-authored or all-registered-simulation sets may show a current amount only when LR eligibility, exact basis, currentness, source-open and quantity/price gates also pass. Mixed or unknown source blocks a current amount in Finding Financials, consequence and S5 Overview regardless of `CURRENT PRICED` or LR eligibility; prior values remain audit-only. Real data remains unknown and unable to show current money until a separate server-authorized `ATTESTED_REAL_SOURCE` follow-on is implemented. Create open registry node `I-attested-real-source-provenance` in `real_pilot_requires` before resolving `I-stored-demo-provenance` or installing a pilot timer; S4-05 may resolve before the real-source node, but its resolution is not pilot readiness. Amend S5-01's source gate to consume stored exact-revision provenance whichever slice merges second. Extend the existing PostgreSQL evidence-ledger writer, not the writer count: rule 8 permits only its INSERTs to publication/link rows, refuses other writers and mutations, preserves existing writer protections, and is backed by database immutability. Visible copy and pilot designation still require the owner's W1 checkpoint; this decision grants neither owner approval nor W1/pilot readiness.

Decision: `D-2026-10-15-a-finding-index`. Under the owner-absence work order item 9, resolve `A-finding-index` for a tenant/Site/domain and selected half-open UTC window of at most 31 days. The W1 read selects the latest immutable S4-01 FindingRevision of each canonical Finding from one consistent S3/S4 basis, includes every intersecting lifecycle state, and uses strict half-open overlap. Its stable row key is `(tenant_id, site_id, finding_id)`; default order is episode start descending, then Finding UUID ascending. Return exact revision/detail and assessment/evidence lineage, scoped accepted-source and analytic/matcher watermarks, selection token, built time, coverage and typed currentness. Complete discovery requires every intersected UTC-day analytic window and neighbours reachable through 20-minute episode continuity matched through each current selection seq. Only complete current scoped discovery under an open S3 Performance cutover gate may state zero Findings; pending, stale, failed and unassessed reads remain visibly Unknown or historical. A closed gate refuses the unpinned index with HTTP 409 `PERFORMANCE_CUTOVER_CLOSED` and its reason, with neither current rows nor a no-Findings claim, as on Finding routes; S4-05 stored provenance joins that gate once merged. A changed basis invalidates the bound page cursor. S4-04 adds a new index read without changing the consumed `findings_over` helper, and must independently prove a watermarked assessed zero-row fixture, a closed-gate 409 variant, a persisted positive-row fixture, exact links after reload, invalidation, Site isolation, first-row equality with the S5-01 card Finding on the same basis, and narrow/desktop UI. Index rows do not depend on money; optional current consequence display consumes LR-01 money eligibility and S4-05 exact-revision source provenance after their reviewed branches enter the build baseline, plus the existing exact-head, quantity, price and currentness gates. Mixed/unknown source and withheld/pending eligibility expose no current amount. S5-02 reuses the Site/window rows for both `mini:3` variants after S4-04 and S5-01 review; S4-03, S5-01's other panels and S3 dispatch do not wait on the index. Full contract and implementation handoff: `.agent/architect-A-finding-index-answers.md`. This decision grants no owner UI copy or walkthrough acceptance and does not implement a global or cross-domain index.

Decision: `D-2026-10-15-s404-contract`. Accept S4-04's separate `/api/sites/{site_code}/finding-index` route and HTTP 409 `INDEX_BASIS_CHANGED` for a well-formed cursor whose fenced basis or scope changed; malformed cursors are 422. Historical stale or failed rows require a durable prior selected snapshot with exact revision IDs; without one, report the applicable non-current status with no rows or current count. Amend continuity discovery to expand adjacent UTC days to a fixed point along actual 20-minute bridges, with a 62-day total cap. Exceeding the cap returns HTTP 409 `INDEX_CONTINUITY_LIMIT` and no current rows, count or empty claim. The selection token records every inspected day and S3/S4 selection seq. Full ruling and packet changes: `.agent/architect-S4-04-answers.md`.
Decision: `D-2026-10-15-s601-reopen`. For `reserve-trial-1`, a newer FindingRevision of the same canonical Finding must show earlier same-Site Actions with their pinned origin revisions, application/outcome states and exact links, even when live recomputation is `FOUNDATION_BASIS_STALE`. An earlier Action for the same battery asset and reserve field blocks a new acceptance while application is pending (including failed attempts awaiting retry) or applied with verification pending. Serve `PRIOR_ACTION_UNRESOLVED` and the blocking Action link separately from the current-basis reason; withhold the new Accept capability and enforce the guard atomically on POST across revision keys. Identical retries retain the original Action and accepted snapshot. S6-02 must define an explicit resolved/closed transition before a later trial can be allowed; a newer Finding revision or completed outcome alone does not authorize one. This amendment is required before S6-01a/S6-01b merge, with updated API fixture, UI at both widths, fresh affected reviews and the unchanged S6-01b owner walkthrough gate. Full ruling: `.agent/architect-S6-01-reopen-answers.md`.
Decision: `D-2026-10-15-p02-demonstration-label`. Resolve S5-01 phase-1 review M3 by declaring authored P02-power-late (KOBO-001, 2026-10-24, `s4-power-late-demo-cases-v1`) in the shared fixture-based demonstration label alongside P01. LR-01 owns this shared-label fix and Finding/Financials proof; S5-01 verifies the same label on eligible Overview money. Preserve 15.8125 USD exact / 15.82 USD displayed only when all existing eligibility, exact-head, currentness, source, quantity and price gates pass; unreadable or conflicting declarations fail closed. This bounded label is temporary presentation metadata. S4-05 replaces it with stored exact-revision provenance, under which unbound or mixed P01/P02 evidence has no current amount. Full ruling: `.agent/architect-S5-01-M3-answers.md`. Owner visual acceptance remains required for LR-01 and S5-01.

Decision: `D-2026-10-16-s6-verification`. Resolve `A-S6-verification` under `D-2026-10-14-action-lifecycle-and-policy-application`, `D-2026-10-15-s601-action-store-and-ui` and the S6-01 reopen hold recorded in `.agent/owner-autonomy-2026-10-15.md` item 9 and merged Action code. `D-2026-10-15-s601-reopen` governs the prior-Action hold. S6-02 freezes a versioned plan before later evidence, comparing separate closed 60-minute baseline and post-effective windows under old and new persisted Foundation revisions, with the same Site, asset, dispatch model, signal roles and predeclared comparability rule. Target is at least 25% less Candidate segment seconds, clipped to each half-open plan window from selected UTC-day `dispatch-3` revisions under S3 bracket/continuity rules; pin exact day revision IDs in the plan selection binding and outcome. Indeterminate or open-bound time is INCONCLUSIVE. Never add an S3 60-minute selection kind or use runtime, money or Finding count as the target. S6-02 adds public requested/delivered critical-load roles and five-minute Lab publication/readiness support; required coverage includes those roles, dispatch roles, cohort/clock basis, SOC and time-valid reserve. No required gap or material conflict may be hidden. Service unserved energy may not increase; later reserve-breach minutes must be zero and not increase; terminal SOC at a comparable horizon may not fall. A missing guardrail is unknown. On a complete pair, target and every guardrail pass yields `VERIFIED`; target or measured guardrail failure yields `INEFFECTIVE`, with `GUARDRAIL_FAIL` as a reason, not an outcome. Missing/ambiguous coverage, comparability, source provenance or unsettled reassessment yields `INCONCLUSIVE` or pending read state; a known failure remains visible without promoting a verdict while other required facts are unknown. Resolve source per window; a compatible pair has the same coherent source class and registered scenario/profile lineage, distinct run digests and intact links. Only `REGISTERED_SIMULATION` or `AUTHORED_DEMONSTRATION` public evidence may support a labelled demo verdict; mixed/unknown source fails closed, and no real-source positive verdict is claimed before real attestation. Late evidence or changed basis withdraws current finality while S3/S4 reassess; append a new immutable outcome when settled, retaining exact plan, assessment, Finding, accepted-envelope and source IDs and old outcomes. The evaluator job appends `RESOLVED` for a final current `VERIFIED` or `INEFFECTIVE`; only VERIFIED or target-miss-only INEFFECTIVE releases the prior-Action hold. Measured reserve/service `GUARDRAIL_FAIL` keeps the Site/asset/field trial blocked with `PRIOR_TRIAL_GUARDRAIL_FAILED` until a future rollback/review contract. `INCONCLUSIVE`, pending and failed application retain the hold. If reassessment invalidates closure, the evaluator job appends `RESOLUTION_WITHDRAWN` and restores the guard atomically with acceptance; a closure/late-reading overlap permanently blocks further acceptance with a typed reason until a future reviewer contract. A changed covering FoundationRevision for either window makes the result pending, then INCONCLUSIVE without a new comparable plan. S6-02 migrates the `action_event` CHECKs for both events and updates `lifecycle.reduce`/`service.is_unresolved` to read latest event under the trial lock; never rewrite history. The system computes metrics and verdict; a server-authorized, labelled SYSTEM demonstration command may request evaluation or plan freeze, never dictate the result or append resolution events. Two fixed-policy Lab runs and success, guardrail-fail and inconclusive variants travel through normal gateway/ingestion; no causal saving is asserted. Non-UI store/rule/read/fixture proof precedes Action Plan/Evidence/Verification and related Recommendation/Changes UI; S6-02 owner visual acceptance remains the owner's. Full implementable contract: `.agent/architect-A-S6-verification-answers.md`.

Decision: `D-2026-10-16-s602-questions`. For `reserve-trial-verification-1`, freeze comparable total feeder-demand and PV-available energy bands at +/-10% of baseline (zero baseline requires zero later) and initial SOC at +/-2 percentage points; compare exact values and fail closed on absent/ambiguous input. Both 60-minute UTC windows use twelve aligned, half-open five-minute slots. Accepted interval power must cover each slot exactly for duration-weighted energy; SOC needs accepted samples at each slot start and window end, with start-sample reserve checks and 300 sampled breach seconds per below-reserve slot. Missing boundaries, conflicting spans or an intra-slot reserve change are unknown. A pending plan replacement receives a new immutable ID and may reuse bounds only before the later run begins and before any later-window acceptance; otherwise it needs a new later window. The S6-02b interim guardrail-failure label is `Trial missed a safety or service limit`, with the measured failure shown; target-only failure is `Target not met`, and unknown required facts are `Could not conclude` with known failures retained. Verification defaults to latest current read state; explicit historical selectors persist with a Historical label and separate current state. This refines `D-2026-10-16-s6-verification`; packet changes and edge proofs are in `.agent/architect-S6-02-answers.md`. Owner plain-language status-copy review remains a single W1-conclusion task, and S6-02b visual acceptance remains the owner's.
Decision: `D-2026-10-16-s602a-cutoff`. For `reserve-trial-verification-1`, the first accepted public report for the same tenant/Site with a declared interval ending at or after `later_start`, from any role or asset, is the observable central proxy for the later run beginning; an unaccepted run/batch does not trip this cutoff because there is no central Lab run table. A replacement after that report needs a new later window and immutable plan ID; identical freeze retries keep their ID, and the cutoff check and replacement insert serialize with acceptance. Freeze requires every needed baseline UTC-day S3 selection to be CURRENT. Later selection binding requires `later_end` to have passed and every needed later day to be CURRENT. Evaluation returns REASSESSMENT_PENDING unless both pinned windows remain CURRENT on their pinned basis. Verification API timestamps use ISO 8601 UTC with `+00:00` throughout. Edge tests and full ruling: `.agent/architect-S6-02a-cutoff-answers.md`. This refines `D-2026-10-16-s602-questions`; S6-02b owner visual acceptance remains the owner checkpoint.

Decision: `D-2026-10-16-s502-parity`. Amend S5-02 question 1: assert parity between the S5-01 selected Finding and S4-04 first index row only for the same imported Site and half-open UTC day when the index is current, the Overview choice is freshly discovered under an open gate, comparable selected-day S3/S4 watermark fields agree, and both Finding and exact revision IDs match. The index's full continuity-day token and the Overview's accepted-source fingerprint have different scopes and are not equality keys. Otherwise display each read's basis and offer reload without a parity claim; persistent ID disagreement on settled comparable bases is a contract defect. Keep the reads separate and do not replace either choice. Required S5-02 packet and proof changes: `.agent/architect-S5-02-answers.md`.

Decision: `D-2026-10-16-a-action-index`. Resolve `A-action-index` for the W1 Site Work Actions list only. Select persisted Actions created in an authenticated tenant/Site half-open UTC window of at most 31 days. Stable identity is `(tenant_id,site_id,action_id)`; order by `created_at` descending then Action UUID ascending, and bind bounded cursors to the consistent row/event selection fence. Return exact origin FindingRevision, latest selected ActionEvent and canonical/exact-event links. A watermarked zero means no persisted Actions created in this scope, not no work of another kind; changed cursors, store failure and unauthorized scope cannot produce empty success. Backdated `occurred_at` does not change recorded event order or list membership. S6-03 adds the index read and Site UI as one reviewed slice with separate persisted positive and zero cases, leaving Incidents, Maintenance and global/cross-domain Work out of scope. Full contract: `.agent/architect-W1-remaining-answers.md`.

Decision: `D-2026-10-16-a-s7-health`. Resolve `A-S7-health` for W1 `health:2#a` and the Unknown-only `asset:3#a`. Site Health selects centrally received gateway diagnostics and registered cadence per authenticated Site; server-receipt contact freshness is separate from the age/trust of gateway-reported queue, clock, disk and source-contact facts. A newly received old diagnostic can show current gateway contact and old/Unknown facts. No gateway, no receipt, stale receipt, and stale projection are distinct watermarked states. Site Health makes no equipment-condition claim. The configured battery detail returns physical condition Unknown with named missing causal inputs; SOC or declared rating alone cannot yield degradation, remaining life, warranty or replacement exposure. Positive `asset:3#b` remains unmapped. `D-edge-health-cases` must persist central heartbeat, stale/no contact, delayed old fact, queue growth, clock offset and disk-pressure/recovery cases, with exact diagnostic IDs, server and reported times, reload, never-received and wrong-Site proofs. S7-01 uses a non-UI/read-and-fixture phase followed by UI and owner review. Full contract: `.agent/architect-W1-remaining-answers.md`; it narrows `D-2026-10-09-pre-s3-evidence-readiness-health` without promoting a panel.

Decision: `D-2026-10-16-s302-capability`. `I-capability-read` is the bounded implementation of `D-2026-10-09-pre-s3-evidence-readiness-health` for one exact selected S3 mini-grid dispatch assessment and accepted public role coverage. S3-02 binds Site, UTC day/window, assessment revision, run/model/cohort, knowledge cutoff, effective Foundation/bindings, accepted evidence IDs and source/analytic watermarks; `I-claim-limit-read` maps that assessment's versioned rule and limitations to a supported classification ceiling with missing/quality/conflict reasons. Pending, stale, failed or unassessed selection cannot produce a current positive claim; an old exact revision may be shown only as historical. Do not substitute configured capability, gateway contact or private Lab truth. The positive `evidence-analysis:2#b` requires rule-backed complete and missing fixtures, exact Evidence drill-down, a reviewed non-UI read phase and then UI/owner review; S2's `#a` explanation stays distinct. This decision does not resolve the implementation node or panel. Full contract: `.agent/architect-W1-remaining-answers.md`.

Decision: `D-2026-10-16-w1-remaining-questions`. Accept the five remaining W1 packet recommendations with bounded clarifications: S6-03 cursors fence all Actions and their events in the selected Site/creation window, including off-page rows, with maximum creation/event-recorded times and Action/event counts, and invalidate a later page when the fence changes; S7-01a uses a versioned two-clock health DTO and one repeatable-read registration/diagnostic snapshot without changing S2 gateway-health in place; S7-01b keys battery detail to the effective configured asset, shows `NOT_CONFIGURED` when absent, and refuses foreign or superseded asset IDs; S3-02a returns exact role-coverage spans and durations under one versioned rule without masking missing/conflicted subspans; S3-02b keeps S2 explanation separate and shows an explicit `UNASSESSED` S3 section until an assessment revision is selected. Implementation detail and review gates remain in the packets. Full answers: `.agent/architect-W1-remaining-q-answers.md`.

Decision: `D-2026-10-16-s405b-label`. For S4-05b, use interim operator labels `Prepared example data` for exact authored evidence, `Generated test data` for exact registered generated evidence, `Sources do not agree` for mixed evidence, and `Source unverified` for unknown evidence, each with adjacent plain source-limit text. Positive labels explicitly say the records are not readings from physical equipment; mixed/unknown never imply a physical source or zero cost. Keep exact source IDs and basis in deeper detail, with no vocabulary-scan exemption for source-state prose. A partly sealed registered Lab stage refuses the entire Commit with `SOURCE_PUBLICATION_REFUSED`; no sealed subset is released. Phase 2 also retires `demonstration_label.py` from Action reads and resolves each Action's pinned origin FindingRevision, failing closed to unknown when unresolved. Full ruling: `.agent/architect-S4-05b-answers.md`. Final visible wording and placement remain the owner's W1 copy checkpoint before S4-05b merge.

Decision: `D-2026-10-16-s602a-replay`. S6-02a may merge after fresh independent review with its complete, source-coherent but INCONCLUSIVE public Lab replay and labelled test-scoped positive evaluator proofs; the public complete-pass criterion remains a carried gap. S6-02b owns `reserve-aware-public-verification-replay` before its owner walkthrough: add a new mini-grid model/profile version whose declared generator-start policy reads effective reserve, preserve old versioned runs, and produce a two-run registered Lab replay through ordinary gateway/S2 acceptance that actually reaches VERIFIED under the existing frozen target, comparability bands, coverage and guardrails. Never synthesize readings, relax thresholds or substitute private truth. The walkthrough must show exact public lineage and reloadable current VERIFIED with simulated/no-savings and withdrawable-resolution limits, plus honestly labelled target-miss, guardrail-fail/hold, inconclusive, withdrawal and overlap cases. Keep `I-sim-verification-cases` and `D-verification-window` open, and withhold S6-02b owner acceptance and `I-S6-02` closure, until that positive public replay and case manifest pass review. Full ruling: `.agent/architect-S6-02a-replay-answers.md`.

Decision: `D-2026-10-16-s602a-holds`. Resolve S6-02a review F4 and F2 before S6-02a merge. A pending plan with no outcome, or a plan with a latest settled INCONCLUSIVE outcome, may be superseded for the same APPLIED Action with a new immutable plan ID; after the observable later-run cutoff the replacement needs a new later window strictly after the old one. The original Action remains unresolved and battery-scoped until a later current final outcome satisfies the existing release rule. No manual or SYSTEM INCONCLUSIVE withdrawal is added. A permanent `PRIOR_TRIAL_REASSESSMENT_OVERLAP` requires exact accepted public reading IDs that arrived after a specific RESOLVED closure, match its frozen bound roles/assets and half-open window, and materially changed its pinned S3 selection or direct verification-input basis; persist old/new lineage and the causal set. An unrelated or unbound late reading, or a Foundation/source/worker-only withdrawal, cannot create that permanent block. A later Action overlaps only if accepted after causal evidence arrived and before that closure was withdrawn. Indeterminate attribution retains the ordinary unresolved hold without inventing permanent overlap. Full ruling and proofs: `.agent/architect-S6-02a-holds-answers.md`.

Decision: `D-2026-10-16-s701-clock`. For the S7-01 v1 two-clock read, a measured absolute gateway clock offset of at most 5000 ms is WITHIN_TOLERANCE; above it is UNTRUSTED. Separately, allow `observed_at` at most 5000 ms after server `received_at` before reported facts become UNKNOWN with OBSERVED_AFTER_RECEIPT. These are separate named constants despite equal initial values, disclosed in the versioned read; changing either requires rule/DTO version review. Server-receipt contact freshness is independent. Keep `summary.status = NO_REGISTERED_SOURCE` for no enabled gateway; add `summary.reason = NO_ENABLED_GATEWAY` when registered gateways exist but all are disabled, or `NO_REGISTERED_GATEWAY` when none exist. Disabled gateways remain listed and excluded from contact summary counts. Null reported fact and source-contact ages when gateway clock trust is UNTRUSTED, and null any individual reported age while its timestamp is after `read_at`; preserve exact reported times and trust/reason, never display a negative age. `ALL_CURRENT` summarizes enabled gateway contact receipts only: S7-01b labels it Gateway contact, not Site or equipment health, and shows registration next to disabled-row receipt status. Full ruling: `.agent/architect-S7-01-clock-answers.md`. This refines `D-2026-10-16-a-s7-health` without promoting a health or asset-condition claim.

Decision: `D-2026-10-16-s602-closure`. For W1, accept S6-02b's genuine two-run registered Lab VERIFIED replay plus explicitly labelled, pinned-clock evaluator-builder non-pass cases as sufficient for `I-sim-verification-cases` and `D-verification-window`. This narrows their W1 acceptance targets and the Lab-only non-pass wording of `D-2026-10-16-s602a-replay`: target miss, measured guardrail fail/hold, inconclusive and late/withdrawn/overlap examples are test-scoped, not Lab runs or normal-ingestion proof. Do not claim otherwise. After F1 and F5 truthfulness fixes, F3 Evidence lineage completion, fresh fix review and actual S6-02b owner acceptance, close the two producer/data nodes, S6-02b nodes and `I-S6-02` in dependency order; the mapped W1 verification, Action Plan and Action Evidence portions may then be delivered with the limitation recorded. This decision alone resolves no node or panel and does not waive owner review. Full ruling: `.agent/architect-S6-02-closure-answers.md`.
