import { describe, expect, it } from "vitest";

import { ROADMAP_WORDS } from "../productWords";

describe("RM-1 (D-E5.34): roadmap lines name what is missing and never read as an error", () => {
  const lines = Object.values(ROADMAP_WORDS);
  it("each line says what is coming or not connected, in plain words", () => {
    for (const line of lines) {
      expect(line).toMatch(/(coming|later|not connected yet)\.?$/i);
    }
  });
  it("no line says error, fail, or carries a code", () => {
    for (const line of lines) {
      expect(line).not.toMatch(/error|fail|refus|invalid|unavailable|[A-Z]{2,}_[A-Z_]+/i);
    }
  });
  it("the three owner examples are verbatim", () => {
    expect(ROADMAP_WORDS.reviewRecommendation).toBe("Reviewing a recommendation needs sign-in, which is coming");
    expect(ROADMAP_WORDS.coldFindingsNotGlobal).toBe("Cold-room findings are listed here; the estate list adds them later");
  });
});
