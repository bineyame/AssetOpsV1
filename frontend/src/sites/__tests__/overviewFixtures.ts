import type { EvidenceRead } from "../siteEvidenceClient";
import type {
  OverviewCard,
  OverviewMetric,
  SiteOverviewClient,
  SiteOverviewReadModel,
} from "../siteOverviewClient";

const NO_ASSESSMENT = {
  status: "NO_ASSESSMENT",
  label: "No assessment yet",
  reason:
    "No analytic assesses this domain yet. The metrics are measured values, not a judgement of how the site is operating.",
};

function measured(
  metric_id: string,
  label: string,
  value: string,
  unit: string,
  signal: [string, string],
  message_id: string,
  at: string | null = null,
): OverviewMetric {
  return {
    metric_id,
    label,
    unit,
    value,
    at,
    basis: "Measured intervals cover 2.67 h.",
    evidence: [{ device_id: signal[0], signal_id: signal[1], message_id }],
    unavailable_because: null,
  };
}

function card(domain_id: string, metrics: OverviewMetric[], gaps: OverviewCard["gaps"] = []): OverviewCard {
  return {
    domain_id,
    label: domain_id,
    assessment: NO_ASSESSMENT,
    metrics,
    coverage: metrics.flatMap((m) =>
      m.evidence.map((e) => ({
        device_id: e.device_id,
        signal_id: e.signal_id,
        status: "REPORTED",
        records: 33,
        good: 32,
        unavailable: 1,
        last_source_time: "2026-10-04T11:00:00Z",
      })),
    ).concat(
      gaps.map((g) => ({
        device_id: g.device_id,
        signal_id: g.signal_id,
        status: g.status,
        records: 0,
        good: 0,
        unavailable: 0,
        last_source_time: null,
      })),
    ),
    gaps,
  };
}

export function populatedOverview(siteId: string): SiteOverviewReadModel {
  const served = measured(
    "served-energy",
    "Served energy, measured intervals",
    "67.3",
    "kWh",
    ["residential-meter", "active-power"],
    "msg-res-1",
  );
  return {
    site_id: siteId,
    site_type: "MINIGRID",
    window: {
      start: "2026-10-04T03:00:00Z",
      end: "2026-10-04T11:00:00Z",
      basis: "LATEST_RELEASE",
      hours: "8.00",
    },
    accepted_in_window: 329,
    sources_in_window: 1,
    objective: { assessment: NO_ASSESSMENT, service_delivered: served },
    // Served in an order the profile does not use, to prove the profile orders.
    cards: [
      card("Renewable", [
        measured("pv-energy", "PV energy, measured intervals", "65.0", "kWh",
          ["pv-inverter-controller", "ac-power"], "msg-pv-1"),
      ]),
      card("Service", [served]),
      card("Dispatch", [
        measured("generator-runtime", "Generator running time, measured intervals", "1.00", "h",
          ["GEN-1", "active_power"], "msg-gen-72"),
      ]),
      card("Battery", [
        measured("soc-latest", "Latest state of charge", "79.08", "%",
          ["battery-pcs-controller", "state-of-charge"], "msg-soc-1", "2026-10-04T11:00:00Z"),
      ]),
      card(
        "Fuel",
        [
          {
            metric_id: "fuel-level-latest",
            label: "Latest tank level",
            unit: "L",
            value: null,
            at: null,
            basis: "The last GOOD sample in the window, at its own source time.",
            evidence: [],
            unavailable_because:
              "No GOOD accepted record in this window for fuel-level-sensor/fuel-level.",
          },
        ],
        [{ device_id: "fuel-level-sensor", signal_id: "fuel-level", status: "NOT_REPORTED" }],
      ),
    ],
    interval_statement: "Energy and running time are summed over measured intervals only.",
    timeline: [
      {
        series_id: "demand",
        label: "Demand (three feeders)",
        unit: "kW",
        kind: "INTERVAL_MEAN",
        basis: "Summed only where all three feeders measured the same interval.",
        points: [
          { start: "2026-10-04T03:10:00Z", end: "2026-10-04T03:15:00Z", value: "15", message_id: null },
          { start: "2026-10-04T03:25:00Z", end: "2026-10-04T03:30:00Z", value: "49", message_id: null },
        ],
      },
      {
        series_id: "soc",
        label: "Battery state of charge",
        unit: "%",
        kind: "STATE_AT_INSTANT",
        basis: "Instantaneous samples at their own source times.",
        points: [{ at: "2026-10-04T03:00:00Z", value: "40", message_id: "msg-soc-0" }],
      },
    ],
    timeline_statement: "The timeline is context, not a status.",
    findings: [],
    findings_statement:
      "No analytic has assessed this site yet, so no Finding exists. This is not a statement that the site is or is not operating well.",
  };
}

export function emptyOverview(siteId: string): SiteOverviewReadModel {
  const gap = (device_id: string, signal_id: string) => ({
    device_id, signal_id, status: "NOT_REPORTED",
  });
  const missing = (metric_id: string, label: string, unit: string, signal: string): OverviewMetric => ({
    metric_id, label, unit, value: null, at: null, basis: "Measured intervals cover 0.00 h.",
    evidence: [], unavailable_because: `No GOOD accepted record in this window for ${signal}.`,
  });
  return {
    ...populatedOverview(siteId),
    window: { start: null, end: null, basis: "LATEST_RELEASE", hours: null },
    accepted_in_window: 0,
    sources_in_window: 0,
    objective: {
      assessment: NO_ASSESSMENT,
      service_delivered: missing("served-energy", "Served energy, measured intervals", "kWh",
        "residential-meter/active-power"),
    },
    cards: ["Service", "Dispatch", "Battery", "Fuel", "Renewable"].map((domain) =>
      card(domain, [missing(`${domain}-m`, `${domain} metric`, "kWh", `${domain}-device/sig`)],
        [gap(`${domain.toLowerCase()}-device`, "sig")]),
    ),
    timeline: populatedOverview(siteId).timeline.map((s) => ({ ...s, points: [] })),
  };
}

export function overviewClient(
  read: EvidenceRead<SiteOverviewReadModel>,
): SiteOverviewClient {
  return { getOverview: () => Promise.resolve(read) };
}
