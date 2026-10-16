import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

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
    expect(authored).toHaveTextContent("Demonstration data.");
    expect(authored.querySelector("details")).not.toHaveAttribute("open");
    expect(authored).toHaveTextContent("pub-1, pub-2");
    const run = shown(block("REGISTERED_SIMULATION", { runs: [{ run_id: "run-1", run_identity_sha256: "x" }] }));
    expect(run).toHaveTextContent("Simulated data.");
    expect(run).toHaveTextContent("run-1");
  });

  it("shows mixed and unknown sets with plain reasons and the exact problem records", () => {
    const mixed = shown(
      block("MIXED", {
        reasons: [{ code: "BOUND_AND_UNBOUND", accepted_evidence_ids: ["ev-2"] }],
        problematic_accepted_evidence_ids: ["ev-2"],
      }),
    );
    expect(mixed).toHaveTextContent("Mixed sources.");
    expect(mixed.querySelector("[data-source-reason='BOUND_AND_UNBOUND']")).toHaveTextContent(
      "Some readings have a confirmed source and some do not. (1 records)",
    );
    expect(mixed).toHaveTextContent("ev-2");
    expect(mixed).not.toHaveTextContent("BOUND_AND_UNBOUND");
    const unknown = shown(block("UNKNOWN", { reasons: [{ code: "NO_POSITIVE_BINDING", accepted_evidence_ids: ["ev-1"] }] }));
    expect(unknown).toHaveTextContent("Source not confirmed.");
    expect(unknown).not.toHaveTextContent("Demonstration data");
  });

  it("reads a missing block as unknown, never as demonstration", () => {
    const none = shown(null);
    expect(none).toHaveAttribute("data-source-provenance", "UNKNOWN");
    expect(none.querySelector("details")).toBeNull();
  });
});
