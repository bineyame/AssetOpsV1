"""The operator Sites API.

This is an operator capability, so it is mounted in both gate states and its
behavior is identical in both. The Simulator Lab gate covers simulator
surfaces and execution, never objects or stores: a Site created while the Lab
was enabled is product history and stays fully visible when the Lab is
switched off.

Read-only by construction. There is no `POST`, `PUT`, `PATCH`, or `DELETE`
here, and no per-Site path: creation lives behind the gate in the Lab's own
router, editing and removal do not exist in M1, and a Site addressed by
`site_id` is the next slice's surface rather than this one's.

The wire shape keeps the provenance-and-status concepts separate, because a
response shape is where they would most easily be collapsed. `origin` is about
the configuration document, `source.mode` is about where evidence comes from,
`lifecycle_status` is about the site's own life, and `template` is provenance
about which template the Foundation was copied from. There is no
`created_in_lab`, `is_simulator_site`, or equivalent field, because such a
field would record which shell created a Site, which nothing consumes.

No evidence-derived field appears at all. No last-data timestamp, no source
health, no evidence availability, no analytics: an evidence-derived field
arrives with the evidence that fills it.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteIdentityConflict,
    SiteRepository,
    SiteStoreUnavailable,
)
from assetops_backend.sites.service import SiteDirectoryService

SITES_ROUTE = "/api/sites"


def site_summary(record: SiteRecord) -> dict[str, object]:
    """The Sites index shape: identity, configuration, and provenance."""
    return {
        "site_id": record.site_id,
        "display_name": record.display_name,
        "site_type": record.site_type,
        "location": {
            "country": record.location.country,
            "locality": record.location.locality,
        },
        "timezone": record.timezone,
        "lifecycle_status": record.lifecycle_status,
        "origin": record.origin,
        "source": {"mode": record.source.mode},
        "template": (
            None
            if record.template is None
            else {
                "template_id": record.template.template_id,
                "template_version": record.template.template_version,
            }
        ),
    }


def build_sites_router(repository: SiteRepository) -> APIRouter:
    """Build the ungated operator Sites router around an injected port."""
    service = SiteDirectoryService(repository)
    router = APIRouter(tags=["sites"])

    @router.get(SITES_ROUTE)
    def list_sites() -> dict[str, object]:
        """List every configured Site.

        An empty list is a real answer: on first run no Site has been
        configured and the index says so, rather than showing a placeholder
        row or a fabricated count.
        """
        try:
            sites = service.list_sites()
        except (
            SiteIdentityConflict,
            SiteConfigurationInvalid,
            SiteStoreUnavailable,
        ) as error:
            # A store that cannot be read is stated as unavailable, never
            # degraded into "no sites are configured": those are different
            # facts and the index must not claim the first when the second is
            # true.
            raise HTTPException(status_code=503, detail=str(error)) from error

        return {"sites": [site_summary(site) for site in sites]}

    return router
