/**
 * DIESEL-K5 (DIESEL-1-R3l, build sheet DIESEL-1 §9l.2): Site › Performance › Fuel in night mode, for a Site with at
 * least one stored fuel-balance window. Composed of the existing v69 components only (status bar, metric cards,
 * value bars, bounded tables, notice) and the existing mini bound classes; every visible number and sentence is the
 * server's (`fuel_balance/night_text.py`); the browser formats no number.
 *
 * MOCK DEVIATION MD-FUEL-K-1 (DIESEL-1-R3l): a night window (6 pm to noon) chosen with a night selector, instead of
 * v69 `fuel`'s hour bar (index.html:623-630 shows Kobo's selected hour).
 */
import { useEffect, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";
import { RangeLink as Link } from "../ui/RangeLink";

import { Badge, ChartNote, DataTable, MetricCard, MetricCards, Notice, Panel, ShowAll, StatusBar, ValueBars } from "../ui";
import { sourceQualification } from "../ui/productWords";
import { useLinkFor } from "./chainRef";
import type { FuelBalanceClient, FuelBridgeRow, FuelNightBody, FuelNightSummary, FuelProvenance, FuelRecordRow } from "./fuelBalanceClient";
import type { MiniRead } from "./miniDepthClient";
import { FUEL_NOTICE, MINI_LOADING, MINI_UNAVAILABLE, UNKNOWN } from "./MiniPerformance";
import "./w4-mini-performance.css";

/** The existing hour-mode chart sentence (MiniPerformance.tsx FuelGlancePanel), kept verbatim. */
const CHART_SENTENCE = "A residual is shown only when every term has a supported range.";
/** Records beyond this many sit behind the shared "Show all" expander. */
const RECORDS_SHOWN = 6;

/** The mini pages' provenance chips (same words as the hour-mode status bar). */
export function fuelProvenanceChips(provenance: FuelProvenance | null | undefined): string[] {
  const selected = provenance?.selected_source_provenance?.classification ?? null;
  const pending = provenance?.pending_source_provenance?.classification ?? null;
  const chips: string[] = [];
  if (selected !== null) chips.push(`Selected sources: ${sourceQualification(selected).label}`);
  if (pending !== null) chips.push(`Pending sources: ${sourceQualification(pending).label}`);
  return chips;
}

function useRead<T>(load: () => Promise<MiniRead<T>>, key: string): MiniRead<T> | null {
  const [state, setState] = useState<{ key: string; value: MiniRead<T> } | null>(null);
  useEffect(() => {
    let active = true;
    void load().then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
    // `load` is rebuilt every render; the key names what it reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state !== null && state.key === key ? state.value : null;
}

/** The mini bound frame (MiniPerformance.tsx `BoundedPanel`), on the existing mock-derived bound classes. */
function BoundedTablePanel({ bound, heading, headingId, children }: { bound: string; heading: string; headingId: string; children: ReactNode }) {
  return (
    <Panel heading={heading} headingId={headingId} flush className={`mini-bound mini-max--${bound} mini-bound--table`}>
      {children}
    </Panel>
  );
}

/** "Balance bridge": five server rows, with the cited count and the Evidence link as the hour bridge has them. */
export function FuelNightBridge({ rows, evidenceHref, headingId }: { rows: FuelBridgeRow[]; evidenceHref: string | null; headingId: string }) {
  return (
    <BoundedTablePanel bound="fuel-bridge" heading="Balance bridge" headingId={headingId}>
      <DataTable labelledBy={headingId}>
        <thead>
          <tr>
            <th scope="col">Term</th>
            <th scope="col">Evidence basis</th>
            <th scope="col">Treatment</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.term} data-fuel-night-term={row.term}>
              <td>
                {row.label}
                <span className="mini-cited">{` · ${row.value}`}</span>
              </td>
              <td>
                {row.basis}
                <span className="mini-cited">
                  {` · ${row.evidence_count} cited record${row.evidence_count === 1 ? "" : "s"}`}
                  {evidenceHref === null || row.evidence_count === 0 ? null : (
                    <>
                      {" · "}
                      <Link to={evidenceHref}>Evidence</Link>
                    </>
                  )}
                </span>
              </td>
              <td>{row.treatment}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </BoundedTablePanel>
  );
}

function RecordRows({ rows }: { rows: FuelRecordRow[] }) {
  return (
    <>
      {rows.map((row) => (
        <tr key={`${row.code}-${row.occurred_at}`} data-fuel-record={row.code}>
          <td>{row.when}</td>
          <td>{row.kind}</td>
          <td>{row.volume}</td>
          <td className="mini-ids">{row.code}</td>
        </tr>
      ))}
    </>
  );
}

function RecordTable({ rows, headingId }: { rows: FuelRecordRow[]; headingId: string }) {
  return (
    <DataTable labelledBy={headingId}>
      <thead>
        <tr>
          <th scope="col">Time</th>
          <th scope="col">Record</th>
          <th scope="col">Volume</th>
          <th scope="col">Reference</th>
        </tr>
      </thead>
      <tbody>
        <RecordRows rows={rows} />
      </tbody>
    </DataTable>
  );
}

/**
 * "Deliveries and tank dips": the K2 records occurring in the night, in order.
 *
 * MOCK DEVIATION MD-FUEL-K5-1 (DIESEL-1-R3l): v69 `fuel` has no record list; its bridge names "Delivery / operator
 * records" (index.html:627). The table reuses the bridge's bound and shows 6 rows before "Show all".
 */
export function FuelNightRecords({ rows, emptyText, headingId }: { rows: FuelRecordRow[]; emptyText: string; headingId: string }) {
  return (
    <BoundedTablePanel bound="fuel-bridge" heading="Deliveries and tank dips" headingId={headingId}>
      {rows.length === 0 ? (
        <p className="not-available-yet v69-chart-note" data-fuel-records-empty>
          {emptyText}
        </p>
      ) : rows.length <= RECORDS_SHOWN ? (
        <RecordTable rows={rows} headingId={headingId} />
      ) : (
        <>
          <RecordTable rows={rows.slice(0, RECORDS_SHOWN)} headingId={headingId} />
          <ShowAll summary={`Show all ${rows.length} records`} name="fuel-records">
            <RecordTable rows={rows.slice(RECORDS_SHOWN)} headingId={headingId} />
          </ShowAll>
        </>
      )}
    </BoundedTablePanel>
  );
}

function NightStatus({ night }: { night: FuelNightBody }) {
  return (
    <StatusBar label="Fuel balance" items data={{ "data-fuel-night-status": night.state }}>
      <span className="status-strip__item">
        <Badge tone="neutral" className={night.tone === "amber" ? "mini-tone--amber status-tone--amber" : "status-tone--neutral"}>
          {night.status}
        </Badge>
      </span>
      {fuelProvenanceChips(night.provenance).map((chip) => (
        <span className="status-strip__item" key={chip} data-mini-provenance>
          <Badge tone="neutral">{chip}</Badge>
        </span>
      ))}
      {night.notes.map((note) => (
        <span className="status-strip__item" key={note} data-fuel-night-note>
          {note}
        </span>
      ))}
    </StatusBar>
  );
}

function NightSelector({ nights, current, onPick }: { nights: FuelNightSummary[]; current: string; onPick: (night: string) => void }) {
  const index = nights.findIndex((n) => n.night_date === current);
  return (
    <nav aria-label="Nights" className="site-date-bar mini-period-bar" data-fuel-nights>
      <label className="v69-chip-field">
        Night{" "}
        <select className="v69-chip-control" value={current} onChange={(e) => onPick(e.target.value)}>
          {nights.map((n) => (
            <option key={n.night_date} value={n.night_date}>
              {`${n.label} · ${n.status}`}
            </option>
          ))}
        </select>
      </label>
      <button type="button" className="v69-chip-control" disabled={index <= 0} onClick={() => onPick(nights[index - 1].night_date)}>
        Previous night
      </button>
      <button
        type="button"
        className="v69-chip-control"
        disabled={index < 0 || index >= nights.length - 1}
        onClick={() => onPick(nights[index + 1].night_date)}
      >
        Next night
      </button>
    </nav>
  );
}

/**
 * "Finding for this night".
 *
 * MOCK DEVIATION MD-FUEL-K5-2 (DIESEL-1-R3l): in night mode this panel replaces v69's "Inspect existing generator fuel
 * interpretation" (index.html:629), which is about the dispatch consequence of a Kobo hour. Hour mode keeps v69's panel.
 */
function NightFindingPanel({ night }: { night: FuelNightBody }) {
  const linkFor = useLinkFor();
  const findingLink = night.finding ? linkFor({ kind: "FUEL_FINDING", site: night.site_code, id: night.finding.finding_id }) : null;
  return (
    <Panel heading="Finding for this night" headingId="fuel-night-finding-heading" className="mini-bound mini-max--fuel-interpretation">
      <div className="mini-scroll" tabIndex={0} role="group" aria-label="Panel content (scrolls)" data-fuel-night-finding>
        {night.finding ? (
          <>
            <p>
              {/* The shell's `linkFor` of the FUEL_FINDING Ref (`siteFuelFindingHref`), never a server path. */}
              {findingLink === null ? (
                night.finding.title
              ) : (
                <Link to={findingLink} data-fuel-night-finding-link>
                  {night.finding.title}
                </Link>
              )}
            </p>
            <p className="prose">{night.finding.text}</p>
          </>
        ) : (
          <p className="prose">{night.finding_note}</p>
        )}
      </div>
    </Panel>
  );
}

export function FuelNightView({ night }: { night: FuelNightBody }) {
  return (
    <>
      <NightStatus night={night} />
      <MetricCards label="Fuel balance summary" data={{ "data-mini-cards": "fuel-night" }} boundClass="mini-cards-bound mini-max--fuel-cards">
        {night.cards.map((card) => (
          <MetricCard key={card.key} label={card.label} value={card.value} word={card.word} note={card.note ?? undefined} data={{ "data-fuel-night-card": card.key }} />
        ))}
      </MetricCards>
      <Panel heading="Fuel balance at a glance" headingId="fuel-night-glance-heading" description="Opening + deliveries − use − closing">
        <ValueBars
          title="Fuel balance terms"
          items={night.bars.map((bar) => ({ key: bar.key, label: bar.label, value: bar.value_l, valueText: bar.text }))}
          unknownText={UNKNOWN}
        />
        <ChartNote data={{ "data-fuel-night-chart-note": "" }}>
          {CHART_SENTENCE}
          {night.margin === null ? null : ` ${night.margin}`}
        </ChartNote>
      </Panel>
      <FuelNightBridge rows={night.bridge} evidenceHref={night.links.evidence} headingId="fuel-night-bridge-heading" />
      <FuelNightRecords rows={night.records} emptyText={night.records_empty} headingId="fuel-night-records-heading" />
      <Notice data={{ "data-mini-notice": "fuel" }}>{FUEL_NOTICE}</Notice>
      {night.finding === undefined ? null : <NightFindingPanel night={night} />}
    </>
  );
}

/**
 * The nights list, when the Site has stored windows (`mode: "NIGHTS"`); "loading" while the read is in flight (PB-8: the
 * page shows its loading line, not hour mode); null for `NONE`, for a failed read and with no client, so the hour mode
 * renders exactly as before in each of those cases.
 */
export function useFuelNights(client: FuelBalanceClient | undefined, siteCode: string): FuelNightSummary[] | "loading" | null {
  const [state, setState] = useState<{ code: string; nights: FuelNightSummary[] | null } | null>(null);
  useEffect(() => {
    if (client === undefined) return undefined;
    let active = true;
    void client.getNights(siteCode).then((read) => {
      if (active) setState({ code: siteCode, nights: read.status === "loaded" && read.value.mode === "NIGHTS" ? read.value.nights : null });
    });
    return () => {
      active = false;
    };
  }, [client, siteCode]);
  if (client === undefined) return null;
  return state !== null && state.code === siteCode ? state.nights : "loading";
}

export function MiniFuelNightsPage({
  client,
  siteCode,
  nights,
}: {
  client: FuelBalanceClient;
  siteCode: string;
  nights: FuelNightSummary[];
}) {
  const [params, setParams] = useSearchParams();
  const asked = params.get("night");
  const latest = nights.length === 0 ? null : nights[nights.length - 1].night_date;
  const current = asked !== null && nights.some((n) => n.night_date === asked) ? asked : latest;
  const key = `${siteCode}|${current ?? ""}`;
  const night = useRead<FuelNightBody>(
    () => (current === null ? Promise.resolve({ status: "unavailable", message: null }) : client.getNight(siteCode, current)),
    key,
  );
  const pick = (next: string) => {
    const copy = new URLSearchParams(params);
    copy.set("night", next);
    setParams(copy);
  };
  return (
    <>
      {current === null ? null : <NightSelector nights={nights} current={current} onPick={pick} />}
      {night === null ? (
        <p role="status">{MINI_LOADING}</p>
      ) : night.status !== "loaded" ? (
        <p role="alert" data-fuel-night-unavailable>
          {night.message ?? MINI_UNAVAILABLE}
        </p>
      ) : (
        <FuelNightView night={night.value} />
      )}
    </>
  );
}
