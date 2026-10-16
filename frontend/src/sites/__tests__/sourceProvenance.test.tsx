import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { SourceProvenanceNotice, type SourceProvenance, type SourceState } from "../sourceProvenance";

function block(state: SourceState, patch: Partial<SourceProvenance> = {}): SourceProvenance {
  return {
    tenant_id: "t1",
    site_id: "s1",
    finding_revision_id: "fr-1",
    consequence_revision_id: null,
    cited_accepted_evidence_ids: ["ev-1", "ev-2"],
    power_accepted_evidence_ids: null,
    state,
    reasons: [],
    accepted_evidence_ids: ["ev-1", "ev-2"],
    problematic_accepted_evidence_ids: [],
    publication_ids: [],
    source_classes: [],
    fixtures: [],
    runs: [],
    evidence: [],
    ...patch,
  };
}

function shown(p: SourceProvenance | null) {
  const { container } = render(<SourceProvenanceNotice provenance={p} subject="finding version" name="t" />);
  return container.querySelector("[data-source-provenance]") as HTMLElement;
}

describe("S4-05b stored source provenance notice", () => {
  it("labels only the two positive stored classes", () => {
    const authored = shown(block("AUTHORED_DEMONSTRATION", { publication_ids: ["pub-1", "pub-2"] }));
    expect(authored).toHaveAttribute("data-source-provenance", "AUTHORED_DEMONSTRATION");
    expect(authored).toHaveTextContent(
      "Prepared example data. These records were prepared for an example. They are not readings from physical equipment.",
    );
    expect(authored.querySelector("details")).not.toHaveAttribute("open");
    expect(authored).toHaveTextContent("pub-1, pub-2");
    const run = shown(block("REGISTERED_SIMULATION", { runs: [{ run_id: "run-1", run_identity_sha256: "x" }] }));
    expect(run).toHaveTextContent(
      "Generated test data. These records were generated for a test. They are not readings from physical equipment.",
    );
    expect(run).toHaveTextContent("run-1");
  });

  it("shows mixed and unknown sets with plain reasons and the exact problem records", () => {
    const mixed = shown(
      block("MIXED", {
        reasons: [{ code: "BOUND_AND_UNBOUND", accepted_evidence_ids: ["ev-2"] }],
        problematic_accepted_evidence_ids: ["ev-2"],
      }),
    );
    expect(mixed).toHaveTextContent(
      "Sources do not agree. The records behind this result have different or unverified sources. No current cost is shown.",
    );
    expect(mixed.querySelector("[data-source-reason='BOUND_AND_UNBOUND']")).toHaveTextContent(
      "Some readings have a confirmed source and some do not. (1 records)",
    );
    expect(mixed).toHaveTextContent("ev-2");
    expect(mixed).not.toHaveTextContent("BOUND_AND_UNBOUND");
    const unknown = shown(block("UNKNOWN", { reasons: [{ code: "NO_POSITIVE_BINDING", accepted_evidence_ids: ["ev-1"] }] }));
    expect(unknown).toHaveTextContent(
      "Source unverified. We cannot establish the source of all records behind this result. No current cost is shown.",
    );
    expect(unknown).not.toHaveTextContent("Prepared example data");
  });

  it("reads a missing block as unknown, never as demonstration", () => {
    const none = shown(null);
    expect(none).toHaveAttribute("data-source-provenance", "UNKNOWN");
    expect(none.querySelector("details")).toBeNull();
  });

  it("reads an unrecognised state (e.g. a later attested class) as Source unverified without throwing", () => {
    const later = shown(block("ATTESTED_REAL_SOURCE" as SourceState));
    expect(later).toHaveAttribute("data-source-provenance", "UNKNOWN");
    expect(later).toHaveTextContent("Source unverified.");
  });

  it("keeps the label visible outside the closed disclosure and to assistive technology", () => {
    render(<SourceProvenanceNotice provenance={block("REGISTERED_SIMULATION")} subject="cost" name="a11y" />);
    const label = screen.getByText("Generated test data.");
    expect(label.closest("details")).toBeNull();
    expect(label).toBeVisible();
  });

  it.each(["AUTHORED_DEMONSTRATION", "REGISTERED_SIMULATION", "MIXED", "UNKNOWN"] as SourceState[])(
    "passes the product vocabulary scan, disclosure included, for a populated %s set",
    (state) => {
      const { container } = render(
        <SourceProvenanceNotice
          provenance={block(state, {
            consequence_revision_id: "cr-1",
            power_accepted_evidence_ids: ["ev-3"],
            reasons:
              state === "MIXED"
                ? [
                    { code: "BOUND_AND_UNBOUND", accepted_evidence_ids: ["ev-2"] },
                    { code: "CROSSED_SOURCE_CLASSES", accepted_evidence_ids: ["ev-1", "ev-2"] },
                  ]
                : state === "UNKNOWN"
                  ? [{ code: "NO_POSITIVE_BINDING", accepted_evidence_ids: ["ev-1"] }]
                  : [],
            publication_ids: ["pub-1"],
            fixtures: [{ fixture_id: "s4-power-demo-cases-v1", fixture_version: "1" }],
            runs: [{ run_id: "run-2026-10-16-a", run_identity_sha256: "abc" }],
            problematic_accepted_evidence_ids: state === "MIXED" || state === "UNKNOWN" ? ["ev-2"] : [],
          })}
          subject="cost"
          name="vocab"
        />,
      );
      const { violations, scanned } = scanProductVocabulary(container, `source ${state}`);
      expect(scanned).toBeGreaterThan(0);
      expect(violations, describeViolations(violations)).toEqual([]);
    },
  );
});
