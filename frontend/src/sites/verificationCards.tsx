/**
 * W1-UX-04 phase 2: the answer cards of the Verification, Plan and Evidence
 * child views of an Action. Words only from the reads already made: the
 * outcome, reasons and source class come from the verification reads, never
 * from the Action summary. A historical selection says so and never reads as
 * current; a missing or unknown value is drawn as "not known", never zero.
 */
import { Link } from "react-router-dom";

import {
  currentnessWords,
  ExactReferences,
  HeadlineVisualCard,
  limitationWords,
  outcomeWords,
  plainTime,
  ProductOutcome,
  ProductStatus,
  StepStrip,
  ValueBars,
  type FailedLimit,
  type ProductWords,
} from "../ui";
import type { ActionBody } from "./actionClient";
import type { VerificationLinks } from "./SiteActionVerification";
import type { EvidenceBody, Metric, OutcomeBody, OutcomeRecord, PlanBody } from "./verificationClient";
import { GUARDRAIL_KEYS, metricName, reasonWords, stateLabel } from "./verificationWords";

/** The plain "as of" bound of a read that carries no instant of its own: the Action read's cutoff, else its last event. */
export function actionReadAsOf(action: ActionBody): string | null {
  return action.selection.cutoff_recorded_at ?? action.last_event?.recorded_at ?? null;
}

function seconds(text: string | null | undefined): number | null {
  if (text === null || text === undefined || text.trim() === "") return null;
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
}

function minutesText(value: number | null): string {
  return value === null ? "not known" : `${Math.round(value / 60)} min`;
}

function find(metrics: readonly Metric[], key: string, window = "COMPARISON"): Metric | null {
  return metrics.find((m) => m.metric_key === key && m.window_name === window) ?? null;
}

/** Failed safety or service limits, exactly as the read returned them. */
export function failedLimits(metrics: readonly Metric[]): FailedLimit[] {
  return GUARDRAIL_KEYS.map((key) => find(metrics, key))
    .filter((m): m is Metric => m !== null && m.state === "FAIL")
    .map((m) => ({
      name: metricName(m.metric_key),
      value: m.value_text ?? "not known",
      threshold: m.threshold_text ?? "not recorded",
      unit: m.unit ?? "",
    }));
}

/**
 * W1-UX-04: the Verification answer card - did the measured trial meet its
 * goal without harmful trade-offs. With no shown record it states the current
 * read state; a selected earlier outcome is Historical beside the current state.
 */
export function VerificationCard({
  outcome,
  record,
  historical,
  action,
  links,
}: {
  outcome: OutcomeBody;
  record: OutcomeRecord | null;
  historical: boolean;
  action: ActionBody;
  links: VerificationLinks;
}) {
  const current = outcome.current_state;
  const currentWords = outcomeWords(current.state, current.reasons, null);
  const limits = record === null ? [] : failedLimits(outcome.metrics);
  const known = record === null ? [] : record.reasons.filter((r) => r.startsWith("KNOWN_FAILURE")).map(reasonWords);
  const words = record === null ? currentWords : outcomeWords(record.outcome, record.reasons, record.details?.source?.source_class ?? null);
  const before = record === null ? null : find(outcome.metrics, "candidate_avoidable_seconds", "BASELINE");
  const after = record === null ? null : find(outcome.metrics, "candidate_avoidable_seconds", "LATER");
  const beforeSeconds = seconds(before?.value_text);
  const afterSeconds = seconds(after?.value_text);
  const scope = "This Action's measured trial";
  const status =
    record !== null && historical ? (
      <ProductStatus words={currentnessWords("HISTORICAL")} scope="An earlier outcome of this Action" asOf={record.recorded_at}>
        <p data-verification-card-historical-outcome>
          Outcome then: {words.label}. Current state: {stateLabel(current.state, current.reasons)}.
        </p>
        {limits.map((limit) => (
          <p key={limit.name} data-verification-card-failed-limit>
            {limit.name} missed its limit: measured {limit.value} {limit.unit}, limit {limit.threshold} {limit.unit}.
          </p>
        ))}
      </ProductStatus>
    ) : (
      <ProductOutcome
        words={words}
        scope={scope}
        asOf={record === null ? actionReadAsOf(action) : record.recorded_at}
        failedLimits={limits}
        knownFailures={known}
      />
    );
  return (
    <HeadlineVisualCard
      dataName="verification"
      headingId="site-verification-answer-heading"
      title="Trial result"
      description="Whether the measured trial met its goal, and whether it stayed within its safety and service limits."
      question="Did the action work without harmful trade-offs?"
      headline={
        record === null ? (
          <>{currentWords.label}.</>
        ) : historical ? (
          <>An earlier outcome, shown as a record: {words.label.toLowerCase()}.</>
        ) : (
          <>{words.label}.</>
        )
      }
      status={status}
      visual={
        record === null ? undefined : (
          <ValueBars
            title="Avoidable generator time, before and after the change"
            items={[
              { label: "Before the change", key: "before", value: beforeSeconds, valueText: minutesText(beforeSeconds) },
              { label: "After the change", key: "after", value: afterSeconds, valueText: minutesText(afterSeconds) },
            ]}
          />
        )
      }
      meaning={
        <p>
          A trial result is judged against a plan fixed before the later readings arrived. It is a policy trial: it
          shows no saving or realized benefit, and a result can be withdrawn if late evidence changes it.
        </p>
      }
      todo={words.next === undefined ? undefined : <p>{words.next}</p>}
      destination={
        <>
          <Link to={links.view("evidence", { outcomeId: record?.outcome_id ?? null })} data-verification-card-evidence-link>
            Open Evidence
          </Link>{" "}
          <Link to={links.view("plan", { planRevisionId: record?.plan_id ?? current.plan_id ?? null })} data-verification-card-plan-link>
            Open the Plan
          </Link>
        </>
      }
      references={
        <ExactReferences
          name="verification-card-references"
          references={[
            { label: "Outcome reference", value: record?.outcome_id ?? current.outcome_id ?? null },
            { label: "Plan reference", value: record?.plan_id ?? current.plan_id ?? null },
            { label: "Outcome code", value: record?.outcome ?? null },
            { label: "Current state code", value: current.state },
            { label: "Reason codes", value: (record?.reasons ?? current.reasons).join(", ") || null },
            { label: "Recorded", value: record === null ? null : plainTime(record.recorded_at) },
          ]}
        />
      }
    />
  );
}

const PLAN_FIXED: ProductWords = {
  label: "Plan fixed before the later readings",
  sentence:
    "The goal, the safety and service limits and both comparison windows were recorded before the later readings arrived. A plan is not a result.",
  next: "Open Verification to see whether the trial met this plan.",
  tone: "neutral",
  code: "CURRENT_PLAN",
  unrecognised: false,
};

/**
 * W1-UX-04: the Plan answer card - what the trial will be judged on. A
 * replaced plan is Historical; no plan is the read's own NO_PLAN state.
 */
export function PlanCard({ body, action, links }: { body: PlanBody; action: ActionBody; links: VerificationLinks }) {
  const plan = body.plan;
  const replaced = plan !== null && body.is_current_plan === false;
  const words: ProductWords =
    plan === null ? outcomeWords(body.verification_state.state, body.verification_state.reasons, null) : replaced ? currentnessWords("HISTORICAL") : PLAN_FIXED;
  const later = plan === null ? null : body.selection_bindings.find((b) => b.window_name.toUpperCase().startsWith("LATER")) ?? null;
  return (
    <HeadlineVisualCard
      dataName="action-plan"
      headingId="site-verification-plan-answer-heading"
      title="Trial plan"
      description="What the trial is judged on, fixed before the later readings arrive."
      question="What will this trial be judged on?"
      headline={
        plan === null ? (
          <>No plan has been fixed for this trial yet.</>
        ) : (
          <>
            Avoidable generator time at least {Math.round((1 - plan.target.ratio[0] / plan.target.ratio[1]) * 100)}% lower,
            within every safety and service limit{replaced ? " (an earlier plan, since replaced)" : ""}.
          </>
        )
      }
      status={
        <ProductStatus
          words={words}
          scope={replaced ? "An earlier plan of this Action" : "This Action's trial plan"}
          asOf={plan === null ? actionReadAsOf(action) : plan.recorded_at}
        />
      }
      visual={
        plan === null ? undefined : (
          <StepStrip
            title="The two comparison windows"
            steps={[
              { label: "Earlier window", state: "done", detail: `${plainTime(plan.baseline_start) ?? "not recorded"} to ${plainTime(plan.baseline_end) ?? "not recorded"}` },
              { label: "Change in effect", state: "done", detail: plainTime(plan.effective_from) ?? "Time not recorded" },
              {
                label: "Later window",
                state: later === null ? "waiting" : "done",
                detail: `${plainTime(plan.later_start) ?? "not recorded"} to ${plainTime(plan.later_end) ?? "not recorded"}${later === null ? "; days not chosen yet" : ""}`,
              },
            ]}
          />
        )
      }
      meaning={
        <p>
          The trial compares an earlier window with a later one of similar demand and sunshine. A difference is not
          proof of cause, and the trial shows no saving.
        </p>
      }
      todo={words.next === undefined ? undefined : <p>{words.next}</p>}
      destination={
        <>
          <Link to={links.view("verification", {})} data-plan-card-verification-link>
            Open Verification
          </Link>{" "}
          <Link to={links.view("evidence", {})} data-plan-card-evidence-link>
            Open Evidence
          </Link>
        </>
      }
      references={
        <ExactReferences
          name="plan-card-references"
          references={[
            { label: "Plan reference", value: plan?.plan_id ?? null },
            { label: "Plan rule version", value: plan?.plan_version ?? null },
            { label: "Change record", value: plan?.change_id ?? null },
            { label: "Current state code", value: body.verification_state.state },
          ]}
        />
      }
    />
  );
}

const BOTH_WINDOWS: ProductWords = {
  label: "Both windows have their readings",
  sentence: "Every five-minute reading the plan needs was received for both windows by the cutoff.",
  next: "Open Verification to see what the readings showed.",
  tone: "neutral",
  code: "COMPLETE",
  unrecognised: false,
};

/**
 * W1-UX-04: the Evidence answer card - what evidence was received and what is
 * missing. Received counts come from the caller's slot check; an empty window
 * is "not known", never zero received.
 */
export function EvidenceCard({
  body,
  received,
  links,
}: {
  body: EvidenceBody;
  received: { baseline: number; later: number };
  links: VerificationLinks;
}) {
  const complete = body.windows.baseline.complete && body.windows.later.complete;
  const words = complete ? BOTH_WINDOWS : limitationWords("MISSING_READINGS");
  const item = (label: string, key: "baseline" | "later") => {
    const total = body.windows[key].slots.length;
    return {
      label,
      key,
      value: total === 0 ? null : received[key],
      valueText: `${received[key]} of ${total} readings`,
    };
  };
  return (
    <HeadlineVisualCard
      dataName="action-evidence"
      headingId="site-verification-evidence-answer-heading"
      title="Trial evidence"
      description="The readings the plan needs for each window, as accepted by the cutoff."
      question="What evidence was received, and what is missing?"
      headline={
        complete ? (
          <>Both comparison windows are complete.</>
        ) : (
          <>Some readings are missing{body.windows.later.complete ? " from the earlier window" : " from the later window"}.</>
        )
      }
      status={<ProductStatus words={words} scope="This Action's trial plan, both windows" asOf={body.knowledge_cutoff} />}
      visual={
        <ValueBars
          title="Complete five-minute readings per window"
          items={[item("Earlier window", "baseline"), item("Later window", "later")]}
        />
      }
      meaning={
        <p>
          Missing readings are never filled in. A window with missing readings cannot support a result, so the trial
          reads as "cannot tell yet" until they arrive or the plan says otherwise.
        </p>
      }
      todo={words.next === undefined ? undefined : <p>{words.next}</p>}
      destination={
        <Link to={links.view("verification", {})} data-evidence-card-verification-link>
          Open Verification
        </Link>
      }
      references={
        <ExactReferences
          name="evidence-card-references"
          references={[
            { label: "Plan reference", value: body.plan_id },
            { label: "Reading cutoff", value: plainTime(body.knowledge_cutoff) },
            { label: "Source of both windows", value: body.source_resolution.pair.source_class },
          ]}
        />
      }
    />
  );
}
