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

/** 5c: a JSON fixture or captured markup read as text (`?raw`): the backend's hand-written World A fixture. */
declare module "*.json?raw" {
  const source: string;
  export default source;
}

declare module "*.html?raw" {
  const source: string;
  export default source;
}
