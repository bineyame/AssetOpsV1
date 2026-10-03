# T027 phase 1 - independent review (Claude)

Reviewer: Claude, as a fresh `assetops-reviewer` instance. Under
`.ai/ROLE_CONFIG.md` the Reviewer is Claude until the Codex reset at 2026-10-03
21:23; Codex reviews this phase retrospectively after that. This reviewer did
not author any part of the slice.

Scope: diff `f7325c3..aa294c2` on `task/T027-commit-ingestion-and-site-overview`
(later commits only add coordinator and owner records). The task's acceptance
criteria were the standard. The packet was treated as a set of claims to check.

## Verdict

**Accept with one fix on the branch (B1).** Phase 1 does what the task asks.
Commit seals once, release goes through the one ingest path, recovery and
idempotence hold under every crash point I tried, Site > Evidence is part A
only, and the tab rule and AC23 are in place. I ran the AC15 proof myself (see
B1), and it holds. Nothing in the slice needs redesign. The one blocking item
is getting that proof into the repository so AC15 stops being "partial".

## Blocking

### B1 (Medium, acceptance gap): AC15 is met but has no committed proof

- Where: `host/tests/test_t027_commit_ingestion.py:194-225`; packet row AC15 and
  deviation 1.
- Problem: AC15 says to repeat reconstruction "with no private simulator
  artifacts or installed runtime composition. No product dependency on
  simulator/host is required." The only rebuild test runs inside the host test
  process. By then the kernel, the gateway and the host modules are already
  imported, so the test cannot show that the rebuild needs none of them. The
  static dependency guard covers imports. It does not cover runtime
  composition.
- Reviewer's own proof (not on the branch): I ran a fresh process from a
  directory outside the repo, with a `sys.meta_path` finder that raised on any
  import of `assetops_simulator`, `host`, `lab_execution`, `source_stages`,
  `kobo`, `lab_app` or `fixtures`. It used `create_app(gate closed)`,
  `build_site_repository()` and an empty `JsonEvidenceStore`, and it ingested
  the owner's real hands-on artifact (`var/commits/run-2626f28e...json`, 329
  envelopes, copied to scratch first). The results:
  - the release was COMPLETED with 329 accepted and 0 rejected;
  - no blocked module was found in `sys.modules`;
  - `/api/simulator-lab/runs` returned 404;
  - with receipt and audit times excluded, the overview, the record list, all
    329 record details and the rejections all equalled the working store's
    payloads.

  So the implementation meets AC15. Only the repeatable proof is missing.
- Failure scenario: a later slice adds a transitive import, for example a
  contracts module that imports `source_stage`, or a lazy simulator import
  inside the read model. The static guard misses it, and nothing fails until
  the internal demo runs with the Lab removed.
- Fix (smallest): add a backend test that starts
  `subprocess.run([sys.executable, "-I", probe])`, with `cwd` outside the repo
  and the blocking finder above. The probe ingests one artifact text written by
  the test (the backend helpers' `sealed(...)` is enough, so no simulator is
  needed to produce it). It then prints the read-model JSON and the list of
  leaked modules. The parent asserts `leaked == []` and equality with the same
  payloads built in process. Phase 2 can extend the same probe to the Overview
  read model. Then update AC15 in the packet to "met for Evidence".

## Non-blocking

### N1 (Medium): the configuration registry is the only copy of a historic Foundation basis

- Where: `backend/assetops_backend/evidence/service.py:215-255`;
  `evidence/adapters/json_evidence_store.py:13-18, 204-213`.
- Problem: the basis for Foundation vN is a snapshot of the Site's current
  Foundation, taken at the first ingest that names vN. The Site repository
  keeps no version history, so after a Foundation edit the registry is the only
  record of how vN read. `clear_derived()` correctly keeps it, and that matches
  AC14's "referenced immutable configuration". However, the registry sits under
  `var/evidence/`, next to the derived documents.
- Reviewer probe: I ingested an artifact, edited the Site to v2, and rebuilt.
  With the registry kept the rebuild was COMPLETED. Into a fully empty store
  the rebuild was REFUSED with `CONFIGURATION_UNRESOLVED`. Neither branch test
  covers rebuild after an edit: the host rebuild test passes only because the
  Site's current Foundation still equals the referenced version.
- Failure scenario: someone "rebuilds from scratch" by deleting `var/evidence`
  after a Foundation change, and historic evidence can no longer be re-ingested.
- Fix: add a test of rebuild after a Foundation edit using `clear_derived()`,
  and say in the store docstring that `registry/` is configuration, not derived
  state. Durable Foundation version history belongs in the backlog. It should
  be in place before configuration editing ships (T034).

### N2 (Low): resuming a release requires the live stage

- Where: `backend/assetops_backend/simulator_lab_api.py:2697-2705`.
- Problem: when an artifact is already filed, the POST still reads the stage. A
  missing stage gives `integrity_digest None`, which is refused as
  `COMMIT_STAGE_CHANGED` with the message "differs from the stage as it is
  now". The sealed artifact is self-verifying and is all a release needs.
- Failure scenario: an interrupted release cannot be resumed after the stage
  store is cleaned, and the refusal misdescribes why.
- Fix: when an artifact exists, refuse only when a stage is present and its
  digest differs, and otherwise release the artifact. At minimum, give an
  absent stage its own message.

### N3 (Low): a REFUSED release has no retry control

- Where: `frontend/src/shell/RunCommitPanel.tsx:157`.
- Problem: "Resume release" appears only for `null` or `IN_PROGRESS`. The
  backend allows a retry after refusal (`service.py:387`), but the panel offers
  no way to do it.
- Fix: offer the same POST for REFUSED, with the refusal shown beside it, or
  say that nothing will change until its cause is fixed.

### N4 (Low): a batch id is checked per Site but looked up globally

- Where: `backend/assetops_backend/evidence/ports.py:63-69`; `service.py:357`.
- Problem: `BATCH_ID_CONFLICT` is checked only within the batch's own Site, but
  `GET /api/ingestion/batches/{id}` returns the first match across all Sites.
  Lab batch ids are artifact digests, so this cannot happen in the Lab. It can
  happen for ordinary sources using the ungated POST.
- Fix: refuse a batch id already used at another Site, or scope the read by
  Site. Backlog is acceptable.

### N5 (Low): `BATCH_ID_CONFLICT` appends a rejection on every retry

- Where: `service.py:360-374`.
- Problem: each refused re-post adds another `Rejection` with `index=None`.
  These count in the `rejection_count` that Site > Evidence shows beside
  per-record rejections.
- Fix: deduplicate by (batch_id, digest), or report batch-level refusals
  separately. Backlog.

### N6 (Low): the evidence store is fine for the demo; carry its limits to the backlog

- Where: `json_evidence_store.py`; `service.py:173`.
- Assessment: one document per Site, rewritten whole per 64-record chunk with
  `.partial` and `os.replace`, is correct, and it matches the task's "simple and
  correct" limit. Measured: the owner's 329-record Site is a 571 KB document
  that loads in about 10 ms, and every read parses all of it. Writes grow
  quadratically within a batch.
- The real limit is that both locks are per process. If the product app and
  `host/lab_app` both run over the same `var/evidence`, one can lose the
  other's updates (read-modify-write).
- Recommendation: do not fix this now. Carry it to
  `.ai/MILESTONE_REVIEW_BACKLOG.md` with two parts: single-writer-process
  assumption, and whole-document rewrite and read cost. Pick it up before
  multi-Site live ingestion or T026A's outage and recovery volumes.

### N7 (Low): navigation-truthfulness does not check the capability filter, `Operator home` or the `/` redirect

- Where: `tools/checks/navigation-truthfulness.ps1`.
- Mutation result: replacing `CANONICAL_OPERATOR_SITE_TABS.filter((tab) =>
  tab.capability)` with the unfiltered inventory, which renders all eight tabs,
  passes the check. The frontend tests do pin this:
  `operatorSiteTabs.test.tsx:53` (`RENDERED_TABS`), `:353` (`/` redirect), and
  `operatorRouteFrames.test.tsx:169-189` (rail is `["Sites"]`).
- AC21 asks only that the check is "updated without loosening". It has not been
  loosened, so this is not an acceptance gap.
- Optional: add a rule that the rendered row comes from the capability filter.

### N8 (Nit): duplicate comment and a stale citation

- `navigation-truthfulness.ps1:257-259` says "v6.9 line 2117 lists five" twice.
- Packet AC23 row (line 74) cites `OperatorShellFrame.test.tsx`, which this
  slice deleted. The redirect is proven by `operatorSiteTabs.test.tsx:353`.

### N9 (Phase 2 note): keep one list of Overview signals

- Where: `backend/assetops_backend/evidence/read_model.py:51-62`
  (`NEEDED_SIGNALS`).
- AC22's presentation profile will also be substrate data keyed by `site_type`.
  Phase 2 should either derive the needed signals from the profile's cards or
  pin the two lists equal in a test, so that coverage and cards cannot drift
  apart.

## Acceptance criteria, as checked against the code and tests

| AC | Reviewer finding |
| --- | --- |
| 1 | Met. `_seal` refuses unless `release_eligible`, stage and digest are all present. `parse_artifact_text` recomputes the manifest and integrity. The store files once with an exclusive create, a round-trip check and `os.replace`. |
| 2 | Met. The artifact id comes from (run, stage digest), and a filed artifact is reused and never rewritten. Resume works (my crash probe below). Caveat: N2. |
| 3 | Met. The batch document is parsed with exact keys. Envelopes are parsed one at a time, and mapping, signal, unit, Site, source, gateway and time-before-basis checks each give an inspectable `Rejection`. Whole-batch refusals have kinds. |
| 4 | Met. The HTTP POST and the Commit both call `IngestionService.ingest`. `source_mode` is provenance on the record and is checked against the Site. |
| 5 | Met. `received_at` comes from ingestion's clock. The host test and the layout run show three distinct timestamps. |
| 6 | Met. Probed: the same records under a new batch id give 0 accepted, 2 duplicates and unchanged records. A reused id with other content gives `BATCH_ID_CONFLICT`, including while the original is IN_PROGRESS, and the original's progress is preserved. |
| 7 | Met. Probed: crashes after k = 0..6 envelopes with chunk size 3 always leave watermark = persisted records = floor(k/3)*3, status IN_PROGRESS. Resume finishes with the same message ids as a clean run, and a second resume returns identical progress. |
| 8 | Met. The read model reads only the evidence store and the Site. The guard is non-vacuous (below). |
| 9 | Met. Distinct ids at the same (device, signal, source_time) are all kept and counted as `overlapping`. Nothing is summed. |
| 10 (Evidence) | Met. Needed signals with no accepted record are `NOT_REPORTED` with no value, rendered as "Coverage gap ... no value here". Nothing is carried forward. |
| 12 (Evidence) | Met. The inspector shows every listed field and three labelled timestamps, and only `signal=`/`source=`/`record=` in the query string change. |
| 13, 19 (Evidence) | Met. Evidence routes are mounted in both gate states, the commit store is never built with the gate closed, and the Lab routes return 404. My subprocess probe confirmed 404 for `/api/simulator-lab/runs`. |
| 14 (Evidence) | Met as worded, since the registry is kept. See N1 for rebuild after an edit. |
| 15 (Evidence) | Met in behaviour (reviewer probe); proof not committed. B1. |
| 16 | Met. A private key anywhere refuses the batch with `UNKNOWN_FIELD`, and an envelope given as an object refuses the batch. Dependency guards pass. |
| 17 | Met. The registered basis is never rewritten, and the read model shows the accepted basis beside the current Foundation. |
| 18 | Met. Commit and release are two facts. "Accepted all" appears only when accepted equals total. The link is built from ingestion's accepted window and lands on Site > Evidence. |
| 20 | Met. Sources, coverage, basis and rejections are shown, with no claim readiness, capability or ceiling wording outside a code comment. |
| 21 | Met. One canonical inventory filtered by capability renders Overview, Foundation and Evidence. Foundation renders Definition, Topology and Controls. No "labelled in place" remains except in comments that say it is not used. The Readiness and `Changes` bans hold (mutation-proven). |
| 23 | Met. `Operator home` and `OperatorShellFrame` are removed, `/` uses `<Navigate replace>` to `/sites`, and the rail is `["Sites"]`. The one remaining "Operator home" string is the T004 historical baseline in `siteFoundationRoute.test.tsx:111`, which is intended. |

## Judgement on the Implementer's choices where the plan was silent

- **Unknown Site refused and not stored:** accept. A rejection needs a Site to be
  filed under, and the 409 response is the inspectable answer. A global intake
  log can wait for live sources.
- **`BATCH_ID_CONFLICT`:** accept, with N4 and N5 for the backlog.
- **Retry after refusal:** accept. A refused batch wrote no records, so reusing
  the id is safe. The UI does not expose it (N3).
- **Needed signals keyed by `site_type`:** accept. It names signals only and
  holds no card state. See N9.
- **`?batch=` highlights rather than filters:** accept. `from` and `to` already
  narrow the view to the release's window, and the highlight claims nothing
  more.
- **One POST for commit and release, resuming IN_PROGRESS:** accept. The broad
  `except` reports the error and the persisted progress rather than a 500,
  which is honest. N2 is the one refinement.
- **Commit shown disabled with its blockers, not hidden:** accept. The
  rendered-tabs rule governs navigation destinations: tabs and subtabs. Commit
  is a control for a capability this build has, and it is ineligible for this
  particular stage. "Rendered, disabled, carrying the reason" is the
  third-affordance state the codebase already uses (`GatedSiteAction`). The
  reason is visible and linked with `aria-describedby`. Hiding it would suggest
  that the Lab cannot commit at all.

## Commit hygiene and the working tree

- **`f0b30ee` / `24b38ee`:** no squash is needed. `24b38ee` is a 2-line type
  field next to the commit it fixes, and the branch merges with a merge commit,
  as `main` does. I did not rebuild `f0b30ee` alone to confirm the type error.
- **`var/`:** no cleanup is required for merge, because `var/` is gitignored.
  Keep `run-2626f28e...` with its commit and its `SITET26` evidence: it is the
  owner's hands-on record and a useful phase 2 rebuild input. The four Drafts
  written at 2026-10-02 23:5x by the early dev-server layout runs are clutter in
  the Lab runs inventory. The owner may remove them; I deleted nothing.

## Checks run by this reviewer

All checks ran serially on `51948dd`, whose code is the same as `aa294c2`.

| Check | Result |
| --- | --- |
| `.venv\Scripts\python.exe -m pytest backend/tests -q` | 1412 passed |
| `pytest host/tests -q` | 602 passed |
| `pytest tests -q` from `simulator/` | 244 passed |
| `pytest simulator/tests` from the repo root | Collection error in `simulator/tests/test_t026_schema2.py:42` (`No module named 'tests'`). This predates T027 and the file is not in the diff. |
| `npx.cmd tsc --noEmit` | Clean, exit 0 |
| `npm.cmd test` | 42 files, 1055 tests passed. The brief expected the sandbox to block this; it ran. |
| `npm.cmd run build` | OK: 102 modules, 475 KB JS |
| `tools/check-architecture.ps1` | "Architecture check passed." |
| `tools/check-agent-workflow.ps1` | "Agent workflow check passed." |

Guard mutations, made in a `git archive` copy only:
- `evidence/service.py` importing `assetops_backend.runs.models`: caught.
- `evidence_api.py` doing `from assetops_contracts import lab_projection`:
  caught.
- `read_model.py` importing `assetops_simulator`: caught twice, by the existing
  product rule and by the new evidence rule.
- A `Readiness` Foundation subtab: caught.
- A `Changes` subtab: caught.
- A `labelled_in_place` tab kind: caught.
- An unfiltered tab inventory: not caught (N7).

Reviewer probes, in scratch only and not committed:
- Four pytest probes passed: crash at every point then resume; same records
  under a new batch id; a conflicting batch id while IN_PROGRESS; rebuild after
  a Foundation edit with and without the registry.
- One isolated-subprocess rebuild of the owner's artifact (B1).

Layout evidence: spot-checked, not rerun. Every T027 claim passes: Commit
panel, link landing, Evidence populated at 1280, 1000 and 640, inspector at
1280 and 640, and empty MG-006. The four failures are disclosed and predate
T027: three "blocked table" claims (MG-006 is READY) and the T025e p95 delta
budget. The gate-closed pass was HTTP only, with no browser pass, as the packet
says.

## Not verified

- I did not rerun the full layout evidence.
- There was no browser pass with the gate closed. Gate-closed behaviour rests on
  backend and frontend tests and my subprocess probe.

## Residual risk not named in the packet

- The configuration registry is the only copy of a historic basis (N1).
- Cross-process lost updates on `var/evidence` (N6).
- Global batch-id lookup (N4).

## Owner question

1. Should the configuration registry (N1) move out of `var/evidence/` into a
   durable configuration-history store before T034 makes Foundation editable,
   or is a backlog entry enough for now?
