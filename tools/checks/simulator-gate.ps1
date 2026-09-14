# Seam: Simulator feature gate.
#
# The gate keeps a single chokepoint:
#
#   - `config/app-config.json` declares a boolean `simulator_lab.enabled`
#   - simulator URLs are declared only in the gated modules, so an entry point
#     or API path cannot be added outside the gate
#
# Do not weaken the checks below to make a task pass.

function Invoke-SimulatorGateCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    # The gate is only as good as its chokepoint. If a simulator URL can be
    # spelled anywhere in the tree, an entry point or API path can be added
    # outside the gate and stay reachable by direct URL after the feature is
    # "disabled" - which is the late failure mode this seam exists to prevent.
    #
    # So: a path literal naming the simulator may appear ONLY in the gated
    # modules below. Everywhere else must import the exported constant.
    # Test files are exempt, because tests must be able to request unserved
    # URLs in order to prove they are unserved.

    $gateConfigPath = "config/app-config.json"

    if (-not (Test-Path -LiteralPath $gateConfigPath -PathType Leaf)) {
        $failures.Add("Missing Simulator Lab gate configuration: $gateConfigPath") | Out-Null
    }
    else {
        try {
            $gateConfig = Get-Content -LiteralPath $gateConfigPath -Raw | ConvertFrom-Json
        } catch {
            $gateConfig = $null
            $failures.Add("$gateConfigPath is not valid JSON") | Out-Null
        }

        if ($null -ne $gateConfig) {
            $simulatorLab = $gateConfig.PSObject.Properties["simulator_lab"]
            if ($null -eq $simulatorLab) {
                $failures.Add("$gateConfigPath must declare a 'simulator_lab' section") | Out-Null
            }
            elseif ($null -eq $simulatorLab.Value.PSObject.Properties["enabled"]) {
                $failures.Add("$gateConfigPath must declare 'simulator_lab.enabled'") | Out-Null
            }
            elseif ($simulatorLab.Value.enabled -isnot [bool]) {
                $failures.Add("$gateConfigPath 'simulator_lab.enabled' must be a boolean") | Out-Null
            }
        }
    }

    # A quoted URL path (starts with "/") that names the simulator.
    $simulatorPathLiteral = '["''](/[^"'']*simulator[^"'']*)["'']'

    $gatedModules = @(
        "backend/assetops_backend/simulator_lab_api.py",
        "frontend/src/shell/simulatorLabRoutes.tsx"
    )

    $gateScanRoots = @(
        @{ Root = "backend"; Extensions = @(".py") },
        @{ Root = "frontend/src"; Extensions = @(".ts", ".tsx", ".js", ".jsx") }
    )

    foreach ($scan in $gateScanRoots) {
        foreach ($module in (Get-ScannedModules -Root $scan.Root -Extensions $scan.Extensions)) {
            if ($gatedModules -contains $module.Path) { continue }

            $lineNumber = 0
            foreach ($line in $module.Lines) {
                $lineNumber++
                if ($line -imatch $simulatorPathLiteral) {
                    $failures.Add(("Simulator URL declared outside the gated module in " +
                        "$($module.Path):${lineNumber}: $($line.Trim()). Import the path " +
                        "constant from a gated module instead.")) | Out-Null
                }
            }
        }
    }

    return $failures
}
