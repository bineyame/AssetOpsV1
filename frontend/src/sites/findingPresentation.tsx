/**
 * Shared pieces of the one canonical Finding presentation (T028): the claim
 * badge, evidence-link lists, the claim drawer and the Findings table. Finding
 * detail, Performance > Dispatch, Site > Findings and the global Findings
 * index all render through these, so an assessment reads the same wherever it
 * is opened.
 */
import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Badge, DataTable, Fact, FactList } from "../ui";
import { RecordDetail } from "./SiteEvidence";
import type {
  AssessmentSummary,
  ClaimLevel,
  EvidenceLink,
} from "./siteAnalyticsClient";
import type {
  EvidenceRead,
  EvidenceRecordDetail,
  SiteEvidenceClient,
} from "./siteEvidenceClient";

/** The backend's claim-level word, shown as it arrives with its level kept as data. */
export function ClaimBadge({ level, label }: { level: ClaimLevel | string; label: string }) {
  return (
    <span className="claim-badge" data-claim-level={level}>
      <Badge tone="neutral">{label}</Badge>
    </span>
  );
}

/** "low to high h", or "at least low h" when the upper bound is open. */
export function boundText(
  bound: { low: string; high?: string | null } | undefined,
  unit: string,
): string {
  if (bound === undefined) {
    return "none";
  }
  if (bound.high === undefined) {
    return `${bound.low} ${unit}`;
  }
  if (bound.high === null) {
    return `at least ${bound.low} ${unit} (upper bound open)`;
  }
  return bound.low === bound.high
    ? `${bound.low} ${unit}`
    : `${bound.low} to ${bound.high} ${unit}`;
}

export function windowText(window: { start: string; end: string }): string {
  return `${window.start} to ${window.end}`;
}

/** Opens one accepted record in the claim drawer, naming the claim it supports. */
export type OpenRecord = (link: EvidenceLink, claim: string) => void;

export function EvidenceLinks({
  links,
  claim,
  open,
}: {
  links: EvidenceLink[];
  claim: string;
  open: OpenRecord;
}) {
  if (links.length === 0) {
    return <span className="overview-note">No accepted record referenced.</span>;
  }
  return (
    <ul className="cell-list evidence-links">
      {links.map((link) => (
        <li key={link.message_id}>
          <button
            type="button"
            className="link-button"
            data-evidence-link={link.message_id}
            onClick={() => open(link, claim)}
          >
            {`${link.device_id} / ${link.signal_id} at ${link.source_time}`}
          </button>
        </li>
      ))}
    </ul>
  );
}

export const CLAIM_DRAWER_ID = "finding-claim-drawer";

/**
 * The claim drawer: claim-specific lineage for one accepted record. It reuses
 * T027's record inspector detail (`RecordDetail`) for the record itself, and
 * adds what the claim adds: which claim the record supports, the assessed
 * window and the algorithm version. Its open state is a query parameter, so
 * opening it never changes the root or the path.
 */
export function ClaimDrawer({
  siteId,
  messageId,
  claim,
  assessedWindow,
  modelVersion,
  evidence,
  onClose,
}: {
  siteId: string;
  messageId: string;
  claim: string | null;
  assessedWindow: { start: string; end: string };
  modelVersion: string;
  evidence: SiteEvidenceClient;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<EvidenceRead<EvidenceRecordDetail> | null>(null);
  useEffect(() => {
    let active = true;
    setDetail(null);
    void evidence.getRecord(siteId, messageId).then((loaded) => {
      if (active) {
        setDetail(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [evidence, siteId, messageId]);

  return (
    <aside
      id={CLAIM_DRAWER_ID}
      className="claim-drawer"
      aria-labelledby="finding-claim-drawer-heading"
      data-claim-drawer={messageId}
    >
      <div className="claim-drawer__head">
        <h2 id="finding-claim-drawer-heading" className="claim-drawer__title">
          Claim evidence
        </h2>
        <button type="button" onClick={onClose}>
          Close evidence
        </button>
      </div>
      <FactList>
        <Fact term="Claim">{claim ?? "Not named"}</Fact>
        <Fact term="Assessed window">{windowText(assessedWindow)}</Fact>
        <Fact term="Algorithm version">{modelVersion}</Fact>
      </FactList>
      <RecordDetail detail={detail} />
    </aside>
  );
}

export type FindingsRow = AssessmentSummary & {
  site_id?: string;
  site_display_name?: string;
  site_type?: string;
};

/** A Findings table row target: where a row click goes. */
export type FindingHref = (row: AssessmentSummary & { site_id?: string }) => string;

/**
 * One Findings table for both indexes. A row click changes the root to the
 * Finding. It carries no KPI strip and no status model of its own: the claim
 * level and confidence are the backend's.
 */
export function FindingsTable({
  rows,
  labelledBy,
  href,
  findingType,
  siteColumn,
}: {
  rows: FindingsRow[];
  labelledBy: string;
  href: FindingHref;
  findingType: (id: string, row?: FindingsRow) => string;
  siteColumn: boolean;
}) {
  const navigate = useNavigate();
  return (
    <DataTable labelledBy={labelledBy}>
      <thead>
        <tr>
          <th scope="col">Finding</th>
          {siteColumn ? <th scope="col">Site</th> : null}
          <th scope="col">Type</th>
          <th scope="col">Claim</th>
          <th scope="col">Interval</th>
          <th scope="col">Confidence</th>
          <th scope="col">Revision</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr
            key={`${row.site_id ?? ""}-${row.assessment_id}`}
            className="clickable-row"
            data-finding-row={row.assessment_id}
            onClick={() => navigate(href(row))}
          >
            <th scope="row">
              <Link to={href(row)} onClick={(event) => event.stopPropagation()}>
                {row.summary}
              </Link>
            </th>
            {siteColumn ? (
              <td>{`${row.site_display_name ?? row.site_id ?? ""} · ${row.site_id ?? ""}`}</td>
            ) : null}
            <td>{findingType(row.finding_type, row)}</td>
            <td>
              <ClaimBadge level={row.claim_level} label={row.label} />
            </td>
            <td>{`${row.interval.first_running_observed} to ${row.interval.last_running_observed}`}</td>
            <td>{confidenceWord(row.confidence)}</td>
            <td>{`${row.revision} of ${row.revisions}`}</td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
}

const CONFIDENCE_WORDS: Record<string, string> = {
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
  NOT_APPLICABLE: "Not applicable",
};

export function confidenceWord(level: string): string {
  return CONFIDENCE_WORDS[level] ?? level;
}

export function Section({
  heading,
  id,
  children,
}: {
  heading: string;
  id: string;
  children: ReactNode;
}) {
  return (
    <section className="finding-section" aria-labelledby={id}>
      <h3 id={id} className="finding-section__heading">
        {heading}
      </h3>
      {children}
    </section>
  );
}
