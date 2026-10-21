# Seam: Navigation truthfulness, operator rail fixtures (W1-UX-07,
# D-2026-10-17-w1-rail). Proves Get-OperatorRailFailures in
# navigation-truthfulness.ps1 is not vacuous: each case mutates the real source
# lines in memory and must fail with the expected message, and the baseline
# (the real tree) must pass. A case that stops failing means the rail guard
# went vacuous for that violation. Returns one failure per broken fixture.
#
# Do not weaken the cases below to make a task pass.

function Invoke-NavigationRailFixturesCheck {
    $fixtureFailures = New-Object System.Collections.Generic.List[string]
    if (-not (Get-Command Get-OperatorRailFailures -CommandType Function -ErrorAction SilentlyContinue)) {
        . (Join-Path $PSScriptRoot "navigation-truthfulness.ps1")
    }
    try {
        $rail = @(Get-Content -LiteralPath "frontend/src/shell/OperatorShellLayout.tsx")
        $app = @(Get-Content -LiteralPath "frontend/src/App.tsx")
        $nav = @(Get-Content -LiteralPath "frontend/src/ui/NavRail.tsx")
        $constants = @()
        foreach ($file in @(Get-ChildItem -LiteralPath "frontend/src/shell" -File |
                Where-Object { $_.Extension -in @(".ts", ".tsx") })) {
            $constants += @(Get-Content -LiteralPath $file.FullName)
        }

        function Edit-Lines([string[]] $lines, [string] $pattern, [string] $replacement) {
            $hit = $false
            $out = foreach ($line in $lines) {
                if (-not $hit -and $line -match $pattern) { $hit = $true; $line -replace $pattern, $replacement }
                else { $line }
            }
            if (-not $hit) { throw "fixture pattern not found: $pattern" }
            return @($out)
        }
        function Remove-Line([string[]] $lines, [string] $pattern) {
            $hit = @($lines | Where-Object { $_ -match $pattern })
            if ($hit.Count -eq 0) { throw "fixture pattern not found: $pattern" }
            return @($lines | Where-Object { $_ -notmatch $pattern })
        }
        function Insert-After([string[]] $lines, [string] $pattern, [string] $newLine) {
            $out = New-Object System.Collections.Generic.List[string]
            $hit = $false
            foreach ($line in $lines) {
                $out.Add($line)
                if (-not $hit -and $line -match $pattern) { $out.Add($newLine); $hit = $true }
            }
            if (-not $hit) { throw "fixture pattern not found: $pattern" }
            return @($out)
        }

        $cases = @(
            @{ Name = "baseline: the real tree passes"; Expect = $null },
            @{ Name = "unavailable root gains a destination (dead link)"; Expect = "Dead link: the unavailable operator rail root 'Portfolio' carries 'to'";
               Rail = (Edit-Lines $rail 'kind: "unavailable", label: "Portfolio"' 'kind: "unavailable", to: "/portfolio", label: "Portfolio"') },
            @{ Name = "unavailable root gains a click handler"; Expect = "carries 'onClick'";
               Rail = (Edit-Lines $rail 'label: "Settings", group: "ADMIN"' 'label: "Settings", onClick: openSettings, group: "ADMIN"') },
            @{ Name = "live root points at a missing route"; Expect = "points at '/findingz'";
               Rail = (Edit-Lines $rail 'to: "/findings"' 'to: "/findingz"') },
            @{ Name = "live root's route removed (only the catch-all would serve it)"; Expect = "points at '/findings'";
               App = (Remove-Line $app 'path=\{FINDINGS_PATH\}') },
            @{ Name = "W3-01: Actions live root points at a missing route"; Expect = "points at '/actionz'";
               Rail = (Edit-Lines $rail 'to: "/actions"' 'to: "/actionz"') },
            @{ Name = "W3-01: Actions route removed (only the catch-all would serve it)"; Expect = "points at '/actions'";
               App = (Remove-Line $app 'path=\{ACTIONS_PATH\}') },
            @{ Name = "W3-01: Actions demoted back to unavailable"; Expect = "the W1 rail is exactly";
               Rail = (Edit-Lines $rail 'kind: "live", to: "/actions", label: "Actions", end: false' 'kind: "unavailable", label: "Actions"') },
            @{ Name = "W3-02: Evidence live root points at a missing route"; Expect = "points at '/evidencz'";
               Rail = (Edit-Lines $rail 'to: "/evidence"' 'to: "/evidencz"') },
            @{ Name = "W3-02: Evidence route removed (only the catch-all would serve it)"; Expect = "points at '/evidence'";
               App = (Remove-Line $app 'path=\{EVIDENCE_PATH\}') },
            @{ Name = "W3-02: Evidence demoted back to unavailable"; Expect = "the W1 rail is exactly";
               Rail = (Edit-Lines $rail 'kind: "live", to: "/evidence", label: "Evidence", end: false' 'kind: "unavailable", label: "Evidence"') },
            @{ Name = "W3-02: Financials promoted to live"; Expect = "the W1 rail is exactly";
               Rail = (Edit-Lines $rail 'kind: "unavailable", label: "Financials"' 'kind: "live", to: "/evidence", label: "Financials"') },
            @{ Name = "W3-01: Incidents promoted to live"; Expect = "the W1 rail is exactly";
               Rail = (Edit-Lines $rail 'kind: "unavailable", label: "Incidents"' 'kind: "live", to: "/actions", label: "Incidents"') },
            @{ Name = "unknown root appended"; Expect = "the W1 rail is exactly";
               Rail = (Insert-After $rail 'label: "Settings", group: "ADMIN"' '  { kind: "unavailable", label: "Reports", group: "ADMIN", icon: "log" },') },
            @{ Name = "label typo"; Expect = "the W1 rail is exactly";
               Rail = (Edit-Lines $rail 'label: "Operational records"' 'label: "Operational record"') },
            @{ Name = "old group caption"; Expect = "the W1 rail is exactly";
               Rail = (Edit-Lines $rail 'label: "Sites", end: false, group: "OPERATIONS"' 'label: "Sites", end: false, group: "OPERATE"') },
            @{ Name = "root promoted to live without review"; Expect = "the W1 rail is exactly";
               Rail = (Edit-Lines $rail 'kind: "unavailable", label: "Assets"' 'kind: "live", to: "/sites", label: "Assets"') },
            @{ Name = "item without an explicit kind"; Expect = "has no explicit kind";
               Rail = (Edit-Lines $rail '\{ kind: "live", to: "/sites"' '{ to: "/sites"') },
            @{ Name = "unparseable inventory line"; Expect = "Unparseable operator rail line";
               Rail = (Insert-After $rail 'label: "Portfolio"' '  ...extraRoots,') },
            @{ Name = "inventory renamed (fail closed)"; Expect = "declares no 'const operatorRailItems";
               Rail = (Edit-Lines $rail 'const operatorRailItems: NavRailItem\[\] = \[' 'const railItems: NavRailItem[] = [') },
            @{ Name = "a link outside the inventory"; Expect = "outside the checked inventory";
               Rail = (Insert-After $rail '\{chrome\?\.footer' '        <NavLink to="/portfolio">Portfolio</NavLink>') },
            @{ Name = "NavRail type stops forbidding to"; Expect = "no longer declares NavRailUnavailableItem";
               Nav = (Remove-Line $nav '^\s*to\?: never;') }
        )
    }
    catch {
        $fixtureFailures.Add("Rail fixtures could not be built: $($_.Exception.Message). Update the fixtures with the rail.") | Out-Null
        return $fixtureFailures
    }

    foreach ($case in $cases) {
        $r = if ($case.ContainsKey("Rail")) { $case.Rail } else { $rail }
        $a = if ($case.ContainsKey("App")) { $case.App } else { $app }
        $n = if ($case.ContainsKey("Nav")) { $case.Nav } else { $nav }
        $result = @(Get-OperatorRailFailures -RailLines $r -AppLines $a -RouteConstantLines $constants -NavRailLines $n)
        if ($null -eq $case.Expect) {
            if ($result.Count -ne 0) {
                $fixtureFailures.Add(("Rail fixture '$($case.Name)': the real tree should pass the " +
                    "operator rail guard but got [$($result -join ' || ')]")) | Out-Null
            }
        }
        elseif (@($result | Where-Object { $_ -like "*$($case.Expect)*" }).Count -eq 0) {
            $fixtureFailures.Add(("Rail fixture '$($case.Name)' did not fail as expected " +
                "('$($case.Expect)'); got [$($result -join ' || ')]. The rail guard is vacuous " +
                "for this violation.")) | Out-Null
        }
    }

    # W1-F5b (D-2026-10-17-f5-subtabs-and-contact): Get-InPageUnavailableEntryFailures is not vacuous. Each case
    # mutates one real module in memory and must fail; the real tree must pass.
    $modules = @(Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))
    function Set-ModuleLines([object[]] $all, [string] $path, [string] $pattern, [string] $replacement) {
        $hit = $false
        $out = foreach ($m in $all) {
            if ($m.Path -ne $path) { $m; continue }
            $lines = foreach ($line in $m.Lines) {
                if (-not $hit -and $line -match $pattern) { $hit = $true; $line -replace $pattern, $replacement } else { $line }
            }
            [pscustomobject]@{ Path = $m.Path; Lines = @($lines) }
        }
        if (-not $hit) { throw "in-page fixture pattern not found in ${path}: $pattern" }
        return @($out)
    }
    $component = "frontend/src/ui/UnavailableEntry.tsx"
    $frames = "frontend/src/shell/SiteAnalyticsFrames.tsx"
    $index = "frontend/src/sites/SiteFindingIndex.tsx"
    $cold = "frontend/src/sites/ColdAssessmentViews.tsx"
    $ev = "frontend/src/sites/EvAssessmentViews.tsx"
    try {
        $inPageCases = @(
            @{ Name = "baseline: the real tree passes"; Expect = $null; Modules = $modules },
            @{ Name = "the entry gains a tab stop"; Expect = "carries tabIndex";
               Modules = (Set-ModuleLines $modules $component 'data-tab-unavailable=\{label\}' 'data-tab-unavailable={label} tabIndex={0}') },
            @{ Name = "the entry gains a click handler"; Expect = "carries an event handler";
               Modules = (Set-ModuleLines $modules $component 'data-chip-unavailable=\{label\}' 'data-chip-unavailable={label} onClick={go}') },
            @{ Name = "the entry becomes a disabled button"; Expect = "carries a button";
               Modules = (Set-ModuleLines $modules $component '<li$' '<button') },
            @{ Name = "an undeclared unbuilt tab is added"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $frames '<UnavailableTab label="Scenarios" />' '<UnavailableTab label="Scenarios" /><UnavailableTab label="Reports" />') },
            # W4-01: Work > Incidents and Maintenance are live; reintroducing either as unavailable text fails.
            @{ Name = "W4-01: Incidents comes back as an unavailable Work subtab"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $frames '<UnavailableTab label="Scenarios" />' '<UnavailableTab label="Scenarios" /><UnavailableTab label="Incidents" />') },
            @{ Name = "W4-01: Maintenance comes back as an unavailable Work subtab"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $frames '<UnavailableTab label="Scenarios" />' '<UnavailableTab label="Scenarios" /><UnavailableTab label="Maintenance" />') },
            @{ Name = "a declared unbuilt tab is dropped"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $frames '<UnavailableTab label="Scenarios" />' '') },
            @{ Name = "Alternatives loses its declared unavailable entry"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $frames 'label: "Alternatives", unavailable: true' 'label: "Alternatives", href: "/x"') },
            @{ Name = "the cold Cooling entry is dropped"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $cold '<UnavailableTab label="Cooling" />' '') },
            @{ Name = "the cold Recommendation entry is dropped"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $cold '<UnavailableTab label="Recommendation" />' '') },
            # W2-06 r7 P8: the EV entries are part of the closed multiset.
            @{ Name = "the EV Recommendation entry is dropped"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $ev '<UnavailableTab label="Recommendation" />' '') },
            @{ Name = "the EV Availability entry is dropped"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $ev '<UnavailableTab label="Availability" />' '') },
            @{ Name = "the EV Energy / site power entry is dropped"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $ev '<UnavailableTab label="Energy / site power" />' '') },
            @{ Name = "an EV entry is duplicated"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $ev '<UnavailableTab label="Availability" />' '<UnavailableTab label="Availability" /><UnavailableTab label="Availability" />') },
            @{ Name = "an arbitrary new EV tab is appended"; Expect = "the W1-plus-W2 inventory is exactly";
               Modules = (Set-ModuleLines $modules $ev '<UnavailableTab label="Energy / site power" />' '<UnavailableTab label="Energy / site power" /><UnavailableTab label="Tariffs" />') },
            @{ Name = "a lens chip with a computed label"; Expect = "non-literal label";
               Modules = (Set-ModuleLines $modules $index '<UnavailableChip label="Risks" />' '<UnavailableChip label={lens} />') },
            @{ Name = "the component is missing (fail closed)"; Expect = "check is vacuous";
               Modules = @($modules | Where-Object { $_.Path -ne $component }) }
        )
    }
    catch {
        $fixtureFailures.Add("In-page unavailable fixtures could not be built: $($_.Exception.Message). Update the fixtures with the rows.") | Out-Null
        return $fixtureFailures
    }
    foreach ($case in $inPageCases) {
        $result = @(Get-InPageUnavailableEntryFailures -Modules $case.Modules)
        if ($null -eq $case.Expect) {
            if ($result.Count -ne 0) {
                $fixtureFailures.Add(("In-page fixture '$($case.Name)': the real tree should pass but got " +
                    "[$($result -join ' || ')]")) | Out-Null
            }
        }
        elseif (@($result | Where-Object { $_ -like "*$($case.Expect)*" }).Count -eq 0) {
            $fixtureFailures.Add(("In-page fixture '$($case.Name)' did not fail as expected ('$($case.Expect)'); " +
                "got [$($result -join ' || ')]. The in-page unavailable guard is vacuous for this violation.")) | Out-Null
        }
    }
    return $fixtureFailures
}
