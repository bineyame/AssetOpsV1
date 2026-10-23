/**
 * W6-01e E2: the global Operational records root (`.agent/W6-01-build-spec.md` section 2, section 3.1
 * A2Q1-A2Q10/X1-X8/CL3-1/CL3-6 and the "E1-E2 pre-flight rulings" P-E2-1..8). Typed responses only: the persisted
 * positive, filtered, historical, zero, 503, 409 and long-body states are captured against the real API in
 * `.agent/W6-01-evidence/E2/`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { OPERATIONAL_RECORDS_PATH } from "../../shell/operatorSiteRoutes";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { OperationalRecordsFrame, operationalKindOf } from "../OperationalRecords";
import {
  createGlobalWorkClient,
  type GlobalOperationalBody,
  type GlobalOperationalRow,
  type GlobalWorkClient,
  type GlobalWorkQuery,
  type GlobalWorkResult,
} from "../globalWorkClient";

const FROM = "2026-10-14T00:00:00Z";
const TO = "2026-10-21T00:00:00Z";
const KNOWN = "2026-10-21T12:00:00Z";
const WINDOW = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;
const PAGE = `/operational-records?${WINDOW}`;
const LONG = "Operator checked the panel and logged readings ".repeat(90).slice(0, 4000);
const ACTOR128 = "service:".concat("x".repeat(120));

function row(n: number, over: Partial<GlobalOperationalRow> = {}): GlobalOperationalRow {
  const id = `00000000-0000-4000-8000-${String(100 + n).padStart(12, "0")}`;
  return {
    site_code: "KOBO-001",
    site_name: "Kobo",
    site_id: "00000000-0000-4000-8000-000000000002",
    site_code_key: "kobo-001",
    canonical_record_id: id,
    root_id: id,
    head_id: id,
    code: `REC-${String(n).padStart(6, "0")}`,
    kind: "OPERATOR_LOG",
    body: `Operator log ${n}`,
    root_occurred_at: "2026-10-18T09:00:00Z",
    occurred_at: "2026-10-18T09:00:00Z",
    recorded_at: "2026-10-21T11:59:02Z",
    period_end: null,
    actor_kind: "SERVICE",
    actor_id: "service:w401-fixture",
    quantity: null,
    unit: null,
    source_document_sha256: null,
    case_id: null,
    case_kind: null,
    case_code: null,
    state: "SUBMITTED",
    supersedes_record_id: null,
    correction_reason: null,
    source_provenance: {
      classification: "UNKNOWN",
      state: "UNKNOWN",
      source_ids: [],
      evidence_ids: [],
      basis_sha256: `sha256:${"0".repeat(64)}`,
      reasons: [],
    },
    links: { site: { label: "Kobo", href: "/sites/KOBO-001" }, case: null },
    ...over,
  };
}

function body(rows: GlobalOperationalRow[], over: Partial<GlobalOperationalBody> = {}): GlobalOperationalBody {
  return {
    schema_version: "global-work-index-1",
    scope: { tenant_id: "00000000-0000-4000-8000-000000000001", authorized_site_count: 2, covered_site_count: 2, access_basis: "sha256:x" },
    window: { from: FROM, to: TO, bounds: "[from, to)" },
    known_at: "2026-10-23T08:00:00Z",
    status: "CURRENT",
    coverage: { state: "COMPLETE", reason: null, sites: [] },
    total_count: rows.length,
    state_counts: null,
    rows,
    next_cursor: null,
    selection_token: "sha256:token",
    ...over,
  };
}

type Answer = GlobalWorkResult<GlobalOperationalBody>;

function client(answers: Record<string, Answer>, gate?: Promise<void>): GlobalWorkClient & { calls: GlobalWorkQuery[] } {
  const calls: GlobalWorkQuery[] = [];
  return {
    calls,
    async incidents() {
      throw new Error("the Operational records page never reads incidents");
    },
    async operationalRecords(query) {
      calls.push(query);
      if (gate) await gate;
      const answer = answers[query.cursor ?? `page-one${query.kind ? `:${query.kind}` : ""}`] ?? answers["page-one"];
      if (answer === undefined) throw new Error(`no answer for ${JSON.stringify(query)}`);
      return answer;
    },
  };
}

const loaded = (value: GlobalOperationalBody): Answer => ({ status: "loaded", value });

function Where() {
  const location = useLocation();
  const trail = (location.state as { globalWorkTrail?: unknown } | null)?.globalWorkTrail;
  return (
    <output data-testid="where" data-trail={JSON.stringify(trail ?? null)}>
      {`${location.pathname}${location.search}`}
    </output>
  );
}

function mount(path: string, reads: GlobalWorkClient, state?: unknown) {
  return render(
    <MemoryRouter initialEntries={[state === undefined ? path : { pathname: path.split("?")[0], search: `?${path.split("?")[1] ?? ""}`, state }]}>
      <Routes>
        <Route path={OPERATIONAL_RECORDS_PATH} element={<OperationalRecordsFrame client={reads} />} />
      </Routes>
      <Where />
    </MemoryRouter>,
  );
}

async function settled() {
  await waitFor(() => expect(document.querySelector("[data-global-work-loading]")).toBeNull());
  await settledScreen();
}

const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const cards = () => document.querySelector("[data-global-work-cards]");
const cell = (tr: Element, i: number) => tr.querySelectorAll("td")[i] as HTMLElement;
const where = () => screen.getByTestId("where");
const chip = (name: string) => within(screen.getByRole("group", { name: "Record type" })).getByRole("button", { name });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W6-01e E2: global Operational records", () => {
  it("renders the mock frame, cards, chips, cells, form, prose and pager over a typed five-row page", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const incident = "00000000-0000-4000-8000-000000000003";
    const rows = [
      row(1, {
        kind: "SHIFT_NOTE",
        head_id: "00000000-0000-4000-8000-000000000999",
        body: "Shift note at KOBO-001: generator stop handed over to the next shift.",
        supersedes_record_id: "00000000-0000-4000-8000-000000000101",
        correction_reason: "Log wording corrected after review",
        case_id: incident,
        case_kind: "INCIDENT",
        case_code: "INC-000001",
        recorded_at: "2026-10-21T12:00:01Z",
        links: {
          site: { label: "Kobo", href: "/sites/KOBO-001" },
          case: { label: "INC-000001", href: "/sites/KOBO-001/work/incidents?from=2026-10-19T00%3A00%3A00Z&to=2026-10-20T00%3A00%3A00Z" },
        },
      }),
      row(2, {
        kind: "MANUAL_READING",
        body: "Manual reading at KOBO-001: Fuel tank dip: 198 L",
        quantity: "198",
        unit: "L",
        case_kind: "MAINTENANCE_REQUEST",
        case_code: "WR-000002",
        links: {
          site: { label: "Kobo", href: "/sites/KOBO-001" },
          case: { label: "WR-000002", href: "/maintenance/requests/00000000-0000-4000-8000-000000000005?site_id=KOBO-001" },
        },
      }),
      row(3, { kind: "SITE_VISIT", body: LONG, period_end: "2026-10-18T10:30:00Z", actor_id: ACTOR128 }),
      row(4, { kind: "SHIFT_NOTE", source_provenance: { ...row(4).source_provenance, classification: "AUTHORED_DEMONSTRATION" } }),
      row(5, { site_code: "KOBO-002", site_name: "Kobo 2", links: { site: { label: "Kobo 2", href: "/sites/KOBO-002" }, case: null } }),
    ];
    const reads = client(
      {
        "page-one": loaded(body(rows, { total_count: 7, next_cursor: "CURSOR-2" })),
        "CURSOR-2": loaded(body([row(6), row(7)], { total_count: 7 })),
      },
      gate,
    );
    mount(PAGE, reads);

    // CL3-1: the loading sentence stands in for the cards and table body; the heading and controls stay.
    expect(text(document.querySelector("[data-global-work-loading]"))).toBe("Loading the operational records across the estate.");
    expect(screen.getByRole("heading", { level: 1, name: "Operational records" })).toBeInTheDocument();
    expect(cards()).toBeNull();
    release();
    await settled();

    expect(reads.calls).toEqual([{ from: FROM, to: TO, known_at: null, cursor: null }]);
    expectV69Panels("oprecords");
    expectPlantedPanelRejected("oprecords");
    expect(screen.getByRole("main", { name: "Operational records" })).toBeInTheDocument();
    const root = document.querySelector('[data-global-work-root="operational-records"]') as HTMLElement;
    expect(root.className).toContain("global-work--oprecords");

    // P-E2-7: plain breadcrumb, subtitle, no tabs, the labelled window form.
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(Array.from(crumbs.querySelectorAll("li")).map(text)).toEqual(["Operational records"]);
    expect(crumbs.querySelector("a")).toBeNull();
    expect(document.body.textContent).toContain("Operator logs, manual readings, shift notes and site visits");
    expect(document.querySelector("[data-global-work-tabs], nav[aria-label='Context tabs']")).toBeNull();
    expect(screen.getByRole("form", { name: "Operational records window" })).toBeInTheDocument();

    // P-E2-3: the four mock headings and first note; amber fourth card; card values bound to total_count.
    const list = Array.from(cards()!.querySelectorAll("li")).map((li) => ({
      label: text(li.querySelector(".v69-metric__label")),
      value: text(li.querySelector(".v69-metric__value")),
      note: text(li.querySelector(".v69-metric__note")),
      amber: li.className.includes("v69-metric--amber"),
    }));
    expect(list).toEqual([
      { label: "Records in window", value: "7", note: "Logs, readings, notes and visits", amber: false },
      { label: "Feeding evidence", value: "Not established", note: "No accepted-evidence publication link", amber: false },
      { label: "In review", value: "No review workflow", note: "All stored records are Submitted", amber: false },
      { label: "Requested, not yet done", value: "Not recorded", note: "No request list recorded", amber: true },
    ]);

    // P-E2-2: five buttons outside panel 1, after the cards; All pressed.
    const chips = screen.getByRole("group", { name: "Record type" });
    expect(chips.className).toContain("v69-chips");
    expect(Array.from(chips.querySelectorAll("button")).map((b) => [text(b), b.getAttribute("aria-pressed")])).toEqual([
      ["All", "true"],
      ["Operator log", "false"],
      ["Manual reading", "false"],
      ["Shift note", "false"],
      ["Site visit", "false"],
    ]);
    const table = panelTitled("Operational records");
    expect(table.contains(chips)).toBe(false);
    expect(cards()!.compareDocumentPosition(chips) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(chips.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    // P-E2-4/7/8: the mock description, column order and the cells.
    expect(text(table.querySelector(".panel__description"))).toBe("What people on site recorded, and the evidence each one feeds");
    expect(Array.from(table.querySelectorAll("th")).map(text)).toEqual([
      "Record",
      "Type",
      "Site",
      "When",
      "By",
      "What it says",
      "Feeds",
      "State",
    ]);
    expect(Array.from(table.querySelectorAll("col")).map((c) => (c as HTMLElement).style.width)).toEqual([
      "140px",
      "110px",
      "125px",
      "150px",
      "150px",
      "220px",
      "150px",
      "105px",
    ]);
    const trs = Array.from(table.querySelectorAll("tbody tr"));
    expect(trs).toHaveLength(5);
    const first = trs[0];
    expect(first.getAttribute("data-global-work-head")).toBe("00000000-0000-4000-8000-000000000999");
    expect(text(cell(first, 0).querySelector("[data-global-work-code]"))).toBe("REC-000001");
    expect(text(cell(first, 0).querySelector("[data-global-work-correction]"))).toBe("Correction: Log wording corrected after review");
    const earlier = cell(first, 0).querySelector("[data-global-work-supersedes]") as HTMLDetailsElement;
    expect(text(earlier.querySelector("summary"))).toBe("Earlier record version");
    expect(text(earlier)).toContain("00000000-0000-4000-8000-000000000101");
    expect(text(cell(first, 0).querySelector("[data-global-work-source] summary"))).toBe("Source unverified");
    expect(text(cell(first, 1))).toBe("Shift note");
    expect(cell(first, 1).querySelector(".v69-chip, .w1f4-action-badge")).toBeNull();
    expect(within(cell(first, 2)).getByRole("link", { name: "Kobo" })).toHaveAttribute("href", "/sites/KOBO-001");
    expect(text(cell(first, 3))).toBe("18 Oct 2026, 09:00 UTC");
    expect(text(cell(first, 4))).toBe("service:w401-fixture");
    expect(text(cell(first, 5).querySelector("[data-global-work-body]"))).toBe(
      "Shift note at KOBO-001: generator stop handed over to the next shift.",
    );
    expect(within(cell(first, 6)).getByRole("link", { name: "INC-000001" })).toHaveAttribute(
      "href",
      "/sites/KOBO-001/work/incidents?from=2026-10-19T00%3A00%3A00Z&to=2026-10-20T00%3A00%3A00Z",
    );
    expect(text(cell(first, 6))).toBe("INC-000001 →");
    const badge = cell(first, 7).querySelector("[data-global-work-state]") as HTMLElement;
    expect(text(badge)).toBe("Submitted");
    expect(badge.className).toContain("w1f4-action-badge--blue");
    // the reading line, the request link
    expect(text(cell(trs[1], 1))).toBe("Manual reading");
    expect(text(cell(trs[1], 5).querySelector("[data-global-work-reading]"))).toBe("Reading: 198 L");
    expect(text(cell(trs[1], 6))).toBe("WR-000002 →");
    expect(within(cell(trs[1], 6)).getByRole("link", { name: "WR-000002" })).toHaveAttribute(
      "href",
      "/maintenance/requests/00000000-0000-4000-8000-000000000005?site_id=KOBO-001",
    );
    expect(cell(trs[0], 0).querySelector("[data-global-work-correction]")).not.toBeNull();
    expect(cell(trs[1], 0).querySelector("[data-global-work-correction], [data-global-work-supersedes]")).toBeNull();
    // the long body: three-line clamp block plus the full-text disclosure; period end and long actor wrap
    const long = cell(trs[2], 5);
    expect(long.querySelector("[data-global-work-body]")?.className).toBe("global-work-clamp");
    const full = long.querySelector("[data-global-work-full-body]") as HTMLDetailsElement;
    expect(text(full.querySelector("summary"))).toBe("Full record text");
    expect(full.textContent).toContain(LONG.trim());
    expect(text(cell(trs[2], 3).querySelector("[data-global-work-period-end]"))).toBe("Until 18 Oct 2026, 10:30 UTC");
    expect(cell(trs[2], 4).querySelector("[data-global-work-actor]")?.className).toBe("global-work-clamp");
    expect(text(cell(trs[2], 4))).toBe(ACTOR128);
    expect(text(cell(trs[2], 6))).toBe("None linked");
    expect(text(cell(trs[3], 0).querySelector("[data-global-work-source] summary"))).toBe("Prepared example data");
    expect(document.body.textContent).not.toMatch(/Accepted|In review ·|Requested ·/);

    // P-E2-5: the inert mock form; only the two authorized fixture Site names.
    const form = panelTitled("Record a manual reading");
    expect(text(form.querySelector(".panel__description"))).toBe("Manual readings cannot be submitted from this page.");
    expect(form.querySelectorAll(".input-row")).toHaveLength(2);
    expect(Array.from(form.querySelectorAll("label.field")).map((l) => l.firstChild?.textContent?.trim())).toEqual([
      "Site",
      "Reading",
      "Value",
      "Taken at",
    ]);
    const [site, reading] = Array.from(form.querySelectorAll("select"));
    expect(Array.from(site.querySelectorAll("option")).map(text)).toEqual(["Kobo Mini-grid", "GreenHarvest Cold Room"]);
    expect(Array.from(reading.querySelectorAll("option")).map(text)).toEqual(["Fuel tank dip", "Stock in chamber", "Meter reading"]);
    expect((form.querySelectorAll("input")[0] as HTMLInputElement).placeholder).toBe("e.g. 192 L");
    expect((form.querySelectorAll("input")[1] as HTMLInputElement).value).toBe("6 Oct 2026 · 16:00 EAT");
    for (const control of Array.from(form.querySelectorAll("select, input, button"))) {
      expect(control).toBeDisabled();
    }
    const submit = form.querySelector(".form-footer button") as HTMLButtonElement;
    expect(text(submit)).toBe("Submit for review · Not available yet");
    expect(submit.querySelector("[data-link-unavailable='Submit for review']")).not.toBeNull();
    expect(text(form.querySelector("[data-global-work-form-reason]"))).toBe("Recording requires an authorized work service.");
    expect(form.textContent).not.toContain("REC-307");
    expect(form.textContent).not.toContain("Depot");
    fireEvent.click(submit);
    expect(reads.calls).toHaveLength(1);

    // P-E2-6: two paragraphs, bold Operator record.
    const prose = panelTitled("How records are used").querySelector(".prose") as HTMLElement;
    const paragraphs = Array.from(prose.querySelectorAll("p")).map(text);
    expect(paragraphs).toEqual([
      "Authored records are kept apart from measured readings. This page shows them as Operator record; none is accepted equipment evidence.",
      "A reading that has not been taken remains a visible gap; this page has no request list to count it.",
    ]);
    expect(text(prose.querySelector("p strong"))).toBe("Operator record");

    // A2Q10 pager
    expect(text(document.querySelector("[data-global-work-showing]"))).toBe("Showing 1–5 of 7");
    expect(screen.getByRole("navigation", { name: "Operational records pages" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await settled();
    expect(text(document.querySelector("[data-global-work-showing]"))).toBe("Showing 6–7 of 7");
    expect(reads.calls[1]).toEqual({ from: FROM, to: TO, known_at: null, cursor: "CURSOR-2" });
  });

  it("kind_invalid_and_filtered_zero: invalid or repeated kind never fetches; filtered zero names its kind", async () => {
    for (const bad of ["BOGUS", "operator_log", ""]) {
      const reads = client({ "page-one": loaded(body([row(1)])) });
      mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&kind=${bad}`, reads);
      await settledScreen();
      const refusal = document.querySelector("[data-page-refusal='INVALID_KIND']") as HTMLElement;
      expect(text(refusal)).toBe("Choose a supported record type.");
      expect(cards()).toBeNull();
      expect(reads.calls).toHaveLength(0);
      expect(Array.from(screen.getByRole("group", { name: "Record type" }).querySelectorAll("button")).every(
        (b) => b.getAttribute("aria-pressed") === "false" && !(b as HTMLButtonElement).disabled,
      )).toBe(true);
      expectV69Panels("oprecords");
      fireEvent.click(chip("Manual reading"));
      await settled();
      expect(text(where())).toBe(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&kind=MANUAL_READING`);
      expect(reads.calls).toEqual([{ from: FROM, to: TO, known_at: KNOWN, cursor: null, kind: "MANUAL_READING" }]);
      cleanup();
    }
    const repeated = client({ "page-one": loaded(body([row(1)])) });
    mount(`${PAGE}&kind=OPERATOR_LOG&kind=OPERATOR_LOG`, repeated);
    await settledScreen();
    expect(document.querySelector("[data-page-refusal='INVALID_KIND']")).not.toBeNull();
    expect(repeated.calls).toHaveLength(0);
    cleanup();

    const zeros: [string, string][] = [
      ["OPERATOR_LOG", "No operator log records in this window."],
      ["MANUAL_READING", "No manual reading records in this window."],
      ["SHIFT_NOTE", "No shift note records in this window."],
      ["SITE_VISIT", "No site visit records in this window."],
      ["all", "No operational records in this window."],
    ];
    for (const [kind, sentence] of zeros) {
      const reads = client({ "page-one": loaded(body([], { total_count: 0 })) });
      mount(`${PAGE}&kind=${kind}`, reads);
      await settled();
      const zero = document.querySelector("[data-global-work-zero]") as HTMLElement;
      expect(Array.from(zero.querySelectorAll("p")).map(text)).toEqual([sentence, "Change the UTC window or open a Site record."]);
      expect(cards()?.querySelector("[data-global-work-card='records_in_window'] .v69-metric__value")?.textContent).toBe("0");
      expect(reads.calls[0].kind).toBe(kind === "all" ? undefined : kind);
      cleanup();
    }
  });

  it("a chip sets the kind, drops the cursor and trail, keeps the window and cutoff; All removes kind", async () => {
    const reads = client({
      "page-one": loaded(body([row(1)], { total_count: 6, next_cursor: "CURSOR-2" })),
      "page-one:SHIFT_NOTE": loaded(body([row(1, { kind: "SHIFT_NOTE" })], { total_count: 1 })),
      "CURSOR-2": loaded(body([row(6)], { total_count: 6 })),
    });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&cursor=CURSOR-2`, reads, { globalWorkTrail: [null] });
    await settled();
    expect(reads.calls[0]).toEqual({ from: FROM, to: TO, known_at: KNOWN, cursor: "CURSOR-2" });
    fireEvent.click(chip("Shift note"));
    await settled();
    expect(text(where())).toBe(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&kind=SHIFT_NOTE`);
    expect(where().getAttribute("data-trail")).toBe("[]");
    expect(chip("Shift note")).toHaveAttribute("aria-pressed", "true");
    expect(chip("All")).toHaveAttribute("aria-pressed", "false");
    expect(reads.calls[1]).toEqual({ from: FROM, to: TO, known_at: KNOWN, cursor: null, kind: "SHIFT_NOTE" });
    // Show keeps the kind (and the cutoff), and drops the cursor
    fireEvent.click(screen.getByRole("button", { name: "Show records" }));
    await settled();
    expect(text(where())).toBe(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&kind=SHIFT_NOTE`);
    // Reload re-reads the same query, kind included
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await settled();
    expect(reads.calls[reads.calls.length - 1]).toEqual({ from: FROM, to: TO, known_at: KNOWN, cursor: null, kind: "SHIFT_NOTE" });
    fireEvent.click(chip("All"));
    await settled();
    expect(text(where())).toBe(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}`);
    expect(chip("All")).toHaveAttribute("aria-pressed", "true");
    expect(reads.calls[reads.calls.length - 1]).toEqual({ from: FROM, to: TO, known_at: KNOWN, cursor: null });
  });

  it("keeps kind on the pager and on the Reload-the-first-page link of a changed list", async () => {
    const reads = client({
      "page-one:SHIFT_NOTE": loaded(body([row(1)], { total_count: 6, next_cursor: "CURSOR-2" })),
      "CURSOR-2": { status: "refused", code: "WORK_BASIS_CHANGED" },
    });
    mount(`${PAGE}&kind=SHIFT_NOTE`, reads);
    await settled();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await settled();
    expect(text(where())).toBe(`${PAGE}&kind=SHIFT_NOTE&cursor=CURSOR-2`);
    expect(reads.calls[1]).toEqual({ from: FROM, to: TO, known_at: null, cursor: "CURSOR-2", kind: "SHIFT_NOTE" });
    const refusal = document.querySelector("[data-page-refusal='WORK_BASIS_CHANGED']") as HTMLElement;
    expect(text(refusal.querySelector("p"))).toBe("The list changed. Reload the first page.");
    expect(within(refusal).getByRole("link", { name: "Reload the first page" })).toHaveAttribute("href", `${PAGE}&kind=SHIFT_NOTE`);
  });

  it("labels an explicit earlier cutoff as historical", async () => {
    const reads = client({ "page-one": loaded(body([row(1)], { status: "HISTORICAL", known_at: KNOWN })) });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}`, reads);
    await settled();
    expect(text(document.querySelector("[data-global-work-status]"))).toBe("Historical as of 21 Oct 2026, 12:00 UTC");
  });

  it("states a read failure, an invalid window and no accessible Sites, never a zero", async () => {
    const down = client({ "page-one": { status: "refused", code: "WORK_STORE_UNAVAILABLE" } });
    mount(PAGE, down);
    await settled();
    expect(text(document.querySelector("[data-page-refusal='WORK_STORE_UNAVAILABLE']"))).toBe("Work records could not be read. Reload.");
    expect(cards()).toBeNull();
    expect(document.querySelector("[data-global-work-zero]")).toBeNull();
    cleanup();
    const none = client({});
    mount(`/operational-records?from=${encodeURIComponent(FROM)}&kind=OPERATOR_LOG`, none);
    await settledScreen();
    expect(text(document.querySelector("[data-page-refusal='INVALID_WINDOW']"))).toBe("Choose a valid date range of at most 31 days.");
    expect(none.calls).toHaveLength(0);
    cleanup();
    const empty = client({ "page-one": loaded(body([], { status: "EMPTY_SCOPE", total_count: 0 })) });
    mount(PAGE, empty);
    await settled();
    expect(text(document.querySelector("[data-global-work-empty-scope]"))).toBe("No accessible Sites.");
    expect(cards()).toBeNull();
  });

  it("reads a client without the optional operationalRecords method as a store refusal, never a throw", async () => {
    mount(PAGE, { async incidents() { throw new Error("unused"); } });
    await settled();
    expect(document.querySelector("[data-page-refusal='WORK_STORE_UNAVAILABLE']")).not.toBeNull();
  });

  it("maps page kinds: absent and all to all, stored kinds to themselves, the rest invalid", () => {
    expect(operationalKindOf([])).toBeNull();
    expect(operationalKindOf(["all"])).toBeNull();
    expect(operationalKindOf(["SITE_VISIT"])).toBe("SITE_VISIT");
    for (const bad of [["ALL"], [""], ["all", "all"], ["OPERATOR_LOG", "SHIFT_NOTE"]]) expect(operationalKindOf(bad)).toBeUndefined();
  });
});

describe("W6-01e E2: the operational records client", () => {
  it("reads /api/work/operational-records with limit=5, sends kind only when chosen, and accepts only null counts", async () => {
    const seen: string[] = [];
    const answers: unknown[] = [body([row(1)]), body([row(1)]), { ...body([row(1)]), state_counts: { OPEN: 1 } }, body([row(1)])];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        seen.push(url);
        return new Response(JSON.stringify(answers.shift() ?? null), { status: 200 });
      }),
    );
    const reads = createGlobalWorkClient();
    const query = { from: FROM, to: TO, known_at: null, cursor: null };
    expect((await reads.operationalRecords!(query)).status).toBe("loaded");
    expect((await reads.operationalRecords!({ ...query, kind: "MANUAL_READING" })).status).toBe("loaded");
    expect(await reads.operationalRecords!(query)).toEqual({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
    await reads.preventive!({ ...query, kind: "MANUAL_READING" });
    expect(seen[0]).toBe("/api/work/operational-records?from=2026-10-14T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&limit=5");
    expect(seen[1]).toBe(
      "/api/work/operational-records?from=2026-10-14T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&limit=5&kind=MANUAL_READING",
    );
    expect(seen[3]).toBe("/api/work/preventive?from=2026-10-14T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&limit=5");
  });
});

describe("W6-01e E2: the /operational-records route in the app shell", () => {
  it("mounts the page under the operator shell with the rail's Operational records root current", async () => {
    const reads = client({ "page-one": loaded(body([row(1)])) });
    render(
      <MemoryRouter initialEntries={[PAGE]}>
        <App flags={featureFlagsWith(false)} globalWork={reads} />
      </MemoryRouter>,
    );
    await settled();
    expect(screen.getByRole("main", { name: "Operational records" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
    const rail = screen.getByRole("navigation", { name: "Operator routes" });
    expect(within(rail).getByRole("link", { name: "Operational records" })).toHaveAttribute("aria-current", "page");
    expect(reads.calls).toHaveLength(1);
  });
});
