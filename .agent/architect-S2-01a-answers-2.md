# S2-01a phase-1 answers — 2026-10-08

**Codex Architect**, per `.ai/ROLE_CONFIG.md`. These decisions answer `.agent/S2-01a-questions-1.md` without reviewing the whole phase. They amend `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` in `.ai/DECISIONS.md`. I do **not** want the owner to weigh in on Q1, Q2 or Q3: each is a bounded consequence of the S1 registered snapshot and the S2 Lab/acquisition contracts, under the Architect's delegated decision authority.

## Q1 — Keep snapshot v1 and the current-row default, with one consistency guard

The stored snapshot did not claim to version Site name, type or timezone; a schema-v2 backfill or reuse of the original import would invent an answer for later legitimate Site edits. S2-01a may use valid current-row values and freeze them on the Draft, but `knowledge_at` selects only the time-valid Foundation/binding pair, not historical Site metadata. An unparseable row must remain a typed refusal.

**Phase 2 change:** refuse setup before Draft creation if the current Site type does not match the selected binding role set, and label the name/timezone shown with the run as current Site metadata frozen at setup rather than facts recovered at `knowledge_at`. No snapshot-v2 migration or import-file fallback. Record the remaining lack of historical Site metadata in `.ai/MILESTONE_REVIEW_BACKLOG.md`; a future historical-metadata claim needs versioned Site metadata or a revised snapshot contract. The S2-02 packet now names the identity review required before evidence acceptance.

## Q2 — Accept the built current/historical classification

An unsuperseded set with `valid_to` later than server now (or open-ended) is still a candidate for new acquisition, even if its `valid_from` is in the future, so current configuration gaps must block it. A set whose validity ended is a historical artifact even when its recorded row remains current; verifying its published bytes and original references rather than today's mutable registration rows is exactly what the earlier Q1 decision intended. A superseded set is historical too; selected Foundation-content gaps continue to refuse, and the selection header describes the artifact, not gateway health or upload authority.

**Phase 2 change:** none for this rule. Keep the historical-ended-period and future-effective-with-current-gaps cases in the focused tests and retain the separate current-gap disclosure.

## Q3 — Accept binding-derived frozen links, with asset identity hardening before S2-02

The S1-01 addendum explicitly says legacy `signal_mappings` are comparison input, while S1-02 binding rows own the operative channel-to-asset meaning. Using the binding revision ID and its asset UUID, then requiring the resolved asset code to occur in the selected Foundation, is right; an assetless Site-level binding supplies no component link and remains in the pinned snapshot. This avoids silently reviving the old YAML mapping authority.

**Phase 2 change:** confirm the host consumes the ten binding-derived Kobo links, including `generator-controller/status`, without reading legacy mapping links or private Lab causes into public reports. No link-construction redesign. Current `asset.asset_code` is still mutable and could redirect an immutable asset UUID to another valid component code; record that carry in `.ai/MILESTONE_REVIEW_BACKLOG.md` and enforce stable asset-code identity with reconciliation before S2-02 accepts evidence, as added to its packet. It must not be left as an unqualified evidence-lineage guarantee.
