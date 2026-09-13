"""Service boundary over the Site template catalog port.

The service receives a `SiteTemplateCatalog` by injection and never learns
where templates are stored. A fake in-memory catalog satisfies it without any
import from `adapters/`, which is the practical test of whether the port is a
real seam or a naming convention.

It deliberately does not catch `yaml.YAMLError`, `OSError`, or any other
store-specific exception. If one reaches here, the adapter failed to translate
it and the seam has leaked; that is a seam failure to fix in the adapter, not
a defensive `except` to add here.
"""

from __future__ import annotations

from assetops_backend.sites.models import SiteTemplate
from assetops_backend.sites.ports import SiteTemplateCatalog


class SiteTemplateCatalogService:
    """Read-only template catalog use cases.

    There is no create, instantiate, copy, edit, upload, import, or delete use
    case, because nothing in this slice can produce a Site.
    """

    def __init__(self, catalog: SiteTemplateCatalog) -> None:
        self._catalog = catalog

    def list_templates(self) -> tuple[SiteTemplate, ...]:
        """Return every shipped template, ordered by template identity.

        Ordering is fixed here so the listing does not depend on directory
        iteration order in whichever adapter is composed.
        """
        return tuple(
            sorted(self._catalog.list_templates(), key=lambda t: t.template_id)
        )

    def get_template(self, template_id: str) -> SiteTemplate:
        """Return one shipped template by its template identity.

        Raises:
            SiteTemplateNotFound: no such `template_id`.
        """
        return self._catalog.get_template(template_id)
