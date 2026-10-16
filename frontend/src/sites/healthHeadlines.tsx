/**
 * The W1 answer cards for Site Health and the battery page (W1-UX-05,
 * `D-2026-10-16-w1-ux`).
 *
 * Health answers "Which source needs attention?" with source contact and
 * reported fact age in separate lanes: a recent receipt is never fresh facts,
 * and neither is equipment condition. The battery page leads with "Battery
 * condition: cannot yet be judged" and the inputs that are missing. Both
 * render only what the S7 reads returned; exact IDs and raw status codes sit in
 * the closed exact-reference disclosure, while the state sentence, scope and
 * "as of" bound stay in the default reading.
 */

import { Link } from "react-router-dom";

import {
  ExactReferences,
  HeadlineVisualCard,
  ProductStatus,
  StepStrip,
  UNRECOGNISED_SENTENCE,
  ValueBars,
  type ProductWords,
  type Step,
} from "../ui";
import type { BatteryDetail, GatewayHealthRow, SourceHealthDocument } from "./healthClient";

/* Words owned by the Health domain ----------------------------------------- */

/** The Site's gateway-contact summary in plain words. Contact is never equipment condition, so nothing is `positive`. */
export function contactSummaryWords(doc: SourceHealthDocument): ProductWords {
  const s = doc.summary;
  switch (s.status) {
    case "ALL_CURRENT":
      return {
        label: "Every enabled gateway is in contact",
        sentence:
          "Each enabled gateway reached the server within its reporting interval. Contact is not equipment condition, and its reports can still be old.",
        tone: "neutral",
        code: s.status,
        unrecognised: false,
      };
    case "NOT_ALL_CURRENT":
      return {
        label: "Some gateways are not in contact",
        sentence: "At least one enabled gateway has not reached the server within its reporting interval, or never has.",
        next: "Open the gateways listed below.",
        tone: "limited",
        code: s.status,
        unrecognised: false,
      };
    case "NO_REGISTERED_SOURCE":
      return {
        label: "No gateway is reporting",
        sentence:
          s.reason === "NO_REGISTERED_GATEWAY"
            ? "No gateway is registered for this site, so nothing is known about source contact."
            : "No gateway is enabled for this site, so nothing is known about source contact.",
        next: "Register or enable the site's gateway.",
        tone: "limited",
        code: s.status,
        unrecognised: false,
      };
    default:
      return {
        label: "Contact state not recognised",
        sentence: UNRECOGNISED_SENTENCE,
        tone: "limited",
        code: String(s.status),
        unrecognised: true,
      };
  }
}

/** One gateway's contact in plain words, for its selected panel. */
export function gatewayContactWords(row: GatewayHealthRow): ProductWords {
  const c = row.contact;
  if (row.registration === "DISABLED") {
    return {
      label: "Disabled gateway",
      sentence: "This gateway is disabled, so its contact is not counted for the site.",
      tone: "neutral",
      code: "DISABLED",
      unrecognised: false,
    };
  }
  if (c.reason === "NEVER_RECEIVED") {
    return {
      label: "Never heard from",
      sentence: "The server has never received a report from this gateway, so nothing is known about it.",
      next: "Check that the gateway is installed, powered and able to reach the server.",
      tone: "problem",
      code: c.reason,
      unrecognised: false,
    };
  }
  switch (c.status) {
    case "CURRENT":
      // W1-UX-06 (`D-2026-10-17-w1-ux-06` Q3): contact and fact age stay distinct. An old report with a trusted,
      // known age says so; an unknown, untrusted or observed-after-receipt age is never called old.
      if (factAgeUnknown(row)) {
        return {
          label: "In contact; its latest report's age cannot be confirmed",
          sentence:
            "The server received this gateway's report within its reporting interval, but the age of what it last reported cannot be confirmed. This is not equipment condition.",
          tone: "limited",
          code: `${c.status} / ${row.reported_facts.reason}`,
          unrecognised: false,
        };
      }
      if (row.reported_facts.status === "OLD") {
        return {
          label: "In contact; its latest report is old",
          sentence:
            "The server received this gateway's report within its reporting interval, but the facts it last reported are old; their age is shown below. This is not equipment condition.",
          tone: "limited",
          code: `${c.status} / ${row.reported_facts.status}`,
          unrecognised: false,
        };
      }
      return {
        label: "In contact",
        sentence: "The server received this gateway's report within its reporting interval. This is not equipment condition.",
        tone: "neutral",
        code: c.status,
        unrecognised: false,
      };
    case "STALE":
      return {
        label: "Out of contact",
        sentence: "Nothing has reached the server within this gateway's reporting interval; when it stopped is not known.",
        next: "Check the gateway's power and network link.",
        tone: "problem",
        code: c.status,
        unrecognised: false,
      };
    case "UNKNOWN":
      return {
        label: "Contact not known",
        sentence: "The read does not say whether this gateway is in contact.",
        tone: "limited",
        code: c.status,
        unrecognised: false,
      };
    default:
      return { label: "Contact not recognised", sentence: UNRECOGNISED_SENTENCE, tone: "limited", code: String(c.status), unrecognised: true };
  }
}

/** True when a gateway's reported facts are of unknown age: never received, untrusted clock or observed after receipt (S7-01b L1). */
export function factAgeUnknown(row: GatewayHealthRow): boolean {
  const f = row.reported_facts;
  return (
    f.fact_age_seconds === null ||
    f.reason === "NEVER_RECEIVED" ||
    f.reason === "OBSERVED_AFTER_RECEIPT" ||
    f.clock.trust === "UNTRUSTED" ||
    f.status === "UNKNOWN"
  );
}

/* Site Health ---------------------------------------------------------------- */

export function HealthHeadline({
  doc,
  siteName,
  gatewayHref,
  batteryHref,
}: {
  doc: SourceHealthDocument;
  siteName: string;
  gatewayHref: (gatewayId: string) => string;
  batteryHref: string;
}) {
  const words = contactSummaryWords(doc);
  const enabled = doc.gateways.filter((g) => g.registration === "ENABLED");
  const noSource = doc.summary.status === "NO_REGISTERED_SOURCE";
  const inContact = enabled.filter((g) => g.contact.status === "CURRENT").length;
  const outOfContact = enabled.filter((g) => g.contact.status === "STALE").length;
  const contactUnknown = enabled.length - inContact - outOfContact;
  const unknownAge = enabled.filter(factAgeUnknown);
  const old = enabled.filter((g) => !factAgeUnknown(g) && g.reported_facts.status === "OLD").length;
  const recent = enabled.length - unknownAge.length - old;
  const attention = enabled.filter(
    (g) => g.contact.status !== "CURRENT" || factAgeUnknown(g) || g.reported_facts.status !== "CURRENT",
  );
  // W1-UX-06 (`D-2026-10-17-w1-ux-06` Q4): an unrecognised summary code, or zero enabled gateways outside the
  // recognised no-source state, never reads positive (never "All 0 enabled gateways").
  const headline = noSource
    ? "No gateway is reporting, so nothing is known about this site's sources"
    : words.unrecognised || enabled.length === 0
      ? "Gateway contact cannot be confirmed"
      : attention.length === 0
        ? `All ${enabled.length} enabled gateways are in contact and their latest reports are recent`
        : `${attention.length} of ${enabled.length} enabled ${enabled.length === 1 ? "gateway needs" : "gateways need"} attention`;
  return (
    <HeadlineVisualCard
      dataName="site-health"
      headingId="site-health-answer-heading"
      question="Which source needs attention?"
      headline={headline}
      status={
        <ProductStatus words={words} scope={`${siteName} · gateway contact and reports`} asOf={doc.read_at} />
      }
      visual={
        noSource ? undefined : (
          <div className="foundation-headline__visuals" data-health-lanes="">
            <ValueBars
              title="Contact: when the server last heard from each gateway"
              items={[
                { key: "in-contact", label: "In contact", value: inContact, valueText: String(inContact) },
                { key: "out-of-contact", label: "Out of contact", value: outOfContact, valueText: String(outOfContact) },
                { key: "never", label: "Never heard or not known", value: contactUnknown, valueText: String(contactUnknown) },
              ]}
            />
            <ValueBars
              title="Reports: how old the latest reported facts are"
              items={[
                { key: "recent", label: "Recent", value: recent, valueText: String(recent) },
                { key: "old", label: "Old", value: old, valueText: String(old) },
                { key: "age-unknown", label: "Age not known", value: unknownAge.length, valueText: String(unknownAge.length) },
              ]}
            />
          </div>
        )
      }
      meaning={
        <p>
          Contact means a gateway reached the server. What it reports can still be old, and neither says anything about
          the equipment’s physical condition.
        </p>
      }
      todo={
        attention.length === 0 ? undefined : (
          <ul data-health-attention="">
            {attention.map((g) => (
              <li key={g.gateway_id} data-health-attention-gateway={g.gateway_external_id}>
                <Link to={gatewayHref(g.gateway_id)}>
                  Open gateway <span data-vocabulary-exempt="source-reference">{g.gateway_external_id}</span>
                </Link>
                : {gatewayContactWords(g).label.toLowerCase()}
                {factAgeUnknown(g)
                  ? "; age of its latest report not known"
                  : g.reported_facts.status === "OLD"
                    ? "; its latest report is old"
                    : ""}
              </li>
            ))}
          </ul>
        )
      }
      destination={<Link to={batteryHref}>Battery condition: battery page →</Link>}
      references={
        <ExactReferences
          name="site-health-references"
          references={[
            { label: "Read time (exact)", value: doc.read_at },
            { label: "Contact summary (exact)", value: doc.summary.status },
            { label: "Summary reason (exact)", value: doc.summary.reason ?? null },
          ]}
        />
      }
    />
  );
}

/* Battery ---------------------------------------------------------------------- */

export function batteryConditionWords(detail: BatteryDetail): ProductWords {
  if (detail.physical_condition.status !== "UNKNOWN") {
    return {
      label: "Condition not recognised",
      sentence: UNRECOGNISED_SENTENCE,
      tone: "limited",
      code: String(detail.physical_condition.status),
      unrecognised: true,
    };
  }
  return {
    label: "Cannot yet be judged",
    sentence:
      "The inputs needed to judge this battery's physical condition are missing. Unknown does not mean normal, and it does not mean faulty.",
    next: "Add the missing inputs listed below.",
    tone: "limited",
    code: detail.physical_condition.reason,
    unrecognised: false,
  };
}

export function BatteryHeadline({
  detail,
  name,
  inputName,
  healthHref,
}: {
  detail: BatteryDetail;
  name: string;
  /** Plain name of a missing input, or null when the code is not known. */
  inputName: (code: string) => string | null;
  healthHref: string;
}) {
  const words = batteryConditionWords(detail);
  const missing = detail.physical_condition.missing_causal_inputs;
  const steps: Step[] = missing.map((input) => ({
    label: inputName(input.input) ?? "An input this page cannot name",
    state: input.status === "MISSING" ? "waiting" : "not-known",
    detail: input.status === "MISSING" ? "Missing" : "Not known",
  }));
  return (
    <HeadlineVisualCard
      dataName="battery-condition"
      headingId="battery-condition-answer-heading"
      question="What can we say about this battery's condition?"
      headline="Battery condition: cannot yet be judged"
      status={<ProductStatus words={words} scope={<span>{name} · physical condition</span>} asOf={detail.read_at} />}
      visual={steps.length === 0 ? undefined : <StepStrip title="Inputs needed to judge condition" steps={steps} />}
      meaning={
        <p>
          The declared rating is what the site’s configuration records, not a measured capacity, and the battery
          charge reading is a separate fact that does not show condition. No remaining life, warranty position or
          replacement date is stated.
        </p>
      }
      todo={
        steps.length === 0 ? undefined : (
          <p>
            {missing.length === 1 ? "One input is" : `${missing.length} inputs are`} missing. Condition stays unknown
            until they exist and a reviewed method uses them.
          </p>
        )
      }
      destination={<Link to={healthHref}>Source contact and reports: Health →</Link>}
      references={
        <ExactReferences
          name="battery-condition-references"
          references={[
            { label: "Asset reference", value: detail.asset.asset_id },
            { label: "Asset code", value: detail.asset.asset_code },
            { label: "Condition reason (exact)", value: detail.physical_condition.reason },
            { label: "Channel status (exact)", value: detail.binding_status },
            { label: "Foundation version record", value: detail.basis.foundation_revision_id },
            { label: "Effective time (exact)", value: detail.basis.effective_at },
          ]}
        />
      }
    />
  );
}
