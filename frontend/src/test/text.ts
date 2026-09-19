/**
 * The text a container renders, with element boundaries preserved.
 *
 * `Node.textContent` concatenates every descendant with nothing between them,
 * so two adjacent elements reading `Configuration is fixed at creation` and
 * `Topology` come out as `...creationTopology`. That silently destroys every
 * assertion anchored on a word boundary: `/\btopology\b/` cannot match there,
 * because there is no boundary between `n` and `T`.
 *
 * For an absence assertion that is the worst possible failure. It passes, and
 * it passes for a reason that has nothing to do with the screen being clean -
 * a banned word glued to its neighbour is invisible to the ban. T013 found a
 * diagram ban that had been dead this way, and jsdom has no `innerText` to
 * fall back on.
 *
 * This joins the text nodes with a space, so words stay words and a boundary
 * ban means what it says.
 */
export function spacedText(container: HTMLElement): string {
  const walker = container.ownerDocument.createTreeWalker(
    container,
    NodeFilter.SHOW_TEXT,
  );

  const parts: string[] = [];
  let node = walker.nextNode();
  while (node !== null) {
    const text = (node.textContent ?? "").trim();
    if (text.length > 0) {
      parts.push(text);
    }
    node = walker.nextNode();
  }

  return parts.join(" ");
}
