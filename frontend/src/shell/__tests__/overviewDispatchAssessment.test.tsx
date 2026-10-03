/**
 * T028 phase 1: the Overview Dispatch card shows the backend's assessment word
 * and one-line reason; the other cards keep "No assessment yet". The three
 * capability rendering rules (AC18) for the card's assessment slot.
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import {
  POPULATED_EVIDENCE,
  evidenceClient,
} from "../../sites/__tests__/evidenceFixtures";
import {
  overviewClient,
  populatedOverview,
} from "../../sites/__tests__/overviewFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import profiles from "../../sites/presentationProfiles.json";
import {
  DEFAULT_CAPABILITY_ORDER,
  capabilityPresentation,
  orphanCapabilityIds,
  presentationProfileFor,
  servedCapabilities,
} from "../../sites/presentationProfile";
import type {
  OverviewAssessment,
  SiteOverviewReadModel as SiteOverview,
} from "../../sites/siteOverviewClient";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};
const DETAIL: SiteDetailClient = {
  getSite: () =>
    Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

const CANDIDATE: OverviewAssessment = {
  status: "CANDIDATE_AVOIDABLE",
  label: "Candidate avoidable",
  reason:
    "4 h of generator runtime with PV and battery capability above load and no binding constraint evidenced (confidence medium).",
  capability_id: "dispatch",
  capability_display_name: "Dispatch",
  model_version: "dispatch-1",
  assessment_ids: ["dispatch-abc"],
  lead_assessment_id: "dispatch-abc",
};

function withDispatch(assessment: OverviewAssessment): SiteOverview {
  const overview = populatedOverview(SITE_ID);
  return {
    ...overview,
    cards: overview.cards.map((card) =>
      card.domain_id === "Dispatch" ? { ...card, assessment } : card,
    ),
  };
}

function renderOverview(value: SiteOverview) {
  return render(
    <MemoryRouter initialEntries={[`/sites/${SITE_ID}`]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({
          status: "loaded",
          value: POPULATED_EVIDENCE,
        })}
        siteOverview={overviewClient({ status: "loaded", value })}
      />
    </MemoryRouter>,
  );
}

function cardFor(name: string): HTMLElement {
  return screen
    .getByRole("heading", { level: 3, name })
    .closest("section") as HTMLElement;
}

describe("the Overview Dispatch card's assessment slot (T028)", () => {
  it("shows the backend's word and reason; other cards keep No assessment yet", async () => {
    renderOverview(withDispatch(CANDIDATE));
    await settledScreen();

    const dispatch = spacedText(cardFor("Dispatch"));
    expect(dispatch).toContain("Dispatch assessment:");
    expect(dispatch).toContain("Candidate avoidable");
    expect(dispatch).toContain(CANDIDATE.reason);
    expect(dispatch).not.toContain("No assessment yet");
    for (const name of ["Service", "Battery", "Fuel", "Renewable"]) {
      expect(spacedText(cardFor(name))).toContain("No assessment yet");
    }
  });

  it("rule 1: an id the profile does not know renders under the backend's name", async () => {
    renderOverview(
      withDispatch({
        ...CANDIDATE,
        capability_id: "dispatch-v2",
        capability_display_name: "Dispatch (new analytic)",
      }),
    );
    await settledScreen();

    const dispatch = spacedText(cardFor("Dispatch"));
    expect(dispatch).toContain("Dispatch (new analytic):");
    expect(dispatch).toContain("Candidate avoidable");
    const unknown = capabilityPresentation(
      presentationProfileFor("MINIGRID"),
      "dispatch-v2",
      "Dispatch (new analytic)",
    );
    expect(unknown).toMatchObject({
      known: false,
      order: DEFAULT_CAPABILITY_ORDER,
      emphasis: "default",
    });
  });

  it("rule 2: a profile id the backend does not serve renders nothing and is named", () => {
    const profile = presentationProfileFor("MINIGRID");
    expect(servedCapabilities(profile, []).map((c) => c.id)).toEqual([]);
    expect(orphanCapabilityIds(profile, [])).toEqual(["dispatch"]);
    expect(orphanCapabilityIds(profile, ["dispatch"])).toEqual([]);
    expect(
      servedCapabilities(profile, [
        { id: "later", display_name: "Later" },
        { id: "dispatch", display_name: "Dispatch" },
      ]).map((c) => [c.id, c.label]),
    ).toEqual([
      ["dispatch", "Dispatch assessment"],
      ["later", "Later"],
    ]);
  });

  it("rule 3: the profile carries no status, reason or gap; state is the backend's", async () => {
    for (const profile of Object.values(profiles)) {
      for (const entry of (profile as { capabilities?: object[] }).capabilities ?? []) {
        expect(Object.keys(entry).sort()).toEqual(
          ["emphasis", "group", "id", "label", "order"],
        );
      }
    }
    renderOverview(
      withDispatch({
        ...CANDIDATE,
        status: "INDETERMINATE",
        label: "Indeterminate",
        reason: "Generator runtime could not be classified: Battery discharge capability: no record.",
      }),
    );
    await settledScreen();
    const dispatch = spacedText(cardFor("Dispatch"));
    expect(dispatch).toContain("Indeterminate");
    expect(dispatch).toContain("Battery discharge capability: no record");
  });
});
