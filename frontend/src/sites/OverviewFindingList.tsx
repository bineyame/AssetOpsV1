/**
 * S5-02 (`mini:3#a/b`, `I-overview-finding-list-ui`): the imported Site Overview's Finding list for the selected
 * UTC day, read from the S4-04 Site Finding index (`GET /api/sites/{site}/finding-index`).
 *
 * The index is its own fenced read. Its scope is the Overview's served day (`window.start`/`window.end`), never the
 * browser clock; the preview is the first page at a small fixed limit and links to the full Site Findings page for
 * the identical window. Only a `CURRENT`, `is_current` read with a count can list rows or say "no Findings"; every
 * other state names itself and gives no count.
 *
 * Parity with the Overview's own Finding card follows `D-2026-10-16-s502-parity`: the first row is said to be the
 * same Finding version only when both reads are current on the same comparable basis for this exact day, the card
 * was freshly discovered under an open source, and both IDs are equal. Otherwise both bases are shown with a reload,
 * and no equality is claimed. Index rows are never hidden or replaced because of a parity outcome.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  currentnessWords,
  Disclosure,
  ExactReferences,
  ProductStatus,
  readResultWords,
  type ExactReference,
  type ProductWords,
} from "../ui";
import type { SiteWindowSummary } from "./siteOverviewClient";
import {
  FINDING_INDEX_DOMAIN,
  type FindingIndexBody,
  type FindingIndexClient,
  type FindingIndexResult,
  type FindingIndexScope,
} from "./findingIndexClient";
import { utcText } from "./SiteFindingIndex";
import { LIFECYCLE_WORDS } from "./findingWords";
import type { Lifecycle } from "./findingClient";

/** The preview's fixed page size (plan review L3): small enough that a busy day shows the first-page-only state. */
export const OVERVIEW_FINDING_PREVIEW_LIMIT = 2;

export interface OverviewFindingListLinks {
  /** The Finding page at one exact Finding version. */
  finding: (findingId: string, revisionId: string) => string;
  /** The full Site Findings page for one index scope. */
  findingList: (scope: FindingIndexScope) => string;
}

export interface OverviewFindingListProps {
  summary: SiteWindowSummary;
  client: FindingIndexClient;
  links: OverviewFindingListLinks;
  /** Read the Overview (and so this list) again. */
  onReload: () => void;
}

export type ParityOutcome =
  | { state: "same" }
  | { state: "different"; reasons: string[] }
  | { state: "not-compared"; reasons: string[] };

function intersects(start: string | null, end: string | null, from: string, to: string): boolean {
  if (start === null) return false;
  const s = Date.parse(start);
  const e = end === null ? Number.POSITIVE_INFINITY : Date.parse(end);
  return s < Date.parse(to) && e > Date.parse(from);
}

const present = (v: unknown) => v !== null && v !== undefined && v !== "";

/** `D-2026-10-16-s502-parity`: compare the Overview card with the index's first row, only on a shared basis. */
export function compareParity(summary: SiteWindowSummary, body: FindingIndexBody): ParityOutcome {
  const reasons: string[] = [];
  const k = summary.known_finding;
  const first = body.rows[0];
  if (body.status !== "CURRENT" || !body.is_current || first === undefined) {
    return { state: "not-compared", reasons: ["The list is not current or has no first row."] };
  }
  if (k === null) return { state: "not-compared", reasons: ["The Overview selected no Finding for this day."] };
  if (summary.freshness.state !== "CURRENT") {
    reasons.push("The Overview itself is not current, so its Finding choice cannot be compared.");
  }
  if (k.selected_by !== "DISCOVERED" || !summary.freshness.source_open || k.audit_only) {
    reasons.push("The Overview's Finding is a kept address pin or audit material, not a fresh choice.");
  }
  const { start, end, utc_date: day } = summary.window;
  if (!intersects(k.episode.start, k.episode.end, start, end)) reasons.push("The Overview's Finding does not overlap this day.");
  if (!intersects(first.episode.start, first.episode.end, start, end)) reasons.push("The list's first Finding does not overlap this day.");
  if (body.site_code !== summary.site_code || body.site_id !== summary.site_id) reasons.push("The two reads name different Sites.");
  if (Date.parse(body.window.from) !== Date.parse(start) || Date.parse(body.window.to) !== Date.parse(end)) {
    reasons.push("The two reads cover different windows.");
  }
  const w = body.watermarks.days.find((d) => d.day === day);
  const m = body.watermarks.matcher;
  if (w === undefined) {
    reasons.push("The list has no basis for this day.");
  } else {
    if (w.status !== "CURRENT" || !w.s4.matched) reasons.push("The list does not report this day as assessed and matched.");
    const pairs: [string, unknown, unknown][] = [
      ["assessment selection", w.s3.selection_seq, summary.watermarks.analytic_selection_seq],
      ["assessment pass", w.s3.run_id, summary.assessment.run_id],
      ["assessment record", w.s3.window_assessment_revision_id, summary.assessment.window_assessment_revision_id],
      ["assessment method", w.s3.model_version, summary.model_version],
      ["input reference", w.s3.input_sha256, summary.watermarks.input_sha256],
      ["configuration reference", w.s3.configuration_sha256, summary.watermarks.configuration_sha256],
      ["matching pass", m?.match_pass_id, summary.watermarks.match_pass_id],
      ["matched through", m?.matched_through_selection_seq, summary.watermarks.matched_through_selection_seq],
    ];
    for (const [name, a, b] of pairs) {
      if (!present(a) || !present(b)) reasons.push(`The ${name} is not recorded by both reads.`);
      else if (String(a) !== String(b)) reasons.push(`The ${name} differs between the two reads.`);
    }
  }
  if (reasons.length > 0) return { state: "not-compared", reasons };
  if (first.finding_id !== k.id || first.finding_revision_id !== k.revision_id) {
    return {
      state: "different",
      reasons: ["On the same basis, the list's first Finding version is not the one chosen above."],
    };
  }
  return { state: "same" };
}

/**
 * W1-UX-02: the exact values behind the Overview's own Finding choice, for the parity disclosure's references.
 * Labelled one value at a time; the plain reasons stay in the "Why they are not compared" list.
 */
function overviewBasisReferences(summary: SiteWindowSummary): ExactReference[] {
  const w = summary.watermarks;
  const text = (v: unknown) => (v === null || v === undefined || v === "" ? null : String(v));
  return [
    { label: "Overview day assessment reference", value: summary.assessment.window_assessment_revision_id },
    { label: "Overview assessment selection number", value: text(w.analytic_selection_seq) },
    { label: "Overview Finding match reference", value: w.match_pass_id },
    { label: "Overview matched through selection number", value: text(w.matched_through_selection_seq) },
    { label: "How the Overview chose its Finding", value: summary.known_finding?.selected_by ?? null },
  ];
}

/** S5-02 parity (`D-2026-10-16-s502-parity`): a same claim only on a shared, current, comparable basis. */
function Parity({ summary, body, onReload }: { summary: SiteWindowSummary; body: FindingIndexBody; onReload: () => void }) {
  const outcome = compareParity(summary, body);
  if (outcome.state === "same") {
    return (
      <p className="v69-chart-note" data-overview-finding-parity="same">
        The first Finding listed is the same Finding version as the one chosen above, on the same assessment and
        matching basis for this day.
      </p>
    );
  }
  return (
    <div data-overview-finding-parity={outcome.state}>
      <p>
        {outcome.state === "different"
          ? "The first Finding listed is not the one chosen above, although both reads report the same basis."
          : "This list and the Finding chosen above come from separate reads that cannot be compared right now."}{" "}
        They are not said to be the same.{" "}
        <button type="button" onClick={onReload} data-overview-finding-reload>
          Reload both
        </button>
      </p>
      <Disclosure name="overview-finding-parity" summary="Why they are not compared">
        <ul>
          {outcome.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
        <p>The exact values behind both choices are listed under How this was worked out.</p>
      </Disclosure>
    </div>
  );
}

function FullList({ href }: { href: string }) {
  return (
    <p>
      <Link to={href} data-overview-finding-full-list>
        Open the full Findings list for this day
      </Link>
    </p>
  );
}

/** The list's plain scope, used by every state line in it. */
function listScope(summary: SiteWindowSummary): string {
  return `Findings overlapping ${summary.window.utc_date}`;
}

/** A CURRENT status that is not `is_current`, or has no count: never a positive claim. */
const NOT_CONFIRMED_WORDS: ProductWords = {
  label: "Not confirmed as current yet",
  sentence: "This list is not confirmed as current for this day, so no Findings are listed and no count is given.",
  next: "Look again after the day has been checked.",
  tone: "waiting",
  code: "CURRENT",
  unrecognised: false,
};

const INCOMPLETE_WORDS: ProductWords = {
  label: "List incomplete",
  sentence: "The Findings list for this day is incomplete, so nothing is said about it.",
  next: "Reload both reads.",
  tone: "limited",
  code: null,
  unrecognised: false,
};

/** The non-current list states in the shared words; CURRENT without a confirmed count is never positive. */
function listWords(body: FindingIndexBody): ProductWords {
  if (body.status === "CURRENT") return NOT_CONFIRMED_WORDS;
  return currentnessWords(body.status);
}

/**
 * W1-UX-02: the list's exact references - the list selection reference, its recorded reasons, each listed row's
 * exact version, and (when parity is not claimed) the Overview's own basis. Labelled one value at a time.
 */
function ListReferences({ summary, body, withBasis }: { summary: SiteWindowSummary; body: FindingIndexBody; withBasis: boolean }) {
  return (
    <div data-finding-index-reasons>
      <ExactReferences
        name="overview-finding-list"
        variant="tech"
        references={[
          { label: "List state", value: body.status },
          ...body.status_reasons.map((reason, i) => ({ label: `Recorded reason ${i + 1}`, value: reason })),
          { label: "List selection reference", value: body.selection_token },
          { label: "List built at", value: body.built_at },
          ...body.rows.flatMap((row, i) => [
            { label: `Listed Finding ${i + 1} reference`, value: row.finding_id },
            { label: `Listed Finding ${i + 1} version reference`, value: row.finding_revision_id },
          ]),
          ...(withBasis ? overviewBasisReferences(summary) : []),
        ]}
      />
    </div>
  );
}

function Loaded({ summary, body, scope, links, onReload }: { summary: SiteWindowSummary; body: FindingIndexBody; scope: FindingIndexScope; links: OverviewFindingListLinks; onReload: () => void }) {
  const full = links.findingList({ ...scope, limit: null, cursor: null });
  if (body.status !== "CURRENT" || !body.is_current || body.total_count === null) {
    return (
      <div data-overview-finding-list={body.status}>
        <ProductStatus words={listWords(body)} scope={listScope(summary)} asOf={body.knowledge_at} />
        <p>No Findings are listed and no count is given. This is not a statement that the day has no Findings.</p>
        <FullList href={full} />
        <ListReferences summary={summary} body={body} withBasis={false} />
      </div>
    );
  }
  if (body.total_count === 0) {
    if (body.rows.length > 0 || !body.selection_token || body.watermarks.days.length === 0) {
      return (
        <div data-overview-finding-list="unavailable">
          <ProductStatus words={INCOMPLETE_WORDS} scope={listScope(summary)} asOf={body.knowledge_at} />
        </div>
      );
    }
    return (
      <div data-overview-finding-list="current-empty">
        <ProductStatus words={readResultWords("proved-empty")} scope={listScope(summary)} asOf={body.knowledge_at} />
        <p>
          <strong>No Findings for this day.</strong> Every day this read inspected (
          {body.discovery.days.join(", ")}) was assessed and matched for Findings through its latest selection, and
          no Finding overlaps {summary.window.utc_date}.
        </p>
        <FullList href={full} />
        <ListReferences summary={summary} body={body} withBasis={false} />
      </div>
    );
  }
  const shown = body.rows.length;
  if (shown === 0) {
    return (
      <div data-overview-finding-list="unavailable">
        <ProductStatus words={INCOMPLETE_WORDS} scope={listScope(summary)} asOf={body.knowledge_at} />
        <p>
          <button type="button" onClick={onReload} data-overview-finding-reload>
            Reload both
          </button>
        </p>
      </div>
    );
  }
  const partial = body.next_cursor !== null || shown < body.total_count;
  const parity = compareParity(summary, body);
  return (
    <div data-overview-finding-list="current-rows">
      {/* W1-F2 compaction: the list's state line in the strip's inline form (same words and bound). */}
      <p className="v69-chart-note overview-finding-list__state">
        <ProductStatus inline words={currentnessWords("CURRENT")} scope={listScope(summary)} asOf={body.knowledge_at} />
      </p>
      <p>
        <strong>
          {body.total_count} {body.total_count === 1 ? "Finding" : "Findings"} overlap this day.
        </strong>{" "}
        Newest period first; each opens at the exact version listed.
      </p>
      <ol className="overview-finding-list" data-overview-finding-rows>
        {body.rows.map((row) => (
          <li key={row.finding_id} data-overview-finding-row={row.finding_id} data-finding-revision={row.finding_revision_id}>
            <Link to={links.finding(row.finding_id, row.finding_revision_id)} data-overview-finding-link>
              {LIFECYCLE_WORDS[row.lifecycle as Lifecycle]?.title ?? "Generator support review"}
            </Link>{" "}
            <small>
              {utcText(row.episode.start)} to {utcText(row.episode.end)} ·{" "}
              {LIFECYCLE_WORDS[row.lifecycle as Lifecycle]?.label ?? "Status not recognised"} · version {row.revision_no}
            </small>
          </li>
        ))}
      </ol>
      {/* W1-F2 compaction: the shown count and the full-list link share one note line. */}
      <p className="v69-chart-note">
        <span data-overview-finding-shown={partial ? "first-page" : "all"}>
          {partial
            ? `Showing the first ${shown} of ${body.total_count}. This is not the whole list.`
            : `Showing all ${shown}.`}
        </span>{" "}
        <Link to={full} data-overview-finding-full-list>
          Open the full Findings list for this day
        </Link>
      </p>
      <Parity summary={summary} body={body} onReload={onReload} />
      <ListReferences summary={summary} body={body} withBasis={parity.state !== "same"} />
    </div>
  );
}

const REFUSAL_WORDS: Record<string, string> = {
  closed: "The Findings list is closed for this Site because its assessments are not released.",
  continuity_limit: "The Findings list could not be built for this day within its search limit.",
  basis_changed: "The Findings list changed while it was being read.",
  invalid: "This day cannot be read as a Findings window.",
  unauthenticated: "Sign in to see this Site's Findings.",
  forbidden: "You do not have access to this Site's Findings.",
  not_imported: "This Site has no imported Findings list.",
  unavailable: "The Findings list could not be read.",
};

/** A refused or failed read: access refusals and an unreadable list use the shared words; the rest are not known. */
function refusalWords(status: string): ProductWords {
  if (status === "unauthenticated" || status === "forbidden") return readResultWords("refused");
  if (status === "unavailable") return readResultWords("unavailable");
  return {
    label: "Not known",
    sentence: REFUSAL_WORDS[status] ?? REFUSAL_WORDS.unavailable,
    tone: "limited",
    code: status,
    unrecognised: !Object.prototype.hasOwnProperty.call(REFUSAL_WORDS, status),
  };
}

function Refused({ result, href, summary }: { result: Exclude<FindingIndexResult, { status: "loaded" }>; href: string; summary: SiteWindowSummary }) {
  return (
    <div data-overview-finding-list={result.status}>
      <ProductStatus words={refusalWords(result.status)} scope={listScope(summary)} asOf={null}>
        <p className="product-status__note" data-overview-finding-refusal>
          {REFUSAL_WORDS[result.status] ?? REFUSAL_WORDS.unavailable}
          {result.message ? ` ${result.message}` : ""}
        </p>
      </ProductStatus>
      <p>No Findings are listed and no count is given. This is not a statement that the day has no Findings.</p>
      <FullList href={href} />
    </div>
  );
}

export function OverviewFindingList({ summary, client, links, onReload }: OverviewFindingListProps) {
  const site = summary.site_code;
  const { start: from, end: to } = summary.window;
  const [read, setRead] = useState<{ key: string; result: FindingIndexResult } | null>(null);
  const key = `${site}|${from}|${to}`;
  const scope: FindingIndexScope = { domain: FINDING_INDEX_DOMAIN, from, to, limit: OVERVIEW_FINDING_PREVIEW_LIMIT, cursor: null };
  useEffect(() => {
    let active = true;
    setRead(null);
    void client
      .getFindingIndex(site, { domain: FINDING_INDEX_DOMAIN, from, to, limit: OVERVIEW_FINDING_PREVIEW_LIMIT, cursor: null })
      .then((result) => {
        // An older day's answer arriving after a date change is dropped (packet "Request").
        if (active) setRead({ key: `${site}|${from}|${to}`, result });
      });
    return () => {
      active = false;
    };
  }, [client, site, from, to]);
  return (
    <section aria-labelledby="overview-finding-list-heading" data-overview-finding-list-for={summary.window.utc_date}>
      <h3 id="overview-finding-list-heading">Findings for {summary.window.utc_date}</h3>
      {read === null || read.key !== key ? (
        <p data-overview-finding-list="loading">Loading the findings for this day.</p>
      ) : read.result.status === "loaded" ? (
        <Loaded summary={summary} body={read.result.value} scope={scope} links={links} onReload={onReload} />
      ) : (
        <Refused result={read.result} href={links.findingList({ ...scope, limit: null })} summary={summary} />
      )}
    </section>
  );
}
