# V-01b — Lab and Evidence visual fidelity

Status: done (owner visual acceptance conditional, 2026-10-13; reviews ACCEPT; merged to main by coordinator)
USER_REVIEW_REQUIRED: true
Depends on: merged S2-02 Lab and Site Evidence surfaces
Branch when activated: task/V-01b-evidence-lab-visual

## Visible outcome and acceptance

Compare app and v6.9 `lab`, `evidence` and `evidence-analysis` by manifest ID and supported panel portion. Capture 1440px desktop and 390px narrow app/mock pairs, or documented equivalents, for populated, missing and supported late/contradictory states. Review panel hierarchy, density, labels, keyboard navigation, Site/window/selection and reload behavior. Follow a visible accepted Evidence value through the read API to its SourceEnvelope; S3-02 owns the later positive claim-limit portion.

Record the exact route, viewport, supported claim, deliberate gap, API/lineage and accepted visual differences for each panel. Run frontend tests, typecheck/build, layout evidence and ledger/registry checks. Independent Reviewer and owner inspect this gate; it supplies visual acceptance only, never technical closure or whole-screen Real by itself.

## Review Outcome (recorded by coordinator, 2026-10-13)

- Reviews read (all six): `.agent/V-01b-review.md` RETURN (Finding 1); `V-01b-fix-rereview.md` RETURN (A, B; owner chose a further fix round, `.agent/owner-V-01b-second-return-2026-10-13.md`); `V-01b-fix2-rereview.md` ACCEPT; Architect `.agent/architect-V-01b-answers.md` required the Q1 Stage correction; `V-01b-fix3-rereview.md` RETURN (F1, tooling only; owner option 1, `.agent/owner-V-01b-fix3-return-2026-10-13.md`); `V-01b-fix4-rereview.md` ACCEPT (`b8bc4ce`, evidence tool `101/101 claims passed; 2 not run` reproduced on a private store). No unresolved disagreement: each RETURN was fixed and re-reviewed.
- Owner checkpoint: `.agent/owner-V-01b-walkthrough-2026-10-13.md` — conditional visual acceptance, layout/copy only, on the packet's named data gaps; headings "Draft run"/"Evidence" kept; "How each limit is set" and "Data sources · data quality" kept. Visual acceptance only, never technical closure or Real.
- Decision: `D-2026-10-13-v01b-visual-and-lab-read-boundaries`.
- Open carries: `.ai/MILESTONE_REVIEW_BACKLOG.md` "V-01b carries (2026-10-13)" (Q1 backend Stage field retirement; Q8 historical drawing unmeasured; not-committed Lab state unmeasured on a fresh store; `.action` primary-button cascade; layout tool preconditions). Registry/ledger closeout follows on a separate branch.
