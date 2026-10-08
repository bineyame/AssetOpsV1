import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import {
  createRunSetupClient,
  isGatewayLedgerStage,
  type GatewayLedgerStage,
  type RunCommitResult,
  type RunSetupClient,
  type RunStageResult,
  type RunSummary,
} from "../runSetupClient";
import { RUNNING_IN_THE_GAP, executionMethods } from "./executionFixtures";

/**
 * S2-01b: a registered run's Stage is the gateway ledger. The Lab shows its
 * exact sealed bytes, queue state and typed holds, says upload is pending with
 * no receipt, and offers no Commit or release.
 */

const RUN_ID = "run-2a0c2b7a4e5d4c8fa1b2c3d4e5f60718";
const URL = `/simulator-lab/runs/${RUN_ID}`;
const SNAPSHOT = "ab".repeat(32);
const SOURCE_A = "5d1e8a90-0000-4000-8000-00000000000a";
const SOURCE_B = "5d1e8a90-0000-4000-8000-00000000000b";

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const RUN: RunSummary = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: null,
  created_at: "2026-10-08T09:00:00Z",
  site_id: "KOBO-001",
  scenario_id: "registered-kobo-daytime",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
  template_lineage: { state: "NOT_RECORDED" },
} as unknown as RunSummary;

function envelope(source: string, sequence: number, batch: string | null, ordinal: number | null) {
  const id = `msg-${source.slice(-1)}-${sequence}`;
  return {
    message_id: id,
    source_id: source,
    sequence_epoch: "1",
    sequence,
    source_time: `2026-09-30T0${sequence}:00:00Z`,
    snapshot_sha256: SNAPSHOT,
    canonical: `{"message_id":"${id}","sequence":${sequence},"value":"54.473684"}`,
    sha256: String(sequence).padStart(2, "0").repeat(32),
    state: batch === null ? "READY" : "STAGED",
    batch_id: batch,
    ordinal,
  };
}

const LEDGER: GatewayLedgerStage = {
  store: "GATEWAY_LEDGER",
  run_id: RUN_ID,
  status: "STAGED",
  statement:
    "The gateway sealed this run's public reports into its local outbox. Upload is pending: nothing has been sent or accepted.",
  execution_status: "COMPLETED",
  release_eligible: false,
  snapshot_sha256: SNAPSHOT,
  site_id: "8a1f0c2e-0000-4000-8000-0000000000aa",
  gateway_id: "8a1f0c2e-0000-4000-8000-0000000000bb",
  sequence_epoch: "1",
  upload_state: "PENDING",
  upload_statement: "Upload pending: no batch has been sent and no receipt exists.",
  receipts: [],
  unavailable_detail: null,
  publication_notes: [],
  queue_depth_by_state: { READY: 1, STAGED: 2 },
  envelopes: [
    envelope(SOURCE_A, 1, "batch-a-1", 1),
    envelope(SOURCE_A, 2, "batch-a-1", 2),
    envelope(SOURCE_B, 1, null, null),
  ],
  batches: [
    {
      batch_id: "batch-a-1",
      source_id: SOURCE_A,
      sequence_epoch: "1",
      snapshot_sha256: SNAPSHOT,
      canonical: '{"batch_id":"batch-a-1","items":[]}',
      sha256: "cd".repeat(32),
      state: "STAGED",
      attempt_count: 0,
      message_ids: ["msg-a-1", "msg-a-2"],
    },
  ],
  holds: [
    {
      hold_id: 7,
      kind: "UNKNOWN_CHANNEL",
      field: "signal_id",
      detail: "kobo-meter/unmapped is not a channel of the active mapping.",
      device_id: "kobo-meter",
      signal_id: "unmapped",
      source_time: "2026-09-30T05:00:00Z",
      seen_count: 2,
    },
  ],
};

const REGISTERED_BASIS = {
  configuration_store: "REGISTERED",
  site_imported: true,
  can_release: false,
  statement: "Frozen at Draft setup from the registered Site configuration named here.",
};

const NOT_COMMITTED: RunCommitResult = {
  status: "loaded",
  commit: { commit: "NOT_COMMITTED", release: null, open_in_assetops: null, release_error: null },
};

function client(stage: RunStageResult): RunSetupClient & { posts: number } {
  const fake = {
    posts: 0,
    listProfiles: () => Promise.resolve({ status: "unavailable" as const }),
    createRun: () => Promise.resolve({ status: "unavailable" as const, message: null }),
    listRuns: () => Promise.resolve({ status: "loaded" as const, runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded" as const, run: RUN }),
    ...executionMethods({ status: "loaded", execution: RUNNING_IN_THE_GAP }, stage),
    getCommit: () => Promise.resolve(NOT_COMMITTED),
    commit: () => {
      fake.posts += 1;
      return Promise.resolve(NOT_COMMITTED);
    },
  };
  return fake;
}

function renderAt(runSetup: RunSetupClient) {
  return render(
    <MemoryRouter initialEntries={[URL]}>
      <App flags={featureFlagsWith(true)} siteDirectory={EMPTY_SITE_DIRECTORY} runSetup={runSetup} />
    </MemoryRouter>,
  );
}

function ledger(): HTMLElement {
  const found = document.querySelector("[data-gateway-ledger]") as HTMLElement | null;
  if (found === null) {
    throw new Error("no gateway ledger view");
  }
  return found;
}

describe("the gateway-ledger Stage (S2-01b)", () => {
  it("parses only a whole, pending, receipt-free ledger", () => {
    expect(isGatewayLedgerStage(LEDGER)).toBe(true);
    expect(isGatewayLedgerStage({ ...LEDGER, receipts: [{ batch_id: "batch-a-1" }] })).toBe(false);
    expect(isGatewayLedgerStage({ ...LEDGER, upload_state: "ACKED" })).toBe(false);
    expect(isGatewayLedgerStage({ ...LEDGER, release_eligible: true })).toBe(false);
    expect(isGatewayLedgerStage({ ...LEDGER, store: "LEGACY_FILE" })).toBe(false);
    expect(
      isGatewayLedgerStage({ ...LEDGER, batches: [{ ...LEDGER.batches[0], sha256: "short" }] }),
    ).toBe(false);
    const { holds: _holds, ...noHolds } = LEDGER;
    expect(isGatewayLedgerStage(noHolds)).toBe(false);
  });

  it("reads a registered Stage body as the gateway ledger, not as unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ stage: LEDGER, frozen_basis: REGISTERED_BASIS }), {
            status: 200,
          }),
        ),
      ),
    );
    try {
      const result = await createRunSetupClient("/profiles", "/runs").getStage(RUN_ID);
      expect(result.status).toBe("gateway");
      expect(result.status === "gateway" && result.stage.envelopes).toHaveLength(3);
      expect(result.status === "gateway" && result.frozenBasis?.configuration_store).toBe(
        "REGISTERED",
      );
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("shows snapshot, epoch, queue, exact batch and envelope bytes, and pending upload", async () => {
    renderAt(client({ status: "gateway", stage: LEDGER, frozenBasis: REGISTERED_BASIS }));
    await settledScreen();

    const view = ledger();
    expect(view.getAttribute("data-gateway-status")).toBe("STAGED");
    expect(view.querySelector("[data-gateway-snapshot]")?.textContent).toBe(SNAPSHOT);
    expect(view.querySelector("[data-gateway-epoch]")?.textContent).toBe("1");
    expect(view.querySelector("[data-gateway-queue]")?.textContent).toBe("1 READY, 2 STAGED");
    expect(view.querySelector("[data-gateway-upload]")?.getAttribute("data-gateway-upload")).toBe(
      "PENDING",
    );
    expect(view.querySelector("[data-gateway-receipts]")?.textContent).toBe("None");
    const words = spacedText(view);
    expect(words).toMatch(/no receipt exists/);
    expect(words).not.toMatch(/\b(accepted|delivered|acknowledged) (all|\d)/i);

    const batchRow = view.querySelector('[data-gateway-batch="batch-a-1"]') as HTMLElement;
    expect(batchRow.querySelector("[data-gateway-batch-sha256]")?.textContent).toBe("cd".repeat(32));
    expect(view.querySelector('[data-gateway-batch-canonical="batch-a-1"]')?.textContent).toBe(
      LEDGER.batches[0].canonical,
    );

    // Selecting an envelope shows its exact stored text, verbatim.
    const unsealed = view.querySelector('[data-gateway-envelope="msg-b-1"]') as HTMLElement;
    expect(unsealed.querySelector("[data-gateway-envelope-state]")?.textContent).toBe("READY");
    fireEvent.click(within(unsealed).getByRole("button"));
    expect(view.querySelector('[data-gateway-envelope-canonical="msg-b-1"]')?.textContent).toBe(
      LEDGER.envelopes[2].canonical,
    );
    expect(spacedText(view)).toMatch(/not sealed into a batch yet/);
  });

  it("shows a typed hold with its field and reason, and no envelope for it", async () => {
    renderAt(client({ status: "gateway", stage: LEDGER, frozenBasis: REGISTERED_BASIS }));
    await settledScreen();

    const hold = ledger().querySelector('[data-gateway-hold="UNKNOWN_CHANNEL"]') as HTMLElement;
    expect(hold.querySelector("[data-gateway-hold-field]")?.textContent).toBe("signal_id");
    expect(hold.textContent).toMatch(/not a channel of the active mapping/);
    expect(spacedText(ledger())).toMatch(/used no sequence number/);
  });

  it("names an unreachable gateway and shows nothing from any other store", async () => {
    const unreachable: GatewayLedgerStage = {
      ...LEDGER,
      status: "GATEWAY_UNAVAILABLE",
      statement: "The gateway could not be reached over its authenticated local channel.",
      sequence_epoch: null,
      unavailable_detail: "connection refused",
      queue_depth_by_state: {},
      envelopes: [],
      batches: [],
      holds: [],
      publication_notes: ["No gateway is provisioned for this Site."],
    };
    renderAt(client({ status: "gateway", stage: unreachable, frozenBasis: REGISTERED_BASIS }));
    await settledScreen();

    const view = ledger();
    expect(view.querySelector("[data-gateway-unavailable]")?.textContent).toMatch(/connection refused/);
    expect(view.querySelector("[data-gateway-notes]")?.textContent).toMatch(/No gateway is provisioned/);
    expect(view.querySelector("[data-gateway-envelope]")).toBeNull();
    expect(document.querySelector("[data-staged-envelope]")).toBeNull();
  });

  it("keeps Commit disabled for a registered run, even with no frozen basis reported", async () => {
    const fake = client({ status: "gateway", stage: LEDGER });
    renderAt(fake);
    await settledScreen();

    const panel = document.querySelector("[data-run-commit]") as HTMLElement;
    const button = within(panel).getByRole("button", { name: "Commit and release" });
    expect(button).toBeDisabled();
    expect(panel.querySelector("[data-commit-basis-block]")?.textContent).toMatch(
      /registered Site configuration/,
    );
    fireEvent.click(button);
    expect(fake.posts).toBe(0);
    expect(screen.queryByRole("button", { name: /Resume release|Retry release/ })).toBeNull();
  });

});

describe("a run whose simulated devices round what they publish (S2-01b)", () => {
  function withResolution(resolution: string | null | undefined): RunSetupClient {
    const execution = {
      ...RUNNING_IN_THE_GAP,
      signals: RUNNING_IN_THE_GAP.signals.map((signal) =>
        resolution === undefined ? signal : { ...signal, resolution },
      ),
    };
    return {
      ...client({ status: "gateway", stage: LEDGER }),
      ...executionMethods({ status: "loaded", execution }, { status: "gateway", stage: LEDGER }),
    };
  }

  it("shows each signal's resolution and never claims reported minus bias is exact", async () => {
    renderAt(withResolution("0.000001"));
    await settledScreen();

    const cells = document.querySelectorAll("[data-signal-resolution]");
    expect(cells.length).toBe(RUNNING_IN_THE_GAP.signals.length);
    expect(cells.length).toBeGreaterThan(0);
    expect(cells[0].getAttribute("data-signal-resolution")).toBe("0.000001");
    const note = document.querySelector("[data-signal-resolution-note]")?.textContent ?? "";
    expect(note).toMatch(/only to within half a step/);
    expect(note).toMatch(/not the value the gap hid/);
  });

  it("adds no resolution column for a run whose devices publish exactly", async () => {
    renderAt(withResolution(undefined));
    await settledScreen();
    expect(document.querySelector("[data-signal-resolution]")).toBeNull();
    expect(document.querySelector("[data-signal-resolution-note]")).toBeNull();
  });
});
