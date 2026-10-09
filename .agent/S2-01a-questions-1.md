# S2-01a questions 1 (Implementer, phase 1)

For the active Architect. None blocks phase 1; each was built on the fail-closed default named. Decision context: `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary`.

## Q1. Site-row facts are not in the pinned snapshot

The `assetops.acquisition-snapshot/1` document pins tenant, Site UUID and code, gateway, Foundation and mapping references, sources and bindings. It does not pin the Site's display name, site type or time zone. The Lab run input (`record_at(site, revision)`) takes those from the current `site` row, so a historical selection still depends on three mutable current-row fields.

- Built default: they are read from the current row. If the strict parser refuses the row (for example a blank name), setup refuses as `REGISTERED_BASIS_UNAVAILABLE` / `SITE_RECORD_INVALID` with no Draft. Nothing is substituted. Tests: `test_a_site_row_the_parser_refuses_is_typed_even_for_a_historical_basis` and the Postgres `test_a_site_row_the_parser_refuses_is_a_typed_refusal_not_a_substitute`.
- Options:
  - (a) Keep this default and fold the issue into the planned registration-identity hardening.
  - (b) Add these facts to a snapshot schema v2. That needs a serializer, migration and backfill rule.
  - (c) Freeze them from the import record or Foundation content.
- Recommendation: (a) for S2-01a. The current-row gap codes (`SITE_*`) are already reported apart from the basis. Only an unparseable row blocks.

## Q2. What counts as a "current/new" acquisition snapshot

Built rule (`binding_service.is_current_snapshot`): a binding set is current when it is still recorded (`superseded_at` null) and its validity has not ended at server now (`valid_to` null or later than now). This includes a future-effective period. A current snapshot refuses on every configuration gap. Any other snapshot is historical: superseded, or its period has ended. A historical snapshot is validated from its stored bytes against immutable references, and current-row gaps (`CURRENT_ROW_GAP_CODES`) are only reported.

- The S1 download route uses the same rule. It now sends `X-AssetOps-Snapshot-Selection`, and the Foundation summary carries `selection` and `current_registration_gaps`.
- A consequence to confirm: an ended period is historical even when it is still recorded. A Lab run in such a period survives a later current-registration edit.
- Recommendation: keep it. Confirm or narrow it.

## Q3. Frozen signal mappings come from the registered bindings

For an imported Site, the run's `signal_mappings` (the device-signal-to-component links the host reads) come from the selected binding set, not from the Foundation content's legacy `signal_mappings` list. Each link is keyed by the binding revision ID. Its component is the binding's asset code, which must be a component of the selected Foundation; otherwise setup refuses.

- A binding with no asset (a Site-level role) is not frozen as a component link. It remains in the frozen snapshot bytes.
- The asset code is looked up from the current `asset` row, by the immutable asset UUID the binding pins.
- Recommendation: accept this for S2-01a. Put asset-code immutability in the same hardening as Q1.
- Phase 2 should confirm that the host's use of these links is unchanged for Kobo. The Draft is `READY` with 10 links, including `generator-controller/status`.
