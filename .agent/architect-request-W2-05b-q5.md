# Architect request: W2-05b q5 (N13–N17)

You are the AssetOps Architect. Read the `.ai/ROLE_CONFIG.md` section "Mockup drives the design; implementers never decide" and the whole of `.agent/W2-05b-build-spec.md` (q1–q4). The code is on `task/W2-05b-ev-producer` at head `89f118b4`. Read `.agent/W2-05b-pending-rulings.md` from that branch with `git show task/W2-05b-ev-producer:<path>`. It holds notes N13–N17.

Commit 4 is built, and commit 5 is being built in parallel. For each of N13–N17, either ratify it with a reason or give the exact correction, with the files and tests involved.

N13 matters most: a run whose c1/c2 frozen mappings are swapped consistently goes undetected. Rule whether this is a defect, and if so give the exact detection rule.

Say whether any correction touches commit 5's scope. Append the rulings to `.agent/W2-05b-build-spec.md` as "Run 5 rulings (q5)". Write nothing else. Do not commit.
