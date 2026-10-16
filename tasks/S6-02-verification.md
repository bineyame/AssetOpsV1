# S6-02 — Later-window verification

Status: implementation-ready as [S6-02a](S6-02a-verification-core.md) then [S6-02b](S6-02b-verification-ui.md). Planner: Codex, 2026-10-16.

S6-02a is non-UI (`USER_REVIEW_REQUIRED: false`) and mergeable after fresh independent review. S6-02b is UI (`USER_REVIEW_REQUIRED: true`) and held for the owner's served walkthrough. The contract is `D-2026-10-16-s6-verification` (`.ai/DECISIONS.md:4155`), `.agent/architect-A-S6-verification-answers.md` and review/re-review carries. Applied activity and measured effect remain separate. No causal or realized-savings claim.

Registry ownership: S6-02a owns `D-verification-window`, `I-sim-verification-cases`, `I-verification-plan-read`, `I-verification-read`, `I-action-evidence-read`; S6-02b owns the corresponding three UI nodes and closes `I-S6-02`. The queue baseline now includes both slice nodes while retaining the original S6 gates. S6-03 Site Work index stays independent.
