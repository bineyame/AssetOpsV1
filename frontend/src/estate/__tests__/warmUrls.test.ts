import { afterEach, expect, it, vi } from "vitest";
import { createEstateClient } from "../estateClient";
import { createFuelBalanceClient } from "../../sites/fuelBalanceClient";

// D-WARM.7: the URLs tools/warm_ranges.py warms (backend/tests/test_warm1_ranges.py asserts the same literals).
afterEach(() => vi.unstubAllGlobals());

async function urlOf(call: (c: ReturnType<typeof createEstateClient>) => Promise<unknown> | undefined) {
  const fetchMock = vi.fn(async () => new Response("{}", { status: 500 }));
  vi.stubGlobal("fetch", fetchMock);
  await call(createEstateClient());
  return String((fetchMock.mock.calls[0] as unknown[])[0]);
}

const W = "from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z";
const q = { from: "2026-11-02T00:00:00Z", to: "2026-11-09T00:00:00Z", known_at: null };

it("sends the state chip and scope-ids requests exactly as the warm tool does", async () => {
  expect(await urlOf((c) => c.findings({ ...q, lens: "all", state: "no_longer_supported", limit: null, cursor: null } as never))).toBe(
    `/api/estate/findings?${W}&state=no_longer_supported`,
  );
  expect(await urlOf((c) => c.portfolioScopeIds?.({ ...q, lens: "all" } as never))).toBe(`/api/estate/portfolio/scope-ids?${W}`);
  for (const lens of ["cost", "risks", "opportunities"]) {
    // D-WARM.8
    expect(await urlOf((c) => c.portfolioScopeIds?.({ ...q, lens } as never))).toBe(`/api/estate/portfolio/scope-ids?${W}&lens=${lens}`);
  }
});

it("sends the Fuel nights range request exactly as the warm tool times it", async () => {
  // SR-12: backend/tests/test_warm1_ranges.py asserts the same literal. The other SR-12 range routes have no page
  // client on main yet: re-check after the SR-5..SR-11 pages merge.
  const fetchMock = vi.fn(async () => new Response("{}", { status: 500 }));
  vi.stubGlobal("fetch", fetchMock);
  await createFuelBalanceClient().getNights("KISIWA-001", { from: q.from, to: q.to });
  expect(String((fetchMock.mock.calls[0] as unknown[])[0])).toBe(`/api/sites/KISIWA-001/fuel-balance/nights?${W}`);
});
