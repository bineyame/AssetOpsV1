"""6a (spec §4; D-P6.1, D-P6.27): the Postgres store of decisions, their options, one-offs, evaluation runs and choices.

The sole runtime writer of the seven decision tables (the persistence guard): plain INSERT statements only, each under
the tenant's advisory lock after an identity read where the spec says so. The unique indexes `decision_once` and
`decision_choice_once` are the backstop: a violation of one is a re-run and returns the stored row. It reads `site`
(`site_by_id`, D-P6.20), `finding` (`mechanism` only), `agreed_action` (`site_id` only) and `operator_account`
(names), and no other table. Numerics go in as `str(Decimal)` and come back as `Decimal`; jsonb binds as
`CAST(:name AS jsonb)`. Driver errors leave as `StoreUnavailable` with no row text.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Iterator, Literal, Mapping
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Row
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from assetops_backend.chain.ports import SiteRef
from assetops_backend.decisions.records import (ChoiceRow, DecisionBundle, DecisionRow, EffectRow, EvaluationRow,
                                                MissingInput, OneOffRow, OptionRow, RunRow, StoreUnavailable)

_DECISION_ONCE = "decision_once"
_CHOICE_ONCE = "decision_choice_once"
_LOCK = text("SELECT pg_advisory_xact_lock(hashtextextended('decision:' || CAST(:tenant_id AS text), 0))")

_SITE = text("SELECT id, site_code, site_type, timezone FROM site WHERE tenant_id = :t AND site_code_key = lower(:c)")
_SITE_BY_ID = text("SELECT id, site_code, site_type, timezone FROM site WHERE tenant_id = :t AND id = :s")
_SITES = text("SELECT id, site_code, name FROM site WHERE tenant_id = :t")
_FINDING = text("SELECT mechanism FROM finding WHERE tenant_id = :t AND site_id = :s AND id = :f")
_ACTION_SITE = text("SELECT site_id FROM agreed_action WHERE tenant_id = :t AND id = :a")
_NAMES = text("SELECT id, display_name FROM operator_account WHERE tenant_id = :t")

_DECISION_COLUMNS = ("id, tenant_id, site_id, structure_key, lever_id, purpose_factor_id, finding_id, period, "
                     "horizon_months, current_settings, rule_version, prepared_by_person_id, prepared_role, "
                     "prepared_by_script, prepared_at")
_FIND = text(f"SELECT {_DECISION_COLUMNS} FROM decision WHERE tenant_id = :tenant_id AND site_id = :site_id "
             "AND lever_id = :lever_id AND period = :period AND finding_id IS NOT DISTINCT FROM :finding_id")
_DECISION = text(f"SELECT {_DECISION_COLUMNS} FROM decision WHERE tenant_id = :t AND id = :d")
_DECISIONS = text(f"SELECT {_DECISION_COLUMNS} FROM decision WHERE tenant_id = :t "
                  "AND (CAST(:lo AS text) IS NULL OR period >= :lo) AND (CAST(:hi AS text) IS NULL OR period <= :hi) "
                  "ORDER BY prepared_at DESC, id DESC")
_OPTIONS = text("SELECT id, tenant_id, decision_id, option_key, generator, settings, position FROM decision_option "
                "WHERE tenant_id = :t AND decision_id = :d ORDER BY position")
_ONE_OFFS = text("SELECT DISTINCT ON (option_id) id, tenant_id, option_id, amount, currency, crew_visits, basis, "
                 "declared_by_person_id, declared_role, declared_by_script, declared_at FROM option_one_off "
                 "WHERE tenant_id = :t AND option_id IN (SELECT id FROM decision_option "
                 "WHERE tenant_id = :t AND decision_id = :d) ORDER BY option_id, declared_at DESC, id DESC")
_RUN = text("SELECT id, tenant_id, decision_id, evaluator_version, outcome, study_sha256, study_identity, known_at, "
            "run_by_person_id, run_role, run_by_script, run_at FROM option_evaluation_run "
            "WHERE tenant_id = :t AND decision_id = :d ORDER BY run_at DESC, id DESC LIMIT 1")
_EVALUATIONS = text("SELECT e.id, e.option_id, e.disposition, e.reason_code, e.rank, e.monthly_change, "
                    "e.horizon_change, e.one_off_id, e.value, e.currency, e.source_class, e.evidence_class, "
                    "e.missing, e.assumed, e.admission, e.dawn FROM option_evaluation e "
                    "JOIN decision_option o ON o.tenant_id = e.tenant_id AND o.id = e.option_id "
                    "WHERE e.tenant_id = :t AND e.run_id = :r ORDER BY o.position")
_EFFECTS = text("SELECT f.evaluation_id, f.factor_id, f.position, f.change_per_month, f.unit, f.currency, f.missing "
                "FROM option_effect f JOIN option_evaluation e ON e.tenant_id = f.tenant_id AND e.id = f.evaluation_id "
                "WHERE f.tenant_id = :t AND e.run_id = :r ORDER BY f.evaluation_id, f.position")
_CHOICE = text("SELECT id, tenant_id, decision_id, option_id, run_id, agreed_action_id, chosen_by_person_id, "
               "chosen_role, chosen_by_script, chosen_at FROM decision_choice WHERE tenant_id = :t AND decision_id = :d")

_INSERT_DECISION = text(
    "INSERT INTO decision (id, tenant_id, site_id, structure_key, lever_id, purpose_factor_id, finding_id, period, "
    "horizon_months, current_settings, rule_version, prepared_by_person_id, prepared_role, prepared_by_script, "
    "prepared_at) VALUES (:id, :tenant_id, :site_id, :structure_key, :lever_id, :purpose_factor_id, :finding_id, "
    ":period, :horizon_months, CAST(:current_settings AS jsonb), :rule_version, :prepared_by_person_id, "
    ":prepared_role, :prepared_by_script, :prepared_at)")
_INSERT_OPTION = text(
    "INSERT INTO decision_option (id, tenant_id, decision_id, option_key, generator, settings, position) "
    "VALUES (:id, :tenant_id, :decision_id, :option_key, :generator, CAST(:settings AS jsonb), :position)")
_INSERT_ONE_OFF = text(
    "INSERT INTO option_one_off (id, tenant_id, option_id, amount, currency, crew_visits, basis, "
    "declared_by_person_id, declared_role, declared_by_script, declared_at) VALUES (:id, :tenant_id, :option_id, "
    ":amount, :currency, :crew_visits, :basis, :declared_by_person_id, :declared_role, :declared_by_script, "
    ":declared_at)")
_INSERT_RUN = text(
    "INSERT INTO option_evaluation_run (id, tenant_id, decision_id, evaluator_version, outcome, study_sha256, "
    "study_identity, known_at, run_by_person_id, run_role, run_by_script, run_at) VALUES (:id, :tenant_id, "
    ":decision_id, :evaluator_version, :outcome, :study_sha256, CAST(:study_identity AS jsonb), :known_at, "
    ":run_by_person_id, :run_role, :run_by_script, :run_at)")
_INSERT_EVALUATION = text(
    "INSERT INTO option_evaluation (id, tenant_id, run_id, option_id, disposition, reason_code, rank, "
    "monthly_change, horizon_change, one_off_id, value, currency, source_class, evidence_class, missing, assumed, "
    "admission, dawn) VALUES (:id, :tenant_id, :run_id, :option_id, :disposition, :reason_code, :rank, "
    ":monthly_change, :horizon_change, :one_off_id, :value, :currency, :source_class, :evidence_class, "
    "CAST(:missing AS jsonb), CAST(:assumed AS jsonb), CAST(:admission AS jsonb), CAST(:dawn AS jsonb))")
_INSERT_EFFECT = text(
    "INSERT INTO option_effect (id, tenant_id, evaluation_id, factor_id, position, change_per_month, unit, "
    "currency, missing) VALUES (:id, :tenant_id, :evaluation_id, :factor_id, :position, :change_per_month, :unit, "
    ":currency, CAST(:missing AS jsonb))")
_INSERT_CHOICE = text(
    "INSERT INTO decision_choice (id, tenant_id, decision_id, option_id, run_id, agreed_action_id, "
    "chosen_by_person_id, chosen_role, chosen_by_script, chosen_at) VALUES (:id, :tenant_id, :decision_id, "
    ":option_id, :run_id, :agreed_action_id, :chosen_by_person_id, :chosen_role, :chosen_by_script, :chosen_at)")


def _json(value: Any) -> str | None:
    return None if value is None else json.dumps(value)


def _num(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _settings_out(settings: Mapping[str, Decimal]) -> str:
    return json.dumps({k: str(v) for k, v in settings.items()})


def _settings_in(raw: Mapping[str, str]) -> dict[str, Decimal]:
    return {k: Decimal(v) for k, v in raw.items()}


def _missing_out(missing: tuple[MissingInput, ...]) -> str:
    return json.dumps([[m.record_kind, m.source_family, m.factor_id] for m in missing])


def _missing_in(raw: list[list[Any]]) -> tuple[MissingInput, ...]:
    return tuple(MissingInput(kind, family, factor) for kind, family, factor in raw)


def _decision_row(r: Row) -> DecisionRow:
    return DecisionRow(r.id, r.tenant_id, r.site_id, r.structure_key, r.lever_id, r.purpose_factor_id, r.finding_id,
                       r.period, r.horizon_months, _settings_in(r.current_settings), r.rule_version,
                       r.prepared_by_person_id, r.prepared_role, r.prepared_by_script, r.prepared_at)


def _option_row(r: Row) -> OptionRow:
    return OptionRow(r.id, r.tenant_id, r.decision_id, r.option_key, r.generator, _settings_in(r.settings),
                     r.position)


def _one_off_row(r: Row) -> OneOffRow:
    return OneOffRow(r.id, r.tenant_id, r.option_id, r.amount, r.currency, r.crew_visits, r.basis,
                     r.declared_by_person_id, r.declared_role, r.declared_by_script, r.declared_at)


def _choice_row(r: Row) -> ChoiceRow:
    return ChoiceRow(r.id, r.tenant_id, r.decision_id, r.option_id, r.run_id, r.agreed_action_id,
                     r.chosen_by_person_id, r.chosen_role, r.chosen_by_script, r.chosen_at)


def _constraint(error: IntegrityError) -> str | None:
    return getattr(getattr(error.orig, "diag", None), "constraint_name", None)


class PostgresDecisionStore:
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)

    def dispose(self) -> None:
        self._engine.dispose()

    @contextmanager
    def _unavailable(self) -> Iterator[None]:
        try:
            yield
        except SQLAlchemyError:
            raise StoreUnavailable() from None

    # --- reads ---------------------------------------------------------------------------------------------------

    @staticmethod
    def _ref(tenant_id: UUID, found: Row | None) -> SiteRef | None:
        return None if found is None else SiteRef(tenant_id, found.id, found.site_code, found.site_type,
                                                  found.timezone)

    def site(self, tenant_id: UUID, site_code: str) -> SiteRef | None:
        with self._unavailable(), self._engine.connect() as c:
            return self._ref(tenant_id, c.execute(_SITE, {"t": tenant_id, "c": site_code}).one_or_none())

    def site_by_id(self, tenant_id: UUID, site_id: UUID) -> SiteRef | None:
        with self._unavailable(), self._engine.connect() as c:
            return self._ref(tenant_id, c.execute(_SITE_BY_ID, {"t": tenant_id, "s": site_id}).one_or_none())

    def finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> str | None:
        with self._unavailable(), self._engine.connect() as c:
            return c.execute(_FINDING, {"t": tenant_id, "s": site_id, "f": finding_id}).scalar_one_or_none()

    @staticmethod
    def _find(c: Connection, tenant_id: UUID, site_id: UUID, lever_id: str, period: str,
              finding_id: UUID | None) -> DecisionRow | None:
        found = c.execute(_FIND, {"tenant_id": tenant_id, "site_id": site_id, "lever_id": lever_id,
                                  "period": period, "finding_id": finding_id}).one_or_none()
        return None if found is None else _decision_row(found)

    def find_decision(self, tenant_id: UUID, site_id: UUID, lever_id: str, period: str,
                      finding_id: UUID | None) -> DecisionRow | None:
        with self._unavailable(), self._engine.connect() as c:
            return self._find(c, tenant_id, site_id, lever_id, period, finding_id)

    @staticmethod
    def _decision_in(c: Connection, tenant_id: UUID, decision_id: UUID):
        found = c.execute(_DECISION, {"t": tenant_id, "d": decision_id}).one_or_none()
        if found is None:
            return None
        options = tuple(_option_row(r) for r in c.execute(_OPTIONS, {"t": tenant_id, "d": decision_id}))
        return _decision_row(found), options

    def decision(self, tenant_id: UUID, decision_id: UUID) -> tuple[DecisionRow, tuple[OptionRow, ...]] | None:
        with self._unavailable(), self._engine.connect() as c:
            return self._decision_in(c, tenant_id, decision_id)

    @staticmethod
    def _one_offs_in(c: Connection, tenant_id: UUID, decision_id: UUID) -> dict[UUID, OneOffRow]:
        rows = c.execute(_ONE_OFFS, {"t": tenant_id, "d": decision_id}).all()
        return {r.option_id: _one_off_row(r) for r in rows}

    def latest_one_offs(self, tenant_id: UUID, decision_id: UUID) -> Mapping[UUID, OneOffRow]:
        with self._unavailable(), self._engine.connect() as c:
            return self._one_offs_in(c, tenant_id, decision_id)

    @staticmethod
    def _run_in(c: Connection, tenant_id: UUID, decision_id: UUID) -> RunRow | None:
        run = c.execute(_RUN, {"t": tenant_id, "d": decision_id}).one_or_none()
        if run is None:
            return None
        effects: dict[UUID, list[EffectRow]] = {}
        for f in c.execute(_EFFECTS, {"t": tenant_id, "r": run.id}):
            effects.setdefault(f.evaluation_id, []).append(
                EffectRow(f.factor_id, f.position, f.change_per_month, f.unit, f.currency, _missing_in(f.missing)))
        evaluations = tuple(
            EvaluationRow(e.id, e.option_id, e.disposition, e.reason_code, e.rank, e.monthly_change,
                          e.horizon_change, e.one_off_id, e.value, e.currency, e.source_class, e.evidence_class,
                          _missing_in(e.missing), tuple(e.assumed), e.admission, e.dawn,
                          tuple(effects.get(e.id, ())))
            for e in c.execute(_EVALUATIONS, {"t": tenant_id, "r": run.id}))
        return RunRow(run.id, run.tenant_id, run.decision_id, run.evaluator_version, run.outcome, run.study_sha256,
                      run.study_identity, run.known_at, run.run_by_person_id, run.run_role, run.run_by_script,
                      run.run_at, evaluations)

    def latest_run(self, tenant_id: UUID, decision_id: UUID) -> RunRow | None:
        with self._unavailable(), self._engine.connect() as c:
            return self._run_in(c, tenant_id, decision_id)

    def agreed_action_site(self, tenant_id: UUID, action_id: UUID) -> UUID | None | Literal[False]:
        with self._unavailable(), self._engine.connect() as c:
            found = c.execute(_ACTION_SITE, {"t": tenant_id, "a": action_id}).one_or_none()
        return False if found is None else found.site_id

    def choice(self, tenant_id: UUID, decision_id: UUID) -> ChoiceRow | None:
        with self._unavailable(), self._engine.connect() as c:
            found = c.execute(_CHOICE, {"t": tenant_id, "d": decision_id}).one_or_none()
        return None if found is None else _choice_row(found)

    def for_tenant(self, tenant_id: UUID, period_from: str | None, period_to: str | None
                   ) -> tuple[DecisionBundle, ...]:
        with self._unavailable(), self._engine.connect() as c:
            names = {r.id: r.display_name for r in c.execute(_NAMES, {"t": tenant_id})}
            sites = {r.id: (r.site_code, r.name) for r in c.execute(_SITES, {"t": tenant_id})}
            out = []
            for d in c.execute(_DECISIONS, {"t": tenant_id, "lo": period_from, "hi": period_to}).all():
                row = _decision_row(d)
                _, options = self._decision_in(c, tenant_id, row.id)
                one_offs = self._one_offs_in(c, tenant_id, row.id)
                run = self._run_in(c, tenant_id, row.id)
                found = c.execute(_CHOICE, {"t": tenant_id, "d": row.id}).one_or_none()
                choice = None if found is None else _choice_row(found)
                people = {row.prepared_by_person_id, *(o.declared_by_person_id for o in one_offs.values())}
                people.update(p.run_by_person_id for p in (run,) if p is not None)
                people.update(p.chosen_by_person_id for p in (choice,) if p is not None)
                code, name = sites[row.site_id]
                out.append(DecisionBundle(row, code, name, options, one_offs, run, choice,
                                          {p: names[p] for p in people}))
            return tuple(out)

    # --- writes --------------------------------------------------------------------------------------------------

    def add_decision(self, row: DecisionRow, options: tuple[OptionRow, ...]) -> tuple[DecisionRow, bool]:
        with self._unavailable():
            try:
                with self._engine.begin() as c:
                    c.execute(_LOCK, {"tenant_id": str(row.tenant_id)})
                    stored = self._find(c, row.tenant_id, row.site_id, row.lever_id, row.period, row.finding_id)
                    if stored is not None:
                        return stored, True
                    c.execute(_INSERT_DECISION, {
                        "id": row.id, "tenant_id": row.tenant_id, "site_id": row.site_id,
                        "structure_key": row.structure_key, "lever_id": row.lever_id,
                        "purpose_factor_id": row.purpose_factor_id, "finding_id": row.finding_id,
                        "period": row.period, "horizon_months": row.horizon_months,
                        "current_settings": _settings_out(row.current_settings), "rule_version": row.rule_version,
                        "prepared_by_person_id": row.prepared_by_person_id, "prepared_role": row.prepared_role,
                        "prepared_by_script": row.prepared_by_script, "prepared_at": row.prepared_at})
                    for o in options:
                        c.execute(_INSERT_OPTION, {"id": o.id, "tenant_id": o.tenant_id,
                                                   "decision_id": o.decision_id, "option_key": o.option_key,
                                                   "generator": o.generator,
                                                   "settings": _settings_out(o.settings), "position": o.position})
                return row, False
            except IntegrityError as error:
                if _constraint(error) != _DECISION_ONCE:
                    raise
            with self._engine.connect() as c:
                stored = self._find(c, row.tenant_id, row.site_id, row.lever_id, row.period, row.finding_id)
            if stored is None:
                raise StoreUnavailable()
            return stored, True

    def add_one_off(self, row: OneOffRow) -> OneOffRow:
        with self._unavailable(), self._engine.begin() as c:
            c.execute(_INSERT_ONE_OFF, {
                "id": row.id, "tenant_id": row.tenant_id, "option_id": row.option_id, "amount": _num(row.amount),
                "currency": row.currency, "crew_visits": row.crew_visits, "basis": row.basis,
                "declared_by_person_id": row.declared_by_person_id, "declared_role": row.declared_role,
                "declared_by_script": row.declared_by_script, "declared_at": row.declared_at})
        return row

    def add_run(self, run: RunRow) -> RunRow:
        with self._unavailable(), self._engine.begin() as c:
            c.execute(_INSERT_RUN, {
                "id": run.id, "tenant_id": run.tenant_id, "decision_id": run.decision_id,
                "evaluator_version": run.evaluator_version, "outcome": run.outcome,
                "study_sha256": run.study_sha256, "study_identity": _json(run.study_identity),
                "known_at": run.known_at, "run_by_person_id": run.run_by_person_id, "run_role": run.run_role,
                "run_by_script": run.run_by_script, "run_at": run.run_at})
            for e in run.evaluations:
                c.execute(_INSERT_EVALUATION, {
                    "id": e.id, "tenant_id": run.tenant_id, "run_id": run.id, "option_id": e.option_id,
                    "disposition": e.disposition, "reason_code": e.reason_code, "rank": e.rank,
                    "monthly_change": _num(e.monthly_change), "horizon_change": _num(e.horizon_change),
                    "one_off_id": e.one_off_id, "value": _num(e.value), "currency": e.currency,
                    "source_class": e.source_class, "evidence_class": e.evidence_class,
                    "missing": _missing_out(e.missing), "assumed": json.dumps(list(e.assumed)),
                    "admission": _json(e.admission), "dawn": _json(e.dawn)})
                for f in e.effects:
                    c.execute(_INSERT_EFFECT, {
                        "id": uuid4(), "tenant_id": run.tenant_id, "evaluation_id": e.id,
                        "factor_id": f.factor_id, "position": f.position,
                        "change_per_month": _num(f.change_per_month), "unit": f.unit, "currency": f.currency,
                        "missing": _missing_out(f.missing)})
        return run

    def add_choice(self, row: ChoiceRow) -> tuple[ChoiceRow, bool]:
        with self._unavailable():
            try:
                with self._engine.begin() as c:
                    c.execute(_LOCK, {"tenant_id": str(row.tenant_id)})
                    found = c.execute(_CHOICE, {"t": row.tenant_id, "d": row.decision_id}).one_or_none()
                    if found is not None:
                        return _choice_row(found), True
                    c.execute(_INSERT_CHOICE, {
                        "id": row.id, "tenant_id": row.tenant_id, "decision_id": row.decision_id,
                        "option_id": row.option_id, "run_id": row.run_id, "agreed_action_id": row.agreed_action_id,
                        "chosen_by_person_id": row.chosen_by_person_id, "chosen_role": row.chosen_role,
                        "chosen_by_script": row.chosen_by_script, "chosen_at": row.chosen_at})
                return row, False
            except IntegrityError as error:
                if _constraint(error) != _CHOICE_ONCE:
                    raise
            stored = self.choice(row.tenant_id, row.decision_id)
            if stored is None:
                raise StoreUnavailable()
            return stored, True

