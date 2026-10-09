# S2-02 questions 7 (fix round 1, before the owner walkthrough)

Each item names the fail-closed default the build already uses. None blocks the walkthrough.

## Q37 - "Halt rotation" after `ISSUE_OUTCOME_UNKNOWN` is an operator instruction, not an enforced lock

- **Built (`888a836`):** an unknown COMMIT outcome keeps the new protected file, prints `ISSUE_OUTCOME_UNKNOWN` with its path, exits 3 and tells the operator not to issue again until the database is reconciled.
- **Gap:** nothing stops a second `issue` once the database is reachable again. The database is the thing that could not be read, so it cannot hold the halt. A local marker would have to live beside the credential files.
- **Default:** keep the instruction only. A second `issue` against a readable database is safe: it reads the current state, issues a new selector, and revokes every earlier credential in one transaction. The kept file is then simply revoked. No secret is lost, because the operator still holds the kept file.
- **Ask:** is a local marker file that `issue` refuses while present wanted for the real pilot?

## Q38 - "Proven non-commit" is a fresh read that finds no row with the new selector

- **Built:** after a lost connection, the reconcile step discards the old pool and opens a new connection. It reads the scoped gateway, the selector's verifier, `credential_ref` and the named sources.
  - No row with the new selector: `NOT_ISSUED`. Only the unissued file is removed.
  - Full match: `ISSUED`.
  - Anything else: `UNKNOWN`. The file is kept.
- **Residual:** Postgres finishes or aborts a COMMIT whose client vanished. In theory, a backend that is still finishing could commit after the fresh read. The window is the server-side commit itself (milliseconds), and the issue transaction holds no long work after its INSERT.
- **Default:** accept this as proof of non-commit for the same-account pilot.
- **Ask:** should a real pilot also wait until no backend from the failed attempt is left in `pg_stat_activity` before it removes the file?

## Q39 - A v3 comparison report closes the gate on servers still running pre-fix code

- **Built:** the regenerated developer KOBO-001 report is schema v3 (`store_root`). Older running servers compare schema v2, so they read the newest report as "another schema", and KOBO-001 Evidence shows AWAITING_EVIDENCE_MIGRATION until they restart on this branch.
- **Default:** fail closed. The owner's servers (8000, 5173/...) were not touched; restart them on `task/S2-02-ingestion-site-evidence` before the walkthrough.

## Q40 - The store-root identity is a digest of the canonical resolved paths

- **Built:** each adapter returns `os.path.normcase(resolve(root))`, and the report stores only `sha256` of the evidence and commit roots.
- **Effect:** renaming or moving the workspace folder needs a new comparison.
  - A path spelled differently but resolving to the same folder (case, `..`, junction) is the same root.
- **Default:** closed on any real move. No path is stored in the report or served by an Evidence route.
