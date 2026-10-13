/**
 * S4-03 phase 3 (`I-finding-history-ui`): the History child view of one
 * durable Finding (mock `finding-history:1`), at
 * `/sites/{site}/findings/{finding}/history[?revision_id=]`.
 *
 * Reads `GET /api/sites/{site}/findings/{id}/history` page by page until the
 * read reports no next page, so every stored version is listed in version
 * order; the loaded count is checked against the read's total. Each row links
 * to that exact version of the Finding and to its Evidence; the selected and
 * the latest version are marked separately. An omitted version is the latest
 * at read time and is labelled so; an unknown or foreign version is refused,
 * never replaced. A History row states only how many cited records were found
 * as accepted records - the full record trail is checked on the Evidence page,
 * so no lineage verdict is drawn here. Versions are kept as recorded: a later
 * reading appends a version and never rewrites an earlier one, and the times
 * shown are not a way to view the Finding as of an earlier moment.
 */
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Fact, FactList, Panel } from "../ui";
import { durationText, minutes, stamp } from "./dispatchWords";
import type { FindingClient, FindingHistoryBody, FindingReadResult, HistoryRevision } from "./findingClient";
import { LIFECYCLE_WORDS, transitionWords } from "./findingWords";

export const HISTORY_PAGE_SIZE = 100;

export interface SiteFindingHistoryLinks {
  /** This Finding's History, at an exact version or (null) the latest at read time. */
  history: (revisionId: string | null) => string;
  /** This Finding's Evidence at an exact version. */
  evidence: (revisionId: string | null) => string;
  /** This or another Finding of the Site, optionally at an exact version. */
  finding: (findingId: string, revisionId?: string | null) => string;
  /** Another Finding's History (merge, split and recurrence links). */
  otherHistory: (findingId: string) => string;
}

type HistoryRead =
  | { status: "loading" }
  | { status: "refused"; read: Exclude<FindingReadResult<FindingHistoryBody>, { status: "loaded" }> }
  | { status: "loaded"; first: FindingHistoryBody; rows: HistoryRevision[]; pages: number; complete: boolean; drift: boolean };

function at(instant: string | null | undefined): number | null {
  if (!instant) {
    return null;
  }
  const value = Date.parse(instant);
  return Number.isFinite(value) ? value : null;
}

function minuteText(value: string): string {
  const m = minutes(value);
  return m === null ? "–" : durationText(m);
}

export function SiteFindingHistory({
  siteId,
  findingId,
  client,
  links,
}: {
  siteId: string;
  findingId: string;
  client: FindingClient;
  links: SiteFindingHistoryLinks;
}) {
  const [params] = useSearchParams();
  const revisionId = params.get("revision_id");
  const [read, setRead] = useState<HistoryRead>({ status: "loading" });

  useEffect(() => {
    let active = true;
    setRead({ status: "loading" });
    void (async () => {
      const first = await client.getFindingHistory(siteId, findingId, revisionId, 0, HISTORY_PAGE_SIZE);
      if (!active) {
        return;
      }
      if (first.status !== "loaded") {
        setRead({ status: "refused", read: first });
        return;
      }
      const rows = [...first.value.revisions];
      let next = first.value.page.next_after_revision_no;
      let pages = 1;
      let complete = true;
      let drift = false;
      while (next !== null) {
        const more = await client.getFindingHistory(siteId, findingId, revisionId, next, HISTORY_PAGE_SIZE);
        if (!active) {
          return;
        }
        if (more.status !== "loaded") {
          complete = false;
          break;
        }
        pages += 1;
        // A version recorded while the pages were read changes the total or the latest: say so, keep what was read.
        if (
          more.value.page.total !== first.value.page.total ||
          more.value.selection.latest_revision_id !== first.value.selection.latest_revision_id
        ) {
          drift = true;
        }
        rows.push(...more.value.revisions);
        next = more.value.page.next_after_revision_no;
      }
      setRead({ status: "loaded", first: first.value, rows, pages, complete, drift });
    })();
    return () => {
      active = false;
    };
  }, [client, siteId, findingId, revisionId]);

  if (read.status === "loading") {
    return <p>Loading the Finding&apos;s history.</p>;
  }
  if (read.status === "refused") {
    return <Refused read={read.read} pinned={revisionId !== null} latestHref={links.history(null)} />;
  }
  const { first: body, rows } = read;
  return (
    <section
      className="site-finding site-finding-history"
      aria-labelledby="finding-history-selection-heading"
      data-finding-history={body.finding.id}
      data-finding-revision={body.selection.revision_id}
      data-history-selected-by={body.selection.selected_by}
      data-history-total={body.page.total}
      data-history-loaded={rows.length}
    >
      <Selection body={body} links={links} />
      <Versions body={body} rows={rows} read={read} links={links} />
      <Related body={body} links={links} />
    </section>
  );
}

function Refused({
  read,
  pinned,
  latestHref,
}: {
  read: Exclude<FindingReadResult<FindingHistoryBody>, { status: "loaded" }>;
  pinned: boolean;
  latestHref: string;
}) {
  const words: Record<typeof read.status, { heading: string; text: string }> = {
    not_found: {
      heading: "Finding not found",
      text: pinned
        ? "This site has no such Finding or no such version of it. The version in the address is kept as given; the latest version is not shown in its place."
        : "This site has no such Finding.",
    },
    unauthenticated: { heading: "Sign-in required", text: "Sign in to read this site's Findings." },
    forbidden: { heading: "No access", text: "Your account has no access to this site's Findings." },
    closed: {
      heading: "Assessments not released",
      text:
        "This site's assessments are not released for use yet, so the current Finding's history is not shown. " +
        "A link to an exact saved version still opens its history as a record.",
    },
    unavailable: {
      heading: "History could not be read",
      text: "The Finding's history could not be read just now. Nothing here means the Finding has no versions.",
    },
  };
  const chosen = words[read.status];
  return (
    <Panel heading={chosen.heading} headingId="finding-history-refused-heading">
      <p data-finding-read={read.status}>{chosen.text}</p>
      {read.message ? <p className="site-finding__note">Reason given: {read.message}</p> : null}
      {read.status === "not_found" && pinned ? (
        <p>
          <Link to={latestHref} data-history-open-latest>
            Open the history at the latest version instead
          </Link>
        </p>
      ) : null}
    </Panel>
  );
}

/** Which version is selected, and how: non-current status first. */
function Selection({ body, links }: { body: FindingHistoryBody; links: SiteFindingHistoryLinks }) {
  const { selection, state } = body;
  const no = selection.revision_no;
  const latestState = LIFECYCLE_WORDS[state.lifecycle];
  return (
    <Panel heading="Version history" headingId="finding-history-selection-heading">
      {body.audit_only ? (
        <p className="site-finding__lead" data-history-audit-only>
          Record only. This site&apos;s assessments are not released for use, so these saved versions are shown as a
          record, not as the current Finding.
        </p>
      ) : null}
      {latestState === undefined || state.lifecycle === "SUPPORTED" ? null : (
        <p className="site-finding__lead" data-history-lifecycle={state.lifecycle}>
          State recorded by the latest version: <strong>{latestState.label}</strong>. {latestState.sentence}
        </p>
      )}
      {!selection.is_latest ? (
        <p className="site-finding__lead" data-history-earlier-version>
          Version {no} is selected. It is an earlier version: version {selection.latest_revision_no} replaces it.{" "}
          <Link to={links.history(selection.latest_revision_id)} data-history-select-latest>
            Select the latest version
          </Link>
        </p>
      ) : selection.selected_by === "LATEST_RECORDED" ? (
        <p data-history-latest-at-read>
          Latest version at the time of reading (version {no}). A version recorded later would replace it on reload.{" "}
          <Link to={links.history(selection.revision_id)} data-history-pin>
            Keep this exact version
          </Link>
        </p>
      ) : (
        <p data-history-pinned-latest>Version {no}, the latest recorded version, selected by its exact reference.</p>
      )}
      <p>
        Versions are kept exactly as recorded. A reading that arrives later adds a new version; it never changes an
        earlier one. The times below describe each version; they are not a way to view the Finding as of an earlier
        moment.
      </p>
      <p>
        <Link to={links.finding(body.finding.id, selection.revision_id)} data-history-open-finding>
          Open version {no} of the Finding
        </Link>
        {" · "}
        <Link to={links.evidence(selection.revision_id)} data-history-open-evidence>
          Open version {no}&apos;s evidence
        </Link>
      </p>
    </Panel>
  );
}

function Versions({
  body,
  rows,
  read,
  links,
}: {
  body: FindingHistoryBody;
  rows: HistoryRevision[];
  read: Extract<HistoryRead, { status: "loaded" }>;
  links: SiteFindingHistoryLinks;
}) {
  const total = body.page.total;
  const groupOf = new Map<string, { count: number; first: number; last: number }>();
  for (const group of body.revision_groups) {
    if (group.kind === "BASIS_REFRESHED" && group.count > 1) {
      for (const id of group.revision_ids) {
        groupOf.set(id, { count: group.count, first: group.first_revision_no, last: group.last_revision_no });
      }
    }
  }
  const recordedAt = new Map(rows.map((r) => [r.id, r.times.recorded_at]));
  return (
    <Panel heading="Every version" headingId="finding-history-versions-heading">
      {body.earlier_versions === "NONE" ? (
        <p data-history-no-earlier>No earlier versions: this Finding has one recorded version.</p>
      ) : null}
      {read.complete && rows.length === total ? (
        <p data-history-complete>
          All {total} recorded versions are listed, oldest first.
        </p>
      ) : (
        <p className="site-finding__lead" data-history-incomplete>
          Only {rows.length} of {total} recorded versions could be read, so this list is incomplete. Reload to read the
          rest.
        </p>
      )}
      {read.drift ? (
        <p className="site-finding__lead" data-history-drift>
          A new version was recorded while this list was being read. Reload to see the list as it is now.
        </p>
      ) : null}
      <ol className="site-finding__versions site-finding-history__list">
        {rows.map((r) => (
          <VersionRow
            key={r.id}
            r={r}
            findingId={body.finding.id}
            group={groupOf.get(r.id)}
            previousRecordedAt={r.previous_revision_id ? recordedAt.get(r.previous_revision_id) ?? null : null}
            links={links}
          />
        ))}
      </ol>
    </Panel>
  );
}

function VersionRow({
  r,
  findingId,
  group,
  previousRecordedAt,
  links,
}: {
  r: HistoryRevision;
  findingId: string;
  group: { count: number; first: number; last: number } | undefined;
  previousRecordedAt: string | null;
  links: SiteFindingHistoryLinks;
}) {
  const state = LIFECYCLE_WORDS[r.lifecycle];
  const accepted = at(r.times.accepted_at);
  const previous = at(previousRecordedAt);
  const lateEvidence = accepted !== null && previous !== null && accepted > previous;
  const cited = r.cited_evidence;
  const priorIds = [...(r.prior_window_assessment_revision_ids ?? []), ...(r.prior_interval_assessment_revision_ids ?? [])];
  return (
    <li
      className="site-finding-history__version"
      data-history-revision={r.id}
      data-history-revision-no={r.revision_no}
      data-history-selected={r.is_selected ? "true" : undefined}
      data-history-latest={r.is_latest ? "true" : undefined}
      aria-current={r.is_selected ? "true" : undefined}
    >
      <h3 className="site-finding__subheading">
        Version {r.revision_no} · {transitionWords(r.transition)}
        {r.is_selected ? <span data-history-selected-mark> · Selected</span> : null}
        {r.is_latest ? <span data-history-latest-mark> · Latest</span> : null}
      </h3>
      {group ? (
        <p className="site-finding__note" data-history-group>
          One of {group.count} assessment updates with the amount unchanged (versions {group.first}–{group.last}); each
          stays its own version.
        </p>
      ) : null}
      {lateEvidence ? (
        <p data-history-late-evidence>
          Cites readings accepted after version {r.revision_no - 1} was recorded. Version {r.revision_no - 1} keeps the
          records it cited.
        </p>
      ) : null}
      <FactList>
        <Fact term="State">{state?.label ?? r.lifecycle}</Fact>
        <Fact term="Version recorded">{stamp(r.times.recorded_at)}</Fact>
        <Fact term="Period">
          {stamp(r.episode.start)} to {stamp(r.episode.end)}
        </Fact>
        <Fact term="Possibly avoidable time">{minuteText(r.minutes.candidate)}</Fact>
        <Fact term="Generator time needed">{minuteText(r.minutes.necessary)}</Fact>
        <Fact term="Time that could not be decided">{minuteText(r.minutes.indeterminate)}</Fact>
        <Fact term="Amount changed from the previous version">{r.revision_no === 1 ? "First version" : r.support_changed ? "Yes" : "No"}</Fact>
        <Fact term="Cited records">
          <span data-history-cited={cited.count} data-history-accepted-rows={cited.accepted_rows}>
            {cited.count} cited; {cited.resolved} of {cited.count} found as accepted records
          </span>
          {cited.accepted_rows === "UNRESOLVED_PRESENT" ? (
            <span data-history-unresolved> ({cited.count - cited.resolved} could not be found)</span>
          ) : null}
          . <Link to={links.evidence(r.id)} data-history-check-evidence={r.id}>Check their record trail on the Evidence page</Link>
        </Fact>
        <Fact term="Readings from">
          {stamp(r.times.source_time.first)} to {stamp(r.times.source_time.last)}
        </Fact>
        <Fact term="Last cited reading received">{stamp(r.times.received_at)}</Fact>
        <Fact term="Last cited reading accepted">{stamp(r.times.accepted_at)}</Fact>
        <Fact term="Analysis finished">{stamp(r.times.analytic_completed_at)}</Fact>
        <Fact term="Assessment rules">{r.model_version}</Fact>
        <Fact term="Assessment behind it">
          <code data-vocabulary-exempt="source-reference">{r.primary_assessment_revision_id.slice(0, 8)}</code>
          {priorIds.length > 0 ? (
            <>
              {" "}
              (previously{" "}
              {priorIds.map((id, index) => (
                <span key={id}>
                  {index > 0 ? ", " : ""}
                  <code data-vocabulary-exempt="source-reference">{id.slice(0, 8)}</code>
                </span>
              ))}
              )
            </>
          ) : null}
        </Fact>
      </FactList>
      <p className="site-finding-history__links">
        <Link to={links.history(r.id)} data-history-select={r.id} aria-current={r.is_selected ? "true" : undefined}>
          Select version {r.revision_no}
        </Link>
        {" · "}
        <Link to={links.finding(findingId, r.id)} data-history-finding-link={r.id}>
          Open this version
        </Link>
        {" · "}
        <Link to={links.evidence(r.id)} data-history-evidence-link={r.id}>
          Its evidence
        </Link>
      </p>
    </li>
  );
}

/** Merge, split and recurrence links stay as recorded; each opens that Finding's own history. */
function Related({ body, links }: { body: FindingHistoryBody; links: SiteFindingHistoryLinks }) {
  const r = body.relations;
  const items: { label: string; id: string }[] = [
    ...r.merged_into.map((m) => ({ label: "Joined into", id: m.canonical_finding_id })),
    ...r.merged_from.map((m) => ({ label: "Joined from", id: m.superseded_finding_id })),
    ...(r.split_from_finding_id ? [{ label: "Split from", id: r.split_from_finding_id }] : []),
    ...r.split_parts.map((id) => ({ label: "Split part", id })),
    ...(r.recurs_after_finding_id ? [{ label: "Recurs after", id: r.recurs_after_finding_id }] : []),
    ...r.recurred_by.map((id) => ({ label: "Recurred as", id })),
  ].filter((item) => item.id && item.id !== body.finding.id);
  if (items.length === 0) {
    return null;
  }
  return (
    <Panel heading="Related Findings" headingId="finding-history-related-heading">
      <ul className="site-finding__inline">
        {items.map((item) => (
          <li key={`${item.label}-${item.id}`}>
            <Link to={links.otherHistory(item.id)} data-history-related={item.id}>
              {item.label} Finding <code data-vocabulary-exempt="source-reference">{item.id.slice(0, 8)}</code> - its history
            </Link>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
