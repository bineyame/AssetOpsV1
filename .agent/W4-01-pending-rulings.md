# W4-01 pending rulings (batched, 2026-10-20, after commit 1 `4cb89c68`)

None blocks commit 1. Each needs an answer before commit 2 or 3 is built. No builder default is assumed.

1. **Client `authorization_basis` on a SERVICE command (commit 2/3).** Review closure B6 says "no
   `authorization_basis` accepted from the client"; S28 says the server "derives/overwrites" it; the request wire
   example still carries `actor.authorization_basis`. When a body includes `actor.authorization_basis`: refuse 422
   `WORK_INPUT_INVALID`, or accept, ignore and exclude it from the canonical hash? Which exact value does the server
   store for the development SERVICE principal (for example the `command_access` grant name)?
2. **Shared provenance patch owner (commit 2, Q11).** Has W3-01 commit 1 (`evidence/public_provenance.py`) merged to
   main, or reached a reviewed state the W4 branch should consume? If not, W4 commit 2 carries "that same reviewed
   patch": name the exact reviewed revision/diff to carry so the two lanes do not produce two variants.
3. **Rule-8 per-table anti-vacuity at commit 2.** S25 requires per-table INSERT counts for all 11 tables in commit 2.
   `maintenance_plan` and `operational_record` writers are in commit 2's service, but the routes arrive in commit 3.
   Confirm all 11 table INSERTs (including plan and operational record) land in `postgres_work_store.py` in commit 2.
