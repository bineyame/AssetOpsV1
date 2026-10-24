/**
 * W5-02 K3a (`.agent/W5-02-build-spec.md` "K3a and K3b: cases", K3 pre-flight rulings 1-6, M5 withdrawal; K2
 * rulings 4, 5, 12, 21, 23): the COLDCHAIN Site > Work > Incidents and Maintenance tabs over the W4 Site work list
 * (`site-work-index-1`), against the v69 `cold-work-incidents` / `cold-work-maintenance` mock
 * (`frontend/mockups/v69/index.html:333-342`). The wire rows carry exactly the W4 row keys; IDs are test constants.
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteWorkCasesFrame } from "../../shell/SiteAnalyticsFrames";
import { expectV69Panels, leadingIntruders } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import type { DomainActionClient } from "../domainActionClient";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import {
  WORK_CONTEXT_NOTICE,
  WORK_CONTEXT_NOTICE_DOMAIN,
  WORK_STRIP_DETAIL,
  WORK_STRIP_DETAIL_DOMAIN,
  coldAssetLabel,
  coldRequestHref,
  eatWindowText,
  siteWindowText,
} from "../siteWorkCases";
import type { WorkClient, WorkIndexBody, WorkIndexResult, WorkKind, WorkRow, WorkScope } from "../workClient";
import { COLD_SITE, FROM, KNOWN, SITE, TO, indexBody } from "./coldWorkFixtures";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

const F1 = "c0ffee01-1111-4111-8111-111111111111";
const F1_REV = "c0ffee01-2222-4222-8222-222222222222";
const F2 = "beef0002-3333-4333-8333-333333333333";
const F2_REV = "beef0002-4444-4444-8444-444444444444";
const GEN = "9e9e9e9e-5555-4555-8555-555555555555";
const PROVENANCE = {
  classification: "UNKNOWN",
  state: "UNKNOWN",
  source_ids: [],
  evidence_ids: [],
  basis_sha256: null,
  reasons: [{ code: "EMPTY_CITATION_SET", accepted_evidence_ids: [] }],
};
const BANNER = "Cold-room operating capabilities and consequence vocabulary within the stable Site shell.";

function incident(n: number, over: Partial<WorkRow> = {}): WorkRow {
  const id = `10000000-0000-4000-8000-${String(100 + n).padStart(12, "0")}`;
  return {
    case_id: id,
    revision_id: id.replace("10000000", "20000000"),
    code: `INC-${String(n).padStart(6, "0")}`,
    title: "Backup response failure",
    narrative: "Grid lost, automatic start failed, chamber above policy",
    occurred_at: "2026-10-06T16:11:00.000000Z",
    recorded_at: "2026-10-06T16:12:00.000000Z",
    state: "OPEN",
    asset_id: null,
    asset_label: null,
    finding_links: [
      { finding_id: F1, finding_revision_id: F1_REV, label: "Finding", href: `/sites/${SITE}/findings/${F1}?revision_id=${F1_REV}` },
      { finding_id: F2, finding_revision_id: F2_REV, label: "Finding", href: `/sites/${SITE}/findings/${F2}?revision_id=${F2_REV}` },
    ],
    action_links: [],
    url: null,
    source_provenance: PROVENANCE,
    ...over,
  };
}

function request(n: number, over: Partial<WorkRow> = {}): WorkRow {
  return {
    ...incident(n),
    code: `WR-${String(n).padStart(6, "0")}`,
    title: "Starter/control inspection",
    narrative: "Inspect the starter and control circuit.",
    occurred_at: "2026-10-06T16:20:00.000000Z",
    finding_links: [],
    asset_id: GEN,
    asset_label: "generator-1 · GENERATOR",
    request_state: "COMPLETED",
    state: "COMPLETED",
    incident_id: null,
    record_id: "30000000-0000-4000-8000-000000000301",
    activity: "Starter and control inspection",
    outcome_note: "Inspection complete; witnessed automatic-start test remains required",
    outcome_state: "UNVERIFIED",
    next_evidence: null,
    next_evidence_copy: "No next evidence recorded",
    ...over,
  };
}

function body(rows: WorkRow[], over: Partial<WorkIndexBody> = {}): WorkIndexBody {
  return {
    schema_version: "site-work-index-1",
    site_code: SITE,
    site_name: "GreenHarvest Cold Room",
    window: { from: FROM, to: TO, bounds: "[from, to)" },
    known_at: KNOWN,
    status: "CURRENT",
    coverage: { state: "COMPLETE", reason: null },
    source_provenance: PROVENANCE,
    total_count: rows.length,
    rows,
    next_cursor: null,
    selection_token: `sha256:${"0".repeat(64)}`,
    ...over,
  };
}

const domainActions: DomainActionClient = {
  getIndex: vi.fn(async () => ({ status: "loaded" as const, value: indexBody([]) })),
  getDetail: vi.fn(async () => ({ status: "unavailable" as const, code: null, message: null, http: 503 })),
} as unknown as DomainActionClient;

function siteDetail(site: SiteDetailReadModel): SiteDetailClient {
  return { getSite: async () => ({ status: "loaded", site }) } as unknown as SiteDetailClient;
}

/** Page reads (no `limit`) answer `page`; the subtab counts (`limit=1`) answer an empty list. */
function workClient(page: WorkIndexResult) {
  const calls: { kind: WorkKind; scope: WorkScope }[] = [];
  const client: WorkClient = {
    getWorkIndex: vi.fn(async (_site: string, kind: WorkKind, scope: WorkScope) => {
      calls.push({ kind, scope });
      return scope.limit === 1 ? { status: "loaded" as const, value: body([]) } : page;
    }),
  };
  return { client, calls };
}

const query = (knownAt: string | null = KNOWN) =>
  `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}${knownAt ? `&known_at=${encodeURIComponent(knownAt)}` : ""}`;

async function mountCases(kind: WorkKind, page: WorkIndexResult, site: SiteDetailReadModel = COLD_SITE, q: string = query()) {
  const work = workClient(page);
  render(
    <MemoryRouter initialEntries={[`/sites/${SITE}/work/${kind}?${q}`]}>
      <Routes>
        <Route
          path={`/sites/:siteId/work/${kind}`}
          element={<SiteWorkCasesFrame detail={siteDetail(site)} sitesPath="/sites" kind={kind} workClient={work.client} domainActions={domainActions} />}
        />
      </Routes>
    </MemoryRouter>,
  );
  await settledScreen();
  return { main: document.querySelector("main") as HTMLElement, work };
}

const loaded = (value: WorkIndexBody): WorkIndexResult => ({ status: "loaded", value });
const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const strip = (main: HTMLElement) => main.querySelector(".status-strip") as HTMLElement;
const headings = (main: HTMLElement) => Array.from(main.querySelectorAll("thead th")).map(text);
const summaries = (el: Element) => Array.from(el.querySelectorAll("summary")).map(text);

afterEach(() => {
  cleanup();
});

describe("W5-02 K3a: Site-time Window formatter (M5 withdrawal)", () => {
  it("formats in the stored Site timezone with the mock month table", () => {
    expect(siteWindowText("2026-10-06T16:11:00Z", "Africa/Addis_Ababa")).toBe("6 Oct · from 19:11");
    expect(siteWindowText("2026-10-06T16:11:00Z", "Etc/UTC")).toBe("6 Oct · from 16:11");
    expect(siteWindowText("2026-10-06T22:11:00Z", "Africa/Addis_Ababa")).toBe("7 Oct · from 01:11");
    // P-K3a-8: `Sep`, never Intl's `Sept`.
    expect(siteWindowText("2026-09-30T09:05:00Z", "Etc/UTC")).toBe("30 Sep · from 09:05");
    expect(siteWindowText("not-an-instant", "Etc/UTC")).toBe("not-an-instant");
    // W4 mini-grid keeps its reviewed fixed-offset formatter.
    expect(eatWindowText("2026-10-06T16:11:00Z")).toBe("6 Oct · from 19:11");
  });

  it("reads only a final exact GENERATOR token as backup generator (R89)", () => {
    expect(coldAssetLabel("generator-1 · GENERATOR")).toBe("generator-1 · backup generator");
    expect(coldAssetLabel("compressor-2 · COMPRESSOR")).toBe("compressor-2 · COMPRESSOR");
    expect(coldAssetLabel("generator-1 · GENERATOR_SET")).toBe("generator-1 · GENERATOR_SET");
    expect(coldAssetLabel("GENERATOR")).toBe("GENERATOR");
  });

  it("forms the W6 C2 request Overview href from the selected ID, stored Site code and explicit cutoff (P-G-4, R68)", () => {
    expect(coldRequestHref("abc/1", "CR TEST", "2026-10-22T09:30:00Z")).toBe(
      `/maintenance/requests/abc%2F1?site_id=CR+TEST&known_at=2026-10-22T09%3A30%3A00Z`,
    );
    expect(coldRequestHref("abc", SITE, null)).toBe(`/maintenance/requests/abc?site_id=${SITE}`);
  });
});

describe("W5-02 K3a: cold Site > Work > Incidents (v69 cold-work-incidents)", () => {
  it("renders the mock strip, columns, Site-time Window, plain Findings with versions, and the domain notice", async () => {
    const { main } = await mountCases("incidents", loaded(body([incident(1)])));
    expectV69Panels("cold-work-incidents");
    expect(text(strip(main))).toContain(`Scoped to GreenHarvest · 1 incidents`);
    expect(text(strip(main))).toContain(WORK_STRIP_DETAIL_DOMAIN.incidents);
    expect(text(strip(main))).not.toContain(WORK_STRIP_DETAIL);
    const manage = main.querySelector("[data-work-manage-link]") as HTMLAnchorElement;
    expect(text(manage)).toBe("Manage in Incidents →");
    expect(manage.getAttribute("href")).toBe(`/incidents?${query()}`);
    expect(main.querySelector("[data-work-status]")).toBeNull();
    expect(headings(main)).toEqual(["Case", "Window", "What happened", "Linked findings", "State"]);
    const row = main.querySelector("tbody tr") as HTMLElement;
    // R73: the INC code is plain text.
    expect(text(row.querySelector("[data-work-case-title]"))).toBe("INC-000001 · Backup response failure");
    expect(row.querySelector("[data-work-case-title] a")).toBeNull();
    expect(text(row.querySelector("[data-work-window]"))).toBe("6 Oct · from 19:11");
    // Ruling 4, R65/R66: two plain `Finding {id8}` labels, each with its own `Finding version` disclosure.
    const findings = Array.from(row.querySelectorAll("[data-work-finding]"));
    expect(findings.map((f) => text(f.querySelector("[data-work-finding-unlinked]")))).toEqual(["Finding c0ffee01", "Finding beef0002"]);
    expect(findings.map((f) => summaries(f))).toEqual([["Finding version"], ["Finding version"]]);
    expect(findings.map((f) => text(f.querySelector("[data-work-finding-revision]")))).toEqual([F1_REV, F2_REV]);
    expect(row.querySelector("a[data-work-finding-link]")).toBeNull();
    expect(Array.from(row.querySelectorAll("a")).length).toBe(0);
    // The foot notice is the domain notice (R01), not the W6 notice; no banner on any product screen (ruling 1).
    expect(text(main.querySelector("[data-cold-work-notice]"))).toBe(WORK_CONTEXT_NOTICE_DOMAIN);
    expect(main.textContent).not.toContain(WORK_CONTEXT_NOTICE);
    expect(document.body.textContent).not.toContain(BANNER);
    // CURRENT: no currentness notice and no coverage line; R92 basis and R93 pages stay.
    expect(main.querySelector("[data-cold-work-currentness]")).toBeNull();
    expect(main.querySelector("[data-work-coverage-line]")).toBeNull();
    expect(summaries(main)).toContain("What this list is based on");
    expect(text(main.querySelector("[data-work-showing]"))).toBe("Showing 1–1 of 1");
    expect(text(main.querySelector(".work-cases-scroll-hint"))).toBe("Scroll the table for more columns →");
    // The page-local Window control stays the one date form (K2 ruling 23).
    expect(main.querySelector("form[data-work-window]")).toBeNull();
    expect(main.querySelector("[data-cold-work-window]")).not.toBeNull();
  });

  it("formats the Window in the stored Site timezone, not a fixed offset", async () => {
    const utcSite = { ...COLD_SITE, timezone: "Etc/UTC" } as SiteDetailReadModel;
    const { main } = await mountCases("incidents", loaded(body([incident(1, { occurred_at: "2026-10-06T22:11:00Z" })])), utcSite);
    expect(text(main.querySelector("[data-work-window]"))).toBe("6 Oct · from 22:11");
  });

  it("keeps the W4 refusal unchanged: title and fixed sentence, no server message, no Retry, no zero (K3 ruling 9)", async () => {
    const cases: [WorkKind, WorkIndexResult, string, string][] = [
      ["incidents", { status: "forbidden", code: "SITE_SCOPE_FORBIDDEN", message: "No access to Site 'CR-TEST-01'." }, "No access", "You do not have access to this site's work."],
      ["maintenance", { status: "unavailable", code: "WORK_STORE_UNAVAILABLE", message: "The work store is unavailable." }, "Work records unavailable", "Work records are unavailable right now. Try again."],
    ];
    for (const [kind, refusal, title, sentence] of cases) {
      const { main } = await mountCases(kind, refusal);
      expectV69Panels(`cold-work-${kind}`);
      const refused = main.querySelector("[data-work-refused]") as HTMLElement;
      expect(refused.getAttribute("data-work-refused")).toBe(refusal.status);
      expect(refused.getAttribute("data-work-code")).toBe(refusal.status === "loaded" ? "" : refusal.code);
      expect(text(refused)).toContain(title);
      expect(text(refused)).toContain(sentence);
      expect(text(refused)).not.toContain(refusal.status === "loaded" ? "" : (refusal.message as string));
      expect(text(refused)).not.toMatch(/Retry/);
      expect(text(strip(main))).not.toMatch(/· 0 /);
      expect(main.querySelector("[data-cold-work-currentness]")).toBeNull();
      cleanup();
    }
  });

  it("passes the product vocabulary scan", async () => {
    const { main } = await mountCases("incidents", loaded(body([incident(1)])));
    const { violations } = scanProductVocabulary(main, "cold-work-incidents");
    expect(violations, describeViolations(violations)).toEqual([]);
  });
});

describe("W5-02 K3a: cold Site > Work > Maintenance (v69 cold-work-maintenance)", () => {
  it("renders the asset label, Completed chip, Activity/Outcome disclosures, next-evidence gap and WR Overview link", async () => {
    const { main } = await mountCases("maintenance", loaded(body([request(1)])));
    expectV69Panels("cold-work-maintenance");
    expect(text(strip(main))).toContain(WORK_STRIP_DETAIL_DOMAIN.maintenance);
    const manage = main.querySelector("[data-work-manage-link]") as HTMLAnchorElement;
    expect(text(manage)).toBe("Manage in Maintenance →");
    expect(manage.getAttribute("href")).toBe(`/maintenance?${query()}`);
    expect(headings(main)).toEqual(["Work request", "Asset", "Activity", "Outcome", "Next evidence"]);
    const row = main.querySelector("tbody tr") as HTMLElement;
    // R68: the WR code opens the selected request Overview with the stored Site code and the explicit cutoff.
    const wr = row.querySelector("a[data-work-request-link]") as HTMLAnchorElement;
    expect(text(wr)).toBe("WR-000001 · Starter/control inspection");
    expect(wr.getAttribute("href")).toBe(coldRequestHref(request(1).case_id, SITE, KNOWN));
    expect(wr.getAttribute("href")).toContain(`site_id=${SITE}&known_at=${encodeURIComponent(KNOWN)}`);
    // R89: composite label, ID in the existing `UTC and IDs` disclosure only.
    expect(text(row.querySelector("[data-work-asset]"))).toBe("generator-1 · backup generator");
    const assetCell = row.querySelector("[data-work-asset]")?.closest("td") as HTMLElement;
    expect(summaries(assetCell)).toEqual(["UTC and IDs"]);
    expect(text(assetCell.querySelector("[data-work-asset-id]"))).toBe(GEN);
    // Ruling 3 + R70: `Completed` chip, then the `Activity recorded` disclosure with the stored activity.
    const activity = row.querySelector("[data-work-activity-cell]") as HTMLElement;
    expect(text(activity.querySelector("[data-work-state]"))).toBe("Completed");
    expect(activity.querySelector("[data-work-state]")?.getAttribute("data-work-tone")).toBe("blue");
    expect(summaries(activity)).toEqual(["Activity recorded"]);
    expect(text(activity.querySelector("[data-work-activity]"))).toBe("Starter and control inspection");
    // R71: the `Unverified` badge, then the `Outcome note` disclosure.
    const outcome = row.querySelector("[data-work-outcome-cell]") as HTMLElement;
    expect(text(outcome.querySelector("[data-work-outcome]"))).toBe("Unverified");
    expect(summaries(outcome)).toEqual(["Outcome note"]);
    expect(text(outcome.querySelector("[data-work-outcome-note]"))).toBe(
      "Inspection complete; witnessed automatic-start test remains required",
    );
    // R72: the honest next-evidence gap; never the mock's witnessed test.
    expect(text(row.querySelector("[data-work-next-evidence]"))).toBe("No next evidence recorded");
    expect(main.textContent).not.toContain("Witnessed automatic-start test");
    expect(document.body.textContent).not.toContain(BANNER);
  });

  it("shows the real state chip for an unfinished request and omits null-value disclosures", async () => {
    const rows = [
      request(1, { request_state: "OPEN", state: "OPEN", activity: null, outcome_note: null, record_id: null }),
      request(2, { request_state: "IN_PROGRESS", state: "IN_PROGRESS", asset_label: "compressor-2 · COMPRESSOR", next_evidence_copy: "Run a witnessed start" }),
    ];
    const { main } = await mountCases("maintenance", loaded(body(rows)), COLD_SITE, query(null));
    const [open, progress] = Array.from(main.querySelectorAll("tbody tr")) as HTMLElement[];
    const chip = (r: HTMLElement) => r.querySelector("[data-work-activity-cell] [data-work-state]") as HTMLElement;
    expect([text(chip(open)), chip(open).getAttribute("data-work-tone")]).toEqual(["Open", "amber"]);
    expect([text(chip(progress)), chip(progress).getAttribute("data-work-tone")]).toEqual(["In progress", "blue"]);
    expect(text(main.querySelector("tbody"))).not.toContain("Completed");
    expect(summaries(open.querySelector("[data-work-activity-cell]") as HTMLElement)).toEqual([]);
    expect(summaries(open.querySelector("[data-work-outcome-cell]") as HTMLElement)).toEqual([]);
    // An unknown asset suffix is shown verbatim; selected next-evidence copy is shown when present.
    expect(text(progress.querySelector("[data-work-asset]"))).toBe("compressor-2 · COMPRESSOR");
    expect(text(progress.querySelector("[data-work-next-evidence]"))).toBe("Run a witnessed start");
    // No explicit cutoff in the address: the Overview href carries no known_at.
    expect((open.querySelector("a[data-work-request-link]") as HTMLAnchorElement).getAttribute("href")).toBe(
      `/maintenance/requests/${request(1).case_id}?site_id=${SITE}`,
    );
  });

  it("passes the product vocabulary scan", async () => {
    const { main } = await mountCases("maintenance", loaded(body([request(1)])));
    const { violations } = scanProductVocabulary(main, "cold-work-maintenance");
    expect(violations, describeViolations(violations)).toEqual([]);
  });
});

describe("W5-02 K3a: cold case currentness and complete zero (K3 pre-flight rulings 4-5, R91)", () => {
  const cases: [string, "blue" | "amber", string][] = [
    ["HISTORICAL", "blue", "Read as of 2026-10-22 09:30 UTC. Later work may differ."],
    ["UNKNOWN", "blue", "No selected source for linked evidence. The work record remains recorded."],
    ["PENDING_RECOMPUTE", "amber", "Linked evidence is being reassessed. The work record remains recorded."],
    ["STALE_SOURCE", "amber", "Linked evidence source is out of date. The work record remains recorded."],
  ];
  for (const kind of ["incidents", "maintenance"] as const) {
    for (const [status, tone, words] of cases) {
      it(`${kind}: ${status} notice sits between the strip and the panel (${tone})`, async () => {
        const row = kind === "incidents" ? incident(1) : request(1);
        const coverage = { state: "INCOMPLETE", reason: "LINK_WORK_PENDING" };
        const { main } = await mountCases(kind, loaded(body([row], { status, coverage })));
        const notice = main.querySelector("[data-cold-work-currentness]") as HTMLElement;
        expect(notice.getAttribute("data-cold-work-currentness")).toBe(status);
        expect(notice.classList.contains("v69-notice--blue")).toBe(tone === "blue");
        expect(text(notice)).toBe(words);
        expect(notice.previousElementSibling?.classList.contains("status-strip")).toBe(true);
        expect(notice.nextElementSibling?.matches("section.panel")).toBe(true);
        expectV69Panels(`cold-work-${kind}`);
        // The guard admits the notice only on the cold screens: on the W4 screen ID it is an intruder.
        expect(leadingIntruders(main, `sitework-${kind}`)).not.toEqual([]);
        // Sourced from `status`, never `coverage`: no in-panel coverage line, no strip status label.
        expect(main.querySelector("[data-work-coverage-line]")).toBeNull();
        expect(main.querySelector("[data-work-status]")).toBeNull();
      });
    }

    it(`${kind}: a CURRENT complete zero shows the mock empty card and basis, no notice and no pages`, async () => {
      const { main } = await mountCases(kind, loaded(body([])));
      expectV69Panels(`cold-work-${kind}`);
      const empty = main.querySelector("[data-work-empty]") as HTMLElement;
      const want =
        kind === "incidents"
          ? ["No incidents at this site", "No operational case was opened in the selected period. A case comes from a linked chain of events, not from a single data gap."]
          : ["No maintenance work at this site", "No inspection or repair has been raised here in the selected period."];
      expect([text(empty.querySelector("h3")), text(empty.querySelector("p"))]).toEqual(want);
      expect(text(strip(main))).toContain(`· 0 ${kind}`);
      expect(main.querySelector("[data-cold-work-currentness]")).toBeNull();
      expect(main.querySelector("[data-work-pages]")).toBeNull();
      expect(summaries(main)).toContain("What this list is based on");
    });

    it(`${kind}: a non-complete zero keeps the currentness notice above the empty card`, async () => {
      const { main } = await mountCases(kind, loaded(body([], { status: "UNKNOWN" })));
      expect(main.querySelector("[data-cold-work-currentness]")?.getAttribute("data-cold-work-currentness")).toBe("UNKNOWN");
      expect(main.querySelector("[data-work-empty]")).not.toBeNull();
      expectV69Panels(`cold-work-${kind}`);
    });
  }
});

describe("W5-02 K3b: cold case long text (K3 pre-flight ruling 7, R94)", () => {
  it("previews long selected values at two lines and replaces the preview with the full value while open", async () => {
    const long = (prefix: string, c: string) => prefix + c.repeat(160 - Array.from(prefix).length);
    const title = long("Starter/control inspection 1 ", "T");
    const activity = long("Starter and control inspection 1 ", "A");
    const { main } = await mountCases("maintenance", loaded(body([request(1, { title, activity })])));
    const row = main.querySelector("tbody tr") as HTMLElement;
    const titleCell = row.querySelector("[data-work-case-title]") as HTMLElement;
    expect(titleCell.querySelector("[data-cold-work-preview]")?.classList.contains("work-cases-clamp")).toBe(true);
    const details = titleCell.querySelector("details") as HTMLDetailsElement;
    expect(text(details.querySelector("summary"))).toBe("Read full text");
    details.open = true;
    fireEvent(details, new Event("toggle"));
    await settledScreen();
    expect(titleCell.querySelector("[data-cold-work-preview]")).toBeNull();
    expect(text(titleCell)).toContain(`WR-000001 · ${title}`);
    // The link survives in the opened body (one value, still the Overview).
    expect(titleCell.querySelectorAll("a[data-work-request-link]").length).toBe(1);
    details.open = false;
    fireEvent(details, new Event("toggle"));
    await settledScreen();
    expect(titleCell.querySelector("[data-cold-work-preview]")).not.toBeNull();
    // K3 ruling 12: the Activity recorded body applies the same rule; the chip stays outside the disclosure and every
    // (nested) control is a native summary of its own details, so it is keyboard-operable.
    const activityCell = row.querySelector("[data-work-activity-cell]") as HTMLElement;
    expect(summaries(activityCell)).toEqual(["Activity recorded", "Read full text"]);
    expect(activityCell.querySelector("[data-work-state]")?.closest("details")).toBeNull();
    for (const summary of Array.from(activityCell.querySelectorAll("summary"))) {
      expect(summary.parentElement?.tagName).toBe("DETAILS");
      (summary as HTMLElement).focus();
      expect(document.activeElement).toBe(summary);
    }
  });
});

describe("W5-02 K3b: every long case cell replaces its preview while open (K3 review L4, rulings 7/12, R94)", () => {
  const long = (prefix: string, c: string) => prefix + c.repeat(160 - Array.from(prefix).length);
  const cases: { label: string; kind: WorkKind; row: () => WorkRow; cell: string; outer: string | null; value: string }[] = [
    { label: "Incident What happened", kind: "incidents", row: () => incident(1, { narrative: long("Grid lost, automatic start failed 1 ", "N") }), cell: "[data-work-narrative]", outer: null, value: long("Grid lost, automatic start failed 1 ", "N") },
    { label: "Maintenance Activity recorded", kind: "maintenance", row: () => request(1, { activity: long("Starter and control inspection 1 ", "A") }), cell: "[data-work-activity-cell]", outer: "Activity recorded", value: long("Starter and control inspection 1 ", "A") },
    { label: "Maintenance Outcome note", kind: "maintenance", row: () => request(1, { outcome_note: long("Inspection complete; test required 1 ", "O") }), cell: "[data-work-outcome-cell]", outer: "Outcome note", value: long("Inspection complete; test required 1 ", "O") },
  ];
  const toggle = async (details: HTMLDetailsElement, open: boolean) => {
    details.open = open;
    fireEvent(details, new Event("toggle"));
    await settledScreen();
  };
  for (const c of cases) {
    it(c.label, async () => {
      const { main } = await mountCases(c.kind, loaded(body([c.row()])));
      const cell = main.querySelector(`tbody tr ${c.cell}`) as HTMLElement;
      if (c.outer !== null) {
        const outer = Array.from(cell.querySelectorAll("details")).find((d) => text(d.querySelector(":scope > summary")) === c.outer) as HTMLDetailsElement;
        await toggle(outer, true);
      }
      const inner = Array.from(cell.querySelectorAll("details")).find((d) => text(d.querySelector(":scope > summary")) === "Read full text") as HTMLDetailsElement;
      expect(cell.querySelector("[data-cold-work-preview]")?.classList.contains("work-cases-clamp")).toBe(true);
      await toggle(inner, true);
      expect(cell.querySelector("[data-cold-work-preview]")).toBeNull();
      expect(text(cell).split(c.value).length - 1).toBe(1);
      await toggle(inner, false);
      expect(cell.querySelector("[data-cold-work-preview]")).not.toBeNull();
    });
  }
});

describe("W5-02 K3a: mini-grid isolation", () => {
  it("keeps the W4 strip, arrowless Manage link, W6 notice and form on MINIGRID", async () => {
    const mini = { ...HYBRID_MINI_GRID_SITE, site_id: SITE } as SiteDetailReadModel;
    const { main } = await mountCases("incidents", loaded(body([incident(1)], { status: "HISTORICAL" })), mini);
    expect(text(strip(main))).toContain(WORK_STRIP_DETAIL);
    expect(text(main.querySelector("[data-work-manage-link]"))).toBe("Manage in Incidents");
    expect(main.querySelector("[data-work-status]")).not.toBeNull();
    expect(main.querySelector("[data-cold-work-currentness]")).toBeNull();
    expect(text(main.querySelector("[data-work-notice]"))).toBe(WORK_CONTEXT_NOTICE);
    expect(main.querySelector("form[data-work-window]")).not.toBeNull();
    expect(main.querySelector("a[data-work-finding-link]")).not.toBeNull();
    expect(main.querySelector("[data-work-finding-revision]")).toBeNull();
    // W5-02c K5 (ruling 12): the cold case-cell CSS scope never applies to a mini-grid Site.
    expect(main.querySelector("[data-cold-cases]")).toBeNull();
  });

  it("scopes the cold case-cell CSS to COLDCHAIN with [data-cold-cases] on both case tabs (W5-02c K5, ruling 12)", async () => {
    for (const kind of ["incidents", "maintenance"] as const) {
      const { main } = await mountCases(kind, loaded(body([incident(1)])));
      expect(main.querySelectorAll(".work-cases[data-cold-cases]")).toHaveLength(1);
      cleanup();
    }
  });
});
