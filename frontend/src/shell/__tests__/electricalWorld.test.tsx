import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import {
  isRunExecution,
  type RunExecution,
  type RunSetupClient,
  type RunSummary,
} from "../runSetupClient";
import { executionMethods } from "./executionFixtures";
import overcastPayload from "./kobo-overcast-execution.json";
import pcs22Payload from "./kobo-pcs-22-execution.json";

/**
 * T024: the electrical world on the Draft run screen.
 *
 * Both payloads were produced by the real backend, not written by hand:
 * `execution_payload` over a projection from the composed execution port, for a
 * Kobo Draft frozen by the real run setup service from the shipped template.
 * `kobo-overcast-execution.json` is the overcast scenario stepped to offset 600,
 * where the evening reserve override is in effect; `kobo-pcs-22-execution.json`
 * is the first step of a run whose PCS is limited to 22 kW against a 30 kW
 * deficit. A fixture with plausible round numbers would let a screen test pass
 * against a payload the backend never produces.
 *
 * Every claim is pinned to its own cell through a `data-` attribute, because the
 * requested and the accepted number sit side by side and a screen that merged
 * them would render every word these tests look for.
 */

const RUN_ID = "run-kobo-overcast";
const ENABLED = featureFlagsWith(true);

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const READY_RUN: RunSummary = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: "READY",
  created_at: "2026-09-29T09:00:00Z",
  site_id: "KOBO-001",
  scenario_id: "kobo-daytime-overcast",
  scenario_version: 1,
  frozen_inputs: [
    {
      identity_field: "site",
      field: "Site",
      value: "KOBO-001",
      answered_by: "SITE_FOUNDATION",
      answered_by_detail: "site KOBO-001 foundation version 1",
      blocking_statement: null,
    },
  ],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

function asExecution(payload: unknown): RunExecution {
  if (!isRunExecution(payload)) {
    throw new Error("the recorded payload no longer matches the client guard");
  }
  return payload;
}

function renderWith(execution: RunExecution) {
  const runSetup: RunSetupClient = {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: READY_RUN }),
    ...executionMethods({ status: "loaded", execution }),
  };
  return render(
    <MemoryRouter initialEntries={[`/simulator-lab/runs/${RUN_ID}`]}>
      <App
        flags={ENABLED}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

function cellOf(selector: string, attribute: string): HTMLElement {
  const row = document.querySelector(selector);
  if (row === null) {
    throw new Error(`no row ${selector}`);
  }
  const found = row.querySelector(`[${attribute}]`);
  if (found === null) {
    throw new Error(`no ${attribute} on ${selector}`);
  }
  return found as HTMLElement;
}

describe("the electrical world on the Draft run screen", () => {
  it("accepts both recorded backend payloads through the client guard", () => {
    expect(isRunExecution(overcastPayload)).toBe(true);
    expect(isRunExecution(pcs22Payload)).toBe(true);
  });

  it("keeps a 30 kW request and a 22 kW acceptance as two cells", async () => {
    renderWith(asExecution(pcs22Payload));
    await settledScreen();

    expect(
      screen.getByRole("heading", { name: "Requested versus accepted control" }),
    ).toBeTruthy();
    const row = '[data-control="battery-power"]';
    expect(cellOf(row, "data-control-requested").textContent).toBe("30 kW");
    expect(cellOf(row, "data-control-accepted").textContent).toBe("22 kW");
    expect(cellOf(row, "data-control-limited-by").textContent).toBe(
      "pcs-discharge-limit 22 kW",
    );
  });

  it("shows each load's demand and service on its own row", async () => {
    renderWith(asExecution(pcs22Payload));
    await settledScreen();

    const rows = document.querySelectorAll("[data-load]");
    expect(rows.length).toBe(3);
    // 39 kW of demand, 9 kW of PV and 22 kW accepted from the battery: 31 kW
    // served in critical-load priority - the clinic's 8 kW, the households'
    // 25 kW gets the remaining 23 - and the mill's 6 kW goes unserved.
    expect(
      cellOf('[data-load="load-demand@load-clinic"]', "data-load-unserved")
        .textContent,
    ).toBe("0 kW");
    expect(
      cellOf('[data-load="load-demand@load-res"]', "data-load-served")
        .textContent,
    ).toBe("23 kW");
    expect(
      cellOf('[data-load="load-demand@load-mill"]', "data-load-unserved")
        .textContent,
    ).toBe("6 kW");
  });

  it("names the override and its origin as the reserve in effect", async () => {
    renderWith(asExecution(overcastPayload));
    await settledScreen();

    expect(
      document.querySelector('[data-electrical-reserve="OVERRIDE"]')
        ?.textContent,
    ).toBe("15 % (override)");
    const effective = document.querySelector(
      '[data-effective-control="OVERRIDE"]',
    );
    expect(effective?.textContent).toContain(
      "scenario override evening-reserve-override",
    );
  });

  it("shows PV, the battery and service against simulation time", async () => {
    renderWith(asExecution(overcastPayload));
    await settledScreen();

    const steps = document.querySelectorAll("[data-electrical-step]");
    expect(steps.length).toBe(41);
    expect(steps[0]?.querySelector("th")?.textContent).toBe(
      "2026-09-22T03:00:00Z",
    );
  });

  it("shows an exact ratio approximately, with the exact text kept", async () => {
    renderWith(asExecution(overcastPayload));
    await settledScreen();

    const soc = document.querySelector("[data-electrical-soc-end] [data-exact]");
    expect(soc).not.toBeNull();
    const exact = soc?.getAttribute("data-exact") ?? "";
    if (exact.includes("/")) {
      expect(soc?.textContent).toMatch(/^≈ \d+\.\d\d %$/);
      expect(soc?.getAttribute("title")).toBe(`exactly ${exact} %`);
    } else {
      expect(soc?.textContent).toBe(`${exact} %`);
    }
  });

  it("renders no electrical panel for a model with no controller", async () => {
    renderWith({ ...asExecution(overcastPayload), electrical: null });
    await settledScreen();

    expect(
      screen.queryByRole("heading", {
        name: "Requested versus accepted control",
      }),
    ).toBeNull();
  });
});
