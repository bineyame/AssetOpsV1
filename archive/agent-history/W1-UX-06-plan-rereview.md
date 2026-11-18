# W1-UX-06 plan re-review

Reviewer: a fresh, independent Claude reviewer who did not author the packet or the amendment. I worked read-only in worktree `AssetOpsV1-review4` at `fd6a1aaf`. The amendment diff is `git diff HEAD~1 HEAD -- tasks`, which touches only `tasks/W1-UX-06-closeout.md`. No suites were run, as dispatched.

## Verdict: ACCEPT

The prior Medium (M1) is resolved, L1 and L2 are addressed, and the packet agrees with `D-2026-10-17-w1-ux-06`. The registry is valid. Two new Lows are noted below; neither blocks.

## M1 (width guard on every cited evidence script): resolved

- `tasks/W1-UX-06-closeout.md:34` replaces the old fixed list of five scripts with an inventory rule. After UX-02/03/04 merge, the Implementer lists every `tools/*-evidence.mjs` named in the umbrella map and in the combined document, and applies ONE shared width check to all of them. Any script left unguarded is recorded **not established**, never met. This is the rule the prior review asked for.
- The minimum list now names the UX-02 sibling, `s408` (the umbrella's S4-08 evidence, `tasks/W1-UX-mockup-fidelity.md:76`), `s502`, `s602b`, `s603`, `s601b`, `s3-dispatch`, `s302`, `s404` and `v01a`. Every named file except the pending w1-ux-02/03 siblings exists in `tools/`.
- The nonexistent `w1-ux-04-evidence.mjs` path is gone. The packet now says "any UX-04 sibling actually present".
- The width proof itself is unchanged and adequate: `innerWidth === width`, `clientWidth` in `[width-20,width]` before measuring, both widths recorded, and a negative test for a wrong width.

## L1 and L2: addressed

- **L1.** `:45` states correctly that `/^As of /` rejects `As of: time not recorded` and that the fix accepts both forms. The code-reality row at `:14` still calls the regex "permissive". The appended note supersedes that description, and the Phase 1 fix was correct either way.
- **L2.** `:45` commits Phase 2 captures in batches by tool, and a failing tool is recorded "not run" with its reason instead of stalling the slice. The header at `:3` still says "S-M"; registry effort `M` stands.

## Architect agreement

`:45` binds the Implementer to `D-2026-10-17-w1-ux-06` and `.agent/architect-W1-UX-06-answers.md`: "implement exactly those labels". The ruling matches the packet's recommendations, with two additions:

- Q3 is scoped: unknown, untrusted or observed-after-receipt fact age must say the age cannot be confirmed, never `OLD`.
- Q4 is amended: no readiness-dependent step appears complete on an unrecognised code alone, and the `NO_REGISTERED_SOURCE` message is kept.

Both additions are reached through the reference. The decision is present at `.ai/DECISIONS.md:5` and `:49`. Nothing conflicts.

## New Lows (non-blocking)

- **N1. Questions section left in recommendation form.** `:21-28` still reads "settle before wording changes", and the Phase 1 and final-proof text says only "approved labels" and "approved unknown/stale copy". Q4's amendment is the most likely to be missed, because its readiness-dependent step and zero-enabled test cases appear only in the answers file. The ruling's test expectations should be listed in the focused proof:
  - old and unknown-age cases for the selected gateway;
  - unrecognised Readiness and Health codes;
  - both zero-enabled cases;
  - no completed readiness-dependent step on an unrecognised code.
- **N2. Inventory list naming.** The minimum list does not name `s701-health-evidence.mjs`, which is the existing Health evidence tool and likely to be cited for the Health rows. The inventory rule already covers it. `s3-dispatch` is written without its `-evidence.mjs` suffix.

## Checks

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs` exited 0 with "Registry valid: 241 nodes, 11 linked pilot panels" and "Area briefs valid".
- No suites were run, and no evidence tools were run, because they need Chrome, the walkthrough DBs and a dev server.
