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
  type Proposal,
  type RecommendationBody,
  type Refusal,
} from "./actionClient";
import {
  CommandRefusal,
  CommandUnavailable,
  granted,
  Ref,
  RefusalPanel,
  SYSTEM_DEMONSTRATION,
  TrialLimitation,
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
        ) : body.state === "AVAILABLE" ? (
          <CommandUnavailable capability={body.system_demo_capability} what="Accepting" />
        ) : (
          <p className="action-note">There is no proposal to accept.</p>
        )}
        <AcceptOutcome outcome={outcome} links={links} />
      </Panel>

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

function LivePanel({ live }: { live: LiveStatus | null }) {
  return (
    <Panel heading="Live recomputation" headingId="site-recommendation-live-heading">
      <p className="action-note">Recomputed from the current stored inputs. This is not the accepted proposal.</p>
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
