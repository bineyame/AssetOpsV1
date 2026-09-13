"""Port, service, adapter, and shipped-catalog tests.

The seam under test is the configuration persistence port. The load-bearing
assertions are structural: a fake in-memory catalog satisfies the service with
no adapter import, the port is not a Site repository in disguise, and storage
vocabulary never crosses the port.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Sequence

import pytest

from assetops_backend.sites.adapters.yaml_site_template_catalog import (
    SHIPPED_SITE_TEMPLATE_ROOT,
    YamlSiteTemplateCatalog,
)
from assetops_backend.sites.composition import build_site_template_catalog
from assetops_backend.sites.models import SiteTemplate
from assetops_backend.sites.ports import (
    SiteTemplateCatalog,
    SiteTemplateCatalogError,
    SiteTemplateConfigurationInvalid,
    SiteTemplateNotFound,
    SiteTemplateStoreUnavailable,
)
from assetops_backend.sites.service import SiteTemplateCatalogService
from test_site_template_parsing import parse, valid_document

SITES_PACKAGE_ROOT = Path(
    sys.modules["assetops_backend"].__file__ or ""
).resolve().parent / "sites"


class FakeSiteTemplateCatalog:
    """An in-memory catalog. Imports nothing from `adapters/`.

    Its existence is the point: if the service could only be exercised through
    the YAML adapter, the port would not be a seam.
    """

    def __init__(self, templates: Sequence[SiteTemplate]) -> None:
        self._templates = tuple(templates)

    def list_templates(self) -> Sequence[SiteTemplate]:
        return self._templates

    def get_template(self, template_id: str) -> SiteTemplate:
        for template in self._templates:
            if template.template_id == template_id:
                return template
        raise SiteTemplateNotFound(f"No template {template_id!r}")


class TestPortShape:
    def test_the_port_exposes_read_operations_only(self) -> None:
        methods = {
            name
            for name in SiteTemplateCatalog.__protocol_attrs__  # type: ignore[attr-defined]
        }

        assert methods == {"list_templates", "get_template"}

    def test_no_site_repository_or_write_adapter_ships_in_this_slice(self) -> None:
        """Creating a Site is a later slice; nothing here anticipates it.

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
        for banned in (
            "SiteRepository",
            "Site",
            "create_site",
            "create",
            "save",
            "write",
            "delete",
            "update",
        ):
            assert banned not in declared, f"{banned} must not exist in this slice"

    def test_the_template_record_is_not_a_kind_of_site(self) -> None:
        template = parse(valid_document())

        assert not isinstance(template, type) and isinstance(template, SiteTemplate)
        assert SiteTemplate.__mro__[1:] == (object,)
        for field in ("site_id", "lifecycle_status", "location", "timezone"):
            assert not hasattr(template, field)

    def test_the_error_vocabulary_covers_this_slice(self) -> None:
        for error in (
            SiteTemplateNotFound,
            SiteTemplateConfigurationInvalid,
            SiteTemplateStoreUnavailable,
        ):
            assert issubclass(error, SiteTemplateCatalogError)


class TestServiceOverAFakeCatalog:
    def test_the_service_is_satisfied_by_a_fake_catalog(self) -> None:
        template = parse(valid_document())
        service = SiteTemplateCatalogService(FakeSiteTemplateCatalog([template]))

        assert service.list_templates() == (template,)
        assert service.get_template("test-archetype") is template

    def test_the_service_orders_the_listing_by_template_identity(self) -> None:
        first = parse({**valid_document(), "template_id": "aaa-archetype"})
        second = parse({**valid_document(), "template_id": "zzz-archetype"})
        service = SiteTemplateCatalogService(FakeSiteTemplateCatalog([second, first]))

        assert [t.template_id for t in service.list_templates()] == [
            "aaa-archetype",
            "zzz-archetype",
        ]

    def test_an_unknown_template_id_raises_the_port_error(self) -> None:
        service = SiteTemplateCatalogService(FakeSiteTemplateCatalog([]))

        with pytest.raises(SiteTemplateNotFound):
            service.get_template("absent-archetype")


class TestShippedCatalog:
    def test_the_composition_root_serves_the_shipped_catalog(self) -> None:
        catalog = build_site_template_catalog()
        templates = SiteTemplateCatalogService(catalog).list_templates()

        assert [t.template_id for t in templates] == ["hybrid-mini-grid-100kw"]

    def test_the_shipped_hybrid_mini_grid_archetype_parses(self) -> None:
        template = build_site_template_catalog().get_template(
            "hybrid-mini-grid-100kw"
        )

        assert template.display_name == "Hybrid Mini-Grid (100 kW)"
        assert template.template_version >= 1
        assert template.foundation.site_type == "MINIGRID"
        assert len(template.foundation.components) > 0

    def test_the_shipped_catalog_root_holds_no_site_identity(self) -> None:
        """M1 ships zero Sites: no shipped document may declare Site identity.

        Loaded keys are inspected rather than raw text, so a comment that
        explains why a template has no `site_id` does not satisfy the check and
        a real `site_id` cannot hide behind one.
        """
        import yaml

        checked = 0
        for path in sorted(SHIPPED_SITE_TEMPLATE_ROOT.rglob("*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            checked += 1

            pending = [document]
            while pending:
                value = pending.pop()
                if isinstance(value, dict):
                    for field in ("site_id", "lifecycle_status", "location"):
                        assert field not in value, f"{path.name} declares {field}"
                    pending.extend(value.values())
                elif isinstance(value, list):
                    pending.extend(value)

        assert checked > 0, "the shipped catalog scan must not be vacuous"

    def test_the_shipped_catalog_root_holds_only_yaml_documents(self) -> None:
        suffixes = {
            path.suffix
            for path in SHIPPED_SITE_TEMPLATE_ROOT.rglob("*")
            if path.is_file()
        }

        assert suffixes == {".yaml"}


class TestAdapterTranslatesStorageFailures:
    """No `OSError`, `yaml.YAMLError`, or `UnicodeDecodeError` may escape."""

    def test_a_missing_catalog_directory_becomes_store_unavailable(
        self, tmp_path: Path
    ) -> None:
        catalog = YamlSiteTemplateCatalog(tmp_path / "absent")

        with pytest.raises(SiteTemplateStoreUnavailable):
            catalog.list_templates()

    def test_unparseable_yaml_becomes_configuration_invalid(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "broken.yaml").write_text("template_id: [", encoding="utf-8")
        catalog = YamlSiteTemplateCatalog(tmp_path)

        with pytest.raises(SiteTemplateConfigurationInvalid, match="valid YAML"):
            catalog.list_templates()

    def test_undecodable_bytes_become_configuration_invalid(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "binary.yaml").write_bytes(b"\xff\xfe\x00template")
        catalog = YamlSiteTemplateCatalog(tmp_path)

        with pytest.raises(SiteTemplateConfigurationInvalid, match="UTF-8"):
            catalog.list_templates()

    def test_an_invalid_document_becomes_configuration_invalid(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "site.yaml").write_text(
            "template_id: x\nsite_id: MG-001\n", encoding="utf-8"
        )
        catalog = YamlSiteTemplateCatalog(tmp_path)

        with pytest.raises(SiteTemplateConfigurationInvalid, match="site_id"):
            catalog.list_templates()

    def test_duplicate_template_identity_across_documents_is_refused(
        self, tmp_path: Path
    ) -> None:
        import yaml

        document = valid_document()
        for name in ("a.yaml", "b.yaml"):
            (tmp_path / name).write_text(yaml.safe_dump(document), encoding="utf-8")

        catalog = YamlSiteTemplateCatalog(tmp_path)

        with pytest.raises(SiteTemplateConfigurationInvalid, match="Duplicate"):
            catalog.list_templates()

    def test_an_unknown_template_id_never_touches_the_filesystem(
        self, tmp_path: Path
    ) -> None:
        """A traversal-shaped id is a miss, not a read outside the root."""
        import yaml

        (tmp_path / "one.yaml").write_text(
            yaml.safe_dump(valid_document()), encoding="utf-8"
        )
        catalog = YamlSiteTemplateCatalog(tmp_path)

        for template_id in ("../../etc/passwd", "/absolute", "absent"):
            with pytest.raises(SiteTemplateNotFound):
                catalog.get_template(template_id)
