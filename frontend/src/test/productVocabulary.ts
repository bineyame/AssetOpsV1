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

const TERMS: Term[] = vocabulary.terms.map((term) => ({
  phrase: term.phrase,
  pattern: new RegExp(
    `(?<![\\p{L}\\p{N}])${escape(term.phrase).replace(/ /g, "\\s+")}(?![\\p{L}\\p{N}])`,
    "caseSensitive" in term && term.caseSensitive ? "u" : "iu",
  ),
}));

const GLOSSES = vocabulary.glosses.map(
  (gloss) => new RegExp(escape(gloss.text), "giu"),
);

function escape(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** The forbidden phrases one piece of text contains, after allowed glosses. */
export function forbiddenPhrases(text: string): string[] {
  let scanned = text;
  for (const gloss of GLOSSES) {
    scanned = scanned.replace(gloss, " ");
  }
  return TERMS.filter((term) => term.pattern.test(scanned)).map((term) => term.phrase);
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
): { violations: VocabularyViolation[]; scanned: number } {
  const violations: VocabularyViolation[] = [];
  let scanned = 0;

  for (const element of Array.from(root.querySelectorAll(`[${EXEMPT_ATTRIBUTE}]`))) {
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
    for (const phrase of forbiddenPhrases(withoutReferences(text, references(parent)))) {
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
      for (const phrase of forbiddenPhrases(withoutReferences(value, references(element)))) {
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
