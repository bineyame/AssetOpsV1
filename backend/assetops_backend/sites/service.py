"""Service boundary over the Site configuration ports.

Each service receives its ports by injection and never learns where anything is
stored. A fake in-memory catalog and a fake in-memory repository satisfy them
with no import from `adapters/`, which is the practical test of whether a port
is a real seam or a naming convention.

It deliberately does not catch `yaml.YAMLError`, `OSError`, or any other
store-specific exception. If one reaches here, the adapter failed to translate
it and the seam has leaked; that is a seam failure to fix in the adapter, not
a defensive `except` to add here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from assetops_backend.sites.foundation_parsing import render_foundation_content
from assetops_backend.sites.models import FoundationContent, SiteRecord, SiteTemplate
from assetops_backend.sites.ports import SiteRepository, SiteTemplateCatalog
from assetops_backend.sites.site_parsing import CreateSiteRequest, parse_site_document


class SiteTemplateCatalogService:
    """Read-only template catalog use cases.

    Browsing templates is read-only. Instantiating one into a Site is a
    different use case with a different port, and it lives in
    `SiteCreationService` below rather than here, so that reading the catalog
    can never acquire a write path.
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


class SiteDirectoryService:
    """Read-only Site use cases, for the operator Sites index.

    This is an operator capability and is never gated: the Simulator Lab gate
    covers surfaces and execution, never objects or stores, so a Site created
    while the Lab was enabled is fully visible when it is disabled.

    It receives a `SiteRepository` by injection and never learns where Sites
    are stored. A fake in-memory repository satisfies it with no import from
    `adapters/`.
    """

    def __init__(self, repository: SiteRepository) -> None:
        self._repository = repository

    def list_sites(self) -> tuple[SiteRecord, ...]:
        """Return every configured Site, ordered by Site identity.

        Ordering is fixed here so the index does not depend on directory
        iteration order in whichever adapter is composed.
        """
        return tuple(sorted(self._repository.list_sites(), key=lambda s: s.site_id))

    def get_site(self, site_id: str) -> SiteRecord:
        """Return one Site by identity.

        Raises:
            SiteNotFound: no such `site_id`.
        """
        return self._repository.get_site(site_id)


class SiteCreationService:
    """Create a Site from a shipped template.

    The one write use case in M1. There is no update, no rename, no duplicate,
    no delete, and no Foundation version bump in place, because creation and
    editing are different capabilities with different risk and M1 has shipped
    only the first.

    What this service decides, and what it refuses to take from the caller, is
    the substance of the slice:

    - The template contributes a deep copy of its Foundation seed. The created
      Site never live-references the template, so a later template change can
      never reach back into a Site that already exists.
    - `origin`, `source.mode`, `lifecycle_status`, and template provenance are
      set here rather than supplied, so no caller can choose its own
      provenance. `USER` and `SIMULATED` are set independently and neither is
      derived from the other: in M1 they coincide because the Lab is the only
      creation path, which is a fact about the milestone and not a rule about
      the fields.
    - The fully materialized document is validated by the same strict parser
      that reads stored documents, with no lenient path, before anything
      touches the store.
    """

    #: The lifecycle status a newly configured Site starts in. A Site that has
    #: just been configured has not been commissioned and is not operating, so
    #: any other default would be a claim about the world.
    INITIAL_LIFECYCLE_STATUS = "PLANNED"

    #: The configuration origin of a Site a user authored. About the document
    #: and its store, never about the evidence.
    CONFIGURATION_ORIGIN = "USER"

    #: Where a Site created in the Simulator Lab gets its evidence from. This
    #: is provenance, never status, health, or an assessment.
    SOURCE_MODE = "SIMULATED"

    #: The Foundation version a created Site starts at. There is no in-place
    #: version bump in M1, so this stays 1 for the whole milestone.
    INITIAL_FOUNDATION_VERSION = 1

    def __init__(
        self,
        repository: SiteRepository,
        catalog: SiteTemplateCatalog,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._catalog = catalog
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def create_site_from_template(self, request: CreateSiteRequest) -> SiteRecord:
        """Materialize, validate, and persist one new Site.

        Raises:
            SiteTemplateNotFound: no shipped template with that `template_id`.
            SiteConfigurationInvalid: the materialized document is not a valid
                Site.
            SiteIdentityConflict: the `site_id` is already in use.
            SiteStoreUnavailable: a store could not be read or written.
        """
        template = self._catalog.get_template(request.template_id)

        document = {
            "site_id": request.site_id,
            "display_name": request.display_name,
            "site_type": template.foundation.site_type,
            "location": {
                "country": request.country,
                "locality": request.locality,
            },
            "timezone": request.timezone,
            "lifecycle_status": self.INITIAL_LIFECYCLE_STATUS,
            "origin": self.CONFIGURATION_ORIGIN,
            "source": {"mode": self.SOURCE_MODE},
            "template": {
                "template_id": template.template_id,
                "template_version": template.template_version,
            },
            "foundation": {
                "version": self.INITIAL_FOUNDATION_VERSION,
                "valid_from": self._now(),
                "summary": template.foundation.summary,
                # A deep copy. The created Site holds its own component values
                # and shares no structure with the template record.
                "components": [
                    {
                        "component_id": component.component_id,
                        "component_type": component.component_type,
                        "display_name": component.display_name,
                        "rating": (
                            None
                            if component.rating is None
                            else {
                                "value": component.rating.value,
                                "unit": component.rating.unit,
                            }
                        ),
                    }
                    for component in template.foundation.components
                ],
                # The rest of the Foundation seed, copied the same way: the
                # renderer builds fresh mappings and lists out of the
                # template's records, so the created Site shares no structure
                # with the template and a later template change cannot reach
                # back into it.
                #
                # A template that declares no topology seeds a Site that
                # declares none. The absence is copied as faithfully as the
                # content, because inventing an empty topology here would let
                # the Site's screen state something the template never said.
                **render_foundation_content(
                    FoundationContent(
                        topology=template.foundation.topology,
                        devices=template.foundation.devices,
                        signal_mappings=template.foundation.signal_mappings,
                        control_assumptions=template.foundation.control_assumptions,
                    )
                ),
            },
        }

        record = parse_site_document(document, source=f"the new site {request.site_id}")

        return self._repository.create_site(record)

    def _now(self) -> str:
        return (
            self._clock()
            .astimezone(timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )
