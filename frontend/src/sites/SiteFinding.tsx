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

import { DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import { clock, durationText, groupLimitations, limitationWords, minutes, qualityWords, roleWords, stamp } from "./dispatchWords";
import type {
  CitedEvidence,
  FindingClient,
  FindingDetailBody,
  FindingReadResult,
  RevisionGroup,
  RevisionSummary,
} from "./findingClient";
import { LocalViews, localView } from "./findingPresentation";
import {
  currentnessWords,
  unconfirmedCause,
  dayOf,
  daysBetween,
  followsClosure,
  LIFECYCLE_WORDS,
  PORTION_FILL,
  portionWords,
  spanMinutes,
  transitionWords,
  versionWords,
} from "./findingWords";

export const FINDING_VIEWS_LABEL = "Finding views";
const EVIDENCE_PREVIEW = 8;

export interface SiteFindingLinks {
  /** This or another Finding of the Site, optionally at an exact version. */
  finding: (findingId: string, revisionId?: string | null) => string;
  /** The Site's Performance > Dispatch at one UTC day, optionally one assessed period. */
  dispatch: (day: string, intervalRevisionId?: string | null) => string;
  /** The Site's accepted records. */
  evidence: string;
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
  return (
    <section
      className="site-finding"
      aria-labelledby="site-finding-state-heading"
      data-finding-id={body.finding.id}
      data-finding-revision={body.selection.revision_id}
      data-finding-lifecycle={body.revision.lifecycle}
      data-finding-currentness={body.revision.currentness.state}
    >
      <LocalViews label={FINDING_VIEWS_LABEL} current={view} params={params} />
      <LeadState body={body} links={links} />
      <StatusChips body={body} />
      {view === "analysis" ? (
        <TechnicalDetail body={body} />
      ) : (
        <div className="site-finding__body">
          <WhatHappened body={body} links={links} />
          <div className="site-finding__pair">
            <WhatLimits body={body} links={links} />
            <Panel heading="What to do next" headingId="site-finding-next-heading">
              {links.recommendation ? (
                <p data-finding-recommendation-link>
                  A fixed rule may propose a battery reserve trial for this version.{" "}
                  <Link to={links.recommendation(body.selection.revision_id)}>Open the recommendation</Link>. Nothing
                  here asks you to change how the generator is operated.
                </p>
              ) : (
                <p data-finding-recommendation-link="none">
                  No recommendation link is offered here; nothing here asks you to change how the generator is operated.
                </p>
              )}
            </Panel>
          </div>
          <WhereToLook body={body} links={links} />
          <Versions body={body} />
          <RecordsSummary body={body} links={links} />
        </div>
      )}
    </section>
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
  return (
    <Panel heading={chosen.heading} headingId="site-finding-refused-heading">
      <p data-finding-read={read.status}>{chosen.text}</p>
      {read.message ? <p className="site-finding__note">Reason given: {read.message}</p> : null}
    </Panel>
  );
}

/** The state that limits what the page shows, first; then the recorded state. */
function LeadState({ body, links }: { body: FindingDetailBody; links: SiteFindingLinks }) {
  const selected = body.revision;
  const lifecycle = LIFECYCLE_WORDS[selected.lifecycle];
  const currentness = currentnessWords(body.audit_only ? "SOURCE_CLOSED" : selected.currentness.state);
  const merged = body.state.merged_into_finding_id;
  const afterClosure =
    selected.lifecycle !== "NO_LONGER_SUPPORTED" && followsClosure(body.revisions, selected);
  const tone = body.audit_only || merged || !body.selection.is_latest || currentness.attention ? "attention" : "plain";
  return (
    <div className={`dispatch-status site-finding__lead site-finding__lead--${tone}`} role="status">
      <h2 id="site-finding-state-heading" className="site-finding__lead-heading">
        {body.audit_only
          ? "Record only: this site's assessments are not released"
          : merged
            ? "Joined into an earlier Finding"
            : !body.selection.is_latest
              ? `Earlier version ${body.selection.revision_no} of ${body.revision_page.total}`
              : currentness.attention && selected.currentness.state !== "CURRENT"
                ? `${lifecycle.label} · ${currentness.label.toLowerCase()}`
                : lifecycle.label}
      </h2>
      {body.audit_only ? (
        <p data-finding-audit-only>
          This exact version is kept as a record. It is not a current result, and whether it is still up to date is
          not checked while the site&apos;s assessments are not released.
        </p>
      ) : null}
      {merged ? (
        <p data-finding-merged={merged}>
          Later records showed one longer period. The earlier Finding now carries the review.{" "}
          <Link to={links.finding(merged)}>Open the Finding that carries the review</Link>
        </p>
      ) : null}
      {!body.selection.is_latest ? (
        <p data-finding-earlier-version>
          A later version replaces this one. <Link to={links.finding(body.finding.id)}>Open the latest version</Link>
        </p>
      ) : null}
      <p data-finding-lifecycle-sentence>
        {lifecycle.sentence}
        {selected.lifecycle === "UNCONFIRMED"
          ? ` ${unconfirmedCause(selected.indeterminate_cause)}`
          : ""}
      </p>
      {afterClosure ? (
        <p data-finding-after-closure>
          {selected.lifecycle === "UNCONFIRMED"
            ? "This review had already been closed as no longer supported. The newer assessment cannot confirm either way; this is not a new issue."
            : "This review had been closed as no longer supported; a later assessment supports it again for the same period."}
        </p>
      ) : null}
      {body.audit_only || merged || !body.selection.is_latest ? null : (
        <p data-finding-currentness={selected.currentness.state}>{currentness.sentence}</p>
      )}
    </div>
  );
}

function StatusChips({ body }: { body: FindingDetailBody }) {
  const selected = body.revision;
  const currentness = currentnessWords(body.audit_only ? "SOURCE_CLOSED" : selected.currentness.state);
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
  const needed = minutes(selected.minutes.necessary) ?? 0;
  const unknown = minutes(selected.minutes.indeterminate) ?? 0;
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
  return (
    <Panel heading="What happened" headingId="site-finding-happened-heading">
      <p className="site-finding__big" data-finding-sentence>
        {supported
          ? `${runWords(body)} For ${durationText(avoidable)} of that time, solar power and the battery reported enough capacity to meet site demand, so the generator was possibly avoidable.`
          : selected.lifecycle === "MERGED"
            ? `This Finding covered ${periodWords(selected.episode.start, selected.episode.end)} before it was joined into an earlier Finding.`
            : selected.lifecycle === "UNCONFIRMED"
              ? `This Finding covers ${periodWords(selected.episode.start, selected.episode.end)}. ${body.selection.is_latest ? "The latest assessment" : "This version"} cannot decide whether any of that time was possibly avoidable.`
              : `This Finding covers ${periodWords(selected.episode.start, selected.episode.end)}. ${body.selection.is_latest ? "The latest assessment" : "This version"} of that period counts no possibly avoidable time.`}
      </p>
      <p>
        Only the possibly avoidable blocks are counted. Needed time and time that cannot be determined stay separate,
        and the whole period is not said to be avoidable. This is a bounded estimate from the reported records, not
        proof of wasted fuel.
      </p>
      <ul className="dispatch-cards" aria-label="Time in this Finding">
        <Card label="Possibly avoidable" value={durationText(avoidable)} note="Counted in this Finding" code="CANDIDATE_AVOIDABLE" />
        <Card label="Needed" value={durationText(needed)} note="A recorded reason required the generator" code="NECESSARY" />
        <Card label="Cannot determine" value={durationText(unknown)} note="Could not be decided either way" code="INDETERMINATE" />
        <Card label="Period covered" value={durationText(period)} note="From first to last block in this Finding" code="PERIOD" />
        <Card label="Fuel and cost" value="Not yet available" note="No fuel or money estimate is made here" code="MONEY" />
      </ul>
      {portions.length > 0 ? (
        <div className="site-finding__timeline">
          <h3 className="site-finding__subheading" id="site-finding-blocks-heading">
            Blocks in this Finding
          </h3>
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
            <span className="dispatch-swatch dispatch-fill--unknown" /> Cannot determine · Times are UTC. Select a
            block to see it.
          </p>
          {chosen ? (
            <div className="dispatch-block-detail" data-finding-portion-detail>
              <h3>
                {portionWords(chosen.classification)}: {stamp(chosen.start)}–{clock(chosen.end)} UTC
              </h3>
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

function Card({ label, value, note, code }: { label: string; value: string; note: string; code: string }) {
  return (
    <li className="dispatch-card" data-finding-card={code}>
      <span className="dispatch-card__label">{label}</span>
      <span className="dispatch-card__value">{value}</span>
      <span className="dispatch-card__note">{note}</span>
    </li>
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
      <ul className="site-finding__limits">
        <li>
          The estimate uses the records sent from site. Solar and battery capacity are as reported; nothing was
          measured directly at the fuel tank.
        </li>
        {recordGap ? (
          <li data-finding-record-gap>
            Some records this version needs are missing or conflict over part of the period, so that part could not
            be decided.
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
            {joined.length === 1 ? "One short gap" : `${joined.length} short gaps`} of 20 minutes or less inside this
            period had records for every minute; they are part of the same period but add no possibly avoidable time.
          </li>
        ) : null}
        {stops.length > 0 ? (
          <li data-finding-stop-bridges={stops.length}>
            The generator stopped {stops.length === 1 ? "once" : `${stops.length} times`} for 20 minutes or less
            (first at {stamp(stops[0].start)} UTC). It reported off at both ends with nothing contrary in between, so
            this is still one period; the stop adds no possibly avoidable time. If few reports arrive during a stop,
            this joining rests on those two off reports.
          </li>
        ) : null}
        {prior ? (
          <li data-finding-recurrence={recurrence.status}>
            This happened before: an earlier Finding covered the same generator, separated from this one by a
            recorded stop. That link says the pattern recurred; it does not say the earlier Finding is still open.{" "}
            <Link to={links.finding(prior)}>Open the earlier Finding to see its own state</Link>
          </li>
        ) : recurrence.status === "NOT_ESTABLISHED" && recurrence.reason !== "NO_EARLIER_FINDING" ? (
          <li data-finding-recurrence={recurrence.status}>
            An earlier Finding exists for this generator, but whether this repeats it is not established: the time
            between them is not fully assessed or no recorded generator stop separates them.
          </li>
        ) : null}
        <li>
          Shown under the pilot&apos;s development access. Sign-in and per-person access are not installed yet.
        </li>
      </ul>
      <p className="site-finding__note">
        <Link to={{ search: "?view=analysis" + (body.selection.is_latest ? "" : `&revision_id=${body.selection.revision_id}`) }}>
          See the technical detail
        </Link>
      </p>
    </Panel>
  );
}

function WhereToLook({ body, links }: { body: FindingDetailBody; links: SiteFindingLinks }) {
  const selected = body.revision;
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
  return (
    <Panel heading="Where to look next" headingId="site-finding-look-heading">
      <ol className="site-finding__look">
        <li>
          <h3>Dispatch {days.length === 1 ? "day" : "days"}</h3>
          <p>How each 15-minute block of the day was assessed, with the records behind it.</p>
          {closed ? (
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
          )}
        </li>
        <li>
          <h3>Accepted records</h3>
          <p>
            {selected.cited_evidence.length} accepted records {minutes(selected.minutes.candidate) ? "support the counted blocks" : "are cited by this version"}. They are listed below and
            on the site&apos;s records page.
          </p>
          <Link to={links.evidence}>Open the site&apos;s records →</Link>
        </li>
        <li>
          <h3>Related Findings</h3>
          {related.length === 0 ? (
            <p>None recorded.</p>
          ) : (
            <ul className="site-finding__inline">
              {related.map((r) => (
                <li key={`${r.label}-${r.id}`}>
                  <Link to={links.finding(r.id)} data-finding-related={r.id}>
                    {r.label} →
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </li>
        {links.history ? (
          <li>
            <h3>History</h3>
            <p>Every recorded version of this Finding, oldest first, with what changed and when.</p>
            <Link to={links.history(body.selection.revision_id)} data-finding-history-link>
              Open the Finding&apos;s history →
            </Link>
          </li>
        ) : null}
      </ol>
    </Panel>
  );
}

function revisionLink(id: string, latestId: string): string {
  return id === latestId ? "?" : `?revision_id=${encodeURIComponent(id)}`;
}

function Versions({ body }: { body: FindingDetailBody }) {
  const byId = new Map(body.revisions.map((r) => [r.id, r]));
  return (
    <Panel heading="Versions" headingId="site-finding-versions-heading">
      <p>
        A Finding keeps every version. Select one to see it as it was recorded; its address stays the same after a
        reload.
      </p>
      <ol className="site-finding__versions">
        {body.revision_groups.map((group) => (
          <VersionGroup key={group.revision_ids[0]} group={group} byId={byId} body={body} />
        ))}
      </ol>
      {body.revision_page.next_after_revision_no !== null ? (
        <p className="site-finding__note">Older versions beyond this page are kept and listed in Analysis.</p>
      ) : null}
    </Panel>
  );
}

function VersionGroup({
  group,
  byId,
  body,
}: {
  group: RevisionGroup;
  byId: Map<string, RevisionSummary>;
  body: FindingDetailBody;
}) {
  const latestId = body.selection.latest_revision_id;
  const entry = (id: string) => {
    const rev = byId.get(id);
    const selected = id === body.selection.revision_id;
    return (
      <Link
        to={{ search: revisionLink(id, latestId) }}
        aria-current={selected ? "true" : undefined}
        data-finding-version={id}
        data-transition={rev?.transition}
      >
        Version {rev?.revision_no ?? "?"}: {transitionWords(rev?.transition ?? "")}
        {rev ? ` · recorded ${stamp(rev.recorded_at)} UTC` : ""}
        {id === latestId ? " (latest)" : ""}
        {selected ? " (shown)" : ""}
      </Link>
    );
  };
  if (group.kind !== "BASIS_REFRESHED" || group.count === 1) {
    return (
      <li className="site-finding__version" data-version-group={group.kind}>
        {entry(group.revision_ids[0])}
        {group.kind === "BASIS_REFRESHED" ? (
          <span className="site-finding__note"> The period and possibly avoidable time did not change.</span>
        ) : null}
      </li>
    );
  }
  const holdsSelected = group.revision_ids.includes(body.selection.revision_id);
  return (
    <li className="site-finding__version" data-version-group={group.kind} data-version-count={group.count}>
      <Disclosure
        name={`versions-${group.first_revision_no}`}
        defaultOpen={holdsSelected}
        summary={`Versions ${group.first_revision_no}–${group.last_revision_no}: ${group.count} assessment updates; period and possibly avoidable time unchanged`}
      >
        <ol className="site-finding__versions">
          {group.revision_ids.map((id) => (
            <li key={id}>{entry(id)}</li>
          ))}
        </ol>
      </Disclosure>
    </li>
  );
}

function RecordsSummary({ body, links }: { body: FindingDetailBody; links: SiteFindingLinks }) {
  const evidence = body.revision.cited_evidence;
  const byRole = new Map<string, number>();
  for (const e of evidence) {
    const key = e.role ?? "unknown";
    byRole.set(key, (byRole.get(key) ?? 0) + 1);
  }
  const notes = body.provenance.case_annotations;
  return (
    <Panel heading="Records behind this version" headingId="site-finding-records-heading">
      <p>
        {evidence.length} accepted records {minutes(body.revision.minutes.candidate) ? "support the counted blocks" : "are cited by this version"}
        {byRole.size > 0
          ? `: ${[...byRole.entries()].map(([role, n]) => `${roleWords(role)} ${n}`).join(", ")}`
          : ""}
        .
      </p>
      {notes.length > 0 ? (
        <aside className="dispatch-demo-notes" aria-label="Demonstration data notes" data-finding-case-notes={notes.length}>
          <h3>Note supplied with the demonstration data</h3>
          <ul>
            {notes.map((note, index) => (
              <li key={index} data-case-kind={String(note.kind ?? "")}>
                {note.kind === "DEMO_MANIFEST_GATEWAY_CASE"
                  ? "These records came through the site's registered gateway, the ordinary delivery path."
                  : "These records are a prepared test case sent with the gateway's credential, not the ordinary delivery path."}
              </li>
            ))}
          </ul>
          <p>This note comes from the demonstration data&apos;s own description; it does not change the result.</p>
        </aside>
      ) : null}
      {evidence.length > 0 ? <EvidenceTable evidence={evidence} links={links} /> : null}
    </Panel>
  );
}

function EvidenceTable({ evidence, links }: { evidence: CitedEvidence[]; links: SiteFindingLinks }) {
  const sorted = [...evidence].sort((a, b) => String(a.source_time ?? "").localeCompare(String(b.source_time ?? "")));
  const head = sorted.slice(0, EVIDENCE_PREVIEW);
  const rest = sorted.slice(EVIDENCE_PREVIEW);
  const table = (rows: CitedEvidence[], id: string) => (
    <DataTable labelledBy={id}>
      <thead>
        <tr>
          <th scope="col">Time (UTC)</th>
          <th scope="col">Measurement</th>
          <th scope="col">Value</th>
          <th scope="col">Quality</th>
          <th scope="col">Record</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((e) => (
          <tr key={e.evidence_id} data-evidence-id={e.evidence_id}>
            <td>{stamp(e.source_time ?? e.interval_start ?? null)}</td>
            <td>{roleWords(e.role ?? "")}</td>
            <td>{e.value === null || e.value === undefined ? "–" : `${e.value}${e.unit ? ` ${e.unit}` : ""}`}</td>
            <td>{qualityWords(e.quality ?? "")}</td>
            <td>
              <code data-vocabulary-exempt="source-reference">{e.evidence_id.slice(0, 8)}</code>
            </td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
  return (
    <>
      <h3 className="site-finding__subheading" id="site-finding-records-first">
        First {head.length} records by time
      </h3>
      {table(head, "site-finding-records-first")}
      {rest.length > 0 ? (
        <Disclosure name="finding-records-rest" summary={`Show the other ${rest.length} records`}>
          <h3 className="site-finding__subheading" id="site-finding-records-rest">
            Other records
          </h3>
          {table(rest, "site-finding-records-rest")}
        </Disclosure>
      ) : null}
      <p className="site-finding__note">
        Each record&apos;s full delivery history is on <Link to={links.evidence}>the site&apos;s records page</Link>; full
        identifiers are in Analysis.
      </p>
    </>
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
          <Fact term="Assessment rule version"><Code value={r.model_version} /></Fact>
          <Fact term="Matching rule version"><Code value={r.matcher_version} /></Fact>
          <Fact term="Minutes (avoidable / needed / undetermined)">
            <Code value={r.minutes.candidate} /> / <Code value={r.minutes.necessary} /> / <Code value={r.minutes.indeterminate} />
          </Fact>
          <Fact term="Primary assessment revision"><Code value={r.primary_assessment_revision_id} /></Fact>
          <Fact term="Selected day assessment revision"><Code value={r.window_assessment_revision_id} /></Fact>
          <Fact term="Assessment pass"><Code value={r.analytic_run_id} /></Fact>
          <Fact term="Site settings revisions"><Code value={r.foundation_revision_ids.join(", ")} /></Fact>
          <Fact term="Signal setup revisions"><Code value={r.binding_set_revision_ids.join(", ")} /></Fact>
          <Fact term="Cited records digest"><Code value={r.cited_evidence_sha256} /></Fact>
          <Fact term="All inputs digest"><Code value={r.input_evidence_sha256} /></Fact>
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
              <th scope="col">Rule version</th>
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
