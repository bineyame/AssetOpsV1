/**
 * Caps ruling 4 test support: jsdom has no layout, so `CellDisclosure`'s overflow check reads stubbed box sizes. A
 * disclosure value whose text is longer than `limit` characters reports a taller content box than its two-line box
 * (it overflows); shorter text fits. `ResizeObserver` is stubbed so a test can fire the resize path by hand.
 */
const VALUE = "cell-disclosure__value";

type Restore = () => void;

export function stubCellOverflow(limit = 40): Restore {
  const proto = HTMLElement.prototype;
  const sh = Object.getOwnPropertyDescriptor(proto, "scrollHeight");
  const ch = Object.getOwnPropertyDescriptor(proto, "clientHeight");
  const overflows = (el: HTMLElement) => (el.textContent ?? "").trim().length > limit;
  Object.defineProperty(proto, "scrollHeight", {
    configurable: true,
    get(this: HTMLElement) {
      if (!this.classList?.contains(VALUE)) return sh?.get?.call(this) ?? 0;
      return overflows(this) ? 80 : 38;
    },
  });
  Object.defineProperty(proto, "clientHeight", {
    configurable: true,
    get(this: HTMLElement) {
      if (!this.classList?.contains(VALUE)) return ch?.get?.call(this) ?? 0;
      return 38;
    },
  });
  return () => {
    if (sh) Object.defineProperty(proto, "scrollHeight", sh);
    if (ch) Object.defineProperty(proto, "clientHeight", ch);
  };
}

export class ResizeObserverStub {
  static instances: ResizeObserverStub[] = [];
  readonly targets: Element[] = [];
  constructor(readonly callback: ResizeObserverCallback) {
    ResizeObserverStub.instances.push(this);
  }
  observe(target: Element) {
    this.targets.push(target);
  }
  unobserve() {}
  disconnect() {
    this.targets.length = 0;
  }
  /** Fires the resize callback for every observed target. */
  static fire() {
    for (const o of ResizeObserverStub.instances) {
      if (o.targets.length > 0) o.callback([], o as unknown as ResizeObserver);
    }
  }
}

/** The disclosure buttons' accessible names in one table row, in cell order. */
export function disclosureNames(tr: Element): string[] {
  return Array.from(tr.querySelectorAll("button[data-cell-disclosure-toggle]")).map(
    (b) => b.getAttribute("aria-label") ?? "",
  );
}
