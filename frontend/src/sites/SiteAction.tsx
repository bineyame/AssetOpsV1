/**
 * S6-01b phase 1: the canonical Site Action root (mock `action-overview`,
 * `action-execution`, `action-history`), at
 * `/sites/{site}/actions/{action}[/execution | /history]` with an optional
 * exact `?event_id=` or server `?recorded_at=` selection.
 *
 * Reads `GET /api/sites/{site}/actions/{action}` and `.../events` with the
 * same selector. The selector stays in the address and every section link, so
 * reload and navigation keep the exact selection; both selectors together are
 * the server's typed `ACTION_SELECTOR_CONFLICT`, shown as such with no silent
 * preference (Architect Q5). Events are listed in the server's
 * `(recorded_at, id)` order, with both the recorded and the happened time; no
 * Action revision is invented.
 *
 * The apply control renders only when the read's `system_demo_capability.apply`
 * allows `APPLY` (Architect Q4). A FAILED attempt leaves the application
 * pending; a refused command or re-read never hides what was already read.
 * Nothing here claims a changed operation, a measured effect or a saving: the
 * outcome stays pending until verification (S6-02).
 *
 * W1-F4 (`D-2026-10-17-mockup-layout-spec`): each of this file's views is the
 * single v69 panel of its screen (Action scope, Activity log, Action history).
 * Around every view, including the Plan, Evidence and Verification views of
 * `SiteActionVerification`, the shell renders only page-level refusals
 * (`div.page-refusal`), never a panel; an unread Action keeps the selected
 * view's panel slots with the gap inside.
 */
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  asOfText,
  ChartNote,
  currentnessWords,
  DataTable,
  ExactReferences,
  KeyValues,
  outcomeWords as productOutcomeWords,
  Panel,
} from "../ui";
import type { ProductTone } from "../ui/productWords";
import { SOURCE_WORDS, sourceState } from "./sourceProvenance";
import { ActionVerification } from "./SiteActionVerification";
import { createVerificationClient, type HistoryBody, type VerificationClient } from "./verificationClient";
import { stateLabel } from "./verificationWords";
import {
  freshIdempotencyKey,
  type ActionBody,
  type ActionClient,
  type ActionEvent,
  type ActionEventsBody,
  type ActionReadResult,
  type CommandResult,
  type EventSelector,
  type PolicyChange,
  type Refusal,
  type Selection,
} from "./actionClient";
import {
  APPLICATION_WORDS,
  applicationWords,
  CommandRefusal,
  CommandUnavailable,
  eventWords,
  granted,
  limitationText,
  outcomeWords,
  Ref,
  SYSTEM_DEMONSTRATION,
  when,
} from "./actionPresentation";
import "./w1f4-action.css";
import { AffectsLine } from "./outcomeCategories";

export const ACTION_VIEWS = ["overview", "plan", "execution", "evidence", "verification", "history"] as const;
export type ActionView = (typeof ACTION_VIEWS)[number];

/** Section labels. The address segment stays `execution`; the label is the operator's word. */
export const ACTION_VIEW_LABELS: Record<ActionView, string> = {
  overview: "Overview",
  plan: "Plan",
  execution: "Application",
  evidence: "Evidence",
  verification: "Verification",
  history: "History",
};

/** S6-02b: the verification selection carried beside the S6-01b event selection. */
export interface ActionSelector extends EventSelector {
  planRevisionId?: string | null;
  outcomeId?: string | null;
}

export interface SiteActionLinks {
  /** A section of this Action with an exact selection (or the latest when every selector is null). */
  view: (view: ActionView, selector: ActionSelector) => string;
  /** A Finding of this Site at an exact version. */
  finding: (findingId: string, revisionId: string | null) => string;
  /** The Recommendation child view of a Finding at an exact version. */
  recommendation: (findingId: string, revisionId: string | null) => string;
  /** The Site Foundation change record an APPLIED event made. */
  change: (changeId: string) => string;
  /** S6-02b: the Site Evidence inspector at one accepted evidence ID. */
  evidenceRecord?: (evidenceId: string) => string;
}

const DEFAULT_VERIFICATION = createVerificationClient();

const LATEST: EventSelector = { eventId: null, recordedAt: null };

interface Reads {
  action: ActionReadResult<ActionBody> | null;
  events: ActionReadResult<ActionEventsBody> | null;
}

export function SiteAction({
  siteId,
  actionId,
  view,
  selector,
  client,
  links,
  onTitle,
  verification = DEFAULT_VERIFICATION,
}: {
  siteId: string;
  actionId: string;
  view: ActionView;
  selector: ActionSelector;
  client: ActionClient;
  links: SiteActionLinks;
  onTitle?: (title: string) => void;
  verification?: VerificationClient;
}) {
  const [reads, setReads] = useState<Reads>({ action: null, events: null });
  const [lastAction, setLastAction] = useState<ActionBody | null>(null);
  const [lastEvents, setLastEvents] = useState<ActionEventsBody | null>(null);
  const [reload, setReload] = useState(0);
  const [outcome, setOutcome] = useState<CommandResult | null>(null);
  const { eventId, recordedAt } = selector;
  const planRevisionId = selector.planRevisionId ?? null;
  const outcomeId = selector.outcomeId ?? null;

  useEffect(() => {
    setLastAction(null);
    setLastEvents(null);
    setOutcome(null);
  }, [siteId, actionId, eventId, recordedAt]);

  useEffect(() => {
    let active = true;
    setReads({ action: null, events: null });
    const chosen = { eventId, recordedAt };
    void client.getAction(siteId, actionId, chosen).then((loaded) => {
      if (!active) return;
      setReads((prior) => ({ ...prior, action: loaded }));
      if (loaded.status === "loaded") setLastAction(loaded.value);
    });
    void client.getActionEvents(siteId, actionId, chosen).then((loaded) => {
      if (!active) return;
      setReads((prior) => ({ ...prior, events: loaded }));
      if (loaded.status === "loaded") setLastEvents(loaded.value);
    });
    return () => {
      active = false;
    };
  }, [client, siteId, actionId, eventId, recordedAt, reload]);

  const body = reads.action?.status === "loaded" ? reads.action.value : lastAction;
  const events = reads.events?.status === "loaded" ? reads.events.value : lastEvents;
  const title = body ? `${body.action.action_code} · Battery reserve trial` : "Action";
  useEffect(() => {
    onTitle?.(title);
  }, [onTitle, title]);

  const loading = (
    <>
      {reads.action === null ? <p>Loading the Action.</p> : null}
      {reads.events === null ? <p>Loading the Action's events.</p> : null}
    </>
  );
  const actionRefusal = reads.action?.status === "refused" ? reads.action : null;
  const eventsRefusal = reads.events?.status === "refused" ? reads.events : null;

  if (body === null) {
    if (actionRefusal === null) return loading;
    // W1-F4: a page-level refusal before the selected view's panel slots, each with its gap inside.
    if (actionRefusal.code === "ACTION_EVENT_NOT_FOUND") {
      return (
        <div className="site-action w1f4-action" data-action-unread="selection-not-found">
          <SelectionNotFound refusal={actionRefusal} view={view} selector={selector} links={links} />
          <ViewSkeleton view={view} gap="The selected record is not shown: the address names an event this Action does not have." />
        </div>
      );
    }
    return (
      <div className="site-action w1f4-action" data-action-unread="refused">
        <PageRefusal refusal={actionRefusal} subject="Action" name="action">
          {actionRefusal.code === "ACTION_SELECTOR_CONFLICT" ? (
            <SelectorConflict view={view} selector={selector} links={links} />
          ) : null}
        </PageRefusal>
        {reads.events === null ? <p>Loading the Action's events.</p> : null}
        <ViewSkeleton view={view} gap="Not shown: the Action could not be read." />
      </div>
    );
  }

  // W1-F4: the shell around every view is only page-level refusals (never a panel); each view owns its panels.
  const own = view === "overview" || view === "execution" || view === "history";
  return (
    <div
      className="site-action w1f4-action"
      data-action-id={body.action.id}
      data-action-application={body.state.application}
      data-action-outcome={body.state.outcome.state}
      data-action-selection={body.selection.kind}
    >
      {loading}
      {actionRefusal ? (
        <PageRefusal refusal={actionRefusal} subject="Action" name="action-reread">
          <p className="action-note">The last successful read is still shown below.</p>
        </PageRefusal>
      ) : null}
      {eventsRefusal ? (
        <PageRefusal refusal={eventsRefusal} subject="Action events" name="action-events">
          {lastEvents ? <p className="action-note">The last successful read is still shown below.</p> : null}
        </PageRefusal>
      ) : null}
      {/* OUT-A A5: one Affects line above every view (overview, application, history, plan, evidence, verification). */}
      <AffectsLine categories={body.categories} variant="action" />
      {view === "overview" ? (
        <Overview body={body} links={links} />
      ) : view === "execution" ? (
        <Application
          body={body}
          events={events}
          eventsRead={reads.events !== null}
          siteId={siteId}
          client={client}
          links={links}
          outcome={outcome}
          onOutcome={(result) => {
            setOutcome(result);
            setReload((n) => n + 1);
          }}
        />
      ) : view === "history" ? (
        <History body={body} events={events} eventsRead={reads.events !== null} links={links} view={view} siteId={siteId} actionId={actionId} verification={verification} />
      ) : null}
      {own ? null : (
        <ActionVerification
          siteId={siteId}
          actionId={actionId}
          view={view}
          selection={{ eventId, recordedAt, planRevisionId, outcomeId }}
          body={body}
          client={verification}
          links={{
            view: (target, chosen) =>
              links.view(target, {
                eventId: null,
                recordedAt: chosen.recordedAt ?? null,
                planRevisionId: chosen.planRevisionId ?? null,
                outcomeId: chosen.outcomeId ?? null,
              }),
            change: links.change,
            event: (id) => links.view("history", { eventId: id, recordedAt: null }),
            finding: links.finding,
            evidenceRecord: links.evidenceRecord ?? ((id) => `#evidence-${id}`),
          }}
        />
      )}
    </div>
  );
}

/** The v69 panel titles of each Action view (`v69-rendered-panels.json`), for the unread skeleton. */
const VIEW_PANELS: Record<ActionView, readonly string[]> = {
  overview: ["Action scope"],
  plan: ["Success criteria"],
  execution: ["Activity log"],
  evidence: ["Evidence requirements"],
  verification: ["Target and guardrails evaluated together", "Activity evidence", "Outcome evidence"],
  history: ["Action history"],
};

/** The selected view's panel slots when the Action itself was not read, with the gap inside each. */
function ViewSkeleton({ view, gap }: { view: ActionView; gap: string }) {
  const panels = VIEW_PANELS[view];
  const slots = panels.map((title, index) => (
    <Panel key={title} heading={title} headingId={`site-action-unread-${index}-heading`}>
      <p className="v69-chart-note w1f4-action-gap-note" data-panel-gap="action-unread">
        {gap}
      </p>
    </Panel>
  ));
  if (view !== "verification") return <>{slots}</>;
  return (
    <>
      {slots[0]}
      <div className="panel-pair">
        {slots[1]}
        {slots[2]}
      </div>
    </>
  );
}

const REFUSAL_TITLES: Record<number, string> = {
  401: "Sign-in required",
  403: "No access",
  404: "Not found",
  409: "Refused",
  422: "Refused",
};

/**
 * A typed read refusal stated before the panel slots (W1-F1 page-refusal rule):
 * the same words and attributes as the shared refusal panel, never a panel or
 * a heading of its own.
 */
function PageRefusal({ refusal, subject, name, children }: { refusal: Refusal; subject: string; name: string; children?: ReactNode }) {
  const title =
    refusal.http === null
      ? `${subject} unavailable`
      : refusal.http === 404
        ? `${subject} not found`
        : (REFUSAL_TITLES[refusal.http] ?? `${subject} unavailable`);
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
  return (
    <div className="page-refusal" role="status" data-page-refusal={name}>
      <p className="page-refusal__title">
        <strong>{title}</strong>
      </p>
      <p data-action-read="refused" data-action-http={refusal.http ?? "none"} data-action-code={refusal.code ?? ""}>
        {text}
        {refusal.code ? (
          <>
            {" "}
            Code: <Ref value={refusal.code} />.
          </>
        ) : null}
      </p>
      {refusal.message ? <p className="action-note">Reason given: {refusal.message}</p> : null}
      {children}
    </div>
  );
}

/**
 * A 404 for the selected event or cutoff, not for the Action (phase-1 review
 * M1): the Action exists, the address names an event it does not have.
 */
function SelectionNotFound({
  refusal,
  view,
  selector,
  links,
}: {
  refusal: Refusal;
  view: ActionView;
  selector: EventSelector;
  links: SiteActionLinks;
}) {
  const what = selector.eventId !== null ? "event" : "recorded time";
  return (
    <div className="page-refusal" role="status" data-page-refusal="selection-not-found">
      <p className="page-refusal__title">
        <strong>{`Selected ${what} not found`}</strong>
      </p>
      <p data-action-read="selection-not-found" data-action-http={refusal.http ?? "none"} data-action-code={refusal.code ?? ""}>
        {selector.eventId !== null
          ? "This Action has no event with the ID in the address."
          : "This Action has no event recorded through the time in the address."}{" "}
        The Action itself is not in question. Code: <Ref value={refusal.code ?? "UNKNOWN"} />.{" "}
        <Link to={links.view(view, LATEST)} data-action-open-latest>
          Open the latest record of this Action
        </Link>
      </p>
    </div>
  );
}

function SelectorConflict({ view, selector, links }: { view: ActionView; selector: EventSelector; links: SiteActionLinks }) {
  return (
    <p className="action-note" data-action-selector-conflict>
      The address names both an exact event and a recorded time, so nothing was chosen for you. Open{" "}
      {selector.eventId ? (
        <Link to={links.view(view, { eventId: selector.eventId, recordedAt: null })}>the exact event only</Link>
      ) : null}
      {" or "}
      {selector.recordedAt ? (
        <Link to={links.view(view, { eventId: null, recordedAt: selector.recordedAt })}>everything recorded through that time</Link>
      ) : null}
      .
    </p>
  );
}

/**
 * The selected record, as one in-panel note line (W1-F4: formerly an
 * "Earlier record selected" panel above the view). An earlier selection says
 * so and links the latest.
 */
function SelectionNote({
  selection,
  view,
  links,
  inline = false,
}: {
  selection: Selection;
  view: ActionView;
  links: SiteActionLinks;
  /** W1-F4 trim: the latest-record count as a part of an existing note line. */
  inline?: boolean;
}) {
  if (selection.kind === "LATEST") {
    if (inline) {
      return (
        <span data-action-selection-notice="LATEST">
          Latest at read time: {selection.event_count} of {selection.total_event_count} events.
        </span>
      );
    }
    return (
      <ChartNote data={{ "data-action-selection-notice": "LATEST" }}>
        Latest at read time: {selection.event_count} of {selection.total_event_count} events.
      </ChartNote>
    );
  }
  return (
    <p
      className="v69-chart-note w1f4-action-earlier"
      data-action-selection-notice={selection.kind}
      data-action-cutoff-event={selection.cutoff_event_id ?? ""}
    >
      <strong>Earlier record.</strong>{" "}
      {selection.kind === "EVENT_ID" ? "Showing the Action as recorded through one exact event" : "Showing everything recorded through"}{" "}
      {selection.kind === "RECORDED_AT" ? when(selection.recorded_at) : null}: {selection.event_count} of{" "}
      {selection.total_event_count} events, in server recorded order.
      {selection.cutoff_event_id ? (
        <>
          {" "}
          Last included event: <Ref value={selection.cutoff_event_id} />, recorded {when(selection.cutoff_recorded_at)}.
        </>
      ) : null}{" "}
      <Link to={links.view(view, LATEST)} data-action-latest-link data-action-history-latest-link={view === "history" ? "" : undefined}>
        Show the latest
      </Link>
    </p>
  );
}

const OUTCOME_STATES = new Set(["VERIFIED", "INEFFECTIVE", "INCONCLUSIVE"]);

type BadgeTone = "green" | "amber" | "red" | "blue" | "muted";
const TONE_BADGE: Record<ProductTone, BadgeTone> = {
  positive: "green",
  limited: "amber",
  waiting: "amber",
  problem: "red",
  neutral: "blue",
};

/** The mock's `.badge` with its tone; the word is always the visible text. */
function StateBadge({ tone, children, data }: { tone: BadgeTone; children: ReactNode; data?: Record<string, string> }) {
  return (
    <span className={`w1f4-action-badge w1f4-action-badge--${tone}`} {...data}>
      {children}
    </span>
  );
}

/** The plain scope and "as of" bound of a state line, as one note part. */
function Bound({ asOf }: { asOf: string | null }) {
  return (
    <>
      <span data-product-status-scope>This Action, from its recorded events</span>
      <span aria-hidden="true"> · </span>
      <span data-product-status-as-of>{asOfText(asOf)}</span>
    </>
  );
}

/**
 * v69 `action-overview` panel 1, "Action scope" (W1-F4): the mock's key values
 * (Action, Source, Owner, Intervention, Outcome) from the Action read, with the
 * former answer card, Origin, Latest Finding version, Accepted trial and
 * Foundation change merged in. Detailed activity is on Execution; the result is
 * on Verification. The state word, scope and as-of stay outside the closed
 * disclosure.
 */
function Overview({ body, links }: { body: ActionBody; links: SiteActionLinks }) {
  const accepted = body.accepted_recommendation;
  const notice = body.newer_revision_notice;
  const change = body.change;
  const v = body.verification ?? null;
  const verificationState = v === null ? body.state.outcome.state : v.state;
  const words = productOutcomeWords(verificationState, v === null ? [] : v.reasons, null);
  const application = APPLICATION_WORDS[body.state.application] ?? "Application state not recognised";
  const source = sourceState(body.source_provenance);
  const sourceWords = SOURCE_WORDS[source];
  const latest = body.selection.kind === "LATEST";
  return (
    <Panel heading="Action scope" headingId="site-action-scope-heading" className="w1f4-action-panel">
      <div data-product-status={words.tone} data-action-scope>
        <KeyValues
          label="Action scope"
          rows={[
            [
              "Action",
              <>
                {body.action.action_code} · Battery reserve trial, accepted {when(body.state.accepted_at)}
              </>,
              "action",
            ],
            [
              "Source",
              <span data-action-origin-revision={body.origin.finding_revision_id}>
                <Link to={links.finding(body.origin.finding_id, body.origin.finding_revision_id)} data-action-origin-link>
                  Finding version
                </Link>{" "}
                ·{" "}
                <Link to={links.recommendation(body.origin.finding_id, body.origin.finding_revision_id)} data-action-recommendation-link>
                  Recommendation
                </Link>
                {notice ? (
                  <span data-action-newer-revision={notice.latest_revision_id}>
                    {" "}
                    · Finding{" "}
                    <Link to={links.finding(body.origin.finding_id, notice.latest_revision_id)}>version {notice.revision_no}</Link> is newer;
                    this Action keeps its own
                  </span>
                ) : (
                  <span data-action-newer-revision="none" />
                )}
              </span>,
              "source",
            ],
            [
              "Owner",
              <span className="w1f4-action-gap" data-panel-gap="owner">
                Not recorded
              </span>,
              "owner",
            ],
            [
              "Intervention",
              <span data-action-accepted-value={accepted.proposed_value}>
                Battery reserve {accepted.old_value}
                {accepted.unit} to {accepted.proposed_value}
                {accepted.unit}
              </span>,
              "intervention",
            ],
            [
              "Application",
              <>
                <span data-action-application-words>{application}</span>
                {body.state.failed_attempts > 0 ? ` (${body.state.failed_attempts} failed attempts)` : ""}
                {change ? (
                  <span data-action-change={change.change_id}>
                    {" "}
                    ·{" "}
                    <Link to={links.change(change.change_id)} data-action-change-link>
                      {change.old_value}
                      {change.unit} to {change.new_value}
                      {change.unit}
                    </Link>{" "}
                    from {when(change.effective_from)} ·{" "}
                    <Link to={links.view("history", { eventId: change.applied_event_id, recordedAt: null })} data-action-applied-event-link>
                      event
                    </Link>
                  </span>
                ) : null}
              </>,
              "application",
            ],
            [
              "Outcome",
              <>
                <StateBadge tone={TONE_BADGE[words.tone]} data={{ "data-product-status-label": "" }}>
                  {words.label}
                </StateBadge>{" "}
                {v ? (
                  <Link to={links.view("verification", LATEST)} data-action-verification-link>
                    Verification
                  </Link>
                ) : (
                  <Link to={links.view("verification", LATEST)}>Verification</Link>
                )}
              </>,
              "outcome",
            ],
          ]}
        />
        <p className="v69-chart-note" data-action-outcome-line>
          <span className="product-status__sentence">{words.sentence}</span>{" "}
          {v ? (
            // The qualified state sentence is on the line above; a repeat would drop its qualifier (VERIFIED) or say it twice (NO_PLAN).
            v.state === "VERIFIED" || v.state === "NO_PLAN" ? (
              <span data-action-verification-state={v.state} />
            ) : (
              <span data-action-outcome-words data-action-verification-state={v.state}>
                {stateLabel(v.state, v.reasons)}.
              </span>
            )
          ) : (
            <span data-action-outcome-words>{outcomeWords(body.state.outcome.state)}</span>
          )}{" "}
          {OUTCOME_STATES.has(verificationState) ? (
            <span data-action-outcome-source-note>
              In this summary no savings or realized benefit is claimed; the source and measured limits are on Verification.{" "}
            </span>
          ) : null}
          <Bound asOf={body.selection.cutoff_recorded_at ?? body.last_event?.recorded_at ?? null} />
          {latest ? (
            <>
              <span aria-hidden="true"> · </span>
              <SelectionNote selection={body.selection} view="overview" links={links} inline />
            </>
          ) : null}
        </p>
      </div>
      <p className="v69-chart-note">
        <span data-action-limitation={accepted.limitation.code}>
          <strong>Trial only.</strong> It tests whether the reserve setting matters; it predicts no less generator time, saving or
          safety effect.
        </span>{" "}
        <span data-source-provenance={source} data-source-provenance-subject="action-origin">
          <strong>{sourceWords.label}.</strong> {sourceWords.statement}
        </span>
      </p>
      {latest ? null : <SelectionNote selection={body.selection} view="overview" links={links} />}
      <ExactReferences
        name="action-state-references"
        variant="tech"
        references={[
          { label: "Action code", value: body.action.action_code },
          { label: "Action reference", value: body.action.id },
          { label: "Accepted at", value: body.state.accepted_at },
          { label: "Origin Finding version", value: body.origin.finding_revision_id },
          ...(notice ? [{ label: "Newer Finding version", value: notice.latest_revision_id }] : []),
          { label: "Rule", value: `${accepted.rule_id} v${accepted.rule_version}` },
          { label: "Trial limitation, in full", value: limitationText(accepted.limitation) },
          { label: "Application state", value: body.state.application },
          { label: "Trial state", value: verificationState },
          { label: "Configuration basis", value: body.basis.foundation_revision_id },
          ...(change
            ? [
                { label: "Change record", value: change.change_id },
                { label: "New configuration version", value: change.new_foundation_revision_id },
              ]
            : []),
          { label: "Assessment periods", value: String(body.basis.assessments.length) },
          { label: "Battery charge readings", value: String(body.basis.evidence.length) },
          { label: "Input reference", value: body.basis.input_sha256 },
          ...(body.source_provenance?.reasons ?? []).map((r, i) => ({ label: `Source note ${i + 1}`, value: r.code })),
          ...(v === null
            ? []
            : [
                { label: "Trial plan reference", value: v.plan_id },
                { label: "Trial outcome reference", value: v.outcome_id },
                ...v.reasons.map((reason, i) => ({ label: `Recorded reason ${i + 1}`, value: reason })),
              ]),
        ]}
      />
    </Panel>
  );
}

/**
 * The default effective time: the next UTC midnight after the later of the
 * read time and now, so a page left open past midnight never defaults to a
 * past instant (phase-1 review L1).
 */
function nextUtcMidnight(after: string | null | undefined): string {
  const read = after ? new Date(after) : null;
  const now = new Date();
  const base = read !== null && read.getTime() > now.getTime() ? read : now;
  const day = new Date(Date.UTC(base.getUTCFullYear(), base.getUTCMonth(), base.getUTCDate() + 1));
  return day.toISOString().slice(0, 16);
}

/** The plain "as of" instant of a selected Action read: the cutoff, else the last recorded event. */
function actionAsOf(body: ActionBody): string | null {
  return body.selection.cutoff_recorded_at ?? body.last_event?.recorded_at ?? null;
}

const EVENT_BADGE: Record<string, [string, BadgeTone]> = {
  ACCEPTED: ["Accepted", "blue"],
  APPLIED: ["Applied", "blue"],
  FAILED: ["Failed", "red"],
  OBSERVED: ["Note", "muted"],
  RESOLVED: ["Resolved", "blue"],
  RESOLUTION_WITHDRAWN: ["Resolution withdrawn", "muted"],
};

/** W1-F4 trim: the Activity log and Action history show this many latest rows by default (as the mock does). */
const SHOWN_ROWS = 3;

/** The exact selector an events read was cut to, so a "show all" link keeps the selected record. */
function selectorOf(selection: Selection): EventSelector {
  if (selection.kind === "EVENT_ID") return { eventId: selection.event_id ?? null, recordedAt: null };
  if (selection.kind === "RECORDED_AT") return { eventId: null, recordedAt: selection.recorded_at ?? null };
  return LATEST;
}

/**
 * v69 `action-execution` panel 1, "Activity log" (W1-F4): the application
 * state as one status line, the latest recorded events (Record | State |
 * Evidence, with time and actor) and the apply control, in one panel. The full
 * list, the failure codes and the "happened at" times are on History; the
 * exact references are in the closed disclosure. Applied is a recorded
 * setting, never a measured effect.
 */
function Application({
  body,
  events,
  eventsRead,
  siteId,
  client,
  links,
  outcome,
  onOutcome,
}: {
  body: ActionBody;
  events: ActionEventsBody | null;
  eventsRead: boolean;
  siteId: string;
  client: ActionClient;
  links: SiteActionLinks;
  outcome: CommandResult | null;
  onOutcome: (result: CommandResult) => void;
}) {
  const basis = body.application_basis;
  const readAt = basis?.read_at ?? body.state.accepted_at;
  const [effective, setEffective] = useState(() => nextUtcMidnight(readAt));
  // Untouched, the default is re-derived when the command is sent; an edited value is the operator's own.
  const [edited, setEdited] = useState(false);
  const [busy, setBusy] = useState(false);
  const capability = body.system_demo_capability?.apply;
  const latest = body.selection.kind === "LATEST";
  const pending = body.state.application === "PENDING";
  // A cleared field is never sent: Apply stays disabled until a time is given (S6-01b review L3).
  const noTime = edited && effective.trim() === "";
  const v = body.verification ?? null;
  const verificationState = v === null ? body.state.outcome.state : v.state;
  const trial = productOutcomeWords(verificationState, v === null ? [] : v.reasons, null);
  const words = applicationWords(body.state.application, body.state.failed_attempts);
  const failed = body.state.failed_attempts;
  const attempts = body.state.application_attempts;
  const all = events?.events ?? [];
  const services = Array.from(new Set(all.map((e) => [e.triggering_service ?? "none", e.triggering_job].filter(Boolean).join(" / "))));

  const apply = async () => {
    if (busy || noTime || basis?.current_foundation_revision_id == null) return;
    setBusy(true);
    const sent = edited ? effective : nextUtcMidnight(readAt);
    if (sent !== effective) setEffective(sent);
    const result = await client.apply(siteId, body.action.id, {
      value: body.accepted_recommendation.proposed_value,
      expected_foundation_revision_id: basis.current_foundation_revision_id,
      effective_from: `${sent}:00+00:00`,
      idempotency_key: freshIdempotencyKey(),
    });
    setBusy(false);
    onOutcome(result);
  };

  const historyLink = (
    <Link to={links.view("history", events ? selectorOf(events.selection) : LATEST)} data-action-work-history-link>
      {all.length > SHOWN_ROWS ? `Show all ${all.length} steps` : "Open History"}
    </Link>
  );

  return (
    <Panel heading="Activity log" headingId="site-action-activity-heading" className="w1f4-action-panel">
      <div data-product-status={words.tone} data-action-work>
        <p className="v69-chart-note w1f4-action-status">
          <StateBadge tone={TONE_BADGE[words.tone]} data={{ "data-product-status-label": "", "data-action-work-headline": "" }}>
            {words.label}
          </StateBadge>{" "}
          <span data-key-value="attempts">
            Attempts: {attempts} recorded, {failed} failed
          </span>
          <span aria-hidden="true"> · </span>
          <span data-key-value="trial">Trial outcome: {trial.label}</span>
          <span aria-hidden="true"> · </span>
          <Bound asOf={actionAsOf(body)} />
        </p>
        <p className="v69-chart-note">
          <span className="product-status__sentence">{words.sentence}</span> Whether it helped, within its safety and service
          limits, is judged only on{" "}
          <Link to={links.view("verification", LATEST)} data-action-work-verification-link>
            Verification
          </Link>
          .
          {latest ? (
            <>
              {" "}
              <SelectionNote selection={body.selection} view="execution" links={links} inline />
            </>
          ) : null}
        </p>
      </div>
      {latest ? null : <SelectionNote selection={body.selection} view="execution" links={links} />}
      {events ? (
        <EventTable
          events={all.slice(-SHOWN_ROWS)}
          change={body.change}
          selection={events.selection}
          links={links}
          view="execution"
          mode="log"
        />
      ) : eventsRead ? (
        <p className="v69-chart-note w1f4-action-gap-note" data-panel-gap="action-events">
          The recorded activity could not be read, so no activity is listed.
        </p>
      ) : null}
      <div className="w1f4-action-apply" data-action-apply>
        {!latest ? (
          <ChartNote>Commands are offered on the latest record only.</ChartNote>
        ) : !pending ? (
          <p className="v69-chart-note">
            {historyLink} · <span data-action-already-applied>Applied; there is nothing more to apply.</span>
          </p>
        ) : granted(capability, "APPLY") && !basis?.current_foundation_revision_id ? (
          <ChartNote data={{ "data-action-apply-no-basis": "" }}>
            Applying is not offered: the read did not state the current Foundation version, so the command could not
            name the version it expects. Reload to read it again.
          </ChartNote>
        ) : granted(capability, "APPLY") ? (
          <>
            <p className="v69-chart-note">
              Applying publishes the accepted reserve ({body.accepted_recommendation.proposed_value}
              {body.accepted_recommendation.unit}) as a new Site Foundation version ({SYSTEM_DEMONSTRATION}); no effect is stated or measured.
              {basis ? (
                <span data-action-expected-foundation={basis.current_foundation_revision_id ?? ""}>
                  {" "}
                  A Foundation change since the read ({when(basis.covers_instant)}) makes it fail as stale.
                </span>
              ) : null}
            </p>
            <div className="form-footer">
              <label className="field w1f4-action-field">
                Effective from (UTC)
                <input
                  type="datetime-local"
                  value={effective}
                  onChange={(event) => {
                    setEdited(true);
                    setEffective(event.target.value);
                  }}
                  data-action-effective-from
                />
              </label>
              <button
                type="button"
                className="button primary"
                data-action-command="APPLY"
                aria-busy={busy}
                disabled={noTime}
                aria-describedby={noTime ? "site-action-apply-no-time" : undefined}
                onClick={() => void apply()}
              >
                Apply trial ({SYSTEM_DEMONSTRATION})
              </button>
            </div>
            {noTime ? (
              <p id="site-action-apply-no-time" className="v69-chart-note" data-action-apply-no-time>
                Enter the effective time to apply.
              </p>
            ) : null}
          </>
        ) : (
          <CommandUnavailable capability={capability} what="Applying" />
        )}
        <ApplyOutcome outcome={outcome} links={links} />
      </div>
      {latest && !pending ? null : <p className="v69-chart-note">{historyLink}</p>}
      <ExactReferences
        name="action-work-references"
        variant="tech"
        references={[
          { label: "Action reference", value: body.action.id },
          { label: "Application state", value: body.state.application },
          { label: "Last failed attempt reason", value: body.state.last_failure?.failure_code ?? null },
          { label: "Last failed attempt at", value: body.state.last_failure?.recorded_at ?? null },
          { label: "Expected current Foundation version", value: basis?.current_foundation_revision_id ?? null },
          { label: "Change record", value: body.change?.change_id ?? null },
          { label: "New site configuration version", value: body.change?.new_foundation_revision_id ?? null },
          ...services.map((service, i) => ({ label: `Recording service ${i + 1}`, value: service })),
        ]}
      />
    </Panel>
  );
}

function ApplyOutcome({ outcome, links }: { outcome: CommandResult | null; links: SiteActionLinks }) {
  if (outcome === null) return null;
  if (outcome.status === "done") {
    return (
      <p role="status" data-action-command-done={outcome.replayed ? "replayed" : "applied"}>
        {outcome.replayed ? "This command was already recorded." : "Applied to the Site Foundation."}{" "}
        {outcome.event ? (
          <Link to={links.view("history", { eventId: outcome.event.id, recordedAt: null })}>Open the event</Link>
        ) : null}
      </p>
    );
  }
  const event = outcome.detail?.event as ActionEvent | undefined;
  const applied = typeof outcome.detail?.applied_event_id === "string" ? outcome.detail.applied_event_id : null;
  return (
    <CommandRefusal refusal={outcome}>
      {event && event.kind === "FAILED" ? (
        <p className="action-note" data-action-failed-event={event.id}>
          {outcome.detail?.replayed === true ? "This repeats an earlier attempt; the stored failed attempt is shown. " : "A failed attempt was recorded. "}
          The application is still pending.{" "}
          <Link to={links.view("history", { eventId: event.id, recordedAt: null })}>Open the failed attempt</Link>
        </p>
      ) : null}
      {applied ? (
        <p className="action-note" data-action-already-applied-event={applied}>
          Already applied; nothing was attempted.{" "}
          <Link to={links.view("history", { eventId: applied, recordedAt: null })}>Open the application event</Link>
        </p>
      ) : null}
    </CommandRefusal>
  );
}


/**
 * v69 `action-history` panel 1, "Action history" (W1-F4): the recorded events
 * and the verification outcome history (earlier and current labels, the
 * withdrawable resolution) as one Event | Meaning table in recorded order, with
 * the exact event and recorded-time selection kept in each event row. The
 * latest rows show by default with an in-place "Show all" toggle; an earlier
 * selection's events (already cut to it) always stay shown. An earlier selection is historical and says so;
 * the verification rows are read as recorded now and are never cut to the
 * selected event.
 */
function History({
  body,
  events,
  eventsRead,
  links,
  view,
  siteId,
  actionId,
  verification,
}: {
  body: ActionBody;
  events: ActionEventsBody | null;
  eventsRead: boolean;
  links: SiteActionLinks;
  view: ActionView;
  siteId: string;
  actionId: string;
  verification: VerificationClient;
}) {
  const [outcomes, setOutcomes] = useState<ActionReadResult<HistoryBody> | null>(null);
  const [showAll, setShowAll] = useState(false);
  useEffect(() => {
    let active = true;
    setOutcomes(null);
    void verification.getHistory(siteId, actionId).then((read) => {
      if (active) setOutcomes(read);
    });
    return () => {
      active = false;
    };
  }, [verification, siteId, actionId]);
  const latest = body.selection.kind === "LATEST";
  const words = latest
    ? {
        label: "Every recorded event",
        sentence: "This is everything recorded for this Action when the page was read.",
        tone: "neutral" as const,
      }
    : currentnessWords("HISTORICAL");
  const selected = body.selection.kind === "EVENT_ID" ? body.selection.event_id : null;
  const history = outcomes?.status === "loaded" ? outcomes.value : null;
  return (
    <Panel heading="Action history" headingId="site-action-history-heading" className="w1f4-action-panel">
      <p className="v69-chart-note w1f4-action-status" data-product-status={words.tone}>
        <StateBadge tone={TONE_BADGE[words.tone]} data={{ "data-product-status-label": "" }}>
          {words.label}
        </StateBadge>{" "}
        <span className="product-status__sentence">{words.sentence}</span> <Bound asOf={actionAsOf(body)} />
        {latest ? (
          <>
            {/* post-W6 W1-b Q30 / R219: the default history's chip; the server's raw event counts sit only in the
                exact references below. */}
            <span aria-hidden="true"> · </span>
            <StateBadge tone="muted" data={{ "data-action-history-latest": "" }}>
              Latest at read time
            </StateBadge>
          </>
        ) : null}
      </p>
      {latest ? null : <SelectionNote selection={body.selection} view={view} links={links} />}
      {events ? (
        <EventTable
          events={events.events}
          change={body.change}
          selection={events.selection}
          links={links}
          view={view}
          mode="history"
          verification={history}
          showAll={showAll}
        />
      ) : eventsRead ? (
        <p className="v69-chart-note w1f4-action-gap-note" data-panel-gap="action-events">
          The recorded events could not be read, so no event is listed.
        </p>
      ) : null}
      {(() => {
        // post-W6 W1-b Q30 / R219: both counts are the de-duplicated union of recorded entries (Q29); with three or
        // fewer every entry shows and neither the truncation sentence nor a toggle appears.
        const rows = events === null ? [] : historyRows(events.events, history, "history");
        const total = rows.length;
        const shownCount = events === null ? 0 : shownHistoryRows(rows, events.selection, showAll, false).length;
        const more =
          events !== null && total > SHOWN_ROWS ? (
            <>
              {showAll ? null : (
                <span data-action-history-truncated>
                  Showing the latest {shownCount} of {total} recorded entries; show all to see every entry.{" "}
                </span>
              )}
              <button
                type="button"
                className="w1f4-action-more"
                aria-expanded={showAll}
                data-action-history-show-all
                onClick={() => setShowAll((open) => !open)}
              >
                {showAll ? `Show the latest ${SHOWN_ROWS}` : `Show all ${total} entries`}
              </button>
            </>
          ) : null;
        if (outcomes !== null && outcomes.status !== "loaded") {
          return (
            <>
              {more ? <p className="v69-chart-note">{more}</p> : null}
              <p
                className="v69-chart-note w1f4-action-gap-note"
                data-panel-gap="verification-history"
                data-action-history-outcomes="unread"
                data-action-http={outcomes.status === "refused" ? (outcomes.http ?? "none") : "none"}
              >
                The verification history could not be read, so no trial outcome is listed here.
              </p>
            </>
          );
        }
        // One note line under the table: the show-all toggle and the outcomes note.
        return (
          <p className="v69-chart-note">
            {more}
            {more ? <span aria-hidden="true"> · </span> : null}
            {outcomes === null ? (
              <span>Loading the verification history.</span>
            ) : history !== null && history.outcomes.length === 0 && history.resolution_events.length === 0 ? (
              <span data-action-history-outcomes="none">No trial outcome recorded yet.</span>
            ) : (
              <span data-action-history-outcomes="listed">
                Trial outcomes are the verification history as recorded now{latest ? "" : ", not cut to the selected record"}; a
                resolution records the current outcome, and later evidence can withdraw it. No event measures an effect; a trial
                result appears only on <Link to={links.view("verification", LATEST)}>Verification</Link>.
              </span>
            )}
          </p>
        );
      })()}
      <ExactReferences
        name="action-history-references"
        variant="tech"
        references={[
          { label: "Action reference", value: body.action.id },
          { label: "Selected event", value: selected ?? null },
          { label: "Selected recorded time", value: body.selection.kind === "RECORDED_AT" ? (body.selection.recorded_at ?? null) : null },
          { label: "Last included event", value: body.selection.cutoff_event_id ?? null },
          {
            label: "Recorded events at read time",
            value:
              body.selection.kind === "LATEST" ? `${body.selection.event_count} of ${body.selection.total_event_count}` : null,
          },
        ]}
      />
    </Panel>
  );
}

function resolutionWords(kind: string): string {
  return kind === "RESOLVED" ? "Resolved" : kind === "RESOLUTION_WITHDRAWN" ? "Resolution withdrawn" : "Recorded event";
}

/** post-W6 W1-b Q29 / R218: the ruled meanings; an unrecognised kind never borrows another kind's meaning. */
export const RESOLVED_MEANING = "The evaluator settled the outcome for this Action.";
export const RESOLUTION_WITHDRAWN_MEANING = "The evaluator withdrew an earlier outcome; the Action is open for a new outcome.";
export const UNKNOWN_EVENT_MEANING = "Recorded event; its meaning is not shown in this build.";
function resolutionMeaning(kind: string): string {
  return kind === "RESOLVED" ? RESOLVED_MEANING : kind === "RESOLUTION_WITHDRAWN" ? RESOLUTION_WITHDRAWN_MEANING : UNKNOWN_EVENT_MEANING;
}

type HistoryRow =
  | { kind: "event"; at: number; event: ActionEvent }
  | { kind: "outcome"; at: number; outcome: HistoryBody["outcomes"][number]; current: boolean }
  | { kind: "resolution"; at: number; resolution: HistoryBody["resolution_events"][number] };

/**
 * post-W6 W1-b Q29 / R218: the History rows, one per recorded entry. An Action event that is also a detailed
 * resolution event (same ID) is shown once, as the resolution row. History sorts by recorded time; the Activity log
 * keeps server order. Q30 / R219: `total` is this de-duplicated union, the count the reader is told about.
 */
export function historyRows(
  events: ActionEvent[],
  verification: HistoryBody | null,
  mode: "log" | "history",
): HistoryRow[] {
  const outcomes = verification?.outcomes ?? [];
  const resolutions = verification?.resolution_events ?? [];
  const resolutionIds = new Set(resolutions.map((r) => r.id));
  const time = (instant: string) => {
    const at = Date.parse(instant);
    return Number.isNaN(at) ? Number.POSITIVE_INFINITY : at;
  };
  const merged: HistoryRow[] = [
    ...events.filter((event) => !resolutionIds.has(event.id)).map((event): HistoryRow => ({ kind: "event", at: time(event.recorded_at), event })),
    ...outcomes.map((outcome, i): HistoryRow => ({ kind: "outcome", at: time(outcome.recorded_at), outcome, current: i === outcomes.length - 1 })),
    ...resolutions.map((resolution): HistoryRow => ({ kind: "resolution", at: time(resolution.recorded_at), resolution })),
  ];
  return mode === "log" ? merged : [...merged].sort((a, b) => a.at - b.at);
}

/** The rows History shows: the latest `SHOWN_ROWS` unless `showAll`; an earlier selection's events always stay. */
function shownHistoryRows(rows: HistoryRow[], selection: Selection, showAll: boolean, log: boolean): HistoryRow[] {
  const isSelected = (event: ActionEvent) => selection.kind === "EVENT_ID" && selection.event_id === event.id;
  const firstShown = showAll || log ? 0 : Math.max(0, rows.length - SHOWN_ROWS);
  const keepEvents = selection.kind !== "LATEST";
  return rows.filter((row, index) => index >= firstShown || (row.kind === "event" && (keepEvents || isSelected(row.event))));
}

/**
 * The recorded events as the mock's table: on Execution `Record | State |
 * Evidence` with time and actor (the caller passes the latest rows), on
 * History `Event | Meaning` with time and the exact selection links, merged
 * in recorded order with the verification outcome rows. History shows the
 * latest rows unless `showAll`; a selected event is always kept.
 */
function EventTable({
  events,
  change,
  selection,
  links,
  view,
  mode,
  verification = null,
  showAll = true,
}: {
  events: ActionEvent[];
  change: PolicyChange | null;
  selection: Selection;
  links: SiteActionLinks;
  view: ActionView;
  mode: "log" | "history";
  verification?: HistoryBody | null;
  showAll?: boolean;
}) {
  const rows = historyRows(events, verification, mode);
  if (rows.length === 0) {
    return (
      <p className="v69-chart-note" data-action-events="none">
        No activity recorded.
      </p>
    );
  }
  const log = mode === "log";
  const isSelected = (event: ActionEvent) => selection.kind === "EVENT_ID" && selection.event_id === event.id;
  // An earlier selection's events read is already cut to that selection, so its events always stay shown.
  const shown = shownHistoryRows(rows, selection, showAll, log);
  const table = (
    <DataTable labelledBy={`site-action-events-caption-${mode}`}>
      <caption id={`site-action-events-caption-${mode}`} className="w1f4-action-caption">
        {log ? "Activity log" : "Action history"}
      </caption>
      <thead>
        <tr>
          {log ? (
            <>
              <th scope="col">Record</th>
              <th scope="col">State</th>
              <th scope="col">Evidence</th>
              <th scope="col">Recorded</th>
              <th scope="col">Acted by</th>
            </>
          ) : (
            <>
              <th scope="col">Event</th>
              <th scope="col">Meaning</th>
              <th scope="col">Recorded</th>
              <th scope="col">Select</th>
            </>
          )}
        </tr>
      </thead>
      <tbody>
        {events.length === 0 ? (
          <tr data-action-events="none">
            <td colSpan={log ? 5 : 4}>No activity recorded.</td>
          </tr>
        ) : null}
        {shown.map((row) => {
          if (row.kind === "outcome") {
            const o = row.outcome;
            return (
              <tr key={`outcome:${o.outcome_id}`} data-action-history-outcome={o.outcome_id}>
                <td>Trial outcome recorded</td>
                <td>
                  <Link to={links.view("verification", { eventId: null, recordedAt: null, outcomeId: o.outcome_id })}>
                    {stateLabel(o.outcome, o.reasons)}
                  </Link>{" "}
                  <StateBadge tone={row.current ? "blue" : "muted"} data={{ "data-action-history-outcome-label": row.current ? "current" : "earlier" }}>
                    {row.current ? "Most recent" : "Earlier, replaced later"}
                  </StateBadge>
                </td>
                <td>{when(o.recorded_at)}</td>
                <td />
              </tr>
            );
          }
          if (row.kind === "resolution") {
            const r = row.resolution;
            return (
              <tr key={`resolution:${r.id}`} data-action-history-resolution={r.kind} data-action-history-resolution-id={r.id}>
                <td>{resolutionWords(r.kind)}</td>
                <td>
                  {resolutionMeaning(r.kind)}
                  {r.verification_outcome_id ? (
                    <>
                      {" "}
                      <Link to={links.view("verification", { eventId: null, recordedAt: null, outcomeId: r.verification_outcome_id })}>
                        {r.kind === "RESOLUTION_WITHDRAWN" ? "Withdrawn outcome" : "Outcome"}
                      </Link>
                    </>
                  ) : null}
                </td>
                <td>{when(r.recorded_at)}</td>
                <td />
              </tr>
            );
          }
          const event = row.event;
          const [badgeWord, badgeTone] = EVENT_BADGE[event.kind] ?? ["Not recognised", "muted"];
          const times = (
            <td data-action-recorded-at={event.recorded_at} data-action-occurred-at={event.occurred_at}>
              {when(event.recorded_at)}
              {event.occurred_before_recorded ? (
                <small>
                  {log ? "(recorded later than it happened)" : <>Happened {when(event.occurred_at)}; recorded later than it happened</>}
                </small>
              ) : null}
            </td>
          );
          return (
            <tr key={`event:${event.id}`} data-action-event={event.id} data-action-event-kind={event.kind} aria-current={isSelected(event) ? "true" : undefined}>
              <td>{eventWords(event.kind)}</td>
              {log ? (
                <>
                  <td>
                    <StateBadge tone={badgeTone}>{badgeWord}</StateBadge>
                  </td>
                  <td>
                    <EventDetails event={event} change={change} links={links} compact />
                  </td>
                  {times}
                  <td data-action-event-actor>{event.actor?.label ?? event.actor_kind}</td>
                </>
              ) : (
                <>
                  <td>
                    <EventDetails event={event} change={change} links={links} />
                  </td>
                  {times}
                  <td>
                    <Link to={links.view(view, { eventId: event.id, recordedAt: null })} data-action-select-event={event.id}>
                      This event
                    </Link>{" "}
                    <Link to={links.view(view, { eventId: null, recordedAt: event.recorded_at })} data-action-select-recorded={event.recorded_at}>
                      Through this time
                    </Link>
                  </td>
                </>
              )}
            </tr>
          );
        })}
      </tbody>
    </DataTable>
  );
  return log ? table : <HistoryEntriesScroll>{table}</HistoryEntriesScroll>;
}

/**
 * post-W6 W1-b caps ruling 2 (Q37): the Action history table (header and every event row) sits in one labelled,
 * keyboard-focusable region with a vertical scroll, so the closed panel stays inside its 800 px cap at 390. The
 * count sentence and the Show all toggle stay outside. Nothing is hidden or truncated; the cue shows only when the
 * rows overflow the region. Same pattern as Interpretation history and the Finding Revision history.
 */
function HistoryEntriesScroll({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [overflows, setOverflows] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (el === null) return;
    const measure = () => setOverflows(el.scrollHeight > el.clientHeight + 1);
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    for (const child of Array.from(el.children)) observer.observe(child);
    return () => observer.disconnect();
  }, [children]);
  return (
    <>
      <p className="w1f4-action-history-cue" data-action-history-scroll-cue hidden={!overflows}>
        Scroll history to see every entry
      </p>
      <div
        ref={ref}
        className="w1f4-action-history-entries"
        role="region"
        aria-label="Action history entries"
        tabIndex={0}
        data-action-history-entries
      >
        {children}
      </div>
    </>
  );
}

/**
 * One event's evidence words. `compact` (the Activity log) is one short line
 * with no codes or IDs; History adds the exact failure code, Foundation
 * versions and change record on a small second line.
 */
function EventDetails({
  event,
  change,
  links,
  compact = false,
}: {
  event: ActionEvent;
  change: PolicyChange | null;
  links: SiteActionLinks;
  compact?: boolean;
}) {
  const changeLink =
    change && change.applied_event_id === event.id ? (
      <Link to={links.change(change.change_id)} data-action-event-change-link>
        {compact ? "Change record" : <Ref value={change.change_id} attr="data-action-event-change" />}
      </Link>
    ) : null;
  if (event.kind === "FAILED") {
    return (
      <span data-action-event-failure={event.failure_code ?? ""}>
        Nothing was changed; still pending.
        {compact ? null : (
          <small
            title={[
              event.expected_foundation_revision_id ? `expected ${event.expected_foundation_revision_id}` : "",
              event.current_foundation_revision_id ? `current ${event.current_foundation_revision_id}` : "",
            ]
              .filter(Boolean)
              .join(", ") || undefined}
          >
            <span className="w1f4-failure-code"><Ref value={event.failure_code ?? "UNKNOWN"} /></span>
            {event.expected_foundation_revision_id && event.current_foundation_revision_id ? (
              <> The Site configuration had changed since this was accepted.</>
            ) : null}
          </small>
        )}
      </span>
    );
  }
  if (event.kind === "APPLIED") {
    if (compact) {
      return <span>New Foundation version recorded{changeLink ? <> · {changeLink}</> : null}</span>;
    }
    return (
      <span>
        New Foundation version recorded
        <small>
          {event.current_foundation_revision_id ? <Ref value={event.current_foundation_revision_id} attr="data-action-event-effective-revision" /> : "version not stated"}
          {changeLink ? <>; change record {changeLink}</> : null}
        </small>
      </span>
    );
  }
  if (event.kind === "OBSERVED") {
    return (
      <span>
        A note only; it changes no application or outcome state.
        {compact ? null : (
          <small>
            <span className="w1f4-failure-code"><Ref value={event.observation_code ?? "UNKNOWN"} /></span>
          </small>
        )}
      </span>
    );
  }
  if (event.kind === "ACCEPTED") return <span>Trial accepted; nothing on the Site changed.</span>;
  // post-W6 W1-b Q29 / R218: a resolution kind has its own meaning, and an unknown kind never reads as ACCEPTED.
  return <span>{resolutionMeaning(event.kind)}</span>;
}
