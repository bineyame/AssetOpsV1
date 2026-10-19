"""Persisted Foundation use cases: import, time-valid read, publish (S1-01).

Pure orchestration over the injected `FoundationStore`; no storage technology
is named here. Times are resolved on the server: a caller may name `at`
(valid time) and `knowledge_at` (recorded time), and both default to the
server clock. A read never substitutes the current configuration for a
period that has none.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence
from uuid import UUID, uuid4

from assetops_backend.sites.binding_alignment import finalize
from assetops_backend.sites.ev_foundation import (
    EV_CONFIGURATION_INVALID,
    EV_SITE_TYPE,
    validate_ev_schedule_interval,
)
from assetops_backend.sites.foundation_content import (
    CONTENT_SCHEMA_VERSION,
    RESERVE_UNIT,
    battery_reserve,
    content_digest,
    content_from_record,
    parse_utc_text,
    record_at,
    with_battery_reserve,
    with_component_properties,
)
from assetops_backend.sites.foundation_records import (
    AssetRow,
    BindingSetRevisionRow,
    ConfigurationPlan,
    ConfigurationState,
    FoundationSiteCodeTaken,
    FoundationSiteNotFound,
    FoundationStore,
    GatewayRow,
    ImportPlan,
    ImportRecord,
    PublishPlan,
    Registrations,
    RevisionRow,
    SourceRow,
    StoredSite,
    TenantRef,
)
from assetops_backend.sites.identity import site_id_key
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import SiteConfigurationInvalid

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _forever_after(value: datetime | None) -> datetime:
    return value if value is not None else datetime.max.replace(tzinfo=timezone.utc)


def binding_set_at(
    sets: Sequence[BindingSetRevisionRow], at: datetime, knowledge_at: datetime
) -> BindingSetRevisionRow | None:
    """The one binding set revision whose valid AND recorded intervals contain both instants."""
    matches = [
        row
        for row in sets
        if row.valid_from <= at < _forever_after(row.valid_to)
        and row.recorded_at <= knowledge_at < _forever_after(row.superseded_at)
    ]
    return matches[0] if len(matches) == 1 else None


def revision_at(
    revisions: Sequence[RevisionRow], at: datetime, knowledge_at: datetime
) -> RevisionRow | None:
    """The one revision whose valid AND recorded intervals contain both instants."""
    matches = [
        row
        for row in revisions
        if row.valid_from <= at < _forever_after(row.valid_to)
        and row.recorded_at <= knowledge_at < _forever_after(row.superseded_at)
    ]
    return matches[0] if len(matches) == 1 else None


class FoundationRefused(Exception):
    """A Foundation request refused with a code a client switches on."""

    def __init__(self, code: str, message: str, *, status: int,
                 current_revision_id: UUID | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        #: The covering revision found under the Site lock, when a change was refused there (S6-01a).
        self.current_revision_id = current_revision_id


# --- import ------------------------------------------------------------------


@dataclass(frozen=True)
class ImportSource:
    """One strictly parsed Site document and the bytes it came from."""

    path: str
    sha256: str
    record: SiteRecord
    document_format: str = "ASSETOPS_SITE_YAML"


@dataclass(frozen=True)
class LegacyDocument:
    """A Site document the legacy YAML stores hold: its code, path and digest."""

    site_code: str
    path: str
    sha256: str


class ImportConflict(Exception):
    """The import needs an explicit reconciliation; nothing was written."""


@dataclass(frozen=True)
class ImportResult:
    tenant: TenantRef
    site: StoredSite
    revision: RevisionRow
    registrations: Registrations
    created: bool


def _value_refusal_code(site_type: str) -> str:
    """W2-05a: an EV_CHARGING Foundation document refused for any value, topology or schedule rule is an EV
    configuration error; every other Site type keeps `FOUNDATION_VALUE_INVALID`."""
    return EV_CONFIGURATION_INVALID if site_type == EV_SITE_TYPE else "FOUNDATION_VALUE_INVALID"


def _check_ev_interval(site_type: str, record: Any, valid_from: datetime, valid_to: datetime | None,
                       source: str) -> None:
    """W2-05a: the connector enable schedule against the Site zone over this revision's effective interval."""
    if site_type == EV_SITE_TYPE:
        validate_ev_schedule_interval(record.foundation, timezone_name=record.timezone, valid_from=valid_from,
                                      valid_to=valid_to, source=source)


def plan_import(tenant: TenantRef, source: ImportSource, now: datetime) -> ImportPlan:
    record = source.record
    foundation = record.foundation
    _check_ev_interval(record.site_type, record, parse_utc_text(foundation.valid_from), None, source.path)
    site_id = uuid4()
    site = StoredSite(
        id=site_id,
        tenant_id=tenant.id,
        site_code=record.site_id,
        name=record.display_name,
        site_type=record.site_type,
        timezone=record.timezone,
        lifecycle=record.lifecycle_status,
        country=record.location.country,
        locality=record.location.locality,
        origin=record.origin,
        proposed_source_mode=record.source.mode,
        template_id=None if record.template is None else record.template.template_id,
        template_version=None if record.template is None else record.template.template_version,
        created_at=now,
        import_record=ImportRecord(
            id=uuid4(),
            source_path=source.path,
            source_sha256=source.sha256,
            source_format=source.document_format,
            imported_at=now,
        ),
    )
    content = content_from_record(record)
    assets: list[AssetRow] = []
    asset_by_code: dict[str, UUID] = {}
    for component in content["components"]:
        asset_id = uuid4()
        asset_by_code[component["component_id"]] = asset_id
        assets.append(
            AssetRow(
                id=asset_id,
                asset_code=component["component_id"],
                asset_type=component["component_type"],
                attributes={
                    "display_name": component["display_name"],
                    "rating": component["rating"],
                    "properties": component["properties"],
                    "registered_from": "IMPORT",
                },
            )
        )
    gateway = GatewayRow(
        id=uuid4(),
        gateway_external_id=f"edge-{record.site_id.lower()}",
        mode=record.source.mode,
        credential_ref=None,
        registered_at=now,
        disabled_at=now,
    )
    sources: list[SourceRow] = []
    for device in content.get("devices") or ():
        if device["component_id"] not in asset_by_code:
            raise SiteConfigurationInvalid(
                f"Device {device['device_id']!r} names component "
                f"{device['component_id']!r}, which is not part of this Site."
            )
        sources.append(
            SourceRow(
                id=uuid4(),
                gateway_id=gateway.id,
                source_external_id=device["device_id"],
                device_kind=device["device_type"],
                asset_id=asset_by_code[device["component_id"]],
                registered_at=now,
                disabled_at=now,
            )
        )
    revision = RevisionRow(
        id=uuid4(),
        version=foundation.version,
        valid_from=parse_utc_text(foundation.valid_from),
        valid_to=None,
        recorded_at=now,
        superseded_at=None,
        schema_version=CONTENT_SCHEMA_VERSION,
        content=content,
        content_sha256=content_digest(content),
        origin="IMPORT",
        derived_from_revision_id=None,
        change_note=f"Imported from {source.path} (sha256 {source.sha256})",
    )
    return ImportPlan(site, tuple(assets), gateway, tuple(sources), revision)


def import_site(
    store: FoundationStore,
    *,
    tenant_slug: str,
    configured_tenant_slug: str,
    source: ImportSource,
    legacy_documents: Sequence[LegacyDocument],
    clock: Clock = utc_now,
) -> ImportResult:
    """Import one Site document, idempotently for the same path and digest."""
    if tenant_slug != configured_tenant_slug:
        raise ImportConflict(
            f"Tenant {tenant_slug!r} is not the configured development tenant "
            f"{configured_tenant_slug!r}. Importing a Site into a different tenant "
            "is a conflict that needs explicit reconciliation."
        )
    code = source.record.site_id
    for document in legacy_documents:
        if site_id_key(document.site_code) == site_id_key(code) and document.path != source.path:
            raise ImportConflict(
                f"Site code {code!r} is also declared by {document.path}, a different "
                f"document from {source.path}. Reconcile the two before importing."
            )
    now = clock()
    tenant = store.ensure_tenant(tenant_slug, "Development tenant", now=now)
    existing = store.find_site(tenant.id, code)
    if existing is not None:
        registered = existing.import_record
        if registered is None or registered.source_path != source.path:
            raise ImportConflict(
                f"Site code {code!r} already exists in tenant {tenant_slug!r} "
                f"from {registered.source_path if registered else 'no import'}; "
                f"{source.path} is a different source."
            )
        if registered.source_sha256 != source.sha256:
            raise ImportConflict(
                f"{source.path} has changed since it was imported (registered sha256 "
                f"{registered.source_sha256}, now {source.sha256}). The Postgres Site "
                "is not overwritten; reconcile the change explicitly."
            )
        revisions = store.revisions(tenant.id, existing.id)
        original = next(r for r in revisions if r.origin == "IMPORT")
        return ImportResult(
            tenant, existing, original, store.registrations(tenant.id, existing.id), False
        )
    plan = plan_import(tenant, source, now)
    try:
        store.insert_import(tenant.id, plan)
    except FoundationSiteCodeTaken as error:
        raise ImportConflict(str(error)) from error
    stored = store.find_site(tenant.id, code)
    assert stored is not None
    return ImportResult(
        tenant, stored, plan.revision, store.registrations(tenant.id, stored.id), True
    )


# --- read and publish ----------------------------------------------------------


@dataclass(frozen=True)
class FoundationView:
    tenant: TenantRef
    site: StoredSite
    at: datetime
    knowledge_at: datetime
    now: datetime
    revision: RevisionRow
    revisions: tuple[RevisionRow, ...]
    registrations: Registrations
    record: SiteRecord
    #: Every binding set revision of the Site, and the one effective at
    #: (`at`, `knowledge_at`), or None when no binding set is in effect (S1-02).
    binding_sets: tuple[BindingSetRevisionRow, ...] = ()
    binding_set: BindingSetRevisionRow | None = None


@dataclass(frozen=True)
class PublishResult:
    site: StoredSite
    plan: PublishPlan
    changed: RevisionRow
    configuration: ConfigurationPlan | None = None


@dataclass(frozen=True)
class CallerTransaction:
    """S6-01a: one S1 publish inside a caller-owned transaction (the Action adapter's).

    `connection` is the caller's open connection; S1 neither begins nor commits on it. `then` receives
    `written_ids(plan)` on that connection after the S1 writes. `recorded_at` is the caller's server instant,
    used as the publish's recorded time so the Foundation rows and the caller's rows share one instant.
    """

    connection: Any
    then: Callable[[dict[str, Any]], None]
    recorded_at: datetime


def written_ids(plan: ConfigurationPlan) -> dict[str, Any]:
    """Every Foundation and binding set revision ID one publication superseded or inserted."""
    inserted = plan.revision_inserts
    return {
        "superseded_foundation_revision_ids": list(plan.supersede_revision_ids),
        "publish_foundation_revision_ids": [r.id for r in inserted if r.origin == "PUBLISH"],
        "split_foundation_revision_ids": [r.id for r in inserted if r.origin == "SPLIT"],
        "superseded_binding_set_revision_ids": list(plan.supersede_binding_set_ids),
        "inserted_binding_set_revision_ids": [r.id for r in plan.binding_set_inserts],
        "superseded_at": plan.superseded_at,
    }


class FoundationService:
    """Tenant-scoped Foundation reads and the narrow S1 publish."""

    def __init__(self, store: FoundationStore, tenant_slug: str, clock: Clock = utc_now) -> None:
        self._store = store
        self._tenant_slug = tenant_slug
        self._clock = clock

    @property
    def store(self) -> FoundationStore:
        return self._store

    def tenant(self) -> TenantRef:
        return self._store.resolve_tenant(self._tenant_slug)

    def now(self) -> datetime:
        return self._clock()

    @property
    def clock(self) -> Clock:
        return self._clock

    def site(self, tenant: TenantRef, site_code: str) -> StoredSite | None:
        return self._store.find_site(tenant.id, site_code)

    def read(
        self, site: StoredSite, tenant: TenantRef, at: datetime | None, knowledge_at: datetime | None
    ) -> FoundationView:
        now = self._clock()
        resolved_at = now if at is None else at
        resolved_knowledge = now if knowledge_at is None else knowledge_at
        revisions = tuple(self._store.revisions(tenant.id, site.id))
        revision = revision_at(revisions, resolved_at, resolved_knowledge)
        if revision is None:
            raise FoundationRefused(
                "FOUNDATION_REVISION_NOT_FOUND",
                f"No Foundation revision of {site.site_code} is effective at "
                f"{resolved_at.isoformat()} as recorded at {resolved_knowledge.isoformat()}. "
                "The current configuration is not substituted.",
                status=404,
            )
        binding_sets = tuple(self._store.binding_sets(tenant.id, site.id))
        return FoundationView(
            tenant=tenant,
            site=site,
            at=resolved_at,
            knowledge_at=resolved_knowledge,
            now=now,
            revision=revision,
            revisions=revisions,
            registrations=self._store.registrations(tenant.id, site.id),
            record=record_at(site, revision),
            binding_sets=binding_sets,
            binding_set=binding_set_at(binding_sets, resolved_at, resolved_knowledge),
        )

    def publish_battery_reserve(
        self,
        tenant: TenantRef,
        site: StoredSite,
        *,
        asset_code: str,
        value: float,
        effective_from: datetime,
        note: str | None,
        expected_revision_id: UUID | None = None,
        expected_value: float | None = None,
        caller: CallerTransaction | None = None,
    ) -> PublishResult:
        """Publish a battery reserve, in its own transaction or (S6-01a) inside a caller's.

        `D-2026-10-15-s601-action-store-and-ui` M1: with `caller`, the publish uses the caller's connection
        without opening or committing a transaction, checks `expected_revision_id` (the covering revision)
        and `expected_value` (its reserve) under the Site lock, and hands every written and superseded ID to
        `caller.then` on that connection after the S1 writes, before the caller's sole commit. Without
        `caller`, this is the ordinary S1 publish in its own transaction.
        """
        def unchanged(content: Mapping[str, Any]) -> str | None:
            reserve = battery_reserve(content)
            if reserve is not None and reserve["asset_code"] == asset_code and float(reserve["value"]) == value:
                return f"The battery reserve is already {value:g}{RESERVE_UNIT}"
            return None

        def expect(replaced: RevisionRow) -> None:
            if expected_revision_id is not None and replaced.id != expected_revision_id:
                raise FoundationRefused(
                    "FOUNDATION_EXPECTED_REVISION_STALE",
                    f"The Foundation revision covering {effective_from.isoformat()} is {replaced.id}, "
                    f"not the expected {expected_revision_id}. Nothing was written.",
                    status=409, current_revision_id=replaced.id)

        def basis(replaced: RevisionRow) -> None:
            if expected_value is None:
                return
            reserve = battery_reserve(replaced.content)
            if reserve is None or reserve["asset_code"] != asset_code or float(reserve["value"]) != expected_value:
                raise FoundationRefused(
                    "FOUNDATION_EXPECTED_VALUE_STALE",
                    f"The battery reserve in v{replaced.version} is no longer {expected_value:g}{RESERVE_UNIT}. "
                    "Nothing was written.", status=409, current_revision_id=replaced.id)

        return self._publish_content_change(
            tenant, site, effective_from=effective_from, note=note, unchanged=unchanged,
            change=lambda content, version: with_battery_reserve(
                content, asset_code=asset_code, value=value, source_version=version
            ),
            expect=expect, basis=basis, caller=caller,
        )

    def publish_component_properties(
        self,
        tenant: TenantRef,
        site: StoredSite,
        *,
        asset_code: str,
        properties: Sequence[Mapping[str, Any]],
        effective_from: datetime,
        note: str,
    ) -> PublishResult:
        """A later-effective revision declaring typed properties on one component.

        Not an operator route: S3-01's labelled simulated demo configuration
        (`D-2026-10-08-s2-registered-kobo-demo-configuration`) publishes the
        template's generator values with their TEMPLATE provenance. Earlier
        revisions are split, never rewritten; the strict parser re-validates
        every key, unit and source.
        """
        def unchanged(content: Mapping[str, Any]) -> str | None:
            return "These properties are already declared" if with_component_properties(
                content, asset_code=asset_code, properties=properties
            ) == content else None

        return self._publish_content_change(
            tenant, site, effective_from=effective_from, note=note, unchanged=unchanged,
            change=lambda content, _version: with_component_properties(
                content, asset_code=asset_code, properties=properties
            ),
        )

    def publish_topology(
        self,
        tenant: TenantRef,
        site: StoredSite,
        *,
        topology: Mapping[str, Any],
        effective_from: datetime,
        note: str,
    ) -> PublishResult:
        """W2-01: a later-effective revision replacing the declared topology.

        Not an operator route: the cold-chain fixtures and tests change topology through the same S1
        revision path as properties. Earlier revisions are split, never rewritten; the strict parser
        (and, for a COLDCHAIN Site, the cold Foundation validator) re-validates the whole document.
        """
        replacement = json.loads(json.dumps(topology))

        def unchanged(content: Mapping[str, Any]) -> str | None:
            return "This topology is already declared" if content.get("topology") == replacement else None

        return self._publish_content_change(
            tenant, site, effective_from=effective_from, note=note, unchanged=unchanged,
            change=lambda content, _version: {**json.loads(json.dumps(content)), "topology": replacement},
        )

    def _publish_content_change(
        self,
        tenant: TenantRef,
        site: StoredSite,
        *,
        effective_from: datetime,
        note: str | None,
        unchanged: Callable[[Mapping[str, Any]], str | None],
        change: Callable[[Mapping[str, Any], int], dict[str, Any]],
        expect: Callable[[RevisionRow], None] = lambda _replaced: None,
        basis: Callable[[RevisionRow], None] = lambda _replaced: None,
        caller: CallerTransaction | None = None,
    ) -> PublishResult:
        now = self._clock() if caller is None else caller.recorded_at
        changed_holder: dict[str, RevisionRow] = {}

        def planner(rows: Sequence[RevisionRow]) -> PublishPlan:
            latest = max(row.recorded_at for row in rows)
            if now < latest:
                # Recorded time must not run backwards (review m3): a server
                # clock behind the last recorded change would close a period
                # before it was recorded. Refused before anything is written.
                raise FoundationRefused(
                    "FOUNDATION_CLOCK_BEHIND",
                    f"The server clock ({now.isoformat()}) is earlier than the last recorded "
                    f"Foundation change ({latest.isoformat()}), so this change cannot be "
                    "recorded. Nothing was written; retry once the clock is correct.",
                    status=409,
                )
            current = [row for row in rows if row.superseded_at is None]
            covering = [
                row
                for row in current
                if row.valid_from <= effective_from < _forever_after(row.valid_to)
            ]
            if len(covering) != 1:
                raise FoundationRefused(
                    "FOUNDATION_INTERVAL_INVALID",
                    f"No currently recorded Foundation period of {site.site_code} contains "
                    f"{effective_from.isoformat()}, so there is no configuration to change "
                    "from that instant.",
                    status=422,
                )
            replaced = covering[0]
            # S6-01a order under the Site lock: the expected covering revision, then no-change, then the
            # expected basis value. Each refusal aborts with nothing written.
            expect(replaced)
            same = unchanged(replaced.content)
            if same is not None:
                raise FoundationRefused(
                    "FOUNDATION_NO_CHANGE", f"{same} in v{replaced.version}.", status=422,
                    current_revision_id=replaced.id,
                )
            basis(replaced)
            next_version = max(row.version for row in rows) + 1
            inserts: list[RevisionRow] = []
            if effective_from > replaced.valid_from:
                inserts.append(
                    RevisionRow(
                        id=uuid4(),
                        version=next_version,
                        valid_from=replaced.valid_from,
                        valid_to=effective_from,
                        recorded_at=now,
                        superseded_at=None,
                        schema_version=replaced.schema_version,
                        content=replaced.content,
                        content_sha256=replaced.content_sha256,
                        origin="SPLIT",
                        derived_from_revision_id=replaced.id,
                        change_note=f"Unchanged earlier segment of v{replaced.version}",
                    )
                )
                next_version += 1
            try:
                content = change(replaced.content, next_version)
            except SiteConfigurationInvalid as error:
                raise FoundationRefused(_value_refusal_code(site.site_type), str(error), status=422) from error
            changed = RevisionRow(
                id=uuid4(),
                version=next_version,
                valid_from=effective_from,
                valid_to=replaced.valid_to,
                recorded_at=now,
                superseded_at=None,
                schema_version=replaced.schema_version,
                content=content,
                content_sha256=content_digest(content),
                origin="PUBLISH",
                derived_from_revision_id=replaced.id,
                change_note=note,
            )
            try:
                changed_record = record_at(site, changed)
                _check_ev_interval(site.site_type, changed_record, changed.valid_from, changed.valid_to,
                                   f"foundation revision {changed.id} (v{changed.version})")
            except SiteConfigurationInvalid as error:
                raise FoundationRefused(_value_refusal_code(site.site_type), str(error), status=422) from error
            inserts.append(changed)
            changed_holder["changed"] = changed
            return PublishPlan(supersede_ids=(replaced.id,), superseded_at=now, inserts=tuple(inserts))

        registrations = self._store.registrations(tenant.id, site.id)
        plan_holder: dict[str, PublishPlan] = {}

        def joint(state: ConfigurationState) -> ConfigurationPlan:
            # S1-02 (decision Q5/Q6): a Foundation change also replaces every
            # binding set revision that named a replaced Foundation revision,
            # aligned to the new periods, with their snapshots pinned - all in
            # this one transaction.
            plan = planner(state.revisions)
            plan_holder["plan"] = plan
            draft = ConfigurationPlan(plan.superseded_at, plan.supersede_ids, plan.inserts, (), ())
            completed, _ = finalize(
                state, draft, tenant_id=tenant.id, site=site, registrations=registrations, now=now
            )
            return completed

        try:
            if caller is None:
                configuration = self._store.publish_configuration(tenant.id, site.id, joint)
            else:
                configuration = self._store.publish_configuration(
                    tenant.id, site.id, joint, connection=caller.connection,
                    then=lambda plan: caller.then(written_ids(plan)))
        except FoundationSiteNotFound as error:
            raise FoundationRefused("SITE_NOT_FOUND", str(error), status=404) from error
        return PublishResult(site=site, plan=plan_holder["plan"], changed=changed_holder["changed"],
                             configuration=configuration)

