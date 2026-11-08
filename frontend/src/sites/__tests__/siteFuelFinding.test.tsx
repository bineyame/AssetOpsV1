import { act, cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteFuelFindingFrame } from "../../shell/SiteAnalyticsFrames";
import { SITE_FUEL_FINDING_ROUTE_PATH, routeFor, siteFuelFindingHref } from "../../shell/operatorSiteRoutes";
import { refOfHref } from "../../test/linkRefs";
import { settledScreen } from "../../test/settled";
import type { FuelBalanceClient, FuelFindingBody, FuelNightBody } from "../fuelBalanceClient";
import type { MiniRead } from "../miniDepthClient";
import { SiteFuelChecks } from "../SiteFuelFinding";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";

/*
 * DIESEL-K5 F6-F8 (build sheet DIESEL-1 §9l.2): the fuel Finding page at its own address (SUPPORTED and
 * NO_LONGER_SUPPORTED lines, the night link, `?revision_id=` pinning), the FUEL_FINDING ref and its linkRefs
 * round-trip, and the Site Findings "Fuel checks" panel (present with rows, absent with none).
 */

afterEach(cleanup);

const CODE = "KISIWA-001";
const FID = "7f1e0a52-3333-4a1e-9e7d-000000000005";
const R1 = "7f1e0a52-3333-4a1e-9e7d-000000000006";
const R2 = "7f1e0a52-3333-4a1e-9e7d-000000000007";
const SITE = {
  site_id: CODE,
  display_name: "Kisiwa island mini-grid",
  site_type: "MINIGRID",
  location: { country: "Tanzania", locality: "Kisiwa" },
  timezone: "Africa/Dar_es_Salaam",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };

const NIGHT = {
  night_date: "2026-10-04",
  label: "Night of 4 Oct · 6 pm to noon",
  state: "UNEXPLAINED",
  status: "Fuel balance: unexplained fuel",
  tone: "amber",
  revision: 1,
  bridge: [
    { term: "OPENING", label: "Opening inventory", value: "869.2 L", basis: "Tank reading at 18:00", treatment: "Declared sensor accuracy ±10 L", evidence_count: 1 },
    { term: "RESIDUAL", label: "Unexplained residual", value: "95.7–144.3 L", basis: "Opening + deliveries − use − closing", treatment: "Compared with the combined margin; never says why fuel left", evidence_count: 3 },
  ],
  records: [{ code: "REC-000004", kind: "Tank dip", when: "07:00, 5 Oct", volume: "706 L", occurred_at: "2026-10-05T04:00:00+00:00" }],
  records_empty: "No delivery or tank dip recorded this night",
  links: { evidence: `/sites/${CODE}/evidence`, fuel_page: `/sites/${CODE}/performance/fuel?night=2026-10-04` },
} as unknown as FuelNightBody;

const CLAIM = "About 95.7–144.3 L left the tank on the night of 4 Oct (6 pm to noon) that the generator's modelled use and the recorded deliveries don't explain.";
const GAP = "The tank sensor sent no readings from 00:45 to 02:30.";
const MONEY = "Worth about 119.57–180.43 USD at your declared 1.25 USD per litre (a modelled range that includes the stated margin)";
const NOT_WHY = "This does not say why the fuel left the tank.";
const MARGIN = "The range allows for the tank sensor's declared accuracy of 10 L at each reading, 10 % either way on the generator's modelled use, and 1 % on each recorded delivery.";
const NO_LONGER = "A later check of this night no longer finds unexplained fuel.";

function body(revision: "1" | "2"): FuelFindingBody {
  const supported = revision === "1";
  return {
    site_code: CODE,
    finding_id: FID,
    revision_id: supported ? R1 : R2,
    revision_no: supported ? 1 : 2,
    lifecycle: supported ? "SUPPORTED" : "NO_LONGER_SUPPORTED",
    lifecycle_text: supported ? "Supported by the latest check" : "No longer supported",
    night_date: "2026-10-04",
    label: "Night of 4 Oct · 6 pm to noon",
    lines: supported
      ? { title: "Unexplained fuel overnight", claim: CLAIM, gap: GAP, money: MONEY, not_why: NOT_WHY, margin: MARGIN, no_longer: null }
      : { title: "Unexplained fuel overnight", claim: null, gap: null, money: null, not_why: NOT_WHY, margin: null, no_longer: NO_LONGER },
    night: NIGHT,
    revisions: [
      { revision_id: R1, revision_no: 1, text: "Version 1 · Supported by the latest check · 16:00, 5 Oct" },
      { revision_id: R2, revision_no: 2, text: "Version 2 · No longer supported · 16:00, 6 Oct" },
    ],
    provenance: { source_provenance: null, selected_source_provenance: { classification: "REGISTERED_SIMULATION" }, pending_source_provenance: null },
    links: { canonical: `/sites/${CODE}/fuel-findings/${FID}`, fuel_night: `/sites/${CODE}/performance/fuel?night=2026-10-04`, fuel_night_label: "Open this night on the Fuel page" },
  };
}

function client(rows: { finding_id: string; night_date: string; lifecycle: string; text: string; href: string }[] = []) {
  const c: FuelBalanceClient = {
    getNights: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getNight: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getFuelFindings: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: { site_code: CODE, rows } })),
    getFuelFinding: vi.fn(
      (_code: string, _id: string, revisionId?: string | null): Promise<MiniRead<FuelFindingBody>> =>
        Promise.resolve({ status: "loaded", value: body(revisionId === R2 ? "2" : "1") }),
    ),
  };
  return c;
}

function renderPage(c: FuelBalanceClient, path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={SITE_FUEL_FINDING_ROUTE_PATH} element={<SiteFuelFindingFrame detail={detail} sitesPath="/sites" client={c} />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("DIESEL-K5 fuel Finding page", () => {
  it("F6: SUPPORTED shows the claim, the gap, money, margin and why-not lines, the night link and the shared tables", async () => {
    const c = client();
    renderPage(c, siteFuelFindingHref(CODE, FID));
    await screen.findByText(CLAIM);
    await settledScreen();
    expect(c.getFuelFinding).toHaveBeenCalledWith(CODE, FID, null);
    const text = document.body.textContent ?? "";
    for (const line of [GAP, MONEY, MARGIN, NOT_WHY, "Supported by the latest check", "Night of 4 Oct · 6 pm to noon", "07:00, 5 Oct", "Compared with the combined margin; never says why fuel left"]) {
      expect(text).toContain(line);
    }
    expect(screen.getByRole("link", { name: "Open this night on the Fuel page" })).toHaveAttribute("href", `/sites/${CODE}/performance/fuel?night=2026-10-04`);
    expect(Array.from(document.querySelectorAll(".panel h2"), (h) => h.textContent)).toEqual([
      "How the night was checked",
      "Balance bridge",
      "Deliveries and tank dips",
      "Versions",
    ]);
    expect(screen.getByRole("link", { name: "Version 2 · No longer supported · 16:00, 6 Oct" })).toHaveAttribute("href", siteFuelFindingHref(CODE, FID, R2));
    expect(screen.getByRole("navigation", { name: "Site sections" }).querySelector('[aria-current="page"]')?.textContent).toBe("Findings");
  });

  it("F6: NO_LONGER_SUPPORTED shows only the no-longer and why-not lines; ?revision_id= pins the version", async () => {
    const c = client();
    renderPage(c, siteFuelFindingHref(CODE, FID, R2));
    await screen.findByText(NO_LONGER);
    expect(c.getFuelFinding).toHaveBeenCalledWith(CODE, FID, R2);
    const text = document.body.textContent ?? "";
    expect(text).toContain(NOT_WHY);
    expect(text).toContain("No longer supported");
    expect(text).not.toContain(CLAIM);
    expect(text).not.toContain(MONEY);
    cleanup();
    const pinned = client();
    renderPage(pinned, siteFuelFindingHref(CODE, FID, R1));
    await screen.findByText(CLAIM);
    expect(pinned.getFuelFinding).toHaveBeenCalledWith(CODE, FID, R1);
  });

  it("F7: routeFor(FUEL_FINDING) and the linkRefs round-trip", () => {
    expect(routeFor({ kind: "FUEL_FINDING", site: CODE, id: FID })).toBe(`/sites/${CODE}/fuel-findings/${FID}`);
    expect(routeFor({ kind: "FUEL_FINDING", site: CODE, id: FID, revision: R1 })).toBe(siteFuelFindingHref(CODE, FID, R1));
    expect(refOfHref(`/sites/${CODE}/fuel-findings/${FID}`)).toEqual({ kind: "FUEL_FINDING", site: CODE, id: FID });
    expect(refOfHref(`/sites/${CODE}/fuel-findings/${FID}?revision_id=${R1}`)).toEqual({ kind: "FUEL_FINDING", site: CODE, id: FID, revision: R1 });
  });
});

describe("DIESEL-K5 F8: the Site Findings Fuel checks panel", () => {
  const WINDOW = { from: "2026-10-01T00:00:00Z", to: "2026-10-08T00:00:00Z" };

  it("is present with rows, one link each", async () => {
    const c = client([{ finding_id: FID, night_date: "2026-10-04", lifecycle: "SUPPORTED", text: "Unexplained fuel overnight · 4 Oct · about 95.7–144.3 L", href: `/sites/${CODE}/fuel-findings/${FID}` }]);
    render(
      <MemoryRouter>
        <SiteFuelChecks client={c} siteCode={CODE} window={WINDOW} findingHref={(id) => siteFuelFindingHref(CODE, id)} />
      </MemoryRouter>,
    );
    const link = await screen.findByRole("link", { name: "Unexplained fuel overnight · 4 Oct · about 95.7–144.3 L" });
    expect(link).toHaveAttribute("href", `/sites/${CODE}/fuel-findings/${FID}`);
    expect(screen.getByRole("heading", { name: "Fuel checks" })).toBeInTheDocument();
    expect(c.getFuelFindings).toHaveBeenCalledWith(CODE, WINDOW);
  });

  it("is absent with no rows", async () => {
    const c = client([]);
    const { container } = render(
      <MemoryRouter>
        <SiteFuelChecks client={c} siteCode={CODE} window={WINDOW} findingHref={(id) => siteFuelFindingHref(CODE, id)} />
      </MemoryRouter>,
    );
    await vi.waitFor(() => expect(c.getFuelFindings).toHaveBeenCalled());
    await act(() => new Promise((r) => setTimeout(r, 0)));
    expect(container.innerHTML).toBe("");
  });
});
