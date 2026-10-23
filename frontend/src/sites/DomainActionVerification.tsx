/**
 * W5-02c K4a (`.agent/W5-02c-K4-preflight-rulings.md` rulings 4, 5, 8; build spec "Action panels"): the two loaded
 * panels of the v69 `cold-action` screen (`frontend/mockups/v69/index.html:742-746`), `Declared outcome criteria` and
 * `Related activity`, from one validated domain Action detail read. No fetches; `domainActionClient.ts` owns the read
 * and the shell in `SiteAnalyticsFrames.tsx` owns the breadcrumb, header, strip, currentness and concluding notices.
 *
 * Nothing here asserts an observed automatic start or cooling restoration: the result cells are the stored initial
 * results (`Not tested`, `Not tested`, `Not established`, `Pending`) and the completed-inspection sentence states
 * activity only.
 */
import { useNavigate } from "react-router-dom";

import { DataTable, Panel } from "../ui";
import type { DomainActionDetail } from "./domainActionClient";
import { coldRequestHref } from "./siteWorkCases";

export const COLD_CRITERIA_TITLE = "Declared outcome criteria";
export const COLD_CRITERIA_COLUMNS = ["Criterion", "Required evidence", "Current result"] as const;
export const COLD_RELATED_TITLE = "Related activity";
/** Build spec "Empty intent": the criteria panel keeps its heading and omits its table. */
export const COLD_INTENT_MISSING = "No outcome criteria have been declared for this Action.";
/** MOCK DEVIATION (D2) R100: the honest selected state when no completed inspection is linked at the cutoff. */
export const COLD_RELATED_NOT_LINKED = "No completed inspection is linked to this Action.";
export const COLD_INSPECT = "Inspect maintenance evidence";
export const COLD_INSPECT_UNAVAILABLE = "Maintenance detail is unavailable for this record.";
export const COLD_SOURCE_FINDING = "Open source Finding →";
export const COLD_SOURCE_FINDING_UNAVAILABLE = "The selected Finding revision cannot be opened here yet.";

/** Build spec "Shared Site UI": the three stored initial result labels. */
export const COLD_RESULT_LABELS: Record<string, string> = {
  NOT_TESTED: "Not tested",
  NOT_ESTABLISHED: "Not established",
  PENDING: "Pending",
};

/** Ruling 5: the completed-inspection sentence, from the selected request title and code only. */
export function coldRelatedCompleted(title: string, code: string): string {
  return `${title} ${code} is complete. A witnessed outcome test remains required.`;
}

/**
 * Ruling 19, MOCK DEVIATION (D2) R102: a selected linked request that is still OPEN or IN_PROGRESS is named with its
 * actual state; the mock's completed wording would claim a completion the record does not hold.
 */
export function coldRelatedOngoing(title: string, code: string, state: "OPEN" | "IN_PROGRESS"): string {
  return `${title} ${code} is ${state === "OPEN" ? "open" : "in progress"}. A witnessed outcome test remains required.`;
}

const CRITERIA_HEADING_ID = "domain-action-criteria-heading";
const RELATED_HEADING_ID = "domain-action-related-heading";
const INSPECT_NOTE_ID = "domain-action-inspect-unavailable";

/**
 * Rulings 5 and 19: the Related activity sentence for the selected request. COMPLETED with its performed record is a
 * completed inspection; a linked OPEN or IN_PROGRESS request is named with its state; anything else (no case, or
 * COMPLETED without its performed record) is the no-completed-inspection sentence.
 */
function relatedSentence(work: DomainActionDetail["links"]["work"]): { kind: string; text: string } {
  if (work.case_id !== null && work.case_title !== null && work.case_code !== null) {
    if (work.request_state === "COMPLETED" && work.record_id !== null) {
      return { kind: "completed", text: coldRelatedCompleted(work.case_title, work.case_code) };
    }
    if (work.request_state === "OPEN" || work.request_state === "IN_PROGRESS") {
      return { kind: work.request_state === "OPEN" ? "open" : "in-progress", text: coldRelatedOngoing(work.case_title, work.case_code, work.request_state) };
    }
  }
  return { kind: "not-linked", text: COLD_RELATED_NOT_LINKED };
}

export function DomainActionVerification({
  detail,
  siteCode,
  knownAt,
}: {
  detail: DomainActionDetail;
  /** The stored Site code, for the selected W6 request Overview address. */
  siteCode: string;
  /** The explicit URL cutoff only (P-G-4); null omits `known_at` from the Overview address. */
  knownAt: string | null;
}) {
  const navigate = useNavigate();
  const work = detail.links.work;
  const related = relatedSentence(work);
  // Ruling 8, MOCK DEVIATION (D1) R68: Inspect opens the selected W6 request Overview (the mock's `workverification`
  // target is unavailable) whenever a case ID is selected.
  const inspectHref = work.case_id === null ? null : coldRequestHref(work.case_id, siteCode, knownAt);
  const intent = detail.intent;
  return (
    <>
      <Panel heading={COLD_CRITERIA_TITLE} headingId={CRITERIA_HEADING_ID}>
        {intent === null ? (
          <p data-domain-action-intent-missing>{COLD_INTENT_MISSING}</p>
        ) : (
          <div data-domain-action-criteria>
            <DataTable labelledBy={CRITERIA_HEADING_ID}>
              <thead>
                <tr>
                  {COLD_CRITERIA_COLUMNS.map((column) => (
                    <th key={column} scope="col">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {intent.criteria.map((criterion) => {
                  const result = detail.results?.find((r) => r.key === criterion.key)?.result ?? null;
                  return (
                    <tr key={criterion.key} data-domain-action-criterion={criterion.key}>
                      <td>{criterion.label}</td>
                      <td>{criterion.required_evidence}</td>
                      <td data-domain-action-result={result ?? ""}>{result === null ? "" : COLD_RESULT_LABELS[result]}</td>
                    </tr>
                  );
                })}
              </tbody>
            </DataTable>
          </div>
        )}
      </Panel>
      <Panel heading={COLD_RELATED_TITLE} headingId={RELATED_HEADING_ID}>
        <div className="domain-action-related" data-domain-action-related={related.kind}>
          <p className="prose" data-domain-action-related-sentence>
            {related.text}
          </p>
          <p className="domain-action-related__controls">
            {inspectHref === null ? (
              <>
                <button
                  type="button"
                  className="button"
                  disabled
                  aria-describedby={INSPECT_NOTE_ID}
                  data-domain-action-inspect="unavailable"
                >
                  {COLD_INSPECT}
                </button>{" "}
                <span className="muted" id={INSPECT_NOTE_ID} data-domain-action-inspect-note>
                  {COLD_INSPECT_UNAVAILABLE}
                </span>
              </>
            ) : (
              <button
                type="button"
                className="button"
                onClick={() => navigate(inspectHref)}
                data-domain-action-inspect="live"
                data-domain-action-inspect-target={inspectHref}
              >
                {COLD_INSPECT}
              </button>
            )}{" "}
            {/* MOCK DEVIATION (D1) R66: the mock's `Open source Finding →` link is muted noninteractive text until an
                exact-revision cold Finding destination exists (ruling 8). */}
            <span className="muted" data-domain-action-finding-control>
              {COLD_SOURCE_FINDING}
            </span>{" "}
            <span className="muted" data-domain-action-finding-note>
              {COLD_SOURCE_FINDING_UNAVAILABLE}
            </span>
          </p>
        </div>
      </Panel>
    </>
  );
}
