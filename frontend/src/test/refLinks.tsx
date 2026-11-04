import type { ReactNode } from "react";
import { MemoryRouter, type MemoryRouterProps } from "react-router-dom";
import { linkFor } from "../shell/operatorSiteRoutes";
import { RefLinkProvider } from "../sites/chainRef";

/**
 * CH-5a2a: a `MemoryRouter` that also provides the shell's `linkFor` to Site components, as `App.tsx` does. A Site
 * component rendered outside a `RefLinkProvider` throws (`sites/chainRef.ts` `useLinkFor`).
 */
export function LinkedMemoryRouter({ children, ...props }: MemoryRouterProps & { children?: ReactNode }) {
  return (
    <MemoryRouter {...props}>
      <RefLinkProvider value={linkFor}>{children}</RefLinkProvider>
    </MemoryRouter>
  );
}
