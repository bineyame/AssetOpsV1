"""The operator Sites API.

This is an operator capability, so it is mounted in both gate states and its
behavior is identical in both. The Simulator Lab gate covers simulator
surfaces and execution, never objects or stores: a Site created while the Lab
was enabled is product history and stays fully visible when the Lab is
switched off.

Read-only by construction. There is no `POST`, `PUT`, `PATCH`, or `DELETE`
here: creation lives behind the gate in the Lab's own router, and editing and
removal do not exist in M1. Two routes, both `GET`: the index, and one Site
addressed by `site_id`.

`site_id` is the only way a Site is addressed. Lookup compares identity
without regard to case, matching the port's case-insensitive uniqueness rule,
so a Site can never exist for the purposes of a conflict and be absent for the
purposes of a lookup. The response always carries the stored canonical
spelling rather than the spelling that was requested, so one Site can never
present as two.

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

from assetops_backend.sites.identity import SITE_ID_RULE, validate_site_id
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteIdentityConflict,
    SiteNotFound,
    SiteRepository,
    SiteStoreUnavailable,
)
from assetops_backend.sites.service import SiteDirectoryService

SITES_ROUTE = "/api/sites"
SITE_DETAIL_ROUTE = "/api/sites/{site_id}"

#: Refusal codes, in the same shape the gated create route uses: the message
#: is the product copy a screen renders, the code is what a client switches
#: on, so neither has to be parsed out of the other.
REFUSAL_SITE_NOT_FOUND = "SITE_NOT_FOUND"
REFUSAL_STORE_UNAVAILABLE = "SITE_STORE_UNAVAILABLE"


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


def site_detail(record: SiteRecord) -> dict[str, object]:
    """The Site Details shape: the index shape plus Foundation metadata.

    What is deliberately absent is the substance of the slice. There is no
    evidence-derived field, no source health, no evidence availability, no
    analytics, and no integration state: none of those has a truthful source
    for a configuration-only Site, and a field carrying a zero, an empty
    series, or a plausible-looking default would be a claim the product cannot
    back.

    The Foundation appears here only as its version and the start of its
    validity interval, which are metadata about the configuration document.
    Foundation *content* - the summary, the components, and later topology,
    devices, mappings, and control assumptions - is the read-only Site
    Configuration surface's shape and arrives with it, so no field for it is
    declared before a screen renders it.
    """
    return {
        **site_summary(record),
        "foundation": {
            "version": record.foundation.version,
            "valid_from": record.foundation.valid_from,
        },
    }


def _refusal(code: str, message: str) -> dict[str, object]:
    """A refusal a screen can render, rather than a stack trace."""
    return {"code": code, "message": message}


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

    @router.get(SITE_DETAIL_ROUTE)
    def read_site(site_id: str) -> dict[str, object]:
        """Return one configured Site by its identity.

        The requested identity is validated here rather than only inside the
        port, so that a malformed identity and an unreadable store cannot
        arrive as the same exception and be reported as the same thing. A
        malformed identity is answered as not found, because no Site can ever
        carry it, and the refusal repeats the identity rule so the answer is
        diagnosable without reading the store.

        An unknown Site is not-found, never an empty Site. A Site that is half
        rendered, or a page of blank fields under a heading, would state that
        the product knows a Site it does not know.
        """
        try:
            validate_site_id(site_id)
        except SiteConfigurationInvalid as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_SITE_NOT_FOUND,
                    f"No site with site ID {site_id!r} is configured, and no "
                    f"site could have that ID. {SITE_ID_RULE}",
                ),
            ) from error

        try:
            record = service.get_site(site_id)
        except SiteNotFound as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_SITE_NOT_FOUND,
                    f"No site with site ID {site_id!r} is configured. Site IDs "
                    "are compared without regard to case, so a different "
                    "capitalisation of a configured site would have been "
                    "found.",
                ),
            ) from error
        except (
            SiteIdentityConflict,
            SiteConfigurationInvalid,
            SiteStoreUnavailable,
        ) as error:
            # The same distinction the index makes: a store that could not be
            # read, or a document that is not valid configuration, is stated
            # as such. Neither degrades into "no such site", because "we could
            # not look" and "it is not there" are different facts.
            raise HTTPException(
                status_code=503,
                detail=_refusal(REFUSAL_STORE_UNAVAILABLE, str(error)),
            ) from error

        return site_detail(record)

    return router
