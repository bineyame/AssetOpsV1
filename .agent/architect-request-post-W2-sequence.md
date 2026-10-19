# Architect request: binding post-W2 two-lane sequence

You are the AssetOps Architect.

## Read first

- `.ai/ROLE_CONFIG.md`, in full: the readiness gate, "Mockup drives the design; implementers never decide", and "Token Efficiency".
- `.agent/owner-post-W2-parallel-plan-2026-10-18.md`, the owner-approved proposal.
- `.agent/owner-W2-walkthrough-not-blocking-2026-10-19.md`.
- `.agent/owner-client-conversations-2026-10-18.md`.
- `tasks/README.md`.
- `frontend/docs/architecture/site-first-execution-plan.md`, plus the wave plan documents it references for W3–W6.
- The v69 dependency registry and its checker, `frontend/docs/architecture/check_v69_dependency_registry.cjs`.
- `.ai/MILESTONE_REVIEW_BACKLOG.md`.
- `.ai/DECISIONS.md`.

W2-07, the last W2 slice, is building now on migration `0026`. Allocate post-W2 migrations from `0027`. This sequence takes effect when W2-07 merges.

## What to produce

Write the binding post-W2 sequence to `.agent/post-W2-sequence.md`, amending the owner proposal and recorded as decision `D-2026-10-20-post-w2-sequence`. It must cover each of the following.

1. **Lanes and slice order.** Use at most two lanes and follow Steps 1–3 as approved. For each step:
   - list the exact slice IDs and names, with each slice's v69 screens and registry nodes;
   - state its dependencies, checked against the registry checker;
   - give a size estimate.
2. **Shared-file ownership.** Give one owning lane per shared file or area: the migrations directory, `main.py` router mounts, the registry, the shell and navigation, the tab-inventory guard (with its multiset rule), the check-all guards, and the shared UI components. State the freeze rule for the W4 core work-case model, including how a change goes through the Architect.
3. **Migration number allocation** per slice, up front, from `0027`.
4. **Cross-slice seam check.** List every W2/W1 seam that the post-W2 slices consume:
   - cold and EV selected reads;
   - Findings;
   - currentness;
   - `source_provenance`;
   - the S4-05 classifier;
   - the tab guard.

   Name the contract each slice must honour, and flag any seam that is unsound or needs an Architect fix first.
5. **W2 owner walkthrough handling.** Structural walkthrough findings must be fixed before W5 builds on the W2 cold and EV screens. Say where that gate sits in the sequence.
6. **OPS-01, the backend test-speed task.** Define its scope and acceptance, and place it in Step 1.
7. **Per-slice readiness.** Each slice still needs its own full build spec with a concrete-artifact pre-build closure before its builder starts. Name the order in which the specs should be written so that neither lane waits.

## Constraints

Write only `.agent/post-W2-sequence.md` and the `.ai/DECISIONS.md` entry. Do not commit.
