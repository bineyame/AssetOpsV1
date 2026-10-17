/**
 * S6-01b `changes:1#a`: one Site Foundation change made by an applied Action,
 * read from `GET /api/sites/{site}/foundation/changes/{change_id}` (S6-01a).
 *
 * W1-F4 (`D-2026-10-17-mockup-layout-spec`): the v69 `changes` layout. A
 * one-line status strip, four metric cards from the real read, then the two
 * v69 panels side by side:
 *
 *   1. Change and effect: the old and new reserve with its unit and asset,
 *      the effective and recorded times, the Foundation versions before and
 *      after, the Action and its exact application event, failed attempts and
 *      the pending outcome. The exact version and signal-assignment IDs sit in
 *      one closed disclosure.
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
  Panel,
  plainTime,
  SITE_SCREEN_DESCRIPTIONS,
  SitePageHeader,
  type MetricTone,
} from "../ui";
import type { SiteSummary } from "./siteReadModel";
import { deriveSiteView } from "./siteViewModel";
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
import type { VerificationSummary } from "./verificationClient";
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
  screen: "changes" | "sitework";
  headingId: string;
}) {
  const view = deriveSiteView(site);
  return (
    <SitePageHeader
      siteName={view.displayName}
      siteId={view.siteId}
      mode={view.sourceMode}
      description={SITE_SCREEN_DESCRIPTIONS[screen]}
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

export function SiteFoundationChange({
  siteId,
  changeId,
  client,
  links,
  onTitle,
}: {
  siteId: string;
  changeId: string;
  client: ActionClient;
  links: SiteFoundationChangeLinks;
  onTitle?: (title: string) => void;
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

  if (read === null) return <p>{FOUNDATION_CHANGE_LOADING}</p>;
  if (read.status === "refused") return <RefusedChange refusal={read} links={links} />;

  const c = read.value.change;
  const verification = read.value.verification ?? null;
  const appliedEvent = links.action(c.action_id, "history", { eventId: c.applied_event_id, recordedAt: null });
  const actionHref = links.action(c.action_id, "overview", LATEST);
  const verificationState = verification === null ? c.outcome.state : verification.state;
  const planId = verification && verification.state !== "NO_PLAN" ? verification.plan_id : null;
  const outcomeText = verification
    ? `Verification: ${stateLabel(verification.state, verification.reasons)}.`
    : pendingOutcomeWords(c.outcome.state);

  return (
    <div className="w1f4-changes-work" data-change-id={c.change_id} data-change-outcome={c.outcome.state}>
      <div className="status-strip status-strip--line" aria-label="Foundation change" data-change-status>
        <span className="status-strip__lead">
          <Badge tone="lifecycle">Battery reserve change · Applied</Badge>
        </span>
        <span className="status-strip__state">Setting changed; effect judged separately</span>
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
        <MetricCard
          label="Target"
          value={planId ? "Set in the plan" : "Not recorded yet"}
          note={planId ? "Frozen before the later window is judged" : "No verification plan is frozen yet"}
          word
          tone={planId ? undefined : "muted"}
          data={{ "data-change-metric": "target" }}
        />
        <MetricCard
          label="Guardrails"
          value={planId ? "Set in the plan" : "Not recorded yet"}
          note={planId ? "Service, reserve and stored-energy limits" : "Limits are set when the plan is frozen"}
          word
          tone={planId ? undefined : "muted"}
          data={{ "data-change-metric": "guardrails" }}
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
            <caption id="site-change-values-caption">Changed value</caption>
            <thead>
              <tr>
                <th scope="col">Setting</th>
                <th scope="col">Before</th>
                <th scope="col">After</th>
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
              </tr>
            </tbody>
          </DataTable>
          <KeyValues
            label="Change record"
            rows={[
              ["Battery", <Ref key="asset" value={c.asset_id} attr="data-change-asset" />, "asset"],
              [
                "Effective from",
                <span key="effective">
                  <span data-change-effective={c.effective_from}>{when(c.effective_from)}</span>
                  {c.validity === "EFFECTIVE_FROM_OPEN_ENDED" ? " onward, with no end date" : null}
                </span>,
                "effective",
              ],
              ["Recorded", <span key="recorded" data-change-recorded={c.recorded_at}>{when(c.recorded_at)}</span>, "recorded"],
              ["Foundation version", <VersionStep key="versions" change={c} />, "versions"],
              [
                "Applied by",
                <span key="action">
                  <Link to={actionHref} data-change-action-link>
                    <Ref value={c.action_id} />
                  </Link>{" "}
                  ({SYSTEM_DEMONSTRATION})
                </span>,
                "action",
              ],
              [
                "Application event",
                <Link key="event" to={appliedEvent} data-change-applied-event-link>
                  <Ref value={c.applied_event_id} />
                </Link>,
                "event",
              ],
              [
                "Outcome",
                <span key="outcome" data-change-outcome-words data-change-verification={verification?.state ?? "UNAVAILABLE"}>
                  {outcomeText}
                </span>,
                "outcome",
              ],
            ]}
          />
          <Attempts attempts={attempts} change={c} links={links} />
          <ChartNote>
            The setting changed when it was applied; being applied is not success. Whether it had any effect is judged
            later, from the trial&apos;s windows.
          </ChartNote>
          <Disclosure name="site-change-versions" summary="Versions and records this change names">
            <ChangeReferences change={c} />
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

      <p className="notice notice--info" data-change-later-sections>
        There is no list of Site changes yet; a change is reached from the Action that made it.{" "}
        <Link to={links.foundation}>Back to the Foundation</Link>
      </p>
    </div>
  );
}

/** The Foundation version before and after the change, by version number. */
function VersionStep({ change }: { change: PolicyChange }) {
  const byId = new Map(change.foundation_revisions.map((revision) => [revision.id, revision]));
  const before = change.superseded_foundation_revision_id ? byId.get(change.superseded_foundation_revision_id) : undefined;
  const after = byId.get(change.new_foundation_revision_id);
  const name = (revision: FoundationRevisionRef | undefined) => (revision ? `v${revision.version}` : "version not named");
  return (
    <span data-change-version-step>
      {name(before)} → {name(after)}
      {change.split_foundation_revision_id ? " (earlier period kept as its own version)" : null}
    </span>
  );
}

/** The exact versions and signal assignments this change names (closed disclosure). */
function ChangeReferences({ change: c }: { change: PolicyChange }) {
  const revisions = [...c.foundation_revisions].sort((a, b) => a.version - b.version);
  const rows: [ReactNode, ReactNode, string][] = [
    ["Change record", <Ref key="id" value={c.change_id} />, "id"],
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
          <Link to={appliedEventHref}>Application record →</Link>
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
            <p>{item.body}</p>
            {item.action}
          </div>
        </li>
      ))}
    </ol>
  );
}

/** Application attempts of the Action, read from its events; FAILED attempts changed nothing. */
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
    <div data-change-attempts={failed.length}>
      {failed.length === 0 ? (
        <ChartNote>No failed application attempts are recorded for this Action.</ChartNote>
      ) : (
        <>
          <ChartNote>
            {failed.length === 1 ? "One earlier attempt" : `${failed.length} earlier attempts`} failed and changed
            nothing:
          </ChartNote>
          <ul className="action-list action-list--codes">
            {failed.map((event) => (
              <li key={event.id} data-change-failed-attempt={event.id}>
                <Link to={links.action(change.action_id, "history", { eventId: event.id, recordedAt: null })}>
                  {eventWords(event.kind)} {when(event.recorded_at)}
                </Link>{" "}
                <Ref value={event.failure_code ?? "UNKNOWN"} />
              </li>
            ))}
          </ul>
        </>
      )}
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
