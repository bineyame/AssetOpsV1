/**
 * S7-01b battery boundary (`asset:3#a`) over S7-01a's asset-boundary read.
 * W1-F5a rebuilt the battery page to the v69 `asset` panels
 * (`D-2026-10-17-mockup-layout-spec`); content is limited to what the read supports:
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

import {
  AttentionList,
  Badge,
  ChartNote,
  DataTable,
  Disclosure,
  ExactReferences,
  Fact,
  FactList,
  KeyValues,
  MetricCard,
  MetricCards,
  MissingClaim,
  Panel,
  ProductStatus,
  StatusBar,
  V69Notice,
} from "../ui";
import type { BatteryDetail, HealthClient } from "./healthClient";
import { batteryConditionWords } from "./healthHeadlines";
import {
  BATTERY_TEXTS,
  HealthRef,
  HealthRefusalPanel,
  refusalText,
  refusalWords,
  useHealthLinks,
  useHealthRead,
} from "./SiteHealth";

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
  const links = useHealthLinks();
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
            <Link to={links.health(siteId)}>Back to Health</Link>
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
              <Link to={links.asset(siteId, b.asset_id)} data-battery-link={b.asset_id}>
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

function BasisFacts({ entry }: { entry: { basis: BatteryDetail["basis"]; read_at: string; rule_id: string } }) {
  const b = entry.basis;
  return (
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
  );
}

function BasisDetails({ entry }: { entry: { basis: BatteryDetail["basis"]; read_at: string; rule_id: string } }) {
  return (
    <Disclosure name="site-battery-technical" summary="Technical details">
      <BasisFacts entry={entry} />
    </Disclosure>
  );
}

/** The battery's nominal rating as the configuration declares it, or null when none is declared. */
function nominal(rating: BatteryDetail["declared_nameplate"]): string | null {
  return rating && rating.value !== null ? `${rating.value} ${rating.unit ?? ""}`.trim() : null;
}

export interface BatteryHeader {
  /** The battery's display name (or its configuration code when it has none). */
  name: string;
  /** "200 kWh", or null when no rating is declared. */
  nominal: string | null;
}

const ASSET_PANELS = [
  "Observed reserve and power exposure",
  "Interpretation and next evidence",
  "Condition evidence and its limits",
] as const;

/**
 * `/sites/{site}/assets/{asset}`: one configured battery, rebuilt by W1-F5a to
 * the v69 `asset` panels. Condition is Unknown with its missing inputs; the
 * exposure history, capacity test and remaining life are stated gaps.
 */
export function SiteBattery({
  siteId,
  siteName,
  assetId,
  client,
  onHeader,
}: {
  siteId: string;
  siteName: string;
  assetId: string;
  client: HealthClient;
  onHeader?: (header: BatteryHeader) => void;
}) {
  const links = useHealthLinks();
  const read = useHealthRead(() => client.getBatteryDetail(siteId, assetId), `asset:${siteId}:${assetId}`);
  const name = read?.status === "loaded" ? read.value.asset.display_name ?? read.value.asset.asset_code : null;
  const rating = read?.status === "loaded" ? nominal(read.value.declared_nameplate) : null;
  useEffect(() => {
    if (name !== null) onHeader?.({ name, nominal: rating });
  }, [name, rating, onHeader]);
  if (read === null) {
    return <p>Loading the battery.</p>;
  }
  if (read.status === "refused") {
    const { heading, text } = refusalText(read, "Battery", DETAIL_TEXTS);
    const gap = (
      // post-W6 shell R149/R120 (Q7/Q17): refusal sentences at the mock `.prose` size (12 px).
      <p className="v69-prose" data-battery-gap="refused">Not shown: the battery could not be read. This is not an empty result.</p>
    );
    return (
      <div className="site-battery" data-battery-refused={read.http ?? "none"}>
        <StatusBar
          data={{ "data-battery-strip": "refused" }}
          action={<Link to={links.health(siteId)}>Back to Health</Link>}
        >
          <ProductStatus inline words={refusalWords(read)} scope={`${siteName} · battery condition`} asOf={null} />
        </StatusBar>
        <div
          className="page-refusal"
          data-page-refusal="battery"
          data-health-read="refused"
          data-health-http={read.http ?? "none"}
          data-health-code={read.code ?? ""}
        >
          <p className="page-refusal__title">
            <strong>{heading}</strong>
          </p>
          <p className="v69-prose">{text}</p>
          <ExactReferences
            name="site-battery-refused-code"
            variant="tech"
            references={[
              { label: "Server answer code", value: read.code },
              { label: "Web status", value: read.http === null ? null : String(read.http) },
            ]}
          />
        </div>
        <div className="panel-pair">
          <Panel heading={ASSET_PANELS[0]} headingId="site-battery-exposure-heading">
            {gap}
          </Panel>
          <Panel heading={ASSET_PANELS[1]} headingId="site-battery-interpretation-heading">
            {gap}
          </Panel>
        </div>
        <Panel heading={ASSET_PANELS[2]} headingId="site-battery-boundary-heading">
          {gap}
        </Panel>
      </div>
    );
  }
  const d = read.value;
  const condition = d.physical_condition;
  const channels = d.bound_channels;
  const missing = condition.missing_causal_inputs;
  const temperatureMissing = missing.some((input) => input.input === "ACCEPTED_BATTERY_TEMPERATURE_HISTORY");
  const displayName = d.asset.display_name ?? d.asset.asset_code;
  const reason = CONDITION_REASON_WORDS[condition.reason] ?? "the inputs are missing";
  return (
    <div className="site-battery" data-battery-asset={d.asset.asset_id} data-battery-condition={condition.status}>
      <StatusBar
        data={{ "data-battery-strip": condition.status }}
        other={<Badge tone="neutral">Capacity: unverified</Badge>}
        action={<Link to={links.health(siteId)}>Source contact: Health →</Link>}
      >
        <ProductStatus
          inline
          words={batteryConditionWords(d)}
          scope={<span data-vocabulary-exempt="user-owned">{displayName} · physical condition</span>}
          asOf={d.read_at}
        />
      </StatusBar>
      <MetricCards label="Battery condition evidence">
        <MetricCard
          label="Reserve exposure"
          value="Not available"
          word
          tone="muted"
          note="No accepted state-of-charge history on this page; see below"
          data={{ "data-battery-metric": "reserve" }}
        />
        <MetricCard
          label="Thermal exposure"
          value="Unknown"
          word
          tone="muted"
          note={temperatureMissing ? "No accepted temperature series" : "Not read on this page"}
          data={{ "data-battery-metric": "thermal" }}
        />
        <MetricCard
          label="Power stress"
          value="Not available"
          word
          tone="muted"
          note="No accepted battery power history on this page; see below"
          data={{ "data-battery-metric": "power" }}
        />
        <MetricCard
          label="Usable capacity"
          value="Unverified"
          word
          tone="muted"
          note={
            rating === null
              ? "No rating is declared, and nothing is measured"
              : `${rating} is a configuration rating, not a measurement`
          }
          data={{ "data-battery-metric": "rating" }}
        />
      </MetricCards>
      <div className="panel-pair">
        <Panel
          heading={ASSET_PANELS[0]}
          headingId="site-battery-exposure-heading"
          description="Accepted state of charge against the reserve the site is set to keep"
        >
          <p className="v69-prose" data-battery-exposure="gap">
            <MissingClaim gapId="G-asset-battery-exposure" placement="asset.exposure.history">
              Reserve breaches and high-power events: not available yet
            </MissingClaim>
            . This page reads no accepted state-of-charge or battery power history, so no exposure is counted. That is
            not zero exposure.
          </p>
          <KeyValues
            label="What this battery is connected to"
            rows={[
              [
                "Signal channels",
                <span data-battery-metric="channels" data-battery-channels={d.binding_status}>
                  {d.binding_status === "BOUND"
                    ? `${channels.length} connected`
                    : d.binding_status === "UNBOUND"
                      ? "None connected"
                      : "Not set up"}
                </span>,
                "channels",
              ],
              ["State of charge", "Not read on this page", "charge"],
            ]}
          />
          <ChartNote>
            A reserve breach is a policy exposure event, not a measurement of capacity loss. Connected channels are not
            condition evidence.
          </ChartNote>
        </Panel>
        <Panel heading={ASSET_PANELS[1]} headingId="site-battery-interpretation-heading">
          <p className="v69-prose">
            <strong>Battery condition cannot yet be judged.</strong> Unknown means not yet measurable: {reason}.
          </p>
          <AttentionList
            label="Inputs needed to judge condition"
            items={missing.map((input) => {
              const words = MISSING_INPUT_WORDS[input.input];
              return {
                key: input.input,
                title: (
                  <span data-battery-missing={input.input}>
                    {words?.name ?? "An input this page cannot name"}
                    {input.status === "MISSING" ? " · missing" : " · not known"}
                  </span>
                ),
                body: words?.why ?? "The read names an input this page does not recognise; its exact code is under Technical details.",
              };
            })}
          />
          <ChartNote>
            <MissingClaim gapId="G-asset-capacity-test" placement="asset.next.capacity-test">
              A capacity test action: not available yet
            </MissingClaim>
            . No test can be raised from this page.
          </ChartNote>
        </Panel>
      </div>
      <Panel heading={ASSET_PANELS[2]} headingId="site-battery-boundary-heading">
        <DataTable labelledBy="site-battery-boundary-heading">
          <thead>
            <tr>
              <th scope="col">Dimension</th>
              <th scope="col">Evidence basis</th>
              <th scope="col">What may be concluded</th>
              <th scope="col">What remains unknown</th>
            </tr>
          </thead>
          <tbody>
            <tr data-battery-boundary="reserve">
              <th scope="row">Reserve discipline</th>
              <td>No accepted state-of-charge history on this page</td>
              <td>Nothing yet</td>
              <td>How often and how long the reserve was breached</td>
            </tr>
            <tr data-battery-boundary="power">
              <th scope="row">High-power exposure</th>
              <td>No accepted battery power history on this page</td>
              <td>Nothing yet</td>
              <td>Stress exposure and the rate of wear</td>
            </tr>
            <tr data-battery-boundary="capacity">
              <th scope="row">Capacity</th>
              <td>Configured rating only</td>
              <td>{rating === null ? "No rating is declared" : `${rating} declared nominal rating`}</td>
              <td>Measured usable capacity</td>
            </tr>
            <tr data-battery-boundary="life">
              <th scope="row">Asset-life consequence</th>
              <td>None</td>
              <td>Nothing</td>
              <td>
                <MissingClaim gapId="G-asset-remaining-life" placement="asset.boundary.remaining-life">
                  Remaining life or a replacement date: not available yet
                </MissingClaim>
              </td>
            </tr>
          </tbody>
        </DataTable>
        <ChartNote data={{ "data-battery-withheld": d.withheld.join(" ") }}>
          {sentence(d.withheld.map((w) => WITHHELD_WORDS[w] ?? "an unrecognised item"))
            .replace(/^./, (c) => c.toUpperCase())}{" "}
          are not stated: the evidence to support them does not exist yet. No remaining-life or replacement date is
          given.
        </ChartNote>
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
            <Fact term="Missing inputs (exact)">
              {missing.map((input) => (
                <span key={input.input}>
                  <HealthRef value={`${input.input} ${input.status}`} />{" "}
                </span>
              ))}
            </Fact>
            <Fact term="Channel status">
              <HealthRef value={d.binding_status} />
            </Fact>
            <Fact term="Declared rating source">
              {d.declared_nameplate ? (
                <>
                  component <HealthRef value={d.declared_nameplate.component_id} /> in Foundation revision{" "}
                  <HealthRef value={d.declared_nameplate.foundation_revision_id} />
                </>
              ) : (
                "none"
              )}
            </Fact>
            <Fact term="State of charge">
              <HealthRef value={d.accepted_state_of_charge.included ? "INCLUDED" : "NOT_INCLUDED"} />
            </Fact>
          </FactList>
          <BasisFacts entry={d} />
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
      </Panel>
      <V69Notice tone="blue">
        Unknown here means not yet measurable. No warranty
        position and no remaining-life estimate are stated. <Link to={links.health(siteId)}>Back to Health</Link>
      </V69Notice>
    </div>
  );
}
