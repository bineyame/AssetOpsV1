/**
 * W5-04 V3a: EV_CHARGING Site > Work > Incidents | Maintenance (v69 `ev-work-incidents`, `ev-work-maintenance`) over
 * the merged W4 `site-work-index-1` wire. Pure component fixtures (`evWorkFixtures.ts`); producer-backed captures are
 * V3b's. Covers readiness rulings 13, 14, 17, 18, 45, 46 and 57, build spec E5-withdrawn (R-10) and R03, R74, R75,
 * R80-R85, R104-R107, R111-R113.
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
  coldRequestHref,
  siteWindowText,
} from "../siteWorkCases";
import type { WorkClient, WorkIndexBody, WorkIndexResult, WorkKind, WorkScope } from "../workClient";
import {
  EV_ACTION_ID,
  EV_FINDING,
  EV_FINDING_REV,
  EV_FROM,
  EV_KNOWN,
  EV_SITE,
  EV_SITE_CODE,
  EV_TO,
  evCaseBody,
  evDomainActionLink,
  evIncident,
  evIndexBody,
  evRequest,
} from "./evWorkFixtures";

const R75_SENTENCE = "The selected Finding revision cannot be opened here yet.";

const domainActions: DomainActionClient = {
  getIndex: vi.fn(async () => ({ status: "loaded" as const, value: evIndexBody([]) })),
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
      return scope.limit === 1 ? { status: "loaded" as const, value: evCaseBody([]) } : page;
    }),
  };
  return { client, calls };
}

const query = (knownAt: string | null = EV_KNOWN) =>
  `from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}${knownAt ? `&known_at=${encodeURIComponent(knownAt)}` : ""}`;

async function mountCases(kind: WorkKind, page: WorkIndexResult, site: SiteDetailReadModel = EV_SITE, q: string = query()) {
  const work = workClient(page);
  render(
    <MemoryRouter initialEntries={[`/sites/${EV_SITE_CODE}/work/${kind}?${q}`]}>
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

/** Ruling 45: no cold-named attribute, class or disclosure name anywhere on the EV page. */
function expectNoColdNames(main: HTMLElement) {
  const all = [main, ...Array.from(main.querySelectorAll("*"))];
  const coldAttrs = all.flatMap((el) => el.getAttributeNames().filter((n) => n.startsWith("data-cold-")));
  const coldClasses = all.flatMap((el) => Array.from(el.classList).filter((c) => c.startsWith("cold-work")));
  const coldNames = Array.from(main.querySelectorAll("details[name], [data-disclosure]"))
    .map((el) => el.getAttribute("name") ?? el.getAttribute("data-disclosure") ?? "")
    .filter((n) => n.startsWith("cold-work"));
  expect({ coldAttrs, coldClasses, coldNames }).toEqual({ coldAttrs: [], coldClasses: [], coldNames: [] });
}

afterEach(() => {
  cleanup();
});

describe("W5-04 V3a: EV Site-time Window (build spec E5 withdrawn, R-10)", () => {
  it("formats the two-zone and date-boundary vectors with K3a's shared formatter", () => {
    expect(siteWindowText("2026-10-06T16:11:00Z", "Etc/UTC")).toBe("6 Oct · from 16:11");
    expect(siteWindowText("2026-10-06T16:11:00Z", "Africa/Addis_Ababa")).toBe("6 Oct · from 19:11");
    expect(siteWindowText("2026-10-06T22:11:00Z", "Africa/Addis_Ababa")).toBe("7 Oct · from 01:11");
  });

  it("renders the occurrence in the stored EV Site zone: Etc/UTC fixture and an Addis Ababa date boundary", async () => {
    const utc = await mountCases("incidents", loaded(evCaseBody([evIncident(1)])));
    expect(text(utc.main.querySelector("[data-work-window]"))).toBe("6 Oct · from 16:11");
    expect(utc.main.textContent).not.toMatch(/EAT/);
    cleanup();
    const addis = { ...EV_SITE, timezone: "Africa/Addis_Ababa" } as SiteDetailReadModel;
    const boundary = await mountCases("incidents", loaded(evCaseBody([evIncident(1, { occurred_at: "2026-10-06T22:11:00Z" })])), addis);
    expect(text(boundary.main.querySelector("[data-work-window]"))).toBe("7 Oct · from 01:11");
  });
});

describe("W5-04 V3a: EV Site > Work > Incidents (v69 ev-work-incidents)", () => {
  it("renders the mock strip, columns, plain INC, Site-time Window, plain Finding with R75 version disclosure and notice", async () => {
    const { main } = await mountCases("incidents", loaded(evCaseBody([evIncident(1)])));
    expectV69Panels("ev-work-incidents");
    // R111: the stored display name's short form; the mock's illustrative `Depot` never appears.
    expect(text(strip(main))).toContain("Scoped to EV · 1 incidents");
    expect(main.textContent).not.toContain("Depot");
    expect(text(strip(main))).toContain(WORK_STRIP_DETAIL_DOMAIN.incidents);
    expect(text(strip(main))).not.toContain(WORK_STRIP_DETAIL);
    // W6 Incidents root is mounted: the kind-specific Manage link keeps the window and the explicit cutoff.
    const manage = main.querySelector("[data-work-manage-link]") as HTMLAnchorElement;
    expect(text(manage)).toBe("Manage in Incidents →");
    expect(manage.getAttribute("href")).toBe(`/incidents?${query()}`);
    expect(headings(main)).toEqual(["Case", "Window", "What happened", "Linked findings", "State"]);
    // Panel-head subtitle (pre-flight 36), never a footer.
    expect(text(main.querySelector("section.panel .panel__description, section.panel header p"))).toBe(
      "A case links chronology, findings and work without copying them",
    );
    const row = main.querySelector("tbody tr") as HTMLElement;
    // R85: the INC code is plain text.
    expect(text(row.querySelector("[data-work-case-title]"))).toBe("INC-000001 · Charging session fault");
    expect(row.querySelector("[data-work-case-title] a")).toBeNull();
    expect(text(row.querySelector("[data-work-narrative]"))).toBe("Connector fault ended a charging session; outcome remains unverified");
    // R74/R75: plain `Finding {id8}`, the selected revision and the unavailable sentence inside `Finding version`.
    const finding = row.querySelector("[data-work-finding]") as HTMLElement;
    expect(text(finding.querySelector("[data-work-finding-unlinked]"))).toBe(`Finding ${EV_FINDING.slice(0, 8)}`);
    expect(finding.querySelector("[data-work-finding-unlinked]")?.classList.contains("domain-work-code")).toBe(true);
    expect(summaries(finding)).toEqual(["Finding version"]);
    expect(text(finding.querySelector("[data-work-finding-revision]"))).toBe(EV_FINDING_REV);
    expect(text(finding.querySelector("[data-domain-work-source-unavailable]"))).toBe(R75_SENTENCE);
    expect(text(row.querySelector("[data-work-state]"))).toBe("Open");
    expect(row.querySelector("[data-work-state]")?.getAttribute("data-work-tone")).toBe("red");
    // R113 (ruling 46): the linked EV domain Action stays plain text until V4a; the row has no anchor at all.
    const actionLink = row.querySelector(`[data-work-action-link="${EV_ACTION_ID}"]`) as HTMLElement;
    expect(text(actionLink)).toBe(`Action ${EV_ACTION_ID.slice(0, 8)}`);
    expect(actionLink.querySelector("[data-work-action-plain]")).not.toBeNull();
    expect(Array.from(row.querySelectorAll("a")).length).toBe(0);
    expect(main.querySelector('a[href*="/actions/"]')).toBeNull();
    // R03: the domain notice's first sentence only; no W6 notice.
    expect(text(main.querySelector("[data-domain-work-notice]"))).toBe(WORK_CONTEXT_NOTICE_DOMAIN);
    expect(main.textContent).not.toContain(WORK_CONTEXT_NOTICE);
    // CURRENT: no notice, no coverage line, no strip status; R105 basis and R106 pages stay.
    expect(main.querySelector("[data-domain-work-currentness]")).toBeNull();
    expect(main.querySelector("[data-work-coverage-line]")).toBeNull();
    expect(main.querySelector("[data-work-status]")).toBeNull();
    expect(summaries(main)).toContain("What this list is based on");
    expect(text(main.querySelector("[data-work-showing]"))).toBe("Showing 1–1 of 1");
    // Ruling 18: EV gets `data-domain-cases`, never `data-cold-cases`.
    expect(main.querySelector(".work-cases")?.getAttribute("data-domain-cases")).toBe("EV_CHARGING");
    expectNoColdNames(main);
  });

  it("mounts exactly one date form: the page-local Window after the subtabs, no W4 in-panel form (ruling 57, R112)", async () => {
    for (const kind of ["incidents", "maintenance"] as const) {
      const { main } = await mountCases(kind, loaded(evCaseBody([kind === "incidents" ? evIncident(1) : evRequest(1)])));
      expect(main.querySelectorAll("form").length).toBe(1);
      const window = main.querySelector("form[data-domain-work-window]") as HTMLFormElement;
      expect(window).not.toBeNull();
      expect(main.querySelector("form[data-work-window]")).toBeNull();
      expect(window.previousElementSibling?.matches("nav.site-subtabs")).toBe(true);
      expect(window.nextElementSibling?.querySelector(".status-strip") ?? window.nextElementSibling).not.toBeNull();
      expect(text(window)).toContain("From (UTC)");
      expect(text(window)).toContain("To (UTC, exclusive)");
      expect(window.querySelector("[data-cold-work-window]")).toBeNull();
      cleanup();
    }
  });

  it("applies the Window: keeps the explicit cutoff, drops the cursor and reads page one", async () => {
    const { main, work } = await mountCases("incidents", loaded(evCaseBody([evIncident(1)])), EV_SITE, `${query()}&cursor=c2`);
    const window = main.querySelector("form[data-domain-work-window]") as HTMLFormElement;
    fireEvent.change(window.querySelector("[data-domain-work-window-from]") as HTMLInputElement, { target: { value: "2026-10-01" } });
    fireEvent.change(window.querySelector("[data-domain-work-window-to]") as HTMLInputElement, { target: { value: "2026-10-03" } });
    fireEvent.submit(window);
    await settledScreen();
    const page = work.calls.filter((c) => c.kind === "incidents" && c.scope.limit !== 1).at(-1)!;
    expect(page.scope).toMatchObject({ from: "2026-10-01T00:00:00Z", to: "2026-10-03T00:00:00Z", knownAt: EV_KNOWN, cursor: null });
  });

  it("keeps the W4 refusal: title and fixed sentence, no server message, no Retry, no zero, no notice", async () => {
    const cases: [WorkKind, WorkIndexResult, string, string][] = [
      ["incidents", { status: "forbidden", code: "SITE_SCOPE_FORBIDDEN", message: "No access to Site 'EV-LAB-001'." }, "No access", "You do not have access to this site's work."],
      ["maintenance", { status: "unavailable", code: "WORK_STORE_UNAVAILABLE", message: "The work store is unavailable." }, "Work records unavailable", "Work records are unavailable right now. Try again."],
    ];
    for (const [kind, refusal, title, sentence] of cases) {
      const { main } = await mountCases(kind, refusal);
      expectV69Panels(`ev-work-${kind}`);
      const refused = main.querySelector("[data-work-refused]") as HTMLElement;
      expect(refused.getAttribute("data-work-refused")).toBe(refusal.status);
      expect(text(refused)).toContain(title);
      expect(text(refused)).toContain(sentence);
      expect(text(refused)).not.toContain(refusal.status === "loaded" ? "" : (refusal.message as string));
      expect(text(refused)).not.toMatch(/Retry|EV work unavailable/);
      // A denial is never a zero: no count, no empty card.
      expect(text(strip(main))).not.toMatch(/· 0 /);
      expect(main.querySelector("[data-work-empty]")).toBeNull();
      expect(main.querySelector("[data-domain-work-currentness]")).toBeNull();
      cleanup();
    }
  });

  it("passes the product vocabulary scan", async () => {
    const { main } = await mountCases("incidents", loaded(evCaseBody([evIncident(1)])));
    const { violations } = scanProductVocabulary(main, "ev-work-incidents");
    expect(violations, describeViolations(violations)).toEqual([]);
  });
});

describe("W5-04 V3a: EV Site > Work > Maintenance (v69 ev-work-maintenance)", () => {
  it("renders the submitted WR: Overview href, asset label, Completed chip, R81/R82 disclosures and R84 gap", async () => {
    const { main } = await mountCases("maintenance", loaded(evCaseBody([evRequest(1)])));
    expectV69Panels("ev-work-maintenance");
    expect(text(strip(main))).toContain("Scoped to EV · 1 maintenance");
    expect(text(strip(main))).toContain(WORK_STRIP_DETAIL_DOMAIN.maintenance);
    const manage = main.querySelector("[data-work-manage-link]") as HTMLAnchorElement;
    expect(text(manage)).toBe("Manage in Maintenance →");
    expect(manage.getAttribute("href")).toBe(`/maintenance?${query()}`);
    expect(headings(main)).toEqual(["Work request", "Asset", "Activity", "Outcome", "Next evidence"]);
    expect(text(main.querySelector("section.panel .panel__description, section.panel header p"))).toBe(
      "Completed work is activity; the outcome is verified separately",
    );
    const row = main.querySelector("tbody tr") as HTMLElement;
    // R83: the WR opens the mounted W6 request Overview with the stored Site code and the explicit cutoff.
    const wr = row.querySelector("a[data-work-request-link]") as HTMLAnchorElement;
    expect(text(wr)).toBe("WR-000001 · Connector diagnostic inspection");
    expect(wr.getAttribute("href")).toBe(coldRequestHref(evRequest(1).case_id, EV_SITE_CODE, EV_KNOWN));
    expect(wr.getAttribute("href")).toBe(
      `/maintenance/requests/${evRequest(1).case_id}?site_id=${EV_SITE_CODE}&known_at=${encodeURIComponent(EV_KNOWN)}`,
    );
    // Ruling 13: the selected W4 asset label unchanged (no cold GENERATOR mapping, no Foundation read, no asset ID).
    expect(text(row.querySelector("[data-work-asset]"))).toBe("connector-2 · CONNECTOR");
    expect(row.querySelector("[data-work-asset-id]")).toBeNull();
    // K3 ruling 3 + R81: `Completed` chip and the stored activity in `Activity recorded`.
    const activity = row.querySelector("[data-work-activity-cell]") as HTMLElement;
    expect(text(activity.querySelector("[data-work-state]"))).toBe("Completed");
    expect(summaries(activity)).toEqual(["Activity recorded"]);
    expect(text(activity.querySelector("[data-work-activity]"))).toBe("Inspect connector and witness a charging session");
    // R82: `Unverified` badge and the attested outcome note; no verified result is implied.
    const outcome = row.querySelector("[data-work-outcome-cell]") as HTMLElement;
    expect(text(outcome.querySelector("[data-work-outcome]"))).toBe("Unverified");
    expect(summaries(outcome)).toEqual(["Outcome note"]);
    expect(text(outcome.querySelector("[data-work-outcome-note]"))).toBe("Inspection recorded; recurrence and availability remain unverified");
    expect(main.textContent).not.toMatch(/\bVerified\b/);
    // R84: the honest next-evidence gap.
    expect(text(row.querySelector("[data-work-next-evidence]"))).toBe("No next evidence recorded");
    // R113: the domain Action link in `UTC and IDs` is plain; the WR Overview is the only anchor in the row.
    expect(row.querySelector("[data-work-action-plain]")).not.toBeNull();
    expect(Array.from(row.querySelectorAll("a")).map((a) => a.getAttribute("href"))).toEqual([wr.getAttribute("href")]);
    expectNoColdNames(main);
  });

  it("shows `No asset linked` without an asset label, and the Overview href without an explicit cutoff", async () => {
    const row = evRequest(1, { asset_id: null, asset_label: null, request_state: "OPEN", state: "OPEN", activity: null, outcome_note: null });
    const { main } = await mountCases("maintenance", loaded(evCaseBody([row])), EV_SITE, query(null));
    const tr = main.querySelector("tbody tr") as HTMLElement;
    expect(text(tr.querySelector("[data-work-asset]"))).toBe("");
    expect(text(tr.querySelectorAll("td")[1])).toContain("No asset linked");
    expect(text(tr.querySelector("[data-work-activity-cell] [data-work-state]"))).toBe("Open");
    expect(summaries(tr.querySelector("[data-work-activity-cell]") as HTMLElement)).toEqual([]);
    expect((tr.querySelector("a[data-work-request-link]") as HTMLAnchorElement).getAttribute("href")).toBe(
      `/maintenance/requests/${row.case_id}?site_id=${EV_SITE_CODE}`,
    );
  });

  it("links a domain Action whose W4 href is null as the same plain label (no lineage)", async () => {
    const { main } = await mountCases("maintenance", loaded(evCaseBody([evRequest(1, { action_links: [evDomainActionLink(null)] })])));
    const link = main.querySelector(`[data-work-action-link="${EV_ACTION_ID}"]`) as HTMLElement;
    expect(text(link)).toBe(`Action ${EV_ACTION_ID.slice(0, 8)}`);
    expect(link.querySelector("a")).toBeNull();
  });

  it("passes the product vocabulary scan", async () => {
    const { main } = await mountCases("maintenance", loaded(evCaseBody([evRequest(1)])));
    const { violations } = scanProductVocabulary(main, "ev-work-maintenance");
    expect(violations, describeViolations(violations)).toEqual([]);
  });
});

describe("W5-04 V3a: EV case currentness and complete zero (R80, R104)", () => {
  const cases: [string, "blue" | "amber", string][] = [
    ["HISTORICAL", "blue", "Read as of 2026-10-06 12:00 UTC. Later work may differ."],
    ["UNKNOWN", "blue", "No selected source for linked evidence. The work record remains recorded."],
    ["PENDING_RECOMPUTE", "amber", "Linked evidence is being reassessed. The work record remains recorded."],
    ["STALE_SOURCE", "amber", "Linked evidence source is out of date. The work record remains recorded."],
  ];
  for (const kind of ["incidents", "maintenance"] as const) {
    for (const [status, tone, words] of cases) {
      it(`${kind}: ${status} notice sits between the strip and the panel (${tone})`, async () => {
        const row = kind === "incidents" ? evIncident(1) : evRequest(1);
        const coverage = { state: "INCOMPLETE", reason: "LINK_WORK_PENDING" };
        const { main } = await mountCases(kind, loaded(evCaseBody([row], { status, coverage })));
        const notice = main.querySelector("[data-domain-work-currentness]") as HTMLElement;
        expect(notice.getAttribute("data-domain-work-currentness")).toBe(status);
        expect(notice.classList.contains("v69-notice--blue")).toBe(tone === "blue");
        expect(text(notice)).toBe(words);
        expect(notice.previousElementSibling?.classList.contains("status-strip")).toBe(true);
        expect(notice.nextElementSibling?.matches("section.panel")).toBe(true);
        expectV69Panels(`ev-work-${kind}`);
        // The guard admits the notice only on the domain screens: on the W4 screen ID it is an intruder.
        expect(leadingIntruders(main, `sitework-${kind}`)).not.toEqual([]);
        expect(main.querySelector("[data-work-coverage-line]")).toBeNull();
        expect(main.querySelector("[data-work-status]")).toBeNull();
        expectNoColdNames(main);
      });
    }

    it(`${kind}: a CURRENT complete zero shows the mock empty card and basis, no notice and no pages`, async () => {
      const { main } = await mountCases(kind, loaded(evCaseBody([])));
      expectV69Panels(`ev-work-${kind}`);
      const empty = main.querySelector("[data-work-empty]") as HTMLElement;
      const want =
        kind === "incidents"
          ? ["No incidents at this site", "No operational case was opened in the selected period. A case comes from a linked chain of events, not from a single data gap."]
          : ["No maintenance work at this site", "No inspection or repair has been raised here in the selected period."];
      expect([text(empty.querySelector("h3")), text(empty.querySelector("p"))]).toEqual(want);
      expect(text(strip(main))).toContain(`· 0 ${kind}`);
      expect(main.querySelector("[data-domain-work-currentness]")).toBeNull();
      expect(main.querySelector("[data-work-pages]")).toBeNull();
      expect(main.querySelector("[data-work-refused]")).toBeNull();
      expect(summaries(main)).toContain("What this list is based on");
    });
  }
});

describe("W5-04 V3a: EV long case text (R107)", () => {
  it("previews long selected values with domain names and replaces the preview while open", async () => {
    const long = "Connector " + "x".repeat(150);
    const { main } = await mountCases("incidents", loaded(evCaseBody([evIncident(1, { narrative: long })])));
    const cell = main.querySelector("[data-work-narrative]") as HTMLElement;
    const wrapper = cell.querySelector("[data-domain-work-longtext]") as HTMLElement;
    expect(wrapper.classList.contains("domain-work-longtext")).toBe(true);
    expect(wrapper.getAttribute("data-domain-work-longtext")).toBe("closed");
    expect(text(cell.querySelector("[data-domain-work-preview]"))).toBe(long);
    const details = cell.querySelector("details") as HTMLDetailsElement;
    expect(summaries(cell)).toEqual(["Read full text"]);
    details.open = true;
    fireEvent(details, new Event("toggle"));
    await settledScreen();
    expect(cell.querySelector("[data-domain-work-preview]")).toBeNull();
    expect(cell.querySelector("[data-domain-work-longtext]")?.getAttribute("data-domain-work-longtext")).toBe("open");
    expect(text(cell)).toContain(long);
    expectNoColdNames(main);
  });
});
