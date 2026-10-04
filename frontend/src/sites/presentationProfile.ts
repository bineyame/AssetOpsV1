/**
 * The domain presentation profile (T027 phase 2, AC22).
 *
 * Static substrate data selected by the read model's `site_type`
 * (`D-2026-10-02-presentation-profile-and-capability-declaration`). `site_type`
 * is domain data, not a shell, mode or variant discriminant. The profile owns
 * only which Overview cards exist and their order; it carries no card state,
 * metric, signal or gap. Those are the backend Overview read model's, and a
 * backend test pins the profile's card ids equal to the backend's domains
 * (`backend/tests/test_t027_overview.py`), so the two lists cannot drift
 * silently.
 */

import profiles from "./presentationProfiles.json";
import type { OverviewCard } from "./siteOverviewClient";

export interface OverviewCardPresentation {
  id: string;
  label: string;
}

/**
 * How a backend capability id is presented (T028 AC18). Label, order, group
 * and emphasis only: which capabilities exist, their Finding types, evidence
 * and claim levels are the backend declaration's
 * (`/api/sites/{id}/analytics`), never the profile's.
 */
export interface CapabilityPresentation {
  id: string;
  label: string;
  order: number;
  group: string | null;
  emphasis: "primary" | "default";
}

/** A Finding type's label: presentation only, keyed by the backend's id (T028). */
export interface FindingTypePresentation {
  id: string;
  label: string;
}

export interface DomainPresentationProfile {
  overview_cards: OverviewCardPresentation[];
  capabilities?: CapabilityPresentation[];
  finding_types?: FindingTypePresentation[];
}

/** Where a capability the profile does not know is placed (rule 1). */
export const DEFAULT_CAPABILITY_ORDER = 1000;

const PROFILES = profiles as Record<string, DomainPresentationProfile>;

/** The profile for a Site type, or `null` when the product has none. */
export function presentationProfileFor(
  siteType: string,
): DomainPresentationProfile | null {
  return PROFILES[siteType] ?? null;
}

/**
 * The Overview cards to render: the profile's cards, in its order, each with
 * the backend card that carries its state. A profile card the backend does not
 * serve renders nothing (there is no state to show); a backend card the
 * profile does not list is not an Overview card (the profile owns which cards
 * exist). The backend pin test keeps both lists equal.
 */
export function orderedOverviewCards(
  profile: DomainPresentationProfile | null,
  cards: OverviewCard[],
): { label: string; card: OverviewCard }[] {
  if (profile === null) {
    return [];
  }
  const byId = new Map(cards.map((card) => [card.domain_id, card]));
  return profile.overview_cards.flatMap((entry) => {
    const card = byId.get(entry.id);
    return card === undefined ? [] : [{ label: entry.label, card }];
  });
}

/**
 * Three rendering rules for backend-served capability ids
 * (`D-2026-10-02-presentation-profile-and-capability-declaration`), applied to
 * a card's assessment slot here and to Performance subtabs, Evidence
 * capability rows and Finding types as those land:
 *
 * 1. a backend id the profile does not know still renders, under the
 *    backend's display name, in a default position - drift is never silent;
 * 2. a profile id the backend does not serve renders nothing
 *    (`servedCapabilities` drops it; `orphanCapabilityIds` names it for the
 *    orphan test);
 * 3. a gap is shown only from backend state: nothing here carries a status,
 *    reason or gap.
 */
export function capabilityPresentation(
  profile: DomainPresentationProfile | null,
  backendId: string,
  backendDisplayName: string,
): CapabilityPresentation & { known: boolean } {
  const entry = profile?.capabilities?.find((item) => item.id === backendId);
  if (entry !== undefined) {
    return { ...entry, known: true };
  }
  return {
    id: backendId,
    label: backendDisplayName,
    order: DEFAULT_CAPABILITY_ORDER,
    group: null,
    emphasis: "default",
    known: false,
  };
}

/** Backend-served capabilities in presentation order (rules 1 and 2). */
export function servedCapabilities(
  profile: DomainPresentationProfile | null,
  served: { id: string; display_name: string }[],
): (CapabilityPresentation & { known: boolean })[] {
  return served
    .map((item) => capabilityPresentation(profile, item.id, item.display_name))
    .sort((a, b) => a.order - b.order || a.id.localeCompare(b.id));
}

/** Profile capability ids the backend does not serve (rule 2's orphans). */
export function orphanCapabilityIds(
  profile: DomainPresentationProfile | null,
  servedIds: string[],
): string[] {
  const served = new Set(servedIds);
  return (profile?.capabilities ?? [])
    .map((item) => item.id)
    .filter((id) => !served.has(id));
}

/**
 * Performance subtabs (T028 AC18): the backend's served analytics, labelled,
 * ordered and grouped by the profile. Rule 1: a served id the profile does not
 * know still renders, under the backend's display name, in the default
 * position. Rule 2: a profile id the backend does not serve is never in
 * `served`, so it renders nothing. A capability the profile places in another
 * group is not a Performance subtab.
 */
export function performanceSubtabs(
  profile: DomainPresentationProfile | null,
  served: { id: string; display_name: string }[],
): (CapabilityPresentation & { known: boolean })[] {
  return servedCapabilities(profile, served).filter(
    (item) => !item.known || item.group === "Performance",
  );
}

/**
 * A Finding type's label (T028 AC18). Rule 1: an id the profile does not know
 * renders with the backend's display name, or the id itself when the backend
 * names none. Rule 2: only a backend id is ever looked up, so a profile entry
 * the backend does not serve renders nothing.
 */
export function findingTypeLabel(
  profile: DomainPresentationProfile | null,
  backendId: string,
  backendDisplayName?: string,
): { id: string; label: string; known: boolean } {
  const entry = profile?.finding_types?.find((item) => item.id === backendId);
  if (entry !== undefined) {
    return { id: backendId, label: entry.label, known: true };
  }
  return { id: backendId, label: backendDisplayName ?? backendId, known: false };
}

/** Profile Finding type ids no served analytic emits (rule 2's orphans). */
export function orphanFindingTypeIds(
  profile: DomainPresentationProfile | null,
  servedFindingTypes: string[],
): string[] {
  const served = new Set(servedFindingTypes);
  return (profile?.finding_types ?? [])
    .map((item) => item.id)
    .filter((id) => !served.has(id));
}
