# T006 - Read-Only Site Configuration

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T006-read-only-site-configuration`

## Feature

Site Foundation And Configuration-Only Site.

## UI-Verifiable Screen Behavior

Site Configuration is addressed by `site_id` and shows the Foundation of that
Site, read-only: Foundation version, validity interval, timezone, lifecycle
status, source mode as provenance, integration readiness, configuration origin,
and the configured components, devices, and signal mappings as plain read-only
content.

The screen states that configuration is fixed at creation in M1. It offers no
edit, Save, Publish, rename, delete, approve, diff, history, or rollback
control, enabled or disabled, and it shows no operational values: no telemetry,
charts, source health, analytics, Replay, or Findings.

## Why This Is Next

This completes the read half of Causal Sequencing step 3a. T005 made Site
identity real and resolvable through the port; this slice makes Foundation
content visible, which is what "configure one mini-grid site" means to a user
and what later slices bind to.

It is also the point where the product must say what it does and does not
promise about configuration. The 2026-09-13 decisions superseded the blanket
deferral of authoring, so the previous read-only wording is now wrong: it can no
longer imply that configuration is merely file-backed and uneditable, because
users will soon create Sites. Honest unavailability, not stale unavailability.

That copy, and the Site/Foundation semantics behind it, are exactly what the
first user-review checkpoint exists to settle. This slice carries the checkpoint
deferred from T005.

## Acceptance Criteria

- Site Configuration is addressed by `site_id` and replaces the parameterless
  `/site-configuration` placeholder route. It is reachable from Site Details.
- An unknown `site_id` renders an explicit not-found state and no fabricated
  configuration.
- The screen renders the Foundation version and the Foundation validity interval
  exactly as declared in the document, with no inferred, defaulted, or
  fabricated dates.
- Lifecycle status, `source.mode`, integration readiness, and configuration
  origin render as four separate, independently labelled facts. None is
  presented as a proxy for another, and none is presented as source health,
  evidence state, or asset condition.
- Configuration origin renders from the Site record, not from a literal. A test
  drives the screen with a fake repository returning a `USER`-origin record and
  asserts the rendered origin changes, so the display is not vacuous while every
  shipped Site is `SHIPPED`.
- Configured components, devices, and signal mappings render from the Foundation
  with identifiers and labels taken from the document, not hard-coded in the
  frontend. A test changes the fixture content through a fake repository and
  asserts the rendered content follows.
- The screen states that configuration is fixed at creation in M1. It does not
  say or imply that configuration is file-backed, that it can be edited
  elsewhere, that a Save or Publish exists somewhere, or that approvals,
  versions in place, or configuration history exist.
- No edit, Save, Publish, rename, `site_id` change, delete, duplicate, approve,
  diff, history, or rollback control is present, enabled or disabled. A disabled
  control that implies a workflow the product does not have is not acceptable.
- API tests assert that `PUT`, `PATCH`, and `DELETE` on `/api/sites/{site_id}`
  are not served, and that no update or delete route exists for a Site anywhere
  in the served route inventory.
- The screen shows explicit No evidence or Unavailable states for operational
  content and renders no zero-value chart, fabricated telemetry, source-health
  value including OFFLINE, analytics, Replay control, or Finding.
- Free text from the document, including `display_name`, notes, and image
  references, renders as text and never as markup, and is never used for lookup,
  routing, or a filename.
- Site Configuration and its API path are served identically with
  `simulator_lab.enabled` true and false, and are not registered through the
  simulator gate.
- All data reaches the screen through the `SiteRepository` port. This slice adds
  no new adapter import outside the single composition module and no new
  `yaml`, `pathlib`, `sqlite3`, or `open(` usage inside the sites package
  outside `adapters/`.
- The carried-forward "no digits inside `<main>`" assertions in
  `operatorRouteFrames.test.tsx` and `simulatorLabGate.test.tsx` are replaced
  with configuration-specific assertions wherever truthful Foundation values now
  render. Replace, never loosen.

## Required Product And Domain Semantics

- Site Configuration in M1 is a read-only view of an already-decided Foundation.
  Configuration is fixed at creation. In-place editing, Save and Publish over an
  existing Foundation, rename, delete, approvals, configuration history, diff,
  and rollback do not exist in M1 and must not be implied.
- `site_id` is immutable after creation.
- Configuration origin (`SHIPPED` or `USER`) is provenance about the
  configuration document. It is a separate concept from `source.mode`, lifecycle
  status, integration readiness, and source health, and none of the five may be
  rendered as a proxy for another.
- Foundation version and validity interval are declared facts about the
  configuration document, not derived state and not evidence.
- Configured content is component truth, which is distinct from device-reported
  evidence. Showing a configured device is not a claim that the device has
  reported anything.
- Presentation metadata is optional and must never affect identity, simulation,
  ingestion, analytics, or evidence interpretation.

## Protected Seams

- Read-only configuration UI: review-time + contract test.
  Site Configuration renders every Site read-only regardless of origin, offers
  no edit, Save, Publish, approval, rename, delete, or history affordance, and
  states that configuration is fixed at creation in M1. No update or delete
  route exists for a Site.
- Configuration-only Site states: CI guard.
  A valid Site with no accepted evidence shows No evidence or Unavailable rather
  than fabricated telemetry, zero-value charts, source health, analytics, or
  Findings.
- YAML configuration authority: unit/contract test.
  Rendered Foundation content comes from the strictly validated document, not
  from frontend defaults or fallbacks.
- Configuration persistence port: CI guard.
  Configuration reaches the screen only through the port. The T005 adapter
  isolation and storage-technology guards still pass unchanged.
- Site identity: contract test.
  The configuration route is addressed by `site_id`; `display_name` is never
  identity, a route segment, or a lookup key.
- Vocabulary separation: CI/review check.
  Configuration language must not borrow source-health vocabulary
  (Online/Stale/Offline) or asset-assessment vocabulary
  (Healthy/Watch/Needs attention/Degraded/Unknown) for lifecycle, source mode,
  or configuration origin.
- Simulator feature gate: CI guard.
  Site Configuration is a product capability and is not gated on
  `simulator_lab.enabled`.

## Focused Tests And Checks

- UI test opening Site Configuration for the canonical Site and asserting
  Foundation version, validity interval, timezone, lifecycle status, source
  mode, integration readiness, and configuration origin all render as distinct
  labelled facts.
- UI test asserting no edit, Save, Publish, rename, delete, duplicate, approve,
  diff, history, or rollback control exists, enabled or disabled.
- UI content test asserting the "fixed at creation in M1" statement is present
  and that the superseded file-backed/uneditable wording is gone.
- UI test driving the screen from a fake repository with altered origin and
  altered Foundation content, proving the rendered values follow the record.
- UI test for the unknown-`site_id` state and for the explicit No evidence /
  Unavailable operational states.
- API test asserting `PUT`, `PATCH`, and `DELETE` on a Site are not served, run
  against the served route inventory rather than a naive route list.
- Route test asserting Site Configuration behaves identically with
  `simulator_lab.enabled` true and false.
- Run `tools/check-architecture.ps1`, including the T005 adapter isolation and
  storage-technology checks.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not add any write path, port mutator, writable store, templates, template
  catalog, or Create action. Those are T007 and T008.
- Do not add in-place editing, Save, Publish, rename, `site_id` change, delete,
  duplicate, Foundation version bump in place, configuration diff, history,
  rollback, or approvals, and do not add disabled placeholders for them.
- Do not render a single-line diagram, auto-layout, a Devices & Sensors screen,
  or a topology view model, and do not make ratings or mappings agree with a
  diagram. Those belong to Causal Sequencing step 4; this slice lists configured
  content as read-only text.
- Do not add scenarios, run setup, simulator execution, gateway staging,
  ingestion, source envelopes, evidence records, source health, charts,
  analytics, Replay, or Findings.
- Do not introduce a database, ORM, migration tool, or cache.
- Do not add port methods speculatively.
- Do not give the simulator a repository handle, and do not gate Site
  Configuration on `simulator_lab.enabled`.
- Do not weaken the T003/T004 route and API boundary tests or the T005 port
  guards, and do not loosen the carried-forward fabricated-value assertions.
  Replace them with configuration-specific assertions where truthful values now
  render; never relax them.

## User Review

User review is required. This is the first of the two checkpoints the Architect
named for this feature, and it carries the checkpoint deferred from T005.

What the user is being asked to settle:

- Site and Foundation semantics as they now appear on screen: the narrowed M1
  field set, Foundation version and validity interval, and the separation of
  lifecycle status, source mode, integration readiness, and configuration
  origin into four independent facts.
- Configuration-only UI language across Sites List, Site Details, and Site
  Configuration: what a Site with no evidence is allowed to say, and that it
  says No evidence or Unavailable rather than showing zero values.
- The read-only statement itself. "Configuration is fixed at creation in M1"
  replaces the superseded file-backed wording, and it is the product's public
  promise about what M1 does not do.

Planning of T007 and T008 already exists so the write path is not designed under
pressure, but both remain provisional until this checkpoint is accepted or
redirected, exactly as T004 was re-planned after the T003 redirection.
