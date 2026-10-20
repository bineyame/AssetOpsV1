# W3-02 Lane A requests (from Lane B)

## Commit 1 - mount the Evidence router (closure 4 B6 row `1`)

Lane B added `estate/evidence_money.py` (`EstateEvidenceService`), `estate/adapters/postgres_evidence_money_read.py` (`PostgresEvidenceMoneyRead`) and `estate_evidence_money_api.py` (`build_estate_evidence_money_router`). The guard allows only `estate/composition.py` to import the estate adapter, so the builder must live there. Exact diffs:

`backend/assetops_backend/estate/composition.py` - add after `build_estate_index_service`:

```python
def build_estate_evidence_service(database_url: str | None) -> Any:
    """W3-02: None without a product database (the router answers 503, never an empty estate)."""
    if not database_url:
        return None
    from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService, ClaimLimitRefusal
    from assetops_backend.estate.adapters.postgres_evidence_money_read import PostgresEvidenceMoneyRead
    from assetops_backend.estate.evidence_money import EstateEvidenceService

    base = build_estate_read(database_url)
    keys = ("findings", "assessments", "actions", "consequences", "eligibility", "cold", "ev", "provenance_reads",
            "inconsistent", "unavailable", "cold_site", "ev_site", "ev_money")
    return EstateEvidenceService(PostgresEvidenceMoneyRead(
        database_url, claim_limits=ClaimLimitReadService(base.assessments), claim_limit_refused=(ClaimLimitRefusal,),
        **{k: getattr(base, k) for k in keys}))
```

The test stand-in `evidence_read` in `backend/tests/test_w302_evidence_scope_snapshot_postgres.py` builds the same object. After the mount, it may call this builder instead.

`backend/assetops_backend/main.py` - imports and mount, after the W3-01 estate router (around `main.py:467`):

```python
from assetops_backend.estate.composition import build_estate_evidence_service  # with the existing estate import
from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router
...
    # W3-02 commit 1: the read-only estate Evidence root `/api/estate/evidence` (same tenant/access seams).
    app.include_router(build_estate_evidence_money_router(
        build_estate_evidence_service(database_url()), registry_tenant(registry),
        access=development_access, unavailable=(SiteStoreUnavailable,)))
```

No shell, registry or guard change is needed for commit 1. Please run the W3-01 estate API tests and the three `test_w302_evidence_*` files after the mount.

## Open questions for Lane A facades
See `.agent/W3-02-pending-rulings.md` c1-q1 (EV `historical_label` condition) and c1-q2 (`unknown_meter` not exposed by `EvSiteReads.capabilities_on`).
