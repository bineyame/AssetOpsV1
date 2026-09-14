# Seam: Stack and module direction (direction half), and Simulator/product
# boundary.
#
# The banned directions stay banned:
#
#   - no direct UI-to-simulator imports
#   - no simulator-to-product imports/writes
#   - no product-to-simulator imports (operator read models and backend code
#     must not import simulator runtime/truth modules)
#
# Do not weaken the checks below to make a task pass.

function Invoke-DependencyDirectionCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    # --- Banned dependency direction: UI -> simulator --------------------------

    # Matches module specifiers that resolve into the simulator root. The
    # PascalCase `SimulatorLab*` component names are intentionally not matched,
    # so the comparison must stay case-sensitive (-cmatch).
    $uiToSimulator = '(?:from|import|require)\s*\(?\s*["''][^"'']*(?:(?:^|[./])simulator/|assetops[_-]simulator)'

    $frontendSources = Get-SourceFiles -Root "frontend/src" -Extensions @(".ts", ".tsx", ".js", ".jsx")

    foreach ($source in $frontendSources) {
        $lineNumber = 0
        foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
            $lineNumber++
            if ($line -cmatch $uiToSimulator) {
                $relative = Resolve-Path -LiteralPath $source.FullName -Relative
                $failures.Add("Banned UI-to-simulator import in ${relative}:${lineNumber}: $($line.Trim())") | Out-Null
            }
        }
    }

    # --- Banned dependency direction: simulator -> product ---------------------

    $simulatorToProduct = '(?:^|\s)(?:from|import)\s+[^\s]*assetops_backend'

    $simulatorSources = Get-SourceFiles -Root "simulator" -Extensions @(".py")

    foreach ($source in $simulatorSources) {
        $lineNumber = 0
        foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
            $lineNumber++
            if ($line -match $simulatorToProduct) {
                $relative = Resolve-Path -LiteralPath $source.FullName -Relative
                $failures.Add("Banned simulator-to-product import in ${relative}:${lineNumber}: $($line.Trim())") | Out-Null
            }
        }
    }

    # --- Banned dependency direction: product -> simulator ---------------------

    # Operator read models, API code, and any other product module must not
    # import simulator runtime or simulator truth modules. The only normal
    # simulator-to-product crossing is released canonical Source Envelopes
    # through ingestion, which is owned by a later slice.
    $productToSimulator = @(
        '(?:^|\s)(?:from|import)\s+[^\s]*assetops_simulator',
        '(?:^|\s)(?:from|import)\s+simulator(?:\.|\s|$)',
        'import_module\(\s*["''](?:assetops_simulator|simulator\.)'
    )

    $productSources = Get-SourceFiles -Root "backend" -Extensions @(".py")

    foreach ($source in $productSources) {
        $lineNumber = 0
        foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
            $lineNumber++
            foreach ($pattern in $productToSimulator) {
                if ($line -match $pattern) {
                    $relative = Resolve-Path -LiteralPath $source.FullName -Relative
                    $failures.Add("Banned product-to-simulator import in ${relative}:${lineNumber}: $($line.Trim())") | Out-Null
                    break
                }
            }
        }
    }

    return $failures
}
