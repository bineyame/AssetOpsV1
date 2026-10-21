/**
 * W4-03 unit 6b: the canonical mini Finding > Alternatives view
 * (`/sites/:siteId/findings/:findingId/alternatives?revision_id=<exact-selected-uuid>`, v69 `alternatives`).
 *
 * Read-only (closure 1): the authored alternatives of one exact W1 Finding revision from `mini-alternatives-1`. The
 * frame passes the revision its W1 Finding read resolved (u6 ruling 5); this view never reads without one. Columns
 * are exactly `Explanation`, `Evidence`, `Disposition` (u5 6b); a `NEEDS_REVIEW` row shows `Needs review for this
 * revision` while its stored disposition stays in the data. The notice is always shown.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { DataTable, Panel } from "../ui";
import { Notice } from "../ui/V69Layout";
import {
  decisionRefusalCopy,
  type AlternativeListBody,
  type AlternativeRow,
  type AlternativesPage,
  type DecisionRead,
  type MiniDecisionsClient,
} from "./miniDecisionsClient";
import "./w4-mini-decisions.css";

export const ALTERNATIVES_HEADING_ID = "mini-alternatives-heading";
export const ALTERNATIVES_HEADING = "Alternatives to investigate";
export const ALTERNATIVES_EMPTY = "No alternatives recorded for this Finding revision.";
export const ALTERNATIVES_NOTICE =
  "Candidate runtime is not proof that stopping the generator would have preserved service.";
export const ALTERNATIVES_NEEDS_REVIEW = "Needs review for this revision";
export const ALTERNATIVES_NO_EVIDENCE = "No accepted record supports or excludes this explanation.";
/** u6 rulings 5 and 6: the noninteractive gap where no exact Finding revision is resolved. */
export const ALTERNATIVES_FINDING_UNAVAILABLE = "Alternatives for this Finding unavailable";

/** The original Alternatives ledger's disposition words. */
const DISPOSITION_WORDS: Record<string, string> = {
  PLAUSIBLE: "Plausible policy explanation",
  CANNOT_EXCLUDE: "Cannot exclude",
  INDETERMINATE: "Indeterminate",
  RULED_OUT: "Ruled out by cited evidence",
};

export function dispositionText(row: AlternativeRow): string {
  if (row.review_state === "NEEDS_REVIEW") return ALTERNATIVES_NEEDS_REVIEW;
  return DISPOSITION_WORDS[row.disposition] ?? row.disposition;
}

function Rows({ rows, recordHref }: { rows: AlternativeRow[]; recordHref: (evidenceId: string) => string }) {
  return (
    <div className="mini-alternatives-table" data-alternatives-table>
      <DataTable labelledBy={ALTERNATIVES_HEADING_ID}>
        <thead>
          <tr>
            <th scope="col">Explanation</th>
            <th scope="col">Evidence</th>
            <th scope="col">Disposition</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              data-alternative-row={row.id}
              data-alternative-revision={row.revision_id}
              data-alternative-review={row.review_state}
              data-disposition={row.disposition}
            >
              <td data-alternative-explanation>{row.explanation}</td>
              <td data-alternative-evidence>
                <span>{row.evidence_summary}</span>
                {row.missing_evidence_reason === null ? null : (
                  <span className="mini-alternatives-note" data-alternative-missing-reason>
                    {row.missing_evidence_reason}
                  </span>
                )}
                {row.cited_accepted_evidence_ids.length === 0 ? (
                  <span className="mini-alternatives-note" data-alternative-no-evidence>
                    {ALTERNATIVES_NO_EVIDENCE}
                  </span>
                ) : (
                  <ul className="mini-alternatives-cited">
                    {row.cited_accepted_evidence_ids.map((id) => (
                      <li key={id}>
                        <Link to={recordHref(id)} data-alternative-cited={id}>
                          <code>{id}</code>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </td>
              <td data-alternative-disposition>{dispositionText(row)}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

export function MiniAlternatives({
  siteCode,
  findingId,
  revisionId,
  client,
  recordHref,
}: {
  siteCode: string;
  findingId: string;
  /** The exact revision the frame's W1 Finding read resolved (`selection.revision_id`). */
  revisionId: string;
  client: MiniDecisionsClient;
  recordHref: (evidenceId: string) => string;
}) {
  const [result, setResult] = useState<DecisionRead<AlternativeListBody> | null>(null);
  // u6b ruling 11: the page request; null is the first page (no cutoff, no cursor).
  const [page, setPage] = useState<AlternativesPage | null>(null);
  const [pending, setPending] = useState(false);
  // The frame keys this component by Site, Finding and revision, so a new identity starts again at page one.
  useEffect(() => {
    let active = true;
    setPending(true);
    void client.getAlternatives(siteCode, findingId, revisionId, page ?? undefined).then((loaded) => {
      if (!active) return;
      // The current page's rows stay until this response resolves.
      setResult(loaded);
      setPending(false);
    });
    return () => {
      active = false;
    };
  }, [client, siteCode, findingId, revisionId, page]);
  const next = result !== null && result.status === "loaded" ? result.value.next_cursor : null;
  return (
    <div className="mini-alternatives" data-mini-alternatives>
      <Panel heading={ALTERNATIVES_HEADING} headingId={ALTERNATIVES_HEADING_ID}>
        {result === null ? (
          <p data-alternatives-loading>Loading the Finding&apos;s alternatives.</p>
        ) : result.status === "loaded" ? (
          <>
            {result.value.currentness.state === "HISTORICAL" ? (
              <p className="mini-alternatives-note" data-alternatives-historical>
                Historical basis
              </p>
            ) : null}
            {result.value.rows.length === 0 ? (
              <p data-alternatives-empty>{ALTERNATIVES_EMPTY}</p>
            ) : (
              <Rows rows={result.value.rows} recordHref={recordHref} />
            )}
            {next === null && page === null ? null : (
              <p className="mini-alternatives-pager" data-alternatives-pager>
                {page === null ? null : (
                  <button type="button" className="link-button" disabled={pending} onClick={() => setPage(null)}>
                    First page
                  </button>
                )}
                {next === null ? null : (
                  <button
                    type="button"
                    className="link-button"
                    disabled={pending}
                    data-alternatives-next
                    onClick={() => setPage({ known_at: result.value.window.known_at, cursor: next })}
                  >
                    Next
                  </button>
                )}
              </p>
            )}
          </>
        ) : (
          <p
            className="mini-alternatives-note"
            data-alternatives-refused={result.status === "refused" ? result.code : "unavailable"}
          >
            {decisionRefusalCopy(result)}
          </p>
        )}
      </Panel>
      <Notice tone="blue" data={{ "data-alternatives-notice": "" }}>
        {ALTERNATIVES_NOTICE}
      </Notice>
    </div>
  );
}
