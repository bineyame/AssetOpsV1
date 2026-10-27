# CC-R1 Links, claim labels, beneficiary key, no-double-count check

Status: in_review

Lane C (commercial). Branch `task/CC-R1-claim-links-beneficiary`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-cc`.
The implementation contract is `.agent/build-spec-commercial-2026-10-27.md` section 0.4 and section "CC-R1", including "Implementer questions and resolutions". The index is `.agent/build-sequence-2026-10-27.md`.

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-cc\backend;C:\Users\assef\Bineyame\AssetOpsV1-cc\contracts;C:\Users\assef\Bineyame\AssetOpsV1-cc\simulator;C:\Users\assef\Bineyame\AssetOpsV1-cc\gateway;C:\Users\assef\Bineyame\AssetOpsV1-cc\host;C:\Users\assef\Bineyame\AssetOpsV1-cc"
```

## Gates (from the spec)

- Pure: two otherwise identical eligible lines that differ only by beneficiary form two groups, never COMPARABLE, with different `group_key`s. Every category has a mapped beneficiary. An existing group key is unchanged.
- `double_count_violations` returns `[]` on every existing `test_w303_portfolio_*` body, and one violation per crafted defect.
- Frontend: the three labels render with `data-claim-level`. The forward link carries `revision_id`. The new text never says "saving" or "saved".
- Tier 2: `test_w303_portfolio_comparison_postgres.py` and `test_w303_portfolio_fixture_postgres.py`.
- Stop: adding `beneficiary` breaks an exact-key test outside `test_w303_*`.

Open: `.agent/CC-R1-questions.md` Q1, the wording of the verdict label (not wired yet). Packet: `.agent/CC-R1-review-packet.md`.
