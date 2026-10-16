/**
 * S7-01b battery boundary (`asset:3#a`) over S7-01a's asset-boundary read.
 * Layout follows v69 `#/asset`; content is limited to what the read supports:
 * physical condition is Unknown with its named missing inputs (or Unknown, not
 * configured). The declared rating and the connected state-of-charge channel
 * are shown under their own labels and are never condition evidence.
 * Degradation, remaining life, warranty and replacement are withheld.
 *
 * The page is addressed by the configured asset ID in the effective Site
 * configuration; an ID outside it is a typed refusal, never a row.
 */
import { useEffect } from "react";
import { Link } from "react-router-dom";

import { siteAssetHref, siteHealthHref } from "../shell/operatorSiteRoutes";
import { Badge, DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import type { BatteryDetail, HealthClient } from "./healthClient";
import { BATTERY_TEXTS, HealthRef, HealthRefusalPanel, useHealthRead } from "./SiteHealth";

const MISSING_INPUT_WORDS: Record<string, { name: string; why: string }> = {
  ACCEPTED_BATTERY_TEMPERATURE_HISTORY: {
    name: "Temperature history",
    why: "No battery temperature signal is connected, so there is no accepted temperature history.",
  },
  ACCEPTED_MEASURED_CAPACITY: {
    name: "Measured usable capacity",
    why: "No capacity test or measured usable capacity is recorded. The declared rating is not a measurement.",
  },
  ACCEPTED_CYCLE_STRESS_HISTORY: {
    name: "Charge and discharge stress history",
    why: "No reviewed rule turns accepted charge and discharge history into a stress measure.",
  },
};

const WITHHELD_WORDS: Record<string, string> = {
  DEGRADATION: "degradation",
  REMAINING_LIFE: "remaining life",
  STRESS_SCORE: "stress score",
  WARRANTY_EXPOSURE: "warranty exposure",
  REPLACEMENT_EXPOSURE: "replacement exposure",
  DIAGNOSIS: "diagnosis",
};

const CONDITION_REASON_WORDS: Record<string, string> = {
  NO_REVIEWED_CAUSAL_BATTERY_RULE: "the inputs needed to judge it are missing",
  UNBOUND: "no signal channel is connected to this battery, and the inputs needed to judge it are missing",
  NO_BINDING_SET: "the site's signal channels are not set up yet, and the inputs needed to judge it are missing",
  NOT_CONFIGURED: "no battery is configured",
};

const DETAIL_TEXTS: Record<string, string> = {
  ...BATTERY_TEXTS,
  ASSET_NOT_IN_EFFECTIVE_BASIS:
    "That asset is not a battery in this site's current configuration, so nothing is shown for it.",
  INVALID_ASSET_ID: "That address does not name an asset.",
};

function sentence(items: string[]): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

/** `/sites/{site}/assets`: the configured battery, or Unknown (not configured) with no asset ID. */
export function SiteBatteryEntry({ siteId, client }: { siteId: string; client: HealthClient }) {
  const read = useHealthRead(() => client.getBatteryEntry(siteId), `battery:${siteId}`);
  if (read === null) {
    return <p>Loading the site's battery.</p>;
  }
  if (read.status === "refused") {
    return (
      <HealthRefusalPanel refusal={read} subject="Battery" headingId="site-battery-refused-heading" texts={BATTERY_TEXTS} />
    );
  }
  const entry = read.value;
  if (entry.configuration === "NOT_CONFIGURED") {
    return (
      <div className="site-battery" data-battery-configuration="NOT_CONFIGURED">
        <div className="evidence-statusbar">
          <Badge tone="neutral">Condition: Unknown</Badge>
          <span className="evidence-statusbar__facts">No battery is configured for this site</span>
        </div>
        <Panel heading="No battery configured" headingId="site-battery-none-heading">
          <p>
            This site's configuration (Foundation version {entry.basis.foundation_version}) has no battery, so there
            is no battery to assess. Battery condition is Unknown because nothing is configured, not because a
            battery is healthy or faulty.
          </p>
          <p>
            <Link to={siteHealthHref(siteId)}>Back to Health</Link>
          </p>
        </Panel>
        <BasisDetails entry={entry} />
      </div>
    );
  }
  return (
    <div className="site-battery" data-battery-configuration="CONFIGURED">
      <Panel heading="Configured batteries" headingId="site-battery-list-heading">
        <ul>
          {entry.batteries.map((b) => (
            <li key={b.asset_id}>
              <Link to={siteAssetHref(siteId, b.asset_id)} data-battery-link={b.asset_id}>
                <span data-vocabulary-exempt="user-owned">{b.display_name ?? b.asset_code}</span>
              </Link>{" "}
              · condition Unknown
            </li>
          ))}
        </ul>
      </Panel>
      <BasisDetails entry={entry} />
    </div>
  );
}

function BasisDetails({ entry }: { entry: { basis: BatteryDetail["basis"]; read_at: string; rule_id: string } }) {
  const b = entry.basis;
  return (
    <Disclosure name="site-battery-technical" summary="Technical details">
      <FactList>
        <Fact term="Foundation revision">
          <span data-battery-foundation={b.foundation_revision_id}>
            <HealthRef value={b.foundation_revision_id} />
          </span>{" "}
          (version {b.foundation_version})
        </Fact>
        <Fact term="Signal channel set revision">
          <span data-battery-channel-set={b.binding_set_revision_id ?? ""}>
            <HealthRef value={b.binding_set_revision_id} />
          </span>
          {b.binding_set_version === null ? "" : ` (version ${b.binding_set_version})`}
        </Fact>
        <Fact term="Configuration in effect at">
          <HealthRef value={b.effective_at} />
        </Fact>
        <Fact term="Known as of">
          <HealthRef value={b.knowledge_at} />
        </Fact>
        <Fact term="Read at (server clock)">
          <HealthRef value={entry.read_at} />
        </Fact>
        <Fact term="Rule">
          <HealthRef value={entry.rule_id} />
        </Fact>
      </FactList>
    </Disclosure>
  );
}

/** `/sites/{site}/assets/{asset}`: one configured battery; condition Unknown with its missing inputs. */
export function SiteBattery({
  siteId,
  assetId,
  client,
  onTitle,
}: {
  siteId: string;
  assetId: string;
  client: HealthClient;
  onTitle?: (title: string) => void;
}) {
  const read = useHealthRead(() => client.getBatteryDetail(siteId, assetId), `asset:${siteId}:${assetId}`);
  const name = read?.status === "loaded" ? read.value.asset.display_name ?? read.value.asset.asset_code : null;
  useEffect(() => {
    if (name !== null) onTitle?.(name);
  }, [name, onTitle]);
  if (read === null) {
    return <p>Loading the battery.</p>;
  }
  if (read.status === "refused") {
    return (
      <HealthRefusalPanel refusal={read} subject="Battery" headingId="site-battery-refused-heading" texts={DETAIL_TEXTS}>
        <p>
          <Link to={siteHealthHref(siteId)}>Back to Health</Link>
        </p>
      </HealthRefusalPanel>
    );
  }
  const d = read.value;
  const condition = d.physical_condition;
  const rating = d.declared_nameplate;
  const channels = d.bound_channels;
  return (
    <div className="site-battery" data-battery-asset={d.asset.asset_id} data-battery-condition={condition.status}>
      <div className="evidence-statusbar">
        <Badge tone="neutral">Condition: Unknown</Badge>
        <Badge tone="neutral">Capacity: unverified</Badge>
        <span className="evidence-statusbar__facts">
          Unknown means not yet measurable: {CONDITION_REASON_WORDS[condition.reason] ?? "the inputs are missing"}.
        </span>
      </div>
      <dl className="metric-row">
        <div className="metric" data-battery-metric="condition">
          <dt>Physical condition</dt>
          <dd>Unknown</dd>
          <dd className="metric__note">{condition.missing_causal_inputs.length} inputs missing</dd>
        </div>
        <div className="metric" data-battery-metric="rating">
          <dt>Declared rating</dt>
          <dd>{rating && rating.value !== null ? `${rating.value} ${rating.unit ?? ""}`.trim() : "Not declared"}</dd>
          <dd className="metric__note">A configuration rating, not a measurement</dd>
        </div>
        <div className="metric" data-battery-metric="charge">
          <dt>State of charge</dt>
          <dd>Not shown</dd>
          <dd className="metric__note">Not read on this page; it would not show condition</dd>
        </div>
        <div className="metric" data-battery-metric="channels" data-battery-channels={d.binding_status}>
          <dt>Signal channels</dt>
          <dd>
            {d.binding_status === "BOUND"
              ? `${channels.length} connected`
              : d.binding_status === "UNBOUND"
                ? "None connected"
                : "Not set up"}
          </dd>
          <dd className="metric__note">Connected channels are not condition evidence</dd>
        </div>
      </dl>
      <Panel
        heading="What is needed to judge condition"
        headingId="site-battery-missing-heading"
        description="Battery condition stays Unknown until these exist and a reviewed rule uses them."
        flush
      >
        <DataTable labelledBy="site-battery-missing-heading">
          <thead>
            <tr>
              <th scope="col">Input</th>
              <th scope="col">Status</th>
              <th scope="col">Why it is missing</th>
            </tr>
          </thead>
          <tbody>
            {condition.missing_causal_inputs.map((input) => {
              const words = MISSING_INPUT_WORDS[input.input];
              return (
                <tr key={input.input} data-battery-missing={input.input}>
                  <th scope="row">{words?.name ?? <HealthRef value={input.input} />}</th>
                  <td>{input.status === "MISSING" ? "Missing" : <HealthRef value={input.status} />}</td>
                  <td>{words?.why ?? <HealthRef value={input.reason} />}</td>
                </tr>
              );
            })}
          </tbody>
        </DataTable>
      </Panel>
      <Panel heading="Not stated on this page" headingId="site-battery-withheld-heading">
        <p data-battery-withheld={d.withheld.join(" ")}>
          {sentence(d.withheld.map((w) => WITHHELD_WORDS[w] ?? w.toLowerCase()))
            .replace(/^./, (c) => c.toUpperCase())}{" "}
          are not stated: the evidence to support them does not exist yet. No remaining-life or replacement date is
          given.
        </p>
      </Panel>
      <div className="notice notice--info" role="note">
        Unknown here means not yet measurable. It does not mean normal, and it does not mean faulty.{" "}
        <Link to={siteHealthHref(siteId)}>Back to Health</Link>
      </div>
      <Disclosure name="site-battery-asset-technical" summary="Technical details">
        <FactList>
          <Fact term="Asset ID">
            <HealthRef value={d.asset.asset_id} />
          </Fact>
          <Fact term="Asset code">
            <HealthRef value={d.asset.asset_code} />
          </Fact>
          <Fact term="Condition reason">
            <HealthRef value={condition.reason} />
          </Fact>
          <Fact term="Channel status">
            <HealthRef value={d.binding_status} />
          </Fact>
          <Fact term="Declared rating source">
            {rating ? (
              <>
                component <HealthRef value={rating.component_id} /> in Foundation revision{" "}
                <HealthRef value={rating.foundation_revision_id} />
              </>
            ) : (
              "none"
            )}
          </Fact>
          <Fact term="State of charge">
            <HealthRef value={d.accepted_state_of_charge.included ? "INCLUDED" : "NOT_INCLUDED"} />
          </Fact>
        </FactList>
        {channels.length > 0 ? (
          <DataTable>
            <thead>
              <tr>
                <th scope="col">Channel revision ID</th>
                <th scope="col">Role</th>
                <th scope="col">Device</th>
                <th scope="col">Signal</th>
                <th scope="col">Gateway ID</th>
                <th scope="col">Source ID</th>
              </tr>
            </thead>
            <tbody>
              {channels.map((c) => (
                <tr key={c.binding_revision_id} data-battery-channel={c.binding_revision_id}>
                  <td>
                    <HealthRef value={c.binding_revision_id} />
                  </td>
                  <td>
                    <HealthRef value={c.role} />
                  </td>
                  <td>
                    <HealthRef value={c.device_id} />
                  </td>
                  <td>
                    <HealthRef value={c.signal_id} />
                  </td>
                  <td>
                    <HealthRef value={c.gateway_id} />
                  </td>
                  <td>
                    <HealthRef value={c.source_id} />
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : null}
      </Disclosure>
      <BasisDetails entry={d} />
    </div>
  );
}
