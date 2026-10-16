/**
 * S4-03 phase 2 (`I-finding-evidence-ui`): the Evidence child view of one
 * durable Finding (mock `finding-evidence:1,2`), at
 * `/sites/{site}/findings/{finding}/evidence[?revision_id=&offset=&record=]`.
 *
 * Reads `GET /api/sites/{site}/findings/{id}/evidence`. The bundle is the
 * selected version's cited accepted records, paged to the full set with its
 * total; the analysis input set is counted separately and never shown as the
 * bundle. Every cited ID is lineage-checked by the read; a link that does not
 * resolve is named in plain words and its positive claim is withheld. The
 * exact version, page and selected record stay in the address, so a reload
 * reopens the same view. An omitted version is the latest at read time and is
 * labelled so; an unknown or foreign version is refused, never replaced.
 */
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { DataTable, Fact, FactList, MissingClaim, Panel } from "../ui";
import { durationText, minutes, qualityWords, roleWords, stamp } from "./dispatchWords";
import type {
  EvidenceAssessment,
  EvidenceRecord,
  FindingClient,
  FindingEvidenceBody,
  FindingReadResult,
  FindingWindowBody,
} from "./findingClient";
import { dayOf, LIFECYCLE_WORDS, sourceModeWords } from "./findingWords";
import { SourceProvenanceNotice } from "./sourceProvenance";

export const FINDING_SECTIONS_LABEL = "Finding sections";
export const EVIDENCE_PAGE_SIZE = 50;

export interface FindingSectionLink {
  id: string;
  label: string;
  href: string;
}

/**
 * The Finding root's sections (the Finding itself and its named child views).
 * Each link keeps the exact selected version; the frame builds the hrefs.
 */
export function FindingSections({ sections, current }: { sections: FindingSectionLink[]; current: string }) {
  return (
    <nav className="site-tabs site-subtabs" aria-label={FINDING_SECTIONS_LABEL}>
      <ol className="site-tabs__list">
        {sections.map((section) => (
          <li className="site-tabs__item" key={section.id}>
            <Link
              className="site-tabs__link"
              to={section.href}
              data-finding-section={section.id}
              aria-current={section.id === current ? "page" : undefined}
            >
              {section.label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}

/**
 * Plain words for each lineage link the read names (`finding_read.BROKEN_WORDS`
 * keys; a test holds the two key sets and wordings equal). A link name this
 * list does not know is never shown as engineering text: it reads "A record
 * link could not be checked" with the code only as technical detail.
 */
export const LINK_WORDS: Record<string, string> = {
  ACCEPTED_EVIDENCE: "no accepted record with this reference exists for this site",
  BATCH: "the delivery batch it arrived in cannot be found",
  ACCEPTANCE_DISPOSITION: "no acceptance decision for this record can be found",
  ENVELOPE: "the stored original message is missing",
  ENVELOPE_DIGEST: "the stored original message does not match its saved fingerprint",
  FOUNDATION_REVISION: "the site setup version it was accepted under cannot be found",
  BINDING_SET_REVISION: "the device links version it was accepted under cannot be found",
  BINDING_REVISION: "the device link it was accepted under cannot be found",
  ASSESSMENT_CITATION: "no assessment behind this version lists this record",
  RUN_INPUT: "this record is not among the records the analysis read",
  ANALYTIC_RUN: "the analysis behind an assessment cannot be found",
  CITED_SET_DIGEST: "the cited records do not match the fingerprint saved with this version",
};

const WITHHELD = "No accepted record with this reference exists for this site, so no measurement, source or message is shown.";

export const UNKNOWN_LINK_WORDS = "A record link could not be checked";

/** One lineage link in plain words; an unknown code is named only as technical detail. */
function LinkText({ link }: { link: string }) {
  const known = LINK_WORDS[link];
  if (known !== undefined) {
    return <>{known}</>;
  }
  return (
    <span data-evidence-unknown-link={link}>
      {UNKNOWN_LINK_WORDS}{" "}
      <span className="site-finding__note" data-evidence-technical-detail>
        (technical detail: <code data-vocabulary-exempt="source-reference">{link}</code>)
      </span>
    </span>
  );
}

function LinkList({ links }: { links: string[] }) {
  return (
    <>
      {links.map((link, index) => (
        <span key={link}>
          {index > 0 ? "; " : ""}
          <LinkText link={link} />
        </span>
      ))}
    </>
  );
}

export interface SiteFindingEvidenceLinks {
  /** This Finding's Evidence view at an exact version (null: latest at read time). */
  evidence: (revisionId: string | null) => string;
  /** This or another Finding of the Site, optionally at an exact version. */
  finding: (findingId: string, revisionId?: string | null) => string;
  /** The Site's Performance > Dispatch at one UTC day, optionally one assessed period. */
  dispatch: (day: string, intervalRevisionId?: string | null) => string;
  /** The Site Evidence record inspector for one exact accepted evidence ID. */
  record: (evidenceId: string) => string;
  /** This Finding's History, with the same exact version selected. */
  history?: (revisionId: string | null) => string;
}

function pageOffset(params: URLSearchParams): number {
  const raw = params.get("offset");
  const value = raw === null ? 0 : Number(raw);
  return Number.isInteger(value) && value >= 0 ? value : 0;
}

export function SiteFindingEvidence({
  siteId,
  findingId,
  client,
  links,
}: {
  siteId: string;
  findingId: string;
  client: FindingClient;
  links: SiteFindingEvidenceLinks;
}) {
  const [params] = useSearchParams();
  const revisionId = params.get("revision_id");
  const offset = pageOffset(params);
  const selectedRecord = params.get("record");
  const [read, setRead] = useState<FindingReadResult<FindingEvidenceBody> | null>(null);

  useEffect(() => {
    let active = true;
    setRead(null);
    void client.getFindingEvidence(siteId, findingId, revisionId, offset, EVIDENCE_PAGE_SIZE).then((loaded) => {
      if (active) {
        setRead(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId, findingId, revisionId, offset]);

  if (read === null) {
    return <p>Loading the Finding&apos;s evidence.</p>;
  }
  if (read.status !== "loaded") {
    return <Refused read={read} pinned={revisionId !== null} latestHref={links.evidence(null)} />;
  }
  const body = read.value;
  const search = (changes: Record<string, string | null>) => {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null) {
        next.delete(key);
      } else {
        next.set(key, value);
      }
    }
    const text = next.toString();
    return text === "" ? "?" : `?${text}`;
  };
  return (
    <section
      className="site-finding site-finding-evidence"
      aria-labelledby="finding-evidence-selection-heading"
      data-finding-evidence={body.finding.id}
      data-finding-revision={body.selection.revision_id}
      data-evidence-selected-by={body.selection.selected_by}
      data-evidence-lineage={body.lineage.status}
      data-evidence-total={body.counts.cited_total}
    >
      <Selection body={body} links={links} />
      <Lineage body={body} />
      <Bundle body={body} />
      <Assessments body={body} links={links} />
      <Records body={body} selected={selectedRecord} search={search} />
      {selectedRecord === null ? null : (
        <RecordLineage body={body} evidenceId={selectedRecord} links={links} closeSearch={search({ record: null })} />
      )}
    </section>
  );
}

function Refused({
  read,
  pinned,
  latestHref,
}: {
  read: Exclude<FindingReadResult<FindingEvidenceBody>, { status: "loaded" }>;
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
        "This site's assessments are not released for use yet, so the current Finding's evidence is not shown. " +
        "A link to an exact saved version still opens its evidence as a record.",
    },
    unavailable: {
      heading: "Evidence could not be read",
      text: "The Finding's evidence could not be read just now. Nothing here means the Finding has no evidence.",
    },
  };
  const chosen = words[read.status];
  return (
    <Panel heading={chosen.heading} headingId="finding-evidence-refused-heading">
      <p data-finding-read={read.status}>{chosen.text}</p>
      {read.message ? <p className="site-finding__note">Reason given: {read.message}</p> : null}
      {read.status === "not_found" && pinned ? (
        <p>
          <Link to={latestHref} data-evidence-open-latest>
            Open the evidence of the latest version instead
          </Link>
        </p>
      ) : null}
    </Panel>
  );
}

/**
 * Lifecycle sentences that name a place on the Finding root ("below") get a
 * page-neutral form here: the Evidence page lists no versions (review N2).
 */
const EVIDENCE_LIFECYCLE_SENTENCE: Partial<Record<string, string>> = {
  UNCONFIRMED:
    "This assessment of the period cannot confirm the earlier result. This is not a new issue; the earlier " +
    "versions stay available in this Finding's history.",
};

/** Which version is shown, and how it was chosen: non-current status first. */
function Selection({ body, links }: { body: FindingEvidenceBody; links: SiteFindingEvidenceLinks }) {
  const { selection } = body;
  const no = selection.revision_no;
  const lifecycle = LIFECYCLE_WORDS[body.revision.lifecycle];
  return (
    <Panel heading={`Evidence for version ${no}`} headingId="finding-evidence-selection-heading">
      {lifecycle === undefined || body.revision.lifecycle === "SUPPORTED" ? null : (
        <p
          className="site-finding__lead"
          data-evidence-lifecycle={body.revision.lifecycle}
        >
          State of this version: <strong>{lifecycle.label}</strong>.{" "}
          {EVIDENCE_LIFECYCLE_SENTENCE[body.revision.lifecycle] ?? lifecycle.sentence}
        </p>
      )}
      {body.audit_only ? (
        <p className="site-finding__lead" data-evidence-audit-only>
          Record only. This site&apos;s assessments are not released for use, so this saved version is shown as a record,
          not as the current Finding, and no Dispatch period is linked.
        </p>
      ) : null}
      <SourceProvenanceNotice provenance={body.source_provenance} subject="finding version" name="evidence" />
      {!selection.is_latest ? (
        <p className="site-finding__lead" data-evidence-earlier-version>
          Earlier version {no}. A later version replaces it; these are the records this earlier version cited.{" "}
          <Link to={links.evidence(selection.latest_revision_id)}>Open the latest version&apos;s evidence</Link>
        </p>
      ) : selection.selected_by === "LATEST_RECORDED" ? (
        <p data-evidence-latest-at-read>
          Latest version at the time of reading (version {no}). A version recorded later would replace it on reload.{" "}
          <Link to={links.evidence(selection.revision_id)} data-evidence-pin>
            Keep this exact version
          </Link>
        </p>
      ) : (
        <p data-evidence-pinned-latest>Version {no}, the latest recorded version, opened by its exact reference.</p>
      )}
      {lifecycle === undefined || body.revision.lifecycle !== "SUPPORTED" ? null : (
        <p
          data-evidence-lifecycle={body.revision.lifecycle}
        >
          State of this version: <strong>{lifecycle.label}</strong>. {lifecycle.sentence}
        </p>
      )}
      <p>
        <Link to={links.finding(body.finding.id, selection.revision_id)} data-evidence-back-to-finding>
          Back to this version of the Finding
        </Link>
        {links.history ? (
          <>
            {" · "}
            <Link to={links.history(selection.revision_id)} data-evidence-to-history>
              See version {no} in the Finding&apos;s history
            </Link>
          </>
        ) : null}
      </p>
    </Panel>
  );
}

/** Whole-set lineage: positive claims only when every link resolves. */
function Lineage({ body }: { body: FindingEvidenceBody }) {
  const { lineage } = body;
  if (lineage.status === "COMPLETE") {
    return (
      <Panel heading="Record trail" headingId="finding-evidence-lineage-heading">
        <p data-evidence-lineage-complete>
          Every one of the {body.counts.cited_total} cited records traces to its accepted record, delivery batch,
          stored message, the site setup it was accepted under, and the assessment that used it. The cited set
          matches the fingerprint saved with this version.
        </p>
      </Panel>
    );
  }
  return (
    <Panel heading="Some record links do not resolve" headingId="finding-evidence-lineage-heading">
      <p className="site-finding__lead" data-evidence-lineage-broken>
        Part of this version&apos;s record trail could not be followed. The broken links are named below; nothing is
        claimed for them, and no cited record is dropped or counted as zero evidence.
      </p>
      {lineage.set_breaks.length > 0 ? (
        <ul data-evidence-set-breaks>
          {lineage.set_breaks.map((b, index) => (
            <li key={index} data-evidence-set-break={b.link}>
              <LinkText link={b.link} />
              {b.assessment_revision_id ? ` (assessment ${b.assessment_revision_id.slice(0, 8)})` : ""}
            </li>
          ))}
        </ul>
      ) : null}
      {lineage.broken_records.length > 0 ? (
        <>
          <p>
            {lineage.broken_records.length} of {body.counts.cited_total} cited records have a broken link
            {body.counts.cited_unresolved > 0
              ? `; ${body.counts.cited_unresolved} do not resolve to an accepted record at all`
              : ""}
            .
          </p>
          <ul data-evidence-broken-records>
            {lineage.broken_records.map((r) => (
              <li key={r.evidence_id} data-evidence-broken-record={r.evidence_id}>
                <code data-vocabulary-exempt="source-reference">{r.evidence_id.slice(0, 8)}</code>:{" "}
                <LinkList links={r.links} />
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </Panel>
  );
}

/** Where the data came from, in plain words; the recorded mode stays in `data-source-mode`. */
function Mode({ value }: { value: string | null | undefined }) {
  return value ? <span data-source-mode={value}>{sourceModeWords(value)}</span> : <>–</>;
}

/** Cited versus input, and where the cited records came from. */
function Bundle({ body }: { body: FindingEvidenceBody }) {
  const { counts, provenance } = body;
  const notes = provenance.case_annotations;
  return (
    <Panel heading="What this version cites" headingId="finding-evidence-bundle-heading">
      <p data-evidence-cited-vs-input>
        This version cites <strong data-evidence-cited-total>{counts.cited_total}</strong> accepted records as support.
        The analysis behind it read <span data-evidence-input-total>{counts.input_distinct_total}</span> accepted records
        in all; only the cited ones are listed here.
      </p>
      <FactList>
        <Fact term="Cited records">{counts.cited_total}</Fact>
        <Fact term="Records the analysis read">{counts.input_distinct_total}</Fact>
        <Fact term="Possibly avoidable time">
          {minutes(body.revision.minutes.candidate) === null ? "–" : durationText(minutes(body.revision.minutes.candidate) ?? 0)}
        </Fact>
        <Fact term="Model">{body.revision.model_version}</Fact>
      </FactList>
      <InputsByMeasurement body={body} />
      <h3 className="site-finding__subheading" id="finding-evidence-sources">
        Where the cited records came from
      </h3>
      <DataTable labelledBy="finding-evidence-sources">
        <thead>
          <tr>
            <th scope="col">Gateway</th>
            <th scope="col">Source</th>
            <th scope="col">Sequence epoch</th>
            <th scope="col">Kind of data</th>
            <th scope="col">Records</th>
          </tr>
        </thead>
        <tbody>
          {provenance.cited_evidence_by_source.map((s) => (
            <tr key={`${s.gateway_id}/${s.source_id}/${s.sequence_epoch}`} data-evidence-source={s.sequence_epoch}>
              <td>
                <code data-vocabulary-exempt="source-reference">{s.gateway_id.slice(0, 8)}</code>
              </td>
              <td>
                <code data-vocabulary-exempt="source-reference">{s.source_id.slice(0, 8)}</code>
              </td>
              <td>{s.sequence_epoch}</td>
              <td>
                <Mode value={s.source_mode} />
              </td>
              <td>{s.count}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      {notes.length > 0 ? (
        <aside className="dispatch-demo-notes" aria-label="Demonstration data notes" data-finding-case-notes={notes.length}>
          <h3>Note supplied with the demonstration data</h3>
          <ul>
            {notes.map((note, index) => (
              <li key={index} data-case-kind={String(note.kind ?? "")}>
                {note.kind === "DEMO_MANIFEST_GATEWAY_CASE"
                  ? "Records on this page came through the site's registered gateway, the ordinary delivery path."
                  : "Records on this page are a prepared test case sent with the gateway's credential, not the ordinary delivery path."}
              </li>
            ))}
          </ul>
          <p>This note comes from the demonstration data&apos;s own description; it does not change the result.</p>
        </aside>
      ) : null}
    </Panel>
  );
}

/**
 * The mock's Input / Source / Coverage / Use summary. Input and Source are
 * counted over the whole cited set by the read (`cited_evidence_by_role`,
 * review N1), never from one page; Coverage and Use have no source, so each
 * is a catalogued missing claim.
 */
function InputsByMeasurement({ body }: { body: FindingEvidenceBody }) {
  const groups = body.provenance.cited_evidence_by_role;
  const { counts } = body;
  return (
    <>
      <h3 className="site-finding__subheading" id="finding-evidence-inputs">
        Cited records by measurement
      </h3>
      <p className="site-finding__note" data-evidence-inputs-scope>
        Counted over all {counts.cited_total} cited records of this version, not only the page shown below.
        {counts.cited_unresolved > 0
          ? ` ${counts.cited_unresolved} do not resolve to a record and are not counted by measurement.`
          : ""}
      </p>
      {groups.length === 0 ? null : (
        <DataTable labelledBy="finding-evidence-inputs">
          <thead>
            <tr>
              <th scope="col">Input</th>
              <th scope="col">Source</th>
              <th scope="col">Records</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.role} data-evidence-input-role={g.role} data-evidence-input-count={g.count}>
                <td>{roleWords(g.role)}</td>
                <td>
                  {g.source_ids.map((id, index) => (
                    <span key={id}>
                      {index > 0 ? ", " : ""}
                      <code data-vocabulary-exempt="source-reference">{id.slice(0, 8)}</code>
                    </span>
                  ))}
                </td>
                <td>{g.count}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      <MissingClaim
        as="p"
        gapId="G-finding-evidence-coverage"
        placement="finding-evidence.bundle.coverage"
        className="site-finding__note"
      >
        How completely each input was reported over the assessed period is not available yet.
      </MissingClaim>
      <MissingClaim
        as="p"
        gapId="G-finding-evidence-use"
        placement="finding-evidence.bundle.use"
        className="site-finding__note"
      >
        What each input was used for in the analysis is not available yet.
      </MissingClaim>
    </>
  );
}

/** The assessments this version cites, with their run, model and as-accepted basis. */
function Assessments({ body, links }: { body: FindingEvidenceBody; links: SiteFindingEvidenceLinks }) {
  return (
    <Panel heading="Assessments behind this version" headingId="finding-evidence-assessments-heading">
      <DataTable labelledBy="finding-evidence-assessments-heading">
        <thead>
          <tr>
            <th scope="col">Period (UTC)</th>
            <th scope="col">Kind</th>
            <th scope="col">Model</th>
            <th scope="col">Site setup used</th>
            <th scope="col">Cited records</th>
            <th scope="col">Dispatch</th>
          </tr>
        </thead>
        <tbody>
          {body.assessments.map((a) => (
            <AssessmentRow key={a.assessment_revision_id} a={a} body={body} links={links} />
          ))}
        </tbody>
      </DataTable>
      <p className="site-finding__note">
        Control settings such as the generator&apos;s minimum operating time are recorded only inside the settings fingerprint of each
        analysis; no separate control version exists.
      </p>
    </Panel>
  );
}

function AssessmentRow({ a, body, links }: { a: EvidenceAssessment; body: FindingEvidenceBody; links: SiteFindingEvidenceLinks }) {
  const day = dayOf(a.window.start);
  const dispatchable = a.assessment_revision_id in body.links.assessment_revisions;
  return (
    <tr data-evidence-assessment={a.assessment_revision_id} data-evidence-assessment-run={a.run_resolved ? "resolved" : "broken"}>
      <td>
        {stamp(a.window.start)} to {stamp(a.window.end)}
      </td>
      <td>
        {a.scope === "WINDOW" ? "Whole day" : "Period"}
        {a.is_primary ? " (primary)" : ""}
      </td>
      <td>{a.model_version}</td>
      <td>
        {a.basis === null ? (
          <span data-evidence-basis-broken>
            <LinkText link="ANALYTIC_RUN" />
          </span>
        ) : (
          <>
            Foundation{" "}
            <code data-vocabulary-exempt="source-reference">
              {a.basis.foundation_revision_ids.map((id) => id.slice(0, 8)).join(", ")}
            </code>
            , device links{" "}
            <code data-vocabulary-exempt="source-reference">
              {a.basis.binding_set_revision_ids.map((id) => id.slice(0, 8)).join(", ")}
            </code>
          </>
        )}
      </td>
      <td>{a.cited_records}</td>
      <td>
        {dispatchable ? (
          <Link
            to={links.dispatch(day, a.scope === "INTERVAL" ? a.assessment_revision_id : null)}
            data-evidence-dispatch-link={a.assessment_revision_id}
          >
            Open on Dispatch
          </Link>
        ) : (
          <span data-evidence-dispatch-withheld>
            {body.audit_only ? "Not linked: record only" : "Not linked"}
          </span>
        )}
      </td>
    </tr>
  );
}

function valueText(r: EvidenceRecord): string {
  if (r.value === null || r.value === undefined) {
    return "–";
  }
  return `${r.value}${r.unit ? ` ${r.unit}` : ""}`;
}

/** One page of the cited records, with paging to the full set. */
function Records({
  body,
  selected,
  search,
}: {
  body: FindingEvidenceBody;
  selected: string | null;
  search: (changes: Record<string, string | null>) => string;
}) {
  const { page } = body;
  const first = page.returned === 0 ? 0 : page.offset + 1;
  const last = page.offset + page.returned;
  const previous = page.offset > 0 ? Math.max(0, page.offset - page.limit) : null;
  return (
    <Panel heading="Cited records" headingId="finding-evidence-records-heading">
      <p data-evidence-page-range>
        Records {first}–{last} of {page.total}, in source time order.
      </p>
      <DataTable labelledBy="finding-evidence-records-heading">
        <thead>
          <tr>
            <th scope="col">Time (UTC)</th>
            <th scope="col">Measurement</th>
            <th scope="col">Value</th>
            <th scope="col">Quality</th>
            <th scope="col">Batch</th>
            <th scope="col">Message fingerprint</th>
            <th scope="col">Record trail</th>
            <th scope="col">Record</th>
          </tr>
        </thead>
        <tbody>
          {body.records.map((r) => (
            <tr
              key={r.evidence_id}
              data-evidence-id={r.evidence_id}
              data-evidence-lineage-status={r.lineage_status}
              aria-current={r.evidence_id === selected ? "true" : undefined}
            >
              {r.resolved ? (
                <>
                  <td>{stamp(r.source_time ?? r.interval?.start ?? null)}</td>
                  <td>{roleWords(r.role ?? "")}</td>
                  <td>{valueText(r)}</td>
                  <td>{qualityWords(r.quality ?? "")}</td>
                  <td>
                    <code data-vocabulary-exempt="source-reference">{(r.batch?.external_batch_id ?? r.batch?.batch_id ?? "").slice(0, 12)}</code>
                  </td>
                  <td>
                    <code data-vocabulary-exempt="source-reference">{(r.envelope?.sha256 ?? "").slice(0, 10)}</code>
                    {r.envelope?.digest_verified
                      ? ""
                      : r.broken_links.includes("ENVELOPE")
                        ? " (stored message missing)"
                        : " (does not match)"}
                  </td>
                </>
              ) : (
                <td colSpan={6} data-evidence-withheld>
                  {WITHHELD}
                </td>
              )}
              <td>
                {r.lineage_status === "RESOLVED"
                  ? "Complete"
                  : <LinkList links={r.broken_links} />}
              </td>
              <td>
                <Link to={search({ record: r.evidence_id })} data-evidence-select={r.evidence_id}>
                  <code data-vocabulary-exempt="source-reference">{r.evidence_id.slice(0, 8)}</code>
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      <nav className="finding-evidence__pages" aria-label="Cited record pages" data-evidence-pages>
        {previous === null ? null : (
          <Link to={search({ offset: previous === 0 ? null : String(previous), record: null })} data-evidence-page="previous">
            Previous {page.limit} records
          </Link>
        )}
        {page.next_offset === null ? (
          <span data-evidence-page="end"> End of the cited records.</span>
        ) : (
          <Link to={search({ offset: String(page.next_offset), record: null })} data-evidence-page="next">
            Next records ({page.next_offset + 1}–{Math.min(page.total, page.next_offset + page.limit)} of {page.total})
          </Link>
        )}
      </nav>
      <p className="site-finding__note">
        Choose a record&apos;s reference to see its full trail here; its stored message opens on the site&apos;s records page.
      </p>
    </Panel>
  );
}

/** finding-evidence:2 — one cited record's source, stored message and assessment trail. */
function RecordLineage({
  body,
  evidenceId,
  links,
  closeSearch,
}: {
  body: FindingEvidenceBody;
  evidenceId: string;
  links: SiteFindingEvidenceLinks;
  closeSearch: string;
}) {
  const r = body.records.find((x) => x.evidence_id === evidenceId);
  if (r === undefined) {
    return (
      <Panel heading="Selected record" headingId="finding-evidence-record-heading">
        <p data-evidence-record-absent>
          The record in the address is not on this page of this version&apos;s cited records. It is not shown, and no other
          record is shown in its place.
        </p>
        <p>
          <Link to={closeSearch}>Clear the selected record</Link>
        </p>
      </Panel>
    );
  }
  const inspector = body.links.records[r.evidence_id] === undefined ? null : links.record(r.evidence_id);
  const words = (link: string) => <LinkText link={link} />;
  return (
    <Panel heading="Selected record" headingId="finding-evidence-record-heading">
      <div data-evidence-record={r.evidence_id} data-evidence-record-lineage={r.lineage_status}>
        {!r.resolved ? (
          <p className="site-finding__lead" data-evidence-withheld>
            {WITHHELD}
          </p>
        ) : (
          <>
            {r.broken_links.length > 0 ? (
              <ul className="site-finding__lead" data-evidence-record-breaks>
                {r.broken_links.map((link) => (
                  <li key={link} data-evidence-record-break={link}>
                    {words(link)}
                  </li>
                ))}
              </ul>
            ) : null}
            <FactList>
              <Fact term="Accepted record">
                <code data-vocabulary-exempt="source-reference">{r.evidence_id}</code>
              </Fact>
              <Fact term="Measurement">
                {roleWords(r.role ?? "")}: {valueText(r)} ({qualityWords(r.quality ?? "")})
              </Fact>
              <Fact term="Source time (UTC)">{stamp(r.source_time ?? r.interval?.start ?? null)}</Fact>
              <Fact term="Received (UTC)">{stamp(r.received_at ?? null)}</Fact>
              <Fact term="Accepted (UTC)">{r.accepted_at ? stamp(r.accepted_at) : words("ACCEPTANCE_DISPOSITION")}</Fact>
              <Fact term="Source">
                gateway <code data-vocabulary-exempt="source-reference">{r.source?.gateway_id ?? "–"}</code>, epoch{" "}
                {r.source?.sequence_epoch ?? "–"}, sequence {String(r.source?.sequence ?? "–")},{" "}
                <Mode value={r.source?.source_mode} />
              </Fact>
              <Fact term="Delivery batch">
                {r.batch?.resolved ? (
                  <code data-vocabulary-exempt="source-reference">{r.batch.external_batch_id ?? r.batch.batch_id}</code>
                ) : (
                  words("BATCH")
                )}
              </Fact>
              <Fact term="Message">
                <code data-vocabulary-exempt="source-reference">{r.message_id ?? "–"}</code>
              </Fact>
              <Fact term="Message fingerprint">
                {r.envelope?.digest_verified ? (
                  <span data-evidence-envelope-verified>
                    <code data-vocabulary-exempt="source-reference">{r.envelope.sha256}</code> (the stored message matches it)
                  </span>
                ) : (
                  <span data-evidence-envelope-broken>
                    {words(r.broken_links.includes("ENVELOPE") ? "ENVELOPE" : "ENVELOPE_DIGEST")}
                  </span>
                )}
              </Fact>
              <Fact term="Accepted under">
                {r.accepted_as?.foundation_resolved ? `Foundation version ${String(r.accepted_as.foundation_version)}` : words("FOUNDATION_REVISION")}
                {"; "}
                {r.accepted_as?.binding_set_resolved
                  ? `device links version ${String(r.accepted_as.binding_set_version)}`
                  : words("BINDING_SET_REVISION")}
                {r.accepted_as?.binding_resolved ? null : <>; {words("BINDING_REVISION")}</>}
                {r.accepted_as?.configuration_outdated ? "; the site setup has changed since" : ""}
              </Fact>
              <Fact term="Used by">
                {(r.used_by?.assessment_revision_ids ?? []).length === 0
                  ? words("ASSESSMENT_CITATION")
                  : (r.used_by?.assessment_revision_ids ?? [])
                      .map((id) => {
                        const a = body.assessments.find((x) => x.assessment_revision_id === id);
                        return a === undefined
                          ? id.slice(0, 8)
                          : `${a.scope === "WINDOW" ? "whole-day" : "period"} assessment ${stamp(a.window.start)}, model ${a.model_version}`;
                      })
                      .join("; ")}
              </Fact>
            </FactList>
          </>
        )}
        <p>
          {inspector === null ? (
            <span data-evidence-inspector-withheld>The stored record cannot be opened from here.</span>
          ) : (
            <Link to={inspector} data-evidence-record-link={r.evidence_id}>
              Open the stored record and its original message
            </Link>
          )}{" "}
          <Link to={closeSearch}>Clear the selected record</Link>
        </p>
      </div>
    </Panel>
  );
}

/**
 * S4-03: the older assessment-keyed Finding page's Evidence tab
 * (`/findings/{site}/{assessment}/evidence`) is not a second Evidence source.
 * It lists, as plain links, the saved Findings whose episode overlaps the
 * assessed window (every UTC day the window touches is read). This is a
 * day-level navigation aid: no link says the old assessment created or cites
 * that Finding, and nothing is opened automatically, even for one result.
 */
const DAY_MS = 86_400_000;

/** Every UTC day (YYYY-MM-DD) a window touches; the end instant itself is excluded. */
export function daysTouched(start: string, end: string): string[] {
  const s = Date.parse(start);
  const e = Date.parse(end);
  if (!Number.isFinite(s) || !Number.isFinite(e) || e < s) {
    return [dayOf(start)];
  }
  const days: string[] = [];
  let cursor = Math.floor(s / DAY_MS) * DAY_MS;
  const last = e > s ? e - 1 : s;
  while (cursor <= last) {
    days.push(new Date(cursor).toISOString().slice(0, 10));
    cursor += DAY_MS;
  }
  return days;
}

/** Strict overlap: a Finding that only touches the window's start or end does not count. */
function overlapsWindow(f: { episode_start: string; episode_end: string }, window: { start: string; end: string }): boolean {
  const fs = Date.parse(f.episode_start);
  const fe = Date.parse(f.episode_end);
  const ws = Date.parse(window.start);
  const we = Date.parse(window.end);
  return fs < we && ws < fe;
}

export function LegacyFindingEvidence({
  siteId,
  assessedWindow,
  findings,
  durableEvidenceHref,
  recordsHref,
}: {
  siteId: string;
  assessedWindow: { start: string; end: string };
  findings: FindingClient;
  durableEvidenceHref: (findingId: string) => string;
  recordsHref: string;
}) {
  const startKey = assessedWindow.start;
  const endKey = assessedWindow.end;
  const days = daysTouched(startKey, endKey);
  const dayKey = days.join(",");
  const [reads, setReads] = useState<FindingReadResult<FindingWindowBody>[] | null>(null);
  useEffect(() => {
    let active = true;
    setReads(null);
    void Promise.all(dayKey.split(",").map((d) => findings.getFindingWindow(siteId, d))).then((loaded) => {
      if (active) {
        setReads(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [findings, siteId, dayKey]);

  if (reads === null) {
    return <p>Loading the Findings recorded for this period.</p>;
  }
  const failed = reads.some((r) => r.status !== "loaded");
  const ids: string[] = [];
  for (const r of reads) {
    if (r.status !== "loaded") {
      continue;
    }
    for (const f of r.value.findings) {
      const id = String(f.finding_id ?? f.id ?? "");
      if (id !== "" && !ids.includes(id) && overlapsWindow(f, { start: startKey, end: endKey })) {
        ids.push(id);
      }
    }
  }
  const label = days.length === 1 ? days[0] : `${days[0]} to ${days[days.length - 1]}`;
  return (
    <Panel
      heading={days.length === 1 ? "Findings recorded for this day" : "Findings recorded for these days"}
      headingId="legacy-finding-evidence-heading"
    >
      {failed && ids.length === 0 ? (
        <p data-legacy-evidence="unavailable">
          The saved Findings for this period could not be read, so no Finding evidence is offered here. The period&apos;s
          accepted records are on <Link to={recordsHref}>the site&apos;s records page</Link>.
        </p>
      ) : ids.length === 0 ? (
        <p data-legacy-evidence="none">
          No saved Finding overlaps this assessed period ({label}), so there is no Finding evidence to open. The period&apos;s
          accepted records are on <Link to={recordsHref}>the site&apos;s records page</Link>.
        </p>
      ) : (
        <>
          <p data-legacy-evidence="candidates">
            {ids.length === 1 ? "One saved Finding overlaps" : `${ids.length} saved Findings overlap`} this assessed period
            ({label}). This list only helps you find a Finding by its day: it does not say this assessment created or cites
            it. Open one to see its own evidence:
          </p>
          {failed ? <p data-legacy-evidence="partial">Some days could not be read, so this list may be incomplete.</p> : null}
          <ul>
            {ids.map((id) => (
              <li key={id}>
                <Link to={durableEvidenceHref(id)} data-legacy-evidence-link={id}>
                  Finding <code data-vocabulary-exempt="source-reference">{id.slice(0, 8)}</code> {days.length === 1 ? "(recorded for the same day)" : "(recorded for an overlapping day)"}
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </Panel>
  );
}
