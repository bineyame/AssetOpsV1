/**
 * Marks exact source-owned identifiers rendered inside authored text, so the
 * T028 product vocabulary guard (`test/productVocabulary.ts`) skips those
 * values and still reads every authored word around them. Section 4 of the
 * T028 presentation decision: source identifiers may remain in clearly
 * labelled reference fields and are never rewritten. Only identifiers belong
 * here - the guard refuses a value that is not identifier-shaped.
 */
export function sourceReferences(
  ...values: Array<string | null | undefined>
): { "data-vocabulary-reference": string } {
  return {
    "data-vocabulary-reference": values
      .filter((value): value is string => typeof value === "string" && value.length > 0)
      .join(" | "),
  };
}
