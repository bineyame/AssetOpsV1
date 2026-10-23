# Seam: Shell overflow containment.
#
# From `.ai/FEATURE_MAP.md`, `### Viewport and overflow commitment`: shell
# chrome is chrome. The rail and the workspace bar stay anchored, and content
# that is too wide scrolls inside the region that owns it rather than pushing
# the document sideways.
#
# Five rules, and the one about hiding matters most because it is the tempting
# wrong fix:
#
#   - every table goes through the shared primitive, which supplies the region
#   - that region actually contains the inline axis
#   - the configured diagram has a region of its own that does the same
#   - the frame is full height standalone and not full height nested, so the
#     Lab keeps its viewport and the operator shell stops claiming a second one
#   - every svg goes through the diagram module, which supplies that region
#   - no shell surface hides page overflow instead of containing it
#
# Hiding is not containing. `overflow-x: hidden` on the document makes the
# scrollbar go away and takes the content off the side of the screen with it,
# which looks like the defect is fixed and means a user cannot reach the last
# columns at all.
#
# This guard reads CSS as text. It asserts that declarations exist, never what
# they compute to at a width, because exact visual fit is review-time evidence
# and a guard that asserted it would be a layout snapshot.
#
# Do not weaken the checks below to make a task pass.

function Invoke-ShellOverflowCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $primitivesCss = "frontend/src/ui/primitives.css"
    $tablePrimitive = "frontend/src/ui/DataTable.tsx"
    $scrollClass = ".data-table__scroll"

    # The configured single line diagram is the second piece of dense content
    # with an intrinsic width. The archetype has five lanes and a lane is wide
    # enough for a component name and a declared rating, so the drawing is
    # wider than the content column at the committed 1280px and far wider below
    # it. It is not a table, so the table rule above cannot reach it, and
    # without a rule of its own it would push the rail sideways exactly as the
    # Sites index did before T011B.
    $diagramScrollClass = ".sld__scroll"
    $diagramModule = "frontend/src/sites/SiteSingleLineDiagram.tsx"

    # T025c: the Lab's recorded day curves are the third. A chart spans the
    # whole run window at the width it measures, and at a narrow viewport that
    # is wider than the column. It gets the diagram's answer, with its own
    # region class and its own module, and the rules below hold it to the same
    # standard: its region declares the inline overflow, its module renders
    # that region, and no other module draws an svg.
    $chartScrollClass = ".history-chart__scroll"
    $chartModule = "frontend/src/shell/HistoryCharts.tsx"

    # T027 phase 2: the operator Site Overview's selected-window timeline is
    # the fourth. It lives in the Site substrate (the operator shell may not
    # import the Lab's charts), scales to its column through a viewBox, and is
    # held to the same three rules: its region declares the inline overflow,
    # its module renders that region, and its module is the only other place
    # an svg may be drawn.
    $timelineScrollClass = ".overview-timeline__scroll"
    $timelineModule = "frontend/src/sites/SiteOverview.tsx"

    # T028 presentation checkpoint 2a: the four assessment graphics are the
    # fifth. They scale to their column through a viewBox, and are held to the
    # same three rules: their region declares the inline overflow, their module
    # renders that region, and their module is the only other place an svg may
    # be drawn.
    $graphicsScrollClass = ".assessment-graphic"
    $graphicsModule = "frontend/src/sites/assessmentGraphics.tsx"

    # W5-01a C2 (Codex retrospective Q-C2-3): the cold Cooling selected-observation
    # graphic is the seventh. It scales to its column through a viewBox and is held
    # to the same three rules: its region declares the inline overflow, its module
    # renders that region, and its module is the only other place an svg may be drawn.
    $coldDepthScrollClass = ".cold-depth-graphic__scroll"
    $coldDepthModule = "frontend/src/sites/coldDepthGraphics.tsx"
    # W5-03a E3: the EV Energy import chart is the sole owner of its svg, inside its own region.
    $evDepthScrollClass = ".ev-depth-graphic__scroll"
    $evDepthModule = "frontend/src/sites/evDepthGraphics.tsx"

    # V-01a round 2: fixed-size icons are the sixth, and the only svg allowed
    # without a region. A rail or component-type icon is drawn at a fixed
    # pixel size (18px rail icons; component icons at an explicit width no
    # larger than a card's icon slot), so it has no intrinsic width to
    # overflow. Only these two modules may draw one, and each must keep its
    # fixed size declared on the element it draws.
    $iconModules = @{
        "frontend/src/ui/RailIcon.tsx"        = 'width={18}'
        "frontend/src/sites/componentIcons.tsx" = 'width={size}'
    }
    $iconSvgSeen = @{}

    if (-not (Test-Path -LiteralPath $primitivesCss -PathType Leaf)) {
        $failures.Add("Missing $primitivesCss, so every overflow rule below is unenforceable") | Out-Null
        return $failures
    }

    # --- The shared vocabulary's rules -----------------------------------------

    # Selector { declarations } pairs, flattened. Enough structure to ask "does
    # this selector declare this property", which is all this guard asks.
    $css = (Get-Content -LiteralPath $primitivesCss -Raw)
    $blocks = @()
    foreach ($match in [regex]::Matches($css, '(?s)([^{}]+)\{([^{}]*)\}')) {
        $blocks += [pscustomobject]@{
            Selector     = ($match.Groups[1].Value -replace '(?s)/\*.*?\*/', '').Trim()
            Declarations = $match.Groups[2].Value
        }
    }

    if ($blocks.Count -eq 0) {
        $failures.Add(("No rule was parsed out of $primitivesCss, so the " +
            "overflow checks are vacuous. Update the check, do not delete it.")) | Out-Null
        return $failures
    }

    function Test-Declares {
        param([object[]] $Blocks, [string] $Selector, [string] $Property)

        foreach ($block in $Blocks) {
            if ($block.Selector -ne $Selector) { continue }
            if ($block.Declarations -match "(?m)^\s*$([regex]::Escape($Property))\s*:") {
                return $true
            }
        }
        return $false
    }

    # 1. The region contains the inline axis. Without this the wrapper is a
    #    plain div and the table overflows straight past it to the document.
    $containsInlineAxis = $false
    foreach ($block in $blocks) {
        if ($block.Selector -ne $scrollClass) { continue }
        if ($block.Declarations -match '(?m)^\s*overflow(-x)?\s*:\s*(auto|scroll)\s*;') {
            $containsInlineAxis = $true
        }
    }

    if (-not $containsInlineAxis) {
        $failures.Add(("$scrollClass in $primitivesCss does not declare " +
            "'overflow-x: auto' or 'overflow-x: scroll'. The region that wraps " +
            "every table is what keeps a wide table from pushing the rail and " +
            "the workspace bar sideways; without the declaration it is a div.")) | Out-Null
    }

    # 1b. The diagram's region contains the inline axis too, for the same
    #     reason and with the same wording: a wrapper that does not declare it
    #     is a div, and the overflow goes straight past it to the document.
    $diagramContainsInlineAxis = $false
    foreach ($block in $blocks) {
        if ($block.Selector -ne $diagramScrollClass) { continue }
        if ($block.Declarations -match '(?m)^\s*overflow(-x)?\s*:\s*(auto|scroll)\s*;') {
            $diagramContainsInlineAxis = $true
        }
    }

    if (-not $diagramContainsInlineAxis) {
        $failures.Add(("$diagramScrollClass in $primitivesCss does not declare " +
            "'overflow-x: auto' or 'overflow-x: scroll'. The configured single " +
            "line diagram has an intrinsic width wider than the content " +
            "column, and without the region that owns it the drawing pushes " +
            "the rail and the workspace bar sideways.")) | Out-Null
    }

    # 1c. The chart region contains the inline axis as well.
    $chartContainsInlineAxis = $false
    foreach ($block in $blocks) {
        if ($block.Selector -ne $chartScrollClass) { continue }
        if ($block.Declarations -match '(?m)^\s*overflow(-x)?\s*:\s*(auto|scroll)\s*;') {
            $chartContainsInlineAxis = $true
        }
    }

    if (-not $chartContainsInlineAxis) {
        $failures.Add(("$chartScrollClass in $primitivesCss does not declare " +
            "'overflow-x: auto' or 'overflow-x: scroll'. A history chart spans " +
            "the run window, and without the region that owns it the drawing " +
            "pushes the rail and the workspace bar sideways.")) | Out-Null
    }

    # 1d. The Overview timeline region contains the inline axis as well.
    $timelineContainsInlineAxis = $false
    foreach ($block in $blocks) {
        if ($block.Selector -ne $timelineScrollClass) { continue }
        if ($block.Declarations -match '(?m)^\s*overflow(-x)?\s*:\s*(auto|scroll)\s*;') {
            $timelineContainsInlineAxis = $true
        }
    }

    if (-not $timelineContainsInlineAxis) {
        $failures.Add(("$timelineScrollClass in $primitivesCss does not declare " +
            "'overflow-x: auto' or 'overflow-x: scroll'. Without the region " +
            "that owns it, the Overview timeline has nothing between it and " +
            "the document.")) | Out-Null
    }

    # 1e. The assessment graphics region contains the inline axis as well.
    $graphicsContainsInlineAxis = $false
    foreach ($block in $blocks) {
        if ($block.Selector -ne $graphicsScrollClass) { continue }
        if ($block.Declarations -match '(?m)^\s*overflow(-x)?\s*:\s*(auto|scroll)\s*;') {
            $graphicsContainsInlineAxis = $true
        }
    }

    if (-not $graphicsContainsInlineAxis) {
        $failures.Add(("$graphicsScrollClass in $primitivesCss does not declare " +
            "'overflow-x: auto' or 'overflow-x: scroll'. Without the region " +
            "that owns it, an assessment graphic has nothing between it and " +
            "the document.")) | Out-Null
    }

    # 2. The frame is full height standalone, and not full height nested.
    #    Both halves are asserted, because deleting either one is a plausible
    #    "cleanup" that breaks the other shell.
    if (-not (Test-Declares -Blocks $blocks -Selector ".app-frame" -Property "min-height")) {
        $failures.Add((".app-frame in $primitivesCss no longer declares a " +
            "min-height. SimulatorLabShell renders that frame standalone, " +
            "outside .app-shell, and a developer workspace with a short page " +
            "should still be full height.")) | Out-Null
    }

    if (-not (Test-Declares -Blocks $blocks -Selector ".app-shell > .app-frame" -Property "min-height")) {
        $failures.Add((".app-shell > .app-frame in $primitivesCss does not " +
            "override min-height. Nested inside the shell, the frame's own " +
            "full-height rule is a second claim on the viewport: an operator " +
            "page comes out at 100vh plus the workspace bar and scrolls " +
            "vertically when it is empty.")) | Out-Null
    }

    # 2b. The phone-width shell rules belong to the two named shells: the
    #     operator Site shell (`.app-frame--operator`) and the Simulator Lab
    #     shell (`.app-frame--lab`, whose phone layout V-01b verifies in the
    #     browser). Both share `.app-frame`, so a bare `.app-frame` or
    #     `.nav-rail` selector in a narrow media block silently changes an
    #     unnamed frame (Architect Q1, S1-03 fix round). Each selector part
    #     must name one of the two shells, and each shell must have at least
    #     one narrow rule, so neither half of the check is vacuous.
    $narrowRuleCount = 0
    $narrowOperatorParts = 0
    $narrowLabParts = 0
    foreach ($media in [regex]::Matches($css, '(?s)@media\s*\(\s*max-width\s*:\s*(\d+)px\s*\)\s*\{((?:[^{}]|\{[^{}]*\})*)\}')) {
        if ([int]$media.Groups[1].Value -gt 640) { continue }
        foreach ($rule in [regex]::Matches($media.Groups[2].Value, '(?s)([^{}]+)\{[^{}]*\}')) {
            $selector = ($rule.Groups[1].Value -replace '(?s)/\*.*?\*/', '').Trim()
            if ($selector -notmatch 'app-frame|nav-rail') { continue }
            $narrowRuleCount++
            foreach ($part in ($selector -split ',')) {
                if ($part -match '^\s*\.app-frame--operator(?![\w-])') {
                    $narrowOperatorParts++
                } elseif ($part -match '^\s*\.app-frame--lab(?![\w-])') {
                    $narrowLabParts++
                } else {
                    $failures.Add(("'$($part.Trim())' in a max-width:$($media.Groups[1].Value)px " +
                        "block of $primitivesCss is not scoped to .app-frame--operator or " +
                        ".app-frame--lab. Both shells share these classes, so an unscoped " +
                        "shell rule here changes a frame unreviewed.")) | Out-Null
                }
            }
        }
    }
    if ($narrowRuleCount -eq 0 -or $narrowOperatorParts -eq 0) {
        $failures.Add(("No narrow-width .app-frame--operator rule was found in " +
            "$primitivesCss, so the scoping check is vacuous. Update the check, " +
            "do not delete it.")) | Out-Null
    }
    if ($narrowLabParts -eq 0) {
        $failures.Add(("No narrow-width .app-frame--lab rule was found in " +
            "$primitivesCss. The Simulator Lab shell at phone width gave its " +
            "main column about 95px of 375px (S1-03 Q1 carry, closed by V-01b).")) | Out-Null
    }

    # 3. Nobody hides page overflow instead of containing it.
    $hidingSelectors = @("html", "body", ".app-shell", ".app-frame", ".app-frame__body", ".app-frame__content")
    foreach ($block in $blocks) {
        if ($hidingSelectors -notcontains $block.Selector) { continue }
        if ($block.Declarations -match '(?m)^\s*overflow(-x)?\s*:\s*(hidden|clip)\s*;') {
            $failures.Add(("$($block.Selector) in $primitivesCss hides " +
                "horizontal overflow. Hiding is not containing: the scrollbar " +
                "goes away and the content on the far side of it goes with it, " +
                "unreachable. Dense content owns its overflow in its own " +
                "region; the shell does not paper over it.")) | Out-Null
        }
    }

    # --- One table pattern -----------------------------------------------------

    # 4. Every table goes through the primitive. A bare <table> somewhere else
    #    is a table with no region around it, which is the defect this slice
    #    fixed, reintroduced one screen at a time.
    $tablePrimitiveSeen = $false

    foreach ($module in (Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -notmatch '<table[\s>]') { continue }

            if ($module.Path -eq $tablePrimitive) {
                $tablePrimitiveSeen = $true
                continue
            }

            $failures.Add(("A table element outside the shared primitive at " +
                "$($module.Path):${lineNumber}: $($line.Trim()). Tables render " +
                "through DataTable in $tablePrimitive, which supplies the " +
                "region that owns their overflow. A bare table has nothing " +
                "between it and the document.")) | Out-Null
        }
    }

    if (-not $tablePrimitiveSeen) {
        $failures.Add(("$tablePrimitive renders no table element, so the " +
            "one-table-pattern check is vacuous. Update the check, do not " +
            "delete it.")) | Out-Null
    }

    # 1f. The cold depth graphic region contains the inline axis as well.
    $coldDepthContainsInlineAxis = $false
    foreach ($block in $blocks) {
        if ($block.Selector -ne $coldDepthScrollClass) { continue }
        if ($block.Declarations -match '(?m)^\s*overflow(-x)?\s*:\s*(auto|scroll)\s*;') {
            $coldDepthContainsInlineAxis = $true
        }
    }

    if (-not $coldDepthContainsInlineAxis) {
        $failures.Add(("$coldDepthScrollClass in $primitivesCss does not declare " +
            "'overflow-x: auto' or 'overflow-x: scroll'. Without the region " +
            "that owns it, the cold depth graphic has nothing between it and " +
            "the document.")) | Out-Null
    }

    # --- One diagram pattern ---------------------------------------------------

    # 5. Every svg goes through the diagram module, and the diagram module
    #    wraps it in the region. An svg rendered anywhere else is a drawing
    #    with nothing between it and the document - the same defect as a bare
    #    table, in the one other place this build has dense content with an
    #    intrinsic width.
    $diagramRegionSeen = $false
    $diagramSvgSeen = $false
    $chartRegionSeen = $false
    $chartSvgSeen = $false
    $timelineRegionSeen = $false
    # 1g. W5-03a E3: the EV depth graphic region contains the inline axis as well.
    $evDepthContainsInlineAxis = $false
    foreach ($block in $blocks) {
        if ($block.Selector -ne $evDepthScrollClass) { continue }
        if ($block.Declarations -match '(?m)^\s*overflow(-x)?\s*:\s*(auto|scroll)\s*;') {
            $evDepthContainsInlineAxis = $true
        }
    }

    if (-not $evDepthContainsInlineAxis) {
        $failures.Add(("$evDepthScrollClass in $primitivesCss does not declare " +
            "'overflow-x: auto' or 'overflow-x: scroll'. Without the region " +
            "that owns it, the EV depth graphic has nothing between it and " +
            "the document.")) | Out-Null
    }

    $timelineSvgSeen = $false
    $graphicsRegionSeen = $false
    $graphicsSvgSeen = $false
    $coldDepthRegionSeen = $false
    $coldDepthSvgSeen = $false
    $evDepthRegionSeen = $false
    $evDepthSvgSeen = $false

    foreach ($module in (Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            if ($line -match [regex]::Escape($diagramScrollClass.TrimStart("."))) {
                if ($module.Path -eq $diagramModule) { $diagramRegionSeen = $true }
            }
            if ($line -match [regex]::Escape($chartScrollClass.TrimStart("."))) {
                if ($module.Path -eq $chartModule) { $chartRegionSeen = $true }
            }
            if ($line -match [regex]::Escape($timelineScrollClass.TrimStart("."))) {
                if ($module.Path -eq $timelineModule) { $timelineRegionSeen = $true }
            }
            if ($line -match ('["`]' + [regex]::Escape($graphicsScrollClass.TrimStart(".")) + '[ "`]')) {
                if ($module.Path -eq $graphicsModule) { $graphicsRegionSeen = $true }
            }
            if ($line -match ('["`]' + [regex]::Escape($coldDepthScrollClass.TrimStart(".")) + '[ "`]')) {
                if ($module.Path -eq $coldDepthModule) { $coldDepthRegionSeen = $true }
            }
            if ($line -match ('["`]' + [regex]::Escape($evDepthScrollClass.TrimStart(".")) + '[ "`]')) {
                if ($module.Path -eq $evDepthModule) { $evDepthRegionSeen = $true }
            }

            # A comment naming the element is not an element. AppHeader's own
            # doc comment says the brand mark is drawn in CSS rather than as an
            # inline <svg>, and a scan that could not tell those apart would
            # report a drawing where there is a sentence about not having one.
            $code = $line.Trim()
            if ($code.StartsWith("*") -or $code.StartsWith("//") -or $code.StartsWith("/*")) { continue }

            # `$` as well as whitespace: a multi-line JSX element puts nothing
            # after the tag name on its own line, and a pattern that required a
            # following character would miss exactly the elements worth finding.
            if ($line -notmatch '<svg(\s|>|$)') { continue }

            if ($module.Path -eq $diagramModule) {
                $diagramSvgSeen = $true
                continue
            }
            if ($module.Path -eq $chartModule) {
                $chartSvgSeen = $true
                continue
            }
            if ($module.Path -eq $timelineModule) {
                $timelineSvgSeen = $true
                continue
            }
            if ($module.Path -eq $graphicsModule) {
                $graphicsSvgSeen = $true
                continue
            }
            if ($module.Path -eq $coldDepthModule) {
                $coldDepthSvgSeen = $true
                continue
            }
            if ($module.Path -eq $evDepthModule) {
                $evDepthSvgSeen = $true
                continue
            }
            if ($iconModules.ContainsKey($module.Path)) {
                $iconSvgSeen[$module.Path] = $true
                if (($module.Lines -join "`n") -notmatch [regex]::Escape($iconModules[$module.Path])) {
                    $failures.Add(("The icon module $($module.Path) draws an svg at line " +
                        "${lineNumber} without its fixed size ($($iconModules[$module.Path])). " +
                        "An icon is allowed outside a region only because it cannot grow.")) | Out-Null
                }
                continue
            }

            $failures.Add(("An svg element outside the diagram and chart modules at " +
                "$($module.Path):${lineNumber}: $($line.Trim()). The " +
                "configured diagram renders through $diagramModule, the Lab's " +
                "history charts through $chartModule and the Overview timeline " +
                "through $timelineModule, the assessment graphics through " +
                "$graphicsModule, the cold depth graphic through $coldDepthModule and the EV depth " +
                "graphic through $evDepthModule, each of which " +
                "supplies the region that owns its overflow. A drawing " +
                "anywhere else has nothing between it and the document.")) | Out-Null
        }
    }

    foreach ($iconModule in $iconModules.Keys) {
        if (-not $iconSvgSeen.ContainsKey($iconModule)) {
            $failures.Add(("$iconModule is allowed to draw a fixed-size icon svg but " +
                "renders none, so its allowance is stale. Remove it from the icon list.")) | Out-Null
        }
    }
    if (-not $diagramSvgSeen) {
        $failures.Add(("$diagramModule renders no svg element, so the " +
            "one-diagram-pattern check is vacuous. Update the check, do not " +
            "delete it.")) | Out-Null
    }

    if (-not $diagramRegionSeen) {
        $failures.Add(("$diagramModule does not render " +
            "$diagramScrollClass, so the drawing it renders has no region " +
            "that owns its overflow. The CSS rule above would then be a rule " +
            "for a class nothing uses.")) | Out-Null
    }

    if (-not $chartSvgSeen) {
        $failures.Add(("$chartModule renders no svg element, so its " +
            "exemption from the one-diagram-pattern check is vacuous. Update " +
            "the check, do not delete it.")) | Out-Null
    }

    if (-not $chartRegionSeen) {
        $failures.Add(("$chartModule does not render $chartScrollClass, so " +
            "the charts it draws have no region that owns their overflow.")) | Out-Null
    }

    if (-not $timelineSvgSeen) {
        $failures.Add(("$timelineModule renders no svg element, so its " +
            "exemption from the one-diagram-pattern check is vacuous. Update " +
            "the check, do not delete it.")) | Out-Null
    }

    if (-not $timelineRegionSeen) {
        $failures.Add(("$timelineModule does not render $timelineScrollClass, " +
            "so the timeline it draws has no region that owns its overflow.")) | Out-Null
    }

    if (-not $graphicsSvgSeen) {
        $failures.Add(("$graphicsModule renders no svg element, so its " +
            "exemption from the one-diagram-pattern check is vacuous. Update " +
            "the check, do not delete it.")) | Out-Null
    }

    if (-not $graphicsRegionSeen) {
        $failures.Add(("$graphicsModule does not render $graphicsScrollClass, " +
            "so the graphics it draws have no region that owns their overflow.")) | Out-Null
    }

    if (-not $coldDepthSvgSeen) {
        $failures.Add(("$coldDepthModule renders no svg element, so its " +
            "exemption from the one-diagram-pattern check is vacuous. Update " +
            "the check, do not delete it.")) | Out-Null
    }

    if (-not $coldDepthRegionSeen) {
        $failures.Add(("$coldDepthModule does not render $coldDepthScrollClass, " +
            "so the graphic it draws has no region that owns its overflow.")) | Out-Null
    }

    if (-not $evDepthSvgSeen) {
        $failures.Add(("$evDepthModule renders no svg element, so its " +
            "exemption from the one-diagram-pattern check is vacuous. Update " +
            "the check, do not delete it.")) | Out-Null
    }

    if (-not $evDepthRegionSeen) {
        $failures.Add(("$evDepthModule does not render $evDepthScrollClass, " +
            "so the graphic it draws has no region that owns its overflow.")) | Out-Null
    }

    return $failures
}
