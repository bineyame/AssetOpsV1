# S2-02r — Credential rotation recovery

Status: carry/follow-up; independent maintenance branch, before non-demo or unattended/multi-operator rotation and real pilot
USER_REVIEW_REQUIRED: false
Branch: task/S2-02r-credential-rotation-recovery
Depends on: merged S2-02; not an `I-S3-01.requires` gate

## Outcome

An operator can reconcile an uncertain credential issue without deleting the only usable protected file or mistaking a late commit for rollback. The same-account supervised S2 demo and S3 Evidence input remain valid.

## Contract and acceptance

- Provide an explicit operator reconcile/status step or durable operation journal for `ISSUE_OUTCOME_UNKNOWN`; keep the file protected while state is unavailable or inconsistent. Do not treat a local marker or `pg_stat_activity` as transaction authority.
- Reconcile in a transaction acquiring the same scoped gateway row `FOR UPDATE` lock as `issue_credential`, waiting for the prior transaction to commit or abort. In that locked snapshot verify selector/verifier, `credential_ref`, expected source enablement and previous active selector. Only confirmed absence of the new selector with the old credential still active permits deleting the new file. A committed new selector returns the new file as issued; timeout/unavailable/inconsistent state remains typed unknown and preserves it.
- Distinguish `NOT_STARTED` only when execution demonstrably never reached the gateway issuance transaction, then clean the unissued file. A generic `LedgerUnavailable` after transaction start remains unknown.
- Test delayed COMMIT racing reconciliation, definitive rollback, committed response loss, unavailable DB and proven pre-transaction failure. Reviewer checks file/DB state and operator instructions after each. No silent second issue or credential disclosure.

Carry operationally: restart the intended server on merged S2 code and verify DB/store-root config before using a v3 comparison report; a moved store needs a fresh comparison. Other S2 review carries remain at their named backlog gates.
