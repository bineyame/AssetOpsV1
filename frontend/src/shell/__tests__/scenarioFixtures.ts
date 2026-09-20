import type {
  ScenarioDetail,
  ScenarioObservationSourceResolution,
  ScenarioParameter,
  ScenarioPrivateExpectation,
  ScenarioSummary,
  ScenarioTargetResolution,
} from "../scenarioCatalogClient";

/**
 * A scenario record shaped like the shipped Fuel Loss Event.
 *
 * Deliberately built here rather than fetched, so a UI assertion is about what
 * the screen renders from a record and not about network timing. Its shape
 * matters in three ways the tests depend on:
 *
 * - it uses every category, every timeline kind and every execution role,
 *   which is what makes the legend assertions non-vacuous. A legend that
 *   covered only what a two-row fixture used would pass while telling the
 *   reviewer nothing;
 * - its digits are distinctive, so a test can collect every digit the screen
 *   renders and check each one back against the record;
 * - its reconciliation does not balance, exactly as the shipped definition's
 *   does not, because the screen's whole job in that panel is to render a
 *   difference rather than hide one.
 */

export const SCENARIO_SUMMARY: ScenarioSummary = {
  scenario_id: "fuel-loss-event",
  display_name: "Fuel Loss Event",
  purpose:
    "Exercise the path from an unaccounted fuel removal through to the " +
    "evidence a later analysis would have to work from.",
  origin: "SHIPPED",
  version: {
    scenario_version: 3,
    version_valid_from: "2026-09-20T00:00:00Z",
    supersedes: 2,
  },
  target_site: {
    policy: "DECLARED_SITE",
    site_id: "MG-001",
    template_id: null,
    requirement:
      "A mini-grid whose foundation declares a fuel-storage component " +
      "feeding a generator.",
  },
};

function causal(
  parameter_id: string,
  display_name: string,
  value: number,
  unit: string,
  canonicalValue: number,
  canonicalUnit: string,
  dimension: string,
  initializes: boolean,
  owner = "SCENARIO_INPUT",
  state_key = "fuel-tank-volume",
  bounds: ScenarioParameter["bounds"] = null,
): ScenarioParameter {
  return {
    parameter_id,
    display_name,
    value,
    unit,
    execution_role: "CAUSAL_INPUT",
    state_key,
    execution_requirement: "REQUIRED",
    ownership: { owner, initializes },
    bounds: bounds ?? null,
    canonical: {
      value: canonicalValue,
      unit: canonicalUnit,
      dimension,
    },
  };
}

function reported(
  parameter_id: string,
  display_name: string,
  value: number,
): ScenarioParameter {
  return {
    parameter_id,
    display_name,
    value,
    unit: "L",
    execution_role: "REPORTED_OBSERVATION",
    state_key: "fuel-tank-volume",
    execution_requirement: "REQUIRED",
    ownership: null,
    bounds: null,
    canonical: { value, unit: "L", dimension: "VOLUME" },
  };
}

export const SCENARIO_DETAIL: ScenarioDetail = {
  ...SCENARIO_SUMMARY,
  public_parameters: [
    causal(
      "tank-capacity",
      "Fuel tank capacity the scenario assumes",
      500,
      "L",
      500,
      "L",
      "VOLUME",
      true,
      "SITE_FOUNDATION",
      "fuel-tank-capacity",
      { state_key: "fuel-tank-volume", bound_kind: "UPPER" },
    ),
    causal(
      "starting-fuel-level",
      "Fuel level at the start of the interval",
      430,
      "L",
      430,
      "L",
      "VOLUME",
      true,
    ),
    {
      parameter_id: "generator-fuel-rate",
      display_name: "Generator fuel consumption while dispatched",
      value: 14,
      unit: "L/h",
      execution_role: "CAUSAL_INPUT",
      state_key: "fuel-tank-volume",
      execution_requirement: "REQUIRED",
      ownership: { owner: "SCENARIO_INPUT", initializes: false },
      bounds: null,
      canonical: {
        value: 0.23333333333333334,
        unit: "L/min",
        dimension: "VOLUME_RATE",
      },
    },
    {
      // A text parameter, which the shipped definition no longer carries: its
      // signal identity moved into `observation_sources` where it is
      // machine-readable. The branch still exists in the parser and on the
      // screen, so the fixture keeps exercising it.
      parameter_id: "observed-signal",
      display_name: "Signal the scenario expects to carry the story",
      value: "fuel-level, from the fuel level sensor on the fuel tank",
      unit: null,
      execution_role: "NON_EXECUTABLE_CONDITION",
      state_key: null,
      execution_requirement: null,
      ownership: null,
      bounds: null,
      canonical: null,
    },
  ],
  observation_sources: [
    {
      source_id: "fuel-level-sensor-reading",
      source_kind: "DEVICE_SIGNAL",
      device_id: "fuel-level-sensor",
      signal_id: "fuel-level",
      cadence_ownership: "NOT_DECLARED",
      description: "The sensor configured on the fuel tank.",
    },
    {
      source_id: "operator-hand-record",
      source_kind: "OPERATOR_RECORD",
      device_id: null,
      signal_id: null,
      cadence_ownership: "NOT_APPLICABLE",
      description: "A site operator writing the level down.",
    },
  ],
  timeline: [
    {
      event_id: "baseline-load-profile",
      sequence: 1,
      offset_minutes: 0,
      entry_kind: "EVENT",
      category: "LOAD",
      description: "Demand follows the site's ordinary weekday shape.",
      execution_role: "FORCING_INPUT",
      state_key: "site-load-demand",
      execution_requirement: "REQUIRED",
      timing: { shape: "INTERVAL_WIDE", duration_minutes: null },
      state_effect: null,
      observation: null,
      parameters: [
        {
          parameter_id: "evening-peak-load",
          display_name: "Evening peak demand",
          value: 72,
          unit: "kW",
          execution_role: "FORCING_INPUT",
          state_key: "site-load-demand",
          execution_requirement: "REQUIRED",
          ownership: { owner: "SCENARIO_INPUT", initializes: false },
          bounds: null,
          canonical: { value: 72, unit: "kW", dimension: "POWER" },
        },
      ],
    },
    {
      event_id: "overcast-day",
      sequence: 2,
      offset_minutes: 720,
      entry_kind: "EVENT",
      category: "WEATHER",
      description: "Irradiance stays well below a clear-sky day.",
      execution_role: "FORCING_INPUT",
      state_key: "plane-of-array-irradiance",
      execution_requirement: "REQUIRED",
      timing: { shape: "WINDOW", duration_minutes: 360 },
      state_effect: null,
      observation: null,
      parameters: [],
    },
    {
      event_id: "generator-run-window",
      sequence: 3,
      offset_minutes: 1080,
      entry_kind: "EVENT",
      category: "EQUIPMENT",
      description: "The generator is dispatched to cover the evening peak.",
      execution_role: "CAUSAL_INPUT",
      state_key: "fuel-tank-volume",
      execution_requirement: "REQUIRED",
      timing: { shape: "WINDOW", duration_minutes: 240 },
      state_effect: {
        direction: "DECREASE",
        quantity_parameter_id: null,
        rate_parameter_id: "generator-fuel-rate",
      },
      observation: null,
      parameters: [
        {
          parameter_id: "dispatched-output",
          display_name: "Generator output while dispatched",
          value: 45,
          unit: "kW",
          execution_role: "NON_EXECUTABLE_CONDITION",
          state_key: null,
          execution_requirement: null,
          ownership: null,
          bounds: null,
          canonical: { value: 45, unit: "kW", dimension: "POWER" },
        },
      ],
    },
    {
      event_id: "unaccounted-fuel-removal",
      sequence: 4,
      offset_minutes: 1500,
      entry_kind: "EVENT",
      category: "LOSS_OR_FRAUD",
      description: "Fuel leaves the tank outside any dispatch window.",
      execution_role: "CAUSAL_INPUT",
      state_key: "fuel-tank-volume",
      execution_requirement: "REQUIRED",
      timing: { shape: "WINDOW", duration_minutes: 45 },
      state_effect: {
        direction: "DECREASE",
        quantity_parameter_id: "volume-removed",
        rate_parameter_id: null,
      },
      observation: null,
      parameters: [
        causal(
          "volume-removed",
          "Volume removed",
          120,
          "L",
          120,
          "L",
          "VOLUME",
          false,
        ),
      ],
    },
    {
      event_id: "fuel-level-reporting-gap",
      sequence: 5,
      offset_minutes: 1490,
      entry_kind: "EVENT",
      category: "DATA_QUALITY",
      description: "The fuel level sensor reports nothing for a while.",
      execution_role: "FORCING_INPUT",
      state_key: "fuel-level-reporting-availability",
      execution_requirement: "REQUIRED",
      timing: { shape: "WINDOW", duration_minutes: 90 },
      state_effect: null,
      observation: null,
      parameters: [],
    },
    {
      event_id: "fuel-level-after-the-gap",
      sequence: 6,
      offset_minutes: 1590,
      entry_kind: "EVIDENCE_CONDITION",
      category: "LOSS_OR_FRAUD",
      description: "Reporting resumes far below what dispatch accounts for.",
      execution_role: "REPORTED_OBSERVATION",
      state_key: "fuel-tank-volume",
      execution_requirement: "REQUIRED",
      timing: { shape: "POINT", duration_minutes: null },
      state_effect: null,
      observation: {
        source_id: "fuel-level-sensor-reading",
        reported_parameter_id: "level-after-the-gap",
      },
      parameters: [
        reported(
          "level-after-the-gap",
          "Fuel level when reporting resumes",
          155,
        ),
      ],
    },
    {
      event_id: "operator-tank-inspection",
      sequence: 7,
      offset_minutes: 1800,
      entry_kind: "INTERVENTION",
      category: "INTERVENTION",
      description: "An operator records the level by hand.",
      execution_role: "REPORTED_OBSERVATION",
      state_key: "fuel-tank-volume",
      execution_requirement: "REQUIRED",
      timing: { shape: "POINT", duration_minutes: null },
      state_effect: null,
      observation: {
        source_id: "operator-hand-record",
        reported_parameter_id: "hand-recorded-level",
      },
      parameters: [
        reported("hand-recorded-level", "Level the operator records", 150),
      ],
    },
    {
      event_id: "scheduled-refuelling",
      sequence: 8,
      offset_minutes: 2400,
      entry_kind: "EVENT",
      category: "MAINTENANCE",
      description: "The scheduled delivery tops the tank up.",
      execution_role: "CAUSAL_INPUT",
      state_key: "fuel-tank-volume",
      execution_requirement: "REQUIRED",
      timing: { shape: "POINT", duration_minutes: null },
      state_effect: {
        direction: "INCREASE",
        quantity_parameter_id: "volume-delivered",
        rate_parameter_id: null,
      },
      observation: null,
      parameters: [
        causal(
          "volume-delivered",
          "Volume delivered",
          300,
          "L",
          300,
          "L",
          "VOLUME",
          false,
        ),
      ],
    },
  ],
  execution_contract: {
    contract_version: 1,
    dispatch_rules: [
      {
        rule_id: "half-open-interval",
        display_name: "Half-open interval and steps",
        statement:
          "An instant belongs to exactly one step, so applying something " +
          "once is a property of the time model.",
      },
      {
        rule_id: "point-applied-once",
        display_name: "A point applies once",
        statement:
          "An offset on a step boundary belongs to the step that begins " +
          "there and never to the step that ends there.",
      },
      {
        rule_id: "window-active-span",
        display_name: "A window's active span",
        statement:
          "The step beginning exactly at the end of a window is outside it.",
      },
    ],
    bound_cases: [
      {
        case_id: "fuel-tank-capacity",
        display_name: "Tank capacity",
        policy: "BOUNDED_AND_RECORDED",
        statement:
          "A change that would take the stored volume above capacity fills " +
          "to capacity and records the volume it could not accept.",
      },
      {
        case_id: "insufficient-fuel",
        display_name: "Insufficient fuel",
        policy: "FAIL_RUN",
        statement:
          "The run stops and names the entry rather than emptying the tank " +
          "quietly.",
      },
      {
        case_id: "invalid-rate",
        display_name: "Invalid rate or quantity",
        policy: "REFUSED_AT_PARSE",
        statement:
          "Refused when the definition is read, so no run setup and no " +
          "kernel ever sees one.",
      },
    ],
    initialization_inputs: [
      {
        parameter_id: "tank-capacity",
        display_name: "Fuel tank capacity the scenario assumes",
        state_key: "fuel-tank-capacity",
        owner: "SITE_FOUNDATION",
        value: 500,
        unit: "L",
        canonical_value: 500,
        canonical_unit: "L",
      },
      {
        parameter_id: "starting-fuel-level",
        display_name: "Fuel level at the start of the interval",
        state_key: "fuel-tank-volume",
        owner: "SCENARIO_INPUT",
        value: 430,
        unit: "L",
        canonical_value: 430,
        canonical_unit: "L",
      },
    ],
    observation_reconciliation: [
      {
        event_id: "fuel-level-after-the-gap",
        source_id: "fuel-level-sensor-reading",
        parameter_id: "level-after-the-gap",
        state_key: "fuel-tank-volume",
        offset_minutes: 1590,
        reported_value: 155,
        declared_value: 254,
        difference: -99,
        unit: "L",
        state: "NOT_ACCOUNTED_FOR",
        reason:
          "the causes declared before this reading do not reach the value " +
          "it reports, and no declared cause accounts for the difference",
        accounted_by: ["generator-run-window", "unaccounted-fuel-removal"],
      },
      {
        event_id: "operator-tank-inspection",
        source_id: "operator-hand-record",
        parameter_id: "hand-recorded-level",
        state_key: "fuel-tank-volume",
        offset_minutes: 1800,
        reported_value: 150,
        declared_value: 254,
        difference: -104,
        unit: "L",
        state: "NOT_ACCOUNTED_FOR",
        reason:
          "the causes declared before this reading do not reach the value " +
          "it reports, and no declared cause accounts for the difference",
        accounted_by: ["generator-run-window", "unaccounted-fuel-removal"],
      },
    ],
  },
};

export const PRIVATE_EXPECTATIONS: ScenarioPrivateExpectation[] = [
  {
    expectation_id: "removal-is-separable-from-consumption",
    display_name: "The removal is separable from ordinary consumption",
    oracle_kind: "DETECTION",
    statement:
      "A later analysis must separate the unaccounted removal from the fuel " +
      "the dispatch window legitimately consumed.",
  },
];

export const OBSERVATION_SOURCE_RESOLUTIONS: ScenarioObservationSourceResolution[] =
  [
    {
      source_id: "fuel-level-sensor-reading",
      state: "RESOLVED",
      device_display_name: "Fuel level sensor",
      signal_display_name: "Fuel level",
      reason:
        "The device fuel-level-sensor the site configures declares the " +
        "signal fuel-level this source reports through.",
      cadence_statement:
        "The site's foundation declares that this signal can report and " +
        "declares no cadence.",
    },
    {
      source_id: "operator-hand-record",
      state: "NOT_APPLICABLE",
      device_display_name: null,
      signal_display_name: null,
      reason:
        "This source is a person recording a value, so there is no " +
        "configured device or signal for it to resolve to.",
      cadence_statement:
        "A person writing a value down reports at no rate, so there is no " +
        "cadence for anything to own.",
    },
  ];

export const RESOLVED_TARGET: ScenarioTargetResolution = {
  state: "RESOLVED",
  site_id: "MG-001",
  display_name: "Kalangala Mini-Grid",
  reason: "The site MG-001 this scenario targets is configured.",
};

export const UNCONFIGURED_TARGET: ScenarioTargetResolution = {
  state: "NOT_CONFIGURED",
  site_id: null,
  display_name: null,
  reason:
    "No site with site ID MG-001 is configured, so the site this scenario " +
    "targets cannot be opened.",
};

export const UNAVAILABLE_TARGET: ScenarioTargetResolution = {
  state: "UNAVAILABLE",
  site_id: null,
  display_name: null,
  reason:
    "The site store could not be read, so whether the site MG-001 is " +
    "configured is unknown.",
};

export const NOT_APPLICABLE_TARGET: ScenarioTargetResolution = {
  state: "NOT_APPLICABLE",
  site_id: null,
  display_name: null,
  reason:
    "This scenario names the kind of site it needs rather than a configured " +
    "site, so there is no site to open.",
};

/**
 * How a parameter reads on screen. The screen's own rule, restated here so the
 * expectation is built from the record rather than read back off the DOM.
 */
function parameterValue(parameter: ScenarioParameter): string {
  return parameter.unit === null
    ? String(parameter.value)
    : `${parameter.value} ${parameter.unit}`;
}

function canonicalValueText(parameter: ScenarioParameter): string {
  return parameter.canonical === null
    ? "Not a quantity"
    : `${parameter.canonical.value} ${parameter.canonical.unit}`;
}

function ownershipText(parameter: ScenarioParameter): string {
  if (parameter.ownership === null) {
    return parameter.execution_role === "REPORTED_OBSERVATION"
      ? "Reported, so it owns nothing"
      : "Not consumed, so it owns nothing";
  }
  return parameter.ownership.initializes
    ? `${parameter.ownership.owner}, starting value`
    : `${parameter.ownership.owner}, used by a change`;
}

/**
 * Every string the scenario detail screen renders FROM THE RECORD, as the
 * screen renders it: one entry per rendered leaf, not per field.
 *
 * This replaces the digit-run comparison the T017 review rejected. That one
 * asked whether each digit run on the screen appeared anywhere in the record,
 * which an invented `7` satisfies as soon as any sequence number is 7. The
 * follow-up - remove the containers that hold record values, then ban digits
 * in what is left - was rejected for the complementary reason: those
 * containers hold authored text too, so a static digit inside a table heading
 * was carved out wholesale.
 *
 * The claim that is actually checkable is at leaf level: a text node on this
 * screen either equals one of these strings, or it contains no digit at all. A
 * heading is authored, so it may not carry a digit; a value is record-backed,
 * so it must match exactly. An invented digit has nowhere to be either.
 *
 * The list is asserted in both directions, so it cannot be padded: every entry
 * here that contains a digit must actually appear on the screen.
 */
export function recordRenderedStrings(
  detail: ScenarioDetail = SCENARIO_DETAIL,
  resolution: ScenarioTargetResolution = RESOLVED_TARGET,
  expectations: ScenarioPrivateExpectation[] = PRIVATE_EXPECTATIONS,
  sources: ScenarioObservationSourceResolution[] = OBSERVATION_SOURCE_RESOLUTIONS,
): string[] {
  const rendered: string[] = [
    detail.display_name,
    detail.origin,
    detail.purpose,
    detail.scenario_id,
    String(detail.version.scenario_version),
    detail.version.version_valid_from,
    detail.target_site.policy,
    detail.target_site.requirement,
    resolution.reason,
  ];

  rendered.push(
    detail.version.supersedes === null
      ? "No earlier version"
      : String(detail.version.supersedes),
  );
  rendered.push(detail.target_site.site_id ?? "None declared");
  rendered.push(detail.target_site.template_id ?? "None declared");

  for (const parameter of detail.public_parameters) {
    rendered.push(
      parameter.display_name,
      parameterValue(parameter),
      canonicalValueText(parameter),
      parameter.execution_role,
      parameter.state_key ?? "Not consumed",
      ownershipText(parameter),
      parameter.parameter_id,
    );
  }

  for (const source of detail.observation_sources) {
    const match = sources.find((item) => item.source_id === source.source_id);
    rendered.push(
      source.source_id,
      source.description,
      source.source_kind,
      source.cadence_ownership,
    );
    rendered.push(
      source.device_id === null
        ? "No device"
        : match?.device_display_name == null
          ? source.device_id
          : `${source.device_id}, ${match.device_display_name}`,
    );
    rendered.push(
      source.signal_id === null
        ? "No signal"
        : match?.signal_display_name == null
          ? source.signal_id
          : `${source.signal_id}, ${match.signal_display_name}`,
    );
    if (match !== undefined) {
      rendered.push(match.reason, match.cadence_statement);
    } else {
      rendered.push(
        "Nothing is known about this source on this installation.",
        "No statement about this source's cadence is available.",
      );
    }
  }

  for (const entry of detail.timeline) {
    rendered.push(
      String(entry.sequence),
      String(entry.offset_minutes),
      entry.timing.shape,
      entry.entry_kind,
      entry.category,
      entry.execution_role,
      executionDetail(entry),
      entry.description,
      entry.event_id,
    );
    if (entry.timing.duration_minutes !== null) {
      rendered.push(`${entry.timing.duration_minutes} min`);
    }
    if (entry.parameters.length === 0) {
      rendered.push("None declared");
    }
    for (const parameter of entry.parameters) {
      // The cell renders these as separate text nodes, so they are separate
      // leaves: `{display_name}: {value}` puts the colon in a node of its own.
      rendered.push(
        parameter.display_name,
        parameterValue(parameter),
        parameter.execution_role,
      );
    }
  }

  for (const input of detail.execution_contract.initialization_inputs) {
    rendered.push(
      input.state_key,
      `${input.value} ${input.unit}`,
      `${input.canonical_value} ${input.canonical_unit}`,
      input.owner,
      input.display_name,
    );
  }

  rendered.push(String(detail.execution_contract.contract_version));

  for (const rule of detail.execution_contract.dispatch_rules) {
    rendered.push(rule.display_name, rule.statement);
  }

  for (const boundCase of detail.execution_contract.bound_cases) {
    rendered.push(
      boundCase.display_name,
      boundCase.policy,
      boundCase.statement,
    );
  }

  for (const item of detail.execution_contract.observation_reconciliation) {
    rendered.push(
      item.event_id,
      item.source_id,
      String(item.offset_minutes),
      `${item.reported_value} ${item.unit}`,
      item.declared_value === null
        ? "Cannot be worked out"
        : `${item.declared_value} ${item.unit}`,
      item.difference === null
        ? "Cannot be worked out"
        : `${item.difference} ${item.unit}`,
      item.state,
      item.reason,
      item.accounted_by.length === 0
        ? "no declared cause is complete by this offset"
        : `counting ${item.accounted_by.join(", ")}`,
    );
  }

  for (const expectation of expectations) {
    rendered.push(
      expectation.display_name,
      expectation.oracle_kind,
      expectation.statement,
    );
  }

  return rendered;
}

/** The screen's own rule for the second line of the execution-role cell. */
function executionDetail(entry: ScenarioDetail["timeline"][number]): string {
  if (entry.state_effect !== null && entry.state_key !== null) {
    const direction =
      entry.state_effect.direction === "INCREASE" ? "raises" : "lowers";
    return `${direction} ${entry.state_key}`;
  }
  if (entry.observation !== null) {
    return `reported through ${entry.observation.source_id}`;
  }
  if (entry.state_key !== null) {
    return `forces ${entry.state_key}`;
  }
  return "not consumed by an executor";
}

/**
 * The same screen, on a record that takes every authored fallback branch.
 *
 * Without this the fallbacks are dead code in every test. Proving the digit
 * rule on the loaded record only was not enough: a deliberate digit inserted
 * into the "No earlier version" fallback PASSED, because this fixture's
 * `supersedes` is set and that branch never rendered. Authored text that no
 * test renders is authored text no assertion covers.
 *
 * It carries no digit anywhere, on purpose. The screen's own fallbacks must
 * not introduce one, and the digit assertion over this record is what says so.
 */
export const SCENARIO_DETAIL_FALLBACKS: ScenarioDetail = {
  ...SCENARIO_DETAIL,
  version: {
    scenario_version: SCENARIO_DETAIL.version.scenario_version,
    version_valid_from: SCENARIO_DETAIL.version.version_valid_from,
    supersedes: null,
  },
  target_site: {
    policy: "TEMPLATE_DERIVED",
    site_id: null,
    template_id: "hybrid-mini-grid",
    requirement: "A site built from the hybrid mini-grid archetype.",
  },
  public_parameters: [],
  observation_sources: [],
  timeline: SCENARIO_DETAIL.timeline.map((entry) => ({
    ...entry,
    parameters: [],
  })),
  execution_contract: {
    ...SCENARIO_DETAIL.execution_contract,
    initialization_inputs: [],
    observation_reconciliation: [],
  },
};
