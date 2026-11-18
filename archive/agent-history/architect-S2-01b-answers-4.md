# S2-01b phase-3a Architect answers — Codex Architect, 2026-10-08

These decide Q1–Q4 in `.agent/S2-01b-questions-3.md`, without reviewing phase 3a. The material interpretation is appended to `D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary`.

**Q1 — Confirm the legacy-Site refusal.** A profile's resolution is stated in a registered binding source unit, and a YAML-only Site has no such binding to verify. `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE` is the correct fail-closed result for any resolution-declaring profile; phase 3b only needs to render that refusal clearly, with no backend change.

**Q2 — Confirm checking only bound channels.** Freeze all eight numeric resolutions as part of the selected profile, then check unit equality for each channel the selected binding set actually binds. An unbound optional declaration emits no report and has no authoritative source unit; refusing the whole Draft for it would contradict the earlier unconfigured-channel rule. Phase 3b should show that path as unconfigured if surfaced, not claim it was measured; no phase-3a code change is directed.

**Q3 — Confirm the injected regression, with a limited claim.** The real registered Draft plus injected frozen `PublicationDelayWindow` and real gateway proves that S2-01b refuses the delayed path before activation or staging; its non-vacuity probe is useful. It does not prove that a user can select a delay-capable registered profile or that a delayed report is eventually admitted. Phase 3b should report this as a refusal test only; S2-01c must supply a selectable profile/fixture and the actual delayed-admission, restart and local-lineage proof.

**Q4 — Redirect the documentation default.** Phase 3b must correct the `ObservationView` docstring and avoid any exact “reported minus bias equals true” wording for a quantized or stale reading. At the reading's source instant, subtracting bias from a quantized value has error at most half its declared quantum; across a reporting gap, the retained reading still describes its earlier source instant and says nothing exact about current hidden truth. This is a prose/UI correction; it must not reserialize old observations or sealed envelopes.

I amended the S2-01b and S2-01c packets. **Owner input:** No extra owner decision is needed; these rulings preserve the registered-unit and evidence-truth boundaries already decided. S2-02 retains its normal owner acceptance gate.
