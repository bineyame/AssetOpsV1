/**
 * S6-01b `changes:1#a`: one Site Foundation change made by an applied Action,
 * read from `GET /api/sites/{site}/foundation/changes/{change_id}` (S6-01a).
 *
 * It shows the old and new reserve with its unit and asset, the effective and
 * recorded times, the superseded, SPLIT and new Foundation versions, the
 * signal assignment versions, the Action and its exact application event, and the
 * pending outcome. It makes no measured-effect verdict: whether the change did
 * anything is a later verification step (S6-02). Failed attempts are read from
 * the Action's own events, beside the change, never instead of it.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  DataTable,
  ExactReferences,
  Fact,
  FactList,
  HeadlineVisualCard,
  outcomeWords,
  Panel,
  plainTime,
  ProductStatus,
  StepStrip,
  type ProductWords,
} from "../ui";
import type {
  ActionClient,
  ActionEventsBody,
  ActionReadResult,
  EventSelector,
  FoundationRevisionRef,
  PolicyChange,
  PolicyChangeBody,
} from "./actionClient";
import { eventWords, outcomeWords as pendingOutcomeWords, Ref, RefusalPanel, SYSTEM_DEMONSTRATION, trialStep, when } from "./actionPresentation";
import { stateLabel } from "./verificationWords";
import { DecisionPathPanel, LaterEffectPanel, type TrialLinks } from "./recommendationVerification";

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

const LATEST: EventSelector = { eventId: null, recordedAt: null };

/** Which part a Foundation version plays in this change. */
function revisionRole(change: PolicyChange, revision: FoundationRevisionRef): string {
  if (revision.id === change.new_foundation_revision_id) return "New version (the changed value)";
  if (revision.id === change.split_foundation_revision_id) return "Earlier period kept (split)";
  if (revision.id === change.superseded_foundation_revision_id) return "Replaced version";
  if (revision.id === change.expected_foundation_revision_id) return "Version the command expected";
  return "Related version";
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
  if (read.status === "refused") {
    return (
      <RefusalPanel refusal={read} subject="Foundation change" headingId="site-change-refused-heading">
        <p>
          <Link to={links.foundation}>Back to the Foundation</Link>
        </p>
      </RefusalPanel>
    );
  }
  const c = read.value.change;
  const appliedEvent = links.action(c.action_id, "history", { eventId: c.applied_event_id, recordedAt: null });
  const revisions = [...c.foundation_revisions].sort((a, b) => a.version - b.version);

  return (
    <section
      className="site-change"
      aria-labelledby="site-change-summary-heading"
      data-change-id={c.change_id}
      data-change-outcome={c.outcome.state}
    >
      <ChangeCard body={read.value} attempts={attempts} links={links} appliedEvent={appliedEvent} />
      <p className="action-status" data-change-status>
        <span className="action-badge">{SYSTEM_DEMONSTRATION}</span> Applied to the Site Foundation by a{" "}
        {SYSTEM_DEMONSTRATION} command. <Link to={links.action(c.action_id, "overview", LATEST)}>Open the Action</Link>
      </p>
      <div className="action-pair">
        <Panel heading="What changed" headingId="site-change-summary-heading">
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
          <FactList>
            <Fact term="Battery">
              <Ref value={c.asset_id} attr="data-change-asset" />
            </Fact>
            <Fact term="Effective from">
              <span data-change-effective={c.effective_from}>{when(c.effective_from)}</span>
              {c.validity === "EFFECTIVE_FROM_OPEN_ENDED" ? " onward, with no end date" : null}
            </Fact>
            <Fact term="Recorded">
              <span data-change-recorded={c.recorded_at}>{when(c.recorded_at)}</span>
            </Fact>
            <Fact term="Change record">
              <Ref value={c.change_id} />
            </Fact>
          </FactList>
        </Panel>
        <Panel heading="Outcome" headingId="site-change-outcome-heading">
          <p data-change-outcome-words data-change-verification={read.value.verification?.state ?? "UNAVAILABLE"}>
            {read.value.verification
              ? `Verification: ${stateLabel(read.value.verification.state, read.value.verification.reasons)}.`
              : pendingOutcomeWords(c.outcome.state)}
          </p>
          <p className="action-note">
            This page records that the setting changed. Whether the change had any effect on the Site is a later
            verification step and is not judged here.
          </p>
          <Attempts attempts={attempts} change={c} links={links} />
        </Panel>
      </div>
      {links.actionChild ? (
        <div className="action-pair">
          <LaterEffectPanel actionId={c.action_id} summary={read.value.verification} links={{ child: links.actionChild }} />
          <DecisionPathPanel
            actionId={c.action_id}
            summary={read.value.verification}
            appliedEventHref={appliedEvent}
            links={{ child: links.actionChild }}
          />
        </div>
      ) : null}
      <Panel heading="Application" headingId="site-change-application-heading">
        <FactList>
          <Fact term="Action">
            <Link to={links.action(c.action_id, "overview", LATEST)} data-change-action-link>
              <Ref value={c.action_id} />
            </Link>
          </Fact>
          <Fact term="Application event">
            <Link to={appliedEvent} data-change-applied-event-link>
              <Ref value={c.applied_event_id} />
            </Link>
          </Fact>
          <Fact term="Acted by">{SYSTEM_DEMONSTRATION}</Fact>
          {c.command_idempotency_key ? (
            <Fact term="Command key">
              <Ref value={c.command_idempotency_key} />
            </Fact>
          ) : null}
        </FactList>
      </Panel>
      <Panel heading="Foundation versions" headingId="site-change-revisions-heading">
        <FactList>
          <Fact term="Expected by the command">
            <Ref value={c.expected_foundation_revision_id} attr="data-change-expected" />
          </Fact>
          <Fact term="New version">
            <Ref value={c.new_foundation_revision_id} attr="data-change-new-foundation" />
          </Fact>
        </FactList>
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
      </Panel>
      <p className="action-note" data-change-later-sections>
        There is no list of Site changes yet; a change is reached from the Action that made it.{" "}
        <Link to={links.foundation}>Back to the Foundation</Link>
      </p>
    </section>
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
  if (attempts === null) return <p>{FOUNDATION_CHANGE_ATTEMPTS_LOADING}</p>;
  if (attempts.status === "refused") {
    return (
      <RefusalPanel refusal={attempts} subject="Action events" headingId="site-change-attempts-refused-heading">
        <p className="action-note">The change above is unaffected.</p>
      </RefusalPanel>
    );
  }
  const failed = attempts.value.events.filter((event) => event.kind === "FAILED");
  return (
    <div data-change-attempts={failed.length}>
      {failed.length === 0 ? (
        <p>No failed application attempts are recorded for this Action.</p>
      ) : (
        <>
          <p>
            {failed.length === 1 ? "One earlier attempt" : `${failed.length} earlier attempts`} failed and changed
            nothing:
          </p>
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

/** W1-UX-04: the change itself, as state-line words. Changing a setting is never a measured result. */
const CHANGE_WORDS: ProductWords = {
  label: "Setting changed; effect judged separately",
  sentence: "The new reserve is recorded for this battery. This does not show that generator use, cost or safety changed.",
  next: "Open Verification to see whether the measured trial met its goal within its limits.",
  tone: "limited",
  code: "APPLIED",
  unrecognised: false,
};

/**
 * W1-UX-04: the Change answer card - what changed, when, and what it did, as
 * a chronological change/effect strip. The effect step is the read's own
 * verification state; failed attempts are "not known" until their read lands.
 */
function ChangeCard({
  body,
  attempts,
  links,
  appliedEvent,
}: {
  body: PolicyChangeBody;
  attempts: ActionReadResult<ActionEventsBody> | null;
  links: SiteFoundationChangeLinks;
  appliedEvent: string;
}) {
  const c = body.change;
  const v = body.verification ?? null;
  const verificationState = v === null ? c.outcome.state : v.state;
  const trial = outcomeWords(verificationState, v === null ? [] : v.reasons, null);
  const failed = attempts?.status === "loaded" ? attempts.value.events.filter((event) => event.kind === "FAILED").length : null;
  return (
    <HeadlineVisualCard
      dataName="change"
      headingId="site-change-answer-heading"
      title="Change and effect"
      description="A change is a setting recorded for the site by an applied Action. Its effect is judged only by a measured trial."
      question="What changed on the site, and what did it do?"
      headline={
        <>
          Battery reserve changed from {c.old_value}
          {c.unit} to {c.new_value}
          {c.unit}, effective {plainTime(c.effective_from)}.
        </>
      }
      status={<ProductStatus words={CHANGE_WORDS} scope="This battery's recorded settings" asOf={c.recorded_at} />}
      visual={
        <StepStrip
          title="Change and effect, in order"
          steps={[
            {
              label: "Earlier attempts that failed",
              state: failed === null ? "not-known" : failed > 0 ? "problem" : "done",
              detail: failed === null ? "Not known yet" : `${failed} recorded; none changed the site`,
            },
            { label: "Setting recorded", state: "done", detail: plainTime(c.recorded_at) ?? "Time not recorded" },
            { label: "Effective from", state: "done", detail: plainTime(c.effective_from) ?? "Time not recorded" },
            { label: "Measured effect", state: trialStep(verificationState), detail: trial.label },
          ]}
        />
      }
      meaning={
        <p>
          The change is a recorded setting, not a measured result. Whether it helped, and whether it stayed within its
          safety and service limits, is shown on Verification.
        </p>
      }
      todo={<p>{CHANGE_WORDS.next}</p>}
      destination={
        <>
          <Link to={links.action(c.action_id, "overview", LATEST)} data-change-card-action-link>
            Open the Action
          </Link>{" "}
          {links.actionChild ? (
            <Link to={links.actionChild(c.action_id, "verification")} data-change-card-verification-link>
              Open Verification
            </Link>
          ) : null}{" "}
          <Link to={appliedEvent} data-change-card-event-link>
            Open the application event
          </Link>
        </>
      }
      references={
        <ExactReferences
          name="change-references"
          references={[
            { label: "Change record", value: c.change_id },
            { label: "Battery", value: c.asset_id },
            { label: "Action reference", value: c.action_id },
            { label: "Application event", value: c.applied_event_id },
            { label: "Trial outcome state", value: verificationState },
          ]}
        />
      }
    />
  );
}
