# T010A - Site Foundation Fetch Seam Integration Test

Status: complete
USER_REVIEW_REQUIRED: false

Intended branch: `task/T010A-site-foundation-fetch-seam-integration-test`

## Feature

Site Foundation And Configuration-Only Site, frontend/backend fetch seam before
canonical fidelity expands the surfaces built on it.

## UI-Verifiable Screen Behavior

This slice renders no new UI. It protects the screen behavior already visible
where the product reads a Site, reads a template, or creates one: Sites index,
Site Details, Foundation, Site Templates, and the create-from-template flow.

If this seam drifts, those screens can show an empty list for an unreadable
store, a not-found state for a malformed response, a partially rendered Site, a
template shaped like a Site, or a generic failure instead of the backend's
refusal copy. The check for this test-only slice is that the real frontend
clients accept representative backend responses and reject mismatches before
T010 adds more visual fidelity on top of the same assumptions.

## Why This Is Next

T006 through T009 left the same open risk: backend API tests and UI tests with
injected fakes do not prove that the real frontend fetch clients understand the
backend's response bodies, status codes, and error envelopes. T008 added one
response-level frontend test for `siteDirectoryClient`, but it still uses
human-written bodies rather than responses emitted by the backend.

T010 would otherwise combine mockup-quality UI work with a new test mechanism.
The split keeps T010 visual and closes the shared contract before the Lab's
template and create surfaces accumulate more UI over an unverified seam.

## Acceptance Criteria

- Mechanism: add a checked-in shared fixture at
  `contract-fixtures/site-foundation-fetch-seam.json`. Backend tests generate
  the fixture body from real FastAPI responses built through `create_app` and
  compare it byte-for-byte or structurally to the checked-in file. Frontend
  response-level tests load that same fixture and assert the real clients
  return the expected named states.
- Anti-rot guard: a normal backend test run fails when the backend-generated
  responses differ from the checked-in fixture. Regeneration is explicit, for
  example through an opt-in environment variable or script named by the test
  failure; updating the fixture without the backend generator agreeing is not a
  passing state.
- Dependency direction: neither side imports the other. Backend code/tests do
  not import frontend modules, frontend code/tests do not import backend
  modules, and the fixture is the third artifact both test suites read.
  `tools/checks/dependency-direction.ps1` remains unchanged in strength.
- Site list shape: `GET /api/sites`, consumed by
  `createSiteDirectoryClient().listSites()`, is covered for a loaded non-empty
  list and for first-run empty state. The non-empty response returns
  `{ status: "loaded", sites: [...] }`; the empty response returns
  `{ status: "loaded", sites: [] }`, never `unavailable`.
- Site detail shape: `GET /api/sites/{site_id}`, consumed by
  `createSiteDirectoryClient().getSite(siteId)`, is covered for a loaded Site
  with Foundation `version`, `valid_from`, `summary`, and `components`, including
  both a rated component and a component whose rating is `null`.
- Site not-found and store/error envelopes: `GET /api/sites/{site_id}`,
  consumed by `createSiteDirectoryClient().getSite(siteId)`, is covered for
  backend 404 as `{ status: "not_found" }` and backend 503 or malformed body as
  `{ status: "unavailable" }`. The test must preserve the distinction between
  "the Site is not configured" and "the store could not be read".
- Template list shape: `GET /api/simulator-lab/site-templates`, consumed by
  `createSiteTemplateCatalogClient(basePath).listTemplates()`, is covered for a
  loaded list and for an empty catalog as `{ status: "loaded", templates: [] }`.
  A backend 503 maps to `{ status: "unavailable" }`, not an empty catalog.
- Template detail shape: `GET /api/simulator-lab/site-templates/{template_id}`,
  consumed by
  `createSiteTemplateCatalogClient(basePath).getTemplate(templateId)`, is
  covered for loaded Foundation content, backend 404 as `{ status: "not_found" }`,
  and backend 503 or malformed body as `{ status: "unavailable" }`.
- Create success shape: `POST /api/simulator-lab/sites`, consumed by
  `createSiteCreationClient(basePath).createSite(input)`, is covered for backend
  201 as `{ status: "created", site }`, where `site` is the Site summary shape
  the operator Sites index also accepts.
- Create validation failure shape: `POST /api/simulator-lab/sites`, consumed by
  `createSiteCreationClient(basePath).createSite(input)`, is covered for backend
  422 with `detail.message` as `{ status: "refused", message }`. At least one
  409 duplicate-identity refusal is covered the same way, because T006 settled
  that conflict copy as renderable product copy.
- Create not-found/error envelopes: `POST /api/simulator-lab/sites`, consumed by
  `createSiteCreationClient(basePath).createSite(input)`, is covered for
  unknown template 404 with `detail.message` as `{ status: "refused", message }`
  and store/catalog 503 with `detail.message` as `{ status: "refused", message }`.
  A malformed refusal body maps to `{ status: "unavailable" }`.
- Gate-disabled seam: with `simulator_lab.enabled=false`, the gated endpoints
  `/api/simulator-lab/status`, `/api/simulator-lab/site-templates`,
  `/api/simulator-lab/site-templates/{template_id}`, and
  `/api/simulator-lab/sites` are unserved. The fixture captures these 404s, and
  frontend client tests assert that the template list client returns
  `unavailable`, the template detail client returns `not_found`, and the create
  client returns `unavailable` for the unserved routes. The ungated
  `/api/sites` and `/api/sites/{site_id}` responses remain available and
  identical in both gate states.
- Simulator Lab status: `GET /api/simulator-lab/status` has no Site Foundation
  frontend client method. It is included as the backend gate sentinel only:
  served with the enabled status body when the gate is open and unserved with
  404 when the gate is closed.

## Required Product And Domain Semantics

- A Site created from the Lab is a normal product Site. Its read responses are
  operator responses under `/api/sites`, not Lab-owned objects.
- A template is not a Site. Template responses must not acquire `site_id`,
  lifecycle status, location, timezone, source mode, evidence, or source health.
- Empty list and unavailable store are different facts. The seam test must keep
  the clients from rendering an empty state when the backend says the store or
  catalog could not be read.
- Refusal copy belongs to the backend response and remains renderable by the
  frontend create client. The frontend must not restate validation rules to
  decide whether a refusal is meaningful.
- The gate covers Lab surfaces and execution, not Site objects or stores. Lab
  endpoints are absent when disabled; operator Site endpoints remain served.

## Protected Seams

- External and data contracts stay strict at boundaries: response bodies are
  accepted only when they match the client read model, otherwise they become a
  named unavailable state.
- Dependency direction is deliberate and testable: a shared fixture is the only
  crossing. No backend-to-frontend or frontend-to-backend import is introduced.
- Simulator feature gate: gated API paths are unserved with the flag off, while
  operator Site reads remain available.
- Template versus Site identity: `template_id` never becomes `site_id`, and the
  template client never accepts a Site-shaped payload as a template.
- Product evidence remains absent: no response fixture may add evidence,
  source-health, analytics, replay, findings, or simulator-truth fields.

## Focused Tests And Checks

- Backend fixture-generation test that exercises the six endpoints through
  `create_app`, in enabled and disabled gate states where relevant, and fails
  when the checked-in fixture is stale.
- Frontend response-level tests for `siteDirectoryClient.ts`,
  `siteTemplateCatalogClient.ts`, and `siteCreationClient.ts` using the shared
  fixture as the response source.
- Tests include successful responses, empty states, validation refusals,
  not-found responses, store/catalog unavailable responses, malformed bodies,
  and gate-disabled unserved routes as named above.
- Existing UI tests remain focused on screens with injected clients; they are
  not converted into broad browser end-to-end tests for this slice.
- Run `tools/check-architecture.ps1`, especially the dependency-direction and
  simulator-gate checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing relevant backend and frontend tests stay green.

## Scope Limits

- Do not change product behavior, routes, response shapes, or user-visible copy
  except where an existing mismatch is exposed and must be fixed to preserve the
  settled contract.
- Do not add a live-backend frontend test, a browser end-to-end test, or a
  shared generated schema. Those are larger mechanisms than this slice needs.
- Do not import backend modules from frontend tests or frontend modules from
  backend tests.
- Do not add a Site edit, update, rename, duplicate, delete, publish, promote,
  template authoring, upload, clone, or import capability.
- Do not move Lab APIs out from behind `simulator_lab.enabled`.
- Do not weaken existing route inventory, simulator-gate, dependency-direction,
  substrate, or fabricated-value guards.
- Do not create T010B or plan any additional task from this split.

## User Review

User review is not required for this slice. It adds no capability, no product
language, and no UI surface. It only makes the existing frontend/backend
contract testable before T010 changes presentation on top of it.

## Review Outcome

Reviewer verdict: accept after one medium finding was fixed on the branch. No
other findings, no blocking open questions. The review was independent: Codex
reviewed work Claude authored, per the role separation in
`.ai/PROJECT_RULES.md`.

Finding: the frontend tests verified the response half of the seam and not the
request half. The fixture records the method, path and body of every captured
request, but the fake `fetch` accepted only `fetch`'s first argument, so
everything about a request except its URL was invisible. The create tests would
have passed while the client stopped sending `POST`, sent an empty body, sent
the wrong site identity, or dropped its `Content-Type` - and the real backend
would not have answered 201 or any of those refusals for such a request. A seam
closed in one direction is not closed.

Fixed on the branch in `2b8db05`. `serve()` records `init` as well as `input`;
`expectRequestMatchedCapture` asserts method, path, body and content type
against the same fixture case the response comes from, so the request half is
checked against the captured contract rather than against literals written in
the test; and `capturedCreateInput` feeds each create call the body the backend
actually received for that case, so a create test cannot drift into asserting a
response the backend would never have sent for the request being made. Fourteen
cases now assert their request, across all three clients and both gate states.

The fix was proven load-bearing, and the first three of these passed silently
before it: sending `GET` instead of `POST` fails six tests, an empty body fails
six, a missing content type fails six, and a wrong Site detail path fails three.

Judgement calls the reviewer examined without objection: the two shared test
timeout changes raise tolerance for a known slow environment rather than
weakening assertions; the seven backend distinction guards cover the product
distinctions the task names and materially narrow the wrong-but-consistent
regeneration failure mode without closing it; the two contract facts the packet
reports are real in the fixture and are correctly captured rather than
"fixed", because changing a response envelope is product scope outside a
test-only slice; and the diff contains no product-code route, response-shape, or
copy change.

Reviewer checks: architecture guard passed, agent workflow guard passed, the
seam test's own 8 tests passed, frontend `tsc --noEmit` clean. The reviewer
independently verified the anti-rot guard rather than taking it on trust, by
changing a captured status in the fixture, watching the backend test fail, and
restoring it.

The reviewer could **not** verify three of the packet's claims, and said so
plainly rather than inferring them. The full backend suite failed in that
environment on pytest temp-directory permissions - `PermissionError: [WinError
5]` on `pytest-of-assef`, 89 errors alongside 215 passes - so `304 passed` was
not confirmed there. The frontend suite and the production build could not run
at all, because Vite failed while loading its config. That is the second
consecutive review unable to run the frontend suite for the same reason, so the
frontend numbers in both T009 and T010A rest on the Implementer's runs alone.
Worth fixing before a third.

Checks re-run in the implementing session after the fix: architecture guard
passed, agent workflow guard passed, backend `pytest -q` 304 passed, frontend
`vitest run` 378 passed across 15 files, `tsc --noEmit` clean, `npm run build`
clean with the bundle unchanged, which confirms the fixture is not shipped.

Also settled here, beyond the task: the frontend flakiness that T007, T008 and
T009 each recorded and none diagnosed. It had two causes, and the second is why
it stayed unexplained - Vitest's 5s per-test timeout was the visible half, while
Testing Library's separate 1s `waitFor` timeout throws "Unable to find an
element", which reads as a real assertion failure rather than a slow machine.
Both raised. The suite then passed repeatedly at full concurrency with the
machine under heavy load.

User review is not required for this slice, as the User Review section above
states. It adds no capability, no product language, and no UI.

The full review packet is at `.agent/T010A-review-packet.md`, the reviewer's
findings at `.agent/T010A-review-findings.md`, and the handoffs beside them. All
are local-only.
