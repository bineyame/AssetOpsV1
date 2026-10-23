/**
 * W5-02 K2a/K2b (`.agent/W5-02-build-spec.md` U1-U4, P-K2a-33..48): the COLDCHAIN Site > Work > Actions tab over the
 * union Site Action index, and the domain Action placeholder shell, against the v69 `cold-work` / `cold-action` mock.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteActionFrame, SiteWorkCasesFrame, SiteWorkFrame } from "../../shell/SiteAnalyticsFrames";
import { OPERATOR_SITE_TABS_LABEL } from "../../shell/operatorSiteTabs";
import { expectV69Panels } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import {
  COLD_WORK_UNEXPECTED,
  COLD_WORK_UNREACHABLE,
  createDomainActionClient,
  type DomainActionClient,
  type DomainDetailResult,
  type DomainIndexBody,
  type DomainIndexResult,
  type DomainIndexScope,
} from "../domainActionClient";
import { WORK_CONTEXT_NOTICE, WORK_CONTEXT_NOTICE_DOMAIN } from "../siteWorkCases";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import type { WorkClient, WorkScope } from "../workClient";
import { defaultWorkWindow } from "../workClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";
import {
  COLD_SITE,
  DOMAIN_ID,
  FINDING,
  FINDING_REV,
  FROM,
  KNOWN,
  SITE,
  TO,
  W1_FINDING,
  W1_ID,
  W1_REV,
  detailBody,
  domainRow,
  indexBody,
  w1Row,
} from "./coldWorkFixtures";

type IndexCall = { siteCode: string; scope: DomainIndexScope };

function domainClient(
  index: (scope: DomainIndexScope) => DomainIndexResult | Promise<DomainIndexResult>,
  detail: (id: string, knownAt: string | null) => DomainDetailResult | Promise<DomainDetailResult> = () => ({
    status: "loaded",
    value: detailBody(),
  }),
) {
  const indexCalls: IndexCall[] = [];
  const detailCalls: { id: string; knownAt: string | null }[] = [];
  const client: DomainActionClient = {
    getIndex: vi.fn(async (siteCode: string, scope: DomainIndexScope) => {
      indexCalls.push({ siteCode, scope });
      return index(scope);
    }),
    getDetail: vi.fn(async (_siteCode: string, id: string, knownAt: string | null) => {
      detailCalls.push({ id, knownAt });
      return detail(id, knownAt);
    }),
  };
  return { client, indexCalls, detailCalls };
}

function workClient() {
  const calls: { kind: string; scope: WorkScope }[] = [];
  const client: WorkClient = {
    getWorkIndex: vi.fn(async (_site: string, kind, scope) => {
      calls.push({ kind, scope });
      return { status: "unavailable" as const, code: null, message: null };
    }),
  };
  return { client, calls };
}

const neverActionIndex = { getActionIndex: vi.fn(() => new Promise<never>(() => undefined)) };

function siteDetail(site: SiteDetailReadModel): SiteDetailClient {
  return { getSite: async () => ({ status: "loaded", site }) } as unknown as SiteDetailClient;
}

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}
const where = () => screen.getByTestId("where").textContent ?? "";

async function mountWork(path: string, domain: DomainActionClient, site: SiteDetailReadModel = COLD_SITE) {
  const work = workClient();
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/sites/:siteId/work"
          element={
            <>
              <SiteWorkFrame detail={siteDetail(site)} sitesPath="/sites" actionIndex={neverActionIndex} workClient={work.client} domainActions={domain} />
              <Where />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
  await settledScreen();
  return { main: document.querySelector("main") as HTMLElement, work };
}

async function mountAction(path: string, domain: DomainActionClient, site: SiteDetailReadModel = COLD_SITE) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        {["/sites/:siteId/actions/:actionId", "/sites/:siteId/actions/:actionId/:actionView"].map((p) => (
          <Route key={p} path={p} element={<><SiteActionFrame detail={siteDetail(site)} sitesPath="/sites" domainActions={domain} /><Where /></>} />
        ))}
      </Routes>
    </MemoryRouter>,
  );
  await settledScreen();
  return document.querySelector("main") as HTMLElement;
}

async function mountCases(kind: "incidents" | "maintenance", path: string, domain: DomainActionClient, site: SiteDetailReadModel = COLD_SITE) {
  const work = workClient();
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path={`/sites/:siteId/work/${kind}`}
          element={
            <>
              <SiteWorkCasesFrame detail={siteDetail(site)} sitesPath="/sites" kind={kind} workClient={work.client} actionIndex={neverActionIndex} domainActions={domain} />
              <Where />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
  await settledScreen();
  return { main: document.querySelector("main") as HTMLElement, work };
}

const setDate = (input: Element | null, value: string) => fireEvent.change(input as HTMLInputElement, { target: { value } });

const workPath = (query = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`) => `/sites/${SITE}/work?${query}`;
const text = (el: Element | null | undefined) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();

let fetchRecord: string[] = [];
function stubFetch(handler: (url: string) => Response | Promise<Response>) {
  fetchRecord = [];
  vi.stubGlobal("fetch", async (url: string) => {
    fetchRecord.push(url);
    return handler(url);
  });
}
const json = (status: number, body: unknown) => new Response(JSON.stringify(body), { status });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

/* ---------- domainActionClient: loaded and refused shapes ---------- */

describe("domainActionClient wire validation (P-K2a-48)", () => {
  const scope: DomainIndexScope = { from: FROM, to: TO, knownAt: KNOWN, cursor: "c1" };

  it("loads a validated union index with limit fixed to five, the cutoff and the cursor", async () => {
    stubFetch(() => json(200, indexBody([domainRow(), w1Row()])));
    const result = await createDomainActionClient().getIndex(SITE, scope);
    expect(result.status).toBe("loaded");
    const url = new URL(fetchRecord[0], "http://x");
    expect(url.pathname).toBe(`/api/sites/${SITE}/domain-work/action-index`);
    expect(url.searchParams.get("limit")).toBe("5");
    expect(url.searchParams.get("known_at")).toBe(KNOWN);
    expect(url.searchParams.get("cursor")).toBe("c1");
  });

  it("refuses a malformed 200 (other Site, extra key, bad row, zero without complete coverage)", async () => {
    for (const body of [
      indexBody([domainRow()], { site_code: "OTHER" }),
      { ...indexBody([domainRow()]), extra: 1 },
      indexBody([domainRow({ state: "CLOSED" as never })]),
      indexBody([], { coverage: { state: "PARTIAL", reason: "LINK_WORK_PENDING" } }),
      indexBody([domainRow()], { total_count: 0 }),
    ]) {
      stubFetch(() => json(200, body));
      const result = await createDomainActionClient().getIndex(SITE, scope);
      expect(result).toEqual({ status: "refused", http: 200, code: null, message: COLD_WORK_UNEXPECTED });
    }
  });

  it("reads the current refusal wire `{detail:{code,message,intent:null,results:null}}` on the index (ruling 7)", async () => {
    stubFetch(() => json(503, { detail: { code: "WORK_STORE_UNAVAILABLE", message: "Work store unavailable.", intent: null, results: null } }));
    expect(await createDomainActionClient().getIndex(SITE, scope)).toEqual({
      status: "refused",
      http: 503,
      code: "WORK_STORE_UNAVAILABLE",
      message: "Work store unavailable.",
    });
  });

  it("names refusals, the changed basis and an unreachable server; never an empty success", async () => {
    stubFetch(() => json(403, { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "You do not have access to this site." } }));
    expect(await createDomainActionClient().getIndex(SITE, scope)).toEqual({
      status: "refused",
      http: 403,
      code: "SITE_SCOPE_FORBIDDEN",
      message: "You do not have access to this site.",
    });
    stubFetch(() => json(409, { detail: { code: "WORK_BASIS_CHANGED", message: "The work list changed; request page one without a cursor." } }));
    expect((await createDomainActionClient().getIndex(SITE, scope)).status).toBe("basis_changed");
    stubFetch(() => json(503, { nothing: true }));
    expect(await createDomainActionClient().getIndex(SITE, scope)).toEqual({ status: "refused", http: 503, code: null, message: COLD_WORK_UNEXPECTED });
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("network");
    });
    expect(await createDomainActionClient().getIndex(SITE, scope)).toEqual({ status: "refused", http: null, code: null, message: COLD_WORK_UNREACHABLE });
  });

  it("rejects an invalid page query before any fetch (invalid page query reads nothing)", async () => {
    stubFetch(() => json(200, indexBody([])));
    const bad = await createDomainActionClient().getIndex(SITE, { ...scope, knownAt: "yesterday" });
    expect(bad).toMatchObject({ status: "refused", code: "INVALID_KNOWN_AT" });
    const window = await createDomainActionClient().getIndex(SITE, { ...scope, from: TO, to: FROM });
    expect(window).toMatchObject({ status: "refused", code: "INVALID_WINDOW" });
    expect(fetchRecord).toEqual([]);
  });

  it("refuses a detail whose links.work misses or mistypes a key (review L2)", async () => {
    const work = detailBody().links.work;
    const { href: _omitted, ...withoutHref } = work;
    for (const bad of [withoutHref, { ...work, case_id: 7 }, { ...work, label: undefined }]) {
      stubFetch(() => json(200, detailBody({ links: { ...detailBody().links, work: bad as never } })));
      expect(await createDomainActionClient().getDetail(SITE, DOMAIN_ID, null)).toEqual({ status: "refused", http: 200, code: null, message: COLD_WORK_UNEXPECTED });
    }
  });

  it("loads a COLDCHAIN detail and refuses a W1 or mismatched one; 404 and refusals keep intent and results null", async () => {
    stubFetch(() => json(200, detailBody()));
    expect((await createDomainActionClient().getDetail(SITE, DOMAIN_ID, KNOWN)).status).toBe("loaded");
    expect(new URL(fetchRecord[0], "http://x").searchParams.get("known_at")).toBe(KNOWN);
    for (const body of [
      detailBody({ action: { ...detailBody().action, domain: "MINIGRID" as never } }),
      detailBody({ site_code: "OTHER" }),
      detailBody({ action: { ...detailBody().action, id: W1_ID } }),
      detailBody({ results: null }),
    ]) {
      stubFetch(() => json(200, body));
      expect(await createDomainActionClient().getDetail(SITE, DOMAIN_ID, null)).toEqual({ status: "refused", http: 200, code: null, message: COLD_WORK_UNEXPECTED });
    }
    // K2 ruling 7: the current wire is `{detail:{code,message,intent:null,results:null}}`.
    stubFetch(() => json(404, { detail: { code: "ACTION_NOT_FOUND", message: "Action was not found at this site.", intent: null, results: null } }));
    expect(await createDomainActionClient().getDetail(SITE, DOMAIN_ID, null)).toEqual({
      status: "not_found",
      http: 404,
      code: "ACTION_NOT_FOUND",
      message: "Action was not found at this site.",
    });
    stubFetch(() => json(503, { detail: { code: "WORK_STORE_UNAVAILABLE", message: "Work store unavailable.", intent: null, results: null } }));
    expect(await createDomainActionClient().getDetail(SITE, DOMAIN_ID, null)).toEqual({
      status: "refused",
      http: 503,
      code: "WORK_STORE_UNAVAILABLE",
      message: "Work store unavailable.",
    });
    // A non-null pair inside `detail` is never a refusal and never loaded state.
    for (const pair of [{ intent: { id: "i" }, results: null }, { intent: null, results: [] }]) {
      stubFetch(() => json(503, { detail: { code: "WORK_STORE_UNAVAILABLE", message: "x", ...pair } }));
      expect(await createDomainActionClient().getDetail(SITE, DOMAIN_ID, null)).toEqual({ status: "refused", http: 503, code: null, message: COLD_WORK_UNEXPECTED });
    }
    // Compatibility only: the older top-level null pair is still read as a refusal (it is not the current wire).
    stubFetch(() => json(503, { detail: { code: "WORK_STORE_UNAVAILABLE", message: "Work store unavailable." }, intent: null, results: null }));
    expect(await createDomainActionClient().getDetail(SITE, DOMAIN_ID, null)).toMatchObject({ status: "refused", http: 503, code: "WORK_STORE_UNAVAILABLE" });
    stubFetch(() => json(503, { detail: { code: "WORK_STORE_UNAVAILABLE", message: "x" }, intent: { id: "i" }, results: null }));
    expect(await createDomainActionClient().getDetail(SITE, DOMAIN_ID, null)).toMatchObject({ message: COLD_WORK_UNEXPECTED });
  });
});

/* ---------- Site > Work > Actions on a COLDCHAIN Site ---------- */

describe("cold Site Actions tab (v69 cold-work)", () => {
  it("renders the mock strip, six columns, mixed W1 and domain rows and the domain notice", async () => {
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow(), w1Row()]) }));
    const { main } = await mountWork(workPath(), client);
    expectV69Panels("cold-work");
    expect(main.querySelector("h1")?.textContent).toContain("GreenHarvest Cold Room");
    expect(main.textContent).toContain("Cold-room operations at this site.");
    const strip = main.querySelector("[data-cold-work-strip]");
    expect(text(strip?.querySelector("[data-site-work-scope]"))).toBe("Scoped to GreenHarvest · 2 actions");
    expect(text(strip)).toContain("Cold-chain Actions recorded at this site");
    expect(text(strip)).toContain("Global Actions does not include cold-chain Actions yet.");
    expect(strip?.querySelector("a")).toBeNull();
    expect(Array.from(main.querySelectorAll("thead th")).map(text)).toEqual(["Action", "Source", "Owner", "Due", "State", "Success criterion"]);
    expect(main.querySelector(".panel__description")?.textContent).toBe("Due dates are not yet set");

    const dom = main.querySelector(`[data-cold-work-row="${DOMAIN_ID}"]`) as HTMLElement;
    const cells = Array.from(dom.querySelectorAll("td"));
    expect(text(cells[0].querySelector("a"))).toBe("ACT-000051 · Witness automatic-start test");
    expect(cells[0].querySelector("a")?.getAttribute("href")).toBe(`/sites/${SITE}/actions/${DOMAIN_ID}/verification`);
    expect(text(cells[2])).toBe("Maintenance lead");
    expect(text(cells[3])).toBe("Not set");
    expect(cells[4].querySelector(".w1f4-action-badge--amber")?.textContent).toBe("Open");
    expect(text(cells[5])).toBe("Start requested → generator runs → power → cooling");

    const w1 = main.querySelector(`[data-cold-work-row="${W1_ID}"]`) as HTMLElement;
    const w1Cells = Array.from(w1.querySelectorAll("td"));
    expect(text(w1Cells[0].querySelector("a"))).toBe("ACT-000050");
    expect(w1Cells[0].querySelector("a")?.getAttribute("href")).toBe(`/sites/${SITE}/actions/${W1_ID}`);
    expect(text(w1Cells[2])).toBe("Not assigned");
    expect(text(w1Cells[3])).toBe("Not set");
    expect(text(w1Cells[4])).toBe("Accepted · not applied");
    expect(text(w1Cells[5])).toBe("No success criterion declared");
    expect(main.textContent).not.toContain("Battery reserve trial");
    expect(main.textContent).not.toContain("Latest step:");

    const notice = main.querySelector("[data-cold-work-notice]");
    expect(notice?.textContent).toBe(WORK_CONTEXT_NOTICE_DOMAIN);
    expect(notice?.querySelector("svg")).not.toBeNull();
    expect(main.textContent).not.toContain(WORK_CONTEXT_NOTICE);
    expect(main.textContent).not.toContain("global create flow");
    // The server's ruled criterion summary contains "runs" (a T028 term); no cold-work screen gloss is registered for
    // it yet (question filed in .agent/W5-02b-questions.md), so only that exact literal is set aside here.
    const { violations } = scanProductVocabulary(main, "cold-work");
    // K2 ruling 14: exactly that one text-node literal is set aside, never a subtree.
    const others = violations.filter((v) => !(v.where === "text" && v.text === "Start requested → generator runs → power → cooling"));
    expect(others, describeViolations(others)).toEqual([]);
  });

  it("removes every W1 helper and the W1 window form on cold", async () => {
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()]) }));
    const { main } = await mountWork(workPath(), client);
    for (const gone of [
      "Showing",
      "Newest first.",
      "Show the first 4",
      "This list holds Actions only",
      "Applied or closed is",
      "What this list is based on",
      "Not recorded",
      "No Actions created at this site in this window",
      "Opening an Action moves you to its own page",
    ]) {
      expect(main.textContent).not.toContain(gone);
    }
    expect(main.querySelector("[data-site-work-window]")).toBeNull();
    // K2 ruling 1: the only form is the page-local cold `Window` control (R88).
    expect(Array.from(main.querySelectorAll("form")).map((f) => f.hasAttribute("data-cold-work-window"))).toEqual([true]);
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to GreenHarvest · 1 actions");
  });

  it("shows the Source as plain `Finding {id8}` with the selected revision in a disclosure, never an anchor (R65/R66)", async () => {
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow(), w1Row()]) }));
    const { main } = await mountWork(workPath(), client);
    for (const [id, finding, rev] of [
      [DOMAIN_ID, FINDING, FINDING_REV],
      [W1_ID, W1_FINDING, W1_REV],
    ]) {
      const source = main.querySelector(`[data-cold-work-row="${id}"] td:nth-child(2)`) as HTMLElement;
      expect(source.querySelector("a")).toBeNull();
      expect(text(source.querySelector("[data-cold-work-source]"))).toBe(`Finding ${finding.slice(0, 8)}`);
      const details = source.querySelector("details") as HTMLDetailsElement;
      expect(details.open).toBe(false);
      expect(text(details.querySelector("summary"))).toBe("Finding version");
      expect(details.querySelector("[data-cold-work-revision]")?.textContent).toBe(rev);
    }
    expect(Array.from(main.querySelectorAll("a")).some((a) => (a.getAttribute("href") ?? "").includes("revision_id"))).toBe(false);
  });

  it("omits the due subtitle when any selected row has a due date, and renders the UTC date", async () => {
    const { client } = domainClient(() => ({
      status: "loaded",
      value: indexBody([domainRow({ due_at: "2026-11-02T21:00:00Z" })], { all_due_dates_unset: false }),
    }));
    const { main } = await mountWork(workPath(), client);
    expect(main.querySelector(".panel__description")).toBeNull();
    expect(text(main.querySelector("[data-cold-work-due]"))).toBe("2026-11-02");
  });

  it("defaults to W4's last seven complete UTC days and reads with no cursor and no cutoff", async () => {
    const { client, indexCalls } = domainClient(() => ({ status: "loaded", value: indexBody([]) }));
    await mountWork(`/sites/${SITE}/work`, client);
    const expected = defaultWorkWindow();
    expect(indexCalls[0].scope).toEqual({ from: expected.from, to: expected.to, knownAt: null, cursor: null });
  });

  it("subtab hrefs keep from, to and known_at, drop the cursor; counts use the union and the same cutoff", async () => {
    const { client, indexCalls } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow(), w1Row()]) }));
    const query = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}&cursor=abc`;
    const { work } = await mountWork(workPath(query), client);
    const tabs = Array.from(document.querySelectorAll('nav[aria-label="Work lists"] a'));
    expect(tabs.map(text)).toEqual(["Actions (2)", "Incidents (—)", "Maintenance (—)"]);
    const keep = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;
    expect(tabs.map((a) => a.getAttribute("href"))).toEqual([
      `/sites/${SITE}/work?${keep}`,
      `/sites/${SITE}/work/incidents?${keep}`,
      `/sites/${SITE}/work/maintenance?${keep}`,
    ]);
    expect(indexCalls.some((c) => c.scope.cursor === null && c.scope.knownAt === KNOWN)).toBe(true);
    expect(indexCalls.some((c) => c.scope.cursor === "abc")).toBe(true);
    await waitFor(() => expect(work.calls.length).toBe(2));
    expect(work.calls.every((c) => c.scope.knownAt === KNOWN && c.scope.cursor === null)).toBe(true);
  });

  it("folds after four rows behind `Show all N Actions`; Next page pins the response cutoff; First page drops the cursor", async () => {
    const rows = Array.from({ length: 5 }, (_, i) =>
      domainRow({ action_id: `6f1c2a7e-0d4b-4c3e-9a51-1b2c3d4e5f6${i}`, action_code: `ACT-00005${i}` }),
    );
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody(rows, { total_count: 7, next_cursor: "next1" }) }));
    const { main } = await mountWork(workPath(`from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&cursor=prev`), client);
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to GreenHarvest · 7 actions");
    const bodyRows = Array.from(main.querySelectorAll("tbody tr")) as HTMLElement[];
    expect(bodyRows.map((r) => r.hidden)).toEqual([false, false, false, false, true]);
    const showAll = main.querySelector("[data-cold-work-show-all]") as HTMLButtonElement;
    expect(showAll.textContent).toBe("Show all 5 Actions");
    const next = new URL(main.querySelector("[data-cold-work-next]")?.getAttribute("href") ?? "", "http://x");
    expect(next.searchParams.get("cursor")).toBe("next1");
    expect(next.searchParams.get("known_at")).toBe(KNOWN);
    expect(next.searchParams.get("limit")).toBeNull();
    const first = new URL(main.querySelector("[data-cold-work-first]")?.getAttribute("href") ?? "", "http://x");
    expect(first.searchParams.get("cursor")).toBeNull();
    expect(first.searchParams.get("from")).toBe(FROM);
    fireEvent.click(showAll);
    expect((Array.from(main.querySelectorAll("tbody tr")) as HTMLElement[]).every((r) => !r.hidden)).toBe(true);
    expect(main.querySelector("[data-cold-work-show-all]")).toBeNull();
  });

  it("restarts page one without the stale cursor after a changed basis (409)", async () => {
    const { client, indexCalls } = domainClient((scope) =>
      scope.cursor
        ? { status: "basis_changed", http: 409, code: "WORK_BASIS_CHANGED", message: "The work list changed; request page one without a cursor." }
        : { status: "loaded", value: indexBody([domainRow()]) },
    );
    const { main } = await mountWork(workPath(`from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}&cursor=stale`), client);
    const panel = main.querySelector("[data-cold-work-refusal]") as HTMLElement;
    expect(text(panel)).toContain("Cold work unavailable");
    expect(text(panel)).toContain("The work list changed; request page one without a cursor.");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(where()).not.toContain("cursor"));
    expect(where()).toContain(`known_at=${encodeURIComponent(KNOWN)}`);
    await settledScreen();
    expect(indexCalls.at(-1)?.scope.cursor).toBeNull();
    expect(main.querySelector("[data-cold-work-row]")).not.toBeNull();
  });

  it("distinguishes a complete zero, a refusal and loading; only a complete zero shows the mock empty", async () => {
    const zero = domainClient(() => ({ status: "loaded", value: indexBody([]) }));
    let { main } = await mountWork(workPath(), zero.client);
    const empty = main.querySelector("[data-cold-work-empty]") as HTMLElement;
    expect(empty.querySelector("svg")).not.toBeNull();
    expect(text(empty.querySelector("h3"))).toBe("No actions at this site");
    expect(text(empty.querySelector("p"))).toBe("No accepted recommendation or evidence request has been raised here yet.");
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to GreenHarvest · 0 actions");
    expect(main.querySelector(".panel__description")).toBeNull();
    expect(main.querySelector("table")).toBeNull();
    cleanup();

    let attempts = 0;
    const refused = domainClient(() => {
      attempts += 1;
      return { status: "refused", http: 503, code: "WORK_STORE_UNAVAILABLE", message: "Work records are unavailable right now." };
    });
    ({ main } = await mountWork(workPath(), refused.client));
    expect(main.querySelector("[data-cold-work-empty]")).toBeNull();
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to GreenHarvest · — actions");
    // K2 ruling 11: the subtab count is unknown too; zero is only a loaded COMPLETE empty selection.
    expect(text(document.querySelector('nav[aria-label="Work lists"] a'))).toBe("Actions (—)");
    expect(main.textContent).not.toContain("0 actions");
    expect(text(main.querySelector("[data-cold-work-refusal]"))).toContain("Cold work unavailable");
    expect(text(main.querySelector("[data-cold-work-refusal-message]"))).toBe("Work records are unavailable right now.");
    expect(main.querySelector(".panel__description")).toBeNull();
    const before = attempts;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(attempts).toBe(before + 1));
    cleanup();

    const pending = domainClient(() => new Promise<DomainIndexResult>(() => undefined));
    render(
      <MemoryRouter initialEntries={[workPath()]}>
        <Routes>
          <Route path="/sites/:siteId/work" element={<SiteWorkFrame detail={siteDetail(COLD_SITE)} sitesPath="/sites" actionIndex={neverActionIndex} workClient={workClient().client} domainActions={pending.client} />} />
        </Routes>
      </MemoryRouter>,
    );
    await screen.findByText("Loading the site's Actions.");
    main = document.querySelector("main") as HTMLElement;
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to GreenHarvest · — actions");
    expect(text(document.querySelector('nav[aria-label="Work lists"] a'))).toBe("Actions (—)");
    expect(main.querySelector("[data-cold-work-empty]")).toBeNull();
  });

  it("puts the currentness notice below the strip for every non-current status (component states)", async () => {
    const cases: [DomainIndexBody["status"], string, "blue" | "amber"][] = [
      ["HISTORICAL", "Read as of 2026-10-22 09:30 UTC. Later work may differ.", "blue"],
      ["PENDING_RECOMPUTE", "Linked evidence is being reassessed. The work record remains recorded.", "amber"],
      ["STALE_SOURCE", "Linked evidence source is out of date. The work record remains recorded.", "amber"],
      ["UNKNOWN", "No selected source for linked evidence. The work record remains recorded.", "blue"],
    ];
    for (const [status, words, tone] of cases) {
      const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()], { status }) }));
      const { main } = await mountWork(workPath(), client);
      const notice = main.querySelector("[data-cold-work-currentness]") as HTMLElement;
      expect(notice.getAttribute("data-cold-work-currentness")).toBe(status);
      expect(text(notice)).toBe(words);
      expect(notice.previousElementSibling?.hasAttribute("data-cold-work-strip")).toBe(true);
      expect(notice.nextElementSibling?.matches("section.panel")).toBe(true);
      // K2 ruling 16: blue info for Historical/Unknown, amber for Pending recompute/Stale source.
      expect(notice.classList.contains("v69-notice--blue")).toBe(tone === "blue");
      // K2 ruling 15 (R91): the panel guard admits the notice only between the strip and panel 1.
      expectV69Panels("cold-work");
      const strip = main.querySelector("[data-cold-work-strip]") as HTMLElement;
      strip.before(notice);
      expect(() => expectV69Panels("cold-work")).toThrow();
      strip.after(notice);
      expectV69Panels("cold-work");
      // No currentness changes the lifecycle chip.
      expect(main.querySelector("[data-cold-work-state]")?.textContent).toBe("Open");
      cleanup();
    }
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()]) }));
    const { main } = await mountWork(workPath(), client);
    expect(main.querySelector("[data-cold-work-currentness]")).toBeNull();
    expectV69Panels("cold-work");
    cleanup();
    const zero = domainClient(() => ({ status: "loaded", value: indexBody([]) }));
    const zeroMain = (await mountWork(workPath(), zero.client)).main;
    expect(zeroMain.querySelector("[data-cold-work-currentness]")).toBeNull();
    expectV69Panels("cold-work");
  });

  it("previews long text at two lines with the full text in `Read full text`", async () => {
    const title = "T".repeat(160);
    const owner = "O".repeat(81);
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow({ title, owner_label: owner })]) }));
    const { main } = await mountWork(workPath(), client);
    const row = main.querySelector(`[data-cold-work-row="${DOMAIN_ID}"]`) as HTMLElement;
    const [action, , ownerCell] = Array.from(row.querySelectorAll("td"));
    expect(action.querySelector(".work-cases-clamp a")).not.toBeNull();
    const full = action.querySelector("details") as HTMLDetailsElement;
    expect(full.querySelector("summary")?.textContent).toBe("Read full text");
    expect(full.querySelector(".disclosure__body")?.textContent).toBe(`ACT-000051 · ${title}`);
    expect(ownerCell.querySelector(".work-cases-clamp")?.textContent).toBe(owner);
    expect(ownerCell.querySelector("details summary")?.textContent).toBe("Read full text");
    expect(ownerCell.querySelector("details .disclosure__body")?.textContent).toBe(owner);
    // At or under the threshold: no preview clamp and no disclosure.
    cleanup();
    const short = domainClient(() => ({ status: "loaded", value: indexBody([domainRow({ owner_label: "O".repeat(80) })]) }));
    const shortMain = (await mountWork(workPath(), short.client)).main;
    expect(shortMain.querySelector("[data-cold-work-owner] details")).toBeNull();
    expect(shortMain.querySelector("[data-cold-work-owner] .work-cases-clamp")).toBeNull();
  });

  it("puts the page-local Window control after the Work subtabs and before the scope strip, showing the default dates (ruling 1, R88)", async () => {
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()]) }));
    const { main } = await mountWork(`/sites/${SITE}/work`, client);
    const form = main.querySelector("[data-cold-work-window]") as HTMLFormElement;
    expect(form.getAttribute("aria-label")).toBe("Window");
    expect(form.previousElementSibling?.matches('nav[aria-label="Work lists"]')).toBe(true);
    expect(form.nextElementSibling?.firstElementChild?.hasAttribute("data-cold-work-strip")).toBe(true);
    const expected = defaultWorkWindow();
    expect((form.querySelector("[data-cold-work-window-from]") as HTMLInputElement).value).toBe(expected.from.slice(0, 10));
    expect((form.querySelector("[data-cold-work-window-to]") as HTMLInputElement).value).toBe(expected.to.slice(0, 10));
    expect(text(form.querySelector("[data-cold-work-window-apply]"))).toBe("Apply");
    expect(form.querySelector("[data-cold-work-window-error]")).toBeNull();
    expectV69Panels("cold-work");
  });

  it("Apply writes from,to into the URL, keeps an explicit known_at, drops the cursor and reads page one (ruling 1)", async () => {
    const { client, indexCalls } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()]) }));
    const query = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}&cursor=abc`;
    const { main } = await mountWork(workPath(query), client);
    const form = main.querySelector("[data-cold-work-window]") as HTMLFormElement;
    expect((form.querySelector("[data-cold-work-window-from]") as HTMLInputElement).value).toBe("2026-10-15");
    expect((form.querySelector("[data-cold-work-window-to]") as HTMLInputElement).value).toBe("2026-10-22");
    setDate(form.querySelector("[data-cold-work-window-from]"), "2026-10-01");
    setDate(form.querySelector("[data-cold-work-window-to]"), "2026-10-20");
    fireEvent.click(form.querySelector("[data-cold-work-window-apply]") as HTMLButtonElement);
    const want = `/sites/${SITE}/work?from=${encodeURIComponent("2026-10-01T00:00:00Z")}&to=${encodeURIComponent("2026-10-20T00:00:00Z")}&known_at=${encodeURIComponent(KNOWN)}`;
    await waitFor(() => expect(where()).toBe(want));
    await settledScreen();
    expect(indexCalls.at(-1)?.scope).toEqual({ from: "2026-10-01T00:00:00Z", to: "2026-10-20T00:00:00Z", knownAt: KNOWN, cursor: null });
    cleanup();
    // No explicit known_at in the URL: none is invented.
    const plain = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()]) }));
    const plainMain = (await mountWork(`/sites/${SITE}/work`, plain.client)).main;
    setDate(plainMain.querySelector("[data-cold-work-window-from]"), "2026-10-01");
    setDate(plainMain.querySelector("[data-cold-work-window-to]"), "2026-11-01");
    fireEvent.click(plainMain.querySelector("[data-cold-work-window-apply]") as HTMLButtonElement);
    await waitFor(() => expect(where()).toBe(`/sites/${SITE}/work?from=${encodeURIComponent("2026-10-01T00:00:00Z")}&to=${encodeURIComponent("2026-11-01T00:00:00Z")}`));
    await settledScreen();
  });

  it("invalid Window input stays on the page with the window error and makes no new read (ruling 1)", async () => {
    const { client, indexCalls } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()]) }));
    const { main } = await mountWork(workPath(), client);
    const before = where();
    const reads = indexCalls.length;
    const form = main.querySelector("[data-cold-work-window]") as HTMLFormElement;
    for (const [from, to] of [
      ["2026-10-20", "2026-10-20"],
      ["2026-10-20", "2026-10-10"],
      ["2026-09-01", "2026-10-03"],
      ["", "2026-10-03"],
      ["2026-10-01", ""],
    ]) {
      setDate(form.querySelector("[data-cold-work-window-from]"), from);
      setDate(form.querySelector("[data-cold-work-window-to]"), to);
      fireEvent.click(form.querySelector("[data-cold-work-window-apply]") as HTMLButtonElement);
      expect(text(form.querySelector("[data-cold-work-window-error]"))).toBe("The window may span at most 31 days.");
      expect(where()).toBe(before);
    }
    await settledScreen();
    expect(indexCalls.length).toBe(reads);
    // Exactly 31 days is a valid window.
    setDate(form.querySelector("[data-cold-work-window-from]"), "2026-09-01");
    setDate(form.querySelector("[data-cold-work-window-to]"), "2026-10-02");
    fireEvent.click(form.querySelector("[data-cold-work-window-apply]") as HTMLButtonElement);
    await waitFor(() => expect(where()).toContain(`from=${encodeURIComponent("2026-09-01T00:00:00Z")}`));
    await settledScreen();
    expect(main.querySelector("[data-cold-work-window-error]")).toBeNull();
  });

  it("keeps the Window control on cold Incidents and Maintenance; Apply preserves known_at and drops the cursor (ruling 1)", async () => {
    for (const kind of ["incidents", "maintenance"] as const) {
      const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()]) }));
      const query = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}&cursor=abc`;
      const { main, work } = await mountCases(kind, `/sites/${SITE}/work/${kind}?${query}`, client);
      const form = main.querySelector("[data-cold-work-window]") as HTMLFormElement;
      expect(form.previousElementSibling?.matches('nav[aria-label="Work lists"]')).toBe(true);
      const keep = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;
      expect(Array.from(document.querySelectorAll('nav[aria-label="Work lists"] a')).map((a) => a.getAttribute("href"))).toEqual([
        `/sites/${SITE}/work?${keep}`,
        `/sites/${SITE}/work/incidents?${keep}`,
        `/sites/${SITE}/work/maintenance?${keep}`,
      ]);
      setDate(form.querySelector("[data-cold-work-window-from]"), "2026-10-02");
      setDate(form.querySelector("[data-cold-work-window-to]"), "2026-10-09");
      fireEvent.click(form.querySelector("[data-cold-work-window-apply]") as HTMLButtonElement);
      const want = `/sites/${SITE}/work/${kind}?from=${encodeURIComponent("2026-10-02T00:00:00Z")}&to=${encodeURIComponent("2026-10-09T00:00:00Z")}&known_at=${encodeURIComponent(KNOWN)}`;
      await waitFor(() => expect(where()).toBe(want));
      await settledScreen();
      const last = work.calls.filter((c) => c.kind === kind).at(-1);
      expect(last?.scope).toMatchObject({ from: "2026-10-02T00:00:00Z", to: "2026-10-09T00:00:00Z", knownAt: KNOWN, cursor: null });
      cleanup();
    }
  });

  it("never takes the cold Work subtitle from Foundation summary (ruling 9, R90)", async () => {
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([domainRow()]) }));
    const site = {
      ...COLD_SITE,
      foundation: { version: 1, valid_from: FROM, summary: "Foundation configuration summary text", components: [], topology: null, devices: null, signal_mappings: null, control_assumptions: null },
    } as unknown as SiteDetailReadModel;
    const { main } = await mountWork(workPath(), client, site);
    expect(main.textContent).toContain("Cold-room operations at this site.");
    expect(main.textContent).not.toContain("Foundation configuration summary text");
  });

  it("keeps a mini-grid Site on the W1 list (no domain read, W1 window form kept)", async () => {
    const { client, indexCalls } = domainClient(() => ({ status: "loaded", value: indexBody([]) }));
    const mini = { ...HYBRID_MINI_GRID_SITE, site_id: SITE } as SiteDetailReadModel;
    render(
      <MemoryRouter initialEntries={[`/sites/${SITE}/work`]}>
        <Routes>
          <Route path="/sites/:siteId/work" element={<SiteWorkFrame detail={siteDetail(mini)} sitesPath="/sites" actionIndex={neverActionIndex} workClient={workClient().client} domainActions={client} />} />
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
    expect(indexCalls).toEqual([]);
    expect(document.querySelector("[data-site-work-window]")).not.toBeNull();
    expect(document.querySelector("[data-cold-work-window]")).toBeNull();
    expect(document.querySelector("[data-cold-work-strip]")).toBeNull();
    expect(Array.from(document.querySelectorAll('nav[aria-label="Work lists"] a')).map((a) => a.getAttribute("href"))).toEqual([
      `/sites/${SITE}/work`,
      `/sites/${SITE}/work/incidents`,
      `/sites/${SITE}/work/maintenance`,
    ]);
  });
});

/* ---------- the domain Action placeholder shell (v69 cold-action) ---------- */

describe("cold domain Action route and placeholder shell (U1, U2)", () => {
  it("renders the mock shell for a validated domain Action on /verification", async () => {
    stubFetch(() => json(599, {}));
    const { client, detailCalls } = domainClient(() => ({ status: "loaded", value: indexBody([]) }));
    const main = await mountAction(`/sites/${SITE}/actions/${DOMAIN_ID}/verification?known_at=${encodeURIComponent(KNOWN)}`, client);
    expect(detailCalls).toEqual([{ id: DOMAIN_ID, knownAt: KNOWN }]);
    const crumbs = main.querySelector("[data-domain-action-crumbs]") as HTMLElement;
    const items = Array.from(crumbs.querySelectorAll("li")).map(text);
    expect(items).toEqual(["Actions", "ACT-000051", "Verification"]);
    expect(crumbs.querySelector("li a")?.getAttribute("href")).toBe("/actions");
    expect(crumbs.querySelectorAll("li a")).toHaveLength(1);
    expect(text(crumbs.querySelector("[data-domain-action-crumb-site]"))).toBe("· site: GreenHarvest Cold Room");
    expect(crumbs.querySelector("[data-domain-action-crumb-site] a")?.getAttribute("href")).toBe(`/sites/${SITE}`);
    expect(text(main.querySelector("h1"))).toBe("ACT-000051 · Witness automatic-start test");
    expect(main.textContent).toContain("Has backup service been restored after the inspection?");
    const openSite = main.querySelector("[data-domain-action-open-site]") as HTMLElement;
    expect(openSite.getAttribute("href")).toBe(`/sites/${SITE}`);
    // K2 ruling 18: the mock `btn(...)` secondary button class, not a bare link.
    expect(openSite.classList.contains("button")).toBe(true);
    expect(openSite.classList.contains("primary")).toBe(false);
    // K2 ruling 1 (R88): no topbar, Site switch or provenance tag on `cold-action`.
    for (const absent of [".topbar", ".site-switch", 'select[aria-label="Switch site"]', ".prov-tag", "[data-cold-work-window]"]) {
      expect(document.querySelector(absent)).toBeNull();
    }
    expect(document.querySelector(`nav[aria-label="${OPERATOR_SITE_TABS_LABEL}"]`)).toBeNull();
    const tabs = Array.from(main.querySelectorAll('nav[aria-label="Action sections"] a'));
    expect(tabs.map(text)).toEqual(["Verification"]);
    expect(tabs[0].getAttribute("aria-current")).toBe("page");
    expect(tabs[0].getAttribute("href")).toBe(`/sites/${SITE}/actions/${DOMAIN_ID}/verification?known_at=${encodeURIComponent(KNOWN)}`);
    expect(main.querySelector("[data-tab-unavailable]")).toBeNull();
    const strip = main.querySelector("[data-domain-action-strip]") as HTMLElement;
    expect(strip.querySelector(".w1f4-action-badge--amber")?.textContent).toBe("Open");
    expect(text(strip.querySelector("[data-domain-action-status-line]"))).toBe(`Maintenance lead · GreenHarvest · Finding ${FINDING.slice(0, 8)}`);
    expect(strip.querySelector("a")).toBeNull();
    expect(strip.querySelector("[data-domain-action-revision]")?.textContent).toBe(FINDING_REV);
    expect(text(main.querySelector("[data-domain-action-panel]"))).toBe("Action details are being prepared.");
    expect(text(main.querySelector("[data-domain-action-notice]"))).toBe("Completed inspection does not establish successful service restoration.");
    expect(main.querySelector("[data-domain-action-currentness]")).toBeNull();
    // K2 ruling 10 / U2 order: one untitled panel right after the status strip, then the blue notice, last.
    const panelBox = main.querySelector("[data-domain-action-panel]")?.closest("section.panel") as HTMLElement;
    expect(main.querySelectorAll("section.panel")).toHaveLength(1);
    expect(panelBox.querySelector("h2")).toBeNull();
    expect(panelBox.previousElementSibling).toBe(strip);
    const notice = main.querySelector("[data-domain-action-notice]") as HTMLElement;
    expect(panelBox.nextElementSibling).toBe(notice);
    expect(notice.classList.contains("v69-notice--blue")).toBe(true);
    expect(notice.nextElementSibling).toBeNull();
    // No battery read on a domain Action.
    expect(fetchRecord).toEqual([]);
    const { violations } = scanProductVocabulary(main, "cold-action");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("shows the historical notice below the status strip and `Not assigned` for a null owner", async () => {
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([]) }), () => ({
      status: "loaded",
      value: detailBody({ status: "HISTORICAL", action: { ...detailBody().action, owner_label: null }, intent: null, results: null }),
    }));
    const main = await mountAction(`/sites/${SITE}/actions/${DOMAIN_ID}/verification`, client);
    const notice = main.querySelector("[data-domain-action-currentness]") as HTMLElement;
    expect(text(notice)).toBe("Read as of 2026-10-22 09:30 UTC. Later work may differ.");
    expect(notice.previousElementSibling?.hasAttribute("data-domain-action-strip")).toBe(true);
    expect(text(main.querySelector("[data-domain-action-status-line]"))).toBe(`Not assigned · GreenHarvest · Finding ${FINDING.slice(0, 8)}`);
    expect(main.querySelector("[data-domain-action-revision]")).toBeNull();
  });

  it("loading shows the shell skeleton and the declaration loading sentence", async () => {
    const { client } = domainClient(() => ({ status: "loaded", value: indexBody([]) }), () => new Promise<DomainDetailResult>(() => undefined));
    render(
      <MemoryRouter initialEntries={[`/sites/${SITE}/actions/${DOMAIN_ID}/verification`]}>
        <Routes>
          <Route path="/sites/:siteId/actions/:actionId/:actionView" element={<SiteActionFrame detail={siteDetail(COLD_SITE)} sitesPath="/sites" domainActions={client} />} />
        </Routes>
      </MemoryRouter>,
    );
    await screen.findByText("Loading the cold Action declaration.");
    expect(document.querySelector('[data-domain-action-shell="loading"] nav[aria-label="Action sections"]')).not.toBeNull();
    expect(document.querySelector("[data-domain-action-strip]")).toBeNull();
  });

  it("a 404 says not found and never falls back to W1; a refusal shows the server message and Retry", async () => {
    stubFetch(() => json(599, {}));
    const missing = domainClient(
      () => ({ status: "loaded", value: indexBody([]) }),
      () => ({ status: "not_found", http: 404, code: "ACTION_NOT_FOUND", message: "Action was not found at this site." }),
    );
    let main = await mountAction(`/sites/${SITE}/actions/${W1_ID}/verification`, missing.client);
    expect(text(main.querySelector("[data-domain-action-panel]"))).toBe("Action was not found at this site.");
    expect(fetchRecord).toEqual([]);
    expect(main.querySelector("[data-domain-action-strip]")).toBeNull();
    cleanup();

    let attempts = 0;
    const refused = domainClient(
      () => ({ status: "loaded", value: indexBody([]) }),
      () => {
        attempts += 1;
        return { status: "refused", http: 403, code: "SITE_SCOPE_FORBIDDEN", message: "You do not have access to this site." };
      },
    );
    main = await mountAction(`/sites/${SITE}/actions/${DOMAIN_ID}/verification`, refused.client);
    const panel = main.querySelector('[data-domain-action-panel="refused"]') as HTMLElement;
    expect(text(panel)).toContain("Cold work unavailable");
    expect(text(panel.querySelector("[data-domain-action-refusal-message]"))).toBe("You do not have access to this site.");
    expect(text(main.querySelector("h1"))).toBe("Action");
    expect(main.querySelector("[data-domain-action-crumb-code]")).toBeNull();
    expect(main.querySelector("[data-domain-action-notice]")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(attempts).toBe(2));
    expect(fetchRecord).toEqual([]);
  });

  it("redirects a bare or legacy address for a domain ID to /verification, preserving known_at (direct reload)", async () => {
    for (const path of [`/sites/${SITE}/actions/${DOMAIN_ID}`, `/sites/${SITE}/actions/${DOMAIN_ID}/history`, `/sites/${SITE}/actions/${DOMAIN_ID}/plan`]) {
      const { client } = domainClient(() => ({ status: "loaded", value: indexBody([]) }));
      await mountAction(`${path}?known_at=${encodeURIComponent(KNOWN)}`, client);
      await waitFor(() => expect(where()).toBe(`/sites/${SITE}/actions/${DOMAIN_ID}/verification?known_at=${encodeURIComponent(KNOWN)}`));
      await settledScreen();
      expect(document.querySelector('[data-domain-action-shell="loaded"]')).not.toBeNull();
      cleanup();
    }
  });

  it("keeps a W1 ID on a cold Site on the W1 detail at its bare address (both IDs on one cold Site)", async () => {
    stubFetch(() => json(404, { detail: { code: "ACTION_NOT_FOUND", message: "No such Action." } }));
    const { client, detailCalls } = domainClient(
      () => ({ status: "loaded", value: indexBody([]) }),
      (id) =>
        id === DOMAIN_ID
          ? { status: "loaded", value: detailBody() }
          : { status: "not_found", http: 404, code: "ACTION_NOT_FOUND", message: "Action was not found at this site." },
    );
    await mountAction(`/sites/${SITE}/actions/${W1_ID}`, client);
    expect(detailCalls[0].id).toBe(W1_ID);
    expect(where()).toBe(`/sites/${SITE}/actions/${W1_ID}`);
    expect(document.querySelector("[data-domain-action-shell]")).toBeNull();
    expect(fetchRecord.some((u) => u.includes(`/api/sites/${SITE}/actions/${W1_ID}`))).toBe(true);
    expect(document.querySelector(`nav[aria-label="${OPERATOR_SITE_TABS_LABEL}"]`)).not.toBeNull();
    cleanup();
    await mountAction(`/sites/${SITE}/actions/${DOMAIN_ID}`, client);
    await waitFor(() => expect(where()).toBe(`/sites/${SITE}/actions/${DOMAIN_ID}/verification`));
  });

  it("a refused (503) domain probe on a bare or legacy address keeps the W1 presenter at its original address (ruling 8)", async () => {
    stubFetch(() => json(404, { detail: { code: "ACTION_NOT_FOUND", message: "No such Action." } }));
    for (const path of [`/sites/${SITE}/actions/${W1_ID}`, `/sites/${SITE}/actions/${W1_ID}/history`, `/sites/${SITE}/actions/${DOMAIN_ID}`]) {
      const { client, detailCalls } = domainClient(
        () => ({ status: "loaded", value: indexBody([]) }),
        () => ({ status: "refused", http: 503, code: "WORK_STORE_UNAVAILABLE", message: "Work records are unavailable right now." }),
      );
      await mountAction(path, client);
      expect(detailCalls).toHaveLength(1);
      expect(where()).toBe(path);
      expect(document.querySelector("[data-domain-action-shell]")).toBeNull();
      expect(document.querySelector("[data-domain-action-probe]")).toBeNull();
      expect(document.body.textContent).not.toContain("Cold work unavailable");
      cleanup();
    }
  });

  it("a W1 ID on the domain /verification address is not found, never the W1 presenter (ruling 8)", async () => {
    stubFetch(() => json(200, {}));
    const { client } = domainClient(
      () => ({ status: "loaded", value: indexBody([]) }),
      () => ({ status: "not_found", http: 404, code: "ACTION_NOT_FOUND", message: "Action was not found at this site." }),
    );
    const main = await mountAction(`/sites/${SITE}/actions/${W1_ID}/verification`, client);
    expect(where()).toBe(`/sites/${SITE}/actions/${W1_ID}/verification`);
    expect(text(main.querySelector('[data-domain-action-panel="not-found"]'))).toBe("Action was not found at this site.");
    expect(fetchRecord).toEqual([]);
    expect(document.querySelector(`nav[aria-label="${OPERATOR_SITE_TABS_LABEL}"]`)).toBeNull();
  });

  it("a mini-grid Site never reads the domain Action", async () => {
    stubFetch(() => json(404, { detail: { code: "ACTION_NOT_FOUND", message: "No such Action." } }));
    const { client, detailCalls } = domainClient(() => ({ status: "loaded", value: indexBody([]) }));
    await mountAction(`/sites/${SITE}/actions/${DOMAIN_ID}/verification`, client, { ...HYBRID_MINI_GRID_SITE, site_id: SITE } as SiteDetailReadModel);
    expect(detailCalls).toEqual([]);
    expect(document.querySelector("[data-domain-action-shell]")).toBeNull();
  });
});
