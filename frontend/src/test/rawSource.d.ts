/** Test-only: the backend source read as text by the bundler (`?raw`), for cross-language parity checks. */
declare module "*.py?raw" {
  const source: string;
  export default source;
}
