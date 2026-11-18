# W3-02 closure 4 check (main c50ea24b)

Method: read the 27 items and spec lines 365-416; spot-checked main. Seams confirmed against code: `estate/scope.py` KEYS (3 roots, `decode_cursor` Finding/Action key sets only), `claim_limit_read.py` (`read/interval_ceiling/_reasons/role_coverage`, no `_on`), `select_dispatch_days_on` (`postgres_assessment_store.py:685`) and `_revision_detail` (:802), cold `_capabilities`/`_money` (private, no `_on`), `ev_site_reads.py` at package top, `select_consequence_on` (no window/quantity/overlap fields), `imported_sites` (ORDER BY site_code_key but not returned). Closure 4 builds on exactly these.

## 27 items
B1 CLOSED. B2 CLOSED (claim_limit_on, day reduction, role gaps). B3 CLOSED (per-window keys). B4 CLOSED (public `_on` facades, no `_ctx`/`open_on`). B5 OPEN-minor: "Site-supported evidence cutoff <= committed watermark" never names where the row-local cutoff/watermark comes from; fallback to base route is defined, so a builder could always fall back, but would have to decide the source. B6 CLOSED (0a-0c, 1-4 serial handoff).
S1 CLOSED. S2 CLOSED. S3 CLOSED. S4 CLOSED. S5 CLOSED. S6 CLOSED. S7 CLOSED. S8 CLOSED. S9 CLOSED. S10 CLOSED. S11 CLOSED. S12 CLOSED. S13 OPEN-minor: node ids and paths are given, but panel titles and the "reviewed paths" are not ("titles and reviewed paths"). S14 CLOSED.
N1 CLOSED. N2 CLOSED. N3 CLOSED. N4 CLOSED (by supersession list, not by pruning; body text still contradicts and relies on the builder reading closure 4). N5 CLOSED (+16). N6 CLOSED. N7 CLOSED.
Result: 25 CLOSED, 2 OPEN-minor (B5, S13). No blocker.

## Per-commit index completeness
Mostly workable for 0a-0c (named files and functions all exist). Gaps:
- Q1. Commits 1-4 point only at "Closure 4 ..." sections plus code. They do not point at the closure 1-3 / body sections that still govern row schema, state precedence, eligibility tables (closure-3 money comparability table, lines ~340-347), the group-key amendment (line 355), the mock ledger/measurements, or required-test lists. Closure 4 says it only supersedes conflicting parts, so a builder told to "read only these" would miss them. Add those section names/line anchors to rows 1-4 (group key to row 3; mock ledger to rows 2 and 4).
- Q2. Row 1 does not list the "W1 day source / pinned facades" and "Wire, token" sections although Evidence consumes both; row 3 omits "Money and proof corrections". Row 0a lists "refusal" but the refusal wrapper lives in the new API file (row 1), so 0a only needs the cursor.
- Q3 (nit). Closure 4 cites main `a0741022`; worktree main is `c50ea24b` (plan merge). Confirm a0741022 is an ancestor; seams matched, so harmless.

## New questions
1. B5 source of the cold/EV Site evidence cutoff (min of estate known_at and what field?).
2. S13 panel titles for the two new registry nodes.
3. Q1/Q2 index additions above (planner edit, no decision needed from owner).
