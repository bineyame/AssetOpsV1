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
  "G-readiness-gateway-firmware": { status: "open", placements: ["readiness.gateway.firmware"] },
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
