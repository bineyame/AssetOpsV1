"""Port, store, and write-path tests for Sites.

The seams under test are the configuration persistence port, the shipped
versus user-authored configuration split, and the untrusted-input write
boundary. The load-bearing assertions are structural: the port carries exactly
three methods and no mutator beyond create, a fake in-memory repository
satisfies the services with no adapter import, the two stores share one
identity space with no overlay, and a failed create leaves the store
byte-identical.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Sequence

import pytest
import yaml

from assetops_backend.sites.adapters.composite_site_repository import (
    CompositeSiteRepository,
)
from assetops_backend.sites.adapters.yaml_shipped_site_store import (
    SHIPPED_SITE_ROOT,
    ReadOnlyYamlSiteStore,
)
from assetops_backend.sites.adapters.yaml_user_site_store import (
    USER_SITE_STORE_ROOT,
    WritableYamlSiteStore,
)
from assetops_backend.sites.composition import build_site_repository
from assetops_backend.sites.identity import site_id_key
from assetops_backend.sites.models import SiteRecord, SiteTemplate
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteIdentityConflict,
    SiteNotFound,
    SiteRepository,
    SiteRepositoryError,
    SiteStoreUnavailable,
    SiteTemplateCatalog,
    SiteTemplateNotFound,
)
from assetops_backend.sites.service import SiteCreationService, SiteDirectoryService
from assetops_backend.sites.site_parsing import (
    CreateSiteRequest,
    parse_create_site_request,
    parse_site_document,
    render_site_document,
)
from test_site_parsing import valid_create_request, valid_site_document
from test_site_template_parsing import parse as parse_template
from test_site_template_parsing import valid_document as valid_template_document

SITES_PACKAGE_ROOT = Path(
    sys.modules["assetops_backend"].__file__ or ""
).resolve().parent / "sites"
REPO_ROOT = SITES_PACKAGE_ROOT.parents[2]


def site(**overrides: object) -> SiteRecord:
    document = valid_site_document()
    document.update(overrides)
    return parse_site_document(document, source="fixture")


def write_document(root: Path, record: SiteRecord, *, name: str | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / (name or f"{site_id_key(record.site_id)}.yaml")
    path.write_text(
        yaml.safe_dump(render_site_document(record), sort_keys=False), encoding="utf-8"
    )
    return path


def snapshot(root: Path) -> dict[str, bytes]:
    """Every file in a store, by name and bytes, so a write can be detected."""
    if not root.is_dir():
        return {}
    return {
        path.name: path.read_bytes() for path in sorted(root.iterdir()) if path.is_file()
    }


class FakeSiteRepository:
    """An in-memory `SiteRepository`. Imports nothing from `adapters/`.

    Its existence is the point: if the services could only be exercised
    through the YAML adapters, the port would not be a seam.
    """

    def __init__(self, records: Sequence[SiteRecord] = ()) -> None:
        self._records = list(records)

    def list_sites(self) -> Sequence[SiteRecord]:
        return tuple(self._records)

    def get_site(self, site_id: str) -> SiteRecord:
        for record in self._records:
            if site_id_key(record.site_id) == site_id_key(site_id):
                return record
        raise SiteNotFound(f"No site with site ID {site_id!r} is configured.")

    def create_site(self, record: SiteRecord) -> SiteRecord:
        for existing in self._records:
            if site_id_key(existing.site_id) == site_id_key(record.site_id):
                raise SiteIdentityConflict(
                    f"Site ID {record.site_id!r} is already in use."
                )
        self._records.append(record)
        return record


class FakeTemplateCatalog:
    def __init__(self, templates: Sequence[SiteTemplate]) -> None:
        self._templates = tuple(templates)

    def list_templates(self) -> Sequence[SiteTemplate]:
        return self._templates

    def get_template(self, template_id: str) -> SiteTemplate:
        for template in self._templates:
            if template.template_id == template_id:
                return template
        raise SiteTemplateNotFound(f"No template {template_id!r}")


def repository_over(tmp_path: Path) -> CompositeSiteRepository:
    return CompositeSiteRepository(
        shipped=ReadOnlyYamlSiteStore(tmp_path / "shipped"),
        user=WritableYamlSiteStore(tmp_path / "user"),
    )


class TestPortShape:
    def test_the_port_exposes_list_get_and_create_only(self) -> None:
        methods = set(SiteRepository.__protocol_attrs__)  # type: ignore[attr-defined]

        assert methods == {"list_sites", "get_site", "create_site"}

    def test_no_mutator_beyond_create_exists_anywhere_in_the_package(self) -> None:
        """Editing and removal are different capabilities that M1 does not have.

        Definitions are read from the syntax tree rather than the file text, so
        the rule is about what the package declares, not about which words its
        docstrings use to say a thing does not exist.
        """
        declared: set[str] = set()
        for path in SITES_PACKAGE_ROOT.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    declared.add(node.name)

        assert declared, "the definition scan must not be vacuous"
        assert "create_site" in declared, "the scan must see the one write there is"
        for banned in (
            "update_site",
            "delete_site",
            "remove_site",
            "archive_site",
            "rename_site",
            "duplicate_site",
            "save_site",
            "upsert_site",
            "put_site",
            "patch_site",
        ):
            assert banned not in declared, f"{banned} must not exist in M1"

    def test_the_two_ports_stay_separate(self) -> None:
        assert not issubclass(SiteRepository, SiteTemplateCatalog)
        assert not issubclass(SiteTemplateCatalog, SiteRepository)

        repository_methods = set(SiteRepository.__protocol_attrs__)  # type: ignore[attr-defined]
        catalog_methods = set(SiteTemplateCatalog.__protocol_attrs__)  # type: ignore[attr-defined]

        assert repository_methods & catalog_methods == set()

    def test_the_error_vocabulary_is_a_parallel_family(self) -> None:
        for error in (
            SiteNotFound,
            SiteIdentityConflict,
            SiteConfigurationInvalid,
            SiteStoreUnavailable,
        ):
            assert issubclass(error, SiteRepositoryError)

        from assetops_backend.sites.ports import SiteTemplateCatalogError

        assert not issubclass(SiteRepositoryError, SiteTemplateCatalogError)
        assert not issubclass(SiteTemplateCatalogError, SiteRepositoryError)

    def test_a_template_record_is_not_accepted_where_a_site_is_required(self) -> None:
        template = parse_template(valid_template_document())

        assert not isinstance(template, SiteRecord)
        assert SiteRecord.__mro__[1:] == (object,)
        assert not hasattr(template, "site_id")


class TestServicesOverFakes:
    def test_the_directory_service_is_satisfied_by_a_fake_repository(self) -> None:
        record = site()
        service = SiteDirectoryService(FakeSiteRepository([record]))

        assert service.list_sites() == (record,)
        assert service.get_site("mg-002") is record

    def test_the_directory_service_orders_the_listing_by_site_identity(self) -> None:
        first = site(site_id="AA-001")
        second = site(site_id="ZZ-001")
        service = SiteDirectoryService(FakeSiteRepository([second, first]))

        assert [s.site_id for s in service.list_sites()] == ["AA-001", "ZZ-001"]

    def test_the_creation_service_is_satisfied_by_fakes(self) -> None:
        template = parse_template(valid_template_document())
        repository = FakeSiteRepository()
        service = SiteCreationService(repository, FakeTemplateCatalog([template]))

        record = service.create_site_from_template(
            parse_create_site_request(
                {**valid_create_request(), "template_id": template.template_id}
            )
        )

        assert record.site_id == "MG-002"
        assert repository.list_sites() == (record,)

    def test_the_service_layer_imports_no_adapter(self) -> None:
        """The practical test of whether the port is a seam or a convention.

        Imports are read from the syntax tree, so a docstring that mentions
        the adapter layer does not trip the rule and an import cannot hide
        behind one.
        """
        tree = ast.parse((SITES_PACKAGE_ROOT / "service.py").read_text(encoding="utf-8"))

        modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)

        assert modules, "the import scan must not be vacuous"
        assert [module for module in modules if "adapters" in module] == []


class TestCreationServiceDecidesProvenance:
    def _service(self) -> tuple[SiteCreationService, FakeSiteRepository, SiteTemplate]:
        template = parse_template(valid_template_document())
        repository = FakeSiteRepository()
        return (
            SiteCreationService(repository, FakeTemplateCatalog([template])),
            repository,
            template,
        )

    def test_origin_mode_and_lifecycle_are_defaulted_by_the_service(self) -> None:
        service, _, template = self._service()

        record = service.create_site_from_template(
            parse_create_site_request(
                {**valid_create_request(), "template_id": template.template_id}
            )
        )

        assert record.origin == "USER"
        assert record.source.mode == "SIMULATED"
        assert record.lifecycle_status == "PLANNED"

    def test_template_identity_is_recorded_as_provenance_and_is_not_identity(
        self,
    ) -> None:
        service, _, template = self._service()

        record = service.create_site_from_template(
            parse_create_site_request(
                {**valid_create_request(), "template_id": template.template_id}
            )
        )

        assert record.template is not None
        assert record.template.template_id == template.template_id
        assert record.template.template_version == template.template_version
        assert record.site_id == "MG-002"
        assert record.site_id != template.template_id

    def test_the_foundation_seed_is_copied_from_the_template(self) -> None:
        service, _, template = self._service()

        record = service.create_site_from_template(
            parse_create_site_request(
                {**valid_create_request(), "template_id": template.template_id}
            )
        )

        assert record.site_type == template.foundation.site_type
        assert record.foundation.summary == template.foundation.summary
        assert [c.component_id for c in record.foundation.components] == [
            c.component_id for c in template.foundation.components
        ]
        assert record.foundation.version == 1

    def test_an_unknown_template_is_refused_and_nothing_is_created(self) -> None:
        service, repository, _ = self._service()

        with pytest.raises(SiteTemplateNotFound):
            service.create_site_from_template(
                parse_create_site_request(
                    {**valid_create_request(), "template_id": "absent-archetype"}
                )
            )

        assert repository.list_sites() == ()

    def test_the_created_site_carries_no_topology_devices_or_mappings(self) -> None:
        service, _, template = self._service()

        record = service.create_site_from_template(
            parse_create_site_request(
                {**valid_create_request(), "template_id": template.template_id}
            )
        )

        for field in ("topology", "devices", "signal_mappings", "control_assumptions"):
            assert not hasattr(record.foundation, field)


class TestShippedSiteStoreShipsEmpty:
    def test_the_shipped_site_store_holds_no_site_on_a_clean_checkout(self) -> None:
        """M1 ships zero Sites, so the Sites index has a genuine empty state."""
        assert SHIPPED_SITE_ROOT.is_dir(), "the shipped site store must exist"
        assert list(SHIPPED_SITE_ROOT.glob("*.yaml")) == []
        assert ReadOnlyYamlSiteStore().list_sites() == ()

    def test_the_composed_repository_lists_no_site_before_one_is_created(self) -> None:
        repository = build_site_repository()

        assert [
            record for record in repository.list_sites() if record.origin == "SHIPPED"
        ] == []

    def test_the_shipped_site_store_is_not_the_writable_store(self) -> None:
        assert USER_SITE_STORE_ROOT != SHIPPED_SITE_ROOT
        assert SHIPPED_SITE_ROOT not in USER_SITE_STORE_ROOT.parents
        assert (REPO_ROOT / "config") not in USER_SITE_STORE_ROOT.parents
        assert USER_SITE_STORE_ROOT not in SHIPPED_SITE_ROOT.parents

    def test_the_read_only_store_offers_no_write_method(self) -> None:
        store = ReadOnlyYamlSiteStore()

        for banned in ("create_site", "write", "save", "delete", "update"):
            assert not hasattr(store, banned)


class TestOneIdentitySpaceAcrossTwoStores:
    def test_the_same_site_id_in_both_stores_fails_loudly_at_load(
        self, tmp_path: Path
    ) -> None:
        """No overlay and no precedence: neither document is used."""
        record = site()
        write_document(tmp_path / "shipped", record)
        write_document(tmp_path / "user", record)

        repository = repository_over(tmp_path)

        with pytest.raises(SiteIdentityConflict, match="MG-002"):
            repository.list_sites()

    def test_a_case_variant_across_the_two_stores_also_fails_loudly(
        self, tmp_path: Path
    ) -> None:
        write_document(tmp_path / "shipped", site(site_id="MG-002"))
        write_document(tmp_path / "user", site(site_id="mg-002"), name="variant.yaml")

        repository = repository_over(tmp_path)

        with pytest.raises(SiteIdentityConflict):
            repository.list_sites()

    def test_disjoint_stores_merge_into_one_listing(self, tmp_path: Path) -> None:
        write_document(tmp_path / "shipped", site(site_id="CC-001", origin="SHIPPED"))
        write_document(tmp_path / "user", site(site_id="MG-002"))

        repository = repository_over(tmp_path)

        assert [record.site_id for record in repository.list_sites()] == [
            "CC-001",
            "MG-002",
        ]

    def test_origin_is_not_encoded_into_identity(self, tmp_path: Path) -> None:
        """A user `site_id` is not prefixed; origin is a field on the record."""
        write_document(tmp_path / "user", site(site_id="MG-002"))

        record = repository_over(tmp_path).get_site("MG-002")

        assert record.site_id == "MG-002"
        assert record.origin == "USER"

    def test_a_site_is_resolved_by_identity_without_regard_to_case(
        self, tmp_path: Path
    ) -> None:
        write_document(tmp_path / "user", site(site_id="MG-002"))

        repository = repository_over(tmp_path)

        assert repository.get_site("mg-002").site_id == "MG-002"
        assert repository.get_site("MG-002").site_id == "MG-002"

    def test_an_unknown_identity_is_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(SiteNotFound):
            repository_over(tmp_path).get_site("MG-404")

    @pytest.mark.parametrize("site_id", ["../escape", "/etc/passwd", "..", "CON"])
    def test_a_malformed_identity_never_reaches_the_filesystem(
        self, tmp_path: Path, site_id: str
    ) -> None:
        with pytest.raises(SiteConfigurationInvalid):
            repository_over(tmp_path).get_site(site_id)


class TestCreateIsCreateIfAbsent:
    def test_a_site_is_created_and_read_back(self, tmp_path: Path) -> None:
        repository = repository_over(tmp_path)
        record = site()

        assert repository.create_site(record) == record
        assert repository.list_sites() == (record,)

    def test_an_existing_identity_in_the_user_store_is_refused(
        self, tmp_path: Path
    ) -> None:
        repository = repository_over(tmp_path)
        repository.create_site(site())

        with pytest.raises(SiteIdentityConflict, match="MG-002"):
            repository.create_site(site(display_name="Another Site"))

    def test_an_existing_identity_in_the_shipped_store_is_refused(
        self, tmp_path: Path
    ) -> None:
        write_document(tmp_path / "shipped", site(origin="SHIPPED", template=None))
        repository = repository_over(tmp_path)

        with pytest.raises(SiteIdentityConflict, match="MG-002"):
            repository.create_site(site())

    @pytest.mark.parametrize("variant", ["mg-002", "Mg-002", "mG-002"])
    def test_a_case_variant_of_an_existing_identity_is_refused(
        self, tmp_path: Path, variant: str
    ) -> None:
        repository = repository_over(tmp_path)
        repository.create_site(site(site_id="MG-002"))

        with pytest.raises(SiteIdentityConflict):
            repository.create_site(site(site_id=variant))

    def test_a_case_variant_in_the_shipped_store_is_refused_too(
        self, tmp_path: Path
    ) -> None:
        write_document(
            tmp_path / "shipped", site(site_id="MG-002", origin="SHIPPED", template=None)
        )
        repository = repository_over(tmp_path)

        with pytest.raises(SiteIdentityConflict):
            repository.create_site(site(site_id="mg-002"))

    def test_a_refused_create_never_overwrites_the_existing_document(
        self, tmp_path: Path
    ) -> None:
        repository = repository_over(tmp_path)
        repository.create_site(site(display_name="Original"))
        before = snapshot(tmp_path / "user")

        with pytest.raises(SiteIdentityConflict):
            repository.create_site(site(site_id="mg-002", display_name="Replacement"))

        assert snapshot(tmp_path / "user") == before
        assert repository.get_site("MG-002").display_name == "Original"


class TestFailedCreatesLeaveTheStoreUnchanged:
    def test_a_conflicting_create_leaves_the_store_byte_identical(
        self, tmp_path: Path
    ) -> None:
        repository = repository_over(tmp_path)
        repository.create_site(site())
        before = snapshot(tmp_path / "user")

        with pytest.raises(SiteIdentityConflict):
            repository.create_site(site())

        assert snapshot(tmp_path / "user") == before

    def test_an_invalid_document_never_reaches_the_store(self, tmp_path: Path) -> None:
        """Validation happens before the write, not after it."""
        repository = repository_over(tmp_path)
        before = snapshot(tmp_path / "user")

        with pytest.raises(SiteConfigurationInvalid):
            parse_site_document(
                {**valid_site_document(), "site_id": "MG/002"}, source="hostile"
            )

        assert snapshot(tmp_path / "user") == before
        assert repository.list_sites() == ()

    def test_a_failure_after_the_staging_file_is_written_leaves_nothing_behind(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = repository_over(tmp_path)
        repository.create_site(site(site_id="CC-001"))
        before = snapshot(tmp_path / "user")

        def failing_replace(source: object, destination: object) -> None:
            raise OSError("the move failed")

        monkeypatch.setattr(os, "replace", failing_replace)

        with pytest.raises(SiteStoreUnavailable):
            repository.create_site(site(site_id="MG-002"))

        monkeypatch.undo()

        assert snapshot(tmp_path / "user") == before
        assert [path.name for path in (tmp_path / "user").iterdir()] == [
            "cc-001.yaml"
        ]
        assert [record.site_id for record in repository.list_sites()] == ["CC-001"]

    def test_the_document_written_is_the_document_that_was_validated(
        self, tmp_path: Path
    ) -> None:
        repository = repository_over(tmp_path)
        record = site()

        repository.create_site(record)

        stored = yaml.safe_load(
            (tmp_path / "user" / "mg-002.yaml").read_text(encoding="utf-8")
        )
        assert parse_site_document(stored, source="stored") == record


class TestPersistence:
    def test_a_created_site_survives_a_restart_against_the_same_store(
        self, tmp_path: Path
    ) -> None:
        repository_over(tmp_path).create_site(site())

        # A second repository over the same roots is what a restart looks like
        # to the store: nothing is carried over in memory.
        restarted = repository_over(tmp_path)

        assert [record.site_id for record in restarted.list_sites()] == ["MG-002"]
        assert restarted.get_site("MG-002").display_name == "Kalangala Mini-Grid"


class TestTemplateInstantiationIsACopy:
    def test_changing_the_template_document_does_not_change_a_created_site(
        self, tmp_path: Path
    ) -> None:
        """A template release must never rewrite a Foundation that exists."""
        from assetops_backend.sites.adapters.yaml_site_template_catalog import (
            YamlSiteTemplateCatalog,
        )

        catalog_root = tmp_path / "templates"
        catalog_root.mkdir()
        document = valid_template_document()
        (catalog_root / "archetype.yaml").write_text(
            yaml.safe_dump(document), encoding="utf-8"
        )

        repository = repository_over(tmp_path)
        service = SiteCreationService(repository, YamlSiteTemplateCatalog(catalog_root))
        request = CreateSiteRequest(
            template_id=document["template_id"],
            site_id="MG-002",
            display_name="Kalangala Mini-Grid",
            country="Uganda",
            locality="Kalangala",
            timezone="Africa/Kampala",
        )
        created = service.create_site_from_template(request)

        changed = valid_template_document()
        changed["template_version"] = 9
        changed["foundation"]["summary"] = "The template was rewritten later."
        changed["foundation"]["components"][0]["rating"] = {"value": 999, "unit": "kW"}
        (catalog_root / "archetype.yaml").write_text(
            yaml.safe_dump(changed), encoding="utf-8"
        )

        after_restart = repository_over(tmp_path).get_site("MG-002")

        assert after_restart == created
        assert after_restart.foundation.summary != changed["foundation"]["summary"]
        assert after_restart.template is not None
        assert after_restart.template.template_version == document["template_version"]
        rating = after_restart.foundation.components[0].rating
        assert rating is not None and rating.value == 100.0


class TestAdaptersTranslateStorageFailures:
    def test_a_missing_store_root_is_an_empty_store_not_a_failure(
        self, tmp_path: Path
    ) -> None:
        """An empty index is the first-run state; it is not an error."""
        assert repository_over(tmp_path).list_sites() == ()

    def test_unparseable_yaml_becomes_configuration_invalid(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "user").mkdir()
        (tmp_path / "user" / "broken.yaml").write_text("site_id: [", encoding="utf-8")

        with pytest.raises(SiteConfigurationInvalid, match="valid YAML"):
            repository_over(tmp_path).list_sites()

    def test_undecodable_bytes_become_configuration_invalid(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "user").mkdir()
        (tmp_path / "user" / "binary.yaml").write_bytes(b"\xff\xfe\x00site")

        with pytest.raises(SiteConfigurationInvalid, match="UTF-8"):
            repository_over(tmp_path).list_sites()

    def test_an_invalid_stored_document_becomes_configuration_invalid(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "user").mkdir()
        (tmp_path / "user" / "site.yaml").write_text(
            "site_id: MG-002\nextra: true\n", encoding="utf-8"
        )

        with pytest.raises(SiteConfigurationInvalid):
            repository_over(tmp_path).list_sites()

    def test_no_storage_exception_escapes_the_port(self, tmp_path: Path) -> None:
        """`OSError` and `yaml.YAMLError` are storage vocabulary, not domain."""
        (tmp_path / "user").mkdir()
        (tmp_path / "user" / "broken.yaml").write_text("site_id: [", encoding="utf-8")

        with pytest.raises(SiteRepositoryError):
            repository_over(tmp_path).list_sites()
