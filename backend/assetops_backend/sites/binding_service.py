"""Signal bindings: validation, joint publication, Readiness and snapshot (S1-02).

Pure orchestration over the injected `FoundationStore`; no storage technology
is named here.

A binding set revision maps every bound device channel of the Site's
registered gateway to a Site asset, a code-owned role, a source and canonical
unit and a conversion, for one valid period and one recorded period. A
publication is one `ConfigurationPlan` written atomically under the Site lock:
it may change the Foundation (declare a channel signal) and the bindings
together, and a binding-only change is still validated against the Foundation
revisions it reads under that lock.

Readiness is configuration only. "Ready to report" says the configuration
names a channel for every required role; it never says a source is healthy or
reporting, and no binding or source is ever presented as an operating state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence
from uuid import UUID, uuid4

from assetops_backend.sites.binding_alignment import (
    SNAPSHOT_SCHEMA_V1,
    SERIALIZERS,
    UNPINNED,
    binding_content,
    canonical_bytes,
    finalize,
)
from assetops_backend.sites.binding_roles import (
    ROLE_SET_BY_SITE_TYPE,
    VERIFICATION_MESSAGES,
    VERIFICATION_POINT_ROLES,
    VERIFICATION_POWER_ROLES,
    VERIFICATION_READINESS_VERSION,
    VERIFICATION_ROLE_SETS,
    serves,
    Role,
    conversion_problem,
    roles_for,
)
from assetops_backend.sites.foundation_content import (
    CURRENT_ROW_GAP_CODES,
    ConfigurationGap,
    battery_reserve,
    configuration_gaps,
    content_digest,
    record_at,
)
from assetops_backend.sites.foundation_records import (
    BindingRow,
    BindingSetRevisionRow,
    ConfigurationPlan,
    ConfigurationState,
    FoundationSiteNotFound,
    FoundationStore,
    Registrations,
    RevisionRow,
    StoredSite,
    TenantRef,
)
from assetops_backend.sites.foundation_service import binding_set_at  # noqa: F401 - re-exported
from assetops_backend.sites.ports import SiteConfigurationInvalid

Clock = Callable[[], datetime]

_END = datetime.max.replace(tzinfo=timezone.utc)

BINDING_ITEM_KEYS = frozenset(
    {"device_id", "signal_id", "asset_id", "role", "source_unit", "canonical_unit", "conversion"}
)

#: Placeholder references on a draft binding set revision; `finalize`
#: replaces them with the aligned Foundation revision and the gateway.
_DRAFT_REF = UUID(int=0)

SNAPSHOT_ACCESS_STATEMENT = (
    "Development configuration download, scoped to the fixed development tenant. "
    "Gateway authentication is pending (S2); this is not authenticated gateway access."
)

READINESS_STATEMENT = (
    "Ready to report means this configuration names a bound channel or a configured "
    "control for every required role, and the Foundation shown has no configuration gap. "
    "It does not mean any device is connected, reporting or healthy; "
    "operational status is not assessed here."
)


def _publication_root(
    all_sets: Sequence[BindingSetRevisionRow], row: BindingSetRevisionRow
) -> BindingSetRevisionRow:
    """The publication a row descends from: walk SPLIT copies (superseded rows
    included) back to the first row that was itself published."""
    by_id = {s.id: s for s in all_sets}
    seen: set[UUID] = set()
    while row.origin == "SPLIT" and row.derived_from_revision_id in by_id and row.id not in seen:
        seen.add(row.id)
        row = by_id[row.derived_from_revision_id]
    return row


def _publication_key(
    all_sets: Sequence[BindingSetRevisionRow], row: BindingSetRevisionRow
) -> tuple[Any, ...]:
    """Publication identity, not row identity: one publication spanning several
    Foundation periods leaves several pieces sharing these fields."""
    root = _publication_root(all_sets, row)
    return (root.origin, root.derived_from_revision_id, root.recorded_at, root.change_note)


def _until(value: datetime | None) -> datetime:
    return _END if value is None else value


def _overlaps(a_from: datetime, a_to: datetime | None, b_from: datetime, b_to: datetime | None) -> bool:
    return a_from < _until(b_to) and b_from < _until(a_to)


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def bindings_digest(role_set: str, bindings: Sequence[BindingRow]) -> str:
    """Content hash of one set's bindings, without row identities.

    An unchanged split copy therefore has the same digest as its original,
    as an unchanged Foundation segment keeps its `content_sha256`.
    """
    rows = sorted((binding_content(b) for b in bindings), key=lambda r: (r["device_id"], r["signal_id"]))
    return hashlib.sha256(canonical_bytes({"role_set": role_set, "bindings": rows})).hexdigest()


class BindingRefused(Exception):
    """A binding publication refused; nothing was written."""

    def __init__(self, code: str, message: str, *, status: int, problems: Sequence[dict[str, str]] = ()) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.problems = list(problems)


# --- requests ------------------------------------------------------------------


@dataclass(frozen=True)
class BindingRequest:
    device_id: str
    signal_id: str
    asset_id: str | None
    role: str
    source_unit: str
    canonical_unit: str
    conversion: dict[str, Any]

    @staticmethod
    def from_wire(item: Any, index: int) -> "BindingRequest":
        if not isinstance(item, dict):
            raise BindingRefused("BINDING_REQUEST_INVALID", f"bindings[{index}] must be an object.", status=422)
        unknown, missing = set(item) - BINDING_ITEM_KEYS, BINDING_ITEM_KEYS - set(item)
        if unknown or missing:
            raise BindingRefused(
                "BINDING_REQUEST_INVALID",
                f"bindings[{index}]: unknown fields {sorted(unknown)}; missing fields {sorted(missing)}.",
                status=422,
            )
        for key in ("device_id", "signal_id", "role", "source_unit", "canonical_unit"):
            if not isinstance(item[key], str) or not item[key]:
                raise BindingRefused(
                    "BINDING_REQUEST_INVALID", f"bindings[{index}].{key} must be non-empty text.", status=422
                )
        if item["asset_id"] is not None and not isinstance(item["asset_id"], str):
            raise BindingRefused(
                "BINDING_REQUEST_INVALID", f"bindings[{index}].asset_id must be a UUID or null.", status=422
            )
        return BindingRequest(
            device_id=item["device_id"],
            signal_id=item["signal_id"],
            asset_id=item["asset_id"],
            role=item["role"],
            source_unit=item["source_unit"],
            canonical_unit=item["canonical_unit"],
            conversion=item["conversion"],
        )


@dataclass(frozen=True)
class DeclaredSignal:
    """A channel signal to declare on an existing device, jointly with its binding."""

    device_id: str
    signal_id: str
    display_name: str
    unit: str


# --- validation ------------------------------------------------------------------


def _declared_signals(content: Mapping[str, Any]) -> dict[tuple[str, str], str]:
    return {
        (device["device_id"], signal["signal_id"]): signal["unit"]
        for device in content.get("devices") or ()
        for signal in device.get("signals") or ()
    }


def critical_load_code(content: Mapping[str, Any]) -> str | None:
    """The first member of a Foundation's critical-load-priority control, or None."""
    for control in content.get("site_controls") or ():
        if control.get("control_key") == "critical-load-priority":
            members = list(control.get("members") or ())
            return str(members[0]) if members else None
    return None


def validate_bindings(
    site: StoredSite,
    role_set: str,
    requests: Sequence[BindingRequest],
    registrations: Registrations,
    foundation: Sequence[RevisionRow],
) -> tuple[BindingRow, ...]:
    """Every request as a binding row, or a refusal naming every problem.

    `foundation` is every currently recorded Foundation revision the binding
    period overlaps (after any joint Foundation change); each must declare the
    channel with the source unit.
    """
    problems: list[dict[str, str]] = []

    def problem(code: str, index: int | None, message: str) -> None:
        problems.append({"code": code, "binding": "" if index is None else str(index), "message": message})

    roles = roles_for(role_set)
    if not roles:
        problem("BINDING_ROLE_SET_UNKNOWN", None, f"Role set {role_set!r} is not defined.")
    gateways = registrations.gateways
    if len(gateways) != 1:
        problem("BINDING_GATEWAY_UNKNOWN", None, f"{site.site_code} must have exactly one registered gateway.")
    assets = {str(a.id): a for a in registrations.assets}
    sources = {
        s.source_external_id: s
        for s in registrations.sources
        if gateways and s.gateway_id == gateways[0].id
    }
    declared = [(_declared_signals(row.content), row) for row in foundation]
    if not foundation:
        problem(
            "BINDING_FOUNDATION_MISSING", None,
            "No currently recorded Foundation period covers this binding period.",
        )

    # ONE means one per Site and never a choice among several (decision Q1,
    # review M2): a Foundation period with more than one eligible component for
    # a ONE role it needs is refused, not resolved by picking one.
    requested_roles = {req.role for req in requests}
    for row in foundation:
        components = list(row.content.get("components") or ())
        for role in roles.values():
            if role.cardinality != "ONE" or not (role.required or role.role in requested_roles):
                continue
            if role.critical_load:
                continue  # the critical-load-priority control names the one asset
            eligible = sorted(c["component_id"] for c in components if c.get("component_type") == role.asset_type)
            if len(eligible) > 1:
                problem(
                    "BINDING_ROLE_AMBIGUOUS", None,
                    f"{role.label} is one per Site in {role_set}, but Foundation v{row.version} declares "
                    f"{len(eligible)} {role.asset_type} components ({', '.join(eligible)}); this release "
                    "does not choose among them.",
                )

    rows: list[BindingRow] = []
    channels: set[tuple[str, str]] = set()
    single: dict[tuple[str, str | None], int] = {}
    for index, req in enumerate(requests):
        channel = (req.device_id, req.signal_id)
        name = f"{req.device_id} / {req.signal_id}"
        if channel in channels:
            problem("BINDING_CHANNEL_OVERLAP", index, f"Channel {name} is bound more than once in this set.")
        channels.add(channel)
        source = sources.get(req.device_id)
        if source is None:
            problem(
                "BINDING_SOURCE_UNKNOWN", index,
                f"Device {req.device_id!r} is not a registered source of {site.site_code}'s gateway.",
            )
        for signals, row in declared:
            unit = signals.get(channel)
            if unit is None:
                problem(
                    "BINDING_SIGNAL_UNDECLARED", index,
                    f"Foundation v{row.version} declares no signal {name}.",
                )
            elif unit != req.source_unit:
                problem(
                    "BINDING_UNIT_MISMATCH", index,
                    f"{name} is declared in {unit!r} in Foundation v{row.version}, not {req.source_unit!r}.",
                )
        asset = None
        if req.asset_id is not None:
            asset = assets.get(req.asset_id)
            if asset is None:
                problem(
                    "BINDING_ASSET_UNKNOWN", index,
                    f"Asset {req.asset_id} is not a registered asset of {site.site_code}.",
                )
        role: Role | None = roles.get(req.role)
        if role is None:
            problem("BINDING_ROLE_UNKNOWN", index, f"Role {req.role!r} is not in {role_set}.")
        elif role.covered_by != "CHANNEL":
            problem(
                "BINDING_ROLE_NOT_A_CHANNEL", index,
                f"{role.label} is covered by a Foundation control, not by a channel binding.",
            )
        else:
            if req.canonical_unit != role.canonical_unit:
                problem(
                    "BINDING_UNIT_MISMATCH", index,
                    f"{role.label} is stated in {role.canonical_unit!r}, not {req.canonical_unit!r}.",
                )
            why = conversion_problem(role, req.source_unit, req.conversion)
            if why is not None:
                problem("BINDING_CONVERSION_INVALID", index, f"{name}: {why}.")
            if req.asset_id is None:
                problem("BINDING_ASSET_REQUIRED", index, f"{role.label} must name the asset it describes.")
            elif asset is not None and asset.asset_type != role.asset_type:
                problem(
                    "BINDING_ROLE_ASSET_MISMATCH", index,
                    f"{role.label} describes a {role.asset_type} asset; {asset.asset_code} is {asset.asset_type}.",
                )
            if role.critical_load and asset is not None:
                for row in foundation:
                    first = critical_load_code(row.content)
                    if first != asset.asset_code:
                        problem(
                            "BINDING_CRITICAL_LOAD_MISMATCH", index,
                            f"{role.label} must name the first load of the critical-load priority in Foundation "
                            f"v{row.version} ({first or 'not configured'}), not {asset.asset_code}.",
                        )
            if role.role == "battery_soc" and asset is not None:
                # The state of charge and the reserve control must describe one battery.
                for row in foundation:
                    reserve = battery_reserve(row.content)
                    if reserve is not None and reserve["asset_code"] != asset.asset_code:
                        problem(
                            "BINDING_BATTERY_MISMATCH", index,
                            f"{role.label} names {asset.asset_code}, but the battery reserve in Foundation "
                            f"v{row.version} is configured on {reserve['asset_code']}.",
                        )
            key = (role.role, req.asset_id if role.cardinality == "PER_ASSET" else None)
            if key in single:
                problem(
                    "BINDING_ROLE_CONFLICT", index,
                    f"{role.label} is already bound by bindings[{single[key]}]"
                    + (" for this asset." if key[1] else "."),
                )
            single.setdefault(key, index)
        if source is not None and gateways:
            rows.append(
                BindingRow(
                    id=uuid4(),
                    gateway_id=gateways[0].id,
                    source_id=source.id,
                    device_id=req.device_id,
                    signal_id=req.signal_id,
                    asset_id=None if asset is None else asset.id,
                    role=req.role,
                    source_unit=req.source_unit,
                    canonical_unit=req.canonical_unit,
                    conversion=req.conversion,
                )
            )
    if problems:
        first = problems[0]
        raise BindingRefused(
            first["code"],
            "The binding set was refused and nothing was written: "
            + " ".join(p["message"] for p in problems),
            status=422,
            problems=problems,
        )
    return tuple(rows)


# --- planning --------------------------------------------------------------------


def _with_signal(content: Mapping[str, Any], signal: DeclaredSignal) -> dict[str, Any] | None:
    """`content` with the signal declared on its device, or None if already declared."""
    updated = json.loads(json.dumps(content))
    for device in updated.get("devices") or ():
        if device["device_id"] != signal.device_id:
            continue
        for existing in device.get("signals") or ():
            if existing["signal_id"] == signal.signal_id:
                if existing["unit"] != signal.unit:
                    raise BindingRefused(
                        "BINDING_UNIT_MISMATCH",
                        f"{signal.device_id} / {signal.signal_id} is already declared in "
                        f"{existing['unit']!r}, not {signal.unit!r}.",
                        status=422,
                    )
                return None
        device["signals"] = [
            *(device.get("signals") or []),
            {"signal_id": signal.signal_id, "display_name": signal.display_name, "unit": signal.unit},
        ]
        return updated
    raise BindingRefused(
        "BINDING_SOURCE_UNKNOWN",
        f"This Site's Foundation declares no device {signal.device_id!r}.",
        status=422,
    )


@dataclass(frozen=True)
class BindingPublishResult:
    plan: ConfigurationPlan
    #: The binding set revision in effect at the effective instant.
    changed: BindingSetRevisionRow
    #: Every aligned revision the change became (one per Foundation period).
    published: tuple[BindingSetRevisionRow, ...]
    #: Where the published set stops applying (None: open-ended). It reaches
    #: through every later period that was only an unchanged copy of the set
    #: being edited, and stops at a later independent binding change.
    applies_until: datetime | None = None
    #: The version of that later independent binding set, when one stopped it.
    stopped_by_version: int | None = None


class BindingService:
    """Tenant-scoped binding publication over the Foundation store."""

    def __init__(self, store: FoundationStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def publish(
        self,
        tenant: TenantRef,
        site: StoredSite,
        *,
        requests: Sequence[BindingRequest],
        effective_from: datetime,
        note: str | None,
        declare: Sequence[DeclaredSignal] = (),
        origin: str = "PUBLISH",
        role_set: str | None = None,
    ) -> BindingPublishResult:
        now = self._clock()
        # S3-01: the Site type's current vocabulary unless the caller names an
        # older version that type still serves (a replayed historical
        # conversion records the version its fixture was written for).
        if role_set is None:
            role_set = ROLE_SET_BY_SITE_TYPE.get(site.site_type)
        elif not serves(site.site_type, role_set):
            raise BindingRefused(
                "BINDING_ROLE_SET_UNKNOWN",
                f"{site.site_type} Sites do not serve role set {role_set!r}.",
                status=422,
            )
        if role_set is None:
            raise BindingRefused(
                "BINDING_ROLE_SET_UNKNOWN", f"No role set is defined for {site.site_type} Sites.", status=422
            )
        holder: dict[str, Any] = {}
        registrations = self._store.registrations(tenant.id, site.id)

        def planner(state: ConfigurationState) -> ConfigurationPlan:
            recorded = [r.recorded_at for r in state.revisions] + [s.recorded_at for s in state.binding_sets]
            if recorded and now < max(recorded):
                raise BindingRefused(
                    "FOUNDATION_CLOCK_BEHIND",
                    f"The server clock ({now.isoformat()}) is earlier than the last recorded "
                    "configuration change, so nothing can be recorded. Nothing was written.",
                    status=409,
                )
            current_sets = [s for s in state.binding_sets if s.superseded_at is None]
            set_inserts: list[BindingSetRevisionRow] = []
            supersede_sets: tuple[UUID, ...] = ()
            if not current_sets:
                binding_set_id, period_to, replaced = uuid4(), None, None
            else:
                covering = [s for s in current_sets if s.valid_from <= effective_from < _until(s.valid_to)]
                if len(covering) != 1:
                    raise BindingRefused(
                        "BINDING_INTERVAL_INVALID",
                        f"No currently recorded binding period of {site.site_code} contains "
                        f"{effective_from.isoformat()}.",
                        status=422,
                    )
                replaced = covering[0]
                binding_set_id = replaced.binding_set_id
                # n6: a Foundation split reissues the same bindings as later
                # unchanged periods. The edit reaches through each contiguous
                # one, so a split boundary never restores the old set; it stops
                # at a later period whose bindings differ (an independent change).
                carried: list[BindingSetRevisionRow] = []
                period_to = replaced.valid_to
                while period_to is not None:
                    following = [
                        s for s in current_sets
                        if s.binding_set_id == replaced.binding_set_id and s.valid_from == period_to
                    ]
                    same_publication = len(following) == 1 and (
                        following[0].bindings_sha256 == replaced.bindings_sha256
                        and _publication_key(state.binding_sets, following[0])
                        == _publication_key(state.binding_sets, replaced)
                    )
                    if not same_publication:
                        if len(following) == 1:
                            holder["stopped_by"] = _publication_root(state.binding_sets, following[0]).version
                        break
                    carried.append(following[0])
                    period_to = following[0].valid_to
                supersede_sets = (replaced.id, *(c.id for c in carried))
                if effective_from > replaced.valid_from:
                    set_inserts.append(
                        replace(
                            replaced,
                            id=uuid4(),
                            valid_to=effective_from,
                            recorded_at=now,
                            superseded_at=None,
                            origin="SPLIT",
                            derived_from_revision_id=replaced.id,
                            change_note=f"Unchanged earlier segment of binding v{replaced.version}",
                            bindings=tuple(replace(b, id=uuid4()) for b in replaced.bindings),
                        )
                    )

            # Joint Foundation change: declare each channel signal in every
            # current Foundation period the binding period overlaps.
            current_rev = [r for r in state.revisions if r.superseded_at is None]
            supersede_revs: list[UUID] = []
            rev_inserts: list[RevisionRow] = []
            next_version = max((r.version for r in state.revisions), default=0) + 1
            if declare:
                for row in sorted(current_rev, key=lambda r: r.valid_from):
                    if not _overlaps(row.valid_from, row.valid_to, effective_from, period_to):
                        continue
                    content: dict[str, Any] | None = None
                    base: Mapping[str, Any] = row.content
                    for signal in declare:
                        changed_content = _with_signal(base, signal)
                        if changed_content is not None:
                            base = content = changed_content
                    if content is None:
                        continue
                    start = max(row.valid_from, effective_from)
                    if row.valid_from < start:
                        rev_inserts.append(
                            RevisionRow(
                                id=uuid4(), version=next_version, valid_from=row.valid_from,
                                valid_to=start, recorded_at=now, superseded_at=None,
                                schema_version=row.schema_version, content=row.content,
                                content_sha256=row.content_sha256, origin="SPLIT",
                                derived_from_revision_id=row.id,
                                change_note=f"Unchanged earlier segment of v{row.version}",
                            )
                        )
                        next_version += 1
                    changed_row = RevisionRow(
                        id=uuid4(), version=next_version, valid_from=start, valid_to=row.valid_to,
                        recorded_at=now, superseded_at=None, schema_version=row.schema_version,
                        content=content, content_sha256=content_digest(content), origin="PUBLISH",
                        derived_from_revision_id=row.id,
                        change_note="Declared channel signal(s) "
                        + ", ".join(f"{s.device_id} / {s.signal_id}" for s in declare)
                        + " with their bindings",
                    )
                    try:
                        record_at(site, changed_row)
                    except SiteConfigurationInvalid as error:
                        raise BindingRefused("FOUNDATION_VALUE_INVALID", str(error), status=422) from error
                    next_version += 1
                    rev_inserts.append(changed_row)
                    supersede_revs.append(row.id)
            after = [r for r in current_rev if r.id not in supersede_revs] + rev_inserts
            if not any(r.valid_from <= effective_from < _until(r.valid_to) for r in after):
                raise BindingRefused(
                    "BINDING_INTERVAL_INVALID",
                    f"No currently recorded Foundation period of {site.site_code} contains "
                    f"{effective_from.isoformat()}; bindings must reference an effective Foundation.",
                    status=422,
                )
            overlapping = [r for r in after if _overlaps(r.valid_from, r.valid_to, effective_from, period_to)]
            bindings = validate_bindings(site, role_set, requests, registrations, overlapping)
            digest = bindings_digest(role_set, bindings)
            if replaced is not None and digest == replaced.bindings_sha256 and not rev_inserts:
                raise BindingRefused(
                    "BINDING_NO_CHANGE",
                    f"The bindings are already exactly these in binding v{replaced.version}.",
                    status=422,
                )
            changed = BindingSetRevisionRow(
                id=uuid4(),
                binding_set_id=binding_set_id,
                version=0,  # assigned by `finalize`
                role_set=role_set,
                valid_from=effective_from,
                valid_to=period_to,
                recorded_at=now,
                superseded_at=None,
                bindings_sha256=digest,
                origin=origin,
                derived_from_revision_id=None if replaced is None else replaced.id,
                change_note=note,
                bindings=bindings,
                foundation_revision_id=_DRAFT_REF,
                gateway_id=_DRAFT_REF,
                snapshot_schema=SNAPSHOT_SCHEMA_V1,
                snapshot_sha256=UNPINNED,
            )
            set_inserts.append(changed)
            draft = ConfigurationPlan(
                superseded_at=now,
                supersede_revision_ids=tuple(supersede_revs),
                revision_inserts=tuple(rev_inserts),
                supersede_binding_set_ids=supersede_sets,
                binding_set_inserts=tuple(set_inserts),
            )
            completed, became = finalize(
                state, draft, tenant_id=tenant.id, site=site, registrations=registrations, now=now
            )
            pieces = became.get(changed.id, ())
            holder["applies_until"] = period_to
            holder["published"] = pieces
            holder["changed"] = next(p for p in pieces if p.valid_from <= effective_from < _until(p.valid_to))
            return completed

        try:
            plan = self._store.publish_configuration(tenant.id, site.id, planner)
        except FoundationSiteNotFound as error:
            raise BindingRefused("SITE_NOT_FOUND", str(error), status=404) from error
        return BindingPublishResult(
            plan=plan,
            changed=holder["changed"],
            published=holder["published"],
            applies_until=holder["applies_until"],
            stopped_by_version=holder.get("stopped_by"),
        )


# --- Readiness and snapshot (configuration only) ------------------------------------


def readiness(
    site: StoredSite,
    revision: RevisionRow,
    registrations: Registrations,
    binding_set: BindingSetRevisionRow | None,
) -> dict[str, Any]:
    """Which required roles this configuration covers, at one selected time.

    The aggregate state is configuration readiness: a required role that no
    channel or control covers, or any configuration gap in the selected
    Foundation revision, makes it INCOMPLETE (review M3). Gaps are reported in
    `foundation_gaps`, apart from the roles; neither is observed health.
    """
    gaps = configuration_gaps(site, revision, registrations)
    # A selected binding set is read under the role-set version it was
    # recorded with (S3-01); with none, the Site type's current vocabulary.
    role_set = binding_set.role_set if binding_set else ROLE_SET_BY_SITE_TYPE.get(site.site_type)
    roles = roles_for(role_set) if role_set else {}
    bindings = binding_set.bindings if binding_set else ()
    asset_by_id = {a.id: a for a in registrations.assets}
    loads = [a for a in registrations.assets if a.asset_type == "LOAD"]
    entries: list[dict[str, Any]] = []
    missing: list[str] = []
    for role in roles.values():
        bound = [b for b in bindings if b.role == role.role]
        base = {
            "role": role.role,
            "label": role.label,
            "required": role.required,
            "canonical_unit": role.canonical_unit,
            "covered_by": role.covered_by,
        }
        if role.covered_by == "FOUNDATION_CONTROL":
            reserve = battery_reserve(revision.content)
            status = "CONFIGURED" if reserve is not None else "NOT_CONFIGURED"
            entries.append({
                **base, "status": status, "subjects": [],
                "foundation_revision_id": str(revision.id),
                "detail": (
                    f"Configured in Foundation v{revision.version}: {reserve['value']:g}{reserve['unit']}."
                    if reserve is not None else f"Foundation v{revision.version} declares no battery reserve."
                ),
            })
            if status != "CONFIGURED" and role.required:
                missing.append(role.label)
            continue
        if role.cardinality == "PER_ASSET" and role.asset_type == "LOAD":
            subjects = []
            for load in loads:
                hits = [b for b in bound if b.asset_id == load.id]
                subjects.append({
                    "asset_id": str(load.id),
                    "asset_code": load.asset_code,
                    "status": "CONFIGURED" if hits else "UNBOUND",
                    "binding_revision_ids": [str(b.id) for b in hits],
                })
                if not hits and role.required:
                    missing.append(f"{role.label} - {load.attributes.get('display_name') or load.asset_code}")
            status = "CONFIGURED" if loads and all(s["status"] == "CONFIGURED" for s in subjects) else "UNBOUND"
            entries.append({**base, "status": status, "subjects": subjects})
            continue
        status = "CONFIGURED" if bound else "UNBOUND"
        entries.append({
            **base,
            "status": status,
            "subjects": [
                {
                    "asset_id": None if b.asset_id is None else str(b.asset_id),
                    "asset_code": asset_by_id[b.asset_id].asset_code if b.asset_id in asset_by_id else None,
                    "status": "CONFIGURED",
                    "binding_revision_ids": [str(b.id)],
                }
                for b in bound
            ],
        })
        if not bound and role.required:
            missing.append(role.label)

    by_channel = {(b.device_id, b.signal_id): b for b in bindings}
    sources = {s.source_external_id: s for s in registrations.sources}
    channels = []
    for device in revision.content.get("devices") or ():
        for signal in device.get("signals") or ():
            hit = by_channel.get((device["device_id"], signal["signal_id"]))
            source = sources.get(device["device_id"])
            channels.append({
                "device_id": device["device_id"],
                "signal_id": signal["signal_id"],
                "display_name": signal.get("display_name"),
                "unit": signal["unit"],
                "source_id": None if source is None else str(source.id),
                "status": "BOUND" if hit else ("UNBOUND" if source else "UNREGISTERED"),
                "binding_revision_id": None if hit is None else str(hit.id),
                "role": None if hit is None else hit.role,
            })
    if binding_set is None:
        state = "UNKNOWN"
    elif missing or gaps:
        state = "INCOMPLETE"
    else:
        state = "READY_TO_REPORT"
    extra: dict[str, Any] = {}
    if binding_set is not None and role_set in VERIFICATION_ROLE_SETS:
        extra["verification_readiness"] = verification_readiness(roles, bindings, loads)
    return {
        **extra,
        "role_set": role_set,
        "state": state,
        "binding_set_revision_id": None if binding_set is None else str(binding_set.id),
        "foundation_revision_id": str(revision.id),
        "roles": entries,
        "missing_roles": missing,
        "foundation_gaps": [gap.to_wire() for gap in gaps],
        "channels": channels,
        "statement": READINESS_STATEMENT
        if binding_set is not None
        else "No signal binding set is in effect for the period shown, so every role is unbound "
        "and readiness is Unknown. Operational status is not assessed here.",
    }




def verification_readiness(
    roles: dict[str, Role], bindings: Sequence[BindingRow], loads: Sequence[Any],
) -> dict[str, Any]:
    """S6-02a: which verification input roles this binding set leaves unbound.

    Additive to configuration readiness and only for a verification role set
    (roles-3); it says what to bind and publish, not whether data arrived.
    `feeder_demand` needs a binding for every load asset.
    """
    missing: list[dict[str, Any]] = []
    for name in VERIFICATION_POWER_ROLES + VERIFICATION_POINT_ROLES:
        role = roles.get(name)
        if role is None:
            continue
        bound = [b for b in bindings if b.role == name]
        lab_message, site_message = VERIFICATION_MESSAGES[name]
        entry = {"role": name, "label": role.label, "lab_message": lab_message, "site_message": site_message}
        if role.cardinality == "PER_ASSET" and role.asset_type == "LOAD":
            unbound = [load for load in loads if not any(b.asset_id == load.id for b in bound)]
            if not loads:
                missing.append({**entry, "asset_codes": []})
            elif unbound:
                missing.append({**entry, "asset_codes": [load.asset_code for load in unbound]})
        elif not bound:
            missing.append(entry)
    return {"version": VERIFICATION_READINESS_VERSION, "ready": not missing, "missing": missing}


@dataclass(frozen=True)
class Snapshot:
    document: dict[str, Any]
    body: bytes
    sha256: str
    schema: str
    foundation_revision_id: UUID
    binding_set: BindingSetRevisionRow
    #: True when the selected binding set is the one a gateway acquires now:
    #: still recorded, and its validity has not ended. A current snapshot is
    #: refused on any configuration gap; a historical one is validated against
    #: its own stored identity and reports current-row gaps here instead.
    current: bool = True
    current_gaps: tuple[ConfigurationGap, ...] = ()


@dataclass(frozen=True)
class SnapshotUnavailable:
    code: str
    reason: str
    status: int


def is_current_snapshot(binding_set: BindingSetRevisionRow, now: datetime) -> bool:
    """Whether a binding set is the current/new acquisition basis at `now`.

    Still recorded (not superseded) and not yet ended in valid time. Anything
    else - superseded since, or a period that has ended - is historical.
    """
    return binding_set.superseded_at is None and (
        binding_set.valid_to is None or binding_set.valid_to > now
    )


def pinned_identity_problems(
    document: Mapping[str, Any],
    tenant_id: UUID,
    site: StoredSite,
    foundation: RevisionRow,
    binding_set: BindingSetRevisionRow,
) -> list[str]:
    """Where the stored snapshot disagrees with its immutable publication references.

    The original registration identity of a pinned snapshot is read from its
    own stored bytes and checked against the immutable revision rows it was
    published with, never against today's gateway/source rows (S1-02 carry n5,
    D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary).
    """
    problems: list[str] = []

    def expect(path: str, actual: Any, wanted: Any) -> None:
        if actual != wanted:
            problems.append(f"{path} is {actual!r}, not {wanted!r}")

    def part(key: str) -> Mapping[str, Any]:
        value = document.get(key)
        return value if isinstance(value, Mapping) else {}

    expect("schema", document.get("schema"), binding_set.snapshot_schema)
    expect("tenant_id", document.get("tenant_id"), str(tenant_id))
    expect("site.site_id", part("site").get("site_id"), str(site.id))
    expect("foundation.revision_id", part("foundation").get("revision_id"), str(foundation.id))
    expect("foundation.version", part("foundation").get("version"), foundation.version)
    expect("foundation.valid_from", part("foundation").get("valid_from"), _iso(foundation.valid_from))
    expect("foundation.valid_to", part("foundation").get("valid_to"), _iso(foundation.valid_to))
    expect("foundation.content_sha256", part("foundation").get("content_sha256"), foundation.content_sha256)
    expect("mapping.binding_set_revision_id", part("mapping").get("binding_set_revision_id"), str(binding_set.id))
    expect("mapping.version", part("mapping").get("version"), binding_set.version)
    expect("mapping.valid_from", part("mapping").get("valid_from"), _iso(binding_set.valid_from))
    expect("mapping.valid_to", part("mapping").get("valid_to"), _iso(binding_set.valid_to))
    expect("mapping.bindings_sha256", part("mapping").get("bindings_sha256"), binding_set.bindings_sha256)
    expect("gateway.gateway_id", part("gateway").get("gateway_id"), str(binding_set.gateway_id))
    sources = {
        s.get("source_id") for s in document.get("sources") or () if isinstance(s, Mapping)
    }
    pinned = {str(b.id): b for b in binding_set.bindings}
    seen: set[str] = set()
    for entry in document.get("bindings") or ():
        if not isinstance(entry, Mapping):
            problems.append("a binding entry is not an object")
            continue
        binding_id = str(entry.get("binding_revision_id"))
        seen.add(binding_id)
        row = pinned.get(binding_id)
        if row is None:
            problems.append(f"binding {binding_id} is not a row of binding v{binding_set.version}")
            continue
        expect(f"binding {binding_id}.device_id", entry.get("device_id"), row.device_id)
        expect(f"binding {binding_id}.signal_id", entry.get("signal_id"), row.signal_id)
        expect(f"binding {binding_id}.source_id", entry.get("source_id"), str(row.source_id))
        expect(f"binding {binding_id}.role", entry.get("role"), row.role)
        expect(f"binding {binding_id}.gateway_id", entry.get("gateway_id"), str(binding_set.gateway_id))
        if entry.get("source_id") not in sources:
            problems.append(f"binding {binding_id} names a source the snapshot does not register")
    for missing in sorted(set(pinned) - seen):
        problems.append(f"binding {missing} of binding v{binding_set.version} is absent from the snapshot")
    return problems


def acquisition_snapshot(
    tenant_id: UUID,
    site: StoredSite,
    revisions: Sequence[RevisionRow],
    registrations: Registrations,
    binding_set: BindingSetRevisionRow | None,
    *,
    now: datetime | None = None,
) -> Snapshot | SnapshotUnavailable:
    """The pinned gateway snapshot of the binding set selected, or why there is none.

    The bytes served are the canonical bytes stored in the publishing
    transaction, checked against the SHA-256 stored with them (decision Q6). They
    are never rebuilt from current registration rows, whose identity fields can
    change after publication (S1-02 fix round, review M1); a stored hash the
    stored bytes do not reproduce is refused, never served.

    Current versus historical (D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary):
    when `now` is given and the selected set is no longer the current
    acquisition basis (`is_current_snapshot`), gaps derived from CURRENT
    mutable rows (`CURRENT_ROW_GAP_CODES`) do not withdraw it. Its original
    registration identity is validated from the stored snapshot instead, and
    the current gaps are reported in `current_gaps`. Gaps of the selected
    Foundation content always refuse, and so does every gap of a current set.
    Without `now` every selection is treated as current, the S1-02 behaviour.
    """
    if binding_set is None:
        return SnapshotUnavailable(
            "ACQUISITION_SNAPSHOT_UNAVAILABLE",
            "No signal binding set is in effect for the period shown, so no gateway snapshot exists.",
            409,
        )
    foundation = next((r for r in revisions if r.id == binding_set.foundation_revision_id), None)
    if foundation is None:
        return SnapshotUnavailable(
            "ACQUISITION_SNAPSHOT_INCONSISTENT",
            f"Binding v{binding_set.version} names a Foundation revision this Site does not hold.",
            500,
        )
    current = now is None or is_current_snapshot(binding_set, now)
    gaps = configuration_gaps(site, foundation, registrations)
    blocking = gaps if current else [g for g in gaps if g.code not in CURRENT_ROW_GAP_CODES]
    if blocking:
        return SnapshotUnavailable(
            "ACQUISITION_SNAPSHOT_UNAVAILABLE",
            "This Foundation has configuration gaps ("
            + ", ".join(g.code for g in blocking)
            + "), so no gateway snapshot can be downloaded.",
            409,
        )
    if binding_set.snapshot_schema not in SERIALIZERS:
        return SnapshotUnavailable(
            "ACQUISITION_SNAPSHOT_SCHEMA_UNSUPPORTED",
            f"Snapshot schema {binding_set.snapshot_schema!r} has no serializer in this build.",
            500,
        )
    body = binding_set.snapshot_canonical
    if not body:
        return SnapshotUnavailable(
            "ACQUISITION_SNAPSHOT_INCONSISTENT",
            f"Binding v{binding_set.version} holds no published snapshot bytes, so none is served.",
            500,
        )
    digest = hashlib.sha256(body).hexdigest()
    if digest != binding_set.snapshot_sha256:
        return SnapshotUnavailable(
            "ACQUISITION_SNAPSHOT_HASH_MISMATCH",
            f"The stored snapshot hashes to {digest}, not the {binding_set.snapshot_sha256} "
            "stored at publication, so it is not served.",
            500,
        )
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        document = None
    if not isinstance(document, dict):
        return SnapshotUnavailable(
            "ACQUISITION_SNAPSHOT_INCONSISTENT",
            f"The stored snapshot of binding v{binding_set.version} is not a JSON object.",
            500,
        )
    problems = pinned_identity_problems(document, tenant_id, site, foundation, binding_set)
    if problems:
        return SnapshotUnavailable(
            "ACQUISITION_SNAPSHOT_INCONSISTENT",
            f"The stored snapshot of binding v{binding_set.version} disagrees with its "
            "publication references: " + "; ".join(problems[:5]) + ".",
            500,
        )
    return Snapshot(
        document=document,
        body=body,
        sha256=digest,
        schema=binding_set.snapshot_schema,
        foundation_revision_id=foundation.id,
        binding_set=binding_set,
        current=current,
        current_gaps=() if current else tuple(g for g in gaps if g.code in CURRENT_ROW_GAP_CODES),
    )
