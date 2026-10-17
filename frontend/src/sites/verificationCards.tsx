/**
 * W1-F4 (D-2026-10-17-mockup-layout-spec): the state words and metric cards of
 * the Verification, Plan and Evidence child views of an Action. They replace the
 * W1-UX-04 answer cards: the verdict now leads the one-line status strip, and
 * the Verification view's four metric cards sit above panel 1, as in the v69
 * mock. Words only from the reads already made: the outcome, reasons and source
 * class come from the verification reads, never from the Action summary. A
 * historical selection says so and never reads as current; a missing or unknown
 * value is drawn as a gap word, never zero.
 */
import { MetricCard, MetricCards, currentnessWords, limitationWords, outcomeWords, type FailedLimit, type MetricTone, type OutcomeWords, type ProductWords } from "../ui";
import type { ActionBody } from "./actionClient";
import type { EvidenceBody, Metric, OutcomeBody, OutcomeRecord, PlanBody } from "./verificationClient";
import { checkWord, decimal, GUARDRAIL_KEYS, metricName, minutes, outcomeName, stateLabel, type Tone } from "./verificationWords";

/** The plain "as of" bound of a read that carries no instant of its own: the Action read's cutoff, else its last event. */
export function actionReadAsOf(action: ActionBody): string | null {
  return action.selection.cutoff_recorded_at ?? action.last_event?.recorded_at ?? null;
}

function seconds(text: string | null | undefined): number | null {
  if (text === null || text === undefined || text.trim() === "") return null;
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
}

export function findMetric(metrics: readonly Metric[], key: string, window = "COMPARISON"): Metric | null {
  return metrics.find((m) => m.metric_key === key && m.window_name === window) ?? null;
}

/** Failed safety or service limits, exactly as the read returned them. */
export function failedLimits(metrics: readonly Metric[]): FailedLimit[] {
  return GUARDRAIL_KEYS.map((key) => findMetric(metrics, key))
    .filter((m): m is Metric => m !== null && m.state === "FAIL")
    .map(plainLimit);
}

/** A failed limit in plain units: the measured value as read, and the limit in words (the exact text stays beside it). */
export function plainLimit(m: Metric): FailedLimit {
  const name = metricName(m.metric_key);
  const n = seconds(m.value_text);
  if (m.metric_key === "below_reserve_seconds") {
    return { name, value: n === null ? "not known" : String(Math.round(n / 60)), threshold: "0", unit: "min" };
  }
  if (m.metric_key === "terminal_soc") {
    const before = seconds(m.threshold_text);
    return { name, value: m.value_text ?? "not known", threshold: before === null ? "not recorded" : `at least ${m.threshold_text}`, unit: "%" };
  }
  if (m.metric_key === "unserved_critical_energy") {
    const before = seconds(m.threshold_text);
    return { name, value: m.value_text ?? "not known", threshold: before === null ? "not recorded" : `at most ${m.threshold_text}`, unit: "kWh" };
  }
  return { name, value: m.value_text ?? "not known", threshold: m.threshold_text ?? "not recorded", unit: m.unit ?? "" };
}

/** The verdict that leads the status strip: what it says, what it is about, and the instant it is bounded by. */
export interface StripVerdict {
  words: ProductWords;
  scope: string;
  asOf: string | null;
  /** Set for an outcome: the source qualification and demonstration note. */
  outcome?: OutcomeWords;
}

/** The Verification view: the shown outcome record, else the current read state. */
export function verificationVerdict(outcome: OutcomeBody | null, record: OutcomeRecord | null, historical: boolean, action: ActionBody): StripVerdict {
  if (outcome === null) {
    return { words: outcomeWords("PENDING", [], null), scope: "This Action's measured trial", asOf: actionReadAsOf(action) };
  }
  const current = outcome.current_state;
  if (record === null) {
    return { words: outcomeWords(current.state, current.reasons, null), scope: "This Action's measured trial", asOf: actionReadAsOf(action) };
  }
  const words = outcomeWords(record.outcome, record.reasons, record.details?.source?.source_class ?? null);
  // A selected earlier outcome is a record, never the current answer: the strip leads with "Historical" words and
  // the outcome then stays in panel 1 under its Historical tag, beside the current state badge.
  return {
    words: historical ? currentnessWords("HISTORICAL") : words,
    outcome: words,
    scope: historical ? "An earlier outcome of this Action" : "This Action's measured trial",
    asOf: record.recorded_at,
  };
}

const PLAN_FIXED: ProductWords = {
  label: "Plan fixed before the later readings",
  sentence: "The goal, the safety and service limits and both comparison windows were recorded before the later readings arrived. A plan is not a result.",
  tone: "neutral",
  code: "CURRENT_PLAN",
  unrecognised: false,
};

/** The Plan view: a replaced or time-selected plan is Historical; no plan is the read's own NO_PLAN state. */
export function planVerdict(body: PlanBody, action: ActionBody): StripVerdict {
  const plan = body.plan;
  if (plan === null) {
    return { words: outcomeWords(body.verification_state.state, body.verification_state.reasons, null), scope: "This Action's trial plan", asOf: actionReadAsOf(action) };
  }
  if (body.is_current_plan === false) {
    return { words: currentnessWords("HISTORICAL"), scope: "An earlier plan of this Action", asOf: plan.recorded_at };
  }
  if (body.verification_state.historical === true) {
    return { words: currentnessWords("HISTORICAL"), scope: "The plan as it stood at the selected earlier time", asOf: body.selector.recorded_at ?? plan.recorded_at };
  }
  return { words: PLAN_FIXED, scope: "This Action's trial plan", asOf: plan.recorded_at };
}

const BOTH_WINDOWS: ProductWords = {
  label: "Both windows have their readings",
  sentence: "Every five-minute reading the plan needs was received for both windows by the cutoff.",
  tone: "neutral",
  code: "COMPLETE",
  unrecognised: false,
};

/** The Evidence view: complete windows, else missing readings (never complete). */
export function evidenceVerdict(body: EvidenceBody): StripVerdict {
  const complete = body.windows.baseline.complete && body.windows.later.complete;
  const historical = body.verification_state.historical === true;
  return {
    words: complete ? BOTH_WINDOWS : limitationWords("MISSING_READINGS"),
    scope: historical ? "Both windows, as the readings stood at the selected earlier time" : "This Action's trial plan, both windows",
    asOf: body.knowledge_cutoff,
  };
}

export function metricTone(tone: Tone): MetricTone {
  return tone === "pass" ? "green" : tone === "fail" ? "red" : tone === "unknown" ? "amber" : "muted";
}

function checkTone(state: string | undefined): MetricTone {
  return state === "PASS" ? "green" : state === "FAIL" ? "red" : "amber";
}

/**
 * The mock's four Verification cards, from the shown outcome's metrics. With
 * no shown outcome every card is a gap word: `gap` says which (Pending while
 * no outcome is current; Not available when the read failed).
 */
export function VerificationMetricCards({ outcome, record, gap }: { outcome: OutcomeBody | null; record: OutcomeRecord | null; gap: "Pending" | "Not available" }) {
  const label = "Verification measures";
  if (outcome === null || record === null) {
    const note = gap === "Pending" ? "No current outcome to measure" : "The verification read failed";
    return (
      <MetricCards label={label} data={{ "data-verification-cards": "gap" }}>
        <MetricCard label="Target change" value={gap} note={note} word tone="muted" data={{ "data-verification-card": "target" }} />
        <MetricCard label="Reserve breaches" value={gap} note={note} word tone="muted" data={{ "data-verification-card": "reserve" }} />
        <MetricCard label="Critical service" value={gap} note={note} word tone="muted" data={{ "data-verification-card": "service" }} />
        <MetricCard label="Final outcome" value={gap} note={gap === "Pending" ? "A plan or activity alone is not a result" : note} assessment tone="muted" data={{ "data-verification-card": "outcome" }} />
      </MetricCards>
    );
  }
  const metrics = outcome.metrics;
  const target = findMetric(metrics, "target_reduction");
  const before = minutes(findMetric(metrics, "candidate_avoidable_seconds", "BASELINE")?.value_text);
  const after = minutes(findMetric(metrics, "candidate_avoidable_seconds", "LATER")?.value_text);
  const below = findMetric(metrics, "below_reserve_seconds");
  const unserved = findMetric(metrics, "unserved_critical_energy");
  const unservedKwh = decimal(unserved?.value_text ?? null);
  return (
    <MetricCards label={label} data={{ "data-verification-cards": "outcome" }}>
      <MetricCard
        label="Target change"
        value={before === null && after === null ? "Unknown" : `${before ?? "unknown"} → ${after ?? "unknown"}`}
        word={before === null && after === null}
        note={target ? `Avoidable generator time · target ${checkWord(target.state).toLowerCase()}` : "Target not evaluated"}
        tone={target ? checkTone(target.state) : "muted"}
        data={{ "data-verification-card": "target" }}
      />
      <MetricCard
        label="Reserve breaches"
        value={minutes(below?.value_text) ?? "Unknown"}
        word={minutes(below?.value_text) === null}
        note={below ? `Time below reserve, sampled every five minutes · ${checkWord(below.state).toLowerCase()}` : "Not evaluated"}
        tone={below ? checkTone(below.state) : "muted"}
        data={{ "data-verification-card": "reserve" }}
      />
      <MetricCard
        label="Critical service"
        value={unservedKwh === null ? "Unknown" : `${unservedKwh} kWh`}
        word={unservedKwh === null}
        note={unserved ? `Critical demand not served · ${checkWord(unserved.state).toLowerCase()}` : "Not evaluated"}
        tone={unserved ? checkTone(unserved.state) : "muted"}
        data={{ "data-verification-card": "service" }}
      />
      <MetricCard
        label="Final outcome"
        value={outcomeName(record.outcome)}
        note={stateLabel(record.outcome, record.reasons)}
        assessment
        tone={record.outcome === "VERIFIED" ? "green" : record.outcome === "INEFFECTIVE" ? "red" : "amber"}
        data={{ "data-verification-card": "outcome" }}
      />
    </MetricCards>
  );
}
