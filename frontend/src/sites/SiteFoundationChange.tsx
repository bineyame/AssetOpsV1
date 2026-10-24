/**
 * S6-01b `changes:1#a`: one Site Foundation change made by an applied Action,
 * read from `GET /api/sites/{site}/foundation/changes/{change_id}` (S6-01a).
 *
 * W1-F4 (`D-2026-10-17-mockup-layout-spec`): the v69 `changes` layout. A
 * one-line status strip, four metric cards from the real read, then the two
 * v69 panels side by side:
 *
 *   1. Change and effect: the mock's compact Field/Before/After/Purpose table
 *      (the reserve and the Foundation version), the outcome and the Action as
 *      two key values, one note with the battery, effective and recorded
 *      times, and the failed attempts in one line. The exact version,
 *      application-event and signal-assignment IDs sit in one closed
 *      disclosure.
 *   2. Decision path: declare success (the frozen plan, or "Not recorded
 *      yet."), apply and observe, then the outcome from the verification block.
 *
 * It makes no measured-effect verdict: whether the change did anything is a
 * later verification step (S6-02). Failed attempts are read from the Action's
 * own events, beside the change, never instead of it. A refused change read is
 * a page-level refusal followed by both panel slots with the gap inside.
 */

import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  Badge,
  ChartNote,
  DataTable,
  Disclosure,
  ExactReferences,
  KeyValues,
  MetricCard,
  MetricCards,
  MissingClaim,
  Notice,
  Panel,
  plainTime,
  SITE_SCREEN_DESCRIPTIONS,
  SitePageHeader,
  type MetricTone,
} from "../ui";
import type { SiteSummary } from "./siteReadModel";
import { deriveSiteView } from "./siteViewModel";
import { COLD_WORK_SUBTITLE_FALLBACK } from "./coldWorkPresentation";
import { EV_WORK_SUBTITLE_FALLBACK } from "./evWorkPresentation";
import type {
  ActionClient,
  ActionEventsBody,
  ActionReadResult,
  EventSelector,
  FoundationRevisionRef,
  PolicyChange,
  PolicyChangeBody,
  Refusal,
} from "./actionClient";
import { eventWords, outcomeWords as pendingOutcomeWords, Ref, SYSTEM_DEMONSTRATION, when } from "./actionPresentation";
import { stateLabel, stateSentence, stateTone } from "./verificationWords";
import type { TrialLinks } from "./recommendationVerification";
import { createVerificationClient, type PlanBody, type VerificationClient, type VerificationSummary } from "./verificationClient";
import "./w1f4-changes-work.css";

export interface SiteFoundationChangeLinks {
  /** A section of the Action that made the change, at an exact selection. */
  action: (actionId: string, view: "overview" | "execution" | "history", selector: EventSelector) => string;
  /** The Site Foundation (its model view). */
  foundation: string;
  /** S6-02b: an Action's Plan, Evidence or Verification child view. */
  actionChild?: TrialLinks["child"];
}

export const FOUNDATION_CHANGE_LOADING = "Loading the Foundation change.";
export const FOUNDATION_CHANGE_ATTEMPTS_LOADING = "Loading the Action's application attempts.";

/** The v69 `changes` panel titles (`v69-rendered-panels.json`). */
export const CHANGE_PANEL_TITLE = "Change and effect";
export const DECISION_PATH_PANEL_TITLE = "Decision path";
export const NOT_RECORDED_YET = "Not recorded yet.";

const LATEST: EventSelector = { eventId: null, recordedAt: null };

/**
 * W1-F4: the mock's Site page heading for `changes` and `sitework` (the site
 * name as h1, its provenance tag and the screen description).
 */
export function ChangesWorkPageHeader({
  site,
  screen,
  headingId,
}: {
  site: SiteSummary;
  screen: "changes" | "sitework" | "sitework-incidents" | "sitework-maintenance";
  headingId: string;
}) {
  const view = deriveSiteView(site);
  return (
    <SitePageHeader
      siteName={view.displayName}
      siteId={view.siteId}
      mode={view.sourceMode}
      description={
        // W5-02 K2a (P-K2a-40, K2 ruling 9): a COLDCHAIN Site's Work pages carry the mock's Site subtitle slot. There is
        // no Site subtitle field, so the cold Work page always reads `Cold-room operations at this site.` under the
        // stored Site name, never Foundation `summary`; mini-grid keeps its screen description.
        // MOCK DEVIATION (D4) R90: the mock `cold-work` site-specific subtitle (`index.html:1138`) is illustrative copy.
        // W5-04 V2a (ruling 20): an EV_CHARGING Site's Work pages always read `EV charging operations at this site.`;
        // MOCK DEVIATION (D4) R78: the mock `SITES.ev` connector/power subtitle is illustrative configuration copy.
        screen === "changes"
          ? SITE_SCREEN_DESCRIPTIONS[screen]
          : site.site_type === "COLDCHAIN"
            ? COLD_WORK_SUBTITLE_FALLBACK
            : site.site_type === "EV_CHARGING"
              ? EV_WORK_SUBTITLE_FALLBACK
              : SITE_SCREEN_DESCRIPTIONS[screen]
      }
      headingId={headingId}
    />
  );
}

/** Which part a Foundation version plays in this change. */
function revisionRole(change: PolicyChange, revision: FoundationRevisionRef): string {
  if (revision.id === change.new_foundation_revision_id) return "New version (the changed value)";
  if (revision.id === change.split_foundation_revision_id) return "Earlier period kept (split)";
  if (revision.id === change.superseded_foundation_revision_id) return "Replaced version";
  if (revision.id === change.expected_foundation_revision_id) return "Version the command expected";
  return "Related version";
}

/** A refused read, in words: the HTTP status and subject, never an empty result. */
function refusalWords(refusal: Refusal, subject: string): { title: string; text: string } {
  const title =
    refusal.http === null
      ? `${subject} unavailable`
      : refusal.http === 404
        ? `${subject} not found`
        : refusal.http === 401
          ? "Sign-in required"
          : refusal.http === 403
            ? "No access"
            : refusal.http === 409 || refusal.http === 422
              ? "Refused"
              : `${subject} unavailable`;
  const text =
    refusal.http === null
      ? "The server could not be reached."
      : refusal.http === 401
        ? "Sign in to read this site's Actions."
        : refusal.http === 403
          ? "Your account has no access to this."
          : refusal.http === 404
            ? `This site has no such ${subject.toLowerCase()}.`
            : `The ${subject.toLowerCase()} could not be read (HTTP ${refusal.http}).`;
  return { title, text };
}

function RefusalDetail({ refusal, text }: { refusal: Refusal; text: string }) {
  return (
    <>
      <span data-action-read="refused" data-action-http={refusal.http ?? "none"} data-action-code={refusal.code ?? ""}>
        {text}
      </span>
      {refusal.code ? (
        <>
          {" "}
          Code: <Ref value={refusal.code} />.
        </>
      ) : null}
      {refusal.message ? ` Reason given: ${refusal.message}` : null}
    </>
  );
}

function metricToneFor(state: string): MetricTone {
  const tone = stateTone(state);
  return tone === "pass" ? "green" : tone === "fail" ? "red" : tone === "unknown" ? "muted" : "amber";
}

const DEFAULT_VERIFICATION = createVerificationClient();

/** post-W6 shell R141 (Q14): copy for the frozen plan's Target and Guardrails cards. */
export const PLAN_DETAILS_NOT_AVAILABLE = "Plan details are not available yet.";

/** The not-available line, tagged as the registered gap (G-changes-plan-figures, register R379). */
function PlanDetailsNotAvailable() {
  return (
    <MissingClaim gapId="G-changes-plan-figures" placement="changes.metrics.plan-figures">
      {PLAN_DETAILS_NOT_AVAILABLE}
    </MissingClaim>
  );
}

type PlanFigures = { target: string; guardrails: string } | null;

/**
 * The stored target and guardrail count of the frozen plan, or null when the exact plan read carries no usable
 * value (a D1 gap; never inferred from the Action or the mock). `ratio` [num, den] means later × den ≤ earlier × num.
 */
export function planFigures(body: PlanBody | null | undefined): PlanFigures {
  const plan = body?.plan ?? null;
  if (plan === null) return null;
  const ratio = plan.target?.ratio;
  const guardrails = plan.guardrails ? Object.keys(plan.guardrails).length : 0;
  if (!Array.isArray(ratio) || ratio.length !== 2) return null;
  const [num, den] = ratio;
  if (!(den > 0) || !(num >= 0) || num >= den || guardrails === 0) return null;
  return { target: `≥${Math.round((1 - num / den) * 100)}% lower`, guardrails: `${guardrails} required` };
}

export function SiteFoundationChange({
  siteId,
  changeId,
  client,
  links,
  onTitle,
  verificationClient = DEFAULT_VERIFICATION,
}: {
  siteId: string;
  changeId: string;
  client: ActionClient;
  links: SiteFoundationChangeLinks;
  onTitle?: (title: string) => void;
  verificationClient?: VerificationClient;
}) {
  const [read, setRead] = useState<ActionReadResult<PolicyChangeBody> | null>(null);
  const [attempts, setAttempts] = useState<ActionReadResult<ActionEventsBody> | null>(null);
  useEffect(() => {
    let active = true;
    setRead(null);
    setAttempts(null);
    void client.getChange(siteId, changeId).then((loaded) => {
      if (!active) return;
      setRead(loaded);
      if (loaded.status !== "loaded") return;
      void client.getActionEvents(siteId, loaded.value.change.action_id, LATEST).then((events) => {
        if (active) setAttempts(events);
      });
    });
    return () => {
      active = false;
    };
  }, [client, siteId, changeId]);

  const change = read?.status === "loaded" ? read.value.change : null;
  useEffect(() => {
    onTitle?.(change ? "Battery reserve change" : "Foundation change");
  }, [onTitle, change]);

  // post-W6 shell R141 (Q14): the frozen plan is read only when the change names one.
  const loadedVerification = read?.status === "loaded" ? (read.value.verification ?? null) : null;
  const frozenPlanId =
    loadedVerification && loadedVerification.state !== "NO_PLAN" ? loadedVerification.plan_id : null;
  const planActionId = change?.action_id ?? null;
  const [planRead, setPlanRead] = useState<{ planId: string; figures: PlanFigures | "pending" | "failed" } | null>(null);
  useEffect(() => {
    if (frozenPlanId === null || planActionId === null) {
      setPlanRead(null);
      return;
    }
    let active = true;
    setPlanRead({ planId: frozenPlanId, figures: "pending" });
    void verificationClient
      .getPlan(siteId, planActionId, { id: frozenPlanId, recordedAt: null })
      .then((loaded) => {
        if (!active) return;
        setPlanRead({ planId: frozenPlanId, figures: loaded.status === "loaded" ? planFigures(loaded.value) : "failed" });
      })
      .catch(() => {
        if (active) setPlanRead({ planId: frozenPlanId, figures: "failed" });
      });
    return () => {
      active = false;
    };
  }, [verificationClient, siteId, planActionId, frozenPlanId]);

  if (read === null) return <p>{FOUNDATION_CHANGE_LOADING}</p>;
  if (read.status === "refused") return <RefusedChange refusal={read} links={links} />;

  const c = read.value.change;
  const verification = read.value.verification ?? null;
  const appliedEvent = links.action(c.action_id, "history", { eventId: c.applied_event_id, recordedAt: null });
  const actionHref = links.action(c.action_id, "overview", LATEST);
  const verificationState = verification === null ? c.outcome.state : verification.state;
  const planId = verification && verification.state !== "NO_PLAN" ? verification.plan_id : null;
  const planFigure = planRead !== null && planRead.planId === planId ? planRead.figures : "pending";
  const figures = typeof planFigure === "object" ? planFigure : null;
  const planState = planId === null ? "none" : planFigure === null ? "absent" : typeof planFigure === "string" ? planFigure : "loaded";
  const outcomeText = verification
    ? `Verification: ${stateLabel(verification.state, verification.reasons)}.`
    : pendingOutcomeWords(c.outcome.state);

  return (
    <div className="w1f4-changes-work" data-change-id={c.change_id} data-change-outcome={c.outcome.state}>
      <div className="status-strip status-strip--line" aria-label="Foundation change" data-change-status>
        <span className="status-strip__lead">
          <Badge tone="lifecycle">Battery reserve change · Applied</Badge>
        </span>
        <span className="status-strip__state">Setting changed; being applied is not success, effect judged separately</span>
        <span className="muted status-strip__item">
          {SYSTEM_DEMONSTRATION} command · effective {plainTime(c.effective_from) ?? when(c.effective_from)} ·{" "}
          <Link to={actionHref} data-change-card-action-link>
            Open the Action
          </Link>
        </span>
        <span className="status-strip__spacer" aria-hidden="true" />
        {links.actionChild ? (
          <Link
            className="status-strip__item"
            to={links.actionChild(c.action_id, "verification")}
            data-change-card-verification-link
          >
            Open verification →
          </Link>
        ) : null}
        <ExactReferences
          name="change-references"
          variant="tech"
          references={[
            { label: "Change record", value: c.change_id },
            { label: "Battery", value: c.asset_id },
            { label: "Action reference", value: c.action_id },
            { label: "Application event", value: c.applied_event_id },
            { label: "Trial outcome state", value: verificationState },
          ]}
        />
      </div>

      <MetricCards label="This change at a glance" data={{ "data-change-metrics": "" }}>
        <MetricCard
          label="Proposed change"
          value={`${c.old_value}${c.unit} → ${c.new_value}${c.unit}`}
          note="Battery reserve · applied"
          data={{ "data-change-metric": "change" }}
        />
        {/* post-W6 shell R141 (Q14): the frozen plan's stored target and guardrail count. While the plan read is
            pending or failed, the cards keep "Set in the plan" and say the details are not available yet.
            MOCK DEVIATION D1 (post-W6 shell Q14, register R379): a plan read with no stored target or
            guardrails shows the same not-available line instead of the mock's values. */}
        <MetricCard
          label="Target"
          value={planId ? (figures ? figures.target : "Set in the plan") : "Not recorded yet"}
          note={planId ? (figures ? "Frozen before the later window is judged" : <PlanDetailsNotAvailable />) : "No verification plan is frozen yet"}
          word={!(planId && figures)}
          tone={planId ? undefined : "muted"}
          data={{ "data-change-metric": "target", "data-change-plan-read": planState }}
        />
        <MetricCard
          label="Guardrails"
          value={planId ? (figures ? figures.guardrails : "Set in the plan") : "Not recorded yet"}
          note={planId ? (figures ? "Service, reserve and stored-energy limits" : <PlanDetailsNotAvailable />) : "Limits are set when the plan is frozen"}
          word={!(planId && figures)}
          tone={planId ? undefined : "muted"}
          data={{ "data-change-metric": "guardrails", "data-change-plan-read": planState }}
        />
        <MetricCard
          label="Outcome"
          value={verification ? stateLabel(verification.state, verification.reasons) : "Not available"}
          note={verification ? "From the verification read; applied is not success" : "The verification state is not available"}
          assessment
          tone={verification ? metricToneFor(verification.state) : "muted"}
          data={{ "data-change-metric": "outcome" }}
        />
      </MetricCards>

      <div className="panel-pair">
        <Panel heading={CHANGE_PANEL_TITLE} headingId="site-change-summary-heading">
          <DataTable labelledBy="site-change-values-caption">
            <caption id="site-change-values-caption" className="visually-hidden">
              Changed value
            </caption>
            <thead>
              <tr>
                <th scope="col">Field</th>
                <th scope="col">Before</th>
                <th scope="col">After</th>
                <th scope="col">Purpose</th>
              </tr>
            </thead>
            <tbody>
              <tr data-change-values>
                <td>Battery reserve</td>
                <td data-change-old>
                  {c.old_value}
                  {c.unit}
                </td>
                <td data-change-new>
                  {c.new_value}
                  {c.unit}
                </td>
                <td className="muted">{NOT_RECORDED_YET}</td>
              </tr>
              <tr>
                <td>Foundation version</td>
                <VersionCells change={c} />
                <td>
                  {c.split_foundation_revision_id ? "Holds the new value; earlier period kept" : "Holds the new value"}
                </td>
              </tr>
            </tbody>
          </DataTable>
          <KeyValues
            label="Change record"
            rows={[
              [
                "Outcome",
                <span key="outcome" data-change-outcome-words data-change-verification={verification?.state ?? "UNAVAILABLE"}>
                  {outcomeText}
                </span>,
                "outcome",
              ],
              [
                "Applied by",
                <Link key="action" to={actionHref} data-change-action-link>
                  The Action ({SYSTEM_DEMONSTRATION}) →
                </Link>,
                "action",
              ],
            ]}
          />
          <ChartNote>
            {/* post-W6 shell R151 (Q15): the change DTO carries no stored battery label, so the sentence says
                "Battery"; the asset UUID stays in the "Battery" row of the technical references above. */}
            <span data-change-asset={c.asset_id}>Battery</span> · effective{" "}
            <span data-change-effective={c.effective_from}>{plainTime(c.effective_from) ?? when(c.effective_from)}</span>
            {c.validity === "EFFECTIVE_FROM_OPEN_ENDED" ? " onward" : null} · recorded{" "}
            <span data-change-recorded={c.recorded_at}>{plainTime(c.recorded_at) ?? when(c.recorded_at)}</span>
          </ChartNote>
          <Attempts attempts={attempts} change={c} links={links} />
          <Disclosure name="site-change-versions" summary="Versions and records this change names">
            <ChangeReferences change={c} appliedEventHref={appliedEvent} />
          </Disclosure>
        </Panel>
        <Panel heading={DECISION_PATH_PANEL_TITLE} headingId="site-change-path-heading">
          <DecisionPath
            actionId={c.action_id}
            summary={verification}
            planId={planId}
            appliedEventHref={appliedEvent}
            links={links}
          />
        </Panel>
      </div>

      {/* post-W6 shell R119 (Q6): the mock's closing blue `.notice` (11 px, boxed); the copy stays this page's own. */}
      <Notice tone="blue" data={{ "data-change-later-sections": "" }}>
        There is no list of Site changes yet; a change is reached from the Action that made it.{" "}
        <Link to={links.foundation}>Back to the Foundation</Link>
      </Notice>
    </div>
  );
}

/** The Foundation version before and after the change, by version number, as two table cells. */
function VersionCells({ change }: { change: PolicyChange }) {
  const byId = new Map(change.foundation_revisions.map((revision) => [revision.id, revision]));
  const before = change.superseded_foundation_revision_id ? byId.get(change.superseded_foundation_revision_id) : undefined;
  const after = byId.get(change.new_foundation_revision_id);
  const name = (revision: FoundationRevisionRef | undefined) => (revision ? `v${revision.version}` : "Not named");
  return (
    <>
      <td data-change-version-before>{name(before)}</td>
      <td data-change-version-after>{name(after)}</td>
    </>
  );
}

/** The exact versions and signal assignments this change names (closed disclosure). */
function ChangeReferences({ change: c, appliedEventHref }: { change: PolicyChange; appliedEventHref: string }) {
  const revisions = [...c.foundation_revisions].sort((a, b) => a.version - b.version);
  const rows: [ReactNode, ReactNode, string][] = [
    ["Change record", <Ref key="id" value={c.change_id} />, "id"],
    ["Action", <Ref key="action" value={c.action_id} />, "action"],
    [
      "Application event",
      <Link key="event" to={appliedEventHref}>
        <Ref value={c.applied_event_id} />
      </Link>,
      "event",
    ],
    ["Expected by the command", <Ref key="expected" value={c.expected_foundation_revision_id} attr="data-change-expected" />, "expected"],
    ["New version", <Ref key="new" value={c.new_foundation_revision_id} attr="data-change-new-foundation" />, "new"],
  ];
  if (c.command_idempotency_key) rows.push(["Command key", <Ref key="key" value={c.command_idempotency_key} />, "key"]);
  return (
    <>
      <KeyValues label="Exact records" rows={rows} />
      <DataTable labelledBy="site-change-revisions-caption">
        <caption id="site-change-revisions-caption">Versions this change names</caption>
        <thead>
          <tr>
            <th scope="col">Version</th>
            <th scope="col">Role</th>
            <th scope="col">Origin</th>
            <th scope="col">Valid from</th>
            <th scope="col">Valid to</th>
            <th scope="col">Recorded</th>
            <th scope="col">ID</th>
          </tr>
        </thead>
        <tbody>
          {revisions.map((revision) => (
            <tr key={revision.id} data-change-revision={revision.id} data-change-revision-origin={revision.origin}>
              <td>{revision.version}</td>
              <td>{revisionRole(c, revision)}</td>
              <td>
                <Ref value={revision.origin} />
              </td>
              <td>{when(revision.valid_from)}</td>
              <td>{revision.valid_to ? when(revision.valid_to) : "No end date"}</td>
              <td>{when(revision.recorded_at)}</td>
              <td>
                <Ref value={revision.id} />
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      <DataTable labelledBy="site-change-bindings-caption">
        <caption id="site-change-bindings-caption">Signal assignment versions</caption>
        <thead>
          <tr>
            <th scope="col">Part</th>
            <th scope="col">ID</th>
          </tr>
        </thead>
        <tbody>
          {c.binding_set_revisions.superseded.map((id) => (
            <tr key={`s-${id}`} data-change-binding="superseded">
              <td>Replaced</td>
              <td>
                <Ref value={id} />
              </td>
            </tr>
          ))}
          {c.binding_set_revisions.inserted.map((id) => (
            <tr key={`i-${id}`} data-change-binding="inserted">
              <td>Written for the new versions</td>
              <td>
                <Ref value={id} />
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </>
  );
}

/** The verification read state as one line; absent on older servers, never invented. */
function VerificationLine({ summary }: { summary: VerificationSummary | null }) {
  if (!summary) {
    return (
      <span data-trial-verification-state="UNAVAILABLE" data-trial-verification-name="change">
        The verification state is not available from this server yet.
      </span>
    );
  }
  return (
    <span data-trial-verification-state={summary.state} data-trial-verification-name="change">
      <span className={`verify-chip verify-chip--${stateTone(summary.state)}`}>{stateLabel(summary.state, summary.reasons)}</span>{" "}
      {stateSentence(summary.state, summary.reasons)}
    </span>
  );
}

/** `changes:2`: declare success, apply and observe, then the outcome (the mock's attention rows). */
function DecisionPath({
  actionId,
  summary,
  planId,
  appliedEventHref,
  links,
}: {
  actionId: string;
  summary: VerificationSummary | null;
  planId: string | null;
  appliedEventHref: string;
  links: SiteFoundationChangeLinks;
}) {
  const child = links.actionChild;
  const outcomeId = summary?.outcome_id ?? null;
  const noOutcome = summary === null || summary.state === "NO_PLAN" || summary.state === "PENDING";
  const items: { key: string; title: string; body: ReactNode; action: ReactNode }[] = [
    {
      key: "declare",
      title: "Declare success before evaluating",
      body: planId ? "The target, coverage, comparable windows and limits are frozen in the plan." : NOT_RECORDED_YET,
      action:
        planId && child ? (
          <Link to={child(actionId, "plan", { planRevisionId: planId })} data-change-plan-link={planId}>
            Inspect plan →
          </Link>
        ) : null,
    },
    {
      key: "apply",
      title: "Apply and observe",
      body: "The applied setting is recorded, then later readings are accepted.",
      action: (
        <span>
          <Link to={appliedEventHref} data-change-applied-event-link>
            Application record →
          </Link>
          {child ? (
            <>
              {" "}
              <Link to={child(actionId, "evidence")}>Inspect accepted evidence →</Link>
            </>
          ) : null}
        </span>
      ),
    },
    {
      key: "outcome",
      title: "Retain, retune or revert",
      body: (
        <>
          {noOutcome ? `${NOT_RECORDED_YET} ` : null}
          <VerificationLine summary={summary} />
        </>
      ),
      action: child ? (
        <span>
          <Link to={child(actionId, "verification")} data-change-verification-link>
            View verification →
          </Link>
          {outcomeId ? (
            <>
              {" "}
              <Link to={child(actionId, "verification", { outcomeId })} data-change-outcome-link={outcomeId}>
                The outcome behind this state (opens as Historical) →
              </Link>
            </>
          ) : null}
        </span>
      ) : null,
    },
  ];
  return (
    <ol className="v69-attention" aria-label="Decision path" data-change-decision-path>
      {items.map((item, index) => (
        <li className="v69-attention__item" key={item.key} data-attention-item={item.key}>
          <span className="v69-attention__rank" aria-hidden="true">
            {index + 1}
          </span>
          <div>
            <h3>{item.title}</h3>
            <p>
              {item.body}
              {item.action ? <> {item.action}</> : null}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}

/** Application attempts of the Action, read from its events; FAILED attempts changed nothing. */
/** post-W6 shell R151 (Q15): plain words for a failed application attempt's stored code. */
export const FAILURE_WORDS: Record<string, string> = {
  ACTION_FOUNDATION_STALE: "The site configuration changed before this was applied",
  ACTION_VALUE_INVALID: "The proposed value was outside the allowed range",
  ACTION_EFFECTIVE_TIME_INVALID: "The effective time was not valid",
};
export const FAILURE_WORDS_UNKNOWN = "The attempt was refused";

export function failureWords(code: string | null | undefined): string {
  return (code ? FAILURE_WORDS[code] : undefined) ?? FAILURE_WORDS_UNKNOWN;
}

function Attempts({
  attempts,
  change,
  links,
}: {
  attempts: ActionReadResult<ActionEventsBody> | null;
  change: PolicyChange;
  links: SiteFoundationChangeLinks;
}) {
  if (attempts === null) return <ChartNote>{FOUNDATION_CHANGE_ATTEMPTS_LOADING}</ChartNote>;
  if (attempts.status === "refused") {
    const words = refusalWords(attempts, "Action events");
    return (
      <p className="not-available-yet v69-chart-note" data-change-attempts-refused>
        <strong>{words.title}.</strong> <RefusalDetail refusal={attempts} text={words.text} /> Failed attempts are not
        known; the change above is unaffected.
      </p>
    );
  }
  const failed = attempts.value.events.filter((event) => event.kind === "FAILED");
  return (
    <div className="v69-chart-note w1f4-change-attempts" data-change-attempts={failed.length}>
      {failed.length === 0 ? (
        "No failed application attempts are recorded for this Action."
      ) : (
        <>
          {failed.length === 1 ? "One earlier attempt" : `${failed.length} earlier attempts`} failed and changed nothing:{" "}
          <ul className="action-list action-list--codes">
            {failed.map((event) => (
              <li key={event.id} data-change-failed-attempt={event.id}>
                <Link
                  to={links.action(change.action_id, "history", { eventId: event.id, recordedAt: null })}
                  title={`${eventWords(event.kind)} ${when(event.recorded_at)}`}
                >
                  {plainTime(event.recorded_at) ?? when(event.recorded_at)}
                </Link>{" "}
                <span data-change-failure-words={event.failure_code ?? "UNKNOWN"}>{failureWords(event.failure_code)}</span>
              </li>
            ))}
          </ul>
          {/* post-W6 shell R151 (Q15): the raw failure codes stay reachable in the technical disclosure. */}
          <ExactReferences
            name="change-failed-attempt-codes"
            variant="tech"
            references={failed.map((event, index) => ({
              label: `Attempt ${index + 1} failure code · ${plainTime(event.recorded_at) ?? when(event.recorded_at)}`,
              value: event.failure_code ?? null,
            }))}
          />
        </>
      )}
    </div>
  );
}

/**
 * W1-F5b: the bare Changes address (the Foundation row's Change & effect entry) with no change selected. This
 * site has no list of changes yet, so the page says so once and keeps both v69 slots with the gap inside each.
 */
export function NoChangeSelected({ foundationHref }: { foundationHref: string }) {
  return (
    <div className="w1f4-changes-work" data-change-index="unavailable">
      <div className="page-refusal" role="status" data-page-refusal="no-change-selected">
        <p className="page-refusal__title">
          <strong>No change selected</strong>
        </p>
        <p>
          This site has no list of Foundation changes yet. A change opens by its own address from the Action that
          made it.
        </p>
        <p>
          <Link to={foundationHref}>Back to the Foundation</Link>
        </p>
      </div>
      <div className="panel-pair">
        <Panel heading={CHANGE_PANEL_TITLE} headingId="site-change-summary-heading">
          <p className="not-available-yet v69-chart-note" data-panel-gap="site-change-summary-heading">
            No change is selected, so no setting, version or outcome is shown.
          </p>
        </Panel>
        <Panel heading={DECISION_PATH_PANEL_TITLE} headingId="site-change-path-heading">
          <p className="not-available-yet v69-chart-note" data-panel-gap="site-change-path-heading">
            No change is selected, so no Action, plan or verification is shown.
          </p>
        </Panel>
      </div>
    </div>
  );
}

/** A refused change read: the page-level refusal, then both v69 slots with the gap inside. */
function RefusedChange({ refusal, links }: { refusal: Refusal; links: SiteFoundationChangeLinks }) {
  const words = refusalWords(refusal, "Foundation change");
  const gap = refusal.http === 404 ? "No change with this address is recorded for this site." : "The change could not be read.";
  return (
    <div className="w1f4-changes-work" data-change-refused={refusal.http ?? "none"}>
      <div className="page-refusal" role="status" data-page-refusal={refusal.http === 404 ? "not-found" : "refused"}>
        <p className="page-refusal__title">
          <strong>{words.title}</strong>
        </p>
        <p>
          <RefusalDetail refusal={refusal} text={words.text} />
        </p>
        <p>
          <Link to={links.foundation}>Back to the Foundation</Link>
        </p>
      </div>
      <div className="panel-pair">
        <Panel heading={CHANGE_PANEL_TITLE} headingId="site-change-summary-heading">
          <p className="not-available-yet v69-chart-note" data-panel-gap="site-change-summary-heading">
            {gap} No setting, version or outcome is shown.
          </p>
        </Panel>
        <Panel heading={DECISION_PATH_PANEL_TITLE} headingId="site-change-path-heading">
          <p className="not-available-yet v69-chart-note" data-panel-gap="site-change-path-heading">
            {gap} {NOT_RECORDED_YET}
          </p>
        </Panel>
      </div>
    </div>
  );
}
