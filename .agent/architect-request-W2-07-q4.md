# Architect request: W2-07 commit 2 readings, and the commit 3 read rule (q4)

You are the AssetOps Architect.

## Read first

- `.ai/ROLE_CONFIG.md`: the "implementers never decide" and "Token Efficiency" sections.
- `.agent/W2-07-build-spec.md`: everything through q3.
- Branch `task/W2-07-ev-site-evidence-money` at `cb391aac`: the "Run 5" note in `.agent/W2-07-phase-handoff.md`, and the code in `financials/ev_money.py`, `ev_recompute.py` and `financials/adapters/postgres_consequence_store.py`. Use `git show`.

## Builder readings and open points

Implementer readings are defects. Confirm or replace each one, using literal values or a table.

1. `source_class` in the basis hash is the stored class, and `source_gate` is the C5 class.
2. Links and tariff fields are written only for ESTIMATED rows. Give the literal null/empty values for every other state.
3. The replay's selected window is `[08:00, 09:05)`, not `[08:00, 09:00)`. The `[08:00, 09:00)` tariff still covers every eligible interval, so the vectors are unchanged. Confirm that the tariff-coverage predicate is the one ruled.
4. **Commit 3 read selection.** An R8 basis replay can make an older consequence revision current again. Rule the exact selection for all five reads: which stored revision is current, and how it is chosen. Give the literal SQL or pseudocode, the ordering, and the named test. Include the q3 "five-read assertion" that was deferred to commit 3.

## Then

Dry-read commits 3–5 against the code. If nothing else is open, say so in one line.

## Output

Append to `.agent/W2-07-build-spec.md` as "Run 5 rulings (q4)". Write nothing else, and do not commit.
