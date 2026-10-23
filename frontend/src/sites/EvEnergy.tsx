/**
 * W5-03a E3: the EV Site Energy page body (v6.9 `energy`), from the selected `/ev/energy` depth read
 * (`.agent/W5-03-build-spec.md` literal ledger, E3 card, closure 2 and the W5-03a pre-flight E3 ruling).
 *
 * Complete metered energy, partial energy and the gross tariff consequence stay separate; an observed peak below the
 * declared limit never exonerates the limit, and an unpriced consequence is never zero or cash.
 * MOCK DEVIATION (D4) R47/R48/R50/R52-R55: status text, card notes, basis badge, conclusion note, bridge rows and
 * chart axes keep the mock forms with selected values or honest fallbacks. MOCK DEVIATION (D2) R46/R49: the
 * `Measure`/`Value` detail disclosure and the partial/unknown coverage lines. MOCK DEVIATION (D1) R06/R51: unconnected
 * sample marks; `Stationary battery` is `Unknown` with the Foundation limitation.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, DataTable, KeyValues, MetricCard, MetricCards, Notice, Panel, StatusBar } from "../ui";
import { Disclosure } from "../ui/Disclosure";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";
import { coldWindowSearch } from "./coldAssessmentClient";
import { EvDepthRefusal, type EvDepthRoutes, hoursText, instantMs } from "./EvAvailability";
import { type EvConsequence, type EvDepthClient, type EvEnergyRead, depthStateNotice, durationText } from "./evDepthClient";
import { EvDepthPowerChart } from "./evDepthGraphics";

export const ENERGY_LOADING = "Loading the site's charging energy.";
export const ENERGY_EMPTY_SAMPLES = "No accepted site-import samples in this window.";
export const ENERGY_EMPTY = "No complete metered delivery is established for this window.";
export const IMPORT_NOTE = "Observed import is not proof of vehicle-requested power";
export const BATTERY_LIMITATION = "Battery configuration is not established by this Foundation.";
const TABLE_ID = "ev-energy-bridge-heading";
const DETAIL_ID = "ev-energy-detail-heading";

/* ---------- formats ---------- */

const kw = (value: string | null) => (value === null ? "Unknown" : `${value} kW`);
const kwh = (value: string | null) => (value === null ? "Unknown" : `${value} kWh`);
const pad = (n: number) => String(n).padStart(2, "0");

/** Closure 2: `HH:MM:SS UTC` of a wire instant, else `Unknown`. */
export function utcSeconds(value: string | null): string {
  if (value === null) return "Unknown";
  const d = new Date(instantMs(value));
  return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`;
}

const estimated = (c: EvConsequence | null): c is EvConsequence => c !== null && c.state === "ESTIMATED";

/** Closure 2: the `Gross tariff estimate` card value. */
export function grossTariffText(c: EvConsequence | null): string {
  if (c === null) return "Unknown";
  return estimated(c) ? `${c.amount ?? "Unknown"} ${c.currency ?? ""}`.trim() : "Unpriced";
}

/** Closure 2: measured basis iff complete metered energy exists and meter coverage is fully known. */
export function measuredBasis(read: EvEnergyRead): boolean {
  return read.energy.metered_complete_kwh !== null && read.energy.unknown_seconds === 0;
}

export function bridgeRows(read: EvEnergyRead): string[][] {
  const e = read.energy;
  const c = e.consequence;
  const first =
    c === null
      ? [e.metered_complete_kwh === null ? "Unknown" : `${e.metered_complete_kwh} kWh complete-record delivery`, "No eligible gross tariff scenario.", "Unpriced", "No collections or profit claim"]
      : [
          c.quantity_kwh === null ? "Unknown" : `${c.quantity_kwh} kWh complete-record delivery`,
          estimated(c) ? `${c.tariff_value ?? "Unknown"} ${c.currency ?? ""}/kWh gross tariff scenario`.replace(" /kWh", "/kWh") : "No eligible tariff applied",
          estimated(c) ? `${c.amount ?? "Unknown"} ${c.currency ?? ""} gross estimate`.replace("  ", " ") : "Unpriced",
          c.limitation ?? "No collections or profit claim",
        ];
  const partial = e.partial_kwh !== null && Number(e.partial_kwh) > 0;
  const second = partial
    ? [`${e.partial_kwh} kWh incomplete-session delivery`, "No complete meter interval", "Not priced", "No extrapolated energy silently added"]
    : ["Incomplete session", "No complete meter interval", "Unavailable", "No extrapolated energy silently added"];
  return [first, second, ["Interrupted service", "No demand/sales baseline", "Unpriced exposure", "No invented lost revenue"]];
}

/* ---------- read ---------- */

function useEnergyRead(client: EvDepthClient, siteCode: string, window: ColdWindowQuery, attempt: number) {
  const key = `${siteCode}|${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}|${attempt}`;
  const [state, setState] = useState<{ key: string; value: ColdRead<EvEnergyRead> } | null>(null);
  useEffect(() => {
    let active = true;
    void client.getEnergy(siteCode, window).then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
    // The key names exactly what is read.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state !== null && state.key === key ? state.value : null;
}

function answerTone(word: string): string | undefined {
  return word === "Yes" ? "ev-tone--green" : word === "Not established" || word === "No" ? "ev-tone--amber" : undefined;
}

function Answer({ word }: { word: string }) {
  const tone = answerTone(word);
  return <Badge tone="neutral" className={tone}>{word}</Badge>;
}

function EnergyBody({ read, routes }: { read: EvEnergyRead; routes: EvDepthRoutes }) {
  const e = read.energy;
  const c = e.consequence;
  const state = read.selection.state;
  const notice = depthStateNotice(state);
  const query = coldWindowSearch(read.window);
  const measured = measuredBasis(read);
  const from = read.window.from;
  const to = read.window.to;
  const windowNote = from === null || to === null ? "No selected window" : `Selected ${hoursText((instantMs(to) - instantMs(from)) / 1000)}-hour window`;
  const below = e.peak_below_limit === "YES" ? "Yes" : e.peak_below_limit === "NO" ? "No" : "Unknown";
  const disclosures: string[] = [];
  if (e.partial_kwh !== null && Number(e.partial_kwh) > 0) disclosures.push(`${e.partial_kwh} kWh from incomplete sessions is shown separately and not included.`);
  if (e.unknown_seconds === null) disclosures.push("Meter coverage cannot be calculated for this window.");
  else if (e.unknown_seconds > 0) disclosures.push(`Meter coverage is unknown for ${durationText(e.unknown_seconds)} of session time.`);
  return (
    <>
      <StatusBar
        label="Charging energy"
        action={
          <Link to={`${routes.analysis}${query}`} data-ev-meter-basis="">
            Inspect meter basis ↗
          </Link>
        }
      >
        <Badge tone="neutral" className={measured ? "ev-depth-badge--blue" : "ev-tone--amber"}>
          {measured ? "Energy basis: measured" : "Energy basis: limited"}
        </Badge>{" "}
        <span className="muted" data-ev-energy-status="">
          {measured
            ? "Complete session meter records · incomplete session energy excluded"
            : "Complete session meter records not established · incomplete session energy kept separate"}
        </span>
      </StatusBar>
      {notice === null ? null : <Notice data={{ "data-ev-depth-state-notice": state }}>{notice}</Notice>}
      <MetricCards label="Charging energy">
        <MetricCard label="Metered session energy" value={kwh(e.metered_complete_kwh)} note="Complete metered sessions only" data={{ "data-ev-energy-card": "energy" }} />
        <MetricCard label="Observed peak import" value={kw(e.observed_peak_import_kw)} note={windowNote} data={{ "data-ev-energy-card": "peak" }} />
        <MetricCard
          label="Declared site limit"
          value={kw(e.configured_import_limit_kw)}
          note={e.configured_import_limit_kw === null ? "No time-valid site limit declared" : "Time-valid configuration"}
          data={{ "data-ev-energy-card": "limit" }}
        />
        <MetricCard
          label="Gross tariff estimate"
          value={grossTariffText(c)}
          note={estimated(c) ? `Scenario tariff: ${c.tariff_value ?? "Unknown"} ${c.currency ?? ""}/kWh`.replace(" /kWh", "/kWh") : "Scenario tariff not established"}
          data={{ "data-ev-energy-card": "tariff" }}
        />
      </MetricCards>
      {disclosures.map((line) => (
        <p key={line} className="prose" data-ev-energy-disclosure="">
          {line}
        </p>
      ))}
      {e.metered_complete_kwh === null ? (
        <p className="not-available-yet" data-ev-energy-empty="">
          {ENERGY_EMPTY}
        </p>
      ) : null}
      <div className="panel-pair">
        <Panel heading="Import power and configured limit" headingId="ev-energy-import-heading">
          <EvDepthPowerChart from={from} to={to} samples={e.import_samples} limitKw={e.configured_import_limit_kw} />
          {e.import_samples.length === 0 ? (
            <p className="not-available-yet" data-ev-samples-empty="">
              {ENERGY_EMPTY_SAMPLES}
            </p>
          ) : null}
          <p className="chart-note" data-ev-import-note="">
            {IMPORT_NOTE}
          </p>
          <Disclosure summary="Measure and value detail" name="ev-energy-detail" variant="tech">
            <h3 id={DETAIL_ID} className="visually-hidden">
              Import measures
            </h3>
            <DataTable labelledBy={DETAIL_ID} stickyFirstColumn>
              <thead>
                <tr>
                  <th scope="col">Measure</th>
                  <th scope="col">Value</th>
                </tr>
              </thead>
              <tbody>
                <tr data-ev-measure="count">
                  <th scope="row">Accepted import samples</th>
                  <td>{String(e.import_sample_count)}</td>
                </tr>
                <tr data-ev-measure="peak">
                  <th scope="row">Observed peak import (sample peak)</th>
                  <td>{kw(e.observed_peak_import_kw)}</td>
                </tr>
                <tr data-ev-measure="peak-time">
                  <th scope="row">Peak sample time (UTC)</th>
                  <td>{utcSeconds(e.peak_sample_at)}</td>
                </tr>
                <tr data-ev-measure="limit">
                  <th scope="row">Declared site limit</th>
                  <td>{kw(e.configured_import_limit_kw)}</td>
                </tr>
                {e.import_samples.map((s) => (
                  <tr key={s.evidence_id} data-ev-measure="sample">
                    <th scope="row">{`Sample ${utcSeconds(s.source_time)}`}</th>
                    <td>{`${s.import_kw} kW`}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </Disclosure>
        </Panel>
        <Panel heading="What can be concluded" headingId="ev-energy-conclude-heading">
          <KeyValues
            label="What can be concluded"
            rows={[
              ["Observed peak below limit", <Answer word={below} />, "below"],
              ["Site limit caused interruption", <Answer word="Not established" />, "interruption"],
              ["Requested vehicle power", "Incomplete evidence", "requested"],
              [
                "Stationary battery",
                <>
                  Unknown <small className="muted">{BATTERY_LIMITATION}</small>
                </>,
                "battery",
              ],
              ["Billing settlement", "Not connected", "billing"],
            ]}
          />
          <p className="chart-note" data-ev-conclusion-note="">
            {estimated(c)
              ? "Revenue is an estimate from metered kWh and the declared tariff, not payment evidence."
              : "No eligible revenue estimate is established; no payment evidence is connected"}
          </p>
        </Panel>
      </div>
      <Panel heading="Technical-to-financial bridge" headingId={TABLE_ID}>
        <DataTable labelledBy={TABLE_ID} stickyFirstColumn>
          <thead>
            <tr>
              {["Quantity", "Assumption", "Result", "Limit"].map((h) => (
                <th key={h} scope="col">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bridgeRows(read).map((row, index) => (
              <tr key={index} data-ev-bridge-row={index + 1}>
                {row.map((cell, i) => (i === 0 ? <th key={i} scope="row">{cell}</th> : <td key={i}>{cell}</td>))}
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
    </>
  );
}

export interface EvEnergyProps {
  /** The imported Site code (the shell Site token), never the internal UUID. */
  siteCode: string;
  window: ColdWindowQuery;
  client: EvDepthClient;
  routes: EvDepthRoutes;
}

export function EvEnergy({ siteCode, window, client, routes }: EvEnergyProps) {
  const [attempt, setAttempt] = useState(0);
  const read = useEnergyRead(client, siteCode, window, attempt);
  if (read === null) return <p className="prose">{ENERGY_LOADING}</p>;
  if (read.status !== "loaded") return <EvDepthRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />;
  return <EnergyBody read={read.value} routes={routes} />;
}
