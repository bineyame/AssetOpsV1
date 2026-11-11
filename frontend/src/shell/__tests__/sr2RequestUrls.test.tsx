/**
 * SR-2 (demo-critical): moving pages onto the shared range must not change any API request for the same range or
 * day, so the demo's pre-built responses (`tools/demo_combined.py` `prebuilt_routes`, which derives each request from
 * the `story_links` web link with `URLSearchParams` encoding) and the demo-script links keep matching. Each case opens
 * a story-link address in the whole App with the real clients and records the URLs the page fetches.
 */
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { settledScreen } from "../../test/settled";

let urls: string[] = [];

beforeEach(() => {
  urls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      urls.push(typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url);
      return Promise.resolve(new Response("{}", { status: 503, headers: { "Content-Type": "application/json" } }));
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function requestsAt(path: string): Promise<string[]> {
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} />
    </MemoryRouter>,
  );
  await settledScreen();
  view.unmount();
  return urls;
}

describe("SR-2 the demo's API requests are byte-identical", () => {
  // The strings are main's (66a38d849) requests for these story-link addresses, recorded before SR-2 changed a page.
  const W = "from=2026-10-25T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z";
  it.each([
    ["/portfolio?from=2026-10-25T00:00:00Z&to=2026-11-02T00:00:00Z", [`/api/estate/portfolio?${W}&limit=50`, `/api/estate/outcome-summary?${W}`]],
    ["/findings?from=2026-10-25T00:00:00Z&to=2026-11-02T00:00:00Z", [`/api/estate/findings?${W}`, `/api/estate/scope?${W}`, `/api/estate/outcome-summary?${W}`]],
    ["/maintenance?from=2026-10-04T00:00:00Z&to=2026-11-04T00:00:00Z", ["/api/work/maintenance?from=2026-10-04T00%3A00%3A00Z&to=2026-11-04T00%3A00%3A00Z&limit=5"]],
  ])("%s requests exactly what it did before SR-2", async (path, expected) => {
    const got = await requestsAt(path);
    for (const url of expected) expect(got).toContain(url);
    // Nothing else on the estate or Work APIs: no second read for a reshaped range.
    expect(got.filter((u) => u.startsWith("/api/estate/") || u.startsWith("/api/work/")).sort()).toEqual([...expected].sort());
  });
});
