/**
 * The W1 answer cards that lead the three stored Foundation views (W1-UX-05,
 * `D-2026-10-16-w1-ux`): Site model ("What is configured?"), Readiness ("What
 * needs connecting or confirming?") and Single line diagram ("How is the site
 * connected, and which parts can report?").
 *
 * Each card answers only to the strength of the selected Foundation read:
 * configuration is never operation, a linked reading channel is never a
 * reporting one, and set-up readiness is never shown as a positive state. The
 * plain state line, its scope (with the precise selected time) and the "as of"
 * bound stay outside the closed exact-reference disclosure, which holds the
 * record references and raw status basis only.
 */

import { Link } from "react-router-dom";

import {
  ExactReferences,
  HeadlineVisualCard,
  ProductStatus,
  StepStrip,
  UNRECOGNISED_SENTENCE,
  ValueBars,
  plainTime,
  type ProductWords,
  type Step,
  type ValueBarItem,
} from "../ui";
import type { FoundationReadModel } from "./siteFoundationClient";
import { readinessCards } from "./ReadinessOverview";
import type { SiteDetailReadModel } from "./siteReadModel";

/* Words owned by the Foundation domain ------------------------------------- */

/**
 * The selected period in plain words. Configuration recorded for a period is
 * never a positive claim about the site, so no period state is `positive`.
 */
export function foundationPeriodWords(foundation: FoundationReadModel): ProductWords {
  const code = foundation.revision.period_state;
  const gaps = foundation.configuration_gaps.length;
  if (foundation.configuration_gaps.some((gap) => gap.code === "NO_EFFECTIVE_REVISION")) {
    return {
      label: "No configuration for this period",
      sentence: "No Foundation version is in effect at the selected time, so nothing is shown as configured.",
      tone: "limited",
      code: "NO_EFFECTIVE_REVISION",
      unrecognised: false,
    };
  }
  const base: Record<string, Omit<ProductWords, "code" | "unrecognised">> = {
    CURRENT: {
      label: "Configuration in effect now",
      sentence: "These are the recorded equipment ratings and settings for the selected time, not measured operation.",
      tone: "neutral",
    },
    PAST: {
      label: "Earlier configuration",
      sentence: "This period has ended. It shows what was recorded then, not what is in effect now.",
      tone: "neutral",
    },
    FUTURE: {
      label: "Scheduled configuration",
      sentence: "This period has not started. It shows what is recorded to take effect, not what is in effect now.",
      tone: "waiting",
    },
  };
  const known = base[code];
  if (known === undefined) {
    return { label: "Period not recognised", sentence: UNRECOGNISED_SENTENCE, tone: "limited", code, unrecognised: true };
  }
  if (gaps > 0) {
    return {
      label: `${known.label}, incomplete`,
      sentence: `${known.sentence} ${gaps === 1 ? "One item is" : `${gaps} items are`} missing from it.`,
      next: "See what is missing in Readiness.",
      tone: "limited",
      code,
      unrecognised: false,
    };
  }
  return { ...known, code, unrecognised: false };
}

/**
 * Set-up readiness in plain words. "Set up to report" is configuration only:
 * it never says a device is connected or reporting, so it is not `positive`.
 */
export function setupReadinessWords(state: string | null | undefined): ProductWords {
  switch (state) {
    case "READY_TO_REPORT":
      return {
        label: "Set up to report",
        sentence:
          "Every required reading has a configured channel. This does not mean any device is connected, reporting or healthy.",
        tone: "neutral",
        code: state,
        unrecognised: false,
      };
    case "INCOMPLETE":
      return {
        label: "Set-up incomplete",
        sentence: "Some required readings or settings are not set up for the period shown.",
        next: "Work through the next steps below.",
        tone: "limited",
        code: state,
        unrecognised: false,
      };
    case "UNKNOWN":
      return {
        label: "Set-up cannot be judged",
        sentence: "No set of linked reading channels is in effect for the period shown, so readiness is not known.",
        next: "Link the reading channels for this period.",
        tone: "limited",
        code: state,
        unrecognised: false,
      };
    default:
      return {
        label: "Set-up state not recognised",
        sentence: UNRECOGNISED_SENTENCE,
        tone: "limited",
        code: state ?? "",
        unrecognised: true,
      };
  }
}

/* Shared pieces -------------------------------------------------------------- */

function scopeOf(foundation: FoundationReadModel): string {
  const at = plainTime(foundation.resolved.at);
  return `${foundation.site.display_name} · Foundation version ${foundation.revision.version}, selected time ${at ?? "not recorded"}`;
}

/** The labelled exact references every Foundation card may need. */
function recordReferences(foundation: FoundationReadModel) {
  return [
    { label: "Selected time (exact)", value: foundation.resolved.at },
    { label: "Foundation version record", value: foundation.revision.revision_id },
    { label: "Foundation content reference", value: foundation.revision.content_sha256 },
    { label: "Reading-channel set record", value: foundation.bindings.binding_set?.binding_set_revision_id ?? null },
  ];
}

const KIND_WORDS: Record<string, string> = {
  PV_ARRAY: "Solar arrays",
  INVERTER: "Inverters",
  BATTERY: "Batteries",
  POWER_CONVERSION_SYSTEM: "Battery power converters",
  GENERATOR: "Generators",
  FUEL_TANK: "Fuel tanks",
  LOAD: "Supplied users",
  COLD_ROOM: "Cold rooms",
  METER: "Meters",
};

const KIND_ORDER = Object.keys(KIND_WORDS);

function equipmentByKind(site: SiteDetailReadModel): ValueBarItem[] {
  const counts = new Map<string, number>();
  for (const component of site.foundation.components) {
    if (component.component_type === "AC_BUS") continue;
    const kind = component.component_type in KIND_WORDS ? component.component_type : "OTHER";
    counts.set(kind, (counts.get(kind) ?? 0) + 1);
  }
  return [...KIND_ORDER, "OTHER"]
    .filter((kind) => counts.has(kind))
    .map((kind) => {
      const n = counts.get(kind) ?? 0;
      return { key: kind, label: KIND_WORDS[kind] ?? "Other equipment", value: n, valueText: String(n) };
    });
}

const SETTING_LABELS: Record<keyof FoundationReadModel["controls"], string> = {
  battery_reserve: "Battery reserve",
  generator_start_stop: "Generator start and stop",
  generator_minimum_runtime: "Shortest generator operation",
  source_priority: "Supply order",
  critical_load_priority: "Critical service order",
};

function settingSteps(foundation: FoundationReadModel): Step[] {
  return (Object.keys(SETTING_LABELS) as (keyof FoundationReadModel["controls"])[]).map((key) => {
    const control = foundation.controls[key];
    const recorded = control.state === "CONFIGURED" || control.state === "DECLARED";
    return {
      label: SETTING_LABELS[key],
      state: recorded ? "done" : control.state === "NOT_CONFIGURED" ? "waiting" : "not-known",
      detail: recorded ? "Recorded" : control.state === "NOT_CONFIGURED" ? "Not recorded" : "Not known",
    };
  });
}

/* Site model --------------------------------------------------------------- */

export function FoundationModelHeadline({
  foundation,
  site,
  readinessHref,
  sldHref,
}: {
  foundation: FoundationReadModel;
  site: SiteDetailReadModel;
  readinessHref: string;
  sldHref: string;
}) {
  const words = foundationPeriodWords(foundation);
  const equipment = equipmentByKind(site);
  const parts = equipment.reduce((sum, item) => sum + (item.value ?? 0), 0);
  const steps = settingSteps(foundation);
  const settings = steps.filter((step) => step.state === "done").length;
  const unresolved = words.code === "NO_EFFECTIVE_REVISION";
  return (
    <HeadlineVisualCard
      dataName="foundation-model"
      headingId="foundation-model-answer-heading"
      question="What is configured for this period?"
      headline={
        unresolved
          ? "No equipment or settings are recorded for the selected time"
          : `${parts} ${parts === 1 ? "piece" : "pieces"} of equipment and ${settings} of ${steps.length} operating settings are recorded`
      }
      status={<ProductStatus words={words} scope={scopeOf(foundation)} asOf={foundation.resolved.knowledge_at} />}
      visual={
        unresolved ? undefined : (
          <div className="foundation-headline__visuals">
            {equipment.length === 0 ? null : <ValueBars title="Recorded equipment by kind" items={equipment} />}
            <StepStrip title="Operating settings" steps={steps} />
          </div>
        )
      }
      meaning={
        <p>
          Ratings and settings are what was recorded for the site, not measured operation. Ratings are declared, not
          checked in the field.
        </p>
      }
      todo={
        <p>
          <Link to={readinessHref}>See what still needs connecting or confirming in Readiness →</Link>
        </p>
      }
      destination={<Link to={sldHref}>How the equipment is connected: Single line diagram →</Link>}
      references={<ExactReferences name="foundation-model-references" references={recordReferences(foundation)} />}
    />
  );
}

/* Readiness ---------------------------------------------------------------- */

export function FoundationReadinessHeadline({
  foundation,
  modelHref,
  evidenceHref,
  healthHref,
}: {
  foundation: FoundationReadModel;
  modelHref: string;
  evidenceHref: string;
  healthHref: string;
}) {
  const { readiness } = foundation;
  const words = setupReadinessWords(readiness.state);
  const missingRoles = readiness.roles.filter((role) => role.required && role.status !== "CONFIGURED");
  const missingChannels = missingRoles.filter((role) => role.covered_by !== "FOUNDATION_CONTROL");
  const missingSettings = missingRoles.filter((role) => role.covered_by === "FOUNDATION_CONTROL");
  const cards = readinessCards(foundation);
  const unknown = readiness.state === "UNKNOWN";
  // W1-UX-06 (`D-2026-10-17-w1-ux-06` Q4): an unrecognised Readiness code shows no readiness-dependent step as
  // complete and no positive headline; directly known configuration facts (cards, gateways) still show.
  const unrecognised = words.unrecognised;
  const gatewayCount = foundation.gateways.length;
  const steps: Step[] = [
    {
      label: "Equipment and settings recorded",
      state: cards.some((c) => c.state === "UNKNOWN")
        ? "not-known"
        : cards.some((c) => c.state === "NEEDS_CONFIGURATION")
          ? "problem"
          : "done",
      detail:
        foundation.configuration_gaps.length === 0
          ? "Nothing missing"
          : `${foundation.configuration_gaps.length} missing`,
    },
    {
      label: "Readings linked to equipment",
      state: unknown || unrecognised ? "not-known" : missingRoles.length === 0 ? "done" : "problem",
      detail: unrecognised
        ? "Set-up state not recognised"
        : unknown
          ? "No linked set for this period"
          : missingRoles.length === 0
            ? "All required"
            : `${missingRoles.length} missing`,
    },
    {
      label: "Gateway registered",
      state: gatewayCount === 0 ? "waiting" : "done",
      detail: gatewayCount === 0 ? "None registered" : "Registered; contact is reported below",
    },
    {
      label: "Commissioning confirmed",
      state: "not-known",
      detail: "Not recorded here",
    },
  ];
  const nextSteps: string[] = [
    ...missingChannels.map((role) => `Link a reading channel for ${role.label}.`),
    ...missingSettings.map((role) => `Set ${role.label} in the Site model.`),
    ...foundation.configuration_gaps.map((gap) => gap.message),
    ...(gatewayCount === 0 ? ["Register the site's gateway."] : []),
  ];
  const outstanding = nextSteps.length;
  return (
    <HeadlineVisualCard
      dataName="foundation-readiness"
      headingId="foundation-readiness-answer-heading"
      question="What needs connecting or confirming?"
      headline={
        unrecognised
          ? "Set-up state not recognised"
          : unknown
            ? "Readiness cannot be judged: no reading channels are linked for this period"
            : outstanding === 0
              ? "Nothing is missing from the set-up; commissioning is not yet confirmed"
              : `${outstanding} ${outstanding === 1 ? "item needs" : "items need"} setting up; commissioning is not yet confirmed`
      }
      status={<ProductStatus words={words} scope={scopeOf(foundation)} asOf={foundation.resolved.knowledge_at} />}
      visual={<StepStrip title="Set-up steps" steps={steps} />}
      meaning={
        <p>
          This view is about set-up only. Being set up to report does not mean any device is connected or reporting;
          contact and reporting are on <Link to={healthHref}>Health</Link>.
        </p>
      }
      todo={
        nextSteps.length === 0 && unrecognised ? (
          <p>The set-up state in this read is not recognised; check the exact references below before relying on it.</p>
        ) : nextSteps.length === 0 ? (
          <p>Record a commissioning confirmation when one exists; nothing else is missing from the set-up.</p>
        ) : (
          <ul data-readiness-next-steps="">
            {nextSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        )
      }
      destination={
        <>
          <Link to={evidenceHref}>What the readings can support: Site Evidence →</Link>{" "}
          <Link to={modelHref}>Recorded equipment and settings: Site model →</Link>
        </>
      }
      references={
        <ExactReferences
          name="foundation-readiness-references"
          references={[
            { label: "Set-up state (exact)", value: readiness.state },
            { label: "Required readings list", value: readiness.role_set },
            ...recordReferences(foundation),
          ]}
        />
      }
    />
  );
}

/* Single line diagram ------------------------------------------------------- */

export function FoundationSldHeadline({
  foundation,
  site,
  readinessHref,
  healthHref,
}: {
  foundation: FoundationReadModel;
  site: SiteDetailReadModel;
  readinessHref: string;
  healthHref: string;
}) {
  const words = foundationPeriodWords(foundation);
  const devices = site.foundation.devices ?? [];
  const linked = new Set(foundation.bindings.mappings.map((binding) => binding.device_id));
  const withLink = devices.filter((device) => linked.has(device.device_id)).length;
  const withoutLink = devices.length - withLink;
  const parts = site.foundation.components.filter((c) => c.component_type !== "AC_BUS").length;
  return (
    <HeadlineVisualCard
      dataName="foundation-sld"
      headingId="foundation-sld-answer-heading"
      question="How is the site connected, and which parts can report?"
      headline={
        devices.length === 0
          ? `${parts} parts are drawn; no device is recorded, so no part can report`
          : `${parts} parts are drawn; ${withLink} of ${devices.length} devices have a linked reading channel`
      }
      status={<ProductStatus words={words} scope={scopeOf(foundation)} asOf={foundation.resolved.knowledge_at} />}
      visual={
        <ValueBars
          title="Devices on the diagram"
          items={[
            { key: "linked", label: "With a linked reading channel", value: withLink, valueText: String(withLink) },
            { key: "unlinked", label: "No linked reading channel", value: withoutLink, valueText: String(withoutLink) },
            { key: "reporting", label: "Reporting now", value: null, valueText: "" },
          ]}
        />
      }
      meaning={
        <p>
          The drawing shows recorded connections, not live power flow. A part marked “no linked channel” cannot report
          readings. Whether linked parts are reporting is not assessed here; source contact is on{" "}
          <Link to={healthHref}>Health</Link>.
        </p>
      }
      todo={
        withoutLink === 0 ? undefined : (
          <p>
            <Link to={readinessHref}>Link the missing reading channels in Readiness →</Link>
          </p>
        )
      }
      references={<ExactReferences name="foundation-sld-references" references={recordReferences(foundation)} />}
    />
  );
}
