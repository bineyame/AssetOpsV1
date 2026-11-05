import { useEffect, useId, useRef, useState, type CSSProperties, type MouseEvent } from "react";
import { Link } from "react-router-dom";
import { useLinkFor } from "../sites/chainRef";
import type { WhyRead } from "../sites/chainClient";
import { isSheetWidth, ModalDialog } from "./Dialog";
import "./blocks.css";

/**
 * CH-5b3 (MA-1 M2, mock `whyBtn` / `whyPop` / `openWhy`): the "Why?" button and the trace dialog. The text is the
 * server's (`/chain/why` `text`); this block only lays it out.
 *
 * MOCK DEVIATION (CH5b3-R Q6): the mock's `aria-label` is "Why? {site} · {category}"; the button's is
 * "Why? {row label}", because the server title is not loaded until the dialog opens.
 * MOCK DEVIATION (CH5b3-R Q6): the mock has no loading or failure line (its text is static). Loading reads
 * WHY_LOADING; every failure, a 422 `CATEGORY_UNKNOWN` included, reads WHY_UNAVAILABLE.
 * MOCK DEVIATION MD-CH5b-5 (CH5b3-R Q5): the mock hides Close above 600 px (a popover closed by an outside click);
 * here the dialog is modal, so Close shows at every width and takes the first focus.
 */

export const WHY_BUTTON = "Why?";
export const WHY_LOADING = "Loading the reasons…";
export const WHY_UNAVAILABLE = "The reasons are not available right now";
export const WHY_HEADS = {
  from: "Comes from",
  days: "Days used",
  change: "What would change it",
} as const;
export const WHY_CLOSE = "Close";

export function WhyButton({ label, onOpen }: { label: string; onOpen: (button: HTMLButtonElement) => void }) {
  const onClick = (event: MouseEvent<HTMLButtonElement>) => {
    // Inside a `<summary>` the click must not also open or close the row.
    event.preventDefault();
    event.stopPropagation();
    onOpen(event.currentTarget);
  };
  return (
    <button
      type="button"
      className="why-btn"
      aria-haspopup="dialog"
      aria-label={`${WHY_BUTTON} ${label}`}
      onClick={onClick}
      data-why-button
    >
      {WHY_BUTTON}
    </button>
  );
}

/** Above 600 px the mock's popover box, placed under the button; at 600 px or less the bottom sheet. */
function placement(opener: HTMLElement | null): {
  sheet: boolean;
  style?: CSSProperties;
} {
  if (isSheetWidth() || opener === null) return { sheet: isSheetWidth() };
  const r = opener.getBoundingClientRect();
  const vw = document.documentElement.clientWidth || window.innerWidth;
  const width = Math.min(360, vw - 24);
  const left = Math.max(12, Math.min(r.left + window.scrollX, window.scrollX + vw - width - 12));
  return {
    sheet: false,
    style: { width, top: r.bottom + window.scrollY + 6, left },
  };
}

export function EvidenceTrace({
  label,
  load,
  opener,
  onClose,
}: {
  /** The row or card label: the title until the server's title arrives. */
  label: string;
  load: () => Promise<WhyRead>;
  opener: HTMLElement | null;
  onClose: () => void;
}) {
  const linkFor = useLinkFor();
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const [read, setRead] = useState<WhyRead | null>(null);
  const [{ sheet, style }] = useState(() => placement(opener));
  useEffect(() => {
    let live = true;
    load().then(
      (r) => live && setRead(r),
      () => live && setRead({ status: "unavailable" }),
    );
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const text = read?.status === "loaded" ? read.value.text : null;
  const state = read === null ? "loading" : text === null ? "unavailable" : "loaded";
  const evidence = text ? linkFor(text.evidence_ref) : null;
  return (
    <ModalDialog
      className={`conf-pop why-pop${sheet ? " sheet" : ""}`}
      labelledBy={titleId}
      onClose={onClose}
      opener={opener}
      initialFocus={closeRef}
      marker="data-why-dialog"
      style={style}
      closeOnOutside
    >
      <div className="conf-head">
        <span id={titleId}>{text?.title ?? label}</span>
        <button type="button" ref={closeRef} className="why-close" onClick={onClose}>
          {WHY_CLOSE}
        </button>
      </div>
      <div data-why-state={state} aria-live="polite">
        {state === "loading" ? <p className="why-p">{WHY_LOADING}</p> : null}
        {state === "unavailable" ? <p className="why-p">{WHY_UNAVAILABLE}</p> : null}
        {text ? (
          <>
            {text.say ? <p className="why-say">{text.say}</p> : null}
            {text.comes_from.length > 0 ? (
              <>
                <div className="eyebrow">{WHY_HEADS.from}</div>
                <ul className="why-from">
                  {text.comes_from.map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {text.days_used ? (
              <>
                <div className="eyebrow">{WHY_HEADS.days}</div>
                <p className="why-p" data-why-days>
                  {text.days_used}
                </p>
              </>
            ) : null}
            {text.would_change ? (
              <>
                <div className="eyebrow">{WHY_HEADS.change}</div>
                <p className="why-p">{text.would_change}</p>
              </>
            ) : null}
            {evidence && text.evidence_label ? (
              <div className="conf-cta">
                <Link to={evidence} onClick={onClose}>
                  {text.evidence_label}
                </Link>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </ModalDialog>
  );
}
