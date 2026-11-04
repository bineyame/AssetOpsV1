"""MD-0 L2m (build sheet §10.2, as reduced by Architect MD0-S2 to KOBO-001): the mechanism dataset seeded through
the product writers into a pg_harness worker DB, then asserted against the §2.6 expectations.

`ASSETOPS_MECHANISM_DAY_SET` picks the day set (`states` by default, `full` for the measured build). Disagreements
with §2.6 are recorded with `pytest.xfail("MD-0-Fn ...")` (R7), never by changing a rule.
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401

import mechanism_dataset as md

DAY_SET = os.environ.get("ASSETOPS_MECHANISM_DAY_SET", "states")
MANIFEST_OUT = os.environ.get("ASSETOPS_MECHANISM_MANIFEST_OUT")


def seeded(store, engine) -> dict:  # noqa: F811
    manifest = md.seed_database(store, engine, "main", DAY_SET)
    if MANIFEST_OUT:
        with open(MANIFEST_OUT, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
    return manifest


def test_seed_builds(store, engine) -> None:  # noqa: F811
    manifest = seeded(store, engine)
    assert manifest["action"] is not None

