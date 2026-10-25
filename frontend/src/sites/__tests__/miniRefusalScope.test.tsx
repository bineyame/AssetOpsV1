import { cleanup, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { MiniDepthClient, MiniRead } from "../miniDepthClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { settledScreen } from "../../test/settled";

/*
 * post-W6 W4 build ruling 5: the Q7 refused frame (strip with `Confidence: Not assessed`, muted tiles, one reason)
 * is for the invalid-window 422 only, on all four mini depth screens. 401/403/404/503 keep their own refusal block
 * and copy; none renders an input-validation frame or a measured confidence.
 */

afterEach(cleanup);

const CODE = "MG-W4-REFUSAL-001";
const SITE = {
  site_id: CODE,
  display_name: "W4 refusal scope",
  site_type: "MINIGRID",
  location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: "Africa/Addis_Ababa",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };
const CAPS = ["service", "fuel", "renewable", "backup"].map((id) => ({ id, display_name: id }));

const SCREENS = [
  ["renewable", "from=2026-10-05T21:00:00Z&to=2026-10-06T21:00:00Z"],
  ["service", "from=2026-10-06T09:00:00Z&to=2026-10-06T10:00:00Z"],
  ["fuel", "from=2026-10-06T09:00:00Z&to=2026-10-06T10:00:00Z"],
  ["backup", "from=2026-10-06T09:00:00Z&to=2026-10-06T10:00:00Z"],
] as const;

const STATUSES = [
  [401, "unauthenticated", "Sign in to read this site's mini-grid assessment."],
  [403, "forbidden", "You do not have access to this site."],
  [404, "not-found", "This page was not found."],
  [503, "unavailable", null],
] as const;

function renderScreen(screen: string, query: string, answer: MiniRead<never>) {
  const reply = vi.fn(() => Promise.resolve(answer));
  const client = {
    getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: CAPS })),
    getRenewable: reply,
    getService: reply,
    getFuel: reply,
    getBackup: reply,
  } as unknown as MiniDepthClient;
  render(
    <MemoryRouter initialEntries={[`/sites/${CODE}/performance/${screen}?${query}`]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} miniDepth={client} />
    </MemoryRouter>,
  );
}

describe("post-W6 W4 build ruling 5: the refused frame is scoped to the invalid-window 422", () => {
  for (const [screen, query] of SCREENS) {
    it.each(STATUSES)(`${screen}: HTTP %s keeps its own refusal (%s), no input-validation frame`, async (http, key, body) => {
      renderScreen(screen, query, { status: "refused", httpStatus: http, code: "X_CODE", message: "server words" } as MiniRead<never>);
      await settledScreen();
      const refusal = await vi.waitFor(() => {
        const el = document.querySelector(`[data-page-refusal="${key}"]`);
        expect(el).not.toBeNull();
        return el as HTMLElement;
      });
      if (body !== null) expect(refusal.textContent).toContain(body);
      expect(document.querySelector("[data-mini-refused-strip]")).toBeNull();
      expect(document.querySelector('[data-page-refusal="invalid-window"]')).toBeNull();
      expect(document.querySelector("[data-mini-cards]")).toBeNull();
      expect(document.body.textContent).not.toMatch(/Confidence: (?!Not assessed)/);
      expect(document.body.textContent).not.toContain("server words");
    });

    it(`${screen}: HTTP 422 renders the frame with Confidence: Not assessed`, async () => {
      renderScreen(screen, query, { status: "refused", httpStatus: 422, code: "INVALID_WINDOW", message: "server words" } as MiniRead<never>);
      await settledScreen();
      const strip = await vi.waitFor(() => {
        const el = document.querySelector(`[data-mini-refused-strip="${screen}"]`);
        expect(el).not.toBeNull();
        return el as HTMLElement;
      });
      expect(strip.querySelector("[data-mini-confidence]")?.textContent).toBe("Confidence: Not assessed");
      expect(document.querySelectorAll('[data-page-refusal="invalid-window"]')).toHaveLength(1);
      expect(document.body.textContent).not.toContain("server words");
    });
  }
});
