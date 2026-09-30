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

This module owns no simulated world and no private simulator truth. Since T022
it SERVES run execution, and it still owns none of it: the three control routes
speak a port the product declares and cannot implement, because only the neutral
composition leaf may import a kernel. What crosses back is a `LabProjection`, and
no trajectory, boundary or model type can be named here at all.

Its Site Templates endpoints read shipped, read-only configuration through the
`SiteTemplateCatalog` port: they return template archetypes, never Sites, and
never operational values. No template endpoint writes anything, and no route here
edits, renames, duplicates, or deletes anything.

Two routes write, and both are Simulator Lab capabilities behind the gate and
under the Lab prefix, absent from the served route inventory when the flag is
false. The three execution controls change no store at all: what they advance is
a handle the leaf holds, and what the leaf persists is a private artifact this
module cannot name a path to.

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

No route here commits, releases an envelope, ingests, resets, injects an event
or replays anything, and none of them returns an assessment, a source-health
result, a confidence, a severity, or a Finding, because none of those has a
truthful source. Starting a run left that list in T022 and staging in T023: a
started run produces private truth, the readings a configured device would have
published, and - through the simulated gateway - staged canonical source
envelopes, which one read route here serves for inspection. None of the three is
evidence about anywhere, and a staged envelope becomes one only after a Commit and
ingestion that no slice has built yet.

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

import re
from dataclasses import replace
from fractions import Fraction
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from assetops_backend.runs.execution_ports import LabExecutionPort
from assetops_backend.runs.models import SimulationRun, readiness_disclosure
from assetops_backend.runs.ports import (
    RunConfigurationInvalid,
    RunIdentityConflict,
    RunNotFound,
    RunStoreUnavailable,
    SimulationRunRepository,
)
from assetops_backend.runs.profiles import (
    ModelProfile,
    PublicationProfile,
)
from assetops_backend.runs.identity import RUN_ID_RULE, validate_run_id
from assetops_backend.runs.provenance import frozen_inputs
from assetops_backend.runs.refusals import RunSetupRefused
from assetops_backend.runs.service import RunInventoryService, RunSetupService
from assetops_backend.scenarios.execution import (
    BOUNDARY_CYCLE,
    BOUND_CASES,
    BOUND_POLICY_STATEMENTS,
    CANONICAL_UNITS,
    COUPLING_RULES,
    DISPATCH_RULES,
    EXECUTION_CONTRACT_VERSION,
    OBSERVATION_RULES,
    REPORTING_RULES,
    canonical_quantity,
    initialization_inputs,
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
from assetops_contracts.execution_contract import DISCRETE_STATE_RULES
from assetops_contracts.lab_history import (
    FAMILY_AVAILABILITY_STATEMENTS,
    SAMPLE_PHASES,
    LabHistory,
)
from assetops_contracts.lab_projection import (
    LAB_CONTROL_REFUSAL_STATEMENTS,
    ElectricalView,
    GeneratorView,
    LabControlRefused,
    LabProjection,
)
from assetops_contracts.observation import (
    READING_QUALITY_STATEMENTS,
    SAMPLE_OUTCOME_STATEMENTS,
    exact_decimal_text,
)
from assetops_contracts.source_envelope import (
    SOURCE_ENVELOPE_SCHEMA_ID,
    SOURCE_ENVELOPE_SCHEMA_VERSION,
    canonical_envelope_json,
)
from assetops_contracts.source_stage import (
    RELEASE_BLOCKER_STATEMENTS,
    SOURCE_STAGE_SCHEMA_VERSION,
    SourceStageView,
)

SIMULATOR_LAB_API_PREFIX = "/api/simulator-lab"

SITE_TEMPLATES_ROUTE = "/site-templates"
SITE_TEMPLATE_DETAIL_ROUTE = "/site-templates/{template_id}"
CREATE_SITE_ROUTE = "/sites"
SCENARIOS_ROUTE = "/scenarios"
SCENARIO_DETAIL_ROUTE = "/scenarios/{scenario_id}"
RUN_PROFILES_ROUTE = "/run-profiles"
CREATE_RUN_ROUTE = "/runs"
RUNS_ROUTE = "/runs"
RUN_DETAIL_ROUTE = "/runs/{run_id}"

# The four execution routes. One read and three controls, and the split is the
# point: reading where a run is changes nothing, and each control is a separate
# act with a separate refusal.
RUN_EXECUTION_ROUTE = "/runs/{run_id}/execution"
RUN_EXECUTION_START_ROUTE = "/runs/{run_id}/execution/start"
RUN_EXECUTION_STEP_ROUTE = "/runs/{run_id}/execution/step"
RUN_EXECUTION_END_ROUTE = "/runs/{run_id}/execution/run-to-end"

# The stage inspector's one route, and it is a read. There is no route that
# edits, deletes, releases or commits a staged envelope: staging happens as a run
# is stepped, and a staged record is immutable.
RUN_STAGE_ROUTE = "/runs/{run_id}/stage"

# T025c. What a run recorded, as a read of its own: a history is tens of
# thousands of rows, and a step response carrying it would ship the whole run
# again at every boundary.
RUN_EXECUTION_HISTORY_ROUTE = "/runs/{run_id}/execution/history"

# T025e live follow. `?since_boundary=n` answers the same `history` document
# with each APPEND family narrowed to the rows recorded after the client's n
# boundaries, plus a sibling `delta` envelope. It is a selection over the
# `LabHistory` the port returns and computes no quantity. Each append family
# is keyed by the offset of the boundary that records its row: an interval
# belongs to the boundary that decided it (`from_offset`), not the one that
# closes it, because that is where the capture records it. That every family
# only ever grows at its end is proven per boundary in
# `host/tests/test_lab_history_prefix.py`; a family that failed it would move
# out of this table into the sent-whole class, never be patched by a client.
HISTORY_APPEND_FAMILY_KEYS: dict[str, str] = {
    "boundaries": "offset_minutes",
    "samples": "offset_minutes",
    "intervals": "from_offset",
    "attempts": "at_offset_minutes",
    "applied_events": "at_offset_minutes",
    "bounded_transitions": "at_offset_minutes",
    "discrete_transitions": "at_offset_minutes",
    # Owner approved 2026-09-30 after phase 1 measured a 71,935 B one-boundary
    # delta, 57,443 B of it `exposures` sent whole: an exposure is recorded at
    # the boundary its window opens, and the prefix guard proves it append-only.
    "exposures": "from_offset",
}
# Frozen with the run: sent by the full read only, empty (or null) in a delta,
# and kept by the client from its base. `coverage` and the manifest scalars
# are neither: they are sent whole in every delta.
HISTORY_STATIC_FAMILIES = (
    "signals",
    "bus_attachments",
    "reporting_gaps",
    "drawing_context",
    "sample_phases",
)
REFUSAL_HISTORY_SINCE_AHEAD = "HISTORY_SINCE_AHEAD"
_WHOLE_NUMBER = re.compile(r"[0-9]+")

# Refusal codes. The message is the product copy a user reads; the code is what
# a client switches on, so neither has to be parsed out of the other.
REFUSAL_INVALID_REQUEST = "SITE_REQUEST_INVALID"
REFUSAL_SITE_ID_IN_USE = "SITE_ID_IN_USE"
REFUSAL_TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
REFUSAL_STORE_UNAVAILABLE = "SITE_STORE_UNAVAILABLE"
REFUSAL_SCENARIO_NOT_FOUND = "SCENARIO_NOT_FOUND"
REFUSAL_SCENARIO_STORE_UNAVAILABLE = "SCENARIO_STORE_UNAVAILABLE"
REFUSAL_RUN_STORE_UNAVAILABLE = "RUN_STORE_UNAVAILABLE"
REFUSAL_RUN_NOT_FOUND = "RUN_NOT_FOUND"
REFUSAL_EXECUTION_REQUEST_INVALID = "EXECUTION_REQUEST_INVALID"


def execution_refusal_code(kind: str) -> str:
    """A control refusal code: the refusal kind, prefixed.

    Derived from `LAB_CONTROL_REFUSALS` exactly as `run_refusal_code` is derived
    from the setup vocabulary, and for the same reason: a kind added to the
    contract with no code here would reach a client as a refusal nobody could
    switch on.
    """
    return f"EXECUTION_{kind}"


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
        # The ADDRESS since T020A1. A reader of a scenario with two tanks
        # needs to see which tank a row is about, and the semantic key alone
        # renders two different declarations as the same text.
        "state_key": parameter.addressed_key,
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
                "state_key": parameter.bounds.state_ref.addressed_key,
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
        "state_key": entry.addressed_key,
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
      the boundary cycle, what a timestamped reading means, whether one exists
      at all, and the bound policies - which are versioned simulator rules
      rather than authored content;
    - what this scenario's own inputs initialize and transition, which is the
      whole of the surface an executor would consume.

    **There is no third part any more, and its removal is T022's.** This payload
    used to carry `observation_reconciliation`: each authored reading beside the
    value the document's own declared causes reached, with the difference between
    them. `D-2026-09-22-reconciliation-panel-retirement` put its removal in the
    slice that falsifies it, and this is that slice. A run now GENERATES the
    reading, from a world a kernel computed, so the honest presentation of what a
    sensor said is the Lab's observation row and not a subtraction over a document.
    A panel comparing an authored number against a partial account of it would now
    be the weaker of two available answers, offered beside the stronger one.
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
        # The cycle a conforming kernel runs at each instant, in order. Carried
        # on the wire rather than drawn on a screen from a local copy, because
        # the order is the contract and a second copy of it is a second thing
        # that can be wrong.
        "boundary_cycle": [
            {
                "phase_id": phase.phase_id,
                "sequence": phase.sequence,
                "display_name": phase.display_name,
                "statement": phase.statement,
            }
            for phase in BOUNDARY_CYCLE
        ],
        "observation_rules": [
            {
                "rule_id": rule.rule_id,
                "reading_class": rule.reading_class,
                "display_name": rule.display_name,
                "statement": rule.statement,
            }
            for rule in OBSERVATION_RULES
        ],
        "bound_cases": [
            {
                "case_id": case.case_id,
                "display_name": case.display_name,
                "policy": case.policy,
                # What the policy itself commits a kernel to, beside the case
                # that carries it. A reader could see `BOUNDED_AND_RECORDED`
                # with nothing saying whether the run then continues.
                "policy_statement": BOUND_POLICY_STATEMENTS[case.policy],
                "statement": case.statement,
            }
            for case in BOUND_CASES
        ],
        "initialization_inputs": [
            {
                "parameter_id": item.parameter_id,
                "display_name": item.display_name,
                "state_key": item.addressed_key,
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
                "state_key": item.addressed_key,
                "direction": item.direction,
                "parameter_id": item.parameter_id,
                "applied_value": item.applied_value,
                "applied_unit": item.applied_unit,
                "starts_at_offset": item.starts_at_offset,
                "complete_at_offset": item.complete_at_offset,
            }
            for item in state_transition_inputs(scenario)
        ],
        # The rules about whether a reading exists at all, beside the rules about
        # what one means. New in T022 and on the wire for the same reason the
        # boundary cycle is: a screen explaining why a step produced no reading
        # should place the contract's own sentence rather than write a second one.
        "reporting_rules": [
            {
                "rule_id": rule.rule_id,
                "display_name": rule.display_name,
                "statement": rule.statement,
            }
            for rule in REPORTING_RULES
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
                # The semantic key and the scope, never a component id. What
                # a profile can model is a kind of claim; which asset a run
                # resolves it on is the scenario's and the site's.
                "scope": state.scope,
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
        # The reporting-path conditions this profile can model, at the same
        # grain a model profile's states are published at: a kind of claim and
        # never a component id. An empty list is a real answer and blocks a
        # scenario that requires one.
        "supported_reporting_states": [
            {
                "state_key": state.state_key,
                "scope": state.scope,
                "supported_roles": sorted(state.supported_roles),
                "statement": state.statement,
            }
            for state in profile.supported_reporting_states
        ],
    }


def run_inventory_row(record: SimulationRun) -> dict[str, object]:
    """Inventory shape: which Drafts exist, and what each one is bound to.

    Identity, the two statuses, the versions a run froze, and the interval it
    covers. Every value comes from the record.

    What is deliberately absent is what an inventory of runs invites: there
    is no progress, no elapsed time, no health, no source quality, no
    evidence state and no count of anything produced, because nothing has
    been produced. A column for one of those would be a column of zeroes, and
    a zero is a measurement.

    The frozen identity is not here either. A row says which runs exist;
    reading one is the detail route's job, the same split the scenario
    catalog uses.
    """
    identity = record.deterministic_identity
    return {
        "run_id": record.run_id,
        "lifecycle_status": record.lifecycle_status,
        "execution_status": record.execution_status,
        "created_at": record.created_at,
        "site_id": identity.site.site_id,
        "foundation_version": identity.site.foundation_version,
        "scenario_id": identity.scenario.scenario_id,
        "scenario_version": identity.scenario.scenario_version,
        "interval": {
            "start_time": identity.interval.start_time,
            "end_time": identity.interval.end_time,
            "duration_minutes": identity.interval.duration_minutes,
        },
        "blocking_reason_count": len(record.blocking_reasons),
    }


def electrical_payload(view: ElectricalView | None) -> dict[str, object] | None:
    """The electrical world of one execution on the wire (T024).

    Private truth for the gated Lab, every quantity as exact text. `steps` is
    PV, the battery and service against simulation time; the `latest_*`
    collections are the most recent step's view, request, acceptance, loads,
    named flows and reserve in effect, kept as separate collections because the
    contract keeps them separate. The coupling rules travel beside them so the
    screen states the contract rather than composing its own sentence.
    """
    if view is None:
        return None

    def exact(value: object) -> str | None:
        # T025a: a typed discrete member (unit `state`) crosses as itself.
        if isinstance(value, str):
            return value
        return None if value is None else exact_decimal_text(value)

    return {
        "battery_address": view.battery_address,
        "generator": generator_payload(view.generator),
        "coupling_rules": [
            {
                "rule_id": rule.rule_id,
                "display_name": rule.display_name,
                "statement": rule.statement,
            }
            for rule in COUPLING_RULES
        ],
        "steps": [
            {
                "from_offset": row.from_offset,
                "to_offset": row.to_offset,
                "simulation_time": row.simulation_time,
                "soc_start": exact(row.soc_start),
                "soc_end": exact(row.soc_end),
                "reserve": exact(row.reserve),
                "reserve_origin": row.reserve_origin,
                "pv_potential": exact(row.pv_potential),
                "pv_output": exact(row.pv_output),
                "curtailed": exact(row.curtailed),
                "clipped": exact(row.clipped),
                "battery_power": exact(row.battery_power),
                "requested_battery_power": exact(row.requested_battery_power),
                "limited_by": list(row.limited_by),
                "demand": exact(row.demand),
                "served": exact(row.served),
                "unserved": exact(row.unserved),
            }
            for row in view.steps
        ],
        "latest_view": [
            {
                "name": item.name,
                "address": item.address,
                "value": exact(item.value),
                "unit": item.unit,
            }
            for item in view.latest_view
        ],
        "latest_requests": [
            {
                "address": item.address,
                "quantity": item.quantity,
                "requested": exact(item.requested),
                "unit": item.unit,
                "reason": item.reason,
            }
            for item in view.latest_requests
        ],
        "latest_controls": [
            {
                "address": item.address,
                "quantity": item.quantity,
                "requested": exact(item.requested),
                "accepted": exact(item.accepted),
                "unit": item.unit,
                "limited_by": list(item.limited_by),
            }
            for item in view.latest_controls
        ],
        "latest_loads": [
            {
                "address": item.address,
                "priority_rank": item.priority_rank,
                "demand_power": exact(item.demand_power),
                "served_power": exact(item.served_power),
                "unserved_power": exact(item.unserved_power),
                "demand_energy": exact(item.demand_energy),
                "served_energy": exact(item.served_energy),
                "unserved_energy": exact(item.unserved_energy),
            }
            for item in view.latest_loads
        ],
        "latest_flows": [
            {
                "flow_id": item.flow_id,
                "from_address": item.from_address,
                "to_address": item.to_address,
                "energy": exact(item.energy),
                "mean_power": exact(item.mean_power),
            }
            for item in view.latest_flows
        ],
        "latest_effective_controls": [
            {
                "address": item.address,
                "from_offset": item.from_offset,
                "to_offset": item.to_offset,
                "value": exact(item.value),
                "unit": item.unit,
                "origin": item.origin,
                "provenance": item.provenance,
            }
            for item in view.latest_effective_controls
        ],
        "latest_balances": list(view.latest_balances),
        "latest_segments": [list(item) for item in view.latest_segments],
        "notes": list(view.notes),
    }


def generator_payload(view: GeneratorView | None) -> dict[str, object] | None:
    """T025a. The generator of a `mini-grid` execution on the wire.

    Four things the contract keeps apart travel as four fields per step: the
    physical state at T, the state over the step, the controller's request and
    the accepted output. Every transition carries its phase, cause and
    instant. The reported status is stated as pending, never omitted.
    """
    if view is None:
        return None
    return {
        "state_address": view.state_address,
        "fuel_address": view.fuel_address,
        "reported_status": view.reported_status,
        "discrete_state_rules": [
            {
                "rule_id": rule.rule_id,
                "display_name": rule.display_name,
                "statement": rule.statement,
            }
            for rule in DISCRETE_STATE_RULES
        ],
        "steps": [
            {
                "from_offset": row.from_offset,
                "to_offset": row.to_offset,
                "simulation_time": row.simulation_time,
                "state_at_t": row.state_at_t,
                "state_for_step": row.state_for_step,
                "requested": row.requested,
                "request_reason": row.request_reason,
                "output": exact_decimal_text(row.output),
                "to_load": exact_decimal_text(row.to_load),
                "to_battery": exact_decimal_text(row.to_battery),
                "fuel_start": exact_decimal_text(row.fuel_start),
                "fuel_end": exact_decimal_text(row.fuel_end),
                "limited_by": list(row.limited_by),
                # T025b: the reported status at T and its quality, or null when
                # the run publishes no status reading (before profile 4).
                "reported_state": row.reported_state,
                "reported_quality": row.reported_quality,
            }
            for row in view.steps
        ],
        "transitions": [
            {
                "address": item.address,
                "previous": item.previous,
                "next": item.next,
                "phase": item.phase,
                "cause": item.cause,
                "controller_ref": item.controller_ref,
                "at_offset_minutes": item.at_offset_minutes,
                "simulation_time": item.simulation_time,
            }
            for item in view.transitions
        ],
    }


def execution_payload(projection: LabProjection) -> dict[str, object]:
    """One gated Lab projection on the wire.

    **Every exact quantity travels as text, and no float appears anywhere.** The
    numeric policy is `EXACT_RATIONAL` and nothing in this build rounds, so a
    payload carrying `3.4987499999999997` where the arithmetic produced `2799/800`
    would be the one place the policy stopped holding - and it would hold the
    screen responsible for formatting a number the wire had already spoiled.
    `exact_decimal_text` writes the decimal the rational has, which every number
    this build has produced does.

    The three vocabularies' own statements are placed beside the rows that carry
    their values, for the reason the readiness disclosure is: a screen composing
    its own sentence about `SUPPRESSED_BY_GAP` would be a second copy of a rule.
    """

    def exact(value: object) -> str | None:
        # T025b: a typed discrete reading (unit `state`) travels as the member
        # text it is - `RUNNING` - and never as a decimal code.
        if isinstance(value, str):
            return value
        return None if value is None else exact_decimal_text(value)

    return {
        "run_id": projection.run_id,
        "status": projection.status,
        "statement": projection.statement,
        "boundaries_completed": projection.boundaries_completed,
        "boundaries_total": projection.boundaries_total,
        "offset_minutes": projection.offset_minutes,
        "simulation_time": projection.simulation_time,
        "interval_start_time": projection.interval_start_time,
        "interval_end_time": projection.interval_end_time,
        "timestep_minutes": projection.timestep_minutes,
        "seed": projection.seed,
        "kernel_version": projection.kernel_version,
        "model_profile_id": projection.model_profile_id,
        "model_profile_version": projection.model_profile_version,
        "publication_profile_id": projection.publication_profile_id,
        "publication_profile_version": projection.publication_profile_version,
        "numeric_policy": projection.numeric_policy,
        "numeric_policy_version": projection.numeric_policy_version,
        "execution_contract_version": projection.execution_contract_version,
        "inputs_identity": projection.inputs_identity,
        "content_digest": projection.content_digest,
        "observation_series_digest": projection.observation_series_digest,
        "reported_count": projection.reported_count,
        "suppressed_by_gap_count": projection.suppressed_by_gap_count,
        "dropped_count": projection.dropped_count,
        "notes": list(projection.notes),
        "failure": (
            None
            if projection.failure is None
            else {
                "kind": projection.failure.kind,
                "subject": projection.failure.subject,
                "statement": projection.failure.statement,
                "at_offset_minutes": projection.failure.at_offset_minutes,
                "detail": list(projection.failure.detail),
            }
        ),
        # Private truth, on a gated surface and nowhere else. The exact stock the
        # kernel holds, which is the left-hand column of the distinction this
        # whole screen exists to make.
        "private_state": [
            {
                "address": row.address,
                "state_key": row.state_key,
                "value": exact(row.value),
                "canonical_unit": row.canonical_unit,
                "kind": row.kind,
            }
            for row in projection.private_state
        ],
        "observations": [
            {
                "address": view.address,
                "state_key": view.state_key,
                "device_id": view.device_id,
                "signal_id": view.signal_id,
                "reading_class": view.reading_class,
                "at_offset_minutes": view.at_offset_minutes,
                "simulation_time": view.simulation_time,
                "canonical_unit": view.canonical_unit,
                "true_value": exact(view.true_value),
                "reported_value": exact(view.reported_value),
                "reported_source_time": view.reported_source_time,
                "reported_at_offset_minutes": view.reported_at_offset_minutes,
                "quality": view.quality,
                "quality_statement": READING_QUALITY_STATEMENTS[view.quality],
                "due": view.due,
                "outcome": view.outcome,
                "outcome_statement": (
                    None
                    if view.outcome is None
                    else SAMPLE_OUTCOME_STATEMENTS[view.outcome]
                ),
                "suppression_reason": view.suppression_reason,
                "cadence_minutes": view.cadence_minutes,
                "bias": exact(view.bias),
                "dropout_per_thousand": view.dropout_per_thousand,
            }
            for view in projection.observations
        ],
        "signals": [
            {
                "device_id": signal.device_id,
                "signal_id": signal.signal_id,
                "address": signal.address,
                "state_key": signal.state_key,
                "reading_class": signal.reading_class,
                "canonical_unit": signal.canonical_unit,
                "cadence_minutes": signal.cadence_minutes,
                "bias": exact(signal.bias),
                "dropout_per_thousand": signal.dropout_per_thousand,
                "statement": signal.statement,
            }
            for signal in projection.signals
        ],
        "reporting_gaps": [
            {
                "event_id": window.event_id,
                "condition_address": window.condition_address,
                "device_id": window.device_id,
                "signal_id": window.signal_id,
                "address": window.address,
                # The shape, the instant the document DECLARED, and the span
                # that instant RESOLVED to. All three, under three names,
                # because for a POINT the first two differ: an entry declared
                # at offset 1490 in a fifteen-minute run silences the sample
                # at 1485. This field was called `offset_minutes` and carried
                # the resolved start, which is the right number under a name
                # that promises the other one - and a reader comparing it with
                # the authored document would have found them disagreeing with
                # nothing on the wire to explain it.
                "timing_shape": window.timing_shape,
                "declared_offset_minutes": window.offset_minutes,
                "start_offset_minutes": window.start_offset_minutes,
                "end_offset_minutes": window.end_offset_minutes,
            }
            for window in projection.reporting_gaps
        ],
        "recent_reports": [
            {
                "device_id": item.device_id,
                "signal_id": item.signal_id,
                "address": item.address,
                "reading_class": item.reading_class,
                "at_offset_minutes": item.at_offset_minutes,
                "source_sample_time": item.source_sample_time,
                "outcome": item.outcome,
                "outcome_statement": SAMPLE_OUTCOME_STATEMENTS[item.outcome],
                "reported_value": exact(item.reported_value),
                "canonical_unit": item.canonical_unit,
                "suppression_reason": item.suppression_reason,
            }
            for item in projection.recent_reports
        ],
        "electrical": electrical_payload(projection.electrical),
    }


def history_payload(
    history: LabHistory, run: SimulationRun | None = None
) -> dict[str, object]:
    """One run's recorded Lab history on the wire (T025c), gated.

    Exact quantities as exact text and discrete members as themselves, like
    `execution_payload`; an absent value is `null`, never zero. Every record
    carries its own offset and address, and every sample its phase, so the
    screen never infers when a value applies from where it sits in a list.
    """

    def exact(value: object) -> str | None:
        if isinstance(value, str):
            return value
        return None if value is None else exact_decimal_text(value)

    failure = history.failure
    return {
        "run_id": history.run_id,
        "status": history.status,
        "source": history.source,
        "statement": history.statement,
        "history_schema_version": history.history_schema_version,
        "boundaries_total": history.boundaries_total,
        "boundaries_recorded": len(history.boundaries),
        "recorded_through_offset_minutes": history.recorded_through_offset,
        "inputs_identity": history.inputs_identity,
        "content_digest": history.content_digest,
        "observation_series_digest": history.observation_series_digest,
        "history_digest": history.history_digest,
        "notes": list(history.notes),
        "failure": None
        if failure is None
        else {
            "kind": failure.kind,
            "subject": failure.subject,
            "statement": failure.statement,
            "at_offset_minutes": failure.at_offset_minutes,
            "detail": list(failure.detail),
        },
        "coverage": [
            {
                "family": entry.family,
                "availability": entry.availability,
                "availability_statement": FAMILY_AVAILABILITY_STATEMENTS[
                    entry.availability
                ],
                "statement": entry.statement,
            }
            for entry in history.coverage
        ],
        "sample_phases": [
            {"phase": phase, "statement": statement}
            for phase, statement in SAMPLE_PHASES.items()
        ],
        "boundaries": [
            {
                "step_index": b.step_index,
                "offset_minutes": b.offset_minutes,
                "simulation_time": b.simulation_time,
                "has_preceding_interval": b.has_preceding_interval,
            }
            for b in history.boundaries
        ],
        "samples": [
            {
                "offset_minutes": s.offset_minutes,
                "address": s.address,
                "state_key": s.state_key,
                "phase": s.phase,
                "unit": s.unit,
                "value": exact(s.value),
            }
            for s in history.samples
        ],
        "intervals": [
            {
                "from_offset": i.from_offset,
                "to_offset": i.to_offset,
                "segments": [list(segment) for segment in i.step.accepted.segments],
                "view": [
                    {
                        "name": e.name,
                        "address": e.address,
                        "value": exact(e.value),
                        "unit": e.unit,
                    }
                    for e in i.step.view.entries
                ],
                "requests": [
                    {
                        "address": r.address,
                        "quantity": r.quantity,
                        "requested": exact(r.requested),
                        "unit": r.unit,
                        "reason": r.reason,
                    }
                    for r in i.step.intent.requests
                ],
                "controls": [
                    {
                        "address": c.address,
                        "quantity": c.quantity,
                        "requested": exact(c.requested),
                        "accepted": exact(c.accepted),
                        "unit": c.unit,
                        "limited_by": list(c.limited_by),
                    }
                    for c in i.step.accepted.controls
                ],
                "loads": [
                    {
                        "address": l.address,
                        "priority_rank": l.priority_rank,
                        "demand_energy": exact(l.demand_energy),
                        "served_energy": exact(l.served_energy),
                        "unserved_energy": exact(l.unserved_energy),
                        "demand_power": exact(l.demand_power),
                        "served_power": exact(l.served_power),
                        "unserved_power": exact(l.unserved_power),
                    }
                    for l in i.step.accepted.loads
                ],
                "flows": [
                    {
                        "flow_id": f.flow_id,
                        "from_address": f.from_address,
                        "to_address": f.to_address,
                        "energy": exact(f.energy),
                        "mean_power": exact(f.mean_power),
                    }
                    for f in i.step.accepted.flows
                ],
                "effective_controls": [
                    {
                        "address": e.address,
                        "from_offset": e.from_offset,
                        "to_offset": e.to_offset,
                        "value": exact(e.value),
                        "unit": e.unit,
                        "origin": e.origin,
                        "provenance": e.provenance,
                    }
                    for e in i.step.accepted.effective_controls
                ],
                "balances": [b.identity_id for b in i.step.accepted.balances],
                "balance_identities": [
                    _balance_identity_payload(b, i.step.accepted.flows, exact)
                    for b in i.step.accepted.balances
                ],
                "notes": list(i.step.accepted.notes),
            }
            for i in history.intervals
        ],
        # T025d: the reporting-path windows the run declared and resolved, so
        # the reporting lane of the timeline reads them from the same recorded
        # result as everything else. The same fields as `execution_payload`'s.
        "reporting_gaps": [
            {
                "event_id": window.event_id,
                "condition_address": window.condition_address,
                "device_id": window.device_id,
                "signal_id": window.signal_id,
                "address": window.address,
                "timing_shape": window.timing_shape,
                "declared_offset_minutes": window.offset_minutes,
                "start_offset_minutes": window.start_offset_minutes,
                "end_offset_minutes": window.end_offset_minutes,
            }
            for window in history.reporting_gaps
        ],
        "exposures": [
            {
                "address": x.address,
                "event_id": x.event_id,
                "parameter_id": x.parameter_id,
                "value": exact(x.value),
                "from_offset": x.from_offset,
                "to_offset": x.to_offset,
            }
            for x in history.exposures
        ],
        "attempts": [
            {
                "at_offset_minutes": o.at_offset_minutes,
                "address": o.address,
                "device_id": o.device_id,
                "signal_id": o.signal_id,
                "state_key": o.state_key,
                "reading_class": o.reading_class,
                "source_sample_time": o.source_sample_time,
                "outcome": o.outcome,
                "reported_value": exact(o.reported_value),
                "canonical_unit": o.canonical_unit,
                "suppression_reason": o.suppression_reason,
            }
            for o in history.attempts
        ],
        "signals": [
            {
                "address": g.address,
                "device_id": g.device_id,
                "signal_id": g.signal_id,
                "reading_class": g.reading_class,
                "canonical_unit": g.canonical_unit,
                "cadence_minutes": g.cadence_minutes,
            }
            for g in history.signals
        ],
        "applied_events": [
            {
                "event_id": e.event_id,
                "address": e.address,
                "direction": e.direction,
                "at_offset_minutes": e.at_offset_minutes,
                "share": exact(e.share),
                "declared": exact(e.declared),
                "origin": e.origin,
                "phase_id": e.phase_id,
            }
            for e in history.applied_events
        ],
        "bounded_transitions": [
            {
                "address": t.address,
                "at_offset_minutes": t.at_offset_minutes,
                "bound_case_id": t.bound_case_id,
                "bound_kind": t.bound_kind,
                "bound_value": exact(t.bound_value),
                "requested": exact(t.requested),
                "accepted": exact(t.accepted),
                "refused": exact(t.refused),
                "event_ids": list(t.event_ids),
            }
            for t in history.bounded_transitions
        ],
        "discrete_transitions": [
            {
                "address": t.address,
                "state_key": t.state_key,
                "previous": t.previous,
                "next": t.next,
                "phase": t.phase,
                "cause": t.cause,
                "at_offset_minutes": t.at_offset_minutes,
                "simulation_time": t.simulation_time,
            }
            for t in history.discrete_transitions
        ],
        "bus_attachments": [
            {
                "role": a.role,
                "component_id": a.component_id,
                "via_component_id": a.via_component_id,
                "bus_component_id": a.bus_component_id,
            }
            for a in history.bus_attachments
        ],
        "drawing_context": _drawing_context_payload(history, run),
    }


def history_delta_payload(
    history: LabHistory, since_boundary: int, run: SimulationRun | None = None
) -> dict[str, object]:
    """The rows `history` recorded after its first `since_boundary` boundaries.

    T025e. The `history` document of `history_payload`, with every append
    family narrowed to rows whose recording boundary lies after boundary
    `since_boundary`, the static families empty (`drawing_context` null), and
    the manifest - `boundaries_recorded`, `recorded_through_offset_minutes`,
    status, digests, coverage, notes, failure - whole. A delta
    is not a verifiable document, so its `history_digest` is always null. The
    route has already refused a `since_boundary` past what is recorded.
    """
    if not 0 <= since_boundary <= len(history.boundaries):
        raise ValueError(
            f"since_boundary {since_boundary} is outside the "
            f"{len(history.boundaries)} boundaries recorded."
        )
    after = (
        None
        if since_boundary == 0
        else history.boundaries[since_boundary - 1].offset_minutes
    )

    def newer(family: str) -> tuple:
        rows = getattr(history, family)
        if after is None:
            return rows
        key = HISTORY_APPEND_FAMILY_KEYS[family]
        return tuple(row for row in rows if getattr(row, key) > after)

    selected = replace(
        history,
        history_digest=None,
        signals=(),
        reporting_gaps=(),
        bus_attachments=(),
        **{family: newer(family) for family in HISTORY_APPEND_FAMILY_KEYS},
    )
    payload = history_payload(selected, run)
    payload["boundaries_recorded"] = len(history.boundaries)
    payload["recorded_through_offset_minutes"] = history.recorded_through_offset
    payload["sample_phases"] = []
    payload["drawing_context"] = None
    return payload


def _parse_since_boundary(raw: str, history: LabHistory) -> int:
    """A delta read's `since_boundary`, or a typed refusal.

    A whole number of boundaries the caller already holds: not negative, not a
    fraction or a word, and not more than this run has recorded. The last is
    a different fact - the request was well formed and the run is not there -
    so it is a 409 with its own code, like a control refusal.
    """
    if not _WHOLE_NUMBER.fullmatch(raw):
        raise HTTPException(
            status_code=422,
            detail=_refusal(
                REFUSAL_EXECUTION_REQUEST_INVALID,
                "A history read's 'since_boundary' is the whole number of "
                f"boundaries already held, and this one is {raw!r}.",
            ),
        )
    since = int(raw)
    recorded = len(history.boundaries)
    if since > recorded:
        raise HTTPException(
            status_code=409,
            detail=_refusal(
                REFUSAL_HISTORY_SINCE_AHEAD,
                f"This run has recorded {recorded} boundaries, so there is "
                f"nothing after boundary {since} to send. Read the whole "
                "history instead.",
            ),
        )
    return since


def _balance_identity_payload(
    balance: Any, flows: Any, exact: Any
) -> dict[str, object]:
    """One recorded balance identity with the exact sums of its named flows.

    T025d. The kernel checks every identity exactly and records only which
    flows it names; the screen needs the numbers to show the balance holding.
    This sums the recorded flow energies by id - it resolves nothing and
    computes no physics. A named flow the interval does not carry leaves the
    sums absent rather than partial.
    """
    energies = {flow.flow_id: flow.energy for flow in flows}
    named = (*balance.sources, *balance.sinks)
    complete = all(flow_id in energies for flow_id in named)
    source_energy = (
        sum((energies[f] for f in balance.sources), Fraction(0)) if complete else None
    )
    sink_energy = (
        sum((energies[f] for f in balance.sinks), Fraction(0)) if complete else None
    )
    return {
        "identity_id": balance.identity_id,
        "sources": list(balance.sources),
        "sinks": list(balance.sinks),
        "source_energy": exact(source_energy),
        "sink_energy": exact(sink_energy),
        "residual": None
        if source_energy is None or sink_energy is None
        else exact(source_energy - sink_energy),
    }


#: What each drawing-context status means, stated once for the wire.
DRAWING_CONTEXT_STATEMENTS = {
    "VERIFIED": (
        "The bus attachments this run executed against are the ones its frozen "
        "identity records, with the declared connections that carry them. A "
        "drawing may bind to them only on the Foundation version named here."
    ),
    "NOT_RECORDED": (
        "This run's history records no bus attachments, so there is no "
        "drawing bound to this run to put its values on."
    ),
    "DISAGREES": (
        "The attachments this run's history records differ from the ones its "
        "frozen identity records, so neither is a safe basis for a drawing."
    ),
}


def _drawing_context_payload(
    history: LabHistory, run: SimulationRun | None
) -> dict[str, object] | None:
    """The run-bound basis for drawing this history on the configured SLD.

    T025d. The history records which attachments the run EXECUTED against;
    the frozen run identity records the same attachments with the declared
    connections that carry each, and the Site and Foundation version they were
    frozen from. Both must agree before a screen may bind recorded values to a
    drawing, and the screen must still check the Site it reads is that version.
    """
    if run is None:
        return None
    identity = run.deterministic_identity
    frozen = identity.bus_attachments
    if history.availability("drawing") != "RECORDED" or not frozen:
        status = "NOT_RECORDED"
    elif tuple(
        (a.role, a.component_id, a.via_component_id, a.bus_component_id)
        for a in history.bus_attachments
    ) != tuple(
        (a.role, a.component_id, a.via_component_id, a.bus_component_id)
        for a in frozen
    ):
        status = "DISAGREES"
    else:
        status = "VERIFIED"
    return {
        "site_id": identity.site.site_id,
        "foundation_version": identity.site.foundation_version,
        "status": status,
        "statement": DRAWING_CONTEXT_STATEMENTS[status],
        "attachments": []
        if status != "VERIFIED"
        else [
            {
                "role": a.role,
                "component_id": a.component_id,
                "via_component_id": a.via_component_id,
                "bus_component_id": a.bus_component_id,
                "connection_ids": list(a.connection_ids),
            }
            for a in frozen
        ],
    }


def stage_payload(view: SourceStageView) -> dict[str, object]:
    """One Draft's staged source envelopes on the wire, for the gated inspector.

    Each envelope travels twice, deliberately: `canonical` is its exact persisted
    text, byte for byte what the stage holds and what a later ingestion will
    parse, and the fields beside it are that same text's metadata split out so a
    screen can show source time and publication time in separate cells without
    parsing anything. The fields are derived from the parsed envelope; the text
    is the envelope's own canonical serialization of it; so the two cannot
    disagree.

    Nothing here is accepted evidence, and the payload says so in its own
    statement rather than leaving a screen to.
    """
    stage = view.stage
    return {
        "run_id": view.run_id,
        "status": view.status,
        "statement": view.statement,
        "execution_status": view.execution_status,
        "release_eligible": view.release_eligible,
        "release_blockers": [
            {"kind": kind, "statement": RELEASE_BLOCKER_STATEMENTS[kind]}
            for kind in view.release_blockers
        ],
        "unreadable_detail": view.unreadable_detail,
        "envelope_schema_id": SOURCE_ENVELOPE_SCHEMA_ID,
        "envelope_schema_version": SOURCE_ENVELOPE_SCHEMA_VERSION,
        "stage_schema_version": SOURCE_STAGE_SCHEMA_VERSION,
        "integrity_digest": view.integrity_digest,
        # How far the stage records its run as published. Eligibility needs
        # this to reach the total; a completed execution alone cannot vouch
        # for what the stage holds.
        "boundaries_total": None if stage is None else stage.boundaries_total,
        "published_through": None if stage is None else stage.published_through,
        "site_id": None if stage is None else stage.site_id,
        "source_id": None if stage is None else stage.source_id,
        "gateway_id": None if stage is None else stage.gateway_id,
        "mapping": (
            None
            if stage is None
            else {
                "mapping_set_id": stage.mapping.mapping_set_id,
                "mapping_version": stage.mapping.mapping_version,
                "publication_latency_seconds": (
                    stage.mapping.publication_latency_seconds
                ),
                "entries": [
                    {
                        "device_id": entry.device_id,
                        "signal_id": entry.signal_id,
                        "measurement": entry.measurement,
                        "unit": entry.unit,
                        "publishes_unavailable": entry.publishes_unavailable,
                    }
                    for entry in stage.mapping.entries
                ],
            }
        ),
        "refused_publications": (
            []
            if stage is None
            else [
                {"message_id": item.message_id, "kind": item.kind}
                for item in stage.refused
            ]
        ),
        "envelopes": (
            []
            if stage is None
            else [
                {
                    "canonical": canonical_envelope_json(envelope),
                    "message_id": envelope.message_id,
                    "sequence": envelope.sequence,
                    "device_id": envelope.device_id,
                    "signal_id": envelope.signal_id,
                    "mapping_set_id": envelope.mapping_set_id,
                    "mapping_version": envelope.mapping_version,
                    "schema_version": envelope.schema_version,
                    "source_time": envelope.source_time,
                    "published_at": envelope.published_at,
                    "measurement": envelope.measurement,
                    "value": (
                        None
                        if envelope.value is None
                        else exact_decimal_text(envelope.value)
                    ),
                    "unit": envelope.unit,
                    "quality": envelope.quality,
                    "unavailable_reason": envelope.unavailable_reason,
                    "interval_start": envelope.interval_start,
                    "interval_end": envelope.interval_end,
                }
                for envelope in stage.envelopes
            ]
        ),
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
        # What the status does not assert, carried by the payload rather than
        # written on a screen. A caller reading this over the wire gets the
        # same statement the screen shows, because it is a property of the
        # status and not a note somebody added to one surface.
        "readiness_disclosure": readiness_disclosure(record.execution_status),
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
                    "state_key": item.addressed_key,
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
                "blocking_statement": row.blocking_statement,
            }
            for row in frozen_inputs(identity, record.blocking_reasons)
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
                "state_key": item.addressed_key,
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
    execution: LabExecutionPort | None = None,
) -> APIRouter:
    """Build the gated router around the injected ports.

    All of them arrive as ports. This module never learns whether templates,
    Sites, or scenarios are files, rows, or objects, it never imports an
    adapter, and it cannot name a kernel: the execution port speaks
    `SimulationRun` in and `LabProjection` out, and both are types the backend is
    allowed to know.

    The Site repository reaches the scenario detail service as well as the
    create service, and that is the only place the two domains meet: a scenario
    declares which Site it needs, and resolving that declaration is a read
    against the Site port. Nothing flows the other way.

    `execution` is optional and its absence is a served state rather than a
    different serving shape. Only the composition leaf can build one - nothing may
    import `host/` - so a build serving this package alone has none, and the four
    execution routes answer `EXECUTION_NOT_COMPOSED`. The route SET stays a
    function of the Lab gate alone, which is what keeps the gate's own test a
    comparison between two states instead of three.
    """
    service = SiteTemplateCatalogService(catalog)
    creation = SiteCreationService(repository, catalog)
    scenario_catalog = ScenarioCatalogService(scenarios)
    scenario_detail = ScenarioDetailService(scenarios, repository)
    run_inventory = RunInventoryService(runs)
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
            # Two facts rather than one. `served` says this build serves the
            # execution surface at all, and `composed` says an execution port is
            # wired behind it - which only the composition leaf can do. A single
            # flag would make a build that serves the controls and cannot execute
            # indistinguishable from one that does neither.
            "run_execution": "served",
            "run_execution_composed": execution is not None,
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

    @router.get(RUNS_ROUTE)
    def list_runs() -> dict[str, object]:
        """Every Draft run setup has written, newest first.

        A store that cannot be read is stated as unavailable rather than
        degraded into "no runs are saved". Those are different facts and an
        inventory must not claim the second when the first is true.
        """
        try:
            records = run_inventory.list_runs()
        except (RunConfigurationInvalid, RunStoreUnavailable) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(REFUSAL_RUN_STORE_UNAVAILABLE, str(error)),
            ) from error

        return {"runs": [run_inventory_row(record) for record in records]}

    @router.get(RUN_DETAIL_ROUTE)
    def read_run(run_id: str) -> dict[str, object]:
        """One Draft by its own identity.

        The requested identity is validated here rather than only inside the
        port, so a malformed identity and an unreadable store cannot arrive
        as the same exception and be reported as the same thing. A malformed
        identity is answered as not found, because no run could ever carry
        it.

        A run that is not there is never another run. The store compares
        identities and this route returns what it answered; there is no
        nearest match and no fallback, because a fallback would put one
        run's frozen identity under another run's name.
        """
        try:
            validate_run_id(run_id)
        except RunConfigurationInvalid as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_RUN_NOT_FOUND,
                    f"No run with run ID {run_id!r} is persisted, and no run "
                    f"could have that ID. {RUN_ID_RULE}",
                ),
            ) from error

        try:
            record = run_inventory.get_run(run_id)
        except RunNotFound as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_RUN_NOT_FOUND,
                    f"No run with run ID {run_id!r} is persisted.",
                ),
            ) from error
        except (RunConfigurationInvalid, RunStoreUnavailable) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(REFUSAL_RUN_STORE_UNAVAILABLE, str(error)),
            ) from error

        return {"run": run_summary(record)}

    # --- Execution ----------------------------------------------------------
    #
    # One read and three controls, behind the Lab gate like everything else on
    # this router. What each of them may NOT do is as much the point as what it
    # does: none of them writes a Site, releases an envelope, stages anything, or
    # commits anything, because no such call exists anywhere in this module and
    # the port has no method that could.

    def _run_or_404(run_id: str) -> SimulationRun:
        """The persisted Draft a control is about, or a typed not-found.

        Shared by all four routes so that an unknown identity is one answer with
        one message rather than four that could drift. Criterion 1's "unknown
        input yields a typed, inspectable outcome" is this, and it is the same
        `RUN_NOT_FOUND` the detail route already answers - a control about a run
        that does not exist is not a new kind of fact.
        """
        try:
            validate_run_id(run_id)
        except RunConfigurationInvalid as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_RUN_NOT_FOUND,
                    f"No run with run ID {run_id!r} is persisted, and no run "
                    f"could have that ID. {RUN_ID_RULE}",
                ),
            ) from error
        try:
            return run_inventory.get_run(run_id)
        except RunNotFound as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_RUN_NOT_FOUND,
                    f"No run with run ID {run_id!r} is persisted.",
                ),
            ) from error
        except (RunConfigurationInvalid, RunStoreUnavailable) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(REFUSAL_RUN_STORE_UNAVAILABLE, str(error)),
            ) from error

    def _port() -> LabExecutionPort:
        """The composed execution port, or a typed answer that there is none.

        Asked BEFORE the run is looked up, and the order is deliberate. A build
        with no port cannot answer any execution question about any run, so
        reading the run store to discover that would be touching a store on
        behalf of a capability this build does not have - the same discipline
        `create_app` uses when it declines to build the run store with the gate
        closed. It also makes the answer a property of the build rather than of
        which identity was asked about.
        """
        if execution is None:
            raise HTTPException(
                status_code=503,
                detail={
                    **_refusal(
                        execution_refusal_code("PORT_NOT_COMPOSED"),
                        LAB_CONTROL_REFUSAL_STATEMENTS[
                            "PORT_NOT_COMPOSED"
                        ],
                    ),
                    "refusal_kind": "PORT_NOT_COMPOSED",
                    "advanced": False,
                },
            )
        return execution

    def _refused(error: LabControlRefused) -> HTTPException:
        """One refused control as a 409, carrying the vocabulary's own statement.

        409 rather than 422, and the difference is worth stating because run setup
        answers 422 beside this. A 422 means the REQUEST was not something that
        could be acted on; every one of these means the request was well formed and
        the RUN is not in a state where it applies. `advanced` is on the body so a
        caller knows nothing moved without having to infer it from the status.

        `detail` carries what only the raising site knew, and it is here because
        its absence lost one. The cadence refusal is about two numbers - a
        signal's rate and this run's timestep - and a per-kind statement cannot
        name them; the exception carrying them used to escape translation
        entirely and arrive as an HTTP 500, so an explanation that had already
        been written never reached anybody. It is appended to the message rather
        than put in a field of its own, because a client that renders the message
        should not have to know there is a second half to look for.
        """
        message = (
            error.statement
            if error.detail is None
            else f"{error.statement} {error.detail}"
        )
        return HTTPException(
            status_code=409,
            detail={
                **_refusal(execution_refusal_code(error.kind), message),
                "refusal_kind": error.kind,
                "subject": error.subject,
                "advanced": False,
            },
        )

    @router.get(RUN_EXECUTION_ROUTE)
    def read_run_execution(run_id: str) -> dict[str, object]:
        """Where this Draft's execution is, without changing it.

        A read, so it takes no token and refuses nothing about the run's state: a
        Draft nothing has executed, one in flight, one that finished, one that
        failed and one whose handle is gone are five answers this returns rather
        than five errors.
        """
        port = _port()
        record = _run_or_404(run_id)
        try:
            projection = port.projection(record)
        except LabControlRefused as error:
            raise _refused(error) from error
        return {"execution": execution_payload(projection)}

    @router.get(RUN_STAGE_ROUTE)
    def read_run_stage(run_id: str) -> dict[str, object]:
        """This Draft's staged source envelopes, re-read and verified.

        A read, served only behind the gate, and the only stage route: nothing
        here edits, deletes, releases or commits a staged envelope.
        """
        port = _port()
        record = _run_or_404(run_id)
        return {"stage": stage_payload(port.staged_envelopes(record))}

    @router.get(RUN_EXECUTION_HISTORY_ROUTE)
    def read_run_execution_history(
        run_id: str, since_boundary: str | None = Query(default=None)
    ) -> dict[str, object]:
        """What this Draft's execution recorded, re-read, never re-executed.

        T025c. A read served only behind the gate. It scans no other run and
        changes no artifact; a run with no recorded history answers with the
        stated reason and no records rather than an error.

        T025e. With `since_boundary=n` it answers only what was recorded after
        the caller's n boundaries, and says so in a sibling `delta` envelope; a
        read without it is unchanged and carries no `delta`.
        """
        port = _port()
        record = _run_or_404(run_id)
        history = port.history(record)
        if since_boundary is None:
            return {"history": history_payload(history, record)}
        since = _parse_since_boundary(since_boundary, history)
        return {
            "history": history_delta_payload(history, since, record),
            "delta": {
                "since_boundary": since,
                "through_boundary": len(history.boundaries),
            },
        }

    @router.post(RUN_EXECUTION_START_ROUTE)
    def start_run_execution(run_id: str) -> dict[str, object]:
        """Begin an execution of an eligible frozen Draft."""
        port = _port()
        record = _run_or_404(run_id)
        try:
            projection = port.start(record)
        except LabControlRefused as error:
            raise _refused(error) from error
        return {"execution": execution_payload(projection)}

    @router.post(RUN_EXECUTION_STEP_ROUTE)
    def step_run_execution(
        run_id: str, request: Any = Body(default=None)
    ) -> dict[str, object]:
        """Advance a started execution by a requested number of boundaries.

        The body carries `boundaries` and `from_boundary`, and the second is what
        makes the control safe to resubmit. It is not a nonce and not a timestamp:
        it is the position the caller believes the run is at, which a caller
        already knows because the projection it is looking at says so.
        """
        port = _port()
        record = _run_or_404(run_id)
        boundaries, from_boundary = _parse_step_request(request)
        try:
            projection = port.step(
                record, boundaries=boundaries, from_boundary=from_boundary
            )
        except LabControlRefused as error:
            raise _refused(error) from error
        return {"execution": execution_payload(projection)}

    @router.post(RUN_EXECUTION_END_ROUTE)
    def run_execution_to_end(run_id: str) -> dict[str, object]:
        """Advance a started execution until its interval is covered."""
        port = _port()
        record = _run_or_404(run_id)
        try:
            projection = port.run_to_end(record)
        except LabControlRefused as error:
            raise _refused(error) from error
        return {"execution": execution_payload(projection)}

    return router


def _parse_step_request(request: Any) -> tuple[int, int]:
    """The two whole numbers a step request carries, or a typed refusal.

    Strict, like every other request parser here: an unknown key, a missing one, a
    non-integer and a boolean are all refused rather than coerced. `True` is an
    `int` in Python and would otherwise arrive as a request to advance one
    boundary, which is a request nobody made.
    """
    if not isinstance(request, dict):
        raise HTTPException(
            status_code=422,
            detail=_refusal(
                REFUSAL_EXECUTION_REQUEST_INVALID,
                "A step request is an object carrying 'boundaries' and "
                "'from_boundary'. Nothing was advanced.",
            ),
        )
    unknown = sorted(set(request) - {"boundaries", "from_boundary"})
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=_refusal(
                REFUSAL_EXECUTION_REQUEST_INVALID,
                f"A step request carries 'boundaries' and 'from_boundary' and "
                f"nothing else; this one also carries {unknown}. Nothing was "
                "advanced.",
            ),
        )
    values: list[int] = []
    for field, floor in (("boundaries", 1), ("from_boundary", 0)):
        value = request.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise HTTPException(
                status_code=422,
                detail=_refusal(
                    REFUSAL_EXECUTION_REQUEST_INVALID,
                    f"A step request's {field!r} is a whole number and this one "
                    f"is {value!r}. Nothing was advanced.",
                ),
            )
        if value < floor:
            raise HTTPException(
                status_code=422,
                detail=_refusal(
                    REFUSAL_EXECUTION_REQUEST_INVALID,
                    f"A step request's {field!r} is at least {floor} and this "
                    f"one is {value}. Nothing was advanced.",
                ),
            )
        values.append(value)
    return values[0], values[1]
