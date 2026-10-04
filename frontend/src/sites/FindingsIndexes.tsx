/**
 * The two Findings indexes (T028 AC21), over one table.
 *
 * - `FindingsIndex` is the Findings rail root's global index: every
 *   configured site's active Findings, each naming its site.
 * - `SiteFindings` is Site > Findings: the same rows for one site, with a
 *   claim-level filter, no KPI strip and no status model of its own.
 *
 * Both list Candidate avoidable and Indeterminate intervals only; a Necessary
 * interval is an assessment without a Finding (owner ruling 2026-10-03) and is
 * listed on Performance > Dispatch. A row click changes the root to the
 * Finding.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Panel } from "../ui";
import { FindingsTable } from "./findingPresentation";
import {
  findingTypeLabel,
  presentationProfileFor,
  type DomainPresentationProfile,
} from "./presentationProfile";
import type {
  AssessmentSummary,
  GlobalFindings,
  SiteAnalyticsClient,
  SiteFindings as SiteFindingsRead,
} from "./siteAnalyticsClient";
import type { EvidenceRead } from "./siteEvidenceClient";

function useRead<T>(load: () => Promise<EvidenceRead<T>>, deps: unknown[]) {
  const [result, setResult] = useState<EvidenceRead<T> | null>(null);
  useEffect(() => {
    let active = true;
    setResult(null);
    void load().then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, deps);
  return result;
}

function Unavailable({ message, id }: { message: string | null; id: string }) {
  return (
    <Panel heading="Findings unavailable" headingId={id}>
      <p>{message ?? "The Findings could not be read."}</p>
    </Panel>
  );
}

export interface FindingsIndexProps {
  client: SiteAnalyticsClient;
  /** A Finding's Overview, or another of its tabs (Analysis for the row's secondary link). */
  findingHref: (siteId: string, assessmentId: string, tab?: "analysis") => string;
}

export function FindingsIndex({ client, findingHref }: FindingsIndexProps) {
  const result = useRead<GlobalFindings>(() => client.getFindings(), [client]);
  if (result === null) {
    return <p>Loading the findings.</p>;
  }
  if (result.status !== "loaded") {
    return (
      <Unavailable
        id="findings-unavailable-heading"
        message={result.status === "unavailable" ? result.message : null}
      />
    );
  }
  const rows = result.value.findings;
  return (
    <section aria-labelledby="findings-index-heading" data-findings-index="global">
      <h2 id="findings-index-heading" className="identity-heading">
        Active Findings
      </h2>
      <p className="overview-note">{result.value.statement}</p>
      {rows.length === 0 ? (
        <p data-findings-empty>No site has an active Finding.</p>
      ) : (
        <FindingsTable
          rows={rows}
          labelledBy="findings-index-heading"
          siteColumn
          href={(row) => findingHref(row.site_id ?? "", row.assessment_id)}
          analysisHref={(row) => findingHref(row.site_id ?? "", row.assessment_id, "analysis")}
          findingType={(id, row) =>
            findingTypeLabel(
              row?.site_type === undefined ? null : presentationProfileFor(row.site_type),
              id,
            ).label
          }
        />
      )}
    </section>
  );
}

const FILTERS: { value: string; label: string }[] = [
  { value: "", label: "All Findings" },
  { value: "CANDIDATE_AVOIDABLE", label: "Possibly avoidable" },
  { value: "INDETERMINATE", label: "Cannot determine" },
];

export interface SiteFindingsProps {
  siteId: string;
  client: SiteAnalyticsClient;
  profile: DomainPresentationProfile | null;
  findingHref: (assessmentId: string, tab?: "analysis") => string;
  dispatchHref: string;
}

export function SiteFindings({
  siteId,
  client,
  profile,
  findingHref,
  dispatchHref,
}: SiteFindingsProps) {
  const result = useRead<SiteFindingsRead>(() => client.getSiteFindings(siteId), [client, siteId]);
  const [filter, setFilter] = useState("");
  if (result === null) {
    return <p>Loading the site&apos;s findings.</p>;
  }
  if (result.status !== "loaded") {
    return (
      <Unavailable
        id="site-findings-unavailable-heading"
        message={result.status === "unavailable" ? result.message : null}
      />
    );
  }
  const all: AssessmentSummary[] = result.value.findings;
  const rows = filter === "" ? all : all.filter((row) => row.claim_level === filter);
  return (
    <section aria-labelledby="site-findings-heading" data-findings-index="site">
      <h2 id="site-findings-heading" className="identity-heading">
        Findings at this site
      </h2>
      <p className="overview-note">
        Periods where the generator possibly operated longer than needed, or
        where that cannot be determined. Periods where it was needed have no
        Finding and are listed on{" "}
        <Link to={dispatchHref}>Performance &gt; Dispatch</Link>.
      </p>
      <p>
        <label>
          {"Outcome "}
          <select
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            data-findings-filter
          >
            {FILTERS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </p>
      {rows.length === 0 ? (
        <p data-findings-empty>
          {all.length === 0
            ? "This site has no active Finding."
            : "No Finding matches this filter."}
        </p>
      ) : (
        <FindingsTable
          rows={rows}
          labelledBy="site-findings-heading"
          siteColumn={false}
          href={(row) => findingHref(row.assessment_id)}
          analysisHref={(row) => findingHref(row.assessment_id, "analysis")}
          findingType={(id) => findingTypeLabel(profile, id).label}
        />
      )}
    </section>
  );
}
