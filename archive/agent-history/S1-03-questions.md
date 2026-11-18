# S1-03 questions (choices made under the ambiguity rule; Architect may overrule)

1. **Narrow viewport shell.** At 390 px the operator rail kept its 216 px column and left the Foundation about 95 px of content, so a 390 px comparison was impossible. Added one shell-wide rule, `@media (max-width: 640px)` in `ui/primitives.css`, that stacks the rail above the content as a wrapping row and sets a 16 px gutter. Every page at ≤640 px changes, including the Lab shell, which shares `.app-frame`. Options: (a) keep it (chosen); (b) scope it to operator Site pages; (c) defer it to V-01 and accept a 390 px failure here.
2. **Legacy Site view addresses.** `/sites/{legacy}/foundation/sld` and `/readiness` render a named panel, "This view needs an imported Site", with a link back to the Foundation. Alternative: a redirect to `/foundation`. Chosen because a shared link should say why it does not show the view.
3. **Legacy-only panels left off the imported Site model:**
   - "Configuration is fixed at creation" is false once the reserve can change.
   - "Key parameters" duplicates the ratings on the topology cards and in the components table.
   - "Not available for this site / Integration readiness" is superseded by the Readiness view.
   The legacy page keeps all three.
4. **Unbound channels on the SLD parts table** are listed under the component their device attaches to. For example, the unbound `battery-pcs-controller / state-of-charge` channel appears under the Battery power conversion system. The bound SOC channel itself appears under Battery, the asset it describes. Alternative: list the unbound channel under the asset its role would describe, which needs a role-to-asset inference S1 does not hold.
