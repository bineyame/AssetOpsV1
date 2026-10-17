/**
 * S4-03 phase 3: the Finding History child view, its paging to the full
 * version list, exact version links, late-append and absent-history states,
 * and the Architect's Q3 proof (old -> new -> Evidence -> old, reload and
 * back/forward keep exact version IDs; an omitted ID is labelled "latest at
 * read time").
 */
import { fireEvent, render, screen, cleanup } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { SiteFindingFrame } from "../../shell/SiteAnalyticsFrames";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { expectStateLineVisible, visibleOutsideClosedDisclosure } from "../../test/productPresentation";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import type {
  FindingClient,
  FindingEvidenceBody,
  FindingHistoryBody,
  FindingReadResult,
  HistoryRevision,
} from "../findingClient";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

const SITE = HYBRID_MINI_GRID_SITE.site_id;
const F = "49281b7c-96ac-456d-ab6b-040bb0760444";
const PA = "d6f4c21f-402f-46cb-b41b-023d36cb8841";
const rid = (n: number) => `rev-${String(n).padStart(4, "0")}`;
const t = (minute: number) => new Date(Date.UTC(2026, 9, 6, 14, 0) + minute * 60_000).toISOString().replace(".000Z", "+00:00");

function revision(n: number, total: number, selected: number, patch: Partial<HistoryRevision> = {}): HistoryRevision {
  return {
    id: rid(n),
    revision_no: n,
    recorded_at: t(n * 10),
    transition: n === 1 ? "OPENED" : "BASIS_REFRESHED",
    lifecycle: "SUPPORTED",
    claim_level: "SUPPORTED",
    support_changed: false,
    model_version: "dispatch-3.1",
    matcher_version: "matcher-1",
    episode: { start: t(0), end: t(30) },
    candidate_minutes: "30",
    primary_assessment_revision_id: PA,
    window_assessment_revision_ids: [],
    interval_assessment_revision_ids: [PA],
    prior_window_assessment_revision_ids: null,
    prior_interval_assessment_revision_ids: null,
    foundation_revision_ids: ["fr-1"],
    binding_set_revision_ids: ["bs-1"],
    cited_evidence_count: 42,
    minutes: { candidate: "30", necessary: "10", indeterminate: "30" },
    previous_revision_id: n === 1 ? null : rid(n - 1),
    is_selected: n === selected,
    is_latest: n === total,
    cited_evidence: { count: 42, resolved: 42, accepted_rows: "ALL_RESOLVED", note: "counts accepted-evidence rows only" },
    times: {
      recorded_at: t(n * 10),
      analytic_completed_at: t(n * 10 - 1),
      source_time: { first: t(0), last: t(30) },
      received_at: t(n * 10 - 3),
      accepted_at: t(n * 10 - 2),
    },
    ...patch,
  };
}

interface Ledger {
  total: number;
  patch?: (n: number) => Partial<HistoryRevision>;
  body?: Partial<FindingHistoryBody>;
  failAfter?: number;
}

/** One page of the stored ledger, as the read serves it. `revisionId` null selects the latest at read time. */
function page(ledger: Ledger, revisionId: string | null, after: number, limit: number): FindingReadResult<FindingHistoryBody> {
  const { total } = ledger;
  const selectedNo = revisionId === null ? total : Number(revisionId.slice(4));
  if (!Number.isInteger(selectedNo) || selectedNo < 1 || selectedNo > total || (revisionId !== null && revisionId !== rid(selectedNo))) {
    return { status: "not_found", message: "No such Finding or revision for this Site." };
  }
  if (ledger.failAfter !== undefined && after >= ledger.failAfter) {
    return { status: "unavailable", message: null };
  }
  const all = Array.from({ length: total }, (_, i) => revision(i + 1, total, selectedNo, ledger.patch?.(i + 1)));
  const rows = all.filter((r) => r.revision_no > after).slice(0, limit);
  const last = rows[rows.length - 1];
  return {
    status: "loaded",
    value: {
      site_code: SITE,
      source_gate: { permitted: true, reason: "OPEN" },
      audit_only: null,
      finding: { id: F } as FindingHistoryBody["finding"],
      selection: {
        revision_id: rid(selectedNo),
        revision_no: selectedNo,
        selected_by: revisionId === null ? "LATEST_RECORDED" : "EXACT_REVISION_ID",
        latest_revision_id: rid(total),
        is_latest: selectedNo === total,
        replay: "Exact stored revisions only.",
        selected_note: revisionId === null ? "latest at read time" : "pinned",
        latest_revision_no: total,
      },
      revisions: rows,
      page: {
        after_revision_no: after,
        limit,
        total,
        returned: rows.length,
        next_after_revision_no: last && last.revision_no < total ? last.revision_no : null,
      },
      earlier_versions: total === 1 ? "NONE" : "PRESENT",
      revision_groups:
        total === 1
          ? [{ kind: "REVISION", label: "", count: 1, revision_ids: [rid(1)], first_revision_no: 1, last_revision_no: 1, support_changed: false }]
          : [
              { kind: "REVISION", label: "", count: 1, revision_ids: [rid(1)], first_revision_no: 1, last_revision_no: 1, support_changed: false },
              {
                kind: "BASIS_REFRESHED",
                label: "assessment basis updated",
                count: total - 1,
                revision_ids: all.slice(1).map((r) => r.id),
                first_revision_no: 2,
                last_revision_no: total,
                support_changed: false,
              },
            ],
      state: { lifecycle: "SUPPORTED", latest_transition: "BASIS_REFRESHED", note: "" },
      relations: {
        canonical_finding_id: F,
        merged_into: [],
        merged_from: [],
        split_from_finding_id: null,
        split_parts: [],
        recurs_after_finding_id: null,
        recurred_by: [],
        recurrence: { status: "NONE" },
      },
      time_kinds: {},
      statement: "Every stored revision.",
      links: {
        canonical: `/sites/${SITE}/findings/${F}`,
        evidence: "",
        history: "",
        performance: { status: "OPEN" },
      },
      ...ledger.body,
    },
  };
}

type Asked = { view: "history" | "evidence"; revisionId: string | null; after?: number };

function client(ledger: Ledger): FindingClient & { asked: Asked[] } {
  const asked: Asked[] = [];
  return {
    asked,
    getFinding: async () => ({ status: "not_found", message: null }),
    getFindingWindow: async () => ({ status: "not_found", message: null }),
    getFindingEvidence: async (_s, _f, revisionId) => {
      asked.push({ view: "evidence", revisionId });
      // The Evidence view is not under test here: a refusal keeps it small while still recording the exact ID asked.
      return { status: "not_found", message: null } as FindingReadResult<FindingEvidenceBody>;
    },
    getFindingHistory: async (_s, _f, revisionId, after, limit) => {
      asked.push({ view: "history", revisionId, after });
      return page(ledger, revisionId, after, limit);
    },
  };
}

function Where() {
  const at = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <output data-testid="where">{at.pathname + at.search}</output>
      <button type="button" onClick={() => navigate(-1)}>
        test-back
      </button>
      <button type="button" onClick={() => navigate(1)}>
        test-forward
      </button>
    </>
  );
}
const where = () => screen.getByTestId("where").textContent ?? "";
const q = (selector: string) => document.querySelector(selector);
const all = (selector: string) => Array.from(document.querySelectorAll(selector));

/** W1-UX-02: the notes of a state line after its state label and sentence, in order. */
function statusNotes(note: Element): Element[] {
  return Array.from(note.parentElement?.children ?? []).filter(
    (el) => !el.matches(".product-status__label, .product-status__sentence"),
  );
}

const detail: SiteDetailClient = { getSite: async () => ({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };

async function frame(path: string, findings: FindingClient) {
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        {["/sites/:siteId/findings/:findingId", "/sites/:siteId/findings/:findingId/:findingView"].map((p) => (
          <Route
            key={p}
            path={p}
            element={
              <>
                <SiteFindingFrame detail={detail} sitesPath="/sites" findings={findings} />
                <Where />
              </>
            }
          />
        ))}
      </Routes>
    </MemoryRouter>,
  );
  await settledScreen();
  return view;
}

const HISTORY = `/sites/${SITE}/findings/${F}/history`;
const EVIDENCE = `/sites/${SITE}/findings/${F}/evidence`;

afterEach(() => cleanup());

describe("Finding History child view (S4-03 phase 3)", () => {
  it("reads every page and lists all versions oldest first, labelling an omitted version as latest at read time", async () => {
    const c = client({ total: 205 });
    const { container } = await frame(HISTORY, c);
    expect(c.asked).toEqual([
      { view: "history", revisionId: null, after: 0 },
      { view: "history", revisionId: null, after: 100 },
      { view: "history", revisionId: null, after: 200 },
    ]);
    const rows = all("[data-history-revision-no]").map((r) => Number(r.getAttribute("data-history-revision-no")));
    expect(rows).toEqual(Array.from({ length: 205 }, (_, i) => i + 1));
    expect(q("[data-history-complete]")).toHaveTextContent("All 205 recorded versions are listed, oldest first.");
    expect(q("[data-history-latest-at-read]")).toHaveTextContent("Latest version at the time of reading (version 205)");
    expect(q("[data-history-pin]")).toHaveAttribute("href", `${HISTORY}?revision_id=${rid(205)}`);
    expect(q("[data-finding-section='history']")).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Finding history");
    const { violations } = scanProductVocabulary(container, "finding history");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("marks the selected and the latest version separately and leads an earlier selection with its status", async () => {
    await frame(`${HISTORY}?revision_id=${rid(1)}`, client({ total: 3 }));
    const lead = q("[data-history-earlier-version]") as HTMLElement;
    expect(lead).toHaveTextContent("Version 1 is selected. It is an earlier version: version 3 replaces it.");
    // W1-UX-02: the earlier-version note is the first note of the answer card's state line, right after the state sentence.
    expect(statusNotes(lead)[0]).toBe(lead);
    expect(expectStateLineVisible(panelTitled("Revision history"))).toBe("Earlier version, kept for the record");
    expect(all("[data-history-selected]").map((r) => r.getAttribute("data-history-revision"))).toEqual([rid(1)]);
    expect(all("[data-history-latest]").map((r) => r.getAttribute("data-history-revision"))).toEqual([rid(3)]);
    expect(q(`[data-history-revision='${rid(1)}']`)).toHaveAttribute("aria-current", "true");
    // Exact version links on every row: History selection, the Finding at that version, its Evidence.
    expect(q(`[data-history-select='${rid(2)}']`)).toHaveAttribute("href", `${HISTORY}?revision_id=${rid(2)}`);
    expect(q(`[data-history-finding-link='${rid(2)}']`)).toHaveAttribute("href", `/sites/${SITE}/findings/${F}?revision_id=${rid(2)}`);
    expect(q(`[data-history-evidence-link='${rid(2)}']`)).toHaveAttribute("href", `${EVIDENCE}?revision_id=${rid(2)}`);
    // Section links keep the exact version.
    expect(q("[data-finding-section='evidence']")).toHaveAttribute("href", `${EVIDENCE}?revision_id=${rid(1)}`);
    expect(q("[data-finding-section='finding']")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}?revision_id=${rid(1)}`);
  });

  it("keeps assessment updates with an unchanged amount individually selectable", async () => {
    await frame(HISTORY, client({ total: 4 }));
    const grouped = all("[data-history-group]");
    expect(grouped).toHaveLength(3);
    expect(grouped[0]).toHaveTextContent("One of 3 assessment updates with the amount unchanged (versions 2–4)");
    expect(all("[data-history-select]")).toHaveLength(4);
  });

  it("states that a single version has no earlier versions", async () => {
    await frame(HISTORY, client({ total: 1 }));
    expect(q("[data-history-no-earlier]")).toHaveTextContent("No earlier versions. This Finding has one recorded version.");
    expect(all("[data-history-revision]")).toHaveLength(1);
  });

  it("shows late-accepted readings on the appended version only, and keeps the earlier version's records", async () => {
    // F04 shape: v1 cites 42; v2 is appended after a delayed reading is accepted and cites 78.
    const patch = (n: number): Partial<HistoryRevision> =>
      n === 1
        ? { times: { ...revision(1, 2, 2).times, accepted_at: t(5) } }
        : {
            transition: "SUPPORT_CHANGED",
            support_changed: true,
            cited_evidence: { count: 78, resolved: 78, accepted_rows: "ALL_RESOLVED", note: "" },
            times: { ...revision(2, 2, 2).times, accepted_at: t(15) },
          };
    await frame(HISTORY, client({ total: 2, patch }));
    expect(q(`[data-history-revision='${rid(1)}'] [data-history-late-evidence]`)).toBeNull();
    expect(q(`[data-history-revision='${rid(2)}'] [data-history-late-evidence]`)).toHaveTextContent(
      "Cites readings accepted after version 1 was recorded. Version 1 keeps the records it cited.",
    );
    expect(q(`[data-history-revision='${rid(1)}'] [data-history-cited]`)).toHaveAttribute("data-history-cited", "42");
    expect(q(`[data-history-revision='${rid(2)}'] [data-history-cited]`)).toHaveAttribute("data-history-cited", "78");
  });

  it("shows found accepted records as a count with a link to Evidence, never as a record-trail verdict", async () => {
    const patch = (n: number): Partial<HistoryRevision> =>
      n === 2 ? { cited_evidence: { count: 42, resolved: 41, accepted_rows: "UNRESOLVED_PRESENT", note: "" } } : {};
    await frame(HISTORY, client({ total: 2, patch }));
    const ok = q(`[data-history-revision='${rid(1)}'] [data-history-cited]`)?.parentElement as HTMLElement;
    expect(ok).toHaveTextContent("42 cited; 42 of 42 found as accepted records");
    const gap = q(`[data-history-revision='${rid(2)}'] [data-history-cited]`)?.parentElement as HTMLElement;
    expect(gap).toHaveTextContent("41 of 42 found as accepted records (1 could not be found)");
    expect(q(`[data-history-check-evidence='${rid(2)}']`)).toHaveAttribute("href", `${EVIDENCE}?revision_id=${rid(2)}`);
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(/lineage|complete record trail|trail complete|fully traced|verified/i);
  });

  it("names the time kinds separately and makes no as-of-a-moment replay claim", async () => {
    await frame(HISTORY, client({ total: 1 }));
    for (const term of ["Version recorded", "Readings from", "Last cited reading received", "Last cited reading accepted", "Analysis finished"]) {
      expect(screen.getByText(term)).toBeInTheDocument();
    }
    // W1-F3 phase D: the Basis cell shows one short phrase; its labelled times sit in a closed per-row disclosure.
    for (const term of ["Readings from", "Last cited reading received", "Last cited reading accepted", "Analysis finished"]) {
      expect(screen.getByText(term).closest("details")).not.toHaveAttribute("open");
    }
    expect(q("[data-history-basis-line]")).toHaveTextContent(/possibly avoidable; .* undecided/);
    expect(q("[data-history-basis-line]")?.closest("details")).toBeNull();
    expect(document.body).toHaveTextContent("they are not a way to view the Finding as of an earlier moment");
    expect(document.body.textContent ?? "").not.toMatch(/knowledge/i);
  });

  it("says the list is incomplete when a later page cannot be read", async () => {
    await frame(HISTORY, client({ total: 205, failAfter: 100 }));
    expect(q("[data-history-incomplete]")).toHaveTextContent("Only 100 of 205 recorded versions could be read");
    expect(q("[data-history-complete]")).toBeNull();
  });

  it("leads a closed-source pinned read with its record-only status", async () => {
    await frame(`${HISTORY}?revision_id=${rid(1)}`, client({
      total: 2,
      body: { audit_only: { non_current: true, reason: "CLOSED", statement: "Audit material only" } },
    }));
    const lead = q("[data-history-audit-only]") as HTMLElement;
    expect(lead).toHaveTextContent("Record only.");
    // W1-UX-02: the record-only note is the first note of the answer card's state line, right after the state sentence.
    expect(statusNotes(lead)[0]).toBe(lead);
    expect(expectStateLineVisible(panelTitled("Revision history"))).toBe("For the record only");
  });

  it("leads with a non-supported latest state in plain words", async () => {
    await frame(HISTORY, client({ total: 2, body: { state: { lifecycle: "NO_LONGER_SUPPORTED", latest_transition: "NO_LONGER_SUPPORTED", note: "" } } }));
    expect(q("[data-history-lifecycle='NO_LONGER_SUPPORTED']")).toHaveTextContent("No longer supported");
    expect(q("[data-history-lifecycle]")).toHaveTextContent("does not mean the generator was repaired");
  });

  it("refuses an unknown version and keeps it in the address instead of showing the latest", async () => {
    const c = client({ total: 3 });
    await frame(`${HISTORY}?revision_id=rev-9999`, c);
    expect(q("[data-finding-read='not_found']")).toHaveTextContent("The version in the address is kept as given");
    expect(where()).toBe(`${HISTORY}?revision_id=rev-9999`);
    expect(all("[data-history-revision]")).toHaveLength(0);
    expect(q("[data-history-open-latest]")).toHaveAttribute("href", HISTORY);
  });

  it.each([
    ["unauthenticated", "Sign in to read this site's Findings."],
    ["forbidden", "Your account has no access to this site's Findings."],
    ["closed", "not released for use yet"],
    ["unavailable", "Nothing here means the Finding has no versions."],
  ] as const)("states a %s read in plain words and lists no versions", async (status, words) => {
    const c: FindingClient = {
      ...client({ total: 1 }),
      getFindingHistory: async () => (status === "closed" ? { status, message: null, note: null } : { status, message: null }),
    };
    await frame(HISTORY, c);
    expect(q(`[data-finding-read='${status}']`)).toHaveTextContent(words);
    expect(all("[data-history-revision]")).toHaveLength(0);
  });
});

describe("Q3: exact versions survive old -> new -> Evidence -> old, reload and back/forward", () => {
  it("keeps exact revision IDs through navigation, reload and history traversal", async () => {
    const c = client({ total: 3 });
    const { unmount } = await frame(`${HISTORY}?revision_id=${rid(1)}`, c);
    expect(q("[data-finding-history]")).toHaveAttribute("data-finding-revision", rid(1));

    // old -> new: select version 3 by its exact ID.
    fireEvent.click(q(`[data-history-select='${rid(3)}']`) as HTMLElement);
    await settledScreen();
    expect(where()).toBe(`${HISTORY}?revision_id=${rid(3)}`);
    expect(q("[data-finding-history]")).toHaveAttribute("data-finding-revision", rid(3));
    expect(q("[data-history-pinned-latest]")).not.toBeNull();

    // new -> Evidence: the section link carries the same exact ID.
    fireEvent.click(q("[data-finding-section='evidence']") as HTMLElement);
    await settledScreen();
    expect(where()).toBe(`${EVIDENCE}?revision_id=${rid(3)}`);
    expect(c.asked[c.asked.length - 1]).toEqual({ view: "evidence", revisionId: rid(3) });

    // Evidence -> old: back twice reaches version 1, read by its exact ID again.
    fireEvent.click(screen.getByText("test-back"));
    await settledScreen();
    expect(where()).toBe(`${HISTORY}?revision_id=${rid(3)}`);
    fireEvent.click(screen.getByText("test-back"));
    await settledScreen();
    expect(where()).toBe(`${HISTORY}?revision_id=${rid(1)}`);
    expect(q("[data-finding-history]")).toHaveAttribute("data-finding-revision", rid(1));
    expect(c.asked[c.asked.length - 1]).toEqual({ view: "history", revisionId: rid(1), after: 0 });

    // Forward returns to the new version.
    fireEvent.click(screen.getByText("test-forward"));
    await settledScreen();
    expect(q("[data-finding-history]")).toHaveAttribute("data-finding-revision", rid(3));

    // Reload of the old address: a fresh mount reads the same exact ID, even after a later append.
    unmount();
    const appended = client({ total: 4 });
    await frame(`${HISTORY}?revision_id=${rid(1)}`, appended);
    expect(appended.asked[0]).toEqual({ view: "history", revisionId: rid(1), after: 0 });
    expect(q("[data-finding-history]")).toHaveAttribute("data-finding-revision", rid(1));
    expect(q("[data-history-earlier-version]")).toHaveTextContent("version 4 replaces it");
  });

  it("labels an omitted version as latest at read time, and a reload after an append moves it", async () => {
    const before = client({ total: 2 });
    const { unmount } = await frame(HISTORY, before);
    expect(q("[data-history-latest-at-read]")).toHaveTextContent("version 2");
    unmount();
    const after = client({ total: 3 });
    await frame(HISTORY, after);
    expect(q("[data-history-latest-at-read]")).toHaveTextContent("version 3");
    expect(after.asked[0]?.revisionId).toBeNull();
  });
});

describe("Finding to Financials bridge link (S4-02a)", () => {
  it("carries the Finding ID and the pinned version", async () => {
    await frame(`${HISTORY}?revision_id=${rid(2)}`, client({ total: 3 }));
    expect(q("[data-finding-financials-link] a")).toHaveAttribute(
      "href",
      `/sites/${SITE}/financials?finding_id=${F}&revision_id=${rid(2)}`,
    );
  });
});

/** W1-UX-02: a state whose read records no time: explicit checks instead of `expectStateLineVisible`. */
function expectUntimedStateLine(card: Element): string {
  const status = card.querySelector("[data-product-status]");
  expect(status, "a shared state line is rendered").not.toBeNull();
  for (const selector of ["[data-product-status-label]", ".product-status__sentence", "[data-product-status-scope]", "[data-product-status-as-of]"]) {
    const el = status!.querySelector(selector);
    expect(el, selector).not.toBeNull();
    expect((el!.textContent ?? "").trim().length, `${selector} has text`).toBeGreaterThan(0);
    expect(visibleOutsideClosedDisclosure(el!), `${selector} is outside any closed disclosure`).toBe(true);
  }
  expect(status!.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
  return status!.querySelector("[data-product-status-label]")?.textContent ?? "";
}

describe("W1-UX-02: Finding History answer card", () => {
  /** W1-F3: the single v69 panel "Revision history" (formerly the answer card). */
  const card = () => panelTitled("Revision history");
  const main = () => document.querySelector("main") as HTMLElement;
  const versionNos = () => all("[data-history-revision]").map((r) => Number(r.getAttribute("data-history-revision-no")));

  it("W1-F3: the Revision history panel states how the conclusion changed in its summary line and table; revision and page cutoff references are labelled detail; W1 vocabulary on <main>", async () => {
    await frame(HISTORY, client({ total: 205 }));
    const answer = card();
    expect(answer.querySelector(".panel__description")?.textContent).toBe("How did the conclusion and workflow change?");
    expect(answer.querySelector("[data-history-summary]")?.textContent).toBe("205 recorded versions; the latest records: Open");
    expect(expectStateLineVisible(answer)).toBe("Latest recorded version when read");
    expect(answer.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    // The plain "as of" is the selected version's recorded time (version 205: 6 Oct 14:00 + 2050 min).
    expect(answer.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of 8 Oct 2026, 00:10 UTC");
    // The mock's Time / Event / Basis table lists every version oldest first, inside the panel.
    expect(versionNos()).toEqual(Array.from({ length: 205 }, (_, i) => i + 1));
    expect(answer.querySelector(`[data-history-revision='${rid(1)}']`)).toHaveTextContent("Version 1 · Opened");
    expect(answer.querySelector(`[data-history-revision='${rid(205)}']`)).toHaveTextContent(
      "Version 205 · Assessment updated; amount unchanged",
    );
    const refs = answer.querySelector("details[data-exact-references]") as HTMLDetailsElement;
    expect(refs.open).toBe(false);
    expect(answer.querySelector(".panel__body")?.lastElementChild).toBe(refs);
    const rows = Array.from(refs.querySelectorAll(".exact-references__row")).map((r) => [r.querySelector("dt")?.textContent, r.querySelector("code")?.textContent]);
    expect(rows).toEqual([
      ["Finding reference", F],
      ["Selected version reference", rid(205)],
      ["Latest version reference", rid(205)],
      ["How the version was chosen", "LATEST_RECORDED"],
      ["First page ends after version", "100"],
    ]);
    // Exact selectors from the card.
    expect(q("[data-history-open-finding]")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}?revision_id=${rid(205)}`);
    expect(q("[data-history-open-evidence]")).toHaveAttribute("href", `${EVIDENCE}?revision_id=${rid(205)}`);
    const w1 = scanProductVocabulary(main(), "finding history (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(100);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    const disclosure = scanDisclosureVocabulary(answer, "finding history exact references");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.scanned).toBeGreaterThan(5);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
  });

  it("W1-UX-02: a historical selection keeps its plain as-of visible and its exact version selector", async () => {
    await frame(`${HISTORY}?revision_id=${rid(1)}`, client({ total: 3 }));
    expect(expectStateLineVisible(card())).toBe("Earlier version, kept for the record");
    expect(card().querySelector("[data-product-status-as-of]")?.textContent).toBe("As of 6 Oct 2026, 14:10 UTC");
    expect(q("[data-history-select-latest]")).toHaveAttribute("href", `${HISTORY}?revision_id=${rid(3)}`);
    expect(q("[data-history-open-finding]")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}?revision_id=${rid(1)}`);
    const w1 = scanProductVocabulary(main(), "finding history earlier (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("W1-F3: a limited (incomplete) list says so in the summary line and lists only the versions read", async () => {
    await frame(HISTORY, client({ total: 205, failAfter: 100 }));
    expect(card().querySelector("[data-history-summary]")?.textContent).toBe("Only 100 of 205 recorded versions could be read");
    expect(card().querySelector("[data-history-incomplete]")).toHaveTextContent("this list is incomplete");
    expect(versionNos()).toHaveLength(100);
    // The selected (latest) version was not among the pages read: its time is not recorded here, never "now".
    expect(expectUntimedStateLine(card())).toBe("Latest recorded version when read");
    const w1 = scanProductVocabulary(main(), "finding history incomplete (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("W1-UX-02: a record-only and a no-longer-supported history keep the state line visible", async () => {
    await frame(`${HISTORY}?revision_id=${rid(2)}`, client({
      total: 2,
      body: {
        audit_only: { non_current: true, reason: "CLOSED", statement: "Audit material only" },
        state: { lifecycle: "NO_LONGER_SUPPORTED", latest_transition: "NO_LONGER_SUPPORTED", note: "" },
      },
    }));
    expect(expectStateLineVisible(card())).toBe("For the record only");
    expect(card().querySelector("[data-history-summary]")?.textContent).toBe("2 recorded versions; the latest records: No longer supported");
    expect(card().querySelector("[data-history-lifecycle='NO_LONGER_SUPPORTED']")?.closest("[data-product-status]")).not.toBeNull();
    const w1 = scanProductVocabulary(main(), "finding history record only (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it.each([
    ["forbidden", "This cannot be shown to you"],
    ["closed", "Not released for use yet"],
    ["unavailable", "This could not be read right now"],
  ] as const)("W1-UX-02: a %s read shows a plain state line and lists no versions", async (status, label) => {
    const c: FindingClient = {
      ...client({ total: 1 }),
      getFindingHistory: async () => (status === "closed" ? { status, message: null, note: null } : { status, message: null }),
    };
    await frame(HISTORY, c);
    expect(expectUntimedStateLine(card())).toBe(label);
    expect(all("[data-history-revision]")).toHaveLength(0);
    const w1 = scanProductVocabulary(main(), `finding history ${status} (W1)`, { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("W1-UX-02: an unknown pinned version is refused with a plain state line, keeping the address", async () => {
    await frame(`${HISTORY}?revision_id=rev-9999`, client({ total: 3 }));
    expect(expectUntimedStateLine(card())).toBe("This record was not found");
    expect(where()).toBe(`${HISTORY}?revision_id=rev-9999`);
  });
});

describe("W1-F3: Finding History renders exactly the v69 panel (finding-history)", () => {
  const panel = () => panelTitled("Revision history");

  it("stocked: one panel 'Revision history' with the table, related Findings and references inside it", async () => {
    await frame(`${HISTORY}?revision_id=${rid(1)}`, client({ total: 3 }));
    expectV69Panels("finding-history");
    expect(document.querySelector("[data-headline-card]"), "no lead card").toBeNull();
    expect(panel().querySelectorAll("table [data-history-revision]")).toHaveLength(3);
    expect(panel().querySelector("[data-history-earlier-version]"), "the selection note sits inside the panel").not.toBeNull();
    expect(panel().querySelector("h3"), "no per-version subsection headings").toBeNull();
    expect(panel().querySelector("details[data-exact-references]")).not.toBeNull();
  });

  it("stocked with relations: related Findings are one line inside the panel, not a second panel", async () => {
    await frame(HISTORY, client({
      total: 2,
      body: {
        relations: {
          merged_into: [],
          merged_from: [],
          split_from_finding_id: null,
          split_parts: [],
          recurs_after_finding_id: "f-earlier-0000",
          recurred_by: [],
        },
      } as never,
    }));
    expectV69Panels("finding-history");
    const line = panel().querySelector("[data-history-related-line]") as HTMLElement;
    expect(line).not.toBeNull();
    expect(line.querySelector("[data-history-related='f-earlier-0000']")).toHaveAttribute(
      "href",
      `/sites/${SITE}/findings/f-earlier-0000/history`,
    );
  });

  it("height phase: the default view shows the latest 3 versions; every earlier version stays reachable, oldest first, behind 'Show all N'", async () => {
    await frame(HISTORY, client({ total: 205 }));
    const shown = all("[data-history-revision]").filter((r) => visibleOutsideClosedDisclosure(r));
    expect(shown.map((r) => Number(r.getAttribute("data-history-revision-no")))).toEqual([203, 204, 205]);
    const showAll = panel().querySelector("details[data-show-all='finding-history-versions']") as HTMLDetailsElement;
    expect(showAll.open).toBe(false);
    expect(showAll.querySelector("summary")).toHaveTextContent("Show all 205 versions (202 earlier)");
    expect(Array.from(showAll.querySelectorAll("[data-history-revision]")).map((r) => Number(r.getAttribute("data-history-revision-no")))).toEqual(
      Array.from({ length: 202 }, (_, i) => i + 1),
    );
    // The state line, the completeness line and the replay disclaimer stay outside any closed disclosure.
    for (const sel of ["[data-history-state-line]", "[data-history-complete]", "[data-history-kept-as-recorded]"]) {
      expect(visibleOutsideClosedDisclosure(panel().querySelector(sel)!), sel).toBe(true);
    }
  });

  it("height phase: an earlier selected version hidden behind 'Show all' opens the expander so the selection is visible", async () => {
    await frame(`${HISTORY}?revision_id=${rid(2)}`, client({ total: 205 }));
    const showAll = panel().querySelector("details[data-show-all='finding-history-versions']") as HTMLDetailsElement;
    expect(showAll.open).toBe(true);
    expect(visibleOutsideClosedDisclosure(panel().querySelector(`[data-history-revision='${rid(2)}']`)!)).toBe(true);
  });

  it("height phase: three or fewer versions need no expander", async () => {
    await frame(HISTORY, client({ total: 3 }));
    expect(panel().querySelector("[data-show-all]")).toBeNull();
  });

  it("one version: the same panel says 'No earlier versions.'", async () => {
    await frame(HISTORY, client({ total: 1 }));
    expectV69Panels("finding-history");
    expect(panel().querySelector("[data-history-no-earlier]")).toHaveTextContent(/^No earlier versions\./);
    expect(panel().querySelectorAll("[data-history-revision]")).toHaveLength(1);
  });

  it.each(["not_found", "forbidden", "closed", "unavailable"] as const)(
    "refused (%s): the same panel with the state line and an in-panel gap, no versions",
    async (status) => {
      const c: FindingClient = {
        ...client({ total: 1 }),
        getFindingHistory: async () => (status === "closed" ? { status, message: null, note: null } : { status, message: null }),
      };
      await frame(HISTORY, c);
      expectV69Panels("finding-history");
      expect(document.querySelector("[data-headline-card]"), "no refusal card").toBeNull();
      expect(panel().querySelector("[data-product-status]")).not.toBeNull();
      expect(panel().querySelector(`[data-history-gap] [data-finding-read='${status}']`)).not.toBeNull();
      expect(all("[data-history-revision]")).toHaveLength(0);
    },
  );
});
