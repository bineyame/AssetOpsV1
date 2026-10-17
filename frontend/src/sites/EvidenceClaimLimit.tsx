/**
 * S3-02b (`evidence-analysis:2#b`): what one selected dispatch assessment can
 * support, beneath S2's distinct "How each limit is set" explanation.
 *
 * The selection travels in the address as `day=<YYYY-MM-DD>&revision=<id>`
 * (the Performance > Dispatch identity); the legacy `assessment` parameter is
 * not read. Without a selected revision the section says "No assessment
 * selected" (UNASSESSED), never a zero. A positive conclusion is stated only
 * when the read is CURRENT with a ceiling from the S3-02a rule; an earlier,
 * out-of-date, pending or failed assessment is shown for audit only.
 *
 * The default reading is plain language, following the v6.9 Evidence Analysis
 * panel "How each limit is set": which readings the conclusion needs, where
 * they are missing or unreliable, and the accepted readings behind each one.
 * Rule, status codes, versions, watermarks and IDs sit behind one closed
 * "Technical details" disclosure.
 */

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { currentnessWords, readResultWords, DataTable, Disclosure, Fact, FactList, plainTime, ProductStatus } from "../ui";
import { PeriodStrip, type StripTone } from "./periodStrip";
import { isDay } from "./dispatchWords";
import type {
  AssessedDay,
  AssessedPeriod,
  CeilingBody,
  ClaimLimitClient,
  ClaimLimitRead,
  ClaimLimitResult,
  ClaimReason,
  RoleCapability,
} from "./claimLimitClient";

export const CLAIM_LIMIT_HEADING_ID = "site-evidence-selected-claim-limit-heading";
/** One labelled exact value in the technical disclosure (the single-value vocabulary exemption). */
const REF = { "data-vocabulary-exempt": "source-reference" } as const;

export const CLAIM_LIMIT_LOADING = "Loading the selected assessment's limit.";
export const ASSESSED_DAY_LOADING = "Loading the day's assessed periods.";

const ROLE_WORDS: Record<string, string> = {
  generator_state: "Generator on or off",
  feeder_demand: "Site demand",
  pv_available_power: "Solar power available",
  pcs_discharge_capability: "Battery output limit",
  battery_soc: "Battery charge level",
};

const SPAN_WORDS: Record<string, string> = {
  COVERED: "covered",
  MISSING: "missing",
  POOR_QUALITY: "unreliable readings",
  CONFLICTED: "conflicting reports",
  NOT_EVALUATED: "not checked",
};

const DAY_STATUS_WORDS: Record<string, string> = {
  CURRENT: "assessed and current",
  PENDING: "waiting to be assessed",
  STALE_PROJECTION: "being reassessed after newer readings",
  FAILED: "not assessed: the assessment failed",
  UNASSESSED: "not assessed",
};

const CLASS_WORDS: Record<string, string> = {
  CANDIDATE_AVOIDABLE: "avoidable",
  NECESSARY: "necessary",
  INDETERMINATE: "undetermined",
};

function roleName(role: string | undefined): string {
  return role === undefined ? "A reading" : (ROLE_WORDS[role] ?? role.replace(/_/g, " "));
}

/** "08:05" from an ISO instant; the instant itself when it has no time part. */
function hhmm(iso: string): string {
  const match = /T(\d{2}:\d{2})/.exec(iso);
  return match === null ? iso : match[1];
}

function period(start: string | undefined, end: string | undefined): string {
  return start === undefined || end === undefined ? "" : `${hhmm(start)}–${hhmm(end)} UTC`;
}

function asNumber(value: number | string | null | undefined): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : 0;
}

function mins(value: number | string | null | undefined): string {
  const n = asNumber(value);
  return `${Number.isInteger(n) ? n : n.toFixed(1)} min`;
}

/** The plain conclusion a ceiling supports; null when none is stated. */
function ceilingSentence(body: CeilingBody | null): string | null {
  if (body === null || body.ceiling === null) {
    return null;
  }
  if (body.ceiling === "INDETERMINATE") {
    return "The readings cannot support a conclusion about this period of generator operation: a reading it needs is missing or unreliable.";
  }
  const word = CLASS_WORDS[body.ceiling] ?? body.ceiling;
  const minutes = body.supported_minutes === null ? "" : ` for ${mins(body.supported_minutes)}`;
  return body.support === "COMPLETE"
    ? `The readings support calling this period of generator operation ${word}${minutes}. Every reading it needs is present for that time.`
    : `The readings support calling this period of generator operation ${word} for at most${minutes.replace(" for", "")}; the rest of the period is limited by the gaps below.`;
}

/** The selected interval's own period from its role spans (the read's `window` is the whole UTC day). */
function assessedPeriod(read: ClaimLimitRead): string {
  const spans = Object.values(read.capability?.roles ?? {}).flatMap((role) => role.spans);
  if (spans.length === 0) {
    return "period not stated";
  }
  const starts = spans.map((s) => s.start).sort();
  const ends = spans.map((s) => s.end).sort();
  return period(starts[0], ends[ends.length - 1]);
}

const WINDOW_SUPPORT_WORDS: Record<string, string> = {
  COMPLETE: "every reading needed is present",
  LIMITED: "some needed readings are missing or unreliable",
  INDETERMINATE: "the readings cannot support a conclusion",
};

type AssessedPeriodItem = AssessedPeriod;

function periodLabel(id: string, periods: AssessedPeriodItem[]): string {
  const found = periods.find((p) => p.id === id);
  const when = found === undefined ? "" : period(found.start, found.end);
  return when === "" ? "An assessed period" : `Period ${when}`;
}

/** Covered and total minutes of a role; the whole-day read carries only minutes by status. */
function roleCoverage(role: RoleCapability): { covered: number; total: number } {
  const byStatus = role.minutes_by_status ?? {};
  const total = Object.values(byStatus).reduce<number>((sum, v) => sum + asNumber(v), 0);
  const covered = role.covered_minutes !== undefined ? asNumber(role.covered_minutes) : asNumber(byStatus.COVERED);
  return { covered, total };
}

function reasonSentence(reason: ClaimReason): string | null {
  const when = period(reason.start, reason.end);
  const at = when === "" ? "" : `, ${when}`;
  switch (reason.code) {
    case "MISSING_ROLE":
      return reason.role === undefined ? `Some needed readings are missing${at}.` : `${roleName(reason.role)} missing${at}.`;
    case "POOR_QUALITY":
      return reason.role === undefined ? `Some readings are unreliable${at}.` : `${roleName(reason.role)}: unreliable readings${at}.`;
    case "CONFLICTING":
      return reason.role === undefined
        ? `Some readings ${reason.scope === "WINDOW" ? "for this day " : ""}conflict${at}.`
        : `${roleName(reason.role)}: conflicting reports${at}.`;
    case "GENERATOR_UNOBSERVED":
      return `The generator's on or off state was not observed${at}.`;
    case "OPEN_BOUND":
      return "The end of the generator's operation is not yet known, so its length is a lower bound.";
    case "MODEL_LIMIT":
      return `Part of the period cannot be classified from these readings${at}.`;
    case "COHORT":
      return "The set of reporting devices for this day was not settled.";
    case "CONFIGURATION":
      return "The site's recorded configuration limits this conclusion.";
    case "RULE_BASIS_INCOMPLETE":
      return "The rule's inputs for this period were incomplete.";
    case "NOT_CURRENT":
    case "NO_REVISION_SELECTED":
      return null;
    default:
      return "Another limit applies; see the technical details.";
  }
}

function headline(read: ClaimLimitRead): { tone: "lifecycle" | "neutral"; text: string } {
  const limit = read.claim_limit;
  switch (read.currentness) {
    case "UNASSESSED":
      return {
        tone: "neutral",
        text: "No assessment selected. Choose an assessed period to see what its readings can support. Nothing is concluded until one is chosen.",
      };
    case "CURRENT": {
      if (read.scope === "WINDOW") {
        return { tone: "lifecycle", text: "This is the whole day's assessment. Each assessed period carries its own limit, listed below." };
      }
      // A positive ceiling only with the rule's current positive claim; Indeterminate is stated as such.
      const positive =
        limit !== null && (limit.current_positive_claim || limit.ceiling === "INDETERMINATE") ? ceilingSentence(limit) : null;
      return { tone: "lifecycle", text: positive ?? "No conclusion is supported for this period." };
    }
    case "HISTORICAL":
      return { tone: "neutral", text: "This is an earlier version of the assessment. It is kept for audit; no current conclusion is drawn from it." };
    case "STALE_PROJECTION":
      return { tone: "neutral", text: "Newer readings arrived after this assessment and it is being redone. No current conclusion is drawn from it." };
    case "PENDING":
      return { tone: "neutral", text: "This assessment is still being worked out. No conclusion is drawn yet." };
    case "FAILED":
      return { tone: "neutral", text: "This assessment could not be completed. No conclusion is drawn from it." };
    default:
      return { tone: "neutral", text: "No conclusion is drawn from this assessment." };
  }
}

function refusalSentence(result: Exclude<ClaimLimitResult<unknown>, { status: "loaded" } | { status: "aborted" }>): string {
  switch (result.status) {
    case "unauthenticated":
      return "Sign in to see this assessment.";
    case "forbidden":
      return "Your account does not have access to this site's assessments.";
    case "not_found":
      return result.code === "ASSESSMENT_REVISION_NOT_FOUND"
        ? "That assessment was not found for this site. It may belong to another site."
        : "This site was not found, so no assessment can be shown.";
    case "closed":
      return "Assessment results are not released for this site yet, so no limit is shown.";
    case "refused":
      switch (result.code) {
        case "INVALID_REVISION_ID":
          return "The assessment named in this address is not a valid reference.";
        case "REVISION_OUTSIDE_WINDOW":
          return "That assessment belongs to a different day than the one selected.";
        case "UNSUPPORTED_RULE_VERSION":
          return "This version of the claim rule is not supported.";
        case "ACCEPTED_LINEAGE_ABSENT":
          return "The accepted readings behind that assessment could not be traced, so no limit is shown.";
        default:
          return "This assessment could not be shown.";
      }
    default:
      return "The assessment store could not be read, so nothing is shown about this assessment.";
  }
}

export interface EvidenceClaimLimitProps {
  siteId: string;
  client: ClaimLimitClient | undefined;
  /** The Performance > Dispatch address of one pinned revision (shell-built). */
  assessmentHref?: (day: string, revisionId: string) => string;
}

export function EvidenceClaimLimit({ siteId, client, assessmentHref }: EvidenceClaimLimitProps) {
  const [params] = useSearchParams();
  const rawDay = params.get("day");
  const day = isDay(rawDay) ? rawDay : null;
  const revision = params.get("revision");
  const [read, setRead] = useState<ClaimLimitResult<ClaimLimitRead> | null>(null);
  // When a refused or unread answer arrived: the only instant such an answer has (it bounds the refusal, not any data).
  const [answeredAt, setAnsweredAt] = useState<string | null>(null);
  const [assessed, setAssessed] = useState<ClaimLimitResult<AssessedDay> | null>(null);

  useEffect(() => {
    if (client === undefined || day === null) {
      setRead(null);
      return undefined;
    }
    const abort = new AbortController();
    setRead(null);
    void client.getClaimLimit(siteId, day, revision, abort.signal).then((answer) => {
      if (!abort.signal.aborted && answer.status !== "aborted") {
        setAnsweredAt(new Date().toISOString());
        setRead(answer);
      }
    });
    return () => abort.abort();
  }, [client, siteId, day, revision]);

  useEffect(() => {
    if (client === undefined || day === null) {
      setAssessed(null);
      return undefined;
    }
    const abort = new AbortController();
    setAssessed(null);
    void client.getAssessedDay(siteId, day, abort.signal).then((answer) => {
      if (!abort.signal.aborted && answer.status !== "aborted") {
        setAssessed(answer);
      }
    });
    return () => abort.abort();
  }, [client, siteId, day]);

  const select = (revisionId: string | null) => {
    const next = new URLSearchParams(params);
    next.set("view", "analysis");
    next.delete("record");
    if (revisionId === null) {
      next.delete("revision");
    } else {
      next.set("revision", revisionId);
    }
    return `?${next.toString()}`;
  };

  return (
      <div className="claim-limit" data-claim-limit-section data-claim-limit-day={day ?? ""} data-claim-limit-revision={revision ?? ""}>
        {/* W1-F2: this read sits inside the v69 "How each limit is set" panel; its label is a line, not a panel. */}
        <p className="claim-limit__label" id={CLAIM_LIMIT_HEADING_ID}>
          <strong>What the readings can support</strong>
        </p>
        <p className="prose">
          Each conclusion lists the readings it needs. When all are present for a period, the full conclusion is
          allowed. When one is missing or unreliable, the conclusion is narrowed to the periods that are covered, and
          the gap is shown rather than filled in.
        </p>
        <DayChooser day={day} />
        {day === null || client === undefined ? null : (
          <AssessedPeriods assessed={assessed} selected={revision} hrefFor={select} />
        )}
        <Body
          siteId={siteId}
          client={client}
          day={day}
          revision={revision}
          read={read}
          answeredAt={answeredAt}
          hrefFor={select}
          assessmentHref={assessmentHref}
          periods={assessed !== null && assessed.status === "loaded" ? assessed.value.periods : []}
        />
      </div>
  );
}

function DayChooser({ day }: { day: string | null }) {
  const [params, setParams] = useSearchParams();
  const [draft, setDraft] = useState(day ?? "");
  useEffect(() => setDraft(day ?? ""), [day]);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!isDay(draft)) {
      return;
    }
    const next = new URLSearchParams(params);
    next.set("view", "analysis");
    next.set("day", draft);
    next.delete("revision");
    next.delete("record");
    setParams(next);
  };
  return (
    <form className="claim-limit__day" onSubmit={submit} data-claim-limit-day-form>
      <label>
        Day (UTC){" "}
        <input type="date" value={draft} onChange={(event) => setDraft(event.target.value)} aria-label="Assessment day (UTC)" />
      </label>{" "}
      <button type="submit">Show this day</button>
    </form>
  );
}

function AssessedPeriods({
  assessed,
  selected,
  hrefFor,
}: {
  assessed: ClaimLimitResult<AssessedDay> | null;
  selected: string | null;
  hrefFor: (revisionId: string | null) => string;
}) {
  if (assessed === null) {
    return <p data-claim-limit-periods="loading">{ASSESSED_DAY_LOADING}</p>;
  }
  if (assessed.status !== "loaded") {
    return (
      <p data-claim-limit-periods="unavailable">
        The day's assessed periods could not be listed. An assessment named in the address is still read below.
      </p>
    );
  }
  if (assessed.value.periods.length === 0) {
    return (
      <p data-claim-limit-periods="none">
        {`This day is ${DAY_STATUS_WORDS[assessed.value.status] ?? "not assessed"}; there is no assessed period to choose.`}
      </p>
    );
  }
  return (
    <nav aria-label="Assessed periods on this day" data-claim-limit-periods="loaded">
      <p className="claim-limit__periods-label">{`Assessed periods (the day is ${DAY_STATUS_WORDS[assessed.value.status] ?? "in a state not known"}):`}</p>
      <ul className="claim-limit__periods">
        {assessed.value.periods.map((p) => (
          <li key={p.id}>
            <Link
              to={hrefFor(p.id)}
              aria-current={p.id === selected ? "true" : undefined}
              data-assessed-period={p.id}
            >
              {p.scope === "WINDOW" ? "Whole day" : period(p.start, p.end)}
            </Link>
          </li>
        ))}
        {selected === null ? null : (
          <li>
            <Link to={hrefFor(null)} data-assessed-period="none">
              Clear selection
            </Link>
          </li>
        )}
      </ul>
    </nav>
  );
}

function Body({
  siteId,
  client,
  day,
  revision,
  read,
  answeredAt,
  hrefFor,
  assessmentHref,
  periods,
}: {
  siteId: string;
  answeredAt: string | null;
  client: ClaimLimitClient | undefined;
  day: string | null;
  revision: string | null;
  read: ClaimLimitResult<ClaimLimitRead> | null;
  hrefFor: (revisionId: string | null) => string;
  assessmentHref?: (day: string, revisionId: string) => string;
  periods: AssessedPeriodItem[];
}) {
  if (day === null) {
    return (
      <div data-claim-limit-state="no-day" data-currentness="UNASSESSED">
        <div className="claim-limit__status">
          <ProductStatus words={currentnessWords("UNASSESSED")} scope="No assessment selected" asOf={null} />
        </div>
        <p>Choose a day, then one of its assessed periods. Nothing is concluded until an assessment is chosen.</p>
      </div>
    );
  }
  if (client === undefined) {
    return (
      <div data-claim-limit-state="unavailable">
        <div className="claim-limit__status">
          <ProductStatus words={readResultWords("unavailable")} scope={`Assessment for ${day}`} asOf={null} />
        </div>
        <p>The assessment store could not be read, so nothing is shown about a selected assessment.</p>
      </div>
    );
  }
  if (read === null) {
    return <p data-claim-limit-state="loading">{CLAIM_LIMIT_LOADING}</p>;
  }
  if (read.status === "aborted") {
    return null;
  }
  if (read.status !== "loaded") {
    return (
      <div data-claim-limit-state={read.status} data-refusal-code={"code" in read ? (read.code ?? "") : ""}>
        <div className="claim-limit__status">
          <ProductStatus
            words={readResultWords(read.status === "not_found" ? "not-found" : read.status === "unavailable" ? "unavailable" : "refused")}
            scope={revision === null ? `Assessment for ${day}` : `Selected assessment for ${day}`}
            asOf={answeredAt}
          />
        </div>
        <p>{refusalSentence(read)}</p>
        {"message" in read && read.message !== null ? (
          <Disclosure name="claim-limit-refusal-technical" summary="Technical details">
            <p>{`${"code" in read && read.code !== null ? `${read.code}: ` : ""}${read.message}`}</p>
          </Disclosure>
        ) : null}
      </div>
    );
  }
  return <Loaded siteId={siteId} read={read.value} revision={revision} hrefFor={hrefFor} assessmentHref={assessmentHref} periods={periods} />;
}

function Loaded({
  read,
  revision,
  hrefFor,
  assessmentHref,
  periods,
}: {
  siteId: string;
  read: ClaimLimitRead;
  revision: string | null;
  hrefFor: (revisionId: string | null) => string;
  assessmentHref?: (day: string, revisionId: string) => string;
  periods: AssessedPeriodItem[];
}) {
  const [params] = useSearchParams();
  const recordHref = (evidenceId: string) => {
    const next = new URLSearchParams(params);
    next.set("view", "analysis");
    next.set("record", evidenceId);
    return `?${next.toString()}`;
  };
  const head = headline(read);
  const limit = read.claim_limit;
  const current = read.currentness === "CURRENT";
  const earlier = !current && limit !== null ? limit.historical_ceiling : null;
  const earlierSentence = earlier === null ? null : ceilingSentence(earlier);
  const intervals = (current ? limit?.interval_ceilings : earlier?.interval_ceilings) ?? [];
  const seen = new Set<string>();
  const reasons = (limit?.reasons ?? [])
    .map(reasonSentence)
    .filter((s): s is string => s !== null && !seen.has(s) && (seen.add(s), true));
  const roles = read.capability?.roles ?? {};
  const roleKeys = read.capability?.required_roles ?? Object.keys(roles);
  const selected = read.assessment_revision_id;
  const whenText = selected === null ? `Day ${read.day}` : `${read.day}, ${read.scope === "WINDOW" ? "whole day" : assessedPeriod(read)}`;

  return (
    <div
      data-claim-limit-state="loaded"
      data-currentness={read.currentness}
      data-ceiling={current ? (limit?.ceiling ?? "") : ""}
      data-support={current ? (limit?.support ?? "") : ""}
      data-scope={read.scope ?? ""}
    >
      <p className="headline-card__question claim-limit__question">What can these readings support?</p>
      <p className="claim-limit__headline" data-claim-limit-headline>
        {head.text}
      </p>
      <div className="claim-limit__status">
        <ProductStatusLine read={read} whenText={whenText} />
      </div>
      <RoleStrip read={read} roleKeys={roleKeys} roles={roles} />
      {reasons.length === 0 ? null : (
        <>
          <h3 className="claim-limit__subheading">What limits it</h3>
          <ul data-claim-limit-reasons>
            {reasons.map((text) => (
              <li key={text}>{text}</li>
            ))}
          </ul>
        </>
      )}
      {read.currentness === "UNASSESSED" ? (
        <p>{`This day is ${DAY_STATUS_WORDS[read.window_status] ?? "in a state not known"}.`}</p>
      ) : null}
      {current && read.scope === "WINDOW" && limit !== null && limit.support !== null ? (
        <p data-claim-limit-window-level>{`Across the whole day: ${WINDOW_SUPPORT_WORDS[limit.support] ?? "no overall level stated"}.`}</p>
      ) : null}
      {earlierSentence === null ? null : (
        <p data-claim-limit-earlier>{`At the time, this version said: ${earlierSentence}`}</p>
      )}
      {intervals.length === 0 || current ? null : (
        <p data-claim-limit-earlier-periods>
          {read.scope === "WINDOW"
            ? "At the time, this version listed these assessed periods:"
            : "At the time, this version listed:"}
        </p>
      )}
      {intervals.length === 0 ? null : (
        <ul className="claim-limit__intervals" data-claim-limit-intervals={current ? "current" : "earlier"}>
          {intervals.map((item) => (
            <li key={item.assessment_revision_id}>
              <Link to={hrefFor(item.assessment_revision_id)} data-interval-ceiling={item.assessment_revision_id}>
                {`${periodLabel(item.assessment_revision_id, periods)}: ${item.ceiling === null ? "no conclusion" : (CLASS_WORDS[item.ceiling] ?? item.ceiling)}${item.support === "COMPLETE" ? ", fully covered" : item.support === "LIMITED" ? ", partly covered" : ""}`}
              </Link>
            </li>
          ))}
        </ul>
      )}
      {roleKeys.length === 0 || read.capability === null ? null : (
        <RoleTable roleKeys={roleKeys} roles={roles} recordHref={recordHref} />
      )}
      {selected === null || assessmentHref === undefined ? null : (
        <p>
          <Link to={assessmentHref(read.day, selected)} data-claim-limit-pinned={selected}>
            Open this assessment in Performance › Dispatch
          </Link>
        </p>
      )}
      <p className="claim-limit__note">
        This describes what the readings show, not the equipment's physical capacity; configured ratings are not
        treated as observed.
      </p>
      <Technical read={read} revision={revision} recordHref={recordHref} />
    </div>
  );
}

/**
 * W1-UX-03: the shared state line for the selected assessment - the plain
 * currentness words, the selected day and period, and "as of" the read.
 * Only CURRENT is positive; any other or unknown code says so plainly.
 */
function ProductStatusLine({ read, whenText }: { read: ClaimLimitRead; whenText: string }) {
  const words = currentnessWords(read.currentness);
  const limit = read.claim_limit;
  // Current, but with no positive conclusion (a whole day, an undetermined or unsupported period): limited, not positive.
  const supported =
    read.scope !== "WINDOW" && limit !== null && limit.current_positive_claim && limit.ceiling !== null && limit.ceiling !== "INDETERMINATE";
  return (
    <ProductStatus
      words={words.tone === "positive" && !supported ? { ...words, tone: "limited" } : words}
      scope={<span className="claim-limit__when">{whenText}</span>}
      asOf={read.read_at}
    />
  );
}

const SPAN_TONES: Record<string, StripTone> = {
  COVERED: "covered",
  MISSING: "gap",
  POOR_QUALITY: "problem",
  CONFLICTED: "problem",
};

/** The selected period's bounds from its role spans; the whole-day read uses its day window. */
function stripBounds(read: ClaimLimitRead): { start: string | null; end: string | null } {
  if (read.scope === "WINDOW") return { start: read.window.start, end: read.window.end };
  const spans = Object.values(read.capability?.roles ?? {}).flatMap((role) => role.spans);
  if (spans.length === 0) return { start: null, end: null };
  const starts = spans.map((s) => s.start).sort();
  const ends = spans.map((s) => s.end).sort();
  return { start: starts[0], end: ends[ends.length - 1] };
}

/**
 * Covered and missing time for each reading the conclusion needs, drawn on
 * the selected period. A needed reading with no spans is "not known", never
 * an empty bar; a span status this screen does not know is drawn as not known.
 */
function RoleStrip({
  read,
  roleKeys,
  roles,
}: {
  read: ClaimLimitRead;
  roleKeys: string[];
  roles: Record<string, RoleCapability>;
}) {
  if (roleKeys.length === 0 || read.capability === null) {
    return null;
  }
  const { start, end } = stripBounds(read);
  return (
    <PeriodStrip
      name="claim-limit-roles"
      title="Where each needed reading is covered or missing in the selected period"
      start={start}
      end={end}
      startText={start === null ? undefined : (plainTime(start) ?? undefined)}
      endText={end === null ? undefined : (plainTime(end) ?? undefined)}
      legend={[
        { tone: "covered", label: "Covered" },
        { tone: "gap", label: "Missing" },
        { tone: "problem", label: "Unreliable or conflicting" },
        { tone: "not-known", label: "Not checked or not known" },
      ]}
      rows={roleKeys.map((key) => {
        const role = roles[key];
        if (role === undefined || role.spans.length === 0) {
          return { key, label: roleName(key), segments: [], notKnown: true, summary: "No readings recorded: not known for this period." };
        }
        const { covered, total } = roleCoverage(role);
        const gaps = role.spans.filter((s) => s.status !== "COVERED");
        return {
          key,
          label: roleName(key),
          segments: role.spans.map((s, i) => ({
            key: `${i}`,
            start: s.start,
            end: s.end,
            tone: SPAN_TONES[s.status] ?? "not-known",
            label: `${SPAN_WORDS[s.status] ?? "not known"} ${period(s.start, s.end)}`,
          })),
          summary:
            total > 0
              ? `${mins(covered)} of ${mins(total)} covered${gaps.length === 0 ? "." : `; ${gaps.map((s) => `${SPAN_WORDS[s.status] ?? "not known"} ${period(s.start, s.end)}`).join("; ")}.`}`
              : "No readings recorded: not known for this period.",
        };
      })}
    />
  );
}

function RoleTable({
  roleKeys,
  roles,
  recordHref,
}: {
  roleKeys: string[];
  roles: Record<string, RoleCapability>;
  recordHref: (evidenceId: string) => string;
}) {
  return (
    <>
      <h3 className="claim-limit__subheading" id="claim-limit-roles-heading">
        Readings this conclusion needs
      </h3>
      <DataTable labelledBy="claim-limit-roles-heading">
        <thead>
          <tr>
            <th scope="col">Reading</th>
            <th scope="col">Covered</th>
            <th scope="col">Gaps</th>
            <th scope="col">Accepted readings</th>
          </tr>
        </thead>
        <tbody>
          {roleKeys.map((key) => {
            const role = roles[key];
            if (role === undefined) {
              return (
                <tr key={key} data-claim-role={key} data-role-status="NO_SPANS">
                  <th scope="row">{roleName(key)}</th>
                  <td>none</td>
                  <td>no readings</td>
                  <td>none</td>
                </tr>
              );
            }
            const { covered, total } = roleCoverage(role);
            const status = role.status ?? (total > 0 && covered >= total ? "COVERED" : covered > 0 ? "INCOMPLETE" : "NO_SPANS");
            const gaps = role.spans.filter((s) => s.status !== "COVERED");
            return (
              <tr key={key} data-claim-role={key} data-role-status={status}>
                <th scope="row">{roleName(key)}</th>
                <td>{total > 0 ? `${mins(covered)} of ${mins(total)}` : "no readings"}</td>
                <td>
                  {gaps.length === 0
                    ? "none"
                    : gaps.map((s) => `${SPAN_WORDS[s.status] ?? "not known"} ${period(s.start, s.end)}`).join("; ")}
                </td>
                <td>
                  {role.evidence_ids.length === 0 ? (
                    "none"
                  ) : (
                    <Disclosure name={`claim-limit-records-${key}`} summary={`${role.evidence_ids.length} readings`}>
                      <ul className="claim-limit__records">
                        {role.evidence_ids.map((id, index) => (
                          <li key={id}>
                            <Link to={recordHref(id)} data-claim-record={id} aria-label={`Open accepted reading ${index + 1} for ${roleName(key)}`}>
                              {`Reading ${index + 1}`}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </Disclosure>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </DataTable>
    </>
  );
}

function list(values: readonly string[] | undefined): ReactNode {
  return values === undefined || values.length === 0 ? "none" : values.join(", ");
}

/**
 * Fix round 1 (F4): server sentences are prose, not single exact values, so the
 * technical disclosure no longer shows them under the single-value exemption.
 * The rule statement and each reason's text are already said in plain words in
 * the default reading (headline and "What limits it"); the reason codes stay as
 * labelled exact values. The one recorded "not inferred" sentence is restated in
 * plain, scanned words; any other wording is named as not shown, never echoed.
 */
const NOT_INFERRED_RECORDED =
  "No physical capacity is inferred: configured capability (Foundation or binding values) is not observed capability, and only the selected revision's accepted public readings are used.";
const NOT_INFERRED_WORDS =
  "Nothing about physical capacity is inferred. Capacity from the site set-up is not treated as measured, and only the accepted readings of the selected version are used.";
const NOT_INFERRED_UNRECOGNISED = "The record also states what is not inferred; that wording is not shown here.";

function Technical({
  read,
  revision,
  recordHref,
}: {
  read: ClaimLimitRead;
  revision: string | null;
  recordHref: (evidenceId: string) => string;
}) {
  const limit = read.claim_limit;
  const source = read.watermarks?.source;
  return (
    <div className="evidence-advanced">
      <Disclosure name="claim-limit-technical" summary="Technical details: rule, versions and record references">
        <FactList>
          <Fact term="Rule"><code {...REF}>{read.rule_id}</code></Fact>
          <Fact term="Assessment state code"><code {...REF}>{read.currentness}</code></Fact>
          <Fact term="Strongest supported classification code"><code {...REF}>{limit?.ceiling ?? "none"}</code></Fact>
          <Fact term="Coverage level code"><code {...REF}>{limit?.support ?? "none"}</code></Fact>
          <Fact term="Supported minutes"><code {...REF}>{limit?.supported_minutes ?? "none"}</code></Fact>
          {limit?.historical_ceiling ? (
            <Fact term="Earlier classification and coverage codes (for the record)">
              <code {...REF}>{`${limit.historical_ceiling.ceiling ?? "none"} · ${limit.historical_ceiling.support ?? "none"}`}</code>
            </Fact>
          ) : null}
          <Fact term="Requested revision"><code {...REF}>{revision ?? "none"}</code></Fact>
          <Fact term="Assessment revision"><code {...REF}>{read.assessment_revision_id ?? "none"}</code></Fact>
          <Fact term="Revision number"><code {...REF}>{read.revision_no ?? "none"}</code></Fact>
          <Fact term="Scope"><code {...REF}>{read.scope ?? "none"}</code></Fact>
          <Fact term="Assessment key"><code {...REF}>{read.assessment_key ?? "none"}</code></Fact>
          <Fact term="Conclusion level code"><code {...REF}>{read.claim_level ?? "none"}</code></Fact>
          <Fact term="Day window"><code {...REF}>{`${read.window.start} to ${read.window.end}`}</code></Fact>
          <Fact term="Day state code"><code {...REF}>{`${read.window_status}${read.window_status_reasons.length ? ` (${read.window_status_reasons.join("; ")})` : ""}`}</code></Fact>
          <Fact term="Current assessment batch, rules and versions">
            <code {...REF}>
              {read.current_selection === null
                ? "none"
                : `${read.current_selection.run_id} · ${read.current_selection.model_version} · ${read.current_selection.revision_ids.join(", ")}`}
            </code>
          </Fact>
          <Fact term="Assessment batch and method"><code {...REF}>{read.run ? `${read.run.run_id} · ${read.run.model_version}` : "none"}</code></Fact>
          <Fact term="Device set state and reference"><code {...REF}>{read.run ? `${read.run.cohort_status} · ${read.run.cohort_sha256}` : "none"}</code></Fact>
          <Fact term="Knowledge cutoff"><code {...REF}>{read.run?.knowledge_cutoff ?? "none"}</code></Fact>
          <Fact term="Foundation revisions"><code {...REF}>{list(read.run?.foundation_revision_ids)}</code></Fact>
          <Fact term="Input set-up revisions"><code {...REF}>{list(read.run?.binding_set_revision_ids)}</code></Fact>
          <Fact term="Latest reading used (taken)"><code {...REF}>{source?.source_time ?? "none"}</code></Fact>
          <Fact term="Latest reading used (sent)"><code {...REF}>{source?.published_at ?? "none"}</code></Fact>
          <Fact term="Latest reading used (received)"><code {...REF}>{source?.received_at ?? "none"}</code></Fact>
          <Fact term="Latest reading used (accepted)"><code {...REF}>{source?.accepted_at ?? "none"}</code></Fact>
          <Fact term="Analysis prepared"><code {...REF}>{read.watermarks?.analytic_built_at ?? "none"}</code></Fact>
          <Fact term="Assessment prepared"><code {...REF}>{read.built_at ?? "none"}</code></Fact>
          <Fact term="Read at"><code {...REF}>{read.read_at}</code></Fact>
          <Fact term="What is not inferred">
            <span data-claim-limit-not-inferred={read.not_inferred === NOT_INFERRED_RECORDED ? "known" : "unrecognised"}>
              {read.not_inferred === NOT_INFERRED_RECORDED ? NOT_INFERRED_WORDS : NOT_INFERRED_UNRECOGNISED}
            </span>
          </Fact>
        </FactList>
        {limit === null || limit.reasons.length === 0 ? null : (
          <ul data-claim-limit-reason-codes>
            {limit.reasons.map((r, index) => (
              <li key={`${r.code}-${index}`} data-reason-code={r.code}>
                Reason code <code {...REF}>{r.code}</code>
              </li>
            ))}
          </ul>
        )}
        {read.accepted_evidence_ids === undefined || read.accepted_evidence_ids.length === 0 ? null : (
          <>
            <p>{`Accepted reading references (${read.accepted_evidence_ids.length})`}</p>
            <ul className="claim-limit__records" data-claim-limit-accepted>
              {read.accepted_evidence_ids.map((id) => (
                <li key={id}>
                  <Link to={recordHref(id)} data-accepted-evidence={id}>
                    <code {...REF}>{id}</code>
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </Disclosure>
    </div>
  );
}
