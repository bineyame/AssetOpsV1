"""W6-01e E2 empty_scope capture (P-E2-12, A1Q2 R4): a TEST-ONLY API composition, never a production grant outcome.

It is `assetops_backend.main.create_app()` with the global work router composed again and placed first, identical
except for its access callback `deny_every_site`, which returns 403 for every Site code, so the global list is
EMPTY_SCOPE. The real reader and the private `*_test` database answer every route. No browser interceptor.
Run: uvicorn api_empty_scope:app --app-dir .agent/W6-01-evidence/E2 (DATABASE_URL names the private DB).
"""
from assetops_backend import main as M


def deny_every_site(request, site_code: str) -> int | None:
    """Test-only access callback: every Site is denied."""
    return 403


app = M.create_app()
_registry = M.ImportedSiteRegistry(M.FoundationService(M.build_foundation_store(M.database_url()),
                                                       M.DEVELOPMENT_TENANT_SLUG, M.utc_now))
_router = M.build_global_work_router(
    M.build_global_work_index_service(M.database_url()), M.registry_tenant(_registry),
    access=deny_every_site, unavailable=(M.SiteStoreUnavailable,),
    details=M.build_global_work_detail_service(M.database_url()), scope=_registry.ledger_scope)
app.router.routes[0:0] = _router.routes
