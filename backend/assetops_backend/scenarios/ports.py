"""The ScenarioDefinition persistence port, owned by the product domain.

Modelled on `assetops_backend/sites/ports.py`, and holding the same line for
the same reason. The port is the seam that makes storage replaceable, so its
signatures and its errors speak domain records only: no `Path`, no file handle,
no YAML text, no loader `dict`, and no store-specific exception may cross it.
An adapter that lets `yaml.YAMLError` or `OSError` escape has not implemented
the port, and a service layer that catches either has already lost the seam.

This is a parallel error family to the Site one, deliberately not a reuse of
it. A missing scenario and a missing Site are different facts about different
identity spaces, and a caller that caught `SiteNotFound` around a scenario
lookup would have confused the two. `ScenarioDefinitionRepository` is not a
subclass, mode, flag, or parameterization of `SiteRepository` and the two never
merge.

Read-only is structural here rather than a convention. T017 has no scenario
creation flow, so there is no `create_scenario` and no adapter has a write path
to implement. The writable user store exists as the other half of the identity
space and as the place later authoring will land; until that slice arrives,
nothing in the product can write a scenario.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from assetops_backend.scenarios.models import ScenarioDefinition


class ScenarioRepositoryError(Exception):
    """Base class for the scenario port's error vocabulary."""


class ScenarioNotFound(ScenarioRepositoryError):
    """No scenario with the requested `scenario_id` exists in either store."""


class ScenarioIdentityConflict(ScenarioRepositoryError):
    """A `scenario_id` resolves to two documents.

    Raised when the same identity is present twice within one store or once in
    each, including as a case variant. It fails loudly rather than resolving to
    one of them: there is no overlay and no precedence, because an identity
    that resolves to different content depending on store state cannot anchor
    the run history that later runs freeze a version against.
    """


class ScenarioConfigurationInvalid(ScenarioRepositoryError):
    """A scenario document is not valid configuration.

    Raised by the strict parser, by identity validation, and by adapters that
    meet undecodable or unparseable stored content. The message names what is
    wrong and what would be acceptable, because a user-authored scenario
    document will meet this text and a shipped-definition defect has to be
    diagnosable without reading the store.
    """


class ScenarioStoreUnavailable(ScenarioRepositoryError):
    """A scenario store could not be read.

    Distinct from `ScenarioConfigurationInvalid`: the content was never
    reached, so nothing is known about whether it is valid. A catalog must be
    able to say "the store could not be read" rather than "no scenario ships".
    """


@runtime_checkable
class ScenarioDefinitionRepository(Protocol):
    """Read access to saved ScenarioDefinitions, across both stores.

    Two methods, and no more. There is no create, update, delete, duplicate,
    publish, or approve, because T017 ships none of those capabilities and a
    port method for one would be a contract with nothing behind it. There is no
    query DSL, no pagination, and no caching method for the same reason.
    """

    def list_scenarios(self) -> Sequence[ScenarioDefinition]:
        """Return every saved scenario from every store.

        Raises:
            ScenarioIdentityConflict: one `scenario_id` resolves twice.
            ScenarioConfigurationInvalid: a stored document is invalid.
            ScenarioStoreUnavailable: a store could not be read.
        """
        ...

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        """Return one scenario by identity, compared without regard to case.

        Raises:
            ScenarioNotFound: no such `scenario_id`.
            ScenarioIdentityConflict: one `scenario_id` resolves twice.
            ScenarioConfigurationInvalid: `scenario_id` is malformed, or a
                stored document is invalid.
            ScenarioStoreUnavailable: a store could not be read.
        """
        ...
