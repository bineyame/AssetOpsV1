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
import { COLD_ACTION_PRESENTATION } from "../coldWorkPresentation";
import { EV_ACTION_LINK_LIVE, EV_ACTION_PRESENTATION } from "../evWorkPresentation";
import { COLD_SITE, DOMAIN_ID, FINDING, FINDING_REV, KNOWN, SITE, detailBody } from "./coldWorkFixtures";
import { EV_ACTION_ID, EV_FINDING, EV_FINDING_REV, EV_FROM, EV_KNOWN, EV_SITE, EV_SITE_CODE, EV_SITE_NAME, EV_TO } from "./evWorkFixtures";

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

  it.each([
    ["OPEN", "open", "is open"],
    ["IN_PROGRESS", "in-progress", "is in progress"],
  ])("names a selected linked %s request with its actual state (ruling 19, R102); Inspect still opens it", async (state, kind, phrase) => {
    const { main } = await mount(() => loaded(positive({ links: { finding: detailBody().links.finding, work: linkedWork(state, null) } })));
    expect(main.querySelector("[data-domain-action-related]")?.getAttribute("data-domain-action-related")).toBe(kind);
    expect(text(main.querySelector("[data-domain-action-related-sentence]"))).toBe(
      `Starter/control inspection WR-000019 ${phrase}. A witnessed outcome test remains required.`,
    );
    const inspect = main.querySelector("[data-domain-action-inspect]") as HTMLButtonElement;
    expect(inspect.disabled).toBe(false);
    expect(inspect.getAttribute("data-domain-action-inspect-target")).toBe(`/maintenance/requests/${CASE_ID}?site_id=${SITE}`);
  });

  it.each<[string, string | null, string, string]>([
    ["VERIFICATION_WINDOW", RECORD_ID, "verification-window", "Work was recorded; verification is open and no outcome is established."],
    ["VERIFICATION_WINDOW", null, "not-linked", "No completed inspection is linked to this Action."],
    ["CANCELLED", RECORD_ID, "cancelled", "The linked request was cancelled; no completed work or verified outcome is established."],
    ["CANCELLED", null, "cancelled", "The linked request was cancelled; no completed work or verified outcome is established."],
  ])("post-W6 R344: a linked %s request (record %s) reads its exact state, never a verified outcome", async (state, record, kind, sentence) => {
    const { main } = await mount(() => loaded(positive({ links: { finding: detailBody().links.finding, work: linkedWork(state, record) } })));
    expect(main.querySelector("[data-domain-action-related]")?.getAttribute("data-domain-action-related")).toBe(kind);
    expect(text(main.querySelector("[data-domain-action-related-sentence]"))).toBe(sentence);
    expect(text(main.querySelector("[data-domain-action-related]"))).not.toContain("is complete");
  });

  it("post-W6 R344: without a linked case, VERIFICATION_WINDOW and CANCELLED states still read not linked", async () => {
    for (const state of ["VERIFICATION_WINDOW", "CANCELLED"]) {
      const work = { ...NO_WORK, request_state: state, record_id: RECORD_ID };
      const { main } = await mount(() => loaded(positive({ links: { finding: detailBody().links.finding, work } })));
      expect(main.querySelector("[data-domain-action-related]")?.getAttribute("data-domain-action-related")).toBe("not-linked");
      cleanup();
    }
  });

  it("a COMPLETED request without its performed record is not a completed inspection; Inspect stays live (ruling 19)", async () => {
    const { main } = await mount(() => loaded(positive({ links: { finding: detailBody().links.finding, work: linkedWork("COMPLETED", null) } })));
    expect(text(main.querySelector("[data-domain-action-related-sentence]"))).toBe("No completed inspection is linked to this Action.");
    const inspect = main.querySelector("[data-domain-action-inspect]") as HTMLButtonElement;
    expect(inspect.disabled).toBe(false);
    expect(inspect.getAttribute("data-domain-action-inspect-target")).toBe(`/maintenance/requests/${CASE_ID}?site_id=${SITE}`);
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

  // post-W6 W5-cold B15-04 (cites R322; W4 Q10, W5 rulings 2): the cold refusal reads its exact code's sentence, never
  // the raw server message, cutoff or Site code; Retry only for 503 and an unreached server; one alert.
  it.each<[number | null, string | null, string, string, boolean]>([
    [422, "INVALID_KNOWN_AT", "'known_at' must be one UTC instant no later than the read time. 2099-01-01T00:00:00Z", "Choose a valid evidence cutoff.", false],
    [403, "SITE_SCOPE_FORBIDDEN", "No access to Site 'COLD-001'.", "You do not have access to this site.", false],
    [503, "WORK_STORE_UNAVAILABLE", "The work store is unavailable.", "Cold work is unavailable right now. Try again.", true],
    [409, "SOMETHING_NEW", "Raw server text COLD-001.", "The attempt was refused.", false],
    [null, null, "The cold work read could not be reached.", "The cold work read could not be reached.", true],
    [503, null, "The cold work read answered in an unexpected shape.", "The cold work read answered in an unexpected shape.", true],
    [500, null, "The cold work read answered in an unexpected shape.", "The cold work read answered in an unexpected shape.", false],
  ])("a %s %s refusal shows one untitled alert panel with the exact-code sentence", async (http, code, message, sentence, retry) => {
    const { main, calls } = await mount(() => ({ status: "refused", http, code, message }));
    expect(main.querySelectorAll("section.panel")).toHaveLength(1);
    expect(main.querySelector("section.panel h2")).toBeNull();
    const panel = main.querySelector('[data-domain-action-panel="refused"]') as HTMLElement;
    expect(panel.getAttribute("data-domain-action-refusal")).toBe(code ?? (http === null ? "UNREACHABLE" : "UNEXPECTED"));
    expect(panel.getAttribute("role")).toBe("alert");
    expect(main.querySelectorAll('[role="alert"]')).toHaveLength(1);
    expect(text(panel)).toContain("Cold work unavailable");
    expect(text(panel.querySelector("[data-domain-action-refusal-message]"))).toBe(sentence);
    expect(text(panel)).not.toContain("COLD-001");
    expect(text(panel)).not.toContain("2099-01-01");
    expect(main.textContent).not.toContain("Related activity");
    const button = panel.querySelector("[data-domain-action-retry]") as HTMLElement | null;
    if (!retry) {
      expect(button).toBeNull();
      expect(panel.querySelector("button")).toBeNull();
      return;
    }
    fireEvent.click(button as HTMLElement);
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

/* ---------- W5-04 V4a: the EV_CHARGING Action detail (v69 `ev-action`, `index.html:710-713`) ---------- */

describe("cold presentation stays the K4 presentation (rulings 41, 47, 53)", () => {
  it("keeps every cold literal, the Finding status tail, the disclosure and the Related panel byte-for-byte", () => {
    expect(COLD_ACTION_PRESENTATION).toMatchObject({
      subtitle: "Has backup service been restored after the inspection?",
      stateOpen: "Open",
      ownerMissing: "Not assigned",
      revisionDisclosure: true,
      loading: "Loading the cold Action declaration.",
      notFound: "Action was not found at this site.",
      unavailable: "Cold work unavailable",
      retry: "Retry",
      closingNotice: "Completed inspection does not establish successful service restoration.",
      windowQuery: false,
      panel: {
        criteriaTitle: "Declared outcome criteria",
        columns: ["Criterion", "Required evidence", "Current result"],
        intentMissing: "No outcome criteria have been declared for this Action.",
        resultLabels: { NOT_TESTED: "Not tested", NOT_ESTABLISHED: "Not established", PENDING: "Pending" },
        related: true,
      },
    });
    expect(COLD_ACTION_PRESENTATION.statusTail({ siteName: "GreenHarvest Cold Store", siteShort: "GreenHarvest", finding: "Finding abcdef12" })).toBe(
      "GreenHarvest · Finding abcdef12",
    );
    expect(COLD_ACTION_PRESENTATION.statusTail({ siteName: "Store", siteShort: "", finding: "Finding abcdef12" })).toBe("Store · Finding abcdef12");
  });
});

const EV_CRITERIA = [
  { key: "WITNESSED_SESSION", label: "Complete a witnessed charging session", required_evidence: "Session start, end, outcome and meter delta" },
  { key: "NO_FAULT_RECURRENCE", label: "No fault recurrence during observation", required_evidence: "Connector diagnostic events with full coverage" },
  { key: "NO_SERVICE_REDUCTION", label: "No reduction in service availability", required_evidence: "Comparable status coverage / operational window" },
];

/** The as-built EV detail wire (`work/domain_action_index.py` `_ev_detail`): three EV criteria, three `PENDING`. */
function evDetail(over: Partial<DomainActionDetail> = {}): DomainActionDetail {
  return {
    schema_version: "domain-action-intent-read-1",
    site_code: EV_SITE_CODE,
    action: {
      id: EV_ACTION_ID,
      action_code: "ACT-000061",
      domain: "EV_CHARGING",
      title: "Investigate connector 2",
      owner_label: "Charging operations",
      due_at: null,
      raised_at: "2026-10-06T09:10:00Z",
      recorded_at: "2026-10-06T09:10:01Z",
      state: "OPEN",
    },
    known_at: EV_KNOWN,
    status: "CURRENT",
    intent: {
      id: "bbbb0000-0000-4000-8000-000000000001",
      recorded_at: "2026-10-06T09:11:00Z",
      criteria: EV_CRITERIA,
      basis: { finding_revision_id: EV_FINDING_REV, work_case_id: null, work_record_id: null, accepted_evidence_ids: [], session_ids: [] },
    },
    results: EV_CRITERIA.map((c) => ({ key: c.key, result: "PENDING", evidence_ids: [] })),
    links: { finding: { label: `Finding ${EV_FINDING.slice(0, 8)}`, href: null }, work: NO_WORK },
    source_provenance: null,
    selection_token: "sha256:ev",
    ...over,
  };
}

const evMissingIntent = (over: Partial<DomainActionDetail> = {}) => evDetail({ intent: null, results: null, status: "UNKNOWN", ...over });

async function mountEv(detail: () => DomainDetailResult | Promise<DomainDetailResult>, path = "/verification", settle = true) {
  const d = domain(detail);
  render(
    <MemoryRouter initialEntries={[`/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}${path}`]}>
      <Routes>
        <Route
          path="/sites/:siteId/actions/:actionId/:actionView"
          element={<SiteActionFrame detail={siteDetail(EV_SITE as SiteDetailReadModel)} sitesPath="/sites" domainActions={d.client} />}
        />
        <Route
          path="/sites/:siteId/actions/:actionId"
          element={<SiteActionFrame detail={siteDetail(EV_SITE as SiteDetailReadModel)} sitesPath="/sites" domainActions={d.client} />}
        />
      </Routes>
      <Where />
    </MemoryRouter>,
  );
  if (settle) await settledScreen();
  else await waitFor(() => expect(document.querySelector("main[data-domain-action-shell]")).not.toBeNull());
  return { main: document.querySelector("main") as HTMLElement, ...d };
}

describe("ev-action loaded page (rulings 15, 41, 43; pre-flight 44-46)", () => {
  it("renders the mock frame, the full Site name status and the sole Declared verification plan with three plain Pending results", async () => {
    const { main, client } = await mountEv(() => loaded(evDetail()));
    expectV69Panels("ev-action");
    // Mock breadcrumb `Actions › {code} › Verification · site: {site}`, heading, question subtitle and Open site.
    expect(Array.from(main.querySelectorAll("[data-domain-action-crumbs] li")).map(text)).toEqual(["Actions", "ACT-000061", "Verification"]);
    expect(main.querySelector("[data-domain-action-crumbs] a")?.getAttribute("href")).toBe("/actions");
    expect(text(main.querySelector("[data-domain-action-crumb-site]"))).toBe(`· site: ${EV_SITE_NAME}`);
    expect(text(main.querySelector("h1"))).toBe("ACT-000061 · Investigate connector 2");
    expect(main.textContent).toContain("What would establish successful service restoration?");
    expect(main.querySelector("[data-domain-action-open-site]")?.getAttribute("href")).toBe(`/sites/${EV_SITE_CODE}`);
    // One Verification tab only.
    expect(Array.from(main.querySelectorAll("[data-action-section]")).map(text)).toEqual(["Verification"]);
    // Pre-flight 44/45, ruling 41: amber `Open`, `{owner} · {full Site display_name}`, no Finding or Finding version.
    const strip = main.querySelector("[data-domain-action-strip]") as HTMLElement;
    expect(strip.querySelector(".w1f4-action-badge--amber")?.textContent).toBe("Open");
    expect(text(strip.querySelector("[data-domain-action-status-line]"))).toBe(`Charging operations · ${EV_SITE_NAME}`);
    expect(strip.textContent).not.toContain("Finding");
    expect(strip.querySelector("[data-domain-action-revision]")).toBeNull();
    expect(main.textContent).not.toContain("Depot");
    // The sole mock panel.
    expect(headings(main)).toEqual(["Declared verification plan"]);
    const table = main.querySelector("[data-domain-action-criteria] table") as HTMLElement;
    expect(Array.from(table.querySelectorAll("thead th")).map(text)).toEqual(["Criterion", "Required evidence", "Current result"]);
    const rows = Array.from(table.querySelectorAll("tbody tr")).map((tr) => Array.from(tr.querySelectorAll("td")).map(text));
    expect(rows).toEqual([
      ["Complete a witnessed charging session", "Session start, end, outcome and meter delta", "Pending"],
      ["No fault recurrence during observation", "Connector diagnostic events with full coverage", "Pending"],
      ["No reduction in service availability", "Comparable status coverage / operational window", "Pending"],
    ]);
    // Plain text, never a chip or badge.
    for (const cell of Array.from(table.querySelectorAll("[data-domain-action-result]"))) {
      expect(cell.children).toHaveLength(0);
    }
    // Pre-flight 46: no Related activity, Inspect, disabled maintenance button or source-Finding control.
    expect(main.textContent).not.toContain("Related activity");
    expect(main.querySelector("button[disabled]")).toBeNull();
    expect(main.querySelector("[data-domain-action-inspect], [data-domain-action-finding-control]")).toBeNull();
    expect(main.textContent).not.toMatch(/Verified|Restored|Passed|Established\b/);
    const notice = main.querySelector("[data-domain-action-notice]") as HTMLElement;
    expect(text(notice)).toBe("A completed investigation or diagnostic reset would not establish a verified outcome.");
    expect(notice.classList.contains("v69-notice--blue")).toBe(true);
    const { violations } = scanProductVocabulary(main, "ev-action");
    expect(violations, describeViolations(violations)).toEqual([]);
    // Ruling 64: the EV Site passes its Site type for the EV fallback copy.
    expect(client.getDetail).toHaveBeenCalledWith(EV_SITE_CODE, EV_ACTION_ID, null, "EV_CHARGING");
  });

  it("shows `Not assigned` for a null owner and keeps a 160-code-point title and owner whole (R109)", async () => {
    const title = "T".repeat(160);
    const owner = "O".repeat(160);
    const { main } = await mountEv(() => loaded(evDetail({ action: { ...evDetail().action, owner_label: null } })));
    expect(text(main.querySelector("[data-domain-action-owner]"))).toBe("Not assigned");
    cleanup();
    const long = await mountEv(() => loaded(evDetail({ action: { ...evDetail().action, title, owner_label: owner } })));
    expect(text(long.main.querySelector("h1"))).toBe(`ACT-000061 · ${title}`);
    expect(text(long.main.querySelector("[data-domain-action-owner]"))).toBe(owner);
    expect(long.main.querySelector("[data-domain-action-owner]")?.className).toBe("domain-action-owner");
  });

  it("a 200 missing intent keeps UNKNOWN currentness above the plan heading with the exact no-criteria sentence (ruling 40)", async () => {
    const { main } = await mountEv(() => loaded(evMissingIntent()));
    expectV69Panels("ev-action");
    expect(headings(main)).toEqual(["Declared verification plan"]);
    expect(text(main.querySelector("[data-domain-action-intent-missing]"))).toBe("No verification criteria have been declared for this Action.");
    expect(main.querySelector("[data-domain-action-criteria]")).toBeNull();
    expect(main.textContent).not.toContain("Pending");
    const strip = main.querySelector("[data-domain-action-strip]") as HTMLElement;
    const notice = main.querySelector('[data-domain-action-currentness="UNKNOWN"]') as HTMLElement;
    expect(strip.nextElementSibling).toBe(notice);
    expect(text(notice)).toBe("No selected source for linked evidence. The work record remains recorded.");
    expect(text(notice.nextElementSibling?.querySelector("h2"))).toBe("Declared verification plan");
  });

  it.each<[DomainStatus, string, "blue" | "amber"]>([
    ["HISTORICAL", "Read as of 2026-10-06 12:00 UTC. Later work may differ.", "blue"],
    ["PENDING_RECOMPUTE", "Linked evidence is being reassessed. The work record remains recorded.", "amber"],
    ["STALE_SOURCE", "Linked evidence source is out of date. The work record remains recorded.", "amber"],
    ["UNKNOWN", "No selected source for linked evidence. The work record remains recorded.", "blue"],
  ])("a loaded %s read puts its R80 notice after the strip and before the plan with the R104 tone", async (status, sentence, tone) => {
    const { main } = await mountEv(() => loaded(evDetail({ status })));
    expectV69Panels("ev-action");
    const strip = main.querySelector("[data-domain-action-strip]") as HTMLElement;
    const notice = main.querySelector(`[data-domain-action-currentness="${status}"]`) as HTMLElement;
    expect(strip.nextElementSibling).toBe(notice);
    expect(text(notice)).toBe(sentence);
    // Amber is the base notice; blue adds its modifier.
    expect(notice.classList.contains("v69-notice--blue")).toBe(tone === "blue");
    expect(text(notice.nextElementSibling?.querySelector("h2"))).toBe("Declared verification plan");
  });

  it("a CURRENT read has no leading notice", async () => {
    const { main } = await mountEv(() => loaded(evDetail()));
    expect(main.querySelector("[data-domain-action-currentness]")).toBeNull();
  });
});

describe("ev-action query selection (ruling 14) and route dispatch (ruling 43)", () => {
  const query = `?from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}&known_at=${encodeURIComponent(EV_KNOWN)}`;
  const expected = `from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}&known_at=${encodeURIComponent(EV_KNOWN)}`;

  it("keeps the selected from,to,known_at on the Verification tab, reads at known_at, and has no Window control", async () => {
    const { main, calls } = await mountEv(() => loaded(evDetail({ status: "HISTORICAL" })), `/verification${query}`);
    expect(calls).toEqual([{ id: EV_ACTION_ID, knownAt: EV_KNOWN }]);
    expect(main.querySelector('[data-action-section="verification"]')?.getAttribute("href")).toBe(
      `/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification?${expected}`,
    );
    expect(main.querySelector("form, input")).toBeNull();
    expect(main.textContent).not.toContain("From (UTC)");
  });

  it.each([""])("redirects a loaded EV domain Action at `%s` to /verification with the same query", async (path) => {
    const { calls } = await mountEv(() => loaded(evDetail({ status: "HISTORICAL" })), `${path}${query}`);
    await waitFor(() => expect(text(screen.getByTestId("where"))).toBe(`/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification?${expected}`));
    await settledScreen();
    expect(document.querySelector("main")?.getAttribute("data-domain-action-shell")).toBe("loaded");
    expect(calls.every((c) => c.knownAt === EV_KNOWN)).toBe(true);
  });

  it("EV_ACTION_LINK_LIVE is on and only EV keeps the window query (R113 closed)", () => {
    expect(EV_ACTION_LINK_LIVE).toBe(true);
    expect(EV_ACTION_PRESENTATION.windowQuery).toBe(true);
    expect(COLD_ACTION_PRESENTATION.windowQuery).toBe(false);
  });
});

describe("ev-action non-loaded states: one untitled panel (rulings 16, 40, 42; R110)", () => {
  it("loading shows one untitled state panel with the EV loading sentence", async () => {
    const { main } = await mountEv(() => new Promise<never>(() => undefined), "/verification", false);
    expect(main.querySelectorAll("section.panel")).toHaveLength(1);
    expect(main.querySelector("section.panel h2")).toBeNull();
    expect(text(main.querySelector('[data-domain-action-panel="loading"]'))).toBe("Loading the EV Action declaration.");
    expect(main.textContent).not.toContain("Declared verification plan");
  });

  it("a 404 shows one untitled not-found panel", async () => {
    const { main } = await mountEv(() => ({ status: "not_found", http: 404, code: "ACTION_NOT_FOUND", message: "Action was not found at this site." }));
    expect(main.querySelectorAll("section.panel")).toHaveLength(1);
    expect(main.querySelector("section.panel h2")).toBeNull();
    expect(text(main.querySelector('[data-domain-action-panel="not-found"]'))).toBe("Action was not found at this site.");
    expect(main.querySelector("[data-domain-action-strip]")).toBeNull();
  });

  it.each([
    [409, "DOMAIN_INTENT_BASIS_CHANGED", "The Action changed while it was being read.", "Reload"],
    [403, "SITE_ACCESS_DENIED", "You do not have access to this site.", null],
    [422, "INVALID_KNOWN_AT", "Choose a valid evidence cutoff.", null],
    [503, "WORK_STORE_UNAVAILABLE", "EV work is unavailable right now. Try again.", "Reload"],
    [500, "SOMETHING_ELSE", "The Action could not be read.", null],
  ])("R349: a %s refusal is mapped by code and status, never the server text, with Reload only where it can help", async (http, code, sentence, action) => {
    const { main, calls } = await mountEv(() => ({ status: "refused", http, code, message: "raw server text 2026-10-06T12:00:00Z" }));
    expect(main.querySelectorAll("section.panel")).toHaveLength(1);
    expect(main.querySelector("section.panel h2")).toBeNull();
    expect(text(main.querySelector("h1"))).toBe("Action unavailable");
    const panel = main.querySelector('[data-domain-action-panel="refused"]') as HTMLElement;
    expect(panel.getAttribute("data-domain-action-refusal")).toBe(code);
    expect(panel.getAttribute("role")).toBe("alert");
    expect(main.querySelectorAll("[role='alert']")).toHaveLength(1);
    expect(text(panel.querySelector("[data-domain-action-refusal-message]"))).toBe(sentence);
    expect(main.textContent).not.toContain("raw server text");
    // The code and status live only in the labelled technical disclosure.
    const detail = panel.querySelector('[data-disclosure="domain-action-technical-detail"]') as HTMLElement;
    expect(text(detail.querySelector("summary"))).toBe("Technical detail");
    expect(text(detail.querySelector("[data-domain-action-technical]"))).toBe(`Status ${http} · code ${code}`);
    expect(panel.querySelector("p:not([data-domain-action-technical]):not([data-domain-action-refusal-message])")?.textContent ?? "").not.toContain(code);
    expect(main.textContent).not.toContain("Cold work unavailable");
    expect(main.querySelector("[data-domain-action-notice]")).toBeNull();
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
    if (action === null) {
      expect(screen.queryByRole("button", { name: "Reload" })).toBeNull();
    } else {
      fireEvent.click(screen.getByRole("button", { name: "Reload" }));
      await settledScreen();
      expect(calls).toHaveLength(2);
    }
  });

  it("R349: the h1 is `Loading Action…` while reading and `Action not found` for a 404", async () => {
    const loading = await mountEv(() => new Promise<never>(() => undefined), "/verification", false);
    expect(text(loading.main.querySelector("h1"))).toBe("Loading Action…");
    cleanup();
    const missing = await mountEv(() => ({ status: "not_found", http: 404, code: "ACTION_NOT_FOUND", message: "x" }));
    expect(text(missing.main.querySelector("h1"))).toBe("Action not found");
    expect(missing.main.querySelector("[data-domain-action-retry]")).toBeNull();
  });

  it("R349: an unreached server reads as unavailable and reloads", async () => {
    const { main } = await mountEv(() => ({ status: "refused", http: null, code: null, message: "The EV work read could not be reached." }));
    expect(text(main.querySelector("[data-domain-action-refusal-message]"))).toBe("EV work is unavailable right now. Try again.");
    expect(screen.getByRole("button", { name: "Reload" })).toBeTruthy();
  });
});

describe("ev-action window (R348)", () => {
  const q = (from: string | null, to: string | null, extra = `&known_at=${encodeURIComponent(EV_KNOWN)}`) =>
    `?${[from === null ? "" : `from=${encodeURIComponent(from)}`, to === null ? "" : `to=${encodeURIComponent(to)}`].filter(Boolean).join("&")}${extra}`;
  const SAME = "The selected window needs both a start and an end, with the start before the end.";

  it.each([
    ["one-sided", q(EV_FROM, null), SAME],
    ["reversed", q(EV_TO, EV_FROM), SAME],
    ["32 days", q("2026-09-01T00:00:00Z", "2026-10-03T00:00:00Z"), "The selected window is longer than 31 days."],
    ["non-UTC", q("2026-10-06T08:00:00+03:00", "2026-10-06T09:00:00+03:00"), SAME],
  ])("a %s window is refused before any read and carried by no link", async (_name, query, sentence) => {
    const { main, calls } = await mountEv(() => loaded(evDetail()), `/verification${query}`);
    expect(calls).toEqual([]);
    const panel = main.querySelector('[data-domain-action-panel="window-invalid"]') as HTMLElement;
    expect(panel.getAttribute("role")).toBe("alert");
    expect(text(panel.querySelector("strong"))).toBe("Window cannot be read");
    expect(text(panel.querySelector("[data-domain-action-refusal-message]"))).toBe(sentence);
    expect(text(main.querySelector("h1"))).toBe("Action unavailable");
    expect(screen.queryByRole("button", { name: /Retry|Reload/ })).toBeNull();
    // The one correction opens the Action without the window and keeps the valid cutoff.
    const without = `/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification?known_at=${encodeURIComponent(EV_KNOWN)}`;
    expect(main.querySelector("[data-domain-action-without-window]")?.getAttribute("href")).toBe(without);
    expect(text(main.querySelector("[data-domain-action-without-window]"))).toBe("Open this Action without a window");
    expect(main.querySelector('[data-action-section="verification"]')?.getAttribute("href")).toBe(without);
    for (const a of Array.from(main.querySelectorAll("a"))) expect(a.getAttribute("href") ?? "").not.toContain("from=");
  });

  it("a valid window is carried unchanged and a bare address (no window) reads normally", async () => {
    const ok = `?from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}&known_at=${encodeURIComponent(EV_KNOWN)}`;
    const { main, calls } = await mountEv(() => loaded(evDetail()), `/verification${ok}`);
    expect(calls).toHaveLength(1);
    expect(main.querySelector('[data-domain-action-panel="window-invalid"]')).toBeNull();
    expect(main.querySelector('[data-action-section="verification"]')?.getAttribute("href")).toContain(`from=${encodeURIComponent(EV_FROM)}`);
    cleanup();
    const bare = await mountEv(() => loaded(evDetail()), "/verification");
    expect(bare.calls).toHaveLength(1);
  });

  it("cold ignores the window entirely: no refusal, the read is made and the tab carries only known_at", async () => {
    const { main, calls } = await mount(() => loaded(positive()), `?from=${encodeURIComponent(EV_TO)}&to=${encodeURIComponent(EV_FROM)}&known_at=${encodeURIComponent(EV_KNOWN)}`);
    expect(calls).toHaveLength(1);
    expect(main.querySelector('[data-domain-action-panel="window-invalid"]')).toBeNull();
    expect(main.querySelector('[data-action-section="verification"]')?.getAttribute("href")).not.toContain("from=");
  });
});

describe("Action section addresses (R350, cold and EV)", () => {
  it.each(["plan", "execution", "evidence", "history"])("EV `/%s` is the shelled not-served state: no read, no redirect, valid params kept", async (section) => {
    const query = `?from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}&known_at=${encodeURIComponent(EV_KNOWN)}`;
    const { main, calls } = await mountEv(() => loaded(evDetail()), `/${section}${query}`);
    expect(calls).toEqual([]);
    expect(text(screen.getByTestId("where"))).toBe(`/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/${section}${query}`);
    expect(text(main.querySelector("h1"))).toBe("Page not available");
    expect(text(main.querySelector("section.panel h2"))).toBe("This address is not served");
    const link = main.querySelector("[data-action-open-verification]") as HTMLElement;
    expect(text(link)).toBe("Open this Action's verification");
    expect(link.getAttribute("href")).toBe(`/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification?from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}&known_at=${encodeURIComponent(EV_KNOWN)}`);
  });

  it("drops an invalid window and an invalid cutoff from the link", async () => {
    const { main } = await mountEv(() => loaded(evDetail()), `/history?from=${encodeURIComponent(EV_TO)}&to=${encodeURIComponent(EV_FROM)}&known_at=yesterday`);
    expect(main.querySelector("[data-action-open-verification]")?.getAttribute("href")).toBe(`/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification`);
  });

  it("the bare route still redirects (R222 alias) and /verification still reads", async () => {
    const { calls } = await mountEv(() => loaded(evDetail()), "");
    await waitFor(() => expect(text(screen.getByTestId("where"))).toBe(`/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification`));
    expect(calls.length).toBeGreaterThan(0);
  });

  it.each(["plan", "history"])("cold `/%s` is the same not-served state with only a valid known_at kept", async (section) => {
    const d = domain(() => loaded(positive()));
    render(
      <MemoryRouter initialEntries={[`/sites/${SITE}/actions/${DOMAIN_ID}/${section}?known_at=${encodeURIComponent(EV_KNOWN)}&from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}`]}>
        <Routes>
          <Route path="/sites/:siteId/actions/:actionId/:actionView" element={<SiteActionFrame detail={siteDetail(COLD_SITE)} sitesPath="/sites" domainActions={d.client} />} />
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
    expect(d.calls).toEqual([]);
    const main = document.querySelector("main") as HTMLElement;
    expect(text(main.querySelector("h1"))).toBe("Page not available");
    expect(text(main.querySelector("section.panel h2"))).toBe("This address is not served");
    expect(main.querySelector("[data-action-open-verification]")?.getAttribute("href")).toBe(`/sites/${SITE}/actions/${DOMAIN_ID}/verification?known_at=${encodeURIComponent(EV_KNOWN)}`);
  });
});

describe("domainActionClient EV detail (rulings 43, 44, 64)", () => {
  const json = (status: number, body: unknown) => new Response(JSON.stringify(body), { status });

  it("parses the EV detail as a domain Action and refuses an EV result other than PENDING", async () => {
    const client = createDomainActionClient();
    vi.stubGlobal("fetch", async () => json(200, evDetail()));
    const ok = await client.getDetail(EV_SITE_CODE, EV_ACTION_ID, null, "EV_CHARGING");
    expect(ok.status === "loaded" && ok.value.action.domain).toBe("EV_CHARGING");
    vi.stubGlobal("fetch", async () => json(200, evMissingIntent()));
    expect((await client.getDetail(EV_SITE_CODE, EV_ACTION_ID, null, "EV_CHARGING")).status).toBe("loaded");
    for (const body of [
      evDetail({ results: evDetail().results!.map((r, i) => (i === 0 ? { ...r, result: "NOT_TESTED" } : r)) }),
      evDetail({ results: evDetail().results!.slice(0, 2) }),
      evDetail({ action: { ...evDetail().action, domain: "MINIGRID" as never } }),
    ]) {
      vi.stubGlobal("fetch", async () => json(200, body));
      expect(await client.getDetail(EV_SITE_CODE, EV_ACTION_ID, null, "EV_CHARGING")).toEqual({
        status: "refused",
        http: 200,
        code: null,
        message: "The EV work read answered in an unexpected shape.",
      });
    }
  });

  it("uses the EV network and malformed sentences for an EV Site and keeps the cold sentences byte-for-byte otherwise", async () => {
    const client = createDomainActionClient();
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("network");
    });
    expect(await client.getDetail(EV_SITE_CODE, EV_ACTION_ID, null, "EV_CHARGING")).toEqual({
      status: "refused",
      http: null,
      code: null,
      message: "The EV work read could not be reached.",
    });
    expect(await client.getDetail(SITE, DOMAIN_ID, null)).toMatchObject({ message: "The cold work read could not be reached." });
    vi.stubGlobal("fetch", async () => json(503, { nothing: true }));
    expect(await client.getDetail(EV_SITE_CODE, EV_ACTION_ID, null, "EV_CHARGING")).toMatchObject({ http: 503, message: "The EV work read answered in an unexpected shape." });
    expect(await client.getDetail(SITE, DOMAIN_ID, null)).toMatchObject({ http: 503, message: "The cold work read answered in an unexpected shape." });
    vi.stubGlobal("fetch", async () =>
      json(409, { detail: { code: "DOMAIN_INTENT_BASIS_CHANGED", message: "The selected EV work basis changed; reload the Action.", intent: null, results: null } }),
    );
    expect(await client.getDetail(EV_SITE_CODE, EV_ACTION_ID, null, "EV_CHARGING")).toEqual({
      status: "refused",
      http: 409,
      code: "DOMAIN_INTENT_BASIS_CHANGED",
      message: "The selected EV work basis changed; reload the Action.",
    });
  });

  it("the network failure reaches the page as the EV refusal panel", async () => {
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("network");
    });
    render(
      <MemoryRouter initialEntries={[`/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification`]}>
        <Routes>
          <Route
            path="/sites/:siteId/actions/:actionId/:actionView"
            element={<SiteActionFrame detail={siteDetail(EV_SITE as SiteDetailReadModel)} sitesPath="/sites" domainActions={createDomainActionClient()} />}
          />
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
    const panel = document.querySelector('[data-domain-action-panel="refused"]') as HTMLElement;
    expect(panel.getAttribute("data-domain-action-refusal")).toBe("UNREACHABLE");
    expect(text(panel.querySelector("[data-domain-action-refusal-message]"))).toBe("EV work is unavailable right now. Try again.");
    expect(screen.getByRole("button", { name: "Reload" })).toBeTruthy();
  });
});
