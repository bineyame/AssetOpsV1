/**
 * W1-UX-05: one exact value inside product wording, marked for the vocabulary
 * guard one value at a time (D-2026-10-16-w1-ux). `UserName` is a name a person
 * entered (a site, equipment, device or signal name); `ExactRef` is a
 * source-owned identifier (a record, component, node, device or signal ID, or
 * a content hash). The words around them stay product words.
 */
export function UserName({ children }: { children: string }) {
  return <span data-vocabulary-exempt="user-owned">{children}</span>;
}

export function ExactRef({ children }: { children: string }) {
  return <code data-vocabulary-exempt="source-reference">{children}</code>;
}
