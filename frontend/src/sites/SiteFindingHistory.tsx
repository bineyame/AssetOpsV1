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

import { DataTable, Disclosure, ExactReferences, Panel, ProductStatus, ShowAll } from "../ui";

/** W1-F3 height phase: how many of the latest versions the default view shows, as the mock's three rows. */
const LATEST_SHOWN = 3;
import { durationText, minutes, stamp } from "./dispatchWords";
import type { FindingClient, FindingHistoryBody, FindingReadResult, HistoryRevision } from "./findingClient";
import { findingRefusalWords } from "./findingPresentation";
import { findingCurrentnessWords, LIFECYCLE_WORDS, transitionWords } from "./findingWords";
import "./w1ux02-finding.css";
import "./w1f3-finding-history.css";

export const HISTORY_PAGE_SIZE = 100;
const HEADING_ID = "finding-history-revisions-heading";
/** The v69 `finding-history` screen question (W1-UX-02). */
export const FINDING_HISTORY_QUESTION = "How did the conclusion and workflow change?";

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
    <div
      className="site-finding site-finding-history"
      data-finding-history={body.finding.id}
      data-finding-revision={body.selection.revision_id}
      data-history-selected-by={body.selection.selected_by}
      data-history-total={body.page.total}
      data-history-loaded={rows.length}
    >
      <RevisionHistory body={body} rows={rows} read={read} links={links} />
    </div>
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
    <div className="site-finding site-finding-history" data-finding-history-refused={read.status}>
      <Panel heading="Revision history" headingId={HEADING_ID} description={FINDING_HISTORY_QUESTION}>
        <ProductStatus
          words={findingRefusalWords(read.status)}
          scope={pinned ? "This Finding's history, at the version in the address" : "This Finding's history"}
          asOf={null}
        />
        <div className="site-finding-history__gap" data-history-gap>
          <p>
            <strong>{chosen.heading}.</strong> <span data-finding-read={read.status}>{chosen.text}</span>
          </p>
          {read.message ? <p className="site-finding__note">Reason given: {read.message}</p> : null}
          {read.status === "not_found" && pinned ? (
            <p>
              <Link to={latestHref} data-history-open-latest>
                Open the history at the latest version instead
              </Link>
            </p>
          ) : null}
        </div>
      </Panel>
    </div>
  );
}

/** How the version was selected, in the shared product words (this read carries no currentness of its own). */
function selectionWords(body: FindingHistoryBody) {
  if (body.audit_only) return findingCurrentnessWords("SOURCE_CLOSED");
  if (!body.selection.is_latest) return findingCurrentnessWords("SUPERSEDED_BY_LATER_REVISION");
  return findingCurrentnessWords(body.selection.selected_by === "LATEST_RECORDED" ? "LATEST_AT_READ" : "LATEST_PINNED");
}

/** W1-F3 review M4: the latest-version label once; the scope carries "Version N of M", so the sentence only says where currentness lives. */
function lineWords(body: FindingHistoryBody) {
  const words = selectionWords(body);
  if (body.audit_only || !body.selection.is_latest) return words;
  return { ...words, sentence: "Whether it is up to date is shown on the Finding's own page." };
}

function historyHeadline(body: FindingHistoryBody, rows: HistoryRevision[], read: Extract<HistoryRead, { status: "loaded" }>): string {
  const total = body.page.total;
  if (!(read.complete && rows.length === total)) {
    return `Only ${rows.length} of ${total} recorded versions could be read`;
  }
  const latest = LIFECYCLE_WORDS[body.state.lifecycle]?.label ?? "a state this page cannot name";
  return total === 1
    ? `One recorded version so far; it records: ${latest}`
    : `${total} recorded versions; the latest records: ${latest}`;
}

/** Merge, split and recurrence links, as recorded; each opens that Finding's own history. */
function relatedItems(body: FindingHistoryBody): { label: string; id: string }[] {
  const r = body.relations;
  return [
    ...r.merged_into.map((m) => ({ label: "Joined into", id: m.canonical_finding_id })),
    ...r.merged_from.map((m) => ({ label: "Joined from", id: m.superseded_finding_id })),
    ...(r.split_from_finding_id ? [{ label: "Split from", id: r.split_from_finding_id }] : []),
    ...r.split_parts.map((id) => ({ label: "Split part", id })),
    ...(r.recurs_after_finding_id ? [{ label: "Recurs after", id: r.recurs_after_finding_id }] : []),
    ...r.recurred_by.map((id) => ({ label: "Recurred as", id })),
  ].filter((item) => item.id && item.id !== body.finding.id);
}

/**
 * W1-F3 (`D-2026-10-17-mockup-layout-spec`, mock `finding-history:1`): the one
 * panel "Revision history". Inside it: the selection's state line with its
 * non-current notes, one summary line (count and latest state; "No earlier
 * versions." for one version; incomplete or changed-while-read), the mock's
 * Time / Event / Basis table with one row per recorded version, related
 * Findings as one line, the kept-as-recorded note, and the exact references
 * last. The way to the selected version and its evidence is the panel-head link.
 */
function RevisionHistory({
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
  const { selection, state } = body;
  const no = selection.revision_no;
  const total = body.page.total;
  const latestState = LIFECYCLE_WORDS[state.lifecycle];
  const selectedRow = rows.find((r) => r.id === selection.revision_id) ?? null;
  const cutoff = body.page.next_after_revision_no;
  const complete = read.complete && rows.length === total;
  const groupOf = new Map<string, { count: number; first: number; last: number }>();
  for (const group of body.revision_groups) {
    if (group.kind === "BASIS_REFRESHED" && group.count > 1) {
      for (const id of group.revision_ids) {
        groupOf.set(id, { count: group.count, first: group.first_revision_no, last: group.last_revision_no });
      }
    }
  }
  const recordedAt = new Map(rows.map((r) => [r.id, r.times.recorded_at]));
  const related = relatedItems(body);
  // W1-F3 height phase: the mock shows the latest few versions; the earlier ones stay in the
  // document, oldest first, behind one "Show all N" expander placed above them.
  const latest = rows.slice(-LATEST_SHOWN);
  const earlier = rows.slice(0, rows.length - latest.length);
  const versionHead = (
    <thead>
      <tr>
        <th scope="col">Version recorded</th>
        <th scope="col">Event</th>
        <th scope="col">Basis</th>
      </tr>
    </thead>
  );
  const versionRow = (r: HistoryRevision) => (
    <VersionRow
      key={r.id}
      r={r}
      group={groupOf.get(r.id)}
      previousRecordedAt={r.previous_revision_id ? recordedAt.get(r.previous_revision_id) ?? null : null}
      links={links}
    />
  );
  return (
    <Panel
      heading="Revision history"
      headingId={HEADING_ID}
      description={FINDING_HISTORY_QUESTION}
      actions={
        <>
          {/* W1-F3 review (height table): one head link; the selected row carries "Its evidence". */}
          <Link to={links.finding(body.finding.id, selection.revision_id)} data-history-open-finding>
            Open version {no} of the Finding
          </Link>
        </>
      }
    >
      <p className="v69-state-line" data-history-state-line>
        <ProductStatus
          inline
          words={lineWords(body)}
          scope={
            !selection.is_latest ? (
              `Version ${no} of ${total} selected`
            ) : selection.selected_by === "LATEST_RECORDED" ? (
              <span data-history-latest-at-read>
                Version {no} of {total}
              </span>
            ) : (
              <span data-history-pinned-latest>
                Version {no} of {total}
              </span>
            )
          }
          asOf={selectedRow?.times.recorded_at ?? null}
        >
          {body.audit_only ? (
            <span className="site-finding__lead" data-history-audit-only>
              {" "}
              Record only. This site&apos;s assessments are not released for use, so these saved versions are shown as
              a record, not as the current Finding.
            </span>
          ) : null}
          {latestState === undefined || state.lifecycle === "SUPPORTED" ? null : (
            <span className="site-finding__lead" data-history-lifecycle={state.lifecycle}>
              {" "}
              State recorded by the latest version: <strong>{latestState.label}</strong>. {latestState.sentence}
            </span>
          )}
          {!selection.is_latest ? (
            <span className="site-finding__lead" data-history-earlier-version>
              {" "}
              Version {no} is selected. It is an earlier version: version {selection.latest_revision_no} replaces it.{" "}
              <Link to={links.history(selection.latest_revision_id)} data-history-select-latest>
                Select the latest version
              </Link>
            </span>
          ) : selection.selected_by === "LATEST_RECORDED" ? (
            <span>
              {" "}
              <Link to={links.history(selection.revision_id)} data-history-pin>
                Keep this exact version
              </Link>
            </span>
          ) : null}
        </ProductStatus>
      </p>
      <p className="site-finding-history__summary">
        {/* W1-F3 review M4: a complete list says its count once, in the headline; only an incomplete list adds a line. */}
        <strong data-history-summary data-history-complete={complete ? "" : undefined}>
          {historyHeadline(body, rows, read)}
        </strong>{" "}
        {body.earlier_versions === "NONE" ? (
          <span data-history-no-earlier>No earlier versions. This Finding has one recorded version.</span>
        ) : null}
        {complete ? null : (
          <span className="site-finding__lead" data-history-incomplete>
            Only {rows.length} of {total} recorded versions could be read, so this list is incomplete. Reload to read
            the rest.
          </span>
        )}
        {read.drift ? (
          <span className="site-finding__lead" data-history-drift>
            {" "}
            A new version was recorded while this list was being read. Reload to see the list as it is now.
          </span>
        ) : null}
      </p>
      {earlier.length === 0 ? null : (
        <ShowAll
          name="finding-history-versions"
          summary={`Show all ${rows.length} versions (${earlier.length} earlier)`}
          defaultOpen={earlier.some((r) => r.is_selected)}
        >
          <DataTable labelledBy={HEADING_ID}>
            {versionHead}
            <tbody>{earlier.map(versionRow)}</tbody>
          </DataTable>
        </ShowAll>
      )}
      <DataTable labelledBy={HEADING_ID}>
        {versionHead}
        <tbody>{latest.map(versionRow)}</tbody>
      </DataTable>
      {related.length === 0 ? null : (
        <p className="site-finding-history__related" data-history-related-line>
          Related Findings:{" "}
          {related.map((item, index) => (
            <span key={`${item.label}-${item.id}`}>
              {index > 0 ? " · " : ""}
              <Link to={links.otherHistory(item.id)} data-history-related={item.id}>
                {item.label} Finding <code data-vocabulary-exempt="source-reference">{item.id.slice(0, 8)}</code> - its
                history
              </Link>
            </span>
          ))}
        </p>
      )}
      <p className="v69-gap-line" data-history-kept-as-recorded>
        Versions are kept as recorded; a later reading adds a version and never changes one. The times describe each
        version; they are not a way to view the Finding as of an earlier moment.
      </p>
      <ExactReferences
        name="finding-history-references"
        references={[
          { label: "Finding reference", value: body.finding.id },
          { label: "Selected version reference", value: selection.revision_id },
          { label: "Latest version reference", value: selection.latest_revision_id },
          { label: "How the version was chosen", value: selection.selected_by },
          ...(cutoff === null ? [] : [{ label: "First page ends after version", value: String(cutoff) }]),
        ]}
      />
    </Panel>
  );
}

/** One recorded version as a Time / Event / Basis row (mock `finding-history:1`). */
function VersionRow({
  r,
  group,
  previousRecordedAt,
  links,
}: {
  r: HistoryRevision;
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
    <tr
      className="site-finding-history__version"
      data-history-revision={r.id}
      data-history-revision-no={r.revision_no}
      data-history-selected={r.is_selected ? "true" : undefined}
      data-history-latest={r.is_latest ? "true" : undefined}
      aria-current={r.is_selected ? "true" : undefined}
    >
      <td>{stamp(r.times.recorded_at)}</td>
      <td>
        <strong>
          Version {r.revision_no} · {transitionWords(r.transition)}
        </strong>
        {r.is_selected ? <span data-history-selected-mark> · Selected</span> : null}
        {r.is_latest ? <span data-history-latest-mark> · Latest</span> : null}
        <small className="site-finding-history__line">
          State: {state?.label ?? r.lifecycle}
          {" · "}
          <Link to={links.history(r.id)} data-history-select={r.id} aria-current={r.is_selected ? "true" : undefined}>
            Select version {r.revision_no}
          </Link>
          {" · "}
          <Link to={links.evidence(r.id)} data-history-evidence-link={r.id}>
            Its evidence
          </Link>
        </small>
        {group ? (
          <small className="site-finding-history__line" data-history-group>
            One of {group.count} assessment updates with the amount unchanged (versions {group.first}–{group.last}); each
            stays its own version.
          </small>
        ) : null}
        {lateEvidence ? (
          <small className="site-finding-history__line" data-history-late-evidence>
            Cites readings accepted after version {r.revision_no - 1} was recorded. Version {r.revision_no - 1} keeps the
            records it cited.
          </small>
        ) : null}
      </td>
      <td>
        <p className="site-finding-history__basis-line" data-history-basis-line>
          {minuteText(r.minutes.candidate)} possibly avoidable; {minuteText(r.minutes.indeterminate)} undecided
        </p>
        <div className="site-finding-history__basis-line">
          <span>
            <span data-history-cited={cited.count} data-history-accepted-rows={cited.accepted_rows}>
              {cited.count} cited; {cited.resolved} of {cited.count} found as accepted records
            </span>
            {cited.accepted_rows === "UNRESOLVED_PRESENT" ? (
              <span data-history-unresolved> ({cited.count - cited.resolved} could not be found)</span>
            ) : null}
            .
          </span>
          {" · "}
        <Disclosure variant="inline" name={`finding-history-basis-${r.revision_no}`} summary="Times and references">
        <dl className="site-finding-history__basis">
          <div>
            <dt>Period</dt>
            <dd>
              {stamp(r.episode.start)} to {stamp(r.episode.end)}
            </dd>
          </div>
          <div>
            <dt>Possibly avoidable time</dt>
            <dd>{minuteText(r.minutes.candidate)}</dd>
          </div>
          <div>
            <dt>Generator time needed</dt>
            <dd>{minuteText(r.minutes.necessary)}</dd>
          </div>
          <div>
            <dt>Time that could not be decided</dt>
            <dd>{minuteText(r.minutes.indeterminate)}</dd>
          </div>
          <div>
            <dt>Amount changed from the previous version</dt>
            <dd>{r.revision_no === 1 ? "First version" : r.support_changed ? "Yes" : "No"}</dd>
          </div>
          <div>
            <dt>Readings from</dt>
            <dd>
              {stamp(r.times.source_time.first)} to {stamp(r.times.source_time.last)}
            </dd>
          </div>
          <div>
            <dt>Last cited reading received</dt>
            <dd>{stamp(r.times.received_at)}</dd>
          </div>
          <div>
            <dt>Last cited reading accepted</dt>
            <dd>{stamp(r.times.accepted_at)}</dd>
          </div>
          <div>
            <dt>Analysis finished</dt>
            <dd>{stamp(r.times.analytic_completed_at)}</dd>
          </div>
          <div>
            <dt>Assessment rules reference</dt>
            <dd>
              <code data-vocabulary-exempt="source-reference">{r.model_version}</code>
            </dd>
          </div>
          <div>
            <dt>Assessment behind it</dt>
            <dd>
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
            </dd>
          </div>
        </dl>
        </Disclosure>
        </div>
      </td>
    </tr>
  );
}
