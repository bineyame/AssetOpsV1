/**
 * The plain first layer of the Readiness view (V-01a round 3,
 * `D-2026-10-12-v01a-round3-readiness-and-organization`): four configuration
 * cards, the "Readiness and commissioning evidence" table and the bounded
 * gateway status panel.
 *
 * Every card and row is derived from the selected effective Foundation read:
 * its typed `configuration_gaps` codes, its role statuses and its
 * registrations. Green means configured for this Foundation version only. No
 * commissioning or field-confirmation record exists yet, so every row's
 * Confirmed column says "Not recorded". The gateway panel composes the S2
 * `gateway-health` read: central server contact checked now, on the server
 * clock, never device connection, accepted readings or equipment condition.
 */

import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Badge, DataTable, Disclosure, Fact, FactList, MissingClaim, Panel, type BadgeTone } from "../ui";
import type { EvidenceRead } from "./evidenceRead";
import { formatInstant } from "./FoundationRevisionPanel";
import type { GatewayHealth, GatewayHealthClient, GatewayHealthEntry } from "./gatewayHealthClient";
import type { FoundationGap, FoundationReadModel } from "./siteFoundationClient";

export const READINESS_TABLE_HEADING_ID = "foundation-readiness-table-heading";
export const READINESS_GATEWAY_HEADING_ID = "foundation-readiness-gateway-heading";

/* Cards ---------------------------------------------------------------------- */

export type CardState = "CONFIGURED" | "NEEDS_CONFIGURATION" | "UNKNOWN";

export interface ReadinessCard {
  key: "definition" | "topology" | "specifications" | "controls";
  label: string;
  state: CardState;
  note: string;
  gaps: FoundationGap[];
}

const CARD_WORD: Record<CardState, string> = {
  CONFIGURED: "Configured",
  NEEDS_CONFIGURATION: "Needs configuration",
  UNKNOWN: "Unknown",
};

const CARD_TONE: Record<CardState, BadgeTone> = {
  CONFIGURED: "configured",
  NEEDS_CONFIGURATION: "config-gap",
  UNKNOWN: "neutral",
};

const DEFINITION_CODES = ["SITE_CODE_INVALID", "SITE_NAME_MISSING", "SITE_TYPE_UNSUPPORTED", "SITE_TIMEZONE_INVALID"];
const TOPOLOGY_CODES = ["COMPONENT_MISSING", "TOPOLOGY_MISSING", "TOPOLOGY_REFERENCE_BROKEN", "AC_BUS_PATH_MISSING"];
const SPECIFICATION_CODES = ["COMPONENT_RATING_MISSING"];
const CONTROL_CODES = ["BATTERY_RESERVE_MISSING", "SITE_CONTROL_MISSING"];
const REGISTRATION_CODES = ["GATEWAY_NOT_REGISTERED", "SOURCE_NOT_REGISTERED"];

function gapsOf(foundation: FoundationReadModel, codes: string[]): FoundationGap[] {
  return foundation.configuration_gaps.filter((gap) => codes.includes(gap.code));
}

/** True when the selected effective Foundation version cannot be resolved. */
function basisUnresolved(foundation: FoundationReadModel): boolean {
  return foundation.configuration_gaps.some((gap) => gap.code === "NO_EFFECTIVE_REVISION");
}

/** The four category cards, from the typed gap codes of the selected version. */
export function readinessCards(foundation: FoundationReadModel): ReadinessCard[] {
  const unknown = basisUnresolved(foundation);
  const card = (
    key: ReadinessCard["key"],
    label: string,
    codes: string[],
    green: string,
    amber: string,
  ): ReadinessCard => {
    const gaps = gapsOf(foundation, codes);
    const state: CardState = unknown ? "UNKNOWN" : gaps.length === 0 ? "CONFIGURED" : "NEEDS_CONFIGURATION";
    const note =
      state === "UNKNOWN"
        ? "No effective Foundation version resolves for the period shown."
        : state === "CONFIGURED"
          ? green
          : `${amber}. ${gaps.length === 1 ? "One gap is" : `${gaps.length} gaps are`} named in the table below.`;
    return { key, label, state, note, gaps };
  };
  return [
    card(
      "definition",
      "Definition",
      DEFINITION_CODES,
      "Site code, name, supported type and time zone are declared.",
      "Site definition needs configuration",
    ),
    card(
      "topology",
      "Topology",
      TOPOLOGY_CODES,
      "Required components are declared and connected to the AC bus. Bindings and registration are shown separately.",
      "Topology needs configuration",
    ),
    card(
      "specifications",
      "Specifications",
      SPECIFICATION_CODES,
      "Required ratings are declared, not field-verified.",
      "Required ratings missing",
    ),
    card(
      "controls",
      "Controls",
      CONTROL_CODES,
      "Reserve and required Site Controls are configured. Configuration, not operating results.",
      "Controls need configuration",
    ),
  ];
}

export function ReadinessCards({ foundation }: { foundation: FoundationReadModel }) {
  return (
    <ul className="readiness-cards" aria-label="Configuration by category" data-readiness-cards="">
      {readinessCards(foundation).map((card) => (
        <li
          key={card.key}
          className={`readiness-card readiness-card--${card.state.toLowerCase()}`}
          data-readiness-card={card.key}
          data-card-state={card.state}
        >
          <span className="readiness-card__label">{card.label}</span>
          <span className="readiness-card__value">
            <Badge tone={CARD_TONE[card.state]}>{CARD_WORD[card.state]}</Badge>
          </span>
          <span className="readiness-card__note">{card.note}</span>
        </li>
      ))}
    </ul>
  );
}

/* Readiness and commissioning evidence --------------------------------------- */

export const NOT_RECORDED = "Not recorded";
export const COMMISSIONING_NOT_RECORDED = "Commissioning confirmation not recorded";

interface EvidenceRow {
  key: string;
  area: string;
  declared: ReactNode;
  needed: string[];
  next: ReactNode;
}

function controlsDeclared(foundation: FoundationReadModel): string {
  const reserve = foundation.controls.battery_reserve;
  const parts: string[] = [];
  parts.push(
    reserve.value === undefined ? "No reserve declared" : `Reserve ${reserve.value}${reserve.unit === "%" ? "%" : ` ${reserve.unit ?? ""}`}`,
  );
  const priorities = [foundation.controls.source_priority, foundation.controls.critical_load_priority];
  const declared = priorities.filter((control) => control.members !== undefined && control.members.length > 0).length;
  parts.push(
    declared === priorities.length
      ? "priorities declared"
      : declared === 0
        ? "no priorities declared"
        : "one of two priorities declared",
  );
  return parts.join("; ");
}

function rows(
  foundation: FoundationReadModel,
  links: { model: string; sld: string; evidence: string },
  onReviewBindings: () => void,
): EvidenceRow[] {
  const messages = (codes: string[]) => gapsOf(foundation, codes).map((gap) => gap.message);
  const { readiness, revision } = foundation;
  const required = readiness.roles.filter((role) => role.required);
  const configured = required.filter((role) => role.status === "CONFIGURED").length;
  const missingRoles = required.filter((role) => role.status !== "CONFIGURED").map((role) => role.label);
  const componentCount = foundation.detail.foundation.components.length;
  const topologyGaps = messages(TOPOLOGY_CODES);
  const ratingGaps = messages(SPECIFICATION_CODES);
  const registeredGateways = foundation.gateways.length;
  const site = foundation.site;
  return [
    {
      key: "definition",
      area: "Site definition",
      declared: `Foundation v${revision.version} published · ${site.site_code} · ${site.site_type} · ${site.timezone}`,
      needed: messages(DEFINITION_CODES),
      next: <Link to={links.model}>Site model →</Link>,
    },
    {
      key: "topology",
      area: "Topology and ratings",
      declared: [
        `${componentCount} component${componentCount === 1 ? "" : "s"}`,
        topologyGaps.length === 0 ? "AC bus connected" : "topology incomplete",
        ratingGaps.length === 0 ? "Required ratings declared" : "some required ratings missing",
      ].join("; "),
      needed: [...topologyGaps, ...ratingGaps],
      next: <Link to={links.sld}>Single line diagram →</Link>,
    },
    {
      key: "controls",
      area: "Controls",
      declared: controlsDeclared(foundation),
      needed: messages(CONTROL_CODES),
      next: <Link to={links.model}>Site model controls →</Link>,
    },
    {
      key: "roles",
      area: "Required role bindings",
      declared:
        foundation.bindings.binding_set === null
          ? `No binding set in effect; ${configured} of ${required.length} required roles configured`
          : `Binding v${foundation.bindings.binding_set.version}; ${configured} of ${required.length} required roles configured`,
      needed: missingRoles.length === 0 ? [] : [`Not configured: ${missingRoles.join(", ")}.`],
      next: (
        <button type="button" className="link-button" data-review-bindings="" onClick={onReviewBindings}>
          Review or change bindings
        </button>
      ),
    },
    {
      key: "gateway",
      area: "Gateway registration",
      declared:
        registeredGateways === 0
          ? "No gateway registered"
          : `Gateway registered (${foundation.gateways.map((g) => g.gateway_external_id).join(", ")}); ${foundation.sources.length} source${foundation.sources.length === 1 ? "" : "s"} registered`,
      needed: messages(REGISTRATION_CODES),
      next: <Link to={links.evidence}>Site Evidence →</Link>,
    },
    {
      key: "commissioning",
      area: "Commissioning",
      declared: (
        <MissingClaim gapId="G-readiness-commissioning" placement="readiness.commissioning.declared">
          No commissioning record type exists in this Foundation
        </MissingClaim>
      ),
      needed: [],
      next: (
        <span data-next-step="none">
          <MissingClaim gapId="G-readiness-commissioning" placement="readiness.commissioning.next-step">
            No commissioning record available
          </MissingClaim>
        </span>
      ),
    },
  ];
}

export interface ReadinessEvidenceTableProps {
  foundation: FoundationReadModel;
  links: { model: string; sld: string; evidence: string };
  onReviewBindings: () => void;
}

export function ReadinessEvidenceTable({ foundation, links, onReviewBindings }: ReadinessEvidenceTableProps) {
  return (
    <Panel
      heading="Readiness and commissioning evidence"
      headingId={READINESS_TABLE_HEADING_ID}
      description={
        <>
          Declared means published in the selected Foundation version.{" "}
          <MissingClaim gapId="G-readiness-commissioning" placement="readiness.commissioning.definition">
            Confirmed means an independent commissioning or field record; none exists yet.
          </MissingClaim>
        </>
      }
    >
      <DataTable labelledBy={READINESS_TABLE_HEADING_ID}>
        <thead>
          <tr>
            <th scope="col">Area</th>
            <th scope="col">Declared</th>
            <th scope="col">Confirmed</th>
            <th scope="col">What is needed</th>
            <th scope="col">Next step</th>
          </tr>
        </thead>
        <tbody>
          {rows(foundation, links, onReviewBindings).map((row) => (
            <tr key={row.key} data-readiness-row={row.key}>
              <th scope="row">{row.area}</th>
              <td>{row.declared}</td>
              <td data-confirmed="not-recorded">
                <MissingClaim gapId="G-readiness-commissioning" placement="readiness.commissioning.confirmed">
                  <Badge tone="neutral">{NOT_RECORDED}</Badge>
                </MissingClaim>
              </td>
              <td>
                <ul className="plain-list">
                  {row.needed.map((text) => (
                    <li key={text}>{text}</li>
                  ))}
                  <MissingClaim
                    as="li"
                    className="muted"
                    gapId="G-readiness-commissioning"
                    placement="readiness.commissioning.needed"
                  >
                    {COMMISSIONING_NOT_RECORDED}
                  </MissingClaim>
                </ul>
              </td>
              <td>{row.next}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

/* Gateway status --------------------------------------------------------------- */

/*
 * G-02 (Architect C5): uptime trend, expected-versus-delivered completeness and
 * signal strength are separate claims with different producers and closure
 * conditions, so each is its own catalogued line, like firmware.
 */
export const GATEWAY_UPTIME_NOT_AVAILABLE_YET =
  "Uptime trend not available yet: no reviewed source reports a gateway's uptime over time.";
export const GATEWAY_COMPLETENESS_NOT_AVAILABLE_YET =
  "Expected-versus-delivered completeness not available yet: no reviewed source compares the reports a gateway should send with those received.";
export const GATEWAY_SIGNAL_NOT_AVAILABLE_YET =
  "Signal strength not available yet: no reviewed source reports a gateway's signal strength.";
/** Catalogued as G-readiness-gateway-firmware: no producer, edge field or read carries a firmware report. */
export const GATEWAY_FIRMWARE_NOT_AVAILABLE_YET =
  "Firmware not available yet: no reviewed source reports what firmware a gateway runs.";
export const DEVICE_CONNECTION_NOT_ESTABLISHED = "Device connection not established here.";
export const GATEWAY_CONTACT_UNAVAILABLE = "Gateway contact unavailable";
export const GATEWAY_CONTACT_UNKNOWN = "Contact unknown — no central diagnostic received";

const CONTACT_WORD: Record<string, string> = { CURRENT: "Current", STALE: "Stale", UNKNOWN: "Unknown" };

function contactSentence(entry: GatewayHealthEntry): string {
  const cadence =
    entry.declared_cadence_seconds === null
      ? "no declared reporting cadence"
      : `a declared cadence of ${entry.declared_cadence_seconds} s`;
  if (entry.status === "CURRENT") {
    return `A gateway diagnostic reached the server within two reporting intervals (${cadence}). This is not a live device connection, accepted readings or equipment condition.`;
  }
  if (entry.status === "STALE") {
    return `The last gateway diagnostic reached the server longer ago than two reporting intervals (${cadence}).`;
  }
  return `${GATEWAY_CONTACT_UNKNOWN}.`;
}

function GatewayEntry({ entry, foundation }: { entry: GatewayHealthEntry; foundation: FoundationReadModel }) {
  const sources = entry.source_contacts.length;
  const disabled = entry.registration === "DISABLED";
  return (
    <div className="gateway-entry" data-gateway-status={entry.status} data-gateway-registration={entry.registration}>
      <dl className="gateway-facts">
        <div>
          <dt>Registered gateway</dt>
          <dd>
            <code>{entry.gateway_external_id}</code>
          </dd>
        </div>
        <div>
          <dt>Registration</dt>
          <dd>{disabled ? "Disabled — switched off for this Site" : "Enabled"}</dd>
        </div>
        <div>
          <dt>Central contact</dt>
          <dd>
            <Badge tone="neutral">{CONTACT_WORD[entry.status] ?? entry.status}</Badge>
          </dd>
        </div>
        <div>
          <dt>Last server contact (server clock)</dt>
          <dd>{entry.last_server_contact === null ? "None received" : formatInstant(entry.last_server_contact)}</dd>
        </div>
      </dl>
      <p data-gateway-contact-sentence="">{contactSentence(entry)}</p>
      <p data-gateway-sources="">
        {sources === 0
          ? "No source is registered behind this gateway."
          : `${sources} source${sources === 1 ? "" : "s"} registered behind this gateway.`}{" "}
        <MissingClaim gapId="G-readiness-source-contact" placement="readiness.gateway.source-connection">
          {DEVICE_CONNECTION_NOT_ESTABLISHED}
        </MissingClaim>
      </p>
      <Disclosure
        name={`gateway-diagnostic-${entry.gateway_external_id}`}
        summary="Advanced details — gateway diagnostic records"
      >
        <FactList>
          <Fact term="Gateway registration ID">
            <code>{entry.gateway_id}</code>
          </Fact>
          <Fact term="Status basis">{`${entry.status_basis}: server receive time against twice the declared cadence`}</Fact>
          <Fact term="Declared cadence">
            {entry.declared_cadence_seconds === null ? "Not declared" : `${entry.declared_cadence_seconds} s`}
          </Fact>
          <Fact term="Diagnostic record ID">{entry.diagnostic_id === null ? "None" : <code>{entry.diagnostic_id}</code>}</Fact>
          <Fact term="Time stated by the gateway (its own clock)">
            {entry.gateway_observed_at === null ? "Unknown" : `${formatInstant(entry.gateway_observed_at)} (${entry.observed_at_clock})`}
          </Fact>
          <Fact term="Gateway clock difference (reported)">
            {entry.clock_offset_ms === null ? "Unknown" : `${entry.clock_offset_ms} ms`}
          </Fact>
          <Fact term="Readings waiting at the gateway (reported)">
            {entry.queue_count === null
              ? "Unknown"
              : `${entry.queue_count}${entry.oldest_queue_age_seconds === null ? "" : `, oldest waiting ${entry.oldest_queue_age_seconds} s`}`}
          </Fact>
          <Fact term="Storage pressure (reported)">
            {entry.disk_pressure === null ? "Unknown" : `${entry.disk_pressure} (${entry.disk_pressure_provenance ?? "as reported"})`}
          </Fact>
          <Fact term="Readings not matched to an input (reported)">
            {entry.mapping_error_count === null ? "Unknown" : entry.mapping_error_count}
          </Fact>
          <Fact term="Last report per source (gateway-reported, not proof of a connected device)">
            {entry.source_contacts.length === 0
              ? "None registered"
              : entry.source_contacts.map((c) => (
                  <span key={c.source_id} data-gateway-source={c.source_id}>
                    <code>{c.source_external_id}</code>
                    {`: ${c.last_contact === null ? "no report" : formatInstant(c.last_contact)}${c.registration === "DISABLED" ? " (switched off)" : ""}. `}
                  </span>
                ))}
          </Fact>
        </FactList>
        <p className="muted">
          Configuration snapshot of this period: {foundation.gateways.length} gateway(s) and {foundation.sources.length}{" "}
          source(s) registered in Foundation v{foundation.revision.version}.
        </p>
      </Disclosure>
    </div>
  );
}

export interface GatewayStatusPanelProps {
  foundation: FoundationReadModel;
  siteId: string;
  gatewayHealth: GatewayHealthClient | undefined;
  evidenceHref: string;
}

/**
 * Registration and central contact, kept apart. Contact is checked now on the
 * server clock; it is never back-dated into the Foundation period shown.
 */
export function GatewayStatusPanel({ foundation, siteId, gatewayHealth, evidenceHref }: GatewayStatusPanelProps) {
  const [health, setHealth] = useState<EvidenceRead<GatewayHealth> | null>(null);
  useEffect(() => {
    if (gatewayHealth === undefined) {
      setHealth({ status: "unavailable", message: null });
      return undefined;
    }
    let active = true;
    setHealth(null);
    void gatewayHealth.getGatewayHealth(siteId).then((loaded) => {
      if (active) setHealth(loaded);
    });
    return () => {
      active = false;
    };
  }, [gatewayHealth, siteId]);

  const period = foundation.revision.period_state;
  const periodNote =
    period === "CURRENT"
      ? `The period shown is Foundation v${foundation.revision.version}, the configuration in effect now. Gateway contact below is a separate check made now on the server clock.`
      : `The period shown is ${period === "PAST" ? "a past" : "a scheduled"} Foundation period (v${foundation.revision.version}, ${formatInstant(foundation.revision.valid_from)} to ${formatInstant(foundation.revision.valid_to)}). Gateway contact below is checked now on the server clock; it did not occur in that period.`;

  let body: ReactNode;
  if (health === null) {
    body = <p>Loading the site&apos;s gateway contact.</p>;
  } else if (health.status !== "loaded") {
    body = (
      <div data-gateway-panel-state="unavailable">
        <p>
          <strong>{GATEWAY_CONTACT_UNAVAILABLE}.</strong>{" "}
          {health.status === "not_found"
            ? "The gateway contact read has no record for this Site."
            : "The gateway contact read did not succeed."}{" "}
          Registration is configuration and is not taken as contact.
        </p>
        <RegistrationOnly foundation={foundation} />
      </div>
    );
  } else if (health.value.gateways.length === 0) {
    body = (
      <div data-gateway-panel-state="none">
        <p>No gateway is registered for this Site, so there is no central contact to report.</p>
      </div>
    );
  } else {
    body = (
      <div data-gateway-panel-state="loaded">
        <p className="muted" data-gateway-read-at="">
          Read at {formatInstant(health.value.read_at)} (server clock).
        </p>
        {health.value.gateways.map((entry) => (
          <GatewayEntry key={entry.gateway_id} entry={entry} foundation={foundation} />
        ))}
      </div>
    );
  }

  return (
    <Panel
      heading="Gateway status"
      headingId={READINESS_GATEWAY_HEADING_ID}
      description={
        <>
          Registration and central server contact only. <Link to={evidenceHref}>Site Evidence →</Link>
        </>
      }
    >
      <p className="notice" data-gateway-period-note={period}>
        {periodNote}
      </p>
      {body}
      <MissingClaim
        as="p"
        className="not-available-yet"
        gapId="G-readiness-gateway-uptime"
        placement="readiness.gateway.uptime"
      >
        {GATEWAY_UPTIME_NOT_AVAILABLE_YET}
      </MissingClaim>
      <MissingClaim
        as="p"
        className="not-available-yet"
        gapId="G-readiness-gateway-completeness"
        placement="readiness.gateway.completeness"
      >
        {GATEWAY_COMPLETENESS_NOT_AVAILABLE_YET}
      </MissingClaim>
      <MissingClaim
        as="p"
        className="not-available-yet"
        gapId="G-readiness-gateway-signal-strength"
        placement="readiness.gateway.signal-strength"
      >
        {GATEWAY_SIGNAL_NOT_AVAILABLE_YET}
      </MissingClaim>
      <MissingClaim
        as="p"
        className="not-available-yet"
        gapId="G-readiness-gateway-firmware"
        placement="readiness.gateway.firmware"
      >
        {GATEWAY_FIRMWARE_NOT_AVAILABLE_YET}
      </MissingClaim>
    </Panel>
  );
}

/** Registration from the selected Foundation read, with no contact claim. */
function RegistrationOnly({ foundation }: { foundation: FoundationReadModel }) {
  if (foundation.gateways.length === 0) return <p>No gateway is registered in this Foundation period.</p>;
  return (
    <p data-gateway-sources="">
      Registered: {foundation.gateways.map((g) => g.gateway_external_id).join(", ")}, with {foundation.sources.length}{" "}
      source{foundation.sources.length === 1 ? "" : "s"}.{" "}
      <MissingClaim gapId="G-readiness-source-contact" placement="readiness.gateway.source-connection-registration">
        {DEVICE_CONNECTION_NOT_ESTABLISHED}
      </MissingClaim>
    </p>
  );
}
