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
# and the configuration persistence, shipped-versus-user-authored configuration
# and shared-Site-substrate seams:
#
#   - adapters are imported only by the composition module or each other
#   - no storage technology above the adapter layer
#   - shipped configuration roots hold no write-capable call, and the shipped
#     Site store ships empty
#   - configuration is written only by the user-store adapter
#   - the writable user store root has one owner and is gitignored
#   - Site presentation is defined only in `frontend/src/sites/`
#   - that substrate is a leaf with no shell, mode, or variant discriminant
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
    $shippedSiteRoot = "config/sites"
    $userSiteStoreModule = "$sitesAdaptersRoot/yaml_user_site_store.py"

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
    #    package is permitted from the single composition module only, plus
    #    from inside the adapter layer itself: one adapter reusing a sibling
    #    adapter's reader does not leak storage technology above the layer,
    #    which is what this check exists to prevent. Everything above the
    #    layer still receives the port by injection.
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

            if ($module.Path.StartsWith("$sitesAdaptersRoot/")) { continue }

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

    # 3. The shipped configuration roots are not writable. Shipped canonical
    #    configuration is read-only at runtime, so no module that resolves a
    #    path inside a shipped root may also hold a write-capable call. T006
    #    adds the shipped Site store to the roots this covers; the writable
    #    user store is a separate root, owned by a separate adapter, and is
    #    checked below.
    if (-not (Test-Path -LiteralPath $shippedCatalogRoot -PathType Container)) {
        Add-Failure "Missing shipped template configuration root: $shippedCatalogRoot"
    }
    elseif (-not (Get-ChildItem -LiteralPath $shippedCatalogRoot -Filter "*.yaml" -File)) {
        Add-Failure "$shippedCatalogRoot ships no template document"
    }

    # The shipped Site store exists and ships empty. M1 ships zero canonical
    # Sites, so a document appearing here would put a Site nobody configured
    # into the operator index and make the first-run empty state a lie.
    if (-not (Test-Path -LiteralPath $shippedSiteRoot -PathType Container)) {
        Add-Failure "Missing shipped site configuration root: $shippedSiteRoot"
    }
    elseif (Get-ChildItem -LiteralPath $shippedSiteRoot -Filter "*.yaml" -File) {
        Add-Failure ("$shippedSiteRoot ships a site document. M1 ships zero " +
            "canonical sites: every site in the product is one a user created.")
    }

    $shippedRootReference = 'site-templates|SHIPPED_SITE_TEMPLATE_ROOT|SHIPPED_SITE_ROOT'
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

    # 4. Writes go through the user-store adapter and nowhere else.
    #
    #    T006 makes the product able to write configuration for the first
    #    time. That is one capability in one module, and this check is what
    #    keeps it that way: a write-capable call anywhere else in the backend
    #    is a second write path that no port, no composition root, and no
    #    atomicity guarantee covers.
    #
    #    Reading is not restricted here - the pattern list deliberately omits
    #    a bare `open(`, which the storage-technology check above already
    #    confines to the adapter layer.
    $writeCall = @(
        '\.write_text\(',
        '\.write_bytes\(',
        '\.mkdir\(',
        '\.touch\(',
        '\.unlink\(',
        '\.rmdir\(',
        '(?:^|\s)os\.(?:remove|unlink|replace|rename|makedirs|mkdir|open|write|truncate)\(',
        '(?:^|\s)shutil\.',
        '(?:^|\s)tempfile\.'
    )
    $writeCallsInUserStore = 0

    foreach ($module in $backendModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $writeCall) {
                if ($line -notmatch $pattern) { continue }

                if ($module.Path -eq $userSiteStoreModule) {
                    $writeCallsInUserStore++
                    break
                }

                Add-Failure ("Write-capable call outside the user site store " +
                    "adapter in $($module.Path):${lineNumber}: $($line.Trim()). " +
                    "Configuration is written only by $userSiteStoreModule, " +
                    "through the SiteRepository port.")
                break
            }
        }
    }

    if ($writeCallsInUserStore -eq 0) {
        Add-Failure ("The write-path check found no write-capable call in " +
            "$userSiteStoreModule, so it is no longer proving anything. " +
            "Update the check, do not delete it.")
    }

    # 5. The writable user store root has exactly one owner.
    #
    #    "Outside the shipped configuration roots" is only checkable if the
    #    root is declared in one place. Two declarations mean two answers to
    #    where user data lives, and the .gitignore check below would then be
    #    covering whichever one it happened to find.
    $userStoreDeclaration = 'USER_SITE_STORE_ROOT\s*='
    $userStoreOwners = @()
    $userStoreRootSegment = $null

    foreach ($module in $backendModules) {
        foreach ($line in $module.Lines) {
            if ($line -notmatch $userStoreDeclaration) { continue }
            $userStoreOwners += $module.Path
            if ($line -match 'USER_SITE_STORE_ROOT\s*=\s*REPO_ROOT\s*/\s*"([^"]+)"') {
                $userStoreRootSegment = $Matches[1]
            }
            break
        }
    }

    if ($userStoreOwners.Count -eq 0) {
        Add-Failure ("No backend module declares USER_SITE_STORE_ROOT, so the " +
            "writable store has no owned configuration point and the " +
            "gitignore check below is vacuous.")
    }
    elseif ($userStoreOwners.Count -gt 1) {
        Add-Failure ("USER_SITE_STORE_ROOT is declared in " +
            "$($userStoreOwners -join ', '). The writable store root must have " +
            "exactly one owner.")
    }
    elseif ($userStoreOwners[0] -ne $userSiteStoreModule) {
        Add-Failure ("USER_SITE_STORE_ROOT is declared in $($userStoreOwners[0]). " +
            "It belongs to $userSiteStoreModule, the adapter that writes it.")
    }

    # 6. The writable user store is outside the shipped roots and gitignored.
    #
    #    User-authored configuration is user data, not shipped configuration.
    #    If it were tracked, a developer's demo site would ship to everyone
    #    and the shipped/user store split would exist only in the code.
    if ($null -eq $userStoreRootSegment) {
        Add-Failure ("USER_SITE_STORE_ROOT is not declared as a path under the " +
            "repository root, so the gitignore check cannot resolve it.")
    }
    else {
        if ($userStoreRootSegment -eq "config") {
            Add-Failure ("The writable user site store resolves inside config/, " +
                "which holds shipped read-only configuration. It must live " +
                "outside every shipped configuration root.")
        }

        $gitignorePath = ".gitignore"
        if (-not (Test-Path -LiteralPath $gitignorePath -PathType Leaf)) {
            Add-Failure "Missing $gitignorePath"
        }
        else {
            $ignored = @(Get-Content -LiteralPath $gitignorePath |
                ForEach-Object { $_.Trim() } |
                Where-Object { $_ -and -not $_.StartsWith("#") })

            if ($ignored.Count -eq 0) {
                Add-Failure "$gitignorePath declares no entries; the coverage check is vacuous"
            }

            $covered = $ignored -contains $userStoreRootSegment -or
                $ignored -contains "$userStoreRootSegment/"
            if (-not $covered) {
                Add-Failure ("$gitignorePath does not cover the writable user " +
                    "site store root '$userStoreRootSegment/'. User-authored " +
                    "configuration must not be tracked.")
            }

            $trackedUserStore = git ls-files -- $userStoreRootSegment
            if ($trackedUserStore) {
                Add-Failure ("$userStoreRootSegment/ holds tracked files. The " +
                    "writable user site store must not be in version control.")
            }
        }
    }

    # --- Shared Site presentation substrate ------------------------------------

    # Two structural checks for the "Shared Site presentation substrate" seam.
    # They are backstops, not the primary guard: render equivalence is, and it
    # needs a second consumer of the substrate to compare against, so it ships
    # with the Lab's Site view. These two are what can be enforced today.
    #
    # Test directories are exempt for the same reason they are exempt above: a
    # test must be able to reach across a boundary in order to prove where it
    # is.

    $substrateRoot = "frontend/src/sites"

    if (-not (Test-Path -LiteralPath $substrateRoot -PathType Container)) {
        Add-Failure "Missing shared Site presentation substrate root: $substrateRoot"
    }

    # 7. Single definition. Site presentation components, Site view-model
    #    derivation, and Site read-model types resolve in the substrate only.
    #    Two shells that each declare one drift into two Site models, and by
    #    the time that is visible both have users.
    #
    #    Template types are excluded by name: a template is not a Site and its
    #    read model belongs to the Lab's template surfaces.
    $substrateDefinitions = @(
        @{
            Name    = "Site read-model type"
            Pattern = '(?:interface|type)\s+Site(?!Template)[A-Za-z]*(?:ReadModel|Summary|Row|View|Record)\b'
        },
        @{
            Name    = "Site presentation component"
            Pattern = 'function\s+Sites?(?:Index|Table|Row|Card|List|Badge|Panel)\b'
        },
        @{
            Name    = "Site view-model derivation"
            Pattern = 'function\s+(?:derive|to|build)Site[A-Za-z]*View\b'
        },
        @{
            # The site-page components. Named separately from the listing
            # components above because they do not share their noun suffixes,
            # and a definition the pattern list does not reach is a definition
            # the single-definition check does not protect.
            #
            # `*Frame` is excluded because that is this tree's name for a shell
            # route frame: a frame supplies the landmark and composes the
            # substrate, and composing is exactly what a shell is allowed to
            # do. What must not exist outside the substrate is a component that
            # decides what a site looks like.
            Name    = "Site detail presentation component"
            Pattern = 'function\s+SiteDetail(?!Frame\b)[A-Za-z]*\s*\('
        }
    )

    $frontendModules = @()
    foreach ($source in (Get-SourceFiles -Root "frontend/src" -Extensions @(".ts", ".tsx"))) {
        $relative = (Resolve-Path -LiteralPath $source.FullName -Relative) `
            -replace '^\.[\\/]', '' -replace '\\', '/'

        if ($relative -match '(^|/)(tests|__tests__)/') { continue }

        $frontendModules += [pscustomobject]@{
            Path      = $relative
            InSites   = $relative.StartsWith("$substrateRoot/")
            Lines     = @(Get-Content -LiteralPath $source.FullName)
        }
    }

    if ($frontendModules.Count -eq 0) {
        Add-Failure "No frontend modules were scanned; the substrate checks would be vacuous"
    }

    foreach ($definition in $substrateDefinitions) {
        $seenInSubstrate = $false

        foreach ($module in $frontendModules) {
            $lineNumber = 0
            foreach ($line in $module.Lines) {
                $lineNumber++
                if ($line -cnotmatch $definition.Pattern) { continue }

                if ($module.InSites) {
                    $seenInSubstrate = $true
                    continue
                }

                Add-Failure ("$($definition.Name) declared outside the shared " +
                    "substrate in $($module.Path):${lineNumber}: $($line.Trim()). " +
                    "It belongs in $substrateRoot, which both shells compose.")
            }
        }

        if (-not $seenInSubstrate) {
            Add-Failure ("The single-definition check found no " +
                "$($definition.Name) in $substrateRoot, so it is no longer " +
                "proving anything. Update the check, do not delete it.")
        }
    }

    # 8. Leaf direction. The substrate imports no shell code, no simulator
    #    code, and no feature flag, and carries no shell, mode, or variant
    #    discriminant. A branch inside the shared core is a fork with extra
    #    steps, and its branches drift independently.
    $substrateBannedImports = @(
        'from\s+["''][^"'']*shell[/"'']',
        'from\s+["''][^"'']*featureFlags',
        'from\s+["''][^"'']*[Ss]imulator'
    )
    $substrateBannedDiscriminants = @(
        '\b(?:variant|isLab|isSimulator|shellVariant|labVariant)\s*\??\s*:',
        '\bshell\s*\??\s*:\s*["'']',
        '["''](?:lab|operator)["'']\s*\|\s*["''](?:lab|operator)["'']'
    )
    $substrateModules = 0
    $substrateImports = 0

    foreach ($module in $frontendModules) {
        if (-not $module.InSites) { continue }
        $substrateModules++

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            if ($line -match 'from\s+["'']') { $substrateImports++ }

            foreach ($pattern in $substrateBannedImports) {
                if ($line -match $pattern) {
                    Add-Failure ("The shared Site substrate is a leaf, but " +
                        "$($module.Path):${lineNumber} imports out of it: " +
                        "$($line.Trim()). $substrateRoot must not import shell " +
                        "code, simulator code, or the feature flag.")
                    break
                }
            }

            foreach ($pattern in $substrateBannedDiscriminants) {
                if ($line -match $pattern) {
                    Add-Failure ("Shell, mode, or variant discriminant in the " +
                        "shared Site substrate at $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). Every shell difference must be an " +
                        "addition around the core, never a branch inside it.")
                    break
                }
            }
        }
    }

    # 9. Navigation truthfulness for the site page. A site is addressed by
    #    `site_id`, so the parameterless `/site-details` placeholder is gone
    #    and the identified route replaced it. This is a pair of assertions on
    #    purpose: a lone "the placeholder is absent" check would also pass on a
    #    tree where nothing addresses a site at all, so the identified route
    #    has to be found for the absence to mean anything - the route
    #    parameter is what is looked for, because the path itself is built from
    #    the Sites path constant rather than spelled out.
    #
    #    `/site-configuration` is deliberately NOT checked here. It is still a
    #    parameterless placeholder and is removed by the slice that gives it an
    #    identified replacement; adding it now would fail the build for a route
    #    this slice does not replace.
    $identifiedSiteRoutePath = 0

    foreach ($module in $frontendModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            if ($line -match '["'']/site-details') {
                Add-Failure ("Parameterless site destination at " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). A site is " +
                    "addressed by site_id; a Site Details link that names no " +
                    "site is not a destination.")
            }

            if ($line -match '/:siteId') {
                $identifiedSiteRoutePath++
            }
        }
    }

    if ($identifiedSiteRoutePath -eq 0) {
        Add-Failure ("No identified site route was found in frontend/src, so " +
            "the navigation-truthfulness check is vacuous. Update the check, " +
            "do not delete it.")
    }

    if ($substrateModules -eq 0) {
        Add-Failure ("No module was scanned under $substrateRoot, so the " +
            "leaf-direction check is vacuous. Update the check, do not delete it.")
    }
    elseif ($substrateImports -eq 0) {
        Add-Failure ("No import was seen under $substrateRoot, so the " +
            "leaf-direction import check is vacuous. Update the check, do not " +
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
