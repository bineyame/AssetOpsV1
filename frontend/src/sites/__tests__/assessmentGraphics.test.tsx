/**
 * T028 presentation checkpoint 2a: the four assessment graphics against the
 * failure modes in spec section 5 (D-2026-10-04-plain-language-analysis-views):
 * timeline geometry against supplied times, open ends, unrecorded and
 * bracketed time, missing versus zero inputs, range endpoints, unavailable fuel
 * with no zero bar, zero evaluated parts as "Not assessed", and the selected
 * part staying the same assessment's part. Not SVG node counts.
 */
import React from "react";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { AssessmentAnalysis } from "../assessmentAnalysis";
import {
  AssessedPeriodTimeline,
  CoverageByInput,
  FuelRange,
  ReportedValues,
  niceMax,
  timelineGeometry,
  type TimelineSource,
} from "../assessmentGraphics";
import type { Assessment, AssessmentSummary, Segment, SegmentInputs } from "../siteAnalyticsClient";
import { CANDIDATE_ASSESSMENT, CANDIDATE_ID, CANDIDATE_SUMMARY } from "./analyticsFixtures";

afterEach(cleanup);

const T = (hhmm: string) => `2026-09-22T${hhmm}:00Z`;

const INPUTS: SegmentInputs = {
  load_kw: "18",
  pv_available_kw: "0",
  soc_pct: "82",
  reserve_pct: "30",
  discharge_capability_kw: null,
  generator_kw: "20",
  reserve_source: "policy",
};

function seg(start: string, end: string, minutes: number, classification: Segment["classification"], observed = true): Segment {
  return {
    start: T(start),
    end: T(end),
    minutes,
    observed,
    classification,
    label: "",
    binding_constraint: null,
    reasons: [],
    missing: [],
    inputs: observed
      ? { at_start: INPUTS, at_end: { ...INPUTS, load_kw: "25", generator_kw: "0" } }
      : {},
    evidence: [],
  };
}

/** Bracketed both ends: off at 03:00, operating 03:15..04:45, off at 05:00. */
const BRACKETED: TimelineSource & { segments: Segment[] } = {
  assessed_window: { start: T("03:00"), end: T("05:00") },
  interval: {
    first_running_observed: T("03:15"),
    last_running_observed: T("04:45"),
    last_stopped_before: T("03:00"),
    first_stopped_after: T("05:00"),
    open_start: false,
    open_end: false,
  },
  segments: [
    seg("03:15", "04:00", 45, "CANDIDATE_AVOIDABLE"),
    seg("04:00", "04:15", 15, "INDETERMINATE", false),
    seg("04:15", "04:45", 30, "NECESSARY"),
  ],
};

/** No record of the generator off on either side. */
const OPEN: TimelineSource = {
  assessed_window: { start: T("03:15"), end: T("04:45") },
  interval: {
    first_running_observed: T("03:15"),
    last_running_observed: T("04:45"),
    last_stopped_before: null,
    first_stopped_after: null,
    open_start: true,
    open_end: true,
  },
  segments: [seg("03:15", "04:45", 90, "CANDIDATE_AVOIDABLE")],
};

const OUTCOMES = ["Possibly avoidable", "Cannot determine", "Needed"];

function inRouter(node: React.ReactNode, path = "/") {
  return render(<MemoryRouter initialEntries={[path]}>{node}</MemoryRouter>);
}

describe("assessed-period timeline", () => {
  it("places every band at its supplied times, bracketed time apart from the parts", () => {
    const g = timelineGeometry(BRACKETED);
    expect(g).not.toBeNull();
    expect(g?.start).toBe(T("03:00"));
    expect(g?.end).toBe(T("05:00"));
    expect(g?.bands.map((b) => [b.kind, b.index, b.x, b.width])).toEqual([
      ["uncertain-start", null, 0, 0.125],
      ["part", 0, 0.125, 0.375],
      ["part", 1, 0.5, 0.125],
      ["part", 2, 0.625, 0.25],
      ["uncertain-end", null, 0.875, 0.125],
    ]);
  });

  it("a short part keeps its true width: no minimum inflates it", () => {
    const g = timelineGeometry({
      ...OPEN,
      assessed_window: { start: T("03:00"), end: T("11:00") },
      interval: { ...OPEN.interval, first_running_observed: T("03:00"), last_running_observed: T("11:00") },
      segments: [seg("03:00", "03:01", 1, "CANDIDATE_AVOIDABLE"), seg("03:01", "11:00", 479, "NECESSARY")],
    });
    expect(g?.bands.map((b) => b.width)).toEqual([1 / 480, 479 / 480]);
  });

  it("draws unrecorded operation hatched and bracketed time dotted, never as a claim", () => {
    inRouter(<AssessedPeriodTimeline source={BRACKETED} outcomes={OUTCOMES} reasons={["a", "b", "c"]} />);
    const kinds = Array.from(document.querySelectorAll("[data-band]")).map((b) => [
      b.getAttribute("data-band"),
      b.getAttribute("data-band-kind"),
      b.getAttribute("data-x"),
      b.getAttribute("data-width"),
    ]);
    expect(kinds).toEqual([
      ["uncertain-start", "uncertain", "0.000000", "0.125000"],
      ["part", "avoidable", "0.125000", "0.375000"],
      ["part", "unrecorded", "0.500000", "0.125000"],
      ["part", "needed", "0.625000", "0.250000"],
      ["uncertain-end", "uncertain", "0.875000", "0.125000"],
    ]);
    // The readable equivalent has the same labels and times, including the bracketed spans.
    const table = document.querySelector("[data-timeline-table]") as HTMLElement;
    const rows = within(table).getAllByRole("row").slice(1).map((r) => r.textContent);
    expect(rows[0]).toContain("03:00 UTC to 03:15 UTC");
    expect(rows[0]).toContain("Start or stop time uncertain");
    expect(rows[2]).toContain("04:00 UTC to 04:15 UTC (15 min)");
    expect(rows[2]).toContain("Cannot determine; generator operation not recorded");
    expect(rows[4]).toContain("04:45 UTC to 05:00 UTC");
    // Legend: the three outcome labels and both patterns, in words.
    const legend = Array.from(document.querySelectorAll("[data-legend]")).map((l) => l.textContent);
    expect(legend).toEqual([
      "Needed",
      "Possibly avoidable",
      "Cannot determine",
      "Generator operation not recorded",
      "Start or stop time uncertain",
    ]);
    expect(screen.getByText(/Assessed period, 22 Sep 2026, 03:00 to 05:00 UTC/)).toBeInTheDocument();
    expect(document.querySelector("[data-open-end]")).toBeNull();
  });

  it("marks and explains an open start and end without inventing a time", () => {
    inRouter(<AssessedPeriodTimeline source={OPEN} outcomes={["Possibly avoidable"]} />);
    expect(document.querySelector('[data-open-end="start"]')).not.toBeNull();
    expect(document.querySelector('[data-open-end="end"]')).not.toBeNull();
    expect(document.querySelectorAll('[data-band-kind="uncertain"]')).toHaveLength(0);
    // The axis ends at the last supplied time; nothing is drawn past it.
    expect(document.querySelector("[data-axis-end]")).toHaveTextContent("04:45 UTC");
    const notes = Array.from(document.querySelectorAll("[data-open-note]")).map((n) => n.textContent);
    expect(notes).toEqual([
      "Start not recorded: no record shows the generator off before 22 Sep 2026 03:15 UTC, so it may have been operating earlier.",
      "End not recorded: no record shows the generator off after 22 Sep 2026 04:45 UTC, so when it stopped is not known.",
    ]);
    expect(screen.getByRole("img").getAttribute("aria-label")).toContain("End not recorded");
  });

  it("compact form keeps the period, its text equivalent and only the kinds present", () => {
    inRouter(<AssessedPeriodTimeline compact source={OPEN} outcomes={["Possibly avoidable"]} />);
    expect(document.querySelector("[data-timeline-table]")).toBeNull();
    expect(screen.getByRole("img")).toHaveAccessibleName(
      "Assessed parts of the period: 03:15 UTC to 04:45 UTC, Possibly avoidable. " +
        "Start not recorded: no record shows the generator off before 22 Sep 2026 03:15 UTC, so it may have been operating earlier. " +
        "End not recorded: no record shows the generator off after 22 Sep 2026 04:45 UTC, so when it stopped is not known.",
    );
    expect(Array.from(document.querySelectorAll("[data-legend]")).map((l) => l.textContent)).toEqual([
      "Possibly avoidable",
    ]);
  });

  it("an unreadable time is said, not drawn", () => {
    inRouter(
      <AssessedPeriodTimeline
        source={{ ...OPEN, assessed_window: { start: "not a time", end: T("04:45") } }}
        outcomes={["Possibly avoidable"]}
      />,
    );
    expect(document.querySelector("[data-timeline-unavailable]")).not.toBeNull();
    expect(document.querySelector("[data-band]")).toBeNull();
  });
});

describe("estimated fuel range", () => {
  const reading = {
    label: "Estimated fuel associated with possibly avoidable operation",
    text: "21.6 to 29.3 litres",
    note: "This is an estimate, not confirmed fuel savings.",
  };

  it("draws the low-to-high interval at its endpoints on a zero-based litre scale", () => {
    inRouter(<FuelRange fuel={{ status: "BOUNDED", low_litres: "21.6", high_litres: "29.3" }} reading={reading} />);
    const figure = document.querySelector('[data-graphic="fuel-range"]') as HTMLElement;
    expect(niceMax(29.3)).toBe(50);
    expect(figure).toHaveAttribute("data-fuel-low", (21.6 / 50).toFixed(6));
    expect(figure).toHaveAttribute("data-fuel-high", (29.3 / 50).toFixed(6));
    expect(figure).toHaveTextContent("0 litres");
    expect(figure).toHaveTextContent("50 litres");
    expect(figure.querySelector("[data-fuel-text]")).toHaveTextContent("Low 21.6 litres to high 29.3 litres");
    expect(figure).toHaveTextContent("not confirmed fuel savings");
    expect(figure.querySelector("figcaption")).toHaveTextContent(reading.label);
  });

  it.each(["UNAVAILABLE", "NOT_APPLICABLE"])("%s fuel shows the backend reason and no bar at zero", (status) => {
    const note = "No fuel estimate: the generator's output was not reported for the possibly avoidable time.";
    inRouter(<FuelRange fuel={{ status }} reading={{ ...reading, text: null, note }} />);
    const block = document.querySelector('[data-graphic="fuel-range"]') as HTMLElement;
    expect(block).toHaveAttribute("data-fuel-unavailable", status);
    expect(block).toHaveTextContent(note);
    expect(block.querySelector("svg")).toBeNull();
    expect(block.textContent).not.toMatch(/\b0 litres\b/);
  });
});

describe("reported values for one part", () => {
  function Values({ which = "start" as "start" | "end", segment = BRACKETED.segments[0] }) {
    return <ReportedValues segment={segment} which={which} onWhich={() => undefined} partLabel="Part 1 of 3" />;
  }

  it("a missing input has no bar; a zero has a zero-width bar; kW share one zero-based scale", () => {
    inRouter(<Values />);
    const row = (id: string) => document.querySelector(`[data-value-row="${id}"]`) as HTMLElement;
    expect(row("discharge_capability_kw")).toHaveAttribute("data-missing", "true");
    expect(row("discharge_capability_kw")).toHaveTextContent("Not reported");
    expect(row("discharge_capability_kw").querySelector("svg")).toBeNull();
    expect(row("pv_available_kw")).toHaveTextContent("0 kW");
    expect(row("pv_available_kw").querySelector("svg")).toHaveAttribute("data-bar-width", "0.000000");
    // Scale max niceMax(20) = 20: demand 18 kW is 0.9, generator 20 kW is 1.
    expect(row("load_kw").querySelector("svg")).toHaveAttribute("data-bar-width", "0.900000");
    expect(row("generator_kw").querySelector("svg")).toHaveAttribute("data-bar-width", "1.000000");
    // Battery charge and reserve on their own 0-100 % scale.
    expect(row("soc_pct").querySelector("svg")).toHaveAttribute("data-bar-width", "0.820000");
    expect(row("reserve_pct")).toHaveTextContent("30 % (site setting)");
  });

  it("switches between the two supplied sets, labelled as values used, not samples", () => {
    function Switching() {
      const [which, setWhich] = React.useState<"start" | "end">("start");
      return <ReportedValues segment={BRACKETED.segments[0]} which={which} onWhich={setWhich} partLabel="Part 1 of 3" />;
    }
    inRouter(<Switching />);
    const end = screen.getByRole("button", { name: "Values used at the end of the assessed part" });
    expect(end).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(end);
    expect(end).toHaveAttribute("aria-pressed", "true");
    expect(document.querySelector('[data-value-row="load_kw"]')).toHaveTextContent("25 kW");
    expect(document.querySelector('[data-value-row="generator_kw"]')).toHaveTextContent("0 kW");
    expect(screen.getByText(/values used at the end of the assessed part, 22 Sep 2026 04:00 UTC/)).toBeInTheDocument();
  });

  it("a part without recorded operation has no values and no bars", () => {
    inRouter(<Values segment={BRACKETED.segments[1]} />);
    expect(document.querySelector("[data-values-none]")).toHaveTextContent("no values");
    expect(document.querySelector("svg")).toBeNull();
  });
});

describe("record coverage by input", () => {
  it("zero assessed parts reads Not assessed with no bar; counts use the parts denominator", () => {
    inRouter(
      <CoverageByInput
        inputs={[
          { input: "soc", label: "Battery SOC", usable_segments: 15, evaluated_segments: 16, gaps: [] },
          { input: "load", label: "Load", usable_segments: 0, evaluated_segments: 0, gaps: [] },
          {
            input: "discharge_capability",
            label: "Discharge capability",
            usable_segments: 0,
            evaluated_segments: 4,
            gaps: [{ start: T("05:00"), end: T("05:15"), minutes: "15" }],
          },
        ]}
        unobserved={[{ start: T("04:00"), end: T("04:15"), minutes: "15" }]}
        words={{ soc: "Battery charge", load: "Site demand", discharge_capability: "Available battery output" }}
      />,
    );
    const row = (id: string) => document.querySelector(`[data-coverage-input="${id}"]`) as HTMLElement;
    expect(row("soc")).toHaveTextContent("Battery charge15 of 16");
    expect(row("soc").querySelector("svg")).toHaveAttribute("data-bar-width", (15 / 16).toFixed(6));
    expect(row("load")).toHaveTextContent("Site demandNot assessed");
    expect(row("load").querySelector("svg")).toBeNull();
    expect(row("load").textContent).not.toMatch(/%/);
    // Evaluated but never usable is a zero count, distinct from not assessed.
    expect(row("discharge_capability")).toHaveTextContent("0 of 4");
    expect(row("discharge_capability")).toHaveTextContent("22 Sep 2026, 05:00 to 05:15 UTC (15 min)");
    expect(document.querySelector("caption")).toHaveTextContent("assessed parts of this period");
    expect(document.querySelector("caption")).toHaveTextContent("not shares of elapsed time");
    expect(document.querySelector("[data-coverage-unobserved]")).toHaveTextContent(
      "Generator operation not recorded: 22 Sep 2026, 04:00 to 04:15 UTC (15 min)",
    );
  });
});

describe("the selected part stays this assessment's part", () => {
  const assessment: Assessment = { ...CANDIDATE_ASSESSMENT, segments: BRACKETED.segments };
  const summary: AssessmentSummary = {
    ...CANDIDATE_SUMMARY,
    reading: {
      ...CANDIDATE_SUMMARY.reading!,
      segments: [
        { outcome: "Possibly avoidable", reason: "Solar and battery could have met demand.", missing: [] },
        { outcome: "Cannot determine", reason: "Generator operation was not recorded.", missing: [] },
        { outcome: "Needed", reason: "Battery charge was at its minimum reserve.", missing: [] },
      ],
    },
  };

  function Where() {
    const location = useLocation();
    return <output data-testid="where">{location.search}</output>;
  }

  function renderAnalysis(search: string) {
    return render(
      <MemoryRouter initialEntries={[`/a${search}`]}>
        <Routes>
          <Route
            path="/a"
            element={
              <>
                <AssessmentAnalysis
                  summary={summary}
                  assessment={assessment}
                  records={{ kind: "tab", href: "/evidence" }}
                  alternativesHref={null}
                />
                <Where />
              </>
            }
          />
        </Routes>
      </MemoryRouter>,
    );
  }

  it("a direct link selects its part in the timeline, the values and the records", () => {
    renderAnalysis("?part=3");
    const analysis = document.querySelector(`[data-analysis="${CANDIDATE_ID}"]`) as HTMLElement;
    expect(analysis.querySelector('[data-graphic="assessed-period-timeline"]')).toHaveAttribute(
      "data-graphic-assessment",
      CANDIDATE_ID,
    );
    expect(analysis.querySelector("[data-analysis-selected-part]")).toHaveAttribute("data-analysis-selected-part", "3");
    expect(analysis.querySelector('[data-graphic="reported-values"]')).toHaveAttribute(
      "data-values-part-start",
      BRACKETED.segments[2].start,
    );
    expect(analysis.querySelector(".period-timeline__band.is-selected")).toHaveAttribute("data-part", "2");
    expect(analysis.querySelector("[data-analysis-selected-part]")).toHaveTextContent(
      "Part 3 of 3, 22 Sep 2026, 04:15 to 04:45 UTC: Needed.",
    );
  });

  it("the parts table selects by keyboard-usable buttons and keeps the choice in the address", () => {
    renderAnalysis("");
    // Default: the first recorded part with the period's own outcome (Possibly avoidable).
    expect(document.querySelector("[data-analysis-selected-part]")).toHaveAttribute("data-analysis-selected-part", "1");
    const button = document.querySelector('[data-select-part="2"]') as HTMLButtonElement;
    expect(button.tagName).toBe("BUTTON");
    fireEvent.click(button);
    expect(screen.getByTestId("where")).toHaveTextContent("?part=2");
    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(document.querySelector("[data-values-none]")).not.toBeNull();
  });

  it("a part not in this period is said so", () => {
    renderAnalysis("?part=9");
    expect(document.querySelector("[data-analysis-part-missing]")).toHaveTextContent(
      "Part 9 is not in this assessed period",
    );
  });
});
