/**
 * S6-01b phase 1: the Recommendation child view of a durable Finding (mock
 * `recommendation:1`), at
 * `/sites/{site}/findings/{finding}/recommendation[?revision_id=]`.
 *
 * Reads `GET /api/sites/{site}/findings/{finding}/recommendation`. Before
 * acceptance the proposal is computed by the server from persisted inputs
 * (rule `reserve-trial-1`), or a typed unavailable reason is shown. Once
 * accepted, the immutable accepted proposal and its Action link are shown
 * beside a separately labelled live recomputation, so a stale current basis
 * never erases the accepted proposal (Architect M2).
 *
 * The accept control renders only when the read's `system_demo_capability`
 * allows `ACCEPT` for this exact record (Architect Q4); otherwise the view is
 * read-only with the server's reason. The trial predicts no saving, and the
 * money consequence is a labelled link to the Finding's own stored figure,
 * never an amount here.
 *
 * `D-2026-10-15-s601-reopen`: every Action already accepted on this Finding
 * (any revision) is listed with its own origin version, application and
 * outcome state and an exact link; it is never relabelled as the selected
 * version's. While an earlier trial is unresolved (`PRIOR_ACTION_UNRESOLVED`)
 * a notice names and links the blocking Action, the live recomputation is
 * shown separately as a second reason, and Accept is disabled with the reason
 * stated. A 409 `PRIOR_ACTION_UNRESOLVED` on accept is reported the same way.
 */
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Disclosure, Fact, FactList, Panel } from "../ui";
import {
  freshIdempotencyKey,
  type AcceptedRecommendation,
  type ActionClient,
  type ActionReadResult,
  type CommandResult,
  type LiveStatus,
  type PriorAction,
  type PriorActionBlock,
  type Proposal,
  type RecommendationBody,
  type Refusal,
} from "./actionClient";
import {
  APPLICATION_WORDS,
  CommandRefusal,
  CommandUnavailable,
  granted,
  Ref,
  RefusalPanel,
  SYSTEM_DEMONSTRATION,
  TrialLimitation,
  outcomeWords,
  when,
} from "./actionPresentation";

export interface SiteRecommendationLinks {
  /** This Finding at an exact version (or the latest when null). */
  finding: (revisionId: string | null) => string;
  /** The canonical Action root. */
  action: (actionId: string) => string;
  /** The Finding's money view, pinned to the exact Finding version. */
  money: (revisionId: string) => string;
}

export function SiteRecommendation({
  siteId,
  findingId,
  client,
  links,
}: {
  siteId: string;
  findingId: string;
  client: ActionClient;
  links: SiteRecommendationLinks;
}) {
  const [params] = useSearchParams();
  const revisionId = params.get("revision_id");
  const [read, setRead] = useState<ActionReadResult<RecommendationBody> | null>(null);
  const [lastLoaded, setLastLoaded] = useState<RecommendationBody | null>(null);
  const [reload, setReload] = useState(0);
  const [outcome, setOutcome] = useState<CommandResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setLastLoaded(null);
    setOutcome(null);
  }, [siteId, findingId, revisionId]);

  useEffect(() => {
    let active = true;
    setRead(null);
    void client.getRecommendation(siteId, findingId, revisionId).then((loaded) => {
      if (!active) return;
      setRead(loaded);
      if (loaded.status === "loaded") setLastLoaded(loaded.value);
    });
    return () => {
      active = false;
    };
  }, [client, siteId, findingId, revisionId, reload]);

  if (read === null && lastLoaded === null) {
    return <p>Loading the recommendation.</p>;
  }
  const body = read?.status === "loaded" ? read.value : lastLoaded;
  const failedRead = read !== null && read.status === "refused" ? read : null;
  if (body === null) {
    return <RefusalPanel refusal={failedRead as Refusal} subject="Recommendation" headingId="site-recommendation-refused-heading" />;
  }

  const accept = async (proposal: Proposal) => {
    setBusy(true);
    const result = await client.accept(siteId, findingId, {
      revision_id: body.revision_id,
      foundation_revision_id: proposal.foundation_revision_id,
      recommendation_key: proposal.recommendation_key,
      proposed_value: proposal.proposed_value,
      idempotency_key: freshIdempotencyKey(),
    });
    setOutcome(result);
    setBusy(false);
    setReload((n) => n + 1);
  };

  const accepted = body.accepted[0] ?? null;
  const held = body.state === "PRIOR_ACTION_UNRESOLVED";
  const block = held ? blockFrom(body) : null;
  const priorActions = body.prior_actions?.items ?? [];
  return (
    <section
      className="site-recommendation"
      aria-labelledby="site-recommendation-heading"
      data-recommendation-state={body.state}
      data-recommendation-basis={body.basis}
      data-recommendation-revision={body.revision_id}
    >
      {read === null ? <p className="action-note">Loading the recommendation.</p> : null}
      {failedRead ? (
        <RefusalPanel refusal={failedRead} subject="Recommendation" headingId="site-recommendation-reread-heading">
          <p className="action-note">The last successful read is still shown below.</p>
        </RefusalPanel>
      ) : null}
      <Panel heading="Battery reserve trial" headingId="site-recommendation-heading">
        <FactList>
          <Fact term="Rule">
            <Ref value={`${body.rule.id} v${body.rule.version}`} attr="data-recommendation-rule" />
          </Fact>
          <Fact term="Finding version">
            <Link to={links.finding(body.revision_id)} data-recommendation-finding-link>
              <Ref value={body.revision_id} />
            </Link>
            {body.is_latest ? " (latest)" : null}
          </Fact>
        </FactList>
        {!body.is_latest ? (
          <p className="action-note" data-recommendation-newer-revision={body.latest_revision_id}>
            A newer version of this Finding exists:{" "}
            <Link to={links.finding(body.latest_revision_id)}>
              <Ref value={body.latest_revision_id} />
            </Link>
            . This page stays on the version in the address.
          </p>
        ) : null}
        <TrialLimitation limitation={body.rule.limitation} />
        {!body.source_open ? (
          <p className="action-note" data-recommendation-source-closed>
            This site's assessments are not released for use, so this is shown as a record only.
          </p>
        ) : null}
      </Panel>

      {accepted ? (
        <div className="site-recommendation__pair">
          <AcceptedPanel accepted={accepted} links={links} />
          <LivePanel live={body.live_status} />
        </div>
      ) : held ? (
        <div className="site-recommendation__pair">
          <PriorActionNotice block={block} links={links} />
          <LivePanel
            live={body.live_status}
            note="Recomputed from the current stored inputs. This is a separate reason, shown for information; it does not make a new trial acceptable here."
          />
        </div>
      ) : body.proposal ? (
        <ProposalPanel heading="Proposed trial" proposal={body.proposal} pinnedNote="Computed from stored inputs when read; not yet accepted." />
      ) : (
        <Panel heading="No trial proposed" headingId="site-recommendation-unavailable-heading">
          <p data-recommendation-unavailable={body.unavailable?.code ?? "UNKNOWN"}>
            The fixed rule proposes no reserve trial for this Finding version.
          </p>
          {body.unavailable ? (
            <p className="action-note">
              Reason: <Ref value={body.unavailable.code} /> {body.unavailable.message}
            </p>
          ) : null}
        </Panel>
      )}

      <Panel heading={`Accept (${SYSTEM_DEMONSTRATION})`} headingId="site-recommendation-accept-heading">
        {accepted ? (
          <p data-recommendation-accepted-action={accepted.action_id}>
            Accepted at {when(accepted.accepted_at)} as{" "}
            <Link to={links.action(accepted.action_id)}>{accepted.action_code}</Link>. Accepting records the trial;
            it changes nothing on the Site.
          </p>
        ) : body.state === "AVAILABLE" && body.proposal && granted(body.system_demo_capability, "ACCEPT") ? (
          <>
            <p className="action-note">
              Accepting records this trial as an Action, acted by a {SYSTEM_DEMONSTRATION} service. It changes
              nothing on the Site; applying it is a separate step.
            </p>
            <button
              type="button"
              className="action-command"
              data-action-command="ACCEPT"
              aria-busy={busy}
              onClick={() => {
                if (!busy && body.proposal) void accept(body.proposal);
              }}
            >
              Accept trial ({SYSTEM_DEMONSTRATION})
            </button>
          </>
        ) : held ? (
          <>
            <button
              type="button"
              className="action-command"
              data-action-command="ACCEPT"
              data-action-command-held="PRIOR_ACTION_UNRESOLVED"
              disabled
              aria-describedby="site-recommendation-accept-held"
            >
              Accept trial ({SYSTEM_DEMONSTRATION})
            </button>
            <p
              id="site-recommendation-accept-held"
              className="action-command-unavailable"
              data-action-command-unavailable="PRIOR_ACTION_UNRESOLVED"
            >
              Accepting is not offered: an earlier trial on this Finding
              {block ? (
                <>
                  {" "}
                  (<Link to={links.action(block.actionId)}>{block.actionCode ?? "the earlier Action"}</Link>)
                </>
              ) : null}{" "}
              is still open. Follow that Action; a new trial waits until it is settled.
            </p>
          </>
        ) : body.state === "AVAILABLE" ? (
          <CommandUnavailable capability={body.system_demo_capability} what="Accepting" />
        ) : (
          <p className="action-note">There is no proposal to accept.</p>
        )}
        <AcceptOutcome outcome={outcome} links={links} />
      </Panel>

      {priorActions.length > 0 ? <PriorActionList items={priorActions} links={links} /> : null}

      {body.money_consequence ? (
        <Panel heading="Money" headingId="site-recommendation-money-heading">
          <p data-recommendation-money-link>
            <Link to={links.money(body.money_consequence.basis.finding_revision_id)}>
              {body.money_consequence.label} of this Finding version
            </Link>
            . That stored figure belongs to the Finding, not to the trial. The trial predicts no saving.
          </p>
        </Panel>
      ) : null}
    </section>
  );
}

function AcceptOutcome({ outcome, links }: { outcome: CommandResult | null; links: SiteRecommendationLinks }) {
  if (outcome === null) return null;
  if (outcome.status === "done") {
    return (
      <p role="status" data-action-command-done={outcome.replayed ? "replayed" : "created"}>
        {outcome.replayed ? "This command was already recorded; " : "Accepted; "}
        {outcome.action ? (
          <Link to={links.action(outcome.action.action_id)}>open {outcome.action.action_code}</Link>
        ) : (
          "the Action is recorded"
        )}
        .
      </p>
    );
  }
  if (outcome.code === "PRIOR_ACTION_UNRESOLVED" && typeof outcome.detail?.blocking_action_id === "string") {
    const detail = outcome.detail;
    const code = typeof detail.blocking_action_code === "string" ? detail.blocking_action_code : null;
    const revisionNo = typeof detail.origin_revision_no === "number" ? detail.origin_revision_no : null;
    const live = (detail.live_status ?? null) as Pick<LiveStatus, "state" | "unavailable"> | null;
    return (
      <div className="action-command-refusal" role="alert" data-action-command-refused="PRIOR_ACTION_UNRESOLVED">
        <p>
          Not accepted: an earlier trial on this Finding is still open, so no new Action was recorded.{" "}
          <Link to={links.action(detail.blocking_action_id as string)} data-accept-held-action-link>
            Open {code ?? "the earlier Action"}
          </Link>
          {revisionNo !== null ? ` (accepted on Finding version ${revisionNo})` : ""}.
        </p>
        <p className="action-note">
          Code: <Ref value="PRIOR_ACTION_UNRESOLVED" />
        </p>
        {live ? (
          <p className="action-note" data-accept-held-live={live.state}>
            Separately, on current inputs:{" "}
            {live.state === "AVAILABLE" ? (
              "the rule would still propose a trial."
            ) : (
              <>
                no proposal. Reason: <Ref value={live.unavailable?.code ?? "UNKNOWN"} /> {live.unavailable?.message ?? ""}
              </>
            )}
          </p>
        ) : null}
      </div>
    );
  }
  if (outcome.code === "ACTION_ACCEPTANCE_CONFLICT" && typeof outcome.detail?.action_id === "string") {
    return (
      <p role="status" data-action-command-done="already-accepted">
        This trial was already accepted.{" "}
        <Link to={links.action(outcome.detail.action_id)}>Open the existing Action</Link>.
      </p>
    );
  }
  return <CommandRefusal refusal={outcome} />;
}

function ProposalPanel({ heading, proposal, pinnedNote }: { heading: string; proposal: Proposal; pinnedNote: string }) {
  const evidenceIds = Array.from(
    new Set(proposal.inputs.segments.map((segment) => segment.selected_soc?.evidence_id).filter((id): id is string => !!id)),
  );
  const assessmentIds = Array.from(new Set(proposal.inputs.segments.map((segment) => segment.assessment_revision_id)));
  return (
    <Panel heading={heading} headingId={`site-recommendation-${heading.toLowerCase().replace(/\W+/g, "-")}-heading`}>
      <p className="action-proposal" data-recommendation-proposal={proposal.proposed_value}>
        Battery reserve <strong>{proposal.old_value}{proposal.unit}</strong> to{" "}
        <strong>{proposal.proposed_value}{proposal.unit}</strong> on <Ref value={proposal.asset_code} />.
      </p>
      <p className="action-note">{pinnedNote}</p>
      <PinnedFacts proposal={proposal} />
      <Disclosure name="recommendation-inputs" summary={`Stored inputs (${assessmentIds.length} assessment, ${evidenceIds.length} readings)`}>
        <FactList>
          <Fact term="Assessment versions">
            {assessmentIds.map((id) => (
              <Ref key={id} value={id} />
            ))}
          </Fact>
          <Fact term="Battery charge readings">
            <span data-recommendation-input-count={evidenceIds.length}>
              {evidenceIds.map((id) => (
                <Ref key={id} value={id} />
              ))}
            </span>
          </Fact>
          <Fact term="Input digest">
            <Ref value={proposal.input_sha256} />
          </Fact>
        </FactList>
      </Disclosure>
    </Panel>
  );
}

function PinnedFacts({ proposal }: { proposal: Proposal | AcceptedRecommendation["snapshot"] }) {
  return (
    <FactList>
      <Fact term="Finding version">
        <Ref value={proposal.finding_revision_id} attr="data-pinned-finding-revision" />
      </Fact>
      <Fact term="Foundation version">
        <Ref value={proposal.foundation_revision_id} attr="data-pinned-foundation-revision" />
      </Fact>
      <Fact term="Primary assessment">
        <Ref value={proposal.primary_assessment_revision_id} />
      </Fact>
    </FactList>
  );
}

function AcceptedPanel({ accepted, links }: { accepted: AcceptedRecommendation; links: SiteRecommendationLinks }) {
  const snapshot = accepted.snapshot;
  return (
    <Panel heading="Accepted proposal" headingId="site-recommendation-accepted-heading">
      <p className="action-proposal" data-recommendation-accepted={snapshot.proposed_value}>
        Battery reserve <strong>{snapshot.old_value}{snapshot.unit}</strong> to{" "}
        <strong>{snapshot.proposed_value}{snapshot.unit}</strong> on <Ref value={snapshot.asset_code} />.
      </p>
      <p className="action-note">
        Stored when accepted ({when(accepted.accepted_at)}); a later change on the Site does not alter it.{" "}
        <Link to={links.action(accepted.action_id)} data-recommendation-action-link>
          {accepted.action_code}
        </Link>
      </p>
      <PinnedFacts proposal={snapshot} />
    </Panel>
  );
}

function LivePanel({
  live,
  note = "Recomputed from the current stored inputs. This is not the accepted proposal.",
}: {
  live: LiveStatus | null;
  note?: string;
}) {
  return (
    <Panel heading="Live recomputation" headingId="site-recommendation-live-heading">
      <p className="action-note">{note}</p>
      {live === null ? (
        <p data-recommendation-live="none">No live recomputation was returned.</p>
      ) : live.state === "AVAILABLE" && live.proposal ? (
        <p data-recommendation-live="AVAILABLE">
          The rule would propose {live.proposal.old_value}
          {live.proposal.unit} to {live.proposal.proposed_value}
          {live.proposal.unit} on current inputs.
        </p>
      ) : (
        <p data-recommendation-live={live.state}>
          No proposal on current inputs.
          {live.unavailable ? (
            <>
              {" "}
              Reason: <Ref value={live.unavailable.code} /> {live.unavailable.message}
            </>
          ) : null}
        </p>
      )}
    </Panel>
  );
}

interface HeldBy {
  actionId: string;
  actionCode: string | null;
  originRevisionId: string | null;
  originRevisionNo: number | null;
  action: PriorAction | null;
  code: string;
  message: string | null;
}

/** The blocking Action, from `prior_action_block`, else from the typed `unavailable` reason. */
function blockFrom(body: RecommendationBody): HeldBy | null {
  const typed: PriorActionBlock | null = body.prior_action_block ?? null;
  const reason = body.unavailable as (NonNullable<RecommendationBody["unavailable"]> & Record<string, unknown>) | null;
  const actionId = typed?.blocking_action_id ?? (typeof reason?.blocking_action_id === "string" ? reason.blocking_action_id : null);
  if (actionId === null) return null;
  const action =
    typed?.blocking_actions.find((item) => item.action_id === actionId) ??
    body.prior_actions?.items.find((item) => item.action_id === actionId) ??
    null;
  const reasonOrigin = typeof reason?.origin_finding_revision_id === "string" ? reason.origin_finding_revision_id : null;
  return {
    actionId,
    actionCode: typed?.blocking_action_code ?? action?.action_code ?? null,
    originRevisionId: typed?.origin_finding_revision_id ?? reasonOrigin ?? action?.origin.finding_revision_id ?? null,
    originRevisionNo: typed?.origin_revision_no ?? action?.origin.revision_no ?? null,
    action,
    code: typed?.code ?? reason?.code ?? "PRIOR_ACTION_UNRESOLVED",
    message: typed?.message ?? reason?.message ?? null,
  };
}

/** The plain notice naming and linking the earlier Action that holds a new acceptance. */
function PriorActionNotice({ block, links }: { block: HeldBy | null; links: SiteRecommendationLinks }) {
  return (
    <Panel heading="An earlier trial is still open" headingId="site-recommendation-prior-block-heading">
      {block ? (
        <>
          <p data-recommendation-prior-block={block.actionId}>
            This Finding already has a reserve trial:{" "}
            <Link to={links.action(block.actionId)} data-recommendation-prior-block-link>
              {block.actionCode ?? "the earlier Action"}
            </Link>
            , accepted on{" "}
            {block.originRevisionId ? (
              <Link to={links.finding(block.originRevisionId)} data-recommendation-prior-block-origin={block.originRevisionId}>
                {block.originRevisionNo !== null ? `Finding version ${block.originRevisionNo}` : "an earlier Finding version"}
              </Link>
            ) : (
              "an earlier Finding version"
            )}
            , not on the version shown on this page. A new trial cannot be accepted while that one is still open.
          </p>
          {block.action ? (
            <p className="action-note" data-recommendation-prior-block-state={block.action.application.state}>
              {block.action.action_code}:{" "}
              {APPLICATION_WORDS[block.action.application.state] ?? block.action.application.state}.{" "}
              {outcomeWords(block.action.outcome.state)}
            </p>
          ) : null}
          <p className="action-note">
            Reason: <Ref value={block.code} /> {block.message}
          </p>
        </>
      ) : (
        <p data-recommendation-prior-block="UNKNOWN">
          An earlier trial on this Finding is still open, so a new trial cannot be accepted here. The server did not
          name it.
        </p>
      )}
    </Panel>
  );
}

/** Every Action on this canonical Finding, each with its own origin version (never relabelled). */
function PriorActionList({ items, links }: { items: PriorAction[]; links: SiteRecommendationLinks }) {
  return (
    <Panel heading="Actions on this Finding" headingId="site-recommendation-prior-actions-heading">
      <p className="action-note">Each Action keeps the Finding version it was accepted on.</p>
      <ul className="action-list">
        {items.map((item) => (
          <li
            key={item.action_id}
            data-recommendation-prior-action={item.action_id}
            data-prior-action-selected-revision={item.origin.is_selected_revision ? "yes" : "no"}
          >
            <Link to={links.action(item.action_id)} data-recommendation-prior-action-link>
              {item.action_code}
            </Link>{" "}
            accepted {when(item.accepted_at)} on{" "}
            <Link to={links.finding(item.origin.finding_revision_id)} data-prior-action-origin={item.origin.finding_revision_id}>
              Finding version {item.origin.revision_no}
            </Link>
            {item.origin.is_selected_revision ? " (this version)" : " (not the version on this page)"}.{" "}
            <span data-prior-action-application={item.application.state}>
              {APPLICATION_WORDS[item.application.state] ?? item.application.state}
              {item.application.failed_attempts > 0
                ? ` (${item.application.failed_attempts} failed ${item.application.failed_attempts === 1 ? "attempt" : "attempts"})`
                : ""}
              .
            </span>{" "}
            <span data-prior-action-outcome={item.outcome.state}>{outcomeWords(item.outcome.state)}</span>
            {item.unresolved ? " Still open." : null}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
