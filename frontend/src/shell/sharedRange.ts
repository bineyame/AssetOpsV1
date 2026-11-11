/**
 * SR-2b: the shared range lives in `ui/sharedRange.ts` so Site pages (a leaf substrate that must not import shell
 * code, `tools/checks/site-substrate.ps1`) can read it through `ui/FocusPicker`. The shell keeps this name.
 */
export * from "../ui/sharedRange";
