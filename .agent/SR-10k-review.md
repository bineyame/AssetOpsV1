# SR-10k review: Kisiwa fuel-check nights over the date range

Reviewer: fresh Claude reviewer (did not author). Branch `task/SR-10k-kisiwa-fuel-nights`, head 1cebb2865, diff `git diff $(git merge-base HEAD main) HEAD` (base 2023addb9). Spec: rev 10b.4 SR-10k, 10c/10d; D-SR.9, D-SR.34, D-SR.45, D-SR.55.

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. Two Low notes, neither blocking.

## Checked
- **Two forms and the mixing refusal** (`fuel_balance_api.py:106-125`): a `T` in either value selects the instant form, and the docstring names both forms. A mixed pair is parsed as instants, so the date half fails `_instant` and returns 422 `INVALID_WINDOW`. `test_mixing_the_two_forms_is_invalid_window` pins both orders. The date form and its `FUEL_BALANCE_RANGE_INVALID` refusal are unchanged (stub test plus K5 Postgres B2).
- **window_days, max 31** (`night_read.py:91-96`): the read uses `chain.read.window_days(from, to, tz)`. An empty result or more than `MAX_NIGHTS` raises `INVALID_WINDOW`. The stub pins 31 days as OK and 32 as refused, and pins the UTC-midnight and Site-local-midnight frames. The Postgres test pins both frames, the empty range, the one-bound refusal and the no-param default.
- **known_at on list and detail** (`MiniPerformance.tsx:1598-1611`, `MiniFuelNights.tsx:334`, `fuelBalanceClient.ts:168-171`): the range's `known_at` goes on both requests. Without one, both URLs are byte-identical to before. A vitest pin covers the client URLs and the page calls. It is built from `rangeWindow` plus `known_at`, which gives the same parameters `rangeParams` would.
- **Out-of-range `?night=`**: the named night is opened. The list stays on the range, the line "This night (4 Nov) is outside the selected date range" is shown, and the selector gets a synthetic option for the night. Nothing writes the address, so the range is not widened. A night that does not exist reaches `getNight`, which keeps the NIGHT_NOT_FOUND refusal.
- **Empty range**: `[data-fuel-nights-empty]` reads "No fuel checks in this date range" and no night is read. Pinned.
- **Old night-date callers**: `getNights(code)` and `getNight(code, date)` with no extra argument produce the old URLs (pinned). The K5 Postgres file passes unchanged.
- **D-SR.9**: the list follows the address range, and the single night stays the drill-in. The range day table for the Kisiwa nights is SR-5's scope (D-SR.11), not this card. `rangeMatrix.ts` does not exist on this base, so there is no matrix row to update.
- **Tests are not vacuous**: the stub asserts the `(lo, hi)` the store receives and the exact dates returned. The vitest cases assert exact call arguments and URLs. The Postgres test seeds four nights and asserts exact subsets.
- **Stray files**: the diff holds 10 files, which are 9 source/test files plus `.agent/SR-10k-packet.md`. There are no ignored, cache or build files.

## Findings
- **Low, `frontend/src/sites/MiniFuelNights.tsx:331,346-349`**: `outside` does not check whether a range is set. With no range in the address, the list is the latest 14 nights. A `?night=` older than those now shows "outside the selected date range" when no range is selected. Before this change it silently opened the latest night. Per D-SR.30, links normally carry the range, so this is an edge case. Fix: pass a `ranged` flag from `MiniFuel` (`shared.status === "set"`) and show the line only when it is set.
- **Low, `frontend/src/sites/MiniFuelNights.tsx:342`**: with an empty range and a `?night=` link, the empty state wins and the named night is not opened. D-SR.55 Q4 says a `?night=` link always opens its night. Fix: return the empty state only when `asked` is null. Otherwise render the outside-range line and the detail under the empty-state line. This is an acceptance edge, not a preference, but it is unlikely on the demo path.

## Checks run (head 1cebb2865, worktree /opt/assetecon/AssetOpsV1-sr10k, branch PYTHONPATH)
- `pytest test_sr10k_fuel_nights_range.py test_k5_fuel_night_text.py`: 33 passed (the packet says 32 before the fix round; the mixing test added 1).
- Postgres `assetops_sr10k_test`: `test_sr10k_fuel_nights_range_postgres.py test_k5_fuel_night_api_postgres.py`: 7 passed, 0 skipped, 19.9 s.
- `npx vitest run src/sites/__tests__/miniFuelNights.test.tsx src/shell/__tests__/sr2RequestUrls.test.tsx`: 2 files, 33 passed.
- `npx tsc --noEmit`: clean (exit 0).
- check-all: not run (the coordinator runs it). Layout evidence: not applicable, since the slice adds one line of prose and one select option.

## Residual risk
- Range bounds that are neither UTC nor Site-local midnights use `window_days`' frame rule. A 31-day window that is not aligned can name 32 days and is refused. The shell writes only UTC-midnight bounds, so the bar cannot produce one. The packet already names this.
