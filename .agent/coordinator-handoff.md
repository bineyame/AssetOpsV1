# Coordinator handoff (2026-10-02, end of T026 build)

A fresh coordinator starts from this file; do not re-derive what it states.

## Where things stand

- Branch `task/T026-dispatch-capable-evidence` holds the full T026 build
  (phases 1, 2, 3a, 3b, a stage-withholding fix, fix rounds 1 and 2).
  Task status `in_review`. Nothing pushed; not merged.
- Claude review: ACCEPT after fix round 1 (B1, B2 fixed) and fix round 2
  (owner ruling `D-2026-10-02-scenario-states-override-issuer`). Review file
  `.agent/T026-review.md`; packet `.agent/T026-review-packet.md`.
- Final suites (serial): host 594, backend 1375, simulator 244 (from
  `simulator/`), frontend 1041, typecheck and build clean, both repo checks
  pass. Contract stays 9.
- Open carries: C2/C8 (held reading reads "no delay recorded" until release),
  C3, C4 (layout evidence not fully green, not re-run after fix rounds), C5
  (prolonged/evening scenario headers point to mini-grid v2), C6, C9, C10.
  AC15 server delta p95 misses 50 ms before T026 too (quiet re-measure:
  pre-T026 ~62 ms, profile 5 ~73 ms); owner ruled it a separate performance
  task (backlog "Carried from T026"), not a T026 defect.

## Next action

Owner hands-on check (USER_REVIEW_REQUIRED). The owner creates a Site from
template v3, discards any earlier profile-5 Draft (C10), makes a Draft of
`kobo-mini-grid-degraded-evidence` on `mini-grid` v3 / profile 5, and follows
the SOC reading sourced 07:00:00Z, published 07:10:03Z. On acceptance: close
out and merge to `main`.

## Standing rules

- Owner rulings and Claude usage rules in `.ai/ROLE_CONFIG.md` (now including
  the 120k hand-off and Sonnet-for-mechanical-steps rules, commit `21628ec`).
- 2026-10-03 21:23 Codex reset: revert the three temporary Claude rows in
  `.ai/ROLE_CONFIG.md`, queue retrospective Codex reviews (T025e, T025f,
  T025g, T026).
