/**
 * POLISH §2 (P-04): review mode for MOCK DEVIATION labels. Client screens never show the labels; one rule in
 * `mock-deviation.css` hides every `[data-mock-deviation]` element unless the root carries
 * `data-review-labels="on"`. `?review=labels` turns review mode on for the browser session, `?review=off` turns it
 * off. Without storage the URL parameter alone decides for that page load. Nothing in the UI links here.
 */
export const REVIEW_LABELS_KEY = "assetops.reviewLabels";

type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">;

/** Applies review mode from the URL and the session; returns whether it is on. Called first in `main.tsx`. */
export function applyReviewLabels(
  search: string = window.location.search,
  storage: () => StorageLike = () => window.sessionStorage,
  root: HTMLElement = document.documentElement,
): boolean {
  const param = new URLSearchParams(search).get("review");
  let on = false;
  if (param === "labels") {
    on = true;
    try {
      storage().setItem(REVIEW_LABELS_KEY, "on");
    } catch {
      // No storage: the parameter decides for this page load only.
    }
  } else if (param === "off") {
    try {
      storage().removeItem(REVIEW_LABELS_KEY);
    } catch {
      // No storage: nothing to remove.
    }
  } else {
    try {
      on = storage().getItem(REVIEW_LABELS_KEY) === "on";
    } catch {
      on = false;
    }
  }
  if (on) root.dataset.reviewLabels = "on";
  else delete root.dataset.reviewLabels;
  return on;
}
