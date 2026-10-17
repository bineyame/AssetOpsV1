/**
 * Plain words for Site Health and the battery page (W1-UX-05/06, kept by
 * W1-F5a). W1-F5a removed the leading answer cards
 * (`D-2026-10-17-mockup-layout-spec`): the screen's condition state leads the
 * status strip, and gateway contact words sit inside the "Data sources" panel.
 * Contact and reported fact age stay separate, and neither is equipment
 * condition.
 */

import { UNRECOGNISED_SENTENCE, type ProductWords } from "../ui";
import type { BatteryDetail, BatteryEntry, GatewayHealthRow, SourceHealthDocument } from "./healthClient";

/* Words owned by the Health domain ----------------------------------------- */

/** The Site's gateway-contact summary in plain words. Contact is never equipment condition, so nothing is `positive`. */
export function contactSummaryWords(doc: SourceHealthDocument): ProductWords {
  const s = doc.summary;
  // W1-UX-06 phase-1 review L1: a contact summary about enabled gateways, sent with none enabled, is not confirmed
  // contact. Fall back non-positively with a next step (the recognised no-source state keeps its own words).
  const enabledCount = doc.gateways.filter((g) => g.registration === "ENABLED").length;
  if ((s.status === "ALL_CURRENT" || s.status === "NOT_ALL_CURRENT") && enabledCount === 0) {
    return {
      label: "Gateway contact cannot be confirmed",
      sentence: "This record lists no enabled gateway, so there is no gateway contact to confirm for this site.",
      next: "Check that the site's gateway is registered and enabled.",
      tone: "limited",
      code: s.status,
      unrecognised: false,
    };
  }
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

/**
 * W1-F5a: the Site Health status-strip state. It is about physical asset
 * condition, the subject of v69 `health`, never gateway contact. The battery
 * entry read is the only asset read; its condition is Unknown, so the site's
 * asset condition cannot yet be judged.
 */
export function siteConditionWords(entry: BatteryEntry): ProductWords {
  const condition = entry.physical_condition;
  if (condition !== undefined && condition.status !== "UNKNOWN") {
    return {
      label: "Condition not recognised",
      sentence: UNRECOGNISED_SENTENCE,
      tone: "limited",
      code: String(condition.status),
      unrecognised: true,
    };
  }
  if (entry.configuration === "NOT_CONFIGURED") {
    return {
      label: "Asset condition cannot yet be judged",
      sentence: "No battery is part of this site's configuration, and no other asset's condition is read here.",
      tone: "limited",
      code: "NOT_CONFIGURED",
      unrecognised: false,
    };
  }
  return {
    label: "Asset condition cannot yet be judged",
    sentence:
      "The inputs needed to judge the configured battery's physical condition are missing. Unknown does not mean normal, and it does not mean faulty.",
    next: "Open the battery to see what is missing.",
    tone: "limited",
    code: condition?.reason ?? "UNKNOWN",
    unrecognised: false,
  };
}
