import { fireEvent, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type {
  SiteDetailReadModel,
  SiteDetailResult,
} from "../../sites/siteReadModel";
import { settledScreen } from "../../test/settled";
import {
  add,
  exactText,
  parseExact,
  readable,
} from "../exactArithmetic";
import { intervalTimeline, runTimeline } from "../historyTimelineModel";
import {
  bindDrawing,
  completedIntervalAt,
  drawnValue,
  drawingSlots,
} from "../intervalDrawingModel";
import type { RunHistory, RunHistoryDrawingContext } from "../runHistory";
import type {
  RunExecution,
  RunSetupClient,
  RunSummary,
} from "../runSetupClient";
import { executionMethods } from "./executionFixtures";
import executionPrefix from "./kobo-policy-execution-prefix.json";
import historyPrefix from "./kobo-policy-history-prefix.json";
import siteDetail from "./kobo-site-detail.json";

/**
 * Recorded interval inspection (T025d phase 1): the run-bound drawing, the
 * requested/accepted panel and the applied timeline at one selected boundary.
 *
 * All three fixtures are the backend's own serializations, written by
 * `host/tests/make_history_fixtures.py`: the policy-varied Kobo run stepped to
 * offset 150 with the generator status silenced from 60 for 30 minutes, and
 * the Kobo Site that run froze. The expected values below are read from the
 * raw flow records by hand, not from the model under test:
 *
 * - [60, 65): the battery discharges (battery_discharge_taken 600/19 kW,
 *   battery_to_load 30 kW), so its bus branch carries 30 kW TO the bus.
 * - [130, 135): it charges (battery_charge_stored 28.5 kW; pv_to_battery 4 +
 *   generator_to_battery 26 = 30 kW), so the same branch carries 30 kW FROM
 *   the bus - the reversal.
 * - The generator goes STOPPED -> STARTING at 40 in physical acceptance and
 *   STARTING -> RUNNING at 45 in apply-events.
 */

const HISTORY = historyPrefix as unknown as RunHistory;
const EXECUTION = executionPrefix as unknown as RunExecution;
const SITE = siteDetail as unknown as SiteDetailReadModel;
const LOADED: SiteDetailResult = { status: "loaded", site: SITE };
const CONTEXT = HISTORY.drawing_context as RunHistoryDrawingContext;
const RUN_ID = HISTORY.run_id;

function bound() {
  const binding = bindDrawing(CONTEXT, LOADED);
  if (binding.status !== "bound") {
    throw new Error(`expected a bound drawing, got ${binding.statement}`);
  }
  return binding;
}

function withSite(changes: (site: SiteDetailReadModel) => SiteDetailReadModel) {
  return {
    status: "loaded",
    site: changes(structuredClone(SITE)),
  } as SiteDetailResult;
}

describe("exact arithmetic over the wire's exact text", () => {
  it("adds ratios and decimals exactly and writes them back exactly", () => {
    const sum = add(parseExact("5/12")!, parseExact("0.75")!);
    expect(exactText(sum)).toBe("7/6");
    expect(exactText(add(parseExact("0.1")!, parseExact("0.2")!))).toBe("0.3");
    expect(exactText(add(parseExact("-3")!, parseExact("1.5")!))).toBe("-1.5");
    expect(exactText(add(parseExact("1/3")!, parseExact("-1/3")!))).toBe("0");
    expect(readable(parseExact("600/19")!)).toBe("600/19 (about 31.58)");
    expect(parseExact("abc")).toBeNull();
  });
});

describe("binding a run to the Site drawing", () => {
  it("binds only the frozen Site at the frozen Foundation version", () => {
    expect(CONTEXT.status).toBe("VERIFIED");
    expect(bindDrawing(CONTEXT, LOADED).status).toBe("bound");
  });

  it("refuses a changed Foundation, a missing connection and an unread Site", () => {
    const moved = bindDrawing(
      CONTEXT,
      withSite((s) => ({ ...s, foundation: { ...s.foundation, version: 2 } })),
    );
    expect(moved).toMatchObject({ status: "unavailable", code: "FOUNDATION_CHANGED" });

    const cut = bindDrawing(
      CONTEXT,
      withSite((s) => {
        s.foundation.topology!.connections = s.foundation.topology!.connections.filter(
          (c) => c.connection_id !== "pcs-to-bus",
        );
        return s;
      }),
    );
    expect(cut).toMatchObject({ status: "unavailable", code: "TOPOLOGY_DIFFERS" });

    expect(bindDrawing(CONTEXT, { status: "unavailable" })).toMatchObject({
      code: "SITE_UNREADABLE",
    });
    expect(bindDrawing(CONTEXT, null)).toMatchObject({ code: "SITE_PENDING" });
    expect(
      bindDrawing({ ...CONTEXT, status: "DISAGREES", attachments: [] }, LOADED),
    ).toMatchObject({ code: "DISAGREES" });
    expect(bindDrawing(null, LOADED)).toMatchObject({ code: "NO_CONTEXT" });
  });
});

describe("the drawing's values at one recorded interval", () => {
  it("shows discharge toward the bus over [60, 65)", () => {
    const slots = drawingSlots(bound(), HISTORY, 65);
    expect(slots.connections.get("pcs-to-bus")).toMatchObject({
      direction: "ALONG",
      text: "30 kW to AC bus",
    });
    expect(slots.connections.get("battery-to-pcs")?.direction).toBe("ALONG");
    expect(slots.connections.get("battery-to-pcs")?.text).toContain("600/19");
    expect(slots.nodes.get("battery")?.text).toMatch(/^discharging/);
    // Each load keeps its own address and its own served power.
    expect(slots.connections.get("bus-to-clinic")?.text).toBe(
      `5 kW to ${SITE.foundation.components.find((c) => c.component_id === "load-clinic")?.display_name}`,
    );
    expect(slots.nodes.get("load-mill")?.text).toBe("served 40 of 40 kW");
  });

  it("reverses the storage branch when the battery charges over [130, 135)", () => {
    const slots = drawingSlots(bound(), HISTORY, 135);
    const branch = slots.connections.get("pcs-to-bus");
    expect(branch?.direction).toBe("AGAINST");
    expect(branch?.text).toMatch(/^30 kW to /);
    expect(slots.connections.get("battery-to-pcs")?.direction).toBe("AGAINST");
    expect(slots.nodes.get("battery")?.text).toMatch(/^charging/);
    // The PV branch carries what it accepted (23 + 4), never its potential.
    expect(slots.connections.get("pv-inverter-to-bus")?.text).toMatch(/^27 kW/);
  });

  it("labels accounting values as values and draws no wire for them", () => {
    const slots = drawingSlots(bound(), HISTORY, 135);
    const pv = slots.nodes.get("pv-array");
    expect(pv?.detail.join(" ")).toContain(
      "pv_potential: 27 kW mean over [130, 135) - an accounting value, not a wire",
    );
    expect(slots.connections.get("pv-array-to-inverter")).toMatchObject({
      direction: "NONE",
      text: "no modeled flow",
    });
    expect(slots.nodes.get("ac-bus")?.text).toBe("Shared bus: aggregate transfer only");
  });

  it("states a zero flow as zero, distinct from no flow", () => {
    // [0, 5): the generator is STOPPED, so its recorded branch flows are
    // exactly zero - a stated 0 kW, not the "no modeled flow" of a connection
    // the model records nothing on.
    const slots = drawingSlots(bound(), HISTORY, 5);
    const generator = slots.connections.get("generator-to-bus");
    expect(generator).toMatchObject({ direction: "NONE", text: "0 kW" });
  });

  it("names the stock instant and the governing step", () => {
    const slots = drawingSlots(bound(), HISTORY, 45);
    const detail = slots.nodes.get("generator")?.detail.join(" | ") ?? "";
    expect(detail).toContain("generator-state RUNNING at 45 min (state at the instant)");
    expect(detail).toContain("generator-state STARTING during [40, 45) (state for the step)");
  });

  it("shows no flow at a boundary where no interval ended", () => {
    expect(completedIntervalAt(HISTORY, 0)).toBeNull();
    const slots = drawingSlots(bound(), HISTORY, 0);
    expect(slots.connections.get("pcs-to-bus")?.text).toBe("no interval ended here");
  });
});

describe("the applied timeline", () => {
  it("places each discrete transition in the state its phase governs", () => {
    const at40 = intervalTimeline(HISTORY, 40).filter(
      (e) => e.kind === "Discrete transition",
    );
    expect(at40).toHaveLength(1);
    expect(at40[0]).toMatchObject({ phase: "physical-acceptance", agrees: true });
    expect(at40[0].applies).toContain("the step beginning at 40 min");

    const at45 = intervalTimeline(HISTORY, 45).filter(
      (e) => e.kind === "Discrete transition",
    );
    // The step decision at 40 governed [40, 45); the apply-events at 45 is state at 45.
    expect(at45.map((e) => e.phase).sort()).toEqual([
      "apply-events",
      "physical-acceptance",
    ]);
    expect(at45.every((e) => e.agrees === true)).toBe(true);
  });

  it("carries interval-wide causes with their span, share and origin", () => {
    const applied = intervalTimeline(HISTORY, 80).filter((e) => e.lane === "APPLIED");
    const evolution = applied.filter((e) => e.origin === "ACCEPTED_FLOW");
    expect(evolution.length).toBeGreaterThan(0);
    for (const entry of evolution) {
      expect(entry.span).toEqual([75, 80]);
      expect(entry.phase).toBe("evolve");
      expect(entry.share).toBe("1");
    }
    expect(applied.some((e) => e.kind === "Forcing level in effect")).toBe(true);
  });

  it("keeps a reporting gap in the reporting lane, never as a physical outage", () => {
    const at75 = intervalTimeline(HISTORY, 75);
    const gap = at75.find((e) => e.kind === "Reporting condition");
    expect(gap).toMatchObject({ lane: "REPORTING", span: [60, 90] });
    expect(
      at75.some(
        (e) => e.kind === "Observation attempt" && e.origin === "SUPPRESSED_BY_GAP",
      ),
    ).toBe(true);
    expect(at75.some((e) => e.lane === "PHYSICAL" && /gap/i.test(e.detail))).toBe(false);
  });

  it("groups a contiguous cause over the whole run and keeps its count", () => {
    const override = runTimeline(HISTORY).find((e) =>
      e.source.startsWith("stop-threshold-override"),
    );
    expect(override?.span).toEqual([0, 155]);
    expect(override?.count).toBe(31);
    expect(
      runTimeline(HISTORY).some(
        (e) => e.kind === "Observation attempt" && e.origin === "REPORTED",
      ),
    ).toBe(false);
  });
});

// --- On the run screen ---------------------------------------------------------

const RUN: RunSummary = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: null,
  created_at: "2026-09-22T09:00:00Z",
  site_id: "KOBO-001",
  scenario_id: "kobo-mini-grid-stop-60",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
  template_lineage: { state: "RECORDED", template_id: "hybrid-mini-grid-100kw", template_version: 2 },
};

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

function client(): RunSetupClient {
  return {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: RUN }),
    ...executionMethods(
      { status: "loaded", execution: EXECUTION },
      undefined,
      { status: "loaded", history: HISTORY },
    ),
  };
}

async function renderWith(site: SiteDetailResult) {
  const detail: SiteDetailClient = { getSite: () => Promise.resolve(site) };
  render(
    <MemoryRouter initialEntries={[`/simulator-lab/runs/${RUN_ID}`]}>
      <App
        flags={featureFlagsWith(true)}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        siteDetail={detail}
        runSetup={client()}
      />
    </MemoryRouter>,
  );
  await settledScreen();
}

function select(offset: number): void {
  // T025e: the one history cursor; the raw records have no select of their own.
  const index = HISTORY.boundaries.findIndex((b) => b.offset_minutes === offset);
  const range = document.getElementById("history-cursor-range") as HTMLInputElement;
  fireEvent.change(range, { target: { value: String(index) } });
}

function one(selector: string): HTMLElement {
  const found = document.querySelector<HTMLElement>(selector);
  if (found === null) throw new Error(`nothing matches ${selector}`);
  return found;
}

describe("one selected interval on the run screen", () => {
  it("draws, inspects and times the same recorded interval", async () => {
    await renderWith(LOADED);
    await waitFor(() => one("[data-drawing-bound]"));
    select(135);

    expect(one("[data-drawing-boundary]").dataset.drawingBoundary).toBe("135");
    const branch = one('[data-sld-connection-value="pcs-to-bus"]');
    expect(branch.dataset.sldDirection).toBe("AGAINST");
    // The drawn label is short (it has to fit a lattice gap); the full
    // statement is its title and its row in the contents table.
    const drawn = Array.from(branch.childNodes)
      .filter((node) => node.nodeType === Node.TEXT_NODE)
      .map((node) => node.textContent)
      .join("");
    expect(drawn).toBe("30 kW");
    expect(branch.querySelector("title")?.textContent).toMatch(
      /^30 kW to .*, against the declared order\)$/,
    );
    expect(one('[data-sld-connection-row="pcs-to-bus"]').textContent).toContain(
      "against the declared order",
    );
    // The control panel reads the same interval, not the latest one.
    expect(one("[data-interval-span]").dataset.intervalSpan).toBe("130-135");
    const battery = one('[data-interval-control="battery-power at battery-state-of-charge@battery"]');
    expect(battery.textContent).toContain(
      completedIntervalAt(HISTORY, 135)!.requests.find(
        (r) => r.quantity === "battery-power",
      )!.reason,
    );
    const generator = one('[data-interval-control="generator-run at generator-state@generator"]');
    expect(generator.textContent).toContain("not limited");
    expect(one('[data-interval-balance="site-sources-and-sinks"]').dataset.balanceHolds).toBe("yes");
    expect(document.querySelectorAll("[data-interval-load]")).toHaveLength(3);

    select(0);
    expect(one("[data-interval-none]").dataset.intervalNone).toBe("0");
  });

  it("uses the historical interval, never the latest step's values", async () => {
    await renderWith(LOADED);
    await waitFor(() => one("[data-drawing-bound]"));
    select(65);
    expect(one('[data-sld-connection-value="pcs-to-bus"]').dataset.sldDirection).toBe(
      "ALONG",
    );
    expect(one("[data-interval-span]").dataset.intervalSpan).toBe("60-65");
    const latest = HISTORY.intervals[HISTORY.intervals.length - 1];
    expect(latest.from_offset).not.toBe(60);
  });

  it("says the drawing is unavailable when the Site's Foundation moved on", async () => {
    await renderWith(
      withSite((s) => ({ ...s, foundation: { ...s.foundation, version: 2 } })),
    );
    const refusal = await waitFor(() => {
      const found = one("[data-drawing-unavailable]");
      expect(found.dataset.drawingUnavailable).not.toBe("SITE_PENDING");
      return found;
    });
    expect(refusal.dataset.drawingUnavailable).toBe("FOUNDATION_CHANGED");
    expect(document.querySelector("[data-sld-connection-value]")).toBeNull();
    // Numerical inspection is unaffected.
    expect(document.querySelector("[data-interval-span], [data-interval-none]")).not.toBeNull();
  });

  it("labels a held STALE reading with its own support (backlog C1)", async () => {
    await renderWith(LOADED);
    select(65);
    const cursor = document.getElementById("history-cursor-range") as HTMLInputElement;
    fireEvent.change(cursor, {
      target: {
        value: String(HISTORY.boundaries.findIndex((b) => b.offset_minutes === 65)),
      },
    });
    const row = Array.from(
      document.querySelectorAll<HTMLElement>("[data-value-row]"),
    ).find((r) => (r.dataset.valueRow ?? "").includes("generator-controller-status"));
    expect(row).toBeDefined();
    expect(row!.textContent).toContain("state at that instant, 45 min");
    expect(row!.textContent).toContain("the held reading's own support");
  });
});

describe("the value drawn on a line", () => {
  it("is exact when short and marked approximate otherwise", () => {
    expect(drawnValue(parseExact("30")!)).toBe("30");
    expect(drawnValue(parseExact("12.5")!)).toBe("12.5");
    // 600/19 kW: the exact text would overlap the boxes a 60 px gap separates.
    expect(drawnValue(parseExact("600/19")!)).toBe("~31.6");
    expect(drawnValue(parseExact("0.123456")!)).toBe("~0.1");
  });
});
