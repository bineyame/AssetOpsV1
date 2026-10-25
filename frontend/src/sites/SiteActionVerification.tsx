/**
 * S6-02b: the Action's Plan, Evidence and Verification child views
 * (`action-plan:1`, `action-evidence:1`, `verification:1-3`), under the S6-01b
 * Action root at `/sites/{site}/actions/{action}/{plan|evidence|verification}`.
 *
 * W1-F4 (D-2026-10-17-mockup-layout-spec): each view renders exactly its v69
 * panels. Plan: one "Success criteria" panel (criteria and both windows).
 * Evidence: one "Evidence requirements" panel (requirements, per-window gaps
 * and, in one closed disclosure, the five-minute readings). Verification: the
 * one-line status strip, four metric cards, then "Target and guardrails
 * evaluated together" full width and "Activity evidence" beside "Outcome
 * evidence". A page-level refusal or selector conflict is stated before the
 * panel slots, which keep their place with the gap inside.
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

import { asOfText, ChartNote, MetricHeader, outcomeWords, DataTable, Disclosure, ExactReferences, Fact, FactList, Panel, type ExactReference, type ProductTone } from "../ui";
import type { ActionBody, ActionReadResult, Refusal } from "./actionClient";
import { Ref, when } from "./actionPresentation";
import { reasonWords as sourceReasonWords } from "./sourceProvenance";
import {
  actionReadAsOf,
  evidenceVerdict,
  findMetric,
  planVerdict,
  plainLimit,
  verificationVerdict,
  VerificationMetricCards,
  type StripVerdict,
} from "./verificationCards";
import type {
  DaySelection,
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
  stateTone,
  type Tone,
  cellWord,
} from "./verificationWords";
import "./w1f4-verification.css";

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
  /** The actual current state, read separately when a view is selected by time or exact record (F1). */
  currentHistory: ActionReadResult<HistoryBody> | null;
  /** The plan the evidence belongs to (origin Finding, day selections, cohorts), read for lineage (F3). */
  evidencePlan: ActionReadResult<PlanBody> | null;
  /** The verification view's plan selection has no outcome yet. */
  noOutcomeForPlan: boolean;
}

const EMPTY: Reads = { outcome: null, history: null, plan: null, evidence: null, conflict: null, currentHistory: null, evidencePlan: null, noOutcomeForPlan: false };

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
    const explicitSel = outcomeId !== null || planRevisionId !== null || recordedAt !== null || eventId !== null;
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
        if (explicitSel) void client.getHistory(siteId, actionId).then((currentHistory) => set({ currentHistory }));
        const chosen = pinned ? pinned.plan_id : planRevisionId;
        set({ plan: await client.getPlan(siteId, actionId, { id: chosen, recordedAt: chosen ? null : cutoff }) });
      } else {
        if (explicitSel) void client.getHistory(siteId, actionId).then((currentHistory) => set({ currentHistory }));
        const read = pinned
          ? await client.getEvidence(siteId, actionId, { id: null, recordedAt: pinned.recorded_at })
          : await client.getEvidence(siteId, actionId, { id: planRevisionId, recordedAt: planRevisionId ? null : cutoff });
        set({ evidence: read });
        if (read.status === "loaded") {
          void client.getPlan(siteId, actionId, { id: read.value.plan_id, recordedAt: null }).then((evidencePlan) => set({ evidencePlan }));
        }
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
  const blocked = reads.conflict !== null;

  const refusals: Refusal[] = [];
  /** The loaded value of a needed read; a refusal is collected for the page-level statement. */
  const value = <T,>(read: ActionReadResult<T> | null, needed: boolean): T | null => {
    if (!needed || blocked || read === null) return null;
    if (read.status !== "loaded") {
      refusals.push(read);
      return null;
    }
    return read.value;
  };
  /** The in-panel gap for a read that has not loaded: a conflict, a refusal or a read in flight. */
  const gapOf = <T,>(read: ActionReadResult<T> | null, loading: string, subject: string): PanelGap | null => {
    if (blocked) return { kind: "conflict", text: "Nothing is shown here: the address names selections that conflict." };
    if (read === null) return { kind: "loading", text: loading };
    if (read.status !== "loaded") return { kind: "refused", text: `The ${subject} could not be read, so nothing is shown here.` };
    return null;
  };
  const outcomeNeeded = view === "verification" ? !reads.noOutcomeForPlan : outcomeId !== null;
  const outcome = value(reads.outcome, outcomeNeeded);
  const history = value(reads.history, view === "verification");
  const plan = value(reads.plan, view === "plan" || reads.noOutcomeForPlan);
  const evidence = value(reads.evidence, view === "evidence");
  const current: VerificationState | null = blocked
    ? null
    : (outcome?.current_state ?? plan?.verification_state ?? evidence?.verification_state ?? history?.current_state ?? null);

  const actualRead = reads.currentHistory;
  const actual: VerificationState | null = history?.current_state ?? (actualRead && actualRead.status === "loaded" ? actualRead.value.current_state : null);
  const actualMissing = view !== "verification" && explicit && actual === null && actualRead !== null;
  const evidenceLineage = view === "evidence" && reads.evidencePlan && reads.evidencePlan.status === "loaded" ? reads.evidencePlan.value : null;

  // The shown outcome record: a historical selection, or the record that is the current state.
  const record = outcome?.outcome ?? null;
  const historicalOutcome = outcome !== null && (outcome.historical_label !== undefined || explicit);
  const showRecord = record !== null && outcome !== null && (historicalOutcome || (outcome.current_state.state === record.outcome && outcome.current_state.outcome_id === record.outcome_id));
  const shown = showRecord ? record : null;

  let verdict: StripVerdict | null = null;
  let references: ExactReference[] = [];
  let next: ReactNode = null;
  if (current !== null && view === "verification" && outcome !== null) {
    verdict = verificationVerdict(outcome, shown, historicalOutcome, body);
    references = [
      { label: "Outcome reference", value: shown?.outcome_id ?? current.outcome_id ?? null },
      { label: "Plan reference", value: shown?.plan_id ?? current.plan_id ?? null },
      { label: "Outcome code", value: shown?.outcome ?? null },
      { label: "Current state code", value: current.state },
      { label: "Reason codes", value: (shown?.reasons ?? current.reasons).join(", ") || null },
    ];
  } else if (current !== null && view === "verification") {
    // No outcome read (the selected plan has none, or the read failed): the read state only, never a result.
    verdict = { words: outcomeWords(current.state, current.reasons, null), scope: "This Action's measured trial", asOf: actionReadAsOf(body) };
    references = [{ label: "Current state code", value: current.state }];
  } else if (current !== null && view === "plan" && plan !== null) {
    verdict = planVerdict(plan, body);
    references = [
      { label: "Plan reference", value: plan.plan?.plan_id ?? null },
      { label: "Plan version", value: plan.plan?.plan_version ?? null },
      { label: "Change record", value: plan.plan?.change_id ?? null },
      { label: "Current state code", value: plan.verification_state.state },
    ];
    next = (
      <Link to={links.view("verification", {})} data-plan-verification-link>
        Open Verification →
      </Link>
    );
  } else if (current !== null && view === "evidence" && evidence !== null) {
    verdict = evidenceVerdict(evidence);
    references = [
      { label: "Plan reference", value: evidence.plan_id },
      { label: "Reading cutoff", value: evidence.knowledge_cutoff },
      { label: "Source of both windows", value: evidence.source_resolution.pair.source_class },
    ];
    next = (
      <Link to={links.view("verification", {})} data-evidence-verification-link>
        Open Verification →
      </Link>
    );
  }

  return (
    <div className="site-verification w1f4-verification" data-verification-view={view} data-verification-explicit={explicit ? "yes" : "no"}>
      {blocked ? (
        <div className="page-refusal" role="status" data-page-refusal="selector-conflict">
          <p className="page-refusal__title">
            <strong>Conflicting selection</strong>
          </p>
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
        </div>
      ) : null}
      {refusals.length > 0 ? (
        <div className="page-refusal" role="status" data-page-refusal="refused">
          <p className="page-refusal__title">
            <strong>{refusalTitle(refusals[0])}</strong>
          </p>
          {refusals.map((refusal, index) => (
            <RefusalLines key={`${refusal.code}-${index}`} refusal={refusal} latestLink={latestLink} />
          ))}
        </div>
      ) : null}
      {current !== null && verdict !== null ? (
        <StateStrip
          verdict={verdict}
          current={current}
          explicit={explicit}
          selection={selection}
          eventCutoff={eventCutoff}
          view={view}
          links={links}
          actual={actual}
          actualMissing={actualMissing}
          references={references}
          next={next}
        />
      ) : null}
      {view === "verification" ? (
        <>
          <VerificationSummaryRow
            gapped={blocked || refusals.length > 0}
            stateWord={verdict?.words.label ?? null}
            source={<Link to={links.finding(body.origin.finding_id, body.origin.finding_revision_id)}>Source Finding version</Link>}
            criterion={
              metric(outcome?.metrics ?? [], "target_reduction") || plan !== null
                ? "At least 25% lower"
                : current?.plan_id || shown?.plan_id
                  ? "Not available"
                  : null
            }
          />
          <VerificationMetricCards outcome={outcome} record={shown} gap={blocked || refusals.length > 0 ? "Not available" : "Pending"} conflict={blocked} />
          <TargetPanel
            outcome={outcome}
            record={shown}
            latest={record}
            historical={historicalOutcome}
            history={history}
            links={links}
            gap={reads.noOutcomeForPlan ? gapOf(reads.plan, VERIFICATION_LOADING.plan, "verification plan") : gapOf(reads.outcome, VERIFICATION_LOADING.outcome, "verification outcome")}
            noOutcomeForPlan={reads.noOutcomeForPlan && plan !== null ? planRevisionId ?? "" : null}
          />
          <div className="panel-pair">
            {/* post-W6 W1-b Q34 / R228 (pre-flight ruling 8): each panel states a history gap only when it differs
                from that panel's main gap, so a selector conflict is printed once per panel. */}
            <ActivityPanel
              body={body}
              history={history}
              links={links}
              gap={blocked ? gapOf(null, "", "") : null}
              historyGap={distinctGap(blocked ? gapOf(null, "", "") : null, gapOf(reads.history, VERIFICATION_LOADING.history, "verification history"))}
            />
            <OutcomeEvidencePanel
              outcome={outcome}
              record={shown}
              history={history}
              links={links}
              gap={reads.noOutcomeForPlan ? null : gapOf(reads.outcome, VERIFICATION_LOADING.outcome, "verification outcome")}
              historyGap={distinctGap(
                reads.noOutcomeForPlan ? null : gapOf(reads.outcome, VERIFICATION_LOADING.outcome, "verification outcome"),
                gapOf(reads.history, VERIFICATION_LOADING.history, "verification history"),
              )}
            />
          </div>
        </>
      ) : null}
      {view === "plan" ? (
        <PlanPanel
          body={plan}
          action={body}
          links={links}
          explicit={explicit}
          gap={plan === null ? gapOf(outcomeId !== null && reads.outcome?.status !== "loaded" ? reads.outcome : reads.plan, outcomeId !== null && reads.outcome === null ? VERIFICATION_LOADING.outcome : VERIFICATION_LOADING.plan, "verification plan") : null}
        />
      ) : null}
      {view === "evidence" ? (
        <EvidencePanel
          body={evidence}
          links={links}
          pinnedOutcome={outcome?.outcome ?? null}
          plan={evidenceLineage}
          gap={evidence === null ? gapOf(outcomeId !== null && reads.outcome?.status !== "loaded" ? reads.outcome : reads.evidence, outcomeId !== null && reads.outcome === null ? VERIFICATION_LOADING.outcome : VERIFICATION_LOADING.evidence, "verification evidence") : null}
        />
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------- shared parts */

interface PanelGap {
  kind: "conflict" | "loading" | "refused";
  text: string;
}

/** A read-state gap inside its v69 panel slot. */
function Gap({ gap }: { gap: PanelGap }) {
  return (
    <p className="v69-chart-note w1f4-verification-gap" data-panel-gap={gap.kind}>
      {gap.text}
    </p>
  );
}

function refusalTitle(refusal: Refusal): string {
  if (refusal.http === null) return "Verification unavailable";
  if (refusal.http === 401) return "Sign-in required";
  if (refusal.http === 403) return "No access";
  if (refusal.http === 404) return "Verification record not found";
  return "Verification read refused";
}

/** One refused verification read, stated at page level (the panels keep their slots below). */
function RefusalLines({ refusal, latestLink }: { refusal: Refusal; latestLink: ReactNode }) {
  const text =
    refusal.http === null
      ? "The server could not be reached."
      : refusal.http === 401
        ? "Sign in to read this site's Actions."
        : refusal.http === 403
          ? "Your account has no access to this."
          : refusal.http === 404
            ? "This site has no such verification record."
            : `The verification record could not be read (HTTP ${refusal.http}).`;
  return (
    <>
      <p data-verification-read="refused" data-verification-http={refusal.http ?? "none"} data-verification-code={refusal.code ?? ""}>
        {text}
        {refusal.code ? (
          <>
            {" "}
            Code: <Ref value={refusal.code} />.
          </>
        ) : null}
        {refusal.message ? <> Reason given: {refusal.message}</> : null}
      </p>
      {refusal.code === CONFLICT ? <p data-verification-selector-conflict={CONFLICT}>Nothing was chosen for you. {latestLink}</p> : null}
      {refusal.http === 404 ? <p>{latestLink}</p> : null}
    </>
  );
}

function Chip({ tone, children, attr }: { tone: Tone; children: ReactNode; attr?: Record<string, string> }) {
  return (
    <span className={`verify-chip verify-chip--${tone}`} {...(attr ?? {})}>
      {children}
    </span>
  );
}

function productChip(tone: ProductTone): Tone {
  return tone === "positive" ? "pass" : tone === "problem" ? "fail" : tone === "limited" ? "unknown" : "waiting";
}

/** The mock's `mheader` on Verification: Owner, Due / SLA, State, Source, Success criterion; gaps are words. */
function VerificationSummaryRow({ gapped, stateWord, source, criterion }: { gapped: boolean; stateWord: string | null; source: ReactNode; criterion: string | null }) {
  const gap = "Not available";
  return (
    <MetricHeader
      label="Verification summary"
      data={{ "data-verification-summary": gapped ? "gap" : "read" }}
      cells={[
        ["Owner", "Not recorded", "owner"],
        ["Due / SLA", "Not set", "due"],
        ["State", gapped ? gap : (stateWord ?? "Pending"), "state"],
        ["Source", gapped ? gap : source, "source"],
        ["Success criterion", gapped ? gap : (criterion ?? "No success criteria recorded"), "criterion"],
      ]}
    />
  );
}

/**
 * The fixed policy-trial limitation, on Plan, Evidence and Verification. The mock has no closing
 * callout, but this is a material limit, so it stays visible as a small note line.
 */
export function TrialNotice() {
  return (
    <p className="v69-chart-note w1f4-verification-notice" data-verification-trial-label="POLICY_TRIAL_NO_SAVINGS">
      Policy trial on Lab or authored test data: no proof of cause, no savings or realized benefit; a resolution is never permanent.
    </p>
  );
}

/**
 * The mock's one-line status strip: the verdict leads, then the read state as a
 * second badge, a Historical label when a selection is explicit (with the actual
 * current state beside it), the state sentence, scope and "as of" bound, and the
 * exact references in a small closed disclosure.
 */
function StateStrip({
  verdict,
  current,
  explicit,
  selection,
  eventCutoff,
  view,
  links,
  actual,
  actualMissing,
  references,
  next,
}: {
  verdict: StripVerdict;
  actual: VerificationState | null;
  actualMissing: boolean;
  current: VerificationState;
  explicit: boolean;
  selection: VerificationSelection;
  eventCutoff: string | null;
  view: VerificationView;
  links: VerificationLinks;
  references: ExactReference[];
  next: ReactNode;
}) {
  const atCutoff = current.historical === true || (explicit && view !== "verification");
  const showActual = explicit && view !== "verification";
  return (
    <section
      className="status-strip status-strip--line w1f4-verification-strip"
      aria-label="Verification state"
      data-verification-current-state={current.state}
      data-product-status={verdict.words.tone}
    >
      <span className="status-strip__lead">
        <span className={`verify-chip verify-chip--${productChip(verdict.words.tone)}`} data-product-status-label>
          {verdict.words.label}
        </span>
      </span>
      <span className="status-strip__item">
        <span className="verify-strip__term">{atCutoff ? "State at the selected time" : "Current state"}</span>{" "}
        <Chip tone={stateTone(current.state)} attr={{ "data-verification-state-label": stateLabel(current.state, current.reasons) }}>
          {stateLabel(current.state, current.reasons)}
        </Chip>
      </span>
      {explicit ? (
        <span className="status-strip__state status-strip__state--historical" data-verification-historical>
          <strong>Historical</strong>{" "}
          {selection.outcomeId
            ? "An exact earlier outcome is selected."
            : selection.planRevisionId
              ? "An exact plan is selected."
              : `Showing what was recorded through ${when(selection.recordedAt ?? eventCutoff)}.`}{" "}
          {showActual
            ? actual !== null
              ? "The actual current state is shown below, separately from this historical state."
              : actualMissing
                ? "The actual current state could not be read here, so do not treat this historical state as current."
                : "The actual current state is being read; until it appears, do not treat this historical state as current."
            : "The current state is shown separately."}{" "}
          <Link to={links.view(view, {})}>Show the current state</Link>
        </span>
      ) : null}
      {showActual && actual !== null ? (
        <span className="status-strip__item" data-verification-actual-current={actual.state}>
          <span className="verify-strip__term">Actual current state</span>{" "}
          <Chip tone={stateTone(actual.state)} attr={{ "data-verification-actual-state-label": stateLabel(actual.state, actual.reasons) }}>
            {stateLabel(actual.state, actual.reasons)}
          </Chip>
        </span>
      ) : null}
      {showActual && actualMissing ? (
        <span className="status-strip__item" data-verification-actual-current-unavailable>
          The actual current state is not available in this view.
        </span>
      ) : null}
      <span className="status-strip__state product-status__sentence">{verdict.words.sentence}</span>
      {verdict.outcome ? (
        <span className="status-strip__item" data-product-outcome-source>
          Source: {verdict.outcome.source.label}
        </span>
      ) : null}
      <span className="status-strip__item muted">
        <span data-product-status-scope>{verdict.scope}</span>
        <span aria-hidden="true"> · </span>
        <span data-product-status-as-of>{asOfText(verdict.asOf)}</span>
      </span>
      <span className="status-strip__spacer" aria-hidden="true" />
      {next === null ? null : <span className="status-strip__action">{next}</span>}
      <ExactReferences variant="tech" name={`verification-${view}-references`} references={references} />
    </section>
  );
}

/** The read state's reasons, as one note inside the view's first panel. */
function CurrentReasons({ current }: { current: VerificationState | null | undefined }) {
  if (!current || current.reasons.length === 0 || current.state === "VERIFIED") return null;
  return (
    <ul className="v69-chart-note w1f4-verification-list" data-verification-current-reasons>
      {current.reasons.map((reason) => (
        <li key={reason}>{reasonWords(reason)}</li>
      ))}
    </ul>
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

function DigDeeper({ name, summary = "Dig deeper: identifiers and typed values", children }: { name: string; summary?: string; children: ReactNode }) {
  return (
    <Disclosure summary={summary} name={`verification-${name}`}>
      {children}
    </Disclosure>
  );
}

function windowBounds(start: string, end: string): string {
  return `${when(start)} to ${when(end)} (end not included)`;
}

/** A window on one line: "2026-10-06 08:00-09:00 UTC" when it starts and ends on the same day. */
function windowShort(start: string, end: string): string {
  const s = when(start).replace(/ UTC$/, "");
  const e = when(end).replace(/ UTC$/, "");
  return s.slice(0, 10) === e.slice(0, 10) ? `${s}\u2013${e.slice(11)} UTC` : `${s} \u2013 ${e} UTC`;
}

function text(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

/* ---------------------------------------------------------------- Verification view */

const metric = (metrics: Metric[], key: string, window = "COMPARISON") => findMetric(metrics, key, window);

/** Panel 1: the plan's target and guardrails against the shown outcome, or the pending/withdrawn gap. */
function TargetPanel({
  outcome,
  record,
  latest,
  historical,
  history,
  links,
  gap,
  noOutcomeForPlan,
}: {
  outcome: OutcomeBody | null;
  record: OutcomeRecord | null;
  latest: OutcomeRecord | null;
  historical: boolean;
  history: HistoryBody | null;
  links: VerificationLinks;
  gap: PanelGap | null;
  noOutcomeForPlan: string | null;
}) {
  const heading = "Target and guardrails evaluated together";
  const headingId = "site-verification-metrics-heading";
  if (noOutcomeForPlan !== null) {
    return (
      <Panel heading={heading} headingId={headingId}>
        <p className="v69-chart-note w1f4-verification-gap" data-panel-gap="pending" data-verification-no-outcome-for-plan={noOutcomeForPlan}>
          No outcome has been recorded for the selected plan yet. That is a waiting state, not an outcome.
        </p>
        <ChartNote>
          <Link to={links.view("plan", { planRevisionId: noOutcomeForPlan || null })}>Open the success criteria</Link>
        </ChartNote>
      </Panel>
    );
  }
  if (outcome === null) {
    return (
      <Panel heading={heading} headingId={headingId}>
        {gap ? <Gap gap={gap} /> : null}
      </Panel>
    );
  }
  const current = outcome.current_state;
  if (record === null) {
    const allOutcomes = history?.outcomes ?? [];
    const prior = allOutcomes.length > 0 ? allOutcomes[allOutcomes.length - 1] : null;
    return (
      <Panel heading={heading} headingId={headingId}>
        <p className="v69-chart-note w1f4-verification-gap" data-panel-gap="pending" data-verification-no-current-outcome={current.state}>
          {latest === null
            ? "No outcome has been recorded for this Action yet, so the target and limits are not evaluated: pending."
            : "The most recent outcome is not current, so it is not shown here as the result."}
        </p>
        <CurrentReasons current={current} />
        {prior ? (
          <p className="v69-chart-note">
            <Link to={links.view("verification", { outcomeId: prior.outcome_id })} data-verification-prior-outcome-link={prior.outcome_id}>
              Open the earlier outcome ({outcomeName(prior.outcome)}, recorded {when(prior.recorded_at)})
            </Link>{" "}
            It opens under a Historical label.
          </p>
        ) : null}
        <ChartNote>
          <Link to={links.view("plan", { planRevisionId: current.plan_id ?? null })}>Open the success criteria</Link>
        </ChartNote>
      </Panel>
    );
  }
  const metrics = outcome.metrics;
  const reasons = record.reasons;
  const label = stateLabel(record.outcome, reasons);
  const windows = (record.details?.windows ?? {}) as Record<string, Record<string, unknown>>;
  const baseline = windows.baseline ?? {};
  const laterWindow = windows.later ?? {};
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
  const guardrailFail = record.outcome === "INEFFECTIVE" && reasons.includes(GUARDRAIL_FAIL);
  return (
    <Panel heading={heading} headingId={headingId}>
      <p
        className="v69-chart-note w1f4-verification-outcome"
        data-verification-outcome={record.outcome}
        data-verification-label={label}
        data-verification-outcome-id={record.outcome_id}
        data-verification-historical-outcome={historical ? "yes" : "no"}
      >
        {historical ? <span className="verify-historical-tag">Historical</span> : null} <strong>{label}</strong> · recorded{" "}
        {when(record.recorded_at)} · outcome: {outcomeName(record.outcome)}.
        {outcome.superseded_by_outcome_id ? (
          <span data-verification-superseded-by={outcome.superseded_by_outcome_id}>
            {" "}
            A later outcome replaced this one:{" "}
            <Link to={links.view("verification", { outcomeId: outcome.superseded_by_outcome_id })}>open the later outcome</Link>.
          </span>
        ) : null}
      </p>
      <DataTable labelledBy="site-verification-metrics-caption">
        <caption id="site-verification-metrics-caption" className="visually-hidden">
          Target and limits, both windows
        </caption>
        <thead>
          <tr>
            <th scope="col">Metric</th>
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
        </tbody>
      </DataTable>
      {failed.length > 0 ? (
        <p className="v69-chart-note w1f4-verification-problem" data-verification-guardrail-fail data-product-outcome-failed-limits>
          {failed.map((m, index) => {
            const plain = plainLimit(m);
            const ids = m.evidence_ids.length > 0 ? m.evidence_ids : laterIds;
            return (
              <span key={m.metric_key} data-verification-failed-limit={m.metric_key}>
                {index > 0 ? "; " : "Failed: "}
                <strong>{plain.name}</strong> measured {plain.value} {plain.unit}, limit {plain.threshold} {plain.unit} (
                <span data-verification-evidence-count={ids.length}>
                  {ids.length} reading{ids.length === 1 ? "" : "s"}
                </span>
                )
              </span>
            );
          })}
          {guardrailFail ? (
            <>
              . {LABEL_GUARDRAIL_FAIL}: the outcome stays ineffective and new reserve trials on this battery are held.
              {reasons.includes("TARGET_MISS") ? " The target was also not met." : ""}
            </>
          ) : (
            "."
          )}
        </p>
      ) : guardrailFail ? (
        <p className="v69-chart-note w1f4-verification-gap" data-panel-gap="not-recorded" data-product-outcome-failed-limits>
          The failed limit's measured value is not in this record. {LABEL_GUARDRAIL_FAIL}: the outcome stays ineffective and
          new reserve trials on this battery are held.{reasons.includes("TARGET_MISS") ? " The target was also not met." : ""}
        </p>
      ) : null}
      {record.outcome === "INCONCLUSIVE" && unknown.length > 0 ? (
        <p className="v69-chart-note" data-verification-unknown-reasons>
          {unknown.map((reason, index) => (
            <span key={reason}>
              {index > 0 ? " " : ""}
              {reasonWords(reason)}
            </span>
          ))}
        </p>
      ) : null}
      {known.length > 0 ? (
        <p className="v69-chart-note w1f4-verification-problem" data-verification-known-failures data-product-outcome-known-failures>
          {known.map((reason, index) => (
            <span key={reason}>
              {index > 0 ? " · " : ""}
              {reasonWords(reason)}
            </span>
          ))}
        </p>
      ) : null}
      <ChartNote>
        Rule fixed in the plan before the later window was read · reserve checked at five-minute samples, not continuously
        {record.outcome === "INCONCLUSIVE" ? " · a later trial may continue under a new plan; this outcome stays readable" : ""} ·{" "}
        <Link to={links.view("plan", { planRevisionId: record.plan_id })} data-verification-criteria-link>
          Open the success criteria
        </Link>
      </ChartNote>
      <DigDeeper name="outcome">
        {failed.length > 0 ? (
          <ul className="action-list" data-verification-failed-readings>
            {failed.map((m) => (
              <li key={m.metric_key} data-verification-failed-metric={m.metric_key}>
                {plainLimit(m).name}, as read: <span data-verification-failed-value>{m.value_text ?? "unknown"}</span> {m.unit ?? ""}, limit{" "}
                <span data-verification-failed-threshold>{m.threshold_text ?? "unknown"}</span> {m.unit ?? ""}. Readings:{" "}
                <EvidenceIds ids={m.evidence_ids.length > 0 ? m.evidence_ids : laterIds} links={links} name={m.metric_key} />
              </li>
            ))}
          </ul>
        ) : null}
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
          <Fact term="Input reference">
            <Ref value={record.basis_sha256} />
          </Fact>
          <Fact term="Recorded by">
            <Ref value={record.actor_id} />
          </Fact>
        </FactList>
        <dl className="v69-key-values" aria-label="Comparability checks">
          <div>
            <dt>Earlier window</dt>
            <dd>{text(baseline.window_start) && text(baseline.window_end) ? windowBounds(text(baseline.window_start)!, text(baseline.window_end)!) : "Not recorded"}</dd>
          </div>
          <div>
            <dt>Later window</dt>
            <dd>{text(laterWindow.window_start) && text(laterWindow.window_end) ? windowBounds(text(laterWindow.window_start)!, text(laterWindow.window_end)!) : "Not recorded"}</dd>
          </div>
          <CheckRow name="feeder_demand_energy_band" before={kwh(baseline.feeder_demand_kwh)} after={kwh(laterWindow.feeder_demand_kwh)} limit="within 10%" m={metric(metrics, "feeder_demand_energy_band")} />
          <CheckRow name="pv_available_energy_band" before={kwh(baseline.pv_available_kwh)} after={kwh(laterWindow.pv_available_kwh)} limit="within 10%" m={metric(metrics, "pv_available_energy_band")} />
          <CheckRow name="initial_soc_band" before={pct(baseline.initial_soc)} after={pct(laterWindow.initial_soc)} limit="within 2 points" m={metric(metrics, "initial_soc_band")} />
          <CheckRow name="window_coverage" before={metric(metrics, "window_coverage", "BASELINE")?.value_text ?? null} after={metric(metrics, "window_coverage", "LATER")?.value_text ?? null} limit="all 12 slots" m={coverage(metrics)} />
          <CheckRow name="source_provenance" before={null} after={sourceWords(metric(metrics, "source_provenance")?.value_text)} both limit="one coherent source per window" m={metric(metrics, "source_provenance")} />
        </dl>
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
                <td>{m.value_text === null ? "unknown" : <Ref value={m.value_text} />}</td>
                <td>{m.threshold_text === null ? "" : <Ref value={m.threshold_text} />}</td>
                <td>{m.unit === null ? "" : <Ref value={m.unit} />}</td>
                <td>{checkWord(m.state)}</td>
                <td>{m.evidence_ids.length}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </DigDeeper>
    </Panel>
  );
}

function coverage(metrics: Metric[]): Metric | null {
  const both = metrics.filter((m) => m.metric_key === "window_coverage");
  if (both.length === 0) return null;
  const state = both.some((m) => m.state === "FAIL") ? "FAIL" : both.every((m) => m.state === "PASS") ? "PASS" : "UNKNOWN";
  return { ...both[0], state };
}

function kwh(value: unknown): string | null {
  const n = decimal(typeof value === "string" ? value : value == null ? null : String(value));
  return n === null ? null : `${n} kWh`;
}

function pct(value: unknown): string | null {
  const n = decimal(typeof value === "string" ? value : value == null ? null : String(value));
  return n === null ? null : `${n}%`;
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

function applicationWord(application: string): string {
  return application === "APPLIED" ? "Applied" : application === "PENDING" ? "Not applied yet" : "Not recognised";
}

/** Panel 2: what was done. Accepted and applied Action events; activity alone never proves the result. */
function ActivityPanel({
  body,
  history,
  links,
  gap,
  historyGap,
}: {
  body: ActionBody;
  history: HistoryBody | null;
  links: VerificationLinks;
  gap: PanelGap | null;
  historyGap: PanelGap | null;
}) {
  const heading = "Activity evidence";
  const headingId = "site-verification-activity-heading";
  if (gap !== null) {
    return (
      <Panel heading={heading} headingId={headingId}>
        <Gap gap={gap} />
      </Panel>
    );
  }
  const change = body.change;
  const events = history?.resolution_events ?? [];
  const latestFinding = body.latest_finding_revision;
  return (
    <Panel heading={heading} headingId={headingId}>
      <dl className="v69-key-values" aria-label="Activity evidence">
        <div data-key-value="change">
          <dt>Policy application record</dt>
          <dd>
            {change ? (
              <Link to={links.change(change.change_id)} data-verification-change-link>
                Battery reserve {change.old_value}
                {change.unit} to {change.new_value}
                {change.unit}
              </Link>
            ) : (
              <span data-panel-gap="not-applied">Not applied yet</span>
            )}
          </dd>
        </div>
        <div data-key-value="applied">
          <dt>Change status</dt>
          <dd>
            {applicationWord(body.state.application)}
            {change ? (
              <>
                {" · "}
                <Link to={links.event(change.applied_event_id)} data-verification-applied-event-link>
                  applied {when(change.recorded_at)}
                </Link>
              </>
            ) : null}
          </dd>
        </div>
        <div data-key-value="resolution">
          <dt>Resolution</dt>
          <dd>
            {history === null ? (
              historyGap ? <span data-panel-gap={historyGap.kind}>{historyGap.text}</span> : null
            ) : events.length === 0 ? (
              <span data-verification-resolution="none">No resolution recorded.</span>
            ) : (
              <ul className="w1f4-verification-inline-list" data-verification-resolution-events>
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
          </dd>
        </div>
        <div data-key-value="owner">
          <dt>Owner</dt>
          <dd>
            <span data-panel-gap="not-recorded">Not recorded</span>
          </dd>
        </div>
      </dl>
      <p className="v69-chart-note">
        Completed work is evidence of activity, not resolution.{" "}
        <span data-verification-resolved-withdrawable>A resolution can be withdrawn by later evidence; it is not permanent.</span>
        {latestFinding && !latestFinding.is_origin ? (
          <span data-verification-later-finding={latestFinding.id}>
            {" "}
            <Link to={links.finding(body.origin.finding_id, latestFinding.id)}>Finding version {latestFinding.revision_no}</Link> is a
            new episode; it does not rewrite this trial.
          </span>
        ) : null}
      </p>
    </Panel>
  );
}

/** One comparability check of the shown outcome, as a key-value row. */
function CheckRow({ name, before, after, limit, m, both = false }: { name: string; before: string | null; after: string | null; limit: string; m: Metric | null; both?: boolean }) {
  return (
    <div data-verification-row={name} data-verification-row-state={m?.state ?? "MISSING"}>
      <dt>{metricName(name)}</dt>
      <dd>
        {both ? `Both windows: ${after ?? "unknown"}` : `${before ?? "unknown"} → ${after ?? "unknown"}`} · {limit}{" "}
        <Chip tone={m ? checkTone(m.state) : "unknown"}>{m ? checkWord(m.state) : "Not evaluated"}</Chip>
      </dd>
    </div>
  );
}

/** Panel 3: the earlier and later source windows, their comparability and the analytic outcome history. */
function OutcomeEvidencePanel({
  outcome,
  record,
  history,
  links,
  gap,
  historyGap,
}: {
  outcome: OutcomeBody | null;
  record: OutcomeRecord | null;
  history: HistoryBody | null;
  links: VerificationLinks;
  gap: PanelGap | null;
  historyGap: PanelGap | null;
}) {
  const outcomes = history?.outcomes ?? [];
  const plans = history?.plans ?? [];
  const metrics = outcome?.metrics ?? [];
  const windows = (record?.details?.windows ?? {}) as Record<string, Record<string, unknown>>;
  const baseline = windows.baseline ?? {};
  const later = windows.later ?? {};
  const checks = record
    ? [
        metric(metrics, "feeder_demand_energy_band"),
        metric(metrics, "pv_available_energy_band"),
        metric(metrics, "initial_soc_band"),
        coverage(metrics),
        metric(metrics, "source_provenance"),
      ]
    : [];
  const comparable = checks.length > 0 && checks.every((m) => m !== null && m.state === "PASS");
  const conditionKeys = ["feeder_demand_energy_band", "pv_available_energy_band", "initial_soc_band", "window_coverage"];
  const notPassing = conditionKeys.map((key, index) => ({ key, m: checks[index] ?? null })).filter(({ m }) => m === null || m.state !== "PASS");
  const sourceCheck = checks[4] ?? null;
  const demonstration = record ? outcomeWords(record.outcome, record.reasons, record.details?.source?.source_class ?? null).demonstrationNote : null;
  const shownOutcomes = outcomes.slice(-3);
  const latestOutcomeId = outcomes.length > 0 ? outcomes[outcomes.length - 1].outcome_id : null;
  return (
    <Panel heading="Outcome evidence" headingId="site-verification-outcomes-heading">
      {gap !== null && outcome === null ? (
        <Gap gap={gap} />
      ) : record === null ? (
        <p className="v69-chart-note w1f4-verification-gap" data-panel-gap="pending" data-verification-comparison="none">
          No comparison of an earlier and a later window is recorded as the current result, so the outcome is pending.
        </p>
      ) : (
        <dl className="v69-key-values" aria-label="Compared windows">
          <div data-key-value="baseline-window">
            <dt>Earlier window</dt>
            <dd>{text(baseline.window_start) && text(baseline.window_end) ? windowShort(text(baseline.window_start)!, text(baseline.window_end)!) : "Not recorded"}</dd>
          </div>
          <div data-key-value="later-window">
            <dt>Later window</dt>
            <dd>{text(later.window_start) && text(later.window_end) ? windowShort(text(later.window_start)!, text(later.window_end)!) : "Not recorded"}</dd>
          </div>
          <div data-key-value="comparability">
            <dt>Comparable conditions</dt>
            <dd data-verification-comparison={comparable ? "comparable" : "not-established"}>
              {notPassing.length === 0 ? (
                <>
                  All {conditionKeys.length} checks <Chip tone="pass">Pass</Chip>
                </>
              ) : (
                <span className="w1f4-verification-problem">
                  {notPassing.map(({ key, m }) => `${metricName(key)}: ${m ? checkWord(m.state) : "Not evaluated"}`).join("; ")}; so the result is inconclusive
                </span>
              )}
            </dd>
          </div>
          <div data-key-value="source">
            <dt>Source</dt>
            <dd>
              {sourceWords(metric(metrics, "source_provenance")?.value_text)}{" "}
              <Chip tone={sourceCheck ? checkTone(sourceCheck.state) : "unknown"}>{sourceCheck ? checkWord(sourceCheck.state) : "Not evaluated"}</Chip>
            </dd>
          </div>
        </dl>
      )}
      <p className="v69-chart-note">
        {history === null && historyGap ? (
          <span className="w1f4-verification-gap" data-panel-gap={historyGap.kind}>
            {historyGap.text}{" "}
          </span>
        ) : null}
        {history !== null && outcomes.length === 0 ? <span data-verification-outcomes="none">No outcome recorded yet. </span> : null}
        <Link className="w1f4-verification-evidence-link" to={links.view("evidence", { outcomeId: record?.outcome_id ?? null })} data-verification-evidence-link>
          {record ? "Inspect the evidence for this outcome" : "Inspect the evidence"} →
        </Link>
      </p>
      {history !== null && outcomes.length > 0 ? (
        <DigDeeper name="attempts" summary="Earlier outcomes and plans">
          <p className="v69-chart-note">
          <span data-verification-outcomes>
            Attempts:{" "}
            {shownOutcomes.map((o, index) => (
              <span key={o.outcome_id} data-verification-outcome-item={o.outcome_id}>
                {index > 0 ? " · " : ""}
                <Link to={links.view("verification", { outcomeId: o.outcome_id })} title={stateLabel(o.outcome, o.reasons)}>
                  {outcomeName(o.outcome)}
                </Link>{" "}
                {when(o.recorded_at).slice(0, 10)} ({o.outcome_id === latestOutcomeId ? "most recent" : "replaced later"}
                {o.outcome_id === record?.outcome_id ? ", shown" : ""})
              </span>
            ))}
            {outcomes.length > shownOutcomes.length ? ` and ${outcomes.length - shownOutcomes.length} earlier` : ""}
            {plans.length > 0 ? (
              <>
                {" "}
                · each keeps its own plan:{" "}
                {plans.map((p, index) => (
                  <span key={p.plan_id}>
                    {index > 0 ? ", " : ""}
                    <Link to={links.view("plan", { planRevisionId: p.plan_id })} data-verification-plan-link={p.plan_id}>
                      plan {index + 1}
                    </Link>
                  </span>
                ))}
              </>
            ) : null}
          </span>
          </p>
        </DigDeeper>
      ) : null}
      {demonstration ? (
        <p className="v69-chart-note w1f4-verification-notice" data-verification-trial-label="POLICY_TRIAL_NO_SAVINGS">
          <span data-product-outcome-demonstration>
            Policy trial on demonstration data: no proof of cause, no savings or realized benefit; a resolution is never permanent.
          </span>
        </p>
      ) : (
        <TrialNotice />
      )}
    </Panel>
  );
}

/* ---------------------------------------------------------------- Plan view */

function PlanPanel({ body, action, links, explicit, gap }: { body: PlanBody | null; action: ActionBody; links: VerificationLinks; explicit: boolean; gap: PanelGap | null }) {
  const heading = "Success criteria";
  const headingId = "site-verification-plan-heading";
  if (body === null) {
    return (
      <Panel heading={heading} headingId={headingId}>
        {gap ? <Gap gap={gap} /> : null}
        <TrialNotice />
      </Panel>
    );
  }
  const plan = body.plan;
  if (plan === null) {
    return (
      <Panel heading={heading} headingId={headingId}>
        <p className="v69-chart-note w1f4-verification-gap" data-panel-gap="no-plan" data-verification-plan="none">
          No success criteria recorded. No verification plan exists{explicit ? " at the selected time" : ""}.{" "}
          {action.change === null
            ? "The change has not been applied yet; a plan is frozen only after it is applied."
            : "The change is applied; the plan has not been frozen yet."}
        </p>
        <CurrentReasons current={body.verification_state} />
        <TrialNotice />
      </Panel>
    );
  }
  const binding = body.selection_bindings[body.selection_bindings.length - 1] ?? null;
  const [num, den] = plan.target.ratio;
  return (
    <Panel heading={heading} headingId={headingId} className="w1f4-verification-plan">
      <p className="v69-chart-note w1f4-verification-lede" data-verification-plan-id={plan.plan_id} data-verification-plan-current={body.is_current_plan ? "yes" : "no"}>
        Fixed {when(plan.recorded_at)}, before the later window was read ·{" "}
        {body.is_current_plan ? "the current plan" : "a later plan replaced this one"}
        {plan.supersedes_plan_id ? (
          <>
            {" "}
            ·{" "}
            <Link to={links.view("plan", { planRevisionId: plan.supersedes_plan_id })} data-verification-supersedes-link>
              open the earlier plan
            </Link>
          </>
        ) : null}
        {body.superseded_by_plan_id ? (
          <>
            {" "}
            ·{" "}
            <Link to={links.view("plan", { planRevisionId: body.superseded_by_plan_id })} data-verification-superseded-plan-link>
              Open the plan that replaced it
            </Link>
          </>
        ) : null}{" "}
        ·{" "}
        <Link to={links.change(plan.change_id)} data-verification-plan-change-link>
          Open the applied change
        </Link>
      </p>
      <CurrentReasons current={body.verification_state} />
      <DataTable labelledBy="site-verification-criteria-caption">
        <caption id="site-verification-criteria-caption" className="visually-hidden">
          Criteria and windows fixed before evaluation (UTC)
        </caption>
        <thead>
          <tr>
            <th scope="col">Criterion</th>
            <th scope="col">Rule</th>
          </tr>
        </thead>
        <tbody>
          <tr data-verification-rule="target">
            <th scope="row">Avoidable generator time</th>
            <td>At least 25% lower than the earlier window&apos;s {minutes(plan.baseline_candidate_seconds) ?? "unknown"}</td>
          </tr>
          <tr data-verification-rule="service">
            <th scope="row">Service limit</th>
            <td>No more critical demand unserved than in the earlier window</td>
          </tr>
          <tr data-verification-rule="reserve">
            <th scope="row">Reserve and stored-energy limits</th>
            <td>No time below the reserve (five-minute samples); end charge at least the earlier window&apos;s</td>
          </tr>
          <tr data-verification-rule="validity">
            <th scope="row">Window validity</th>
            <td>
              Demand and solar within {Number(plan.bands.feeder_demand_energy_relative) * 100}%, starting charge within{" "}
              {plan.bands.initial_soc_points} points, all {plan.coverage.slots_per_window} slots read
            </td>
          </tr>
          <tr data-verification-rule="windows">
            <th scope="row">Windows (UTC)</th>
            <td>
              <span data-verification-window="baseline">Earlier {windowShort(plan.baseline_start, plan.baseline_end).replace(/ UTC$/, "")}</span>
              {" · "}
              <span data-verification-window="later" data-verification-later-bound={binding ? "yes" : "no"}>
                later {windowShort(plan.later_start, plan.later_end).replace(/ UTC$/, "")}
                {binding ? null : (
                  <span className="w1f4-verification-problem" data-verification-later-pending>
                    {" "}
                    · Pending: needs the daily assessment for {plan.later_selection_rule.required_days.join(", ")}
                  </span>
                )}
              </span>
            </td>
          </tr>
        </tbody>
      </DataTable>
      <DigDeeper name="plan">
        <DataTable labelledBy="site-verification-exact-criteria-caption">
          <caption id="site-verification-exact-criteria-caption">Exact rules and windows</caption>
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
              <td>Battery charge at the end of the later window is at least the earlier window&apos;s.</td>
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
            <tr>
              <th scope="row">Earlier window (before the change)</th>
              <td>
                {windowBounds(plan.baseline_start, plan.baseline_end)}; daily assessment used:{" "}
                {plan.baseline_selection.days.map((d) => d.day).join(", ") || "none"}
              </td>
            </tr>
            <tr>
              <th scope="row">Later window (after the change)</th>
              <td>
                {windowBounds(plan.later_start, plan.later_end)}; daily assessment used:{" "}
                {binding ? binding.selection.days.map((d) => d.day).join(", ") : "pending"}
              </td>
            </tr>
          </tbody>
        </DataTable>
        <p className="action-note">
          If the earlier window&apos;s energy total is zero, the later total must also be zero. Every assigned demand point
          counts toward the site total; a missing assignment fails comparability. The later window judges avoidable
          generator time against the new, lower reserve. This is an observed policy trial, not proof of cause.{" "}
          <Link to={links.event(plan.applied_event_id)}>Applied event</Link> ·
          Effective from {when(plan.effective_from)}.
        </p>
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
          <Fact term="Plan content reference">
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
      <TrialNotice />
    </Panel>
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

interface WindowLineage {
  planRead: boolean;
  originFindingRevisionId: string | null;
  assessmentRevisionIds: string[];
  days: DaySelection[];
  /** The later selection binding was not found (not appended yet, or not read). */
  bound: boolean;
}

function lineageFor(name: "baseline" | "later", body: EvidenceBody, plan: PlanBody | null): WindowLineage {
  const target = (name === "baseline" ? body.target.baseline : body.target.later) as { assessment_revision_ids?: string[] };
  const assessmentRevisionIds = target.assessment_revision_ids ?? [];
  let days: DaySelection[] = [];
  let bound = true;
  if (name === "baseline") {
    days = plan?.plan?.baseline_selection.days ?? [];
  } else {
    const bindings = (plan?.selection_bindings ?? []).filter((b) => b.window_name === "LATER" && b.recorded_at <= body.knowledge_cutoff);
    const chosen =
      bindings.find((b) => b.id === body.target.later_selection_binding_id) ?? bindings[bindings.length - 1] ?? null;
    bound = chosen !== null;
    days = chosen?.selection.days ?? [];
  }
  return { planRead: plan !== null, originFindingRevisionId: plan?.plan?.origin_finding_revision_id ?? null, assessmentRevisionIds, days, bound };
}

/**
 * The single "Evidence requirements" panel: the requirement table with status
 * badges, every window gap and the lineage summary in the default reading, and
 * the per-window five-minute readings, comparability and identifiers in one
 * closed disclosure. A single reading opens in the Site Evidence inspector.
 */
function EvidencePanel({ body, links, pinnedOutcome, plan, gap }: { body: EvidenceBody | null; links: VerificationLinks; pinnedOutcome: OutcomeRecord | null; plan: PlanBody | null; gap: PanelGap | null }) {
  const heading = "Evidence requirements";
  const headingId = "site-verification-evidence-heading";
  if (body === null) {
    return (
      <Panel heading={heading} headingId={headingId}>
        {gap ? <Gap gap={gap} /> : null}
        <TrialNotice />
      </Panel>
    );
  }
  const pair = body.source_resolution.pair;
  const targetLater = body.target.later as { candidate_seconds?: number | null; state: string; reasons?: string[] };
  const targetReasons = [...body.target.baseline.reasons, ...(targetLater.reasons ?? [])];
  const lineage = { baseline: lineageFor("baseline", body, plan), later: lineageFor("later", body, plan) };
  return (
    <Panel heading={heading} headingId={headingId}>
      <p className="v69-chart-note w1f4-verification-lede">
        <span data-verification-knowledge-cutoff={body.knowledge_cutoff}>
          Readings as accepted by {when(body.knowledge_cutoff)}
          {pinnedOutcome ? ", when the selected outcome was recorded" : ""}
        </span>{" "}
        · below reserve is read from the battery charge at each slot start: a five-minute sample, not continuous proof
      </p>
      <CurrentReasons current={body.verification_state} />
      <DataTable labelledBy="site-verification-requirements-caption">
        <caption id="site-verification-requirements-caption" className="visually-hidden">
          Evidence set and status
        </caption>
        <thead>
          <tr>
            <th scope="col">Evidence set</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          <RequirementRow name="baseline" label="Earlier window readings" ok={body.windows.baseline.complete} detail={`${body.windows.baseline.slots.filter((s) => s.complete).length}/${body.windows.baseline.slots.length} slots complete · ${sourceWords(body.source_resolution.baseline.state)}`}>
            <WindowGaps name="baseline" window={body.windows.baseline} />
          </RequirementRow>
          <RequirementRow name="later" label="Later window readings" ok={body.windows.later.complete} detail={`${body.windows.later.slots.filter((s) => s.complete).length}/${body.windows.later.slots.length} slots complete · ${sourceWords(body.source_resolution.later.state)}`}>
            <WindowGaps name="later" window={body.windows.later} />
          </RequirementRow>
          <RequirementRow
            name="target"
            label="Avoidable generator time, both windows"
            ok={body.target.met}
            detail={`${minutes(body.target.baseline.candidate_seconds) ?? "unknown"} to ${
              targetLater.state === "NOT_BOUND" ? "pending (later selection not appended yet)" : minutes(targetLater.candidate_seconds) ?? "unknown"
            }`}
          >
            {targetReasons.length > 0 ? (
              <>
                {" · "}
                <span className="w1f4-verification-problem" data-verification-target-reasons>
                  {targetReasons.map((reason, index) => (
                    <span key={reason} data-verification-problem={problemCode(reason)}>
                      {index > 0 ? "; " : ""}
                      {problemWords(reason)}
                    </span>
                  ))}
                </span>
              </>
            ) : null}
          </RequirementRow>
          <tr data-verification-requirement-pair="conditions">
            <th scope="row">Comparable conditions and source</th>
            <td>
              <RequirementCell name="comparability" ok={body.comparability.state === "PASS" ? true : body.comparability.state === "FAIL" ? false : null} detail={`comparable: ${checkWord(body.comparability.state)}`} />
              {" · "}
              <RequirementCell
                name="source"
                ok={pair.state === "PASS" ? true : pair.state === "FAIL" ? false : null}
                detail={`source: ${sourcePair(body.source_resolution.baseline.state, body.source_resolution.later.state)}`}
                chip={false}
              />
            </td>
          </tr>
        </tbody>
      </DataTable>
      {(["baseline", "later"] as const)
        .filter((name) => !lineage[name].planRead || !lineage[name].bound)
        // An unread plan is one fact for both windows: state it once.
        .filter((name) => name === "baseline" || lineage.baseline.planRead || lineage[name].planRead)
        .map((name) => (
          <p key={name} className="v69-chart-note w1f4-verification-gap" data-verification-lineage-summary={name}>
            {lineageSummary(name, lineage[name], body.source_resolution[name])}
          </p>
        ))}
      <DigDeeper name="evidence-detail" summary="Five-minute readings, comparability and identifiers per window">
        {(["baseline", "later"] as const)
          .filter((name) => lineage[name].planRead && lineage[name].bound)
          .map((name) => (
            <p key={name} className="action-note" data-verification-lineage-summary={name}>
              {lineageSummary(name, lineage[name], body.source_resolution[name])}
            </p>
          ))}
        <ComparabilityTable body={body} />
        <WindowDetail name="baseline" window={body.windows.baseline} source={body.source_resolution.baseline} links={links} lineage={lineage.baseline} />
        <WindowDetail name="later" window={body.windows.later} source={body.source_resolution.later} links={links} lineage={lineage.later} />
      </DigDeeper>
      <TrialNotice />
    </Panel>
  );
}

/** post-W6 W1-b Q32 / R221: every "Available" requirement chip is blue (info); availability is not a pass. */
export function requirementTone(ok: boolean | null): Tone {
  return ok === true ? "info" : ok === false ? "fail" : "unknown";
}

/** post-W6 W1-b Q32 / R221: both windows' source words, said once when they are the same. */
export function sourcePair(baseline: string | null | undefined, later: string | null | undefined): string {
  const a = sourceWords(baseline);
  const b = sourceWords(later);
  return a === b ? a : `${a} / ${b}`;
}

/** post-W6 W1-b Q34: a panel's history gap, or null when it says the same as the panel's main gap. */
function distinctGap(main: PanelGap | null, history: PanelGap | null): PanelGap | null {
  return history !== null && main !== null && history.kind === main.kind && history.text === main.text ? null : history;
}

function requirementWord(ok: boolean | null): string {
  return ok === true ? "Available" : ok === false ? "Incomplete" : "Not established";
}

function RequirementRow({ name, label, ok, detail, children }: { name: string; label: string; ok: boolean | null; detail: string; children?: ReactNode }) {
  return (
    <tr data-verification-requirement={name} data-verification-requirement-ok={ok === null ? "unknown" : ok ? "yes" : "no"}>
      <th scope="row">{label}</th>
      <td>
        <Chip tone={requirementTone(ok)}>{requirementWord(ok)}</Chip> {detail}
        {children}
      </td>
    </tr>
  );
}

/** Two requirements sharing one table row (the mock's "comparable conditions" set). */
function RequirementCell({ name, ok, detail, chip = true }: { name: string; ok: boolean | null; detail: string; chip?: boolean }) {
  return (
    <span data-verification-requirement={name} data-verification-requirement-ok={ok === null ? "unknown" : ok ? "yes" : "no"}>
      {chip ? (
        <>
          <Chip tone={requirementTone(ok)}>{requirementWord(ok)}</Chip>{" "}
        </>
      ) : null}
      <span className={ok === true ? undefined : "w1f4-verification-problem"}>
        {detail}
        {chip || ok === true ? "" : ` (${requirementWord(ok).toLowerCase()})`}
      </span>
    </span>
  );
}

/** A window's gaps, conflicts and missing samples: a material limit, always in the default reading (its row's cell). */
function WindowGaps({ name, window }: { name: "baseline" | "later"; window: EvidenceWindow }) {
  const problems = [...window.problems, ...window.slots.flatMap(slotProblems)];
  if (problems.length === 0) {
    return (
      <span data-verification-window-problems="none" data-verification-window-gaps={name}>
        {" "}
        · no gaps
      </span>
    );
  }
  const shown = problems.slice(0, 2);
  return (
    <>
      {" · "}
      <span className="w1f4-verification-problem" data-verification-window-problems={name}>
        {shown.map((p, index) => (
          <span key={index} data-verification-problem={problemCode(p)}>
            {index > 0 ? "; " : ""}
            {problemWords(p)}
          </span>
        ))}
        {problems.length > shown.length ? `; and ${problems.length - shown.length} more (listed in the readings below)` : ""}
      </span>
    </>
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

function lineageSummary(name: string, lineage: WindowLineage, source: SourceSide): string {
  if (!lineage.planRead) return "The plan this comparison was fixed under could not be read, so the assessed days and cohort are not shown.";
  if (!lineage.bound) return "The later window has no day selection recorded yet, so no assessments are selected for it.";
  const sources = new Set(lineage.days.map((d) => d.run_id)).size;
  const n = lineage.days.length;
  return `${n} assessed day${n === 1 ? "" : "s"} selected, taken from ${sources} registered source${sources === 1 ? "" : "s"}; ${lineage.assessmentRevisionIds.length} generator-time assessment${lineage.assessmentRevisionIds.length === 1 ? "" : "s"} and ${source.runs.length} source record${source.runs.length === 1 ? "" : "s"} back the ${name === "baseline" ? "earlier" : "later"} window.`;
}

/** One window's five-minute readings, source and lineage identifiers (inside the panel's closed disclosure). */
function WindowDetail({ name, window, source, links, lineage }: { name: "baseline" | "later"; window: EvidenceWindow; source: SourceSide; links: VerificationLinks; lineage: WindowLineage }) {
  const title = name === "baseline" ? "Earlier window (before the change)" : "Later window (after the change)";
  const problems = [...window.problems, ...window.slots.flatMap(slotProblems)];
  const terminal = pointCell(window.terminal_soc_sample ?? undefined, "%");
  return (
    <div className="w1f4-verification-window" data-verification-evidence-window={name} data-verification-window-complete={window.complete ? "yes" : "no"}>
      <p className="w1f4-verification-window__title">
        <strong>{title}</strong> · {windowBounds(window.window_start, window.window_end)}
      </p>
      <dl className="v69-key-values" aria-label={title}>
        <div>
          <dt>Source</dt>
          <dd>
            <span data-verification-window-source={source.state}>{sourceWords(source.state)}</span>
          </dd>
        </div>
        <div>
          <dt>Site demand energy</dt>
          <dd data-verification-card={`${name}-demand`}>{kwh(window.feeder_demand_kwh) ?? "unknown"} (all assigned demand points)</dd>
        </div>
        <div>
          <dt>Available solar energy</dt>
          <dd data-verification-card={`${name}-solar`}>{kwh(window.pv_available_kwh) ?? "unknown"}</dd>
        </div>
        <div>
          <dt>Critical demand not served</dt>
          <dd data-verification-card={`${name}-unserved`}>{kwh(window.unserved_critical_kwh) ?? "unknown"} (requested minus delivered)</dd>
        </div>
        <div>
          <dt>Battery charge, start to end</dt>
          <dd data-verification-card={`${name}-charge`}>
            {pct(window.initial_soc) ?? "unknown"} to {pct(window.terminal_soc) ?? "unknown"} (end sample: {terminal.text})
          </dd>
        </div>
      </dl>
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
      <FactList>
        <Fact term="Origin Finding revision">
          {lineage.originFindingRevisionId ? <Ref value={lineage.originFindingRevisionId} attr="data-verification-origin-finding-revision" /> : "not available"}
        </Fact>
        <Fact term="Selected assessment revisions">
          {lineage.assessmentRevisionIds.length === 0
            ? "none selected"
            : lineage.assessmentRevisionIds.map((id) => <Ref key={id} value={id} attr="data-verification-assessment-revision" />)}
        </Fact>
        <Fact term="Source records">
          {source.runs.length === 0
            ? "none recorded"
            : source.runs.map((run, index) => <Ref key={index} value={JSON.stringify(run)} attr="data-verification-source-run" />)}
        </Fact>
      </FactList>
      {lineage.days.length > 0 ? (
        <DataTable labelledBy={`site-verification-cohorts-${name}-caption`}>
          <caption id={`site-verification-cohorts-${name}-caption`}>Selected days, cohort and source</caption>
          <thead>
            <tr>
              <th scope="col">Day</th>
              <th scope="col">Cohort</th>
              <th scope="col">Day group reference</th>
              <th scope="col">Source</th>
              <th scope="col">Model</th>
              <th scope="col">Input reference</th>
              <th scope="col">Configuration reference</th>
            </tr>
          </thead>
          <tbody>
            {lineage.days.map((d) => (
              <tr key={d.day} data-verification-lineage-day={d.day}>
                <th scope="row">{d.day}</th>
                <td>
                  <code data-vocabulary-exempt="source-reference">{d.cohort_status}</code>
                </td>
                <td><Ref value={d.cohort_sha256} /></td>
                <td><Ref value={d.run_id} /></td>
                <td><Ref value={d.model_version} /></td>
                <td><Ref value={d.input_sha256} /></td>
                <td><Ref value={d.configuration_sha256} /></td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      ) : null}
      <p className="action-note">Accepted readings used for this window ({window.evidence_ids.length}), each opening in Evidence:</p>
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
            {/* W1-UX-06: each reason is an object from the backend; show its exact code (an object is not renderable). */}
            {source.reasons.map((reason, index) => {
              // Review L4: the plain words (reasonWords) sit beside the exact code; a code-less reason reads as not recognised.
              const code = typeof reason === "string" ? reason : reason.code;
              const known = typeof code === "string" && code !== "";
              return (
                <span key={index}>
                  {known ? <Ref value={code} attr="data-verification-source-reason" /> : null}{" "}
                  <span data-verification-source-reason-words>{known ? sourceReasonWords(code) : "Reason not recognised."}</span>
                </span>
              );
            })}
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
    </div>
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

