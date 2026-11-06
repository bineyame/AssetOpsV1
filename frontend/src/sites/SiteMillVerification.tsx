/**
 * CH-9b3 (CH9b3-R Q5-Q7): the mill verdict page body at `/sites/{code}/domain-actions/{id}/verification`. One
 * Panel and one DataTable from the existing components; no cost-check or trial-hours card (both null), no new
 * layout. The stored outcome's words come from `verificationWords.ts` ("Target not met", "Could not conclude"); the
 * sentence, the before/after line and the not-judged text are the server's own (`verification_families`).
 *
 * MOCK DEVIATION D1 (R700, MD-CH9b-1): v70 has no mill verdict page. The page, its "Target met" headline, the
 * not-judged line and the table are new; see `.agent/review-packet-CH-9b3.md` "Mock to new".
 */
import { useEffect, useState } from "react";

import { DataTable, Panel } from "../ui";
import type { MillVerification, MillVerificationClient, MillVerificationResult } from "./millVerificationClient";
import { LABEL_INCONCLUSIVE, LABEL_TARGET_MISS, stateSentence } from "./verificationWords";

export const MILL_LOADING = "Loading the Action's verification.";
export const MILL_NOT_FOUND = "No such Action for this site.";
export const MILL_PANEL_HEADING_ID = "mill-verification-heading";

/** The headline of a mill verdict state (MOCK DEVIATION R700 for "Target met" and "Not judged yet"). */
export function millHeadline(state: string): string {
  switch (state) {
    case "VERIFIED":
      return "Target met";
    case "INEFFECTIVE":
      return LABEL_TARGET_MISS;
    case "INCONCLUSIVE":
      return LABEL_INCONCLUSIVE;
    case "NOT_JUDGED":
      return "Not judged yet";
    case "NO_PLAN":
      return "No verification plan yet";
    default:
      return "State not recognised";
  }
}

export function useMillVerification(client: MillVerificationClient, siteCode: string, actionId: string) {
  const [state, setState] = useState<MillVerificationResult | null>(null);
  useEffect(() => {
    let live = true;
    setState(null);
    void client.read(siteCode, actionId).then((r) => {
      if (live) setState(r);
    });
    return () => {
      live = false;
    };
  }, [client, siteCode, actionId]);
  return state;
}

function kwh(value: string | null): string {
  return value === null ? "Not available yet" : `${value} kWh a day`;
}

function days(n: number): string {
  return `${n} of 3`;
}

export function MillVerificationBody({ state }: { state: MillVerificationResult | null }) {
  if (state === null) return <p role="status">{MILL_LOADING}</p>;
  if (state.status === "not_found") return <p role="alert">{MILL_NOT_FOUND}</p>;
  if (state.status === "error") return <p role="alert">{state.message}</p>;
  return <MillVerificationPanel body={state.body} />;
}

export function MillVerificationPanel({ body }: { body: MillVerification }) {
  const lines = body.state === "NO_PLAN" ? [stateSentence("NO_PLAN")] : [body.sentence, body.line, body.not_judged_text];
  return (
    <Panel heading="Verification" headingId={MILL_PANEL_HEADING_ID} description="Midday use of the Site's productive loads, before and after the change">
      <p data-mill-state={body.state}>
        <strong>{millHeadline(body.state)}</strong>
      </p>
      {lines
        .filter((l): l is string => l !== null && l !== "")
        .map((l) => (
          <p key={l} data-mill-line>
            {l}
          </p>
        ))}
      {body.metrics.length === 0 ? null : (
        <DataTable labelledBy={MILL_PANEL_HEADING_ID}>
          <thead>
            <tr>
              <th scope="col">Measure</th>
              <th scope="col">Before the change</th>
              <th scope="col">After the change</th>
              <th scope="col">Fully checked days (before, after)</th>
              <th scope="col">Needed to pass</th>
            </tr>
          </thead>
          <tbody>
            {body.metrics.map((m) => (
              <tr key={m.metric_key} data-mill-metric={m.state}>
                <th scope="row">{m.label}</th>
                <td>{kwh(m.before)}</td>
                <td>{kwh(m.after)}</td>
                <td>
                  {days(m.days_before)}, {days(m.days_after)}
                </td>
                <td>{m.threshold === null ? "At least 10% above before" : `At least 10% above before: ${m.threshold} kWh a day`}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      <p className="mock-deviation-line" data-mock-deviation="R700">
        MOCK DEVIATION D1 (R700)
      </p>
    </Panel>
  );
}
