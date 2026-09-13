$ErrorActionPreference = "Stop"

# CI architecture guard for the "Stack and module direction",
# "Simulator/product boundary" and "Simulator feature gate" protected seams.
#
# Current scope: verify that the expected backend, frontend, and simulator roots
# exist in the modular-monolith shape, and that the banned dependency directions
# stay banned:
#
#   - no direct UI-to-simulator imports
#   - no simulator-to-product imports/writes
#   - no product-to-simulator imports (operator read models and backend code
#     must not import simulator runtime/truth modules)
#
# and that the Simulator Lab gate keeps a single chokepoint:
#
#   - `config/app-config.json` declares a boolean `simulator_lab.enabled`
#   - simulator URLs are declared only in the gated modules, so an entry point
#     or API path cannot be added outside the gate
#
# Do not weaken the checks below to make a task pass.

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    $failures = New-Object System.Collections.Generic.List[string]

    function Add-Failure($message) {
        $failures.Add($message) | Out-Null
    }

    # Enumerate source files under a root, pruning ignored directories BEFORE
    # descending into them and tolerating directories the process cannot read.
    #
    # Get-ChildItem -Recurse walks every subtree first and filters afterwards,
    # so a permission-denied cache directory (pytest and npm both create these)
    # aborts the whole scan under $ErrorActionPreference = "Stop". A guard that
    # fails for reasons unrelated to the seam it protects gets ignored, so this
    # prunes first and reports unreadable directories without failing the run.
    $ignoredDirectories = @(
        ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
        "node_modules", "dist", "build", "coverage", ".mypy_cache", ".ruff_cache"
    )

    function Get-SourceFiles {
        param(
            [Parameter(Mandatory = $true)] [string] $Root,
            [string[]] $Extensions
        )

        if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
            return @()
        }

        $found = New-Object System.Collections.Generic.List[System.IO.FileInfo]
        $pending = New-Object System.Collections.Generic.Stack[string]
        $pending.Push((Resolve-Path -LiteralPath $Root).Path)

        while ($pending.Count -gt 0) {
            $directory = $pending.Pop()

            try {
                $entries = Get-ChildItem -LiteralPath $directory -Force -ErrorAction Stop
            } catch {
                Write-Host "  note: skipped unreadable directory $directory"
                continue
            }

            foreach ($entry in $entries) {
                if ($entry.PSIsContainer) {
                    if ($ignoredDirectories -contains $entry.Name) { continue }
                    if ($entry.Name -like "*.egg-info") { continue }
                    $pending.Push($entry.FullName)
                    continue
                }

                if ($Extensions -and ($entry.Extension -notin $Extensions)) { continue }
                $found.Add($entry) | Out-Null
            }
        }

        return $found
    }

    # --- Expected module roots -------------------------------------------------

    $requiredDirectories = @(
        "backend",
        "backend/assetops_backend",
        "frontend",
        "frontend/src",
        "simulator",
        "simulator/assetops_simulator"
    )

    foreach ($directory in $requiredDirectories) {
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            Add-Failure "Missing expected module root: $directory"
        }
    }

    $requiredFiles = @(
        "backend/pyproject.toml",
        "backend/assetops_backend/__init__.py",
        "backend/assetops_backend/main.py",
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/src/main.tsx",
        "simulator/assetops_simulator/__init__.py"
    )

    foreach ($file in $requiredFiles) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            Add-Failure "Missing expected root marker file: $file"
        }
    }

    # --- Declared stack --------------------------------------------------------

    if (Test-Path -LiteralPath "backend/pyproject.toml") {
        $backendProject = Get-Content -LiteralPath "backend/pyproject.toml" -Raw
        if ($backendProject -notmatch "fastapi") {
            Add-Failure "backend/pyproject.toml must declare a FastAPI dependency"
        }
    }

    if (Test-Path -LiteralPath "frontend/package.json") {
        $frontendPackage = Get-Content -LiteralPath "frontend/package.json" -Raw
        foreach ($required in @("react", "typescript")) {
            if ($frontendPackage -notmatch $required) {
                Add-Failure "frontend/package.json must declare $required"
            }
        }
    }

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
                Add-Failure "Banned UI-to-simulator import in ${relative}:${lineNumber}: $($line.Trim())"
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
                Add-Failure "Banned simulator-to-product import in ${relative}:${lineNumber}: $($line.Trim())"
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
                    Add-Failure "Banned product-to-simulator import in ${relative}:${lineNumber}: $($line.Trim())"
                    break
                }
            }
        }
    }

    # --- Simulator feature gate ------------------------------------------------

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
        Add-Failure "Missing Simulator Lab gate configuration: $gateConfigPath"
    }
    else {
        try {
            $gateConfig = Get-Content -LiteralPath $gateConfigPath -Raw | ConvertFrom-Json
        } catch {
            $gateConfig = $null
            Add-Failure "$gateConfigPath is not valid JSON"
        }

        if ($null -ne $gateConfig) {
            $simulatorLab = $gateConfig.PSObject.Properties["simulator_lab"]
            if ($null -eq $simulatorLab) {
                Add-Failure "$gateConfigPath must declare a 'simulator_lab' section"
            }
            elseif ($null -eq $simulatorLab.Value.PSObject.Properties["enabled"]) {
                Add-Failure "$gateConfigPath must declare 'simulator_lab.enabled'"
            }
            elseif ($simulatorLab.Value.enabled -isnot [bool]) {
                Add-Failure "$gateConfigPath 'simulator_lab.enabled' must be a boolean"
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
        foreach ($source in (Get-SourceFiles -Root $scan.Root -Extensions $scan.Extensions)) {
            $relative = (Resolve-Path -LiteralPath $source.FullName -Relative) `
                -replace '^\.[\\/]', '' -replace '\\', '/'

            if ($gatedModules -contains $relative) { continue }
            if ($relative -match '(^|/)(tests|__tests__)/') { continue }

            $lineNumber = 0
            foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
                $lineNumber++
                if ($line -imatch $simulatorPathLiteral) {
                    Add-Failure ("Simulator URL declared outside the gated module in " +
                        "${relative}:${lineNumber}: $($line.Trim()). Import the path " +
                        "constant from a gated module instead.")
                }
            }
        }
    }

    # --- Configuration persistence port ----------------------------------------

    # Three checks protect the "Configuration persistence port" and
    # "Shipped versus user-authored configuration" seams. They exist so that
    # replacing the store stays one new adapter module plus one composition
    # change, and so that shipped canonical configuration cannot acquire a
    # write path by accident.
    #
    # Test files are exempt for the same reason they are exempt from the gate
    # scan: a test must be able to reach an adapter directly in order to prove
    # what the adapter does.

    $sitesRoot = "backend/assetops_backend/sites"
    $sitesAdaptersRoot = "$sitesRoot/adapters"
    $compositionModule = "$sitesRoot/composition.py"
    $shippedCatalogRoot = "config/site-templates"

    function Get-BackendModules {
        $modules = @()
        foreach ($source in (Get-SourceFiles -Root "backend" -Extensions @(".py"))) {
            $relative = (Resolve-Path -LiteralPath $source.FullName -Relative) `
                -replace '^\.[\\/]', '' -replace '\\', '/'

            if ($relative -match '(^|/)(tests|__tests__)/') { continue }

            $modules += [pscustomobject]@{
                Path  = $relative
                Lines = @(Get-Content -LiteralPath $source.FullName)
            }
        }
        return $modules
    }

    $backendModules = Get-BackendModules

    if ($backendModules.Count -eq 0) {
        Add-Failure "No backend modules were scanned; the persistence checks would be vacuous"
    }

    # 1. Adapter isolation. An import that resolves into the sites adapters
    #    package is permitted from the single composition module only.
    $adapterImport = '(?:^|\s)(?:from|import)\s+[A-Za-z_.]*adapters(?:[.\s]|$)'
    $adapterImportSeen = $false

    foreach ($module in $backendModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -notmatch $adapterImport) { continue }

            if ($module.Path -eq $compositionModule) {
                $adapterImportSeen = $true
                continue
            }

            Add-Failure ("Banned adapter import in $($module.Path):${lineNumber}: " +
                "$($line.Trim()). Only $compositionModule may import " +
                "$sitesAdaptersRoot; every other caller receives the port by injection.")
        }
    }

    if (-not $adapterImportSeen) {
        Add-Failure ("The adapter-isolation check found no adapter import in " +
            "$compositionModule, so it is no longer proving anything. Update the " +
            "check, do not delete it.")
    }

    # 2. No storage technology above the adapter layer. Inside the sites
    #    package but outside adapters/, storage modules and direct file
    #    opening are banned: a port that speaks paths and YAML is not a seam.
    $storageTechnology = @(
        '(?:^|\s)import\s+yaml(?:[.\s]|$)',
        '(?:^|\s)from\s+yaml(?:[.\s]|$)',
        '(?:^|\s)import\s+pathlib(?:[.\s]|$)',
        '(?:^|\s)from\s+pathlib(?:[.\s]|$)',
        '(?:^|\s)import\s+sqlite3(?:[.\s]|$)',
        '(?:^|\s)from\s+sqlite3(?:[.\s]|$)',
        'open\('
    )
    $storageTechnologySeenInAdapters = $false

    foreach ($module in $backendModules) {
        $insideSites = $module.Path.StartsWith("$sitesRoot/")
        $insideAdapters = $module.Path.StartsWith("$sitesAdaptersRoot/")
        if (-not $insideSites) { continue }

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $storageTechnology) {
                if ($line -notmatch $pattern) { continue }

                if ($insideAdapters) {
                    $storageTechnologySeenInAdapters = $true
                    break
                }

                Add-Failure ("Storage technology above the adapter layer in " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). Move it into " +
                    "$sitesAdaptersRoot and speak domain records across the port.")
                break
            }
        }
    }

    if (-not $storageTechnologySeenInAdapters) {
        Add-Failure ("The storage-technology check matched nothing inside " +
            "$sitesAdaptersRoot, so its patterns may no longer match real " +
            "storage code. Update the check, do not delete it.")
    }

    # 3. The shipped catalog is not writable. Shipped canonical configuration
    #    is read-only at runtime, so no module that resolves a path inside the
    #    shipped root may also hold a write-capable call.
    if (-not (Test-Path -LiteralPath $shippedCatalogRoot -PathType Container)) {
        Add-Failure "Missing shipped template configuration root: $shippedCatalogRoot"
    }
    elseif (-not (Get-ChildItem -LiteralPath $shippedCatalogRoot -Filter "*.yaml" -File)) {
        Add-Failure "$shippedCatalogRoot ships no template document"
    }

    $shippedRootReference = 'site-templates|SHIPPED_SITE_TEMPLATE_ROOT'
    $writeCapable = @(
        '\.write_text\(',
        '\.write_bytes\(',
        '\.mkdir\(',
        '\.touch\(',
        '\.unlink\(',
        '\.rmdir\(',
        '(?:^|\s)os\.(?:remove|unlink|replace|rename|makedirs|mkdir)\(',
        '(?:^|\s)shutil\.',
        '(?:^|\s)tempfile\.',
        'open\('
    )
    $shippedRootModules = 0

    foreach ($module in $backendModules) {
        $namesShippedRoot = $false
        foreach ($line in $module.Lines) {
            if ($line -match $shippedRootReference) { $namesShippedRoot = $true; break }
        }
        if (-not $namesShippedRoot) { continue }

        $shippedRootModules++

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $writeCapable) {
                if ($line -match $pattern) {
                    Add-Failure ("Write-capable call in a module that resolves the " +
                        "shipped catalog root, $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). Shipped configuration is read-only at runtime.")
                    break
                }
            }
        }
    }

    if ($shippedRootModules -eq 0) {
        Add-Failure ("No backend module resolves $shippedCatalogRoot, so the " +
            "shipped-catalog write check is vacuous. Update the check, do not " +
            "delete it.")
    }

    if ($failures.Count -gt 0) {
        Write-Host "Architecture check failed:"
        foreach ($failure in $failures) {
            Write-Host "- $failure"
        }
        exit 1
    }

    Write-Host "Architecture check passed."
}
finally {
    Pop-Location
}
