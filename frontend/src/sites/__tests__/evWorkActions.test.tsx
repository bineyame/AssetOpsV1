/**
 * W5-04 V2a (`.agent/W5-04-build-spec.md` V2a card, "Mock element, table cells and copy ledger"; readiness rulings 14,
 * 17-20, 39, 44-46): the EV_CHARGING Site > Work > Actions tab over the union Site Action index, against the v69
 * `ev-work` mock (`index.html:334-343`). Pure component fixtures shaped from the as-built V1b wire (ruling 39); no
 * producer-backed claim is made here.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteWorkCasesFrame, SiteWorkFrame } from "../../shell/SiteAnalyticsFrames";
import { expectV69Panels } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import {
  COLD_WORK_UNEXPECTED,
  COLD_WORK_UNREACHABLE,
  EV_WORK_UNEXPECTED,
  EV_WORK_UNREACHABLE,
  createDomainActionClient,
  type DomainActionClient,
  type DomainIndexResult,
  type DomainIndexScope,
} from "../domainActionClient";
import { evActionCount } from "../evWorkPresentation";
import { WORK_CONTEXT_NOTICE, WORK_CONTEXT_NOTICE_DOMAIN } from "../siteWorkCases";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { WorkClient, WorkScope } from "../workClient";
import { defaultWorkWindow } from "../workClient";
import {
  EV_ACTION_ID,
  EV_FINDING,
  EV_FINDING_REV,
  EV_FROM,
  EV_KNOWN,
  EV_SITE,
  EV_SITE_CODE,
  EV_SUMMARY,
  EV_TO,
  EV_W1_ID,
  evIndexBody,
  evPinUnavailableRow,
  evRow,
  evRows,
  evW1Row,
} from "./evWorkFixtures";

type IndexCall = { siteCode: string; scope: DomainIndexScope; siteType: string | undefined };

function domainClient(index: (scope: DomainIndexScope) => DomainIndexResult | Promise<DomainIndexResult>) {
  const calls: IndexCall[] = [];
  const client: DomainActionClient = {
    getIndex: vi.fn(async (siteCode: string, scope: DomainIndexScope, siteType?: string) => {
      calls.push({ siteCode, scope, siteType });
      return index(scope);
    }),
    getDetail: vi.fn(async () => ({ status: "refused" as const, http: 503, code: null, message: "not used" })),
  };
  return { client, calls };
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
const detail: SiteDetailClient = { getSite: async () => ({ status: "loaded", site: EV_SITE }) } as unknown as SiteDetailClient;

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}
const where = () => screen.getByTestId("where").textContent ?? "";
const text = (el: Element | null | undefined) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const setDate = (input: Element | null, value: string) => fireEvent.change(input as HTMLInputElement, { target: { value } });
const workPath = (query = `from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}&known_at=${encodeURIComponent(EV_KNOWN)}`) =>
  `/sites/${EV_SITE_CODE}/work?${query}`;
const loaded = (value: ReturnType<typeof evIndexBody>): DomainIndexResult => ({ status: "loaded", value });

async function mountWork(path: string, domain: DomainActionClient) {
  const work = workClient();
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/sites/:siteId/work"
          element={
            <>
              <SiteWorkFrame detail={detail} sitesPath="/sites" actionIndex={neverActionIndex} workClient={work.client} domainActions={domain} />
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

/** Every attribute name in the subtree (EV must carry no cold-named attribute or class; ruling 45). */
function coldNames(root: Element): string[] {
  const out: string[] = [];
  for (const el of [root, ...Array.from(root.querySelectorAll("*"))]) {
    for (const attr of Array.from(el.attributes)) {
      if (attr.name.startsWith("data-cold-work")) out.push(attr.name);
      if (attr.name === "class" && /\bcold-work/.test(attr.value)) out.push(`class=${attr.value}`);
      if (attr.name === "data-disclosure" && attr.value.startsWith("cold-work")) out.push(`disclosure=${attr.value}`);
    }
  }
  return out;
}

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

/* ---------- domainActionClient: the EV index parser (ruling 46) and fallback sentences (ruling 44) ---------- */

describe("domainActionClient EV index (rulings 44, 46)", () => {
  const scope: DomainIndexScope = { from: EV_FROM, to: EV_TO, knownAt: EV_KNOWN, cursor: null };

  it("parses an EV row (string title, OPEN) as a domain Action beside a W1 row; one EV row never invalidates the index", async () => {
    stubFetch(() => json(200, evIndexBody([evRow(), evW1Row()])));
    const result = await createDomainActionClient().getIndex(EV_SITE_CODE, scope, "EV_CHARGING");
    expect(result.status).toBe("loaded");
    if (result.status !== "loaded") return;
    expect(result.value.rows.map((r) => [r.domain, r.state])).toEqual([
      ["EV_CHARGING", "OPEN"],
      ["MINIGRID", expect.objectContaining({ application: "PENDING" })],
    ]);
    expect(new URL(fetchRecord[0], "http://x").pathname).toBe(`/api/sites/${EV_SITE_CODE}/domain-work/action-index`);
  });

  it("refuses an EV row that breaks the domain shape (null title, W1 state, history link)", async () => {
    for (const row of [
      evRow({ title: null }),
      evRow({ state: { application: "PENDING", failed_attempts: 0 } as never }),
      evRow({ links: { action: `/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification`, history: "/h" } }),
    ]) {
      stubFetch(() => json(200, evIndexBody([row])));
      expect(await createDomainActionClient().getIndex(EV_SITE_CODE, scope, "EV_CHARGING")).toEqual({
        status: "refused",
        http: 200,
        code: null,
        message: EV_WORK_UNEXPECTED,
      });
    }
  });

  it("uses the EV network and malformed-200 sentences on an EV Site and keeps the cold sentences byte-for-byte otherwise", async () => {
    stubFetch(() => json(200, { nothing: true }));
    expect(await createDomainActionClient().getIndex(EV_SITE_CODE, scope, "EV_CHARGING")).toMatchObject({ message: EV_WORK_UNEXPECTED });
    expect(await createDomainActionClient().getIndex(EV_SITE_CODE, scope)).toMatchObject({ message: COLD_WORK_UNEXPECTED });
    expect(await createDomainActionClient().getIndex(EV_SITE_CODE, scope, "COLDCHAIN")).toMatchObject({ message: COLD_WORK_UNEXPECTED });
    stubFetch(() => json(503, { nothing: true }));
    expect(await createDomainActionClient().getIndex(EV_SITE_CODE, scope, "EV_CHARGING")).toEqual({ status: "refused", http: 503, code: null, message: EV_WORK_UNEXPECTED });
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("network");
    });
    expect(await createDomainActionClient().getIndex(EV_SITE_CODE, scope, "EV_CHARGING")).toEqual({ status: "refused", http: null, code: null, message: EV_WORK_UNREACHABLE });
    expect(await createDomainActionClient().getIndex(EV_SITE_CODE, scope)).toEqual({ status: "refused", http: null, code: null, message: COLD_WORK_UNREACHABLE });
    expect(EV_WORK_UNREACHABLE).toBe("The EV work read could not be reached.");
    expect(EV_WORK_UNEXPECTED).toBe("The EV work read answered in an unexpected shape.");
  });
});

/* ---------- Site > Work > Actions on an EV_CHARGING Site ---------- */

describe("EV Site Actions tab (v69 ev-work)", () => {
  it("renders the mock strip, six columns and the positive EV row with its live selected Action link (R113 closed in V4a)", async () => {
    const { client, calls } = domainClient(() => loaded(evIndexBody([evRow()])));
    const { main } = await mountWork(workPath(), client);
    expectV69Panels("ev-work");
    expect(main.querySelector("h1")?.textContent).toContain("EV charging lab");
    // Ruling 20 / R78: the generic subtitle, always.
    expect(main.textContent).toContain("EV charging operations at this site.");
    expect(main.textContent).not.toContain("Depot");
    const strip = main.querySelector("[data-domain-work-strip]");
    // Ruling 19 / R79: singular `1 action`; R111: the stored Site name's short name.
    expect(text(strip?.querySelector("[data-site-work-scope]"))).toBe("Scoped to EV · 1 action");
    expect(text(strip)).toContain("EV Actions recorded at this site");
    expect(text(strip)).toContain("Global Actions does not include EV Actions yet.");
    expect(text(strip)).not.toContain("Manage in Actions");
    expect(strip?.querySelector("a")).toBeNull();
    expect(Array.from(main.querySelectorAll("thead th")).map(text)).toEqual(["Action", "Source", "Owner", "Due", "State", "Success criterion"]);
    expect(main.querySelector(".panel__description")?.textContent).toBe("Due dates are not yet set");

    const row = main.querySelector(`[data-domain-work-row="${EV_ACTION_ID}"]`) as HTMLElement;
    expect(row.getAttribute("data-domain-work-domain")).toBe("EV_CHARGING");
    const cells = Array.from(row.querySelectorAll("td"));
    // Ruling 46 / R113: V4a mounts the EV detail route and EV_ACTION_LINK_LIVE turns the selected `links.action` live.
    const link = cells[0].querySelector("a");
    expect(link?.getAttribute("href")).toBe(`/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification`);
    expect(link?.getAttribute("data-domain-work-action-link")).toBe("domain");
    expect(text(link)).toBe("ACT-000061 · Investigate connector 2");
    expect(cells[0].querySelector("[data-domain-work-action-plain]")).toBeNull();
    expect(text(cells[2])).toBe("Charging operations");
    expect(text(cells[3])).toBe("Not set");
    expect(cells[4].querySelector(".w1f4-action-badge--amber")?.textContent).toBe("Open");
    expect(text(cells[5])).toBe(EV_SUMMARY);
    expect(Array.from(main.querySelectorAll("a")).filter((a) => (a.getAttribute("href") ?? "").includes(`/actions/${EV_ACTION_ID}`))).toHaveLength(1);

    const notice = main.querySelector("[data-domain-work-notice]");
    expect(notice?.textContent).toBe(WORK_CONTEXT_NOTICE_DOMAIN);
    expect(main.textContent).not.toContain(WORK_CONTEXT_NOTICE);
    expect(main.textContent).not.toContain("global create flow");
    // The read carries the EV Site type (ruling 44) at the URL window and cutoff, page one.
    expect(calls.find((c) => c.scope.cursor === null && c.siteType === "EV_CHARGING")?.scope).toEqual({
      from: EV_FROM,
      to: EV_TO,
      knownAt: EV_KNOWN,
      cursor: null,
    });
    const { violations } = scanProductVocabulary(main, "ev-work");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("carries data-domain-work-* only: no cold-named attribute, class or disclosure on the EV surface (ruling 45)", async () => {
    const { client } = domainClient(() => loaded(evIndexBody(evRows(5))));
    const { main } = await mountWork(workPath(), client);
    expect(coldNames(main)).toEqual([]);
    expect(main.getAttribute("data-domain-work-page")).toBe("actions");
    expect(main.querySelector("[data-domain-work='actions']")).not.toBeNull();
    expect(main.querySelector("form[data-domain-work-window]")).not.toBeNull();
    expect(main.querySelector(".domain-work-actions")).not.toBeNull();
  });

  it("shows the Source as plain `Finding {id8}` with the revision and the unavailable exact-revision note (R74/R75)", async () => {
    const { client } = domainClient(() => loaded(evIndexBody([evRow()])));
    const { main } = await mountWork(workPath(), client);
    const source = main.querySelector(`[data-domain-work-row="${EV_ACTION_ID}"] td:nth-child(2)`) as HTMLElement;
    expect(source.querySelector("a")).toBeNull();
    expect(text(source.querySelector("[data-domain-work-source]"))).toBe(`Finding ${EV_FINDING.slice(0, 8)}`);
    const details = source.querySelector("details") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(text(details.querySelector("summary"))).toBe("Finding version");
    expect(details.querySelector("[data-domain-work-revision]")?.textContent).toBe(EV_FINDING_REV);
    expect(text(details.querySelector("[data-domain-work-source-unavailable]"))).toBe("The selected Finding revision cannot be opened here yet.");
    expect(Array.from(main.querySelectorAll("a")).some((a) => (a.getAttribute("href") ?? "").includes("revision_id"))).toBe(false);
  });

  it("counts one and many with the EV grammar (ruling 19)", async () => {
    expect(evActionCount(0)).toBe("0 actions");
    expect(evActionCount(1)).toBe("1 action");
    expect(evActionCount(3)).toBe("3 actions");
    const { client } = domainClient(() => loaded(evIndexBody(evRows(3))));
    const { main } = await mountWork(workPath(), client);
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to EV · 3 actions");
  });

  it("shows the exact mock successful zero, with no table and a zero count (pre-flight 27)", async () => {
    const { client } = domainClient(() => loaded(evIndexBody([])));
    const { main } = await mountWork(workPath(), client);
    expectV69Panels("ev-work");
    const empty = main.querySelector("[data-domain-work-empty]");
    expect(text(empty?.querySelector("h3"))).toBe("No actions at this site");
    expect(text(empty?.querySelector("p"))).toBe("No accepted recommendation or evidence request has been raised here yet.");
    expect(main.querySelector("table")).toBeNull();
    expect(main.querySelector(".panel__description")).toBeNull();
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to EV · 0 actions");
    expect(main.querySelector("[data-domain-work-currentness]")).toBeNull();
  });

  it("drops the due subtitle when a row has a due date and shows the stored fallbacks", async () => {
    const { client } = domainClient(() =>
      loaded(evIndexBody([evRow({ due_at: "2026-10-20T00:00:00Z", owner_label: null, criterion_summary: null })])),
    );
    const { main } = await mountWork(workPath(), client);
    expect(main.querySelector(".panel__description")).toBeNull();
    const cells = Array.from(main.querySelectorAll(`[data-domain-work-row="${EV_ACTION_ID}"] td`));
    expect(text(cells[2])).toBe("Not assigned");
    expect(text(cells[3])).toBe("2026-10-20");
    expect(text(cells[5])).toBe("No success criterion declared");
  });

  it("keeps a W1 row's own title, state and W1 link beside the linked EV row (pre-flight 28)", async () => {
    const { client } = domainClient(() => loaded(evIndexBody([evRow(), evW1Row()])));
    const { main } = await mountWork(workPath(), client);
    const w1 = main.querySelector(`[data-domain-work-row="${EV_W1_ID}"]`) as HTMLElement;
    const cells = Array.from(w1.querySelectorAll("td"));
    expect(text(cells[0].querySelector("a"))).toBe("ACT-000060");
    expect(cells[0].querySelector("a")?.getAttribute("href")).toBe(`/sites/${EV_SITE_CODE}/actions/${EV_W1_ID}`);
    expect(text(cells[4])).toBe("Accepted · not applied");
    expect(text(cells[5])).toBe("No success criterion declared");
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to EV · 2 actions");
    expect(main.querySelector(`[data-domain-work-row="${EV_ACTION_ID}"] td a`)?.getAttribute("href")).toBe(
      `/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification`,
    );
  });

  it("places the selected-state notice between strip and panel with the R104 tones; none on CURRENT (R80)", async () => {
    const cases: [string, string, string][] = [
      ["HISTORICAL", "blue", "Read as of 2026-10-06 12:00 UTC. Later work may differ."],
      ["PENDING_RECOMPUTE", "amber", "Linked evidence is being reassessed. The work record remains recorded."],
      ["STALE_SOURCE", "amber", "Linked evidence source is out of date. The work record remains recorded."],
      ["UNKNOWN", "blue", "No selected source for linked evidence. The work record remains recorded."],
    ];
    for (const [status, tone, sentence] of cases) {
      const { client } = domainClient(() => loaded(evIndexBody([evRow()], { status: status as never })));
      const { main } = await mountWork(workPath(), client);
      const notice = main.querySelector("[data-domain-work-currentness]") as HTMLElement;
      expect(notice.getAttribute("data-domain-work-currentness")).toBe(status);
      expect(text(notice)).toBe(sentence);
      // R104: blue info for Historical/Unknown, amber (non-blue) for Pending recompute/Stale source.
      expect(notice.classList.contains("v69-notice--blue")).toBe(tone === "blue");
      expect(notice.previousElementSibling?.hasAttribute("data-domain-work-strip")).toBe(true);
      expect(notice.nextElementSibling?.matches("section.panel, .panel")).toBe(true);
      expectV69Panels("ev-work");
      cleanup();
    }
  });

  it("refuses 403/503 as `EV work unavailable` with the server message and Retry; no zero, no empty copy", async () => {
    for (const [http, code, message] of [
      [403, "SITE_SCOPE_FORBIDDEN", "You do not have access to this site."],
      [503, "WORK_STORE_UNAVAILABLE", "Work store unavailable."],
    ] as const) {
      let n = 0;
      const { client, calls } = domainClient(() => {
        n += 1;
        return { status: "refused", http, code, message };
      });
      const { main } = await mountWork(workPath(), client);
      const state = main.querySelector("[data-domain-work-state-panel='refused']") as HTMLElement;
      expect(state.getAttribute("data-domain-work-refusal")).toBe(code);
      expect(text(state)).toContain("EV work unavailable");
      expect(text(state.querySelector("[data-domain-work-refusal-message]"))).toBe(message);
      expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to EV · — actions");
      expect(main.textContent).not.toContain("No actions at this site");
      expect(main.textContent).not.toContain("0 actions");
      const before = calls.length;
      fireEvent.click(state.querySelector("[data-domain-work-retry]") as HTMLButtonElement);
      await waitFor(() => expect(calls.length).toBeGreaterThan(before));
      expect(n).toBeGreaterThan(1);
      cleanup();
    }
  });

  it("shows the EV network sentence through the real client on an EV Site (ruling 44)", async () => {
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("network");
    });
    const { main } = await mountWork(workPath(), createDomainActionClient());
    await waitFor(() => expect(main.querySelector("[data-domain-work-refusal-message]")).not.toBeNull());
    expect(text(main.querySelector("[data-domain-work-refusal-message]"))).toBe("The EV work read could not be reached.");
    expect(main.textContent).not.toContain("cold work read");
  });

  it("folds a five-row page after four rows behind `Show all 5 Actions` (R108)", async () => {
    const { client } = domainClient(() => loaded(evIndexBody(evRows(5))));
    const { main } = await mountWork(workPath(), client);
    const rows = Array.from(main.querySelectorAll("tbody tr")) as HTMLElement[];
    expect(rows.map((r) => r.hidden)).toEqual([false, false, false, false, true]);
    const showAll = main.querySelector("[data-domain-work-show-all]") as HTMLButtonElement;
    expect(text(showAll)).toBe("Show all 5 Actions");
    fireEvent.click(showAll);
    expect((Array.from(main.querySelectorAll("tbody tr")) as HTMLElement[]).every((r) => !r.hidden)).toBe(true);
  });

  it("defaults to the seven complete UTC days without a window (R-9) and the subrow carries from,to,known_at", async () => {
    const { client, calls } = domainClient(() => loaded(evIndexBody([evRow()])));
    const { main, work } = await mountWork(`/sites/${EV_SITE_CODE}/work?known_at=${encodeURIComponent(EV_KNOWN)}`, client);
    const expected = defaultWorkWindow();
    expect(calls.some((c) => c.scope.from === expected.from && c.scope.to === expected.to && c.scope.knownAt === EV_KNOWN)).toBe(true);
    const form = main.querySelector("[data-domain-work-window]") as HTMLFormElement;
    expect((form.querySelector("[data-domain-work-window-from]") as HTMLInputElement).value).toBe(expected.from.slice(0, 10));
    expect((form.querySelector("[data-domain-work-window-to]") as HTMLInputElement).value).toBe(expected.to.slice(0, 10));
    const subtabs = Array.from(main.querySelectorAll(".site-subtabs a")).map((a) => a.getAttribute("href") ?? "");
    for (const href of subtabs) {
      const url = new URL(href, "http://x");
      expect(url.searchParams.get("from")).toBe(expected.from);
      expect(url.searchParams.get("to")).toBe(expected.to);
      expect(url.searchParams.get("known_at")).toBe(EV_KNOWN);
      expect(url.searchParams.get("cursor")).toBeNull();
    }
    // The subrow's W4 case counts read the same window and cutoff.
    await waitFor(() => expect(work.calls.length).toBe(2));
    for (const call of work.calls) expect(call.scope).toMatchObject({ from: expected.from, to: expected.to, knownAt: EV_KNOWN });
    await waitFor(() => expect(text(main.querySelector(".site-subtabs a[aria-current='page']"))).toBe("Actions (1)"));
  });

  it("applies a window keeping known_at and dropping the cursor; an invalid window reads nothing (ruling 14, R112)", async () => {
    const { client, calls } = domainClient(() => loaded(evIndexBody([evRow()])));
    const { main } = await mountWork(workPath(`${new URLSearchParams({ from: EV_FROM, to: EV_TO, known_at: EV_KNOWN, cursor: "c9" })}`), client);
    const form = main.querySelector("[data-domain-work-window]") as HTMLFormElement;
    expect(text(form)).toContain("From (UTC)");
    expect(text(form)).toContain("To (UTC, exclusive)");
    const before = calls.length;
    setDate(form.querySelector("[data-domain-work-window-from]"), "2026-09-01");
    setDate(form.querySelector("[data-domain-work-window-to]"), "2026-10-03");
    fireEvent.click(form.querySelector("[data-domain-work-window-apply]") as HTMLButtonElement);
    expect(text(form.querySelector("[data-domain-work-window-error]"))).toBe("The window may span at most 31 days.");
    expect(calls.length).toBe(before);
    setDate(form.querySelector("[data-domain-work-window-from]"), "2026-10-01");
    setDate(form.querySelector("[data-domain-work-window-to]"), "2026-10-08");
    fireEvent.click(form.querySelector("[data-domain-work-window-apply]") as HTMLButtonElement);
    await waitFor(() => expect(where()).toContain("from=2026-10-01"));
    const url = new URL(where(), "http://x");
    expect(url.searchParams.get("from")).toBe("2026-10-01T00:00:00Z");
    expect(url.searchParams.get("to")).toBe("2026-10-08T00:00:00Z");
    expect(url.searchParams.get("known_at")).toBe(EV_KNOWN);
    expect(url.searchParams.get("cursor")).toBeNull();
  });
});

/* ---------- V2a review Low-3 and ruling 53: pager, 409 restart and the pinned Source ---------- */

describe("EV Actions pager, changed basis and pinned Source (review Low-3, ruling 53)", () => {
  it("Next page pins the response known_at and First page drops the cursor", async () => {
    const { client } = domainClient(() => loaded(evIndexBody(evRows(5), { total_count: 7, next_cursor: "next1" })));
    const { main } = await mountWork(workPath(`from=${encodeURIComponent(EV_FROM)}&to=${encodeURIComponent(EV_TO)}&cursor=prev`), client);
    expect(text(main.querySelector("[data-site-work-scope]"))).toBe("Scoped to EV · 7 actions");
    const next = new URL(main.querySelector("[data-domain-work-next]")?.getAttribute("href") ?? "", "http://x");
    expect(next.searchParams.get("cursor")).toBe("next1");
    expect(next.searchParams.get("known_at")).toBe(EV_KNOWN);
    expect(next.searchParams.get("limit")).toBeNull();
    const first = new URL(main.querySelector("[data-domain-work-first]")?.getAttribute("href") ?? "", "http://x");
    expect(first.searchParams.get("cursor")).toBeNull();
    expect(first.searchParams.get("from")).toBe(EV_FROM);
    expect(first.searchParams.get("to")).toBe(EV_TO);
  });

  it("restarts page one without the stale cursor after a 409 WORK_BASIS_CHANGED, keeping known_at", async () => {
    const { client, calls } = domainClient((scope) =>
      scope.cursor
        ? { status: "basis_changed", http: 409, code: "WORK_BASIS_CHANGED", message: "The work list changed; request page one without a cursor." }
        : loaded(evIndexBody([evRow()])),
    );
    const { main } = await mountWork(workPath(`${new URLSearchParams({ from: EV_FROM, to: EV_TO, known_at: EV_KNOWN, cursor: "stale" })}`), client);
    const panel = main.querySelector("[data-domain-work-refusal]") as HTMLElement;
    expect(panel.getAttribute("data-domain-work-refusal")).toBe("WORK_BASIS_CHANGED");
    expect(text(panel)).toContain("EV work unavailable");
    expect(text(panel)).toContain("The work list changed; request page one without a cursor.");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(where()).not.toContain("cursor"));
    expect(new URL(where(), "http://x").searchParams.get("known_at")).toBe(EV_KNOWN);
    await settledScreen();
    expect(calls.at(-1)?.scope.cursor).toBeNull();
    expect(main.querySelector(`[data-domain-work-row="${EV_ACTION_ID}"]`)).not.toBeNull();
  });

  it("shows the selected row Source as supplied, pinned or unavailable, with no list/detail disagreement copy (ruling 53)", async () => {
    for (const [row, status] of [
      [evRow(), "CURRENT"],
      [evPinUnavailableRow(), "UNKNOWN"],
    ] as const) {
      const { client } = domainClient(() => loaded(evIndexBody([row], { status })));
      const { main } = await mountWork(workPath(), client);
      const source = main.querySelector(`[data-domain-work-row="${EV_ACTION_ID}"] td:nth-child(2)`) as HTMLElement;
      expect(source.querySelector("a")).toBeNull();
      expect(text(source.querySelector("[data-domain-work-source]"))).toBe(`Finding ${EV_FINDING.slice(0, 8)}`);
      expect(source.querySelector("[data-domain-work-revision]")?.textContent).toBe(EV_FINDING_REV);
      expect(main.querySelector("[data-domain-work-currentness]") === null).toBe(status === "CURRENT");
      expect(main.textContent ?? "").not.toMatch(/differ from the detail|disagree/i);
      cleanup();
    }
  });
});

/* ---------- The EV case tabs' shared Work chrome (V2a scope only; V3a owns the case cells) ---------- */

describe("EV Work case tabs: subtitle and subrow (ruling 45, R78)", () => {
  it("reads the Actions count from the union index at the URL cutoff and shows the EV subtitle", async () => {
    const { client, calls } = domainClient(() => loaded(evIndexBody([evRow()])));
    const work = workClient();
    render(
      <MemoryRouter initialEntries={[`/sites/${EV_SITE_CODE}/work/incidents?${new URLSearchParams({ from: EV_FROM, to: EV_TO, known_at: EV_KNOWN })}`]}>
        <Routes>
          <Route
            path="/sites/:siteId/work/incidents"
            element={<SiteWorkCasesFrame detail={detail} sitesPath="/sites" kind="incidents" workClient={work.client} actionIndex={neverActionIndex} domainActions={client} />}
          />
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
    const main = document.querySelector("main") as HTMLElement;
    expect(main.textContent).toContain("EV charging operations at this site.");
    await waitFor(() => expect(calls.length).toBeGreaterThan(0));
    expect(calls[0]).toEqual({ siteCode: EV_SITE_CODE, scope: { from: EV_FROM, to: EV_TO, knownAt: EV_KNOWN, cursor: null }, siteType: "EV_CHARGING" });
    await waitFor(() => expect(text(main.querySelector(".site-subtabs a"))).toBe("Actions (1)"));
    const href = main.querySelector(".site-subtabs a")?.getAttribute("href") ?? "";
    expect(new URL(href, "http://x").searchParams.get("known_at")).toBe(EV_KNOWN);
    expect(coldNames(main)).toEqual([]);
    // Ruling 57 interim: subrow only in V2a; the EV case tab keeps its single W4 window form and has no page-local
    // Window until V3a mounts it together with `windowForm=false`.
    expect(main.querySelector("[data-domain-work-window]")).toBeNull();
    expect(main.querySelectorAll("form").length).toBe(1);
  });
});
