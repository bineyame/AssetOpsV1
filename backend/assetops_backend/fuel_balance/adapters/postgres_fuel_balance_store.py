"""DIESEL-K3 (`.agent/build-sheet-DIESEL-1.md` §9d.4-§9d.5): the `fuel_balance_window` store and its read port.

`transaction` runs one assessment in one transaction: `known_at` (`clock_timestamp()`, or the test-only override) is
taken first, then the Site's timezone and assets, the per-night advisory lock, the latest revision, the fuel records
(K2's `select_fuel_records` on this connection) and the declared tank and no-load-basis properties. Readings, SFC and
the no-load rate are read through `PostgresActionStore` with the same `known_at`; those reads are as-known filtered on
append-only rows, so they need no shared snapshot. A row is inserted only when its inputs digest differs from the
latest revision's. The read port reads in one `REPEATABLE READ READ ONLY` transaction.

DIESEL-K4a adds `night_window_on` (the Finding service's clock, lock and window read on its own connection) and the
`FuelFindingReadPort` reads (`fuel_findings`, `fuel_finding`), read-only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from assetops_backend import read_scope
from assetops_backend.actions.verification_rules import Reading, parse_exact
from assetops_backend.fuel_balance.model import (
    FINDINGS_REFUSED, PARAMETER_VERSION, WINDOWS_REFUSED, FuelBalanceWindow, FuelFinding)
from assetops_backend.work.fuel_records import FuelRecord

#: K2's `select_fuel_records(c, tenant, site, tank, lo, hi, known_at)`, injected by the composition (rule 1: only
#: `work/composition.py` may import `work.adapters`); it runs on this store's connection.
FuelRecordsOnConnection = Callable[[Connection, UUID, UUID, UUID, datetime, datetime, datetime],
                                   tuple[FuelRecord, ...]]

_COLUMNS = ("id, tenant_id, site_id, tank_asset_id, generator_asset_id, night_date, window_start, window_end, "
            "revision, parameter_version, recorded_at, state, reason, residual_low, residual_high, gap_minutes, "
            "gap_spans, limitations, terms, evidence_ids, record_ids, input_sha256")

# The `_generator_property_history` shape (postgres_action_store.py:647-670): each FoundationRevision overlapping
# `[lo, hi)` as known at `k`.
_REVISIONS = ("SELECT id, valid_from, valid_to, content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
              "AND valid_from < :hi AND (valid_to IS NULL OR valid_to > :lo) AND recorded_at <= :k "
              "AND (superseded_at IS NULL OR superseded_at > :k) ORDER BY valid_from")


@dataclass(frozen=True)
class AssetRow:
    id: str
    asset_code: str
    asset_type: str


@dataclass(frozen=True)
class PropertyRevision:
    """One FoundationRevision's properties of one component: `values[key]` = every `(value, unit)` declared."""

    revision_id: str
    valid_from: datetime
    valid_to: datetime | None
    values: dict[str, list[tuple[Any, Any]]]


def _utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


def _time(text_value: str) -> datetime:
    return datetime.fromisoformat(text_value.replace("Z", "+00:00")).astimezone(timezone.utc)


def to_window(row: Any) -> FuelBalanceWindow:
    m = row._mapping
    return FuelBalanceWindow(
        id=m["id"], tenant_id=m["tenant_id"], site_id=m["site_id"], tank_asset_id=m["tank_asset_id"],
        generator_asset_id=m["generator_asset_id"], night_date=m["night_date"],
        window_start=_utc(m["window_start"]), window_end=_utc(m["window_end"]), revision=m["revision"],
        parameter_version=m["parameter_version"], recorded_at=_utc(m["recorded_at"]), state=m["state"],
        reason=m["reason"], residual_low=parse_exact(m["residual_low"]), residual_high=parse_exact(m["residual_high"]),
        gap_minutes=m["gap_minutes"], gap_spans=tuple((_time(a), _time(b)) for a, b in m["gap_spans"]),
        limitations=tuple(m["limitations"]), terms=dict(m["terms"]), evidence_ids=tuple(m["evidence_ids"]),
        record_ids=tuple((a, b) for a, b in m["record_ids"]), input_sha256=m["input_sha256"])


class _Tx:
    """One assessment transaction; every read uses `known_at`."""

    def __init__(self, c: Connection, actions: Any, fuel_records: FuelRecordsOnConnection, tenant_id: UUID,
                 site_id: UUID, known_at: datetime) -> None:
        self.c, self._actions, self.tenant_id, self.site_id, self.known_at = c, actions, tenant_id, site_id, known_at
        self._fuel_records = fuel_records
        self._p = {"t": tenant_id, "s": site_id}

    def timezone(self) -> str | None:
        return self.c.execute(text("SELECT timezone FROM site WHERE tenant_id = :t AND id = :s"), self._p).scalar()

    def active_assets(self) -> list[AssetRow]:
        return [AssetRow(str(r.id), r.asset_code, r.asset_type) for r in self.c.execute(text(
            "SELECT id, asset_code, asset_type FROM asset WHERE tenant_id = :t AND site_id = :s AND retired_at IS NULL "
            "ORDER BY asset_code"), self._p)]

    def lock(self, tank_asset_id: str, night_date: date) -> None:
        self.c.execute(text("SELECT pg_advisory_xact_lock(hashtext('fuel-balance:' || :s || ':' || :a || ':' || :d))"),
                       {"s": str(self.site_id), "a": str(tank_asset_id), "d": night_date.isoformat()})

    def latest(self, tank_asset_id: str, night_date: date) -> FuelBalanceWindow | None:
        row = self.c.execute(text(
            f"SELECT {_COLUMNS} FROM fuel_balance_window WHERE tenant_id = :t AND site_id = :s AND tank_asset_id = :a "
            "AND night_date = :d ORDER BY revision DESC LIMIT 1"), {**self._p, "a": tank_asset_id, "d": night_date}
        ).first()
        return None if row is None else to_window(row)

    def fuel_records(self, tank_asset_id: str, lo: datetime, hi: datetime) -> tuple[FuelRecord, ...]:
        return self._fuel_records(self.c, self.tenant_id, self.site_id, UUID(str(tank_asset_id)), lo, hi,
                                  self.known_at)

    def properties(self, asset_code: str, keys: tuple[str, ...], lo: datetime, hi: datetime
                   ) -> list[PropertyRevision]:
        out = []
        for r in self.c.execute(text(_REVISIONS), {**self._p, "lo": lo, "hi": hi, "k": self.known_at}):
            values: dict[str, list[tuple[Any, Any]]] = {k: [] for k in keys}
            for comp in (r.content or {}).get("components") or ():
                if str(comp.get("component_id")) != str(asset_code):
                    continue
                for p in comp.get("properties") or ():
                    if p.get("property_key") in values:
                        values[p["property_key"]].append((p.get("value"), p.get("unit")))
            out.append(PropertyRevision(str(r.id), _utc(r.valid_from), None if r.valid_to is None else _utc(r.valid_to),
                                        values))
        return out

    def readings(self, lo: datetime, hi: datetime, roles: tuple[str, ...]) -> list[Reading]:
        """Accepted evidence of these roles touching `[lo, hi]` as accepted by `known_at`, as
        `verification_rules.Reading` exactly as `actions/verification.py:653-658` builds them."""
        return [Reading(id=str(r["id"]), role=r["role"], asset_id=None if r["asset_id"] is None else str(r["asset_id"]),
                        measurement=r["measurement"], source_time=r["source_time"],
                        interval_start=r["interval_start"], interval_end=r["interval_end"],
                        value_text=r["normalized_value_text"], unit=r["normalized_unit"], quality=r["quality"])
                for r in self._actions.window_readings(self.tenant_id, self.site_id, lo, hi, list(roles),
                                                       self.known_at)]

    def sfc_history(self, generator_asset_id: str, lo: datetime, hi: datetime) -> list[Any]:
        return self._actions.sfc_history(self.tenant_id, self.site_id, generator_asset_id, lo, hi, self.known_at)

    def no_load_history(self, generator_asset_id: str, lo: datetime, hi: datetime) -> list[Any]:
        return self._actions.no_load_history(self.tenant_id, self.site_id, generator_asset_id, lo, hi, self.known_at)

    def append(self, latest: FuelBalanceWindow | None, row: dict[str, Any]) -> FuelBalanceWindow:
        values = {**row, "id": uuid4(), "t": self.tenant_id, "s": self.site_id,
                  "revision": 1 if latest is None else latest.revision + 1, "recorded_at": self.known_at,
                  "parameter_version": PARAMETER_VERSION}
        for key in ("gap_spans", "limitations", "terms", "evidence_ids", "record_ids"):
            values[key] = json.dumps(values[key], sort_keys=True)
        inserted = self.c.execute(text(
            "INSERT INTO fuel_balance_window (id, tenant_id, site_id, tank_asset_id, generator_asset_id, night_date, "
            "window_start, window_end, revision, parameter_version, recorded_at, state, reason, residual_low, "
            "residual_high, gap_minutes, gap_spans, limitations, terms, evidence_ids, record_ids, input_sha256) "
            "VALUES (:id, :t, :s, :tank_asset_id, :generator_asset_id, :night_date, :window_start, :window_end, "
            ":revision, :parameter_version, :recorded_at, :state, :reason, :residual_low, :residual_high, "
            ":gap_minutes, CAST(:gap_spans AS jsonb), CAST(:limitations AS jsonb), CAST(:terms AS jsonb), "
            f"CAST(:evidence_ids AS jsonb), CAST(:record_ids AS jsonb), :input_sha256) RETURNING {_COLUMNS}"),
            values).one()
        return to_window(inserted)


class PostgresFuelBalanceStore:
    """The `fuel_balance_window` writer (`transaction`) and `FuelBalanceReadPort` (`windows`, `window`)."""

    def __init__(self, database_url: str | None, *, actions: Any, fuel_records: FuelRecordsOnConnection,
                 statement_timeout_ms: int = 30_000, lock_timeout_ms: int = 5_000,
                 test_db_clock_override: Callable[[], datetime] | None = None) -> None:
        """`actions` is the Action store (`window_readings`, `sfc_history`, `no_load_history`) and `fuel_records` K2's
        caller-connection read, both injected by `fuel_balance/composition.py`."""
        self._database_url = database_url
        # Test-only virtual DB instant (the Work store's seam); production composition never passes it.
        self.test_db_clock_override = test_db_clock_override
        self._options = f"-c statement_timeout={int(statement_timeout_ms)} -c lock_timeout={int(lock_timeout_ms)}"
        self._engine: Engine | None = None
        self._actions = actions
        self._fuel_records = fuel_records

    def _connect(self) -> Engine:
        if not self._database_url:
            raise RuntimeError("DATABASE_URL is not set, so the fuel balance store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True,
                                         connect_args={"options": self._options})
        return self._engine

    def dispose(self) -> None:
        self._actions.dispose()
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def transaction(self, tenant_id: UUID, site_id: UUID, work: Callable[[_Tx], Any]) -> Any:
        with self._connect().begin() as c:
            known_at = (self.test_db_clock_override() if self.test_db_clock_override is not None
                        else c.execute(text("SELECT clock_timestamp()")).scalar_one())
            known_at = _utc(known_at)
            assert known_at.utcoffset() == timedelta(0)
            return work(_Tx(c, self._actions, self._fuel_records, tenant_id, site_id, known_at))

    def site_by_code(self, site_code: str) -> tuple[UUID, UUID] | None:
        with self._connect().connect() as c:
            rows = c.execute(text("SELECT tenant_id, id FROM site WHERE site_code_key = lower(:c)"),
                             {"c": site_code}).all()
        return (rows[0].tenant_id, rows[0].id) if len(rows) == 1 else None

    # --- FuelBalanceReadPort -----------------------------------------------------------------------------------

    def _read(self, work: Callable[[Connection], Any]) -> Any:
        with self._connect().connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            c.execute(text("SET TRANSACTION READ ONLY"))
            return work(c)

    def windows(self, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID, lo: date, hi: date,
                known_at: datetime) -> tuple[FuelBalanceWindow, ...]:
        if (not isinstance(lo, date) or not isinstance(hi, date) or isinstance(lo, datetime)
                or isinstance(hi, datetime) or not lo < hi or not isinstance(known_at, datetime)
                or known_at.tzinfo is None or known_at.utcoffset() != timedelta(0)):
            raise ValueError(WINDOWS_REFUSED)
        return self._read(lambda c: tuple(to_window(r) for r in c.execute(text(
            f"SELECT DISTINCT ON (night_date) {_COLUMNS} FROM fuel_balance_window WHERE tenant_id = :t "
            "AND site_id = :s AND tank_asset_id = :a AND night_date >= :lo AND night_date < :hi "
            "AND recorded_at <= :k ORDER BY night_date, revision DESC"),
            {"t": tenant_id, "s": site_id, "a": tank_asset_id, "lo": lo, "hi": hi, "k": known_at})))

    def has_windows(self, tenant_id: UUID, site_id: UUID, known_at: datetime) -> bool:
        """DIESEL-K5 (§9l.2): whether the Site has at least one stored window as known at `known_at` (the Fuel
        page's night mode; read-only)."""
        return bool(self._read(lambda c: c.execute(text(
            "SELECT EXISTS (SELECT 1 FROM fuel_balance_window WHERE tenant_id = :t AND site_id = :s "
            "AND recorded_at <= :k)"), {"t": tenant_id, "s": site_id, "k": known_at}).scalar_one()))

    def night_context(self, tenant_id: UUID, site_id: UUID) -> tuple[str | None, str | None, datetime]:
        """DIESEL-K5 (§9l.2): the Site's time zone, its one active fuel tank (None unless exactly one) and the read
        instant (`clock_timestamp()` through `read_scope`), on one read-only snapshot."""
        def work(c: Connection) -> tuple[str | None, str | None, datetime]:
            p = {"t": tenant_id, "s": site_id}
            tz = c.execute(text("SELECT timezone FROM site WHERE tenant_id = :t AND id = :s"), p).scalar_one_or_none()
            tanks = c.execute(text("SELECT id FROM asset WHERE tenant_id = :t AND site_id = :s "
                                   "AND asset_type = 'FUEL_TANK' AND retired_at IS NULL"), p).scalars().all()
            now = read_scope.read_instant(c.execute(text("SELECT clock_timestamp()")).scalar_one())
            return tz, (str(tanks[0]) if len(tanks) == 1 else None), _utc(now)
        return self._read(work)

    def night_records_and_provenance(self, tenant_id: UUID, site_id: UUID, windows: list[FuelBalanceWindow],
                                     known_at: datetime, records_of: FuelBalanceWindow | None,
                                     link_rows: Any) -> tuple[list[FuelRecord], dict[str, Any]]:
        """DIESEL-K5 (§9l.2): on one read-only snapshot, K2's fuel records occurring in `records_of`'s window as known
        at `known_at` (none when `records_of` is None) and the mini-depth provenance blocks (`mini_blocks`, reused) with
        the windows' ids as the basis selection and their evidence ids as the cited set."""
        from assetops_backend.mini_depth.provenance import mini_blocks

        def work(c: Connection) -> tuple[list[FuelRecord], dict[str, Any]]:
            records = [] if records_of is None else list(self._fuel_records(
                c, tenant_id, site_id, records_of.tank_asset_id, records_of.window_start, records_of.window_end,
                known_at))
            blocks = mini_blocks(c, link_rows, tenant_id, site_id, selected_revision_ids=[w.id for w in windows],
                                 selected_evidence_ids=[i for w in windows for i in w.evidence_ids],
                                 pending_evidence_ids=None)
            return records, blocks
        return self._read(work)

    def window(self, tenant_id: UUID, site_id: UUID, window_id: UUID) -> FuelBalanceWindow | None:
        def work(c):
            row = c.execute(text(f"SELECT {_COLUMNS} FROM fuel_balance_window WHERE tenant_id = :t AND site_id = :s "
                                 "AND id = :i"), {"t": tenant_id, "s": site_id, "i": window_id}).first()
            return None if row is None else to_window(row)
        return self._read(work)

    # --- DIESEL-K4a (§9j.5, §9j.6): the unexplained-fuel Finding ---------------------------------------------

    def night_window_on(self, c: Connection, tenant_id: UUID, site_id: UUID,
                        night_date: date) -> tuple[datetime, FuelBalanceWindow | None]:
        """On the Finding service's connection: `known_at` (`clock_timestamp()` or the test-only override), the
        per-night Finding lock, and the night's latest window revision as known at `known_at` (None when none)."""
        known_at = _utc(self.test_db_clock_override() if self.test_db_clock_override is not None
                        else c.execute(text("SELECT clock_timestamp()")).scalar_one())
        c.execute(text("SELECT pg_advisory_xact_lock(hashtext('fuel-finding:' || :s || ':' || :d))"),
                  {"s": str(site_id), "d": night_date.isoformat()})
        row = c.execute(text(
            f"SELECT {_COLUMNS} FROM fuel_balance_window WHERE tenant_id = :t AND site_id = :s AND night_date = :d "
            "AND recorded_at <= :k ORDER BY recorded_at DESC, revision DESC LIMIT 1"),
            {"t": tenant_id, "s": site_id, "d": night_date, "k": known_at}).first()
        return known_at, None if row is None else to_window(row)

    def _fuel_findings(self, c: Connection, tenant_id: UUID, site_id: UUID, finding_id: UUID | None,
                       known_at: datetime | None) -> list[FuelFinding]:
        p = {"t": tenant_id, "s": site_id, "f": None if finding_id is None else str(finding_id), "k": known_at}
        heads = c.execute(text(
            "SELECT DISTINCT ON (f.id) f.id AS finding_id, r.id AS revision_id, r.revision_no, r.lifecycle, r.claim, "
            "r.created_at, r.episode_start, r.episode_end FROM finding f JOIN finding_revision r "
            "ON r.tenant_id = f.tenant_id AND r.site_id = f.site_id AND r.finding_id = f.id "
            "WHERE f.tenant_id = :t AND f.site_id = :s AND f.domain = 'fuel_balance' "
            "AND (CAST(:f AS uuid) IS NULL OR f.id = CAST(:f AS uuid)) "
            "AND (CAST(:k AS timestamptz) IS NULL OR r.created_at <= CAST(:k AS timestamptz)) "
            "ORDER BY f.id, r.revision_no DESC"), p).all()
        out = []
        for h in heads:
            w = c.execute(text(f"SELECT {_COLUMNS} FROM fuel_balance_window WHERE tenant_id = :t AND site_id = :s "
                               "AND id = :i"), {**p, "i": h.claim["fuel_balance_window_id"]}).one()
            row = c.execute(text(
                "SELECT * FROM fuel_residual_consequence_revision WHERE tenant_id = :t AND site_id = :s "
                "AND finding_revision_id = :r"), {**p, "r": h.revision_id}).first()
            consequence = None if row is None else {
                k: (None if v is None else v if isinstance(v, datetime) else str(v)) for k, v in row._mapping.items()}
            window = to_window(w)
            out.append(FuelFinding(h.finding_id, h.revision_id, h.revision_no, h.lifecycle, window.night_date, window,
                                   consequence, _utc(h.created_at)))
        return out

    @staticmethod
    def _instant(value: Any) -> bool:
        return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() == timedelta(0)

    def fuel_findings(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                      known_at: datetime | None) -> tuple[FuelFinding, ...]:
        """The latest revision per fuel Finding as known at `known_at` (None = now) whose cited window intersects
        `[lo, hi)`, ordered by night."""
        if (not self._instant(lo) or not self._instant(hi) or not lo < hi
                or (known_at is not None and not self._instant(known_at))):
            raise ValueError(FINDINGS_REFUSED)
        found = self._read(lambda c: self._fuel_findings(c, tenant_id, site_id, None, known_at))
        kept = [f for f in found if f.window.window_start < hi and f.window.window_end > lo]
        return tuple(sorted(kept, key=lambda f: (f.night_date, str(f.finding_id))))

    def fuel_finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID,
                     known_at: datetime | None) -> FuelFinding | None:
        if known_at is not None and not self._instant(known_at):
            raise ValueError(FINDINGS_REFUSED)
        found = self._read(lambda c: self._fuel_findings(c, tenant_id, site_id, finding_id, known_at))
        return found[0] if found else None
