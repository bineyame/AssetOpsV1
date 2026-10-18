# Architect request - W2-05a five implementer judgements (2026-10-18). Owner rule: implementer decisions are defects ruled by the Architect. Brief rulings; edit `.agent/W2-05a-build-spec.md` in place (include the mock mapping for the affected screen elements); amend `D-2026-10-18-w2-05-buildspec`. No code.

From the commit-3 implementer (branch task/W2-05a-ev-foundation):
1. `enabled_schedule` shape `{enabled, time_zone, weekly}` with `enabled` from the connector's `ev-connector-enabled`. Confirm or specify.
2. `ev-clock-error-bound` absent from the response (no field-list slot). Should it be served and shown (where in the mock: ev-foundation / ev-readiness)?
3. `feed` always an object with `asset_id` null when no feed; `meter_asset_id` = the single meter the feed supplies, else null. Confirm or specify.
4. `SOURCE_NOT_CONTACTED` raised only when contact is NEVER, not STALE. Confirm or specify.
5. Contact freshness measured at request time (as the cold read) rather than at the selected `at`. Confirm or specify, consistent with the W2-03 window-end freshness ruling.
Check each against the v69 mock screens `ev-foundation`, `ev-readiness`, `ev-sld` so nothing the mock shows is dropped. Print a 3-line summary.
