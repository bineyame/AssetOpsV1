"""Source types v1: what each operator export may carry (2a spec §7; D-2A.7).

A batch names one source type; a record whose kind the source type does not
emit is refused (`CANONICAL_SOURCE_TYPE record.kind`). Readings and fuel
records keep their existing formats (`EXISTING_FORMATS`).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class SourceType:
    id: str
    kinds: frozenset[str]
    words: str


_TABLE = (
    ("billing_export", ("CHARGE", "RECEIPT", "ADJUSTMENT"),
     "customer billing or vending export (prepaid and postpaid)"),
    ("mobile_money_statement", ("RECEIPT", "SETTLEMENT"), "mobile-money settlement statement"),
    ("meter_register", ("METER_ASSIGNMENT",), "meter register with effective dates"),
    ("meter_data_export", ("CUSTOMER_METER_READ",), "meter-data system export"),
    ("expense_ledger", ("EXPENSE", "ADJUSTMENT"),
     "supplier invoices, credit notes, quotes, fuel purchases and payroll lines"),
    ("budget_workbook", ("BUDGET_LINE",), "monthly budget lines by Site and line"),
    ("contract_documents", ("CONTRACT_DOCUMENT",),
     "warranty, EPC, O&M and SLA, insurance and storage contracts"),
    ("storage_ledger", ("STORAGE_MOVEMENT",), "storage ledger, check-in and check-out per batch"),
    ("customer_invoicing", ("CHARGE", "RECEIPT", "ADJUSTMENT"), "cold-room invoices, receipts and credit notes"),
    ("storage_rate_card", ("TARIFF_SCHEDULE",), "storage rate card"),
    ("tariff_sheet", ("TARIFF_SCHEDULE",), "mini-grid tariff sheet"),
    ("electricity_bill", ("CHARGE",), "cold-room electricity bill"),
    ("utility_invoice", ("CHARGE", "TARIFF_SCHEDULE"),
     "utility invoice with time-of-use and demand lines, and its tariff schedule"),
    ("fleet_roster", ("FLEET_ROSTER",), "fleet roster: bus, block, return, departure, required kWh"),
    ("depot_dispatch_log", ("DEPARTURE",), "depot dispatch log of departures"),
    ("service_tickets", ("SERVICE_TICKET",), "service tickets (vendor portal export)"),
    ("penalty_statement", ("EXPENSE",), "transport authority penalty statement"),
)

SOURCE_TYPES = MappingProxyType({
    source_id: SourceType(source_id, frozenset(kinds), words) for source_id, kinds, words in _TABLE
})

EXISTING_FORMATS = MappingProxyType({
    "READING": "assetops_contracts.source_envelope_v4",
    "OPERATIONAL_RECORD": "assetops_contracts.operational_records",
})
