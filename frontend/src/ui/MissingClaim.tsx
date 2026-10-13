import type { ReactNode } from "react";
import { isKnownGapPlacement, UI_GAP_CATALOGUE, type GapId, type GapPlacement } from "./gapCatalogue";

type MissingClaimTag = "p" | "span" | "div" | "li" | "dd" | "td";

export interface MissingClaimProps<G extends GapId> {
  /** Registry gap ID. Rendered only as `data-gap-id`, never as visible text. */
  gapId: G;
  /** Stable placement ID registered for this gap; conditional branches each carry their own. */
  placement: GapPlacement<G>;
  as?: MissingClaimTag;
  className?: string;
  /** The honest product copy naming what is missing. */
  children: ReactNode;
}

/**
 * A visible missing-capability statement tied to a catalogued gap. The type
 * system rejects an unknown gap or placement; at runtime an unknown pair
 * throws rather than rendering an untraceable missing state.
 */
export function MissingClaim<G extends GapId>({ gapId, placement, as = "span", className, children }: MissingClaimProps<G>) {
  if (!isKnownGapPlacement(gapId, placement)) {
    throw new Error(`MissingClaim: ${String(gapId)} at ${String(placement)} is not a catalogued gap placement`);
  }
  const Tag = as;
  return (
    <Tag
      className={className}
      data-gap-id={gapId}
      data-gap-placement={placement}
      data-gap-status={UI_GAP_CATALOGUE[gapId].status}
    >
      {children}
    </Tag>
  );
}
