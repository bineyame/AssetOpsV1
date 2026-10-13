/**
 * Typed mirror of the registry mock-gap catalogue (`mock_gaps` in
 * `frontend/docs/architecture/v69-dependency-registry-pilot.json`,
 * D-2026-10-12-mock-gap-closure-mechanism).
 *
 * Only gaps the UI may reference appear here: an open gap, or a resolved gap
 * whose reviewed UI transition still renders (`resolved_transition`). Each
 * entry lists exactly the registry `ui_placements`. `tools/checks/missing-claim-scan.mjs`
 * keeps this mirror equal to the registry and every `<MissingClaim>` use equal to it.
 *
 * A gap ID is inspection metadata. It is never product copy.
 */
export const UI_GAP_CATALOGUE = {
  "G-finding-evidence-coverage": { status: "open", placements: ["finding-evidence.bundle.coverage"] },
  "G-finding-evidence-use": { status: "open", placements: ["finding-evidence.bundle.use"] },
  "G-foundation-change-record": { status: "open", placements: ["foundation.controls.change-record"] },
  "G-foundation-constraint-evidence": { status: "open", placements: ["foundation.controls.constraint-evidence"] },
  "G-foundation-financial-assumptions": { status: "open", placements: ["foundation.identity.financial-assumptions"] },
  "G-foundation-productive-use": { status: "open", placements: ["foundation.identity.productive-use"] },
  "G-readiness-commissioning": { status: "open", placements: ["readiness.commissioning.definition", "readiness.commissioning.confirmed", "readiness.commissioning.needed", "readiness.commissioning.declared", "readiness.commissioning.next-step"] },
  "G-readiness-gateway-completeness": { status: "open", placements: ["readiness.gateway.completeness"] },
  "G-readiness-gateway-firmware": { status: "open", placements: ["readiness.gateway.firmware"] },
  "G-readiness-gateway-signal-strength": { status: "open", placements: ["readiness.gateway.signal-strength"] },
  "G-readiness-gateway-uptime": { status: "open", placements: ["readiness.gateway.uptime"] },
  "G-readiness-source-contact": { status: "open", placements: ["readiness.gateway.source-connection", "readiness.gateway.source-connection-registration", "readiness.sources.arrival"] },
  "G-sites-attention-counts": { status: "open", placements: ["sites.inventory.attention-counts"] },
  "G-sites-operating-view": { status: "open", placements: ["sites.inventory.operating-view", "sites.inventory.analysis-note"] },
  "G-sites-setup-progress": { status: "open", placements: ["sites.inventory.setup-progress"] },
  "G-sld-protection-metering": { status: "open", placements: ["sld.diagram.protection-metering"] },
  "G-sld-reporting-status": { status: "open", placements: ["sld.diagram.reporting-status", "sld.diagram.readings-status", "sld.diagram.bus-slot", "sld.diagram.node-slot", "sld.contents.readings-slot", "sld.contents.caption", "sld.intro.readings-status"] },
} as const satisfies Record<
  string,
  { readonly status: "open" | "resolved_transition"; readonly placements: readonly string[] }
>;

export type GapId = keyof typeof UI_GAP_CATALOGUE;
export type GapPlacement<G extends GapId> = (typeof UI_GAP_CATALOGUE)[G]["placements"][number];

/** True only for a known gap ID and one of its registered placements. */
export function isKnownGapPlacement(gapId: string, placement: string): boolean {
  if (!Object.prototype.hasOwnProperty.call(UI_GAP_CATALOGUE, gapId)) return false;
  const placements: readonly string[] = UI_GAP_CATALOGUE[gapId as GapId].placements;
  return placements.includes(placement);
}
