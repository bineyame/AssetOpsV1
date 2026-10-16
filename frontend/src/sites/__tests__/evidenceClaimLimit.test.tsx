/**
 * S3-02b: the selected assessment's claim limit on Evidence Analysis
 * (`evidence-analysis:2#b`). Payloads are S3-02a's normalised API samples
 * (`backend/tests/fixtures/s3_claim_limit_api_samples.json`) with each
 * normalised `<uuid>` replaced by a distinct ID so every link is exact.
 */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import samples from "../../../../backend/tests/fixtures/s3_claim_limit_api_samples.json";
import { settledScreen } from "../../test/settled";
import { expectStateLineVisible } from "../../test/productPresentation";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { currentnessWords, readResultWords } from "../../ui";
import {
  createClaimLimitClient,
  type AssessedDay,
  type ClaimLimitClient,
  type ClaimLimitRead,
  type ClaimLimitResult,
} from "../claimLimitClient";
import { EvidenceClaimLimit } from "../EvidenceClaimLimit";
import { SiteEvidence } from "../SiteEvidence";
import { LEDGER_EVIDENCE, ledgerClient } from "./ledgerEvidenceFixtures";

type SampleName = keyof typeof samples.responses;

let counter = 0;
function distinct(value: unknown): unknown {
  if (value === "<uuid>") {
    counter += 1;
    return `00000000-0000-4000-8000-${String(counter).padStart(12, "0")}`;
  }
  if (Array.isArray(value)) return value.map(distinct);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, distinct(v)]));
  }
  return value;
}

const REV = "11111111-1111-4111-8111-111111111111";
function sample(name: SampleName, revision: string | null = REV): ClaimLimitRead {
  const body = distinct(samples.responses[name]) as ClaimLimitRead;
  return { ...body, assessment_revision_id: body.assessment_revision_id === null ? null : revision };
}

const DAY_PERIODS: AssessedDay = {
  status: "CURRENT",
  periods: [
    { id: "22222222-2222-4222-8222-222222222222", scope: "WINDOW", start: "2026-10-06T00:00:00Z", end: "2026-10-07T00:00:00Z", claim_level: "LIMITED" },
    { id: REV, scope: "INTERVAL", start: "2026-10-06T08:00:00Z", end: "2026-10-06T08:30:00Z", claim_level: "CANDIDATE_AVOIDABLE" },
  ],
};

interface Call {
  day: string;
  revision: string | null;
  signal?: AbortSignal;
}

function fake(
  answer: (call: Call) => Promise<ClaimLimitResult<ClaimLimitRead>> | ClaimLimitResult<ClaimLimitRead>,
  day: ClaimLimitResult<AssessedDay> = { status: "loaded", value: DAY_PERIODS },
): ClaimLimitClient & { calls: Call[] } {
  const calls: Call[] = [];
  return {
    calls,
    getClaimLimit: async (_site, d, revision, signal) => {
      const call = { day: d, revision, signal };
      calls.push(call);
      return answer(call);
    },
    getAssessedDay: async () => day,
  };
}

function Where() {
  const at = useLocation();
  return <output data-testid="where">{at.search}</output>;
}

const dispatchHref = (day: string, rev: string) => `/sites/KOBO-001/performance/dispatch?day=${day}&revision=${rev}`;

function mount(client: ClaimLimitClient | undefined, search: string) {
  return render(
    <MemoryRouter initialEntries={[`/sites/KOBO-001/evidence${search}`]}>
      <Routes>
        <Route
          path="/sites/:siteId/evidence"
          element={
            <>
              <EvidenceClaimLimit siteId="KOBO-001" client={client} assessmentHref={dispatchHref} />
              <Where />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

function section(container: HTMLElement): HTMLElement {
  return container.querySelector("[data-claim-limit-section]") as HTMLElement;
}

function state(container: HTMLElement): HTMLElement {
  return container.querySelector("[data-claim-limit-state]") as HTMLElement;
}

/** The default reading: everything outside the closed technical disclosure. */
function plainText(container: HTMLElement): string {
  const copy = section(container).cloneNode(true) as HTMLElement;
  copy.querySelectorAll("[data-disclosure^='claim-limit-technical']").forEach((n) => n.remove());
  return copy.textContent ?? "";
}

const SEARCH = `?view=analysis&day=2026-10-06&revision=${REV}`;

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Evidence Analysis selected claim limit (S3-02b)", () => {
  it("states 'No assessment selected' without a day and reads nothing", async () => {
    const client = fake(() => ({ status: "loaded", value: sample("full-candidate") }));
    const { container } = mount(client, "?view=analysis");
    await settledScreen();
    expect(state(container).dataset.claimLimitState).toBe("no-day");
    expect(state(container).dataset.currentness).toBe("UNASSESSED");
    expect(section(container).textContent).toContain("No assessment selected");
    expect(client.calls).toHaveLength(0);
  });

  it("reads the day without a revision as UNASSESSED and lists the day's assessed periods", async () => {
    const client = fake(() => ({ status: "loaded", value: sample("no-revision-selected", null) }));
    const { container } = mount(client, "?view=analysis&day=2026-10-06");
    await settledScreen();
    expect(client.calls).toEqual([expect.objectContaining({ day: "2026-10-06", revision: null })]);
    expect(state(container).dataset.currentness).toBe("UNASSESSED");
    expect(state(container).dataset.ceiling).toBe("");
    expect(section(container).textContent).toContain("No assessment selected");
    const periods = container.querySelectorAll("[data-assessed-period]");
    expect([...periods].map((a) => a.textContent)).toEqual(["Whole day", "08:00–08:30 UTC"]);
  });

  it("does not read the legacy `assessment` parameter as the selection", async () => {
    const client = fake(() => ({ status: "loaded", value: sample("no-revision-selected", null) }));
    mount(client, `?view=analysis&day=2026-10-06&assessment=${REV}`);
    await settledScreen();
    expect(client.calls[0].revision).toBeNull();
  });

  it("full coverage: a current Candidate ceiling in plain words, technical facts behind a closed disclosure", async () => {
    const client = fake(() => ({ status: "loaded", value: sample("full-candidate") }));
    const { container } = mount(client, SEARCH);
    await settledScreen();
    expect(client.calls[0]).toEqual(expect.objectContaining({ day: "2026-10-06", revision: REV }));
    const s = state(container);
    expect(s.dataset.currentness).toBe("CURRENT");
    expect(s.dataset.ceiling).toBe("CANDIDATE_AVOIDABLE");
    expect(s.dataset.support).toBe("COMPLETE");
    expect(container.querySelector("[data-claim-limit-headline]")?.textContent).toBe(
      "The readings support calling this period of generator operation avoidable for 30 min. Every reading it needs is present for that time.",
    );
    const rows = [...container.querySelectorAll("tr[data-claim-role]")];
    expect(rows.map((r) => r.getAttribute("data-claim-role"))).toEqual([
      "generator_state",
      "feeder_demand",
      "pv_available_power",
      "pcs_discharge_capability",
      "battery_soc",
    ]);
    expect(rows.every((r) => r.getAttribute("data-role-status") === "COVERED")).toBe(true);
    expect(container.querySelector(".claim-limit__when")?.textContent).toBe("2026-10-06, 08:00–08:30 UTC");
    const plain = plainText(container);
    for (const internal of ["s3-claim-limit-1", "CANDIDATE_AVOIDABLE", "COMPLETE", "dispatch-3.2", REV, "pv_available_power"]) {
      expect(plain).not.toContain(internal);
    }
    const technical = container.querySelector("[data-disclosure='claim-limit-technical']") as HTMLDetailsElement;
    expect(technical.open).toBe(false);
    expect(technical.textContent).toContain("s3-claim-limit-1");
    expect(technical.textContent).toContain(REV);
    expect(technical.textContent).toContain("dispatch-3.2");
    expect(technical.textContent).toContain("SELECTED_UNIQUE");
  });

  it("missing PV: Indeterminate, the missing span named, no positive claim", async () => {
    const { container } = mount(fake(() => ({ status: "loaded", value: sample("missing-pv") })), SEARCH);
    await settledScreen();
    expect(state(container).dataset.ceiling).toBe("INDETERMINATE");
    expect(state(container).dataset.support).toBe("NONE");
    expect(container.querySelector("[data-claim-limit-headline]")?.textContent).toContain("cannot support a conclusion");
    const pv = container.querySelector("tr[data-claim-role='pv_available_power']") as HTMLElement;
    expect(pv.dataset.roleStatus).not.toBe("COVERED");
    expect(pv.textContent).toContain("missing 08:00–08:30 UTC");
    expect(container.querySelector("[data-claim-limit-reasons]")?.textContent).toContain("Solar power available missing");
  });

  it("poor quality and conflicting reports: a limited ceiling over the covered minutes only", async () => {
    const { container } = mount(fake(() => ({ status: "loaded", value: sample("poor-quality-conflict") })), SEARCH);
    await settledScreen();
    expect(state(container).dataset.support).toBe("LIMITED");
    expect(container.querySelector("[data-claim-limit-headline]")?.textContent).toContain("avoidable for at most 5 min");
    const pcs = container.querySelector("tr[data-claim-role='pcs_discharge_capability']") as HTMLElement;
    expect(pcs.textContent).toContain("unreliable readings 08:05–08:20 UTC");
    const pv = container.querySelector("tr[data-claim-role='pv_available_power']") as HTMLElement;
    expect(pv.textContent).toContain("conflicting reports 08:20–08:30 UTC");
    const reasons = container.querySelector("[data-claim-limit-reasons]")?.textContent ?? "";
    expect(reasons).toContain("Battery output limit: unreliable readings, 08:05–08:20 UTC.");
    expect(reasons).toContain("Solar power available: conflicting reports, 08:20–08:30 UTC.");
  });

  it.each([
    ["late-revision/withdrawn", "HISTORICAL", "earlier version"],
    ["stale-selection", "STALE_PROJECTION", "being redone"],
  ] as const)("%s: audit only, never a current positive claim", async (name, currentness, words) => {
    const { container } = mount(fake(() => ({ status: "loaded", value: sample(name) })), SEARCH);
    await settledScreen();
    const s = state(container);
    expect(s.dataset.currentness).toBe(currentness);
    expect(s.dataset.ceiling).toBe("");
    const headline = container.querySelector("[data-claim-limit-headline]")?.textContent ?? "";
    expect(headline).toContain(words);
    expect(headline).toMatch(/no current conclusion/i);
    expect(container.querySelector("[data-claim-limit-earlier]")?.textContent).toContain("At the time, this version said:");
  });

  it("a withdrawn whole-day revision lists its earlier per-period ceilings as history", async () => {
    const { container } = mount(fake(() => ({ status: "loaded", value: sample("late-revision/withdrawn-window") })), SEARCH);
    await settledScreen();
    expect(state(container).dataset.currentness).toBe("HISTORICAL");
    expect(container.querySelector("[data-claim-limit-intervals]")?.getAttribute("data-claim-limit-intervals")).toBe("earlier");
  });

  it("a whole-day read states its coverage in minutes derived from the spans, never 0", async () => {
    const read = sample("late-revision/withdrawn-window");
    const { container } = mount(fake(() => ({ status: "loaded", value: read })), SEARCH);
    await settledScreen();
    const rows = [...container.querySelectorAll<HTMLElement>("tr[data-claim-role]")];
    expect(rows.length).toBeGreaterThan(0);
    for (const row of rows) {
      expect(row.textContent).toContain("30 min of 30 min");
      expect(row.textContent).not.toMatch(/(^|\D)0 min of/);
      expect(row.getAttribute("data-role-status")).toBe("COVERED");
    }
  });

  it.each(["late-revision/withdrawn-window", "stale-selection/window"] as const)(
    "%s: the whole day's per-period list is introduced as history, with each period's time",
    async (name) => {
      const { container } = mount(fake(() => ({ status: "loaded", value: sample(name) })), SEARCH);
      await settledScreen();
      expect(container.querySelector("[data-claim-limit-earlier-periods]")?.textContent).toContain("At the time, this version listed");
      expect(container.querySelector("[data-claim-limit-intervals]")?.getAttribute("data-claim-limit-intervals")).toBe("earlier");
      expect(container.querySelector("[data-claim-limit-window-level]")).toBeNull();
    },
  );

  it("a current whole day shows its own level and each period's time range", async () => {
    const base = sample("late-revision/withdrawn-window");
    const item = base.claim_limit!.historical_ceiling!.interval_ceilings![0];
    const read = {
      ...base,
      currentness: "CURRENT",
      claim_limit: { ...base.claim_limit!, ceiling: null, support: "COMPLETE", interval_ceilings: [item], current_positive_claim: false },
    } as ClaimLimitRead;
    const day: AssessedDay = {
      status: "CURRENT",
      periods: [{ id: item.assessment_revision_id, scope: "INTERVAL", start: "2026-10-13T08:00:00Z", end: "2026-10-13T08:30:00Z", claim_level: "CANDIDATE_AVOIDABLE" }],
    };
    const { container } = mount(fake(() => ({ status: "loaded", value: read }), { status: "loaded", value: day }), SEARCH);
    await settledScreen();
    expect(container.querySelector("[data-claim-limit-window-level]")?.textContent).toContain("every reading needed is present");
    expect(container.querySelector("[data-claim-limit-intervals]")?.textContent).toContain("Period 08:00–08:30 UTC");
  });

  it("links every selected accepted ID to its exact Evidence drill-down, keeping day and revision", async () => {
    const read = sample("full-candidate");
    const { container } = mount(fake(() => ({ status: "loaded", value: read })), SEARCH);
    await settledScreen();
    const accepted = [...container.querySelectorAll<HTMLAnchorElement>("a[data-accepted-evidence]")];
    expect(accepted.map((a) => a.dataset.acceptedEvidence)).toEqual(read.accepted_evidence_ids);
    for (const a of accepted) {
      const q = new URLSearchParams(a.getAttribute("href")?.split("?")[1]);
      expect(q.get("record")).toBe(a.dataset.acceptedEvidence);
      expect(q.get("day")).toBe("2026-10-06");
      expect(q.get("revision")).toBe(REV);
      expect(q.get("view")).toBe("analysis");
    }
    const roles = read.capability?.roles ?? {};
    const roleIds = (read.capability?.required_roles ?? []).flatMap((key) => roles[key].evidence_ids);
    const roleLinks = [...container.querySelectorAll<HTMLAnchorElement>("a[data-claim-record]")];
    expect(roleLinks.map((a) => a.dataset.claimRecord)).toEqual(roleIds);
    fireEvent.click(roleLinks[0]);
    expect(screen.getByTestId("where").textContent).toContain(`record=${roleIds[0]}`);
    expect(screen.getByTestId("where").textContent).toContain(`revision=${REV}`);
  });

  it("links the pinned revision to Performance › Dispatch", async () => {
    const { container } = mount(fake(() => ({ status: "loaded", value: sample("full-candidate") })), SEARCH);
    await settledScreen();
    expect(container.querySelector("a[data-claim-limit-pinned]")?.getAttribute("href")).toBe(dispatchHref("2026-10-06", REV));
  });

  it("selects a period from the keyboard-reachable list; the address carries it and a reload reads the same revision", async () => {
    const client = fake(({ revision }) =>
      revision === null
        ? { status: "loaded", value: sample("no-revision-selected", null) }
        : { status: "loaded", value: sample("full-candidate", revision) },
    );
    const { container, unmount } = mount(client, "?view=analysis&day=2026-10-06");
    await settledScreen();
    const link = container.querySelector<HTMLAnchorElement>(`a[data-assessed-period='${REV}']`) as HTMLAnchorElement;
    expect(link.tagName).toBe("A");
    expect(link.getAttribute("href")).not.toBeNull();
    link.focus();
    expect(document.activeElement).toBe(link);
    fireEvent.click(link);
    await settledScreen();
    const search = screen.getByTestId("where").textContent ?? "";
    expect(new URLSearchParams(search).get("revision")).toBe(REV);
    expect(client.calls.at(-1)).toEqual(expect.objectContaining({ revision: REV }));
    expect(container.querySelector(`a[data-assessed-period='${REV}']`)?.getAttribute("aria-current")).toBe("true");
    unmount();
    const reloaded = fake(({ revision }) => ({ status: "loaded", value: sample("full-candidate", revision ?? REV) }));
    const again = mount(reloaded, search);
    await settledScreen();
    expect(reloaded.calls).toEqual([expect.objectContaining({ day: "2026-10-06", revision: REV })]);
    expect(state(again.container).dataset.currentness).toBe("CURRENT");
  });

  it("chooses a day with the form and clears any revision", async () => {
    const client = fake(() => ({ status: "loaded", value: sample("no-revision-selected", null) }));
    const { container } = mount(client, SEARCH);
    await settledScreen();
    const input = within(section(container)).getByLabelText("Assessment day (UTC)");
    fireEvent.change(input, { target: { value: "2026-10-08" } });
    fireEvent.submit(container.querySelector("[data-claim-limit-day-form]") as HTMLFormElement);
    await settledScreen();
    const q = new URLSearchParams(screen.getByTestId("where").textContent ?? "");
    expect(q.get("day")).toBe("2026-10-08");
    expect(q.get("revision")).toBeNull();
  });

  it("drops a superseded selection's late answer", async () => {
    const pending: Array<(r: ClaimLimitResult<ClaimLimitRead>) => void> = [];
    const client = fake(
      () => new Promise<ClaimLimitResult<ClaimLimitRead>>((resolve) => pending.push(resolve)),
    );
    const { container } = mount(client, "?view=analysis&day=2026-10-06&revision=first");
    await act(async () => {});
    const second = container.querySelector<HTMLAnchorElement>(`a[data-assessed-period='${REV}']`) as HTMLAnchorElement;
    fireEvent.click(second);
    await act(async () => {});
    expect(client.calls.map((c) => c.revision)).toEqual(["first", REV]);
    expect(client.calls[0].signal?.aborted).toBe(true);
    await act(async () => pending[1]({ status: "loaded", value: sample("missing-pv") }));
    await act(async () => pending[0]({ status: "loaded", value: sample("full-candidate", "first") }));
    await settledScreen();
    expect(state(container).dataset.ceiling).toBe("INDETERMINATE");
  });

  it.each([
    [401, { detail: { code: "UNAUTHENTICATED", message: "x" } }, "unauthenticated", "Sign in"],
    [403, { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "x" } }, "forbidden", "does not have access"],
    [404, { detail: "No imported Site 'NOPE' in this tenant." }, "not_found", "site was not found"],
    [404, { detail: { code: "ASSESSMENT_REVISION_NOT_FOUND", message: "x" } }, "not_found", "may belong to another site"],
    [422, { detail: { code: "REVISION_OUTSIDE_WINDOW", message: "x" } }, "refused", "different day"],
    [422, { detail: { code: "INVALID_REVISION_ID", message: "x" } }, "refused", "not a valid reference"],
    [422, { detail: { code: "UNSUPPORTED_RULE_VERSION", message: "x" } }, "refused", "rule is not supported"],
    [409, { detail: { code: "ACCEPTED_LINEAGE_ABSENT", message: "x" } }, "refused", "could not be traced"],
    [409, { detail: { code: "PERFORMANCE_CUTOVER_CLOSED", message: "x" } }, "closed", "not released"],
    [503, { detail: { code: "ASSESSMENT_STORE_UNAVAILABLE", message: "x" } }, "unavailable", "could not be read"],
  ] as const)("refuses visibly on %i (%s) through the real client", async (status, body, named, words) => {
    const paths: string[] = [];
    vi.stubGlobal("fetch", async (path: string) => {
      paths.push(path);
      if (!path.includes("/claim-limit")) {
        return new Response(JSON.stringify({ status: "CURRENT", intervals: [], window_assessment: null }), { status: 200 });
      }
      return new Response(JSON.stringify(body), { status });
    });
    const { container } = mount(createClaimLimitClient("/api/sites"), SEARCH);
    await settledScreen();
    expect(paths).toContain(`/api/sites/KOBO-001/performance/dispatch/windows/2026-10-06/claim-limit?revision=${REV}`);
    const s = state(container);
    expect(s.dataset.claimLimitState).toBe(named);
    expect(s.textContent).toContain(words);
    expect(container.querySelector("[data-claim-limit-headline]")).toBeNull();
  });

  it.each([
    ["another day", { day: "2026-10-07" }],
    ["another revision", { assessment_revision_id: "99999999-9999-4999-8999-999999999999" }],
  ])("the real client does not show a response for %s", async (_name, override) => {
    vi.stubGlobal("fetch", async (path: string) =>
      path.includes("/claim-limit")
        ? new Response(JSON.stringify({ ...sample("full-candidate"), ...override }), { status: 200 })
        : new Response(JSON.stringify({ status: "CURRENT", intervals: [], window_assessment: null }), { status: 200 }),
    );
    const { container } = mount(createClaimLimitClient("/api/sites"), SEARCH);
    await settledScreen();
    expect(state(container).dataset.claimLimitState).toBe("unavailable");
    expect(container.querySelector("[data-claim-limit-headline]")).toBeNull();
  });

  it("the real client maps the day's window read into assessed periods", async () => {
    vi.stubGlobal("fetch", async (path: string) =>
      path.includes("/claim-limit")
        ? new Response(JSON.stringify(sample("no-revision-selected", null)), { status: 200 })
        : new Response(
            JSON.stringify({
              status: "CURRENT",
              window_assessment: { id: "w", window_start: "2026-10-06T00:00:00Z", window_end: "2026-10-07T00:00:00Z", claim_level: "LIMITED" },
              intervals: [
                {
                  id: "i",
                  window_start: "2026-10-06T00:00:00Z",
                  window_end: "2026-10-07T00:00:00Z",
                  claim_level: "CANDIDATE_AVOIDABLE",
                  result: { segments: [{ start: "2026-10-06T08:15:00Z", end: "2026-10-06T08:30:00Z" }, { start: "2026-10-06T08:00:00Z", end: "2026-10-06T08:15:00Z" }] },
                },
              ],
            }),
            { status: 200 },
          ),
    );
    const { container } = mount(createClaimLimitClient("/api/sites"), "?view=analysis&day=2026-10-06");
    await settledScreen();
    expect([...container.querySelectorAll("[data-assessed-period]")].map((a) => a.getAttribute("data-assessed-period"))).toEqual(["w", "i"]);
    expect(container.querySelector("[data-assessed-period='i']")?.textContent).toBe("08:00–08:30 UTC");
  });
});

describe("the section on the Evidence Analysis page", () => {
  function page(search: string, claimLimit?: ClaimLimitClient) {
    const client = { ...ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }), claimLimit };
    return render(
      <MemoryRouter initialEntries={[`/sites/KOBO-001/evidence${search}`]}>
        <Routes>
          <Route
            path="/sites/:siteId/evidence"
            element={<SiteEvidence siteId="KOBO-001" client={client} assessmentHref={dispatchHref} />}
          />
        </Routes>
      </MemoryRouter>,
    );
  }

  it("sits beneath S2's own explanation on every Analysis view, unassessed when nothing is selected", async () => {
    const { container } = page("?view=analysis", fake(() => ({ status: "loaded", value: sample("full-candidate") })));
    await settledScreen();
    const s2 = container.querySelector("[data-evidence-claim-limit]") as HTMLElement;
    const s3 = section(container);
    expect(s2).not.toBeNull();
    expect(s3).not.toBeNull();
    expect(s2.compareDocumentPosition(s3) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(state(container).dataset.currentness).toBe("UNASSESSED");
  });

  it("is absent from the Overview", async () => {
    const { container } = page("", fake(() => ({ status: "loaded", value: sample("full-candidate") })));
    await settledScreen();
    expect(section(container)).toBeNull();
  });

  it("opens an accepted reading in the page's record inspector after the link is followed", async () => {
    const read = sample("full-candidate");
    const ledger = ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE });
    const { container } = render(
      <MemoryRouter initialEntries={[`/sites/KOBO-001/evidence${SEARCH}`]}>
        <Routes>
          <Route
            path="/sites/:siteId/evidence"
            element={<SiteEvidence siteId="KOBO-001" client={{ ...ledger, claimLimit: fake(() => ({ status: "loaded", value: read })) }} />}
          />
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
    const id = read.accepted_evidence_ids?.[0] as string;
    fireEvent.click(container.querySelector(`a[data-accepted-evidence='${id}']`) as HTMLElement);
    await settledScreen();
    expect(ledger.recordKeys).toContain(id);
  });
});

describe("W1-UX-03: evidence-analysis on the shared state line and span strip", () => {
  it("opts the selected assessment into the W1 vocabulary set; the default reading has no raw codes", async () => {
    for (const name of ["full-candidate", "missing-pv", "poor-quality-conflict", "stale-selection", "late-revision/withdrawn"] as const) {
      const { container, unmount } = mount(fake(() => ({ status: "loaded", value: sample(name) })), SEARCH);
      await settledScreen();
      const copy = section(container).cloneNode(true) as HTMLElement;
      // The S3-02b technical disclosure keeps its labelled exact references; everything else is the default reading.
      copy.querySelectorAll("[data-disclosure^='claim-limit-technical']").forEach((n) => n.remove());
      const scan = scanProductVocabulary(copy, `evidence-analysis ${name} (W1)`, { set: "w1" });
      expect(scan.scanned).toBeGreaterThan(10);
      expect(describeViolations(scan.violations)).toBe("");
      expect(plainText(container)).not.toMatch(/claim limit|ceiling/i);
      unmount();
    }
  });

  it("CURRENT is the only positive state line; it carries scope and 'as of' the read", async () => {
    const { container } = mount(fake(() => ({ status: "loaded", value: sample("full-candidate") })), SEARCH);
    await settledScreen();
    const s = state(container);
    expect(expectStateLineVisible(s)).toBe(currentnessWords("CURRENT").label);
    expect(s.querySelector("[data-product-status]")?.getAttribute("data-product-status")).toBe("positive");
    expect(s.querySelector("[data-product-status-scope]")?.textContent).toBe("2026-10-06, 08:00–08:30 UTC");
    expect(s.querySelector("[data-product-status-as-of]")?.textContent).toMatch(/^As of \d/);
  });

  it.each(["missing-pv", "poor-quality-conflict", "stale-selection", "late-revision/withdrawn"] as const)(
    "%s: a non-positive state line stays visible beside the headline", async (name) => {
    const { container } = mount(fake(() => ({ status: "loaded", value: sample(name) })), SEARCH);
    await settledScreen();
    const s = state(container);
    const label = expectStateLineVisible(s);
    expect(label.length).toBeGreaterThan(0);
    // An undetermined or limited period is current but not a positive state; audit-only versions never are.
    if (name === "missing-pv" || name === "stale-selection" || name === "late-revision/withdrawn") {
      expect(s.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    }
    expect(s.querySelector("[data-product-status-as-of]")?.textContent).toMatch(/^As of /);
  });

  it("an unknown currentness code falls back non-positively and never shows the code", async () => {
    const odd = { ...sample("full-candidate"), currentness: "SOMETHING_NEW" } as ClaimLimitRead;
    const { container } = mount(fake(() => ({ status: "loaded", value: odd })), SEARCH);
    await settledScreen();
    const s = state(container);
    expectStateLineVisible(s);
    expect(s.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    expect(plainText(container)).not.toContain("SOMETHING_NEW");
    expect(container.querySelector("[data-claim-limit-headline]")?.textContent).toBe("No conclusion is drawn from this assessment.");
  });

  it("draws covered and missing time per needed reading; a missing role is a 'not known' mark, never an empty bar", async () => {
    const { container } = mount(fake(() => ({ status: "loaded", value: sample("missing-pv") })), SEARCH);
    await settledScreen();
    const strip = container.querySelector("[data-period-strip='claim-limit-roles']") as HTMLElement;
    expect(strip).not.toBeNull();
    const pv = strip.querySelector("[data-period-strip-row='pv_available_power']") as HTMLElement;
    expect(pv.querySelector("[data-period-strip-segment='gap']")).not.toBeNull();
    expect(pv.textContent).toContain("missing 08:00–08:30 UTC");
    expect(strip.querySelectorAll("[data-period-strip-segment='covered']").length).toBeGreaterThan(0);

    const read = sample("missing-pv");
    const roles = { ...(read.capability?.roles ?? {}) };
    delete roles.pv_available_power;
    const withoutPv = { ...read, capability: { ...read.capability!, roles } } as ClaimLimitRead;
    const second = mount(fake(() => ({ status: "loaded", value: withoutPv })), SEARCH);
    await settledScreen();
    const row = second.container.querySelector("[data-period-strip='claim-limit-roles'] [data-period-strip-row='pv_available_power']") as HTMLElement;
    expect(row.dataset.periodStripKnown).toBe("not-known");
    expect(row.querySelector("[data-period-strip-mark='not-known']")).not.toBeNull();
    expect(row.querySelector("[data-period-strip-segment]")).toBeNull();
    expect(row.textContent).toContain("not known");
  });

  it.each([
    [{ status: "forbidden", message: null }, "refused"],
    [{ status: "unavailable", message: null }, "unavailable"],
    [{ status: "not_found", code: "ASSESSMENT_REVISION_NOT_FOUND", message: null }, "not-found"],
    [{ status: "refused", code: "REVISION_OUTSIDE_WINDOW", message: null }, "refused"],
  ] as const)("a refused or unread assessment keeps a plain non-positive state line (%o)", async (answer, kind) => {
    const { container } = mount(fake(() => answer as ClaimLimitResult<ClaimLimitRead>), SEARCH);
    await settledScreen();
    const s = state(container);
    expect(expectStateLineVisible(s)).toBe(readResultWords(kind).label);
    expect(s.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    expect(container.querySelector("[data-claim-limit-headline]")).toBeNull();
    expect(container.querySelector("[data-period-strip]")).toBeNull();
  });
});
