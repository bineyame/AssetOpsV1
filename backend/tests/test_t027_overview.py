"""T027 phase 2: the mini-grid Site Overview read model (AC10, AC11, AC12, AC13,
AC19, AC22). AC14/AC15 for the Overview ride on `t027_isolated_probe.build`.

Computation is exercised over accepted records held in a fake store; the
route and gate cases go through ingestion like any other source.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from route_inventory import served_paths
from run_fixtures import FakeSites
from assetops_backend.evidence.models import AcceptedRecord, SiteEvidence
from assetops_backend.evidence.overview import DOMAIN_METRICS, OverviewReadModel
from assetops_backend.evidence.read_model import NEEDED_SIGNALS, OVERVIEW_DOMAIN_SIGNALS
from assetops_contracts.ingestion_batch import ingestion_batch_document
from test_t027_ingestion import SITE_ID, a_batch, a_site, client_for, envelope, texts

PROFILES = Path(__file__).resolve().parents[2] / "frontend" / "src" / "sites" / "presentationProfiles.json"


class FakeStore:
    def __init__(self, records: list[AcceptedRecord]) -> None:
        self.evidence = SiteEvidence(site_id=SITE_ID, records=tuple(records))

    def load_site(self, site_id: str) -> SiteEvidence:
        return self.evidence if site_id == SITE_ID else SiteEvidence(site_id=site_id)


def record(device: str, signal: str, minute: int, value: str | None, *,
           interval: bool = True, gateway: str = "g", unit: str = "kW") -> AcceptedRecord:
    end = f"2026-09-22T00:{minute:02d}:00Z"
    start = f"2026-09-22T00:{minute - 5:02d}:00Z"
    return AcceptedRecord(
        message_id=f"{device}-{signal}-{minute}-{gateway}",
        envelope_text="{}", content_digest="d", site_id=SITE_ID, source_id="s",
        gateway_id=gateway, device_id=device, signal_id=signal, family="MEASUREMENT",
        measurement="INTERVAL_MEAN" if interval else "STATE_AT_INSTANT",
        source_time=end, published_at=end, received_at=end, batch_id="b",
        source_mode="SIMULATED", mapping_set_id="m", mapping_version=1,
        foundation_version=1, foundation_valid_from="2026-01-01T00:00:00Z",
        original_value=value, original_unit=unit, normalized_value=value,
        normalized_unit=unit, quality="GOOD" if value is not None else "UNAVAILABLE",
        unavailable_reason=None if value is not None else "NO_MEASUREMENT",
        interval_start=start if interval and value is not None else None,
        interval_end=end if interval and value is not None else None,
    )


def minigrid_site():
    return replace(a_site(), site_type="MINIGRID")


def a_day_without_fuel() -> list[AcceptedRecord]:
    rows = []
    for minute in (10, 25):
        rows += [
            record("residential-meter", "active-power", minute, "12"),
            record("clinic-meter", "active-power", minute, "6"),
            record("mill-meter", "active-power", minute, "24"),
            record("generator-controller", "ac-power", minute, "30" if minute == 25 else "0"),
            record("pv-inverter-controller", "ac-power", minute, "18"),
            record("generator-controller", "status", minute,
                   "RUNNING" if minute == 25 else "STOPPED", interval=False, unit="state"),
            record("battery-pcs-controller", "state-of-charge", minute,
                   "949/12" if minute == 25 else "40", interval=False, unit="%"),
        ]
    return rows


def overview(records: list[AcceptedRecord]) -> dict:
    return OverviewReadModel(FakeStore(records)).site_overview(minigrid_site())


def metric(payload: dict, domain: str, metric_id: str) -> dict:
    card = next(c for c in payload["cards"] if c["domain_id"] == domain)
    return next(m for m in card["metrics"] if m["metric_id"] == metric_id)


class TestOneListOfOverviewSignals:
    """Review N9: the profile's cards, the backend domains and coverage agree."""

    def test_the_profile_cards_are_the_backend_domains_in_order(self) -> None:
        profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
        assert set(profiles) == set(OVERVIEW_DOMAIN_SIGNALS)
        for site_type, domains in OVERVIEW_DOMAIN_SIGNALS.items():
            cards = [card["id"] for card in profiles[site_type]["overview_cards"]]
            assert cards == [domain for domain, _ in domains]
        assert set(DOMAIN_METRICS) == {d for ds in OVERVIEW_DOMAIN_SIGNALS.values() for d, _ in ds}

    def test_needed_signals_are_derived_from_the_domains(self) -> None:
        derived = {(n.device_id, n.signal_id, d) for n in NEEDED_SIGNALS["MINIGRID"] for d in n.needed_by}
        assert derived == {
            (device, signal, domain)
            for domain, signals in OVERVIEW_DOMAIN_SIGNALS["MINIGRID"]
            for device, signal in signals
        }

    def test_the_profile_owns_no_card_state(self) -> None:
        profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
        for profile in profiles.values():
            assert set(profile) == {"overview_cards"}
            for card in profile["overview_cards"]:
                assert set(card) == {"id", "label"}


class TestCards:
    def test_every_card_is_no_assessment_yet_and_nothing_is_unknown(self) -> None:
        payload = overview(a_day_without_fuel())
        assert [c["domain_id"] for c in payload["cards"]] == [
            "Service", "Dispatch", "Battery", "Fuel", "Renewable"]
        for card in payload["cards"]:
            assert card["assessment"]["status"] == "NO_ASSESSMENT"
            assert card["assessment"]["label"] == "No assessment yet"
        assert payload["objective"]["assessment"]["status"] == "NO_ASSESSMENT"
        assert payload["findings"] == []
        assert "unknown" not in json.dumps(payload).lower()

    def test_metrics_sum_measured_intervals_only(self) -> None:
        payload = overview(a_day_without_fuel())
        served = metric(payload, "Service", "served-energy")
        # (12 + 6 + 24) kW x 5 min x 2 intervals = 7 kWh; the 10 minutes between
        # the two measured intervals are not counted.
        assert (served["value"], served["unit"]) == ("7.0", "kWh")
        assert payload["objective"]["service_delivered"] == served
        assert metric(payload, "Dispatch", "generator-runtime")["value"] == "0.08"
        assert metric(payload, "Dispatch", "generator-energy")["value"] == "2.5"
        assert metric(payload, "Dispatch", "generator-status-running")["value"] == "1 of 2"
        assert metric(payload, "Renewable", "pv-energy")["value"] == "3.0"
        latest = metric(payload, "Battery", "soc-latest")
        assert (latest["value"], latest["unit"], latest["at"]) == ("79.08", "%", "2026-09-22T00:25:00Z")
        assert metric(payload, "Battery", "soc-min")["value"] == "40"
        assert payload["window"]["hours"] == "0.25"

    def test_an_uncovered_card_names_its_gap_and_has_no_value(self) -> None:
        fuel = next(c for c in overview(a_day_without_fuel())["cards"] if c["domain_id"] == "Fuel")
        assert fuel["gaps"] == [
            {"device_id": "fuel-level-sensor", "signal_id": "fuel-level", "status": "NOT_REPORTED"}]
        [level] = fuel["metrics"]
        assert level["value"] is None and level["evidence"] == []
        assert "fuel-level-sensor/fuel-level" in level["unavailable_because"]
        # Tank level only: no consumption or loss metric exists.
        assert not any("consum" in m["metric_id"] or "loss" in m["metric_id"]
                       for m in fuel["metrics"])

    def test_unavailable_records_are_counted_never_filled(self) -> None:
        rows = [r for r in a_day_without_fuel() if r.signal_id != "state-of-charge"]
        rows.append(record("battery-pcs-controller", "state-of-charge", 10, None,
                           interval=False, unit="%"))
        battery = next(c for c in overview(rows)["cards"] if c["domain_id"] == "Battery")
        assert battery["coverage"][0]["status"] == "NO_GOOD_RECORD"
        assert battery["coverage"][0]["unavailable"] == 1
        assert all(m["value"] is None for m in battery["metrics"])

    def test_overlapping_records_are_neither_summed_nor_replaced(self) -> None:
        rows = a_day_without_fuel() + [
            record("residential-meter", "active-power", 25, "60", gateway="other")]
        payload = overview(rows)
        # The 00:20-00:25 residential span has two distinct records: it is used
        # by no metric (12 x 5 min once, plus the clinic and mill spans).
        assert metric(payload, "Service", "residential-meter-energy")["value"] == "1.0"
        demand = payload["timeline"][0]
        assert [p["start"] for p in demand["points"]] == ["2026-09-22T00:05:00Z"]

    def test_empty_site_names_every_gap_and_has_no_window(self) -> None:
        payload = OverviewReadModel(FakeStore([])).site_overview(
            replace(minigrid_site(), site_id="MG-EMPTY"))
        assert payload["window"] == {"start": None, "end": None,
                                     "basis": "LATEST_RELEASE", "hours": None}
        assert payload["accepted_in_window"] == 0
        for card in payload["cards"]:
            assert card["gaps"] and all(m["value"] is None for m in card["metrics"])
            assert card["assessment"]["status"] == "NO_ASSESSMENT"
        assert all(series["points"] == [] for series in payload["timeline"])

    def test_evidence_links_name_accepted_records(self) -> None:
        rows = a_day_without_fuel()
        ids = {r.message_id: (r.device_id, r.signal_id) for r in rows}
        payload = overview(rows)
        links = [link for card in payload["cards"] for m in card["metrics"] for link in m["evidence"]]
        assert links
        for link in links:
            assert ids[link["message_id"]] == (link["device_id"], link["signal_id"])

    def test_a_site_type_with_no_domains_has_no_cards(self) -> None:
        payload = OverviewReadModel(FakeStore([])).site_overview(
            replace(a_site(), site_type="COLD_CHAIN"))
        assert payload["cards"] == []


class TestOverviewRoute:
    def test_served_with_the_gate_closed_from_accepted_evidence_only(self, tmp_path) -> None:
        client = client_for(tmp_path, FakeSites((minigrid_site(),)))
        before = client.get(f"/api/sites/{SITE_ID}/overview").json()
        assert before["accepted_in_window"] == 0
        client.post("/api/ingestion/batches",
                    json=ingestion_batch_document(a_batch(texts(envelope(1, value="88")))))
        after = client.get(f"/api/sites/{SITE_ID}/overview").json()
        level = metric(after, "Fuel", "fuel-level-latest")
        assert (level["value"], level["unit"]) == ("88", "L")
        [link] = level["evidence"]
        detail = client.get(f"/api/sites/{SITE_ID}/evidence/records/{link['message_id']}")
        assert detail.status_code == 200
        assert "/api/sites/{site_id}/overview" in served_paths(client.app)
        assert client.get("/api/simulator-lab/runs").status_code == 404

    def test_unknown_site_and_bad_window(self, tmp_path) -> None:
        client = client_for(tmp_path, FakeSites((minigrid_site(),)))
        assert client.get("/api/sites/MG-404/overview").status_code == 404
        bad = client.get(f"/api/sites/{SITE_ID}/overview", params={"from": "yesterday"})
        assert bad.status_code == 422


def test_a_closed_build_still_reads_overview_beside_evidence(tmp_path) -> None:
    client: TestClient = client_for(tmp_path, FakeSites((minigrid_site(),)))
    paths = served_paths(client.app)
    assert {"/api/sites/{site_id}/evidence", "/api/sites/{site_id}/overview"} <= set(paths)
    assert not any("simulator-lab" in path for path in paths)
