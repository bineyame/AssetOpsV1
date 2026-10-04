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
  NextStep,
  Reading,
} from "./siteAnalyticsClient";
import type {
  EvidenceRead,
  EvidenceRecordDetail,
  SiteEvidenceClient,
} from "./siteEvidenceClient";
import { sourceReferences } from "./vocabularyReference";

/**
 * Display words for the three backend classifications, the same as the
 * backend's `plain.OUTCOMES` (D-2026-10-04-plain-language-analysis-views).
 * Used where only a level is at hand (revision history); everywhere else the
 * served `reading.outcome` is shown.
 */
export const OUTCOME_WORDS: Record<string, string> = {
  CANDIDATE_AVOIDABLE: "Possibly avoidable",
  NECESSARY: "Needed",
  INDETERMINATE: "Cannot determine",
};

/** An outcome word, shown as it arrives with its backend level kept as data. */
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
  return readablePeriod(window.start, window.end);
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function parts(iso: string): { day: string; time: string } | null {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  const pad = (n: number) => String(n).padStart(2, "0");
  return {
    day: `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`,
    time: `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}`,
  };
}

/**
 * A backend timestamp for reading, with its timezone named: "22 Sep 2026 03:05
 * UTC". Practitioner-first presentation: the ISO form stays in the record
 * detail; an unparseable value is shown as it arrived.
 */
export function readableTime(iso: string): string {
  const p = parts(iso);
  return p === null ? iso : `${p.day} ${p.time} UTC`;
}

/** "22 Sep 2026, 03:05 to 05:20 UTC", or both days when the period spans midnight. */
export function readablePeriod(start: string, end: string): string {
  const a = parts(start);
  const b = parts(end);
  if (a === null || b === null) {
    return `${start} to ${end}`;
  }
  return a.day === b.day
    ? `${a.day}, ${a.time} to ${b.time} UTC`
    : `${a.day} ${a.time} to ${b.day} ${b.time} UTC`;
}

/** Where a next step's link goes: an alternative, or the Site's evidence page. */
export type NextStepHref = (step: NextStep) => string | null;

/**
 * The backend's next steps for an assessment, each linked to what it concerns,
 * with the framing that they are checks and not instructions. Nothing here is
 * inferred: the steps are `reading.next_steps` as served.
 */
export function NextSteps({ reading, href }: { reading: Reading; href: NextStepHref }) {
  return (
    <>
      <ul className="cell-list" data-next-steps>
        {reading.next_steps.map((step) => {
          const to = href(step);
          return (
            <li key={step.id} data-next-step={step.id}>
              {to === null ? step.text : <Link to={to}>{step.text}</Link>}
            </li>
          );
        })}
      </ul>
      <p className="overview-note" data-next-step-framing>
        {reading.framing}
      </p>
    </>
  );
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
            {...sourceReferences(`${link.device_id} / ${link.signal_id}`)}
            onClick={() => open(link, claim)}
          >
            {`${link.device_id} / ${link.signal_id}, ${readableTime(link.source_time)}`}
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
          Supporting record
        </h2>
        <button type="button" onClick={onClose}>
          Close record
        </button>
      </div>
      <FactList>
        <Fact term="Supports">{claim ?? "Not named"}</Fact>
        <Fact term="Period assessed">{readablePeriod(assessedWindow.start, assessedWindow.end)}</Fact>
        <Fact term="Assessment method">{modelVersion}</Fact>
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
 * Finding's Overview; a secondary link opens the same Finding's Analysis. It
 * carries no KPI strip, severity or ranking: the outcome, confidence and
 * limitation are the backend's plain reading.
 */
export function FindingsTable({
  rows,
  labelledBy,
  href,
  analysisHref,
  findingType,
  siteColumn,
}: {
  rows: FindingsRow[];
  labelledBy: string;
  href: FindingHref;
  analysisHref: FindingHref;
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
          <th scope="col">Period</th>
          <th scope="col">Outcome</th>
          <th scope="col">Confidence and main limitation</th>
          <th scope="col">Analysis</th>
          <th scope="col">Type</th>
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
                {row.reading?.headline ?? "Assessed generator period"}
              </Link>
              {row.reading === undefined ? null : (
                <span className="overview-note" data-finding-row-reason>
                  {` ${row.reading.reason}`}
                </span>
              )}
            </th>
            {siteColumn ? (
              <td>{`${row.site_display_name ?? row.site_id ?? ""} · ${row.site_id ?? ""}`}</td>
            ) : null}
            <td>{readablePeriod(row.interval.first_running_observed, row.interval.last_running_observed)}</td>
            <td>
              <ClaimBadge
                level={row.claim_level}
                label={row.reading?.outcome ?? OUTCOME_WORDS[row.claim_level] ?? "Assessed"}
              />
            </td>
            <td>
              {row.reading?.confidence.word ?? confidenceWord(row.confidence)}
              {row.reading?.confidence.principal_limitation == null ? null : (
                <span className="overview-note">{` ${row.reading.confidence.principal_limitation}`}</span>
              )}
            </td>
            <td>
              <Link
                to={analysisHref(row)}
                data-finding-row-analysis={row.assessment_id}
                onClick={(event) => event.stopPropagation()}
              >
                View analysis
              </Link>
            </td>
            <td>{findingType(row.finding_type, row)}</td>
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
  NOT_APPLICABLE: "Not stated",
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

/** A contextual view of one page: Overview (default) or Analysis. */
export type LocalView = "overview" | "analysis";

/** `?view=analysis` selects Analysis; anything else, or none, is Overview. */
export function localView(params: URLSearchParams): LocalView {
  return params.get("view") === "analysis" ? "analysis" : "overview";
}

/** The same address at another view, every other parameter kept. */
export function localViewSearch(params: URLSearchParams, view: LocalView): string {
  const next = new URLSearchParams(params);
  if (view === "overview") {
    next.delete("view");
  } else {
    next.set("view", view);
  }
  const text = next.toString();
  return text === "" ? "?" : `?${text}`;
}

/**
 * The `Overview | Analysis` view pair inside Dispatch and Site Evidence
 * (D-2026-10-04-plain-language-analysis-views). Contextual views of one page,
 * not capabilities and not an expert mode.
 */
export function LocalViews({
  label,
  current,
  params,
}: {
  label: string;
  current: LocalView;
  params: URLSearchParams;
}) {
  return (
    <nav className="site-tabs site-subtabs local-views" aria-label={label}>
      <ol className="site-tabs__list">
        {(["overview", "analysis"] as const).map((view) => (
          <li className="site-tabs__item" key={view}>
            <Link
              className="site-tabs__link"
              to={{ search: localViewSearch(params, view) }}
              data-local-view={view}
              aria-current={view === current ? "page" : undefined}
            >
              {view === "overview" ? "Overview" : "Analysis"}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}
