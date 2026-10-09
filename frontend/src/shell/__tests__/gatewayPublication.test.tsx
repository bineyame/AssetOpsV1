import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import {
  PUBLICATION_REFUSAL_KINDS,
  createRunSetupClient,
  isGatewayDiagnostics,
  isRunPublicationSchedule,
  type AdvancePublicationResult,
  type GatewayDiagnostics,
  type GatewayLedgerStage,
  type RunCommitResult,
  type RunPublicationSchedule,
  type RunSetupClient,
  type RunSummary,
} from "../runSetupClient";
import { RUNNING_IN_THE_GAP, executionMethods } from "./executionFixtures";

/**
 * S2-01c: a registered RUN_VIRTUAL run's delayed-publication schedule, the
 * publication-clock advance with its six refusals, and the local gateway's
 * diagnostics. Each instant names its clock; an unavailable gateway or an
 * absent schedule is never shown as an empty queue.
 */

const RUN_ID = "run-2a0c2b7a4e5d4c8fa1b2c3d4e5f60718";
const URL = `/simulator-lab/runs/${RUN_ID}`;
const SOURCE = "5d1e8a90-0000-4000-8000-00000000000a";

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const RUN = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "COMPLETED",
  readiness_disclosure: null,
  created_at: "2026-10-08T09:00:00Z",
  site_id: "KOBO-001",
  scenario_id: "kobo-daytime-post-run-publication",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
  template_lineage: { state: "NOT_RECORDED" },
} as unknown as RunSummary;

const LEDGER: GatewayLedgerStage = {
  store: "GATEWAY_LEDGER",
  run_id: RUN_ID,
  status: "STAGED",
  statement: "Every admitted envelope is sealed. Upload is pending.",
  execution_status: "COMPLETED",
  release_eligible: false,
  snapshot_sha256: "ab".repeat(32),
  site_id: "site-a",
  gateway_id: "gateway-a",
  sequence_epoch: "1",
  upload_state: "PENDING",
  upload_statement: "Upload pending: no batch has been sent and no receipt exists.",
  receipts: [],
  unavailable_detail: null,
  publication_notes: [],
  queue_depth_by_state: {},
  envelopes: [],
  batches: [],
  holds: [],
  seal_refusals: [],
};

const CLOCK_LABELS = {
  source_time: "SOURCE_TIME",
  scheduled_release_at: "RUN_VIRTUAL_SCHEDULED",
  clock_instant: "RUN_VIRTUAL",
  admitted_through: "RUN_VIRTUAL",
  ordinary_stopped_at: "RUN_VIRTUAL",
  released_at_clock: "RUN_VIRTUAL",
  published_at: "GATEWAY_STAMPED_RUN_VIRTUAL",
};

function report(overrides: Partial<RunPublicationSchedule["reports"][number]>) {
  return {
    report_key: "soc-1500",
    device_id: "bms-1",
    signal_id: "battery_soc",
    source_time: "2026-09-30T15:00:00Z",
    scheduled_release_at: "2026-09-30T15:05:00Z",
    state: "PENDING",
    released_at_clock: null,
    message_id: null,
    sequence: null,
    outcome: null,
    published_at: null,
    ...overrides,
  };
}

const PENDING_AT_END: RunPublicationSchedule = {
  store: "LAB_PUBLICATION_SCHEDULE",
  run_id: RUN_ID,
  status: "AVAILABLE",
  detail: null,
  publication_clock: "RUN_VIRTUAL",
  statement: "Lab-private schedule of this run's delayed public reports.",
  clock_labels: CLOCK_LABELS,
  clock_instant: "2026-09-30T15:00:00Z",
  world_reached_instant: "2026-09-30T15:00:00Z",
  world_complete: true,
  admitted_through: "2026-09-30T15:00:00Z",
  ordinary_publication: "COMPLETE",
  ordinary_stopped_at: null,
  pending_count: 1,
  released_count: 1,
  reports: [
    report({
      report_key: "soc-1045",
      source_time: "2026-09-30T10:45:00Z",
      scheduled_release_at: "2026-09-30T10:55:00Z",
      state: "RELEASED",
      released_at_clock: "2026-09-30T11:00:00Z",
      message_id: "msg-1045",
      sequence: 44,
      outcome: "ADMITTED",
      published_at: "2026-09-30T11:00:00Z",
    }),
    report({}),
  ],
};

/** After an advance that jumped past due: published at the later instant. */
const RELEASED_AFTER_END: RunPublicationSchedule = {
  ...PENDING_AT_END,
  clock_instant: "2026-09-30T15:10:00Z",
  pending_count: 0,
  released_count: 2,
  reports: [
    PENDING_AT_END.reports[0],
    report({
      state: "RELEASED",
      released_at_clock: "2026-09-30T15:10:00Z",
      message_id: "msg-1500",
      sequence: 293,
      outcome: "ADMITTED",
      published_at: "2026-09-30T15:10:00Z",
    }),
  ],
};

const AVAILABLE: GatewayDiagnostics = {
  status: "AVAILABLE",
  statement: "The local gateway's own read at its real UTC clock. Not device or asset health.",
  observed_at_clock: "GATEWAY_REAL_UTC",
  current: {
    site_id: "site-a",
    gateway_id: "gateway-a",
    source_mode: "SIMULATED",
    sequence_epoch: "1",
    observed_at: "2026-10-09T08:00:00Z",
    queue: {
      queue_count: 3,
      oldest_queued_at: "2026-10-09T07:59:00Z",
      oldest_queue_age_seconds: 60,
      sealed_pending_batches: 1,
      sealed_pending_envelopes: 2,
      unbatched_envelopes: 1,
      held_reports: 2,
      active_seal_refusals: 0,
      dead_letter_envelopes: 0,
    },
    mapping_error_count: 1,
    source_contacts: [
      { source_id: SOURCE, last_contact_at: "2026-10-09T07:59:30Z", provenance: "OBSERVED_SIMULATED_REPORT" },
      { source_id: "silent-source", last_contact_at: null, provenance: null },
    ],
    clock_offset: { value_ms: null, provenance: null, observed_at: null },
    disk_pressure: {
      level: "STOP",
      provenance: "INJECTED_FAULT_FIXTURE",
      free_bytes: null,
      observed_at: "2026-10-09T07:58:00Z",
    },
    acquisition: "REFUSED_DISK_PRESSURE_STOP",
    diagnostic_count: 2,
    pending_diagnostic_count: 2,
    upload: "PENDING",
    config_sha256: "ef".repeat(32),
    config: { emission_cadence_seconds: 60 },
  },
  last_emitted: {
    gateway_id: "gateway-a",
    sequence_epoch: "1",
    diagnostic_sequence: 2,
    observed_at: "2026-10-09T07:59:00Z",
    payload_text: "{}",
    sha256: "12".repeat(32),
    state: "READY",
    last_attempt_at: null,
  },
};

const UNAVAILABLE: GatewayDiagnostics = {
  status: "GATEWAY_UNAVAILABLE",
  detail: "the gateway IPC did not answer",
  statement: "The local gateway's own read at its real UTC clock.",
  observed_at_clock: "GATEWAY_REAL_UTC",
  current: null,
  last_emitted: null,
};

const NOT_COMMITTED: RunCommitResult = {
  status: "loaded",
  commit: { commit: "NOT_COMMITTED", release: null, open_in_assetops: null, release_error: null },
};

function client(
  schedule: RunPublicationSchedule,
  diagnostics: GatewayDiagnostics,
  advance: AdvancePublicationResult = {
    status: "loaded",
    publication: RELEASED_AFTER_END,
    publicationRefused: null,
    releaseBasis: "STORED_SCHEDULE_ONLY",
    releaseBasisStatement:
      "No live world session (the Lab host restarted): only the stored delayed reports' exact text was released.",
  },
): RunSetupClient & { advances: string[] } {
  const fake = {
    advances: [] as string[],
    listProfiles: () => Promise.resolve({ status: "unavailable" as const }),
    createRun: () => Promise.resolve({ status: "unavailable" as const, message: null }),
    listRuns: () => Promise.resolve({ status: "loaded" as const, runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded" as const, run: RUN }),
    ...executionMethods(
      { status: "loaded", execution: RUNNING_IN_THE_GAP },
      { status: "gateway", stage: LEDGER, frozenBasis: null },
    ),
    getCommit: () => Promise.resolve(NOT_COMMITTED),
    commit: () => Promise.resolve(NOT_COMMITTED),
    getPublication: () => Promise.resolve({ status: "loaded" as const, publication: schedule }),
    advancePublication: (_runId: string, instant: string) => {
      fake.advances.push(instant);
      return Promise.resolve(advance);
    },
    getGatewayDiagnostics: () =>
      Promise.resolve({ status: "loaded" as const, gateway: diagnostics }),
  };
  return fake;
}

/**
 * B2: the advance form fills its instant from the schedule in an effect, after
 * the read settles; a click before then lands on a disabled button and does
 * nothing. Wait for the suggested instant and an enabled button first.
 */
async function readyAdvanceButton(suggested = "2026-09-30T15:05:00Z"): Promise<HTMLButtonElement> {
  return waitFor(() => {
    const input = screen.getByLabelText(/Advance the publication clock to/) as HTMLInputElement;
    expect(input.value).toBe(suggested);
    const button = screen.getByRole("button", { name: "Advance publication clock" }) as HTMLButtonElement;
    expect(button.disabled).toBe(false);
    return button;
  });
}

function renderAt(runSetup: RunSetupClient) {
  return render(
    <MemoryRouter initialEntries={[URL]}>
      <App flags={featureFlagsWith(true)} siteDirectory={EMPTY_SITE_DIRECTORY} runSetup={runSetup} />
    </MemoryRouter>,
  );
}

function section(selector: string): HTMLElement {
  const found = document.querySelector(selector) as HTMLElement | null;
  if (found === null) {
    throw new Error(`no ${selector}`);
  }
  return found;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("parsing the publication and diagnostics reads (S2-01c)", () => {
  it("accepts a whole schedule and refuses one carrying private or invented fields", () => {
    expect(isRunPublicationSchedule(PENDING_AT_END)).toBe(true);
    const leaked = { ...report({}), report_text: "{}" };
    expect(isRunPublicationSchedule({ ...PENDING_AT_END, reports: [leaked] })).toBe(false);
    const cause = { ...report({}), delay_event_id: "battery-soc-publication-delay" };
    expect(isRunPublicationSchedule({ ...PENDING_AT_END, reports: [cause] })).toBe(false);
    // An absent schedule is a status, never an empty or invented list.
    expect(
      isRunPublicationSchedule({ ...PENDING_AT_END, status: "NO_SCHEDULE", reports: [report({})] }),
    ).toBe(false);
    expect(isRunPublicationSchedule({ ...PENDING_AT_END, status: "EMPTY" })).toBe(false);
    // The ordinary watermark is part of the read, and its state is a known one.
    expect(isRunPublicationSchedule({ ...PENDING_AT_END, ordinary_publication: "PARTIAL" })).toBe(false);
    const { admitted_through: _dropped, ...withoutWatermark } = PENDING_AT_END;
    expect(isRunPublicationSchedule(withoutWatermark)).toBe(false);
  });

  it("refuses an unavailable gateway carrying counters, and a malformed upload code", () => {
    expect(isGatewayDiagnostics(AVAILABLE)).toBe(true);
    expect(isGatewayDiagnostics(UNAVAILABLE)).toBe(true);
    expect(isGatewayDiagnostics({ ...UNAVAILABLE, current: AVAILABLE.current })).toBe(false);
    // S2-02: a gateway-verified central receipt is real now; the newest stored
    // diagnostic may be ACKED without making the whole read unavailable.
    expect(
      isGatewayDiagnostics({ ...AVAILABLE, last_emitted: { ...AVAILABLE.last_emitted, state: "ACKED" } }),
    ).toBe(true);
    expect(
      isGatewayDiagnostics({ ...AVAILABLE, last_emitted: { ...AVAILABLE.last_emitted, refusal_code: 409 } }),
    ).toBe(false);
    expect(
      isGatewayDiagnostics({
        ...AVAILABLE,
        current: { ...AVAILABLE.current, config: { text: "secret" } },
      }),
    ).toBe(false);
  });

  it("reads the three routes at their paths and keeps a typed refusal kind", async () => {
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((path: string, init?: RequestInit) => {
        calls.push(`${init?.method ?? "GET"} ${path} ${init?.body ?? ""}`.trim());
        if (path.endsWith("/publication/advance")) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                detail: {
                  code: "EXECUTION_REFUSED",
                  refusal_kind: "PUBLICATION_CLOCK_BACKWARD",
                  message: "The publication clock never moves backward.",
                  advanced: false,
                },
              }),
              { status: 409 },
            ),
          );
        }
        if (path.endsWith("/publication")) {
          return Promise.resolve(new Response(JSON.stringify({ publication: PENDING_AT_END })));
        }
        return Promise.resolve(new Response(JSON.stringify({ gateway: UNAVAILABLE })));
      }),
    );
    const api = createRunSetupClient("/api/simulator-lab/run-profiles", "/api/simulator-lab/runs");
    const read = await api.getPublication!(RUN_ID);
    expect(read.status === "loaded" && read.publication.pending_count).toBe(1);
    const refused = await api.advancePublication!(RUN_ID, "2026-09-30T14:00:00Z");
    expect(refused).toMatchObject({ status: "refused", refusalKind: "PUBLICATION_CLOCK_BACKWARD" });
    const gateway = await api.getGatewayDiagnostics!();
    expect(gateway.status === "loaded" && gateway.gateway.status).toBe("GATEWAY_UNAVAILABLE");
    expect(calls).toEqual([
      `GET /api/simulator-lab/runs/${RUN_ID}/publication`,
      `POST /api/simulator-lab/runs/${RUN_ID}/publication/advance {"instant":"2026-09-30T14:00:00Z"}`,
      "GET /api/simulator-lab/gateway/diagnostics",
    ]);
  });
});

describe("the delayed-publication view (S2-01c)", () => {
  it("labels each instant's clock and keeps scheduled and actual publication apart", async () => {
    renderAt(client(PENDING_AT_END, AVAILABLE));
    await settledScreen();

    const view = section("[data-publication]");
    expect(view.querySelector("[data-publication-clock]")?.textContent).toBe(
      "the run's virtual publication clock",
    );
    expect(view.querySelector("[data-publication-world]")?.getAttribute("data-publication-world")).toBe(
      "COMPLETE",
    );
    const words = spacedText(view);
    expect(words).toMatch(/Source time \(source time: the reading's own instant\)/);
    expect(words).toMatch(/Scheduled release \(scheduled on the run's virtual publication clock\)/);
    expect(words).toMatch(
      /Published at \(stamped by the gateway on the run's virtual publication clock\)/,
    );

    const waiting = view.querySelector('[data-publication-report="soc-1500"]') as HTMLElement;
    expect(waiting.getAttribute("data-publication-report-state")).toBe("PENDING");
    expect(waiting.querySelector("[data-publication-published-at]")?.textContent).toBe(
      "no envelope yet",
    );
    const released = view.querySelector('[data-publication-report="soc-1045"]') as HTMLElement;
    expect(released.querySelector("[data-publication-scheduled]")?.textContent).toBe(
      "2026-09-30T10:55:00Z",
    );
    expect(released.querySelector("[data-publication-published-at]")?.textContent).toBe(
      "2026-09-30T11:00:00Z",
    );
  });

  it("advances to the next release, then shows the later actual publication and the release basis", async () => {
    const fake = client(PENDING_AT_END, AVAILABLE);
    renderAt(fake);
    await settledScreen();

    await readyAdvanceButton();
    const input = screen.getByLabelText(/Advance the publication clock to/) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "2026-09-30T15:10:00Z" } });
    fireEvent.click(screen.getByRole("button", { name: "Advance publication clock" }));

    await screen.findByText(/only the stored delayed reports' exact text was released/);
    expect(fake.advances).toEqual(["2026-09-30T15:10:00Z"]);
    const row = section('[data-publication-report="soc-1500"]');
    expect(row.getAttribute("data-publication-report-state")).toBe("RELEASED");
    // Jumped past due: published at the later instant, not backdated to 15:05.
    expect(row.querySelector("[data-publication-source-time]")?.textContent).toBe(
      "2026-09-30T15:00:00Z",
    );
    expect(row.querySelector("[data-publication-published-at]")?.textContent).toBe(
      "2026-09-30T15:10:00Z",
    );
    expect(
      section("[data-publication-release-basis]").getAttribute("data-publication-release-basis"),
    ).toBe("STORED_SCHEDULE_ONLY");
  });

  it("marks a report whose release is due but not admitted", async () => {
    renderAt(client({ ...PENDING_AT_END, clock_instant: "2026-09-30T15:05:00Z" }, AVAILABLE));
    await settledScreen();
    expect(
      section('[data-publication-report="soc-1500"]').getAttribute("data-publication-report-state"),
    ).toBe("DUE");
  });

  it.each(PUBLICATION_REFUSAL_KINDS.map((kind) => [kind]))(
    "names the %s refusal in plain words and moves nothing",
    async (kind) => {
      renderAt(
        client(PENDING_AT_END, AVAILABLE, {
          status: "refused",
          refusalKind: kind,
          code: "EXECUTION_REFUSED",
          message: "server statement",
        }),
      );
      await settledScreen();
      fireEvent.click(await readyAdvanceButton());
      const refusal = await waitFor(() => section(`[data-publication-refusal="${kind}"]`));
      expect(spacedText(refusal)).toMatch(/^Not advanced\. .+ server statement$/);
      expect(
        section('[data-publication-report="soc-1500"]').getAttribute(
          "data-publication-report-state",
        ),
      ).toBe("PENDING");
    },
  );

  it("shows a gateway HELD release as held, with no envelope or publication instant (C1)", async () => {
    const held = report({
      report_key: "soc-held",
      state: "RELEASED",
      released_at_clock: "2026-09-30T15:10:00Z",
      outcome: "HELD",
    });
    renderAt(
      client(
        { ...PENDING_AT_END, reports: [PENDING_AT_END.reports[0], held], pending_count: 0, released_count: 2 },
        AVAILABLE,
      ),
    );
    await settledScreen();
    const row = section('[data-publication-report="soc-held"]');
    expect(row.getAttribute("data-publication-report-state")).toBe("HELD");
    expect(spacedText(row)).toMatch(/Submitted, held by the gateway/);
    expect(spacedText(row)).not.toMatch(/Released to the local gateway|not readable/);
    expect(row.querySelector("[data-publication-published-at]")?.textContent).toBe(
      "Held by the gateway (HELD): no envelope and no publication instant",
    );
    expect(section("[data-publication-released]").textContent).toBe(
      "0 waiting, 1 released, 1 held by the gateway",
    );
  });

  it("keeps 'not readable' for an admitted release whose Stage could not be read", async () => {
    const unread = { ...PENDING_AT_END.reports[0], published_at: null };
    renderAt(client({ ...PENDING_AT_END, reports: [unread, PENDING_AT_END.reports[1]] }, AVAILABLE));
    await settledScreen();
    expect(
      section('[data-publication-report="soc-1045"]').querySelector("[data-publication-published-at]")
        ?.textContent,
    ).toBe("not readable from the gateway");
  });

  it("names an executed run's missing schedule as lost state, not NO_SCHEDULE or an empty queue", async () => {
    renderAt(
      client(
        {
          ...PENDING_AT_END,
          status: "SCHEDULE_MISSING",
          detail: "schedule gone",
          reports: [],
          pending_count: 0,
          released_count: 0,
        },
        AVAILABLE,
      ),
    );
    await settledScreen();
    const view = section("[data-publication]");
    expect(view.getAttribute("data-publication-status")).toBe("SCHEDULE_MISSING");
    expect(spacedText(view.querySelector("[data-publication-missing]") as HTMLElement)).toMatch(
      /executed, but its publication schedule is missing\. schedule gone .*not an empty queue/,
    );
    expect(view.querySelector("[data-publication-none]")).toBeNull();
    expect(view.querySelector("[data-publication-pending]")).toBeNull();
    expect(screen.queryByRole("button", { name: "Advance publication clock" })).toBeNull();
  });

  it("shows a complete ordinary watermark with no gap warning", async () => {
    renderAt(client(PENDING_AT_END, AVAILABLE));
    await settledScreen();
    const view = section("[data-publication]");
    const ordinary = view.querySelector("[data-ordinary-publication]") as HTMLElement;
    expect(ordinary.getAttribute("data-ordinary-publication")).toBe("COMPLETE");
    expect(ordinary.textContent).toMatch(/Published through 2026-09-30T15:00:00Z\./);
    expect(view.querySelector("[data-publication-gap]")).toBeNull();
  });

  it("labels a run with an ordinary gap incomplete and shows a refused advance plainly (R1)", async () => {
    const gap: RunPublicationSchedule = {
      ...PENDING_AT_END,
      admitted_through: "2026-09-30T07:30:00Z",
      ordinary_publication: "INCOMPLETE",
    };
    const fake = client(gap, AVAILABLE, {
      status: "refused",
      refusalKind: "PUBLICATION_GAP",
      code: "EXECUTION_PUBLICATION_GAP",
      message:
        "Ordinary publication is admitted through 2026-09-30T07:30:00Z; the world reached 2026-09-30T15:00:00Z.",
    });
    renderAt(fake);
    await settledScreen();
    const view = section("[data-publication]");
    expect(
      view.querySelector("[data-ordinary-publication]")?.getAttribute("data-ordinary-publication"),
    ).toBe("INCOMPLETE");
    const warning = section('[data-publication-gap="INCOMPLETE"]');
    expect(spacedText(warning)).toMatch(
      /^This run is not fully published\. Ordinary readings are published through 2026-09-30T07:30:00Z; the world reached 2026-09-30T15:00:00Z\. .*no delayed report is released past the gap\.$/,
    );
    fireEvent.click(await readyAdvanceButton());
    const refusal = await waitFor(() => section('[data-publication-refusal="PUBLICATION_GAP"]'));
    expect(spacedText(refusal)).toMatch(
      /^Not advanced\. Ordinary publication stopped .*Nothing was moved, admitted or sealed\. .*admitted through 2026-09-30T07:30:00Z; the world reached 2026-09-30T15:00:00Z\.$/,
    );
    expect(fake.advances).toEqual(["2026-09-30T15:05:00Z"]);
    // The refused advance released nothing and the gap is still shown.
    expect(
      section('[data-publication-report="soc-1500"]').getAttribute("data-publication-report-state"),
    ).toBe("PENDING");
    expect(document.querySelector('[data-publication-gap="INCOMPLETE"]')).not.toBeNull();
    expect(document.querySelector("[data-publication-advanced]")).toBeNull();
  });

  it("shows a terminal gap as needing a new run, never as fully published", async () => {
    renderAt(
      client(
        {
          ...PENDING_AT_END,
          admitted_through: "2026-09-30T03:45:00Z",
          ordinary_publication: "TERMINAL_GAP",
          ordinary_stopped_at: "2026-09-30T04:00:00Z",
        },
        AVAILABLE,
      ),
    );
    await settledScreen();
    const warning = section('[data-publication-gap="TERMINAL_GAP"]');
    expect(spacedText(warning)).toMatch(
      /published through 2026-09-30T03:45:00Z; .*passed 2026-09-30T04:00:00Z before it was published.*Start a new run/,
    );
    expect(section("[data-ordinary-publication]").textContent).toMatch(/^Incomplete for good/);
  });

  it("never shows an absent schedule as an empty queue", async () => {
    renderAt(
      client(
        { ...PENDING_AT_END, status: "NO_SCHEDULE", reports: [], pending_count: 0, released_count: 0 },
        AVAILABLE,
      ),
    );
    await settledScreen();
    const view = section("[data-publication]");
    expect(view.querySelector("[data-publication-none]")?.textContent).toMatch(
      /not an empty queue/,
    );
    expect(view.querySelector("[data-publication-pending]")).toBeNull();
    expect(screen.queryByRole("button", { name: "Advance publication clock" })).toBeNull();
  });
});

describe("the gateway diagnostics view (S2-01c)", () => {
  it("labels the real-UTC read, injected pressure, unknown offset and unknown contact", async () => {
    renderAt(client(PENDING_AT_END, AVAILABLE));
    await settledScreen();

    const view = section("[data-diagnostics]");
    const words = spacedText(view);
    expect(words).toMatch(/Read at \(gateway's real UTC clock\)/);
    expect(view.querySelector("[data-diagnostics-queue]")?.textContent).toMatch(
      /^3 envelopes waiting for upload: 2 sealed in 1 batches, 1 not sealed yet$/,
    );
    expect(view.querySelector("[data-diagnostics-clock-offset]")?.textContent).toBe(
      "Unknown: not measured",
    );
    expect(view.querySelector("[data-diagnostics-disk]")?.textContent).toBe(
      "STOP, injected by a labelled fault fixture, not measured",
    );
    expect(words).toMatch(/Refused at disk pressure STOP, before any sequence number is used/);
    expect(within(section(`[data-diagnostics-contact="${SOURCE}"]`)).getByText(/not proof a device is alive/)).toBeTruthy();
    expect(spacedText(section('[data-diagnostics-contact="silent-source"]'))).toMatch(
      /Unknown: no report observed .*not a healthy source/,
    );
    expect(view.querySelector("[data-diagnostics-last-emitted]")?.textContent).toMatch(
      /sequence 2 .* no central receipt exists/,
    );
    expect(words).not.toMatch(/\bhealthy\b(?! source)/i);
  });

  it("shows an unreachable gateway as unavailable, with no counters at all", async () => {
    renderAt(client(PENDING_AT_END, UNAVAILABLE));
    await settledScreen();

    const view = section("[data-diagnostics]");
    expect(view.getAttribute("data-diagnostics-status")).toBe("GATEWAY_UNAVAILABLE");
    expect(spacedText(view)).toMatch(/Gateway unavailable\. the gateway IPC did not answer/);
    expect(view.querySelector("[data-diagnostics-queue]")).toBeNull();
    expect(view.querySelector("[data-diagnostics-disk]")).toBeNull();
    expect(spacedText(view)).not.toMatch(/\b0 envelopes\b/);
  });
});
