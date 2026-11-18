# Review CH-5b2: "Why?" trace, why routes, five stored chain routes with ETag/304

- Reviewer: fresh Claude (independent; did not author the slice). 2026-11-05.
- Branch `task/CH-5b2-why-trace`, worktree `AssetOpsV1-ch5b2`, head `ec2e02edc`. Base = merge-base with main =
  `9b8fb6498` = plan2 HEAD (main is an ancestor of HEAD). Diff `git diff 9b8fb6498...HEAD -- ':!.agent'`, 18 files.
- Judged against: build sheet CH-5b (§0, R1-R4, Revision OWN-CH5c, §2.1-§2.3, CH-5b2 unit, CH5b2-R Q1-Q11, SCOPE-1),
  CH-5c §8.8 #5, mock `frontend/mockups/v70/index.html:411-438`.

## Verdict: REVISE (one Medium; a documentation and label fix round, no code logic change)

The server logic holds: no stale 304 or 200 path found, `trace_facts` is one SELECT and asserted, every node except
`row_state` carries real ids, the ruled copy is in place (one guard-forced word aside), the heredoc append is clean, and
the merge with CH-9b1 is textually clean. What blocks is that the MOCK DEVIATION labelling, which §2.3 and Q9 require, is
incomplete. After that fix, this reviewer would accept, once the Architect confirms KD-3 below.

## Findings

### M1 (Medium, acceptance gap): MOCK DEVIATION list and two labels missing
- §2.3: "Each line is a MOCK DEVIATION candidate ... The packet lists them old (mock) → new." The packet
  (`.agent/review-packet-CH-5b2.md` KD-4, line 54) only points at `index.html:430`. It does not list the deviations.
- CH5b2-R Q9 rules the estate `would_change` pick ("the first Site ... that has a non-'New readings' line") **is** a MOCK
  DEVIATION. `backend/assetops_backend/chain/why.py:265` carries no label.
- The estate `evidence_label` is `None` (`why.py:272`), while the mock's `pf:` entries all carry one ('Renewable evidence',
  'Risk findings', 'Estate evidence'). No ruling covers this and nothing labels it, so CH-5b3 has no server label for the
  Portfolio link.
- Fix: (a) add the old→new table for every `WHY_TEXT`/`MEASURE_LABEL` line to the packet (MD-CH5b-1). (b) Add a
  `MOCK DEVIATION (CH5b2-R Q9)` comment at `why.py:265`. (c) Either label the null estate `evidence_label` as a MOCK
  DEVIATION (frontend owner CH-5b3) or give it a `why.estate.evidence` template, as the Architect chooses.

### Architect confirmations (packet top items; this reviewer's technical view)
- **KD-3 "Critical supply served"** (`vocabulary.py:183`) replaces the ruled "Critical load served". I verified the
  cause: `frontend/src/test/productVocabulary.json:56` forbids `load` ("unexplained abbreviations"), so the ruled string
  would fail guard V. "Critical supply served" passes and keeps the meaning. Technically sound, but it is a change to a
  ruled literal, so it must not merge until the Architect records the ruling.
- **KD-4 estate `say` fallback:** correct as ruled. The Portfolio card headline is computed in the browser
  (`frontend/src/estate/PortfolioOutcomes.tsx` card rules, "labelled keep → CH-6"). The server summary carries only the
  per-Site row `headline` (`site_outcomes/read.py:586`). Q9's own "otherwise" branch therefore applies, and it is
  labelled (`vocabulary.py:172`). Nothing to add upstream in this slice.
- **KD-5, the 304 runs admission and the Site-set read:** correct, and it should stay that way. The route admission
  (`board_site`, `opened`/disclosure; estate `admit`) must run before a 304, or an unadmitted caller could revalidate.
  The store's (a) is the watermark, then `c.sites`, then one `chain_response` lookup. That lookup is the "one indexed
  live-row lookup" of §8.8 #5, and the L2m test pins it (`len(store) == 3` for the Site routes). Recommend that the
  Architect amend the §8.8 #5 wording to "admission + watermark + Site set + one live-row lookup" so that it matches.
- **KD-6 `threads_through`** (`site_chain.py:104`): bounded correctly. It keeps occurrences with `episode_start < hi` and
  events with `effective_day <= day` visible at the cutoff, so it carries no thread history from after the window end.
  The cost is that threads CLOSED or WITHDRAWN long before the window also produce `thread`/`finding` nodes. The text is
  still board-anchored (Q8: a line is emitted only when the board row lists the item). See L5 for Actions.

### Low
- **L1** `chain/adapters/postgres_chain_read.py:145` `_EPOCH =datetime(...)`: an edit slip removed the space (the line
  was `_EPOCH = datetime`). Cosmetic. Restore it.
- **L2** `chain_api.py:91` `_done` adds `Cache-Control` only on the success path. The 422/404/503 refusals raise out of
  `perf.route`, so they carry no `Cache-Control: private, no-cache`, although §2.2 says "every chain and why response".
  Low impact (no `Last-Modified`, so no heuristic caching). Fix with a `try/finally`, or accept it and note it.
- **L3** `why_trace_ms` (`perf-budgets-v1.json`, `test_ch5b_why_postgres.py`) times only `trace_facts` + `why.trace`.
  The trace-specific `threads_through`, `actions_of` and the verification read for the related ids (`why.py:227-250`)
  are outside the timer. The packet says "shared Site chain reads excluded", but these are not shared reads.
  `measured_by` is set and the budget value is unchanged; the measurement is a little narrow.
- **L4** `_TRACE_FACTS` (`postgres_chain_read.py:133`) does not apply `_FINDING_HEADS`' `finding_merge` exclusion. A
  superseded Finding reached through a thread occurrence gets a `finding` node that the board would not show. Its ids
  are still real.
- **L5** Actions in the trace are bounded by `k`, not by the window end (`actions_of`, `why.py:245`). This matches the
  board's own `in_hand` (`site_outcomes/board.py:764`), so the text agrees with the board. But for a past day read live,
  R3 `would_change` and the `action` nodes can reflect an Action agreed after that day. Architect awareness only.
- **L6** KD-8: a one-day NOT_EXPECTED window renders "0 of 0 days checked". No ruled copy exists, so this needs a ruling
  before CH-5b3 shows it.

## Checks run (by this reviewer)

| Check | Result |
|---|---|
| L0 + scoped: `test_ch5b_why.py`, `test_ch5a2_contract/refs`, `test_ch5a2b_claims`, `test_out_b4_route`, `test_ch5c_store_off`, `test_ch5c_env_parity`, `test_ch5c2_clock_guard`, `test_out_b2_vocabulary` (guard V), `tools/checks/test_chain_coherence.py`, `tools/checks/test_perf_budget.py` | **311 passed**, 21 s |
| Postgres via `tools\run-host-tests.ps1` (DB 127.0.0.1:55432 `assetops_test`): `test_ch5a2_chain_api_postgres.py` (the refactored chain routes) | **6 passed**, 29 s |
| Ad hoc probe (scratch, not committed): Site why on COLD-LAB-001 / EV-LAB-001 × 4 categories, with no window and with a week window | all 200 (cold/EV windows with null `to` do not crash `threads_through`). KOBO with no `date` fails only on the L0 fixture's `db_today` guard, a fixture limit |
| Guard A `tools\check-architecture.ps1` (ASSETOPS_GUARD_PYTHON set) | PASS |
| Guard W `tools\check-agent-workflow.ps1` | PASS |
| Estate guard self-tests `tools/checks/test_estate_guard.py`, in 5 `-k` parts (1 / 4 / 5 / 3 / 2 tests) | **15/15 passed**. Parts: 78 s, 184 s, 379 s, 408 s, 175 s, about 20.4 min in total. The suite needs about 20 min, so it cannot finish under one 10-minute cap. This explains the builder's kill, and it is not a regression from this slice |
| `git merge-tree --write-tree HEAD task/CH-9b1-opportunity-actions` (`c43042ff0`) | clean, exit 0, no conflicts |
| `git diff --check` over the diff | clean |

## Specific checks

- **No stale 304/200.** The 304 comes only from `row is not None` after `c.lookup(route, key, W, version, now)`. That
  lookup is the CH-5c live-row lookup (`valid_until > greatest(...)`), and the tag already includes `valid_until`
  (`response_store.py` `etag`). `compose_only` returns before any lookup with no ETag. Store off gives
  `responses is None`, so `compose()` runs directly with no ETag. A body that was never stored (race, unstored, failure)
  carries no ETag. `tag_matches`: strong comparison, a list, `*`, and `W/` never matches. A false match is impossible;
  the only cost is an extra 200. Tests cover each case.
- **Key coverage.** The Site routes key on Site, domain, the derived `day/from/to/known_at/pin` and `category`. The
  thread route keys on `from/to/known_at` and the thread id. The estate routes key on `parsed_key` (every scope field
  after defaulting), the admitted Site set and the raw `category`. Every input the bodies read is in the key or in W.
  `finding`, `finding_revision` and `finding_revision_evidence` are in `config/chain/watermark-inputs-v1.json:47-55`.
- **`trace_facts`.** One statement: the evidence count is a correlated subquery. It is memoised under
  `chain.trace_facts` (`read.py`). L2m asserts exactly 1 `finding_revision_evidence`+`LATERAL` statement per request
  and a ledger count ≤ 1.
- **Trace ids.** `measure_day` ids are composite snapshot keys (`{day}/{measure}/{subject}`), built from stored
  natural-key fields. `analytic`, `finding`, `thread` and `action` ids are stored uuids. Q3 is asserted (L0 and L2m).
- **Copy.** Every `why.*` string matches §2.3 and CH5b2-R Q6/Q7/Q9 verbatim. The only change is KD-3. Guard V passes on
  every formatted template.
- **`why_trace_ms`.** `measured_by` is set, the limit is still 50, and `test_perf_budget.py` is updated (see L3).
- **W6 module list.** The diff adds exactly 2 alphabetised lines (`chain.why`, `chain_api`). `test_ch5c2_clock_guard`
  passes over the grown list (0 clock violations in either module).
- **Heredoc append to `vocabulary.py`.** The committed blob has LF endings throughout, valid UTF-8 (`·`, `→` intact, no
  mojibake) and no trailing whitespace. The diff is a pure append at the end of the file. The module imports, and its
  tests pass. No corruption.
- **CH-9b1 traps.** CH-9b1 changes `actions_of`'s origin match (opportunity origins) and adds
  `origin_opportunity_id` to `_SITE_ACTIONS`. `why.trace` already tolerates occurrences with no `finding_id` (an
  opportunity-only thread gives a thread node, no Finding line, and `unmatched += 1`). Migration 0051 is lane 2 only, and
  CH-5b2 adds no migration.

## Not verified (honest gaps)

- L2m `test_ch5b_why_postgres.py` was not rerun (25-minute template rebuild, excluded by the dispatch). Its evidence
  (median 10.01 ms, D4/D11 reached, ACT-K1 verification, 304 statements) predates the main merge, and the packet says the
  template is stale after the `main.py` import-line merge.
- W6 and `chain_response_probe fresh` on the `ch5b2` clone (46 requests, 0 unlisted modules, 43/43 fresh equal) were not
  rerun; they need a clone and a settle.
- The full backend suite was not run (dispatch and demo-sprint policy). No frontend in this unit.
- The merged CH-5b2 + CH-9b1 tree was not tested. Whichever merges second should run `test_ch5b_why.py` and the
  `test_ch9b1_*` files on the merged head.

## Residual risk not in the packet

- KD-7: the Cold-tag-unchanged half of `late_fill` remains covered only by CH-5c tests, and L2m checks the tag change on
  the Site chain route only, not on the why route. The why route shares the same W and key path, so the risk is low.
- The estate why composes N Site boards plus N traces per miss (`chain_api.py` `_estate_why`). It is not on a perf
  budget. CH-5b3's `perf_budget.py` report mode should include `/api/estate/chain/why`.

## Coordinator verification (fix round 1, 42174a0ee) — ACCEPT
- M1: estate `would_change` and `evidence_label` carry MOCK DEVIATION labels (Q9, CH5b2-R2); packet has the mock→new table. Diff limited to labels, `_EPOCH` spacing, and `Cache-Control` on refusals (L2, asserted in a test). No logic change to store/ETag paths.
- Builder: 195 passed incl. guard V vocabulary; guards A, W pass. L2m not rerun (template stale; evidence predates main merge) — the second of CH-5b2/CH-9b1 to merge runs `test_ch5b_why.py` + `test_ch9b1_*` on the merged head.
