import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import { RUN_COMMIT_HEADING_ID } from "../RunCommitPanel";
import type {
  ReleaseBatch,
  RunCommit,
  RunCommitResult,
  RunSetupClient,
  RunStageResult,
  RunSummary,
} from "../runSetupClient";
import {
  COMPLETED,
  NOT_STAGED,
  STAGED_IN_THE_GAP,
  executionMethods,
} from "./executionFixtures";

/**
 * The Lab run screen's Commit and release panel (T027 AC7, AC18).
 *
 * Commit and release are two facts. The release fact is ingestion's: it never
 * says every record was accepted unless accepted equals total, an interrupted
 * release names how far it got and offers to resume, and "Open in AssetOps"
 * appears only when ingestion reports an accepted window.
 */

const RUN_ID = "run-1f0c2b7a4e5d4c8fa1b2c3d4e5f60718";
const URL = `/simulator-lab/runs/${RUN_ID}`;

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const RUN: RunSummary = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: null,
  created_at: "2026-09-22T09:00:00Z",
  site_id: "MG-001",
  scenario_id: "fuel-loss-event",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
  template_lineage: {
    state: "RECORDED",
    template_id: "hybrid-mini-grid-100kw",
    template_version: 2,
  },
};

const ELIGIBLE: RunStageResult = {
  status: "loaded",
  stage: {
    ...STAGED_IN_THE_GAP,
    execution_status: "COMPLETED",
    release_eligible: true,
    release_blockers: [],
    published_through: 165,
  },
};

const NOT_ELIGIBLE: RunStageResult = { status: "loaded", stage: NOT_STAGED };

const COMMIT_SUMMARY = {
  artifact_id: "artifact-run-1f0c",
  integrity_digest: "sha256:0123456789abcdef0123456789abcdef",
  envelope_count: 125,
  sealed_at: "2026-10-02T10:00:00Z",
  run_id: RUN_ID,
  site_id: "MG-001",
};

function release(overrides: Partial<ReleaseBatch>): ReleaseBatch {
  return {
    batch_id: "artifact-run-1f0c",
    site_id: "MG-001",
    source_id: "kobo-gw-1",
    gateway_id: "gw-1",
    source_mode: "SIMULATED",
    status: "COMPLETED",
    total: 125,
    processed: 125,
    accepted: 125,
    duplicates: 0,
    rejected: 0,
    conflicts: 0,
    refusal: null,
    started_at: "2026-10-02T10:00:01Z",
    completed_at: "2026-10-02T10:00:03Z",
    window_start: "2026-07-01T00:00:00Z",
    window_end: "2026-07-01T06:00:00Z",
    ...overrides,
  };
}

const HREF =
  "/sites/MG-001/evidence?from=2026-07-01T00:00:00Z&to=2026-07-01T06:00:00Z&batch=artifact-run-1f0c";

function committed(batch: ReleaseBatch | null, releaseError: string | null = null): RunCommitResult {
  const commit: RunCommit = {
    commit: COMMIT_SUMMARY,
    release: batch,
    open_in_assetops:
      batch === null || batch.window_start === null || batch.window_end === null
        ? null
        : {
            site_id: "MG-001",
            window_start: batch.window_start,
            window_end: batch.window_end,
            batch_id: batch.batch_id,
            href: HREF,
          },
    release_error: releaseError,
  };
  return { status: "loaded", commit };
}

const NOT_COMMITTED: RunCommitResult = {
  status: "loaded",
  commit: {
    commit: "NOT_COMMITTED",
    release: null,
    open_in_assetops: null,
    release_error: null,
  },
};

function client(
  stage: RunStageResult,
  read: RunCommitResult,
  answers: RunCommitResult[] = [],
): RunSetupClient & { posts: number } {
  const fake = {
    posts: 0,
    listProfiles: () => Promise.resolve({ status: "unavailable" as const }),
    createRun: () => Promise.resolve({ status: "unavailable" as const, message: null }),
    listRuns: () => Promise.resolve({ status: "loaded" as const, runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded" as const, run: RUN }),
    ...executionMethods({ status: "loaded", execution: COMPLETED }, stage),
    getCommit: () => Promise.resolve(read),
    commit: () => {
      fake.posts += 1;
      return Promise.resolve(answers[fake.posts - 1] ?? answers[answers.length - 1]);
    },
  };
  return fake;
}

function renderAt(runSetup: RunSetupClient) {
  return render(
    <MemoryRouter initialEntries={[URL]}>
      <App
        flags={featureFlagsWith(true)}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

function panel(): HTMLElement {
  return document
    .getElementById(RUN_COMMIT_HEADING_ID)
    ?.closest("section") as HTMLElement;
}

describe("the Commit panel", () => {
  it("disables Commit on a stage that is not release-eligible and names its blockers", async () => {
    renderAt(client(NOT_ELIGIBLE, NOT_COMMITTED));
    await settledScreen();

    const button = within(panel()).getByRole("button", { name: "Commit and release" });
    expect(button).toBeDisabled();
    const blockers = Array.from(
      panel().querySelectorAll("[data-commit-blocker]"),
    ).map((item) => item.getAttribute("data-commit-blocker"));
    expect(blockers).toEqual(NOT_STAGED.release_blockers.map((item) => item.kind));
    expect(blockers.length).toBeGreaterThan(0);
    expect(within(panel()).queryByRole("link", { name: "Open in AssetOps" })).toBeNull();
  });

  it("commits an eligible stage and shows Commit and release as two facts with Open in AssetOps", async () => {
    const runSetup = client(ELIGIBLE, NOT_COMMITTED, [committed(release({}))]);
    renderAt(runSetup);
    await settledScreen();

    const button = within(panel()).getByRole("button", { name: "Commit and release" });
    expect(button).toBeEnabled();
    fireEvent.click(button);
    await screen.findByText(/Sealed artifact-run-1f0c/);

    expect(runSetup.posts).toBe(1);
    const terms = Array.from(panel().querySelectorAll("dt")).map((term) => term.textContent);
    expect(terms).toEqual(["Commit", "Release"]);
    const words = spacedText(panel());
    expect(words).toContain("125 envelopes, sealed at 2026-10-02T10:00:00Z");
    expect(words).toContain("integrity digest sha256:0123456789ab…");
    expect(words).toMatch(/COMPLETED, 125 of 125 processed/);
    expect(words).toMatch(/Ingestion accepted all 125 records/);
    expect(
      within(panel()).getByRole("link", { name: "Open in AssetOps" }),
    ).toHaveAttribute("href", HREF);
    expect(within(panel()).queryByRole("button", { name: "Resume release" })).toBeNull();
  });

  it("never says every record was accepted when some were rejected", async () => {
    renderAt(
      client(
        ELIGIBLE,
        committed(release({ accepted: 120, rejected: 3, duplicates: 2 })),
      ),
    );
    await settledScreen();

    const words = spacedText(panel());
    expect(words).toMatch(/Ingestion accepted 120 of 125 records/);
    expect(words).toContain("3 rejected");
    expect(words).toContain("2 duplicates");
    expect(words).not.toMatch(/accepted all/i);
    expect(words).not.toMatch(/every record/i);
  });

  it("shows an interrupted release with how far it got, the error verbatim and Resume release", async () => {
    const interrupted = committed(
      release({
        status: "IN_PROGRESS",
        processed: 40,
        accepted: 40,
        completed_at: null,
      }),
      "OSError: disk full",
    );
    const runSetup = client(ELIGIBLE, interrupted, [committed(release({}))]);
    renderAt(runSetup);
    await settledScreen();

    const words = spacedText(panel());
    expect(words).toMatch(/Release interrupted after 40 of 125/);
    expect(words).not.toMatch(/accepted all/i);
    expect(panel().querySelector("[data-commit-release-error]")?.textContent).toContain(
      "OSError: disk full",
    );

    fireEvent.click(within(panel()).getByRole("button", { name: "Resume release" }));
    await screen.findByText(/Ingestion accepted all 125 records/);
    expect(runSetup.posts).toBe(1);
    expect(panel().querySelector("[data-commit-release-error]")).toBeNull();
  });

  it("names a refused Commit and its blockers without claiming a seal", async () => {
    const refused: RunCommitResult = {
      status: "refused",
      code: "COMMIT_REFUSED",
      message: "This draft's stage is not eligible for Commit, so nothing was sealed or released.",
      releaseBlockers: [{ kind: "STAGING_INCOMPLETE", statement: "Not every boundary." }],
    };
    renderAt(client(ELIGIBLE, NOT_COMMITTED, [refused]));
    await settledScreen();

    fireEvent.click(within(panel()).getByRole("button", { name: "Commit and release" }));
    await screen.findByText(/nothing was sealed or released/);
    expect(
      panel().querySelector("[data-commit-refusal]")?.getAttribute("data-commit-refusal"),
    ).toBe("COMMIT_REFUSED");
    expect(spacedText(panel())).toContain("STAGING_INCOMPLETE");
    expect(panel().querySelector('[data-commit-state="COMMITTED"]')).toBeNull();
  });

  it("states the stage's eligibility as Commit's condition, not as a missing capability", async () => {
    renderAt(client(ELIGIBLE, NOT_COMMITTED));
    await settledScreen();

    const release = document.querySelector("[data-stage-release]");
    expect(release?.textContent).not.toMatch(/do not exist/);
  });
});
