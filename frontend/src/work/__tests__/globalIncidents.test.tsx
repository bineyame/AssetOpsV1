/**
 * W6-01a A2: the global Incidents root (`.agent/W6-01-build-spec.md` section 2 and section 3.1 A2Q1-A2Q10, CL3-1).
 * Typed responses only: the persisted positive, zero, historical, refused and cursor-changed states are captured
 * against the real API in `.agent/W6-01-evidence/A2/`; `No accessible Sites.` is proven here only (A1Q2 R4).
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { INCIDENTS_PATH } from "../../shell/operatorSiteRoutes";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { GlobalIncidentsFrame } from "../GlobalIncidents";
import {
  createGlobalWorkClient,
  defaultGlobalWorkWindow,
  globalWorkPageQuery,
  type GlobalIncidentRow,
  type GlobalIncidentsBody,
  type GlobalWorkClient,
  type GlobalWorkQuery,
  type GlobalWorkResult,
} from "../globalWorkClient";

const FROM = "2026-10-14T00:00:00Z";
const TO = "2026-10-21T00:00:00Z";
const KNOWN = "2026-10-21T12:00:00Z";
const PAGE = `/incidents?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;
const SITE_INCIDENTS = `/sites/KOBO-001/work/incidents?from=2026-10-14T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&known_at=2026-10-21T12%3A00%3A00Z`;
const TITLE200 = "Backupgeneratorautomaticstartfailure".repeat(6).slice(0, 200);
const OWNER128 = "Fieldmaintenancesupervisorteam".repeat(5).slice(0, 128);

function row(n: number, over: Partial<GlobalIncidentRow> = {}): GlobalIncidentRow {
  return {
    site_code: "KOBO-001",
    site_name: "Kobo",
    site_id: "00000000-0000-4000-8000-000000000002",
    site_code_key: "kobo-001",
    case_id: `00000000-0000-4000-8000-${String(100 + n).padStart(12, "0")}`,
    code: `INC-${String(n).padStart(6, "0")}`,
    kind: "INCIDENT",
    revision_id: `00000000-0000-4000-8000-${String(200 + n).padStart(12, "0")}`,
    title: `Stress incident ${n}`,
    narrative: "Operator reported a stop; cause not established.",
    occurred_at: "2026-10-19T09:00:00Z",
    created_at: "2026-10-21T11:59:00Z",
    recorded_at: "2026-10-21T11:59:00Z",
    state: "OPEN",
    owner: null,
    asset_id: null,
    asset_label: null,
    incident_id: null,
    linked_request_codes: [],
    finding_links: [],
    action_links: [],
    source_provenance: {
      classification: "UNKNOWN",
      state: "UNKNOWN",
      source_ids: [],
      evidence_ids: [],
      basis_sha256: `sha256:${"0".repeat(64)}`,
      reasons: [],
    },
    links: { site: { label: "Kobo", href: "/sites/KOBO-001" }, site_incidents: { label: "Site incidents", href: SITE_INCIDENTS } },
    ...over,
  };
}

function body(rows: GlobalIncidentRow[], over: Partial<GlobalIncidentsBody> = {}): GlobalIncidentsBody {
  return {
    schema_version: "global-work-index-1",
    scope: { tenant_id: "00000000-0000-4000-8000-000000000001", authorized_site_count: 2, covered_site_count: 2, access_basis: "sha256:x" },
    window: { from: FROM, to: TO, bounds: "[from, to)" },
    known_at: KNOWN,
    status: "CURRENT",
    coverage: { state: "COMPLETE", reason: null, sites: [] },
    total_count: rows.length,
    state_counts: { OPEN: rows.length, IN_PROGRESS: 0, CLOSED: 0 },
    rows,
    next_cursor: null,
    selection_token: "sha256:token",
    ...over,
  };
}

type Answer = GlobalWorkResult<GlobalIncidentsBody>;

/** A typed client: answers by cursor (null is page one); records every query it is asked. */
function client(answers: Record<string, Answer>, gate?: Promise<void>): GlobalWorkClient & { calls: GlobalWorkQuery[] } {
  const calls: GlobalWorkQuery[] = [];
  return {
    calls,
    async incidents(query) {
      calls.push(query);
      if (gate) await gate;
      const answer = answers[query.cursor ?? "page-one"];
      if (answer === undefined) throw new Error(`no answer for ${JSON.stringify(query)}`);
      return answer;
    },
  };
}

const loaded = (value: GlobalIncidentsBody): Answer => ({ status: "loaded", value });

function Where() {
  const location = useLocation();
  return (
    <output data-testid="where" data-trail={JSON.stringify((location.state as { globalWorkTrail?: unknown } | null)?.globalWorkTrail ?? null)}>
      {`${location.pathname}${location.search}`}
    </output>
  );
}

function mount(path: string, reads: GlobalWorkClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={INCIDENTS_PATH} element={<GlobalIncidentsFrame client={reads} />} />
      </Routes>
      <Where />
    </MemoryRouter>,
  );
}

/** The loading sentence is outside `settledScreen`'s list, so wait for its element too. */
async function settled() {
  await waitFor(() => expect(document.querySelector("[data-global-work-loading]")).toBeNull());
  await settledScreen();
}

const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const cards = () => document.querySelector("[data-global-work-cards]");
const cell = (tr: Element, i: number) => tr.querySelectorAll("td")[i] as HTMLElement;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W6-01a A2: global Incidents", () => {
  it("renders the mock panels, cards, cells and pager over a typed five-row page", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const rows = [
      row(1, { title: TITLE200, owner: OWNER128, state: "IN_PROGRESS" }),
      row(2, {
        state: "CLOSED",
        finding_links: [{ label: "Finding a1b2c3d4", href: "/sites/KOBO-001/findings/f1?revision_id=r1" }],
        action_links: [{ label: "Action e5f6a7b8", href: null }],
        linked_request_codes: ["WR-000007", "WR-000008"],
        source_provenance: { ...row(2).source_provenance, classification: "AUTHORED_DEMONSTRATION" },
      }),
      row(3, { linked_request_codes: ["WR-000009"] }),
      row(4, { source_provenance: { ...row(4).source_provenance, classification: "REGISTERED_SIMULATION" } }),
      row(5, { source_provenance: { ...row(5).source_provenance, classification: "MIXED" } }),
    ];
    const reads = client(
      {
        "page-one": loaded(body(rows, { total_count: 6, state_counts: { OPEN: 4, IN_PROGRESS: 1, CLOSED: 1 }, next_cursor: "CURSOR-2" })),
        "CURSOR-2": loaded(body([row(6)], { total_count: 6, state_counts: { OPEN: 4, IN_PROGRESS: 1, CLOSED: 1 } })),
      },
      gate,
    );
    mount(PAGE, reads);

    // CL3-1: the loading sentence stands in for the cards and table body; the heading and controls stay.
    expect(text(document.querySelector("[data-global-work-loading]"))).toBe("Loading the incidents across the estate.");
    expect(screen.getByRole("heading", { level: 1, name: "Incidents" })).toBeInTheDocument();
    expect(document.querySelector("[data-global-work-controls]")).not.toBeNull();
    expect(cards()).toBeNull();
    expect(document.querySelector("table")).toBeNull();
    release();
    await settled();

    expect(reads.calls).toEqual([{ from: FROM, to: TO, known_at: null, cursor: null }]);
    expectV69Panels("incidents");
    expectPlantedPanelRejected("incidents");
    expect(screen.getByRole("main", { name: "Incidents" })).toBeInTheDocument();
    expect(document.body.textContent).toContain("Operational event cases · linked Findings and work");

    // Controls (section 2) and the status line; no cutoff input (A2Q5).
    const bar = document.querySelector("[data-global-work-bar]") as HTMLElement;
    expect(within(bar).getByLabelText("From (UTC)")).toHaveValue("2026-10-14");
    expect(within(bar).getByLabelText("To (UTC, exclusive)")).toHaveValue("2026-10-21");
    expect(within(bar).getAllByRole("button").map((b) => b.textContent)).toEqual(["Show records", "Reload"]);
    expect(bar.querySelectorAll("input")).toHaveLength(2);
    expect(text(document.querySelector("[data-global-work-status]"))).toBe("As known at 21 Oct 2026, 12:00 UTC");

    // A2Q1 cards: Open = OPEN + IN_PROGRESS over the full selection, not the page.
    expect(
      Array.from(cards()!.querySelectorAll("li")).map((li) => [
        text(li.querySelector(".v69-metric__label")),
        text(li.querySelector(".v69-metric__value")),
        text(li.querySelector(".v69-metric__note")),
      ]),
    ).toEqual([
      ["Open incidents", "5", "Open or in progress in this window"],
      ["High severity", "Not assessed", "Severity is not recorded on work cases"],
      ["Awaiting evidence", "Not assessed", "No case evidence review state"],
      ["Closed verified", "Not assessed", "Closed does not verify an outcome"],
    ]);
    expect(document.body.textContent).not.toMatch(/INC-203|GreenHarvest|F-118|WR-019|ACT-051|Maintenance lead/);

    // A2Q7: the footer is the panel sub-line; A2Q8 columns and cells.
    const panel = panelTitled("Incident cases");
    expect(text(panel.querySelector(".panel__description"))).toBe(
      "An incident connects authored events and linked records; a gap alone does not create a case.",
    );
    expect(Array.from(panel.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Incident",
      "Site",
      "Start",
      "Severity",
      "State",
      "Owner",
      "Findings / work",
    ]);
    const trs = Array.from(panel.querySelectorAll("tbody tr"));
    expect(trs).toHaveLength(5);
    const first = trs[0];
    const titleLink = within(cell(first, 0)).getByRole("link");
    expect(titleLink.textContent).toBe(`INC-000001 · ${TITLE200}`);
    expect(titleLink.getAttribute("href")).toBe(SITE_INCIDENTS);
    expect(cell(first, 0).querySelector(".global-work-clamp")).toContainElement(titleLink);
    const full = cell(first, 0).querySelector("[data-global-work-full-title]") as HTMLDetailsElement;
    expect(full.tagName).toBe("DETAILS");
    expect(full.open).toBe(false);
    expect(text(full.querySelector("summary"))).toBe("Full title text");
    expect(text(full)).toBe(`Full title text${TITLE200}`);
    const source = cell(first, 0).querySelector("[data-global-work-source]") as HTMLDetailsElement;
    expect(text(source.querySelector("summary"))).toBe("Source unverified");
    expect(text(source)).toContain("The origin of this authored work record is not established. No work outcome is verified.");
    expect(within(cell(first, 1)).getByRole("link", { name: "Kobo" })).toHaveAttribute("href", "/sites/KOBO-001");
    expect(text(cell(first, 2))).toBe("19 Oct 2026, 09:00 UTC");
    expect(text(cell(first, 3))).toBe("Not recorded");
    expect(text(cell(first, 4))).toBe("In progress");
    expect(text(cell(first, 5))).toBe(OWNER128);
    expect(text(cell(first, 6))).toBe("None linked");
    // Every cell value sits in a three-line clamp block, never on the `td` itself.
    for (const td of Array.from(first.querySelectorAll("td")).filter((_, i) => i !== 4)) {
      expect(td.querySelector(".global-work-clamp"), td.textContent ?? "").not.toBeNull();
    }

    const second = trs[1];
    expect(text(cell(second, 4))).toBe("Closed");
    expect(cell(second, 4).querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "neutral");
    expect(text(cell(second, 5))).toBe("Not assigned");
    expect(text(cell(second, 6))).toBe("Finding a1b2c3d4 · Action e5f6a7b8 / WR-000007 · WR-000008");
    expect(within(cell(second, 6)).getAllByRole("link").map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
      ["Finding a1b2c3d4", "/sites/KOBO-001/findings/f1?revision_id=r1"],
    ]);
    expect(text(cell(second, 0).querySelector("[data-global-work-source] summary"))).toBe("Prepared example data");
    expect(text(cell(trs[2], 6))).toBe("WR-000009");
    expect(cell(trs[2], 4).querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "red");
    expect(text(cell(trs[3], 0).querySelector("[data-global-work-source] summary"))).toBe("Generated test data");
    expect(text(cell(trs[4], 0).querySelector("[data-global-work-source] summary"))).toBe("Sources do not agree");

    // Scroll affordance, pager (A2Q10) and the Case boundaries panel.
    expect(text(panel.querySelector("[data-global-work-scroll-hint]"))).toBe("Scroll table horizontally");
    expect(text(panel.querySelector("[data-global-work-showing]"))).toBe("Showing 1–5 of 6");
    expect(panel.querySelector("[data-global-work-previous]")).toBeNull();
    expect(text(panelTitled("Case boundaries"))).toContain(
      "A closed case records a workflow step. Cause and outcome need their own evidence.",
    );

    fireEvent.click(panel.querySelector("[data-global-work-next]") as HTMLElement);
    await settled();
    expect(reads.calls[1]).toEqual({ from: FROM, to: TO, known_at: null, cursor: "CURSOR-2" });
    expect(screen.getByTestId("where").textContent).toBe(`${PAGE}&cursor=CURSOR-2`);
    expect(screen.getByTestId("where").getAttribute("data-trail")).toBe("[null]");
    const page2 = panelTitled("Incident cases");
    expect(text(page2.querySelector("[data-global-work-showing]"))).toBe("Showing 6–6 of 6");
    expect(page2.querySelector("[data-global-work-next]")).toBeNull();
    // The card still counts the full selection on page two.
    expect(text(cards()!.querySelector(".v69-metric__value"))).toBe("5");

    fireEvent.click(page2.querySelector("[data-global-work-previous]") as HTMLElement);
    await settled();
    expect(screen.getByTestId("where").textContent).toBe(PAGE);
    expect(screen.getByTestId("where").getAttribute("data-trail")).toBe("[]");
    expect(text(document.querySelector("[data-global-work-showing]"))).toBe("Showing 1–5 of 6");
  });

  it("labels an explicit earlier cutoff as historical and forwards it unchanged", async () => {
    const reads = client({ "page-one": loaded(body([row(1)], { status: "HISTORICAL" })) });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&site_id=KOBO-001`, reads);
    await settled();
    expect(reads.calls).toEqual([{ from: FROM, to: TO, known_at: KNOWN, cursor: null }]);
    expect(text(document.querySelector("[data-global-work-status]"))).toBe("Historical as of 21 Oct 2026, 12:00 UTC");
    expect(cards()).not.toBeNull();
  });

  it("states a complete zero as zero, with cards", async () => {
    const reads = client({ "page-one": loaded(body([], { state_counts: { OPEN: 0, IN_PROGRESS: 0, CLOSED: 0 } })) });
    mount(PAGE, reads);
    await settled();
    expectV69Panels("incidents");
    expect(text(cards()!.querySelector(".v69-metric__value"))).toBe("0");
    expect(Array.from(document.querySelectorAll("[data-global-work-zero] p")).map(text)).toEqual([
      "No incident cases in this window.",
      "Change the UTC window or open a Site record.",
    ]);
    expect(document.querySelector("table")).toBeNull();
    expect(document.querySelector("[data-global-work-pager]")).toBeNull();
  });

  it("states no accessible Sites without cards or a zero (typed EMPTY_SCOPE only)", async () => {
    const reads = client({
      "page-one": loaded(
        body([], {
          status: "EMPTY_SCOPE",
          coverage: { state: "EMPTY_SCOPE", reason: "NO_ACCESSIBLE_SITES", sites: [] },
          state_counts: { OPEN: 0, IN_PROGRESS: 0, CLOSED: 0 },
        }),
      ),
    });
    mount(PAGE, reads);
    await settled();
    expectV69Panels("incidents");
    expect(text(document.querySelector("[data-global-work-empty-scope]"))).toBe("No accessible Sites.");
    expect(cards()).toBeNull();
    expect(document.querySelector("[data-global-work-zero]")).toBeNull();
    expect(document.body.textContent).not.toContain("No incident cases in this window.");
  });

  it.each([
    ["UNAUTHENTICATED", "Sign in to see work records.", false],
    ["INVALID_WINDOW", "Choose a valid date range of at most 31 days.", false],
    ["INVALID_KNOWN_AT", "Choose a valid cutoff time.", false],
    ["INVALID_LIMIT", "Choose a page size from 1 to 100.", false],
    ["INVALID_CURSOR", "The list changed. Reload the first page.", true],
    ["WORK_BASIS_CHANGED", "The list changed. Reload the first page.", true],
    ["WORK_STORE_UNAVAILABLE", "Work records could not be read. Reload.", false],
  ] as const)("refusal %s states its sentence and never a zero", async (code, sentence, firstPage) => {
    const reads = client({ "page-one": { status: "refused", code }, C9: { status: "refused", code } });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&cursor=C9`, reads);
    await settled();
    expectV69Panels("incidents");
    const block = document.querySelector(`[data-global-work-refusal="${code}"]`) as HTMLElement;
    expect(text(block.querySelector("p"))).toBe(sentence);
    expect(cards()).toBeNull();
    expect(document.querySelector("table, [data-global-work-zero], [data-global-work-status]")).toBeNull();
    const link = block.querySelector("[data-global-work-first-page]");
    if (firstPage) {
      expect(text(link)).toBe("Reload the first page");
      expect(link).toHaveAttribute("href", `${PAGE}&known_at=${encodeURIComponent(KNOWN)}`);
    } else {
      expect(link).toBeNull();
    }
  });

  it.each([
    ["one bound missing", `/incidents?from=${encodeURIComponent(FROM)}`, "INVALID_WINDOW"],
    ["not a UTC midnight", `/incidents?from=2026-10-14T01:00:00Z&to=${encodeURIComponent(TO)}`, "INVALID_WINDOW"],
    ["more than 31 days", `/incidents?from=2026-09-01T00:00:00Z&to=${encodeURIComponent(TO)}`, "INVALID_WINDOW"],
    ["out of order", `/incidents?from=${encodeURIComponent(TO)}&to=${encodeURIComponent(FROM)}`, "INVALID_WINDOW"],
    ["repeated from", `${PAGE}&from=${encodeURIComponent(FROM)}`, "INVALID_WINDOW"],
    ["bad cutoff", `${PAGE}&known_at=yesterday`, "INVALID_KNOWN_AT"],
  ])("an invalid page query (%s) is refused without a fetch", async (_name, path, code) => {
    const reads = client({});
    mount(path, reads);
    await settled();
    expect(reads.calls).toEqual([]);
    expect(document.querySelector(`[data-global-work-refusal="${code}"]`)).not.toBeNull();
    expect(cards()).toBeNull();
  });

  it("uses the seven complete UTC days when both bounds are absent, and Show records restarts at page one", async () => {
    const reads = client({ "page-one": loaded(body([row(1)])) });
    mount("/incidents", reads);
    await settled();
    expect(reads.calls[0]).toEqual({ ...defaultGlobalWorkWindow(), known_at: null, cursor: null });
    fireEvent.change(screen.getByLabelText("From (UTC)"), { target: { value: "2026-10-01" } });
    fireEvent.change(screen.getByLabelText("To (UTC, exclusive)"), { target: { value: "2026-10-08" } });
    fireEvent.click(screen.getByRole("button", { name: "Show records" }));
    await settled();
    expect(screen.getByTestId("where").textContent).toBe(
      "/incidents?from=2026-10-01T00%3A00%3A00Z&to=2026-10-08T00%3A00%3A00Z",
    );
    expect(reads.calls[1]).toEqual({ from: "2026-10-01T00:00:00Z", to: "2026-10-08T00:00:00Z", known_at: null, cursor: null });
    // Reload re-reads the same query.
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await settled();
    expect(reads.calls[2]).toEqual(reads.calls[1]);
  });
});

describe("W6-01a A2: global work client", () => {
  it("sends limit=5 and only the page keys, and maps refusals, failures and malformed answers", async () => {
    const seen: string[] = [];
    const answers: [number, unknown][] = [
      [200, body([row(1)])],
      [409, { detail: { code: "WORK_BASIS_CHANGED", message: "x" }, rows: null, total_count: null }],
      [200, { schema_version: "global-work-index-1", rows: [] }],
      [500, { detail: { code: "SOMETHING_ELSE" } }],
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        seen.push(url);
        const [status, json] = answers.shift() ?? [500, null];
        return new Response(JSON.stringify(json), { status });
      }),
    );
    const reads = createGlobalWorkClient();
    const query = { from: FROM, to: TO, known_at: KNOWN, cursor: "C2" };
    expect((await reads.incidents(query)).status).toBe("loaded");
    expect(await reads.incidents(query)).toEqual({ status: "refused", code: "WORK_BASIS_CHANGED" });
    expect(await reads.incidents(query)).toEqual({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
    expect(await reads.incidents(query)).toEqual({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
    expect(seen[0]).toBe(
      "/api/work/incidents?from=2026-10-14T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&known_at=2026-10-21T12%3A00%3A00Z&cursor=C2&limit=5",
    );
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new Error("offline"))));
    expect(await createGlobalWorkClient().incidents(query)).toEqual({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
  });

  it("accepts object state counts on /incidents and refuses null ones (W6-01b P-B2-2)", async () => {
    const answers: unknown[] = [body([row(1)]), { ...body([row(1)]), state_counts: null }];
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(answers.shift() ?? null), { status: 200 })),
    );
    const reads = createGlobalWorkClient();
    const query = { from: FROM, to: TO, known_at: null, cursor: null };
    expect((await reads.incidents(query)).status).toBe("loaded");
    expect(await reads.incidents(query)).toEqual({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
  });

  it("ignores undeclared page keys", () => {
    const parsed = globalWorkPageQuery(new URLSearchParams(`from=${FROM}&to=${TO}&site_id=KOBO-001&limit=50`));
    expect(parsed).toEqual({ status: "valid", query: { from: FROM, to: TO, known_at: null, cursor: null } });
  });
});

describe("W6-01a A2: the /incidents route in the app shell", () => {
  it("mounts the page under the operator shell with the rail's Incidents root current", async () => {
    const reads = client({ "page-one": loaded(body([row(1)])) });
    render(
      <MemoryRouter initialEntries={[PAGE]}>
        <App flags={featureFlagsWith(false)} globalWork={reads} />
      </MemoryRouter>,
    );
    await settled();
    expect(screen.getByRole("main", { name: "Incidents" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
    const rail = screen.getByRole("navigation", { name: "Operator routes" });
    const link = within(rail).getByRole("link", { name: "Incidents" });
    expect(link).toHaveAttribute("href", "/incidents");
    expect(link).toHaveAttribute("aria-current", "page");
    expect(reads.calls).toHaveLength(1);
  });
});
