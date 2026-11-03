/** Test-only: the backend source read as text by the bundler (`?raw`), for cross-language parity checks. */
declare module "*.py?raw" {
  const source: string;
  export default source;
}

/** Test-only: a frontend source read as text (`?raw`), e.g. App.tsx for the CH-0 screen-route list. */
declare module "*.tsx?raw" {
  const source: string;
  export default source;
}
