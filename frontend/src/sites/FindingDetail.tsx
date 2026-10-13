/**
 * Finding detail (T028): the trust-defining page. It renders one backend
 * assessment by its `assessment_id` - the same object Performance > Dispatch
 * and the Overview card name - and recomputes nothing.
 *
 * Tabs: `Overview | Analysis | Evidence | Alternatives`
 * (D-2026-10-04-plain-language-analysis-views, amending AC21 and
 * `D-2026-10-02-rendered-tabs-per-capability`; Recommendation and History
 * wait for T034). Overview is the plain default reading: what happened, when,
 * how confident and what limits it, the estimated fuel associated with it and
 * what to check next, all from the backend's plain `reading`. Analysis
 * explains how the conclusion follows from the inputs (shared with Dispatch).
 * Evidence lists the records behind each assessed part, each opening the
 * record drawer; Alternatives lists the other possible explanations.
 *
 * Everything shown is reconstructible from accepted evidence with the
 * Simulator Lab off: this module reads the operator analytics and evidence
 * routes only.
 */
import { useEffect, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import { Fact, FactList, Panel } from "../ui";
import { AssessmentAnalysis } from "./assessmentAnalysis";
import { AssessedPeriodTimeline, FuelRange } from "./assessmentGraphics";
import {
  ClaimBadge,
  ClaimDrawer,
  EvidenceLinks,
  NextSteps,
  OUTCOME_WORDS,
  readablePeriod,
  Section,
  windowText,
  type NextStepHref,
  type OpenRecord,
} from "./findingPresentation";
import type { FindingClient } from "./findingClient";
import type { DomainPresentationProfile } from "./presentationProfile";
import { LegacyFindingEvidence } from "./SiteFindingEvidence";
import { findingTypeLabel } from "./presentationProfile";
import type {
  Assessment,
  AssessmentDetail,
  Reading,
  SiteAnalyticsClient,
} from "./siteAnalyticsClient";
import type { EvidenceRead, SiteEvidenceClient } from "./siteEvidenceClient";

export type FindingDetailTab = "overview" | "analysis" | "evidence" | "alternatives";

export const FINDING_DETAIL_TABS: { id: FindingDetailTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "analysis", label: "Analysis" },
  { id: "evidence", label: "Evidence" },
  { id: "alternatives", label: "Alternatives" },
];

export const FINDING_TABS_LABEL = "Finding sections";

const DETAIL_UNAVAILABLE = "Detail not available for this part of the assessment.";

export interface FindingDetailProps {
  siteId: string;
  /** The site's display name, for the plain header. */
  siteName?: string;
  assessmentId: string;
  tab: FindingDetailTab;
  client: SiteAnalyticsClient;
  evidence: SiteEvidenceClient;
  profile: DomainPresentationProfile | null;
  tabHref: (tab: FindingDetailTab) => string;
  dispatchHref: string;
  /** Current results, for a withdrawn assessment. */
  currentResultsHref?: string;
  evidencePageHref: string;
  /** Lets the frame title the page once the assessment is read. */
  onLoaded?: (detail: AssessmentDetail) => void;
  /**
   * S4-03: the Evidence tab of this assessment-keyed page is not a second
   * Evidence source. It resolves the period's saved Finding and opens that
   * Finding's Evidence view (`LegacyFindingEvidence`).
   */
  findings: FindingClient;
  durableEvidenceHref: (findingId: string) => string;
}

export function FindingDetail({
  siteId,
  siteName,
  assessmentId,
  tab,
  client,
  evidence,
  profile,
  tabHref,
  dispatchHref,
  currentResultsHref,
  evidencePageHref,
  onLoaded,
  findings,
  durableEvidenceHref,
}: FindingDetailProps) {
  const [result, setResult] = useState<EvidenceRead<AssessmentDetail> | null>(null);
  const [params, setParams] = useSearchParams();

  useEffect(() => {
    let active = true;
    setResult(null);
    void client.getAssessment(siteId, assessmentId).then((loaded) => {
      if (active) {
        setResult(loaded);
        if (loaded.status === "loaded" && onLoaded !== undefined) {
          onLoaded(loaded.value);
        }
      }
    });
    return () => {
      active = false;
    };
    // onLoaded is a frame callback; re-reading on its identity would loop.
  }, [client, siteId, assessmentId]);

  if (result === null) {
    return <p>Loading the assessment.</p>;
  }
  if (result.status === "not_found") {
    return (
      <Panel heading="No such assessment" headingId="finding-not-found-heading">
        <p>
          No assessed period with that reference exists for this site. This says
          only that the assessment does not exist, not that the period was found
          to be in order.
        </p>
        {currentResultsHref === undefined ? null : (
          <p>
            <Link to={currentResultsHref}>See the current results on Performance &gt; Dispatch</Link>
          </p>
        )}
      </Panel>
    );
  }
  if (result.status === "unavailable") {
    return (
      <Panel heading="Assessment unavailable" headingId="finding-unavailable-heading">
        <p>{result.message ?? "The assessment could not be read."}</p>
      </Panel>
    );
  }

  const detail = result.value;
  const a = detail.assessment;
  const record = params.get("record");
  const claim = params.get("claim");
  const open: OpenRecord = (link, claimText) => {
    const next = new URLSearchParams(params);
    next.set("record", link.message_id);
    next.set("claim", claimText);
    setParams(next);
  };
  const close = () => {
    const next = new URLSearchParams(params);
    next.delete("record");
    next.delete("claim");
    setParams(next);
  };
  const findingType = findingTypeLabel(profile, a.finding_type);

  return (
    <div className="finding-detail" data-finding={detail.assessment_id}>
      <FactList>
        <Fact term="Outcome">
          <ClaimBadge
            level={detail.claim_level}
            label={detail.reading?.outcome ?? OUTCOME_WORDS[detail.claim_level] ?? "Assessed"}
          />{" "}
          <span data-finding-type={findingType.id} data-profile-known={findingType.known}>
            {findingType.label}
          </span>
        </Fact>
        <Fact term="Site">{siteName ?? siteId}</Fact>
        <Fact term="Equipment">{detail.reading?.generator ?? "Generator"}</Fact>
        <Fact term="Period assessed">
          <span data-finding-window>{windowText(a.assessed_window)}</span>
        </Fact>
      </FactList>
      {detail.active ? null : (
        <p data-finding-retired>
          This assessment has been withdrawn and replaced; it is kept for reference.
          {currentResultsHref === undefined ? null : (
            <>
              {" "}
              <Link to={currentResultsHref}>See the current results on Performance &gt; Dispatch</Link>.
            </>
          )}
        </p>
      )}

      <nav className="site-tabs finding-tabs" aria-label={FINDING_TABS_LABEL}>
        <ol className="site-tabs__list">
          {FINDING_DETAIL_TABS.map((item) => (
            <li className="site-tabs__item" key={item.id}>
              <Link
                className="site-tabs__link"
                to={tabHref(item.id)}
                aria-current={item.id === tab ? "page" : undefined}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ol>
      </nav>

      <div className={record === null ? "finding-body" : "finding-body finding-body--drawer"}>
        <div className="finding-body__main">
          {detail.reading === undefined && tab !== "evidence" ? (
            <p data-finding-reading-unavailable>
              The plain reading of this assessment is not available, so it is not
              summarised here. Its records remain on the Evidence tab.
            </p>
          ) : tab === "overview" && detail.reading !== undefined ? (
            <FindingOverview
              detail={detail}
              reading={detail.reading}
              dispatchHref={dispatchHref}
              evidencePageHref={evidencePageHref}
              tabHref={tabHref}
            />
          ) : tab === "analysis" ? (
            <AssessmentAnalysis
              summary={detail}
              assessment={a}
              revisionHistory={detail.revision_history}
              records={{ kind: "tab", href: tabHref("evidence") }}
              alternativesHref={tabHref("alternatives")}
              coverageHref={`${evidencePageHref}?view=analysis&assessment=${encodeURIComponent(detail.assessment_id)}`}
              links={
                <li>
                  <Link to={dispatchHref}>See this period on Performance &gt; Dispatch</Link>
                </li>
              }
            />
          ) : tab === "evidence" ? (
            <LegacyFindingEvidence
              siteId={siteId}
              assessedWindow={a.assessed_window}
              findings={findings}
              durableEvidenceHref={durableEvidenceHref}
              recordsHref={evidencePageHref}
            />
          ) : (
            <FindingAlternatives assessment={a} reading={detail.reading} open={open} />
          )}
        </div>
        {record === null ? null : (
          <ClaimDrawer
            siteId={siteId}
            messageId={record}
            claim={claim}
            assessedWindow={a.assessed_window}
            modelVersion={a.model_version}
            evidence={evidence}
            onClose={close}
          />
        )}
      </div>
    </div>
  );
}

/** Other possible explanations still open that bear on the conclusion. */
function stillOpen(a: Assessment, reading: Reading): Reading["alternatives"] {
  return reading.alternatives.filter(
    (alt, index) =>
      a.alternatives[index]?.status === "NOT_EXCLUDED" && alt.id !== "UNMEASURED_PV_VARIATION",
  );
}

function FindingOverview({
  detail,
  reading,
  dispatchHref,
  evidencePageHref,
  tabHref,
}: {
  detail: AssessmentDetail;
  reading: Reading;
  dispatchHref: string;
  evidencePageHref: string;
  tabHref: (tab: FindingDetailTab) => string;
}) {
  const a = detail.assessment;
  const alternativesTabHref = tabHref("alternatives");
  const open = stillOpen(a, reading);
  const stepHref: NextStepHref = (step) =>
    step.target.kind === "alternative"
      ? `${alternativesTabHref}#${alternativeAnchor(step.target.id)}`
      : step.target.kind === "site_evidence"
        ? evidencePageHref
        : null;
  return (
    <div className="finding-overview">
      <Section heading="What happened" id="finding-claim-heading">
        <p className="finding-claim" data-finding-claim={a.claim_level}>
          <strong>{reading.headline}</strong> {reading.reason}
        </p>
        <p data-finding-meaning className="overview-note">
          {reading.meaning}
        </p>
      </Section>

      <Section heading="When, and for how long" id="finding-facts-heading">
        <AssessedPeriodTimeline
          source={a}
          outcomes={reading.segments.map((s) => s.outcome)}
          reasons={reading.segments.map((s) => s.reason)}
          partHref={(index) => `${tabHref("analysis")}?part=${index + 1}`}
          assessmentId={detail.assessment_id}
        />
        <FactList>
          <Fact term="Recorded: generator operating">
            {readablePeriod(a.interval.first_running_observed, a.interval.last_running_observed)}
          </Fact>
          <Fact term="Generator operating time">{reading.operating_time}</Fact>
          <Fact term="Assessed: possibly avoidable">{reading.portions.possibly_avoidable}</Fact>
          <Fact term="Assessed: needed">{reading.portions.needed}</Fact>
          <Fact term="Assessed: cannot determine">{reading.portions.cannot_determine}</Fact>
          {reading.reasons_needed.length === 0 ? null : (
            <Fact term="Reasons for the needed time">{reading.reasons_needed.join(", ")}</Fact>
          )}
        </FactList>
        <p className="overview-note">
          These are separate estimates, not parts of one total. How each is
          worked out is on the <Link to={tabHref("analysis")}>Analysis</Link> tab.
        </p>
      </Section>

      <Section heading="How confident, and what limits it" id="finding-confidence-heading">
        <p>
          <span data-finding-confidence={a.confidence.level}>
            <strong>{`Confidence: ${reading.confidence.word}.`}</strong>
          </span>
          {reading.confidence.principal_limitation === null
            ? null
            : ` ${reading.confidence.principal_limitation}`}
        </p>
        {reading.missing.length === 0 ? null : (
          <p data-finding-gaps>{`Missing or conflicting records: ${reading.missing.join("; ")}.`}</p>
        )}
        <ul className="cell-list" data-claim-limits>
          {reading.limits.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        {open.length === 0 ? null : (
          <p data-finding-open-alternatives>
            {"Other possible explanations still open: "}
            {open.map((alt, index) => (
              <span key={alt.id}>
                {index === 0 ? "" : ", "}
                <Link to={`${alternativesTabHref}#${alternativeAnchor(alt.id)}`}>{alt.label}</Link>
              </span>
            ))}
            .
          </p>
        )}
      </Section>

      <Section heading="Estimated fuel" id="finding-consequence-heading">
        <div data-finding-fuel={a.fuel.status}>
          <FuelRange fuel={a.fuel} reading={reading.fuel} />
        </div>
      </Section>

      <Section heading="What to check next" id="finding-next-heading">
        <NextSteps reading={reading} href={stepHref} />
        <ul className="cell-list" data-finding-supporting>
          <li>
            <Link to={tabHref("analysis")}>See how this conclusion was reached</Link>
            {" (Analysis tab)."}
          </li>
          <li>
            <Link to={tabHref("evidence")}>Open the supporting records</Link>
            {" for each part of this period (Evidence tab)."}
          </li>
          <li>
            <Link to={alternativesTabHref}>
              {open.length === 0
                ? "Review the other explanations considered"
                : `Compare ${open.length} other possible explanation${open.length === 1 ? "" : "s"} still open`}
            </Link>
            {" (Alternatives tab)."}
          </li>
          <li>
            <Link to={dispatchHref}>See this period on Performance &gt; Dispatch</Link>.
          </li>
        </ul>
      </Section>
    </div>
  );
}

/** The Alternatives tab anchor a next step links to. */
export function alternativeAnchor(id: string): string {
  return `alternative-${id}`;
}

function FindingAlternatives({
  assessment,
  reading,
  open,
}: {
  assessment: Assessment;
  reading: Reading | undefined;
  open: OpenRecord;
}) {
  // A next step links an alternative by its anchor; bring it into view.
  const { hash } = useLocation();
  useEffect(() => {
    if (hash.length > 1) {
      document.getElementById(hash.slice(1))?.scrollIntoView?.({ block: "start" });
    }
  }, [hash]);
  return (
    <Section heading="Other possible explanations" id="finding-alternatives-heading">
      <p className="overview-note">
        Each explanation is judged only on the records available for this
        period. &quot;Not supported by the available records&quot; does not mean
        it has been ruled out in general.
      </p>
      <ol className="claim-list">
        {assessment.alternatives.map((alt, index) => {
          const plain = reading?.alternatives[index];
          const label = plain?.label ?? "Other possible explanation";
          return (
            <li
              key={alt.id}
              id={alternativeAnchor(alt.id)}
              className="claim-list__item"
              data-alternative={alt.id}
            >
              <p className="claim-list__head">
                <strong>{label}</strong>{" "}
                <span data-alternative-status={alt.status}>{plain?.status ?? "Still possible"}</span>
              </p>
              <p>{plain?.statement ?? DETAIL_UNAVAILABLE}</p>
              {alt.gaps === undefined || alt.gaps.length === 0 ? null : (
                <p data-alternative-gaps>
                  {`Not reported: ${alt.gaps.map((g) => `${readablePeriod(g.start, g.end)} (${g.minutes} min)`).join(", ")}.`}
                </p>
              )}
              <EvidenceLinks
                links={alt.evidence}
                claim={`Other possible explanation: ${label}`}
                open={open}
              />
            </li>
          );
        })}
      </ol>
    </Section>
  );
}
