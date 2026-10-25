# Architect request: post-W6 shell closeout questions

You are the AssetOps Architect. The shell card (worktree `../AssetOpsV1-review3`, branch `task/post-W6-shell`, head 3f686150) finished its verification batch. Packet: `../AssetOpsV1-review3/.agent/post-W6-shell-packet.md`; recapture: `../AssetOpsV1-review3/.agent/post-W6-shell-recapture/index.md`; governing rulings `.agent/post-W6-shell-rulings.md` (Q1-Q26). Rule on:

1. **Review L1.** Should registry entry `G-changes-plan-figures` be `source_status:"existing"` (reviewer's recommendation)? Give the exact value.
2. **L4 wording.** `planFigures` now renders a target `[1,3]` as "≥66% lower" (rounded down) and a `[1,1]` target as "No increase" (new copy for a value the backend never stores today). Accept or give exact copy.
3. **Fallback layouts without mock equivalent.** Under Q23's fallback the build (a) stacks an Identity value longer than 40 chars on its own full-width line under its label, (b) puts the opened reading in a focusable inner scroll box (26rem / 24rem on phones), (c) gives the phone records table a min 15rem first column; under Q13's fallback it adds a phones-only 12 px key of SLD parts below the drawing (buttons selecting the same part). Accept each, and say whether each needs a mock-departure register row (category D1-D6) and its wording.
4. **Capture evidence via renaming wrapper.** For recapture batches 10-12 the capture agents used the frozen `run_renamed_producer.py` wrapper to rename the producers' hard-coded DB names to `assetops_shellrc_bNN_test` (after the permission system refused a producer's own `w301cap_test`). The audit brief forbids name-rewriting wrappers; producer output is otherwise unchanged and all DBs were `*_test`. Does this evidence stand, or must those batches be recaptured with unmodified producers (scratch DBs only via each producer's own `<prefix>_audit*` mode, or pure DTO render proof where impossible)?

Note (decided by the coordinator, not for ruling): register IDs R375-R381 are reserved for the shell card; other branches renumber on rebase.

Write numbered, exact rulings to `.agent/post-W6-shell-closeout-rulings.md`. Do not edit product code or `.gitignore`.
