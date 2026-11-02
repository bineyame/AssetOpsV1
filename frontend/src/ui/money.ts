/**
 * WALK1-6 D3 (Addendum 9, R696): the one display rule for money amounts, shared by the EV Site views and the
 * outcome boards. The server keeps sending exact Decimal strings; only the display rounds.
 */

/** Display rounding of an exact Decimal string to two places, half even on the absolute value, without a float. */
export function money2(value: string): string {
  const negative = value.startsWith("-");
  const [whole, frac = ""] = (negative ? value.slice(1) : value).split(".");
  const padded = frac.padEnd(2, "0");
  let cents = BigInt(whole || "0") * 100n + BigInt(padded.slice(0, 2));
  const rest = padded.slice(2);
  if (/[1-9]/.test(rest)) {
    const half = rest[0] === "5" && !/[1-9]/.test(rest.slice(1));
    if (rest[0] > "5" || (rest[0] === "5" && !half) || (half && cents % 2n === 1n)) cents += 1n;
  }
  const text = `${cents / 100n}.${String(cents % 100n).padStart(2, "0")}`;
  return negative && cents !== 0n ? `-${text}` : text;
}
