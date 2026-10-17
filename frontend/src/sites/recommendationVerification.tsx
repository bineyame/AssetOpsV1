/**
 * S6-02b `recommendation:2-3` and `changes:1#b` / `changes:2`: how the accepted
 * trial will be judged, what evidence it needs, and the later effect of an
 * applied change. The verification state shown is the read's `verification`
 * block (S6-02a F5), never `state.outcome` or the Change's apply-time outcome.
 * The accepted recommendation snapshot stays pinned; this only links to the
 * frozen plan once one exists.
 */
import { Link } from "react-router-dom";

import { AttentionList, ChartNote, DataTable, Panel } from "../ui";
import type { VerificationSummary } from "./verificationClient";
import { stateLabel, stateSentence, stateTone } from "./verificationWords";

export type VerificationChild = "plan" | "evidence" | "verification";

export interface TrialLinks {
  /** A verification child of an Action (current state when no selector is given). */
  child: (actionId: string, view: VerificationChild, selector?: { planRevisionId?: string | null; outcomeId?: string | null }) => string;
}

export function VerificationStateLine({
  summary,
  name,
  note = false,
}: {
  summary: VerificationSummary | null | undefined;
  name: string;
  /** W1-F4: render as one v69 chart-note line inside a v69 panel. */
  note?: boolean;
}) {
  const extra = note ? " v69-chart-note" : "";
  if (!summary) {
    return (
      <p className={`action-note${extra}`} data-trial-verification-state="UNAVAILABLE" data-trial-verification-name={name}>
        The verification state is not available from this server yet.
      </p>
    );
  }
  return (
    <p className={`action-status${extra}`} data-trial-verification-state={summary.state} data-trial-verification-name={name}>
      <span className={`verify-chip verify-chip--${stateTone(summary.state)}`}>{stateLabel(summary.state, summary.reasons)}</span>
      <span className="action-note">{stateSentence(summary.state, summary.reasons)}</span>
    </p>
  );
}

/** `recommendation:2`: success declared before evaluating, linked to the frozen plan once present. */
export function DeclaredSuccessPanel({
  actionId,
  summary,
  links,
}: {
  actionId: string;
  summary: VerificationSummary | null | undefined;
  links: TrialLinks;
}) {
  const planId = summary && summary.state !== "NO_PLAN" ? summary.plan_id : null;
  return (
    <Panel heading="Declare success before evaluating" headingId="site-recommendation-success-heading">
      <DataTable labelledBy="site-recommendation-success-caption">
        <caption id="site-recommendation-success-caption">How the trial will be judged</caption>
        <thead>
          <tr>
            <th scope="col">Role</th>
            <th scope="col">Criterion</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Target</th>
            <td>Generator time that could have been avoided falls by at least 25%</td>
          </tr>
          <tr>
            <th scope="row">Limit</th>
            <td>No time below the reserve in the later window (five-minute samples)</td>
          </tr>
          <tr>
            <th scope="row">Limit</th>
            <td>No increase in critical demand not served</td>
          </tr>
          <tr>
            <th scope="row">Limit</th>
            <td>Battery charge at the end of the window at least as high as before</td>
          </tr>
          <tr>
            <th scope="row">Evidence</th>
            <td>Every reading present in both windows; demand, solar and starting charge comparable</td>
          </tr>
        </tbody>
      </DataTable>
      {planId ? (
        <ChartNote data={{ "data-recommendation-plan-link": planId }}>
          <Link to={links.child(actionId, "plan", { planRevisionId: planId })}>Open the frozen plan</Link>. The accepted
          proposal stays as it was accepted.
        </ChartNote>
      ) : (
        <ChartNote data={{ "data-recommendation-plan-link": "none" }}>
          The plan is frozen after the change is applied; it does not exist yet.
        </ChartNote>
      )}
    </Panel>
  );
}

/** `recommendation:3`: the evidence needed to verify, with the current verification state. */
export function EvidenceNeededPanel({
  actionId,
  actionCode,
  summary,
  links,
  actionHref,
}: {
  actionId: string;
  actionCode: string;
  summary: VerificationSummary | null | undefined;
  links: TrialLinks;
  actionHref: string;
}) {
  return (
    <Panel heading="Evidence needed to verify" headingId="site-recommendation-evidence-heading">
      <AttentionList
        label="Evidence needed to verify"
        items={[
          {
            key: "applied",
            title: "Applied change record",
            body: "The applied setting change and when it took effect.",
            action: <Link to={actionHref}>Open {actionCode} →</Link>,
          },
          {
            key: "later",
            title: "Later operating readings",
            body: "Readings in a later window, accepted under the frozen plan.",
            action: (
              <Link to={links.child(actionId, "evidence")} data-recommendation-evidence-link>
                Inspect the evidence →
              </Link>
            ),
          },
          {
            key: "outcome",
            title: "Outcome",
            body: "Decided from the target and the limits together.",
            action: (
              <Link to={links.child(actionId, "verification")} data-recommendation-verification-link>
                Open verification →
              </Link>
            ),
          },
        ]}
      />
      <VerificationStateLine summary={summary} name="recommendation" note />
    </Panel>
  );
}

/** `changes:1#b`: the later-window effect of an applied change; APPLIED is never success. */
export function LaterEffectPanel({
  actionId,
  summary,
  links,
}: {
  actionId: string;
  summary: VerificationSummary | null | undefined;
  links: TrialLinks;
}) {
  const outcomeId = summary?.outcome_id ?? null;
  return (
    <Panel heading="Later effect" headingId="site-change-effect-heading">
      <p className="action-note">
        The setting changed when it was applied. Whether that worked is judged later, from the trial's windows; being
        applied is not success.
      </p>
      <VerificationStateLine summary={summary} name="change" />
      <ul className="action-list">
        <li>
          <Link to={links.child(actionId, "verification")} data-change-verification-link>
            Current verification state
          </Link>
        </li>
        {outcomeId ? (
          <li>
            <Link to={links.child(actionId, "verification", { outcomeId })} data-change-outcome-link={outcomeId}>
              The outcome behind this state (opens as Historical)
            </Link>
          </li>
        ) : null}
      </ul>
    </Panel>
  );
}

/** `changes:2`: the decision path from the applied change to an outcome. */
export function DecisionPathPanel({
  actionId,
  summary,
  appliedEventHref,
  links,
}: {
  actionId: string;
  summary: VerificationSummary | null | undefined;
  appliedEventHref: string;
  links: TrialLinks;
}) {
  const planId = summary && summary.state !== "NO_PLAN" ? summary.plan_id : null;
  return (
    <Panel heading="Decision path" headingId="site-change-path-heading">
      <ol className="action-list verify-steps" data-change-decision-path>
        <li>
          Declare success before evaluating.{" "}
          {planId ? (
            <Link to={links.child(actionId, "plan", { planRevisionId: planId })} data-change-plan-link={planId}>
              Inspect the plan
            </Link>
          ) : (
            <span className="action-note">No plan is frozen yet.</span>
          )}
        </li>
        <li>
          Apply and observe: the applied setting is recorded, then later readings are accepted.{" "}
          <Link to={appliedEventHref}>Application record</Link>,{" "}
          <Link to={links.child(actionId, "evidence")}>accepted evidence</Link>
        </li>
        <li>
          Outcome, from the target and limits together.{" "}
          <Link to={links.child(actionId, "verification")}>View verification</Link>
        </li>
      </ol>
    </Panel>
  );
}
