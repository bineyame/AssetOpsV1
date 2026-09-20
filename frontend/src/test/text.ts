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

/**
 * A copy of a container with one named region's subtree removed.
 *
 * For a ban that used to hold over a whole screen and now holds everywhere
 * except one region that earned an exception. T016 is the first slice with
 * any: the configured diagram renders, so `diagram` is a word the screen is
 * finally allowed to say, and the control vocabulary is a thing the review
 * checkpoint has to be able to ask about. Neither exception may leak: outside
 * those regions both bans hold exactly as they did.
 *
 * It throws when the selector matches nothing, and that is the important part.
 * A narrowing helper that silently found no region would assert over the whole
 * screen while the test's name claimed a narrower scope - and on a screen that
 * had lost the region, the ban it was narrowed for would pass for the wrong
 * reason. This is the shape of failure this project has shipped five times,
 * and it is cheap to close here.
 */
export function withoutRegion(
  container: HTMLElement,
  selector: string,
): HTMLElement {
  const clone = container.cloneNode(true) as HTMLElement;
  const regions = Array.from(clone.querySelectorAll(selector));

  if (regions.length === 0) {
    throw new Error(
      `withoutRegion found nothing matching ${selector}. The exception it ` +
        "carves out is not on this screen, so an assertion made against the " +
        "result would be about the whole screen while claiming to be about " +
        "everything outside one region.",
    );
  }

  for (const region of regions) {
    region.remove();
  }
  return clone;
}
