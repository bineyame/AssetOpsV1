# S2-01a — Registered Kobo Lab basis

Status: outline; refine after S1-02 review, before activation
USER_REVIEW_REQUIRED: false
Milestone: S2 Evidence
Depends on: S1-02
Branch: task/S2-01a-registered-lab-basis
Architect cut: `D-2026-10-07-s2-edge-split-and-demo-source`

## Visible result

Imported KOBO-001 can create and run a Lab Draft from the effective, registered Postgres Foundation and SignalBinding snapshot. Lab shows the selected revision IDs/hash and configuration gaps after reload. Commit to product Evidence remains blocked until S2-02.

## Contract and acceptance

Read the S1-02 published snapshot for the selected Site/source time. Freeze its public configuration basis on the Lab run; reject an absent, superseded-at-selection or incomplete registered mapping with a clear reason. The Lab kernel may retain private scenario causes and oracle, but the gateway-facing report uses only public device observations. Historical YAML Stage GET remains read-only and labelled with its frozen basis; a pre-import Stage cannot be reinterpreted as newly registered evidence.

Reviewer starts, steps and reopens one Kobo run, changes a Foundation/binding version, and proves a new run selects the new basis while the old run keeps its original basis. Check blocked Commit and absence of Lab-private fields in the public report. This closes `I-lab-registered-basis` and `I-S2-01a` together. S2-01b supplies durable publication.
