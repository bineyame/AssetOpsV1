/**
 * W5-02c K4a (`.agent/W5-02c-K4-preflight-rulings.md` rulings 3-10; build spec "Action panels"): the loaded v69
 * `cold-action` panels (`frontend/mockups/v69/index.html:742-746`), the selected Related activity branches, the
 * Inspect and source-Finding controls, the currentness placement and the untitled non-loaded state panel.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteActionFrame } from "../../shell/SiteAnalyticsFrames";
import { expectV69Panels } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import {
  createDomainActionClient,
  type DomainActionClient,
  type DomainActionDetail,
  type DomainDetailResult,
  type DomainStatus,
} from "../domainActionClient";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { COLD_SITE, DOMAIN_ID, FINDING, FINDING_REV, KNOWN, SITE, detailBody } from "./coldWorkFixtures";

const CASE_ID = "c0ffee00-1111-4222-8333-444455556666";
const RECORD_ID = "d00dfeed-1111-4222-8333-444455556666";
const CRITERIA = [
  { key: "AUTOMATIC_START", label: "Automatic start", required_evidence: "Accepted command followed by successful running status" },
  { key: "POWER_DELIVERY", label: "Power delivery", required_evidence: "Generator supply reaches the cooling system" },
  { key: "COOLING_RECOVERY", label: "Cooling recovery", required_evidence: "Temperature recovery within declared test conditions" },
  { key: "RECURRENCE", label: "Recurrence", required_evidence: "Covered observation window without a qualifying repeat" },
];
const RESULTS = ["NOT_TESTED", "NOT_TESTED", "NOT_ESTABLISHED", "PENDING"];
const NO_WORK = { case_id: null, case_code: null, case_title: null, request_state: null, record_id: null, label: null, href: null };
const linkedWork = (request_state: string, record_id: string | null = RECORD_ID) => ({
  case_id: CASE_ID,
  case_code: "WR-000019",
  case_title: "Starter/control inspection",
  request_state,
  record_id,
  label: "Maintenance request WR-000019",
  href: null,
});

/** The positive fixture Action: four declared criteria, initial results and the completed linked WR. */
function positive(over: Partial<DomainActionDetail> = {}): DomainActionDetail {
  const base = detailBody();
  return detailBody({
    intent: { ...(base.intent as NonNullable<DomainActionDetail["intent"]>), criteria: CRITERIA },
    results: CRITERIA.map((c, i) => ({ key: c.key, result: RESULTS[i], evidence_ids: [] })),
    links: { finding: base.links.finding, work: linkedWork("COMPLETED") },
    ...over,
  });
}

function domain(detail: () => DomainDetailResult | Promise<DomainDetailResult>) {
  const calls: { id: string; knownAt: string | null }[] = [];
  const client: DomainActionClient = {
    getIndex: vi.fn(async () => ({ status: "refused" as const, http: 503, code: null, message: "unused" })),
    getDetail: vi.fn(async (_site: string, id: string, knownAt: string | null) => {
      calls.push({ id, knownAt });
      return detail();
    }),
  };
  return { client, calls };
}

const siteDetail = (site: SiteDetailReadModel): SiteDetailClient =>
  ({ getSite: async () => ({ status: "loaded", site }) }) as unknown as SiteDetailClient;

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}

async function mount(detail: () => DomainDetailResult | Promise<DomainDetailResult>, query = "", settle = true) {
  const site: SiteDetailReadModel = COLD_SITE;
  const d = domain(detail);
  render(
    <MemoryRouter initialEntries={[`/sites/${SITE}/actions/${DOMAIN_ID}/verification${query}`]}>
      <Routes>
        <Route
          path="/sites/:siteId/actions/:actionId/:actionView"
          element={<SiteActionFrame detail={siteDetail(site)} sitesPath="/sites" domainActions={d.client} />}
        />
        <Route path="/maintenance/requests/:caseId" element={<Where />} />
      </Routes>
    </MemoryRouter>,
  );
  if (settle) await settledScreen();
  else await waitFor(() => expect(document.querySelector("main[data-domain-action-shell]")).not.toBeNull());
  return { main: document.querySelector("main") as HTMLElement, ...d };
}

const loaded = (value: DomainActionDetail): DomainDetailResult => ({ status: "loaded", value });
const text = (el: Element | null | undefined) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const headings = (main: HTMLElement) => Array.from(main.querySelectorAll("section.panel h2")).map(text);

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("cold-action Declared outcome criteria (ruling 4, build spec Action panels)", () => {
  it("renders the four declared criteria with the stored initial results, in the mock columns", async () => {
    const { main } = await mount(() => loaded(positive()));
    expectV69Panels("cold-action");
    expect(headings(main)).toEqual(["Declared outcome criteria", "Related activity"]);
    const table = main.querySelector("[data-domain-action-criteria] table") as HTMLElement;
    expect(Array.from(table.querySelectorAll("thead th")).map(text)).toEqual(["Criterion", "Required evidence", "Current result"]);
    const rows = Array.from(table.querySelectorAll("tbody tr")).map((tr) => Array.from(tr.querySelectorAll("td")).map(text));
    expect(rows).toEqual([
      ["Automatic start", "Accepted command followed by successful running status", "Not tested"],
      ["Power delivery", "Generator supply reaches the cooling system", "Not tested"],
      ["Cooling recovery", "Temperature recovery within declared test conditions", "Not established"],
      ["Recurrence", "Covered observation window without a qualifying repeat", "Pending"],
    ]);
    // No observed outcome is asserted.
    expect(main.textContent).not.toMatch(/Verified|Restored|Passed|Established\b/);
    const { violations } = scanProductVocabulary(main, "cold-action");
    // As K2 ruling 14: exactly the stored mock criterion text node (`running` status) is set aside, never a subtree.
    const others = violations.filter((v) => !(v.where === "text" && v.text === "Accepted command followed by successful running status"));
    expect(others, describeViolations(others)).toEqual([]);
  });

  it("keeps the criteria heading with the exact missing sentence and no table for a null intent", async () => {
    const { main } = await mount(() => loaded(detailBody({ intent: null, results: null, links: { finding: detailBody().links.finding, work: NO_WORK } })));
    expectV69Panels("cold-action");
    expect(headings(main)).toEqual(["Declared outcome criteria", "Related activity"]);
    expect(text(main.querySelector("[data-domain-action-intent-missing]"))).toBe("No outcome criteria have been declared for this Action.");
    expect(main.querySelector("table")).toBeNull();
    expect(main.textContent).not.toContain("Pending");
    expect(main.textContent).not.toContain("Not tested");
    // No revision without a declared basis.
    expect(main.querySelector("[data-domain-action-revision]")).toBeNull();
  });
});

describe("cold-action Related activity (ruling 5, R100) and controls (ruling 8, R66/R68)", () => {
  it("states the selected completed WR and opens its Overview from Inspect, without known_at when the URL has none", async () => {
    const { main } = await mount(() => loaded(positive()));
    expect(text(main.querySelector("[data-domain-action-related-sentence]"))).toBe(
      "Starter/control inspection WR-000019 is complete. A witnessed outcome test remains required.",
    );
    const inspect = main.querySelector("[data-domain-action-inspect]") as HTMLButtonElement;
    expect(inspect.tagName).toBe("BUTTON");
    expect(inspect.getAttribute("type")).toBe("button");
    expect(inspect.className).toBe("button");
    expect(inspect.disabled).toBe(false);
    expect(text(inspect)).toBe("Inspect maintenance evidence");
    expect(main.querySelector("[data-domain-action-inspect-note]")).toBeNull();
    fireEvent.click(inspect);
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toBe(`/maintenance/requests/${CASE_ID}?site_id=${SITE}`);
  });

  it("carries only an explicit URL cutoff into the Overview address", async () => {
    const { calls } = await mount(() => loaded(positive({ status: "HISTORICAL" })), `?known_at=${encodeURIComponent(KNOWN)}`);
    expect(calls).toEqual([{ id: DOMAIN_ID, knownAt: KNOWN }]);
    fireEvent.click(document.querySelector("[data-domain-action-inspect]") as HTMLElement);
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toBe(
      `/maintenance/requests/${CASE_ID}?site_id=${SITE}&known_at=${encodeURIComponent(KNOWN)}`,
    );
  });

  it("at a cutoff with no linked work says no completed inspection and disables Inspect with the adjacent sentence", async () => {
    const { main } = await mount(() => loaded(positive({ status: "HISTORICAL", links: { finding: detailBody().links.finding, work: NO_WORK } })), `?known_at=${encodeURIComponent(KNOWN)}`);
    expectV69Panels("cold-action");
    expect(text(main.querySelector("[data-domain-action-related-sentence]"))).toBe("No completed inspection is linked to this Action.");
    const inspect = main.querySelector("[data-domain-action-inspect]") as HTMLButtonElement;
    expect(inspect.tagName).toBe("BUTTON");
    expect(inspect.className).toBe("button");
    expect(inspect.disabled).toBe(true);
    const note = main.querySelector("[data-domain-action-inspect-note]") as HTMLElement;
    expect(inspect.getAttribute("aria-describedby")).toBe(note.id);
    expect(text(note)).toBe("Maintenance detail is unavailable for this record.");
    expect(inspect.nextElementSibling).toBe(note);
  });

  it.each(["OPEN", "IN_PROGRESS"])("a selected linked %s request is not a completed inspection; Inspect still opens it", async (state) => {
    const { main } = await mount(() => loaded(positive({ links: { finding: detailBody().links.finding, work: linkedWork(state, null) } })));
    expect(text(main.querySelector("[data-domain-action-related-sentence]"))).toBe("No completed inspection is linked to this Action.");
    const inspect = main.querySelector("[data-domain-action-inspect]") as HTMLButtonElement;
    expect(inspect.disabled).toBe(false);
    expect(inspect.getAttribute("data-domain-action-inspect-target")).toBe(`/maintenance/requests/${CASE_ID}?site_id=${SITE}`);
  });

  it("a COMPLETED request without a performed record is not a completed inspection", async () => {
    const { main } = await mount(() => loaded(positive({ links: { finding: detailBody().links.finding, work: linkedWork("COMPLETED", null) } })));
    expect(text(main.querySelector("[data-domain-action-related-sentence]"))).toBe("No completed inspection is linked to this Action.");
  });

  it("shows `Open source Finding →` as muted noninteractive text followed by its sentence, after Inspect", async () => {
    const { main } = await mount(() => loaded(positive({ links: { finding: { label: `Finding ${FINDING.slice(0, 8)}`, href: `/sites/${SITE}/findings/${FINDING}?revision_id=${FINDING_REV}` }, work: linkedWork("COMPLETED") } })));
    const control = main.querySelector("[data-domain-action-finding-control]") as HTMLElement;
    expect(text(control)).toBe("Open source Finding →");
    expect(control.tagName).toBe("SPAN");
    expect(control.classList.contains("muted")).toBe(true);
    expect(control.hasAttribute("href") || control.hasAttribute("tabindex") || control.closest("a, button") !== null).toBe(false);
    expect(text(control.nextElementSibling)).toBe("The selected Finding revision cannot be opened here yet.");
    const related = main.querySelector("[data-domain-action-related]") as HTMLElement;
    expect(related.querySelectorAll("a")).toHaveLength(0);
    const order = Array.from(related.querySelectorAll("[data-domain-action-inspect], [data-domain-action-finding-control]"));
    expect(order.map((el) => el.hasAttribute("data-domain-action-inspect"))).toEqual([true, false]);
  });
});

describe("cold-action strip, currentness and non-loaded states (rulings 3, 4, 6, 9, 10)", () => {
  it("strip: owner span, derived short Site name, plain Finding label; breadcrumb keeps the full name; no Due date", async () => {
    const { main } = await mount(() => loaded(positive({ action: { ...detailBody().action, due_at: "2026-11-01T00:00:00Z" } })));
    const line = main.querySelector("[data-domain-action-status-line]") as HTMLElement;
    expect(text(line)).toBe(`Maintenance lead · GreenHarvest · Finding ${FINDING.slice(0, 8)}`);
    expect(text(line.querySelector("[data-domain-action-owner]"))).toBe("Maintenance lead");
    expect(text(main.querySelector("[data-domain-action-crumb-site] a"))).toBe("GreenHarvest Cold Room");
    expect(main.textContent).not.toContain("2026-11-01");
    expect(main.textContent).not.toMatch(/\bDue\b/);
  });

  it("keeps a 160-code-point title and owner whole (no clamp or ellipsis)", async () => {
    const title = `Witness ${"t".repeat(152)}`;
    const owner = `Lead ${"y".repeat(155)}`;
    const { main } = await mount(() => loaded(detailBody({ action: { ...detailBody().action, title, owner_label: owner }, intent: null, results: null, links: { finding: detailBody().links.finding, work: NO_WORK } })));
    expect(text(main.querySelector("h1"))).toBe(`ACT-000051 · ${title}`);
    expect(text(main.querySelector("[data-domain-action-owner]"))).toBe(owner);
    expect(main.textContent).not.toContain("…");
  });

  it.each<DomainStatus>(["HISTORICAL", "PENDING_RECOMPUTE", "STALE_SOURCE", "UNKNOWN"])(
    "a loaded %s read puts its notice right after the strip and before Declared outcome criteria",
    async (status) => {
      const { main } = await mount(() => loaded(positive({ status })));
      expectV69Panels("cold-action");
      const strip = main.querySelector("[data-domain-action-strip]") as HTMLElement;
      const notice = main.querySelector(`[data-domain-action-currentness="${status}"]`) as HTMLElement;
      expect(strip.nextElementSibling).toBe(notice);
      expect(text(notice.nextElementSibling?.querySelector("h2"))).toBe("Declared outcome criteria");
    },
  );

  it("a CURRENT read has no leading notice", async () => {
    const { main } = await mount(() => loaded(positive()));
    expect(main.querySelector("[data-domain-action-currentness]")).toBeNull();
    expect(text((main.querySelector("[data-domain-action-strip]") as HTMLElement).nextElementSibling?.querySelector("h2"))).toBe("Declared outcome criteria");
  });

  it("loading shows one untitled state panel and no Related activity heading", async () => {
    const { main } = await mount(() => new Promise<never>(() => undefined), "", false);
    expect(main.querySelectorAll("section.panel")).toHaveLength(1);
    expect(main.querySelector("section.panel h2")).toBeNull();
    expect(text(main.querySelector('[data-domain-action-panel="loading"]'))).toBe("Loading the cold Action declaration.");
    expect(main.textContent).not.toContain("Related activity");
  });

  it("a 404 shows one untitled not-found panel", async () => {
    const { main } = await mount(() => ({ status: "not_found", http: 404, code: "ACTION_NOT_FOUND", message: "Action was not found at this site." }));
    expect(main.querySelectorAll("section.panel")).toHaveLength(1);
    expect(main.querySelector("section.panel h2")).toBeNull();
    expect(text(main.querySelector('[data-domain-action-panel="not-found"]'))).toBe("Action was not found at this site.");
    expect(main.textContent).not.toContain("Declared outcome criteria");
  });

  it.each([
    [403, "SITE_ACCESS_DENIED", "You do not have access to this site's work."],
    [422, "INVALID_KNOWN_AT", "'known_at' must be one UTC instant no later than the read time."],
    [503, "WORK_STORE_UNAVAILABLE", "The work store is unavailable."],
  ])("a %s refusal shows one untitled panel with the server message and Retry", async (http, code, message) => {
    const { main, calls } = await mount(() => ({ status: "refused", http, code, message }));
    expect(main.querySelectorAll("section.panel")).toHaveLength(1);
    expect(main.querySelector("section.panel h2")).toBeNull();
    const panel = main.querySelector('[data-domain-action-panel="refused"]') as HTMLElement;
    expect(panel.getAttribute("data-domain-action-refusal")).toBe(code);
    expect(text(panel)).toContain("Cold work unavailable");
    expect(text(panel.querySelector("[data-domain-action-refusal-message]"))).toBe(message);
    expect(main.textContent).not.toContain("Related activity");
    fireEvent.click(panel.querySelector("[data-domain-action-retry]") as HTMLElement);
    await settledScreen();
    expect(calls).toHaveLength(2);
  });
});

describe("domainActionClient detail results (K4a)", () => {
  const json = (body: unknown) => new Response(JSON.stringify(body), { status: 200 });

  it("loads aligned initial results and refuses misaligned or unknown result values as an unexpected shape", async () => {
    const client = createDomainActionClient();
    vi.stubGlobal("fetch", async () => json(positive()));
    expect((await client.getDetail(SITE, DOMAIN_ID, null)).status).toBe("loaded");
    const bad = [
      positive({ results: positive().results!.slice(0, 3) }),
      positive({ results: [...positive().results!].reverse() }),
      positive({ results: positive().results!.map((r, i) => (i === 0 ? { ...r, result: "VERIFIED" } : r)) }),
    ];
    for (const body of bad) {
      vi.stubGlobal("fetch", async () => json(body));
      const result = await client.getDetail(SITE, DOMAIN_ID, null);
      expect(result.status).toBe("refused");
      expect(result.status === "refused" && result.message).toBe("The cold work read answered in an unexpected shape.");
    }
  });
});
