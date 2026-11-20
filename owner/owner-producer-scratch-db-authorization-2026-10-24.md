# Owner authorization: producer scratch databases (2026-10-24)

Owner answer to the post-W6 audit question: "Allow tool scratch DBs".

Scope: in container `assetopsv1-postgres-1`, audit agents may create and drop databases whose names start with a reviewed producer's own guarded prefix followed by `_audit` (for example `assetops_s601b_audit`, `assetops_s602b_audit`, `assetops_s603_owner_audit`, `assetops_s701_owner_audit`, `assetops_s302_audit`). Only the producer tool itself creates them (its `prepare`/`build` mode) and drops them (its `drop` mode) straight after capture.

Run each producer unmodified. Do not use any wrapper that rewrites a producer's guard or DB name (the batch-02 `run_renamed_producer.py` approach is superseded). `*_test` DBs remain authorized as before (`.agent/owner-test-db-authorization-2026-10-18.md`). No other database may be created, altered or dropped.
