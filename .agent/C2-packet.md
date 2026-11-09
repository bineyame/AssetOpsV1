# E4-C2 review packet: prebuild follows the story calendar (D-E4.1)

Branch `task/E4-C2-prebuild-follows-calendar` (from main 1f40cca0d). Commits 58f06b99d, f8b95e251.

## Delivered
- **Product** `backend/assetops_backend/chain/adapters/file_chain_config.py`: `load_prebuilt_routes()` reads the file
  named by `ASSETOPS_PREBUILT_ROUTES` when set and non-empty (re-read on every call, since the tool rewrites it), and
  otherwise reads the config default (still `lru_cache`d, in `_default_prebuilt_routes`). The schema is still
  `chain.prebuilt.parse`. The variable is NOT in `COMPOSER_ENV` or `SERVE_KEYS`. The config default is unchanged
  (card item 3).
- **Tool** `tools/demo_combined.py`:
  - Pure `prebuilt_routes(story, days, kisiwa, sites_last_day)` maps the `story_links` rows to API requests: Portfolio
    to portfolio (`lens=all`) plus outcome-summary; Findings to findings (`lens=all&state=all`); each
    `/sites/{code}` and `/sites/EV-LAB-001/ev` board to `/api/sites/{code}/outcome-board` with the same query,
    `URLSearchParams` encoded. It then adds the S and month estate requests and, for each Site, the board for every
    date from S+1 to its last date: Kobo and Kisiwa by `date`, Cold and EV on the whole UTC day. Duplicates are
    removed.
  - `sites_last_day`: for the core Sites, the latest `days.json` day; for Kisiwa, the latest story night or
    DONE/PUBLISHED added night.
  - `Demo.write_prebuilt_routes()` writes `<work>/prebuilt-routes.json`. It runs in `performance_and_prebuild` before
    the prebuild child and at `serve` start before Popen. `serve_env` sets `ASSETOPS_PREBUILT_ROUTES` when the file
    exists.

## Acceptance (card D-E4.1)
| Item | Status | Test |
|---|---|---|
| var set -> file's requests | PASS | `test_e4_prebuilt_routes_source.py` |
| unset/empty -> default | PASS | same |
| `code_version` equal with/without (cache cleared), with a COMPOSER_ENV control that moves it | PASS | same |
| not in COMPOSER_ENV / SERVE_KEYS | PASS | same |
| S=2026-11-07: board.day per story-day link + week/S/month estate | PASS | `test_e4_prebuilt_routes_generator.py` |
| no date outside the calendar or the added dates | PASS | same |
| file rewritten when the last added date moves; written before prebuild and at serve | PASS | same |

## Checks
- Targeted runs (plan2 `.venv`, RAM was at least 2.5 GB before each run):
  - new files, `test_ch5c_env_parity`, `test_demo_combined_links`, `test_ch5c_store_off`: 43 passed;
  - `test_demo_combined_mill`, `test_own_g1_add_dates`: passed (122 with finish_rows before the stub fix);
  - `test_demo_combined_finish_rows`: 63 passed, after the stub fix.
- Non-vacuity check: three mutations made together (the env read ignored, the name added to `COMPOSER_ENV`, the write
  removed from `performance_and_prebuild`) produced 5 failures. All three were reverted with `git checkout`. After the
  revert, 15 tests pass.
- Not run: the full suite or `prepare` (per brief); `check-architecture.ps1`.

## Deviations / notes
- `test_demo_combined_finish_rows.py:1208`: its `SimpleNamespace` stub gained `write_prebuilt_routes=lambda: None`.
  This is test-only.
- The env var is set only when the file exists. A story with no S writes no file, which keeps the CH-5c parity stub
  working.
- The Kobo board on S is always added, because the "Overview, day S" link prints only when `kobo.json` exists, and the
  card's signature carries no `kobo`.
- EV added dates are warmed every day, even on days with no EV session, as the card says. This raises the number of
  requests a prebuild sends.
- Process: one id rename in `demo_combined.py` was made with a python one-off and not with Edit. Line endings were
  checked and are unchanged.
- The existing `tree` snapshot does not contain this code. It takes effect only after the fresh prepare (D-E4.5).
