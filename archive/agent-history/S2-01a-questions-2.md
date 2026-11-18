# S2-01a phase 2: questions for the Architect

None of these blocks S2-01a. Each is built on the fail-closed default named below. Each matters for the S2-01b and S2-02 demo path.

## Q4: the converted KOBO-001 binding set binds 10 of the 12 legacy signal links

**Finding.** The ten registered binding links match the legacy YAML Foundation's component links exactly, pair for pair. They include `generator-controller/status`. The legacy Foundation has two more links that no binding row carries:
- `battery-pcs-controller/discharge-capability` to `battery-pcs`
- `pv-inverter-controller/available-power` to `pv-inverter`

Per AC2 and the Q3 answer, a registered Draft freezes links only from binding rows, so these two pairs have no component link.

**Effect.** With publication profile 3 or 4 and the daytime model, nothing changes: the registered and legacy runs give identical observations and digests (`host/tests/test_registered_kobo_execution.py`). Profile 5 declares these two capability signals. Under it, the host would list them among the reporting paths the installation does not configure (`execution_adapter.py`, the unconfigured-path notes) and report no capability. Today that combination cannot run, for the reason in Q5.

**Options.**
- (a) Keep the current behaviour: the binding set is the authority, and an unbound channel is not reported.
- (b) Have a later S1 binding publication or conversion add the two capability channels, with their roles.
- (c) Refuse setup when the selected publication profile declares a signal the binding set does not bind.

**Recommendation.** (a) now. Choose (b) if the S2-02 demo needs dispatch capability evidence.

**Default built:** (a).

## Q5: the imported KOBO-001 Foundation does not carry the generator parameters the mini-grid models need

**Finding.** Two Drafts were set up from the registered basis (KOBO-001 Foundation v2 in the test fixture):
- With `mini-grid` v3 and the `kobo-mini-grid-degraded-evidence` scenario, the Draft is BLOCKED with `INITIAL_VALUE_NOT_RESOLVED` for four generator parameters: `generator-rated-power`, `generator-start-soc-threshold`, `generator-stop-soc-threshold` and `generator-start-delay`.
- With the `kobo-daytime` scenario, the same model also blocks, with two more reasons: `fuel-tank-volume` and `generator-state`.

The legacy host fixtures run the mini-grid models only because they build the Site from template v3 content. A Draft from the registered basis runs with the daytime model only.

**Effect.** This is an honest block, not a defect in S2-01a: a blocked Draft names what its Foundation lacks. But generator status cannot be observed end to end from a registered Draft until the registered Foundation carries those values. The host consumption of the `generator-controller/status` link is therefore proven at the link-resolution level (`_component_carrying`), not by a staged generator-status report.

**Options.**
- (a) Leave it as it is.
- (b) Publish the generator parameters as a registered Foundation revision through an S1-style publication, in S2-01b or the S2-02 demo setup.

**Recommendation.** (b), before the S2-02 demo relies on generator evidence.

**Default built:** (a).
