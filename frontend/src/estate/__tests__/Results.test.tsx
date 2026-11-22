/**
 * IA-P P3b (spec §5.3, I14): Results at `/results`: `PageHeader` "Results" with "What changed in this review", then
 * `ProgressPanel` moved verbatim from the Portfolio's What changed tab, reading the estate portfolio's page 1 for the
 * window. The progress assertions are `estatePortfolio.test.tsx`'s `rendersChangeDisclosureWithoutRecoveredMoney`,
 * moved here with the panel.
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { settledScreen } from "../../test/settled";
import { ResultsPage, RESULTS_PATH } from "../Results";
import { loadedPortfolio, portfolioBody, portfolioClient, refused } from "./portfolioFixtures";

const ENTRY = `${RESULTS_PATH}?from=2026-10-13&to=2026-10-19`;

function renderAt(entry: string, client: ReturnType<typeof portfolioClient>) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <main>
        <Routes>
          <Route path={RESULTS_PATH} element={<ResultsPage client={client} />} />
        </Routes>
      </main>
    </MemoryRouter>,
  );
}

const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();

const progressRow = (id: string, selected: boolean, origin?: boolean) => ({
  action_id: id,
  action_code: "A1",
  selected_action_event_id: "ev",
  verification_plan_id: null,
  verification_outcome_id: null,
  application_state: "APPLIED" as const,
  resolution_state: null,
  verification_outcome: null,
  recorded_at: "2026-10-06T10:00:00Z",
  origin_revision_selected: selected,
  ...(origin === undefined ? {} : { origin_selected: origin }),
});

describe("IA-P P3b: Results", () => {
  it("shows the header and the progress panel read from the portfolio's page 1 for the window", async () => {
    const body = portfolioBody({
      rows: [],
      total_count: 0,
      progress: { ...portfolioBody().progress, pending_trial_count: null, verified_resolution_count: 2, rows: [progressRow("act-1", true), progressRow("act-2", false), progressRow("act-3", false, true), progressRow("act-4", true, false)] },
    });
    const client = portfolioClient(loadedPortfolio(body));
    renderAt(ENTRY, client);
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Results");
    expect(document.body.textContent).toContain("What changed in this review");
    expect(client.calls).toHaveLength(1);
    expect(client.calls[0]).toMatchObject({ from: "2026-10-13T00:00:00Z", to: "2026-10-20T00:00:00Z", lens: "all", limit: 50, cursor: null });
    const progress = document.querySelector("main")!;
    expect(text(progress)).toContain("Completed activity · Not known yet");
    expect(text(progress)).toContain("Trials waiting for a result · Unknown");
    expect(text(progress)).toContain("Fixes confirmed · 2");
    expect(text(progress)).toContain("Recovered value not known yet");
    expect(progress.querySelectorAll("[data-portfolio-origin-unselected]")).toHaveLength(2);
    expect(progress.querySelector("[data-portfolio-progress-row='act-3'] [data-portfolio-origin-unselected]")).toBeNull();
    expect(progress.querySelector("[data-portfolio-progress-row='act-4'] [data-portfolio-origin-unselected]")).not.toBeNull();
    expect(text(progress)).not.toMatch(/\$|USD/);
  });

  it("a refusal shows the estate refusal, not the panel", async () => {
    renderAt(ENTRY, portfolioClient(refused(503, "ESTATE_STORE_UNAVAILABLE", "The estate store cannot be read right now.")));
    await settledScreen();
    expect(document.body.textContent).toContain("The estate store cannot be read right now.");
    expect(document.querySelector("[data-portfolio-progress-row]")).toBeNull();
  });
});
