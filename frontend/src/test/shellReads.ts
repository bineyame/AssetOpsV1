/**
 * IA-P P6 (spec §6 P6): the shell's "Waiting for you" reads the Decisions read (every page of
 * `/api/estate/portfolio`, `limit=50`) on every operator page. A test that pins a page's own requests drops the
 * shell's read with `pageRequests`; a test about the estate portfolio read itself counts it on purpose.
 */
export function isShellInboxRead(url: string): boolean {
  return url.startsWith("/api/estate/portfolio?") && /[?&]limit=50(?:&|$)/.test(url);
}

export function pageRequests(urls: readonly string[]): string[] {
  return urls.filter((u) => !isShellInboxRead(u));
}
