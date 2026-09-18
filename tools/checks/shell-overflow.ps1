# Seam: Shell overflow containment.
#
# From `.ai/FEATURE_MAP.md`, `### Viewport and overflow commitment`: shell
# chrome is chrome. The rail and the workspace bar stay anchored, and content
# that is too wide scrolls inside the region that owns it rather than pushing
# the document sideways.
#
# Four rules, and the last one matters most because it is the tempting wrong
# fix:
#
#   - every table goes through the shared primitive, which supplies the region
#   - that region actually contains the inline axis
#   - the frame is full height standalone and not full height nested, so the
#     Lab keeps its viewport and the operator shell stops claiming a second one
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

    return $failures
}
