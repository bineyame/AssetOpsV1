"""Read-only YAML adapter over the shipped Site template catalog.

The shipped catalog is git-tracked configuration that is read-only at runtime.
This module opens files for reading only: it has no write, create, rename,
delete, or temporary-file path, and `tools/check-architecture.ps1` fails the
build if a write-capable call appears in any module that names the shipped
catalog root.

Its other job is translation. `OSError`, `yaml.YAMLError`, and
`UnicodeDecodeError` are storage vocabulary and must not escape: every one is
converted into the port's error vocabulary before it crosses the seam, so no
caller above this layer can be written against a file-and-YAML store.

`get_template` resolves an identity by scanning parsed documents rather than by
building a path from the requested id. That is deliberate: an id that never
touches the filesystem cannot traverse it.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from assetops_backend.sites.models import SiteTemplate
from assetops_backend.sites.parsing import parse_site_template
from assetops_backend.sites.ports import (
    SiteTemplateConfigurationInvalid,
    SiteTemplateNotFound,
    SiteTemplateStoreUnavailable,
)

REPO_ROOT = Path(__file__).resolve().parents[4]

#: The shipped, read-only template configuration root. Separate from any Site
#: store: no Site ships in M1, and the writable user store a later slice adds
#: must not live here.
SHIPPED_SITE_TEMPLATE_ROOT = REPO_ROOT / "config" / "site-templates"

#: A shipped document larger than this is refused before it is loaded, so a
#: defective or hostile file cannot be expanded in memory first.
MAX_DOCUMENT_BYTES = 128 * 1024


class YamlSiteTemplateCatalog:
    """A `SiteTemplateCatalog` backed by read-only shipped YAML documents."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = SHIPPED_SITE_TEMPLATE_ROOT if root is None else root

    def list_templates(self) -> tuple[SiteTemplate, ...]:
        templates: list[SiteTemplate] = []
        seen: dict[str, str] = {}

        for path in self._document_paths():
            template = self._load(path)
            previous = seen.get(template.template_id)
            if previous is not None:
                raise SiteTemplateConfigurationInvalid(
                    f"Duplicate template_id {template.template_id!r} in "
                    f"{previous} and {path.name}"
                )
            seen[template.template_id] = path.name
            templates.append(template)

        return tuple(templates)

    def get_template(self, template_id: str) -> SiteTemplate:
        for template in self.list_templates():
            if template.template_id == template_id:
                return template

        raise SiteTemplateNotFound(
            f"No shipped site template with template_id {template_id!r}"
        )

    def _document_paths(self) -> list[Path]:
        try:
            if not self._root.is_dir():
                raise SiteTemplateStoreUnavailable(
                    f"Site template catalog directory is missing: {self._root}"
                )
            return sorted(
                path for path in self._root.iterdir() if path.suffix == ".yaml"
            )
        except OSError as error:
            raise SiteTemplateStoreUnavailable(
                f"Site template catalog could not be read: {self._root}"
            ) from error

    def _load(self, path: Path) -> SiteTemplate:
        try:
            size = path.stat().st_size
            if size > MAX_DOCUMENT_BYTES:
                raise SiteTemplateConfigurationInvalid(
                    f"Site template document {path.name} is {size} bytes, above "
                    f"the limit of {MAX_DOCUMENT_BYTES}"
                )
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise SiteTemplateConfigurationInvalid(
                f"Site template document {path.name} is not valid UTF-8"
            ) from error
        except OSError as error:
            raise SiteTemplateStoreUnavailable(
                f"Site template document could not be read: {path.name}"
            ) from error

        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise SiteTemplateConfigurationInvalid(
                f"Site template document {path.name} is not valid YAML"
            ) from error

        return parse_site_template(document, source=path.name)
