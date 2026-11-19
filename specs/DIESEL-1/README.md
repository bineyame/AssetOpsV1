# DIESEL-1: split map

`.agent/build-sheet-DIESEL-1.md` (668 KB, 6292 lines, sha256 `1781f0d7395511ea`) moved here on 2026-11-18 (declutter step 4) and was split by its own headings, verbatim and in order, into `spec.md` 25 KB, `rulings.md` 18 KB, `rulings-2.md` 44 KB, `rulings-3.md` 38 KB, `rulings-4.md` 43 KB, `rulings-5.md` 44 KB, `rulings-6.md` 52 KB, `rulings-7.md` 50 KB, `rulings-8.md` 45 KB, `rulings-9.md` 57 KB, `rulings-10.md` 52 KB, `rulings-11.md` 40 KB, `rulings-12.md` 58 KB, `rulings-13.md` 55 KB, `rulings-14.md` 41 KB. Open the part a citation names; an old `file:line` citation maps through the table (old lines -> part lines). Proof: `python tools/declutter/split_specs.py --verify`.

| # | Old lines | Part | Part lines | Section |
| --- | --- | --- | --- | --- |
| 1 | 1-15 | `spec.md` | 1-15 | Build sheet DIESEL-1: the diesel-hybrid example Site "Kisiwa" (unit... |
| 2 | 16-81 | `spec.md` | 16-81 | 1. Order, lanes, conflicts and dates |
| 3 | 82-247 | `rulings.md` | 1-166 | 2. D0: the Kisiwa simulator trial (full ruling, ready for a builder... |
| 4 | 248-342 | `spec.md` | 82-176 | 3. D1–D5 (decisions pinned; literals and dates finalised in one car... |
| 5 | 343-370 | `spec.md` | 177-204 | 4. E3 impact |
| 6 | 371-385 | `spec.md` | 205-219 | 5. Plan HTML (`Docs/demo-sprint/client-demo-plan.html`): rows to ch... |
| 7 | 386-393 | `spec.md` | 220-227 | 6. Totals |
| 8 | 394-405 | `spec.md` | 228-239 | 7. Owner questions (plain language; for the coordinator to send bef... |
| 9 | 406-701 | `rulings-2.md` | 1-296 | 8. Ruling DIESEL-1-R2: Kisiwa re-planned around unexplained fuel (s... |
| 10 | 702-889 | `rulings-3.md` | 1-188 | 9. Ruling DIESEL-1-R3: after F0's stop (registered probe path, tank... |
| 11 | 890-915 | `rulings-3.md` | 189-214 | 9a. Ruling DIESEL-1-R3a: F0r's S6 stop at conversion |
| 12 | 916-963 | `rulings-3.md` | 215-262 | 9b. Ruling DIESEL-1-R3b: F0r result, F8, merge, next K units, setup... |
| 13 | 964-1434 | `rulings-4.md` | 1-471 | 9c. Ruling DIESEL-1-R3c: the K1 and K2 consolidated cards |
| 14 | 1435-1743 | `rulings-5.md` | 1-309 | 9d. Ruling DIESEL-1-R3d: the K3 consolidated card (`fuel-balance-1`... |
| 15 | 1744-1824 | `rulings-5.md` | 310-390 | 9e. Ruling DIESEL-1-R3e: F0 evidence line endings (K1 review L1) |
| 16 | 1825-2154 | `rulings-6.md` | 1-330 | 9f. Ruling DIESEL-1-R3f: K0 pre-flight (Q1–Q10) |
| 17 | 2155-2230 | `rulings-6.md` | 331-406 | 9g. Ruling DIESEL-1-R3g: K3 stop S4 (K2's fuel-records reader in th... |
| 18 | 2231-2369 | `rulings-6.md` | 407-545 | 9h. Ruling DIESEL-1-R3h: K3 stop S1 (600 idle seconds on every Kisi... |
| 19 | 2370-2472 | `rulings-6.md` | 546-648 | 9i. Ruling DIESEL-1-R3i: K0's two S5 stops, five deviations, and a ... |
| 20 | 2473-2839 | `rulings-7.md` | 1-367 | 9j. Ruling DIESEL-1-R3j: the K4 consolidated card (the unexplained-... |
| 21 | 2840-2948 | `rulings-8.md` | 1-109 | 9k. Ruling DIESEL-1-R3k: K4a pre-flight stop (two unfiltered Findin... |
| 22 | 2949-2955 | `rulings-8.md` | 110-116 | 9l. Ruling DIESEL-1-R3l: the K5 and K7 consolidated cards |
| 23 | 2956-2998 | `rulings-8.md` | 117-159 | 9l.1 Code reality and the decisions it forces (READ) |
| 24 | 2999-3328 | `rulings-8.md` | 160-489 | 9l.2 K5 card: the Fuel page night mode, the fuel Finding page and t... |
| 25 | 3329-3725 | `rulings-9.md` | 1-397 | 9l.3 K7 card: the Kisiwa story days in the demo prepare, 2.4 (range... |
| 26 | 3726-3746 | `rulings-9.md` | 398-418 | 9l.4 Effects on other cards |
| 27 | 3747-3790 | `rulings-9.md` | 419-462 | 9l.5 Order, lanes, critical path, tripwire, size and date |
| 28 | 3791-3803 | `rulings-9.md` | 463-475 | 9l.6 Owner questions |
| 29 | 3804-3811 | `rulings-9.md` | 476-483 | 9m. Ruling DIESEL-1-R3m: K7-D stop S-7 (the fuel Finding as an Acti... |
| 30 | 3812-3834 | `rulings-9.md` | 484-506 | 9m.1 Code reality: why S-7 fires, and the decisions it forces (READ) |
| 31 | 3835-3849 | `rulings-9.md` | 507-521 | 9m.2 Migration `backend/migrations/versions/0057_fuel_verification.... |
| 32 | 3850-3956 | `rulings-9.md` | 522-628 | 9m.3 K6a card: the fuel Finding as a domain-Action origin (0057), 0... |
| 33 | 3957-4256 | `rulings-10.md` | 1-300 | 9m.4 K6b card: `fuel-residual-within-band-1`, the verdict page and ... |
| 34 | 4257-4292 | `rulings-10.md` | 301-336 | 9m.5 Effects on K7 (K7-D step 5 and K7-F's freeze step) |
| 35 | 4293-4315 | `rulings-10.md` | 337-359 | 9m.6 Sizes, critical path, tripwire, date |
| 36 | 4316-4325 | `rulings-10.md` | 360-369 | 9m.7 Owner questions |
| 37 | 4326-4388 | `rulings-10.md` | 370-432 | 9n. Ruling DIESEL-1-R3k2: K4a review FIX, M1 (a window that returns... |
| 38 | 4389-4416 | `rulings-10.md` | 433-460 | 9m2. Ruling DIESEL-1-R3m2: K6a stop S-a3 (the maintenance request's... |
| 39 | 4417-4514 | `rulings-11.md` | 1-98 | 9j2. Ruling DIESEL-1-R3j2: K4b pre-flight stop S-a (the chain graph... |
| 40 | 4515-4601 | `rulings-11.md` | 99-185 | 9o. Ruling DIESEL-1-R3n: after K7-D's scratch prepare (E3 timing, t... |
| 41 | 4602-4737 | `rulings-11.md` | 186-321 | 9j3. Ruling DIESEL-1-R3j3: K4b review FIX, H1 (two untracked fuel t... |
| 42 | 4738-5143 | `rulings-12.md` | 1-406 | 9p. Ruling DIESEL-1-R3p — K8 consolidated card (four Sites on the e... |
| 43 | 5144-5326 | `rulings-12.md` | 407-589 | 9q. Ruling DIESEL-1-R3q — K9 pre-rehearsal answers (Q1–Q5) |
| 44 | 5327-5404 | `rulings-13.md` | 1-78 | 9r. Ruling DIESEL-1-R3r — Kisiwa Overview evidence state |
| 45 | 5405-5519 | `rulings-13.md` | 79-193 | 9s. Ruling DIESEL-1-R3s — Kisiwa's closed Performance gate (board P... |
| 46 | 5520-5606 | `rulings-13.md` | 194-280 | 9s2. Ruling DIESEL-1-R3s2 — R3s addendum: why Kisiwa's board days n... |
| 47 | 5607-5911 | `rulings-13.md` | 281-585 | 9t. Ruling DIESEL-1-R3t — K10 v2 after owner answer |
| 48 | 5912-6091 | `rulings-14.md` | 1-180 | 9u. Ruling DIESEL-1-R3u — four-Site rehearsal failures (F-COH, MILL... |
| 49 | 6092-6173 | `rulings-14.md` | 181-262 | 9t4. Ruling DIESEL-1-R3t4 — K10 stop K10-s1 (Kobo pre-mill days), K... |
| 50 | 6174-6292 | `rulings-14.md` | 263-381 | 9v. Ruling DIESEL-1-R3v — step-3 failures CO-2 and F-COH (COH-18 Ki... |
