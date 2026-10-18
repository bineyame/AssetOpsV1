import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  Badge,
  BigClaim,
  Breadcrumbs,
  type Crumb,
  CausalTimeline,
  ChartNote,
  DataTable,
  ExactReferences,
  KeyValues,
  MetricCard,
  MetricCards,
  Notice,
  PageHeader,
  Panel,
  SITE_SCREEN_DESCRIPTIONS,
  SitePageHeader,
  StatusBar,
  type TimelineEvent,
} from "../ui";
import {
  type ColdAssessmentClient,
  type ColdBackupRead,
  type ColdChainRead,
  type ColdFindingDetailRead,
  type ColdFindingsRead,
  type ColdRead,
  type ColdStepRead,
  type ColdTemperatureRead,
  type ColdWindowQuery,
  coldWindowSearch,
} from "./coldAssessmentClient";
import {
  STEP_ESTABLISHES,
  claimWord,
  classificationWord,
  SIMULATION_SOURCE_SENTENCE,
  currentnessWord,
  lifecycleWord,
  plainCode,
  plainLimitation,
  reasonWord,
  startResultWord,
  stepLabel,
  stepStateWord,
  temperatureStateWord,
  transitionWord,
} from "./coldAssessmentWords";
import { ColdTemperatureChart } from "./assessmentGraphics";
import { NOT_ASSESSED, NOT_RECORDED, between, date, dayHm, decimal, deg, hm, num, range, windowText } from "./coldFormat";
import { UnavailableTab } from "../ui/UnavailableEntry";
import "./w2-cold-assessment.css";

/*
 * W2-03 commit 5: the four cold assessment screens of a COLDCHAIN Site in their exact v69 panel slots
 * (`.agent/W2-03-build-spec.md` "Commit 5 - exact v69 slots"; `D-2026-10-17-mockup-layout-spec`):
 *
 *   temperature             1 Temperature with operating context, 2 Excursion context, 3 How each limit is set (mock: Claim boundary)
 *   coldbackup              1 What the chain shows, 2 Reconstructed event chain, 3 Backup event chains,
 *                           4 Evidence by causal step
 *   cold-finding            1 Bounded conclusion, 2 Operational context, 3 Recommended next step
 *   cold-finding-excursion  1 Bounded conclusion, 2 Temperature, 3 Recommended next step
 *
 * Every value comes from the selected cold reads; a slot the read cannot fill keeps its panel and names the gap.
 * No spoilage, product-loss, failed-part or Incident claim is made, and no mock value is a default.
 */

export const COLD_ASSESSMENT_LOADING = "Loading the site's cold assessment.";
export const COLD_FINDING_LOADING = "Loading the Finding.";
export const COLD_PERFORMANCE_HEADING_ID = "cold-performance-heading";
export const COLD_FINDING_HEADING_ID = "cold-finding-heading";
export const NO_RECORDED_NEXT_STEP = "No recorded next step";
export { NOT_ASSESSED, NOT_RECORDED } from "./coldFormat";

export type ColdPerformanceView = "temperature" | "backup";

export interface ColdLinks {
  temperature: string;
  backup: string;
  finding: (findingId: string) => string;
  record: (evidenceId: string) => string;
  analysis: (assessmentRevisionId: string) => string;
}

const unique = (items: string[]) => Array.from(new Set(items));

/* ---------- reads ---------- */

function useRead<T>(load: (() => Promise<ColdRead<T>>) | null, key: string): ColdRead<T> | null {
  const [state, setState] = useState<{ key: string; value: ColdRead<T> } | null>(null);
  useEffect(() => {
    if (load === null) return undefined;
    let active = true;
    void load().then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
    // `load` is rebuilt every render; the key names what it reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, load === null]);
  return state !== null && state.key === key ? state.value : null;
}

const loaded = <T,>(read: ColdRead<T> | null): T | null => (read !== null && read.status === "loaded" ? read.value : null);

function windowKey(window: ColdWindowQuery): string {
  return `${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}`;
}

/* ---------- shared pieces ---------- */

function Gap({ id, children }: { id: string; children: ReactNode }) {
  return (
    <p className="not-available-yet v69-chart-note" data-panel-gap={id}>
      {children}
    </p>
  );
}

function refusalText(read: Exclude<ColdRead<unknown>, { status: "loaded" }>): { key: string; title: string; body: string } {
  if (read.status === "refused" && read.httpStatus === 403) {
    return {
      key: "forbidden",
      title: "Source permission refused",
      body: "This site's source records may not be shown to you, so no assessment is shown.",
    };
  }
  if (read.status === "refused" && read.httpStatus === 404) {
    return { key: "not-found", title: "Not found", body: "No cold-chain record with this address is stored for this site." };
  }
  if (read.status === "refused" && read.httpStatus === 422) {
    return { key: "invalid-window", title: "Window cannot be read", body: "The selected window is not a valid UTC window of at most 31 days." };
  }
  if (read.status === "refused" && read.httpStatus === 401) {
    return { key: "unauthenticated", title: "Sign in required", body: "Sign in to read this site's cold-chain assessment." };
  }
  return { key: "unavailable", title: "Assessment unavailable", body: "The cold-chain assessment could not be read. Nothing is shown as assessed until it can be." };
}

function PageRefusal({ read, window }: { read: Exclude<ColdRead<unknown>, { status: "loaded" }>; window: ColdWindowQuery }) {
  const text = refusalText(read);
  return (
    <div className="page-refusal" role="status" data-page-refusal={text.key}>
      <p className="page-refusal__title">
        <strong>{text.title}</strong>
      </p>
      <p>{text.body}</p>
      <ExactReferences
        name="cold-refusal-references"
        variant="tech"
        references={[
          { label: "Refusal code", value: read.status === "refused" ? read.code : null },
          { label: "Server message", value: read.message },
          { label: "Selected window start (exact)", value: window.from },
          { label: "Selected window end (exact)", value: window.to },
        ]}
      />
    </div>
  );
}

/** One line: the Finding's exact accepted records as numbered links, then its assessment (Analysis) link. */
function EvidenceLine({ finding, links }: { finding: ColdFindingDetailRead; links: ColdLinks }) {
  return (
    <p className="v69-chart-note cold-evidence-line" data-evidence-links={finding.evidence_ids.length}>
      {finding.evidence_ids.length === 0 ? "No accepted record is linked" : "Accepted records:"}
      {finding.evidence_ids.map((id, index) => (
        <Link key={id} to={links.record(id)} data-evidence-link={id} aria-label={`Accepted record ${index + 1}`}>
          {index + 1}
        </Link>
      ))}
      <span aria-hidden="true">·</span>
      <Link to={links.analysis(finding.assessment_revision_id)} data-analysis-link={finding.assessment_revision_id}>
        Open the assessment →
      </Link>
    </p>
  );
}

function gapNotes(read: ColdTemperatureRead): ReactNode {
  if (read.gaps.length === 0) return null;
  return (
    <ChartNote data={{ "data-cold-gaps": String(read.gaps.length) }}>
      {read.gaps.map((gap, i) => (
        <span key={`${gap.start}-${gap.end}`} data-cold-gap={gap.start ?? ""}>
          {i > 0 ? " · " : ""}
          {`No usable reading ${hm(gap.start)}–${hm(gap.end)} (${reasonWord(gap.reason).toLowerCase()}`}
          {gap.expected_points !== null ? `, ${gap.received_points ?? 0} of ${gap.expected_points} expected` : ""})
        </span>
      ))}
    </ChartNote>
  );
}

/* ---------- temperature ---------- */

function cadenceMinutes(read: ColdTemperatureRead): number | null {
  const a = date(read.window.from);
  const b = date(read.window.to);
  const n = read.coverage.expected_points;
  if (a === null || b === null || n === null || n === 0) return null;
  return Math.round((b.getTime() - a.getTime()) / 60000 / n);
}

function peakPoint(read: ColdTemperatureRead, peak: string | null): string | null {
  const target = num(peak);
  if (target === null) return null;
  const match = read.points.find((p) => num(p.value) === target);
  return match === undefined ? null : match.at;
}

function limitOf(read: ColdTemperatureRead, direction: string | undefined): { word: string; value: string | null } {
  return direction === "LOW"
    ? { word: "below", value: read.policy?.low_deg_c ?? null }
    : { word: "above", value: read.policy?.high_deg_c ?? null };
}

function grid(backup: ColdBackupRead | null): ColdStepRead | null {
  const chain = backup?.chains[0];
  return chain?.steps.find((s) => s.kind === "GRID" && s.state === "OBSERVED") ?? null;
}

function findingFor(findings: ColdFindingsRead | null, episodeId: string | null, kind: string) {
  if (findings === null) return null;
  return findings.items.find((f) => f.kind === kind && (episodeId === null || f.claim.episode_id === episodeId)) ?? null;
}

function TemperatureStatus({ read }: { read: ColdTemperatureRead | null }) {
  if (read === null) return null;
  const cadence = cadenceMinutes(read);
  const policy = read.policy;
  const known = read.coverage.known_points;
  const expected = read.coverage.expected_points;
  return (
    <StatusBar label="Temperature state">
      <Badge tone="neutral">{temperatureStateWord(read.state)}</Badge>{" "}
      <Badge tone="neutral">{known === null ? "Coverage not assessed" : `Coverage: ${known} / ${expected} readings`}</Badge>{" "}
      {[
        policy === null ? "Policy not recorded" : `Policy ${decimal(policy.low_deg_c) ?? "?"}–${decimal(policy.high_deg_c) ?? "?"} °C`,
        policy?.probe_asset_id ? "one chamber probe" : "no chamber probe selected",
        cadence === null ? null : `readings every ${cadence} min`,
        windowText(read.window.from, read.window.to),
        currentnessWord(read.currentness.state),
      ]
        .filter(Boolean)
        .join(" · ")}
    </StatusBar>
  );
}

function TemperatureCards({ read }: { read: ColdTemperatureRead }) {
  const x = read.excursions[0];
  const limit = limitOf(read, x?.direction);
  const none = read.state === "NO_EXCURSION_OBSERVED" ? "None observed" : NOT_ASSESSED;
  const peak = x === undefined ? null : num(x.peak_observed);
  const lim = num(limit.value);
  return (
    <MetricCards label="Temperature exposure">
      <MetricCard
        label={`Time ${limit.word} ${limit.value === null ? "policy" : `${decimal(limit.value)}°C`}`}
        value={x === undefined ? none : range(x.duration_bounds.low, x.duration_bounds.high, "min")}
        note={x === undefined ? "No confirmed excursion in this window" : x.open ? "Still outside policy at the window end" : "Between the last in-policy and first out-of-policy readings"}
        word={x === undefined || x.duration_bounds.low === null}
        data={{ "data-cold-card": "duration" }}
      />
      <MetricCard
        label="Peak"
        value={x === undefined ? none : deg(x.peak_observed)}
        note={peak !== null && lim !== null ? `${decimal(Math.abs(peak - lim))} °C ${limit.word} the ${decimal(lim)} °C limit` : "Highest observed reading, never interpolated"}
        word={x === undefined}
        data={{ "data-cold-card": "peak" }}
      />
      <MetricCard
        label="Exposure size"
        value={x === undefined ? none : range(x.degree_minute_bounds.low, x.degree_minute_bounds.high, "°C·min")}
        note="Area beyond the limit, bounded by the readings"
        word={x === undefined}
        data={{ "data-cold-card": "exposure" }}
      />
      <MetricCard label="Product outcome" value="Not determined" note="Temperature exposure is not spoilage" word data={{ "data-cold-card": "product" }} />
    </MetricCards>
  );
}

function temperatureTimeline(read: ColdTemperatureRead, backup: ColdBackupRead | null): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  const lost = grid(backup);
  if (lost !== null) events.push({ key: "grid", time: hm(lost.at), title: "Power lost", detail: "Grid supply record", tone: "danger" });
  const compressor = coolingRunning(backup?.chains[0]);
  if (compressor) events.push({ key: "cooling", time: hm(compressor.at), title: "Cooling running", detail: "Compressor record" });
  const x = read.excursions[0];
  if (x !== undefined) {
    const limit = limitOf(read, x.direction);
    events.push({ key: "start", time: between(x.start_bounds.earliest, x.start_bounds.latest), title: `Went ${limit.word} ${deg(limit.value)}`, detail: "Chamber probe", tone: "danger" });
    const at = peakPoint(read, x.peak_observed);
    events.push({ key: "peak", time: at === null ? "—" : hm(at), title: "Peak observed", detail: deg(x.peak_observed), tone: "danger" });
    events.push(
      x.open || x.end_bounds.latest === null
        ? { key: "end", time: hm(read.window.to), title: "Still outside policy", detail: "At the window end", tone: "gap" }
        : { key: "end", time: between(x.end_bounds.earliest, x.end_bounds.latest), title: "Back within policy", detail: "Chamber probe" },
    );
  }
  return events.sort((a, b) => String(a.time).localeCompare(String(b.time)));
}

function TemperaturePanels({
  read,
  backup,
  findings,
  links,
  gap,
}: {
  read: ColdTemperatureRead | null;
  backup: ColdBackupRead | null;
  findings: ColdFindingsRead | null;
  links: ColdLinks;
  gap: string | null;
}) {
  const x = read?.excursions[0];
  const finding = x === undefined ? null : findingFor(findings, x.episode_id, "EXCURSION");
  const limit = read === null ? { word: "above", value: null } : limitOf(read, x?.direction);
  const lost = grid(backup);
  const door = (read?.excluded ?? []).filter((e) => e.reason === "DOOR_EVENT");
  const timeline = read === null ? [] : temperatureTimeline(read, backup);
  const excluded = (read?.excluded ?? []).filter((e) => e.reason !== "DOOR_EVENT");
  return (
    <>
      <div className="panel-pair">
        <Panel heading="Temperature with operating context" headingId="cold-temperature-chart-heading">
          {read === null ? (
            <Gap id="cold-temperature-chart-heading">{gap}</Gap>
          ) : (
            <>
              <ColdTemperatureChart read={read} label={`Chamber temperature, ${windowText(read.window.from, read.window.to)}, with the policy band`} />
              {gapNotes(read)}
              {timeline.length > 0 ? <CausalTimeline events={timeline} label="Operating context" /> : null}
            </>
          )}
        </Panel>
        <Panel heading="Excursion context" headingId="cold-excursion-heading">
          {read === null ? (
            <Gap id="cold-excursion-heading">{gap}</Gap>
          ) : (
            <>
              <KeyValues
                label="Excursion context"
                rows={[
                  [
                    "Excursion window",
                    x === undefined
                      ? read.state === "NO_EXCURSION_OBSERVED"
                        ? "No excursion observed"
                        : NOT_ASSESSED
                      : `Began ${between(x.start_bounds.earliest, x.start_bounds.latest)} · ${
                          x.open || x.end_bounds.latest === null ? `still outside policy at ${hm(read.window.to)}` : `ended ${between(x.end_bounds.earliest, x.end_bounds.latest)}`
                        }`,
                    "window",
                  ],
                  [`${limit.word === "below" ? "Lower" : "Upper"} policy limit`, deg(limit.value), "limit"],
                  [
                    "Peak observed",
                    x === undefined ? NOT_ASSESSED : `${deg(x.peak_observed)}${peakPoint(read, x.peak_observed) ? ` at ${hm(peakPoint(read, x.peak_observed))}` : ""}`,
                    "peak",
                  ],
                  [
                    "Power outage",
                    lost === null ? (
                      backup === null ? NOT_ASSESSED : "No grid loss recorded"
                    ) : (
                      <>
                        Observed {hm(lost.at)} · <Link to={links.backup}>backup chain →</Link>
                      </>
                    ),
                    "outage",
                  ],
                  ["Door opening", door.length === 0 ? "No record" : `Door record ${door.map((d) => hm(d.as_of)).join(", ")} · context only`, "door"],
                  // The capture tool treats any "Loading" text as a page still loading (W2-01 deviation 6 precedent).
                  ["Stock loading / batch", NOT_RECORDED, "loading"],
                  ["Defrost", NOT_RECORDED, "defrost"],
                ]}
              />
              {x === undefined ? null : finding !== null ? (
                <p className="cold-panel-link">
                  <Link to={links.finding(finding.finding_id)} data-finding-link={finding.finding_id}>
                    Open the Finding →
                  </Link>
                </p>
              ) : (
                <Gap id="cold-excursion-finding">No Finding is recorded for this excursion.</Gap>
              )}
              <ExactReferences
                name="cold-excursion-references"
                references={[
                  { label: "Episode", value: x?.episode_id ?? null },
                  { label: "Episode version", value: x?.revision_id ?? null },
                  { label: "Cold room", value: read.policy?.room_asset_id ?? null },
                  { label: "Chamber probe", value: read.policy?.probe_asset_id ?? null },
                ]}
              />
            </>
          )}
        </Panel>
      </div>
      <Notice>
        Durations are bounded by the reading spacing. Exposure size is bounded the same way (lowest and highest reading in each step); it does not
        describe what happened to the product.
      </Notice>
      <Panel heading="How each limit is set" headingId="cold-claim-boundary-heading">
        {read === null ? (
          <Gap id="cold-claim-boundary-heading">{gap}</Gap>
        ) : (
          <>
            <p className="prose">
              {x !== undefined
                ? `The accepted probe readings support a ${claimWord(x.claim_level).toLowerCase()} temperature excursion ${limit.word} policy. Product quality or spoilage conclusions need product identity, an exposure policy and further evidence.`
                : read.state === "NO_EXCURSION_OBSERVED"
                  ? "The accepted probe readings stay within policy for this window. This says nothing about product condition."
                  : "The accepted probe readings do not support a temperature conclusion for this window."}
            </p>
            <p className="v69-chart-note" data-cold-claim-facts>
              {[
                read.coverage.known_points === null
                  ? "No usable-reading count is selected"
                  : `${read.coverage.known_points} of ${read.coverage.expected_points} expected readings usable (${Math.round((num(read.coverage.ratio) ?? 0) * 100)}%)`,
                excluded.length === 0 ? "no records set aside" : `set aside: ${excluded.map((e) => reasonWord(e.reason).toLowerCase()).join(", ")}`,
              ].join(" · ")}
              {" · source: "}
              <span data-cold-source>{classificationWord(read.source_provenance.classification)}</span>
              {read.source_provenance.classification === "REGISTERED_SIMULATION" ? <> <span data-cold-source-sentence>{SIMULATION_SOURCE_SENTENCE}</span></> : null}
            </p>
            <ul className="cold-limits" data-cold-limitations>
              {unique(read.limitations).map((text) => (
                <li key={text}>{plainLimitation(text)}</li>
              ))}
            </ul>
            <ExactReferences
              name="cold-claim-references"
              references={[
                { label: "Source classification", value: read.source_provenance.classification },
                { label: "Source IDs", value: read.source_provenance.source_ids.join(", ") || null },
                { label: "Assessment versions", value: read.currentness.watermark.assessment_revision_ids.join(", ") || null },
                { label: "Assessment basis", value: read.source_provenance.basis_sha256 },
                { label: "Evidence time", value: read.window.known_at },
                { label: "Records not used", value: excluded.map((e) => e.evidence_id).join(", ") || null },
              ]}
            />
          </>
        )}
      </Panel>
    </>
  );
}

/* ---------- backup chain ---------- */

/** The step's observed outcome in words; a probe step's outcome is its temperature. */
function outcomeText(s: ColdStepRead): string | null {
  if (s.outcome === null) return null;
  return s.kind === "PROBE" ? deg(s.outcome) : plainCode(s.outcome);
}

const ADVERSE = /FAIL|LOSS|LOST|^OFF$|UNPOWERED|STOPPED/;
const RUNNING = /^(RUNNING|ON|POWERED|STARTED)$/;

/** The compressor step only when it shows cooling running (an observed OFF is not "cooling resumed"). */
function coolingRunning(chain: ColdChainRead | undefined): ColdStepRead | undefined {
  const s = chain?.steps.find((x) => x.kind === "COMPRESSOR");
  return s !== undefined && s.state === "OBSERVED" && s.outcome !== null && RUNNING.test(s.outcome) ? s : undefined;
}

/** What an observed step establishes and its limit; an adverse state (off, unpowered, failed) says only that. */
function establishes(s: ColdStepRead, chain?: ColdChainRead): [string, string] {
  if (s.kind === "PROBE" && !coolingRunning(chain)) return ["Chamber temperature after the compressor record", "No spoilage determination"];
  if (["GENERATOR", "BUS", "COMPRESSOR"].includes(s.kind) && s.outcome !== null && ADVERSE.test(s.outcome)) {
    return [`${stepLabel(s.kind)} recorded ${outcomeText(s)?.toLowerCase()}`, "Does not identify the cause"];
  }
  return STEP_ESTABLISHES[s.kind] ?? ["—", "—"];
}

function stepOf(chain: ColdChainRead | undefined, kind: string): ColdStepRead | undefined {
  return chain?.steps.find((s) => s.kind === kind);
}

function stepCell(step: ColdStepRead | undefined, verb: string): string {
  if (step === undefined) return "Not bound";
  if (step.state === "MISSING") return NOT_RECORDED;
  if (step.state === "CONTRADICTORY") return "Records disagree";
  return `${outcomeText(step) ?? verb} ${hm(step.at)}`;
}

function chainSentence(chain: ColdChainRead | undefined, contradicted: boolean): string {
  if (chain === undefined) return "No grid outage is recorded in this window.";
  if (contradicted || chain.result === "CONTRADICTORY") return "Accepted records disagree about the start result, so no start failure is claimed.";
  if (chain.result === "OBSERVED_FAILURE") return "The automatic generator start failed after the grid was lost.";
  if (chain.result === "OBSERVED_SUCCESS") return "The generator started after the grid was lost.";
  return "The start response cannot be established from the accepted records.";
}

function BackupStatus({ read }: { read: ColdBackupRead | null }) {
  if (read === null) return null;
  const chain = read.chains[0];
  return (
    <StatusBar label="Backup chain state">
      <Badge tone="neutral">{chain === undefined ? NOT_ASSESSED : startResultWord(chain.result)}</Badge>{" "}
      <Badge tone="neutral">Evidence: {claimWord(read.claim_level)}</Badge>{" "}
      {[
        `${read.chains.length === 1 ? "One outage" : `${read.chains.length} outages`} in the selected window`,
        windowText(read.window.from, read.window.to),
        currentnessWord(read.currentness.state),
      ].join(" · ")}
    </StatusBar>
  );
}

function chainTimeline(chain: ColdChainRead, links: ColdLinks): TimelineEvent[] {
  return chain.steps.map((s) => ({
    key: s.kind,
    time: s.at === null ? "—" : hm(s.at),
    title: `${stepLabel(s.kind)}${s.outcome ? ` · ${outcomeText(s)}` : ""}`,
    detail:
      s.state === "OBSERVED" && s.evidence_id !== null ? (
        <Link to={links.record(s.evidence_id)} data-evidence-link={s.evidence_id}>
          Accepted record
        </Link>
      ) : (
        stepStateWord(s.state)
      ),
    tone: s.state === "OBSERVED" ? (s.outcome !== null && ADVERSE.test(s.outcome) ? "danger" : undefined) : "gap",
  }));
}

function missingLine(chain: ColdChainRead): string | null {
  return chain.missing_steps.length === 0 ? null : `Not recorded: ${chain.missing_steps.map((s) => stepLabel(s).toLowerCase()).join(", ")}.`;
}

function BackupPanels({
  read,
  temperature,
  links,
  gap,
}: {
  read: ColdBackupRead | null;
  temperature: ColdTemperatureRead | null;
  links: ColdLinks;
  gap: string | null;
}) {
  const chain = read?.chains[0];
  const contradicted = (read?.contradictions.length ?? 0) > 0;
  const excluded = read?.excluded ?? [];
  const x = temperature?.excursions[0];
  return (
    <>
      <Panel heading="What the chain shows" headingId="cold-chain-shows-heading">
        {read === null ? (
          <Gap id="cold-chain-shows-heading">{gap}</Gap>
        ) : (
          <>
            <BigClaim data={{ "data-cold-chain-claim": chain?.result ?? "none" }}>{chainSentence(chain, contradicted)}</BigClaim>
            <p className="prose">
              {[
                chain === undefined ? null : missingLine(chain),
                contradicted ? "Conflicting accepted start outcomes are kept as excluded records." : null,
                "Which part failed, if any, is not determined here.",
              ]
                .filter(Boolean)
                .join(" ")}
            </p>
          </>
        )}
      </Panel>
      {read === null ? null : (
        <MetricCards label="Backup chain">
          <MetricCard label="Grid-loss event" value={stepOf(chain, "GRID")?.state === "OBSERVED" ? hm(stepOf(chain, "GRID")?.at) : NOT_RECORDED} note="Grid supply record" word={stepOf(chain, "GRID")?.state !== "OBSERVED"} />
          <MetricCard label="Automatic start" value={chain === undefined ? NOT_ASSESSED : startResultWord(chain.result)} note="Start request and result records" word />
          <MetricCard label="Manual recovery" value={NOT_RECORDED} note="No operational log is connected" word />
          <MetricCard label="Cooling resumed" value={coolingRunning(chain) ? hm(coolingRunning(chain)?.at) : NOT_RECORDED} note={stepOf(chain, "COMPRESSOR")?.state === "OBSERVED" && !coolingRunning(chain) ? `Compressor ${outcomeText(stepOf(chain, "COMPRESSOR")!)?.toLowerCase()} at ${hm(stepOf(chain, "COMPRESSOR")?.at)}; no running record` : "Compressor record"} word={!coolingRunning(chain)} />
        </MetricCards>
      )}
      <Panel heading="Reconstructed event chain" headingId="cold-chain-steps-heading">
        {read === null ? (
          <Gap id="cold-chain-steps-heading">{gap}</Gap>
        ) : chain === undefined ? (
          <Gap id="cold-chain-steps-heading">No grid outage in this window, so there is no chain to reconstruct.</Gap>
        ) : (
          <CausalTimeline events={chainTimeline(chain, links)} label="Reconstructed event chain" />
        )}
      </Panel>
      <Panel heading="Backup event chains" headingId="cold-chain-table-heading" description="Each outage in the selected window">
        {read === null ? (
          <Gap id="cold-chain-table-heading">{gap}</Gap>
        ) : (
          <DataTable labelledBy="cold-chain-table-heading">
            <thead>
              <tr>
                {["When", "Grid", "Start requested", "Generator", "Power to compressor", "Compressor response", "Outcome for service", "Result"].map((h) => (
                  <th key={h} scope="col">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {read.chains.length === 0 ? (
                <tr>
                  <td>No outage in the selected window</td>
                  <td>—</td>
                  <td>—</td>
                  <td>—</td>
                  <td>—</td>
                  <td>—</td>
                  <td>—</td>
                  <td>
                    <Badge tone="neutral">No event</Badge>
                  </td>
                </tr>
              ) : (
                read.chains.map((c) => (
                  <tr key={c.correlation_id ?? c.episode_id ?? "chain"} data-cold-chain-row>
                    <td>{dayHm(stepOf(c, "GRID")?.at ?? stepOf(c, "START_REQUEST")?.at ?? null)}</td>
                    <td>{stepCell(stepOf(c, "GRID"), "Lost")}</td>
                    <td>{stepCell(stepOf(c, "START_REQUEST"), "Seen")}</td>
                    <td>{stepCell(stepOf(c, "START_RESULT"), "Result")}</td>
                    <td>{[stepCell(stepOf(c, "TRANSFER"), "Transfer"), stepCell(stepOf(c, "BUS"), "Bus")].filter((s) => s !== "Not bound").join(" · ")}</td>
                    <td>{stepCell(stepOf(c, "COMPRESSOR"), "Running")}</td>
                    <td>{x === undefined ? (temperature?.state === "NO_EXCURSION_OBSERVED" ? "Within policy" : NOT_ASSESSED) : `${limitOf(temperature!, x.direction).word === "above" ? "Above" : "Below"} policy · ${range(x.duration_bounds.low, x.duration_bounds.high, "min")}`}</td>
                    <td>
                      <span className={`cold-result cold-result--${c.result === "OBSERVED_FAILURE" ? "danger" : c.result === "CONTRADICTORY" ? "warning" : "neutral"}`} data-cold-result={c.result}>
                        <Badge tone="neutral">{startResultWord(c.result)}</Badge>
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </DataTable>
        )}
      </Panel>
      <Panel heading="Evidence by causal step" headingId="cold-chain-evidence-heading">
        {read === null ? (
          <Gap id="cold-chain-evidence-heading">{gap}</Gap>
        ) : chain === undefined ? (
          <Gap id="cold-chain-evidence-heading">No chain step has accepted evidence in this window.</Gap>
        ) : (
          <>
            <DataTable labelledBy="cold-chain-evidence-heading">
              <thead>
                <tr>
                  {["Step", "Accepted observation", "What it establishes", "Limit"].map((h) => (
                    <th key={h} scope="col">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {chain.steps.map((s) => (
                  <tr key={s.kind} data-cold-step={s.kind} data-cold-step-state={s.state}>
                    <td>{stepLabel(s.kind)}</td>
                    <td>
                      {s.state === "OBSERVED" ? (
                        <>
                          {s.outcome ? `${outcomeText(s)} at ` : "At "}
                          {hm(s.at)}
                          {s.evidence_id === null ? null : (
                            <>
                              {" · "}
                              <Link to={links.record(s.evidence_id)} data-evidence-link={s.evidence_id}>
                                record
                              </Link>
                            </>
                          )}
                        </>
                      ) : (
                        stepStateWord(s.state)
                      )}
                    </td>
                    <td>{s.state === "OBSERVED" ? establishes(s, chain)[0] : "Nothing for this step"}</td>
                    <td>{s.state === "OBSERVED" ? establishes(s, chain)[1] : s.state === "MISSING" ? "No accepted record shows this step" : "Accepted records disagree"}</td>
                  </tr>
                ))}
                <tr data-cold-step="TEMPERATURE">
                  <td>Temperature</td>
                  <td>{x === undefined ? (temperature === null ? NOT_ASSESSED : "No excursion observed") : `Peak ${deg(x.peak_observed)}`}</td>
                  <td>{x === undefined ? "—" : "Bounded exposure"}</td>
                  <td>No spoilage determination</td>
                </tr>
              </tbody>
            </DataTable>
            {excluded.length === 0 ? null : (
              <p className="v69-chart-note" data-cold-excluded={excluded.length}>
                Records not used: {excluded.map((e) => reasonWord(e.reason).toLowerCase()).join(" · ")}.
              </p>
            )}
            <ExactReferences
              name="cold-chain-references"
              references={[
                ...chain.steps.map((s) => ({ label: `${stepLabel(s.kind)} records`, value: (s.evidence_ids ?? (s.evidence_id ? [s.evidence_id] : [])).join(", ") || null })),
                ...excluded.map((e, i) => ({ label: `Not used ${i + 1} (${reasonWord(e.reason).toLowerCase()})`, value: e.evidence_id })),
                { label: "Start correlation", value: chain.correlation_id },
                { label: "Episode", value: chain.episode_id },
              ]}
            />
          </>
        )}
      </Panel>
      <Notice tone="blue">The backup chain and the temperature view share accepted records. No Incident or failed-part diagnosis is made here.</Notice>
    </>
  );
}

/* ---------- Performance frame ---------- */

export interface ColdPerformanceFrameProps {
  view: ColdPerformanceView;
  siteId: string;
  siteName: string;
  mode: string | null;
  window: ColdWindowQuery;
  client: ColdAssessmentClient;
  links: ColdLinks;
  tabs: ReactNode;
  parentTrail: Crumb[];
  subtabHref: (id: "temperature" | "backup") => string;
}

export function ColdPerformanceFrame(props: ColdPerformanceFrameProps) {
  const { view, siteId, window, client, links } = props;
  const key = `${siteId}|${windowKey(window)}`;
  const temperature = useRead(() => client.getTemperature(siteId, window), `t|${key}`);
  const backup = useRead(() => client.getBackupChain(siteId, window), `b|${key}`);
  const findings = useRead(() => client.listFindings(siteId, window), `f|${key}`);
  const primary = view === "temperature" ? temperature : backup;
  const ready = temperature !== null && backup !== null && findings !== null;
  const gap =
    primary !== null && primary.status !== "loaded" ? refusalText(primary).body : null;
  return (
    <main aria-labelledby={COLD_PERFORMANCE_HEADING_ID} data-cold-view={view === "temperature" ? "temperature" : "coldbackup"}>
      <Breadcrumbs trail={[...props.parentTrail, { label: "Performance" }]} />
      <SitePageHeader
        siteName={props.siteName}
        siteId={siteId}
        mode={props.mode}
        description={SITE_SCREEN_DESCRIPTIONS[view === "temperature" ? "temperature" : "coldbackup"]}
        headingId={COLD_PERFORMANCE_HEADING_ID}
      />
      {props.tabs}
      <nav className="site-tabs site-subtabs" aria-label="Performance sections">
        <ol className="site-tabs__list">
          <li className="site-tabs__item">
            <Link className="site-tabs__link" to={props.subtabHref("temperature")} data-performance-subtab="temperature" aria-current={view === "temperature" ? "page" : undefined}>
              Temperature
            </Link>
          </li>
          <UnavailableTab label="Cooling" />
          <li className="site-tabs__item">
            <Link className="site-tabs__link" to={props.subtabHref("backup")} data-performance-subtab="backup" aria-current={view === "backup" ? "page" : undefined}>
              Backup
            </Link>
          </li>
        </ol>
      </nav>
      {!ready ? (
        <p>{COLD_ASSESSMENT_LOADING}</p>
      ) : view === "temperature" ? (
        <>
          {temperature.status === "loaded" ? <TemperatureStatus read={temperature.value} /> : <PageRefusal read={temperature} window={window} />}
          {temperature.status === "loaded" ? <TemperatureCards read={temperature.value} /> : null}
          <TemperaturePanels read={loaded(temperature)} backup={loaded(backup)} findings={loaded(findings)} links={links} gap={gap} />
        </>
      ) : (
        <>
          {backup.status === "loaded" ? <BackupStatus read={backup.value} /> : <PageRefusal read={backup} window={window} />}
          <BackupPanels read={loaded(backup)} temperature={loaded(temperature)} links={links} gap={gap} />
        </>
      )}
    </main>
  );
}

/* ---------- Finding detail ---------- */

export interface ColdFindingFrameProps {
  siteId: string;
  siteName: string;
  findingId: string;
  window: ColdWindowQuery;
  client: ColdAssessmentClient;
  links: ColdLinks;
  tabs: ReactNode;
  parentTrail: Crumb[];
}

function str(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function bounds(value: unknown): { earliest: string | null; latest: string | null } {
  const v = (value ?? {}) as Record<string, unknown>;
  return { earliest: str(v.earliest), latest: str(v.latest) };
}

function rangeOf(value: unknown): { low: string | null; high: string | null } {
  const v = (value ?? {}) as Record<string, unknown>;
  return { low: str(v.low), high: str(v.high) };
}

function FindingStatus({ finding, siteName }: { finding: ColdFindingDetailRead; siteName: string }) {
  return (
    <StatusBar label="Finding state">
      <Badge tone="lifecycle">{lifecycleWord(finding.lifecycle)}</Badge>{" "}
      {[siteName, `evidence ${claimWord(finding.claim_level).toLowerCase()}`, windowText(finding.window.from, finding.window.to), currentnessWord(finding.currentness.state)].join(" · ")}
    </StatusBar>
  );
}

/** The Finding's limits, once each; the no-spoilage sentence is already the panel's own prose line. */
function limitsLine(finding: ColdFindingDetailRead): ReactNode {
  const limits = unique(finding.limitations).filter((text) => !/^No spoilage/.test(text));
  if (limits.length === 0) return null;
  return (
    <ul className="cold-limits" data-cold-limitations>
      {limits.map((text) => (
        <li key={text}>{plainLimitation(text)}</li>
      ))}
    </ul>
  );
}

function findingReferences(finding: ColdFindingDetailRead) {
  return [
    { label: "Finding", value: finding.finding_id },
    { label: "Finding version", value: finding.revision_id },
    { label: "Episode", value: finding.episode_id },
    { label: "Episode version", value: finding.episode_revision_id },
    { label: "Assessment version", value: finding.assessment_revision_id },
    { label: "Finding basis", value: finding.basis_sha256 },
    { label: "Accepted records", value: finding.evidence_ids.join(", ") || null },
    { label: "Earlier versions", value: finding.revisions.slice(1).map((r) => `${r.revision_no}: ${r.revision_id}`).join(", ") || null },
  ];
}

function versionsLine(finding: ColdFindingDetailRead): string {
  const latest = finding.revisions[0];
  if (latest === undefined) return NOT_RECORDED;
  return `${finding.revisions.length} · latest: ${transitionWord(latest.transition).toLowerCase()}, ${dayHm(latest.created_at)} UTC`;
}

function NextStepPanel({ links, related }: { links: { href: string; label: string }[]; related: ReactNode }) {
  return (
    <Panel heading="Recommended next step" headingId="cold-next-step-heading">
      <Gap id="cold-next-step-heading">{NO_RECORDED_NEXT_STEP}. No Action or Recommendation record is linked to this Finding.</Gap>
      {links.map((l) => (
        <p className="cold-panel-link" key={l.href}>
          <Link to={l.href}>{l.label}</Link>
        </p>
      ))}
      {related}
    </Panel>
  );
}

function StartFindingPanels({ finding, backup, links }: { finding: ColdFindingDetailRead; backup: ColdRead<ColdBackupRead>; links: ColdLinks }) {
  const result = str(finding.claim.result);
  const missing = Array.isArray(finding.claim.missing_steps) ? (finding.claim.missing_steps as string[]) : [];
  const chain = loaded(backup)?.chains.find((c) => c.correlation_id === str(finding.claim.correlation_id)) ?? null;
  const request = finding.episode_bounds.start.latest;
  return (
    <>
      <Panel heading="Bounded conclusion" headingId="cold-conclusion-heading">
        <BigClaim>
          {result === "OBSERVED_FAILURE"
            ? `A commanded automatic generator start failed${request ? ` after the request at ${hm(request)}` : ""}.`
            : result === "OBSERVED_SUCCESS"
              ? "The commanded automatic generator start succeeded."
              : "The start response is not established by the accepted records."}
        </BigClaim>
        <p className="prose">The chronology does not establish product spoilage or the component that caused the failed start.</p>
        {limitsLine(finding)}
        <p className="cold-panel-link">
          <Link to={links.backup}>Inspect the backup chain →</Link>
        </p>
      </Panel>
      <div className="panel-pair">
        <Panel heading="Operational context" headingId="cold-operational-heading">
          {chain !== null ? (
            <CausalTimeline events={chainTimeline(chain, links)} label="Reconstructed event chain" />
          ) : (
            <Gap id="cold-operational-chain">
              {backup.status === "loaded" ? "The selected backup chain does not include this start request." : refusalText(backup).body}
            </Gap>
          )}
          <KeyValues
            label="Operational context"
            rows={[
              ["Missing steps", missing.length === 0 ? "None" : missing.map((s) => stepLabel(s)).join(", "), "missing"],
              ["Versions", versionsLine(finding), "versions"],
            ]}
          />
          <EvidenceLine finding={finding} links={links} />
          <ExactReferences name="cold-finding-references" references={findingReferences(finding)} />
        </Panel>
        <NextStepPanel links={[{ href: links.backup, label: "Open the Backup view →" }]} related={null} />
      </div>
    </>
  );
}

function ExcursionFindingPanels({
  finding,
  temperature,
  findings,
  links,
}: {
  finding: ColdFindingDetailRead;
  temperature: ColdRead<ColdTemperatureRead>;
  findings: ColdFindingsRead | null;
  links: ColdLinks;
}) {
  const t = loaded(temperature);
  const direction = str(finding.claim.direction) ?? "HIGH";
  const limit = t === null ? { word: direction === "LOW" ? "below" : "above", value: null } : limitOf(t, direction);
  const duration = rangeOf(finding.claim.duration_bounds);
  const dm = rangeOf(finding.claim.degree_minute_bounds);
  const start = bounds(finding.claim.start_bounds);
  const end = bounds(finding.claim.end_bounds);
  const open = finding.claim.open === true || end.latest === null;
  const peak = str(finding.claim.peak_observed);
  const related = findings?.items.find((f) => f.kind === "START_RESPONSE") ?? null;
  return (
    <>
      <Panel heading="Bounded conclusion" headingId="cold-conclusion-heading">
        <BigClaim>
          {`The chamber was ${limit.word} ${limit.value === null ? "policy" : deg(limit.value)} for ${range(duration.low, duration.high, "minutes").replace(/^At least/, "at least")}, starting ${between(start.earliest, start.latest)}${
            open ? " and still outside policy at the window end" : `, back within policy ${between(end.earliest, end.latest)}`
          }${peak === null ? "" : `, peaking at ${deg(peak)}`}.`}
        </BigClaim>
        <p className="prose">This is exposure context. It does not establish spoilage, product loss or a money value.</p>
        {limitsLine(finding)}
        <p className="cold-panel-link">
          <Link to={links.temperature}>Inspect the temperature readings →</Link>
        </p>
      </Panel>
      <div className="panel-pair">
        <Panel heading="Temperature" headingId="cold-finding-temperature-heading">
          {t === null ? (
            <Gap id="cold-finding-temperature-heading">{temperature.status === "loaded" ? "" : refusalText(temperature).body}</Gap>
          ) : (
            <>
              <ColdTemperatureChart read={t} label={`Chamber temperature, ${windowText(t.window.from, t.window.to)}, with the policy band`} />
              {gapNotes(t)}
            </>
          )}
          <KeyValues
            label="Temperature"
            rows={[
              ["Peak observed", deg(peak), "peak"],
              ["Exposure size", range(dm.low, dm.high, "°C·min"), "exposure"],
            ]}
          />
          <EvidenceLine finding={finding} links={links} />
          <ExactReferences name="cold-finding-references" references={findingReferences(finding)} />
        </Panel>
        <NextStepPanel
          links={[{ href: links.temperature, label: "Open the Temperature view →" }]}
          related={
            related === null ? null : (
              <p className="cold-panel-link">
                <Link to={links.finding(related.finding_id)} data-finding-link={related.finding_id}>
                  Related: backup start Finding →
                </Link>
              </p>
            )
          }
        />
      </div>
    </>
  );
}

function FindingSkeleton({ gap }: { gap: string }) {
  return (
    <>
      <Panel heading="Bounded conclusion" headingId="cold-conclusion-heading">
        <Gap id="cold-conclusion-heading">{gap}</Gap>
      </Panel>
      <div className="panel-pair">
        <Panel heading="Operational context" headingId="cold-operational-heading">
          <Gap id="cold-operational-heading">{gap}</Gap>
        </Panel>
        <Panel heading="Recommended next step" headingId="cold-next-step-heading">
          <Gap id="cold-next-step-heading">{NO_RECORDED_NEXT_STEP}.</Gap>
        </Panel>
      </div>
    </>
  );
}

export function ColdFindingFrame(props: ColdFindingFrameProps) {
  const { siteId, findingId, window, client, links } = props;
  const finding = useRead(() => client.getFinding(siteId, findingId, window), `d|${siteId}|${findingId}|${windowKey(window)}`);
  const detail = loaded(finding);
  // The companion reads use the Finding's own selected window, so the chart and chain match its revision.
  const own: ColdWindowQuery | null = detail === null ? null : { from: detail.window.from, to: detail.window.to, known_at: detail.window.known_at };
  const ownKey = own === null ? "" : windowKey(own);
  const isExcursion = detail?.kind === "EXCURSION";
  const temperature = useRead(own !== null && isExcursion ? () => client.getTemperature(siteId, own) : null, `t|${siteId}|${ownKey}`);
  const backup = useRead(own !== null && !isExcursion ? () => client.getBackupChain(siteId, own) : null, `b|${siteId}|${ownKey}`);
  const findings = useRead(own !== null && isExcursion ? () => client.listFindings(siteId, own) : null, `f|${siteId}|${ownKey}`);
  const ownLinks: ColdLinks =
    own === null
      ? links
      : {
          ...links,
          temperature: `${links.temperature.split("?")[0]}${coldWindowSearch(own)}`,
          backup: `${links.backup.split("?")[0]}${coldWindowSearch(own)}`,
        };
  const companionReady = detail === null || (isExcursion ? temperature !== null && findings !== null : backup !== null);
  const title = detail?.title ?? "Finding";
  return (
    <main aria-labelledby={COLD_FINDING_HEADING_ID} data-cold-view={detail === null ? "cold-finding" : isExcursion ? "cold-finding-excursion" : "cold-finding"}>
      <Breadcrumbs trail={[...props.parentTrail, { label: "Finding" }]} />
      <PageHeader title={title} headingId={COLD_FINDING_HEADING_ID} subtitle={`${props.siteName} · cold-chain finding`} />
      {props.tabs}
      <nav className="site-tabs site-subtabs" aria-label="Finding sections">
        <ol className="site-tabs__list">
          <li className="site-tabs__item">
            <span className="site-tabs__link" aria-current="page">
              Overview
            </span>
          </li>
          <UnavailableTab label="Recommendation" />
        </ol>
      </nav>
      {finding === null || !companionReady ? (
        <p>{finding === null ? COLD_FINDING_LOADING : COLD_ASSESSMENT_LOADING}</p>
      ) : finding.status !== "loaded" ? (
        <>
          <PageRefusal read={finding} window={window} />
          <FindingSkeleton gap={refusalText(finding).body} />
        </>
      ) : (
        <>
          <FindingStatus finding={finding.value} siteName={props.siteName} />
          {isExcursion ? (
            <ExcursionFindingPanels finding={finding.value} temperature={temperature!} findings={loaded(findings)} links={ownLinks} />
          ) : (
            <StartFindingPanels finding={finding.value} backup={backup!} links={ownLinks} />
          )}
        </>
      )}
    </main>
  );
}
