/**
 * W3-02 commit 2: the estate Evidence root (v6.9 `globalevidence`, `I-estate-evidence-root`) read from
 * `GET /api/estate/evidence` (`estate-evidence-1`). Copy and layout follow `.agent/W3-02-build-spec.md`: the mock
 * ledger, "Refusals and UI states", closure 1 "Mock copy, navigation and measured layout", closure 2 Q27 (inert
 * example destinations and the Unlocks dictionary) and closure 5 S13 (the two panel titles). Every value is a
 * server field; the page scores nothing, builds no Site route and invents no Action. Mock numbers never render.
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { DataTable, Disclosure, MetricCard, MetricCards, Notice, PageHeader, Panel } from "../ui";
import { UnavailableInline, UnavailableLinkEntry } from "../ui/UnavailableEntry";
import type { EstateEnvelope } from "./estateClient";
import {
  createEstateEvidenceMoneyClient,
  type EstateEvidenceBody,
  type EstateEvidenceMoneyClient,
  type EvidenceGap,
  type EvidenceReadiness,
  type EvidenceResult,
  type EvidenceRow,
} from "./estateEvidenceMoneyClient";
import { EstateDateBar, EstateRefusal, Pager, estateHref, queryFromParams, utcInstant } from "./estateShared";
import "./estateEvidence.css";

export const ESTATE_EVIDENCE_PATH = "/evidence";

export const EVIDENCE_TITLE = "Portfolio evidence";
/** The mock eyebrow; `PageHeader` has no eyebrow slot, so the shell crumb carries it (Lane A request). */
export const EVIDENCE_EYEBROW = "Evidence";
export const EVIDENCE_SUBTITLE = "Cross-site claim readiness, recurring gaps and instrumentation priorities";
export const COVERAGE_PANEL = "Capability coverage across sites";
export const GAPS_PANEL = "Recurring evidence gaps";
export const COVERAGE_SUBTITLE = "Each row links to site-owned readiness; this page does not independently score the claims";
export const EVIDENCE_NOTICE =
  "Source connectivity is not physical asset health. Evidence Full/Limited/None/N-A is a separate vocabulary from Healthy/Watch/Degraded.";

export const NO_ACCESSIBLE_SITES = "No accessible Sites";
export const NO_SELECTED_EVIDENCE = "No selected evidence for this window";
export const STILL_ASSESSED = "Some Sites are still being assessed";
export const NO_GAPS = "No recurring evidence gaps recorded for this window";
export const NO_UNLOCKS = "No supported capability recorded";
export const NO_NEXT_STEP = "Next step not recorded";

/** Closure 2 Q27: the four static mock CTA slots, kept as inert examples outside the data-backed table. */
export const EXAMPLE_DESTINATIONS = ["ACT-049, ACT-061", "Map transfer switch", "Operational records", "Preventive plan"] as const;

/** Closure 2 Q27: the closed `Unlocks` dictionary, keyed by the display capability's base key. */
const UNLOCK_LABEL: Readonly<Record<string, string>> = {
  GENERATOR_SUPPORT: "Generator support",
  temperature: "Temperature compliance",
  backup: "Backup response",
  cooling: "Cooling recovery",
  exposure: "Product exposure",
  sessions: "Session outcomes",
  availability: "Connector availability",
  energy: "Delivered energy",
  cause: "Cause of interruption",
};

/** The mock readiness chip words and closure 1 tones (page-local `estate-tone--*`, no shared `BadgeTone`). */
const READINESS_WORDS: Readonly<Record<EvidenceReadiness, { text: string; tone: string }>> = {
  FULL: { text: "Full", tone: "green" },
  LIMITED: { text: "Limited", tone: "amber" },
  NONE: { text: "None", tone: "gray" },
  UNKNOWN: { text: "Unknown", tone: "gray" },
  CONTRADICTORY: { text: "Contradictory", tone: "red" },
  NOT_APPLICABLE: { text: "N/A", tone: "gray" },
};

/** Row context shown beside the readiness chip: pending amber, historical blue (ledger `Readiness`). */
const CONTEXT_WORDS: Readonly<Record<string, { text: string; tone: string }>> = {
  PENDING_RECOMPUTE: { text: "New evidence is being assessed", tone: "amber" },
  STALE_SOURCE: { text: "May miss newer readings", tone: "amber" },
  UNASSESSED: { text: "Not yet assessed", tone: "gray" },
  UNKNOWN: { text: "Not yet assessed", tone: "gray" },
};

export function historicalAsOf(instant: string): string {
  return `Historical as of ${utcInstant(instant)}`;
}

/** `2026-10-14 08:00–16:00 UTC`, or both dates when the bounds cross a day. */
function windowText(row: EvidenceRow): string | null {
  if (row.window_start === null || row.window_end === null) return null;
  const [a, b] = [row.window_start, row.window_end];
  const sameDay = a.slice(0, 10) === b.slice(0, 10);
  return sameDay
    ? `${a.slice(0, 10)} ${a.slice(11, 16)}–${b.slice(11, 16)} UTC`
    : `${a.slice(0, 10)} ${a.slice(11, 16)} – ${b.slice(0, 10)} ${b.slice(11, 16)} UTC`;
}

/** Closure 2 Q27: dedupe, sort by key, join labels with ` · `; nothing selected is `No supported capability recorded`. */
export function unlocksText(unlocks: string[]): string {
  const labels: string[] = [];
  for (const key of [...unlocks].sort()) {
    const label = UNLOCK_LABEL[key.split("@")[0]];
    if (label !== undefined && !labels.includes(label)) labels.push(label);
  }
  return labels.length === 0 ? NO_UNLOCKS : labels.join(" · ");
}

function Cards({ body }: { body: EstateEvidenceBody }) {
  const limited = body.summary.limited_site_count;
  const empty = body.status === "EMPTY_SCOPE";
  return (
    <MetricCards columns={3} label="Evidence summary" data={{ "data-estate-cards": "" }}>
      <MetricCard
        label="Sites with limited claims"
        value={empty ? "0 of 0" : limited === null ? "Not assessed" : `${limited} of ${body.scope.authorized_site_count}`}
        word={!empty && limited === null}
        tone="muted"
        note={empty ? NO_ACCESSIBLE_SITES : limited === null ? "Some Site evidence is unavailable" : "Sites with a selected limited capability"}
        data={{ "data-estate-card": "limited_site_count" }}
      />
      <MetricCard
        label="Priority evidence actions"
        value="Not assessed"
        word
        tone="muted"
        note="Priority is not recorded for estate evidence gaps"
        data={{ "data-estate-card": "priority_gap_count" }}
      />
      <MetricCard
        label="Unsupported claims"
        value="Not assessed"
        word
        tone="muted"
        note="No cross-domain unsupported-claim count is recorded"
        data={{ "data-estate-card": "unsupported_claim_count" }}
      />
    </MetricCards>
  );
}

function Chip({ tone, text, data }: { tone: string; text: string; data: Record<string, string> }) {
  return (
    <span className={`estate-chip estate-tone--${tone}`} {...data}>
      {text}
    </span>
  );
}

function RowDetails({ row }: { row: EvidenceRow }) {
  const d = row.disclosure;
  return (
    <Disclosure summary="Record details" name="estate-evidence-row" variant="inline">
      <dl className="estate-evidence-facts">
        <dt>Capability key</dt>
        <dd>{d.capability_key}</dd>
        <dt>Selected state</dt>
        <dd>{row.raw_state}</dd>
        <dt>Selected revisions</dt>
        <dd>{row.selected_revision_ids.length > 0 ? row.selected_revision_ids.join(", ") : "None selected"}</dd>
        {row.gap_codes.length > 0 ? (
          <>
            <dt>Gap codes</dt>
            <dd>{row.gap_codes.join(", ")}</dd>
          </>
        ) : null}
        {d.historical !== null ? (
          <>
            <dt>{d.historical.label}</dt>
            <dd>{d.historical.statements.join(" ")}</dd>
          </>
        ) : null}
      </dl>
      <pre className="estate-evidence-raw">{JSON.stringify({ constituents: d.constituents, reasons: d.reasons, prior_selection: d.prior_selection ?? null }, null, 1)}</pre>
    </Disclosure>
  );
}

function CoverageRow({ row, asOf }: { row: EvidenceRow; asOf: string }) {
  const readiness = READINESS_WORDS[row.readiness] ?? READINESS_WORDS.UNKNOWN;
  const context = row.raw_state === "HISTORICAL" ? null : CONTEXT_WORDS[row.raw_state];
  const window = windowText(row);
  return (
    <tr data-estate-evidence-row={`${row.site_id}|${row.capability_key}`}>
      <td>
        <Link className="estate-cell__primary" to={row.links.site_readiness} data-estate-site-link>
          {row.site_name} · {row.domain_label}
        </Link>
        {row.links.site_readiness_label !== null ? (
          <span className="estate-cell__secondary" data-estate-current-view>
            {row.links.site_readiness_label}
          </span>
        ) : null}
      </td>
      <td>
        <span className="estate-cell__primary">{row.capability_label}</span>
        {window !== null ? <span className="estate-cell__secondary">{window}</span> : null}
        <RowDetails row={row} />
      </td>
      <td>
        <Chip tone={readiness.tone} text={readiness.text} data={{ "data-estate-readiness": row.readiness }} />
        {row.raw_state === "HISTORICAL" ? (
          <Chip tone="blue" text={historicalAsOf(asOf)} data={{ "data-estate-row-context": "HISTORICAL" }} />
        ) : context !== undefined && context !== null ? (
          <Chip tone={context.tone} text={context.text} data={{ "data-estate-row-context": row.raw_state }} />
        ) : null}
      </td>
      <td>{row.current_ceiling ?? "No current ceiling"}</td>
      <td>{row.next_evidence ?? "Not recorded"}</td>
    </tr>
  );
}

function CoverageTable({ body }: { body: EstateEvidenceBody }) {
  const asOf = body.summary.as_of ?? body.window.known_at;
  return (
    <div className="estate-evidence-table estate-evidence-table--coverage">
      <DataTable labelledBy="estate-evidence-coverage-heading">
        <colgroup>
          {[18, 18, 14, 26, 24].map((width, index) => (
            <col key={index} style={{ width: `${width}%` }} />
          ))}
        </colgroup>
        <thead>
          <tr>
            {["Site / domain", "Operational capability", "Readiness", "Current ceiling", "Next evidence"].map((h) => (
              <th key={h} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.rows.map((row) => (
            <CoverageRow key={`${row.site_id}|${row.capability_key}`} row={row} asOf={asOf} />
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

function GapRow({ gap, names }: { gap: EvidenceGap; names: ReadonlyMap<string, string> }) {
  const sites = gap.site_codes.map((code) => names.get(code) ?? code);
  return (
    <tr data-estate-gap={`${gap.domain}|${gap.gap_code}|${gap.missing_role ?? ""}`}>
      <td>
        <span className="estate-cell__primary">{gap.label}</span>
        <Disclosure summary="Record details" name="estate-evidence-gap" variant="inline">
          <dl className="estate-evidence-facts">
            <dt>Gap code</dt>
            <dd>{gap.gap_code}</dd>
            <dt>Missing role</dt>
            <dd>{gap.missing_role ?? "None named"}</dd>
            <dt>Site codes</dt>
            <dd>{gap.site_codes.join(", ")}</dd>
          </dl>
        </Disclosure>
      </td>
      <td data-estate-gap-sites>{sites.join(" · ")}</td>
      <td data-estate-gap-unlocks>{unlocksText(gap.unlocks)}</td>
      <td data-estate-gap-step>
        {gap.next_step === null ? NO_NEXT_STEP : <UnavailableInline label={gap.next_step} />}
      </td>
    </tr>
  );
}

function GapsTable({ body }: { body: EstateEvidenceBody }) {
  const names = new Map(body.rows.map((row) => [row.site_code, row.site_name]));
  return (
    <div className="estate-evidence-table estate-evidence-table--gaps">
      <DataTable labelledBy="estate-evidence-gaps-heading">
        <colgroup>
          {[41, 14, 29, 16].map((width, index) => (
            <col key={index} style={{ width: `${width}%` }} />
          ))}
        </colgroup>
        <thead>
          <tr>
            {["Gap", "Sites", "Unlocks", "Next step"].map((h) => (
              <th key={h} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.gaps.map((gap) => (
            <GapRow key={`${gap.domain}|${gap.gap_code}|${gap.missing_role ?? ""}`} gap={gap} names={names} />
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

function ExampleDestinations() {
  return (
    <div className="note estate-evidence-examples" data-estate-examples>
      <span className="estate-evidence-examples__label">Example destinations</span>
      {EXAMPLE_DESTINATIONS.map((label) => (
        <UnavailableLinkEntry key={label} label={label} />
      ))}
    </div>
  );
}

/** The state table's panel notes (outside the table, headers kept): empty scope, no selection, partial, historical. */
function CoverageNotes({ body }: { body: EstateEvidenceBody }) {
  const notes: [string, string][] = [];
  if (body.status === "EMPTY_SCOPE") notes.push(["empty-scope", NO_ACCESSIBLE_SITES]);
  else if (body.total_count === 0) notes.push(["no-selection", NO_SELECTED_EVIDENCE]);
  if (body.status !== "EMPTY_SCOPE" && body.coverage.state !== "COMPLETE") notes.push(["partial", STILL_ASSESSED]);
  if (body.status === "HISTORICAL") notes.push(["historical", historicalAsOf(body.summary.as_of ?? body.window.known_at)]);
  return (
    <>
      {notes.map(([key, text]) => (
        <p key={key} className="estate-evidence-note" data-estate-note={key}>
          {text}
        </p>
      ))}
    </>
  );
}

/** The shared date bar reads only `status` and `window`; the new roots add `EMPTY_SCOPE`, which it ignores. */
function barBody(body: EstateEvidenceBody | null): EstateEnvelope | null {
  return body === null ? null : (body as unknown as EstateEnvelope);
}

export function EstateEvidencePage({ client }: { client?: EstateEvidenceMoneyClient }) {
  const reads = useMemo(() => client ?? createEstateEvidenceMoneyClient(), [client]);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const query = queryFromParams(params);
  const key = params.toString();
  const [result, setResult] = useState<{ key: string; read: EvidenceResult<EstateEvidenceBody> } | null>(null);

  useEffect(() => {
    let live = true;
    void reads.evidence(query).then((read) => {
      if (live) setResult({ key, read });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);

  const firstPage = estateHref(ESTATE_EVIDENCE_PATH, query);
  const read = result?.key === key ? result.read : null;
  const body = read?.status === "loaded" ? read.value : null;
  const next =
    body === null || body.next_cursor === null ? null : estateHref(ESTATE_EVIDENCE_PATH, query, { cursor: body.next_cursor });

  return (
    <div className="estate-page estate-evidence" data-estate-root="evidence">
      <PageHeader title={EVIDENCE_TITLE} subtitle={EVIDENCE_SUBTITLE} />
      <EstateDateBar
        key={`${query.from}|${query.to}|${query.known_at ?? ""}`}
        query={query}
        body={barBody(body)}
        onApply={(nextQuery) => navigate(estateHref(ESTATE_EVIDENCE_PATH, nextQuery))}
      />
      {read === null ? (
        <p className="estate-loading" data-estate-loading>
          Loading evidence across the estate.
        </p>
      ) : read.status === "refused" ? (
        <EstateRefusal code={read.code} copy={read.copy} firstPage={firstPage} />
      ) : (
        <>
          <Cards body={read.value} />
          <Panel heading={COVERAGE_PANEL} headingId="estate-evidence-coverage-heading" description={COVERAGE_SUBTITLE}>
            <CoverageTable body={read.value} />
            <CoverageNotes body={read.value} />
            <Pager next={next} first={firstPage} paged={query.cursor !== null} />
          </Panel>
          <Panel heading={GAPS_PANEL} headingId="estate-evidence-gaps-heading">
            <GapsTable body={read.value} />
            {read.value.gaps.length === 0 ? (
              <p className="estate-evidence-note" data-estate-note="no-gaps">
                {NO_GAPS}
              </p>
            ) : null}
            <ExampleDestinations />
          </Panel>
          <Notice tone="blue" data={{ "data-estate-notice": "" }}>
            {EVIDENCE_NOTICE}
          </Notice>
        </>
      )}
    </div>
  );
}
