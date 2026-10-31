# Build sheet LINK-LINEAGE · the board links an Action across basis-only Finding revisions

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-31. Owner, verbatim (`.agent/owner-client-demo-sequence-2026-10-31.md`):
"yes to both, go ahead" (decision 1). Code read at main `15eed62c8` (IDX-GAPS and FIX-S4-DOMAIN merged). Branch
`task/LINK-LINEAGE-board-action` from `15eed62c8`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-link`.
Backend paths are relative to `backend/assetops_backend/` unless they start with `backend/`, `tools/` or `frontend/`.
Effort **0.75 builder day** + one `-Tier all`. This sheet is self-contained.

## 0. Rules that bind every unit

- One narrow board rule. Categories, statuses, placement, Earlier/In-hand lists and every other link stay as they are.
- The rule widens only the Finding→Action join used for the status signal's `applied` flag and for Must-not-harm
  (`site_outcomes/board.py:468-470` `exact_actions`, used at `:477` and `:607`). Nothing else reads it.
- Any revision that is not a pure basis refresh breaks the link. When in doubt (missing revision, failed read), no
  link: today's exact behaviour.
- No frontend change: `must_not_harm` already renders (`OutcomeBoard.tsx`). No wire field, schema or copy is added.
- Do not touch `estate/**` (the estate Finding→Action join `estate/portfolio.py:125-135` stays exact; out of scope),
  `analytics/finding_read.py` logic, migrations, `field/ gateway/ contracts/ simulator/ host/`.

## 1. Code reality

| Fact | Where |
|---|---|
| The join: `a.origin_finding_id == f.finding_id and a.origin_revision_id == f.revision_id`, mini Actions only (`not a.is_domain`) | `board.py:466-470` |
| `applied` on the Finding signal → `PRIMARY_FINDING_APPLIED` (WATCH) instead of `PRIMARY_FINDING_OPEN` | `board.py:477`, `outcomes/status.py:70-79` |
| Must-not-harm needs a linked Action with a verification state other than None/NO_PLAN | `board.py:605-614` |
| Earlier lists join on `origin_finding_id` only, so ACT already appears there (CO-1 note) | `board.py:563-579` |
| Mini Findings = index heads (latest revision); Actions carry their origin revision | `mini.py:473-496`, `:503-531` |
| Cold and EV build only domain Actions (`is_domain=True`, `cold.py:201-205`; EV reuses it, `ev.py:122`), which the join never considers | — |
| Revision history with `transition`, `lifecycle`, `episode {start,end}`, `revision_no`, paged ≤ 500 | `analytics/finding_read.py:570-623` `FindingReadService.history`, `_summary` `:257-275` |
| A BASIS_REFRESHED write already requires an unchanged lifecycle and support digest (bounds included) | `finding_episode.py:617-618`, `:793-794` |
| The service instance exists in `main.py:539` (`finding_reads`) but is not passed to the board | `main.py:615-621`, `site_outcomes/composition.py:47-77` |

**Composers (asked: all three or only where it can occur).** Only **mini**. The rule lives in the shared `board.py`
join, so it is composer-agnostic, but cold and EV never build a non-domain Action, so their `refreshed_from` stays
empty and no history port is added to `ColdPorts`/`EvPorts`. U1 test N6 pins that a domain Action never links.

## 2. The rule (exact)

An Action `a` (non-domain) links to the shown Finding revision `s` of Finding `f` when
`a.origin_finding_id == f.finding_id` and either `a.origin_revision_id == s.id` (today) **or**
`refresh_chain(revisions, a.origin_revision_id, s.id)` is True:

```python
def refresh_chain(revisions: Sequence[Mapping], origin_id: str, shown_id: str) -> bool:
    """True iff every revision after the origin up to and including the shown one is BASIS_REFRESHED with the
    origin's lifecycle and episode bounds. `revisions` = history rows in revision_no order (every page)."""
```
Read from the origin `o` (the row whose `id == origin_id`) to the shown row `s`. **What breaks the chain** (each → False):
1. `o` or `s` absent from `revisions`; `revisions` empty or None (failed/unknown read).
2. `o.revision_no >= s.revision_no` (the same revision is the exact rule; an origin after the shown pin never links).
3. The rows with `o.no < r.no <= s.no` are not exactly `s.no - o.no` contiguous numbers (a missing page).
4. Any such `r` with `transition != "BASIS_REFRESHED"` (SUPPORT_CHANGED, NO_LONGER_SUPPORTED, REOPENED, SPLIT,
   MERGED_INTO, MODEL_REEVALUATED or any other).
5. Any such `r` with `lifecycle != o.lifecycle`, or `episode.start != o.episode.start`, or `episode.end != o.episode.end`
   (compared as the jsonable-encoded strings the port returns).
Revisions after `s` are never read for the decision, so a pinned `known_at` board stays correct.

**Calls (logged):** C1 the chain stops at the shown revision, not the latest, so pins hold. C2 lifecycle and episode
are checked explicitly although BASIS_REFRESHED implies them (the owner's wording; defence against a future writer).
C3 merges/splits always break (different Finding or transition). C4 a failed history read records the port failure
(board PARTIAL, as every other port) and does not link; the default port (tests, fakes) returns None with no failure.
C5 the estate Findings/Portfolio Action join stays exact: the owner approved the board rule only.

## 3. Units (3). Effort 0.75 d

### U1 · Pure rule and the board join · 0.25 d
Files: `site_outcomes/board.py`, new `backend/tests/test_link_lineage.py`.
- `board.py` module level: `BASIS_REFRESHED = "BASIS_REFRESHED"` and `refresh_chain` (§2), pure.
- `FindingFact` (`:115`) adds a last, defaulted field `refreshed_from: tuple[str, ...] = ()` = the origin revision IDs
  for which the composer proved `refresh_chain` true for this shown revision.
- `assemble` (`:468-470`): rename `exact_actions` → `linked_actions`; predicate becomes
  `a.origin_finding_id == f.finding_id and (a.origin_revision_id == f.revision_id or a.origin_revision_id in f.refreshed_from)`.
  Update the two call sites and the `_row` parameter name. Docstring: one line naming D-2026-10-31-board-action-refresh-lineage.
- Tests `test_link_lineage.py` (no DB). History rows built by a helper `rev(no, transition, lifecycle="SUPPORTED",
  start="2026-10-06T14:20:00Z", end="2026-10-06T15:20:00Z")`:
  - P1 r1 origin, r2 BR, shown r2 → True. P2 r1, r2 BR, r3 BR, shown r3 → True. P3 r1..r3 with r3 SUPPORT_CHANGED,
    shown r2 → True (pin, C1).
  - N1 r2 SUPPORT_CHANGED → False. N2 r2 BR with lifecycle `UNCONFIRMED` → False. N3 r2 BR, episode end +5 min → False.
    N4 episode start changed → False. N5 r2 BR, r3 NO_LONGER_SUPPORTED, shown r3 → False. N7 origin absent → False.
    N8 origin == shown → False. N9 origin r3, shown r2 → False. N10 rows r1, r3 only (gap) → False. N11 None/[] → False.
  - Board (fake `SiteFacts` as in `test_out_b1_board.py`): Finding F r2 `refreshed_from=("r1",)`, Action origin (F, r1),
    applied, verification PENDING, with a CHECKED-outside outcome →
    B1 Cost `must_not_harm == {"text": <the board's existing sentence>, "href": action.verification_href}` and the
    primary MG-2 outcome reason `PRIMARY_FINDING_APPLIED` (unless the fake declares a MISSED objective);
    B2 same facts with `refreshed_from=()` → `must_not_harm is None`, reason `PRIMARY_FINDING_OPEN` (today);
    N6 the same Action with `is_domain=True` → no link; B3 Earlier lists are byte-identical between B1 and B2.

### U2 · The history port and the mini composer · 0.25 d
Files: `site_outcomes/mini.py`, `site_outcomes/read.py`, `site_outcomes/composition.py`, `main.py`, tests.
- `MiniPorts` (`mini.py:132`) adds last: `finding_history: Callable[[str, str], list[dict[str, Any]] | None] = lambda f, r: None`
  (Finding ID, shown revision ID → every history row, or None).
- `read.py` `BoardServices` adds `finding_reads: Any = None  # FindingReadService (analytics/finding_read.py:570)`.
  `mini_ports` binds:
  ```python
  def finding_history(finding_id: str, revision_id: str) -> list[dict[str, Any]] | None:
      _open(s.finding_index_gate, site, "finding index gate")
      svc, rows, after = _need(s.finding_reads, "finding_history"), [], 0
      while True:
          body = svc.history(t, sid, UUID(finding_id), UUID(revision_id), after_revision_no=after, limit=500)
          if body is None:
              return None
          rows += jsonable_encoder(body["revisions"])
          after = body["page"]["next_after_revision_no"]
          if after is None:
              return rows
  ```
- `composition.py` `build_outcome_board_service(..., finding_reads: Any = None)` → `BoardServices(finding_reads=...)`;
  `main.py:615-621` passes `finding_reads=finding_reads`. Nothing else in `main.py` changes.
- `mini.py` after `_findings` and `_actions` (around `:340-360`): new pure-ish
  `_lineage(reads, ports, findings, actions) -> tuple[FindingFact, ...]`: for each Finding, the set of origin revision
  IDs of non-domain Actions with the same Finding ID and a different origin revision; when non-empty, **one**
  `reads.call("finding_history", ports.finding_history, f.finding_id, f.revision_id)` per Finding; return
  `dataclasses.replace(f, refreshed_from=tuple(sorted(o for o in origins if refresh_chain(rows, o, f.revision_id))))`.
  No call when every Action matches exactly or no Action points at the Finding.
- Tests (extend `backend/tests/test_out_b2_mini.py` fakes; no DB): M1 exact match → the port is never called;
  M2 refreshed chain → link + Must-not-harm; M3 port raises → `"finding_history" in failed`, read_state PARTIAL, no
  link; M4 default `MiniPorts` without the field → no link, no failure; M5 two Actions on one Finding → one call.
  The real service: M6 feed `FindingReadService(fake_store, dispatch)` whose `finding_detail` returns the N1-N5 shapes
  through the real `history` (so the negatives cross the real reader): no link in each; the P1 shape links.
  `test_out_b4_main_binding.py` / `test_out_b4_imports.py`: `BoardServices.finding_reads` is the app's instance;
  a closed finding-index gate makes the port refuse (PortUnavailable recorded), never a link.

### U3 · Postgres pins, DEMO hand-off, register · 0.25 d + `-Tier all`
- U3a (record first, in the packet): on the `kobo_guardrail` fixture (`test_out_b4_board_postgres.py:360-434`) and
  the e4 `kobo_verified` fixture, record for each board day: the shown Finding revision, ACT-000001's origin revision,
  the history transitions between them, and `refresh_chain`'s result.
- `test_kobo_guardrail_two_board_days`: replace `assert cost["must_not_harm"] is None` (`:433`) with the rule computed
  inline in the test from `GET /api/sites/KOBO-001/findings/{f01}/history?revision_id=<shown>` (an independent
  4-line loop, not `refresh_chain`): chain true → `must_not_harm["href"]` equals ACT-000001's verification href and
  the text names the safeguard outcomes; chain false → None. Add the same check for Day B (the "Day B Must-not-harm
  text and href" left to CO-1 at `:423-425`). Update those comments (lines 391-392, 423-426) to cite this slice.
- `test_out_e4_readback_postgres.py`: every current assertion stays; add `must_not_harm` recorded and asserted by the
  same inline rule. If a fixture's chain is false, the assertion is None and the packet records why.
- Register: R552 note "LINK-LINEAGE merged (board rule); closes when DEMO-SPARSE CO-1's original assertions pass on
  the combined dataset". R552 is **resolved** by the CO-1 run (§5), not by this merge alone.
- `.ai/DECISIONS.md`: append §7.

## 4. Validation tier

| Unit | Tests |
|---|---|
| U1 | `test_link_lineage.py test_out_b1_board.py test_out_c2_board.py test_out_d4_board.py test_idx_gaps_board.py` |
| U2 | U1 set + `test_out_b2_mini.py test_out_b2_vocabulary.py test_out_b4_read.py test_out_b4_route.py test_out_b4_imports.py test_out_b4_main_binding.py test_out_e4_readback.py` |
| U3 | U2 set + `test_out_b4_board_postgres.py test_out_e4_readback_postgres.py test_out_b4_window.py` |

Parallel with COV-PARTIAL (separate worktree): no shared product file. Merge this first; COV-PARTIAL's `-Tier all`
runs after, on main with this slice (one heavy job at a time).
`tools\check-all.ps1` at every commit. **Merge gate: one `tools\run-backend-suite-in-container.ps1 -Tier all`** on an
idle machine (`main.py` wiring and the shared `site_outcomes/` seam). Known failure to ignore: the w301 estate index
`INVALID_CURSOR` (pre-existing on main, `70a68ddb1`). No vitest (no frontend change). Captures: none required; one
1440 px capture of the Kobo board day with the Must-not-harm line is attached by the DEMO-A rebuild (§5).

## 5. Effect on DEMO-SPARSE (CO-1) and the b4/e4 assertions

- **CO-1 is restored to its original text** (`build-sheet-DEMO-SPARSE.md` §5): Cost `must_not_harm` with ACT-048's
  verification href; ACT on the Cost row; no "linked finding outside this view". In `tools/demo_combined_finish.py`
  `co1` (`:139-154` in the `-demo3` tree): delete the re-premised negatives (`:144-148`); assert
  `k["action"] in cost["must_not_harm"]["href"]` and `"/verification?event_id=" in` it; keep `outside == []`; record
  `cost_state` and the MG-2 outcome reason (expected `PRIMARY_FINDING_APPLIED` → Watch, or `OBJECTIVE_MISSED` → Needs
  attention when the declared zero-target objective is missed that day; assert the recorded branch). Return
  `"r552": "resolved: refresh lineage"`. If the recorded chain on day S is not all BASIS_REFRESHED, stop and report.
- b4 restored Day A checks (`:427-433`) keep their moves/checked assertions; only the Must-not-harm line follows §3 U3.
- **Who edits CO-1:** if DEMO-A has not merged when LINK-LINEAGE merges (expected), DEMO-A merges main and makes the
  CO-1 edit before its final `prepare`. If DEMO-A merged first, this slice's U3 makes the edit and runs one
  `-Tier slow` build test (one `prepare`, about 25 min).
- **Dataset rebuild:** the data does not change (a read-time rule). The acceptance runs inside `prepare`, so CO-1 is
  re-checked by DEMO-A's next `prepare`; no extra rebuild is needed if that `prepare` happens after this merge.

## 6. Screens this changes (for the walkthrough)

Kobo mini overview board (`mini`, day S): Cost row gains the Must-not-harm line; Cost status may move from Needs
attention to Watch (applied Action). Portfolio outcome matrix and the Optimize card dot for Kobo follow that board
(the summary reads the board). No other screen. **Mock deviations: none new.** It restores the mock's Must-not-harm
on the Cost row (`v70/outcomes.js:120`), the subject of R552.

## 7. DECISIONS entry (append verbatim)

Decision: `D-2026-10-31-board-action-refresh-lineage` (Architect: Claude, build sheet LINK-LINEAGE). Owner, verbatim
(`.agent/owner-client-demo-sequence-2026-10-31.md`): "yes to both, go ahead". The Site outcome board links a mini
Action to the shown revision of its origin Finding also when every revision after the origin, up to the shown one, is
BASIS_REFRESHED with the origin's lifecycle and episode bounds; any other transition, a missing revision or a failed
history read keeps the exact-revision rule. The link drives only the applied status signal and Must-not-harm; Earlier
lists, estate joins and cold/EV are unchanged. Closes R552 when DEMO-SPARSE CO-1 passes on the combined dataset.

## 8. Pre-flight (one batch in `.agent/LINK-LINEAGE-preflight.md`, then stop)

- [ ] Worktree on `15eed62c8`, clean; never `-ExecutionPolicy`; no BOM (`write_text(..., encoding="utf-8")` / Edit tool).
- [ ] DB names only `assetops_link_<x>_test` in `assetopsv1-postgres-1`.
- [ ] Confirm `grep -n "exact_actions" site_outcomes/*.py` shows only `board.py` (3 hits); any other hit: stop.
- [ ] Confirm `FindingReadService.history` signature and `page.next_after_revision_no` as in §1.
- [ ] Confirm no test fake constructs `FindingFact` positionally past `in_window` (the new field is last, defaulted).
