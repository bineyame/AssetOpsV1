"""Composed scenario stores, over one globally unique `scenario_id` space.

Three things are proved here and they are separate claims:

- the port's contract holds over the composite - not found, identity conflict,
  configuration invalid, store unavailable, and nothing else;
- there is no overlay and no precedence between the shipped and user stores, so
  the same identity in both is refused rather than resolved;
- the adapters translate, so no `OSError`, `yaml.YAMLError`, or
  `UnicodeDecodeError` reaches a caller.

The last one is the seam. A port whose errors are domain errors on paper and
storage errors in practice is a naming convention, and the only way to tell the
difference is to break the store and watch what comes out.

These tests reach directly into `adapters/`, which the architecture guard bans
everywhere else. That exemption is deliberate and stated in the guard: a test
must be able to reach an adapter in order to prove what the adapter does.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from scenario_fixtures import scenario_document

from assetops_backend.scenarios.adapters.composite_scenario_repository import (
    CompositeScenarioRepository,
)
from assetops_backend.scenarios.adapters.yaml_scenario_documents import (
    MAX_DOCUMENT_BYTES,
)
from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import (
    SHIPPED_SCENARIO_ROOT,
    ReadOnlyYamlScenarioStore,
)
from assetops_backend.scenarios.adapters.yaml_user_scenario_store import (
    USER_SCENARIO_STORE_ROOT,
    UserYamlScenarioStore,
)
from assetops_backend.scenarios.composition import build_scenario_repository
from assetops_backend.scenarios.ports import (
    ScenarioConfigurationInvalid,
    ScenarioDefinitionRepository,
    ScenarioIdentityConflict,
    ScenarioNotFound,
    ScenarioStoreUnavailable,
)


def write_scenario(root: Path, name: str, **overrides: object) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    document = scenario_document()
    document.update(overrides)
    path = root / f"{name}.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def composite(shipped: Path, user: Path) -> CompositeScenarioRepository:
    return CompositeScenarioRepository(
        shipped=ReadOnlyYamlScenarioStore(shipped),
        user=UserYamlScenarioStore(user),
    )


class TestTheCompositeSatisfiesThePort:
    def test_the_composed_repository_is_a_scenario_repository(
        self, tmp_path: Path
    ) -> None:
        assert isinstance(
            composite(tmp_path / "shipped", tmp_path / "user"),
            ScenarioDefinitionRepository,
        )

    def test_the_real_composition_is_a_scenario_repository(self) -> None:
        assert isinstance(build_scenario_repository(), ScenarioDefinitionRepository)

    def test_a_missing_root_is_an_empty_store_and_not_a_failure(
        self, tmp_path: Path
    ) -> None:
        """The user store does not exist until somebody puts a document in it,
        and that is not a reason to refuse to render the catalog."""
        assert composite(tmp_path / "absent", tmp_path / "also-absent").list_scenarios() == ()

    def test_an_unknown_identity_is_not_found(self, tmp_path: Path) -> None:
        write_scenario(tmp_path / "shipped", "one", scenario_id="one")

        with pytest.raises(ScenarioNotFound):
            composite(tmp_path / "shipped", tmp_path / "user").get_scenario("two")

    def test_a_malformed_identity_is_refused_as_configuration(
        self, tmp_path: Path
    ) -> None:
        """A `scenario_id` never becomes a path, so a traversal attempt is
        refused by the identity rule before anything is located."""
        with pytest.raises(ScenarioConfigurationInvalid):
            composite(tmp_path / "shipped", tmp_path / "user").get_scenario(
                "../../config/scenarios/fuel-loss-event"
            )


class TestOneIdentitySpace:
    def test_identity_is_compared_without_regard_to_case(
        self, tmp_path: Path
    ) -> None:
        write_scenario(tmp_path / "shipped", "one", scenario_id="Example-Scenario")

        record = composite(tmp_path / "shipped", tmp_path / "user").get_scenario(
            "example-scenario"
        )

        # The stored spelling comes back, not the requested one: one scenario
        # must never be able to present as two.
        assert record.scenario_id == "Example-Scenario"

    def test_the_same_identity_in_both_stores_is_a_conflict(
        self, tmp_path: Path
    ) -> None:
        write_scenario(tmp_path / "shipped", "one", scenario_id="shared")
        write_scenario(tmp_path / "user", "one", scenario_id="shared")

        with pytest.raises(ScenarioIdentityConflict):
            composite(tmp_path / "shipped", tmp_path / "user").list_scenarios()

    def test_a_case_variant_across_the_stores_is_a_conflict(
        self, tmp_path: Path
    ) -> None:
        write_scenario(tmp_path / "shipped", "one", scenario_id="shared")
        write_scenario(tmp_path / "user", "one", scenario_id="SHARED")

        with pytest.raises(ScenarioIdentityConflict):
            composite(tmp_path / "shipped", tmp_path / "user").list_scenarios()

    def test_a_duplicate_within_one_store_is_a_conflict(
        self, tmp_path: Path
    ) -> None:
        write_scenario(tmp_path / "shipped", "first", scenario_id="shared")
        write_scenario(tmp_path / "shipped", "second", scenario_id="Shared")

        with pytest.raises(ScenarioIdentityConflict):
            composite(tmp_path / "shipped", tmp_path / "user").list_scenarios()

    def test_a_conflict_is_refused_on_read_as_well_as_on_list(
        self, tmp_path: Path
    ) -> None:
        """Reading the conflicting identity must not resolve to one of them.

        A read that quietly picked a store would be precedence, arrived at by
        accident rather than by decision.
        """
        write_scenario(tmp_path / "shipped", "one", scenario_id="shared")
        write_scenario(tmp_path / "user", "one", scenario_id="shared")

        with pytest.raises(ScenarioIdentityConflict):
            composite(tmp_path / "shipped", tmp_path / "user").get_scenario("shared")

    def test_there_is_no_overlay_and_no_precedence(self, tmp_path: Path) -> None:
        """Neither document is used, and neither store wins.

        The failure this prevents is subtle: with precedence, the same
        `scenario_id` would mean different content depending on whether a user
        file happened to be present, and a run that froze a version against it
        would have frozen nothing.
        """
        write_scenario(
            tmp_path / "shipped",
            "one",
            scenario_id="shared",
            display_name="The shipped one",
        )
        write_scenario(
            tmp_path / "user",
            "one",
            scenario_id="shared",
            display_name="The user one",
        )

        with pytest.raises(ScenarioIdentityConflict) as refusal:
            composite(tmp_path / "shipped", tmp_path / "user").list_scenarios()

        message = str(refusal.value)
        assert "no precedence" in message
        assert "neither document is used" in message

    def test_distinct_identities_from_both_stores_compose(
        self, tmp_path: Path
    ) -> None:
        write_scenario(tmp_path / "shipped", "one", scenario_id="from-shipped")
        write_scenario(tmp_path / "user", "two", scenario_id="from-user")

        records = composite(tmp_path / "shipped", tmp_path / "user").list_scenarios()

        assert [record.scenario_id for record in records] == [
            "from-shipped",
            "from-user",
        ]
        assert [record.origin for record in records] == ["SHIPPED", "USER"]

    def test_identity_is_read_from_the_document_and_not_the_file_name(
        self, tmp_path: Path
    ) -> None:
        """A file name is a storage detail. If identity came out of one, the
        disjointness rule would depend on how the host cases file names."""
        write_scenario(
            tmp_path / "shipped", "some-file-name", scenario_id="declared-identity"
        )

        records = composite(tmp_path / "shipped", tmp_path / "user").list_scenarios()

        assert [record.scenario_id for record in records] == ["declared-identity"]


class TestTheAdaptersTranslate:
    """No storage exception crosses the port."""

    def test_invalid_yaml_becomes_a_configuration_refusal(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "shipped"
        root.mkdir(parents=True)
        (root / "broken.yaml").write_text("scenario_id: [unclosed", encoding="utf-8")

        with pytest.raises(ScenarioConfigurationInvalid):
            composite(root, tmp_path / "user").list_scenarios()

    def test_undecodable_bytes_become_a_configuration_refusal(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "shipped"
        root.mkdir(parents=True)
        (root / "broken.yaml").write_bytes(b"\xff\xfe\x00scenario_id")

        with pytest.raises(ScenarioConfigurationInvalid):
            composite(root, tmp_path / "user").list_scenarios()

    def test_an_oversized_document_is_refused_before_it_is_loaded(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "shipped"
        root.mkdir(parents=True)
        (root / "huge.yaml").write_text(
            "# " + "x" * (MAX_DOCUMENT_BYTES + 1), encoding="utf-8"
        )

        with pytest.raises(ScenarioConfigurationInvalid, match="above the limit"):
            composite(root, tmp_path / "user").list_scenarios()

    def test_an_unreadable_store_is_unavailable_not_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """"The store could not be read" and "no scenario is saved" are
        different facts, and a catalog must not state the second for the first.
        """
        root = tmp_path / "shipped"
        root.mkdir(parents=True)

        def refuse(self: Path) -> object:
            raise OSError("the store is not readable")

        monkeypatch.setattr(Path, "iterdir", refuse)

        with pytest.raises(ScenarioStoreUnavailable):
            composite(root, tmp_path / "user").list_scenarios()

    def test_an_unreadable_document_is_unavailable_not_invalid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = tmp_path / "shipped"
        write_scenario(root, "one", scenario_id="one")

        def refuse(self: Path, *args: object, **kwargs: object) -> str:
            raise OSError("the document is not readable")

        monkeypatch.setattr(Path, "read_text", refuse)

        with pytest.raises(ScenarioStoreUnavailable):
            composite(root, tmp_path / "user").list_scenarios()


class TestTheShippedStore:
    def test_the_shipped_root_is_tracked_configuration(self) -> None:
        assert SHIPPED_SCENARIO_ROOT.is_dir()
        assert (SHIPPED_SCENARIO_ROOT / "fuel-loss-event.yaml").is_file()

    def test_the_user_store_lives_outside_every_shipped_root(self) -> None:
        assert USER_SCENARIO_STORE_ROOT != SHIPPED_SCENARIO_ROOT
        assert "config" not in USER_SCENARIO_STORE_ROOT.parts

    def test_neither_store_has_a_write_method(self) -> None:
        """T017 ships no scenario creation flow, and that is structural.

        Not a convention and not a disabled button: there is no method on
        either store, and no method on the port, that could write a scenario.
        """
        write_verbs = ("create", "save", "write", "update", "delete", "rename")

        for store in (ReadOnlyYamlScenarioStore, UserYamlScenarioStore):
            for name in dir(store):
                assert not name.startswith(write_verbs), (
                    f"{store.__name__}.{name} looks like a write path. The "
                    "slice that adds scenario authoring adds the write, its "
                    "atomicity, and its guard exemption together."
                )

    def test_the_shipped_fuel_loss_event_reads_through_the_real_composition(
        self,
    ) -> None:
        """The catalog shows a real record on a fresh checkout.

        This is the reason the shipped store does not ship empty: T017 has no
        create flow, so without a tracked definition the catalog would render
        its empty state and the slice would have nothing to inspect.
        """
        record = build_scenario_repository().get_scenario("fuel-loss-event")

        assert record.display_name == "Fuel Loss Event"
        assert record.origin == "SHIPPED"
        assert record.target_site.policy == "DECLARED_SITE"
        assert record.target_site.site_id == "MG-001"
        assert len(record.timeline) > 0
        assert len(record.private_expectations) > 0
