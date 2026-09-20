import type {
  ScenarioDetail,
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
 * matters in two ways the tests depend on:
 *
 * - it uses every proposed category and every proposed timeline kind, which is
 *   what makes the legend assertion non-vacuous. A legend that covered only
 *   what a two-row fixture used would pass while telling the reviewer nothing;
 * - its digits are distinctive, so a test can collect every digit the screen
 *   renders and check each one back against the record.
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

export const SCENARIO_DETAIL: ScenarioDetail = {
  ...SCENARIO_SUMMARY,
  public_parameters: [
    {
      parameter_id: "tank-capacity",
      display_name: "Fuel tank capacity the scenario assumes",
      value: 500,
      unit: "L",
    },
    {
      parameter_id: "observed-signal",
      display_name: "Signal the scenario expects to carry the story",
      value: "fuel-level, from the fuel level sensor on the fuel tank",
      unit: null,
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
      parameters: [
        {
          parameter_id: "evening-peak-load",
          display_name: "Evening peak demand",
          value: 72,
          unit: "kW",
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
      parameters: [],
    },
    {
      event_id: "generator-run-window",
      sequence: 3,
      offset_minutes: 1080,
      entry_kind: "EVENT",
      category: "EQUIPMENT",
      description: "The generator is dispatched to cover the evening peak.",
      parameters: [
        {
          parameter_id: "run-window-length",
          display_name: "Length of the dispatch window",
          value: 240,
          unit: "min",
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
      parameters: [
        {
          parameter_id: "volume-removed",
          display_name: "Volume removed",
          value: 120,
          unit: "L",
        },
      ],
    },
    {
      event_id: "fuel-level-reporting-gap",
      sequence: 5,
      offset_minutes: 1490,
      entry_kind: "EVENT",
      category: "DATA_QUALITY",
      description: "The fuel level sensor reports nothing for a while.",
      parameters: [],
    },
    {
      event_id: "fuel-level-after-the-gap",
      sequence: 6,
      offset_minutes: 1590,
      entry_kind: "EVIDENCE_CONDITION",
      category: "LOSS_OR_FRAUD",
      description: "Reporting resumes far below what dispatch accounts for.",
      parameters: [],
    },
    {
      event_id: "operator-tank-inspection",
      sequence: 7,
      offset_minutes: 1800,
      entry_kind: "INTERVENTION",
      category: "INTERVENTION",
      description: "An operator records the level by hand.",
      parameters: [],
    },
    {
      event_id: "scheduled-refuelling",
      sequence: 8,
      offset_minutes: 2400,
      entry_kind: "EVENT",
      category: "MAINTENANCE",
      description: "The scheduled delivery tops the tank up.",
      parameters: [],
    },
  ],
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
  resolution: ScenarioTargetResolution = RESOLVED_TARGET,
): string[] {
  const rendered: string[] = [
    SCENARIO_DETAIL.display_name,
    SCENARIO_DETAIL.origin,
    SCENARIO_DETAIL.purpose,
    SCENARIO_DETAIL.scenario_id,
    String(SCENARIO_DETAIL.version.scenario_version),
    SCENARIO_DETAIL.version.version_valid_from,
    SCENARIO_DETAIL.target_site.policy,
    SCENARIO_DETAIL.target_site.requirement,
    resolution.reason,
  ];

  rendered.push(
    SCENARIO_DETAIL.version.supersedes === null
      ? "No earlier version"
      : String(SCENARIO_DETAIL.version.supersedes),
  );
  rendered.push(SCENARIO_DETAIL.target_site.site_id ?? "None declared");
  rendered.push(SCENARIO_DETAIL.target_site.template_id ?? "None declared");

  for (const parameter of SCENARIO_DETAIL.public_parameters) {
    rendered.push(
      parameter.display_name,
      parameterValue(parameter),
      parameter.parameter_id,
    );
  }

  for (const entry of SCENARIO_DETAIL.timeline) {
    rendered.push(
      String(entry.sequence),
      String(entry.offset_minutes),
      entry.entry_kind,
      entry.category,
      entry.description,
      entry.event_id,
    );
    for (const parameter of entry.parameters) {
      rendered.push(parameter.display_name, parameterValue(parameter));
    }
  }

  for (const expectation of PRIVATE_EXPECTATIONS) {
    rendered.push(
      expectation.display_name,
      expectation.oracle_kind,
      expectation.statement,
    );
  }

  return rendered;
}
