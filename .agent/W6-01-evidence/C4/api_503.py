"""W6-01d C4 503 capture: a TEST-ONLY API composition (the C1 `test_refusal_order_401_403_404_503` outage pattern).

It is `assetops_backend.main.create_app()` with the global work router of `main.py` composed again and placed first,
identical except for its Site scope `outage`, which raises `SiteStoreUnavailable` as the C1 test's `Api(outage)` does.
The route answers 503 `WORK_STORE_UNAVAILABLE`. No browser interceptor or fabricated response.
Run: uvicorn api_503:app --app-dir .agent/W6-01-evidence/C4 (DATABASE_URL names the private DB).
"""
from assetops_backend import main as M


def outage(code: str):
    """Test-only Site scope: the Site store is down."""
    raise M.SiteStoreUnavailable("down")


app = M.create_app()
_registry = M.ImportedSiteRegistry(M.FoundationService(M.build_foundation_store(M.database_url()),
                                                       M.DEVELOPMENT_TENANT_SLUG, M.utc_now))
_router = M.build_global_work_router(
    M.build_global_work_index_service(M.database_url()), M.registry_tenant(_registry),
    unavailable=(M.SiteStoreUnavailable,),
    details=M.build_global_work_detail_service(M.database_url()), scope=outage)
app.router.routes[0:0] = _router.routes
