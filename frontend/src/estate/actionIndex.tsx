/**
 * The estate Actions words that outlived the root's table. IA-P P2 (spec §5.2) moved the Actions root onto the
 * home-list component (`estate/homeLists.tsx`); the route and the row-title rule stay here, reused.
 */
import { displayCode } from "../ui/displayCode";
import type { EstateActionRow } from "./estateClient";

export const ESTATE_ACTIONS_PATH = "/actions";

/**
 * Post-W6 W3-estate Q5 (R293): the row title is the selected stored `action_title` when present, otherwise the
 * `action_code` alone. No Action-kind wording is supplied by the page.
 */
export function actionRowTitle(row: Pick<EstateActionRow, "action_title" | "action_code">): string {
  const title: unknown = row.action_title;
  return typeof title === "string" && title.trim() !== "" ? title : displayCode(row.action_code);
}

