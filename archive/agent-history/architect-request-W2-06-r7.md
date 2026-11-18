# Architect request: W2-06 run 8 pending rulings (r7)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide" and "Token Efficiency";
- `.agent/W2-06-build-spec.md`, with all rulings through r6;
- the run-8 section (P1–P8) of `.agent/W2-06-pending-rulings.md` on branch `task/W2-06-ev-assessment` (`git show task/W2-06-ev-assessment:.agent/W2-06-pending-rulings.md`);
- the packet `.agent/W2-06-review-packet.md` on the same branch.

Commit 5 is at `0dcedf16`.

**P1–P7** are interim copy and display choices that the builder implemented. For each one, either confirm it or give the exact replacement: the literal copy, the component, and the test assertion. The v69 EV mock screens are authoritative.

**P8** blocks check-all. `tools/checks/navigation-truthfulness.ps1` fixes the inventory of unbuilt tabs at the six W1 entries, but commit 5 renders the mock's EV tabs `Availability` and `Energy / site power` (sessions) and a second `Recommendation` (ev-finding). check-all is at 8/10, with Navigation truthfulness and Architecture seams failing; the seams failure comes through the rail fixture baseline. Rule the exact inventory change, as a literal list with its multiplicity rule, plus whatever baseline/fixture update the Architecture seams guard needs. Name the guard test or self-test that must prove the new entries without letting arbitrary additions through.

Append the result to `.agent/W2-06-build-spec.md` as "Run 8 rulings (r7)", amending `D-2026-10-18-w2-06-07-buildspec`. Also amend `D-2026-10-17-f5-subtabs-and-contact` if P8 needs it. Write nothing else. Do not commit.
