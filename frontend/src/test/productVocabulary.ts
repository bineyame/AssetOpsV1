/**
 * The T028 product vocabulary guard (D-2026-10-04-plain-language-analysis-views,
 * `.agent/T028-architect-presentation.md` section 4).
 *
 * It scans what a screen actually says - every rendered text node, including
 * text a backend delivered, graphics' captions, legends and `<title>`s - and
 * every accessible label an assistive technology would read (`aria-label`,
 * `title`, `alt`, `placeholder`, `aria-description`), against the versioned
 * list in `productVocabulary.json`. Matching is on word boundaries, so `run`
 * does not match `truncate`, and a failure names the page and the phrase.
 *
 * Exclusions are only the three the decision names, applied to one element at
 * a time with `data-vocabulary-exempt="<reason>"`: an exact source-owned
 * reference value, a user-owned name, or a Lab entry. An exempt element must
 * wrap a single value - one with element children is itself a violation - so a
 * whole panel or a backend response cannot be exempted by marking its root.
 *
 * The guard is a regression aid. A person still has to judge plain meaning,
 * uncertainty and claim strength.
 */
import vocabulary from "./productVocabulary.json";

export interface VocabularyViolation {
  page: string;
  phrase: string;
  /** Where the phrase was found: `text` or the attribute name. */
  where: string;
  text: string;
}

const LABEL_ATTRIBUTES = [
  "aria-label",
  "aria-description",
  "aria-roledescription",
  "title",
  "alt",
  "placeholder",
] as const;

export const EXEMPT_ATTRIBUTE = "data-vocabulary-exempt";
/**
 * Exact source-owned reference values inside authored text, on the element
 * that renders them, separated by " | ". The scan removes exactly those values
 * from that element's text and labels and still scans the authored words
 * around them. A value must have the shape of an identifier (letters, digits,
 * `.`, `_`, `-`, joined by " / ", optionally " vN"), so prose cannot be
 * passed off as a reference.
 */
export const REFERENCE_ATTRIBUTE = "data-vocabulary-reference";
const REFERENCE_SHAPE = /^[A-Za-z0-9._-]+(?: \/ [A-Za-z0-9._-]+)*(?: v\d+)?$/;
export const VOCABULARY_VERSION: number = vocabulary.version;
export const EXEMPTION_REASONS = Object.keys(vocabulary.exemptions);

interface Term {
  phrase: string;
  pattern: RegExp;
}

/** A `code` term also treats `_` as part of a word, so `PENDING` is not found inside `PENDING_REASSESSMENT`. */
function phraseTerm(phrase: string, caseSensitive: boolean, code = false): Term {
  const word = code ? "\\p{L}\\p{N}_" : "\\p{L}\\p{N}";
  return {
    phrase,
    pattern: new RegExp(
      `(?<![${word}])${escape(phrase).replace(/ /g, "\\s+")}(?![${word}])`,
      caseSensitive ? "u" : "iu",
    ),
  };
}

const TERMS: Term[] = vocabulary.terms.map((term) =>
  phraseTerm(term.phrase, "caseSensitive" in term && term.caseSensitive === true),
);

const GLOSSES = vocabulary.glosses.map(
  (gloss) => new RegExp(escape(gloss.text), "giu"),
);

function escape(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * The W1 set (D-2026-10-16-w1-ux, D-2026-10-16-w1-ux-disclosure), versioned
 * separately inside the same file. A route opts in as its W1 slice migrates
 * it; the T028 list keeps applying to every route either way.
 *
 * Raw codes are matched case-sensitively: a closed list of single-word state
 * codes, plus shape patterns for uppercase underscore tokens, UUIDs, digests
 * and rule/model versions. Allow-listed units and acronyms (SOC, UTC, kW, kWh,
 * PV) are never reported as raw codes; the T028 gloss rule for acronyms is a
 * separate rule and still applies.
 */
export const W1_VOCABULARY_VERSION: number = vocabulary.w1.version;
const W1_ALLOWED = new Set<string>(vocabulary.w1.allowedAcronyms);
const W1_TERMS: Term[] = vocabulary.w1.terms.map((term) => phraseTerm(term.phrase, false));
const W1_CODES: Term[] = vocabulary.w1.codes.map((code) => phraseTerm(code, true, true));
const W1_PATTERNS = vocabulary.w1.patterns.map((p) => ({ name: p.name, pattern: new RegExp(p.source, `${p.flags}g`) }));
const W1_GLOSSES = vocabulary.w1.glosses.map((gloss) => new RegExp(escape(gloss.text), "giu"));
const DISCLOSURE_TERMS: Term[] = [
  ...vocabulary.w1.disclosure.phrases.map((phrase) => phraseTerm(phrase, false)),
  ...vocabulary.w1.disclosure.words.map((word) => phraseTerm(word, false)),
  ...vocabulary.w1.disclosure.codes.map((code) => phraseTerm(code, true, true)),
];
const UNDERSCORE_CODE = W1_PATTERNS[0];

/** Which list a scan applies: the T028 list alone, or T028 plus the W1 set. */
export type VocabularySet = "t028" | "w1";

/**
 * The raw codes one piece of text contains: closed-list state codes and the
 * shape patterns, minus allow-listed units and acronyms. Case-sensitive, so
 * ordinary lower-case words ("current", "pending") are never codes.
 */
export function rawCodes(text: string): string[] {
  const found: string[] = [];
  for (const code of W1_CODES) if (code.pattern.test(text)) found.push(code.phrase);
  for (const { name, pattern } of W1_PATTERNS) {
    for (const match of text.matchAll(pattern)) {
      if (W1_ALLOWED.has(match[0])) continue;
      found.push(`${name}: ${match[0]}`);
    }
  }
  return found;
}

function withoutGlosses(text: string, glosses: RegExp[]): string {
  let scanned = text;
  for (const gloss of glosses) scanned = scanned.replace(gloss, " ");
  return scanned;
}

/** The forbidden phrases one piece of text contains, after allowed glosses. */
export function forbiddenPhrases(text: string, set: VocabularySet = "t028"): string[] {
  if (set === "t028") {
    const scanned = withoutGlosses(text, GLOSSES);
    return TERMS.filter((term) => term.pattern.test(scanned)).map((term) => term.phrase);
  }
  const scanned = withoutGlosses(text, [...W1_GLOSSES, ...GLOSSES]);
  return [
    ...TERMS.filter((term) => term.pattern.test(scanned)).map((term) => term.phrase),
    ...W1_TERMS.filter((term) => term.pattern.test(scanned)).map((term) => term.phrase),
    ...rawCodes(scanned),
  ];
}

/**
 * The narrower disclosure list (D-2026-10-16-w1-ux-disclosure): internal
 * analytics phrases, implementation words, raw state labels and any raw
 * uppercase underscore token. Units and acronyms are not codes.
 */
export function disclosurePhrases(text: string): string[] {
  const scanned = withoutGlosses(text, W1_GLOSSES);
  const found = DISCLOSURE_TERMS.filter((term) => term.pattern.test(scanned)).map((term) => term.phrase);
  for (const match of scanned.matchAll(UNDERSCORE_CODE.pattern)) {
    if (W1_ALLOWED.has(match[0]) || found.includes(match[0])) continue;
    found.push(`${UNDERSCORE_CODE.name}: ${match[0]}`);
  }
  return found;
}

function references(element: Element | null): string[] {
  const holder = element?.closest(`[${REFERENCE_ATTRIBUTE}]`) ?? null;
  const raw = holder?.getAttribute(REFERENCE_ATTRIBUTE) ?? "";
  return raw.split(" | ").filter((value) => value.length > 0 && REFERENCE_SHAPE.test(value));
}

function withoutReferences(text: string, values: string[]): string {
  let out = text;
  for (const value of values) out = out.split(value).join(" ");
  return out;
}

function exemptReason(element: Element | null): string | null {
  const exempt = element?.closest(`[${EXEMPT_ATTRIBUTE}]`) ?? null;
  return exempt === null ? null : exempt.getAttribute(EXEMPT_ATTRIBUTE);
}

/**
 * Every vocabulary violation inside `root`, labelled with `page`.
 *
 * Also returns how many text pieces were scanned, so a caller can prove the
 * scan saw a populated screen rather than an empty or loading one.
 */
export function scanProductVocabulary(
  root: HTMLElement,
  page: string,
  options: { set?: VocabularySet } = {},
): { violations: VocabularyViolation[]; scanned: number } {
  return scanWith(root, page, (text) => forbiddenPhrases(text, options.set ?? "t028"));
}

/**
 * Scan each closed exact-reference disclosure inside `root` (its summary, its
 * labels and every text node and accessible name) against the narrower
 * disclosure list. Individually exempt values are skipped one value at a
 * time; nothing else is. Also returns the number of disclosures found, so a
 * caller can prove the scan was not vacuous.
 */
export function scanDisclosureVocabulary(
  root: HTMLElement,
  page: string,
): { violations: VocabularyViolation[]; scanned: number; disclosures: number } {
  const disclosures = Array.from(root.querySelectorAll<HTMLElement>("[data-exact-references]"));
  const violations: VocabularyViolation[] = [];
  let scanned = 0;
  for (const disclosure of disclosures) {
    const result = scanWith(disclosure, page, disclosurePhrases);
    violations.push(...result.violations);
    scanned += result.scanned;
  }
  return { violations, scanned, disclosures: disclosures.length };
}

function scanWith(
  root: HTMLElement,
  page: string,
  check: (text: string) => string[],
): { violations: VocabularyViolation[]; scanned: number } {
  const violations: VocabularyViolation[] = [];
  let scanned = 0;

  // The root itself is checked too, so a scanned container cannot exempt itself.
  const exemptElements = [root, ...Array.from(root.querySelectorAll(`[${EXEMPT_ATTRIBUTE}]`))].filter((e) =>
    e.hasAttribute(EXEMPT_ATTRIBUTE),
  );
  for (const element of exemptElements) {
    const reason = element.getAttribute(EXEMPT_ATTRIBUTE) ?? "";
    if (!EXEMPTION_REASONS.includes(reason)) {
      violations.push({ page, phrase: `unknown exemption "${reason}"`, where: EXEMPT_ATTRIBUTE, text: element.outerHTML.slice(0, 160) });
    } else if (element.children.length > 0) {
      violations.push({ page, phrase: "exemption wraps more than one value", where: EXEMPT_ATTRIBUTE, text: element.outerHTML.slice(0, 160) });
    }
  }

  for (const element of Array.from(root.querySelectorAll(`[${REFERENCE_ATTRIBUTE}]`))) {
    const raw = element.getAttribute(REFERENCE_ATTRIBUTE) ?? "";
    for (const value of raw.split(" | ")) {
      if (!REFERENCE_SHAPE.test(value)) {
        violations.push({ page, phrase: "a reference value is not an identifier", where: REFERENCE_ATTRIBUTE, text: value });
      }
    }
  }

  const walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
    const text = (node.textContent ?? "").trim();
    if (text.length === 0) continue;
    const parent = node.parentElement;
    if (parent !== null && ["SCRIPT", "STYLE"].includes(parent.tagName)) continue;
    if (exemptReason(parent) !== null) continue;
    scanned += 1;
    for (const phrase of check(withoutReferences(text, references(parent)))) {
      violations.push({ page, phrase, where: "text", text });
    }
  }

  const elements = [root, ...Array.from(root.querySelectorAll("*"))];
  for (const element of elements) {
    if (exemptReason(element) !== null) continue;
    for (const attribute of LABEL_ATTRIBUTES) {
      const value = element.getAttribute(attribute);
      if (value === null || value.trim().length === 0) continue;
      scanned += 1;
      for (const phrase of check(withoutReferences(value, references(element)))) {
        violations.push({ page, phrase, where: attribute, text: value });
      }
    }
  }

  return { violations, scanned };
}

/** A failure message naming each page, phrase and the text it was found in. */
export function describeViolations(violations: VocabularyViolation[]): string {
  return violations
    .map((v) => `${v.page}: "${v.phrase}" in ${v.where}: ${v.text.slice(0, 200)}`)
    .join("\n");
}
