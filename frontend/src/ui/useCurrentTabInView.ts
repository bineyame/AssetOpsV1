import { useLayoutEffect, useRef } from "react";

/**
 * W1-F5b (carry 10): a tab row never wraps; like the mock's `.tabs` it scrolls inside itself at 390 px. This
 * keeps the current tab inside the visible part of its row after every render, so the reader always sees where
 * they are (the Site row's later tabs, such as Work, would otherwise start off-screen).
 */
export function useCurrentTabInView<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useLayoutEffect(() => {
    const list = ref.current?.querySelector<HTMLElement>(".site-tabs__list");
    const current = list?.querySelector<HTMLElement>('[aria-current="page"]');
    if (!list || !current || list.scrollWidth <= list.clientWidth) return;
    const row = list.getBoundingClientRect();
    const tab = current.getBoundingClientRect();
    const margin = 16;
    if (tab.right > row.right) list.scrollLeft += tab.right - row.right + margin;
    else if (tab.left < row.left) list.scrollLeft -= row.left - tab.left + margin;
  });
  return ref;
}
