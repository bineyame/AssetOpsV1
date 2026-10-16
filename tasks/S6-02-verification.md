# S6-02 — Later-window verification

Status: implementation-ready as [S6-02a](S6-02a-verification-core.md) then [S6-02b](S6-02b-verification-ui.md). Planner: Codex, 2026-10-16.

S6-02a is non-UI (`USER_REVIEW_REQUIRED: false`) and mergeable after fresh independent review. S6-02b is UI (`USER_REVIEW_REQUIRED: true`) and held for the owner's served walkthrough. The contract is `D-2026-10-16-s6-verification` (`.ai/DECISIONS.md:4155`), `.agent/architect-A-S6-verification-answers.md` and review/re-review carries. Applied activity and measured effect remain separate. No causal or realized-savings claim.

Registry ownership: S6-02a owns `D-verification-window`, `I-sim-verification-cases`, `I-verification-plan-read`, `I-verification-read`, `I-action-evidence-read`; its graph path depends on S6-01a, not the S6-01 umbrella or S6-01b owner gate. S6-02b owns the corresponding three UI nodes and closes `I-S6-02`, which requires S6-02b and retains its S6-01 umbrella dependency. The queue baseline includes both slice nodes. S6-03 Site Work index stays independent.

**Architect rulings:** `D-2026-10-16-s602-questions` fixes version-1 10% feeder-demand/PV-available energy and 2-point initial-SOC comparability bands; UTC-aligned half-open five-minute interval integration with sampled SOC/reserve; plan replacement cutoff at first later report acceptance or later run start; interim labels **Trial missed a safety or service limit**, **Target not met**, **Could not conclude**; and latest-current default with explicit historical selector. The child packets carry the exact calculations, fail-closed cases and UI assertions.

**Plan fix round 1 (2026-10-16):** Applied Architect rulings and plan-review dependency correction; the core remains implementation-ready after S6-01a and the UI remains held for served owner review.
