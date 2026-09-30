/**
 * Exact rational arithmetic on the wire's exact text (T025d).
 *
 * The history carries every quantity as exact text - an integer, a terminating
 * decimal or a ratio such as `5/12`. Adding two of them in floating point would
 * make a balance that holds exactly look as though it missed by 1e-16, and a
 * branch total that is exactly zero look like a tiny flow. This module adds and
 * compares them exactly, with BigInt, and writes the result back in the same
 * exact form. It is display arithmetic over recorded values: it sums, it
 * resolves nothing.
 */

export interface Exact {
  /** Numerator, carrying the sign. */
  n: bigint;
  /** Denominator, always positive and coprime with `n`. */
  d: bigint;
}

function gcd(a: bigint, b: bigint): bigint {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) {
    [x, y] = [y, x % y];
  }
  return x;
}

function reduced(n: bigint, d: bigint): Exact {
  if (d === 0n) throw new Error("A ratio with a zero denominator.");
  const sign = d < 0n ? -1n : 1n;
  const g = gcd(n, d) || 1n;
  return { n: (sign * n) / g, d: (sign * d) / g };
}

export const ZERO: Exact = { n: 0n, d: 1n };

/** The exact value of wire text, or null when the text is not an exact number. */
export function parseExact(text: string): Exact | null {
  const ratio = /^(-?\d+)\/(\d+)$/.exec(text);
  if (ratio !== null) {
    return ratio[2] === "0" ? null : reduced(BigInt(ratio[1]), BigInt(ratio[2]));
  }
  const decimal = /^(-?)(\d+)(?:\.(\d+))?$/.exec(text);
  if (decimal === null) return null;
  const fraction = decimal[3] ?? "";
  const digits = BigInt(`${decimal[2]}${fraction}`);
  const scale = 10n ** BigInt(fraction.length);
  return reduced(decimal[1] === "-" ? -digits : digits, scale);
}

export function add(a: Exact, b: Exact): Exact {
  return reduced(a.n * b.d + b.n * a.d, a.d * b.d);
}

export function negate(a: Exact): Exact {
  return { n: -a.n, d: a.d };
}

export function sum(values: Exact[]): Exact {
  return values.reduce(add, ZERO);
}

export function sign(a: Exact): -1 | 0 | 1 {
  return a.n === 0n ? 0 : a.n < 0n ? -1 : 1;
}

export function abs(a: Exact): Exact {
  return a.n < 0n ? negate(a) : a;
}

/**
 * Exact text for a value: a terminating decimal when it has one, the ratio
 * otherwise. The same forms the wire uses, so a sum reads like a recorded value.
 */
export function exactText(a: Exact): string {
  let twos = 0n;
  let fives = 0n;
  let rest = a.d;
  while (rest % 2n === 0n) {
    rest /= 2n;
    twos += 1n;
  }
  while (rest % 5n === 0n) {
    rest /= 5n;
    fives += 1n;
  }
  if (rest !== 1n) return `${a.n}/${a.d}`;
  const places = twos > fives ? twos : fives;
  const scaled = (a.n * 10n ** places) / a.d;
  if (places === 0n) return scaled.toString();
  const negative = scaled < 0n;
  const digits = (negative ? -scaled : scaled)
    .toString()
    .padStart(Number(places) + 1, "0");
  const whole = digits.slice(0, digits.length - Number(places));
  const fraction = digits.slice(digits.length - Number(places)).replace(/0+$/, "");
  return `${negative ? "-" : ""}${whole}${fraction === "" ? "" : `.${fraction}`}`;
}

/** Exact text with a rounded reading aid for a ratio, e.g. `5/12 (about 0.42)`. */
export function readable(a: Exact): string {
  const text = exactText(a);
  if (!text.includes("/")) return text;
  return `${text} (about ${(Number(a.n) / Number(a.d)).toFixed(2)})`;
}
