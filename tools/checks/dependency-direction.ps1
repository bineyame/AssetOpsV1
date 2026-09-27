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

    # --- Banned dependency direction: anything -> host -----------------------
    #
    # `host/` is the composition leaf. It may import both sides, and nothing may
    # import it: v4 section 3.2 rules 3 and 4 together. That is what keeps the
    # crossing in one place rather than letting a product module reach a kernel
    # through a leaf that is allowed to know about both.
    #
    # `assetops_host` is banned too, although no such package exists. A later
    # slice that packaged the leaf would otherwise find the ban silently missing
    # the name it had chosen.

    # Anchored for the same reason as the contracts patterns below: `host` is an
    # ordinary English word and these trees talk about the leaf in prose.
    $intoHost = @(
        '^\s*(?:from|import)\s+host(?:\.|\s|$)',
        '^\s*(?:from|import)\s+[^\s]*assetops_host',
        'import_module\(\s*["''](?:host\.|assetops_host)',
        '(?:from|import|require)\s*\(?\s*["''][^"'']*(?:^|[./])host/'
    )

    $mayNotImportHost = @(
        @{ Root = "backend";   Extensions = @(".py") },
        @{ Root = "simulator"; Extensions = @(".py") },
        @{ Root = "contracts"; Extensions = @(".py") },
        @{ Root = "frontend/src"; Extensions = @(".ts", ".tsx", ".js", ".jsx") }
    )

    foreach ($tree in $mayNotImportHost) {
        foreach ($source in (Get-SourceFiles -Root $tree.Root -Extensions $tree.Extensions)) {
            $lineNumber = 0
            foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
                $lineNumber++
                foreach ($pattern in $intoHost) {
                    if ($line -match $pattern) {
                        $relative = Resolve-Path -LiteralPath $source.FullName -Relative
                        $failures.Add("Banned import of the composition leaf in ${relative}:${lineNumber}: $($line.Trim()). host/ may import both sides and nothing may import host/.") | Out-Null
                        break
                    }
                }
            }
        }
    }

    # --- The neutral contracts are neutral -----------------------------------
    #
    # `contracts/` holds the schemas and versioned rules both sides speak. A
    # contract that imported either side would stop being neutral and would make
    # the simulator reach the backend transitively - which is the hole v4 section
    # 3.2 rule 5 exists to close, and which no other check here would see.

    # Anchored at the start of the line, which is where a Python import
    # statement is. The three patterns above this function pre-date T021 and
    # match `import` anywhere after whitespace; that is fine for them and is not
    # fine here, because these modules discuss both sides at length in their own
    # docstrings and a prose sentence naming `assetops_backend` is not an import
    # of it. Anchoring is the narrower rule AND the correct one: an import
    # statement cannot appear mid-sentence.
    $contractsMayNotImport = @(
        '^\s*(?:from|import)\s+[^\s]*assetops_backend',
        '^\s*(?:from|import)\s+[^\s]*assetops_simulator',
        '^\s*(?:from|import)\s+(?:backend|simulator)(?:\.|\s|$)',
        'import_module\(\s*["''](?:assetops_backend|assetops_simulator)'
    )

    $contractSources = Get-SourceFiles -Root "contracts" -Extensions @(".py")

    if ($contractSources.Count -eq 0) {
        $failures.Add(("No module was scanned under contracts/, so the " +
            "neutrality check below is vacuous. Update the check, do not " +
            "delete it.")) | Out-Null
    }

    foreach ($source in $contractSources) {
        $lineNumber = 0
        foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
            $lineNumber++
            foreach ($pattern in $contractsMayNotImport) {
                if ($line -match $pattern) {
                    $relative = Resolve-Path -LiteralPath $source.FullName -Relative
                    $failures.Add("Banned import in the neutral contracts at ${relative}:${lineNumber}: $($line.Trim()). A shared contract that imports one side is not dependency-neutral.") | Out-Null
                    break
                }
            }
        }
    }

    return $failures
}
