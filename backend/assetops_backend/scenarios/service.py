"""Service boundary over the scenario port.

Each service receives its ports by injection and never learns where anything is
stored. A fake in-memory repository satisfies them with no import from
`adapters/`, which is the practical test of whether a port is a real seam or a
naming convention.

Neither service catches `yaml.YAMLError`, `OSError`, or any other
store-specific exception. If one reaches here, the adapter failed to translate
it and the seam has leaked; that is a seam failure to fix in the adapter, not a
defensive `except` to add here.

`ScenarioDetailService` is the one place that holds both ports at once, and the
reason it does is the target-site rule. The parser validates the shape of a
scenario's target-site declaration and stops there; resolving a declared
`site_id` to a configured Site is a read against the Site store, so it belongs
above the parser and below the route. The result is a target-resolution state
the screen renders - never a parse failure, and never an exception that makes a
readable scenario unreadable because a Site is missing.
"""

from __future__ import annotations

from assetops_backend.scenarios.models import (
    ObservationSource,
    ObservationSourceResolution,
    ScenarioDefinition,
    ScenarioTargetResolution,
)
from assetops_backend.scenarios.ports import ScenarioDefinitionRepository
from assetops_backend.sites.models import FoundationDevice
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteIdentityConflict,
    SiteNotFound,
    SiteRepository,
    SiteStoreUnavailable,
)


class ScenarioCatalogService:
    """Read-only scenario catalog use cases.

    Ordering is fixed here so the catalog does not depend on directory
    iteration order in whichever adapter is composed.
    """

    def __init__(self, repository: ScenarioDefinitionRepository) -> None:
        self._repository = repository

    def list_scenarios(self) -> tuple[ScenarioDefinition, ...]:
        """Return every saved scenario, ordered by scenario identity."""
        return tuple(
            sorted(
                self._repository.list_scenarios(),
                key=lambda scenario: scenario.scenario_id,
            )
        )

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        """Return one scenario by its identity.

        Raises:
            ScenarioNotFound: no such `scenario_id`.
        """
        return self._repository.get_scenario(scenario_id)


class ScenarioDetailService:
    """One scenario, plus what its declared target Site resolves to.

    This service creates, renames, clones, and promotes nothing. It reads a
    scenario and it reads a Site, and the only thing it decides is which of the
    four target-resolution states is true.
    """

    def __init__(
        self,
        repository: ScenarioDefinitionRepository,
        sites: SiteRepository,
    ) -> None:
        self._repository = repository
        self._sites = sites

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        """Return one scenario by its identity.

        Raises:
            ScenarioNotFound: no such `scenario_id`.
        """
        return self._repository.get_scenario(scenario_id)

    def resolve_target_site(
        self, scenario: ScenarioDefinition
    ) -> ScenarioTargetResolution:
        """Resolve the declared target Site into a screen state.

        Four states, and they are four different facts rather than two shades
        of failure:

        - `NOT_APPLICABLE`: the scenario names an archetype rather than a Site,
          so there is no concrete Site to open and nothing went wrong.
        - `RESOLVED`: the declared `site_id` is configured. The Site's own
          canonical spelling and display name come back, so a link is built
          from what is configured rather than from what the document
          capitalised.
        - `NOT_CONFIGURED`: no Site with that identity is configured here. A
          shipped scenario on a fresh checkout is legitimately in this state.
        - `UNAVAILABLE`: the Site store could not be read, or holds something
          invalid, so nothing is known about whether that Site exists. This is
          never collapsed into `NOT_CONFIGURED`: "we could not look" and "it is
          not there" are different facts and a screen must not state the second
          when the first is true.
        """
        target = scenario.target_site

        if target.policy != "DECLARED_SITE" or target.site_id is None:
            return ScenarioTargetResolution(
                state="NOT_APPLICABLE",
                site_id=None,
                display_name=None,
                reason=(
                    "This scenario names the kind of site it needs rather than "
                    "a configured site, so there is no site to open."
                ),
            )

        declared = target.site_id

        try:
            site = self._sites.get_site(declared)
        except SiteNotFound:
            return ScenarioTargetResolution(
                state="NOT_CONFIGURED",
                site_id=None,
                display_name=None,
                reason=(
                    f"No site with site ID {declared} is configured, so the "
                    "site this scenario targets cannot be opened. Site IDs are "
                    "compared without regard to case."
                ),
            )
        except (
            SiteConfigurationInvalid,
            SiteIdentityConflict,
            SiteStoreUnavailable,
        ):
            return ScenarioTargetResolution(
                state="UNAVAILABLE",
                site_id=None,
                display_name=None,
                reason=(
                    "The site store could not be read, so whether the site "
                    f"{declared} is configured is unknown. This is a statement "
                    "about the store, not a statement that the site is absent."
                ),
            )

        return ScenarioTargetResolution(
            state="RESOLVED",
            site_id=site.site_id,
            display_name=site.display_name,
            reason=(
                f"The site {site.site_id} this scenario targets is configured."
            ),
        )

    def resolve_observation_sources(
        self, scenario: ScenarioDefinition
    ) -> tuple[ObservationSourceResolution, ...]:
        """Resolve each declared observation source against the target Site.

        The same split the target-site declaration uses, for the same reason:
        the parser validates that a device-signal source names a well-formed
        device and signal, and whether this installation configures them is a
        read against the Site store. A scenario whose device is not configured
        is still a readable scenario with an unresolved source; it is not a
        broken document and it does not take the catalog down.

        An operator record resolves to `NOT_APPLICABLE` and does so
        deliberately rather than by omission: a hand-recorded value has a real
        identity and no device, and a screen has to be able to say that
        instead of leaving a blank where a device would be.

        `cadence_statement` is produced here and is always about ownership. It
        never states a cadence, because a Foundation declares that a signal can
        report and declares no rate, and this service has nothing to derive one
        from - not the device's name, not its display text, and not the spacing
        between the entries that report through it.
        """
        target = scenario.target_site
        devices: tuple[FoundationDevice, ...] | None = None
        unavailable = False
        no_target = False

        if target.policy == "DECLARED_SITE" and target.site_id is not None:
            try:
                site = self._sites.get_site(target.site_id)
            except SiteNotFound:
                no_target = True
            except (
                SiteConfigurationInvalid,
                SiteIdentityConflict,
                SiteStoreUnavailable,
            ):
                unavailable = True
            else:
                devices = site.foundation.devices
        else:
            no_target = True

        return tuple(
            self._resolve_one_source(
                source,
                devices=devices,
                unavailable=unavailable,
                no_target=no_target,
            )
            for source in scenario.observation_sources
        )

    def _resolve_one_source(
        self,
        source: ObservationSource,
        *,
        devices: tuple[FoundationDevice, ...] | None,
        unavailable: bool,
        no_target: bool,
    ) -> ObservationSourceResolution:
        if source.source_kind != "DEVICE_SIGNAL":
            return ObservationSourceResolution(
                source_id=source.source_id,
                state="NOT_APPLICABLE",
                device_display_name=None,
                signal_display_name=None,
                reason=(
                    "This source is a person recording a value, so there is "
                    "no configured device or signal for it to resolve to."
                ),
                cadence_statement=(
                    "A person writing a value down reports at no rate, so "
                    "there is no cadence for anything to own."
                ),
            )

        cadence_statement = (
            "The site's foundation declares that this signal can report and "
            "declares no cadence. Nothing in this build infers one from the "
            "device's name, from what a screen shows, or from the spacing "
            "between the entries that report through it; a cadence arrives "
            "when a versioned observation profile declares one."
        )

        if unavailable:
            return ObservationSourceResolution(
                source_id=source.source_id,
                state="UNAVAILABLE",
                device_display_name=None,
                signal_display_name=None,
                reason=(
                    "The site store could not be read, so whether the device "
                    f"{source.device_id} is configured is unknown. This is a "
                    "statement about the store, not a statement that the "
                    "device is absent."
                ),
                cadence_statement=cadence_statement,
            )

        if no_target:
            return ObservationSourceResolution(
                source_id=source.source_id,
                state="NOT_CONFIGURED",
                device_display_name=None,
                signal_display_name=None,
                reason=(
                    "No configured site is resolved for this scenario, so the "
                    f"device {source.device_id} this source reports through "
                    "cannot be looked up."
                ),
                cadence_statement=cadence_statement,
            )

        if devices is None:
            return ObservationSourceResolution(
                source_id=source.source_id,
                state="NOT_CONFIGURED",
                device_display_name=None,
                signal_display_name=None,
                reason=(
                    "The site this scenario targets declares no devices at "
                    f"all, so it declares no {source.device_id} for this "
                    "source to report through."
                ),
                cadence_statement=cadence_statement,
            )

        for device in devices:
            if device.device_id != source.device_id:
                continue
            for signal in device.signals:
                if signal.signal_id != source.signal_id:
                    continue
                return ObservationSourceResolution(
                    source_id=source.source_id,
                    state="RESOLVED",
                    device_display_name=device.display_name,
                    signal_display_name=signal.display_name,
                    reason=(
                        f"The device {device.device_id} the site configures "
                        f"declares the signal {signal.signal_id} this source "
                        "reports through."
                    ),
                    cadence_statement=cadence_statement,
                )

        return ObservationSourceResolution(
            source_id=source.source_id,
            state="NOT_CONFIGURED",
            device_display_name=None,
            signal_display_name=None,
            reason=(
                f"No configured device {source.device_id} reporting "
                f"{source.signal_id} was found for the site this scenario "
                "targets, so this source names an identity this installation "
                "does not have."
            ),
            cadence_statement=cadence_statement,
        )
