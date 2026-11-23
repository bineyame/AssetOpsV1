/**
 * IA-P P6 (D-IAP.37 Q14): the one focus-trapping drawer, moved unchanged from `estate/DeepDiveMonth.tsx` (5c unit 3,
 * vNEXT `uxOpen`/`uxClose`). The month's step and outcome drawers and the shell's "Waiting for you" use it.
 */
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import "./drawer.css";

/** `DD_COPY.close`'s word. */
export const DRAWER_CLOSE = "Close";

/* ---------- drawers (vNEXT `uxOpen`/`uxClose`: dialog, focus to Close, Escape and scrim close, focus returns) ---------- */

export interface DrawerApi {
  openId: string | null;
  open: (id: string, opener: HTMLElement) => void;
  close: () => void;
}

export function useDrawers(): DrawerApi {
  const [openId, setOpenId] = useState<string | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  const restore = useRef(false);
  useEffect(() => {
    if (openId === null && restore.current) {
      restore.current = false;
      opener.current?.focus();
    }
  }, [openId]);
  const open = useCallback((id: string, el: HTMLElement) => {
    opener.current = el;
    setOpenId(id);
  }, []);
  const close = useCallback(() => {
    restore.current = true;
    setOpenId(null);
  }, []);
  return { openId, open, close };
}

export function Drawer({ id, title, api, children }: { id: string; title: string; api: DrawerApi; children: ReactNode }) {
  const panel = useRef<HTMLDivElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const shown = api.openId === id;
  const { close } = api;
  // Rev 4 (L1, L2; vNEXT `uxOpen`): while open, Escape and the Tab cycle are handled on `document`, so they hold
  // wherever focus is (also after "Show all" replaced the focused button), and `body` carries `dd-locked`.
  useEffect(() => {
    if (!shown) return undefined;
    closeButton.current?.focus();
    document.body.classList.add("dd-locked");
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return;
      }
      if (event.key !== "Tab" || panel.current === null) return;
      const focusable = [...panel.current.querySelectorAll<HTMLElement>("button, a[href], summary, [tabindex='0']")];
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const out = !focusable.includes(document.activeElement as HTMLElement);
      if (event.shiftKey && (out || document.activeElement === first)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (out || document.activeElement === last)) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.classList.remove("dd-locked");
    };
  }, [shown, close]);
  if (!shown) return null;
  const titleId = `${id}-title`;
  return (
    <div className="dd-drawer" data-dd-drawer={id}>
      <div className="dd-drawer__scrim" data-dd-scrim onClick={api.close} />
      <div className="dd-drawer__panel" role="dialog" aria-modal="true" aria-labelledby={titleId} ref={panel}>
        <div className="dd-drawer__head">
          <h2 id={titleId}>{title}</h2>
          <button type="button" className="dd-button" ref={closeButton} onClick={api.close}>
            {DRAWER_CLOSE}
          </button>
        </div>
        <div className="dd-drawer__body">{children}</div>
      </div>
    </div>
  );
}
