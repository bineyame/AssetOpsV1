/**
 * S6-02b: the Action's Plan, Evidence and Verification child views
 * (`action-plan:1`, `action-evidence:1`, `verification:1-3`), under the S6-01b
 * Action root at `/sites/{site}/actions/{action}/{plan|evidence|verification}`.
 *
 * Selection (D-2026-10-16-s602-questions):
 * - no selector: the latest current read state, including PENDING and
 *   REASSESSMENT_PENDING after a withdrawal, with an explicit link to the
 *   prior outcome;
 * - `?outcome_id=` an exact immutable outcome, `?plan_revision_id=` an exact
 *   frozen plan, `?recorded_at=` a server cutoff (an S6-01b `?event_id=` is
 *   read as its recorded cutoff); an explicit selection is shown under a
 *   prominent "Historical" label with the current state beside it, separately;
 * - conflicting selectors are a typed `VERIFICATION_SELECTOR_CONFLICT`, never a
 *   silent preference.
 *
 * The current state comes from the verification reads (`current_state`,
 * `verification_state`), never from the Action's `state.outcome` (S6-02a F5).
 * Every case is a policy trial on Lab or authored test data: no causal proof,
 * no savings or realized benefit, and a RESOLVED can be withdrawn.
 */
import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import type { ActionBody, ActionReadResult, Refusal } from "./actionClient";
import { Ref, RefusalPanel, when } from "./actionPresentation";
import type {
  EvidenceBody,
  EvidenceWindow,
  HistoryBody,
  Metric,
  OutcomeBody,
  OutcomeRecord,
  PlanBody,
  PointCell,
  PowerCell,
  Slot,
  SourceSide,
  VerificationClient,
  VerificationPlan,
  VerificationState,
} from "./verificationClient";
import {
  checkTone,
  checkWord,
  decimal,
  GUARDRAIL_FAIL,
  GUARDRAIL_KEYS,
  LABEL_GUARDRAIL_FAIL,
  metricName,
  METRIC_WORDS,
  minutes,
  outcomeName,
  problemCode,
  problemWords,
  reasonWords,
  sourceWords,
  stateLabel,
  stateSentence,
  stateTone,
  type Tone,
  cellWord,
} from "./verificationWords";

export const VERIFICATION_VIEWS = ["plan", "evidence", "verification"] as const;
export type VerificationView = (typeof VERIFICATION_VIEWS)[number];

export const VERIFICATION_LOADING = {
  plan: "Loading the verification plan.",
  evidence: "Loading the verification evidence.",
  outcome: "Loading the verification outcome.",
  history: "Loading the verification history.",
} as const;

export interface VerificationSelection {
  eventId: string | null;
  recordedAt: string | null;
  planRevisionId: string | null;
  outcomeId: string | null;
}

export interface VerificationLinks {
  /** A verification child view with an exact selection (the current state when all are null). */
  view: (view: VerificationView, selection: { planRevisionId?: string | null; outcomeId?: string | null; recordedAt?: string | null }) => string;
  /** The Site Foundation change record. */
  change: (changeId: string) => string;
  /** The Action History at one exact event. */
  event: (eventId: string) => string;
  /** A Finding at an exact version. */
  finding: (findingId: string, revisionId: string | null) => string;
  /** The Site Evidence inspector at one accepted evidence ID. */
  evidenceRecord: (evidenceId: string) => string;
}

const CONFLICT = "VERIFICATION_SELECTOR_CONFLICT";

interface Reads {
  outcome: ActionReadResult<OutcomeBody> | null;
  history: ActionReadResult<HistoryBody> | null;
  plan: ActionReadResult<PlanBody> | null;
  evidence: ActionReadResult<EvidenceBody> | null;
  conflict: string | null;
  /** The verification view's plan selection has no outcome yet. */
  noOutcomeForPlan: boolean;
}

const EMPTY: Reads = { outcome: null, history: null, plan: null, evidence: null, conflict: null, noOutcomeForPlan: false };

/** Selector combinations with no single meaning (checked before any read). */
export function selectorConflict(selection: VerificationSelection): string | null {
  const exact = selection.planRevisionId !== null || selection.outcomeId !== null;
  if (selection.eventId !== null && exact) {
    return "The address names an Action event and an exact plan or outcome. An event is a point in the Action's record, not a verification selection.";
  }
  if (selection.recordedAt !== null && exact) {
    return "The address names a recorded time and an exact plan or outcome. Choose one.";
  }
  return null;
}

export function ActionVerification({
  siteId,
  actionId,
  view,
  selection,
  body,
  client,
  links,
}: {
  siteId: string;
  actionId: string;
  view: VerificationView;
  selection: VerificationSelection;
  body: ActionBody;
  client: VerificationClient;
  links: VerificationLinks;
}) {
  const [reads, setReads] = useState<Reads>(EMPTY);
  const { eventId, recordedAt, planRevisionId, outcomeId } = selection;
  const eventCutoff = eventId !== null ? body.selection.cutoff_recorded_at : null;

  useEffect(() => {
    let active = true;
    const set = (patch: Partial<Reads>) => {
      if (active) setReads((prior) => ({ ...prior, ...patch }));
    };
    setReads(EMPTY);
    const conflict = selectorConflict({ eventId, recordedAt, planRevisionId, outcomeId });
    if (conflict !== null) {
      setReads({ ...EMPTY, conflict });
      return () => {
        active = false;
      };
    }
    const cutoff = recordedAt ?? eventCutoff;
    void (async () => {
      let pinned: OutcomeRecord | null = null;
      if (outcomeId !== null) {
        const read = await client.getOutcome(siteId, actionId, { id: outcomeId, recordedAt: null });
        set({ outcome: read });
        if (read.status !== "loaded") return;
        pinned = read.value.outcome;
        if (pinned && planRevisionId !== null && pinned.plan_id !== planRevisionId) {
          set({
            conflict:
              "The address names a plan and an outcome that belongs to another plan. Nothing was chosen for you.",
          });
          return;
        }
      }
      if (view === "verification") {
        const history = await client.getHistory(siteId, actionId);
        set({ history });
        if (outcomeId !== null) return;
        if (planRevisionId !== null) {
          if (history.status !== "loaded") return;
          const mine = history.value.outcomes.filter((o) => o.plan_id === planRevisionId);
          const last = mine[mine.length - 1];
          if (!last) {
            const plan = await client.getPlan(siteId, actionId, { id: planRevisionId, recordedAt: null });
            set({ plan, noOutcomeForPlan: true });
            return;
          }
          set({ outcome: await client.getOutcome(siteId, actionId, { id: last.outcome_id, recordedAt: null }) });
          return;
        }
        set({ outcome: await client.getOutcome(siteId, actionId, { id: null, recordedAt: cutoff }) });
      } else if (view === "plan") {
        const chosen = pinned ? pinned.plan_id : planRevisionId;
        set({ plan: await client.getPlan(siteId, actionId, { id: chosen, recordedAt: chosen ? null : cutoff }) });
      } else {
        const read = pinned
          ? await client.getEvidence(siteId, actionId, { id: null, recordedAt: pinned.recorded_at })
          : await client.getEvidence(siteId, actionId, { id: planRevisionId, recordedAt: planRevisionId ? null : cutoff });
        set({ evidence: read });
        if (pinned && read.status === "loaded" && read.value.plan_id !== pinned.plan_id) {
          set({ conflict: "The evidence read at this outcome's time belongs to another plan. Nothing was chosen for you." });
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [client, siteId, actionId, view, eventId, eventCutoff, recordedAt, planRevisionId, outcomeId]);

  const explicit = outcomeId !== null || planRevisionId !== null || recordedAt !== null || eventId !== null;
  const latestLink = (
    <Link to={links.view(view, {})} data-verification-current-link>
      Show the current state
    </Link>
  );

  if (reads.conflict !== null) {
    return (
      <Panel heading="Conflicting selection" headingId="site-verification-conflict-heading">
        <p data-verification-selector-conflict={CONFLICT}>{reads.conflict}</p>
        <p className="action-note">
          Code: <Ref value={CONFLICT} />
        </p>
        <ul className="action-list">
          {outcomeId ? (
            <li>
              <Link to={links.view(view, { outcomeId })}>Open the exact outcome only</Link>
            </li>
          ) : null}
          {planRevisionId ? (
            <li>
              <Link to={links.view(view, { planRevisionId })}>Open the exact plan only</Link>
            </li>
          ) : null}
          {recordedAt ? (
            <li>
              <Link to={links.view(view, { recordedAt })}>Open everything recorded through that time</Link>
            </li>
          ) : null}
          <li>{latestLink}</li>
        </ul>
      </Panel>
    );
  }

  const loading: ReactNode[] = [];
  const refusals: Refusal[] = [];
  const watch = <T,>(read: ActionReadResult<T> | null, needed: boolean, sentence: string): T | null => {
    if (!needed) return null;
    if (read === null) {
      loading.push(<p key={sentence}>{sentence}</p>);
      return null;
    }
    if (read.status !== "loaded") {
      refusals.push(read);
      return null;
    }
    return read.value;
  };
  const outcomeNeeded = view === "verification" ? !reads.noOutcomeForPlan : outcomeId !== null;
  const outcome = watch(reads.outcome, outcomeNeeded, VERIFICATION_LOADING.outcome);
  const history = watch(reads.history, view === "verification", VERIFICATION_LOADING.history);
  const plan = watch(reads.plan, view === "plan" || reads.noOutcomeForPlan, VERIFICATION_LOADING.plan);
  const evidence = watch(reads.evidence, view === "evidence", VERIFICATION_LOADING.evidence);
  const current: VerificationState | null =
    outcome?.current_state ?? plan?.verification_state ?? evidence?.verification_state ?? history?.current_state ?? null;

  return (
    <div className="site-verification" data-verification-view={view} data-verification-explicit={explicit ? "yes" : "no"}>
      {loading}
      {refusals.map((refusal, index) => (
        <RefusalPanel
          key={`${refusal.code}-${index}`}
          refusal={refusal}
          subject="Verification"
          headingId={`site-verification-refused-${index}-heading`}
        >
          {refusal.code === CONFLICT ? <p data-verification-selector-conflict={CONFLICT}>Nothing was chosen for you. {latestLink}</p> : null}
          {refusal.http === 404 ? <p>{latestLink}</p> : null}
        </RefusalPanel>
      ))}
      {current ? (
        <CurrentStrip
          current={current}
          explicit={explicit}
          selection={selection}
          eventCutoff={eventCutoff}
          view={view}
          links={links}
        />
      ) : null}
      {view === "verification" && reads.noOutcomeForPlan && plan ? (
        <Panel heading="No outcome for this plan" headingId="site-verification-no-outcome-heading">
          <p data-verification-no-outcome-for-plan={planRevisionId ?? ""}>
            No outcome has been recorded for the selected plan yet. That is a waiting state, not an outcome.
          </p>
        </Panel>
      ) : null}
      {view === "verification" && outcome ? (
        <VerificationBody outcome={outcome} history={history} body={body} explicit={explicit} links={links} />
      ) : null}
      {view === "plan" && plan ? <PlanBodyView body={plan} action={body} links={links} explicit={explicit} /> : null}
      {view === "evidence" && evidence ? (
        <EvidenceBodyView body={evidence} links={links} pinnedOutcome={outcome?.outcome ?? null} />
      ) : null}
      <TrialNotice />
    </div>
  );
}

/* ---------------------------------------------------------------- shared parts */

function Chip({ tone, children, attr }: { tone: Tone; children: ReactNode; attr?: Record<string, string> }) {
  return (
    <span className={`verify-chip verify-chip--${tone}`} {...(attr ?? {})}>
      {children}
    </span>
  );
}

/** The fixed policy-trial limitation, on every verification view. */
export function TrialNotice() {
  return (
    <p className="action-limitation" data-verification-trial-label="POLICY_TRIAL_NO_SAVINGS">
      Policy trial on Lab or authored test data. It compares two observed windows under a plan fixed in advance. It
      does not prove the change caused the difference, and it shows no savings or realized benefit. A resolution can
      be withdrawn later; it is never permanent.
    </p>
  );
}

function CurrentStrip({
  current,
  explicit,
  selection,
  eventCutoff,
  view,
  links,
}: {
  current: VerificationState;
  explicit: boolean;
  selection: VerificationSelection;
  eventCutoff: string | null;
  view: VerificationView;
  links: VerificationLinks;
}) {
  const atCutoff = current.historical === true;
  return (
    <div className="verify-strip" data-verification-current-state={current.state}>
      {explicit ? (
        <p className="verify-historical" data-verification-historical>
          <strong>Historical</strong>{" "}
          {selection.outcomeId
            ? "An exact earlier outcome is selected."
            : selection.planRevisionId
              ? "An exact plan is selected."
              : `Showing what was recorded through ${when(selection.recordedAt ?? eventCutoff)}.`}{" "}
          The current state is shown separately. <Link to={links.view(view, {})}>Show the current state</Link>
        </p>
      ) : null}
      <p className="action-status">
        <span className="verify-strip__term">{atCutoff ? "State at the selected time" : "Current state"}</span>
        <Chip tone={stateTone(current.state)} attr={{ "data-verification-state-label": stateLabel(current.state, current.reasons) }}>
          {stateLabel(current.state, current.reasons)}
        </Chip>
        <span className="action-note">{stateSentence(current.state, current.reasons)}</span>
      </p>
      {current.reasons.length > 0 && current.state !== "VERIFIED" ? (
        <ul className="action-list" data-verification-current-reasons>
          {current.reasons.map((reason) => (
            <li key={reason}>{reasonWords(reason)}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function EvidenceIds({ ids, links, limit = 6, name }: { ids: readonly string[]; links: VerificationLinks; limit?: number; name: string }) {
  if (ids.length === 0) return <span className="action-note">No accepted reading cited.</span>;
  const shown = ids.slice(0, limit);
  return (
    <span className="verify-ids" data-verification-evidence-ids={name} data-verification-evidence-count={ids.length}>
      {shown.map((id, index) => (
        <span key={id}>
          {index > 0 ? ", " : ""}
          <Link to={links.evidenceRecord(id)}>
            <Ref value={id} />
          </Link>
        </span>
      ))}
      {ids.length > limit ? ` and ${ids.length - limit} more` : ""}
    </span>
  );
}

function DigDeeper({ name, children }: { name: string; children: ReactNode }) {
  return (
    <Disclosure summary="Dig deeper: identifiers and typed values" name={`verification-${name}`}>
      {children}
    </Disclosure>
  );
}

function windowBounds(start: string, end: string): string {
  return `${when(start)} to ${when(end)} (end not included)`;
}

/* ---------------------------------------------------------------- Verification view */

function metric(metrics: Metric[], key: string, window = "COMPARISON"): Metric | null {
  return metrics.find((m) => m.metric_key === key && m.window_name === window) ?? null;
}

function VerificationBody({
  outcome,
  history,
  body,
  explicit,
  links,
}: {
  outcome: OutcomeBody;
  history: HistoryBody | null;
  body: ActionBody;
  explicit: boolean;
  links: VerificationLinks;
}) {
  const current = outcome.current_state;
  const record = outcome.outcome;
  const historicalLabel = outcome.historical_label !== undefined || explicit;
  const showRecord = record !== null && (historicalLabel || current.state === record.outcome && current.outcome_id === record.outcome_id);
  const allOutcomes = history?.outcomes ?? [];
  const prior = allOutcomes.length > 0 ? allOutcomes[allOutcomes.length - 1] : null;
  return (
    <>
      {!showRecord ? (
        <Panel heading="Outcome" headingId="site-verification-outcome-heading">
          <p data-verification-no-current-outcome={current.state}>
            {record === null
              ? "No outcome has been recorded for this Action yet."
              : "The most recent outcome is not current, so it is not shown here as the result."}
          </p>
          {prior ? (
            <p>
              <Link to={links.view("verification", { outcomeId: prior.outcome_id })} data-verification-prior-outcome-link={prior.outcome_id}>
                Open the earlier outcome ({outcomeName(prior.outcome)}, recorded {when(prior.recorded_at)})
              </Link>{" "}
              <span className="action-note">It opens under a Historical label.</span>
            </p>
          ) : null}
        </Panel>
      ) : (
        <OutcomeView outcome={outcome} record={record!} historical={historicalLabel} links={links} />
      )}
      <div className="site-action__pair">
        <ActivityPanel body={body} history={history} links={links} />
        <OutcomeListPanel history={history} selectedId={showRecord ? record!.outcome_id : null} links={links} />
      </div>
    </>
  );
}

function OutcomeView({
  outcome,
  record,
  historical,
  links,
}: {
  outcome: OutcomeBody;
  record: OutcomeRecord;
  historical: boolean;
  links: VerificationLinks;
}) {
  const metrics = outcome.metrics;
  const reasons = record.reasons;
  const label = stateLabel(record.outcome, reasons);
  const windows = (record.details?.windows ?? {}) as Record<string, Record<string, unknown>>;
  const baseline = windows.baseline ?? {};
  const later = windows.later ?? {};
  const laterIds = record.basis?.evidence_ids?.later ?? [];
  const failed = GUARDRAIL_KEYS.map((k) => metric(metrics, k)).filter((m): m is Metric => m !== null && m.state === "FAIL");
  const unknown = reasons.filter((r) => !r.startsWith("KNOWN_FAILURE"));
  const known = reasons.filter((r) => r.startsWith("KNOWN_FAILURE"));
  const target = metric(metrics, "target_reduction");
  const before = metric(metrics, "candidate_avoidable_seconds", "BASELINE");
  const after = metric(metrics, "candidate_avoidable_seconds", "LATER");
  const unserved = metric(metrics, "unserved_critical_energy");
  const below = metric(metrics, "below_reserve_seconds");
  const terminal = metric(metrics, "terminal_soc");
  const evidenceHref = links.view("evidence", { outcomeId: record.outcome_id });
  return (
    <>
      <Panel heading={historical ? "Selected outcome" : "Outcome"} headingId="site-verification-outcome-heading">
        <div
          className={`verify-headline verify-headline--${stateTone(record.outcome)}`}
          data-verification-outcome={record.outcome}
          data-verification-label={label}
          data-verification-outcome-id={record.outcome_id}
          data-verification-historical-outcome={historical ? "yes" : "no"}
        >
          {historical ? <span className="verify-historical-tag">Historical</span> : null}
          <p className="action-proposal">{label}</p>
          <p className="action-note">
            {stateSentence(record.outcome, reasons)} Recorded {when(record.recorded_at)}. Outcome:{" "}
            {outcomeName(record.outcome)}.
          </p>
          {outcome.superseded_by_outcome_id ? (
            <p className="action-note" data-verification-superseded-by={outcome.superseded_by_outcome_id}>
              A later outcome replaced this one:{" "}
              <Link to={links.view("verification", { outcomeId: outcome.superseded_by_outcome_id })}>open the later outcome</Link>.
            </p>
          ) : null}
        </div>
        <div className="verify-cards">
          <Card label="Avoidable generator time" value={`${minutes(before?.value_text) ?? "unknown"} to ${minutes(after?.value_text) ?? "unknown"}`} note={target ? `Target: ${checkWord(target.state)}` : "Target not evaluated"} tone={target ? checkTone(target.state) : "unknown"} name="target" />
          <Card label="Time below reserve (sampled)" value={minutes(below?.value_text) ?? "unknown"} note={below ? checkWord(below.state) : "Not evaluated"} tone={below ? checkTone(below.state) : "unknown"} name="reserve" />
          <Card label="Critical demand not served" value={unserved?.value_text != null ? `${decimal(unserved.value_text)} kWh` : "unknown"} note={unserved ? checkWord(unserved.state) : "Not evaluated"} tone={unserved ? checkTone(unserved.state) : "unknown"} name="service" />
          <Card label="Final outcome" value={outcomeName(record.outcome)} note={label} tone={stateTone(record.outcome)} name="outcome" />
        </div>
      </Panel>

      {record.outcome === "INEFFECTIVE" && reasons.includes(GUARDRAIL_FAIL) ? (
        <Panel heading={LABEL_GUARDRAIL_FAIL} headingId="site-verification-guardrail-heading">
          <ul className="action-list" data-verification-guardrail-fail>
            {failed.map((m) => (
              <li key={m.metric_key} data-verification-failed-metric={m.metric_key}>
                <strong>{metricName(m.metric_key)}</strong>: later window{" "}
                <span data-verification-failed-value>{m.value_text ?? "unknown"}</span> {m.unit ?? ""}, limit{" "}
                <span data-verification-failed-threshold>{m.threshold_text ?? "unknown"}</span> {m.unit ?? ""}. Evidence:{" "}
                <EvidenceIds ids={m.evidence_ids.length > 0 ? m.evidence_ids : laterIds} links={links} name={m.metric_key} />
              </li>
            ))}
          </ul>
          {reasons.includes("TARGET_MISS") ? <p className="action-note">The target was also not met.</p> : null}
          <p className="action-note">
            The outcome stays recorded as ineffective. A failed safety or service limit closes this trial and holds new
            reserve trials on this battery.
          </p>
        </Panel>
      ) : null}

      {record.outcome === "INCONCLUSIVE" ? (
        <Panel heading="Why it could not conclude" headingId="site-verification-inconclusive-heading">
          <ul className="action-list" data-verification-unknown-reasons>
            {unknown.map((reason) => (
              <li key={reason}>{reasonWords(reason)}</li>
            ))}
          </ul>
          {known.length > 0 ? (
            <Disclosure summary="Known failures (not a verdict)" name="verification-known-failures">
              <ul className="action-list" data-verification-known-failures>
                {known.map((reason) => (
                  <li key={reason}>{reasonWords(reason)}</li>
                ))}
              </ul>
            </Disclosure>
          ) : null}
          <p className="action-note">
            A later trial may continue under a new plan that replaces this one; this outcome stays readable.
          </p>
        </Panel>
      ) : null}

      <Panel heading="Target and limits evaluated together" headingId="site-verification-metrics-heading">
        <p className="action-note">Rules were fixed in the plan before the later window was read.</p>
        <DataTable labelledBy="site-verification-metrics-caption">
          <caption id="site-verification-metrics-caption">Each measure, both windows</caption>
          <thead>
            <tr>
              <th scope="col">Measure</th>
              <th scope="col">Role</th>
              <th scope="col">Before</th>
              <th scope="col">After</th>
              <th scope="col">Limit</th>
              <th scope="col">Result</th>
            </tr>
          </thead>
          <tbody>
            <MetricRow name="target_reduction" before={minutes(before?.value_text)} after={minutes(after?.value_text)} limit="At least 25% lower" m={target} />
            <MetricRow name="unserved_critical_energy" before={kwh(baseline.unserved_critical_kwh)} after={kwh(unserved?.value_text)} limit="No more than before" m={unserved} />
            <MetricRow name="below_reserve_seconds" before={minutes(baseline.below_reserve_seconds as number)} after={minutes(below?.value_text)} limit="None" m={below} />
            <MetricRow name="terminal_soc" before={pct(terminal?.threshold_text)} after={pct(terminal?.value_text)} limit="At least as high as before" m={terminal} />
            <MetricRow name="feeder_demand_energy_band" before={kwh(baseline.feeder_demand_kwh)} after={kwh(later.feeder_demand_kwh)} limit="Within 10%" m={metric(metrics, "feeder_demand_energy_band")} />
            <MetricRow name="pv_available_energy_band" before={kwh(baseline.pv_available_kwh)} after={kwh(later.pv_available_kwh)} limit="Within 10%" m={metric(metrics, "pv_available_energy_band")} />
            <MetricRow name="initial_soc_band" before={pct(baseline.initial_soc)} after={pct(later.initial_soc)} limit="Within 2 points" m={metric(metrics, "initial_soc_band")} />
            <MetricRow name="window_coverage" before={metric(metrics, "window_coverage", "BASELINE")?.value_text ?? null} after={metric(metrics, "window_coverage", "LATER")?.value_text ?? null} limit="All 12 slots" m={coverage(metrics)} />
            <MetricRow name="source_provenance" before={null} after={sourceWords(metric(metrics, "source_provenance")?.value_text)} both limit="One coherent source per window" m={metric(metrics, "source_provenance")} />
          </tbody>
        </DataTable>
        <p className="action-note">
          Time below the reserve is checked at each five-minute sample; it is not continuous proof of battery charge.{" "}
          <Link to={evidenceHref} data-verification-evidence-link>
            Inspect the evidence for this outcome
          </Link>
        </p>
        <DigDeeper name="outcome">
          <FactList>
            <Fact term="Outcome ID">
              <Ref value={record.outcome_id} />
            </Fact>
            <Fact term="Typed outcome">
              <Ref value={record.outcome} attr="data-verification-typed-outcome" />
            </Fact>
            <Fact term="Reasons">
              {reasons.map((r) => (
                <span key={r}>
                  <Ref value={r} />{" "}
                </span>
              ))}
            </Fact>
            <Fact term="Plan">
              <Link to={links.view("plan", { planRevisionId: record.plan_id })}>
                <Ref value={record.plan_id} />
              </Link>
            </Fact>
            <Fact term="Later-window selection">
              <Ref value={record.selection_binding_id} />
            </Fact>
            <Fact term="Supersedes">{record.supersedes_outcome_id ? <Ref value={record.supersedes_outcome_id} /> : "none"}</Fact>
            <Fact term="Input fingerprint">
              <Ref value={record.basis_sha256} />
            </Fact>
            <Fact term="Recorded by">
              <Ref value={record.actor_id} />
            </Fact>
          </FactList>
          <DataTable labelledBy="site-verification-metric-keys-caption">
            <caption id="site-verification-metric-keys-caption">Stored measures</caption>
            <thead>
              <tr>
                <th scope="col">Key</th>
                <th scope="col">Window</th>
                <th scope="col">Value</th>
                <th scope="col">Limit</th>
                <th scope="col">Unit</th>
                <th scope="col">Result</th>
                <th scope="col">Readings</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((m) => (
                <tr key={`${m.metric_key}-${m.window_name}`} data-verification-metric-key={m.metric_key} data-verification-metric-state={m.state}>
                  <td>
                    <Ref value={m.metric_key} />
                  </td>
                  <td>
                    <Ref value={m.window_name} />
                  </td>
                  <td>{m.value_text ?? "unknown"}</td>
                  <td>{m.threshold_text ?? ""}</td>
                  <td>{m.unit ?? ""}</td>
                  <td>{checkWord(m.state)}</td>
                  <td>{m.evidence_ids.length}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </DigDeeper>
      </Panel>
    </>
  );
}

function coverage(metrics: Metric[]): Metric | null {
  const both = metrics.filter((m) => m.metric_key === "window_coverage");
  if (both.length === 0) return null;
  const state = both.some((m) => m.state === "FAIL") ? "FAIL" : both.every((m) => m.state === "PASS") ? "PASS" : "UNKNOWN";
  return { ...both[0], state };
}

function kwh(text: unknown): string | null {
  const value = decimal(typeof text === "string" ? text : text == null ? null : String(text));
  return value === null ? null : `${value} kWh`;
}

function pct(text: unknown): string | null {
  const value = decimal(typeof text === "string" ? text : text == null ? null : String(text));
  return value === null ? null : `${value}%`;
}

function Card({ label, value, note, tone, name }: { label: string; value: string; note: string; tone: Tone; name: string }) {
  return (
    <div className={`verify-card verify-card--${tone}`} data-verification-card={name}>
      <span className="verify-card__label">{label}</span>
      <span className="verify-card__value">{value}</span>
      <span className="verify-card__note">{note}</span>
    </div>
  );
}

/** `both`: one value judged over the window pair (the source check), shown once across both columns. */
function MetricRow({ name, before, after, limit, m, both = false }: { name: string; before: string | null; after: string | null; limit: string; m: Metric | null; both?: boolean }) {
  return (
    <tr data-verification-row={name} data-verification-row-state={m?.state ?? "MISSING"}>
      <th scope="row">{metricName(name)}</th>
      <td>{METRIC_WORDS[name]?.role ?? ""}</td>
      {both ? (
        <td colSpan={2}>Both windows: {after ?? "unknown"}</td>
      ) : (
        <>
          <td>{before ?? "unknown"}</td>
          <td>{after ?? "unknown"}</td>
        </>
      )}
      <td>{limit}</td>
      <td>
        <Chip tone={m ? checkTone(m.state) : "unknown"}>{m ? checkWord(m.state) : "Not evaluated"}</Chip>
      </td>
    </tr>
  );
}

function ActivityPanel({ body, history, links }: { body: ActionBody; history: HistoryBody | null; links: VerificationLinks }) {
  const change = body.change;
  const events = history?.resolution_events ?? [];
  const latestFinding = body.latest_finding_revision;
  return (
    <Panel heading="Activity evidence" headingId="site-verification-activity-heading">
      <FactList>
        <Fact term="Applied change">
          {change ? (
            <Link to={links.change(change.change_id)} data-verification-change-link>
              Battery reserve {change.old_value}
              {change.unit} to {change.new_value}
              {change.unit}
            </Link>
          ) : (
            "Not applied yet"
          )}
        </Fact>
        <Fact term="Application record">
          {change ? (
            <Link to={links.event(change.applied_event_id)} data-verification-applied-event-link>
              Applied {when(change.recorded_at)}
            </Link>
          ) : (
            "none"
          )}
        </Fact>
      </FactList>
      <p className="action-note">Applying the change is evidence of activity, not of success.</p>
      <h3 className="verify-subheading">Resolution activity</h3>
      {events.length === 0 ? (
        <p data-verification-resolution="none">No resolution recorded.</p>
      ) : (
        <ul className="action-list" data-verification-resolution-events>
          {events.map((event) => (
            <li key={event.id} data-verification-resolution-kind={event.kind}>
              {event.kind === "RESOLVED" ? "Resolved" : event.kind === "RESOLUTION_WITHDRAWN" ? "Resolution withdrawn" : "Resolution activity"}{" "}
              {when(event.recorded_at)}
              {event.verification_outcome_id ? (
                <>
                  {" "}
                  (
                  <Link to={links.view("verification", { outcomeId: event.verification_outcome_id })}>
                    {event.kind === "RESOLUTION_WITHDRAWN" ? "withdrawn outcome" : "outcome"}
                  </Link>
                  )
                </>
              ) : null}
              .
            </li>
          ))}
        </ul>
      )}
      <p className="action-note" data-verification-resolved-withdrawable>
        A resolution records the current outcome; later evidence can withdraw it. It is not permanent.
      </p>
      {latestFinding && !latestFinding.is_origin ? (
        <p className="action-note" data-verification-later-finding={latestFinding.id}>
          The Finding has a later version ({latestFinding.revision_no}):{" "}
          <Link to={links.finding(body.origin.finding_id, latestFinding.id)}>open it</Link>. It is a new episode; it does
          not rewrite this trial or its outcome.
        </p>
      ) : null}
    </Panel>
  );
}

function OutcomeListPanel({ history, selectedId, links }: { history: HistoryBody | null; selectedId: string | null; links: VerificationLinks }) {
  const outcomes = history?.outcomes ?? [];
  const plans = history?.plans ?? [];
  return (
    <Panel heading="Outcome evidence" headingId="site-verification-outcomes-heading">
      {outcomes.length === 0 ? (
        <p data-verification-outcomes="none">No outcome recorded yet.</p>
      ) : (
        <ul className="action-list" data-verification-outcomes>
          {outcomes.map((o, index) => (
            <li key={o.outcome_id} data-verification-outcome-item={o.outcome_id}>
              <Link to={links.view("verification", { outcomeId: o.outcome_id })}>
                {stateLabel(o.outcome, o.reasons)}
              </Link>{" "}
              ({outcomeName(o.outcome)}), recorded {when(o.recorded_at)}
              {index === outcomes.length - 1 ? " - most recent" : " - replaced later"}
              {o.outcome_id === selectedId ? " - shown above" : ""}.
            </li>
          ))}
        </ul>
      )}
      <p className="action-note">Each outcome keeps its own plan and evidence and stays readable.</p>
      {plans.length > 0 ? (
        <p className="action-note">
          Plans:{" "}
          {plans.map((p, index) => (
            <span key={p.plan_id}>
              {index > 0 ? ", " : ""}
              <Link to={links.view("plan", { planRevisionId: p.plan_id })} data-verification-plan-link={p.plan_id}>
                plan {index + 1}
              </Link>
            </span>
          ))}
        </p>
      ) : null}
    </Panel>
  );
}

/* ---------------------------------------------------------------- Plan view */

function PlanBodyView({ body, action, links, explicit }: { body: PlanBody; action: ActionBody; links: VerificationLinks; explicit: boolean }) {
  const plan = body.plan;
  if (plan === null) {
    return (
      <Panel heading="Success criteria" headingId="site-verification-plan-heading">
        <p data-verification-plan="none">
          No verification plan exists{explicit ? " at the selected time" : ""}.{" "}
          {action.change === null
            ? "The change has not been applied yet; a plan is frozen only after it is applied."
            : "The change is applied; the plan has not been frozen yet."}
        </p>
      </Panel>
    );
  }
  const binding = body.selection_bindings[body.selection_bindings.length - 1] ?? null;
  const [num, den] = plan.target.ratio;
  return (
    <>
      <Panel heading="Success criteria" headingId="site-verification-plan-heading">
        <p data-verification-plan-id={plan.plan_id} data-verification-plan-current={body.is_current_plan ? "yes" : "no"}>
          Fixed {when(plan.recorded_at)}, before the later window was read.{" "}
          {body.is_current_plan ? "This is the current plan." : "A later plan replaced this one."}
        </p>
        {plan.supersedes_plan_id ? (
          <p className="action-note">
            It continues an earlier plan:{" "}
            <Link to={links.view("plan", { planRevisionId: plan.supersedes_plan_id })} data-verification-supersedes-link>
              open the earlier plan
            </Link>
            .
          </p>
        ) : null}
        {body.superseded_by_plan_id ? (
          <p className="action-note">
            <Link to={links.view("plan", { planRevisionId: body.superseded_by_plan_id })} data-verification-superseded-plan-link>
              Open the plan that replaced it
            </Link>
          </p>
        ) : null}
        <DataTable labelledBy="site-verification-criteria-caption">
          <caption id="site-verification-criteria-caption">Criteria fixed before evaluation</caption>
          <thead>
            <tr>
              <th scope="col">Criterion</th>
              <th scope="col">Rule</th>
            </tr>
          </thead>
          <tbody>
            <tr data-verification-criterion="target">
              <th scope="row">Avoidable generator time</th>
              <td>
                At least 25% lower: later seconds times {den} at most earlier seconds times {num}, in whole seconds. Earlier
                window: {minutes(plan.baseline_candidate_seconds) ?? "unknown"}.
              </td>
            </tr>
            <tr data-verification-criterion="service">
              <th scope="row">Service limit</th>
              <td>Critical demand not served (requested minus delivered) is no higher than in the earlier window.</td>
            </tr>
            <tr data-verification-criterion="reserve">
              <th scope="row">Reserve limit</th>
              <td>No time below the reserve in the later window, checked at each five-minute sample (not continuous).</td>
            </tr>
            <tr data-verification-criterion="terminal">
              <th scope="row">Stored-energy limit</th>
              <td>Battery charge at the end of the later window is at least the earlier window's.</td>
            </tr>
            <tr data-verification-criterion="comparability">
              <th scope="row">Comparable windows</th>
              <td>
                Total site demand energy and available solar energy each within{" "}
                {Number(plan.bands.feeder_demand_energy_relative) * 100}% of the earlier window; starting battery charge
                within {plan.bands.initial_soc_points} points. Limits are inclusive.
              </td>
            </tr>
            <tr data-verification-criterion="coverage">
              <th scope="row">Evidence coverage</th>
              <td>
                Every required reading in all {plan.coverage.slots_per_window} five-minute slots of each window, plus a
                battery charge sample at each slot start and at the window end. Anything missing makes the result
                inconclusive.
              </td>
            </tr>
          </tbody>
        </DataTable>
        <ul className="action-list verify-explain">
          <li>If the earlier window's energy total is zero, the later total must also be zero.</li>
          <li>Every assigned demand point counts toward the site total; a missing assignment fails comparability.</li>
          <li>
            The later window judges avoidable generator time against the new, lower reserve. This is an observed policy
            trial, not proof of cause.
          </li>
        </ul>
      </Panel>
      <Panel heading="Windows" headingId="site-verification-windows-heading">
        <DataTable labelledBy="site-verification-windows-caption">
          <caption id="site-verification-windows-caption">Two windows, UTC, twelve five-minute slots each</caption>
          <thead>
            <tr>
              <th scope="col">Window</th>
              <th scope="col">From</th>
              <th scope="col">To (not included)</th>
              <th scope="col">Daily assessment used</th>
            </tr>
          </thead>
          <tbody>
            <tr data-verification-window="baseline">
              <th scope="row">Earlier (before the change)</th>
              <td>{when(plan.baseline_start)}</td>
              <td>{when(plan.baseline_end)}</td>
              <td>{plan.baseline_selection.days.map((d) => d.day).join(", ") || "none"}</td>
            </tr>
            <tr data-verification-window="later" data-verification-later-bound={binding ? "yes" : "no"}>
              <th scope="row">Later (after the change)</th>
              <td>{when(plan.later_start)}</td>
              <td>{when(plan.later_end)}</td>
              <td>
                {binding ? (
                  binding.selection.days.map((d) => d.day).join(", ")
                ) : (
                  <span data-verification-later-pending>
                    Pending: needs the daily assessment for {plan.later_selection_rule.required_days.join(", ")}
                  </span>
                )}
              </td>
            </tr>
          </tbody>
        </DataTable>
        <FactList>
          <Fact term="Change">
            <Link to={links.change(plan.change_id)} data-verification-plan-change-link>
              Open the applied change
            </Link>
          </Fact>
          <Fact term="Application record">
            <Link to={links.event(plan.applied_event_id)}>Applied event</Link>
          </Fact>
          <Fact term="Effective from">{when(plan.effective_from)}</Fact>
        </FactList>
        <DigDeeper name="plan">
          <FactList>
            <Fact term="Plan ID">
              <Ref value={plan.plan_id} />
            </Fact>
            <Fact term="Plan version">
              <Ref value={plan.plan_version} attr="data-verification-plan-version" />
            </Fact>
            <Fact term="Rule">
              <Ref value={plan.rule_id} />
            </Fact>
            <Fact term="Plan digest">
              <Ref value={plan.plan_sha256} />
            </Fact>
            <Fact term="Earlier Foundation version">
              <Ref value={plan.old_foundation_revision_id} attr="data-verification-old-foundation" />
            </Fact>
            <Fact term="New Foundation version">
              <Ref value={plan.new_foundation_revision_id} attr="data-verification-new-foundation" />
            </Fact>
            <Fact term="Applied event">
              <Ref value={plan.applied_event_id} />
            </Fact>
            <Fact term="Battery">
              <Ref value={plan.battery_asset_id} />
            </Fact>
            <Fact term="Assessment model">
              <Ref value={plan.basis.model_version} />
            </Fact>
            <Fact term="Clock">{plan.basis.clock_basis.startsWith("UTC") ? "UTC, attested per day" : "See basis"}</Fact>
          </FactList>
          <DaySelections name="baseline" days={plan.baseline_selection.days} />
          {binding ? <DaySelections name="later" days={binding.selection.days} bindingId={binding.id} /> : null}
          <p className="action-note">
            Signal assignment versions (earlier window):{" "}
            {plan.basis.baseline_bindings.binding_set_revision_ids.map((id) => (
              <Ref key={id} value={id} />
            ))}
          </p>
        </DigDeeper>
      </Panel>
    </>
  );
}

function DaySelections({ name, days, bindingId }: { name: string; days: VerificationPlan["baseline_selection"]["days"]; bindingId?: string }) {
  return (
    <div data-verification-day-selection={name}>
      <p className="action-note">
        {name === "baseline" ? "Earlier window" : "Later window"} daily assessment
        {bindingId ? (
          <>
            {" "}
            (selection <Ref value={bindingId} />)
          </>
        ) : null}
        :
      </p>
      <ul className="action-list">
        {days.map((d) => (
          <li key={d.day}>
            {d.day}: <Ref value={d.run_id} />, window versions{" "}
            {d.window_revision_ids.map((id) => (
              <Ref key={id} value={id} />
            ))}
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---------------------------------------------------------------- Evidence view */

function EvidenceBodyView({ body, links, pinnedOutcome }: { body: EvidenceBody; links: VerificationLinks; pinnedOutcome: OutcomeRecord | null }) {
  const pair = body.source_resolution.pair;
  const targetLater = body.target.later as { candidate_seconds?: number | null; state: string };
  return (
    <>
      <Panel heading="Evidence requirements" headingId="site-verification-evidence-heading">
        <p className="action-note" data-verification-knowledge-cutoff={body.knowledge_cutoff}>
          Readings as accepted by {when(body.knowledge_cutoff)}
          {pinnedOutcome ? ", when the selected outcome was recorded" : ""}.
        </p>
        <DataTable labelledBy="site-verification-requirements-caption">
          <caption id="site-verification-requirements-caption">Evidence set and status</caption>
          <thead>
            <tr>
              <th scope="col">Evidence set</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            <RequirementRow name="baseline" label="Earlier window readings" ok={body.windows.baseline.complete} detail={`${body.windows.baseline.slots.filter((s) => s.complete).length}/${body.windows.baseline.slots.length} slots complete`} />
            <RequirementRow name="later" label="Later window readings" ok={body.windows.later.complete} detail={`${body.windows.later.slots.filter((s) => s.complete).length}/${body.windows.later.slots.length} slots complete`} />
            <RequirementRow name="comparability" label="Comparable windows" ok={body.comparability.state === "PASS" ? true : body.comparability.state === "FAIL" ? false : null} detail={checkWord(body.comparability.state)} />
            <RequirementRow name="source" label="Coherent source per window" ok={pair.state === "PASS" ? true : pair.state === "FAIL" ? false : null} detail={`${sourceWords(body.source_resolution.baseline.state)} / ${sourceWords(body.source_resolution.later.state)}`} />
            <RequirementRow
              name="target"
              label="Avoidable generator time, both windows"
              ok={body.target.met}
              detail={`${minutes(body.target.baseline.candidate_seconds) ?? "unknown"} to ${
                targetLater.state === "NOT_BOUND" ? "pending (later selection not appended yet)" : minutes(targetLater.candidate_seconds) ?? "unknown"
              }`}
            />
          </tbody>
        </DataTable>
        {[...body.target.baseline.reasons, ...((body.target.later as { reasons?: string[] }).reasons ?? [])].length > 0 ? (
          <ul className="action-list" data-verification-target-reasons>
            {[...body.target.baseline.reasons, ...((body.target.later as { reasons?: string[] }).reasons ?? [])].map((reason) => (
              <li key={reason} data-verification-problem={problemCode(reason)}>
                Avoidable generator time: {problemWords(reason)}
              </li>
            ))}
          </ul>
        ) : null}
        <ComparabilityTable body={body} />
      </Panel>
      <WindowPanel name="baseline" window={body.windows.baseline} source={body.source_resolution.baseline} links={links} />
      <WindowPanel name="later" window={body.windows.later} source={body.source_resolution.later} links={links} />
    </>
  );
}

function RequirementRow({ name, label, ok, detail }: { name: string; label: string; ok: boolean | null; detail: string }) {
  const tone: Tone = ok === true ? "pass" : ok === false ? "fail" : "unknown";
  return (
    <tr data-verification-requirement={name} data-verification-requirement-ok={ok === null ? "unknown" : ok ? "yes" : "no"}>
      <th scope="row">{label}</th>
      <td>
        <Chip tone={tone}>{ok === true ? "Available" : ok === false ? "Incomplete" : "Not established"}</Chip> {detail}
      </td>
    </tr>
  );
}

const CHECK_NAMES: Record<string, string> = {
  feeder_demand_energy: "Site demand energy",
  pv_available_energy: "Available solar energy",
  initial_soc: "Battery charge at the start",
};

function ComparabilityTable({ body }: { body: EvidenceBody }) {
  return (
    <DataTable labelledBy="site-verification-comparability-caption">
      <caption id="site-verification-comparability-caption">Comparability against the frozen bands</caption>
      <thead>
        <tr>
          <th scope="col">Measure</th>
          <th scope="col">Earlier</th>
          <th scope="col">Later</th>
          <th scope="col">Difference</th>
          <th scope="col">Allowed</th>
          <th scope="col">Result</th>
        </tr>
      </thead>
      <tbody>
        {body.comparability.checks.map((c) => (
          <tr key={c.metric} data-verification-comparability={c.metric} data-verification-comparability-state={c.state}>
            <th scope="row">{CHECK_NAMES[c.metric] ?? "Unrecognised measure"}</th>
            <td>{decimal(c.baseline) ?? "unknown"} {c.unit}</td>
            <td>{decimal(c.later) ?? "unknown"} {c.unit}</td>
            <td>{decimal(c.difference) ?? "unknown"}</td>
            <td>up to {decimal(c.threshold) ?? "unknown"} {c.unit}</td>
            <td>
              <Chip tone={checkTone(c.state)}>{checkWord(c.state)}</Chip>
            </td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
}

function powerCell(cell: PowerCell | undefined): { text: string; state: string } {
  if (!cell) return { text: "not required", state: "NONE" };
  if (cell.state === "COVERED") return { text: `${decimal(cell.kwh) ?? "?"} kWh`, state: cell.state };
  return { text: cell.problems.length > 0 ? problemWords(cell.problems[0]) : cellWord(cell.state), state: cell.state };
}

function pointCell(cell: PointCell | undefined, suffix = ""): { text: string; state: string } {
  if (!cell) return { text: "not required", state: "NONE" };
  if (cell.state === "KNOWN") return { text: `${decimal(cell.value) ?? cell.value}${suffix}`, state: cell.state };
  return { text: cell.problems.length > 0 ? problemWords(cell.problems[0]) : cellWord(cell.state), state: cell.state };
}

function demand(slot: Slot): { text: string; state: string } {
  const cells = Object.values(slot.feeder_demand ?? {});
  if (cells.length === 0) return { text: "No demand point assigned", state: "MISSING" };
  const bad = cells.find((c) => c.state !== "COVERED");
  if (bad) return { text: bad.problems.length > 0 ? problemWords(bad.problems[0]) : cellWord(bad.state), state: bad.state };
  return { text: `${decimal(slot.feeder_demand_kwh) ?? "?"} kWh`, state: "COVERED" };
}

function slotIds(slot: Slot): string[] {
  const ids: string[] = [];
  for (const c of Object.values(slot.feeder_demand ?? {})) ids.push(...c.evidence_ids);
  for (const key of ["generator_power", "pcs_discharge_capability", "pv_available_power", "critical_load_requested_power", "critical_load_delivered_power", "generator_state", "soc_start"] as const) {
    const cell = slot[key];
    if (cell) ids.push(...cell.evidence_ids);
  }
  return ids;
}

function WindowPanel({ name, window, source, links }: { name: "baseline" | "later"; window: EvidenceWindow; source: SourceSide; links: VerificationLinks }) {
  const title = name === "baseline" ? "Earlier window (before the change)" : "Later window (after the change)";
  const problems = [...window.problems, ...window.slots.flatMap(slotProblems)];
  const terminal = pointCell(window.terminal_soc_sample ?? undefined, "%");
  return (
    <Panel heading={title} headingId={`site-verification-window-${name}-heading`}>
      <div data-verification-evidence-window={name} data-verification-window-complete={window.complete ? "yes" : "no"}>
        <p className="action-note">{windowBounds(window.window_start, window.window_end)}</p>
        <p className="action-status">
          <span className="verify-strip__term">Source</span>
          <span data-verification-window-source={source.state}>{sourceWords(source.state)}</span>
        </p>
        <div className="verify-cards">
          <Card label="Site demand energy" value={kwh(window.feeder_demand_kwh) ?? "unknown"} note="All assigned demand points" tone="waiting" name={`${name}-demand`} />
          <Card label="Available solar energy" value={kwh(window.pv_available_kwh) ?? "unknown"} note="Over the window" tone="waiting" name={`${name}-solar`} />
          <Card label="Critical demand not served" value={kwh(window.unserved_critical_kwh) ?? "unknown"} note="Requested minus delivered" tone="waiting" name={`${name}-unserved`} />
          <Card label="Battery charge, start to end" value={`${pct(window.initial_soc) ?? "unknown"} to ${pct(window.terminal_soc) ?? "unknown"}`} note={`End sample: ${terminal.text}`} tone="waiting" name={`${name}-charge`} />
        </div>
        {problems.length > 0 ? (
          <ul className="action-list" data-verification-window-problems={name}>
            {problems.slice(0, 12).map((p, index) => (
              <li key={index} data-verification-problem={problemCode(p)}>
                {problemWords(p)}
              </li>
            ))}
            {problems.length > 12 ? <li>and {problems.length - 12} more</li> : null}
          </ul>
        ) : (
          <p className="action-note" data-verification-window-problems="none">
            No gaps, conflicts or missing samples.
          </p>
        )}
        <DataTable labelledBy={`site-verification-slots-${name}-caption`}>
          <caption id={`site-verification-slots-${name}-caption`}>Five-minute slots (UTC, end not included)</caption>
          <thead>
            <tr>
              <th scope="col">Slot</th>
              <th scope="col">Site demand</th>
              <th scope="col">Solar available</th>
              <th scope="col">Critical requested</th>
              <th scope="col">Critical delivered</th>
              <th scope="col">Generator</th>
              <th scope="col">Battery charge</th>
              <th scope="col">Reserve</th>
              <th scope="col">Below reserve</th>
              <th scope="col">Readings</th>
            </tr>
          </thead>
          <tbody>
            {window.slots.map((slot) => {
              const cells = [
                demand(slot),
                powerCell(slot.pv_available_power),
                powerCell(slot.critical_load_requested_power),
                powerCell(slot.critical_load_delivered_power),
                pointCell(slot.generator_state),
                pointCell(slot.soc_start, "%"),
                slot.reserve?.state === "KNOWN"
                  ? { text: `${decimal(slot.reserve.value)}%`, state: "KNOWN" }
                  : { text: slot.reserve && slot.reserve.problems.length > 0 ? problemWords(slot.reserve.problems[0]) : "Unknown", state: "UNKNOWN" },
              ];
              return (
                <tr key={slot.slot_start} data-verification-slot={slot.slot_start} data-verification-slot-complete={slot.complete ? "yes" : "no"}>
                  <th scope="row">{slot.slot_start.slice(11, 16)}</th>
                  {cells.map((cell, index) => (
                    <td key={index} data-verification-cell-state={cell.state}>
                      {cell.text}
                    </td>
                  ))}
                  <td>{slot.below_reserve_seconds === null ? "unknown" : slot.below_reserve_seconds > 0 ? "Yes (sampled)" : "No"}</td>
                  <td>{slotIds(slot).length}</td>
                </tr>
              );
            })}
          </tbody>
        </DataTable>
        <p className="action-note">
          Below reserve is read from the battery charge sample at each slot start: a five-minute sample, not continuous
          proof. Generator state is the sample at the slot start.
        </p>
        <DigDeeper name={`evidence-${name}`}>
          <p className="action-note">Accepted readings used for this window ({window.evidence_ids.length}):</p>
          <EvidenceIds ids={window.evidence_ids} links={links} limit={200} name={name} />
          <FactList>
            <Fact term="Source state">
              <Ref value={source.state} />
            </Fact>
            <Fact term="Publications">
              {source.publication_ids.map((id) => (
                <Ref key={id} value={id} />
              ))}
            </Fact>
            <Fact term="Source classes">
              {source.source_classes.map((id) => (
                <Ref key={id} value={id} />
              ))}
            </Fact>
            {source.reasons.length > 0 ? (
              <Fact term="Source reasons">
                {source.reasons.map((id) => (
                  <Ref key={id} value={id} />
                ))}
              </Fact>
            ) : null}
            <Fact term="Power values">
              <Ref value={window.power_semantics} />
            </Fact>
            <Fact term="Reserve check">
              <Ref value={window.guardrail_basis} />
            </Fact>
          </FactList>
          {problems.length > 0 ? (
            <ul className="action-list">
              {problems.map((p, index) => (
                <li key={index}>
                  <Ref value={typeof p === "string" ? p : JSON.stringify(p)} />
                </li>
              ))}
            </ul>
          ) : null}
        </DigDeeper>
      </div>
    </Panel>
  );
}

function slotProblems(slot: Slot): unknown[] {
  const out: unknown[] = [];
  for (const c of Object.values(slot.feeder_demand ?? {})) out.push(...c.problems);
  for (const key of ["generator_power", "pcs_discharge_capability", "pv_available_power", "critical_load_requested_power", "critical_load_delivered_power", "generator_state", "soc_start"] as const) {
    const cell = slot[key];
    if (cell) out.push(...cell.problems);
  }
  if (slot.reserve) out.push(...slot.reserve.problems);
  return out;
}
