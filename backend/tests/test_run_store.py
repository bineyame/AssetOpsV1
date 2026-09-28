"""The run store: a Draft survives a restart, or it was never written.

These tests reach the adapter directly, which is what a test is allowed to do
and a product module is not. Everything above the composition module receives
the port.

Two properties carry the weight. A persisted Draft comes back byte-for-byte
equal as a record - not similar, equal - because a frozen identity that does
not survive its own round trip is not frozen. And a create that fails leaves
the store exactly as it was: no partial document, no stray file, nothing a
later read would pick up.
"""

from __future__ import annotations

import threading
from dataclasses import replace
from pathlib import Path

import pytest
from scenario_fixtures import scenario_document

from assetops_backend.scenarios.parsing import parse_scenario_document
from run_fixtures import (
    FakeRuns,
    FakeScenarios,
    FakeSites,
    model_profile,
    publication_profile,
    scenario,
    setup_request,
    site,
)

from assetops_backend.runs.adapters import yaml_run_documents, yaml_run_store
from assetops_backend.runs.adapters.yaml_run_documents import DOCUMENT_SUFFIX
from assetops_backend.runs.adapters.yaml_run_store import (
    RUN_STORE_ROOT,
    YamlRunStore,
)
from assetops_backend.runs.models import FrozenParameter, SimulationRun
from assetops_backend.runs.ports import (
    RunConfigurationInvalid,
    RunIdentityConflict,
    RunNotFound,
    RunStoreUnavailable,
)
from assetops_backend.runs.service import RunSetupService


def a_run(**overrides) -> SimulationRun:
    """One frozen Draft, produced by the real service.

    Built rather than hand-written, so the document these tests round-trip is
    the document the product actually writes.
    """
    setup = RunSetupService(
        FakeRuns(),
        FakeSites((site(),)),
        FakeScenarios((scenario(),)),
        model_profiles=(model_profile(),),
        publication_profiles=(publication_profile(),),
        now=lambda: "2026-09-21T09:00:00Z",
    )
    return setup.create_draft_run(setup_request(**overrides))


class TestPersistence:
    def test_a_draft_survives_a_restart(self, tmp_path: Path) -> None:
        """A second store over the same root is what a restart looks like."""
        record = a_run()
        YamlRunStore(tmp_path).create_run(record)

        after_restart = YamlRunStore(tmp_path)

        assert after_restart.get_run(record.run_id) == record
        assert after_restart.list_runs() == (record,)

    def test_the_whole_frozen_identity_round_trips(self, tmp_path: Path) -> None:
        record = a_run()
        YamlRunStore(tmp_path).create_run(record)

        stored = YamlRunStore(tmp_path).get_run(record.run_id)

        assert stored.deterministic_identity == record.deterministic_identity
        assert stored.blocking_reasons == record.blocking_reasons
        assert stored.created_at == record.created_at
        assert stored.execution_status == record.execution_status

    def test_a_blocked_draft_round_trips_with_its_reasons(
        self, tmp_path: Path
    ) -> None:
        setup = RunSetupService(
            FakeRuns(),
            FakeSites((site(),)),
            FakeScenarios((scenario(),)),
            model_profiles=(model_profile(),),
            publication_profiles=(publication_profile(gateway_id=None),),
            now=lambda: "2026-09-21T09:00:00Z",
        )
        record = setup.create_draft_run(setup_request())
        assert record.execution_status == "BLOCKED"

        YamlRunStore(tmp_path).create_run(record)

        assert YamlRunStore(tmp_path).get_run(record.run_id) == record

    def test_overlapping_drafts_are_allowed(self, tmp_path: Path) -> None:
        """Two Drafts over the same site, scenario and interval. Deliberately
        permitted: experimentation is what a Draft is for, and Commit is where
        overlap is decided."""
        store = YamlRunStore(tmp_path)
        first = a_run()
        second = a_run()

        store.create_run(first)
        store.create_run(second)

        assert first.run_id != second.run_id
        assert {record.run_id for record in store.list_runs()} == {
            first.run_id,
            second.run_id,
        }

    def test_an_empty_store_is_empty_rather_than_unreadable(
        self, tmp_path: Path
    ) -> None:
        store = YamlRunStore(tmp_path / "not-created-yet")

        assert store.list_runs() == ()

    def test_an_unknown_run_is_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(RunNotFound):
            YamlRunStore(tmp_path).get_run("run-" + "0" * 32)


class TestTheWriteIsAllOrNothing:
    def test_the_same_identity_is_never_written_twice(
        self, tmp_path: Path
    ) -> None:
        store = YamlRunStore(tmp_path)
        record = a_run()
        store.create_run(record)

        with pytest.raises(RunIdentityConflict):
            store.create_run(record)

        assert len(store.list_runs()) == 1

    def test_no_staging_file_is_left_behind(self, tmp_path: Path) -> None:
        store = YamlRunStore(tmp_path)
        store.create_run(a_run())

        left = [path.name for path in tmp_path.iterdir()]

        assert len(left) == 1
        assert left[0].endswith(DOCUMENT_SUFFIX)

    def test_a_hand_edited_document_is_refused_rather_than_read(
        self, tmp_path: Path
    ) -> None:
        """The store's own parser is strict about the product's own output.

        A status somebody typed is exactly the thing that must not come back
        as a run: this edit makes a run with blocking reasons claim to be
        READY, which the record's invariant refuses.
        """
        store = YamlRunStore(tmp_path)
        setup = RunSetupService(
            FakeRuns(),
            FakeSites((site(),)),
            FakeScenarios((scenario(),)),
            model_profiles=(model_profile(),),
            publication_profiles=(publication_profile(gateway_id=None),),
            now=lambda: "2026-09-21T09:00:00Z",
        )
        store.create_run(setup.create_draft_run(setup_request()))

        document = next(tmp_path.glob(f"*{DOCUMENT_SUFFIX}"))
        document.write_text(
            document.read_text(encoding="utf-8").replace(
                "execution_status: BLOCKED", "execution_status: READY"
            ),
            encoding="utf-8",
        )

        with pytest.raises(RunConfigurationInvalid):
            YamlRunStore(tmp_path).list_runs()

    def test_an_unreadable_document_is_refused_rather_than_skipped(
        self, tmp_path: Path
    ) -> None:
        store = YamlRunStore(tmp_path)
        store.create_run(a_run())

        document = next(tmp_path.glob(f"*{DOCUMENT_SUFFIX}"))
        document.write_text("this: is: not: a run", encoding="utf-8")

        with pytest.raises(RunConfigurationInvalid):
            YamlRunStore(tmp_path).list_runs()


class TestAnUnansweredInitialValueSurvivesTheStore:
    """A blocked Draft whose initial value nobody answered for.

    The absent case is part of the frozen deterministic identity, so it has
    to round trip like every other part of it. A store that wrote it and read
    it back as something else - a zero, an error - would lose exactly the
    fact the run was blocked for.
    """

    def _blocked_with_a_hole(self) -> SimulationRun:
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "MODEL_RULE"
        setup = RunSetupService(
            FakeRuns(),
            FakeSites((site(),)),
            FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            ),
            model_profiles=(model_profile(),),
            publication_profiles=(publication_profile(),),
            now=lambda: "2026-09-22T09:00:00Z",
        )
        record = setup.create_draft_run(setup_request())
        assert record.execution_status == "BLOCKED"
        assert record.deterministic_identity.initialization_inputs[0].value is None
        return record

    def test_it_round_trips(self, tmp_path: Path) -> None:
        record = self._blocked_with_a_hole()
        YamlRunStore(tmp_path).create_run(record)

        stored = YamlRunStore(tmp_path).get_run(record.run_id)

        assert stored == record
        assert stored.deterministic_identity.initialization_inputs[0].value is None
        assert (
            stored.deterministic_identity.initialization_inputs[0].unit == "L"
        )

    def test_half_an_absent_value_is_refused(self, tmp_path: Path) -> None:
        """The two number fields are absent together or present together."""
        YamlRunStore(tmp_path).create_run(self._blocked_with_a_hole())
        document = next(tmp_path.glob(f"*{DOCUMENT_SUFFIX}"))
        text = document.read_text(encoding="utf-8")
        assert "canonical_value: null" in text
        document.write_text(
            text.replace("canonical_value: null", "canonical_value: 0.0"),
            encoding="utf-8",
        )

        with pytest.raises(RunConfigurationInvalid):
            YamlRunStore(tmp_path).list_runs()

    def test_a_stored_reason_about_another_state_does_not_explain_it(
        self, tmp_path: Path
    ) -> None:
        """A hand-edited document in the shape the final review constructed.

        This is why the rule lives on the record rather than in the service:
        the service cannot produce this, and a document can.
        """
        YamlRunStore(tmp_path).create_run(self._blocked_with_a_hole())
        document = next(tmp_path.glob(f"*{DOCUMENT_SUFFIX}"))
        text = document.read_text(encoding="utf-8")
        assert "subject: example-stored-volume" in text
        document.write_text(
            text.replace(
                "subject: example-stored-volume",
                "subject: example-publication",
            ).replace(
                "kind: INITIAL_VALUE_NOT_RESOLVED",
                "kind: GATEWAY_IDENTITY_NOT_RESOLVED",
            ),
            encoding="utf-8",
        )

        with pytest.raises(RunConfigurationInvalid):
            YamlRunStore(tmp_path).list_runs()

    def test_a_stored_ready_run_may_not_carry_one(self, tmp_path: Path) -> None:
        """The record's invariant, met through the parser."""
        YamlRunStore(tmp_path).create_run(self._blocked_with_a_hole())
        document = next(tmp_path.glob(f"*{DOCUMENT_SUFFIX}"))
        text = document.read_text(encoding="utf-8")
        start = text.index("blocking_reasons:")
        end = text.index("unsupported_optional_inputs:")
        document.write_text(
            text[:start].replace(
                "execution_status: BLOCKED", "execution_status: READY"
            )
            + "blocking_reasons: []\n"
            + text[end:],
            encoding="utf-8",
        )

        with pytest.raises(RunConfigurationInvalid):
            YamlRunStore(tmp_path).list_runs()


class TestAStoredRunMayNotContradictItself:
    """The two cadence fields say different kinds of thing, and a document
    where they disagree is a run a reader cannot interpret.

    Reached by editing a written document rather than by constructing a
    record, because this is the parser's rule and the parser only ever sees
    documents. The store writes valid ones; the point is what happens when
    something else does not.
    """

    def _stored(self, tmp_path: Path) -> Path:
        YamlRunStore(tmp_path).create_run(a_run())
        return next(tmp_path.glob(f"*{DOCUMENT_SUFFIX}"))

    def test_a_cadence_on_an_operator_record_is_refused(
        self, tmp_path: Path
    ) -> None:
        """Two real fields disagreeing, which is worth checking.

        The pair of tests that used to sit here checked `cadence_resolution`
        against the fields it restated - a record against itself. T020
        deleted the field, so those went with it. This one remains because a
        person writing a value down reports at no rate: a cadence on an
        operator record is a document saying two things that cannot both be
        true.
        """
        document = self._stored(tmp_path)
        text = document.read_text(encoding="utf-8")
        # Replaced rather than inserted: a second `cadence_minutes` key in
        # the same block is a duplicate YAML key, which the loader resolves
        # to the last one, and the test then proves nothing.
        assert text.count("cadence_minutes: null") == 1
        document.write_text(
            text.replace("cadence_minutes: null", "cadence_minutes: 15"),
            encoding="utf-8",
        )

        with pytest.raises(RunConfigurationInvalid):
            YamlRunStore(tmp_path).list_runs()

    def test_a_document_still_carrying_the_deleted_key_is_read(
        self, tmp_path: Path
    ) -> None:
        """The Drafts written before T020 stay readable.

        A run document accepts keys it does not know, so the thirty-four runs
        in the store carrying `cadence_resolution` are read with the key
        ignored rather than refused. Nothing was cleared, and this is the
        test that says so rather than a sentence in a packet.
        """
        document = self._stored(tmp_path)
        text = document.read_text(encoding="utf-8")
        assert "    cadence_minutes: 15\n" in text
        document.write_text(
            text.replace(
                "    cadence_minutes: 15\n",
                "    cadence_minutes: 15\n"
                "    cadence_resolution: MODEL_PROFILE\n",
            ),
            encoding="utf-8",
        )

        stored = YamlRunStore(tmp_path).list_runs()

        assert len(stored) == 1
        binding = {
            item.source_id: item
            for item in stored[0].deterministic_identity.observation_bindings
        }["example-device-reading"]
        assert binding.cadence_minutes == 15

    def test_an_unknown_cadence_owner_is_refused(self, tmp_path: Path) -> None:
        """The field the review found being read as free text while every
        field beside it was a closed vocabulary."""
        document = self._stored(tmp_path)
        document.write_text(
            document.read_text(encoding="utf-8").replace(
                "cadence_ownership: NOT_DECLARED",
                "cadence_ownership: EVERY_FIFTEEN_MINUTES",
            ),
            encoding="utf-8",
        )

        with pytest.raises(RunConfigurationInvalid):
            YamlRunStore(tmp_path).list_runs()

    def test_the_document_this_edits_is_the_one_the_store_writes(
        self, tmp_path: Path
    ) -> None:
        """Non-vacuity: the three edits above each replace text that is
        really there, so none of them is a test of a string that never
        appeared in a run document."""
        text = self._stored(tmp_path).read_text(encoding="utf-8")

        assert "cadence_minutes: 15" in text
        assert "cadence_ownership: NOT_DECLARED" in text
        # And the key T020 deleted is not written any more, which is the
        # other half of "the document this edits is the one the store writes".
        assert "cadence_resolution" not in text


class TestTheStoreRoot:
    def test_the_root_is_outside_every_shipped_configuration_root(self) -> None:
        """A run is a record this installation produced, so it is no more
        shippable than a user's site."""
        parts = RUN_STORE_ROOT.parts

        assert parts[-2:] == ("var", "runs")
        assert "config" not in parts


class TestTheBoundaryThatActuallyStopsAValuelessResolvedParameter:
    """Where a resolved parameter with no number is stopped, and where it is not.

    `runs/service.py` used to comment that the run record would refuse such a
    parameter loudly if a future slice reopened the shape the scenario parser
    now closes. A second independent review showed that is false:
    `FrozenParameter` is annotated and not validated, and
    `SimulationRun.__post_init__` checks initialization rows rather than
    resolved parameters, so a record built that way comes back `READY` with no
    reasons.

    The protection is real and it is one layer out. `YamlRunStore.create_run`
    re-reads its own staged document before committing it, and the run
    document parser will not take a resolved parameter with no number - so the
    write is refused and the directory is left empty.

    This is here rather than asserted in a comment because a future author
    will build on whichever of those two statements they read. The record
    below is constructed directly, bypassing the parser that refuses to
    produce it, which is the only way such a record can exist at all.
    """

    def _record_with_a_valueless_resolved_parameter(self) -> SimulationRun:
        record = a_run()
        identity = record.deterministic_identity
        scenario_binding = identity.scenario
        return replace(
            record,
            deterministic_identity=replace(
                identity,
                scenario=replace(
                    scenario_binding,
                    resolved_parameters=scenario_binding.resolved_parameters
                    + (
                        FrozenParameter(
                            parameter_id="foundation-coefficient",
                            value=None,  # type: ignore[arg-type]
                            unit="L/kWh",
                            answered_by="SCENARIO",
                        ),
                    ),
                ),
            ),
        )

    def test_the_run_record_itself_does_not_reject_it(self) -> None:
        """Stated as a test so the limitation cannot be mistaken again.

        If a later slice makes `FrozenParameter` validate, this fails and
        whoever changes it gets to delete it and say so - which is the point.
        A limitation nobody has written down is a limitation somebody assumes
        away.
        """
        record = self._record_with_a_valueless_resolved_parameter()

        assert record.execution_status == "READY"
        assert record.blocking_reasons == ()
        assert record.deterministic_identity.scenario.resolved_parameters[
            -1
        ].value is None

    def test_the_store_refuses_it_and_leaves_nothing_behind(
        self, tmp_path: Path
    ) -> None:
        store = YamlRunStore(tmp_path)

        with pytest.raises(RunConfigurationInvalid) as error:
            store.create_run(self._record_with_a_valueless_resolved_parameter())

        assert "resolved_parameter.value" in str(error.value)
        assert store.list_runs() == ()
        assert list(tmp_path.iterdir()) == []

    def test_the_same_record_with_a_number_is_written(
        self, tmp_path: Path
    ) -> None:
        """Non-vacuous: the refusal is about the absent number.

        Without this the test above would pass against a store that refused
        every record, or against a fixture that was malformed for some other
        reason.
        """
        record = a_run()
        store = YamlRunStore(tmp_path)

        store.create_run(record)

        assert [item.run_id for item in store.list_runs()] == [record.run_id]


def a_store_of(
    root: Path, count: int
) -> tuple[YamlRunStore, tuple[SimulationRun, ...]]:
    """A store holding `count` Drafts, and the records it holds."""
    store = YamlRunStore(root)
    records = tuple(a_run() for _ in range(count))
    for record in records:
        store.create_run(record)
    return store, records


@pytest.fixture(scope="module")
def ten(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[YamlRunStore, tuple[SimulationRun, ...]]:
    """Ten stored Drafts, written once and shared by the reads that use them.

    Module-scoped because every test taking it only reads: each write fsyncs a
    document, and rebuilding the same ten per test cost more than the rest of
    this file put together. Tests that corrupt or rearrange a store build their
    own.
    """
    return a_store_of(tmp_path_factory.mktemp("ten-runs"), 10)


class TestASingleReadCostsOneRun:
    """One read reads one run, and reads it exactly as strictly as before.

    The defect these close is not hypothetical and was not found by a test: the
    owner stepped the first real run and every interaction took about nine
    seconds, because `get_run` parsed all 216 stored documents to answer a
    question about one of them.

    Cost is asserted by counting documents parsed rather than by timing. A clock
    measures the machine that happens to be running; a count measures the
    property - that a store of any size costs one parse - and it fails loudly on
    the change that would reintroduce the defect.
    """

    @pytest.fixture
    def parsed(self, monkeypatch: pytest.MonkeyPatch) -> list[Path]:
        """Every document the store parses, in the order it parses them.

        Both module references are replaced because there are two: the bulk
        reader calls its own module's name and the store calls the one it
        imported. Patching one would count half the store's reading and would
        make the assertions below true of a store that still walks everything.
        """
        seen: list[Path] = []
        real = yaml_run_documents.read_run_record

        def counting(path: Path) -> SimulationRun:
            seen.append(path)
            return real(path)

        monkeypatch.setattr(yaml_run_documents, "read_run_record", counting)
        monkeypatch.setattr(yaml_run_store, "read_run_record", counting)
        return seen

    def test_the_count_sees_the_whole_store_being_read(
        self,
        ten: tuple[YamlRunStore, tuple[SimulationRun, ...]],
        parsed: list[Path],
    ) -> None:
        """Non-vacuity for every assertion below.

        If the counter could not observe the bulk reader, "one read parses one
        document" would be true of an instrument that cannot see more than one.
        """
        store, _ = ten
        parsed.clear()

        store.list_runs()

        assert len(parsed) == 10

    def test_one_read_parses_one_document(
        self,
        ten: tuple[YamlRunStore, tuple[SimulationRun, ...]],
        parsed: list[Path],
    ) -> None:
        store, records = ten
        wanted = records[0]
        parsed.clear()

        assert store.get_run(wanted.run_id) == wanted

        assert len(parsed) == 1
        assert parsed[0].name == f"{wanted.run_id}{DOCUMENT_SUFFIX}"

    def test_the_cost_does_not_grow_with_the_store(
        self,
        tmp_path: Path,
        ten: tuple[YamlRunStore, tuple[SimulationRun, ...]],
        parsed: list[Path],
    ) -> None:
        """The same read, against a store three times the size.

        The record read is the one written first, so a store that answered
        cheaply only for whatever it wrote last would fail here.
        """
        ten_store, ten_records = ten
        thirty_store, thirty_records = a_store_of(tmp_path / "thirty", 30)

        parsed.clear()
        assert ten_store.get_run(ten_records[0].run_id) == ten_records[0]
        cost_of_ten = len(parsed)

        parsed.clear()
        assert thirty_store.get_run(thirty_records[0].run_id) == thirty_records[0]
        cost_of_thirty = len(parsed)

        assert cost_of_ten == 1
        assert cost_of_thirty == 1

    def test_a_case_variant_resolves_the_same_record(
        self,
        ten: tuple[YamlRunStore, tuple[SimulationRun, ...]],
        parsed: list[Path],
    ) -> None:
        """Identity comparison still decides, and still folds case."""
        store, records = ten
        wanted = records[3]
        parsed.clear()

        assert store.get_run(wanted.run_id.upper()) == wanted
        assert len(parsed) == 1

    def test_an_identity_no_run_could_carry_is_not_found(
        self, ten: tuple[YamlRunStore, tuple[SimulationRun, ...]]
    ) -> None:
        """And it never becomes a path.

        A separator, a parent reference and a drive letter are all refused by
        the shape rule before anything is opened, so a read cannot address a
        file outside the store however the identity is spelled. The store is
        populated, so a refusal here is about the identity rather than about an
        empty directory.
        """
        store, _ = ten

        for identity in (
            "../../../etc/passwd",
            "run-0000/../../secret",
            "C:/Windows/win.ini",
            "not-a-run",
        ):
            with pytest.raises(RunNotFound):
                store.get_run(identity)

    def test_a_well_formed_absent_identity_is_not_found(
        self, ten: tuple[YamlRunStore, tuple[SimulationRun, ...]]
    ) -> None:
        store, _ = ten

        with pytest.raises(RunNotFound):
            store.get_run("run-" + "0" * 32)

    def test_the_requested_runs_own_broken_document_refuses_with_its_reason(
        self, tmp_path: Path
    ) -> None:
        """The fast path is not a looser path.

        The edit is the one `TestTheWriteIsAllOrNothing` makes against the
        inventory: a hand-typed status the record's own invariant refuses. A
        single read of that run has to refuse it for the same reason.
        """
        store = YamlRunStore(tmp_path)
        setup = RunSetupService(
            FakeRuns(),
            FakeSites((site(),)),
            FakeScenarios((scenario(),)),
            model_profiles=(model_profile(),),
            publication_profiles=(publication_profile(gateway_id=None),),
            now=lambda: "2026-09-21T09:00:00Z",
        )
        blocked = setup.create_draft_run(setup_request())
        store.create_run(blocked)

        document = tmp_path / f"{blocked.run_id}{DOCUMENT_SUFFIX}"
        document.write_text(
            document.read_text(encoding="utf-8").replace(
                "execution_status: BLOCKED", "execution_status: READY"
            ),
            encoding="utf-8",
        )

        with pytest.raises(RunConfigurationInvalid) as refusal:
            YamlRunStore(tmp_path).get_run(blocked.run_id)

        assert blocked.run_id in str(refusal.value)

    def test_one_broken_document_does_not_break_an_unrelated_read(
        self, tmp_path: Path
    ) -> None:
        """Criterion 4, and the one behaviour this slice deliberately changes.

        Before, a single read walked the store, so any unreadable document
        anywhere refused every read. Now a run whose own document is sound
        reads back. The inventory is unchanged and still fails whole, which is
        asserted here rather than assumed: a partial inventory would be a wrong
        answer rather than a slow one.
        """
        store, records = a_store_of(tmp_path, 5)
        wanted = records[0]
        broken = records[-1]

        (tmp_path / f"{broken.run_id}{DOCUMENT_SUFFIX}").write_text(
            "this: is: not: a run", encoding="utf-8"
        )

        assert YamlRunStore(tmp_path).get_run(wanted.run_id) == wanted

        with pytest.raises(RunConfigurationInvalid):
            YamlRunStore(tmp_path).list_runs()

    def test_a_document_filed_under_another_name_is_still_found(
        self, tmp_path: Path, parsed: list[Path]
    ) -> None:
        """The records already on disk are the test, including rearranged ones.

        No document this store wrote is filed under anything but its own
        case-folded identity, so this is about a store somebody rearranged by
        hand. It is here because the change being guarded is one that could be
        right going forward and silently wrong going backward: a read that only
        ever looked at the expected name would make a record the inventory
        still lists unreachable by identity.
        """
        store, records = a_store_of(tmp_path, 5)
        moved = records[2]
        (tmp_path / f"{moved.run_id}{DOCUMENT_SUFFIX}").rename(
            tmp_path / f"run-{'f' * 32}{DOCUMENT_SUFFIX}"
        )
        parsed.clear()

        assert store.get_run(moved.run_id) == moved

        # Finding it cost the whole store, which is the honest price of a name
        # that leads nowhere and is the price it always was.
        assert len(parsed) == 5

    def test_a_run_is_never_answered_under_another_runs_name(
        self, tmp_path: Path
    ) -> None:
        """Locating by name is not reading identity out of a name.

        The document filed as `run-ff...ff` declares a different run. Asking for
        `run-ff...ff` must not return it, because a lookup that fell back to
        whatever was filed there would put one run's frozen identity under
        another run's name.
        """
        store, records = a_store_of(tmp_path, 3)
        moved = records[0]
        impostor = f"run-{'f' * 32}"
        (tmp_path / f"{moved.run_id}{DOCUMENT_SUFFIX}").rename(
            tmp_path / f"{impostor}{DOCUMENT_SUFFIX}"
        )

        with pytest.raises(RunNotFound):
            store.get_run(impostor)

        assert store.get_run(moved.run_id) == moved

    def test_a_read_during_a_write_returns_a_whole_record(
        self, tmp_path: Path
    ) -> None:
        """Concurrency is unchanged, at the level a reader meets it.

        One thread creates runs while another reads an existing one. Every read
        must return that record whole and equal - never a partial document,
        never a staging file, never a refusal - and every write must land.
        """
        store = YamlRunStore(tmp_path)
        target = a_run()
        store.create_run(target)
        pending = [a_run() for _ in range(10)]

        failures: list[BaseException] = []
        reads = 0
        done = threading.Event()

        def write() -> None:
            try:
                for record in pending:
                    store.create_run(record)
            except BaseException as error:  # pragma: no cover - asserted below
                failures.append(error)
            finally:
                done.set()

        def read() -> None:
            nonlocal reads
            while not done.is_set():
                try:
                    assert store.get_run(target.run_id) == target
                except BaseException as error:
                    failures.append(error)
                    return
                reads += 1

        writer = threading.Thread(target=write)
        reader = threading.Thread(target=read)
        reader.start()
        writer.start()
        writer.join()
        reader.join()

        assert failures == []
        assert reads > 0
        assert len(store.list_runs()) == len(pending) + 1
        assert [
            path.name
            for path in tmp_path.iterdir()
            if not path.name.endswith(DOCUMENT_SUFFIX)
        ] == []

    def test_a_stat_failure_crosses_the_seam_as_a_store_failure(
        self,
        ten: tuple[YamlRunStore, tuple[SimulationRun, ...]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The one filesystem touch outside the strict reader still translates.

        `is_file` answers False for "not there" and lets a permission denial, a
        sharing violation and an unacceptable path through. Untranslated, that
        `OSError` crosses the port and the route that answers 503 for an
        unreachable store answers 500 instead - so the caller is told the
        server broke rather than that the store could not be read.

        Raised only for the requested document, so what is being measured is
        the stat on the fast path rather than any other file the store touches.
        """
        store, records = ten
        wanted = records[0]
        real_is_file = Path.is_file

        def denied(self: Path) -> bool:
            if self.name == f"{wanted.run_id}{DOCUMENT_SUFFIX}":
                raise PermissionError(13, "Access is denied")
            return real_is_file(self)

        monkeypatch.setattr(Path, "is_file", denied)

        with pytest.raises(RunStoreUnavailable) as refusal:
            store.get_run(wanted.run_id)

        assert wanted.run_id in str(refusal.value)

    def test_a_document_outside_the_store_is_never_opened(
        self, tmp_path: Path
    ) -> None:
        """The shape check is load-bearing, and this is what it bears.

        The packet for this slice called the shape check defence in depth and
        said it had found no mutation that could fail a test without it. This
        is that mutation's target: the identity comparison cannot prevent an
        out-of-root read, because the file is opened and parsed BEFORE there is
        an identity to compare. Neuter `is_allocated_run_id_key` and this
        refusal becomes `RunConfigurationInvalid` naming a file the store does
        not own, which is both an arbitrary read and an existence oracle.

        The sentinel is deliberately not a valid run document. A valid one
        would be refused by the identity comparison anyway, so the test would
        pass either way and prove nothing.
        """
        root = tmp_path / "store"
        root.mkdir()
        (tmp_path / "outside.yaml").write_text(
            "this: is: not: a run", encoding="utf-8"
        )
        store = YamlRunStore(root)

        with pytest.raises(RunNotFound):
            store.get_run("../outside")
