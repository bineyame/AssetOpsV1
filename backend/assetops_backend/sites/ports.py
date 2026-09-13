"""Configuration persistence ports owned by the product domain.

The port is the seam that makes storage replaceable. Its signatures and its
errors speak domain records only: no `Path`, no file handle, no YAML text, no
loader `dict`, and no store-specific exception may cross it. An adapter that
lets `yaml.YAMLError` or `OSError` escape has not implemented the port, and a
service layer that catches either has already lost the seam.

Two ports live here and they stay separate. `SiteTemplateCatalog` is a
read-only catalog of shipped templates; `SiteRepository` reaches configured
Sites. Neither is a subclass, mode, flag, or parameterization of the other, and
they carry parallel error vocabularies rather than one shared family, because a
missing template and a missing Site are different facts about different
identity spaces.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from assetops_backend.sites.models import SiteRecord, SiteTemplate


class SiteTemplateCatalogError(Exception):
    """Base class for the port's error vocabulary."""


class SiteTemplateNotFound(SiteTemplateCatalogError):
    """No template with the requested `template_id` is in the catalog."""


class SiteTemplateConfigurationInvalid(SiteTemplateCatalogError):
    """A template document exists but is not valid configuration.

    Raised by the strict parser and by adapters that meet undecodable or
    unparseable stored content. The message names the offending field or
    document so a shipped-catalog defect is diagnosable without reading the
    store.
    """


class SiteTemplateStoreUnavailable(SiteTemplateCatalogError):
    """The catalog itself could not be read.

    Distinct from `SiteTemplateConfigurationInvalid`: the content was never
    reached, so nothing is known about whether it is valid.
    """


@runtime_checkable
class SiteTemplateCatalog(Protocol):
    """Read-only access to shipped Site configuration templates.

    Read-only is structural, not a convention: there is no create, update,
    delete, upload, or import method, so no caller can write through this port
    and no adapter has a write path to implement.
    """

    def list_templates(self) -> Sequence[SiteTemplate]:
        """Return every shipped template.

        Raises:
            SiteTemplateConfigurationInvalid: a shipped document is invalid.
            SiteTemplateStoreUnavailable: the catalog could not be read.
        """
        ...

    def get_template(self, template_id: str) -> SiteTemplate:
        """Return one shipped template by its template identity.

        Raises:
            SiteTemplateNotFound: no such `template_id`.
            SiteTemplateConfigurationInvalid: a shipped document is invalid.
            SiteTemplateStoreUnavailable: the catalog could not be read.
        """
        ...


# --- Site repository -------------------------------------------------------
#
# A parallel family, deliberately not a reuse of the template errors above.
# The two ports answer different questions and fail for different reasons, and
# a caller that catches `SiteTemplateNotFound` around a Site lookup has already
# confused the two identity spaces.


class SiteRepositoryError(Exception):
    """Base class for the Site port's error vocabulary."""


class SiteNotFound(SiteRepositoryError):
    """No Site with the requested `site_id` exists in either store."""


class SiteIdentityConflict(SiteRepositoryError):
    """A `site_id` is already in use, or resolves to two documents.

    Raised on create when the identity is already present in the shipped or
    the user store, including as a case variant, and on read when the same
    identity is present in both stores. The second case fails loudly rather
    than resolving to one of them: there is no overlay and no precedence,
    because an identity that resolves to different content depending on store
    state cannot anchor the history that later runs, envelopes, and evidence
    records are keyed on.
    """


class SiteConfigurationInvalid(SiteRepositoryError):
    """A Site document, or a proposed one, is not valid configuration.

    Raised by the strict parser, by identity validation, and by adapters that
    meet undecodable or unparseable stored content. The message names what is
    wrong and what would be acceptable, because for a user-authored document
    this text is product copy, not a diagnostic.
    """


class SiteStoreUnavailable(SiteRepositoryError):
    """A Site store could not be read or written.

    Distinct from `SiteConfigurationInvalid`: the content was never reached,
    so nothing is known about whether it is valid.
    """


@runtime_checkable
class SiteRepository(Protocol):
    """Access to configured Sites, across the shipped and user stores.

    Three methods, and no more. There is no `update_site` and no
    `delete_site`, because M1 has decided that configuration is fixed at
    creation and that removing a Site is a developer action on the store: a
    port method for either would be a capability with no product behind it.
    There is no query or filter DSL, no pagination, no transaction, and no
    caching method, because no slice needs one and a speculative one would
    become a contract before a caller had proved its shape.

    This is not a mode, flag, or parameterization of `SiteTemplateCatalog`,
    and the two protocols never merge.
    """

    def list_sites(self) -> Sequence[SiteRecord]:
        """Return every configured Site from every store.

        Raises:
            SiteIdentityConflict: one `site_id` resolves in both stores.
            SiteConfigurationInvalid: a stored document is invalid.
            SiteStoreUnavailable: a store could not be read.
        """
        ...

    def get_site(self, site_id: str) -> SiteRecord:
        """Return one Site by identity, compared without regard to case.

        Raises:
            SiteNotFound: no such `site_id`.
            SiteIdentityConflict: one `site_id` resolves in both stores.
            SiteConfigurationInvalid: `site_id` is malformed, or a stored
                document is invalid.
            SiteStoreUnavailable: a store could not be read.
        """
        ...

    def create_site(self, record: SiteRecord) -> SiteRecord:
        """Persist a new Site, and only ever a new one.

        Create-if-absent, never upsert. An existing `site_id` in either store,
        including a case variant of one, is refused and nothing is written.

        Raises:
            SiteIdentityConflict: the `site_id` is already in use.
            SiteConfigurationInvalid: the record is not a valid Site.
            SiteStoreUnavailable: the store could not be written.
        """
        ...
