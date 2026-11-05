import {
  useEffect,
  useRef,
  type CSSProperties,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
  type RefObject,
} from "react";
import "./blocks.css";

/**
 * CH-5b3 (CH5b-R R9, CH5b3-R Q5): the one modal focus handling, moved here from `F/sites/OutcomeBoard.tsx`. A native
 * `<dialog>`, modal when supported; Tab is trapped inside, Escape closes and focus returns to the opener. The board
 * explainer, the early-warning list and the "Why?" trace (`EvidenceTrace`) all use it, so there is no second trap.
 */

export const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** The mock's switch to a bottom sheet (`openWhy`: `innerWidth<=600`). */
export const SHEET_MAX_WIDTH = 600;
export const isSheetWidth = (width: number = window.innerWidth) => width <= SHEET_MAX_WIDTH;

export function ModalDialog({
  className,
  labelledBy,
  onClose,
  opener,
  initialFocus,
  marker,
  style,
  closeOnOutside = false,
  children,
}: {
  className: string;
  labelledBy: string;
  onClose: () => void;
  opener: HTMLElement | null;
  initialFocus: RefObject<HTMLElement>;
  marker: string;
  style?: CSSProperties;
  /** A click on the backdrop (outside the dialog box) closes it, as the mock's popover does. */
  closeOnOutside?: boolean;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (dialog !== null && typeof dialog.showModal === "function" && !dialog.open) {
      try {
        dialog.showModal();
      } catch {
        dialog.setAttribute("open", "");
      }
    } else if (dialog !== null && !dialog.open) {
      dialog.setAttribute("open", "");
    }
    initialFocus.current?.focus();
    return () => opener?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opener]);
  const onKeyDown = (event: KeyboardEvent<HTMLDialogElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== "Tab" || ref.current === null) return;
    const items = Array.from(ref.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (items.length === 0) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };
  const onClick = (event: MouseEvent<HTMLDialogElement>) => {
    if (!closeOnOutside || event.target !== ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const inside =
      event.clientX >= r.left && event.clientX <= r.right && event.clientY >= r.top && event.clientY <= r.bottom;
    if (!inside) onClose();
  };
  return (
    <dialog
      ref={ref}
      className={className}
      aria-labelledby={labelledBy}
      onKeyDown={onKeyDown}
      onClick={onClick}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      style={style}
      {...{ [marker]: "" }}
    >
      {children}
    </dialog>
  );
}

/** The outcome explainer shell (side panel with a heading and a close button), as before the move. */
export function ExplainerDialog({
  title,
  titleId,
  onClose,
  opener,
  marker,
  children,
}: {
  title: string;
  titleId: string;
  onClose: () => void;
  opener: HTMLButtonElement | null;
  marker: string;
  children: ReactNode;
}) {
  const closeRef = useRef<HTMLButtonElement>(null);
  return (
    <ModalDialog
      className="ob-dialog"
      labelledBy={titleId}
      onClose={onClose}
      opener={opener}
      initialFocus={closeRef}
      marker={marker}
    >
      <div className="ob-dialog-head">
        <h2 id={titleId}>{title}</h2>
        <button type="button" ref={closeRef} className="ob-dialog-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>
      {children}
    </ModalDialog>
  );
}
