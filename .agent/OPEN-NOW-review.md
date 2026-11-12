# OPEN-NOW review (Claude reviewer, 2026-11-12)

Reviewed: `task/OPEN-NOW-work-read` at `a2e792ddb`, diff vs merge-base `8a4b4fe4d`, against card OPEN-NOW (sequence doc rev 3 l.89-94) and the portfolio-layout proposal ~l.578-581. Packet `.agent/OPEN-NOW-packet.md`. The worktree was later merged with main (`d8733388b`). That merge does not touch any OPEN-NOW product file.

**Verdict: ACCEPT WITH NOTES**, conditional on the Architect's answer on Actions and on the packet's Postgres list passing.

## Actions "open" definition (flagged, not ruled)
- The card says the counts are "by work kind: requests, actions, as the Work pages show them", with the example "Open now: 3 requests, 1 action".
- The code counts **incidents and maintenance requests only**: `OPEN_STATES = {"OPEN", "IN_PROGRESS"}` on the reduced W4 case state (`contracts/assetops_contracts/work_open_now.py:15`, `work/open_now.py:23-29`).
- **No Actions are counted**, and the Site Actions subtab gets no line. The packet discloses this as deviation 1: the Action index has no `known_at` cutoff, and its lifecycle (ACCEPTED, PENDING, APPLIED) has no "open" state.
- The incidents count is an addition the card did not name.
- This is an acceptance gap against the card wording, pending the Architect's definition.

## Findings
- **Low.** `work/global_index.py:537-542`: one case that cannot be reduced, anywhere and at any date, now turns the whole global incidents or maintenance list into `WORK_STORE_UNAVAILABLE`. Before, only cases inside the window could. The Site list (`site_index.py:390`) is likewise exposed to out-of-window chains.
- **Low.** `global_index.py`: the open count uses `gx.imported_sites(tenant_id, request.to)`, the list's Site scope. A Site imported after the window end is left out, even though the line says "whatever the dates".
- **Low (test).** `test_open_now_postgres.py`: `page_two` is a `limit=1` read of an empty window with no cursor, so the cursor page-two path (`site_index.py` known_at from the cursor) is not exercised.
- **Low.** `open_now.py:40-46` and every list read run one events query per case across all admitted Sites, on page one and page two alike. Fine at demo scale; the packet names it.
- **Note.** The shared plan2 venv resolves `assetops_contracts` from `C:\Users\assef\Bineyame\AssetOPsV1\contracts`, which does not have `work_open_now.py` (`ModuleNotFoundError`). Any runtime on that venv needs the branch's `contracts` on its path. This is environmental: the same drift already breaks `V4_CHANNEL_MAPPINGS_BY_PROFILE`.
- **Note.** R338 is the cold-work window row, and S17 is absent. The packet's statement on the register checks out.

## Checks I ran
- No DB. With `PYTHONPATH` set to the branch's contracts: imports and wording all pass. The sentences are "Nothing open now", "Open now: 1 incident, 3 requests, whatever the dates", and the summed wire is correct.
- `tsc --noEmit` on `d8733388b`: exit 0.
- `check-architecture.ps1` and `check-agent-workflow.ps1` on `d8733388b`: both passed.
- **Not run:** Postgres (lane rule). The packet itself lists 8 files still to run, so the backend window, known_at and Site-scope claims are unverified. Also not run: vitest and build (sandbox), and layout evidence (the packet says not run; it is a plain `<p>`, so the risk is low).
