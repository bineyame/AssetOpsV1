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
    return $fixtureFailures
}
