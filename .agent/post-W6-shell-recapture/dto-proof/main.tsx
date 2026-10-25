/* DTO RENDER PROOF (post-W6 shell Q23, Q24): the real App and route components, with every read answered by
   selected fixture DTOs modelled on the vitest fakes. Only the selected text fields are lengthened to 160 characters.
   This is NOT an app screenshot from a producer. */
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "../../../frontend/src/App";
import { featureFlagsWith } from "../../../frontend/src/config/featureFlags";
import "../../../frontend/src/ui/tokens.css";
import "../../../frontend/src/ui/primitives.css";
import type { SiteDetailClient, SiteDirectoryClient } from "../../../frontend/src/sites/siteDirectoryClient";
import type { FoundationReadModel, SiteFoundationClient } from "../../../frontend/src/sites/siteFoundationClient";
import type { LedgerRecordDetail, LedgerRecordPage } from "../../../frontend/src/sites/ledgerEvidenceClient";
import { EMPTY_ANALYTICS_CLIENT } from "../../../frontend/src/sites/__tests__/analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../../frontend/src/sites/__tests__/sldFixtures";
import {
  LEDGER_EVIDENCE,
  LEDGER_PAGE,
  LEDGER_RECORD,
  ledgerClient,
} from "../../../frontend/src/sites/__tests__/ledgerEvidenceFixtures";
import { foundation, PAST, VERSIONS } from "./foundationFixture";

/** A hyphenated identifier of exactly `n` characters, made of real words. */
export function long(seed: string, n = 160): string {
  const words = ["north", "feeder", "battery", "inverter", "string", "meter", "channel", "bank", "phase", "output", "cabinet", "relay"];
  let s = seed;
  let i = 0;
  while (s.length < n) s += "-" + words[i++ % words.length];
  return s.slice(0, n).replace(/-$/, "x");
}
/** Plain words of exactly `n` characters. */
export function longWords(seed: string, n = 160): string {
  return long(seed, n).replace(/-/g, " ");
}

const path = window.location.pathname;
const proof = path.includes("/foundation") ? "foundation" : "mini-evidence";
document.documentElement.dataset.dtoProof = proof;

let app: React.ReactNode;
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };

if (proof === "mini-evidence") {
  const [first] = LEDGER_PAGE.records;
  const sourceId = long("kobo-inverter-1-west");
  const records = [1, 2, 3, 4, 5].map((n) => ({
    ...first,
    evidence_id: `${first.evidence_id.slice(0, -1)}${n}`,
    message_id: long(`msg-000${n}`),
    role: null,
    signal_id: long(`ac-power-${n}`),
    device_id: long(`inv-${n}`),
    source: { ...first.source, external_id: sourceId },
    gateway: { ...first.gateway, external_id: long("kobo-gw-1-east") },
    source_time: `2026-09-22T${String(5 + n).padStart(2, "0")}:00:00Z`,
  }));
  const page: LedgerRecordPage = { ...LEDGER_PAGE, records, total: 5, next_cursor: null };
  const evidence = { ...LEDGER_EVIDENCE, sources: [{ ...LEDGER_EVIDENCE.sources[0], external_id: sourceId }] };
  const client = ledgerClient({ status: "loaded", value: evidence });
  (client.ledger as { listRecords: unknown }).listRecords = () => Promise.resolve({ status: "loaded", value: page });
  (client.ledger as { getRecord: unknown }).getRecord = (_site: string, key: string) => {
    const row = records.find((r) => r.evidence_id === key) ?? records[0];
    const detail: LedgerRecordDetail = { ...LEDGER_RECORD, ...row, receipt: LEDGER_RECORD.receipt };
    return Promise.resolve({ status: "loaded", value: detail });
  };
  const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };
  app = (
    <App
      flags={featureFlagsWith(false)}
      siteDirectory={directory}
      siteDetail={detail}
      siteEvidence={client}
      siteAnalytics={EMPTY_ANALYTICS_CLIENT}
    />
  );
} else {
  const site = HYBRID_MINI_GRID_SITE;
  const load = site.foundation.components.find((c) => c.component_type === "LOAD")!;
  const country = site.location.country;
  const longSite = {
    ...site,
    display_name: longWords("Kalangala", 160 - ` · ${site.site_id}`.length),
    location: { country, locality: longWords("Kalangala", 160 - `, ${country}`.length) },
    timezone: long("Africa/Kampala"),
    foundation: {
      ...site.foundation,
      components: site.foundation.components.map((c) =>
        c.component_id === load.component_id ? { ...c, display_name: longWords("Distribution load") } : c,
      ),
    },
  };
  const base = foundation(PAST, site.site_id, longSite);
  const value: FoundationReadModel = {
    ...base,
    assets: [
      { asset_id: "a-clinic", asset_code: "load-clinic", asset_type: "LOAD", display_name: longWords("Clinic", 52) },
      { asset_id: "a-res", asset_code: "load-res", asset_type: "LOAD", display_name: longWords("Residences", 52) },
    ],
    controls: {
      ...base.controls,
      critical_load_priority: { ...base.controls.critical_load_priority, members: ["load-clinic", "load-res", load.component_id] },
    },
  };
  const client: SiteFoundationClient = {
    getFoundation: () => Promise.resolve({ status: "loaded", value }),
    listVersions: () => Promise.resolve({ status: "loaded", value: VERSIONS }),
    publishReserve: () => Promise.reject(new Error("DTO proof: read-only")),
    publishBindings: () => Promise.reject(new Error("DTO proof: read-only")),
    snapshotUrl: (s: string, at: string) => `/api/sites/${s}/foundation/snapshot?at=${at}`,
  } as SiteFoundationClient;
  const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: longSite }) };
  app = (
    <App
      flags={featureFlagsWith(false)}
      siteDirectory={{ listSites: () => Promise.resolve({ status: "loaded", sites: [longSite] }) }}
      siteDetail={detail}
      siteAnalytics={EMPTY_ANALYTICS_CLIENT}
      siteFoundation={client}
    />
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>{app}</BrowserRouter>
  </React.StrictMode>,
);
