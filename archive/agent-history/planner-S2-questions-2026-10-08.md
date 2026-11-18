# S2 planning questions for Architect — 2026-10-08

## Q1 — Historical registered snapshot availability (S1-02 carry n5)

S1-02 persists exact canonical combined snapshot bytes and their hash at publication. `sites/binding_service.py::acquisition_snapshot` verifies those bytes but first calls `configuration_gaps(site, foundation, registrations)` using current registration rows. A later source external-ID edit can therefore make `GET /api/sites/{id}/foundation/snapshot?at=<earlier time>` return 409 even though the earlier registered snapshot is intact. S2-01a must select and freeze a historical valid basis for an explicitly earlier Lab run; S2-02 later validates accepted-as lineage.

Options:

1. Serve a pinned historical snapshot when its stored bytes/hash and originally registered references are valid at the requested source time; report today's registration gaps separately, and continue to refuse a new/current snapshot with gaps.
2. Keep current-registration gaps as a gate for every download, including history; historical Lab setup remains unavailable after such an edit until current registration is repaired.
3. Forbid mutation of registration identity fields at the database boundary, with a migration/repair path for any already changed rows; historical download still needs a defined rule for non-identity current gaps.

Recommendation: 1 for historical reads, plus 3 as a later integrity hardening task. It preserves published bytes and makes time selection meaningful without treating an invalid current configuration as healthy. Please specify whether a historical run may select a superseded-at-knowledge-time but originally valid registered snapshot, and what `knowledge_at` should mean for Lab selection.

Can S2-01a implementation proceed? **Partly.** The adapter, freeze, execution and UI work can proceed using the existing fail-closed 409 behavior. Final historical-selection acceptance and n5 closure need this decision; the Implementer must not bypass the check or substitute YAML in the meantime.

## Q2 — One frozen basis across a Lab run interval

The existing Lab setup request declares `start_time` and `end_time`, and a Draft freezes its inputs once. S1 Foundation/binding versions have effective periods. S2-01a promises one frozen registered snapshot on a run, while the technical design checks each future envelope's source time against its originally registered valid range. A run crossing a Foundation/binding boundary could produce readings after the frozen snapshot's period ends.

Options:

1. Require the full run interval to fit one selected registered basis; refuse a cross-boundary setup with the boundary time and let the user create two runs.
2. Allow one run to carry multiple pinned bases and switch mappings at the boundary; this expands S2-01a storage and S2-01b gateway handoff.
3. Allow one frozen basis after its effective end and rely on later ingestion rejection; the Lab would knowingly produce unpublishable readings.

Recommendation: 1 for S2-01a. It preserves the small frozen-run contract and makes refusal visible before execution. Can implementation proceed? **Yes**, with option 1 as a fail-closed default; change it only on Architect direction. The selected basis should be evaluated at run `start_time`, with the run's requested Foundation version matching it.
