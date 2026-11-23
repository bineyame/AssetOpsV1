"""DDR (`specs/DDR-rehearsal/spec.md` §2; D-DDR.1, D-DDR.3, D-DDR.11): checks that each rehearsal step left its record.

    python -m assetops_backend.rehearsal_check --tenant SLUG --month YYYY-MM [--expect PATH]

Read-only. Each gate reads the store its step writes, never another gate's result (D-DDR.3). Output is codes and
facts only (D-DDR.11): one JSON line per gate on stdout; exit 0 when all pass, else 4 with `DDR_GATE_FAILED G<n> <CODE>`
on stderr for the first failure; exit 2 with the refusal code alone before any read. No key path or key content is
printed (D-DS4.19).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Sequence

DEFAULT_EXPECT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ddr" / "lakeside-2026-10.expect.json"
GATES = ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10")
STEPS = {"G1": "S1", "G2": "S2", "G3": "S4", "G4": "S4", "G5": "S5", "G6": "S6", "G7": "S8", "G8": "S9", "G9": None,
         "G10": "S11"}
_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class Fail(Exception):
    """A gate's first failing condition: its §2.4 code and facts."""

    def __init__(self, code: str, **facts: Any) -> None:
        super().__init__(code)
        self.code = code
        self.facts = facts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.rehearsal_check",
                                     description="Check that each rehearsal step left its record.")
    parser.add_argument("--tenant", required=True, help="the tenant's slug")
    parser.add_argument("--month", required=True, help="the month, YYYY-MM")
    parser.add_argument("--expect", default=str(DEFAULT_EXPECT), help="the expectation file (JSON)")
    return parser


# --- the reads (D-DDR.3: each gate reads the store its step writes) ---------------------------------------------------

#: The composition each gate reads through, named in `READ_FAILED` (spec §2.4).
STORES = {"G1": "build_account_service", "G2": "build_commercial_reads", "G3": "build_commercial_reads",
          "G4": "build_structure_read", "G5": "build_commercial_reads", "G6": "build_structure_snapshot",
          "G7": "build_commercial_reconciliation", "G8": "build_structure_snapshot", "G9": "build_deep_dive_read",
          "G10": "build_agreed_actions"}
KEY_DIR_ENV = "ASSETOPS_PSEUDONYM_KEY_DIR"
ORG_STATEMENT = None  # `site_id` of the organisation's statement
PRICE = "diesel_price"
PRICE_SOURCE = "commercial:"
PERSON = "person:"
#: Spec §3.4: the body keys G9 compares, in order (D-DDR.7). `status_line` is compared after its first sentence.
SCREEN_KEYS = ("schema", "operator", "month", "month_words", "state", "standing", "headline", "status_line", "tiles",
               "notices", "bridge", "cash", "outcomes", "decisions", "not_available", "fresh")
_SENTENCE_END = ". "


class ReadFailed(Exception):
    """A read the gate needs could not be made; `store` is the composition's name."""

    def __init__(self, store: str) -> None:
        super().__init__(store)
        self.store = store


class Stores:
    """The checker's reads over the database (each composition built on first use, all disposed by `close`)."""

    def __init__(self, url: str, key_dir: str) -> None:
        self._url = url
        self._key_dir = key_dir
        self._built: dict[str, Any] = {}
        self._disposers: list[Callable[[], None]] = []

    def _get(self, name: str) -> Any:
        if name not in self._built:
            self._built[name] = self._build(name)
        return self._built[name]

    def _build(self, name: str) -> Any:
        url = self._url
        if name == "build_account_service":
            from assetops_backend.accounts.composition import build_account_service
            service = build_account_service(url)
            self._disposers.append(service._store.dispose)
            return service
        if name == "build_commercial_reads":
            from assetops_backend.commercial.composition import build_commercial_reads
            reads = build_commercial_reads(url)
            self._disposers.append(reads.dispose)
            return reads
        if name == "build_commercial_reconciliation":
            from assetops_backend.structure.reconciliation_composition import build_commercial_reconciliation
            reconciliation, dispose = build_commercial_reconciliation(url)
            self._disposers.append(dispose)
            return reconciliation
        if name == "build_structure_read":
            from assetops_backend.structure.composition import build_structure_read
            service = build_structure_read(url)
            self._disposers.append(service.dispose)
            return service.read
        if name == "build_target_read":
            from assetops_backend.structure.targets.composition import build_target_read
            service = build_target_read(url)
            self._disposers.append(service.dispose)
            return service.read
        if name == "build_structure_snapshot":
            from assetops_backend.structure_snapshot.composition import build_structure_snapshot
            service = build_structure_snapshot(url)
            self._disposers.append(service.dispose)
            return service
        if name == "build_agreed_actions":
            from assetops_backend.actions.agreed_composition import build_agreed_actions
            service = build_agreed_actions(url)
            self._disposers.append(service.dispose)
            return service.service
        if name == "build_foundation_store":
            from assetops_backend.sites.composition import build_foundation_store
            store = build_foundation_store(url)
            self._disposers.append(lambda: _dispose_engine(store))
            return store
        raise KeyError(name)

    def _read(self, name: str, read: Callable[[Any], Any]) -> Any:
        try:
            return read(self._get(name))
        except ReadFailed:
            raise
        except Exception:  # noqa: BLE001 - any store fault is that gate's READ_FAILED (spec §2.4)
            raise ReadFailed(name) from None

    # G1
    def tenant_id(self, slug: str) -> Any:
        return self._read("build_account_service", lambda s: s.tenant_by_slug(slug))

    def people(self, tenant_id: Any) -> tuple:
        return self._read("build_account_service", lambda s: s._store.people(tenant_id))

    def sites(self, tenant_id: Any) -> tuple:
        return self._read("build_commercial_reads", lambda r: r.store.site_rows(tenant_id))

    def key(self, tenant_id: Any) -> bytes:
        """3A2's port over the key folder; raises its `PseudonymKey*` exception (no path or key is printed)."""
        from assetops_backend.commercial.composition import FileKeyStore
        return FileKeyStore(self._key_dir).key(tenant_id)

    # G2, G3, G5
    def profile(self, tenant_id: Any, profile_id: str) -> Any:
        return self._read("build_commercial_reads", lambda r: r.store.source_profile_latest(tenant_id, profile_id))

    def held_uploads(self, tenant_id: Any) -> tuple:
        return self._read("build_commercial_reads", lambda r: r.store.held_uploads(tenant_id))

    def upload(self, tenant_id: Any, upload_id: Any) -> Any:
        return self._read("build_commercial_reads", lambda r: r.store.upload(tenant_id, upload_id))

    def statements(self, tenant_id: Any) -> tuple:
        return self._read("build_commercial_reads", lambda r: r.store.accounts_statements(tenant_id))

    # G4
    def site_refs(self, slug: str) -> tuple:
        found = self._read("build_structure_snapshot", lambda s: s.store.tenant_sites(slug))
        return () if found is None else found[1]

    def site_inputs(self, site: Any, month: str) -> Any:
        return self._read("build_structure_read", lambda r: r.site_inputs(site, month))

    def site_actual(self, site: Any, month: str) -> Any:
        return self._read("build_structure_read", lambda r: r.site(site, month))

    def site_targets(self, site: Any, month: str) -> Any:
        return self._read("build_target_read", lambda r: r.site(site, month))

    # G6, G7, G8
    def portfolio_history(self, tenant_id: Any, month: str) -> tuple:
        return self._read("build_structure_snapshot", lambda s: s.store.portfolio_history(tenant_id, month))

    def asked(self, row: Any) -> tuple:
        from assetops_backend.structure_snapshot import codec
        return tuple(codec.payload_of(row)["sites"])

    def served(self, tenant_id: Any, month: str) -> Any:
        return self._read("build_structure_snapshot", lambda s: s.read.portfolio(tenant_id, month))

    def opens(self, tenant_id: Any, statement: Any) -> tuple[bool, str]:
        check = self._read("build_commercial_reconciliation", lambda r: r.check(tenant_id, statement))
        return check.opens, check.state

    # G9, G10
    def screen(self, slug: str, month: str) -> dict:
        """The route's read (`deep_dive_api.py`): the served tenant and the names through `ImportedSiteRegistry`."""
        from assetops_backend.sites.cutover import ImportedSiteRegistry
        from assetops_backend.sites.foundation_service import FoundationService
        try:
            store = self._get("build_foundation_store")
            registry = ImportedSiteRegistry(FoundationService(store, slug))
            tenant = registry.tenant()
            names = {s.site_code: s.name for s in registry.imported_sites()}
        except Exception:  # noqa: BLE001
            raise ReadFailed("build_foundation_store") from None
        if tenant is None:
            raise ReadFailed("build_foundation_store")
        from assetops_backend.deep_dive.composition import build_deep_dive_read
        try:
            read, dispose = build_deep_dive_read(self._url)
        except Exception:  # noqa: BLE001
            raise ReadFailed("build_deep_dive_read") from None
        try:
            return read.month(tenant, month, names)
        except Exception:  # noqa: BLE001
            raise ReadFailed("build_deep_dive_read") from None
        finally:
            dispose()

    def actions(self, tenant_id: Any) -> tuple:
        return self._read("build_agreed_actions", lambda s: s.for_tenant(tenant_id))

    def close(self) -> None:
        for dispose in reversed(self._disposers):
            try:
                dispose()
            except Exception:  # noqa: BLE001 - every store is disposed
                pass


def _dispose_engine(store: Any) -> None:
    engine = getattr(store, "_engine", None)
    if engine is not None:
        engine.dispose()


# --- facts ------------------------------------------------------------------------------------------------------------

def _money(value: Any) -> str | None:
    if value is None:
        return None
    return format(Decimal(value).quantize(Decimal("0.01")), "f")


def _at(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _id(value: Any) -> str | None:
    return None if value is None else str(value)


def _same_money(expected: str | None, found: Any) -> bool:
    if expected is None or found is None:
        return expected is None and found is None
    return Decimal(expected) == Decimal(found)


# --- the gates (spec §2.2; each reports its first failing condition in §2.4's order) --------------------------------

class Run:
    def __init__(self, services: Any, tenant_id: Any, slug: str, month: str, expect: dict) -> None:
        self.s = services
        self.tid = tenant_id
        self.slug = slug
        self.month = month
        self.x = expect
        self._ids: dict[str, Any] | None = None

    def fresh(self) -> None:
        """Each gate reads the people itself (D-DDR.3): nothing read for one gate is reused by the next."""
        self._ids = None

    def person(self, email: str) -> Any:
        """A person's id by email, read from the accounts store by the gate that needs it."""
        if self._ids is None:
            self._ids = {p.email: p.person_id for p in self.s.people(self.tid)}
        return self._ids.get(email)

    def org_statements(self) -> list:
        return [r for r in self.s.statements(self.tid) if r.site_id is ORG_STATEMENT and r.period == self.month]

    # G1 (S1)
    def g1(self) -> None:
        from assetops_backend.commercial.pseudonym import (PseudonymKeyErased, PseudonymKeyMissing,
                                                           PseudonymKeyUnusable)
        found = sorted(f"{r.site_code}:{r.site_type}" for r in self.s.sites(self.tid))
        if found != sorted(self.x["sites"]):
            raise Fail("TENANT_SITES", expected=sorted(self.x["sites"]), found=found)
        people = self.s.people(self.tid)
        holders: dict[str, list] = {}
        for p in people:
            for g in p.grants:
                holders.setdefault(g.role, []).append((p.email, g))
        for role, want in self.x["grants"].items():
            emails = sorted({e for e, _ in holders.get(role, [])})
            exact = want["exactly"] if "exactly" in want else None
            if (exact is not None and emails != sorted(exact)) or \
                    (exact is None and not set(want["at_least"]) <= set(emails)):
                raise Fail("GRANTS", role=role, expected=sorted(exact if exact is not None else want["at_least"]),
                           found=emails)
        named = {e for want in self.x["grants"].values() for e in want.get("exactly", want.get("at_least", []))}
        for role, rows in sorted(holders.items()):
            for email, g in rows:
                if email in named and g.by_service != self.x["granted_by"]:
                    raise Fail("GRANTED_BY", email=email, found=g.by_service)
        try:
            self.s.key(self.tid)
        except PseudonymKeyErased:
            raise Fail("KEY_STATE", state="ERASED") from None
        except PseudonymKeyMissing:
            raise Fail("KEY_STATE", state="MISSING") from None
        except PseudonymKeyUnusable:
            raise Fail("KEY_STATE", state="UNUSABLE") from None

    # G2 (S2)
    def g2(self) -> None:
        want = self.x["profile"]
        row = self.s.profile(self.tid, want["profile_id"])
        if row is None:
            raise Fail("PROFILE_MISSING", profile=want["profile_id"])
        if row.status != want["status"] or row.version != want["version"]:
            raise Fail("PROFILE_STATE", status=row.status, version=row.version)
        admitter = self.person(want["admitted_by"])
        if row.admitted_by != admitter:
            raise Fail("ADMITTER", expected=_id(admitter), found=_id(row.admitted_by))
        for file in ("profile", "sample"):
            found = getattr(row, f"{file}_sha256")
            if found != want[f"{file}_sha256"]:
                raise Fail("PROFILE_SHA", file=file, expected=want[f"{file}_sha256"], found=found)

    # G3 (S3, S4)
    def g3(self) -> None:
        want = self.x["readers"]
        held = self.s.held_uploads(self.tid)
        accepted: dict[str, list] = {}
        for h in held:
            if not h.waiting:
                accepted.setdefault(h.reader, []).append(h)
        for reader in want["accepted"]:
            if reader not in accepted:
                raise Fail("READER_MISSING", reader=reader)
        present = {h.reader for h in held}
        for reader in want["absent"]:
            if reader in present:
                raise Fail("READER_PRESENT", reader=reader)
        submitter = self.person(want["submitted_by"])
        for reader in want["accepted"]:  # every accepted upload of the reader, not one of them
            for h in accepted[reader]:
                if h.submitted_by != submitter:
                    raise Fail("SUBMITTER", reader=reader, expected=_id(submitter), found=_id(h.submitted_by))
        accepter = self.person(want["accepted_by"])
        for reader in want["accepted"]:
            for h in accepted[reader]:
                record = self.s.upload(self.tid, h.upload_id)
                found = None if record is None or record.decision is None else record.decision.decided_by
                if found != accepter:
                    raise Fail("ACCEPTER", reader=reader, expected=_id(accepter), found=_id(found))

    # G4 (S4)
    def g4(self) -> None:
        refs = {r.site_code: r for r in self.s.site_refs(self.slug)}
        read = {}
        for code in self.x["stated"]:
            ref = refs.get(code)
            if ref is None:
                raise Fail("FIGURE", site=code, factor=next(iter(self.x["stated"][code])),
                           expected=next(iter(self.x["stated"][code].values())), found=None)
            read[code] = (self.s.site_inputs(ref, self.month), self.s.site_actual(ref, self.month))
        found = {code: {f: _leaf(read[code], f) for f in self.x["stated"][code]} for code in read}
        for code, factors in self.x["stated"].items():
            for factor, expected in factors.items():
                value = found[code][factor].value if found[code][factor] is not None else None
                if expected is not None and not _same_money(expected, value):
                    raise Fail("FIGURE", site=code, factor=factor, expected=expected, found=_money(value))
        for code, factors in self.x["stated"].items():
            for factor, expected in factors.items():
                leaf = found[code][factor]
                if expected is None and leaf is not None and leaf.value is not None:
                    raise Fail("NOT_ABSENT", site=code, factor=factor, found=_money(leaf.value))
        for code, causes in self.x["absent_causes"].items():
            for factor, expected in causes.items():
                leaf = found[code][factor]
                cause = None if leaf is None or leaf.missing is None else leaf.missing.cause
                if cause != expected:
                    raise Fail("CAUSE", site=code, factor=factor, expected=expected, found=cause)
        for code in self.x["stated"]:
            price = _leaf(read[code], PRICE)
            if price is None or price.value is None or not price.sources:
                raise Fail("PRICE_SOURCE", site=code, source=None)
            for source in price.sources:
                if not source.startswith(PRICE_SOURCE):
                    raise Fail("PRICE_SOURCE", site=code, source=source)
        targets = {code: self.s.site_targets(refs[code], self.month) for code in self.x["target_contribution"]}
        for code, expected in self.x["target_contribution"].items():
            value = targets[code].structure.values[_CONTRIBUTION].value
            if not _same_money(expected, value):
                raise Fail("TARGET", site=code, field=_CONTRIBUTION, expected=expected, found=_money(value))
        for code, want in self.x["target_checks"].items():
            checks = [c for c in targets[code].checks if c.factor_id == want["factor_id"]]
            if not checks:
                raise Fail("TARGET", site=code, field="factor_id", expected=want["factor_id"], found=None)
            check = checks[0]
            for field in ("stated", "computed"):
                if not _same_money(want[field], getattr(check, field)):
                    raise Fail("TARGET", site=code, field=field, expected=want[field],
                               found=_money(getattr(check, field)))
            for field in ("currency", "agrees"):
                if getattr(check, field) != want[field]:
                    raise Fail("TARGET", site=code, field=field, expected=want[field], found=getattr(check, field))

    # G5 (S5)
    def g5(self) -> None:
        want = self.x["statements"][0]
        rows = self.org_statements()
        if not rows:
            raise Fail("STATEMENT_MISSING", period=self.month)
        first = rows[0]
        for field in ("revenue", "fuel_cost"):
            if getattr(first, field) != want[field]:
                raise Fail("STATEMENT_FIELD", field=field, expected=want[field], found=getattr(first, field))
        if first.recorded_by_script is not True:
            raise Fail("STATEMENT_FIELD", field="recorded_by_script", expected=True, found=first.recorded_by_script)
        recorder = self.person(want["recorded_by"])
        if first.recorded_by != recorder:
            raise Fail("RECORDER", expected=_id(recorder), found=_id(first.recorded_by))
        if first.result_at_record != want["result"]:
            raise Fail("RESULT", expected=want["result"], found=first.result_at_record)

    def _builder(self) -> str:
        return f"{PERSON}{self.person(self.x['analyst'])}"

    # G6 (S6)
    def g6(self) -> None:
        builder = self._builder()
        rows = [r for r in self.s.portfolio_history(self.tid, self.month) if r.built_by == builder]
        if not rows:
            raise Fail("SNAPSHOT_MISSING", period=self.month, built_by=builder)
        statements = self.org_statements()
        first = statements[0].recorded_at if statements else None
        after = [r for r in rows if first is not None and r.as_of > first]
        if not after:
            raise Fail("BEFORE_STATEMENT", as_of=_at(rows[-1].as_of), recorded_at=_at(first))
        if len(statements) > 1:
            following = statements[1].recorded_at
            between = [r for r in after if r.as_of < following]
            if not between:
                raise Fail("AFTER_NEXT_STATEMENT", as_of=_at(after[0].as_of), recorded_at=_at(following))
            after = between
        asked = self.s.asked(after[-1])
        if list(asked) != self.x["asked"]:
            raise Fail("ASKED", expected=self.x["asked"], found=list(asked))

    # G7 (S8)
    def g7(self) -> None:
        want = self.x["statements"][1]
        rows = self.org_statements()
        if len(rows) < 2:
            raise Fail("STATEMENT_MISSING", period=self.month)
        latest = rows[-1]
        recorder = self.person(want["recorded_by"])
        if latest.recorded_by != recorder:
            raise Fail("RECORDER", expected=_id(recorder), found=_id(latest.recorded_by))
        opens, state = self.s.opens(self.tid, latest)
        if not opens:
            raise Fail("GATE_SHUT", result=state)

    # G8 (S9)
    def g8(self) -> None:
        rows = self.s.portfolio_history(self.tid, self.month)
        if not rows:
            raise Fail("SNAPSHOT_MISSING", period=self.month)
        latest = rows[-1]
        builder = self._builder()
        if latest.built_by != builder:
            raise Fail("BUILDER", expected=builder, found=latest.built_by)
        statements = self.org_statements()
        if statements and not latest.as_of > statements[-1].recorded_at:
            raise Fail("BEFORE_STATEMENT", as_of=_at(latest.as_of), recorded_at=_at(statements[-1].recorded_at))
        for h in self.s.held_uploads(self.tid):
            if h.waiting:
                continue
            record = self.s.upload(self.tid, h.upload_id)
            accepted_at = None if record is None or record.decision is None else record.decision.decided_at
            if accepted_at is not None and not latest.as_of > accepted_at:
                raise Fail("BEFORE_UPLOAD", as_of=_at(latest.as_of), accepted_at=_at(accepted_at))
        served = self.s.served(self.tid, self.month)
        if served.freshness is None or not served.freshness.current:
            reasons = () if served.freshness is None else served.freshness.reasons
            raise Fail("NOT_CURRENT", reason=reasons[0] if reasons else served.state)

    # G9 (the read)
    def g9(self) -> None:
        body = self.s.screen(self.slug, self.month)
        if body.get("state") != SERVED:
            raise Fail("STATE", found=body.get("state"))
        fresh = body.get("fresh") or {}
        if fresh.get("current") is not True:
            served = self.s.served(self.tid, self.month)
            reasons = () if served.freshness is None else served.freshness.reasons
            raise Fail("NOT_CURRENT", reason=reasons[0] if reasons else served.state)
        want = self.x["screen"]
        if fresh.get("untracked_text") != want["fresh"]["untracked_text"]:  # D-DD.181: both ways, None included
            raise Fail("UNTRACKED")
        for key in SCREEN_KEYS:
            found = body.get(key)
            if key == "status_line" and isinstance(found, str):
                found = found.partition(_SENTENCE_END)[2]
            path = _differs(f"$.{key}", want.get(key), found)
            if path is not None:
                raise Fail("SCREEN", path=path)

    # G10 (S11)
    def g10(self) -> None:
        want = self.x["action"]
        actions = self.s.actions(self.tid)
        if not actions:
            raise Fail("ACTION_MISSING")
        first = actions[0]
        found = {"title": first.title, "created_by_name": first.created_by_name, "owner_name": first.owner_name,
                 "due_on": first.due_on.isoformat(), "site_code": first.site_code, "factor_id": first.factor_id}
        for field, expected in want.items():
            if found[field] != expected:
                raise Fail("ACTION_FIELD", field=field, expected=expected, found=found[field])
        body = self.s.screen(self.slug, self.month)
        shown = body.get("actions") or {}
        if shown.get("connected") is not True:
            raise Fail("SCREEN_NOT_CONNECTED")
        rows = shown.get("rows") or []
        if not rows or rows[0].get("title") != want["title"]:
            raise Fail("SCREEN_ROW", field="title")


SERVED = "SERVED"
_CONTRIBUTION = "contribution"


def _leaf(read: tuple[Any, Any], factor: str) -> Any:
    """A Site's figure as the record states it (`stated`), else its leaf, else the worked-out value (`collected`)."""
    inputs, actual = read
    for source in (inputs.stated, inputs.leaves, actual.values):
        if factor in source:
            return source[factor]
    return None


def _differs(path: str, want: Any, found: Any) -> str | None:
    """The first JSON path at which `found` differs from `want`, in `want`'s key order; None when equal."""
    if isinstance(want, dict) and isinstance(found, dict):
        for key in list(want) + [k for k in found if k not in want]:
            if key not in want or key not in found:
                return f"{path}.{key}"
            inner = _differs(f"{path}.{key}", want[key], found[key])
            if inner is not None:
                return inner
        return None
    if isinstance(want, list) and isinstance(found, list):
        for i, (w, f) in enumerate(zip(want, found)):
            inner = _differs(f"{path}[{i}]", w, f)
            if inner is not None:
                return inner
        return None if len(want) == len(found) else f"{path}[{min(len(want), len(found))}]"
    return None if want == found and type(want) is type(found) else path


# --- the command ------------------------------------------------------------------------------------------------------

def _refuse(code: str) -> int:
    sys.stderr.write(f"{code}\n")
    return 2


def main(argv: Sequence[str] | None = None, *, services: Any = None) -> int:
    """Spec §2.1. `services` replaces the database reads (tests); the settings are read from the environment."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    url = os.environ.get("DATABASE_URL")
    if not url:
        return _refuse("NO_DATABASE")
    key_dir = os.environ.get(KEY_DIR_ENV)
    if not key_dir:
        return _refuse("NO_KEY_DIR")
    if not _MONTH.match(args.month):
        return _refuse("BAD_MONTH")
    try:
        expect = json.loads(Path(args.expect).read_text(encoding="utf-8"))
        if not isinstance(expect, dict):
            raise ValueError
    except (OSError, ValueError):
        return _refuse("EXPECT_UNREADABLE")
    owned = services is None
    if owned:
        services = Stores(url, key_dir)
    try:
        try:
            tenant_id = services.tenant_id(args.tenant)
        except ReadFailed:
            return _refuse("READ_FAILED")
        if tenant_id is None:
            return _refuse("UNKNOWN_TENANT")
        return _gates(Run(services, tenant_id, args.tenant, args.month, expect))
    finally:
        if owned:
            services.close()


def _gates(run: Run) -> int:
    first = None
    for gate in GATES:
        line = {"gate": gate, "step": STEPS[gate], "state": "PASS", "code": None, "facts": {}}
        run.fresh()
        try:
            getattr(run, gate.lower())()
        except Fail as failed:
            line.update(state="FAIL", code=failed.code, facts=failed.facts)
        except ReadFailed as failed:
            line.update(state="FAIL", code="READ_FAILED", facts={"store": failed.store})
        except Exception:  # noqa: BLE001 - an injected read that raises is that gate's READ_FAILED
            line.update(state="FAIL", code="READ_FAILED", facts={"store": STORES[gate]})
        if line["state"] == "FAIL" and first is None:
            first = (gate, line["code"])
        sys.stdout.write(json.dumps(line, sort_keys=False) + "\n")
    if first is None:
        return 0
    sys.stderr.write(f"DDR_GATE_FAILED {first[0]} {first[1]}\n")
    return 4


if __name__ == "__main__":
    sys.exit(main())
