/**
 * S4-01 phase 3: the Site-scoped durable Finding detail (mock `finding:1,2,4`;
 * `finding:3` "What to do next" links to the S6-01b Recommendation view).
 *
 * Reads `GET /api/sites/{site}/findings/{id}[?revision_id=]`. The selected
 * version (`?revision_id=`) and the view (`?view=analysis`) stay in the
 * address, so a reload reopens the exact stored version, including an earlier
 * one a later version replaced. The page leads with the state that limits what
 * it shows: a closed source (audit record only), a merge, an earlier version,
 * then the recorded state and whether it is up to date. Possibly avoidable,
 * needed and undetermined time stay separate; nothing here is a fuel or money
 * figure, a recommendation or an Action.
 */
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  DataTable,
  ExactReferences,
  Fact,
  FactList,
  AttentionList,
  BigClaim,
  HeadlineVisualCard,
  MetricCard,
  MetricCards,
  Panel,
  ProductStatus,
  ShowAll,
  StatusBar,
  StepStrip,
  asOfText,
  type AttentionItem,
  type ProductWords,
  type Step,
} from "../ui";
import { clock, durationText, groupLimitations, limitationWords, minutes, roleWords, stamp } from "./dispatchWords";
import type {
  FindingClient,
  FindingDetailBody,
  FindingReadResult,
} from "./findingClient";
import { findingRefusalWords, LocalViews, localView, localViewSearch, type LocalView } from "./findingPresentation";
import {
  findingCurrentnessWords,
  unconfirmedCause,
  dayOf,
  daysBetween,
  followsClosure,
  LIFECYCLE_WORDS,
  PORTION_FILL,
  portionWords,
  spanMinutes,
  versionWords,
} from "./findingWords";
import { SourceProvenanceNotice } from "./sourceProvenance";
import "./w1ux02-finding.css";

export const FINDING_VIEWS_LABEL = "Finding views";
/** The v69 `finding` screen question (W1-UX-02). */
export const FINDING_QUESTION = "What is the defensible conclusion and its consequence?";

export interface SiteFindingLinks {
  /** This or another Finding of the Site, optionally at an exact version. */
  finding: (findingId: string, revisionId?: string | null) => string;
  /** The Site's Performance > Dispatch at one UTC day, optionally one assessed period. */
  dispatch: (day: string, intervalRevisionId?: string | null) => string;
  /** The Site's accepted records. */
  evidence: string;
  /** W1-F3: this Finding's Evidence child view, with the exact version selected. */
  findingEvidence?: (revisionId: string | null) => string;
  /** S4-03: this Finding's History child view, with the exact version selected. */
  history?: (revisionId: string | null) => string;
  /** S6-01b: this Finding's Recommendation child view, with the exact version selected. */
  recommendation?: (revisionId: string | null) => string;
}

export function SiteFinding({
  siteId,
  findingId,
  client,
  links,
  onTitle,
}: {
  siteId: string;
  findingId: string;
  client: FindingClient;
  links: SiteFindingLinks;
  onTitle?: (title: string) => void;
}) {
  const [params] = useSearchParams();
  const revisionId = params.get("revision_id");
  const view = localView(params);
  const [read, setRead] = useState<FindingReadResult<FindingDetailBody> | null>(null);

  useEffect(() => {
    let active = true;
    setRead(null);
    void client.getFinding(siteId, findingId, revisionId).then((loaded) => {
      if (active) {
        setRead(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId, findingId, revisionId]);

  const title = read?.status === "loaded" ? titleOf(read.value) : "Finding";
  useEffect(() => {
    onTitle?.(title);
  }, [onTitle, title]);

  if (read === null) {
    return <p>Loading the Finding.</p>;
  }
  if (read.status !== "loaded") {
    return <Refused read={read} pinned={revisionId !== null} />;
  }
  const body = read.value;
  const shared = {
    className: "site-finding",
    "data-finding-id": body.finding.id,
    "data-finding-revision": body.selection.revision_id,
    "data-finding-lifecycle": body.revision.lifecycle,
    "data-finding-currentness": body.revision.currentness.state,
  };
  if (view === "analysis") {
    // The Finding Analysis view (not one of the W1-F3 screens) keeps its answer card and technical panels.
    return (
      <section {...shared} aria-labelledby="site-finding-state-heading">
        <LocalViews label={FINDING_VIEWS_LABEL} current={view} params={params} />
        <FindingAnswer body={body} links={links} view={view} params={params} />
        <StatusChips body={body} />
        <TechnicalDetail body={body} />
      </section>
    );
  }
  // W1-F3: the v69 `finding` form: statusbar, What happened, four metric cards,
  // the limits / next-step pair, then Where to look next. Versions live on
  // History and the record lists on Evidence.
  return (
    <div {...shared}>
      <LocalViews label={FINDING_VIEWS_LABEL} current={view} params={params} />
      <FindingStatusBar body={body} />
      <WhatHappened body={body} links={links} />
      <FindingMetrics body={body} />
      <div className="panel-pair">
        <WhatLimits body={body} links={links} />
        <WhatNext body={body} links={links} />
      </div>
      <WhereToLook body={body} links={links} params={params} />
    </div>
  );
}

function titleOf(body: FindingDetailBody): string {
  return LIFECYCLE_WORDS[body.revision.lifecycle]?.title ?? "Finding";
}

function Refused({ read, pinned }: { read: Exclude<FindingReadResult<FindingDetailBody>, { status: "loaded" }>; pinned: boolean }) {
  const words: Record<typeof read.status, { heading: string; text: string }> = {
    not_found: {
      heading: "Finding not found",
      text: pinned
        ? "This site has no such Finding or no such version of it."
        : "This site has no such Finding.",
    },
    unauthenticated: { heading: "Sign-in required", text: "Sign in to read this site's Findings." },
    forbidden: { heading: "No access", text: "Your account has no access to this site's Findings." },
    closed: {
      heading: "Assessments not released",
      text:
        "This site's assessments are not released for use yet, so no current Finding, and no 'no Finding' " +
        "result, is shown. A link to an exact earlier version still opens as a record.",
    },
    unavailable: { heading: "Finding unavailable", text: "The Finding could not be read." },
  };
  const chosen = words[read.status];
  const gap = (name: string) => (
    <p className="v69-gap-line" data-finding-panel-gap={name}>
      {chosen.heading}: nothing is shown here, and this is not a result that no Finding exists.
    </p>
  );
  // W1-F3: the page-level refusal, then the four v69 panel slots with the gap stated in each.
  return (
    <div className="site-finding" data-finding-refused={read.status}>
      <div className="page-refusal" role="status" data-page-refusal={read.status}>
        <p className="page-refusal__title">
          <strong>{chosen.heading}</strong>
        </p>
        <ProductStatus
          words={findingRefusalWords(read.status)}
          scope={pinned ? "This Finding, at the version in the address" : "This Finding"}
          asOf={null}
        />
        <p data-finding-read={read.status}>{chosen.text}</p>
        {read.message ? <p className="site-finding__note">Reason given: {read.message}</p> : null}
      </div>
      <Panel heading="What happened" headingId="site-finding-happened-heading">
        {gap("happened")}
      </Panel>
      <div className="panel-pair">
        <Panel heading="What limits this conclusion" headingId="site-finding-limits-heading">
          {gap("limits")}
        </Panel>
        <Panel heading="What to do next" headingId="site-finding-next-heading">
          {gap("next")}
        </Panel>
      </div>
      <Panel heading="Where to look next" headingId="site-finding-look-heading">
        {gap("look")}
      </Panel>
    </div>
  );
}

/** The code whose words lead: a closed source, a merge, an earlier version, then the recorded currentness. */
function statusCode(body: FindingDetailBody): string {
  if (body.audit_only) return "SOURCE_CLOSED";
  if (body.state.merged_into_finding_id) return "MERGED_INTO_CANONICAL";
  if (!body.selection.is_latest) return "SUPERSEDED_BY_LATER_REVISION";
  return body.revision.currentness.state;
}

/** The conclusion this version records, no stronger than its lifecycle and counted minutes. */
function conclusionText(body: FindingDetailBody): string {
  const selected = body.revision;
  switch (selected.lifecycle) {
    case "SUPPORTED":
      return `${durationText(minutes(selected.minutes.candidate) ?? 0)} of generator time possibly avoidable`;
    case "UNCONFIRMED":
      return "cannot decide whether any time was possibly avoidable";
    case "NO_LONGER_SUPPORTED":
      return "no possibly avoidable time is counted";
    default:
      return "carried by an earlier Finding";
  }
}

function headlineText(body: FindingDetailBody, words: ProductWords & { attention: boolean }): string {
  const lifecycle = LIFECYCLE_WORDS[body.revision.lifecycle];
  if (body.audit_only) return "Record only: this site's assessments are not released";
  if (body.state.merged_into_finding_id) return "Joined into an earlier Finding";
  if (!body.selection.is_latest) return `Earlier version ${body.selection.revision_no} of ${body.revision_page.total}`;
  return words.attention
    ? `${lifecycle.label} in the last recorded version: ${conclusionText(body)}`
    : `${lifecycle.label}: ${conclusionText(body)}`;
}

/** Conclusion, cause, consequence and next useful step; each step's state comes from the read. */
function causalSteps(body: FindingDetailBody, links: SiteFindingLinks): Step[] {
  const selected = body.revision;
  const lifecycle = LIFECYCLE_WORDS[selected.lifecycle];
  const recordGap = selected.indeterminate_cause?.kind === "RECORD_GAP";
  const conclusion: Step = {
    label: "Conclusion",
    state: selected.lifecycle === "UNCONFIRMED" || selected.lifecycle === "MERGED" ? "not-known" : "done",
    detail: lifecycle.label,
  };
  const cause: Step =
    selected.lifecycle === "SUPPORTED"
      ? { label: "Cause", state: "done", detail: "The generator stayed on while solar and the battery reported enough capacity" }
      : selected.lifecycle === "NO_LONGER_SUPPORTED"
        ? { label: "Cause", state: "done", detail: "A complete later assessment finds no possibly avoidable time" }
        : selected.lifecycle === "UNCONFIRMED"
          ? {
              label: "Cause",
              state: recordGap ? "problem" : "not-known",
              detail: recordGap ? "Some records are missing or conflict" : "The assessment could not decide",
            }
          : { label: "Cause", state: "not-known", detail: "Carried by the earlier Finding" };
  const consequence: Step = {
    label: "Consequence",
    state: "not-known",
    detail: "No fuel or money figure is worked out on this page",
  };
  const merged = body.state.merged_into_finding_id;
  const next: Step =
    body.audit_only || merged || !body.selection.is_latest
      ? {
          label: "Next useful step",
          state: "waiting",
          detail: merged ? "Open the Finding that carries the review" : body.audit_only ? "Wait for the assessments to be released" : "Open the latest version",
        }
      : selected.lifecycle === "SUPPORTED" && links.recommendation
        ? { label: "Next useful step", state: "waiting", detail: "Review the proposed trial" }
        : { label: "Next useful step", state: "waiting", detail: "Check the Dispatch day and the records behind it" };
  return [conclusion, cause, consequence, next];
}

function couldChangeText(body: FindingDetailBody): string {
  if (body.audit_only) {
    return "Nothing changes this record while the site's assessments are not released; a later released assessment would record a new version.";
  }
  if (body.state.merged_into_finding_id) {
    return "The earlier Finding now carries the review; later changes are recorded there.";
  }
  if (!body.selection.is_latest) {
    return "A later version already replaces this one; the latest version holds the current conclusion.";
  }
  const recordGap = body.revision.indeterminate_cause?.kind === "RECORD_GAP";
  return (
    "A newer assessment of these days, for example after late or corrected readings arrive, would record a new " +
    "version of this Finding." +
    (recordGap ? " Records that fill the missing part could let the undecided time be decided." : "")
  );
}

/**
 * The shared state line of the shown version, with its material notes beside
 * it: the stored source, record-only, merged, earlier-version and
 * after-closure notes. Used by the Overview's What happened panel and the
 * Analysis view's answer card.
 */
function FindingStateLine({
  body,
  links,
  compact = false,
}: {
  body: FindingDetailBody;
  links: SiteFindingLinks;
  /**
   * W1-F3 review M4: inside What happened the strip owns the state label, version and period, and the panel
   * description owns the period again; the panel keeps the non-positive sentence, the material notes and the as-of.
   */
  compact?: boolean;
}) {
  const selected = body.revision;
  const words = findingCurrentnessWords(statusCode(body));
  const merged = body.state.merged_into_finding_id;
  const afterClosure = selected.lifecycle !== "NO_LONGER_SUPPORTED" && followsClosure(body.revisions, selected);
  const notes = (
    <>
      <SourceProvenanceNotice provenance={body.source_provenance} subject="finding version" name="finding" />
      {body.audit_only ? (
        <span data-finding-audit-only>{" "}
          This exact version is kept as a record. It is not a current result, and whether it is still up to date is
          not checked while the site&apos;s assessments are not released.
        </span>
      ) : null}
      {merged ? (
        <span data-finding-merged={merged}>{" "}
          Later records showed one longer period. The earlier Finding now carries the review.{" "}
          <Link to={links.finding(merged)}>Open the Finding that carries the review</Link>
        </span>
      ) : null}
      {!body.selection.is_latest ? (
        <span data-finding-earlier-version>{" "}
          A later version replaces this one. <Link to={links.finding(body.finding.id)}>Open the latest version</Link>
        </span>
      ) : null}
      {afterClosure ? (
        <span data-finding-after-closure>{" "}
          {selected.lifecycle === "UNCONFIRMED"
            ? "This review had already been closed as no longer supported. The newer assessment cannot confirm either way; this is not a new issue."
            : "This review had been closed as no longer supported; a later assessment supports it again for the same period."}
        </span>
      ) : null}
    </>
  );
  if (compact) {
    return (
      <span className={`status-strip__state product-status--inline product-status--${words.tone}`} data-product-status={words.tone} data-finding-panel-state>
        {words.tone === "positive" ? null : <span className="product-status__sentence">{words.sentence}</span>}
        {notes}{" "}
        <span className="product-status__bound">
          <span data-product-status-as-of>{asOfText(body.watermarks.finding_recorded_at)}</span>
        </span>
      </span>
    );
  }
  return (
    <ProductStatus
      inline
      words={words}
      scope={`Version ${body.selection.revision_no} of ${body.revision_page.total} · ${periodWords(selected.episode.start, selected.episode.end)}`}
      asOf={body.watermarks.finding_recorded_at}
    >
      {notes}
    </ProductStatus>
  );
}

/**
 * W1-UX-02: the v69 answer card. The defensible conclusion leads, with the
 * plain state line (currentness, scope, "as of" the shown version's recorded
 * time) and the material notes beside it, then the causal strip, what could
 * change it, what to do, the Analysis destination and the exact references
 * last.
 */
function FindingAnswer({
  body,
  links,
  view,
  params,
}: {
  body: FindingDetailBody;
  links: SiteFindingLinks;
  view: LocalView;
  params: URLSearchParams;
}) {
  const words = findingCurrentnessWords(statusCode(body));
  return (
    <HeadlineVisualCard
      dataName="finding"
      headingId="site-finding-state-heading"
      question={FINDING_QUESTION}
      headline={headlineText(body, words)}
      status={<FindingStateLine body={body} links={links} />}
      visual={<StepStrip title="From conclusion to next step" steps={causalSteps(body, links)} />}
      meaning={
        <>
          <LifecycleSentence body={body} />
          <CouldChange body={body} />
        </>
      }
      todo={<NextStep body={body} links={links} />}
      destination={
        view === "analysis" ? (
          <Link to={{ search: localViewSearch(params, "overview") }} data-finding-destination="overview">
            Back to the plain reading (Overview)
          </Link>
        ) : (
          <Link to={{ search: localViewSearch(params, "analysis") }} data-finding-destination="analysis">
            See how this conclusion was reached (Analysis)
          </Link>
        )
      }
      references={<FindingReferences body={body} />}
    />
  );
}

function LifecycleSentence({ body }: { body: FindingDetailBody }) {
  const selected = body.revision;
  return (
    <p data-finding-lifecycle-sentence>
      {LIFECYCLE_WORDS[selected.lifecycle].sentence}
      {selected.lifecycle === "UNCONFIRMED" ? ` ${unconfirmedCause(selected.indeterminate_cause)}` : ""}
    </p>
  );
}

function CouldChange({ body }: { body: FindingDetailBody }) {
  return (
    <p data-finding-could-change>
      <strong>What could change it:</strong> {couldChangeText(body)}
    </p>
  );
}

/** finding:3: the supported Recommendation link at the exact version read, or that none is recorded. */
function NextStep({ body, links }: { body: FindingDetailBody; links: SiteFindingLinks }) {
  return links.recommendation ? (
    <div data-finding-recommendation-link>
      <p>
        A fixed rule may propose a battery reserve trial for this version. Nothing here asks you to change how the
        generator is operated.
      </p>
      <p className="form-footer">
        <Link className="button primary" to={links.recommendation(body.selection.revision_id)}>
          Open the recommendation
        </Link>
      </p>
    </div>
  ) : (
    <p data-finding-recommendation-link="none">
      No recorded next action. Nothing here asks you to change how the generator is operated.
    </p>
  );
}

function FindingReferences({ body }: { body: FindingDetailBody }) {
  const selected = body.revision;
  return (
    <ExactReferences
      name="finding-references"
      references={[
        { label: "Finding reference", value: body.finding.id },
        { label: "Shown version reference", value: body.selection.revision_id },
        { label: "Latest version reference", value: body.selection.latest_revision_id },
        { label: "Recorded state code", value: selected.lifecycle },
        { label: "Up-to-date check code", value: findingCurrentnessWords(statusCode(body)).code },
        { label: "Change code", value: selected.transition },
      ]}
    />
  );
}

function StatusChips({ body }: { body: FindingDetailBody }) {
  const selected = body.revision;
  const currentness = findingCurrentnessWords(statusCode(body));
  return (
    <ul className="site-finding__chips" aria-label="Finding status">
      <li className="site-finding__chip" data-chip="state">
        State: {LIFECYCLE_WORDS[selected.lifecycle].label}
      </li>
      <li className="site-finding__chip" data-chip="currentness">
        {currentness.label}
      </li>
      <li className="site-finding__chip" data-chip="version">
        {versionWords(body)}
      </li>
      <li className="site-finding__chip" data-chip="period">
        {periodWords(selected.episode.start, selected.episode.end)}
      </li>
    </ul>
  );
}

/** The mock's statusbar: the state, currentness, version and period badges in one line. */
function FindingStatusBar({ body }: { body: FindingDetailBody }) {
  const selected = body.revision;
  const currentness = findingCurrentnessWords(statusCode(body));
  return (
    <StatusBar label="Finding status" data={{ "data-finding-statusbar": "" }}>
      {/* W1-F3 review H2: the mock's Priority and Confidence chips; no read assesses either yet. */}
      <span className="badge badge--not-assessed" data-chip="priority" data-not-assessed>
        Priority: not assessed
      </span>
      <span className="badge badge--not-assessed" data-chip="confidence" data-not-assessed>
        Confidence: not assessed
      </span>
      <span className="badge badge--lifecycle" data-chip="state">
        State: {LIFECYCLE_WORDS[selected.lifecycle].label}
      </span>
      <span className="badge badge--neutral" data-chip="currentness">
        {currentness.label}
      </span>
      <span className="badge badge--neutral" data-chip="version">
        {versionWords(body)}
      </span>
      <span className="status-strip__spacer" />
      <span data-chip="period">{periodWords(selected.episode.start, selected.episode.end)}</span>
    </StatusBar>
  );
}

function periodWords(start: string, end: string): string {
  const first = dayOf(start);
  const last = dayOf(end);
  return first === last
    ? `${first} ${clock(start)}–${clock(end)} UTC`
    : `${first} ${clock(start)} – ${last} ${clock(end)} UTC`;
}

interface Portion {
  start: string;
  end: string;
  classification: string;
  intervalRevisionId: string;
  evidenceCount: number | null;
}

function portionsOf(body: FindingDetailBody): Portion[] {
  const claim = body.revision.claim;
  const spans: Portion[] = (claim.candidate_spans ?? []).map((s) => ({
    start: s.start,
    end: s.end,
    classification: "CANDIDATE_AVOIDABLE",
    intervalRevisionId: s.assessment_revision_id,
    evidenceCount: s.evidence_ids?.length ?? null,
  }));
  const others: Portion[] = (claim.other_portions ?? []).map((p) => ({
    start: p.start,
    end: p.end,
    classification: p.classification,
    intervalRevisionId: p.assessment_revision_id,
    evidenceCount: null,
  }));
  return [...spans, ...others].sort((a, b) => Date.parse(a.start) - Date.parse(b.start));
}

function runWords(body: FindingDetailBody): string {
  const { start, end } = body.revision.episode;
  const stops = (body.revision.claim.continuity ?? []).flatMap((gap) => gap.stops ?? []).length;
  return stops > 0
    ? `The generator ran between ${periodWords(start, end)}, with ${stops === 1 ? "one short stop" : `${stops} short stops`} recorded in that time.`
    : `The generator stayed on from ${periodWords(start, end)}.`;
}

function WhatHappened({ body, links }: { body: FindingDetailBody; links: SiteFindingLinks }) {
  const [params, setParams] = useSearchParams();
  const selected = body.revision;
  const portions = portionsOf(body);
  const chosenIndex = Number(params.get("portion"));
  const chosen = params.get("portion") !== null && Number.isInteger(chosenIndex) ? (portions[chosenIndex] ?? null) : null;
  const avoidable = minutes(selected.minutes.candidate) ?? 0;
  const period = spanMinutes(selected.episode.start, selected.episode.end);
  const startMs = Date.parse(selected.episode.start);
  const total = Math.max(1, Date.parse(selected.episode.end) - startMs);
  const choose = (index: number | null) => {
    const next = new URLSearchParams(params);
    if (index === null) {
      next.delete("portion");
    } else {
      next.set("portion", String(index));
    }
    setParams(next, { replace: true });
  };
  const supported = selected.lifecycle === "SUPPORTED";
  const words = findingCurrentnessWords(statusCode(body));
  return (
    <Panel
      heading="What happened"
      headingId="site-finding-happened-heading"
      description={`Period covered · ${periodWords(selected.episode.start, selected.episode.end)} · ${durationText(period)}`}
    >
      <BigClaim data={{ "data-finding-claim": "" }}>{headlineText(body, words)}</BigClaim>
      <div className="site-finding__state v69-state-line" data-finding-state>
        <FindingStateLine body={body} links={links} compact />
      </div>
      <p className="v69-prose site-finding__sentence" data-finding-sentence>
        {supported
          ? `${runWords(body)} For ${durationText(avoidable)} of that time, solar power and the battery reported enough capacity to meet site demand, so the generator was possibly avoidable.`
          : selected.lifecycle === "MERGED"
            ? `This Finding covered ${periodWords(selected.episode.start, selected.episode.end)} before it was joined into an earlier Finding.`
            : selected.lifecycle === "UNCONFIRMED"
              ? `This Finding covers ${periodWords(selected.episode.start, selected.episode.end)}. ${body.selection.is_latest ? "The latest assessment" : "This version"} cannot decide whether any of that time was possibly avoidable.`
              : `This Finding covers ${periodWords(selected.episode.start, selected.episode.end)}. ${body.selection.is_latest ? "The latest assessment" : "This version"} of that period counts no possibly avoidable time.`}
      </p>
      {portions.length > 0 ? (
        <div className="site-finding__timeline">
          <p className="v69-eyebrow" id="site-finding-blocks-heading">
            Blocks in this Finding
          </p>
          <ol className="site-finding__blocks" aria-labelledby="site-finding-blocks-heading">
            {portions.map((p, index) => {
              const left = ((Date.parse(p.start) - startMs) / total) * 100;
              const width = Math.max(0.6, ((Date.parse(p.end) - Date.parse(p.start)) / total) * 100);
              const pressed = chosen === p;
              return (
                <li key={`${p.start}-${index}`} style={{ left: `${left}%`, width: `${width}%` }}>
                  <button
                    type="button"
                    className={`dispatch-block dispatch-fill--${PORTION_FILL[p.classification] ?? "unknown"}`}
                    aria-pressed={pressed}
                    aria-label={`${portionWords(p.classification)}, ${clock(p.start)}–${clock(p.end)} UTC`}
                    data-portion={p.classification}
                    onClick={() => choose(pressed ? null : index)}
                  />
                </li>
              );
            })}
          </ol>
          <div className="dispatch-track__axis site-finding__axis" aria-hidden="true">
            <span>{clock(selected.episode.start)}</span>
            <span>{clock(selected.episode.end)}</span>
          </div>
          <p className="site-finding__legend">
            <span className="dispatch-swatch dispatch-fill--avoidable" /> Possibly avoidable{" "}
            <span className="dispatch-swatch dispatch-fill--needed" /> Needed{" "}
            <span className="dispatch-swatch dispatch-fill--unknown" /> Cannot determine · Times are UTC; select a block.
          </p>
          {chosen ? (
            <div className="dispatch-block-detail" data-finding-portion-detail>
              <p>
                <strong>
                  {portionWords(chosen.classification)}: {stamp(chosen.start)}–{clock(chosen.end)} UTC
                </strong>
              </p>
              <p>
                {durationText(spanMinutes(chosen.start, chosen.end))}
                {chosen.evidenceCount !== null ? `, supported by ${chosen.evidenceCount} accepted records` : ""}.{" "}
                <Link to={links.dispatch(dayOf(chosen.start), chosen.intervalRevisionId)} data-finding-dispatch-link>
                  See this block on the Dispatch day
                </Link>
              </p>
            </div>
          ) : null}
        </div>
      ) : (
        <p data-finding-no-blocks>No block is counted in this version.</p>
      )}
    </Panel>
  );
}

/** The mock's four metric cards: the separate minute counts and the fuel and cost slot this page does not fill. */
function FindingMetrics({ body }: { body: FindingDetailBody }) {
  const selected = body.revision;
  const avoidable = minutes(selected.minutes.candidate) ?? 0;
  const needed = minutes(selected.minutes.necessary) ?? 0;
  const unknown = minutes(selected.minutes.indeterminate) ?? 0;
  return (
    <MetricCards columns={4} label="Time in this Finding">
      <MetricCard
        label="Possibly avoidable"
        value={durationText(avoidable)}
        note="Counted in this Finding"
        tone="amber"
        data={{ "data-finding-card": "CANDIDATE_AVOIDABLE" }}
      />
      <MetricCard
        label="Needed"
        value={durationText(needed)}
        note="A recorded reason required the generator"
        tone="green"
        data={{ "data-finding-card": "NECESSARY" }}
      />
      <MetricCard
        label="Cannot determine"
        value={durationText(unknown)}
        note="Could not be decided either way"
        tone="muted"
        data={{ "data-finding-card": "INDETERMINATE" }}
      />
      <MetricCard
        label="Fuel and cost"
        value="Not available"
        note="No fuel or money estimate is made on this page"
        tone="muted"
        word
        data={{ "data-finding-card": "MONEY" }}
      />
    </MetricCards>
  );
}

function WhatLimits({ body, links }: { body: FindingDetailBody; links: SiteFindingLinks }) {
  const selected = body.revision;
  const groups = groupLimitations(selected.limitations);
  // Segment-level record gaps never reach a revision's limitations; the read classifies them (re-review C8).
  const recordGap = selected.indeterminate_cause?.kind === "RECORD_GAP";
  const stops = (selected.claim.continuity ?? []).flatMap((gap) => gap.stops ?? []);
  const joined = (selected.claim.continuity ?? []).filter((gap) => !(gap.stops ?? []).length);
  const recurrence = body.relations.recurrence;
  const prior = body.relations.recurs_after_finding_id;
  return (
    <Panel heading="What limits this conclusion" headingId="site-finding-limits-heading">
      {/* W1-F3 review H1: every material limit stays visible, one sentence each. Only the access note and
          the SUPPORTED lifecycle sentence sit behind the expander. */}
      <ul className="site-finding__limits v69-prose" data-finding-limits>
        <li data-finding-bounded>
          Only the possibly avoidable blocks are counted, as a bounded estimate from the site records, not proof of
          wasted fuel.
        </li>
        {recordGap ? (
          <li data-finding-record-gap>
            Some records this version needs are missing or conflict over part of the period, so that part is undecided.
          </li>
        ) : null}
        {selected.claim.end_reason === "SERIES_LIMIT" ? (
          <li data-finding-end-reason="SERIES_LIMIT">
            This finding ends at {stamp(selected.episode.end)} UTC because later generator records could not be put in a
            proven time order, so later time is not judged and no current cost is shown.
          </li>
        ) : null}
        {groups.length === 0 ? (
          recordGap ? null : <li data-finding-limitations="none">No record gaps or conflicts were found over this period.</li>
        ) : (
          groups.map((g) => (
            <li key={g.code} data-limitation={g.code}>
              {limitationWords(g.code)}
              {g.items.length > 1 ? ` (${g.items.length} places)` : ""}.
            </li>
          ))
        )}
        {joined.length > 0 ? (
          <li data-finding-joined-gaps={joined.length}>
            {joined.length === 1 ? "One short gap" : `${joined.length} short gaps`} of 20 minutes or less had records for
            every minute and add no possibly avoidable time.
          </li>
        ) : null}
        {stops.length > 0 ? (
          <li data-finding-stop-bridges={stops.length}>
            The generator stopped {stops.length === 1 ? "once" : `${stops.length} times`} for 20 minutes or less (first
            at {stamp(stops[0].start)} UTC); off reports at both ends keep it one period, and this joining rests on those
            two off reports.
          </li>
        ) : null}
        {prior ? (
          <li data-finding-recurrence={recurrence.status}>
            This recurred after a recorded stop since an earlier Finding on the same generator, which does not say the
            earlier Finding is still open. <Link to={links.finding(prior)}>Open the earlier Finding to see its own state</Link>
          </li>
        ) : recurrence.status === "NOT_ESTABLISHED" && recurrence.reason !== "NO_EARLIER_FINDING" ? (
          <li data-finding-recurrence={recurrence.status}>
            An earlier Finding exists for this generator, but whether this repeats it is not established.
          </li>
        ) : null}
      </ul>
      <ShowAll name="finding-limits-context" summary="Access and review context">
        <ul className="site-finding__limits v69-prose" data-finding-limits-context>
          <li>Shown under the pilot&apos;s development access; sign-in and per-person access are not installed yet.</li>
          {selected.lifecycle === "SUPPORTED" ? (
            <li className="site-finding__meaning-item">
              <LifecycleSentence body={body} />
            </li>
          ) : null}
        </ul>
      </ShowAll>
      <div className="v69-prose site-finding__meaning">
        {selected.lifecycle === "SUPPORTED" ? null : <LifecycleSentence body={body} />}
        <CouldChange body={body} />
      </div>
    </Panel>
  );
}

/** finding:3 "What to do next". */
function WhatNext({ body, links }: { body: FindingDetailBody; links: SiteFindingLinks }) {
  return (
    <Panel heading="What to do next" headingId="site-finding-next-heading">
      <div className="v69-prose">
        <NextStep body={body} links={links} />
      </div>
    </Panel>
  );
}

/** finding:4: each destination with the exact selection, as the mock's attention list; exact references last. */
function WhereToLook({ body, links, params }: { body: FindingDetailBody; links: SiteFindingLinks; params: URLSearchParams }) {
  const selected = body.revision;
  const rev = body.selection.revision_id;
  const days = daysBetween(selected.episode.start, selected.episode.end);
  const primaryInterval =
    selected.interval_assessment_revision_ids.includes(selected.primary_assessment_revision_id)
      ? selected.primary_assessment_revision_id
      : null;
  const closed = body.links.performance.status === "CLOSED";
  const related: { label: string; id: string }[] = [
    ...(body.relations.recurs_after_finding_id ? [{ label: "Earlier Finding this repeats", id: body.relations.recurs_after_finding_id }] : []),
    ...body.relations.recurred_by.map((id) => ({ label: "Later Finding that repeats this", id })),
    ...(body.relations.split_from_finding_id ? [{ label: "Finding this was split from", id: body.relations.split_from_finding_id }] : []),
    ...body.relations.split_parts.map((id) => ({ label: "Part split from this Finding", id })),
    ...body.relations.merged_from.map((m) => ({ label: "Finding joined into this one", id: m.superseded_finding_id })),
    ...body.relations.merged_into.map((m) => ({ label: "Finding that carries this review", id: m.canonical_finding_id })),
  ];
  const cited = selected.cited_evidence.length;
  const items: AttentionItem[] = [
    {
      key: "analysis",
      title: "Analysis",
      body: "How the readings lead to the classification, block by block, with the full references of this version.",
      action: (
        <Link to={{ search: localViewSearch(params, "analysis") }} data-finding-destination="analysis">
          Open Analysis →
        </Link>
      ),
    },
    {
      key: "evidence",
      title: "Evidence",
      body: `${cited} accepted records ${minutes(selected.minutes.candidate) ? "support the counted blocks" : "are cited by this version"}, with where each came from.`,
      action: links.findingEvidence ? (
        <Link to={links.findingEvidence(rev)} data-finding-evidence-link>
          Open Evidence →
        </Link>
      ) : (
        <Link to={links.evidence} data-finding-evidence-link="site">
          Open the site&apos;s records →
        </Link>
      ),
    },
    ...(links.history
      ? [
          {
            key: "history",
            title: "History",
            body: "Every recorded version of this Finding, oldest first, with what changed and when.",
            action: (
              <Link to={links.history(rev)} data-finding-history-link>
                Open History →
              </Link>
            ),
          },
        ]
      : []),
    {
      key: "dispatch",
      title: `Dispatch ${days.length === 1 ? "day" : "days"}`,
      body: "How each 15-minute block of the day was assessed, with the records behind it.",
      action: closed ? (
        <p data-finding-dispatch-closed>Not available while this site&apos;s assessments are not released.</p>
      ) : (
        <ul className="site-finding__inline">
          {days.map((day, index) => (
            <li key={day}>
              <Link to={links.dispatch(day, index === 0 ? primaryInterval : null)} data-finding-dispatch-day={day}>
                Open {day} →
              </Link>
            </li>
          ))}
        </ul>
      ),
    },
    {
      key: "related",
      title: "Related Findings",
      body: related.length === 0 ? "None recorded." : "Each opens with its own state.",
      action:
        related.length === 0 ? undefined : (
          <ul className="site-finding__inline">
            {related.map((r) => (
              <li key={`${r.label}-${r.id}`}>
                <Link to={links.finding(r.id)} data-finding-related={r.id}>
                  {r.label} →
                </Link>
              </li>
            ))}
          </ul>
        ),
    },
  ];
  return (
    <Panel heading="Where to look next" headingId="site-finding-look-heading">
      <AttentionList items={items} label="Where to look next" />
      <FindingReferences body={body} />
    </Panel>
  );
}

function Code({ value }: { value: string | null | undefined }) {
  return value ? <code data-vocabulary-exempt="source-reference">{value}</code> : <span>–</span>;
}

function TechnicalDetail({ body }: { body: FindingDetailBody }) {
  const r = body.revision;
  return (
    <div className="site-finding__body" data-finding-technical>
      <Panel heading="Finding and selected version" headingId="site-finding-tech-ids-heading">
        <FactList>
          <Fact term="Finding ID"><Code value={body.finding.id} /></Fact>
          <Fact term="Finding key"><Code value={body.finding.finding_key} /></Fact>
          <Fact term="Anchor start"><Code value={body.finding.anchor_start} /></Fact>
          <Fact term="Selected version"><Code value={r.id} /> ({body.selection.revision_no} of {body.revision_page.total}, <Code value={body.selection.selected_by} />)</Fact>
          <Fact term="Latest version"><Code value={body.selection.latest_revision_id} /></Fact>
          <Fact term="Change code"><Code value={r.transition} /></Fact>
          <Fact term="Recorded state"><Code value={r.lifecycle} /> / <Code value={r.claim_level} /></Fact>
          <Fact term="Up-to-date check"><Code value={body.audit_only ? "SOURCE_CLOSED" : r.currentness.state} /></Fact>
          <Fact term="Latest version state"><Code value={body.state.lifecycle} /> / <Code value={body.state.projection} /></Fact>
          <Fact term="Assessment rules reference"><Code value={r.model_version} /></Fact>
          <Fact term="Matching rules reference"><Code value={r.matcher_version} /></Fact>
          <Fact term="Minutes (avoidable / needed / undetermined)">
            <Code value={r.minutes.candidate} /> / <Code value={r.minutes.necessary} /> / <Code value={r.minutes.indeterminate} />
          </Fact>
          <Fact term="Primary assessment revision"><Code value={r.primary_assessment_revision_id} /></Fact>
          <Fact term="Selected day assessment revision"><Code value={r.window_assessment_revision_id} /></Fact>
          <Fact term="Assessment pass"><Code value={r.analytic_run_id} /></Fact>
          <Fact term="Site settings revisions"><Code value={r.foundation_revision_ids.join(", ")} /></Fact>
          <Fact term="Signal setup revisions"><Code value={r.binding_set_revision_ids.join(", ")} /></Fact>
          <Fact term="Cited records check value"><Code value={r.cited_evidence_sha256} /></Fact>
          <Fact term="All inputs check value"><Code value={r.input_evidence_sha256} /></Fact>
          <Fact term="Recorded at"><Code value={body.watermarks.finding_recorded_at} /></Fact>
          <Fact term="Assessment built at"><Code value={body.watermarks.analytic_built_at} /></Fact>
          <Fact term="Access"><Code value={body.access_basis.split(":")[0]} /></Fact>
          <Fact term="Source gate"><Code value={body.links.performance.status} /></Fact>
        </FactList>
        <p className="site-finding__note">
          Only exact stored versions are offered; a view of the Finding as of an arbitrary past time is not.
        </p>
        {r.limitations.length > 0 ? (
          <ul className="dispatch-limits dispatch-limits--raw">
            {r.limitations.map((l) => (
              <li key={l}><Code value={l} /></li>
            ))}
          </ul>
        ) : null}
      </Panel>
      <Panel heading="Assessments cited by this version" headingId="site-finding-tech-assessments-heading">
        <DataTable labelledBy="site-finding-tech-assessments-heading">
          <thead>
            <tr>
              <th scope="col">Scope</th>
              <th scope="col">Day</th>
              <th scope="col">Assessment revision</th>
              <th scope="col">Assessment pass</th>
              <th scope="col">Primary</th>
            </tr>
          </thead>
          <tbody>
            {r.assessments.map((a) => (
              <tr key={a.assessment_revision_id} data-assessment-revision={a.assessment_revision_id}>
                <td><Code value={a.scope} /></td>
                <td>{dayOf(a.window_start)}</td>
                <td><Code value={a.assessment_revision_id} /></td>
                <td><Code value={String(a.analytic_run_id ?? "")} /></td>
                <td>{a.is_primary ? "Yes" : ""}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        {(r.indeterminate_reasons ?? []).length > 0 ? (
          <>
            <h3 className="site-finding__subheading" id="site-finding-tech-undecided">Portions that could not be decided</h3>
            <DataTable labelledBy="site-finding-tech-undecided">
              <thead>
                <tr>
                  <th scope="col">From</th>
                  <th scope="col">To</th>
                  <th scope="col">Cause kind</th>
                  <th scope="col">Assessment words</th>
                </tr>
              </thead>
              <tbody data-tech-undecided>
                {(r.indeterminate_reasons ?? []).map((p, i) => (
                  <tr key={`${p.assessment_revision_id}-${p.start ?? i}`}>
                    <td>{p.start ? stamp(p.start) : "–"}</td>
                    <td>{p.end ? stamp(p.end) : "–"}</td>
                    <td><Code value={p.kind} /></td>
                    <td><Code value={[...p.missing, ...p.reasons].join("; ")} /></td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </>
        ) : null}
        <h3 className="site-finding__subheading" id="site-finding-tech-currentness">Up-to-date check by day</h3>
        <DataTable labelledBy="site-finding-tech-currentness">
          <thead>
            <tr>
              <th scope="col">Day</th>
              <th scope="col">Status</th>
              <th scope="col">Cited day revision</th>
              <th scope="col">Currently selected</th>
            </tr>
          </thead>
          <tbody>
            {r.currentness.windows.map((w) => (
              <tr key={w.day} data-currentness-day={w.day}>
                <td>{w.day}</td>
                <td><Code value={w.status} /></td>
                <td><Code value={w.cited_window_assessment_revision_id} /></td>
                <td><Code value={w.currently_selected_window_assessment_revision_id} /></td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        <h3 className="site-finding__subheading" id="site-finding-tech-passes">Assessment passes</h3>
        <DataTable labelledBy="site-finding-tech-passes">
          <thead>
            <tr>
              <th scope="col">Pass</th>
              <th scope="col">Rules reference</th>
              <th scope="col">Day</th>
              <th scope="col">Record series</th>
              <th scope="col">Inputs</th>
            </tr>
          </thead>
          <tbody>
            {r.runs.map((run) => (
              <tr key={String(run.id)}>
                <td><Code value={String(run.id ?? "")} /></td>
                <td><Code value={run.model_version} /></td>
                <td>{run.window_start ? dayOf(run.window_start) : "–"}</td>
                <td><Code value={run.cohort_sha256?.slice(0, 16)} /></td>
                <td>{run.input_evidence_count ?? "–"}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
      <Panel heading="Cited accepted records" headingId="site-finding-tech-evidence-heading">
        <DataTable labelledBy="site-finding-tech-evidence-heading">
          <thead>
            <tr>
              <th scope="col">Record</th>
              <th scope="col">Time (UTC)</th>
              <th scope="col">Measurement</th>
              <th scope="col">Delivery batch</th>
              <th scope="col">Gateway / source / sequence</th>
            </tr>
          </thead>
          <tbody>
            {r.cited_evidence.map((e) => (
              <tr key={e.evidence_id} data-tech-evidence-id={e.evidence_id}>
                <td><Code value={e.evidence_id} /></td>
                <td>{stamp(e.source_time ?? e.interval_start ?? null)}</td>
                <td>{roleWords(e.role ?? "")}</td>
                <td><Code value={e.batch_id} /></td>
                <td>
                  <Code value={e.gateway_id?.slice(0, 8)} /> / <Code value={e.source_id?.slice(0, 8)} /> /{" "}
                  <Code value={e.sequence_epoch} />
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        <p className="site-finding__note">{body.provenance.cited_evidence_by_source.length} delivery sources. Generator off reports at stop ends: {r.off_reports.length}.</p>
        {body.provenance.case_annotations.map((note, index) => (
          <p key={index} className="site-finding__note" data-case-id={String(note.case_id ?? "")}>
            Demonstration case: <Code value={String(note.case_id ?? "")} /> <Code value={String(note.kind ?? "")} />
          </p>
        ))}
      </Panel>
      <Panel heading="Relations" headingId="site-finding-tech-relations-heading">
        <FactList>
          <Fact term="Carries the review"><Code value={body.relations.canonical_finding_id} /></Fact>
          <Fact term="Repeats"><Code value={body.relations.recurs_after_finding_id} /></Fact>
          <Fact term="Repeat link status"><Code value={body.relations.recurrence.status} /></Fact>
          <Fact term="Split from"><Code value={body.relations.split_from_finding_id} /></Fact>
          <Fact term="Split parts"><Code value={body.relations.split_parts.join(", ")} /></Fact>
          <Fact term="Joined from"><Code value={body.relations.merged_from.map((m) => m.superseded_finding_id).join(", ")} /></Fact>
          <Fact term="Repeated by"><Code value={body.relations.recurred_by.join(", ")} /></Fact>
        </FactList>
      </Panel>
      <Panel heading="Every version" headingId="site-finding-tech-versions-heading">
        <DataTable labelledBy="site-finding-tech-versions-heading">
          <thead>
            <tr>
              <th scope="col">No.</th>
              <th scope="col">Version</th>
              <th scope="col">Change code</th>
              <th scope="col">State</th>
              <th scope="col">Changed amount</th>
              <th scope="col">Avoidable minutes</th>
            </tr>
          </thead>
          <tbody>
            {body.revisions.map((rev) => (
              <tr key={rev.id} data-tech-version={rev.id}>
                <td>{rev.revision_no}</td>
                <td><Code value={rev.id} /></td>
                <td><Code value={rev.transition} /></td>
                <td><Code value={rev.lifecycle} /></td>
                <td>{rev.support_changed ? "Yes" : "No"}</td>
                <td><Code value={rev.candidate_minutes} /></td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
    </div>
  );
}
