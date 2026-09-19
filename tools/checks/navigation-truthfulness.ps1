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
                        "labelled in place, never disabled: these are not " +
                        "switched off, they are not built.")) | Out-Null
                    break
                }
            }
        }
    }

    return $failures
}

# The Foundation subtab row: one definition, in the shared substrate, with
# `Changes` absent and the superseded mockup vocabulary gone.
#
# This row lives in the substrate rather than a shell, unlike the operator Site
# tab row above it. The difference is real: which aspects a workspace divides a
# Site into is a shell's opinion, but what a Foundation is made of is the same
# whoever renders it, so both shells present these four.
function Get-FoundationSubtabFailures {
    $failures = New-Object System.Collections.Generic.List[string]

    $inventoryName = "FOUNDATION_SUBTABS"
    $substrateRoot = "frontend/src/sites"

    # v6.9 line 2117 lists five. `Changes` is filtered out by the accepted T008
    # checkpoint: lines 2149 and 2225-2228 make it a real intervention and
    # change-effect capability rather than the mockup's `Version History`, no
    # configuration-change model exists, and naming it would promise a meaning
    # a reader would guess wrongly. Absent in every state, not labelled.
    $forbiddenSubtab = "Changes"

    # What T013 replaced. These were the old mockup-derived subtab names and
    # they must not come back as a Foundation subtab row.
    $supersededVocabulary = @("Summary", "Components", "Control Logic", "Settings")

    # A subtab this build cannot open is labelled, never disabled. Same rule as
    # the tab row above, same reason.
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

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            if ($line -match "label\s*:\s*[""']$forbiddenSubtab[""']") {
                $failures.Add(("'$forbiddenSubtab' is declared as a Foundation " +
                    "subtab at $($module.Path):${lineNumber}: $($line.Trim()). " +
                    "v6.9 makes it an intervention and change-effect " +
                    "capability, no configuration-change model exists, and the " +
                    "T008 checkpoint removed that territory rather than " +
                    "leaving it as chrome. It is absent in every state, not " +
                    "labelled in place.")) | Out-Null
            }

            foreach ($label in $supersededVocabulary) {
                if ($line -match "label\s*:\s*[""']$label[""']") {
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
                        "labelled in place, never disabled.")) | Out-Null
                    break
                }
            }
        }
    }

    return $failures
}
