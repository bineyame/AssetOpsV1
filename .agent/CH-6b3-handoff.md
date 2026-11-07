# CH-6b3 handoff

- **State:** CH6b3-R3 steps 1-5 committed. Step 6 (scoped backend run; drained polish clone `ch6b3r3`; L3m collect/check; guards) and step 7 (packet) in progress.
- **Landed:** `claims.py` `LATEST_KNOWN`; vocabulary "{n} confirmed, from the days checked" (MD-CH6-8 / R708); `card_notes` Protect None, no coverage clause; `DAYS_CHECKED` "assessed"; `not assessed:` strip; `_estate_why` takes the card's days_line + `window_open`; COH-17 rows L2, L3, W3, N1 + C2 absent-key fix with planted breaks (`test_chain_coherence.py` 138 pass); frontend 5 estate test files 110 pass, tsc clean; junction removed.
- **Golden changed:** `estate_week_2026-10-25.json` kobo threads open 1 -> 0, in_hand 0 -> 1 (T1 ACTION_IN_HAND effective 1 Nov, known by k).
- **Scoped run:** `var/ch6b3r3_scoped.log` (background, run-host-tests, 20 files).
- **Next:** `chain_clone.py create ch6b3r3 --migrate`, backfill `--steps a,b,c,d` (DATABASE_URL = clone), settle, drain `mini_depth.worker run-pending --limit 500`, settle, `chain_coherence.py collect --work var/ch6b3work --database-url <clone> --out var/ch6b3r3_bundle`, check `--expect tools/checks/fixtures/chain_coherence/expected-today.json`; compare 1/1/1, 2/1/2, 3/2/3, 2/1/2; drop clone. Then L3m collect/check on the existing states template; guards A, W, N, V, M, ratchet; packet.
