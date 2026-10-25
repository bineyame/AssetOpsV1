/**
 * S6-01b phase 1: the Recommendation child view of a durable Finding, at
 * `/sites/{site}/findings/{finding}/recommendation[?revision_id=]`.
 *
 * W1-F4 (`D-2026-10-17-mockup-layout-spec`): the screen renders exactly the
 * v69 `recommendation` panels. A one-line status strip carries the state,
 * scope and "as of" bound; then panels 1 and 2 side by side (Proposed
 * intervention | Declare success before evaluating), the acceptance-limit
 * notice line, and panel 3 (Evidence needed to verify) full width. The former
 * W1-UX-04 answer card, the battery reserve trial, accepted proposal, live
 * recomputation, prior-action hold, Actions-on-this-Finding list, accept
 * control and money link are merged into panel 1. W1-F4 trim: panel 1 is the
 * mock's claim line, one prose paragraph (the trial-only limitation), five
 * key-value rows (source state among them), the accept control or accepted /
 * held line (hold reason and earlier Action state inline) and one note line
 * (next step and money qualifier link); rule, IDs, live recomputation, the
 * Actions list and stored inputs sit in the closed "How this was worked out".
 * A refused read keeps the three slots, each with its gap stated inside.
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
 * the hold names and links the blocking Action, the live recomputation is
 * shown separately as a second reason, and Accept is disabled with the reason
 * stated. A 409 `PRIOR_ACTION_UNRESOLVED` on accept is reported the same way.
 */
import { useEffect, useState, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { asOfText, Badge, ChartNote, Disclosure, ExactReferences, Fact, FactList, KeyValues, Panel } from "../ui";
import { SOURCE_WORDS, SourceProvenanceNotice, sourceState } from "./sourceProvenance";
import { DeclaredSuccessPanel, EvidenceNeededPanel, type TrialLinks } from "./recommendationVerification";
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
  SYSTEM_DEMONSTRATION,
  TrialLimitation,
  outcomeWords,
  recommendationWords,
  when,
} from "./actionPresentation";
import "./w1f4-recommendation.css";

export interface SiteRecommendationLinks {
  /** This Finding at an exact version (or the latest when null). */
  finding: (revisionId: string | null) => string;
  /** The canonical Action root. */
  action: (actionId: string) => string;
  /** S6-02b: an Action's Plan, Evidence or Verification child view. */
  actionChild?: TrialLinks["child"];
  /** The Finding's money view, pinned to the exact Finding version. */
  money: (revisionId: string) => string;
}

/** The v69 panel titles of `recommendation`, in order. */
const PROPOSED = "Proposed intervention";
const SUCCESS = "Declare success before evaluating";
const EVIDENCE = "Evidence needed to verify";

const ACCEPT_LIMIT =
  "Accepting creates managed work. It does not close the Finding, verify the change or send a real controller command.";

export function SiteRecommendation({
  siteId,
  findingId,
  client,
  links,
  onTitle,
}: {
  siteId: string;
  findingId: string;
  client: ActionClient;
  links: SiteRecommendationLinks;
  /** W1-F5b review M2: the page heads with the Finding's name, as Finding, Evidence and History do. */
  onTitle?: (title: string) => void;
}) {
  const [params] = useSearchParams();
  const revisionId = params.get("revision_id");
  const [read, setRead] = useState<ActionReadResult<RecommendationBody> | null>(null);
  const [lastLoaded, setLastLoaded] = useState<RecommendationBody | null>(null);
  const [reload, setReload] = useState(0);
  const [outcome, setOutcome] = useState<CommandResult | null>(null);
  const [busy, setBusy] = useState(false);

  // post-W6 W1-a Q16 / R193: the heading is the frame's: the resolved Finding record's title, or "Finding" when the
  // selection refuses. This view no longer sets a fixed name.
  void onTitle;

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
    return <RefusedRecommendation refusal={failedRead as Refusal} />;
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
  const held = HELD_STATES.has(body.state);
  const block = held ? blockFrom(body) : null;
  const priorActions = body.prior_actions?.items ?? [];
  const words = recommendationWords(accepted ? "ACCEPTED" : body.state);
  const shown = accepted ? accepted.snapshot : body.proposal;
  const holdCode = block?.code ?? body.state;

  const acceptedAction = accepted ? priorActions.find((item) => item.action_id === accepted.action_id) ?? null : null;
  const source = sourceState(body.source_provenance);

  const acceptControl = accepted ? (
    <ChartNote data={{ "data-recommendation-accepted-action": accepted.action_id }}>
      Accepted {when(accepted.accepted_at)} as{" "}
      <Link to={links.action(accepted.action_id)} data-recommendation-action-link>
        {accepted.action_code}
      </Link>
      {acceptedAction ? ` (${applicationText(acceptedAction)})` : null}; stored as accepted, so a later change on the
      Site does not alter it. Accepting changes nothing on the Site.
    </ChartNote>
  ) : body.state === "AVAILABLE" && body.proposal && granted(body.system_demo_capability, "ACCEPT") ? (
    <div className="form-footer">
      <button
        type="button"
        className="button primary"
        data-action-command="ACCEPT"
        aria-busy={busy}
        onClick={() => {
          if (!busy && body.proposal) void accept(body.proposal);
        }}
      >
        Accept trial ({SYSTEM_DEMONSTRATION})
      </button>
    </div>
  ) : held ? (
    <>
      <div className="form-footer">
        <button
          type="button"
          className="button primary"
          data-action-command="ACCEPT"
          data-action-command-held={body.state}
          disabled
          aria-describedby="site-recommendation-accept-held"
        >
          Accept trial ({SYSTEM_DEMONSTRATION})
        </button>
      </div>
      <p
        id="site-recommendation-accept-held"
        className="action-command-unavailable v69-chart-note"
        data-action-command-unavailable={body.state}
      >
        Accepting is not offered: an earlier trial {block?.otherFinding ? "on this battery" : "on this Finding"}
        {block ? (
          <>
            {" "}
            (
            <Link to={links.action(block.actionId)} data-recommendation-prior-block-link>
              {block.actionCode ?? "the earlier Action"}
            </Link>
            )
          </>
        ) : null}{" "}
        {body.state === "PRIOR_TRIAL_GUARDRAIL_FAILED"
          ? "missed a safety or service limit, so no new trial on this battery can be accepted."
          : body.state === "PRIOR_TRIAL_REASSESSMENT_OVERLAP"
            ? "overlapped late evidence that withdrew its result, so new trials on this battery stay held."
            : "is still open; a new trial waits until it settles."}{" "}
        <PriorActionHold block={block} links={links} code={holdCode} />
      </p>
    </>
  ) : body.state === "AVAILABLE" ? (
    <CommandUnavailable capability={body.system_demo_capability} what="Accepting" />
  ) : (
    <ChartNote>There is no proposal to accept{body.unavailable ? `: ${body.unavailable.message}` : "."}</ChartNote>
  );

  return (
    <div
      className="site-recommendation w1f4-recommendation"
      data-recommendation-state={body.state}
      data-recommendation-basis={body.basis}
      data-recommendation-revision={body.revision_id}
    >
      {read === null ? <p className="action-note">Loading the recommendation.</p> : null}
      {failedRead ? (
        <RefusalLine refusal={failedRead} kind="reread">
          <p className="page-refusal__note">The last successful read is still shown below.</p>
        </RefusalLine>
      ) : null}
      <RecommendationStrip body={body} accepted={accepted} block={block} links={links} />

      <div className="panel-pair">
        <Panel heading={PROPOSED} headingId="site-recommendation-heading" className="w1f4-recommendation__proposed">
          {accepted ? (
            <div className="w1f4-recommendation__claim" data-recommendation-accepted={accepted.snapshot.proposed_value}>
              Battery reserve {accepted.snapshot.old_value}
              {accepted.snapshot.unit} to {accepted.snapshot.proposed_value}
              {accepted.snapshot.unit} on <Ref value={accepted.snapshot.asset_code} />, as a measured trial.
            </div>
          ) : held ? (
            <div className="w1f4-recommendation__claim" data-recommendation-held={holdCode}>
              {HOLD_HEADINGS[holdCode] ?? HOLD_HEADINGS.PRIOR_ACTION_UNRESOLVED}.
            </div>
          ) : body.proposal ? (
            <div className="w1f4-recommendation__claim" data-recommendation-proposal={body.proposal.proposed_value}>
              Battery reserve {body.proposal.old_value}
              {body.proposal.unit} to {body.proposal.proposed_value}
              {body.proposal.unit} on <Ref value={body.proposal.asset_code} />, as a measured trial.
            </div>
          ) : (
            <div className="w1f4-recommendation__claim" data-recommendation-unavailable={body.unavailable?.code ?? "UNKNOWN"}>
              The fixed rule proposes no reserve trial for this Finding version.
            </div>
          )}

          {/* The mock's one prose paragraph: the trial-only limitation, always visible. */}
          <TrialLimitation limitation={body.rule.limitation} />

          <KeyValues
            label="Proposed intervention"
            rows={[
              ["Suggested owner", <span key="owner" data-panel-gap="site-recommendation-owner">Not recorded</span>, "owner"],
              ["Action type", `Battery reserve trial (${SYSTEM_DEMONSTRATION})`, "type"],
              [
                "Origin",
                <span key="origin">
                  <Link to={links.finding(body.revision_id)} data-recommendation-finding-link>
                    This Finding version
                  </Link>
                  {body.is_latest ? (
                    " (latest)"
                  ) : (
                    <span data-recommendation-newer-revision={body.latest_revision_id}>
                      {" · a "}
                      <Link to={links.finding(body.latest_revision_id)}>newer version</Link> exists
                    </span>
                  )}
                </span>,
                "origin",
              ],
              [
                "Configuration change",
                shown ? (
                  <span key="change">
                    Battery reserve {shown.old_value}
                    {shown.unit} to {shown.proposed_value}
                    {shown.unit}
                  </span>
                ) : (
                  <span key="change" data-panel-gap="site-recommendation-change">
                    None proposed
                  </span>
                ),
                "change",
              ],
              [
                "Source",
                <span key="source" data-recommendation-source-state={source}>
                  {SOURCE_WORDS[source].label}
                </span>,
                "source",
              ],
            ]}
          />

          {acceptControl}
          <AcceptOutcome outcome={outcome} links={links} />

          <p className="v69-chart-note">
            <span data-recommendation-next="">{words.next ?? words.sentence}</span>{" "}
            {body.money_consequence ? (
              <span data-recommendation-money-link="">
                <Link to={links.money(body.money_consequence.basis.finding_revision_id)}>
                  {body.money_consequence.label} of this Finding version
                </Link>
                : the Finding&apos;s figure, not the trial&apos;s; the trial predicts no saving.
              </span>
            ) : (
              <span data-recommendation-money-link="finding">
                <Link to={links.money(body.revision_id)}>What this Finding means in money</Link>: any figure is the Finding&apos;s,
                not the trial&apos;s; the trial predicts no saving.
              </span>
            )}
            {!body.source_open ? (
              <span data-recommendation-source-closed="">
                {" "}
                This site&apos;s assessments are not released for use, so this is shown as a record only.
              </span>
            ) : null}
          </p>

          <Disclosure name="recommendation-method" summary="How this was worked out">
            <FactList>
              <Fact term="Rule">
                <Ref value={`${body.rule.id} v${body.rule.version}`} attr="data-recommendation-rule" />
              </Fact>
              <Fact term="Finding version">
                <Ref value={body.revision_id} />
              </Fact>
              {!body.is_latest ? (
                <Fact term="Newer Finding version">
                  <Ref value={body.latest_revision_id} />
                </Fact>
              ) : null}
              {body.unavailable ? (
                <Fact term={held ? "Hold reason" : "Reason no trial is proposed"}>
                  <Ref value={body.unavailable.code} /> {body.unavailable.message}
                </Fact>
              ) : held && block ? (
                <Fact term="Hold reason">
                  <Ref value={block.code} /> {block.message}
                </Fact>
              ) : null}
            </FactList>
            <SourceProvenanceNotice provenance={body.source_provenance} subject="finding version" name="recommendation" />
            {accepted ? (
              <LiveLines live={body.live_status} />
            ) : held ? (
              <LiveLines
                live={body.live_status}
                note="Live recomputation, from the current stored inputs. This is a separate reason, shown for information; it does not make a new trial acceptable here."
              />
            ) : null}
            {priorActions.length > 0 ? <PriorActionList items={priorActions} links={links} /> : null}
            {shown ? <StoredInputs shown={shown} proposal={accepted ? null : body.proposal} /> : null}
          </Disclosure>
        </Panel>

        {accepted && links.actionChild ? (
          <DeclaredSuccessPanel
            actionId={accepted.action_id}
            summary={body.verification?.[accepted.action_id]}
            links={{ child: links.actionChild }}
          />
        ) : (
          <Panel heading={SUCCESS} headingId="site-recommendation-success-heading">
            <PanelGap id="site-recommendation-success-heading">No success criteria recorded.</PanelGap>
            <ChartNote>The trial&apos;s success criteria are recorded with its acceptance; this Finding version has none.</ChartNote>
          </Panel>
        )}
      </div>

      <p className="notice notice--info w1f4-recommendation__notice" data-recommendation-accept-limit>
        {ACCEPT_LIMIT}
      </p>

      {accepted && links.actionChild ? (
        <EvidenceNeededPanel
          actionId={accepted.action_id}
          actionCode={accepted.action_code}
          summary={body.verification?.[accepted.action_id]}
          links={{ child: links.actionChild }}
          actionHref={links.action(accepted.action_id)}
        />
      ) : (
        <Panel heading={EVIDENCE} headingId="site-recommendation-evidence-heading">
          <PanelGap id="site-recommendation-evidence-heading">Requirements not recorded.</PanelGap>
          <ChartNote>Evidence requirements exist only for an accepted trial.</ChartNote>
        </Panel>
      )}
    </div>
  );
}

/** An honest in-panel gap line. */
function PanelGap({ id, children }: { id: string; children: ReactNode }) {
  return (
    <p className="v69-chart-note w1f4-recommendation__gap" data-panel-gap={id}>
      {children}
    </p>
  );
}

const REFUSAL_TITLES: Record<number, string> = {
  401: "Sign-in required",
  403: "No access",
  404: "Recommendation not found",
  409: "Refused",
  422: "Refused",
};

/** The typed refusal of a read, as the page-level refusal line (never an h2 panel). */
function RefusalLine({ refusal, kind, children }: { refusal: Refusal; kind: string; children?: ReactNode }) {
  const title =
    refusal.http === null ? "Recommendation unavailable" : (REFUSAL_TITLES[refusal.http] ?? "Recommendation unavailable");
  const text =
    refusal.http === null
      ? "The server could not be reached."
      : refusal.http === 401
        ? "Sign in to read this site's Actions."
        : refusal.http === 403
          ? "Your account has no access to this."
          : refusal.http === 404
            ? "This site has no such recommendation."
            : `The recommendation could not be read (HTTP ${refusal.http}).`;
  return (
    <div className="page-refusal" role="status" data-page-refusal={kind}>
      <p className="page-refusal__title">
        <strong>{title}</strong>
      </p>
      <p data-action-read="refused" data-action-http={refusal.http ?? "none"} data-action-code={refusal.code ?? ""}>
        {text}
      </p>
      {refusal.code ? (
        <p className="action-note">
          Code: <Ref value={refusal.code} />
        </p>
      ) : null}
      {refusal.message ? <p className="action-note">Reason given: {refusal.message}</p> : null}
      {children}
    </div>
  );
}

/** A refused first read: the refusal line, then the three v69 slots, each with its gap inside. */
function RefusedRecommendation({ refusal }: { refusal: Refusal }) {
  const gap = "The recommendation could not be read, so nothing is shown here.";
  return (
    <div className="site-recommendation w1f4-recommendation" data-recommendation-state="REFUSED">
      <RefusalLine refusal={refusal} kind="refused" />
      <div className="panel-pair">
        <Panel heading={PROPOSED} headingId="site-recommendation-heading">
          <PanelGap id="site-recommendation-heading">{gap}</PanelGap>
        </Panel>
        <Panel heading={SUCCESS} headingId="site-recommendation-success-heading">
          <PanelGap id="site-recommendation-success-heading">No success criteria recorded. {gap}</PanelGap>
        </Panel>
      </div>
      <Panel heading={EVIDENCE} headingId="site-recommendation-evidence-heading">
        <PanelGap id="site-recommendation-evidence-heading">Requirements not recorded. {gap}</PanelGap>
      </Panel>
    </div>
  );
}

function AcceptOutcome({ outcome, links }: { outcome: CommandResult | null; links: SiteRecommendationLinks }) {
  if (outcome === null) return null;
  if (outcome.status === "done") {
    return (
      <p role="status" className="v69-chart-note" data-action-command-done={outcome.replayed ? "replayed" : "created"}>
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
      <p role="status" className="v69-chart-note" data-action-command-done="already-accepted">
        This trial was already accepted.{" "}
        <Link to={links.action(outcome.detail.action_id)}>Open the existing Action</Link>.
      </p>
    );
  }
  return <CommandRefusal refusal={outcome} />;
}

/** The stored inputs and pinned versions behind the shown proposal (inside "How this was worked out"). */
function StoredInputs({ shown, proposal }: { shown: Proposal | AcceptedRecommendation["snapshot"]; proposal: Proposal | null }) {
  const evidenceIds = proposal
    ? Array.from(new Set(proposal.inputs.segments.map((segment) => segment.selected_soc?.evidence_id).filter((id): id is string => !!id)))
    : [];
  const assessmentIds = proposal ? Array.from(new Set(proposal.inputs.segments.map((segment) => segment.assessment_revision_id))) : [];
  return (
    <div data-recommendation-inputs={proposal ? `${assessmentIds.length} assessment, ${evidenceIds.length} readings` : "pinned"}>
      <PinnedFacts proposal={shown} />
      {proposal ? (
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
          <Fact term="Input reference">
            <Ref value={proposal.input_sha256} />
          </Fact>
        </FactList>
      ) : null}
    </div>
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

/** The live recomputation: a labelled note line, then what the rule says on current inputs. */
function LiveLines({
  live,
  note = "Live recomputation, from the current stored inputs. This is not the accepted proposal.",
}: {
  live: LiveStatus | null;
  note?: string;
}) {
  return (
    <>
      <ChartNote>{note}</ChartNote>
      {live === null ? (
        <ChartNote data={{ "data-recommendation-live": "none" }}>No live recomputation was returned.</ChartNote>
      ) : live.state === "AVAILABLE" && live.proposal ? (
        <ChartNote data={{ "data-recommendation-live": "AVAILABLE" }}>
          The rule would propose {live.proposal.old_value}
          {live.proposal.unit} to {live.proposal.proposed_value}
          {live.proposal.unit} on current inputs.
        </ChartNote>
      ) : (
        <ChartNote data={{ "data-recommendation-live": live.state }}>
          No proposal on current inputs.
          {live.unavailable ? (
            <>
              {" "}
              Reason: <Ref value={live.unavailable.code} /> {live.unavailable.message}
            </>
          ) : null}
        </ChartNote>
      )}
    </>
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
  /** The blocking Action was accepted on another Finding (the hold is per battery). */
  otherFinding: boolean;
  /** The guardrail-failed outcome behind `PRIOR_TRIAL_GUARDRAIL_FAILED`. */
  outcomeId: string | null;
  /** The withdrawn outcome behind `PRIOR_TRIAL_REASSESSMENT_OVERLAP`. */
  withdrawnOutcomeId: string | null;
  withdrawnActionId: string | null;
}

/** The typed prior-trial holds (S6-01 unresolved, S6-02a guardrail failure and reassessment overlap). */
const HELD_STATES = new Set(["PRIOR_ACTION_UNRESOLVED", "PRIOR_TRIAL_GUARDRAIL_FAILED", "PRIOR_TRIAL_REASSESSMENT_OVERLAP"]);

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
    otherFinding: action !== null && action.origin.finding_id !== body.finding_id,
    outcomeId: typed?.blocking_outcome_id ?? (typed?.code === "PRIOR_TRIAL_GUARDRAIL_FAILED" ? action?.resolution?.outcome_id ?? null : null),
    withdrawnOutcomeId: typeof typed?.overlaps?.[0]?.withdrawn_outcome_id === "string" ? (typed.overlaps[0].withdrawn_outcome_id as string) : null,
    withdrawnActionId: typeof typed?.overlaps?.[0]?.closure_action_id === "string" ? (typed.overlaps[0].closure_action_id as string) : null,
  };
}

/** The hold's plain claim line in panel 1. */
const HOLD_HEADINGS: Record<string, string> = {
  PRIOR_ACTION_UNRESOLVED: "An earlier trial is still open",
  PRIOR_TRIAL_GUARDRAIL_FAILED: "An earlier trial missed a safety or service limit",
  PRIOR_TRIAL_REASSESSMENT_OVERLAP: "An earlier trial's result was withdrawn after a new acceptance",
};

/**
 * The earlier Action that holds a new acceptance, as inline spans of the one
 * held-accept note: its origin version, its application and outcome state, and
 * the outcome link behind a guardrail or overlap hold. The typed reason code
 * sits in "How this was worked out".
 */
function PriorActionHold({ block, links, code }: { block: HeldBy | null; links: SiteRecommendationLinks; code: string }) {
  if (block === null) {
    return <span data-recommendation-prior-block="UNKNOWN">The server did not name the earlier trial.</span>;
  }
  return (
    <>
      <span data-recommendation-prior-block={block.actionId}>
        It was accepted on{" "}
        {block.originRevisionId ? (
          <Link to={links.finding(block.originRevisionId)} data-recommendation-prior-block-origin={block.originRevisionId}>
            {block.originRevisionNo !== null ? `Finding version ${block.originRevisionNo}` : "an earlier Finding version"}
          </Link>
        ) : (
          "an earlier Finding version"
        )}
        {block.otherFinding ? " of a different Finding" : ", not on the version shown on this page"}.
      </span>
      {block.otherFinding ? (
        <span data-recommendation-prior-block-other-finding={block.action?.origin.finding_id ?? ""}>
          {" "}
          The hold is per battery; this page&apos;s Finding is not that one.
        </span>
      ) : null}
      {block.action ? (
        <span data-recommendation-prior-block-state={block.action.application.state}>
          {" "}
          {APPLICATION_WORDS[block.action.application.state] ?? block.action.application.state}.{" "}
          {outcomeWords(block.action.outcome.state)}
        </span>
      ) : null}
      {code !== "PRIOR_ACTION_UNRESOLVED" ? (
        <span data-recommendation-prior-block-code={code}>
          {block.outcomeId && links.actionChild ? (
            <>
              {" "}
              <Link
                to={links.actionChild(block.actionId, "verification", { outcomeId: block.outcomeId })}
                data-recommendation-prior-block-outcome={block.outcomeId}
              >
                Open that outcome
              </Link>
              .
            </>
          ) : null}
          {block.withdrawnOutcomeId && block.withdrawnActionId && links.actionChild ? (
            <>
              {" "}
              <Link
                to={links.actionChild(block.withdrawnActionId, "verification", { outcomeId: block.withdrawnOutcomeId })}
                data-recommendation-prior-block-withdrawn={block.withdrawnOutcomeId}
              >
                Open the withdrawn outcome
              </Link>
              .
            </>
          ) : null}
        </span>
      ) : null}
    </>
  );
}

/** An Action's application words, with its failed attempts counted (never dropped). */
function applicationText(item: PriorAction): string {
  const failed = item.application.failed_attempts;
  return `${APPLICATION_WORDS[item.application.state] ?? item.application.state}${
    failed > 0 ? `, ${failed} failed ${failed === 1 ? "attempt" : "attempts"}` : ""
  }`;
}

/** Every Action on this canonical Finding, each with its own origin version (never relabelled). */
function PriorActionList({ items, links }: { items: PriorAction[]; links: SiteRecommendationLinks }) {
  return (
    <div className="w1f4-recommendation__prior" data-recommendation-prior-actions>
      <ChartNote>Actions on this Finding. Each keeps the Finding version it was accepted on.</ChartNote>
      <ul className="action-list w1f4-recommendation__prior-list">
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
    </div>
  );
}

/** The latest end of the stored input windows: the plain "as of" bound of a proposal. */
function inputsAsOf(segments: readonly { end: string }[] | null | undefined): string | null {
  const ends = (segments ?? []).map((segment) => segment.end).filter((end) => !!end).sort();
  return ends.length === 0 ? null : ends[ends.length - 1];
}

/** The latest recorded step of the Actions holding new trials: resolution, failed attempt or acceptance. */
function heldAsOf(body: RecommendationBody): string | null {
  const blocking = (body.prior_action_block?.blocking_actions ?? []) as (PriorAction & { resolution?: { recorded_at?: string | null } | null })[];
  const times = blocking
    .flatMap((action) => [action.resolution?.recorded_at, action.application?.last_failure?.recorded_at, action.accepted_at])
    .filter((t): t is string => typeof t === "string" && t !== "")
    .sort((a, b) => Date.parse(a) - Date.parse(b));
  return times.length === 0 ? null : times[times.length - 1];
}

/**
 * The mock's one-line status strip: the Recommendation badge and state word as
 * the lead, the state sentence, the scope and "as of" bound, then the next
 * link and the exact references. A proposal or acceptance is never a result.
 * (Replaces the W1-UX-04 answer card; its state line keeps the shared hooks.)
 */
function RecommendationStrip({
  body,
  accepted,
  block,
  links,
}: {
  body: RecommendationBody;
  accepted: AcceptedRecommendation | null;
  block: HeldBy | null;
  links: SiteRecommendationLinks;
}) {
  const words = recommendationWords(accepted ? "ACCEPTED" : body.state);
  const shown = accepted ? accepted.snapshot : body.proposal;
  // The read carries no read instant: the bound is the acceptance time, else the latest stored input it was computed from.
  // A hold is bounded by the latest recorded step of the blocking Action(s).
  const asOf = accepted
    ? accepted.accepted_at
    : block !== null
      ? heldAsOf(body)
      : inputsAsOf(shown?.inputs?.segments ?? body.live_status?.proposal?.inputs?.segments ?? body.segments);
  const scope = `This Finding version, battery reserve rule${accepted ? " (stored when accepted)" : ""}`;
  return (
    <section
      className="status-strip status-strip--line w1f4-recommendation__strip"
      aria-label="Recommendation state"
      data-product-status={words.tone}
    >
      <span className="status-strip__lead">
        <Badge tone="neutral">Recommendation</Badge>{" "}
        <strong className="status-strip__state" data-product-status-label>
          {words.label}
        </strong>
      </span>
      <span className="status-strip__item product-status__sentence">{words.sentence}</span>
      <span className="muted status-strip__item">
        <span data-product-status-scope>{scope}</span>
        <span aria-hidden="true"> · </span>
        <span data-product-status-as-of>{asOfText(asOf)}</span>
      </span>
      <span className="status-strip__spacer" aria-hidden="true" />
      <span className="status-strip__action">
        {accepted ? (
          <>
            <Link to={links.action(accepted.action_id)} data-recommendation-card-action-link>
              Open the Action
            </Link>
            {links.actionChild ? (
              <>
                {" · "}
                <Link to={links.actionChild(accepted.action_id, "verification")} data-recommendation-card-verification-link>
                  Open Verification
                </Link>
              </>
            ) : null}
          </>
        ) : block ? (
          <Link to={links.action(block.actionId)} data-recommendation-card-held-link>
            Open the earlier Action
          </Link>
        ) : (
          <Link to={links.finding(body.revision_id)} data-recommendation-card-finding-link>
            Open the Finding
          </Link>
        )}
      </span>
      <ExactReferences
        name="recommendation-references"
        variant="tech"
        references={[
          { label: "Rule", value: `${body.rule.id} v${body.rule.version}` },
          { label: "Finding version", value: body.revision_id },
          { label: "Recommendation state", value: body.state },
          { label: "Reason no trial is proposed", value: body.unavailable?.code ?? null },
          { label: "Input reference", value: shown?.input_sha256 ?? null },
          { label: "Action reference", value: accepted?.action_id ?? null },
        ]}
      />
    </section>
  );
}
