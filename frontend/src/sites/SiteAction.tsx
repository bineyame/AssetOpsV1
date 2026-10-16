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
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  DataTable,
  ExactReferences,
  Fact,
  FactList,
  HeadlineVisualCard,
  currentnessWords,
  outcomeWords as productOutcomeWords,
  Panel,
  ProductStatus,
  StepStrip,
  type StepState,
} from "../ui";
import { SourceProvenanceNotice } from "./sourceProvenance";
import { ActionVerification } from "./SiteActionVerification";
import { createVerificationClient, type VerificationClient } from "./verificationClient";
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
  outcomeWords,
  plainEventWords,
  Ref,
  RefusalPanel,
  SYSTEM_DEMONSTRATION,
  TrialLimitation,
  when,
} from "./actionPresentation";

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
    if (actionRefusal.code === "ACTION_EVENT_NOT_FOUND") {
      return <SelectionNotFound refusal={actionRefusal} view={view} selector={selector} links={links} />;
    }
    return (
      <>
        <RefusalPanel refusal={actionRefusal} subject="Action" headingId="site-action-refused-heading">
          {actionRefusal.code === "ACTION_SELECTOR_CONFLICT" ? (
            <SelectorConflict view={view} selector={selector} links={links} />
          ) : null}
        </RefusalPanel>
        {reads.events === null ? <p>Loading the Action's events.</p> : null}
      </>
    );
  }

  return (
    <section
      className="site-action"
      aria-labelledby="site-action-state-heading"
      data-action-id={body.action.id}
      data-action-application={body.state.application}
      data-action-outcome={body.state.outcome.state}
      data-action-selection={body.selection.kind}
    >
      {loading}
      {actionRefusal ? (
        <RefusalPanel refusal={actionRefusal} subject="Action" headingId="site-action-reread-heading">
          <p className="action-note">The last successful read is still shown below.</p>
        </RefusalPanel>
      ) : null}
      {eventsRefusal ? (
        <RefusalPanel refusal={eventsRefusal} subject="Action events" headingId="site-action-events-refused-heading">
          {lastEvents ? <p className="action-note">The last successful read is still shown below.</p> : null}
        </RefusalPanel>
      ) : null}
      <SelectionNotice selection={body.selection} view={view} links={links} />
      {view === "overview" ? (
        <Overview body={body} links={links} />
      ) : view === "execution" ? (
        <Application
          body={body}
          events={events}
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
        <History body={body} events={events} links={links} view={view} />
      ) : (
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
    </section>
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
    <Panel heading={`Selected ${what} not found`} headingId="site-action-selection-missing-heading">
      <p data-action-read="selection-not-found" data-action-http={refusal.http ?? "none"} data-action-code={refusal.code ?? ""}>
        {selector.eventId !== null
          ? "This Action has no event with the ID in the address."
          : "This Action has no event recorded through the time in the address."}{" "}
        The Action itself is not in question.
      </p>
      <p className="action-note">
        Code: <Ref value={refusal.code ?? "UNKNOWN"} />
      </p>
      <p>
        <Link to={links.view(view, LATEST)} data-action-open-latest>
          Open the latest record of this Action
        </Link>
      </p>
    </Panel>
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

function SelectionNotice({ selection, view, links }: { selection: Selection; view: ActionView; links: SiteActionLinks }) {
  if (selection.kind === "LATEST") {
    return (
      <p className="action-note" data-action-selection-notice="LATEST">
        Latest at read time: {selection.event_count} of {selection.total_event_count} events.
      </p>
    );
  }
  return (
    <Panel heading="Earlier record selected" headingId="site-action-selection-heading">
      <p data-action-selection-notice={selection.kind} data-action-cutoff-event={selection.cutoff_event_id ?? ""}>
        {selection.kind === "EVENT_ID" ? "Showing the Action as recorded through one exact event" : "Showing everything recorded through"}{" "}
        {selection.kind === "RECORDED_AT" ? when(selection.recorded_at) : null}: {selection.event_count} of{" "}
        {selection.total_event_count} events, in server recorded order.{" "}
        <Link to={links.view(view, LATEST)} data-action-latest-link>
          Show the latest
        </Link>
      </p>
      {selection.cutoff_event_id ? (
        <p className="action-note">
          Last included event: <Ref value={selection.cutoff_event_id} />, recorded {when(selection.cutoff_recorded_at)}.
        </p>
      ) : null}
    </Panel>
  );
}

const OUTCOME_STATES = new Set(["VERIFIED", "INEFFECTIVE", "INCONCLUSIVE"]);

function trialStep(state: string): StepState {
  if (state === "VERIFIED") return "done";
  if (state === "INEFFECTIVE") return "problem";
  if (state === "NO_PLAN" || state === "PENDING" || state === "REASSESSMENT_PENDING") return "waiting";
  return "not-known";
}

/**
 * W1-UX-01: the Action's intervention and outcome state on the shared answer
 * card. The outcome words come from the shared map, keyed on the read's
 * verification state and reasons; the Overview summary carries no source
 * class, so the words never claim a demonstration or field source and the
 * card says where the source and measured limits are.
 */
function ActionStateCard({ body, links }: { body: ActionBody; links: SiteActionLinks }) {
  const v = body.verification ?? null;
  const verificationState = v === null ? body.state.outcome.state : v.state;
  const words = productOutcomeWords(verificationState, v === null ? [] : v.reasons, null);
  const applied = body.state.application === "APPLIED";
  const application = APPLICATION_WORDS[body.state.application] ?? "Application state not recognised";
  const asOf = body.selection.cutoff_recorded_at ?? body.last_event?.recorded_at ?? null;
  return (
    <HeadlineVisualCard
      dataName="action-state"
      headingId="site-action-state-heading"
      title="Action"
      description="An Action is proposed or recorded work on this site. It is not proof that anything changed."
      question="What is the current intervention and outcome state?"
      headline={
        <>
          Accepted; <span data-action-application-words>{application}</span>
          {body.state.failed_attempts > 0 ? ` (${body.state.failed_attempts} failed attempts)` : ""}
        </>
      }
      status={
        <ProductStatus words={words} scope="This Action, from its recorded events" asOf={asOf}>
          {OUTCOME_STATES.has(verificationState) ? (
            <p className="product-status__note" data-action-outcome-source-note>
              This summary does not say where the trial&apos;s readings came from, and no savings or realized benefit is
              claimed here. The source and the measured limits are on Verification.
            </p>
          ) : null}
        </ProductStatus>
      }
      visual={
        <StepStrip
          title="Where this Action stands"
          steps={[
            { label: "Accepted", state: "done", detail: when(body.state.accepted_at) },
            {
              label: "Applied",
              state: applied ? "done" : body.state.failed_attempts > 0 ? "problem" : "waiting",
              detail: applied && body.state.applied_at !== null ? when(body.state.applied_at) : application,
            },
            { label: "Trial outcome", state: trialStep(verificationState), detail: words.label },
          ]}
        />
      }
      meaning={
        <>
          {v ? (
            // The qualified state sentence is on the shared line; a repeat would drop its qualifier.
            v.state === "VERIFIED" ? (
              <span data-action-verification-state={v.state} />
            ) : (
              <p data-action-outcome-words data-action-verification-state={v.state}>
                {stateLabel(v.state, v.reasons)}.
              </p>
            )
          ) : (
            <p data-action-outcome-words>{outcomeWords(body.state.outcome.state)}</p>
          )}
          <p className="action-note">
            The Site&apos;s operation is not shown as changed by this Action, and no effect is measured here.
          </p>
        </>
      }
      todo={words.next === undefined ? undefined : <p>{words.next}</p>}
      destination={
        v ? (
          <Link to={links.view("verification", LATEST)} data-action-verification-link>
            Open Verification
          </Link>
        ) : undefined
      }
      references={
        <ExactReferences
          name="action-state-references"
          references={[
            { label: "Action code", value: body.action.action_code },
            { label: "Action reference", value: body.action.id },
            { label: "Accepted at", value: body.state.accepted_at },
            { label: "Application state", value: body.state.application },
            { label: "Trial state", value: verificationState },
            ...(v === null
              ? []
              : [
                  { label: "Trial plan reference", value: v.plan_id },
                  { label: "Trial outcome reference", value: v.outcome_id },
                  ...v.reasons.map((reason, i) => ({ label: `Recorded reason ${i + 1}`, value: reason })),
                ]),
          ]}
        />
      }
    />
  );
}

function Overview({ body, links }: { body: ActionBody; links: SiteActionLinks }) {
  const accepted = body.accepted_recommendation;
  const notice = body.newer_revision_notice;
  return (
    <div className="site-action__body">
      <ActionStateCard body={body} links={links} />
      <div className="site-action__pair">
        <Panel heading="Origin" headingId="site-action-origin-heading">
          <p data-action-origin-revision={body.origin.finding_revision_id}>
            Accepted for Finding version{" "}
            <Link to={links.finding(body.origin.finding_id, body.origin.finding_revision_id)} data-action-origin-link>
              <Ref value={body.origin.finding_revision_id} />
            </Link>
            .{" "}
            <Link to={links.recommendation(body.origin.finding_id, body.origin.finding_revision_id)} data-action-recommendation-link>
              Recommendation at that version
            </Link>
          </p>
          <SourceProvenanceNotice provenance={body.source_provenance} subject="finding version" name="action-origin" />
        </Panel>
        <Panel heading="Latest Finding version" headingId="site-action-latest-heading">
          {notice ? (
            <p data-action-newer-revision={notice.latest_revision_id}>
              A newer version (number {notice.revision_no}) exists:{" "}
              <Link to={links.finding(body.origin.finding_id, notice.latest_revision_id)}>
                <Ref value={notice.latest_revision_id} />
              </Link>
              . This Action stays with the version it was accepted for; the newer one is shown beside it, not
              substituted.
            </p>
          ) : (
            <p data-action-newer-revision="none">The origin version is still the latest.</p>
          )}
        </Panel>
      </div>
      <Panel heading="Accepted trial" headingId="site-action-accepted-heading">
        <p className="action-proposal" data-action-accepted-value={accepted.proposed_value}>
          Battery reserve <strong>{accepted.old_value}{accepted.unit}</strong> to{" "}
          <strong>{accepted.proposed_value}{accepted.unit}</strong>, rule{" "}
          <Ref value={`${accepted.rule_id} v${accepted.rule_version}`} />.
        </p>
        <TrialLimitation limitation={accepted.limitation} />
        <FactList>
          <Fact term="Foundation version">
            <Ref value={body.basis.foundation_revision_id} attr="data-action-basis-foundation" />
          </Fact>
          <Fact term="Assessment periods">{body.basis.assessments.length}</Fact>
          <Fact term="Battery charge readings">{body.basis.evidence.length}</Fact>
          <Fact term="Input reference">
            <Ref value={body.basis.input_sha256} />
          </Fact>
        </FactList>
      </Panel>
      {body.change ? <ChangeSummary change={body.change} links={links} /> : null}
      <p className="action-note" data-action-later-sections>
        Whether the change worked is judged in{" "}
        <Link to={links.view("plan", LATEST)}>Plan</Link>, <Link to={links.view("evidence", LATEST)}>Evidence</Link> and{" "}
        <Link to={links.view("verification", LATEST)}>Verification</Link>, from a plan fixed before the later window.
      </p>
    </div>
  );
}

function ChangeSummary({ change, links }: { change: PolicyChange; links: SiteActionLinks }) {
  return (
    <Panel heading="Foundation change" headingId="site-action-change-heading">
      <p data-action-change={change.change_id}>
        Battery reserve {change.old_value}
        {change.unit} to {change.new_value}
        {change.unit}, effective from {when(change.effective_from)}, recorded {when(change.recorded_at)}.{" "}
        <Link to={links.view("history", { eventId: change.applied_event_id, recordedAt: null })} data-action-applied-event-link>
          Application event
        </Link>{" "}
        <Link to={links.change(change.change_id)} data-action-change-link>
          Open the Foundation change
        </Link>
      </p>
      <FactList>
        <Fact term="Change record">
          <Ref value={change.change_id} />
        </Fact>
        <Fact term="New Foundation version">
          <Ref value={change.new_foundation_revision_id} attr="data-action-change-new-foundation" />
        </Fact>
        <Fact term="Outcome">{outcomeWords(change.outcome.state)}</Fact>
      </FactList>
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

function Application({
  body,
  events,
  siteId,
  client,
  links,
  outcome,
  onOutcome,
}: {
  body: ActionBody;
  events: ActionEventsBody | null;
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

  return (
    <div className="site-action__body">
      <WorkCard body={body} links={links} />
      <Panel heading="Application" headingId="site-action-application-heading">
        <FactList>
          <Fact term="Application">
            <span data-action-application-words>{APPLICATION_WORDS[body.state.application] ?? body.state.application}</span>
          </Fact>
          <Fact term="Attempts">
            {body.state.application_attempts} ({body.state.failed_attempts} failed)
          </Fact>
          {body.state.last_failure ? (
            <Fact term="Last failed attempt">
              <Ref value={body.state.last_failure.failure_code} /> at {when(body.state.last_failure.recorded_at)}
            </Fact>
          ) : null}
          <Fact term="Outcome">{outcomeWords(body.state.outcome.state)}</Fact>
        </FactList>
        {pending && body.state.failed_attempts > 0 ? (
          <p className="action-note" data-action-failed-still-pending>
            A failed attempt changes nothing: the application is still pending and can be attempted again.
          </p>
        ) : null}
      </Panel>

      <Panel heading={`Apply (${SYSTEM_DEMONSTRATION})`} headingId="site-action-apply-heading">
        {!latest ? (
          <p className="action-note">Commands are offered on the latest record only.</p>
        ) : !pending ? (
          <p className="action-note" data-action-already-applied>
            Applied; there is nothing more to apply.
          </p>
        ) : granted(capability, "APPLY") && !basis?.current_foundation_revision_id ? (
          <p className="action-note" data-action-apply-no-basis>
            Applying is not offered: the read did not state the current Foundation version, so the command could not
            name the version it expects. Reload to read it again.
          </p>
        ) : granted(capability, "APPLY") ? (
          <>
            <p className="action-note">
              Applying publishes the accepted reserve ({body.accepted_recommendation.proposed_value}
              {body.accepted_recommendation.unit}) as a new Site Foundation version, acted by a {SYSTEM_DEMONSTRATION}{" "}
              service. No effect is stated or measured.
            </p>
            {basis ? (
              <p className="action-note" data-action-expected-foundation={basis.current_foundation_revision_id ?? ""}>
                Expected current Foundation version{" "}
                {basis.current_foundation_revision_id ? <Ref value={basis.current_foundation_revision_id} /> : "none"} (as
                read at {when(basis.covers_instant)}). The server checks the version covering the effective time; a
                change between the two makes the attempt fail as stale.
              </p>
            ) : null}
            <label className="action-field">
              Effective from (UTC){" "}
              <input
                type="datetime-local"
                value={effective}
                onChange={(event) => {
                  setEdited(true);
                  setEffective(event.target.value);
                }}
                data-action-effective-from
              />
            </label>{" "}
            <button
              type="button"
              className="action-command"
              data-action-command="APPLY"
              aria-busy={busy}
              disabled={noTime}
              aria-describedby={noTime ? "site-action-apply-no-time" : undefined}
              onClick={() => void apply()}
            >
              Apply trial ({SYSTEM_DEMONSTRATION})
            </button>
            {noTime ? (
              <p id="site-action-apply-no-time" className="action-note" data-action-apply-no-time>
                Enter the effective time to apply.
              </p>
            ) : null}
          </>
        ) : (
          <CommandUnavailable capability={capability} what="Applying" />
        )}
        <ApplyOutcome outcome={outcome} links={links} />
      </Panel>

      {body.change ? <ChangeSummary change={body.change} links={links} /> : null}

      <Panel heading="Recorded activity" headingId="site-action-activity-heading">
        {events ? <EventTable events={events.events} change={body.change} selection={events.selection} links={links} view="execution" select={false} /> : null}
      </Panel>
    </div>
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

/** The plain "as of" instant of a selected Action read: the cutoff, else the last recorded event. */
function actionAsOf(body: ActionBody): string | null {
  return body.selection.cutoff_recorded_at ?? body.last_event?.recorded_at ?? null;
}

/**
 * W1-UX-04: the Application view's answer card - what work was done and what
 * is next. Applied is a recorded setting, never a measured effect.
 */
function WorkCard({ body, links }: { body: ActionBody; links: SiteActionLinks }) {
  const v = body.verification ?? null;
  const verificationState = v === null ? body.state.outcome.state : v.state;
  const trial = productOutcomeWords(verificationState, v === null ? [] : v.reasons, null);
  const words = applicationWords(body.state.application, body.state.failed_attempts);
  const applied = body.state.application === "APPLIED";
  const failed = body.state.failed_attempts;
  const attempts = body.state.application_attempts;
  return (
    <HeadlineVisualCard
      dataName="action-work"
      headingId="site-action-state-heading"
      title="Work done"
      description="An Action is proposed or recorded work on this site. Applying it changes a recorded setting; it does not prove an effect."
      question="What work was done, and what is next?"
      headline={
        <>
          <span data-action-work-headline>{words.label}</span>. {attempts} attempt{attempts === 1 ? "" : "s"} to apply
          recorded{failed > 0 ? `, ${failed} failed` : ""}.
        </>
      }
      status={<ProductStatus words={words} scope="This Action, from its recorded events" asOf={actionAsOf(body)} />}
      visual={
        <StepStrip
          title="The work so far"
          steps={[
            { label: "Accepted", state: "done", detail: when(body.state.accepted_at) },
            {
              label: "Attempts to apply",
              state: failed > 0 && !applied ? "problem" : attempts > 0 ? "done" : "waiting",
              detail: `${attempts} recorded, ${failed} failed`,
            },
            {
              label: "Applied",
              state: applied ? "done" : "waiting",
              detail: applied && body.state.applied_at !== null ? when(body.state.applied_at) : "Not yet",
            },
            { label: "Trial outcome", state: trialStep(verificationState), detail: trial.label },
          ]}
        />
      }
      meaning={
        <p>
          Work done is not the same as a result. Whether the change helped, and whether it stayed within its safety and
          service limits, is judged only on Verification.
        </p>
      }
      todo={words.next === undefined ? undefined : <p>{words.next}</p>}
      destination={
        <>
          <Link to={links.view("history", LATEST)} data-action-work-history-link>
            Open History
          </Link>{" "}
          <Link to={links.view("verification", LATEST)} data-action-work-verification-link>
            Open Verification
          </Link>
        </>
      }
      references={
        <ExactReferences
          name="action-work-references"
          references={[
            { label: "Action reference", value: body.action.id },
            { label: "Application state", value: body.state.application },
            { label: "Last failed attempt reason", value: body.state.last_failure?.failure_code ?? null },
            { label: "Change record", value: body.change?.change_id ?? null },
            { label: "New site configuration version", value: body.change?.new_foundation_revision_id ?? null },
          ]}
        />
      }
    />
  );
}

const EVENT_STEP: Record<string, StepState> = { ACCEPTED: "done", APPLIED: "done", OBSERVED: "done", FAILED: "problem" };

/**
 * W1-UX-04: the History view's answer card - a chronological story of the
 * selected events. An earlier selection is historical and says so; the plain
 * "as of" bound stays beside it.
 */
function HistoryCard({ body, events, links }: { body: ActionBody; events: ActionEventsBody | null; links: SiteActionLinks }) {
  const latest = body.selection.kind === "LATEST";
  const words = latest
    ? {
        label: "Every recorded event",
        sentence: "This is everything recorded for this Action when the page was read.",
        tone: "neutral" as const,
        code: "LATEST",
        unrecognised: false,
      }
    : currentnessWords("HISTORICAL");
  const selected = body.selection.kind === "EVENT_ID" ? body.selection.event_id : null;
  return (
    <HeadlineVisualCard
      dataName="action-history"
      headingId="site-action-state-heading"
      title="History"
      description="The recorded events of this Action, oldest first. Choosing one shows the Action as it stood then."
      question="What happened to this Action, and when?"
      headline={
        <>
          {latest ? "Latest record" : "An earlier record"}: {body.selection.event_count} of{" "}
          {body.selection.total_event_count} events.
        </>
      }
      status={<ProductStatus words={words} scope="This Action, from its recorded events" asOf={actionAsOf(body)} />}
      visual={
        events === null || events.events.length === 0 ? undefined : (
          <StepStrip
            title="What happened, in order"
            steps={events.events.map((event, i) => ({
              // Numbered: the strip keys steps by label, and the same kind can recur.
              label: `${i + 1}. ${plainEventWords(event.kind)}`,
              state: EVENT_STEP[event.kind] ?? "not-known",
              detail: `${when(event.occurred_at)}${event.id === selected ? " (selected)" : ""}`,
            }))}
          />
        )
      }
      meaning={
        <p>
          Events record what was decided and done. None of them measures an effect; a trial result appears only on
          Verification.
        </p>
      }
      destination={
        latest ? undefined : (
          <Link to={links.view("history", LATEST)} data-action-history-latest-link>
            Show the latest record
          </Link>
        )
      }
      references={
        <ExactReferences
          name="action-history-references"
          references={[
            { label: "Action reference", value: body.action.id },
            { label: "Selected event", value: selected ?? null },
            { label: "Selected recorded time", value: body.selection.kind === "RECORDED_AT" ? (body.selection.recorded_at ?? null) : null },
            { label: "Last included event", value: body.selection.cutoff_event_id ?? null },
          ]}
        />
      }
    />
  );
}

function History({ body, events, links, view }: { body: ActionBody; events: ActionEventsBody | null; links: SiteActionLinks; view: ActionView }) {
  return (
    <div className="site-action__body">
      <HistoryCard body={body} events={events} links={links} />
      <Panel heading="Recorded events" headingId="site-action-history-heading">
        <p className="action-note">
          Every recorded event of {body.action.action_code}, in the order the server recorded them. Choose an event
          to see the Action as it stood then, or everything recorded through that time.
        </p>
        {events ? (
          <EventTable events={events.events} change={body.change} selection={events.selection} links={links} view={view} select />
        ) : null}
      </Panel>
    </div>
  );
}

function EventTable({
  events,
  change,
  selection,
  links,
  view,
  select,
}: {
  events: ActionEvent[];
  change: PolicyChange | null;
  selection: Selection;
  links: SiteActionLinks;
  view: ActionView;
  select: boolean;
}) {
  if (events.length === 0) {
    return <p data-action-events="none">No events are recorded in this selection.</p>;
  }
  return (
    <DataTable labelledBy="site-action-events-caption">
      <caption id="site-action-events-caption">Recorded events</caption>
      <thead>
        <tr>
          <th scope="col">Event</th>
          <th scope="col">Recorded</th>
          <th scope="col">Happened</th>
          <th scope="col">Acted by</th>
          <th scope="col">Source</th>
          <th scope="col">Details</th>
          {select ? <th scope="col">Select</th> : null}
        </tr>
      </thead>
      <tbody>
        {events.map((event) => {
          const selected = selection.kind === "EVENT_ID" && selection.event_id === event.id;
          return (
            <tr
              key={event.id}
              data-action-event={event.id}
              data-action-event-kind={event.kind}
              aria-current={selected ? "true" : undefined}
            >
              <td>{eventWords(event.kind)}</td>
              <td data-action-recorded-at={event.recorded_at}>{when(event.recorded_at)}</td>
              <td data-action-occurred-at={event.occurred_at}>
                {when(event.occurred_at)}
                {event.occurred_before_recorded ? <span className="action-note"> (recorded later than it happened)</span> : null}
              </td>
              <td>
                {event.actor?.label ?? event.actor_kind} <Ref value={event.actor_kind} />
              </td>
              <td>
                <Ref value={event.triggering_service ?? "none"} />
                {event.triggering_job ? <Ref value={event.triggering_job} /> : null}
              </td>
              <td>
                <EventDetails event={event} change={change} links={links} />
              </td>
              {select ? (
                <td>
                  <Link to={links.view(view, { eventId: event.id, recordedAt: null })} data-action-select-event={event.id}>
                    This event
                  </Link>{" "}
                  <Link to={links.view(view, { eventId: null, recordedAt: event.recorded_at })} data-action-select-recorded={event.recorded_at}>
                    Through this time
                  </Link>
                </td>
              ) : null}
            </tr>
          );
        })}
      </tbody>
    </DataTable>
  );
}

function EventDetails({ event, change, links }: { event: ActionEvent; change: PolicyChange | null; links: SiteActionLinks }) {
  if (event.kind === "FAILED") {
    return (
      <span data-action-event-failure={event.failure_code ?? ""}>
        <Ref value={event.failure_code ?? "UNKNOWN"} /> Nothing was changed; the application stays pending.
        {event.expected_foundation_revision_id ? (
          <>
            {" "}
            Expected <Ref value={event.expected_foundation_revision_id} />
          </>
        ) : null}
        {event.current_foundation_revision_id ? (
          <>
            , current <Ref value={event.current_foundation_revision_id} />
          </>
        ) : null}
      </span>
    );
  }
  if (event.kind === "APPLIED") {
    return (
      <span>
        New Foundation version{" "}
        {event.current_foundation_revision_id ? <Ref value={event.current_foundation_revision_id} attr="data-action-event-effective-revision" /> : "not stated"}
        {change && change.applied_event_id === event.id ? (
          <>
            ; change record{" "}
            <Link to={links.change(change.change_id)} data-action-event-change-link>
              <Ref value={change.change_id} attr="data-action-event-change" />
            </Link>
          </>
        ) : null}
      </span>
    );
  }
  if (event.kind === "OBSERVED") {
    return (
      <span>
        <Ref value={event.observation_code ?? "UNKNOWN"} /> A note only; it changes no application or outcome state.
      </span>
    );
  }
  return <span>Trial accepted; nothing on the Site changed.</span>;
}
