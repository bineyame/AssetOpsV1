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

from assetops_backend.runs.adapters.yaml_run_documents import DOCUMENT_SUFFIX
from assetops_backend.runs.adapters.yaml_run_store import (
    RUN_STORE_ROOT,
    YamlRunStore,
)
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.ports import (
    RunConfigurationInvalid,
    RunIdentityConflict,
    RunNotFound,
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
