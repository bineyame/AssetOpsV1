import { describe, expect, it } from "vitest";
import rows from "../__fixtures__/money-text.json";
import { boardMoneyText } from "../../sites/OutcomeBoard";

// CH-6a2 (build sheet CH-6 R8, §A4): the server's `money_text` (backend/tests/test_ch6_claims.py) and the board's
// `boardMoneyText` read this one fixture, so the two renderings cannot drift.
type Row = { low: string | null; high: string | null; currency: string | null; text: string | null };
const fixture = rows as Row[];

describe("boardMoneyText against the shared money-text fixture (CH-6a2)", () => {
  it("has cases", () => expect(fixture.length).toBeGreaterThan(10));
  it.each(fixture.map((row) => [`${row.low} ${row.high} ${row.currency}`, row] as const))("%s", (_name, row) => {
    expect(boardMoneyText({ amount_low: row.low, amount_high: row.high, currency: row.currency })).toBe(row.text);
  });
});
