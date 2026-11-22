"""DD2.4 (spec `specs/DD-demo-data/spec.md` §3, §5.6; D-DD.24; DD2.2 review residual risk): the departure log's
profile, admitted by the analyst, then its sample uploaded, accepted by the finance lead and stored. The stored
canonical records carry `block_met` as a JSON boolean, end to end, on PostgreSQL."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.profiles import SourceProfiles
    from assetops_backend.commercial.service import CommercialRecords
    from assetops_backend.commercial.uploads import Actor, CommercialUploads, UploadScope
    from test_3a1_commercial_postgres import Seeder
    from test_3a1_commercial_service import Clock
    from test_3a2_commercial_upload_postgres import _person
    from test_3a2_commercial_upload_service import KEY, T_SUBMIT, Keys

PROFILES = Path(__file__).resolve().parents[1] / "conversions" / "profiles"
PID = "ev-departures-illustrative"
FIN, ANALYST = "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST"


def test_d1_departures_admitted_uploaded_accepted_and_stored_with_a_boolean(store, engine) -> None:  # noqa: F811
    seeder = Seeder(engine)
    tid = seeder.add_tenant("acme")
    for code in ("EV-KAS", "EV-RUI"):
        seeder.add_site(tid, code)
    pg = PostgresCommercialStore(URL)
    try:
        clock = Clock(T_SUBMIT)
        profiles = SourceProfiles(pg, clock=clock, real_data=False)
        svc = CommercialUploads(CommercialRecords(pg, clock=clock), pg, Keys({tid: KEY}), clock=clock, real_data=False,
                                profiles=profiles)
        ana, fiona = (Actor(_person(engine, tid, n), role) for n, role in (("ana", ANALYST), ("fiona", FIN)))
        profile, sample, expected = (
            (PROFILES / f"{PID}.{s}").read_bytes() for s in ("profile.json", "sample.csv", "expected.json"))
        row = profiles.admit(tid, ana, profile, sample, expected)
        assert (row.reader, row.version) == (f"profile.{PID}.v1", 1)
        answer = svc.submit(tid, UploadScope(None, None), ana, sample, file_name="departures.csv",
                            reader_id=row.reader, media_type="text/csv")
        assert svc.decide(tid, UploadScope(None, None), fiona, answer["upload_id"], "ACCEPT")["state"] == "ACCEPTED"
        with engine.connect() as c:
            stored = c.execute(text("SELECT canonical FROM commercial_record_revision WHERE tenant_id = :t "
                                    "AND kind = 'DEPARTURE'"), {"t": UUID(str(tid))}).scalars().all()
        bodies = sorted((json.loads(s)["source_record_id"], json.loads(s)["body"]["block_met"]) for s in stored)
        assert bodies == sorted((r["source_record_id"], r["body"]["block_met"]) for r in json.loads(expected))
        assert [b for _, b in bodies].count(False) == 1 and all(isinstance(b, bool) for _, b in bodies)
    finally:
        pg.dispose()
