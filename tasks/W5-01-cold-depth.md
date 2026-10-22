# W5-01 Cold depth

Status: planned, closed build contract in [`.agent/W5-01-build-spec.md`](../.agent/W5-01-build-spec.md). Lane A. Decision `D-2026-10-22-w5-01-w5-03-buildspec`.

## Purpose and order

Deliver v6.9 `cooling`, `cold-health`, and `cold-scenarios` for an authorized COLDCHAIN Site. Split at the backend pipeline/page cap:

| Merge | Result | Units | Migration | Predecessor |
| --- | --- | --- | --- | --- |
| W5-01a | Selected cooling recovery and cold Health, with explicit missing context and exact W2 lineage | C1–C3 | None | W2-F `2df2a3da`, W4-03 `44cc88c2` |
| W5-01b | Authored cold Financial scenarios, plus refused cold Finding Unknown strip | C4–C5 | `0032_w5_cold_scenarios`, `down_revision="0030_w4_mini_decisions"` because `0031` was reserved and unused | reviewed W5-01a |

W5-01b merges before W5-02 (`0033`). W5-03 (`0034`) follows W5-02. Each sub-slice has its own focused checks, independent review and merge; owner visible acceptance follows the wave walkthrough. No W4-01 case model change is authorized.

## Observable acceptance

- Cooling shows only selected accepted probe/compressor/backup evidence. The W2 selected start chain does not establish an ordered recovery, so the current available replay is **Limited**, not a measured 36/42-minute comparison or compressor diagnosis. A missing door/loading/ambient/defrost context stays Unknown. Its links retain Site, half-open UTC window and cutoff.
- Health distinguishes a failed generator start observation from equipment condition. Cooling plant condition, probe spatial coverage, product outcome and root cause are Unknown or Limited. No gateway receipt or configured asset makes physical condition healthy.
- Financial scenarios have immutable authored revisions and explicit assumptions. They are never labelled observed, verified savings, current consequence or product loss. Zero scenarios means no authored rows in the scoped selection, with a watermark; failed/unauthorized reads cannot become an empty success.
- The refused cold Finding page shows `Finding state` / `Unknown` / `Confidence: Unknown` above `PageRefusal`; `coldRoutes.test.tsx::w2f_finding_strip_confidence` asserts it. W2-F's L1 is thereby closed. L2 capture provenance is outside this product slice.
- Both 1440 and 390 captures cover positive, empty, pending, historical and refusal where applicable. Every capture uses the producers and one-clock rule in the build spec. New page captures and their layout assertions are done by the page's unit.

## Review and completion

Each unit owns only its named files. C1 and C4 are per-unit review gates for shared read/router/schema code; C2, C3 and C5 are reviewed before their sub-slice merge. Run focused backend/frontend tests for each unit, `tools/check-all.ps1` after shared navigation/registry changes, and one same-revision real-Postgres backend full suite per sub-slice outside another heavy builder. Capture mock/app 1440/390 pairs, horizontal overflow and height caps. Stop processes started for captures and drop private `*_test` databases. A reviewer checks exact DTO fields, source IDs, route guards, visible literals and producer-backed states before the first builder starts. This task grants no implementation latitude beyond the attached unit cards.
