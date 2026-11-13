/**
 * SR-7b (rev 10 §10.3, rev 10a.2 Q7; D-SR.25): Site Evidence's claim-limit section over the date range. No `day` →
 * the `claim-limit-range` day table; `day&revision` → the existing one-day section plus "Back to the whole range".
 */
import { act, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { settledScreen } from "../../test/settled";
import { EvidenceClaimLimit } from "../EvidenceClaimLimit";
import { CLAIM_LIMIT_NO_SELECTION, CLAIM_LIMIT_RANGE_NOT_APPLICABLE, OPEN_THIS_DAY } from "../ClaimLimitRange";
import type { ClaimLimitClient } from "../claimLimitClient";
import { createSiteRangeClient, type ClaimLimitRangeBody, type ClaimLimitRangeDay, type RangeRead, type SiteRangeClient } from "../siteRangeClient";
import { BACK_TO_RANGE } from "../SiteRangeParts";
import { RETRYING_COPY, STILL_UNAVAILABLE_COPY } from "../temporarilyUnavailable";

const RANGE = "from=2026-11-02T00%3A00%3A00Z&to=2026-11-05T00%3A00%3A00Z";
const REV = "33333333-3333-4333-8333-333333333333";

const day = (d: string, over: Partial<ClaimLimitRangeDay> = {}): ClaimLimitRangeDay => ({
  day: d,
  revision_id: REV,
  available: true,
  state: "FULL",
  current_ceiling: null,
  ceiling_statement: null,
  window_assessment_revision_id: REV,
  gap_count: 0,
  reasons: [],
  link: `/sites/KOBO-001/evidence?day=${d}&revision=${REV}`,
  ...over,
});

const BODY: ClaimLimitRangeBody = {
  schema_version: "site-claim-limit-range-1",
  site: { site_code: "KOBO-001", site_name: "Kobo", timezone: "Africa/Nairobi" },
  window: { from: "2026-11-02T00:00:00Z", to: "2026-11-05T00:00:00Z", known_at: null },
  days: [
    day("2026-11-02", { current_ceiling: "CANDIDATE_AVOIDABLE", ceiling_statement: "At most CANDIDATE_AVOIDABLE over 45 min" }),
    day("2026-11-03", { state: "CONTRADICTORY", gap_count: 2 }),
    day("2026-11-04", { revision_id: null, state: "NO_SELECTION", window_assessment_revision_id: null, link: null }),
  ],
  summary: { days_with_positive_claim: 1, days_indeterminate: 1, days_without_selection: 1, days_requested: 3 },
};

const NO_DAY_READ: ClaimLimitClient = {
  getClaimLimit: () => Promise.resolve({ status: "unavailable", code: null, message: null }),
  getAssessedDay: () => Promise.resolve({ status: "unavailable", code: null, message: null }),
};

function stub(answer: RangeRead<ClaimLimitRangeBody>): SiteRangeClient & { calls: unknown[][] } {
  const calls: unknown[][] = [];
  const no = () => Promise.resolve({ status: "unavailable" as const, code: null });
  return {
    calls,
    getServiceRange: no,
    getBackupRange: no,
    getClaimLimitRange: (...args) => {
      calls.push(args);
      return Promise.resolve(answer);
    },
  };
}

function Where() {
  return <output data-testid="where">{useLocation().search}</output>;
}

function mount(search: string, rangeClient?: SiteRangeClient) {
  return render(
    <MemoryRouter initialEntries={[`/sites/KOBO-001/evidence${search}`]}>
      <Routes>
        <Route
          path="/sites/:siteId/evidence"
          element={
            <>
              <EvidenceClaimLimit siteId="KOBO-001" client={NO_DAY_READ} rangeClient={rangeClient} />
              <Where />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

const rows = () =>
  Array.from(document.querySelectorAll("[data-claim-limit-range-day]"), (tr) =>
    Array.from(tr.querySelectorAll("th, td"), (c) => c.textContent),
  );

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("SR-7b the claim limit over the range", () => {
  it("no day: one range read with the address window; one row per day, no invented ceiling, no link without a selection", async () => {
    const client = stub({ status: "loaded", value: BODY });
    mount(`?view=analysis&${RANGE}&known_at=2026-11-05T06%3A00%3A00Z`, client);
    await settledScreen();
    expect(client.calls).toEqual([
      ["KOBO-001", { from: "2026-11-02T00:00:00Z", to: "2026-11-05T00:00:00Z", known_at: "2026-11-05T06:00:00Z" }, expect.any(Function)],
    ]);
    expect(screen.getByText("1 of 3 days support a conclusion · 1 undetermined · 1 without an assessment")).toBeTruthy();
    expect(rows()).toEqual([
      ["2 Nov", "The readings support calling this day's generator operation avoidable", "None", OPEN_THIS_DAY],
      ["3 Nov", "Readings for this day conflict, so no conclusion is drawn", "2 reading gaps", OPEN_THIS_DAY],
      ["4 Nov", CLAIM_LIMIT_NO_SELECTION, "–", "–"],
    ]);
    // The server's statement is system wording (`CANDIDATE_AVOIDABLE`): never shown.
    expect(document.body.textContent).not.toContain("CANDIDATE_AVOIDABLE");
    // The row link opens the existing one-day section on the Analysis view, carrying the range and cutoff (SR-4a).
    const link = screen.getAllByRole("link", { name: OPEN_THIS_DAY })[0].getAttribute("href") ?? "";
    const q = new URLSearchParams(link.split("?")[1]);
    expect(link.split("?")[0]).toBe("/sites/KOBO-001/evidence");
    expect([q.get("day"), q.get("revision"), q.get("view"), q.get("known_at")]).toEqual(["2026-11-02", REV, "analysis", "2026-11-05T06:00:00Z"]);
    expect([q.get("from"), q.get("to")]).toEqual(["2026-11-02T00:00:00Z", "2026-11-05T00:00:00Z"]);
  });

  it("day&revision: the existing one-day section plus Back to the whole range (day and revision dropped, range kept)", async () => {
    const client = stub({ status: "loaded", value: BODY });
    mount(`?view=analysis&${RANGE}&day=2026-11-02&revision=${REV}`, client);
    await settledScreen();
    expect(client.calls).toEqual([]);
    expect(document.querySelector("[data-claim-limit-range]")).toBeNull();
    const back = screen.getByRole("link", { name: BACK_TO_RANGE }).getAttribute("href") ?? "";
    expect(back).toBe(`/sites/KOBO-001/evidence?view=analysis&${RANGE}`);
  });

  it("no day and no range keeps the old no-day line; no range read", async () => {
    const client = stub({ status: "loaded", value: BODY });
    mount("?view=analysis", client);
    await settledScreen();
    expect(client.calls).toEqual([]);
    expect(document.querySelector('[data-claim-limit-state="no-day"]')).not.toBeNull();
  });

  it.each([
    [404, "CLAIM_LIMIT_RANGE_NOT_APPLICABLE", CLAIM_LIMIT_RANGE_NOT_APPLICABLE],
    [404, "SITE_NOT_FOUND", "This site was not found."],
    [409, "PERFORMANCE_CUTOVER_CLOSED", "Assessment results are not released for this site yet, so no limit is shown."],
    [422, "INVALID_WINDOW", "Choose a valid date range of at most 31 days."],
    [401, "NOT_AUTHENTICATED", "Sign in to see this range."],
    [403, "FORBIDDEN", "Your account does not have access to this site."],
  ])("refusal %s %s is named in words, never the code", async (httpStatus, code, words) => {
    mount(`?${RANGE}`, stub({ status: "refused", httpStatus, code, message: "SERVER TEXT" }));
    expect(await screen.findByText(words)).toBeTruthy();
    expect(document.body.textContent).not.toContain(code);
    expect(document.body.textContent).not.toContain("SERVER TEXT");
  });

  it("503 SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE: Retrying… while it retries the same URL, then the body", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const urls: string[] = [];
    const answers = [
      new Response(JSON.stringify({ detail: { code: "SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE" } }), { status: 503 }),
      new Response(JSON.stringify(BODY), { status: 200 }),
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        urls.push(String(input));
        return Promise.resolve(answers.shift() as Response);
      }),
    );
    mount(`?${RANGE}`, createSiteRangeClient("/api/sites", [50]));
    expect(await screen.findByText(RETRYING_COPY)).toBeTruthy();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60);
    });
    await settledScreen();
    expect(urls).toEqual([`/api/sites/KOBO-001/claim-limit-range?${RANGE}`, `/api/sites/KOBO-001/claim-limit-range?${RANGE}`]);
    expect(rows()).toHaveLength(3);
  });

  it("503 still unavailable after the last retry: the still-unavailable line, never a data state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify({ detail: { code: "SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE" } }), { status: 503 }))),
    );
    mount(`?${RANGE}`, createSiteRangeClient("/api/sites", []));
    expect(await screen.findByText(STILL_UNAVAILABLE_COPY)).toBeTruthy();
    expect(document.querySelector("[data-claim-limit-range]")).toBeNull();
  });
});
