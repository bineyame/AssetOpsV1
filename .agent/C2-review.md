# E4-C2 review: prebuild follows the story calendar (D-E4.1)

Reviewer: fresh Claude (Opus), read-only. Diff: `main...task/E4-C2-prebuild-follows-calendar` (base 1f40cca0d, head 573e331c6).

## Verdict: ACCEPT WITH NOTES. M1 must be fixed on the branch before merge, because Medium findings block.

## Findings

1. **Medium (PF1 gap): the Kisiwa Findings link's board read is not warmed on a fresh build.** `tools/demo_combined.py:388-397`
   maps only `/portfolio`, `/findings` and `/sites/{code}[/ev]`.
   - The link "KISIWA-001 Findings, story nights S-9d to S+1d" (`/sites/KISIWA-001/findings?from=S-9d&to=S+2d`) opens `SiteEarlyWarnings`.
   - That panel issues the stored request `outcome-board?date=miniBoardDay(to)`, which is `date=S+1` (`frontend/src/shell/SiteAnalyticsFrames.tsx:584`, `frontend/src/sites/EarlyWarnings.tsx` `miniBoardDay`).
   - The request is covered only by the S+1..last loop. On a fresh build, Kisiwa's last date is its last story night, which is S (computed on the E4 build: 2026-11-07). So the request composes on first open, and PF1 ("every API request behind every links row") fails for that row.
   - Fix: map `/sites/{code}/findings` links to the board request their page issues: `date=miniBoardDay(to)` for MINIGRID Sites, and the `from`/`to` window for Cold and EV. Add a test.
2. **Low (PF3 and cost: not made unreachable by C2; escalate to the Architect).**
   - On the E4 build's own files (`AssetOpsV1-e3/var/polish_client2`), the new list is 39 requests plus 3 scope-ids, 42 in all, against 23 before: 22 Kobo boards, 4 Cold, 3 EV, 3 Kisiwa, and 10 estate requests.
   - A true no-data tick is all hits, at about 50 ms each (`chain/prebuild.py` docstring). That is roughly 2-20 s, so PF3 is reachable as far as C2 is concerned.
   - However, the E4 serve-loop logs (`logs/39..99-prebuild.log`) show 14-15 of 23 requests *stored* on every tick: the 10 estate requests plus about 5 boards, probably Cold and EV. If the E4 rerun classes those as no-data ticks, PF3's `stored: 0` fails independently of C2.
   - With C2, such a tick composes about 17 requests at about 9.7 s each, roughly 165 s against about 145 s now.
   - The first prebuild after each drain composes all 42 requests, about 5-6 min against 116 s, which adds roughly 10 min or more to a prepare.
   - Recommendation: the Architect decides before the E4 rerun whether these per-tick restores are data arrival. The C2 card needs no change.
3. **Low: the file write is not atomic, and malformed input surfaces as differing errors.**
   - `demo_combined.py:700` uses `write_text`. A separate add-dates process and the serve loop both rewrite the file while the other's prebuild child may read it.
   - A torn read raises `ChainConfigError` (`file_chain_config.py:111-113`), so that prebuild fails loudly, and the next tick recovers.
   - When the variable names a missing file, the read fails loudly, which is acceptable for a deployment input.
   - A wrong schema raises `ValueError`, and missing keys raise `KeyError`, not `ChainConfigError`.
   - Fix: write to a temporary file and then `os.replace`.
4. **Low: a stale docstring.** `backend/assetops_backend/chain/prebuild.py:3` still says the list is `config/chain/prebuilt-routes-v1.json`.

## Seams (verified by reading the code)

- **`code_version`:** the file sits at `<work>/prebuilt-routes.json`. That is outside `tree/`, so it is not in the hashed `backend`, `config`, `host` or `contracts`, and it is outside every `F` root (`config/chain/file-inputs-v1.json`).
- **Setting lists:** the variable is in neither `COMPOSER_ENV` nor `SERVE_KEYS`. The test includes a control that does move `code_version`.
- **API process:** it never reads the list. Only the prebuild child and the tools do.
- **Re-reading:** the file is re-read on every call, as the card intends. `paths()` reads it twice per run, which is harmless.

## Deviations settled

1. **Finish-rows stub (`test_demo_combined_finish_rows.py:1208`):** legitimate. `performance_and_prebuild` now calls `self.write_prebuilt_routes()`, so the fake needs the attribute. The assertion is unchanged, so this is not a weakening.
2. **Variable set only when the file exists:** OK. It falls back to the config default, as the card specifies.
3. **Kobo S board always added:** harmless, because duplicates are removed.
4. **EV warmed every day:** follows the card. On the E4 data, EV's last date (11-03) is before S+1, so no requests are added today.
5. **Heredoc rename:** a process breach, with no stray result. `tools/demo_combined.py` is +127/-0, all additions. `git diff --check` is clean, no CR was introduced, and the eol attributes are unchanged (i/lf).
6. **Fresh prepare needed:** matches D-E4.5.

## Routes and wasted work

- Every route in the list is either a links row or a board from S+1 to the Site's last date, as the card asks.
- Mapping and query encoding are checked:
  - the Portfolio and Findings stored keys are parsed keys, so the generator's explicit `lens=all` and `state=all` give the same key the frontend's request does;
  - the EV page renders `OutcomeBoard` with the link's window.
- No wasted routes beyond what the card mandates.
- DS-1a covers its beats except as in M1: Portfolio and Findings for the week, the story boards, Kisiwa S-5d and S, and the step-7 Kobo yesterday board.

## Checks

- **Targeted pytest: NOT RUN.** Free RAM stayed at 2.37-2.47 GB for more than 10 minutes, below the 2.5 GB gate. The packet's numbers (43 / 63 / 122 passed) are unverified by this review.
- **Generator dry run on the E4 work files:** read-only, no database. It gave the 42-request count above.
- **Not run:** `check-architecture.ps1`, the full suite and `prepare`.
