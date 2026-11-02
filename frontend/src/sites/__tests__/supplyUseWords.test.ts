import { describe, expect, it } from "vitest";

import { forbiddenPhrases } from "../../test/productVocabulary";
import { STATE_PROPERTY_WORDS, propertyValueText } from "../siteViewModel";

/** WALK1-3 §4.2: the Foundation page shows a declared supply use in plain words, never the stored code. */
describe("WALK1-3 supply use words", () => {
  it("each declared supply use reads in plain words", () => {
    const text = (value: string) => propertyValueText({ property_key: "supply-use", value, unit: "state" });
    expect([text("PRODUCTIVE"), text("HOUSEHOLD"), text("ESSENTIAL_SERVICE")]).toEqual([
      "Productive use",
      "Household",
      "Essential service",
    ]);
  });

  it("other properties keep their value and unit", () => {
    expect(propertyValueText({ property_key: "ev-connector-enabled", value: "ENABLED", unit: "state" })).toBe(
      "ENABLED state",
    );
    expect(propertyValueText({ property_key: "pv-available-uncertainty", value: 3, unit: "kW" })).toBe("3 kW");
  });

  it("the words pass the client vocabulary scan", () => {
    for (const word of Object.values(STATE_PROPERTY_WORDS["supply-use"])) {
      expect(forbiddenPhrases(word, "w1")).toEqual([]);
    }
  });
});
