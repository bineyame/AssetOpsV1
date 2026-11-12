# SR-4a + SR-4b review (fresh Claude reviewer, 2026-11-12)

Scope: `59acd65c4` (4a) and `59bccda4d` (4b) on `task/SR-4-site-range`; later commits read only to say whether an issue was fixed (HEAD `ebef46a3a`). Spec: rev 8 §8.1-8.5, rev 10d, D-SR.1-8/40-42. 4c and the fix rounds are another reviewer's.

## Verdict: REJECT until H-1 is fixed (it needs an Architect ruling first)

Otherwise 4a/4b are sound. The codemod changes imports only, and links that are not Site links behave exactly as before. The safety net uses the order the spec gives. `pageDay` and the edge stepping match the spec. The guard catches real violations.

## Findings

**H-1 (High, needs an Architect ruling; the code follows rev 8 §8.2 as written). Short ranges on Renewable, and one-day ranges on Service, Backup and Fuel, are refused.**
- **Code.** `frontend/src/sites/miniDepthClient.ts:342` (Renewable: the window passes through when it spans at most 5 days). `:384` (Service, also used by Backup/Fuel: it passes through when the span is exactly `DAY_MS`).
- **Tests.** Both are pinned in `frontend/src/ui/__tests__/sharedRange.test.tsx:31-40, :56-63`.
- **Why the server refuses.** The window goes to the server as the bar's UTC-midnight bounds. `backend/assetops_backend/mini_depth/read.py:112-138` (`hour_windows`, which `_row_hours` also calls at :565) accepts only exact Site-local midnights for renewable, and exactly one local clock hour for service, fuel and backup. Anything else is `INVALID_WINDOW`.
  - Kobo is Africa/Addis_Ababa and Kisiwa is Africa/Dar_es_Salaam (both +3).
  - So the bar's own "Yesterday" preset, or any custom 2-5 day range, opens Renewable as a refusal.
  - "Yesterday" also opens Service, Backup and Fuel as a refusal.
  - A one-hour story address does the same: `carryRange` rounds it to one UTC day, so the Renewable tab gets that day.
- **Why it is a regression.** On main these tabs opened with no range (today's local day, which is valid). 4a now carries the range into them. The rev 8 rationale "exactly one day (story links)" does not hold, because the server never accepts a one-day service window.
- **Still present at HEAD.** `miniDepthClient.ts` is unchanged since 4b, and SR-7/SR-8 are not on main.
- **Possible fix (Architect to rule).**
  - Renewable: read a UTC-day range of 5 days or fewer as the Site-local days of those UTC dates (the D-SR.45 Q-J1 `window_days` rule: `localDaysWindow(tz, localDateOf(range.from), n)`). Pass the address through only when its bounds are already local midnights.
  - Service, Backup and Fuel: drop the one-day pass-through, so a one-day range gives the 12:00 local hour of `pageDay`.
  - Re-pin both tests.

**M-1 (Medium, fixed later in 4c). 4b on its own is not honest and has a failing test.**
- At `59bccda4d`, `shell/__tests__/sharedRange.test.tsx` fails 1/23: "the label is true per route class, including a demo story link".
  - Bare `/sites/MG-002` now gets the safety-net range.
  - The bar then says "All pages" over the one-day mini board. The test expects "This page's own dates".
- The packet's 4b test list leaves this file out.
- Rev 8 §8.4 plans to merge a, b and c separately, with "every commit leaves the screen honest". That does not hold for a or b alone.
- At HEAD the file passes 24/24.
- **Fix:** merge 4a+4b only together with 4c.

**L-1 (Low, still present at HEAD). The safety net can add a second `known_at`.** `frontend/src/shell/SharedRangeBar.tsx:124-132`.
- The previous range (which may carry `known_at`) is copied, then every address parameter is appended.
- So a bare Site address that names its own `known_at` ends up with two, which `readSharedRange` treats as invalid. The D-SR.41b correction link `…?known_at=<K>` is one way to reach this.
- This is the same defect D-SR.42(d) fixed in `withRange`. The safety net should use the same per-key rule: the address's own `known_at` wins.

**L-2 (Low, hardening). The guard only matches double-quoted named imports.** `tools/checks/site-links-carry-range.ps1:20`.
- It misses single-quoted imports, `import * as`, re-exports, `.ts` files and raw `<a href="/sites…">`.
- None of these exist today (checked by grep).

**L-3 (Low, test gaps).**
- Nothing tests that the previous range wins over `day`. It is correct in the code, but only steps 2 and 3 are tested on their own.
- `siteRangeCarry` gives Kisiwa the Kobo fixture, so Kisiwa's own tab row (Fuel) is never opened.
- The Kisiwa `finding-windows/<day>` request is not pinned.
- Every read except the Site detail answers 503, so links inside loaded content are not tested at runtime. The spec allows this.

**L-4 (Low). Service and Renewable measure the raw `from`/`to` strings, not `readSharedRange`.**
- A day-form address that `readSharedRange` accepts gives the wrong span. For example, `from=2026-11-08&to=2026-11-08` has span 0, is sent as it is, and is refused.
- This needs a hand-typed address. Behaviour before SR-4 was the same.

## Checked and fine
- **Codemod.** 97 `.tsx` files are touched. Every non-test hunk is an import line (`Link` removed from the `react-router-dom` import, `RangeLink as Link` added); no other line changed.
  - `tsc --noEmit` is clean on a `git archive` snapshot of `59bccda4d` and on HEAD.
  - No relative `Link` targets exist.
  - `carryRange` returns targets that are not Site paths, and object targets with no pathname, unchanged. So Foundation, Prices, record and global links are unchanged, except that Site targets now carry the range, as D-SR.2 and 10d row 1 intend.
- **Safety net.**
  - The order is previous in-app range, then 7 days ending on `day`, then `entryRange()`.
  - It covers Overview, Performance(/x), Findings, Evidence, Work(/incidents|/maintenance), Financials(/assumptions|/scenarios), Health and `/ev/...`.
  - It leaves Prices, Foundation, record pages and the index alone, and leaves an invalid range alone.
  - The outlet is mounted once in `OperatorShellLayout`, so the `useRef` survives navigation.
- **Day defaults.**
  - `pageDay` returns day, else `range.to`, else today.
  - The Overview sends `date=<range.to>`, and the backend's legacy branch accepts `date`.
  - Dispatch and the Kisiwa night window use the same `day`.
  - `todayUtc` is deleted.
  - The remaining `toISOString().slice(0,10)` hits format instants, except `SiteAnalyticsFrames.tsx:460` and `workClient.ts:192`, which the packet explains.
  - The edge text is right at the first and last day of the range, and stepping outside the range is unclamped.
- **Guard.** It is not vacuous: run on its own on the snapshot, it passes the 4b tree and fails when main's pre-4a `operatorSiteTabs.tsx` is restored (1 failure). The self-test fixtures cover plain, aliased, multi-line and exempt imports. It passes at HEAD.
- **D-SR.9.** Link carrying is exercised for mini (Kobo and Kisiwa), Cold and EV on every tab. The 4b day defaults are mini-only, as the spec intends; Cold and EV read the window. H-1 breaks Renewable, Service, Backup and Fuel on Kobo and Kisiwa (mini) for short ranges.
- **known_at.** It travels on links and through the safety net. The duplicate in `withRange` (4a) was fixed by D-SR.42(d) and is pinned in `rangeLink.test` 12/12. The safety-net duplicate is L-1.

## Checks run
- vitest at `59bccda4d` (snapshot):
  - `rangeLink` 8/8
  - `siteRangeCarry` 10/10
  - `ui/sharedRange` 7/7
  - `shell/sharedRange` **22/23 (1 fail, M-1)**
  - `s5SiteWindowOverview` 69/69
- vitest at HEAD `ebef46a3a`:
  - `rangeLink` 12/12
  - `siteRangeCarry` 10/10
  - `ui/sharedRange` 7/7
  - `shell/sharedRange` 24/24
  - `s5SiteWindowOverview` 69/69
- `tsc --noEmit`: clean at both revisions.
- Guard: run on its own, passes at both revisions and fails on the pre-4a file.
- Not run: check-all and full suites (the coordinator runs them); the DB and live-serve checks in the packet's pre-flight (f). H-1 is shown from the backend source, not from a live request.

## Re-review (fix round 2) - ACCEPT WITH NOTES

Reviewed b3ed3db95 (fix round bd1670482..b3ed3db95; H-1 itself landed in bd1670482). Rulings D-SR.57, D-SR.59.

Verified:
- H-1 closed per D-SR.59 in `miniDepthClient.ts`: Renewable passes through only exact local midnights 1-5 days apart, else `localDaysWindow(range.from, n)` for <=5 days, last-5 rule beyond; Service/Backup/Fuel pass through only an exact one-local-hour instant window, "Yesterday" gives 12:00 local of `pageDay`; reversed/unparseable pass-through kept (R313). L-4: ranges measured through `addressRange`/`pageDay`; raw parses remain only in the two exact pass-through checks.
- Contract fixture feeds both sides: vitest `ui/__tests__/sharedRange.test.tsx` and `backend/tests/test_sr4_mini_windows_contract.py` (66 passed, incl. a non-vacuous refusal test). Scratch-copy mutations: the pre-fix client (7f9a0bd9e) fails 14 tests; a tampered fixture value fails the vitest side. The pytest side fails if the server loosens or the fixture window is invalid.
- sr2RequestUrls "Yesterday" pin present and passes; L-1 per-key safety net (`SharedRangeBar.tsx`) + test (exactly one known_at); D-SR.57 `withRange` per-key known_at + `rangeLink` tests (own known_at kept; no-address-known_at adds nothing); Scenarios header rewritten; WindowSpan removed from Service/Backup/Fuel hour views (FocusPicker the sole declarer); MOCK DEVIATION labels added; L-2 guard covers single quotes, re-export, namespace, with self-test fixtures expecting exact flagged set (non-vacuous); L-3 tests present.
- Both re-pins match the rulings: miniRenewableRoutes label "Site-local days 2026-10-16 to 2026-10-20 (Africa/Addis_Ababa)" (D-SR.59 point 2); shell sharedRange withRange adds address known_at (D-SR.57 L3).
- Ran: pytest contract file 66 passed; vitest on sharedRange (ui+shell), rangeLink, sr2RequestUrls, miniRenewableRoutes, siteRangeCarry, miniDecisions: 7 files / 168 passed; `tsc --noEmit` clean. check-all and the full suite not run (as instructed). No stray/untracked files (only ignored __pycache__).

Notes (non-blocking):
- N1 (Low now, Medium for any negative-offset Site; answers the builder's question): yes, a D-SR.9/D-SR.59 defect for -5 zones. Service default hour and the long-range Renewable rule use `localDateOf(tz, <UTC midnight>)`, which lands one local day early (fixture: Bogota "Yesterday" 11 Nov gives service 17:00Z = 12:00 local on 10 Nov; ruling text says 12:00 local of `pageDay`). The short-range Renewable path correctly uses the date string. Fix: use the date string directly (`pageDay`, `range.to`) and regenerate the fixture's Bogota service/7d/30d windows deliberately. The +3 demo Sites are unaffected, but the fixture currently pins the wrong -5 behaviour, so a future correct fix will fail it until re-pinned. Architect should confirm.
- N2: the frontend vitest and the pytest side run independently, so the pair is enforced by the shared fixture, not by one command; acceptable per D-SR.59.
