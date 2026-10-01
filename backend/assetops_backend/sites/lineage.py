"""Whether a Site's recorded template lineage is behind the shipped template.

Advisory provenance, computed on read and never stored on the Site (T025f,
`D-2026-10-01-run-binds-scenario-to-site`, Versioning). A Site records the
`(template_id, template_version)` it was copied from; a shipped template may
since have moved to a later version. Templates copy and never migrate an
existing Site, so this module only states the comparison. It rewrites nothing,
chooses nothing and blocks nothing.

`template_id` stays provenance only. It is compared against the shipped
catalog's identities to answer this one question; it never addresses a Site,
routes a request or names a file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from assetops_backend.sites.models import SiteTemplate, SiteTemplateProvenance

TemplateLineageState = Literal[
    # The Site was created from no template.
    "NO_TEMPLATE",
    # The recorded version is the shipped template's current version.
    "CURRENT",
    # The shipped template has moved past the recorded version.
    "BEHIND",
    # No shipped template carries the recorded `template_id` any more.
    "NOT_SHIPPED",
    # The recorded version is above every version this build ships. Not
    # "current": the record names a version this catalog never shipped.
    "UNRECOGNISED_VERSION",
]


@dataclass(frozen=True)
class TemplateLineage:
    """The comparison, with both versions so a reader can see the basis."""

    state: TemplateLineageState
    current_template_version: int | None


def assess_template_lineage(
    provenance: SiteTemplateProvenance | None,
    shipped: Sequence[SiteTemplate],
) -> TemplateLineage:
    """Compare one Site's recorded lineage against the shipped catalog."""
    if provenance is None:
        return TemplateLineage(state="NO_TEMPLATE", current_template_version=None)

    current = next(
        (
            template
            for template in shipped
            if template.template_id == provenance.template_id
        ),
        None,
    )
    if current is None:
        return TemplateLineage(state="NOT_SHIPPED", current_template_version=None)

    version = current.template_version
    if provenance.template_version == version:
        state: TemplateLineageState = "CURRENT"
    elif provenance.template_version < version:
        state = "BEHIND"
    else:
        state = "UNRECOGNISED_VERSION"
    return TemplateLineage(state=state, current_template_version=version)
