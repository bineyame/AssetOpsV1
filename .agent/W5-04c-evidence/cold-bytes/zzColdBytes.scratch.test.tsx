// SCRATCH (not committed): W5-04c cold byte-identity probe. Renders every cold Action detail state and writes the
// settled document outerHTML per state to $COLD_BYTES_OUT. Run at base and head, then diff the two files.
import { cleanup, render, waitFor } from "@testing-library/react";
import { writeFileSync } from "node:fs";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, it, vi } from "vitest";

import { SiteActionFrame } from "../../shell/SiteAnalyticsFrames";
import { settledScreen } from "../../test/settled";
import { createDomainActionClient, type DomainActionClient, type DomainActionDetail, type DomainDetailResult } from "../domainActionClient";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { COLD_SITE, DOMAIN_ID, KNOWN, SITE, detailBody } from "./coldWorkFixtures";

const CRITERIA = [
  { key: "AUTOMATIC_START", label: "Automatic start", required_evidence: "Accepted command followed by successful running status" },
  { key: "POWER_DELIVERY", label: "Power delivery", required_evidence: "Generator supply reaches the cooling system" },
  { key: "COOLING_RECOVERY", label: "Cooling recovery", required_evidence: "Temperature recovery within declared test conditions" },
  { key: "RECURRENCE", label: "Recurrence", required_evidence: "Covered observation window without a qualifying repeat" },
];
const RESULTS = ["NOT_TESTED", "NOT_TESTED", "NOT_ESTABLISHED", "PENDING"];
const NO_WORK = { case_id: null, case_code: null, case_title: null, request_state: null, record_id: null, label: null, href: null };
const work = (request_state: string, record_id: string | null) => ({
  case_id: "c0ffee00-1111-4222-8333-444455556666",
  case_code: "WR-000019",
  case_title: "Starter/control inspection",
  request_state,
  record_id,
  label: "Maintenance request WR-000019",
  href: null,
});
function positive(over: Partial<DomainActionDetail> = {}): DomainActionDetail {
  const base = detailBody();
  return detailBody({
    intent: { ...(base.intent as NonNullable<DomainActionDetail["intent"]>), criteria: CRITERIA },
    results: CRITERIA.map((c, i) => ({ key: c.key, result: RESULTS[i], evidence_ids: [] })),
    links: { finding: base.links.finding, work: work("COMPLETED", "d00dfeed-1111-4222-8333-444455556666") },
    ...over,
  });
}
const L = (value: DomainActionDetail): DomainDetailResult => ({ status: "loaded", value });
const LONG = "X".repeat(160);

const STATES: Record<string, () => DomainDetailResult> = {
  positive: () => L(positive()),
  missingIntent: () => L(detailBody({ intent: null, results: null, links: { finding: detailBody().links.finding, work: NO_WORK } })),
  open: () => L(positive({ links: { finding: detailBody().links.finding, work: work("OPEN", null) } })),
  inProgress: () => L(positive({ links: { finding: detailBody().links.finding, work: work("IN_PROGRESS", null) } })),
  completedNoRecord: () => L(positive({ links: { finding: detailBody().links.finding, work: work("COMPLETED", null) } })),
  noCase: () => L(positive({ links: { finding: detailBody().links.finding, work: NO_WORK } })),
  historical: () => L(positive({ status: "HISTORICAL" })),
  pending: () => L(positive({ status: "PENDING_RECOMPUTE" })),
  stale: () => L(positive({ status: "STALE_SOURCE" })),
  unknown: () => L(positive({ status: "UNKNOWN" })),
  ownerNull: () => L(positive({ action: { ...detailBody().action, owner_label: null } })),
  long: () => L(positive({ action: { ...detailBody().action, title: LONG, owner_label: LONG } })),
  noRevision: () => L(positive({ intent: { ...(positive().intent as NonNullable<DomainActionDetail["intent"]>), basis: {} } })),
  notFound: () => ({ status: "not_found", http: 404, code: "ACTION_NOT_FOUND", message: "Action was not found at this site." }),
  refused503: () => ({ status: "refused", http: 503, code: "WORK_STORE_UNAVAILABLE", message: "The work store is unavailable." }),
  refused409: () => ({ status: "refused", http: 409, code: "DOMAIN_INTENT_BASIS_CHANGED", message: "The selected cold work basis changed; reload the Action." }),
  unreachable: () => ({ status: "refused", http: null, code: null, message: "The cold work read could not be reached." }),
};

const siteDetail = { getSite: async () => ({ status: "loaded", site: COLD_SITE }) } as unknown as SiteDetailClient;

function client(fn: () => DomainDetailResult | Promise<DomainDetailResult>): DomainActionClient {
  return { getIndex: vi.fn(), getDetail: vi.fn(async () => fn()) } as unknown as DomainActionClient;
}

function mount(path: string, c: DomainActionClient) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/sites/:siteId/actions/:actionId/:actionView" element={<SiteActionFrame detail={siteDetail} sitesPath="/sites" domainActions={c} />} />
        <Route path="/sites/:siteId/actions/:actionId" element={<SiteActionFrame detail={siteDetail} sitesPath="/sites" domainActions={c} />} />
      </Routes>
    </MemoryRouter>,
  );
}

const out: Record<string, string> = {};
afterEach(() => cleanup());

describe("cold bytes", () => {
  for (const [name, fn] of Object.entries(STATES)) {
    for (const query of ["", `?known_at=${encodeURIComponent(KNOWN)}`]) {
      it(`${name}${query}`, async () => {
        mount(`/sites/${SITE}/actions/${DOMAIN_ID}/verification${query}`, client(fn));
        await settledScreen();
        await waitFor(() => {
          if (document.querySelector("[data-domain-action-shell='loading']")) throw new Error("loading");
        });
        out[`${name}${query}`] = document.body.outerHTML;
      });
    }
  }
  it("loading", async () => {
    mount(`/sites/${SITE}/actions/${DOMAIN_ID}/verification`, client(() => new Promise<DomainDetailResult>(() => {})));
    await waitFor(() => {
      if (!document.querySelector("[data-domain-action-shell='loading']")) throw new Error("not yet");
    });
    out.loading = document.body.outerHTML;
  });
  it("redirect from bare and plan", async () => {
    for (const p of ["", "/plan"]) {
      mount(`/sites/${SITE}/actions/${DOMAIN_ID}${p}?known_at=${encodeURIComponent(KNOWN)}`, client(STATES.positive));
      await settledScreen();
      await waitFor(() => {
        if (!document.querySelector("[data-domain-action-shell='loaded']")) throw new Error("not yet");
      });
      out[`redirect${p}`] = document.body.outerHTML;
      cleanup();
    }
  });
  it("http client fallbacks", async () => {
    const cases: Record<string, () => Promise<Response>> = {
      net: async () => {
        throw new TypeError("network");
      },
      shape: async () => new Response(JSON.stringify({ nope: 1 }), { status: 200 }),
      bad503: async () => new Response("x", { status: 503 }),
    };
    for (const [k, f] of Object.entries(cases)) {
      vi.stubGlobal("fetch", vi.fn(f));
      mount(`/sites/${SITE}/actions/${DOMAIN_ID}/verification`, createDomainActionClient());
      await settledScreen();
      await waitFor(() => {
        if (!document.querySelector("[data-domain-action-panel='refused']")) throw new Error("not yet");
      });
      out[`http-${k}`] = document.body.outerHTML;
      cleanup();
      vi.unstubAllGlobals();
    }
  });
  it("write", () => {
    writeFileSync(process.env.COLD_BYTES_OUT ?? "cold-bytes.json", JSON.stringify(out, null, 1));
  });
});
