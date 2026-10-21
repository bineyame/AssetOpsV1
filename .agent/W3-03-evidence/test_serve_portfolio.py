"""W3-03 run 2 capture harness (capture-scoped, not product code).

Builds the reviewed clean four-Site Portfolio fixture (`test_w303_portfolio_fixture_postgres.build_portfolio_fixture`,
closure 4 B3) in the private `w303m_test` DB, then serves the real `create_app()` on 127.0.0.1:9781 inside this
test, with the estate snapshots pinned to the fixture's frozen read clock. Capture-only control endpoint (POST):
`/__capture/empty-site` adds the authorized, unselected `W303-EMPTY-001` EV Site (the partial variant).
The Portfolio cursor key is generated per run from `secrets` and never printed.
Run: `python -m pytest .agent/W3-03-evidence/test_serve_portfolio.py -s -p no:cacheprovider`.
"""
import os
import secrets
import sys
from pathlib import Path

WT = Path(__file__).resolve().parents[2]
URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/w303m_test"
os.environ["ASSETOPS_TEST_DATABASE_URL"] = URL
os.environ["DATABASE_URL"] = URL
os.environ["ASSETOPS_TEST_TEMPLATE"] = "0"
os.environ["ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX"] = secrets.token_hex(32)
sys.path.insert(0, str(WT / "backend" / "tests"))

from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: E402,F401 - replay factories
from test_w303_portfolio_fixture_postgres import build_portfolio_fixture  # noqa: E402


def test_serve(request, monkeypatch, capsys):
    import uvicorn
    from test_w301_estate_index_postgres import add_empty_site

    from assetops_backend.main import create_app

    fx = build_portfolio_fixture(request, monkeypatch, capsys)
    app = create_app()

    @app.post("/__capture/empty-site")
    def empty_site() -> dict:
        site = add_empty_site(fx.engine, fx.site_ids["EV-LAB-001"], "W303-EMPTY-001")
        return {"site": str(site)}

    with capsys.disabled():
        print(f"SERVE frozen={fx.frozen.isoformat()} sites={sorted(fx.site_ids)}", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=9781, log_level="warning")
