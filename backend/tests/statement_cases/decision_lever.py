"""6h (spec section 5.4, D-P6.58): the cases of the `decision_lever.*` statements, one per variant. The English is
section 5.4's wording, written by hand (W2), never computed."""
from __future__ import annotations

from decimal import Decimal

from assetops_backend.i18n import Evidence, Month, Name, Percent, State

from statement_cases import Case

SITE = Name("Kobo", "site.name")


def _title(lever: str, english: str) -> Case:
    return Case("decision_lever.title", lever.lower(), {"lever": State(lever), "site": SITE}, f"Kobo {english}")


def _question(lever: str, english: str) -> Case:
    return Case("decision_lever.question", lever.lower(), {"lever": State(lever), "site": SITE},
                f"What should we do about the Kobo {english}?")


def _pct(value: str) -> Percent:
    return Percent(Decimal(value), Evidence("DECLARED"))


_SETTINGS = {"stop_from": _pct("0.8"), "stop_to": _pct("0.9"), "reserve_from": _pct("0.3"), "reserve_to": _pct("0.2")}


def _option(option: str, english: str) -> Case:
    return Case("decision_lever.option_label", option.lower(), {"option": State(option), **_SETTINGS}, english,
                ["declared"])


def _record(record: str, english: str) -> Case:
    return Case("decision_lever.record", record.lower(), {"record": State(record), "site": SITE}, english)


CASES = [
    _title("GENERATOR_STOP_RESERVE", "generator stop setting"),
    _title("BACKUP_COVER", "stock cover while the backup is restored"),
    _title("CHAMBER_EFFICIENCY", "electricity above what occupancy explains"),
    _title("STORAGE_CONTRACT", "storage contract"),
    _title("CHARGING_SCHEDULE", "charging schedule"),
    _title("CHARGER_RESTORE", "departures while a charger is restored"),
    _title("FLEET_CAPACITY_USE", "extra buses on spare charging"),
    _title("GENERATOR_REDUNDANCY", "evening supply with no standby generator"),
    _title("PRODUCTIVE_DEMAND", "new daytime demand"),
    _title("FUEL_RECONCILIATION", "fuel the model cannot explain"),
    _question("GENERATOR_STOP_RESERVE", "generator stop setting"),
    _question("BACKUP_COVER", "stock cover while the backup is restored"),
    _question("CHAMBER_EFFICIENCY", "electricity above what occupancy explains"),
    _question("STORAGE_CONTRACT", "storage contract"),
    _question("CHARGING_SCHEDULE", "charging schedule"),
    _question("CHARGER_RESTORE", "departures while a charger is restored"),
    _question("FLEET_CAPACITY_USE", "extra buses on spare charging"),
    _question("GENERATOR_REDUNDANCY", "evening supply with no standby generator"),
    _question("PRODUCTIVE_DEMAND", "new daytime demand"),
    _question("FUEL_RECONCILIATION", "fuel the model cannot explain"),
    Case("decision_lever.no_action", "keep_settings", {"words": State("KEEP_SETTINGS")},
         "Keep the current generator settings"),
    Case("decision_lever.no_action", "keep", {"words": State("KEEP")}, "Keep things as they are"),
    Case("decision_lever.no_action", "wait_for_remedy", {"words": State("WAIT_FOR_REMEDY")},
         "Wait for the supplier's remedy"),
    _option("NO_ACTION", "Keep the current generator settings"),
    _option("STOP", "Stop the generator at 90% battery instead of 80%"),
    _option("RESERVE_DOWN", "Lower the battery reserve from 30% to 20%"),
    _option("RESERVE_UP", "Raise the battery reserve from 30% to 20%"),
    _option("STOP_RESERVE_DOWN",
            "Stop the generator at 90% battery instead of 80%, and lower the reserve from 30% to 20%"),
    _option("STOP_RESERVE_UP",
            "Stop the generator at 90% battery instead of 80%, and raise the reserve from 30% to 20%"),
    _option("STOPGAP_AND_CLAIM", "Put a stopgap in place and claim the repair from the supplier"),
    _option("SELF_REPAIR", "Repair it ourselves"),
    _option("REPAIR", "Repair it"),
    _option("REPLACE", "Replace it"),
    _option("STORAGE_CONTRACT", "Sign the storage contract"),
    _option("DEADLINE_AWARE", "Charge on a schedule that meets every departure"),
    _option("CHEAPEST_WINDOW", "Charge in the cheapest window only"),
    _option("LOCAL_REPAIR", "Have it repaired locally"),
    _option("RESCHEDULE", "Change the charging schedule around the fault"),
    _option("ABSORB_PART", "Take part of the offered buses"),
    _option("ABSORB_ALL", "Take all the offered buses"),
    _option("ADD_CHARGERS", "Add chargers"),
    _option("ADD_STORAGE", "Add battery storage"),
    _option("NEW_CONNECTION", "Connect the new customer"),
    _option("INVESTIGATE", "Investigate the fuel records"),
    _record("BACKUP_COVER__UNCOVERED_NIGHTS", "the rota: the nights it leaves uncovered"),
    _record("CHAMBER_EFFICIENCY__EXCESS_KWH", "the repair quote and the electricity above the model after the repair"),
    _record("CHAMBER_EFFICIENCY__MODEL_FACTOR", "the replacement's rated efficiency"),
    _record("STORAGE_CONTRACT__CONTRACT_CRATE_DAYS", "the storage contract's crate-days a month"),
    _record("STORAGE_CONTRACT__CONTRACT_RATE", "the storage contract's rate"),
    _record("STORAGE_CONTRACT__HANDLING", "the contract's handling cost a month"),
    _record("CHARGER_RESTORE__COVERED_BUS_NIGHTS", "the cover arranged: bus-nights charged elsewhere"),
    _record("CHARGER_RESTORE__EXTRA_MISSED_DEPARTURES", "the restore date and the departures it would miss"),
    _record("FLEET_CAPACITY_USE__BUSES", "the route offer: buses in the fleet"),
    _record("GENERATOR_REDUNDANCY__REDUCED_DAYS", "the repair or supply quote and its restore date"),
    _record("PRODUCTIVE_DEMAND__PRODUCTIVE_KWH", "the customer's signed demand a month"),
    _record("FUEL_RECONCILIATION__UNEXPLAINED_L", "the investigation's result"),
    Case("decision_lever.study", "charging_schedule",
         {"lever": State("CHARGING_SCHEDULE"), "site": SITE, "month": Month(2026, 10)},
         "a charging replay of Kobo's own October 2026 under this schedule"),
]
