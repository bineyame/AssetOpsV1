/**
 * IA-P P6 (spec §6 P6; IA-1 §4.3; D-IAP.37 Q12 to Q16): "Waiting for you", the top-bar control and its drawer.
 *
 * - The badge is the Decisions tile's "Waiting for a choice" figure from the one shared function
 *   (`waitingForAChoice`), so badge = tile in every case, truncated included. It is absent at 0.
 * - The rows come only from `decisionItems(loaded.first, loaded.rows)` on the Decisions read's cache key (the app's
 *   estate client, `EstateClientProvider`), so the shell adds no read (Q12; 6f1 U2's §4.4 sweep finds this call).
 * - The drawer is `ui/Drawer` (Q14): dialog, focus to Close, Escape and the scrim close it, focus returns here.
 * - "For you" is not available yet: who decides is not recorded until the decision records (6a; MD-IAP-4).
 * - "Since you last looked" says each progress row in `ProgressPanel`'s words (Q15).
 */
import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import { Drawer, useDrawers } from "../ui/Drawer";
import { displayCode } from "../ui/displayCode";
import { RailIcon } from "../ui/RailIcon";
import { RangeLink as Link } from "../ui/RangeLink";
import { withRange } from "../ui/sharedRange";
import { createEstateClient, type EstateClient } from "../estate/estateClient";
import { useEstateRead, useProvidedEstateClient } from "../estate/estateReadCache";
import { progressOutcomeWords } from "../estate/EstatePortfolio";
import { DECISIONS_PATH, NOT_AVAILABLE_YET, decisionItems, waitingForAChoice, waitingTotalOf } from "../estate/homeLists";
import { queryFromParams } from "../estate/estateShared";
import { PLACEMENT_GROUP_LABEL } from "../estate/portfolioWords";
import "./waitingForYou.css";

export const INBOX_TITLE = "Waiting for you";
export const INBOX_ID = "ia-inbox";
/** "In your portfolio" shows this many waiting rows, then "View all {n}". */
export const INBOX_CAP = 10;
/** "Since you last looked" shows this many progress rows, then "See all in Results". */
export const INBOX_SINCE_CAP = 3;
export const INBOX_COPY = {
  forYou: "For you",
  portfolio: "In your portfolio",
  since: "Since you last looked",
  nothingWaiting: "Nothing else is waiting for a choice",
  noChange: "No change recorded in this range",
  seeResults: "See all in Results",
  loading: "Loading Decisions…",
} as const;

const RESULTS_PATH = "/results";

export function WaitingForYou({ client }: { client?: EstateClient }) {
  const provided = useProvidedEstateClient();
  const reads = useMemo(() => client ?? provided ?? createEstateClient(), [client, provided]);
  const [params] = useSearchParams();
  const query = queryFromParams(params);
  const read = useEstateRead(reads, "portfolio", query);
  const loaded = read?.status === "loaded" ? read.value : null;
  const items = useMemo(() => (loaded === null ? [] : decisionItems(loaded.first, loaded.rows)), [loaded]);
  const waiting = loaded === null ? 0 : waitingForAChoice(items, waitingTotalOf(loaded));
  const waitingRows = useMemo(() => items.filter((i) => i.state === "waiting"), [items]);
  const progress = loaded === null ? [] : loaded.first.progress.rows.slice(0, INBOX_SINCE_CAP);
  const api = useDrawers();

  const pending =
    read === null ? <p className="estate-loading">{INBOX_COPY.loading}</p> : read.status === "refused" ? <p>{read.copy}</p> : null;

  return (
    <>
      <button
        type="button"
        className="ia-inbox"
        aria-haspopup="dialog"
        aria-controls={INBOX_ID}
        onClick={(event) => api.open(INBOX_ID, event.currentTarget)}
      >
        <RailIcon name="action" />
        <span className="ia-inbox__label">{INBOX_TITLE}</span>
        {waiting > 0 ? (
          <span className="ia-inbox__badge">
            <span aria-hidden="true">{waiting}</span>
            <span className="visually-hidden">, {waiting} waiting</span>
          </span>
        ) : null}
      </button>
      <div id={INBOX_ID}>
        <Drawer id={INBOX_ID} title={INBOX_TITLE} api={api}>
          <section className="ia-inbox__section" aria-labelledby="ia-inbox-for-you">
            <h3 id="ia-inbox-for-you">{INBOX_COPY.forYou}</h3>
            <p>{NOT_AVAILABLE_YET}</p>
          </section>
          <section className="ia-inbox__section" aria-labelledby="ia-inbox-portfolio">
            <h3 id="ia-inbox-portfolio">{INBOX_COPY.portfolio}</h3>
            {pending ??
              (waitingRows.length === 0 ? (
                <p>{INBOX_COPY.nothingWaiting}</p>
              ) : (
                <>
                  <ul className="ia-inbox__rows">
                    {waitingRows.slice(0, INBOX_CAP).map((i) => {
                      const words = (
                        <>
                          {i.row.title} <small>{i.row.site_name} · {PLACEMENT_GROUP_LABEL[i.row.placement.group]}</small>
                        </>
                      );
                      return (
                        <li key={i.row.finding_id}>
                          {i.target === null ? (
                            <span>{words}</span>
                          ) : (
                            <Link to={i.target} onClick={api.close}>
                              {words}
                            </Link>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                  {waiting > Math.min(waitingRows.length, INBOX_CAP) ? (
                    <Link to={withRange(`${DECISIONS_PATH}?state=waiting`, params)} onClick={api.close}>
                      View all {waiting}
                    </Link>
                  ) : null}
                </>
              ))}
          </section>
          <section className="ia-inbox__section" aria-labelledby="ia-inbox-since">
            <h3 id="ia-inbox-since">{INBOX_COPY.since}</h3>
            {pending ?? (
              <>
                {progress.length === 0 ? (
                  <p>{INBOX_COPY.noChange}</p>
                ) : (
                  <ul className="ia-inbox__rows">
                    {progress.map((r) => (
                      <li key={r.action_id}>
                        Action {displayCode(r.action_code)} · {progressOutcomeWords(r.verification_outcome)}
                      </li>
                    ))}
                  </ul>
                )}
                <Link to={withRange(RESULTS_PATH, params)} onClick={api.close}>
                  {INBOX_COPY.seeResults}
                </Link>
              </>
            )}
          </section>
        </Drawer>
      </div>
    </>
  );
}
