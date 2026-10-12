import { cleanup, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import type {
  GatewayLedgerStage,
  RegisteredRelease,
  RunCommitResult,
  RunExecutionResult,
  RunSetupClient,
  RunStageResult,
  RunSummary,
} from "../runSetupClient";
import {
  COMPLETED,
  NOT_COMMITTED_READ,
  NOT_STAGED,
  NOT_STARTED,
  executionMethods,
} from "./executionFixtures";

/**
 * V-01b phase b2: the Lab run page opens on the mock's "Gateway & Ingestion"
 * overview - status bar, four-box flow strip and the four lab panels - built
 * only from the reads the page already makes. Delivery comes from the Commit
 * read; a missing read or fact is named, never filled with a mock value.
 */

const RUN_ID = "run-7c0e5a1b2d3f4a5b6c7d8e9f0a1b2c3d";
const URL = `/simulator-lab/runs/${RUN_ID}`;
const SNAPSHOT = "ab".repeat(32);

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const RUN = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: null,
  created_at: "2026-10-08T09:00:00Z",
  site_id: "KOBO-001",
  scenario_id: "kobo-mini-grid-prolonged",
  scenario_version: 2,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
  template_lineage: { state: "NOT_RECORDED" },
} as unknown as RunSummary;

function canonical(device: string, signal: string, time: string, value: string): string {
  return JSON.stringify({
    mapping: { binding_set_id: "bs-1", version: 6 },
    message: { message_id: `m-${time}`, sequence: 1, sequence_epoch: "e1" },
    payload: { family: "MEASUREMENT", measurement: "STATE_AT_INSTANT", quality: "GOOD", unavailable_reason: null, unit: "L", value },
    schema: { id: "assetops.source-envelope", version: 3 },
    source: { device_id: device, gateway_id: "gw-1", signal_id: signal, site_id: "site-uuid", source_id: "src-1" },
    timing: { interval_end: null, interval_start: null, published_at: time, source_time: time },
  });
}

function envelope(id: string, time: string, batch: string | null, value: string) {
  return {
    message_id: id,
    source_id: "src-1",
    sequence_epoch: "e1",
    sequence: 1,
    source_time: time,
    snapshot_sha256: SNAPSHOT,
    canonical: canonical("fuel-level-sensor", "fuel-level", time, value),
    sha256: "ef".repeat(32),
    state: batch === null ? "READY" : "ACKED",
    batch_id: batch,
    ordinal: batch === null ? null : 0,
  };
}

const LEDGER: GatewayLedgerStage = {
  store: "GATEWAY_LEDGER",
  run_id: RUN_ID,
  status: "STAGED",
  statement: "Every report the gateway admitted for this run is in a sealed local batch.",
  execution_status: "COMPLETED",
  release_eligible: false,
  snapshot_sha256: SNAPSHOT,
  site_id: "site-uuid",
  gateway_id: "gw-1",
  sequence_epoch: "e1",
  upload_state: "PENDING",
  upload_statement: "Upload pending: no batch has been sent and no receipt exists.",
  receipts: [],
  unavailable_detail: null,
  publication_notes: [],
  queue_depth_by_state: { ACKED: 2, READY: 1 },
  // Out of source-time order on purpose: the overview shows the earliest.
  envelopes: [
    envelope("msg-late", "2026-09-21T06:00:00Z", "batch-1", "410"),
    envelope("msg-early", "2026-09-21T01:00:00Z", "batch-1", "498.5"),
    envelope("msg-loose", "2026-09-21T07:00:00Z", null, "400"),
  ],
  batches: [
    {
      batch_id: "batch-1",
      source_id: "src-1",
      sequence_epoch: "e1",
      snapshot_sha256: SNAPSHOT,
      canonical: '{"batch_id":"batch-1"}',
      sha256: "cd".repeat(32),
      state: "ACKED",
      attempt_count: 1,
      message_ids: ["msg-early", "msg-late"],
    },
  ],
  holds: [
    {
      hold_id: 3,
      kind: "UNKNOWN_CHANNEL",
      field: "signal_id",
      detail: "not a channel",
      device_id: "kobo-meter",
      signal_id: "unmapped",
      source_time: "2026-09-21T02:00:00Z",
      seen_count: 1,
    },
  ],
  seal_refusals: [],
};

const RECEIPT = {
  receipt_sha256: "c".repeat(64),
  server_received_at: "2026-10-09T09:00:00Z",
  server_completed_at: "2026-10-09T09:00:01Z",
};

function release(receipt: typeof RECEIPT | null): RegisteredRelease {
  return {
    status: "AVAILABLE",
    detail: null,
    execution_status: "COMPLETED",
    delivery: {
      stage_status: "STAGED",
      envelope_count: 3,
      unbatched_envelope_count: 1,
      held_report_count: 1,
      batch_count: 2,
      released_batch_count: 2,
      batches_by_state: { ACKED: receipt === null ? 0 : 1, IN_FLIGHT: 0, READY: receipt === null ? 2 : 1, REFUSED: 0, STAGED: 0 },
      shared_batch_ids: [],
      batches: [
        { batch_id: "batch-1", source_id: "src-1", state: receipt === null ? "READY" : "ACKED", released: true, shared_with_another_run: false, item_count: 2, receipt, decisions: receipt === null ? {} : { ACCEPTED: 1, DUPLICATE: 1 }, last_error_code: null },
        { batch_id: "batch-2", source_id: "src-1", state: "READY", released: true, shared_with_another_run: false, item_count: 1, receipt: null, decisions: {}, last_error_code: null },
      ],
      decisions: receipt === null ? { ACCEPTED: 0, CONFLICT: 0, DUPLICATE: 0, REJECTED: 0 } : { ACCEPTED: 1, CONFLICT: 0, DUPLICATE: 1, REJECTED: 0 },
      refusals: [],
      last_upload_error: null,
      release_state: "IN_PROGRESS",
      gateway_complete: false,
    },
    released_now: null,
    publication_gap: "NONE",
    publication_gap_detail: null,
    publication_schedule: null,
    fully_released: false,
    release_blockers: ["RECEIPTS_PENDING"],
  };
}

function released(receipt: typeof RECEIPT | null): RunCommitResult {
  return {
    status: "loaded",
    commit: {
      commit: "RELEASED_TO_GATEWAY",
      release: null,
      open_in_assetops: null,
      release_error: null,
      registered_release: release(receipt),
      fully_released: false,
      statement: "Not every batch has a durable central receipt yet.",
    },
  };
}

function client(
  execution: RunExecutionResult,
  stage: RunStageResult,
  commit: Promise<RunCommitResult>,
): RunSetupClient {
  return {
    listProfiles: () => Promise.resolve({ status: "unavailable" as const }),
    createRun: () => Promise.resolve({ status: "unavailable" as const, message: null }),
    listRuns: () => Promise.resolve({ status: "loaded" as const, runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded" as const, run: RUN }),
    ...executionMethods(execution, stage),
    getCommit: () => commit,
  } as unknown as RunSetupClient;
}

function renderAt(runSetup: RunSetupClient) {
  return render(
    <MemoryRouter initialEntries={[URL]}>
      <App flags={featureFlagsWith(true)} siteDirectory={EMPTY_SITE_DIRECTORY} runSetup={runSetup} />
    </MemoryRouter>,
  );
}

function one(selector: string, scope: ParentNode = document): HTMLElement {
  const found = scope.querySelector<HTMLElement>(selector);
  if (found === null) {
    throw new Error(`nothing matches ${selector}`);
  }
  return found;
}

function words(selector: string): string {
  return spacedText(one(selector));
}

function kv(term: string): string {
  const terms = Array.from(one("[data-ingestion-release]").querySelectorAll("dt"));
  const dt = terms.find((t) => t.textContent === term);
  if (dt === undefined) {
    throw new Error(`no release fact ${term}`);
  }
  return (dt.nextElementSibling?.textContent ?? "").trim();
}

const GATEWAY = { status: "gateway", stage: LEDGER } as const;
const EXECUTED: RunExecutionResult = { status: "loaded", execution: COMPLETED };

afterEach(cleanup);

describe("the Gateway & Ingestion overview (V-01b b2)", () => {
  it("opens the run page on Gateway & Ingestion, above the execution and recorded history", async () => {
    renderAt(client(EXECUTED, GATEWAY, Promise.resolve(released(RECEIPT))));
    await settledScreen();

    const main = one("main");
    expect(main.querySelector("h2")?.textContent).toBe("Gateway & Ingestion");
    const overview = one("[data-run-ingestion]");
    const history = one("#run-history-section-heading");
    expect(history.textContent).toBe("Execution and recorded history");
    expect(overview.compareDocumentPosition(one("[data-cockpit]")) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(history.compareDocumentPosition(one("[data-cockpit]")) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const titles = Array.from(overview.querySelectorAll(".panel__heading")).map((h) => h.textContent);
    expect(titles).toEqual(
      expect.arrayContaining(["Selected canonical envelope", "Truth versus observed", "Release and ingestion", "What never crosses"]),
    );
    const envelopePanel = one("#run-ingestion-envelope-heading").closest("section") as HTMLElement;
    expect(spacedText(envelopePanel)).toMatch(/Exactly the source boundary; no private-truth field/);
  });

  it("states commit, execution and central receipts from the reads, and links to Site Evidence for the run interval", async () => {
    renderAt(client(EXECUTED, GATEWAY, Promise.resolve(released(RECEIPT))));
    await settledScreen();

    const bar = one("[data-ingestion-status]");
    const badges = Array.from(bar.querySelectorAll(".badge")).map((b) => b.textContent);
    expect(badges).toEqual(["Released to gateway", "Execution completed"]);
    expect(words("[data-ingestion-delivery]")).toBe("1 of 2 batches have a central receipt");
    expect(words("[data-ingestion-frozen]")).toMatch(/minimal-fuel-tank v1/);
    expect(words("[data-ingestion-frozen]")).toMatch(/kobo-mini-grid-prolonged v2/);
    const link = one("a[data-ingestion-evidence-link]", bar) as HTMLAnchorElement;
    expect(link.textContent).toBe("Open Site Evidence →");
    const href = new window.URL(link.getAttribute("href") ?? "", "http://x");
    expect(href.pathname).toBe("/sites/KOBO-001/evidence");
    expect(href.searchParams.get("from")).toBe(COMPLETED.interval_start_time);
    expect(href.searchParams.get("to")).toBe(COMPLETED.interval_end_time);
  });

  it("shows the four flow boxes with real facts, private boxes private and the accepted box public", async () => {
    renderAt(client(EXECUTED, GATEWAY, Promise.resolve(released(RECEIPT))));
    await settledScreen();

    const boxes = Array.from(document.querySelectorAll("[data-flow-box]")).map((b) => b.getAttribute("data-flow-box"));
    expect(boxes).toEqual(["world", "reports", "envelopes", "accepted"]);
    expect(one("[data-flow-box='world']").className).toMatch(/\bprivate\b/);
    expect(one("[data-flow-box='reports']").className).toMatch(/\bprivate\b/);
    expect(one("[data-flow-box='accepted']").className).toMatch(/\bpublic\b/);
    expect(words("[data-flow-box='world']")).toMatch(/165 of 165 steps simulated/);
    expect(words("[data-flow-box='reports']")).toMatch(/96 reports published, 5 dropped/);
    expect(words("[data-flow-box='reports']")).toMatch(/3 admitted by the gateway, 1 held/);
    expect(words("[data-flow-box='envelopes']")).toMatch(/2 of 3 envelopes in 1 sealed batch/);
    expect(words("[data-flow-box='accepted']")).toMatch(/1 accepted, 1 duplicate, 0 conflict, 0 rejected/);
    expect(words("[data-flow-box='accepted']")).toMatch(/1 of 2 batches have a central receipt/);
  });

  it("shows the earliest stored envelope as a compact code block and says who assigns received_at", async () => {
    renderAt(client(EXECUTED, GATEWAY, Promise.resolve(released(RECEIPT))));
    await settledScreen();

    const code = one("[data-ingestion-envelope]");
    expect(code.tagName).toBe("PRE");
    expect(code.getAttribute("data-ingestion-envelope")).toBe("msg-early");
    expect(code.textContent).toMatch(/^device_id: fuel-level-sensor$/m);
    expect(code.textContent).toMatch(/^source_time: 2026-09-21T01:00:00Z$/m);
    expect(code.textContent).toMatch(/^value: "498.5"$/m);
    expect(code.textContent).toMatch(/^mapping: bs-1 \/ v6$/m);
    const note = words("[data-ingestion-panel='envelope']");
    expect(note).toMatch(/received_at is assigned by ingestion, never the gateway/);
    expect(note).toMatch(/Every envelope is under Advanced details/);
  });

  it("compares private truth with what each device reported, and names the missing product consequence once", async () => {
    renderAt(client(EXECUTED, GATEWAY, Promise.resolve(released(RECEIPT))));
    await settledScreen();

    const panel = one("[data-ingestion-panel='truth']");
    const rows = panel.querySelectorAll("tr[data-truth-row]");
    expect(rows).toHaveLength(COMPLETED.signals.length);
    const fuel = one("tr[data-truth-row='fuel-level-sensor:fuel-level']", panel);
    expect(spacedText(fuel)).toMatch(/01:45/);
    expect(one("[data-truth-private]", fuel).textContent).toBe("254.02 L");
    expect(one("[data-truth-observed]", fuel).textContent).toBe("373.52 L");
    const generator = one("tr[data-truth-row='generator-controller:ac-power']", panel);
    expect(one("[data-truth-private]", generator).textContent).toBe("not measured here");
    const headers = Array.from(panel.querySelectorAll("th[scope='col']")).map((th) => th.textContent);
    expect(headers).toEqual(["At / signal", "Private truth", "Observed"]);
    expect(words("[data-ingestion-missing='product-consequence']")).toMatch(/^Not available yet: /);
  });

  it("states release and ingestion from the Commit read, keeps the Commit panel there, and labels the Stage's upload line", async () => {
    renderAt(client(EXECUTED, GATEWAY, Promise.resolve(released(RECEIPT))));
    await settledScreen();

    expect(kv("Commit")).toBe("Released to gateway");
    expect(kv("Batches")).toBe("2 sealed, 2 released");
    expect(kv("Central receipts")).toBe("1 of 2 batches");
    expect(kv("Accepted")).toBe("1");
    expect(kv("Duplicates")).toBe("1");
    expect(kv("Conflicts")).toBe("0");
    expect(kv("Rejected")).toBe("0");
    const inspect = one("a[data-ingestion-inspect]") as HTMLAnchorElement;
    expect(inspect.textContent).toBe("Inspect accepted records");
    const href = new window.URL(inspect.getAttribute("href") ?? "", "http://x");
    expect(href.searchParams.get("view")).toBe("analysis");
    expect(href.searchParams.get("from")).toBe(COMPLETED.interval_start_time);
    expect(one("[data-run-ingestion]").contains(one("[data-run-commit]"))).toBe(true);

    // Q1: the Stage's own upload line stays, labelled as the gateway's local statement.
    expect(one("[data-gateway-upload]").textContent).toMatch(/Upload pending/);
    expect(words("[data-gateway-upload-label]")).toMatch(/gateway's local Stage statement/);
    expect(words("[data-gateway-upload-label]")).toMatch(/Release and ingestion/);
    expect(one('[data-disclosure="stage"] > summary').textContent).toMatch(/^Advanced details — /);
    // What never crosses keeps the boundary and names the missing destination.
    expect(words("[data-ingestion-panel='boundary']")).toMatch(/The gateway observes, maps and publishes\./);
    expect(words("[data-ingestion-missing='dispatch-link']")).toMatch(/^Not available yet: /);
  });

  it("offers no Site Evidence link and says nothing was received when no batch has a central receipt", async () => {
    renderAt(client(EXECUTED, GATEWAY, Promise.resolve(released(null))));
    await settledScreen();

    expect(document.querySelector("a[data-ingestion-evidence-link]")).toBeNull();
    expect(document.querySelector("a[data-ingestion-inspect]")).toBeNull();
    expect(words("[data-ingestion-delivery]")).toBe("0 of 2 batches have a central receipt");
    expect(words("[data-ingestion-received]")).toBe("Nothing from this run has been received centrally.");
  });

  it("names a run that is neither executed nor committed honestly", async () => {
    renderAt(
      client(
        { status: "loaded", execution: NOT_STARTED },
        { status: "loaded", stage: NOT_STAGED },
        Promise.resolve(NOT_COMMITTED_READ),
      ),
    );
    await settledScreen();

    const badges = Array.from(one("[data-ingestion-status]").querySelectorAll(".badge")).map((b) => b.textContent);
    expect(badges).toEqual(["Not committed", "Execution not started"]);
    expect(words("[data-ingestion-received]")).toBe("Nothing from this run has been received centrally.");
    expect(document.querySelector("a[data-ingestion-evidence-link]")).toBeNull();
    expect(words("[data-flow-box='world']")).toMatch(/0 of 165 steps simulated/);
    expect(words("[data-flow-box='accepted']")).toMatch(/Not committed: nothing released/);
    expect(words("[data-ingestion-panel='envelope']")).toMatch(/No envelope is stored for this run yet/);
    expect(kv("Commit")).toBe("Not committed");
    const rows = one("[data-ingestion-panel='truth']").querySelectorAll("tr[data-truth-row]");
    expect(rows).toHaveLength(NOT_STARTED.signals.length);
    expect(spacedText(rows[0] as HTMLElement)).toMatch(/No step yet/);
  });

  it("says when a read is loading or unavailable instead of showing a value", async () => {
    renderAt(
      client(
        { status: "unavailable", message: null },
        { status: "unavailable", message: null },
        new Promise<RunCommitResult>(() => undefined),
      ),
    );
    await waitFor(() => expect(document.querySelector("[data-flow-box='world']")).not.toBeNull());
    await waitFor(() => expect(words("[data-flow-box='envelopes']")).toMatch(/Stage not available/));
    expect(words("[data-flow-box='world']")).toMatch(/Execution not available/);
    expect(words("[data-flow-box='accepted']")).toMatch(/Loading the commit status\./);
    expect(document.querySelector("a[data-ingestion-evidence-link]")).toBeNull();
    expect(words("[data-ingestion-panel='truth']")).toMatch(/Execution not available/);
  });
});
