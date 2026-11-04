"""CH-1a and CH-2: the composition root of the chain (day snapshots, threads); the only importer of its adapters.

The chain input reader receives the existing read services built by their own domains' composition functions
(guard rule 1: no other domain's adapters are imported here).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from assetops_backend.chain.adapters.file_chain_config import (
    load_coverage_policy,
    load_event_register,
    load_operating_calendar,
    load_thread_lifecycle,
)
from assetops_backend.chain.adapters.postgres_event_store import EventStoreUnavailable, PostgresEventStore
from assetops_backend.chain.adapters.postgres_chain_inputs import PostgresChainInputs
from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
from assetops_backend.chain.adapters.postgres_thread_sources import PostgresThreadSources
from assetops_backend.chain.adapters.postgres_thread_store import PostgresThreadStore, ThreadStoreUnavailable
from assetops_backend.chain.builder import SnapshotBuilder
from assetops_backend.chain.measure_impls import build_measure_set
from assetops_backend.chain.reader import SnapshotReader

__all__ = ["load_coverage_policy", "load_operating_calendar", "ChainServices", "build_chain_services",
           "build_chain_inputs", "build_snapshot_store", "build_snapshot_reader", "build_snapshot_builder",
           "PostgresThreadSources", "PostgresThreadStore", "ThreadStoreUnavailable", "build_thread_sources",
           "build_thread_store", "load_event_register", "PostgresEventStore", "EventStoreUnavailable",
           "build_event_store"]


def build_snapshot_store(database_url: str | None) -> PostgresSnapshotStore | None:
    return PostgresSnapshotStore(database_url) if database_url else None


def build_snapshot_reader(database_url: str | None) -> SnapshotReader | None:
    store = build_snapshot_store(database_url)
    return None if store is None else SnapshotReader(store)


def build_chain_inputs(database_url: str) -> PostgresChainInputs:
    from assetops_backend.analytics.composition import (
        build_cold_read_service,
        build_dispatch_read_service,
        build_ev_read_service,
    )
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.financials.composition import (
        build_assumption_read_service,
        build_ev_site_read_service,
    )
    from assetops_backend.mini_depth.read import MiniDepthRead

    return PostgresChainInputs(
        database_url, mini=MiniDepthRead.from_url(database_url, build_link_rows_reader()),
        assumptions=build_assumption_read_service(database_url),
        dispatch=build_dispatch_read_service(database_url), cold=build_cold_read_service(database_url),
        ev_reads=build_ev_read_service(database_url), ev_site=build_ev_site_read_service(database_url))


def build_snapshot_builder(database_url: str, inputs: Any = None,
                           store: PostgresSnapshotStore | None = None) -> SnapshotBuilder:
    """The builder over the given (or a new) store and the given (or the real) chain input reader."""
    return SnapshotBuilder(store or PostgresSnapshotStore(database_url),
                           build_measure_set(build_chain_inputs(database_url) if inputs is None else inputs),
                           load_coverage_policy(), load_operating_calendar())


@dataclass
class ChainServices:
    builder: SnapshotBuilder
    reader: SnapshotReader
    inputs: Any
    dispose: Callable[[], None]
    events: Any = None  # CH-1b: the event store (the backfill records its `backfill.site` provenance event)


def build_chain_services(database_url: str | None) -> ChainServices | None:
    """The CLI's services on one store; None without a database URL."""
    if not database_url:
        return None
    store = PostgresSnapshotStore(database_url)
    inputs = build_chain_inputs(database_url)
    builder = build_snapshot_builder(database_url, inputs, store)
    events = PostgresEventStore(database_url)

    def dispose() -> None:
        inputs.dispose()
        store.dispose()
        events.dispose()

    return ChainServices(builder, SnapshotReader(store), inputs, dispose, events)


def build_thread_store(database_url: str | None) -> PostgresThreadStore | None:
    return PostgresThreadStore(database_url) if database_url else None


def build_thread_sources(database_url: str | None) -> PostgresThreadSources | None:
    """The read-only source reader, or None when no database is configured (the board then reads no threads)."""
    return PostgresThreadSources(database_url) if database_url else None


def build_event_store(database_url: str | None) -> PostgresEventStore | None:
    """CH-1b: the outbox consumer, dirty queue and backfill-event store; None without a database URL."""
    return PostgresEventStore(database_url) if database_url else None


def thread_lifecycle_policy() -> Any:
    """CH-3: the thread lifecycle policy (`config/chain/thread-lifecycle-v1.json`), for callers outside the adapters."""
    from assetops_backend.chain.adapters.file_chain_config import load_thread_lifecycle
    return load_thread_lifecycle()


def build_chain_reader(database_url: str | None, *, consequences: Any = None,
                       verification: Callable[..., Any] | None = None) -> Any:
    """CH-5a1 §A2: the board's ChainReader, or None without a database. `consequences` is the overview's own
    consequence read (`site_overview.upstream.consequence_read`, pre-flight P6); the reader never disposes it.
    Returns `(reader, dispose)`, `dispose` releasing only the engines this function opened."""
    if not database_url:
        return None, (lambda: None)
    from fastapi.encoders import jsonable_encoder
    from uuid import UUID

    from assetops_backend.chain.adapters.postgres_chain_read import PostgresChainRead
    from assetops_backend.chain.read import ChainReader
    from assetops_backend.site_overview.read import stored_source

    store = PostgresSnapshotStore(database_url)
    port = PostgresChainRead(database_url, snapshots=SnapshotReader(store))

    money = None
    if consequences is not None:
        def money(t: Any, s: Any, fid: str, rid: str, is_latest: bool, source_open: bool) -> Any:
            body = consequences.read(t, s, UUID(fid), UUID(rid), finding_revision_is_latest=is_latest,
                                     source_open=source_open, limit=1) or {}
            return {"body": jsonable_encoder(body), "source": jsonable_encoder(stored_source(body, t, s, rid))}

    def dispose() -> None:
        port.dispose()
        store.dispose()

    return ChainReader(port, verification=verification, money=money), dispose


def chain_policy_versions() -> dict[str, str | None]:
    """CH-5a2a §B1: the `policy_versions` of the `outcome-chain-1` bodies, from the loaded chain configuration (the
    status policy is the board's, added by `chain_api`). Injected into `chain_api.build_chain_router`."""
    return {"coverage": load_coverage_policy().policy_version,
            "register": load_event_register().register_version,
            "lifecycle": load_thread_lifecycle().policy_version}
