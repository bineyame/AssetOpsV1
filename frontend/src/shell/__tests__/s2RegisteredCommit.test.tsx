import { cleanup, fireEvent, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { settledScreen } from "../../test/settled";
import { RunCommitPanel } from "../RunCommitPanel";
import { registeredReleaseClaim } from "../RegisteredDeliveryView";
import { diagnosticUploadText } from "../GatewayPublicationPanels";
import type { RegisteredRelease, RunCommit, RunCommitResult, RunSetupClient } from "../runSetupClient";

/**
 * S2-02 phase 3b: Lab Commit/status for a registered run reads GET commit's
 * `registered_release`. Stage STAGED never reads as all published or
 * uploaded; a terminal gap or an unknown schedule is never fully released; a
 * shared batch is blocked; an unreadable gateway is unavailable, not refused.
 */

const BATCH = {
  batch_id: "b-1",
  source_id: "kobo-inverter-1",
  state: "ACKED",
  released: true,
  shared_with_another_run: false,
  item_count: 2,
  receipt: { receipt_sha256: "c".repeat(64), server_received_at: "2026-10-09T09:00:00.000001Z", server_completed_at: "2026-10-09T09:00:01.000001Z" },
  decisions: { ACCEPTED: 2 },
  last_error_code: null,
};

const COMPLETE: RegisteredRelease = {
  status: "AVAILABLE",
  detail: null,
  execution_status: "COMPLETED",
  delivery: {
    stage_status: "STAGED",
    envelope_count: 2,
    unbatched_envelope_count: 0,
    held_report_count: 0,
    batch_count: 1,
    released_batch_count: 1,
    batches_by_state: { STAGED: 0, READY: 0, IN_FLIGHT: 0, ACKED: 1, REFUSED: 0 },
    shared_batch_ids: [],
    batches: [BATCH],
    decisions: { ACCEPTED: 2 },
    refusals: [],
    last_upload_error: null,
    release_state: "TERMINAL",
    gateway_complete: true,
  },
  released_now: null,
  publication_gap: "NONE",
  publication_gap_detail: null,
  publication_schedule: {
    ordinary_publication: "COMPLETE",
    clock_instant: "2026-09-22T18:00:00Z",
    admitted_through: "2026-09-22T18:00:00Z",
    world_reached_instant: "2026-09-22T18:00:00Z",
    world_complete: true,
    ordinary_stopped_at: null,
    delayed_report_count: 1,
    delayed_pending_count: 0,
  },
  fully_released: true,
  release_blockers: [],
};

function withSchedule(patch: Partial<NonNullable<RegisteredRelease["publication_schedule"]>>): RegisteredRelease {
  return { ...COMPLETE, publication_schedule: { ...COMPLETE.publication_schedule!, ...patch } };
}

function loaded(view: RegisteredRelease, commit: RunCommit["commit"] = "RELEASED_TO_GATEWAY"): RunCommitResult {
  return {
    status: "loaded",
    commit: {
      commit,
      release: null,
      open_in_assetops: null,
      release_error: null,
      registered_release: view,
      fully_released: view.fully_released,
      statement: "Statement from the server.",
    },
  };
}

function renderPanel(read: RunCommitResult, answer?: RunCommitResult) {
  const fake = {
    posts: 0,
    getCommit: () => Promise.resolve(read),
    commit: () => {
      fake.posts += 1;
      return Promise.resolve(answer ?? read);
    },
  };
  render(
    <MemoryRouter>
      <RunCommitPanel runId="run-1" runSetup={fake as unknown as RunSetupClient} stage={null} />
    </MemoryRouter>,
  );
  return fake;
}

function claimShown(): string | null {
  return document.querySelector("[data-registered-release]")?.getAttribute("data-registered-release") ?? null;
}

afterEach(cleanup);

describe("registered run Commit/status", () => {
  it("reads as fully released only when the server, the blockers and the schedule all agree", async () => {
    renderPanel(loaded(COMPLETE));
    await settledScreen();
    expect(claimShown()).toBe("FULLY_RELEASED");
    expect(document.querySelector("[data-publication-completeness]")?.getAttribute("data-publication-completeness")).toBe("COMPLETE");
  });

  it.each([
    ["a terminal gap", withSchedule({ ordinary_publication: "TERMINAL_GAP", ordinary_stopped_at: "2026-09-22T12:00:00Z" })],
    ["an incomplete schedule", withSchedule({ ordinary_publication: "INCOMPLETE" })],
    ["an unknown schedule", { ...COMPLETE, publication_schedule: null, publication_gap: "UNKNOWN" }],
    ["a listed blocker", { ...COMPLETE, release_blockers: ["RECEIPTS_PENDING"] }],
  ])("never claims fully released with %s, even when the server flag says so", (_name, view) => {
    expect(registeredReleaseClaim(view as RegisteredRelease)).toBe("NOT_FULLY_RELEASED");
  });

  it("shows a STAGED Stage with an incomplete schedule as not fully released and says what STAGED covers", async () => {
    const view = { ...withSchedule({ ordinary_publication: "INCOMPLETE" }), fully_released: false, release_blockers: ["PUBLICATION_GAP"] };
    renderPanel(loaded(view));
    await settledScreen();
    expect(claimShown()).toBe("NOT_FULLY_RELEASED");
    expect(document.querySelector("[data-stage-status='STAGED']")?.textContent).toMatch(
      /does not show that every expected report was published or uploaded/,
    );
    expect(document.querySelector("[data-commit-blocker='PUBLICATION_GAP']")?.textContent).toMatch(/never published/);
    expect(document.body.textContent).not.toMatch(/Fully released/);
  });

  it("shows a terminal gap as incomplete for good", async () => {
    const view = {
      ...withSchedule({ ordinary_publication: "TERMINAL_GAP", ordinary_stopped_at: "2026-09-22T12:00:00Z" }),
      fully_released: false,
      release_blockers: ["PUBLICATION_INSTANT_PASSED"],
    };
    renderPanel(loaded(view));
    await settledScreen();
    expect(document.querySelector("[data-publication-completeness='TERMINAL_GAP']")?.textContent).toMatch(/Incomplete for good/);
    expect(document.querySelector("[data-commit-blocker='PUBLICATION_INSTANT_PASSED']")).not.toBeNull();
  });

  it("shows a shared batch blocked and does not release it under this run", async () => {
    const view: RegisteredRelease = {
      ...COMPLETE,
      fully_released: false,
      release_blockers: ["BATCH_SHARED_WITH_ANOTHER_RUN", "NOT_ALL_BATCHES_RELEASED"],
      delivery: {
        ...COMPLETE.delivery!,
        batch_count: 2,
        released_batch_count: 1,
        shared_batch_ids: ["b-2"],
        gateway_complete: false,
        batches: [BATCH, { ...BATCH, batch_id: "b-2", state: "STAGED", released: false, shared_with_another_run: true, receipt: null, decisions: {} }],
      },
    };
    renderPanel(loaded(view));
    await settledScreen();
    expect(document.querySelector("[data-registered-batch='b-2']")?.textContent).toMatch(/Blocked: shared with another run/);
    expect(document.querySelector("[data-release-counts]")?.textContent).toMatch(/1 shared with another run and blocked/);
    // Every unshared batch is already released, so no release is offered for the shared one.
    expect(document.querySelector("[data-registered-release] button")).toBeNull();
  });

  it("shows an unreadable gateway as unavailable, not as a refusal or as progress", async () => {
    renderPanel(
      loaded({
        ...COMPLETE,
        status: "GATEWAY_UNAVAILABLE",
        detail: "no gateway is configured for this host",
        delivery: null,
        publication_schedule: null,
        publication_gap: null,
        fully_released: false,
        release_blockers: ["GATEWAY_UNAVAILABLE"],
      }),
    );
    await settledScreen();
    expect(claimShown()).toBe("UNAVAILABLE");
    expect(document.querySelector("[data-commit-state='UNAVAILABLE']")?.textContent).toMatch(/this is not a refusal/);
  });

  it("offers Commit and release for a completed run with unreleased batches and shows the answer", async () => {
    const before: RegisteredRelease = {
      ...COMPLETE,
      fully_released: false,
      release_blockers: ["NOT_ALL_BATCHES_RELEASED", "RECEIPTS_PENDING"],
      delivery: { ...COMPLETE.delivery!, released_batch_count: 0, gateway_complete: false, batches: [{ ...BATCH, state: "STAGED", released: false, receipt: null }] },
    };
    const fake = renderPanel(loaded(before, "NOT_COMMITTED"), loaded(COMPLETE));
    await settledScreen();
    fireEvent.click(document.querySelector("[data-registered-release] button") as HTMLElement);
    await settledScreen();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(fake.posts).toBe(1);
    expect(claimShown()).toBe("FULLY_RELEASED");
  });
});

describe("local diagnostic upload state", () => {
  it("never shows a retried diagnostic as refused or received", () => {
    expect(diagnosticUploadText({ state: "ACKED", last_attempt_at: "x" })).toMatch(/verified receipt/);
    expect(diagnosticUploadText({ state: "READY", last_attempt_at: null })).toMatch(/waits for upload/);
    const retried = diagnosticUploadText({ state: "READY", last_attempt_at: "2026-10-09T09:00:00Z" });
    expect(retried).toMatch(/did not produce a receipt; it waits to be retried/);
    expect(retried).not.toMatch(/refused|received by/);
  });
});
