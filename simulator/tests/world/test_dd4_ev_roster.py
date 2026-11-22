"""DD4.3 (spec §4.5, §5.3; D-DD.52; pre-flight Q8, Q9): the one roster function extended to 6 Nov."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime

from assetops_simulator.world import exports_ev

from .books_support import EV, built, files_by_name, m_site

NOVEMBER = [f"2026-11-0{d}" for d in range(1, 6)]
SITES = {"EV-EMB": (20, "140.000"), "EV-KAS": (8, "150.000"), "EV-RUI": (14, "140.000")}


def roster() -> list[dict]:
    return list(files_by_name(built()[3])[f"{EV}.profile.ev-fleet-roster.csv"].records)


def test_r1_november_nights_one_to_five_unscaled() -> None:
    rows = [r for r in roster() if r["clocks"]["effective_from"] >= "2026-11"]
    count = Counter((r["site_code"], r["clocks"]["effective_from"]) for r in rows)
    expected = {(code, night): buses + (1 if (code, night) in {("EV-KAS", n) for n in exports_ev.SPARE_NIGHTS["EV-KAS"]}
                                        else 0)
                for code, (buses, _) in SITES.items() for night in NOVEMBER}
    assert count == expected
    for r in rows:
        assert r["body"]["required_kwh"] == SITES[r["site_code"]][1]
    view = built()[0]
    last = max(datetime.fromisoformat(r["body"]["departure_at"]) for r in rows)
    assert last.date() == date.fromisoformat(view["as_of"]) and last.hour < 6


def test_r2_spare_nights_parity_with_the_manifest() -> None:
    kas = m_site(EV, "EV-KAS")
    seen = kas["observations"]["november_to_date"]
    nights = exports_ev.SPARE_NIGHTS["EV-KAS"]
    assert len(nights) == seen["spare_bus_nights"] and kas["physical"]["spare_buses"] == 1
    assert all(seen["short_nights_from"] <= n < seen["period_end"] for n in nights)
    assert set(exports_ev.SPARE_NIGHTS) == {"EV-KAS"}


def test_r3_spare_row_shape() -> None:
    spare = [r for r in roster() if r["subject"]["ref"] == "EV-KAS-S01"]
    assert [r["clocks"]["effective_from"] for r in spare] == list(exports_ev.SPARE_NIGHTS["EV-KAS"])
    r = spare[0]
    assert r["body"]["block_ref"] == "EV-KAS-BLK-S01" and r["body"]["required_kwh"] == "150.000"
    assert r["body"]["return_at"] == f"{r['clocks']['effective_from']}T22:00:00+03:00"
    assert r["source_record_id"] == f"gen:EV-KAS:{r['clocks']['effective_from']}:roster:S01"
