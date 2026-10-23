"""W6-01c C2 403 capture (P-C2-11): a TEST-ONLY API composition, never a production grant outcome.

It is `assetops_backend.main.create_app()` with the global work router of `main.py:547-550` composed again and placed
first, identical except for its access callback `deny_fixture_site`, which returns 403 for the fixture Site code
`KOBO-001`. The real reader and the private `*_test` database answer every route. No browser interceptor.
Run: uvicorn api_403:app --app-dir .agent/W6-01-evidence/C2 (DATABASE_URL names the private DB).
"""
from assetops_backend import main as M


def deny_fixture_site(request, site_code: str) -> int | None:
    """Test-only access callback: 403 for the fixture Site, development access otherwise."""
    return 403 if site_code == "KOBO-001" else None


app = M.create_app()
_registry = M.ImportedSiteRegistry(M.FoundationService(M.build_foundation_store(M.database_url()),
                                                       M.DEVELOPMENT_TENANT_SLUG, M.utc_now))
_router = M.build_global_work_router(
    M.build_global_work_index_service(M.database_url()), M.registry_tenant(_registry),
    access=deny_fixture_site, unavailable=(M.SiteStoreUnavailable,),
    details=M.build_global_work_detail_service(M.database_url()), scope=_registry.ledger_scope)
app.router.routes[0:0] = _router.routes
