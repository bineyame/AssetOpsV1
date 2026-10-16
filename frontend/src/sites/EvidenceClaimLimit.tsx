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
 * panel "How a claim limit is set": which readings the conclusion needs, where
 * they are missing or unreliable, and the accepted readings behind each one.
 * Rule, status codes, versions, watermarks and IDs sit behind one closed
 * "Technical details" disclosure.
 */

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Badge, DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import { isDay } from "./dispatchWords";
import type {
  AssessedDay,
  CeilingBody,
  ClaimLimitClient,
  ClaimLimitRead,
  ClaimLimitResult,
  ClaimReason,
  RoleCapability,
} from "./claimLimitClient";

export const CLAIM_LIMIT_HEADING_ID = "site-evidence-selected-claim-limit-heading";
export const CLAIM_LIMIT_LOADING = "Loading the selected assessment's limit.";
export const ASSESSED_DAY_LOADING = "Loading the day's assessed periods.";

const ROLE_WORDS: Record<string, string> = {
  generator_state: "Generator on or off",
  feeder_demand: "Site demand",
  pv_available_power: "Solar power available",
  pcs_discharge_capability: "Battery discharge capability",
  battery_soc: "Battery charge level",
};

const SPAN_WORDS: Record<string, string> = {
  COVERED: "covered",
  MISSING: "missing",
  POOR_QUALITY: "unreliable readings",
  CONFLICTED: "conflicting reports",
  NOT_EVALUATED: "not checked",
};

const CURRENTNESS_WORDS: Record<string, string> = {
  CURRENT: "Current assessment",
  HISTORICAL: "Earlier version · audit only",
  STALE_PROJECTION: "Out of date · being redone",
  PENDING: "Assessment pending",
  FAILED: "Assessment failed",
  UNASSESSED: "No assessment selected",
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
    return "The readings cannot support a conclusion about this generator run: a reading it needs is missing or unreliable.";
  }
  const word = CLASS_WORDS[body.ceiling] ?? body.ceiling;
  const minutes = body.supported_minutes === null ? "" : ` for ${mins(body.supported_minutes)}`;
  return body.support === "COMPLETE"
    ? `The readings support calling this generator run ${word}${minutes}. Every reading it needs is present for that time.`
    : `The readings support calling this generator run ${word} for at most${minutes.replace(" for", "")}; the rest of the period is limited by the gaps below.`;
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
      return "The end of the run is not yet known, so its length is a lower bound.";
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
    <Panel heading="What the selected assessment can support" headingId={CLAIM_LIMIT_HEADING_ID}>
      <div className="claim-limit" data-claim-limit-section data-claim-limit-day={day ?? ""} data-claim-limit-revision={revision ?? ""}>
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
          hrefFor={select}
          assessmentHref={assessmentHref}
        />
      </div>
    </Panel>
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
      <p className="claim-limit__periods-label">{`Assessed periods (the day is ${DAY_STATUS_WORDS[assessed.value.status] ?? assessed.value.status}):`}</p>
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
  hrefFor,
  assessmentHref,
}: {
  siteId: string;
  client: ClaimLimitClient | undefined;
  day: string | null;
  revision: string | null;
  read: ClaimLimitResult<ClaimLimitRead> | null;
  hrefFor: (revisionId: string | null) => string;
  assessmentHref?: (day: string, revisionId: string) => string;
}) {
  if (day === null) {
    return (
      <div data-claim-limit-state="no-day" data-currentness="UNASSESSED">
        <p className="claim-limit__status">
          <Badge tone="neutral">No assessment selected</Badge>
        </p>
        <p>Choose a day, then one of its assessed periods. Nothing is concluded until an assessment is chosen.</p>
      </div>
    );
  }
  if (client === undefined) {
    return (
      <p data-claim-limit-state="unavailable">
        The assessment store could not be read, so nothing is shown about a selected assessment.
      </p>
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
        <p className="claim-limit__status">
          <Badge tone="neutral">Not shown</Badge>
        </p>
        <p>{refusalSentence(read)}</p>
        {"message" in read && read.message !== null ? (
          <Disclosure name="claim-limit-refusal-technical" summary="Technical details">
            <p>{`${"code" in read && read.code !== null ? `${read.code}: ` : ""}${read.message}`}</p>
          </Disclosure>
        ) : null}
      </div>
    );
  }
  return <Loaded siteId={siteId} read={read.value} revision={revision} hrefFor={hrefFor} assessmentHref={assessmentHref} />;
}

function Loaded({
  read,
  revision,
  hrefFor,
  assessmentHref,
}: {
  siteId: string;
  read: ClaimLimitRead;
  revision: string | null;
  hrefFor: (revisionId: string | null) => string;
  assessmentHref?: (day: string, revisionId: string) => string;
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

  return (
    <div
      data-claim-limit-state="loaded"
      data-currentness={read.currentness}
      data-ceiling={current ? (limit?.ceiling ?? "") : ""}
      data-support={current ? (limit?.support ?? "") : ""}
      data-scope={read.scope ?? ""}
    >
      <p className="claim-limit__status">
        <Badge tone={head.tone === "lifecycle" ? "lifecycle" : "neutral"}>
          {CURRENTNESS_WORDS[read.currentness] ?? read.currentness}
        </Badge>{" "}
        <span className="claim-limit__when">
          {selected === null ? `Day ${read.day}` : `${read.day}, ${read.scope === "WINDOW" ? "whole day" : assessedPeriod(read)}`}
        </span>
      </p>
      <p className="claim-limit__headline" data-claim-limit-headline>
        {head.text}
      </p>
      {read.currentness === "UNASSESSED" ? (
        <p>{`This day is ${DAY_STATUS_WORDS[read.window_status] ?? read.window_status}.`}</p>
      ) : null}
      {earlierSentence === null ? null : (
        <p data-claim-limit-earlier>{`At the time, this version said: ${earlierSentence}`}</p>
      )}
      {intervals.length === 0 ? null : (
        <ul className="claim-limit__intervals" data-claim-limit-intervals={current ? "current" : "earlier"}>
          {intervals.map((item) => (
            <li key={item.assessment_revision_id}>
              <Link to={hrefFor(item.assessment_revision_id)} data-interval-ceiling={item.assessment_revision_id}>
                {`An assessed period: ${item.ceiling === null ? "no conclusion" : (CLASS_WORDS[item.ceiling] ?? item.ceiling)}${item.support === "COMPLETE" ? ", fully covered" : item.support === "LIMITED" ? ", partly covered" : ""}`}
              </Link>
            </li>
          ))}
        </ul>
      )}
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
            const total = Object.values(role.minutes_by_status).reduce<number>((sum, v) => sum + asNumber(v), 0);
            const gaps = role.spans.filter((s) => s.status !== "COVERED");
            return (
              <tr key={key} data-claim-role={key} data-role-status={role.status}>
                <th scope="row">{roleName(key)}</th>
                <td>{total > 0 ? `${mins(role.covered_minutes)} of ${mins(total)}` : mins(role.covered_minutes)}</td>
                <td>
                  {gaps.length === 0
                    ? "none"
                    : gaps.map((s) => `${SPAN_WORDS[s.status] ?? s.status} ${period(s.start, s.end)}`).join("; ")}
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
      <Disclosure name="claim-limit-technical" summary="Technical details — rule, versions and record IDs">
        <FactList>
          <Fact term="Rule">{read.rule_id}</Fact>
          <Fact term="Status code">{read.currentness}</Fact>
          <Fact term="Classification ceiling">{limit?.ceiling ?? "none"}</Fact>
          <Fact term="Support">{limit?.support ?? "none"}</Fact>
          <Fact term="Supported minutes">{limit?.supported_minutes ?? "none"}</Fact>
          <Fact term="Rule statement">{limit?.statement ?? limit?.historical_ceiling?.statement ?? "none"}</Fact>
          {limit?.historical_ceiling ? (
            <Fact term="Earlier ceiling (audit only)">
              {`${limit.historical_ceiling.ceiling ?? "none"} · ${limit.historical_ceiling.support ?? "none"}`}
            </Fact>
          ) : null}
          <Fact term="Requested revision">{revision ?? "none"}</Fact>
          <Fact term="Assessment revision">{read.assessment_revision_id ?? "none"}</Fact>
          <Fact term="Revision number">{read.revision_no ?? "none"}</Fact>
          <Fact term="Scope">{read.scope ?? "none"}</Fact>
          <Fact term="Assessment key">{read.assessment_key ?? "none"}</Fact>
          <Fact term="Claim level">{read.claim_level ?? "none"}</Fact>
          <Fact term="Day window">{`${read.window.start} to ${read.window.end}`}</Fact>
          <Fact term="Day status">{`${read.window_status}${read.window_status_reasons.length ? ` (${read.window_status_reasons.join("; ")})` : ""}`}</Fact>
          <Fact term="Current selection">
            {read.current_selection === null
              ? "none"
              : `run ${read.current_selection.run_id} · ${read.current_selection.model_version} · revisions ${read.current_selection.revision_ids.join(", ")}`}
          </Fact>
          <Fact term="Run">{read.run ? `${read.run.run_id} · ${read.run.model_version}` : "none"}</Fact>
          <Fact term="Cohort">{read.run ? `${read.run.cohort_status} · ${read.run.cohort_sha256}` : "none"}</Fact>
          <Fact term="Knowledge cutoff">{read.run?.knowledge_cutoff ?? "none"}</Fact>
          <Fact term="Foundation revisions">{list(read.run?.foundation_revision_ids)}</Fact>
          <Fact term="Binding-set revisions">{list(read.run?.binding_set_revision_ids)}</Fact>
          <Fact term="Source watermark (reading time)">{source?.source_time ?? "none"}</Fact>
          <Fact term="Source watermark (published)">{source?.published_at ?? "none"}</Fact>
          <Fact term="Source watermark (received)">{source?.received_at ?? "none"}</Fact>
          <Fact term="Source watermark (accepted)">{source?.accepted_at ?? "none"}</Fact>
          <Fact term="Analysis built">{read.watermarks?.analytic_built_at ?? "none"}</Fact>
          <Fact term="Assessment built">{read.built_at ?? "none"}</Fact>
          <Fact term="Read at">{read.read_at}</Fact>
          <Fact term="Not inferred">{read.not_inferred}</Fact>
        </FactList>
        {limit === null || limit.reasons.length === 0 ? null : (
          <ul data-claim-limit-reason-codes>
            {limit.reasons.map((r, index) => (
              <li key={`${r.code}-${index}`} data-reason-code={r.code}>{`${r.code}: ${r.text}`}</li>
            ))}
          </ul>
        )}
        {read.accepted_evidence_ids === undefined || read.accepted_evidence_ids.length === 0 ? null : (
          <>
            <p>{`Accepted Evidence IDs (${read.accepted_evidence_ids.length})`}</p>
            <ul className="claim-limit__records" data-claim-limit-accepted>
              {read.accepted_evidence_ids.map((id) => (
                <li key={id}>
                  <Link to={recordHref(id)} data-accepted-evidence={id}>
                    {id}
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
