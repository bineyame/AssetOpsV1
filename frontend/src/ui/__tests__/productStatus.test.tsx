import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  asOfText,
  currentnessWords,
  DEMONSTRATION_OUTCOME_NOTE,
  ExactReferences,
  HeadlineVisualCard,
  limitationWords,
  moneyWords,
  outcomeWords,
  ProductOutcome,
  ProductStatus,
  readResultWords,
  StepStrip,
  UNRECOGNISED_SENTENCE,
  ValueBars,
  type ProductWords,
} from "..";

import { AS_OF_PATTERN, visibleOutsideClosedDisclosure } from "../../test/productPresentation";

/** Words that claim a current, verified or positive state. */
const POSITIVE = /\b(up to date|latest checked|verified|confirmed|target met|saving|savings achieved)\b/i;

const NON_CURRENT = [
  "PENDING_REASSESSMENT",
  "REASSESSMENT_PENDING",
  "PENDING",
  "STALE",
  "STALE_PROJECTION",
  "FAILED",
  "UNASSESSED",
  "NOT_ASSESSED",
  "UNKNOWN",
  "HISTORICAL",
  "AUDIT_ONLY",
];

describe("W1 shared vocabulary: currentness matrix", () => {
  it("each currentness code reads as the reviewed sentence", () => {
    expect(currentnessWords("UNASSESSED").label).toBe("We have not checked this period");
    expect(currentnessWords("PENDING_REASSESSMENT").label).toBe("New readings call for another assessment");
    expect(currentnessWords("STALE").label).toBe("This result may miss newer readings");
    expect(currentnessWords("STALE_PROJECTION").label).toBe("This result may miss newer readings");
    expect(currentnessWords("UNKNOWN").label).toBe("We cannot judge this yet");
    expect(currentnessWords("CURRENT").label).toBe("Using the latest checked readings");
    expect(currentnessWords("CURRENT").tone).toBe("positive");
  });

  it("pending reassessment does not claim that processing has started", () => {
    const words = currentnessWords("PENDING_REASSESSMENT");
    expect(`${words.label} ${words.sentence} ${words.next ?? ""}`).not.toMatch(/\b(started|in progress|processing|being (re)?assessed|underway)\b/i);
  });

  it("no non-current code is promoted to a positive state", () => {
    for (const code of NON_CURRENT) {
      const words = currentnessWords(code);
      expect(words.tone, code).not.toBe("positive");
      expect(`${words.label} ${words.sentence}`, code).not.toMatch(POSITIVE);
      expect(words.unrecognised, code).toBe(false);
    }
  });

  it("an unknown code gets the neutral fallback, keeps the code for detail only, and is never positive", () => {
    for (const code of ["SOMETHING_NEW", "current", "", null, undefined, "toString", "__proto__"]) {
      const words = currentnessWords(code);
      expect(words.unrecognised, String(code)).toBe(true);
      expect(words.sentence).toBe(UNRECOGNISED_SENTENCE);
      expect(words.tone).not.toBe("positive");
      if (typeof code === "string" && code.length > 0) {
        expect(`${words.label} ${words.sentence} ${words.next ?? ""}`).not.toContain(code);
      }
    }
    expect(currentnessWords("SOMETHING_NEW").code).toBe("SOMETHING_NEW");
    expect(limitationWords("SOME_REASON").sentence).toBe(UNRECOGNISED_SENTENCE);
    expect(moneyWords("SOME_STATE").sentence).toBe(UNRECOGNISED_SENTENCE);
  });
});

describe("W1 shared vocabulary: refusal, empty and money", () => {
  it("refused and unavailable are not empty, and differ from a proved empty", () => {
    const refused = readResultWords("refused");
    const unavailable = readResultWords("unavailable");
    const empty = readResultWords("proved-empty");
    expect(refused.sentence).toMatch(/not empty/);
    expect(unavailable.sentence).toMatch(/not empty/);
    expect(empty.label).toBe("Checked: nothing to report");
    expect(new Set([refused.label, unavailable.label, empty.label]).size).toBe(3);
    for (const words of [refused, unavailable, empty]) expect(words.tone).not.toBe("positive");
  });

  it("withheld money and a missing price are different sentences and never zero", () => {
    expect(moneyWords("WITHHELD").label).toBe("No current amount can be shown");
    expect(moneyWords("WITHHELD_GENERATOR_SERIES").label).toBe("No current amount can be shown");
    expect(moneyWords("NO_PRICE").label).toBe("No price recorded");
    expect(moneyWords("WITHHELD").label).not.toBe(moneyWords("NO_PRICE").label);
    for (const code of ["WITHHELD", "WITHHELD_GENERATOR_SERIES", "MIXED_OR_UNKNOWN_SOURCE", "PENDING_REASSESSMENT", "NO_PRICE", "UNPRICED"]) {
      const words = moneyWords(code);
      expect(`${words.label} ${words.sentence}`, code).not.toMatch(/\$\s*0|\b0(\.0+)?\b|zero cost/);
      expect(words.tone, code).not.toBe("positive");
    }
  });
});

describe("W1 shared vocabulary: trial outcomes keyed on outcome, reason and source", () => {
  it("a measured safety or service failure reads as a missed limit, with metric, value, threshold and unit beside it", () => {
    const words = outcomeWords("INEFFECTIVE", ["GUARDRAIL_FAIL", "GUARDRAIL:reserve"], "LIVE");
    expect(words.label).toBe("Trial missed a safety or service limit");
    expect(words.showsFailedLimit).toBe(true);
    const { container } = render(
      <ProductOutcome
        words={words}
        scope="Trial at Kobo"
        asOf="2026-10-16T10:05:00Z"
        failedLimits={[{ name: "Battery reserve", value: "24", threshold: "30", unit: "%" }]}
      />,
    );
    const limits = container.querySelector("[data-product-outcome-failed-limits]");
    expect(limits?.textContent).toBe("Battery reserve: measured 24 %, limit 30 %");
    expect(container.textContent).not.toMatch(/Target not met/);
  });

  it("a guardrail failure with no measured value says so, never silently drops the limit", () => {
    const { container } = render(
      <ProductOutcome words={outcomeWords("INEFFECTIVE", ["GUARDRAIL_FAIL"], "LIVE")} scope="Trial" asOf={null} />,
    );
    expect(container.querySelector("[data-product-outcome-failed-limits]")?.textContent).toMatch(/not in this record/);
  });

  it("a target-only miss reads Target not met and shows no failed limit", () => {
    const words = outcomeWords("INEFFECTIVE", ["TARGET_MISS"], "LIVE");
    expect(words.label).toBe("Target not met");
    expect(words.showsFailedLimit).toBe(false);
    const { container } = render(<ProductOutcome words={words} scope="Trial" asOf="2026-10-16T10:05:00Z" />);
    expect(container.querySelector("[data-product-outcome-failed-limits]")).toBeNull();
    expect(container.textContent).not.toMatch(/safety or service limit/);
  });

  it("could-not-conclude keeps a known failure visible beside it", () => {
    const words = outcomeWords("INCONCLUSIVE", ["KNOWN_FAILURE:reserve", "TARGET_UNKNOWN"], "LIVE");
    expect(words.label).toBe("Could not conclude");
    const { container } = render(
      <ProductOutcome words={words} scope="Trial" asOf="2026-10-16T10:05:00Z" knownFailures={["Battery reserve fell below its limit"]} />,
    );
    const failures = container.querySelector("[data-product-outcome-known-failures]");
    expect(failures?.textContent).toBe("Known failure: Battery reserve fell below its limit");
    expect(visibleOutsideClosedDisclosure(failures as Element)).toBe(true);
  });

  it("a verified demonstration result says policy trial, no savings or realized benefit, and its source", () => {
    const words = outcomeWords("VERIFIED", [], "REGISTERED_SIMULATION");
    expect(words.label).toBe("Target met within the sampled limits");
    expect(words.sentence).toMatch(/five-minute sample/);
    expect(words.sentence).toMatch(/not continuous proof/);
    expect(words.demonstrationNote).toBe(DEMONSTRATION_OUTCOME_NOTE);
    const { container } = render(<ProductOutcome words={words} scope="Trial" asOf="2026-10-16T10:05:00Z" />);
    expect(container.querySelector("[data-product-outcome-demonstration]")?.textContent).toMatch(/policy trial/);
    expect(container.querySelector("[data-product-outcome-demonstration]")?.textContent).toMatch(/no savings or realized benefit/);
    expect(container.querySelector("[data-product-outcome-source]")?.textContent).toBe(
      "Source: Generated test data, not field readings",
    );
    for (const demo of ["AUTHORED_DEMONSTRATION", "SIMULATED"]) {
      expect(outcomeWords("VERIFIED", [], demo).demonstrationNote).toBe(DEMONSTRATION_OUTCOME_NOTE);
      expect(outcomeWords("VERIFIED", [], demo).source.label).toMatch(/not field readings/);
    }
  });

  it("a verified result on an unestablished source is not shown as positive", () => {
    for (const source of [null, "MIXED", "UNKNOWN", "SOMETHING_ELSE"]) {
      const words = outcomeWords("VERIFIED", [], source);
      expect(words.tone).toBe("limited");
      expect(words.source.label).toBe("Where these readings came from is not established");
    }
  });

  it("an unrecognised outcome is neutral and carries no demonstration claim", () => {
    const words = outcomeWords("SOMETHING_NEW", [], "LIVE");
    expect(words.sentence).toBe(UNRECOGNISED_SENTENCE);
    expect(words.tone).not.toBe("positive");
  });
});

describe("W1 shared presentation: state, scope and as-of stay visible with the disclosure closed", () => {
  const AS_OF = "2026-10-16T10:05:00Z";
  const CASES: Array<[string, ProductWords]> = [
    ["unassessed", currentnessWords("UNASSESSED")],
    ["pending", currentnessWords("PENDING")],
    ["pending reassessment", currentnessWords("PENDING_REASSESSMENT")],
    ["stale", currentnessWords("STALE_PROJECTION")],
    ["unknown", currentnessWords("UNKNOWN")],
    ["refused", readResultWords("refused")],
    ["withheld money", moneyWords("WITHHELD")],
    ["proved zero", readResultWords("proved-empty")],
  ];

  for (const [name, words] of CASES) {
    it(`${name}: state sentence, scope and as-of are outside the closed disclosure`, () => {
      render(
        <HeadlineVisualCard
          dataName="test"
          headingId="h"
          question="What can we rely on?"
          headline="Answer"
          status={<ProductStatus words={words} scope="Kobo, 16 Oct 2026" asOf={AS_OF} />}
          meaning={<p>Meaning</p>}
          references={<ExactReferences name="test-refs" references={[{ label: "Assessment reference", value: "rev-1" }]} />}
        />,
      );
      const details = document.querySelector("details[data-exact-references]") as HTMLDetailsElement;
      expect(details.open).toBe(false);
      for (const text of [words.label, words.sentence, "Kobo, 16 Oct 2026", "As of 16 Oct 2026, 10:05 UTC"]) {
        const el = screen.getByText(text);
        expect(visibleOutsideClosedDisclosure(el), `${name}: ${text}`).toBe(true);
      }
      // The exact value is in the disclosure, not in the default reading.
      expect(visibleOutsideClosedDisclosure(screen.getByText("rev-1"))).toBe(false);
    });
  }
});

describe("W1 shared presentation: primitives", () => {
  it("the as-of bound is plain, and a missing instant never becomes now", () => {
    expect(asOfText("2026-10-16T10:05:00Z")).toBe("As of 16 Oct 2026, 10:05 UTC");
    expect(asOfText(null)).toBe("As of: time not recorded");
    expect(asOfText("not a time")).toBe("As of: time not recorded");
  });

  it("the shared as-of acceptance pattern takes exactly the two forms asOfText emits (W1-UX-06)", () => {
    for (const instant of ["2026-10-16T10:05:00Z", "2026-01-01T00:00:00Z", "2026-12-31T23:59:00Z", null, "not a time"]) {
      expect(asOfText(instant)).toMatch(AS_OF_PATTERN);
    }
    for (const wrong of ["As of now", "As of ", "As of : time not recorded", "As of 16 Oct 2026", "As of 16 Oct 2026, 10:05", "as of 16 Oct 2026, 10:05 UTC", "Updated 16 Oct 2026, 10:05 UTC"]) {
      expect(wrong).not.toMatch(AS_OF_PATTERN);
    }
  });

  it("the disclosure summary is fixed text, keyboard reachable, and holds labelled values only", () => {
    const { container } = render(
      <ExactReferences name="refs" references={[{ label: "Reason code", value: "GUARDRAIL_FAIL" }, { label: "Assessment reference", value: null }]} />,
    );
    const summary = container.querySelector("summary") as HTMLElement;
    expect(summary.textContent).toBe("How this was worked out");
    expect(summary.getAttribute("aria-label")).toBeNull();
    summary.focus();
    expect(document.activeElement).toBe(summary);
    expect(container.querySelector("code")?.getAttribute("data-vocabulary-exempt")).toBe("source-reference");
    expect(within(container).getByText("not recorded")).toBeTruthy();
    expect(render(<ExactReferences name="none" references={[]} />).container.innerHTML).toBe("");
  });

  it("an unknown value draws a distinct not-known mark and text, never a zero-length bar", () => {
    const { container } = render(
      <ValueBars
        title="Readings by outcome"
        items={[
          { label: "Accepted", value: 288, valueText: "288" },
          { label: "Rejected", value: 0, valueText: "0" },
          { label: "Late", value: null, valueText: "ignored" },
        ]}
      />,
    );
    const rows = container.querySelectorAll("[data-value-bar]");
    expect(rows).toHaveLength(3);
    const late = rows[2];
    expect(late.getAttribute("data-value-bar")).toBe("not-known");
    expect(late.querySelector("[data-value-bar-mark='not-known']")).not.toBeNull();
    expect(late.querySelector("[data-value-bar-mark='known']")).toBeNull();
    expect(late.textContent).toMatch(/not known/);
    expect(late.textContent).not.toMatch(/ignored|\b0\b/);
    expect((rows[0].querySelector("[data-value-bar-mark='known']") as HTMLElement).style.width).toBe("100%");
    expect(rows[1].querySelector(".value-bars__value")?.textContent).toBe("0");
    expect(rows[1].getAttribute("data-value-bar")).toBe("known");
    expect(container.querySelector("ul")?.getAttribute("aria-label")).toBe(
      "Readings by outcome. Accepted: 288; Rejected: 0; Late: not known",
    );
  });

  it("a step strip says each step's state in words, including not known", () => {
    const { container } = render(
      <StepStrip
        title="Where this stands"
        steps={[
          { label: "Accepted", state: "done", detail: "16 Oct" },
          { label: "Applied", state: "waiting", detail: "Not applied yet" },
          { label: "Trial outcome", state: "not-known", detail: "We cannot judge this yet" },
        ]}
      />,
    );
    const steps = Array.from(container.querySelectorAll("[data-step]"));
    expect(steps.map((s) => s.querySelector(".step-strip__state")?.textContent)).toEqual(["Done", "Not yet", "Not known"]);
    expect(container.querySelector("ol")).not.toBeNull();
  });

  it("no plan is a waiting state, never an outcome", () => {
    const words = outcomeWords("NO_PLAN", [], "LIVE");
    expect(words.label).toBe("No trial plan yet");
    expect(words.tone).not.toBe("positive");
    expect(words.showsFailedLimit).toBe(false);
  });
});
