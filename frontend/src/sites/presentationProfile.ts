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

export interface DomainPresentationProfile {
  overview_cards: OverviewCardPresentation[];
}

const PROFILES: Record<string, DomainPresentationProfile> = profiles;

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
