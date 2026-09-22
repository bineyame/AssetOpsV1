"""Gated Simulator Lab API surface (product side).

`create_app` builds this router only when `simulator_lab.enabled` is true. When
the flag is false the router is never mounted, so every
`/api/simulator-lab/*` path is genuinely unserved and returns 404 rather than
being served-but-empty or hidden behind UI navigation.

This module is one of the two allowlisted places in the tree that may spell a
simulator URL; `tools/check-architecture.ps1` fails the build if one appears
anywhere else. Lab-only paths therefore hang off `SIMULATOR_LAB_API_PREFIX`,
which keeps them behind the single existing chokepoint instead of introducing
a second one.

This module owns no simulated world, no private simulator truth, and no run
execution. Its Site Templates endpoints read shipped, read-only configuration
through the `SiteTemplateCatalog` port: they return template archetypes, never
Sites, and never operational values. No template endpoint writes anything, and
no route here edits, renames, duplicates, or deletes anything.

Two routes write, and both are Simulator Lab capabilities behind the gate and
under the Lab prefix, absent from the served route inventory when the flag is
false.

Creating a Site from a template is the first. What it creates is not a Lab
object: it is a normal product Site in the product store, carrying simulated
source mode as provenance, and it stays fully visible when the Lab is switched
off. There is no publish step and no promote step, because it was a product
object from the instant it existed.

Setting up a Draft run is the second, added by T019. It freezes the inputs a
later causal kernel will consume and persists the Draft; it executes nothing,
stages nothing, commits nothing, and produces no evidence, and there is no
route here that could. A request that cannot be frozen is refused and
allocates no `run_id`; one that freezes and cannot be executed by the selected
profile is persisted as `BLOCKED` with its reasons, which is the distinction
`runs/refusals.py` states and this module reports faithfully rather than
flattening into one failure.

The scenario routes T017 adds are reads, through the
`ScenarioDefinitionRepository` port. They serve saved `ScenarioDefinition`
records: what a simulated interval is intended to do, before any run exists.
No route here starts, stages, commits, ingests, or replays anything, and none
of them returns an assessment, a source-health result, a confidence, a
severity, or a Finding, because none of those has a truthful source.

The scenario detail route carries the private test-oracle expectations in a
section of its own, built by a payload function that never reads any public
field and vice versa. That is the public/private boundary: it is in the record
and in the payload builders, not in what a screen chooses to draw. The catalog
listing carries no expectation at all, and the operator Sites API - which is
mounted in both gate states and lives in another module - has no field one
could occupy.

Every path runs handler to service to port to adapter, with no shortcut to
storage. This module names no file, no path, and no serialization format.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.ports import (
    RunConfigurationInvalid,
    RunIdentityConflict,
    RunStoreUnavailable,
    SimulationRunRepository,
)
from assetops_backend.runs.profiles import (
    ModelProfile,
    PublicationProfile,
)
from assetops_backend.runs.provenance import frozen_inputs
from assetops_backend.runs.refusals import RunSetupRefused
from assetops_backend.runs.service import RunSetupService
from assetops_backend.scenarios.execution import (
    BOUND_CASES,
    CANONICAL_UNITS,
    DISPATCH_RULES,
    EXECUTION_CONTRACT_VERSION,
    canonical_quantity,
    initialization_inputs,
    reconcile_reported_observations,
    state_transition_inputs,
)
from assetops_backend.scenarios.identity import (
    SCENARIO_ID_RULE,
    validate_scenario_id,
)
from assetops_backend.scenarios.models import (
    ObservationSource,
    ObservationSourceResolution,
    PrivateExpectation,
    ScenarioDefinition,
    ScenarioParameter,
    ScenarioTargetResolution,
    TimelineEntry,
)
from assetops_backend.scenarios.ports import (
    ScenarioConfigurationInvalid,
    ScenarioDefinitionRepository,
    ScenarioIdentityConflict,
    ScenarioNotFound,
    ScenarioStoreUnavailable,
)
from assetops_backend.scenarios.service import (
    ScenarioCatalogService,
    ScenarioDetailService,
)
from assetops_backend.sites.models import SiteTemplate
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteIdentityConflict,
    SiteRepository,
    SiteStoreUnavailable,
    SiteTemplateCatalog,
    SiteTemplateConfigurationInvalid,
    SiteTemplateNotFound,
    SiteTemplateStoreUnavailable,
)
from assetops_backend.sites.service import (
    SiteCreationService,
    SiteTemplateCatalogService,
)
from assetops_backend.sites.site_parsing import parse_create_site_request
from assetops_backend.sites_api import site_summary

SIMULATOR_LAB_API_PREFIX = "/api/simulator-lab"

SITE_TEMPLATES_ROUTE = "/site-templates"
SITE_TEMPLATE_DETAIL_ROUTE = "/site-templates/{template_id}"
CREATE_SITE_ROUTE = "/sites"
SCENARIOS_ROUTE = "/scenarios"
SCENARIO_DETAIL_ROUTE = "/scenarios/{scenario_id}"
RUN_PROFILES_ROUTE = "/run-profiles"
CREATE_RUN_ROUTE = "/runs"

# Refusal codes. The message is the product copy a user reads; the code is what
# a client switches on, so neither has to be parsed out of the other.
REFUSAL_INVALID_REQUEST = "SITE_REQUEST_INVALID"
REFUSAL_SITE_ID_IN_USE = "SITE_ID_IN_USE"
REFUSAL_TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
REFUSAL_STORE_UNAVAILABLE = "SITE_STORE_UNAVAILABLE"
REFUSAL_SCENARIO_NOT_FOUND = "SCENARIO_NOT_FOUND"
REFUSAL_SCENARIO_STORE_UNAVAILABLE = "SCENARIO_STORE_UNAVAILABLE"
REFUSAL_RUN_STORE_UNAVAILABLE = "RUN_STORE_UNAVAILABLE"


def run_refusal_code(kind: str) -> str:
    """A run setup refusal code: the refusal kind, prefixed.

    The kinds are `RUN_SETUP_REFUSAL_KINDS` and each is a different fact with
    a different fix, so they arrive as different codes rather than as one code
    with a message a client would have to read. Derived rather than listed,
    because a kind added there with no code here would be reported as a
    refusal nobody could switch on.
    """
    return f"RUN_{kind}"


def _refusal(code: str, message: str) -> dict[str, object]:
    """A refusal a screen can render, rather than a stack trace."""
    return {"code": code, "message": message}


def _summarize(template: SiteTemplate) -> dict[str, object]:
    """Listing shape: template identity plus what kind of Site it would make.

    No `site_id`, no lifecycle status, no location, no timezone, no source
    mode: a template has none of those, so the wire shape has no field for
    them to leak into.
    """
    return {
        "template_id": template.template_id,
        "template_version": template.template_version,
        "display_name": template.display_name,
        "site_type": template.foundation.site_type,
        "summary": template.foundation.summary,
    }


def _detail(template: SiteTemplate) -> dict[str, object]:
    return {
        **_summarize(template),
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
    }


# --- Scenario payloads ------------------------------------------------------
#
# Two builders, and the split between them IS the public/private boundary.
#
# `scenario_public_summary` and `scenario_public_detail` read only the public
# fields of a `ScenarioDefinition`. Neither mentions `private_expectations`, so
# neither can leak one by omission, by a later field being added to a loop, or
# by a screen forgetting to filter. `scenario_private_expectations` reads only
# that field and nothing else.
#
# A test asserts that directly: a record whose expectations carry a sentinel
# renders a public payload the sentinel does not appear in, and the same
# sentinel does appear in the private payload, so the assertion cannot pass
# because the sentinel was never there.


def scenario_parameter(parameter: ScenarioParameter) -> dict[str, object]:
    """One authored parameter, with what an executor may do with it.

    `unit` is `null` for a text parameter rather than an empty string, because
    no unit and a blank unit are different facts and a screen renders them
    differently.

    `canonical` is present for every quantity and absent for text. It carries
    the value in canonical terms with its dimension, so a consumer converts
    without parsing the display text a screen shows - which is the difference
    between a contract and a convention about formatting.

    `ownership` is absent for a reported observation, and that absence is a
    fact rather than a gap: a reported value has no owner because it
    initializes nothing.
    """
    payload: dict[str, object] = {
        "parameter_id": parameter.parameter_id,
        "display_name": parameter.display_name,
        "value": parameter.value,
        "unit": parameter.unit,
        "execution_role": parameter.execution_role,
        "state_key": parameter.state_key,
        "execution_requirement": parameter.execution_requirement,
        "ownership": (
            None
            if parameter.ownership is None
            else {
                "owner": parameter.ownership.owner,
                "initializes": parameter.ownership.initializes,
            }
        ),
        "bounds": (
            None
            if parameter.bounds is None
            else {
                "state_key": parameter.bounds.state_key,
                "bound_kind": parameter.bounds.bound_kind,
            }
        ),
        "canonical": None,
    }

    if parameter.unit is not None and isinstance(parameter.value, float):
        value, unit, dimension = canonical_quantity(
            parameter.value, parameter.unit
        )
        payload["canonical"] = {
            "value": value,
            "unit": unit,
            "dimension": dimension,
        }

    return payload


def scenario_timeline_entry(entry: TimelineEntry) -> dict[str, object]:
    """One authored timeline row, in the order and placement it declares.

    There is no instant and no run duration here: an offset is measured from
    the start of a simulated interval nobody has chosen yet. There is no
    outcome, no observed value, and no status, because this row is what the
    simulated world will be told to do and not a report that it did it.

    `state_effect` and `observation` are mutually exclusive by construction in
    the record, so a client reading this payload can tell a cause from a
    reading without interpreting any wording.
    """
    return {
        "event_id": entry.event_id,
        "sequence": entry.sequence,
        "offset_minutes": entry.offset_minutes,
        "entry_kind": entry.entry_kind,
        "category": entry.category,
        "description": entry.description,
        "execution_role": entry.execution_role,
        "state_key": entry.state_key,
        "execution_requirement": entry.execution_requirement,
        "timing": {
            "shape": entry.timing.shape,
            "duration_minutes": entry.timing.duration_minutes,
        },
        "state_effect": (
            None
            if entry.state_effect is None
            else {
                "direction": entry.state_effect.direction,
                "quantity_parameter_id": (
                    entry.state_effect.quantity_parameter_id
                ),
                "rate_parameter_id": entry.state_effect.rate_parameter_id,
            }
        ),
        "observation": (
            None
            if entry.observation is None
            else {
                "source_id": entry.observation.source_id,
                "reported_parameter_id": (
                    entry.observation.reported_parameter_id
                ),
            }
        ),
        "parameters": [
            scenario_parameter(parameter) for parameter in entry.parameters
        ],
    }


def scenario_observation_source(source: ObservationSource) -> dict[str, object]:
    """One declared source, as the document declares it.

    `cadence_ownership` is a statement about who owns the reporting rate and
    never a rate. There is no field here a cadence could occupy, which is what
    keeps "nothing infers a cadence" from depending on nobody trying.
    """
    return {
        "source_id": source.source_id,
        "source_kind": source.source_kind,
        "device_id": source.device_id,
        "signal_id": source.signal_id,
        "cadence_ownership": source.cadence_ownership,
        "description": source.description,
    }


def scenario_observation_source_resolution(
    resolution: ObservationSourceResolution,
) -> dict[str, object]:
    """What one declared source resolved to on this installation."""
    return {
        "source_id": resolution.source_id,
        "state": resolution.state,
        "device_display_name": resolution.device_display_name,
        "signal_display_name": resolution.signal_display_name,
        "reason": resolution.reason,
        "cadence_statement": resolution.cadence_statement,
    }


def scenario_execution_contract(
    scenario: ScenarioDefinition,
) -> dict[str, object]:
    """The executable meaning of this scenario, for a later run setup.

    Three kinds of thing, deliberately in one section so a reader and a client
    meet them together:

    - the semantics every scenario shares - canonical units, dispatch rules,
      and bound policies - which are versioned simulator rules rather than
      authored content;
    - what this scenario's own inputs initialize and transition, which is the
      whole of the surface an executor would consume;
    - whether each reported observation is reached by the causal inputs the
      same scenario declares.

    The last one is contract arithmetic, not execution. It states a
    disagreement where one exists instead of letting a reported number quietly
    stand in for private world state, and it changes nothing.
    """
    return {
        "contract_version": EXECUTION_CONTRACT_VERSION,
        "canonical_units": [
            {
                "unit": unit,
                "canonical_unit": canonical.canonical_unit,
                "dimension": canonical.dimension,
            }
            for unit, canonical in sorted(CANONICAL_UNITS.items())
        ],
        "dispatch_rules": [
            {
                "rule_id": rule.rule_id,
                "display_name": rule.display_name,
                "statement": rule.statement,
            }
            for rule in DISPATCH_RULES
        ],
        "bound_cases": [
            {
                "case_id": case.case_id,
                "display_name": case.display_name,
                "policy": case.policy,
                "statement": case.statement,
            }
            for case in BOUND_CASES
        ],
        "initialization_inputs": [
            {
                "parameter_id": item.parameter_id,
                "display_name": item.display_name,
                "state_key": item.state_key,
                "owner": item.owner,
                "value": item.value,
                "unit": item.unit,
                "canonical_value": item.canonical_value,
                "canonical_unit": item.canonical_unit,
            }
            for item in initialization_inputs(scenario)
        ],
        "state_transition_inputs": [
            {
                "event_id": item.event_id,
                "state_key": item.state_key,
                "direction": item.direction,
                "parameter_id": item.parameter_id,
                "applied_value": item.applied_value,
                "applied_unit": item.applied_unit,
                "starts_at_offset": item.starts_at_offset,
                "complete_at_offset": item.complete_at_offset,
            }
            for item in state_transition_inputs(scenario)
        ],
        "observation_reconciliation": [
            {
                "event_id": item.event_id,
                "source_id": item.source_id,
                "parameter_id": item.parameter_id,
                "state_key": item.state_key,
                "offset_minutes": item.offset_minutes,
                "reported_value": item.reported_value,
                "declared_value": item.declared_value,
                "difference": item.difference,
                "unit": item.unit,
                "state": item.state,
                "reason": item.reason,
                "accounted_by": list(item.accounted_by),
            }
            for item in reconcile_reported_observations(scenario)
        ],
    }


def scenario_public_summary(scenario: ScenarioDefinition) -> dict[str, object]:
    """Catalog shape: scenario identity, version identity, and target.

    No timeline, no parameters, and no expectation. A catalog row says which
    scenarios are saved; reading one is the detail route's job.

    `target_site` is the declaration the document makes, not a resolution. The
    catalog does not read the Site store, so it states which site a scenario
    asks for without claiming that site is configured.
    """
    return {
        "scenario_id": scenario.scenario_id,
        "display_name": scenario.display_name,
        "purpose": scenario.purpose,
        "origin": scenario.origin,
        "version": {
            "scenario_version": scenario.version.scenario_version,
            "version_valid_from": scenario.version.version_valid_from,
            "supersedes": scenario.version.supersedes,
        },
        "target_site": {
            "policy": scenario.target_site.policy,
            "site_id": scenario.target_site.site_id,
            "template_id": scenario.target_site.template_id,
            "requirement": scenario.target_site.requirement,
        },
    }


def scenario_public_detail(scenario: ScenarioDefinition) -> dict[str, object]:
    """The catalog shape plus the public timeline, parameters and contract."""
    return {
        **scenario_public_summary(scenario),
        "timeline": [
            scenario_timeline_entry(entry) for entry in scenario.timeline
        ],
        "public_parameters": [
            scenario_parameter(parameter)
            for parameter in scenario.public_parameters
        ],
        "observation_sources": [
            scenario_observation_source(source)
            for source in scenario.observation_sources
        ],
        "execution_contract": scenario_execution_contract(scenario),
    }


def scenario_private_expectations(
    scenario: ScenarioDefinition,
) -> list[dict[str, object]]:
    """The private test-oracle expectations, and nothing else.

    Served on the gated Simulator Lab detail route only. These are developer
    metadata about what a future test should be able to conclude; they are not
    evidence, not provenance, and not a product claim, and no operator payload,
    export, or analytic has a field they could occupy.
    """
    return [
        {
            "expectation_id": expectation.expectation_id,
            "display_name": expectation.display_name,
            "oracle_kind": expectation.oracle_kind,
            "statement": expectation.statement,
        }
        for expectation in scenario.private_expectations
    ]


def scenario_target_resolution(
    resolution: ScenarioTargetResolution,
) -> dict[str, object]:
    """What the declared target Site resolved to, as a screen state.

    Beside the scenario rather than inside it, because it is not scenario
    content: it is what this installation's Site store answered when asked
    about the Site the scenario declares. The same scenario resolves
    differently on two machines and the document does not change.
    """
    return {
        "state": resolution.state,
        "site_id": resolution.site_id,
        "display_name": resolution.display_name,
        "reason": resolution.reason,
    }


# --- Run payloads -----------------------------------------------------------
#
# A Draft run leaves this module in two shapes at once, and they are two
# readings of one record rather than two records. `deterministic_identity` is
# the structured frozen identity a later inventory and a later kernel consume;
# `frozen_inputs` is the same identity as one row per value, each naming who
# answered for it, which is what the setup summary renders. Both are derived
# from the record here, so neither can drift from the other.


def run_profile_summary(profile: ModelProfile) -> dict[str, object]:
    """One versioned model profile, and the states it can model."""
    return {
        "model_profile_id": profile.model_profile_id,
        "model_profile_version": profile.model_profile_version,
        "display_name": profile.display_name,
        "statement": profile.statement,
        "supported_states": [
            {
                "state_key": state.state_key,
                "supported_roles": sorted(state.supported_roles),
                "statement": state.statement,
            }
            for state in profile.supported_states
        ],
    }


def publication_profile_summary(
    profile: PublicationProfile,
) -> dict[str, object]:
    """One versioned publication profile, and what it resolves.

    A value it does not declare is `null` rather than absent or defaulted. A
    reader has to be able to see that the cadence, the simulator source or the
    gateway is undeclared, because that is what blocks a run.
    """
    return {
        "publication_profile_id": profile.publication_profile_id,
        "publication_profile_version": profile.publication_profile_version,
        "display_name": profile.display_name,
        "statement": profile.statement,
        "device_signal_cadence_minutes": profile.device_signal_cadence_minutes,
        "simulator_source_id": profile.simulator_source_id,
        "gateway_id": profile.gateway_id,
    }


def run_summary(record: SimulationRun) -> dict[str, object]:
    """One Draft run: its identity, what it froze, and why it may not run.

    There is no progress, no elapsed time, no state, no staged envelope, no
    commit eligibility and no evidence here, because none of those exists and
    the record has no field one could arrive in.
    """
    identity = record.deterministic_identity
    return {
        "run_id": record.run_id,
        "lifecycle_status": record.lifecycle_status,
        "execution_status": record.execution_status,
        "created_at": record.created_at,
        "site_id": identity.site.site_id,
        "scenario_id": identity.scenario.scenario_id,
        "scenario_version": identity.scenario.scenario_version,
        "deterministic_identity": {
            "site": {
                "site_id": identity.site.site_id,
                "foundation_version": identity.site.foundation_version,
                "foundation_valid_from": identity.site.foundation_valid_from,
                "site_type": identity.site.site_type,
                "timezone": identity.site.timezone,
            },
            "scenario": {
                "scenario_id": identity.scenario.scenario_id,
                "scenario_version": identity.scenario.scenario_version,
                "resolved_parameters": [
                    {
                        "parameter_id": parameter.parameter_id,
                        "value": parameter.value,
                        "unit": parameter.unit,
                        "answered_by": parameter.answered_by,
                    }
                    for parameter in identity.scenario.resolved_parameters
                ],
            },
            "interval": {
                "start_time": identity.interval.start_time,
                "end_time": identity.interval.end_time,
                "duration_minutes": identity.interval.duration_minutes,
                "timestep_minutes": identity.interval.timestep_minutes,
            },
            "seed": identity.seed,
            "profiles": {
                "model_profile_id": identity.profiles.model_profile_id,
                "model_profile_version": identity.profiles.model_profile_version,
                "publication_profile_id": (
                    identity.profiles.publication_profile_id
                ),
                "publication_profile_version": (
                    identity.profiles.publication_profile_version
                ),
                "execution_contract_version": (
                    identity.profiles.execution_contract_version
                ),
            },
            "initialization_inputs": [
                {
                    "state_key": item.state_key,
                    "parameter_id": item.parameter_id,
                    "value": item.value,
                    "unit": item.unit,
                    "canonical_value": item.canonical_value,
                    "canonical_unit": item.canonical_unit,
                    "answered_by": item.answered_by,
                    "answered_by_detail": item.answered_by_detail,
                }
                for item in identity.initialization_inputs
            ],
            "observation_bindings": [
                {
                    "source_id": item.source_id,
                    "source_kind": item.source_kind,
                    "device_id": item.device_id,
                    "signal_id": item.signal_id,
                    "cadence_ownership": item.cadence_ownership,
                    "cadence_minutes": item.cadence_minutes,
                    "cadence_resolution": item.cadence_resolution,
                }
                for item in identity.observation_bindings
            ],
            "publication": {
                "simulator_source_id": identity.publication.simulator_source_id,
                "gateway_id": identity.publication.gateway_id,
            },
            "signal_mappings": [
                {
                    "mapping_id": item.mapping_id,
                    "device_id": item.device_id,
                    "signal_id": item.signal_id,
                    "component_id": item.component_id,
                }
                for item in identity.signal_mappings
            ],
            "intervention_history": list(identity.intervention_history),
        },
        "frozen_inputs": [
            {
                "identity_field": row.identity_field,
                "field": row.field,
                "value": row.value,
                "answered_by": row.answered_by,
                "answered_by_detail": row.answered_by_detail,
            }
            for row in frozen_inputs(identity)
        ],
        "blocking_reasons": [
            {
                "kind": reason.kind,
                "subject": reason.subject,
                "statement": reason.statement,
            }
            for reason in record.blocking_reasons
        ],
        "unsupported_optional_inputs": [
            {
                "state_key": item.state_key,
                "execution_role": item.execution_role,
                "statement": item.statement,
            }
            for item in record.unsupported_optional_inputs
        ],
    }


def build_simulator_lab_router(
    catalog: SiteTemplateCatalog,
    repository: SiteRepository,
    scenarios: ScenarioDefinitionRepository,
    runs: SimulationRunRepository,
    model_profiles: tuple[ModelProfile, ...],
    publication_profiles: tuple[PublicationProfile, ...],
) -> APIRouter:
    """Build the gated router around the injected ports.

    All three arrive as ports. This module never learns whether templates,
    Sites, or scenarios are files, rows, or objects, and it never imports an
    adapter.

    The Site repository reaches the scenario detail service as well as the
    create service, and that is the only place the two domains meet: a scenario
    declares which Site it needs, and resolving that declaration is a read
    against the Site port. Nothing flows the other way.
    """
    service = SiteTemplateCatalogService(catalog)
    creation = SiteCreationService(repository, catalog)
    scenario_catalog = ScenarioCatalogService(scenarios)
    scenario_detail = ScenarioDetailService(scenarios, repository)
    run_setup = RunSetupService(
        runs,
        repository,
        scenarios,
        model_profiles=model_profiles,
        publication_profiles=publication_profiles,
    )
    router = APIRouter(prefix=SIMULATOR_LAB_API_PREFIX, tags=["simulator-lab"])

    @router.get("/status")
    def read_simulator_lab_status() -> dict[str, object]:
        """Report that the Simulator Lab surface is served in this build.

        This is a statement about the gate, not about any Site, device,
        source, or simulator run. No run exists, so none can be started,
        inspected, rerun, or compared against simulator truth.
        """
        return {
            "simulator_lab_enabled": True,
            "run_execution": "not_implemented",
            "truth_overlays": "not_implemented",
        }

    @router.get(SITE_TEMPLATES_ROUTE)
    def list_site_templates() -> dict[str, object]:
        """List the shipped Site configuration templates."""
        try:
            templates = service.list_templates()
        except (
            SiteTemplateConfigurationInvalid,
            SiteTemplateStoreUnavailable,
        ) as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

        return {"templates": [_summarize(template) for template in templates]}

    @router.get(SITE_TEMPLATE_DETAIL_ROUTE)
    def read_site_template(template_id: str) -> dict[str, object]:
        """Return the Foundation content one shipped template would produce."""
        try:
            template = service.get_template(template_id)
        except SiteTemplateNotFound as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except (
            SiteTemplateConfigurationInvalid,
            SiteTemplateStoreUnavailable,
        ) as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

        return _detail(template)

    @router.post(CREATE_SITE_ROUTE, status_code=201)
    def create_site(request: Any = Body(default=None)) -> dict[str, object]:
        """Create one Site from a shipped template.

        The request body is parsed by the domain's own strict parser rather
        than by a framework model, so that a refusal is product copy naming
        what is wrong and what would be acceptable, instead of a validation
        dump. Nothing is written unless the fully materialized document
        passes the same parser that reads stored documents.
        """
        try:
            parsed = parse_create_site_request(request)
        except SiteConfigurationInvalid as error:
            raise HTTPException(
                status_code=422,
                detail=_refusal(REFUSAL_INVALID_REQUEST, str(error)),
            ) from error

        try:
            record = creation.create_site_from_template(parsed)
        except SiteTemplateNotFound as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_TEMPLATE_NOT_FOUND,
                    f"No shipped site template with template ID "
                    f"{parsed.template_id!r} exists, so no site was created. "
                    "Choose a template from the shipped catalog.",
                ),
            ) from error
        except SiteIdentityConflict as error:
            raise HTTPException(
                status_code=409,
                detail=_refusal(
                    REFUSAL_SITE_ID_IN_USE,
                    f"{error} Site IDs are unique across every site store "
                    "and are compared without regard to case, so the same ID "
                    "in a different capitalisation is the same site. Nothing "
                    "was written. Choose a different site ID.",
                ),
            ) from error
        except SiteConfigurationInvalid as error:
            raise HTTPException(
                status_code=422,
                detail=_refusal(REFUSAL_INVALID_REQUEST, str(error)),
            ) from error
        except (SiteStoreUnavailable, SiteTemplateStoreUnavailable) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(
                    REFUSAL_STORE_UNAVAILABLE,
                    f"{error} Nothing was written.",
                ),
            ) from error

        return site_summary(record)

    @router.get(SCENARIOS_ROUTE)
    def list_scenarios() -> dict[str, object]:
        """List every saved ScenarioDefinition.

        A store that cannot be read, and a duplicate identity across the two
        stores, are both stated as unavailable rather than degraded into "no
        scenarios are saved". Those are different facts, and a catalog must not
        claim the second when the first is true.
        """
        try:
            saved = scenario_catalog.list_scenarios()
        except (
            ScenarioIdentityConflict,
            ScenarioConfigurationInvalid,
            ScenarioStoreUnavailable,
        ) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(REFUSAL_SCENARIO_STORE_UNAVAILABLE, str(error)),
            ) from error

        return {
            "scenarios": [
                scenario_public_summary(scenario) for scenario in saved
            ]
        }

    @router.get(SCENARIO_DETAIL_ROUTE)
    def read_scenario(scenario_id: str) -> dict[str, object]:
        """Return one saved scenario, and what its declared target resolves to.

        The requested identity is validated here rather than only inside the
        port, so a malformed identity and an unreadable store cannot arrive as
        the same exception and be reported as the same thing. A malformed
        identity is answered as not found, because no scenario could ever carry
        it.

        The target resolution is computed after the scenario is read and never
        decides whether it can be read. A scenario whose declared Site is not
        configured is a readable scenario with an unresolved target, which is a
        screen state rather than a broken document.
        """
        try:
            validate_scenario_id(scenario_id)
        except ScenarioConfigurationInvalid as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_SCENARIO_NOT_FOUND,
                    f"No scenario with scenario ID {scenario_id!r} is saved, "
                    f"and no scenario could have that ID. {SCENARIO_ID_RULE}",
                ),
            ) from error

        try:
            scenario = scenario_detail.get_scenario(scenario_id)
        except ScenarioNotFound as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_SCENARIO_NOT_FOUND,
                    f"No scenario with scenario ID {scenario_id!r} is saved. "
                    "Scenario IDs are compared without regard to case, so a "
                    "different capitalisation of a saved scenario would have "
                    "been found.",
                ),
            ) from error
        except (
            ScenarioIdentityConflict,
            ScenarioConfigurationInvalid,
            ScenarioStoreUnavailable,
        ) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(REFUSAL_SCENARIO_STORE_UNAVAILABLE, str(error)),
            ) from error

        resolution = scenario_detail.resolve_target_site(scenario)
        sources = scenario_detail.resolve_observation_sources(scenario)

        return {
            "scenario": scenario_public_detail(scenario),
            "target_resolution": scenario_target_resolution(resolution),
            "observation_source_resolutions": [
                scenario_observation_source_resolution(item)
                for item in sources
            ],
            # The private half, in a section of its own. Built by a function
            # that reads no public field, so a client cannot confuse the two
            # for one another either.
            "private_expectations": scenario_private_expectations(scenario),
        }

    @router.get(RUN_PROFILES_ROUTE)
    def list_run_profiles() -> dict[str, object]:
        """The versioned profiles a run setup may select.

        Served so a person setting a run up can see what a profile models and
        what it resolves before choosing it, rather than discovering it from
        the reasons a Draft came back blocked.

        These are declared simulator rules rather than stored configuration,
        so there is no store to be unavailable and no failure state here.
        """
        return {
            "model_profiles": [
                run_profile_summary(profile) for profile in model_profiles
            ],
            "publication_profiles": [
                publication_profile_summary(profile)
                for profile in publication_profiles
            ],
        }

    @router.post(CREATE_RUN_ROUTE, status_code=201)
    def create_run(request: Any = Body(default=None)) -> dict[str, object]:
        """Set up one Draft SimulationRun, or refuse without allocating one.

        The two outcomes are deliberately different shapes, because they are
        different facts. A refusal is a 422 carrying the refusal kind and the
        product copy that names what is wrong: no `run_id` was allocated and
        nothing was written, so there is nothing to go and look at. A created
        Draft is a 201 carrying the frozen inputs and, when it is `BLOCKED`,
        the reasons - it exists, it is persisted, and a reader can inspect
        exactly what it froze and why it may not execute.

        Nothing here executes, steps, stages, commits, ingests or replays, and
        no field of the response says that anything did.
        """
        try:
            record = run_setup.create_draft_run(request)
        except RunSetupRefused as error:
            raise HTTPException(
                status_code=422,
                detail={
                    **_refusal(run_refusal_code(error.kind), error.message),
                    "refusal_kind": error.kind,
                    "run_created": False,
                },
            ) from error
        except (SiteStoreUnavailable, SiteConfigurationInvalid) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(
                    REFUSAL_STORE_UNAVAILABLE,
                    f"{error} No run was created.",
                ),
            ) from error
        except (
            ScenarioIdentityConflict,
            ScenarioConfigurationInvalid,
            ScenarioStoreUnavailable,
        ) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(
                    REFUSAL_SCENARIO_STORE_UNAVAILABLE,
                    f"{error} No run was created.",
                ),
            ) from error
        except (
            RunStoreUnavailable,
            RunConfigurationInvalid,
            RunIdentityConflict,
        ) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(
                    REFUSAL_RUN_STORE_UNAVAILABLE,
                    f"{error} Nothing was written.",
                ),
            ) from error

        return {"run": run_summary(record)}

    return router
