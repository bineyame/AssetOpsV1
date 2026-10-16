import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  describeViolations,
  disclosurePhrases,
  forbiddenPhrases,
  rawCodes,
  scanDisclosureVocabulary,
  scanProductVocabulary,
  W1_VOCABULARY_VERSION,
} from "../../test/productVocabulary";
import { currentnessWords, ExactReferences, HeadlineVisualCard, ProductStatus, ValueBars } from "..";

describe("W1 vocabulary set: raw-code pattern", () => {
  it("is versioned", () => {
    expect(W1_VOCABULARY_VERSION).toBeGreaterThanOrEqual(1);
  });

  it("catches leaked codes: underscore codes, closed single-word codes, UUIDs, digests and versions", () => {
    expect(rawCodes("State: GUARDRAIL_FAIL")).toEqual(["uppercase underscore code: GUARDRAIL_FAIL"]);
    expect(rawCodes("PENDING_REASSESSMENT")).toEqual(["uppercase underscore code: PENDING_REASSESSMENT"]);
    for (const code of ["CURRENT", "STALE", "UNKNOWN", "UNASSESSED", "VERIFIED", "INEFFECTIVE", "INCONCLUSIVE", "REFUSED", "WITHDRAWN"]) {
      expect(rawCodes(`It is ${code} now`), code).toEqual([code]);
    }
    expect(rawCodes("record 3f2a9c1e-0b4d-4e5f-9a8b-1c2d3e4f5a6b")[0]).toMatch(/^UUID: /);
    expect(rawCodes(`digest ${"a1".repeat(32)}`)[0]).toMatch(/^digest: /);
    expect(rawCodes("using dispatch-rule-v2 today")).toEqual(["rule or model version: dispatch-rule-v2"]);
  });

  it("does not flag units, acronyms or ordinary lower-case words", () => {
    expect(rawCodes("SOC UTC kW kWh PV")).toEqual([]);
    expect(rawCodes("Battery charge (SOC) 30 % at 10:05 UTC; 12 kW, 40 kWh; solar power (PV)")).toEqual([]);
    expect(rawCodes("current, stale, pending, unknown and verified are plain words")).toEqual([]);
    expect(rawCodes("Current readings are Pending")).toEqual([]);
  });

  it("adds the W1 terms to the T028 list and allows ordinary operational wording", () => {
    for (const phrase of ["claim limit", "basis fingerprint", "typed reason", "cursor", "watermark", "fixture", "stage", "model version"]) {
      expect(forbiddenPhrases(`The ${phrase} here`, "w1"), phrase).toContain(phrase);
      expect(forbiddenPhrases(`The ${phrase} here`, "t028"), phrase).not.toContain(phrase);
    }
    expect(forbiddenPhrases("Why the generator ran at 06:00", "w1")).toEqual([]);
    expect(forbiddenPhrases("The scenario run finished", "w1")).toEqual(expect.arrayContaining(["scenario", "run"]));
    // The T028 list alone is unchanged.
    expect(forbiddenPhrases("Why the generator ran at 06:00")).toEqual(["ran"]);
  });
});

function card(overrides: { headline?: string; summaryLabel?: string; refLabel?: string; refValue?: string } = {}) {
  return (
    <main>
      <HeadlineVisualCard
        dataName="probe"
        headingId="probe-h"
        question="What can we rely on?"
        headline={overrides.headline ?? "288 readings were accepted for this day"}
        status={<ProductStatus words={currentnessWords("STALE_PROJECTION")} scope="Kobo, 16 Oct 2026" asOf="2026-10-16T10:05:00Z" />}
        visual={<ValueBars title="Readings by outcome" items={[{ label: "Accepted", value: 288, valueText: "288" }, { label: "Late", value: null, valueText: "" }]} />}
        meaning={<p>The day is covered by one source.</p>}
        todo={<p>Look again after the day has been checked again.</p>}
        references={
          <ExactReferences
            name="probe-refs"
            references={[
              { label: overrides.refLabel ?? "Reason code", value: overrides.refValue ?? "GUARDRAIL_FAIL" },
              { label: "Assessment reference", value: "3f2a9c1e-0b4d-4e5f-9a8b-1c2d3e4f5a6b" },
            ]}
          />
        }
      />
    </main>
  );
}

describe("W1 vocabulary set: shared card mutation tests", () => {
  it("the shared card with labelled exact values passes the W1 set and the disclosure list, and the scan saw text", () => {
    const { container } = render(card());
    const full = scanProductVocabulary(container, "probe", { set: "w1" });
    expect(describeViolations(full.violations)).toBe("");
    expect(full.scanned).toBeGreaterThan(10);
    const disclosure = scanDisclosureVocabulary(container, "probe");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.scanned).toBeGreaterThan(2);
    expect(describeViolations(disclosure.violations)).toBe("");
  });

  it("a raw code leaked into the headline is caught by the W1 set", () => {
    const { container } = render(card({ headline: "Day is STALE_PROJECTION" }));
    const found = scanProductVocabulary(container, "probe", { set: "w1" }).violations.map((v) => v.phrase);
    expect(found).toContain("uppercase underscore code: STALE_PROJECTION");
  });

  it("a raw code in an SVG title and in an accessible label is caught", () => {
    const { container } = render(
      <div>
        <svg role="img" aria-label="Day VERIFIED">
          <title>Outcome GUARDRAIL_FAIL</title>
        </svg>
      </div>,
    );
    const found = scanProductVocabulary(container, "probe", { set: "w1" }).violations;
    expect(found.map((v) => `${v.where}:${v.phrase}`)).toEqual(
      expect.arrayContaining(["aria-label:VERIFIED", "text:uppercase underscore code: GUARDRAIL_FAIL"]),
    );
  });

  it("a code or implementation word in a disclosure label is caught; the labelled value alone is not", () => {
    const { container } = render(card({ refLabel: "Run payload REFUSED" }));
    const found = scanDisclosureVocabulary(container, "probe").violations.map((v) => v.phrase);
    expect(found).toEqual(expect.arrayContaining(["run", "payload", "REFUSED"]));
    expect(found).not.toContain("uppercase underscore code: GUARDRAIL_FAIL");
  });

  it("an unlabelled value outside its own exempt position is caught, and a raw code in a collapsed summary or its accessible name is caught", () => {
    const { container } = render(
      <div>
        <details data-exact-references>
          <summary aria-label="Why: GUARDRAIL_FAIL">How this was worked out (NO_FINDING)</summary>
          <p>The reason was GUARDRAIL_FAIL and the commit was replayed.</p>
        </details>
      </div>,
    );
    const found = scanDisclosureVocabulary(container, "probe").violations.map((v) => `${v.where}:${v.phrase}`);
    expect(found).toEqual(
      expect.arrayContaining(["aria-label:GUARDRAIL_FAIL", "text:NO_FINDING", "text:GUARDRAIL_FAIL", "text:commit"]),
    );
  });

  it("the disclosure list does not flag units and acronyms, or ordinary operational wording", () => {
    expect(disclosurePhrases("Battery charge (SOC) at 10:05 UTC, 12 kW, 40 kWh, solar (PV)")).toEqual([]);
    expect(disclosurePhrases("Why the generator ran")).toEqual([]);
  });

  it("an exemption cannot cover the disclosure container", () => {
    const { container } = render(
      <div>
        <details data-exact-references data-vocabulary-exempt="source-reference">
          <summary>How this was worked out</summary>
          <p>run payload</p>
        </details>
      </div>,
    );
    const found = scanDisclosureVocabulary(container, "probe").violations.map((v) => v.phrase);
    expect(found).toContain("exemption wraps more than one value");
  });
});
