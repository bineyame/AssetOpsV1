/**
 * W3-02 commit 4: plain words and money display for the estate Financials root (`.agent/W3-02-build-spec.md`
 * closure 1 "Money row and comparison contract" display rules and "Mock copy, navigation and measured layout" tones).
 * Every value is a stored server field: the helpers only format it. Exact Decimal strings are rounded without a float.
 */
import type {
  FinancialAmount,
  FinancialCategory,
  FinancialDiagnosticCode,
  FinancialEligibility,
  FinancialGroupState,
  WireDecimal,
} from "./estateEvidenceMoneyClient";

/** The ledger's category dictionary; `RECORDED_REPAIR` keeps its own label and is never merged into product exposure. */
export const CATEGORY_LABEL: Readonly<Record<FinancialCategory, string>> = {
  CANDIDATE_OPERATING_COST_EXPOSURE: "Candidate operating-cost exposure",
  POTENTIAL_PRODUCT_EXPOSURE: "Potential product exposure",
  GROSS_TARIFF_SCENARIO: "Gross tariff estimate",
  RECORDED_REPAIR: "Recorded repair",
};

export const categoryLabel = (category: string): string =>
  CATEGORY_LABEL[category as FinancialCategory] ?? "Category not described";

/** The ledger's `Value` words for a line that has no current value, with the closure 1 page-local tones. */
export const ELIGIBILITY_WORDS: Readonly<Record<Exclude<FinancialEligibility, "ELIGIBLE">, { text: string; tone: string }>> = {
  UNPRICED: { text: "Unpriced", tone: "amber" },
  WITHHELD: { text: "Withheld", tone: "gray" },
  UNKNOWN: { text: "Unknown", tone: "gray" },
  HISTORICAL: { text: "Historical", tone: "blue" },
  PENDING: { text: "Pending", tone: "amber" },
  CONFLICT: { text: "Not comparable", tone: "red" },
};

/** Group result words and tones (closure 1: COMPARABLE green, SINGLE_LINE amber, OVERLAPPING_BASIS red, rest gray). */
export const GROUP_STATE_WORDS: Readonly<Record<FinancialGroupState, { text: string; tone: string }>> = {
  COMPARABLE: { text: "Comparable", tone: "green" },
  SINGLE_LINE: { text: "Single line", tone: "amber" },
  INELIGIBLE: { text: "Not totalled", tone: "gray" },
  OVERLAPPING_BASIS: { text: "Overlapping basis", tone: "red" },
  UNKNOWN_COVERAGE: { text: "Coverage incomplete", tone: "gray" },
  NO_LINES: { text: "No lines", tone: "gray" },
};

/** Plain reason words for the closed reason vocabulary, including commit-3 L4's `PARTITION_INELIGIBLE`. */
const REASON_WORDS: Readonly<Record<string, string>> = {
  UNKNOWN_COVERAGE: "some Sites have no complete selection",
  PENDING: "new work is being assessed",
  UNPRICED: "no price is recorded",
  WITHHELD: "the value is withheld",
  HISTORICAL: "historical record",
  UNKNOWN_SOURCE: "the source is not known",
  MIXED_SOURCE: "the source is mixed",
  BASIS_NOT_PROVEN: "a separate technical basis is not proven",
  OVERLAPPING_BASIS: "the technical basis overlaps another line",
  ASSUMPTION_UNKNOWN: "the assumptions cannot be compared",
  NO_LINES: "no consequence lines in this category",
  PARTITION_INELIGIBLE: "grouped with a line that cannot be totalled",
};

export const reasonWord = (code: string): string => REASON_WORDS[code] ?? "reason not described";
/** Post-W6 W3-estate Q13: whether a reason code has plain words (unknown codes are shown as a raw detail). */
export const hasReasonWord = (code: string): boolean => code in REASON_WORDS;

export function reasonText(codes: string[]): string {
  const words = codes.map(reasonWord);
  if (words.length === 0) return "";
  const text = words.join("; ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Commit-3 L3: the diagnostic names a category with more than one value, not a pairwise difference. */
const DIAGNOSTIC_WORDS: Readonly<Record<FinancialDiagnosticCode, string>> = {
  MIXED_CURRENCY: "more than one currency",
  DIFFERENT_PERIOD: "more than one period kind",
  DIFFERENT_WINDOW: "more than one window",
  DIFFERENT_ASSUMPTION: "more than one assumption value",
};

export function diagnosticText(category: string, code: string, lineCount: number): string {
  const what = DIAGNOSTIC_WORDS[code as FinancialDiagnosticCode] ?? "values that differ";
  const lines = lineCount === 1 ? "1 line" : `${lineCount} lines`;
  return `${categoryLabel(category)}: ${what} · ${lines} in the differing-value category`;
}

/** ISO 4217 minor units, as the backend's `financials/consequence_read.py:MINOR_UNITS`. */
const MINOR_UNITS: Readonly<Record<string, number>> = {
  USD: 2, EUR: 2, GBP: 2, CHF: 2, CAD: 2, AUD: 2, NZD: 2, ZAR: 2, INR: 2, CNY: 2,
  ETB: 2, KES: 2, TZS: 2, UGX: 0, RWF: 0, NGN: 2, GHS: 2, XOF: 0, XAF: 0, MAD: 2,
  EGP: 2, JPY: 0, KRW: 0, VND: 0, CLP: 0, ISK: 0, BHD: 3, KWD: 3, OMR: 3, JOD: 3,
  TND: 3, LYD: 3, IQD: 3,
};

export type Rounding = "floor" | "ceil" | "even";

/** Rounds an exact decimal string to `places` without a float: floor/ceil (outward bounds) or half even. */
export function roundDecimal(value: WireDecimal, places: number, mode: Rounding): string | null {
  if (value === null) return null;
  const text = String(value).trim();
  if (!/^-?\d+(\.\d+)?$/.test(text)) return null;
  const negative = text.startsWith("-");
  const [whole, frac = ""] = (negative ? text.slice(1) : text).split(".");
  let units = BigInt(`${whole}${frac.padEnd(places, "0").slice(0, places)}` || "0");
  const rest = frac.slice(places);
  if (/[1-9]/.test(rest)) {
    if (mode === "even") {
      const exactHalf = rest[0] === "5" && !/[1-9]/.test(rest.slice(1));
      if (rest[0] > "5" || (rest[0] === "5" && !exactHalf) || (exactHalf && units % 2n === 1n)) units += 1n;
    } else if ((mode === "ceil") !== negative) {
      units += 1n; // away from zero: ceil of a positive, floor of a negative
    }
  }
  const scale = 10n ** BigInt(places);
  const body = places === 0 ? `${units}` : `${units / scale}.${String(units % scale).padStart(places, "0")}`;
  return negative && units !== 0n ? `-${body}` : body;
}

export const NOT_DISPLAYABLE = "Value not displayable for this currency";

function withCurrency(value: string, currency: string): string {
  return currency === "USD" ? `$${value}` : `${currency} ${value}`;
}

/**
 * A stored money range for display: outward to the currency minor unit (W1 bounds and comparable group sums), or
 * half even to two places (EV, the same rule as its Site page). Null when the currency or bounds cannot be shown.
 */
export function moneyText(amount: FinancialAmount | null | undefined, rounding: "outward" | "even2"): string | null {
  if (amount === null || amount === undefined || amount.currency === null) return null;
  const places = rounding === "even2" ? 2 : MINOR_UNITS[amount.currency];
  if (places === undefined) return null;
  const low = roundDecimal(amount.low, places, rounding === "even2" ? "even" : "floor");
  const high = roundDecimal(amount.high, places, rounding === "even2" ? "even" : "ceil");
  if (low === null || high === null) return null;
  return low === high ? withCurrency(low, amount.currency) : `${withCurrency(low, amount.currency)}–${withCurrency(high, amount.currency)}`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function day(wire: string): string {
  return `${Number(wire.slice(8, 10))} ${MONTHS[Number(wire.slice(5, 7)) - 1] ?? "?"} ${wire.slice(0, 4)}`;
}

/** Closure 1: `d MMM yyyy · HH:mm–HH:mm UTC` for one day, otherwise both full UTC endpoints. */
export function moneyWindowText(start: string | null, end: string | null): string | null {
  if (start === null || end === null) return null;
  if (start.slice(0, 10) === end.slice(0, 10)) return `${day(start)} · ${start.slice(11, 16)}–${end.slice(11, 16)} UTC`;
  return `${day(start)} · ${start.slice(11, 16)} UTC – ${day(end)} · ${end.slice(11, 16)} UTC`;
}

const UNIT_WORDS: Readonly<Record<string, string>> = { L: "L", kWh: "kWh", degC_min: "°C-min" };

function trim(value: WireDecimal): string | null {
  if (value === null) return null;
  const text = String(value);
  return /^-?\d+\.\d+$/.test(text) ? text.replace(/0+$/, "").replace(/\.$/, "") : text;
}

/** Quantity in `L`, `kWh` or `°C-min`; anything unestablished is `Quantity not established`. */
export function quantityText(quantity: { low: WireDecimal; high: WireDecimal; unit: string | null }): string | null {
  const unit = quantity.unit === null ? undefined : UNIT_WORDS[quantity.unit];
  const low = trim(quantity.low);
  const high = trim(quantity.high);
  if (unit === undefined || (low === null && high === null)) return null;
  if (low === null || high === null || low === high) return `${low ?? high} ${unit}`;
  return `${low}–${high} ${unit}`;
}
