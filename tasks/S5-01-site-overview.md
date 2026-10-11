# S5-01 — Derived Site Overview

Status: outline; refine after preceding task review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S5 Overview
Depends on: S4-02
Branch: task/S5-01-site-overview
Planner: Codex, 2026-10-07

## Visible outcome

Mini-grid Overview shows selected-window assessment, timeline, bounded cost and drill-downs.

## Persisted object and read contract

SiteWindowSummary projection/read model and `GET /api/sites/{id}/overview?from=&to=` with source/analytic watermarks.

## Demo acceptance

Change date range; cards open exact assessment, Finding, consequence and evidence; reload projection.

## Missing/conflicting evidence

Unassessed objective is Unknown and stale projection says pending.

## Evidence lineage

Each card carries selected claim IDs and resolves their accepted SourceEnvelope chain.

## Review and refinement

S5-01 owns `I-site-overview-read/ui` for selected-window context, timeline and bounded money (`mini:1/2/4`), composing accepted S3 assessment and S4 Finding/financial records with source/analytic watermarks. Until the Site index exists, `mini:3` is honestly unavailable. [S5-02](S5-02-overview-finding-list.md) owns its separate empty and positive variants after [S4-04](S4-04-site-finding-index.md). No new Overview record is assumed. Keep the W3 global Findings index separate.

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Global Sites/Portfolio roots and unearned status cards.
