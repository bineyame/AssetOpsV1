import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GapGroup } from "../GapGroup";
import { groupGaps, type GapItem } from "../gapGroup";

const NA = "No cold assessment for this window";

describe("groupGaps (UQ-FI-2, D-UQFI.4)", () => {
  it("groups by exact fact and keeps subject order", () => {
    const lines = groupGaps([
      { subject: "Temperature", fact: NA }, { subject: "Power", fact: "Not available yet" }, { subject: "Doors", fact: NA },
    ]);
    expect(lines).toEqual([
      { fact: NA, subjects: [{ subject: "Temperature" }, { subject: "Doors" }] },
      { fact: "Not available yet", subjects: [{ subject: "Power" }] },
    ]);
  });

  it("never merges different reasons or near-identical facts", () => {
    const lines = groupGaps([
      { subject: "A", fact: "Not available yet", reason: "NO_READINGS" },
      { subject: "B", fact: "Not available yet", reason: "NOT_ANALYSED" },
      { subject: "C", fact: "Not available yet." },
      { subject: "D", fact: "not available yet" },
    ]);
    expect(lines.map((l) => l.subjects.map((s) => s.subject))).toEqual([["A"], ["B"], ["C"], ["D"]]);
  });

  it("orders lines by D-E5.46 precedence, other facts first-seen", () => {
    const lines = groupGaps([
      { subject: "x", fact: "Unknown" },
      { subject: "a", fact: "Not analysed yet" },
      { subject: "b", fact: "Still processing" },
      { subject: "c", fact: "Readings for this day conflict" },
      { subject: "d", fact: "No readings received for this day" },
      { subject: "e", fact: "Not enough readings received to analyse this day" },
      { subject: "y", fact: "Not worked out yet" },
    ]);
    expect(lines.map((l) => l.subjects[0].subject)).toEqual(["d", "c", "e", "a", "b", "x", "y"]);
  });

  it("preserves every gap id on its subject", () => {
    const items: GapItem[] = [
      { subject: "P", fact: "not assessed", gapId: "GAP-1" }, { subject: "C", fact: "not assessed", gapId: "GAP-2" },
    ];
    expect(groupGaps(items)[0].subjects).toEqual([{ subject: "P", gapId: "GAP-1" }, { subject: "C", gapId: "GAP-2" }]);
  });
});

describe("<GapGroup>", () => {
  it("renders one line per fact; fact and subjects are separate nodes, nothing composed", () => {
    const { container } = render(
      <section>
        <GapGroup
          items={[{ subject: "Temperature", fact: NA, gapId: "G1" }, { subject: "Doors", fact: NA, gapId: "G2" }]}
          renderSingle={(it) => <p>{it.fact}</p>}
        />
      </section>,
    );
    const lines = container.querySelectorAll(".gap-group");
    expect(lines).toHaveLength(1);
    expect(screen.getByText(NA).className).toBe("gap-group__fact");
    const subjects = [...container.querySelectorAll(".gap-group__subject")];
    expect(subjects.map((li) => [li.textContent, li.getAttribute("data-gap-id")])).toEqual([["Temperature", "G1"], ["Doors", "G2"]]);
    expect(container.textContent).not.toContain(`${NA}:`);
  });

  it("renders a single gap exactly as today", () => {
    const { container } = render(
      <GapGroup items={[{ subject: "Power", fact: "Not available yet" }]} renderSingle={(it) => <p className="today">{it.subject} {it.fact}</p>} />,
    );
    expect(container.innerHTML).toBe('<p class="today">Power Not available yet</p>');
  });

  it("renders the subject through renderSubject (a MissingClaim keeps its own gap id)", () => {
    const { container } = render(
      <GapGroup
        items={[{ subject: "Priority", fact: "not assessed", gapId: "G1" }, { subject: "Confidence", fact: "not assessed", gapId: "G2" }]}
        renderSingle={() => null}
        renderSubject={(it) => <span data-gap-id={it.gapId}>{it.subject}</span>}
      />,
    );
    expect([...container.querySelectorAll("[data-gap-id]")].map((n) => n.getAttribute("data-gap-id"))).toEqual(["G1", "G2"]);
  });
});
