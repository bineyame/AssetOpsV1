# Seam: Mockup fidelity versus product honesty (navigation half).
#
# A navigation destination appears only when the route behind it renders a
# truthful surface. A site is addressed by `site_id`, so the parameterless
# `/site-details` and `/site-configuration` placeholders are gone and the
# identified routes replaced them.
#
# T011A adds the operator Site tab row, which is the same rule applied one
# level down: a tab is a destination only when a route renders a truthful
# surface for the identified site, and a tab that names an aspect the product
# cannot show yet is a label and nothing else - never a disabled control, which
# would say the capability exists and is switched off.
#
# W1-UX-07 (D-2026-10-17-w1-rail) shows the full v6.9 operator rail: two live
# roots and nine unavailable ones rendered as text. Get-OperatorRailFailures
# holds that inventory to the ruling; its fixtures are
# tools/checks/navigation-rail-fixtures.ps1.
#
# W1-F5b (D-2026-10-17-f5-subtabs-and-contact) extends the owner's rule to the
# named in-page tab rows and the Site Findings lens chips, as a narrow declared
# inventory: Get-InPageUnavailableEntryFailures. Its fixtures are in the same
# fixtures file.
#
# Do not weaken the checks below to make a task pass.

function Invoke-NavigationTruthfulnessCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    # These are paired assertions on purpose: a lone "the placeholder is
    # absent" check would also pass on a tree where nothing addresses a site at
    # all, so the identified route has to be found for the absence to mean
    # anything - the route parameter is what is looked for, because the path
    # itself is built from the Sites path constant rather than spelled out.
    #
    # T008 removed `/site-configuration`, so it is banned here the same way.
    # Its identified replacement is looked for as a path built ON the site's
    # own address rather than beside it, which is the invariant worth holding:
    # a Foundation that hangs off `${SITE_DETAIL_ROUTE_PATH}` cannot quietly
    # become a parameterless destination again, because it has nowhere to put
    # the identity it would have to drop.
    #
    # The two parameterless bans keep their T002 spelling. They name addresses
    # this product removed, not a surface it still has, so `Site Configuration`
    # is the right words for what is being refused.
    $identifiedSiteRoutePath = 0
    $identifiedSiteFoundationRoutePath = 0

    # The address T008 served the Foundation at. It survives only as a
    # compatibility redirect, and only the route table may name it: an href
    # builder, a link, a tab or a breadcrumb that reached for it would be the
    # old name coming back as a second way in.
    $legacyFoundationAddress = '/configuration'
    $legacyFoundationAddressOwner = "frontend/src/shell/operatorSiteRoutes.ts"
    $legacyFoundationRouteTable = "frontend/src/App.tsx"
    $legacyFoundationAddressSightings = 0

    foreach ($module in (Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            if ($line -match '["'']/site-details') {
                $failures.Add(("Parameterless site destination at " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). A site is " +
                    "addressed by site_id; a Site Details link that names no " +
                    "site is not a destination.")) | Out-Null
            }

            if ($line -match '["'']/site-configuration') {
                $failures.Add(("Parameterless site destination at " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). A site is " +
                    "addressed by site_id; a Site Configuration link that names " +
                    "no site is not a destination.")) | Out-Null
            }

            if ($line -match '/:siteId') {
                $identifiedSiteRoutePath++
            }

            if ($line -match '\$\{SITE_DETAIL_ROUTE_PATH\}/foundation') {
                $identifiedSiteFoundationRoutePath++
            }

            # The legacy address, anywhere it is spelled as a path fragment.
            # Comments are not exempt: this is a string match, and a comment
            # that has to spell it can spell it without a leading slash.
            if ($line -match [regex]::Escape($legacyFoundationAddress)) {
                if ($module.Path -eq $legacyFoundationAddressOwner) {
                    $legacyFoundationAddressSightings++
                    continue
                }

                if ($module.Path -eq $legacyFoundationRouteTable) { continue }

                $failures.Add(("The legacy Foundation address is named at " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). " +
                    "'$legacyFoundationAddress' is a compatibility redirect, " +
                    "declared once in $legacyFoundationAddressOwner and " +
                    "registered once in $legacyFoundationRouteTable. Nothing " +
                    "else may link, tab, or build it: the surface is " +
                    "/foundation.")) | Out-Null
            }
        }
    }

    if ($identifiedSiteRoutePath -eq 0) {
        $failures.Add(("No identified site route was found in frontend/src, so " +
            "the navigation-truthfulness check is vacuous. Update the check, " +
            "do not delete it.")) | Out-Null
    }

    if ($identifiedSiteFoundationRoutePath -eq 0) {
        $failures.Add(("No identified Foundation route was found in " +
            "frontend/src, so banning the parameterless one proves nothing. " +
            "A site's Foundation is addressed under that site. Update the " +
            "check, do not delete it.")) | Out-Null
    }

    if ($legacyFoundationAddressSightings -eq 0) {
        $failures.Add(("$legacyFoundationAddressOwner no longer declares the " +
            "legacy Foundation address, so the check that confines it is " +
            "vacuous. Either the compatibility redirect was dropped, which is " +
            "a product decision and not a cleanup, or the declaration moved. " +
            "Update the check, do not delete it.")) | Out-Null
    }

    foreach ($failure in (Get-OperatorSiteTabFailures)) {
        $failures.Add($failure) | Out-Null
    }

    foreach ($failure in (Get-FoundationSubtabFailures)) {
        $failures.Add($failure) | Out-Null
    }

    foreach ($failure in (Get-InPageUnavailableEntryFailures)) {
        $failures.Add($failure) | Out-Null
    }

    return $failures
}

# The operator Site tab row: one definition, in the operator shell, carrying
# operator vocabulary and no disabled affordance.
function Get-OperatorSiteTabFailures {
    $failures = New-Object System.Collections.Generic.List[string]

    $inventoryName = "OPERATOR_SITE_TABS"
    $shellRoot = "frontend/src/shell"
    $substrateRoot = "frontend/src/sites"

    # The mockup's Site tabs in `ScreenMockups.png` screen 2. They are the
    # Lab's run vocabulary: layout evidence that a Site page has a tab row, and
    # not vocabulary authority for the operator product.
    $labRunTabVocabulary = @(
        "Configuration", "Devices", "Gateway", "Ingestion", "Events", "Logs"
    )

    # A tab that the product cannot open is a label. Disabled says the
    # capability exists and is unavailable right now, which is a different and
    # false claim, and a title attribute is the same claim whispered.
    $disabledAffordance = @(
        '\bdisabled\s*[=:]',
        'aria-disabled\s*=',
        'not-allowed',
        'coming soon',
        '\btitle\s*='
    )

    $declarations = @()
    $inventoryModules = @()

    foreach ($module in (Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))) {
        $declaresInventory = $false

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -match "(?:const|let|var|enum)\s+$inventoryName\s*(?::|=)") {
                $declarations += "$($module.Path):${lineNumber}"
                $declaresInventory = $true
            }
        }

        if ($declaresInventory) { $inventoryModules += $module }
    }

    if ($declarations.Count -eq 0) {
        $failures.Add(("No module declares $inventoryName, so every operator " +
            "Site tab check below is vacuous. The tab row renders from one " +
            "inventory that the rendering and the tests both read. Update the " +
            "check, do not delete it.")) | Out-Null
        return $failures
    }

    if ($declarations.Count -gt 1) {
        $failures.Add(("$inventoryName is declared in " +
            "$($declarations -join ', '). The operator Site tab row has one " +
            "definition; two are two answers to what a Site is divided into.")) | Out-Null
    }

    foreach ($module in $inventoryModules) {
        if ($module.Path.StartsWith("$substrateRoot/")) {
            $failures.Add(("$inventoryName is declared in $($module.Path), " +
                "inside the shared Site substrate. The substrate owns what a " +
                "Site is; which aspects a workspace divides it into is a " +
                "shell's opinion, and the Lab's Site view will hold a " +
                "different one. It belongs in $shellRoot.")) | Out-Null
        }
        elseif (-not $module.Path.StartsWith("$shellRoot/")) {
            $failures.Add(("$inventoryName is declared in $($module.Path). " +
                "The operator Site tab row belongs to the operator shell, in " +
                "$shellRoot.")) | Out-Null
        }

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            foreach ($label in $labRunTabVocabulary) {
                if ($line -match "label\s*:\s*[""']$label[""']") {
                    $failures.Add(("Lab run tab vocabulary in the operator " +
                        "Site tab row at $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). '$label' is a Simulator Lab run tab " +
                        "from the mockup, not an operator Site tab. The " +
                        "operator vocabulary is v6.9's at lines 464 and 615.")) | Out-Null
                }
            }

            foreach ($pattern in $disabledAffordance) {
                if ($line -match $pattern) {
                    $failures.Add(("Disabled affordance in the operator Site " +
                        "tab row at $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). A tab the product cannot open is " +
                        "not rendered, never disabled, never labelled in " +
                        "place in operator views " +
                        "(D-2026-10-02-rendered-tabs-per-capability): these " +
                        "are not switched off, they are not built.")) | Out-Null
                    break
                }
            }

            if ($line -match 'labelled_in_place' -or $line -match 'kind\s*:\s*[""'']labelled') {
                $failures.Add(("Labelled-in-place tab kind in the operator " +
                    "Site tab row at $($module.Path):${lineNumber}: " +
                    "$($line.Trim()). A tab the product cannot open is not " +
                    "rendered, never disabled, never labelled in place in " +
                    "operator views " +
                    "(D-2026-10-02-rendered-tabs-per-capability). The row " +
                    "renders the canonical inventory filtered by " +
                    "capability.")) | Out-Null
            }
        }
    }

    # T027 fix round N7: three more rules, each paired with a presence check so
    # that an absence is never read from a tree that stopped declaring the thing.
    #
    # 1. The rendered row is the inventory filtered by capability. Without the
    #    filter every tab is rendered, including those the product cannot open.
    foreach ($module in $inventoryModules) {
        $text = ($module.Lines -join "`n")
        if ($text -notmatch ($inventoryName + '\s*(?::[^=]+)?=\s*CANONICAL_' + $inventoryName +
                '\s*\.filter\(\s*\(?\s*\w+\s*\)?\s*=>\s*\w+\.capability\s*\)')) {
            $failures.Add(("$inventoryName in $($module.Path) is not " +
                "CANONICAL_$inventoryName filtered by capability. The tab row " +
                "renders only tabs the product can open " +
                "(D-2026-10-02-rendered-tabs-per-capability); an unfiltered " +
                "inventory renders every tab.")) | Out-Null
        }
    }

    # 2. The operator rail: see Get-OperatorRailFailures (W1-UX-07).
    foreach ($failure in (Get-OperatorRailFailures)) {
        $failures.Add($failure) | Out-Null
    }

    # 3. `/` redirects to Sites rather than rendering a placeholder frame.
    $appModule = @(Get-ScannedModules -Root "frontend/src" -Extensions @(".tsx") |
        Where-Object { $_.Path -eq "frontend/src/App.tsx" })
    if ($appModule.Count -eq 0 -or
        (($appModule[0].Lines -join "`n") -notmatch
            'path\s*=\s*"/"\s+element\s*=\s*\{\s*<Navigate\s+to=\{SITES_PATH\}\s+replace\s*/>\s*\}')) {
        $failures.Add(("frontend/src/App.tsx does not redirect / to Sites " +
            "(Route path=""/"" with Navigate to SITES_PATH, replace). " +
            "T027 removed the Operator home placeholder; / has no surface of " +
            "its own.")) | Out-Null
    }

    return $failures
}

# The Foundation view row (S1-03): one definition, in the shared substrate,
# naming exactly the three supported views - Site model, Single line diagram,
# Readiness, in v6.9's order - with `Changes` absent and the superseded
# vocabulary (including the old Definition | Topology | Controls contents row)
# gone.
#
# This row lives in the substrate rather than a shell, unlike the operator Site
# tab row above it. The difference is real: which aspects a workspace divides a
# Site into is a shell's opinion, but what a Foundation is made of is the same
# whoever renders it, so both shells present these four.
function Get-FoundationSubtabFailures {
    $failures = New-Object System.Collections.Generic.List[string]

    $inventoryName = "FOUNDATION_SUBTABS"
    $substrateRoot = "frontend/src/sites"

    # The three supported views, in order (Architect decision
    # D-2026-10-08-s1-foundation-organization, section 2, which revises the
    # S1-02 D2 ruling that kept Readiness off this row). `Readiness` is S1-02
    # configuration readiness; claim/capability readiness stays on Site >
    # Evidence. Every view is navigable: none is disabled or labelled in place.
    #
    # W1-F5b (D-2026-10-17-f5-subtabs-and-contact): the owner's full mock-menu
    # rule restores the mock's fourth entry, `Change & effect`, declared once
    # after the three views as a live link to the existing Foundation Changes
    # route. It is the only addition: the row is still exactly these labels.
    $requiredViews = @("Site model", "Single line diagram", "Readiness", "Change & effect")

    # `Changes` is filtered out by the accepted T008
    # checkpoint: lines 2149 and 2225-2228 make it a real intervention and
    # change-effect capability rather than the mockup's `Version History`, no
    # configuration-change model exists, and naming it would promise a meaning
    # a reader would guess wrongly. Absent in every state, not labelled.
    # W1-F5b: `Change & effect` is now the declared fourth entry (above); the
    # other spellings stay forbidden so the row has one name for it.
    $forbiddenSubtab = "Changes"
    $forbiddenChangeLabels = @("Change and effect")

    # What T013 replaced. These were the old mockup-derived subtab names and
    # they must not come back as a Foundation subtab row.
    # S1-03 adds the Definition | Topology | Controls contents row it replaced.
    $supersededVocabulary = @("Summary", "Components", "Control Logic", "Settings",
        "Definition", "Topology", "Controls")

    # A subtab this build cannot open is not rendered, never disabled, never
    # labelled in place in operator views. Same rule as the tab row above, same
    # reason (D-2026-10-02-rendered-tabs-per-capability).
    $disabledAffordance = @(
        '\bdisabled\s*[=:]',
        'aria-disabled\s*=',
        'not-allowed',
        'coming soon',
        '\btitle\s*='
    )

    # A quoted literal may use ", ' or a backtick.
    $quote = '["''`]'

    $declarations = @()
    $inventoryModules = @()

    foreach ($module in (Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))) {
        $declaresInventory = $false

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -match "(?:const|let|var|enum)\s+$inventoryName\s*(?::|=)") {
                $declarations += "$($module.Path):${lineNumber}"
                $declaresInventory = $true
            }
        }

        if ($declaresInventory) { $inventoryModules += $module }
    }

    if ($declarations.Count -eq 0) {
        $failures.Add(("No module declares $inventoryName, so every Foundation " +
            "subtab check below is vacuous. The row renders from one inventory " +
            "that the rendering and the tests both read. Update the check, do " +
            "not delete it.")) | Out-Null
        return $failures
    }

    if ($declarations.Count -gt 1) {
        $failures.Add(("$inventoryName is declared in " +
            "$($declarations -join ', '). The Foundation subtab row has one " +
            "definition; two are two answers to what a Foundation is made of.")) | Out-Null
    }

    foreach ($module in $inventoryModules) {
        if (-not $module.Path.StartsWith("$substrateRoot/")) {
            $failures.Add(("$inventoryName is declared in $($module.Path). " +
                "What a Foundation is made of is the same whoever renders it, " +
                "so the row belongs in the shared substrate at $substrateRoot, " +
                "not in a shell.")) | Out-Null
        }

        $declaredLabels = @()
        foreach ($line in $module.Lines) {
            $labelMatch = [regex]::Match($line, "label\s*:\s*$quote([^""'``$]+)$quote")
            if ($labelMatch.Success) { $declaredLabels += $labelMatch.Groups[1].Value }
            elseif ($line -match 'label\s*:' -and $line -notmatch 'label\s*:\s*string\s*[;,]?\s*$') {
                $failures.Add(("A Foundation view label is not a plain string " +
                    "literal at $($module.Path): $($line.Trim()). A label held in " +
                    "a constant or built from a template could say anything, so " +
                    "this check cannot tell which views the row offers.")) | Out-Null
            }
        }
        if (($declaredLabels -join "|") -ne ($requiredViews -join "|")) {
            $failures.Add(("$inventoryName in $($module.Path) declares " +
                "'$($declaredLabels -join ", ")'. The Foundation view row is " +
                "exactly '$($requiredViews -join ", ")', in v6.9's order " +
                "(D-2026-10-08-s1-foundation-organization, " +
                "D-2026-10-17-f5-subtabs-and-contact): three supported, " +
                "navigable views, then Change & effect, and no other.")) | Out-Null
        }

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            foreach ($changeLabel in $forbiddenChangeLabels) {
                if ($line -match ("label\s*:\s*$quote" + [regex]::Escape($changeLabel) + $quote)) {
                    $failures.Add(("'$changeLabel' is declared as a Foundation " +
                        "view at $($module.Path):${lineNumber}. v6.9 makes it an " +
                        "intervention and change-effect capability with no " +
                        "supported model; it is absent in every state.")) | Out-Null
                }
            }

            if ($line -match "label\s*:\s*$quote$forbiddenSubtab$quote") {
                $failures.Add(("'$forbiddenSubtab' is declared as a Foundation " +
                    "subtab at $($module.Path):${lineNumber}: $($line.Trim()). " +
                    "v6.9 makes it an intervention and change-effect " +
                    "capability, no configuration-change model exists, and the " +
                    "T008 checkpoint removed that territory rather than " +
                    "leaving it as chrome. It is absent in every state, not " +
                    "labelled in place.")) | Out-Null
            }

            foreach ($label in $supersededVocabulary) {
                if ($line -match "label\s*:\s*$quote$label$quote") {
                    $failures.Add(("Superseded Foundation subtab vocabulary at " +
                        "$($module.Path):${lineNumber}: $($line.Trim()). " +
                        "'$label' is the mockup-derived name T013 replaced; the " +
                        "row is v6.9's at line 2117, filtered.")) | Out-Null
                }
            }

            foreach ($pattern in $disabledAffordance) {
                if ($line -match $pattern) {
                    $failures.Add(("Disabled affordance in the Foundation " +
                        "subtab row at $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). A subtab this build cannot open is " +
                        "not rendered, never disabled, never labelled in " +
                        "place in operator views.")) | Out-Null
                    break
                }
            }

            if ($line -match 'labelled_in_place' -or $line -match 'kind\s*:\s*[""'']labelled') {
                $failures.Add(("Labelled-in-place subtab kind in the " +
                    "Foundation subtab row at $($module.Path):${lineNumber}: " +
                    "$($line.Trim()). A subtab this build cannot open is not " +
                    "rendered, never disabled, never labelled in place in " +
                    "operator views " +
                    "(D-2026-10-02-rendered-tabs-per-capability).")) | Out-Null
            }

        }
    }


    # A Change & effect / Changes destination hard-coded anywhere else in the
    # app (beside the view row, inside a view) is the same absent capability,
    # enabled, disabled or labelled in place. Rendered pages are also checked
    # in frontend tests; this catches it at the source.
    foreach ($module in (Get-ScannedModules -Root "frontend/src" -Extensions @(".tsx"))) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -match '>\s*(Changes|Change\s*(&amp;|&|and)\s*effect)\s*<' -or
                $line -match '(?:aria-label|title)="\s*(Changes|Change\s*(&amp;|&|and)\s*effect)\s*"') {
                $failures.Add(("A '$($Matches[1])' destination is written into " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). v6.9 makes it " +
                    "an intervention and change-effect capability with no " +
                    "supported model; it is absent in every state, not " +
                    "disabled and not labelled in place.")) | Out-Null
            }
        }
    }

    return $failures
}

# The operator rail (W1-UX-07, owner decision 2026-10-17,
# D-2026-10-17-w1-rail): the full v6.9 root inventory is visible, and only
# roots with a truthful cross-site destination are links. This is a scoped
# exception to the live-items-only rail, never to the Site tab rules above,
# which still reject disabled affordances and labelled-in-place capabilities.
#
# Invariants, all fail-closed:
#   - the inventory `operatorRailItems` is found, parsed line by line, and is
#     what the shell passes to NavRail; an unparseable line fails;
#   - exactly the six groups and eleven roots, in v6.9 order, with exactly two
#     live roots: Sites -> /sites and Findings -> /findings;
#   - an unavailable root carries no destination or handler (to, href, end,
#     onClick, onKeyDown, tabIndex);
#   - each live target is registered in the operator route table, inside
#     OperatorShellLayout and not as the `*` catch-all (whose `Page not
#     available` frame never counts as a route);
#   - NavRail's model still forbids `to` on an unavailable item.
#
# Parameters exist so tools/checks/navigation-rail-fixtures.ps1 can feed mutated
# fixtures; with none, the real files are read.
function Get-OperatorRailFailures {
    param(
        [string[]] $RailLines,
        [string[]] $AppLines,
        [string[]] $RouteConstantLines,
        [string[]] $NavRailLines
    )
    $failures = New-Object System.Collections.Generic.List[string]
    $railPath = "frontend/src/shell/OperatorShellLayout.tsx"
    $appPath = "frontend/src/App.tsx"
    $navRailPath = "frontend/src/ui/NavRail.tsx"

    if ($null -eq $RailLines -and (Test-Path -LiteralPath $railPath -PathType Leaf)) {
        $RailLines = @(Get-Content -LiteralPath $railPath)
    }
    if ($null -eq $AppLines -and (Test-Path -LiteralPath $appPath -PathType Leaf)) {
        $AppLines = @(Get-Content -LiteralPath $appPath)
    }
    if ($null -eq $NavRailLines -and (Test-Path -LiteralPath $navRailPath -PathType Leaf)) {
        $NavRailLines = @(Get-Content -LiteralPath $navRailPath)
    }
    if ($null -eq $RouteConstantLines) {
        $RouteConstantLines = @()
        foreach ($file in @(Get-ChildItem -LiteralPath "frontend/src/shell" -File |
                Where-Object { $_.Extension -in @(".ts", ".tsx") })) {
            $RouteConstantLines += @(Get-Content -LiteralPath $file.FullName)
        }
    }
    foreach ($pair in @(@($railPath, $RailLines), @($appPath, $AppLines), @($navRailPath, $NavRailLines))) {
        if ($null -eq $pair[1] -or @($pair[1]).Count -eq 0) {
            $failures.Add(("$($pair[0]) was not found or is empty, so the operator " +
                "rail check is vacuous. Update the check, do not delete it.")) | Out-Null
        }
    }
    if ($failures.Count -gt 0) { return $failures }

    $expected = @(
        "live|Portfolio|OPERATIONS|/portfolio",
        "live|Sites|OPERATIONS|/sites",
        "unavailable|Assets|OPERATIONS|",
        "live|Findings|INTELLIGENCE|/findings",
        "live|Actions|WORK|/actions",
        "live|Incidents|WORK|/incidents",
        "live|Maintenance|WORK|/maintenance",
        "live|Operational records|WORK|/operational-records",
        "live|Evidence|ASSURANCE|/evidence",
        "live|Financials|BUSINESS|/financials",
        "unavailable|Settings|ADMIN|"
    )
    $allowedKeys = @("kind", "to", "label", "end", "group", "icon")
    $forbiddenOnUnavailable = @("to", "href", "end", "onClick", "onKeyDown", "tabIndex")
    $propPattern = '(\w+)\s*:\s*("([^"]*)"|''([^'']*)''|true|false|[^,}]+)'

    # Locate the inventory.
    $start = -1
    for ($i = 0; $i -lt $RailLines.Count; $i++) {
        if ($RailLines[$i] -match '^\s*const\s+operatorRailItems\s*:\s*NavRailItem\[\]\s*=\s*\[\s*$') {
            $start = $i
            break
        }
    }
    if ($start -lt 0) {
        $failures.Add(("$railPath declares no 'const operatorRailItems: NavRailItem[] = [' " +
            "inventory, so the operator rail cannot be checked. Update the check, " +
            "do not delete it.")) | Out-Null
        return $failures
    }
    $found = @()
    $end = -1
    $liveTargets = @()
    for ($i = $start + 1; $i -lt $RailLines.Count; $i++) {
        $line = $RailLines[$i]
        $lineNumber = $i + 1
        if ($line -match '^\s*\];\s*$') { $end = $i; break }
        if ($line -match '^\s*$' -or $line -match '^\s*(//|/?\*)') { continue }
        if ($line -notmatch '^\s*\{(.*)\},?\s*$') {
            $failures.Add(("Unparseable operator rail line at ${railPath}:${lineNumber}: " +
                "$($line.Trim()). One item object per line.")) | Out-Null
            continue
        }
        $body = $Matches[1]
        $props = @{}
        foreach ($m in [regex]::Matches($body, $propPattern)) {
            $value = if ($m.Groups[3].Success) { $m.Groups[3].Value }
                elseif ($m.Groups[4].Success) { $m.Groups[4].Value }
                else { $m.Groups[2].Value.Trim() }
            $props[$m.Groups[1].Value] = $value
        }
        $residue = ([regex]::Replace($body, $propPattern, '')) -replace '[\s,]', ''
        if ($residue -ne "") {
            $failures.Add(("Unparseable operator rail item at ${railPath}:${lineNumber}: " +
                "$($line.Trim()) (left over: $residue).")) | Out-Null
        }
        foreach ($key in $props.Keys) {
            if ($allowedKeys -notcontains $key) {
                $failures.Add(("Operator rail item at ${railPath}:${lineNumber} carries " +
                    "'$key', which the rail model does not have: $($line.Trim())")) | Out-Null
            }
        }
        $kind = if ($props.ContainsKey("kind")) { $props["kind"] } else { "" }
        if ($kind -notin @("live", "unavailable")) {
            $failures.Add(("Operator rail item at ${railPath}:${lineNumber} has no explicit " +
                "kind 'live' or 'unavailable': $($line.Trim())")) | Out-Null
        }
        if ($kind -eq "unavailable") {
            foreach ($key in $forbiddenOnUnavailable) {
                if ($props.ContainsKey($key)) {
                    $failures.Add(("Dead link: the unavailable operator rail root " +
                        "'$($props["label"])' carries '$key' at ${railPath}:${lineNumber}. " +
                        "An unavailable root is text, never a destination " +
                        "(D-2026-10-17-w1-rail).")) | Out-Null
                }
            }
        }
        $to = if ($props.ContainsKey("to")) { $props["to"] } else { "" }
        if ($kind -eq "live") {
            $liveTargets += [pscustomobject]@{ To = $to; Label = $props["label"]; Line = $lineNumber }
        }
        $found += "$kind|$($props["label"])|$($props["group"])|$to"
    }
    if ($end -lt 0) {
        $failures.Add(("The operator rail inventory in $railPath is not closed by '];' " +
            "on its own line, so it cannot be parsed. Update the check.")) | Out-Null
        $end = $RailLines.Count - 1
    }
    if ($found.Count -eq 0) {
        $failures.Add(("$railPath declares no operator rail items, so the rail rule " +
            "is vacuous. Update the check, do not delete it.")) | Out-Null
    }
    elseif (($found -join ";") -ne ($expected -join ";")) {
        $failures.Add(("$railPath declares the rail items [$($found -join '; ')] but " +
            "the W1 rail is exactly [$($expected -join '; ')] (kind|label|group|to, in " +
            "order; D-2026-10-17-w1-rail). A root becomes live only in the slice " +
            "that supplies its cross-site route, with this list changed and reviewed.")) | Out-Null
    }

    # The shell renders this inventory, and no destination outside it.
    if (($RailLines -join "`n") -notmatch '<NavRail\s+label="Operator routes"\s+items=\{operatorRailItems\}\s*/>') {
        $failures.Add(("$railPath does not pass operatorRailItems to the 'Operator routes' " +
            "NavRail, so the checked inventory is not what renders.")) | Out-Null
    }
    for ($i = 0; $i -lt $RailLines.Count; $i++) {
        $line = $RailLines[$i]
        $lineNumber = $i + 1
        if ($line -match '^\s*(//|/?\*)') { continue }
        if ($line -match 'Operator home') {
            $failures.Add(("Operator home returned to the operator rail at " +
                "${railPath}:${lineNumber}: $($line.Trim()). T027 removed it; " +
                "/ redirects to Sites.")) | Out-Null
        }
        if ($i -ge $start -and $i -le $end) { continue }
        if ($line -match '<(NavLink|Link|a)\b|\bhref\s*=|\bto\s*[:=]') {
            $failures.Add(("A navigation destination outside the checked inventory at " +
                "${railPath}:${lineNumber}: $($line.Trim()).")) | Out-Null
        }
    }

    # Each live target is a registered operator route, not the catch-all.
    $constants = @{}
    foreach ($line in $RouteConstantLines) {
        if ($line -match '^\s*export\s+const\s+(\w+)\s*=\s*"([^"]+)"\s*;') {
            $constants[$Matches[1]] = $Matches[2]
        }
    }
    $operatorStart = -1
    $catchAll = -1
    for ($i = 0; $i -lt $AppLines.Count; $i++) {
        if ($operatorStart -lt 0 -and $AppLines[$i] -match '<Route\s+element=\{<OperatorShellLayout\s*/>\}>') {
            $operatorStart = $i
        }
        if ($AppLines[$i] -match 'path\s*=\s*"\*"') { $catchAll = $i }
    }
    if ($operatorStart -lt 0 -or $catchAll -lt 0 -or $catchAll -lt $operatorStart) {
        $failures.Add(("$appPath has no '<Route element={<OperatorShellLayout />}>' block " +
            "before a 'path=""*""' catch-all, so live rail targets cannot be proven " +
            "registered. Update the check, do not delete it.")) | Out-Null
    }
    else {
        foreach ($target in $liveTargets) {
            $registered = $false
            for ($i = $operatorStart + 1; $i -lt $catchAll; $i++) {
                $line = $AppLines[$i]
                if ($line -match 'path\s*=\s*"([^"]+)"' -and $Matches[1] -eq $target.To) {
                    $registered = $true
                }
                elseif ($line -match 'path\s*=\s*\{(\w+)\}' -and $constants.ContainsKey($Matches[1]) -and
                    $constants[$Matches[1]] -eq $target.To) {
                    $registered = $true
                }
            }
            if (-not $registered) {
                $failures.Add(("The live operator rail root '$($target.Label)' points at " +
                    "'$($target.To)' (${railPath}:$($target.Line)), which is not a route " +
                    "registered in the operator route table of $appPath. The catch-all " +
                    "'Page not available' frame is not a destination.")) | Out-Null
            }
        }
    }

    # NavRail's model forbids a destination on an unavailable item.
    if (($NavRailLines -join "`n") -notmatch
        'interface\s+NavRailUnavailableItem[^{]*\{[^}]*kind:\s*"unavailable";[^}]*to\?:\s*never;') {
        $failures.Add(("$navRailPath no longer declares NavRailUnavailableItem with " +
            "kind: ""unavailable"" and to?: never, so the type no longer forbids a " +
            "destination on an unavailable root.")) | Out-Null
    }

    return $failures
}


# W1-F5b (D-2026-10-17-f5-subtabs-and-contact): the unbuilt entries of the named
# v69 in-page rows - Finding > Alternatives, Financials > Scenarios (W1-F5b also listed
# Work > Incidents and Maintenance until W4-01 made them live), and (W2-03 q3, D-2026-10-18-w2-03-answers) the cold
# Performance > Cooling and cold Finding > Recommendation; W2-06 r7 P8 adds the EV
# Performance > Availability and Energy / site power and EV Finding > Recommendation
# (so Recommendation appears twice, once per Finding frame) - and the Site Findings lens chips Cost, Risks and
# Opportunities render as "Not available yet" text through one component,
# frontend/src/ui/UnavailableEntry.tsx. This is a narrow exception to the
# absent-tab rule above, never a general one:
#   - the component is not a control (no to, href, handler, tab stop, button,
#     link, role or disabled state);
#   - the entries rendered through it are exactly the declared multiset (a
#     closed inventory: spelling and multiplicity both matter), with literal labels (the one dynamic use is FindingSections, whose
#     entries are declared as `label: "...", unavailable: true`);
#   - nothing else may render it.
# Parameters exist so the fixtures can feed mutated modules; with none, the
# real tree is read.
function Get-InPageUnavailableEntryFailures {
    param(
        [object[]] $Modules
    )
    $failures = New-Object System.Collections.Generic.List[string]
    $componentPath = "frontend/src/ui/UnavailableEntry.tsx"
    $dynamicOwner = "frontend/src/sites/SiteFindingEvidence.tsx"
    # W1-plus-W2 closed multiset (W2-06 r7 P8): Recommendation x 2 (cold and EV Finding
    # frames), every other entry once. W4-01 (build spec "Per-panel copy and layout
    # dry-read") removes Work > Incidents and Maintenance: both subtabs are live
    # routes now. The rail's unavailable Incidents and Maintenance roots stay (W6).
    # W4-03 unit 6a (closure 4 S13): the Financials subrow is split by Site type; mini
    # Scenarios is a live route, so the one remaining Scenarios entry is cold's (EV has
    # no Scenarios slot).
    # W4-03 unit 6b (closure 4 B4, closure 5, u5 6b, u6 ruling 4): canonical mini Alternatives is a live route, so
    # Alternatives has zero unavailable occurrences; the mini Finding row's Analysis slot is the one new entry.
    # W5-01a C2: cold Performance > Cooling is a live route (`/sites/{site_code}/performance/cooling`), so its
    # one unavailable occurrence is gone; the live subtab and page branch are held below.
    # W6-01b B3 (F4): the global Maintenance page's Preventive view is live, so its B2 entry is gone again.
    # W6-01c C2 (F4): the work request Overview's Context tabs render Maintenance record, Verification and History
    # unavailable, once each in `workRequestShared.tsx`; C3 removes Maintenance record and C4 removes History.
    # W6-01c C3 (F4): the Maintenance record tab is live (`WORK_REQUEST_RECORD_ROUTE_PATH`), so its entry is gone.
    # W6-01d C4 (F4, 2026-10-23): the History tab is live (`WORK_REQUEST_HISTORY_ROUTE_PATH`), so its entry is gone.
    # W5-03a E2: EV Performance > Availability is a live route (`/sites/{site_code}/performance/availability`), so
    # its one unavailable occurrence is gone; the live subtab and page branch are held below.
    # W5-03a E3: EV Performance > Energy / site power is live (`/sites/{site_code}/performance/energy`), so its
    # one unavailable occurrence is gone too; its live subtab and page branch are held below.
    $expectedTabs = @("Scenarios", "Scenarios", "Recommendation", "Recommendation",
        "Analysis", "Verification")
    # W2-F unit 4b (M12): EV Financials/Assumptions carry the mock's Scenarios slot as one literal in EvSiteViews.tsx.
    $expectedChips = @("Cost", "Risks", "Opportunities")

    if ($null -eq $Modules) {
        $Modules = @(Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))
    }

    $component = @($Modules | Where-Object { $_.Path -eq $componentPath })
    if ($component.Count -eq 0) {
        $failures.Add(("$componentPath was not found, so the in-page unavailable " +
            "entry check is vacuous. Update the check, do not delete it.")) | Out-Null
        return $failures
    }

    $forbidden = @(
        @{ Pattern = '\bto\s*=';            Name = "to" },
        @{ Pattern = '\bhref\b';            Name = "href" },
        @{ Pattern = '\bon[A-Z]\w*\s*=';   Name = "an event handler" },
        @{ Pattern = 'tabIndex';             Name = "tabIndex" },
        @{ Pattern = '\bdisabled\b';        Name = "disabled" },
        @{ Pattern = '<button\b';            Name = "a button" },
        @{ Pattern = '<(Link|NavLink|a)\b';  Name = "a link" },
        @{ Pattern = '\brole\s*=';          Name = "a role" },
        @{ Pattern = 'cursor:\s*pointer';    Name = "a pointer affordance" }
    )
    $lineNumber = 0
    foreach ($line in $component[0].Lines) {
        $lineNumber++
        if ($line -match '^\s*(\*|//|/\*)') { continue }
        foreach ($rule in $forbidden) {
            if ($line -match $rule.Pattern) {
                $failures.Add(("The in-page unavailable entry at ${componentPath}:${lineNumber} " +
                    "carries $($rule.Name): $($line.Trim()). An unbuilt tab or chip is " +
                    "readable text, not a control: no destination, handler, tab stop or " +
                    "disabled state (D-2026-10-17-f5-subtabs-and-contact).")) | Out-Null
            }
        }
    }

    $tabs = New-Object System.Collections.Generic.List[string]
    $chips = New-Object System.Collections.Generic.List[string]
    foreach ($module in $Modules) {
        if ($module.Path -eq $componentPath) { continue }
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($m in [regex]::Matches($line, '<Unavailable(Tab|Chip)\b([^>]*)')) {
                $kind = $m.Groups[1].Value
                $literal = [regex]::Match($m.Groups[2].Value, 'label="([^"]+)"')
                if ($literal.Success) {
                    if ($kind -eq "Tab") { $tabs.Add($literal.Groups[1].Value) | Out-Null }
                    else { $chips.Add($literal.Groups[1].Value) | Out-Null }
                }
                elseif (-not ($kind -eq "Tab" -and $module.Path -eq $dynamicOwner)) {
                    $failures.Add(("Unavailable$kind with a non-literal label at " +
                        "$($module.Path):${lineNumber}: $($line.Trim()). The unbuilt in-page " +
                        "entries are a declared inventory; a computed label could name any " +
                        "tab.")) | Out-Null
                }
            }
            foreach ($m in [regex]::Matches($line, 'label:\s*"([^"]+)",\s*unavailable:\s*true')) {
                $tabs.Add($m.Groups[1].Value) | Out-Null
            }
        }
    }

    foreach ($pair in @(@("tab", $expectedTabs, $tabs), @("lens chip", $expectedChips, $chips))) {
        $got = @($pair[2] | Sort-Object)
        $want = @($pair[1] | Sort-Object)
        if (($got -join "|") -ne ($want -join "|")) {
            $failures.Add(("The unbuilt in-page $($pair[0]) entries are '$($pair[2] -join ", ")'; " +
                "the W1-plus-W2 inventory is exactly the multiset '$($pair[1] -join ", ")' " +
                "(D-2026-10-17-f5-subtabs-and-contact, W2-06 r7 P8). An entry becomes live only with " +
                "a reviewed, truthful destination; a new unbuilt entry is a ruling, not a " +
                "cleanup.")) | Out-Null
        }
    }

    # W5-01a C2: the live cold Cooling subtab and its page branch stay in the cold Performance frame.
    $coldFramePath = "frontend/src/sites/ColdAssessmentViews.tsx"
    $coldFrame = @($Modules | Where-Object { $_.Path -eq $coldFramePath })
    $coldText = if ($coldFrame.Count -eq 0) { "" } else { $coldFrame[0].Lines -join "`n" }
    if (-not ($coldText.Contains('data-performance-subtab="cooling"') -and $coldText.Contains('<ColdCooling'))) {
        $failures.Add(("The live cold Cooling subtab or page branch is missing from ${coldFramePath}: it must " +
            "carry both data-performance-subtab=""cooling"" and <ColdCooling (W5-01a C2).")) | Out-Null
    }

    # W5-03a E2: the live EV Availability subtab stays in the EV Performance frame and its page branch in the
    # Site Performance frame.
    $evFramePath = "frontend/src/sites/EvAssessmentViews.tsx"
    $evPagePath = "frontend/src/shell/SiteAnalyticsFrames.tsx"
    $evFrame = @($Modules | Where-Object { $_.Path -eq $evFramePath })
    $evPage = @($Modules | Where-Object { $_.Path -eq $evPagePath })
    $evFrameText = if ($evFrame.Count -eq 0) { "" } else { $evFrame[0].Lines -join "`n" }
    $evPageText = if ($evPage.Count -eq 0) { "" } else { $evPage[0].Lines -join "`n" }
    if (-not ($evFrameText.Contains('data-performance-subtab="availability"') -and $evPageText.Contains('<EvAvailability'))) {
        $failures.Add(("The live EV Availability subtab or page branch is missing: ${evFramePath} must carry " +
            "data-performance-subtab=""availability"" and ${evPagePath} must render <EvAvailability (W5-03a E2).")) | Out-Null
    }
    if (-not ($evFrameText.Contains('data-performance-subtab="energy"') -and $evPageText.Contains('<EvEnergy'))) {
        $failures.Add(("The live EV Energy / site power subtab or page branch is missing: ${evFramePath} must carry " +
            "data-performance-subtab=""energy"" and ${evPagePath} must render <EvEnergy (W5-03a E3).")) | Out-Null
    }

    # W5-01b C5 (P-C5-9..16): the cold Financials Scenarios tab is live for COLDCHAIN only. The Scenarios view
    # renders <ColdScenarios as the direct consequent of the site_type === "COLDCHAIN" branch, the cold Financials
    # rows pass scenarios="live", and every other non-mini-grid Site keeps the one fallback literal at its own
    # FinancialsSections branch (so a second occurrence elsewhere cannot stand in for it).
    $framesPath = "frontend/src/shell/SiteAnalyticsFrames.tsx"
    $framesModule = @($Modules | Where-Object { $_.Path -eq $framesPath })
    $framesText = if ($framesModule.Count -eq 0) { "" } else { $framesModule[0].Lines -join "`n" }
    $coldBranch = [regex]::IsMatch($framesText, 'site_type === "COLDCHAIN" \? \(\s*<ColdScenarios\b')
    if (-not ($coldBranch -and $framesText.Contains('scenarios="live"'))) {
        $failures.Add(("${framesPath}: the cold Financials Scenarios destination is live (W5-01b C5): the Scenarios " +
            "view must render <ColdScenarios directly under site_type === ""COLDCHAIN"" and the cold Financials rows " +
            "must pass scenarios=""live"".")) | Out-Null
    }
    if (-not $framesText.Contains('{scenarios === "live" ? null : <UnavailableTab label="Scenarios" />}')) {
        $failures.Add(("${framesPath}: the non-cold Scenarios fallback must stay at its FinancialsSections branch " +
            "({scenarios === ""live"" ? null : <UnavailableTab label=""Scenarios"" />}) for every other non-mini-grid " +
            "Site (W5-01b C5).")) | Out-Null
    }

    return $failures
}
