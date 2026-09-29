# T022B - Responsive Runs inventory and Draft setup

Status: planned
USER_REVIEW_REQUIRED: true

Map: A hardening; keeps the Lab entry path usable before the broader runtime.
Depends on: T022A and T023.
Next: T024.
Branch: task/T022B-run-store-libyaml
Sizing: one adapter compatibility change, runtime checks and measured UI proof.

## Outcome

On the demo machine at its actual store size, the Runs inventory becomes usable
within 1 s and a successful Draft setup becomes visible in run detail within
2 s. Opening a run, stepping it and refreshing its stage remain responsive.

This slice owns T022A criterion 2 under `D-2026-09-29-run-store-libyaml`.
T022A remains complete; its outstanding inventory acceptance is settled here
by evidence against those budgets. The entry-screen delay is already present,
so this work precedes T024's electrical runtime rather than enlarging it.

## Read for detail

- `.ai/DECISIONS.md`: `D-2026-09-29-run-store-libyaml` is the controlling
  decision; its loader, runtime requirement, placement and budgets are settled.
- `.agent/libyaml-architect-recommendation.md`: compatibility cases,
  measurement protocol, residual risks and deferred-work triggers.
- `tasks/completed/T022A-run-store-read-cost.md`: criterion 2 and its dated
  disposition; the earlier open-decision notes are historical.
- `.ai/MILESTONE_REVIEW_BACKLOG.md`: "Reading the run store still costs the
  whole store, twice" and its 2026-09-29 routing.
- Shared checks and protected seams: `tasks/README.md`, `.ai/ARCHITECTURE.md`.

## Deliver

Use explicit `yaml.load(text, Loader=CSafeLoader)` at the shared run-document
load point in `backend/assetops_backend/runs/adapters/yaml_run_documents.py`.
Inventory, direct/fallback reads and staged write readback use that same policy.
Keep UTF-8 decoding before YAML, `parse_run_document` and `safe_dump`.
Require the C extension on supported installation/CI targets, with a clear
diagnostic when absent and no silent pure-Python fallback.

## Acceptance criteria

1. Generated and currently readable stored runs yield equal domain records
   under the baseline and candidate readers. Compare the current owner corpus
   read-only (223 records at the Architect probe; record the actual count).
   Preserve frozen values, identities, payloads, statuses and domain refusals.
2. Declare and test the four known syntax/error differences at the real reader
   seam: literal tab after a colon and tab inside a flow sequence are accepted;
   literal `\uD800` and `\U00110000` escapes are refused as invalid YAML with
   `RunConfigurationInvalid`. These are adapter compatibility changes, not
   exact lexical equivalence. Resolve any newly found frozen-value, identity,
   domain-refusal or currently readable owner-document difference before acceptance.
3. Retain UTF-8 and size/count bounds, translated port errors, ordering,
   whole-inventory failure on an invalid document, identity/case/path checks,
   misfiled-record fallback, locking, both create identity scans and atomic
   publication. Unknown IDs still raise `RunNotFound`; corrupt unrelated files
   do not break a canonical single-run hit. Failed writes leave no partial record.
4. Mechanism checks establish one document parse for a canonical hit, N for
   inventory and 2N + 1 reads for successful creation into N valid records
   (both identity scans and staged readback). This changes the per-record cost;
   inventory and creation retain O(N) work.
5. Verify C-extension availability on supported installation/CI targets and
   exercise the missing-extension diagnostic. Record OS, Python, PyYAML and
   libyaml versions; availability on one workstation alone is insufficient.
6. Compare baseline/candidate inventory and successful Draft setup through
   composed `host/lab_app.py` at the actual store size, then at 500 and 2,000
   representative records in isolated stores. Record starting/ending counts,
   total bytes and representative layouts. Publish the demonstrated size/byte
   envelope and where retained full-store reads cease to meet the budgets;
   the budgets are not a promise that all 2,000 records fit them.
7. Browser evidence measures navigation to usable Runs inventory and successful
   setup submission to populated run detail against the 1 s / 2 s budgets on
   the demo machine at actual size. Report repeated quiet-run median and range,
   all samples, and a browser/dev-server-load sample separately. An adapter
   speedup alone does not establish these interaction budgets.
8. Regress run detail, execution read, Lab step and post-step stage refresh
   end to end. Run/stage contents and the Lab/product boundary remain unchanged.
   Preserve owner data; creation, execution and performance fixtures use
   isolated stores, with no owner-record rewrite, migration or deletion.

## Proof

Keep a small reproducible measurement harness with the implementation evidence,
preferably in `tools/`, runnable from another checkout without owner data.
Interleave baseline/candidate samples, distinguish first and warm reads and
record machine/load conditions, exact commands, fixtures and timing boundaries.
Historical adapter ratios are context, not HTTP/browser results or new budgets.

At the real reader seam, cover the recommendation's valid controls, four
differences and matching negative cases: malformed YAML, invalid UTF-8,
oversize documents, non-mapping roots, unsafe/unknown tags and invalid escapes.
Include representative stored layouts, scalar types, duplicate/merge/alias
behavior, wrong domain values and generated write/readback. Compare domain
records and translated errors, not low-level YAML exception wording. Preserve
inherited unknown-field/duplicate-key policy; finite probes do not prove general
parser equivalence. Retain corpus comparison evidence without committing data.

Run both repository guards and backend, host, simulator and frontend regression
checks from `tasks/README.md`. Include the browser interaction evidence above;
layout evidence is additionally required if implementation changes layout.

## Scope limits and follow-up triggers

Only the run-store YAML load policy changes. Site/scenario readers, private
execution artifacts and source-stage JSON retain their readers. This adapter
change requires no stored-format migration or execution-contract version move.

Removing create's scans, changing fallback, caches, indexes, pagination and
storage redesign remain deferred. A setup-budget miss triggers profiling of
the composed path; an inventory-budget breach or reaching the measured size/
byte envelope triggers the smallest evidenced follow-up before T027, not an
automatic scope expansion or a raised 2,000-document guard.

T026 owns measurement of whole-stage rewrite/full-series republication with its
larger allowlist; investigate earlier if T024/T025 step latency regresses.
Recheck inventory, setup and step before T027 with the expanded runtime/evidence,
including T024's larger frozen inputs once available. Isolate evidence writes;
tooling retention follows only when growth consumes the measured envelope.

## Review

An independent Reviewer checks the compatibility seam, runtime requirement,
storage guarantees and reproducibility of the composed/browser evidence.
The owner opens Runs and creates a Draft on the demo machine and judges usability.
Report T022A criterion 2 explicitly against the budgets: if they are missed,
record partial improvement, leave that criterion open and profile the remaining
cost before proposing a bounded successor. A parser speedup alone is not completion.
Review outcome: pending.
