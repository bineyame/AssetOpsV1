import { describe, expect, it } from "vitest";

import { SEPARATE_SESSIONS_WORDS, groupLimitations, limitationWords } from "../dispatchWords";

const OVERLAP =
  "AMBIGUOUS_COHORT: a source reports the same time span under more than one sequence epoch (a@1, a@2); no coherent default cohort; select one explicitly";
const SUCCESSIVE =
  "AMBIGUOUS_COHORT: a source reports in this window under more than one sequence epoch (a@1, a@2); central evidence does not attest that they are one physical stream, so the default cohort does not blend them; select one explicitly";

describe("PB-6 K5: the two AMBIGUOUS_COHORT reasons read differently", () => {
  it("epochs that follow one another read as separate recording sessions, not as overlapping", () => {
    const [g] = groupLimitations([SUCCESSIVE]);
    expect(limitationWords(g.code, g.items)).toBe(SEPARATE_SESSIONS_WORDS);
    expect(SEPARATE_SESSIONS_WORDS).toBe(
      "Readings for this day came from two separate recording sessions of one source; they are not joined, so the day is not analysed",
    );
  });
  it("the overlapping case keeps today's sentence, as does a bare code", () => {
    const [g] = groupLimitations([OVERLAP]);
    const today = "Two overlapping series of records report the same times; neither is chosen, so the day is not assessed";
    expect(limitationWords(g.code, g.items)).toBe(today);
    expect(limitationWords("AMBIGUOUS_COHORT")).toBe(today);
    // a mixed group is not all-successive: it keeps the overlap sentence
    const [m] = groupLimitations([OVERLAP, SUCCESSIVE]);
    expect(limitationWords(m.code, m.items)).toBe(today);
  });
});
