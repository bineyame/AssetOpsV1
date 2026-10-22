/**
 * W4-03 unit 7: the typed five-day Opportunity detail (v69 `opportunity-finding`, Overview only per closure 4 B5) and
 * the exact W4-02 renewable CTA (closure 4 S14, closure 1 Q17-Q30).
 *
 * Every value is the persisted read's: the frozen physical `status`/`headroom_kw`/day counts, read-time
 * `currentness` and selected provenance (the u5 ruling 1 positive gate), and the compatible authored scenario's
 * gated fields. Mock `F-109`, Medium, 18–20 kW, 3/5, 10 kW × 1 h, the tariff and $2.50 never appear as defaults; a
 * missing source reads as its exact gap copy (u4 value mapping, u6 dry-read).
 */
import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Badge, BigClaim, KeyValues, MetricCard, MetricCards, Panel, StatusBar } from "../ui";
import { localDateOf, addDays, localMidnightUtc } from "./miniDepthClient";
import { decisionRefusalCopy } from "./miniDecisionsClient";
import type {
  DecisionRead,
  MiniDecisionsClient,
  OpportunityBound,
  OpportunityDetailBody,
  OpportunityListBody,
} from "./miniDecisionsClient";
import { scenarioMoney } from "./MiniScenarios";
import "./w4-mini-decisions.css";

export { decisionRefusalCopy };

export const OPPORTUNITY_MODEL = "mini-opportunity/1";
export const OPPORTUNITY_LOADING = "Loading the opportunity.";
export const OPPORTUNITY_DECISION_LOADING = "Loading the opportunity decision.";
export const OPPORTUNITY_ZERO = "Opportunity decision unavailable for this selected five-day study.";
export const OPPORTUNITY_SHORT = "Opportunity decision unavailable for fewer than five assessed days.";
export const OPPORTUNITY_ROOT_GAP = "Global Findings unavailable; this opportunity is reached from Renewable evaluation.";
export const RENEWABLE_UNAVAILABLE = "Renewable evaluation unavailable";
export const FEASIBILITY_LIMIT =
  "Electrical feasibility does not establish customer demand, collections or a realised financial benefit.";
export const NO_OPPORTUNITY_EVIDENCE = "No selected opportunity evidence";

const STUDY_DAYS = 5;
const UNKNOWN = "Unknown";
const NOT_ESTABLISHED = "Not established";
const PENDING_STATES = new Set(["PENDING_RECOMPUTE", "STALE_SOURCE"]);
const GATE_STATES = new Set(["CURRENT", "HISTORICAL"]);
const BLOCKED_CLASSES = new Set(["MIXED", "UNKNOWN"]);

const CURRENTNESS_WORDS: Record<string, string> = {
  CURRENT: "Current selection",
  PENDING_RECOMPUTE: "Recompute pending",
  STALE_SOURCE: "Source changed since selection",
  HISTORICAL: "Historical basis",
  UNKNOWN: "Selection unknown",
};

type Body = Pick<OpportunityDetailBody, "opportunity" | "status" | "currentness" | "selected_source_provenance">;

const selectedClassOk = (body: Body) => {
  const c = body.selected_source_provenance?.classification ?? null;
  return c !== null && !BLOCKED_CLASSES.has(c);
};

/** All five days assessed (`ELIGIBLE|EXCLUDED`) in the frozen result. */
const fiveAssessed = (body: Body) => body.opportunity !== null && body.opportunity.assessed_days === STUDY_DAYS;

/** A frozen SUPPORTED five-day result readable at this cutoff (current or historical, resolved selected class). */
export function supportedRead(body: Body): boolean {
  return body.status === "SUPPORTED" && fiveAssessed(body) && GATE_STATES.has(body.currentness.state) && selectedClassOk(body);
}

/** u5 ruling 1 (the read test's `positive()`): the only inputs that may render the green chip. */
export function positiveOpportunity(body: Body): boolean {
  return (
    body.status === "SUPPORTED" &&
    (body.opportunity?.eligible_days ?? 0) > 0 &&
    body.currentness.state === "CURRENT" &&
    selectedClassOk(body)
  );
}

/** Closure 1 chip tones: green only the positive gate, blue historical, amber limited/pending, grey otherwise. */
export function opportunityTone(body: Body): "green" | "blue" | "amber" | "gray" {
  if (positiveOpportunity(body)) return "green";
  if (body.currentness.state === "HISTORICAL") return "blue";
  if (body.status === "LIMITED" || PENDING_STATES.has(body.currentness.state)) return "amber";
  return "gray";
}

function kwText(bound: OpportunityBound | null): string | null {
  if (bound === null) return null;
  return bound.low === bound.high ? `${bound.low} kW` : `${bound.low}–${bound.high} kW`;
}

/** The proposal fits each counted hour iff its kW is at most every eligible day's lower bound (u4 headroom rule). */
function proposalFits(body: OpportunityDetailBody): boolean {
  const o = body.opportunity;
  if (o === null || o.proposed_load_kw === null || (o.eligible_days ?? 0) === 0) return false;
  const kw = Number(o.proposed_load_kw);
  const eligible = o.day_rows.filter((r) => r.decision === "ELIGIBLE");
  return (
    eligible.length > 0 && eligible.every((r) => r.opportunity_kwh !== null && kw <= Number(r.opportunity_kwh.low))
  );
}

function grossText(body: OpportunityDetailBody): string | null {
  const g = body.opportunity?.gross_sales_scenario ?? null;
  return g === null ? null : scenarioMoney(g.amount, g.currency);
}

function grossGap(body: OpportunityDetailBody): string {
  return PENDING_STATES.has(body.currentness.state) ? "Withheld pending evidence" : "Not calculated";
}

/** The frontend renewable address: the authorized Site code plus the stored study `from`/`to`/`known_at` (u6). */
export function renewableHref(body: OpportunityDetailBody, siteCode: string, performanceHref: string): string | null {
  const raw = body.links.renewable;
  if (raw === null) return null;
  const q = raw.indexOf("?");
  if (q < 0) return null;
  const params = new URLSearchParams(raw.slice(q + 1));
  const from = params.get("from");
  const to = params.get("to");
  const knownAt = params.get("known_at");
  if (from === null || to === null || knownAt === null || siteCode === "") return null;
  const out = new URLSearchParams({ from, to, known_at: knownAt });
  return `${performanceHref}?${out.toString()}`;
}

function evidenceUnion(body: OpportunityDetailBody): string[] {
  return Array.from(new Set((body.opportunity?.day_rows ?? []).flatMap((r) => r.evidence_ids))).sort();
}

function OpportunityStatus({ body }: { body: OpportunityDetailBody }) {
  const o = body.opportunity!;
  const tone = opportunityTone(body);
  const recommendation = supportedRead(body) && (o.eligible_days ?? 0) > 0 && o.headroom_kw !== null;
  return (
    <StatusBar label="Opportunity status" items data={{ "data-opportunity-status": body.status }}>
      <span className="status-strip__item" data-opportunity-chip={tone}>
        <Badge tone="neutral" className={`mini-opportunity-tone--${tone}`}>
          {`${o.code} · Opportunity`}
        </Badge>
      </span>
      <span className="status-strip__item" data-opportunity-confidence>
        Confidence: Not assessed
      </span>
      <span className="status-strip__item" data-opportunity-currentness={body.currentness.state}>
        {CURRENTNESS_WORDS[body.currentness.state] ?? body.currentness.state}
      </span>
      <span className="status-strip__item v69-statusbar__other" data-opportunity-secondary>
        {recommendation ? "Recommendation · demand unverified" : "Decision pending · evidence limited"}
      </span>
    </StatusBar>
  );
}

function OpportunityCards({ body }: { body: OpportunityDetailBody }) {
  const o = body.opportunity!;
  const headroom = body.status === "SUPPORTED" ? kwText(o.headroom_kw) : null;
  const days = fiveAssessed(body) && o.eligible_days !== null ? `${o.eligible_days} / ${o.assessed_days}` : NOT_ESTABLISHED;
  const linked = o.scenario_id !== null;
  const gross = grossText(body);
  return (
    <MetricCards label="Opportunity summary" data={{ "data-opportunity-cards": "" }}>
      {/* PR-12.2: a nonnumeric honest state is a `word` value; numeric and monetary values stay verbatim. */}
      <MetricCard
        label="Usable headroom"
        value={headroom ?? UNKNOWN}
        word={headroom === null}
        note="After the selected retained margin"
      />
      <MetricCard
        label="Eligible days"
        value={days}
        word={days === NOT_ESTABLISHED}
        note={fiveAssessed(body) ? "Separate five-day study" : "Five-day study incomplete"}
      />
      <MetricCard
        label="Proposed load"
        value={o.proposed_load_kw === null ? "No load proposed" : `${o.proposed_load_kw} kW`}
        word={o.proposed_load_kw === null}
        note={linked ? "Linked scenario (name unavailable)" : "No scenario linked"}
      />
      <MetricCard
        label="Gross sales scenario"
        value={gross ?? grossGap(body)}
        word={gross === null}
        note="Before costs; collections unverified"
      />
    </MetricCards>
  );
}

function BoundedOpportunity({ body, recordHref }: { body: OpportunityDetailBody; recordHref: (id: string) => string }) {
  const [open, setOpen] = useState(false);
  const o = body.opportunity!;
  const ids = evidenceUnion(body);
  const claim = !supportedRead(body)
    ? "The selected evidence does not establish a recurring productive-use opportunity."
    : proposalFits(body)
      ? `Renewable capacity appears available for a one-hour productive load in ${o.eligible_days} adequately observed windows.`
      : `Measured renewable headroom is available in ${o.eligible_days} of ${o.assessed_days} assessed windows; no added load has been validated.`;
  return (
    <Panel heading="Bounded opportunity" headingId="mini-opportunity-bounded-heading" className="mini-opportunity-panel">
      <BigClaim data={{ "data-opportunity-claim": "" }}>{claim}</BigClaim>
      <p className="prose">{FEASIBILITY_LIMIT}</p>
      <p>
        <button
          type="button"
          className="link-button v69-claim-button"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          data-opportunity-evidence-open
        >
          Inspect opportunity evidence
        </button>
      </p>
      {open ? (
        <div className="mini-opportunity-drawer" data-opportunity-evidence>
          {ids.length === 0 ? (
            <p>{NO_OPPORTUNITY_EVIDENCE}</p>
          ) : (
            <ul className="mini-scenarios-pins">
              {ids.map((id) => (
                <li key={id}>
                  <Link to={recordHref(id)} data-opportunity-cited={id}>
                    <code>{id}</code>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </Panel>
  );
}

function NextDecision({ body, renewable }: { body: OpportunityDetailBody; renewable: string | null }) {
  const o = body.opportunity!;
  const ready = supportedRead(body) && (o.eligible_days ?? 0) > 0 && o.headroom_kw !== null;
  return (
    <Panel heading="Next decision" headingId="mini-opportunity-next-heading" className="mini-opportunity-panel">
      <p className="prose">
        {ready
          ? "Validate local demand, schedule any proposed load, and check critical service and storage guardrails before a trial."
          : "Complete the missing renewable and service evidence before a load decision."}
      </p>
      <p data-opportunity-renewable>
        {renewable === null ? (
          <span className="mini-scenarios-gap">{RENEWABLE_UNAVAILABLE}</span>
        ) : (
          <Link className="button primary" to={renewable}>
            Open renewable evaluation
          </Link>
        )}
      </p>
    </Panel>
  );
}

function ConsequenceBasis({ body }: { body: OpportunityDetailBody }) {
  const o = body.opportunity!;
  const technical = body.status === "SUPPORTED" ? kwText(o.headroom_kw) : null;
  const linked = o.scenario_id !== null;
  const gross = grossText(body);
  return (
    <Panel heading="Consequence basis" headingId="mini-opportunity-basis-heading" className="mini-opportunity-panel">
      <KeyValues
        label="Consequence basis"
        rows={[
          ["Technical quantity", technical === null ? UNKNOWN : `${technical} usable headroom`, "technical"],
          ["Scenario energy", linked ? "Unavailable in this read" : "No load scenario", "energy"],
          ["Tariff", linked ? "Unavailable in this read" : "No tariff declared", "tariff"],
          ["Gross sales", gross === null ? grossGap(body) : `${gross} · scenario`, "gross"],
          ["Managed Action", "Not yet accepted", "action"],
        ]}
      />
    </Panel>
  );
}

/** The Overview body in the mock's order: status, four cards, Bounded opportunity, Next decision | Consequence basis. */
export function MiniOpportunityPage({
  body,
  renewable,
  recordHref,
}: {
  body: OpportunityDetailBody;
  renewable: string | null;
  recordHref: (id: string) => string;
}) {
  return (
    <div className="mini-opportunity" data-opportunity-page>
      <OpportunityStatus body={body} />
      <OpportunityCards body={body} />
      <BoundedOpportunity body={body} recordHref={recordHref} />
      <div className="panel-pair">
        <NextDecision body={body} renewable={renewable} />
        <ConsequenceBasis body={body} />
      </div>
    </div>
  );
}

/** One detail read for the route's Site and opportunity ID. */
export function useOpportunity(
  client: MiniDecisionsClient,
  siteCode: string,
  opportunityId: string,
  enabled: boolean,
  knownAt: readonly string[] = [],
): DecisionRead<OpportunityDetailBody> | null {
  // PR-12.6: keyed by Site, ID and cutoff, so a changed `known_at` is a new read.
  const cutoff = JSON.stringify(knownAt);
  const key = `${siteCode}|${opportunityId}|${cutoff}`;
  const [state, setState] = useState<{ key: string; read: DecisionRead<OpportunityDetailBody> } | null>(null);
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    void client.getOpportunity(siteCode, opportunityId, JSON.parse(cutoff) as string[]).then((read) => {
      if (active) setState({ key, read });
    });
    return () => {
      active = false;
    };
  }, [client, siteCode, opportunityId, cutoff, key, enabled]);
  return state !== null && state.key === key ? state.read : null;
}

/* ---------- W4-02 renewable CTA (closure 4 S14) ---------- */

/** The selected renewable window as whole Site-local days, or null when its bounds are not local midnights. */
export function selectedLocalDays(
  timeZone: string,
  from: string | null,
  to: string | null,
): { first: string; last: string; days: number } | null {
  if (from === null || to === null) return null;
  const fromMs = Date.parse(from);
  const toMs = Date.parse(to);
  if (Number.isNaN(fromMs) || Number.isNaN(toMs) || toMs <= fromMs) return null;
  const first = localDateOf(timeZone, fromMs);
  if (localMidnightUtc(timeZone, first) !== fromMs) return null;
  for (let days = 1; days <= STUDY_DAYS; days += 1) {
    if (localMidnightUtc(timeZone, addDays(first, days)) === toMs) return { first, last: addDays(first, days - 1), days };
  }
  return null;
}

type CtaState =
  | { kind: "short" }
  | { kind: "loading" }
  | { kind: "zero" }
  | { kind: "one"; id: string }
  | { kind: "refused"; copy: string };

/** S14: exactly one current study with the selected five days and `mini-opportunity/1`; never pick among several. */
export function matchStudy(list: OpportunityListBody, first: string, last: string): CtaState {
  const hits = list.rows.filter(
    (r) =>
      r.opportunity !== null &&
      r.opportunity.first_day === first &&
      r.opportunity.last_day === last &&
      r.opportunity.model_version === OPPORTUNITY_MODEL,
  );
  if (hits.length === 0) return { kind: "zero" };
  if (hits.length > 1) return { kind: "refused", copy: "Decisions are unavailable right now. Try again." };
  return { kind: "one", id: hits[0].opportunity!.id };
}

/**
 * The renewable page's `Opportunity decision` entry: no lookup for a 1–4-day selection; otherwise one scoped list
 * read for the five selected local days (at the renewable read's cutoff) and the exact-match rule above.
 */
export function OpportunityDecisionEntry({
  client,
  siteCode,
  timeZone,
  window,
  detailHref,
}: {
  client: MiniDecisionsClient;
  siteCode: string;
  timeZone: string;
  window: { from: string | null; to: string | null; known_at: string | null };
  /** PR-12.6: the detail address carries the renewable read's cutoff (null: current time). */
  detailHref: (opportunityId: string, knownAt: string | null) => string;
}): ReactNode {
  const days = selectedLocalDays(timeZone, window.from, window.to);
  const five = days !== null && days.days === STUDY_DAYS;
  const key = `${siteCode}|${window.from}|${window.to}|${window.known_at}`;
  const [state, setState] = useState<{ key: string; cta: CtaState } | null>(null);
  useEffect(() => {
    if (!five || days === null) return;
    let active = true;
    void client.listOpportunities(siteCode, { from: window.from!, to: window.to!, known_at: window.known_at }).then((read) => {
      if (!active) return;
      setState({
        key,
        cta: read.status === "loaded" ? matchStudy(read.value, days.first, days.last) : { kind: "refused", copy: decisionRefusalCopy(read) },
      });
    });
    return () => {
      active = false;
    };
    // `key` carries the window; `days` is derived from it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, key, five]);
  const cta: CtaState = !five ? { kind: "short" } : state !== null && state.key === key ? state.cta : { kind: "loading" };
  return (
    <p data-opportunity-decision={cta.kind}>
      {cta.kind === "one" ? (
        <Link to={detailHref(cta.id, window.known_at)}>Opportunity decision →</Link>
      ) : (
        <span className="mini-scenarios-gap">
          {cta.kind === "short"
            ? OPPORTUNITY_SHORT
            : cta.kind === "zero"
              ? OPPORTUNITY_ZERO
              : cta.kind === "loading"
                ? OPPORTUNITY_DECISION_LOADING
                : cta.copy}
        </span>
      )}
    </p>
  );
}
