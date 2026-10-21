"""W3-03 capture harness (capture-scoped, not product code; runs 2 and 3).

Builds the reviewed clean four-Site Portfolio fixture (`test_w303_portfolio_fixture_postgres.build_portfolio_fixture`,
closure 4 B3) in a private `*_test` DB (`W303_DB`, default `w303o_test`), then serves the real `create_app()` on
127.0.0.1:9781 inside this test, with the estate snapshots pinned to the fixture's frozen read clock.
The Portfolio cursor key is generated per run from `secrets` and never printed.

Run-3 process selectors (environment, read once at start; r2 "Run-3 captures"):
- `W303_COLD_DRAIN=0` builds the persisted `a_lineless_cold` variant (`cold_drain=False`; the `pending` capture).
- `W303_NO_CURSOR_KEY=1` leaves `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` unset (the `refusal-503` capture).
- `W303_ROUTER=capture` shadows the mounted `/api/estate/portfolio` route with the same
  `build_estate_portfolio_router` over the same `build_estate_portfolio_service`, whose `authenticate` and `tenant`
  seams follow `/__capture/mode` (the `empty` foreign-tenant and `refusal-401` captures). Without it the route is the
  unmodified `create_app()` mount.
Capture-only control endpoints (POST):
- `/__capture/empty-site` adds the authorized, unselected `W303-EMPTY-001` EV Site (partial and 409 variants).
- `/__capture/mode?limit1=0|1&auth=ok|deny&tenant=fixture|foreign`: `limit1=1` rewrites every Portfolio request's
  `limit` to 1 (page one then carries a signed cursor, and page two keeps the same limit, for the 409 load-more path); `auth=deny` makes the
  capture router's `authenticate` refuse every request (no valid Bearer is ever sent); `tenant=foreign` selects a
  fresh tenant UUID with zero authorized Sites. No HTTP response is replaced or handcrafted.
Run: `python -m pytest .agent/W3-03-evidence/test_serve_portfolio.py -s -p no:cacheprovider`.
"""
import os
import secrets
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode
from uuid import uuid4

WT = Path(__file__).resolve().parents[2]
DB = os.environ.get("W303_DB", "w303o_test")
assert DB.endswith("_test"), DB
URL = f"postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/{DB}"
os.environ["ASSETOPS_TEST_DATABASE_URL"] = URL
os.environ["DATABASE_URL"] = URL
os.environ["ASSETOPS_TEST_TEMPLATE"] = "0"
if os.environ.get("W303_NO_CURSOR_KEY") == "1":
    os.environ.pop("ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX", None)
else:
    os.environ["ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX"] = secrets.token_hex(32)
sys.path.insert(0, str(WT / "backend" / "tests"))

from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: E402,F401 - replay factories
from test_w303_portfolio_fixture_postgres import build_portfolio_fixture  # noqa: E402

PORTFOLIO = "/api/estate/portfolio"


def test_serve(request, monkeypatch, capsys):
    import uvicorn
    from test_w301_estate_index_postgres import add_empty_site

    from assetops_backend.estate.composition import build_estate_portfolio_service
    from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
    from assetops_backend.finding_api import development_access
    from assetops_backend.main import create_app
    from assetops_backend.sites.ports import SiteStoreUnavailable

    fx = build_portfolio_fixture(request, monkeypatch, capsys,
                                 cold_drain=os.environ.get("W303_COLD_DRAIN", "1") != "0")
    app = create_app()
    mode = {"limit1": False, "auth": "ok", "tenant": "fixture"}
    foreign = uuid4()

    if os.environ.get("W303_ROUTER") == "capture":
        # Included routers are matched in list order, so the capture router is moved to the front and shadows the
        # create_app() mount of the same path (FastAPI keeps included routers as lazy entries without a `path`).
        app.include_router(build_estate_portfolio_router(
            build_estate_portfolio_service(URL),
            lambda: foreign if mode["tenant"] == "foreign" else fx.tenant_id,
            authenticate=lambda req: 401 if mode["auth"] == "deny" else None,
            access=development_access, unavailable=(SiteStoreUnavailable,)))
        app.router.routes.insert(0, app.router.routes.pop())

    @app.post("/__capture/empty-site")
    def empty_site() -> dict:
        site = add_empty_site(fx.engine, fx.site_ids["EV-LAB-001"], "W303-EMPTY-001")
        return {"site": str(site)}

    @app.post("/__capture/mode")
    def set_mode(limit1: str | None = None, auth: str | None = None, tenant: str | None = None) -> dict:
        if limit1 is not None:
            mode["limit1"] = limit1 == "1"
        if auth in ("ok", "deny"):
            mode["auth"] = auth
        if tenant in ("fixture", "foreign"):
            mode["tenant"] = tenant
        return dict(mode)

    async def served(scope, receive, send):
        if scope["type"] == "http" and scope["path"] == PORTFOLIO and mode["limit1"]:
            pairs = parse_qsl(scope["query_string"].decode(), keep_blank_values=True)
            pairs = [(k, "1" if k == "limit" else v) for k, v in pairs]
            scope = {**scope, "query_string": urlencode(pairs).encode()}
        await app(scope, receive, send)

    with capsys.disabled():
        print(f"SERVE db={DB} frozen={fx.frozen.isoformat()} sites={sorted(fx.site_ids)} "
              f"router={os.environ.get('W303_ROUTER', 'main')}", flush=True)
        uvicorn.run(served, host="127.0.0.1", port=9781, log_level="warning")
