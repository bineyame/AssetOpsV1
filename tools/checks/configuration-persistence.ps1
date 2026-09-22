# Seams: Configuration persistence port, and Shipped versus user-authored
# configuration.
#
# These exist so that replacing a store stays one new adapter module plus one
# composition change, and so that shipped canonical configuration cannot
# acquire a write path by accident.
#
#   - adapters are imported only by their own domain's composition module or
#     by a sibling adapter in the same layer
#   - no storage technology above the adapter layer, in any configuration
#     domain
#   - shipped configuration roots hold no write-capable call, the shipped Site
#     store ships empty, and the shipped scenario store ships the definition
#     the catalog needs
#   - configuration is written only by the user-store adapter
#   - each writable user store root has one owner and is gitignored
#
# T017 adds a second configuration domain, so the rules below are stated once
# and applied per domain rather than written out twice. Two copies would drift,
# and a seam enforced for Sites and forgotten for scenarios is the same as a
# seam that is not enforced: the scenario port would leak the first time
# somebody reached past it.
#
# T019 registers a third domain, and it is deliberately not configuration: a
# SimulationRun is a record this installation produced, not a document
# somebody authored. It is registered here anyway because the persistence
# seam it needs is exactly this one - a port, one composition module, one
# adapter layer, one write path, one owned root outside version control - and
# the guard caught the run store the moment it appeared, which is the whole
# point of the "resolves outside every known domain" failure below. A second
# copy of these rules for runs would be the drift this file was written to
# avoid.
#
# Test files are exempt from the scans below for the same reason they are
# exempt elsewhere: a test must be able to reach an adapter directly in order
# to prove what the adapter does.
#
# Do not weaken the checks below to make a task pass.

function Invoke-ConfigurationPersistenceCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $backendRoot = "backend/assetops_backend"

    # One entry per configuration domain. A domain is a package with a port, a
    # composition module, an adapter layer, and at least one store root.
    #
    # `Writer` is the one module allowed to write that domain's configuration,
    # or `$null` when the domain has no write path at all. Scenarios have none:
    # T017 ships no scenario creation flow, so the absence is structural and
    # the single-writer rule below covers the domain by construction.
    $domains = @(
        @{
            Name        = "Site"
            Package     = "$backendRoot/sites"
            Composition = "$backendRoot/sites/composition.py"
            Writer      = "$backendRoot/sites/adapters/yaml_user_site_store.py"
            UserRootVar = "USER_SITE_STORE_ROOT"
            UserRootOwner = "$backendRoot/sites/adapters/yaml_user_site_store.py"
        },
        @{
            Name        = "scenario"
            Package     = "$backendRoot/scenarios"
            Composition = "$backendRoot/scenarios/composition.py"
            Writer      = $null
            UserRootVar = "USER_SCENARIO_STORE_ROOT"
            UserRootOwner = "$backendRoot/scenarios/adapters/yaml_user_scenario_store.py"
        },
        @{
            Name        = "run"
            Package     = "$backendRoot/runs"
            Composition = "$backendRoot/runs/composition.py"
            Writer      = "$backendRoot/runs/adapters/yaml_run_store.py"
            UserRootVar = "RUN_STORE_ROOT"
            UserRootOwner = "$backendRoot/runs/adapters/yaml_run_store.py"
        }
    )

    foreach ($domain in $domains) {
        $domain.Adapters = "$($domain.Package)/adapters"
    }

    $shippedCatalogRoot = "config/site-templates"
    $shippedSiteRoot = "config/sites"
    $shippedScenarioRoot = "config/scenarios"

    $backendModules = Get-ScannedModules -Root "backend" -Extensions @(".py")

    if ($backendModules.Count -eq 0) {
        $failures.Add("No backend modules were scanned; the persistence checks would be vacuous") | Out-Null
    }

    # 1. Adapter isolation. An import that resolves into a domain's adapters
    #    package is permitted from that domain's single composition module
    #    only, plus from inside that same adapter layer: one adapter reusing a
    #    sibling adapter's reader does not leak storage technology above the
    #    layer, which is what this check exists to prevent. Everything above
    #    the layer still receives the port by injection.
    #
    #    Crossing domains is not permitted either. The Site composition module
    #    may not import a scenario adapter, because that would be a second
    #    place scenario storage is chosen.
    $adapterImport = '(?:^|\s)(?:from|import)\s+[A-Za-z_.]*adapters(?:[.\s]|$)'
    $adapterImportTarget = 'assetops_backend\.([A-Za-z_][A-Za-z0-9_]*)\.adapters'
    $adapterImportsSeen = @{}

    foreach ($domain in $domains) { $adapterImportsSeen[$domain.Name] = 0 }

    foreach ($module in $backendModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -notmatch $adapterImport) { continue }

            $targetDomain = $null
            if ($line -match $adapterImportTarget) {
                $package = $Matches[1]
                $targetDomain = $domains | Where-Object {
                    $_.Package -eq "$backendRoot/$package"
                } | Select-Object -First 1
            }

            if ($null -eq $targetDomain) {
                $failures.Add(("Adapter import that resolves outside every known " +
                    "configuration domain in $($module.Path):${lineNumber}: " +
                    "$($line.Trim()). Add the domain to " +
                    "tools/checks/configuration-persistence.ps1 so its seam is " +
                    "enforced, rather than letting the import go unchecked.")) | Out-Null
                continue
            }

            if ($module.Path -eq $targetDomain.Composition) {
                $adapterImportsSeen[$targetDomain.Name]++
                continue
            }

            if ($module.Path.StartsWith("$($targetDomain.Adapters)/")) { continue }

            $failures.Add(("Banned adapter import in $($module.Path):${lineNumber}: " +
                "$($line.Trim()). Only $($targetDomain.Composition) may import " +
                "$($targetDomain.Adapters); every other caller receives the " +
                "$($targetDomain.Name) port by injection.")) | Out-Null
        }
    }

    foreach ($domain in $domains) {
        if ($adapterImportsSeen[$domain.Name] -eq 0) {
            $failures.Add(("The adapter-isolation check found no adapter import in " +
                "$($domain.Composition), so it is no longer proving anything for " +
                "the $($domain.Name) domain. Update the check, do not delete it.")) | Out-Null
        }
    }

    # 2. No storage technology above the adapter layer. Inside a configuration
    #    package but outside its adapters/, storage modules and direct file
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
    $storageTechnologySeen = @{}
    foreach ($domain in $domains) { $storageTechnologySeen[$domain.Name] = $false }

    foreach ($module in $backendModules) {
        $domain = $domains | Where-Object {
            $module.Path.StartsWith("$($_.Package)/")
        } | Select-Object -First 1
        if ($null -eq $domain) { continue }

        $insideAdapters = $module.Path.StartsWith("$($domain.Adapters)/")

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $storageTechnology) {
                if ($line -notmatch $pattern) { continue }

                if ($insideAdapters) {
                    $storageTechnologySeen[$domain.Name] = $true
                    break
                }

                $failures.Add(("Storage technology above the adapter layer in " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). Move it into " +
                    "$($domain.Adapters) and speak domain records across the port.")) | Out-Null
                break
            }
        }
    }

    foreach ($domain in $domains) {
        if (-not $storageTechnologySeen[$domain.Name]) {
            $failures.Add(("The storage-technology check matched nothing inside " +
                "$($domain.Adapters), so its patterns may no longer match real " +
                "storage code. Update the check, do not delete it.")) | Out-Null
        }
    }

    # 3. The shipped configuration roots are not writable. Shipped canonical
    #    configuration is read-only at runtime, so no module that resolves a
    #    path inside a shipped root may also hold a write-capable call.
    if (-not (Test-Path -LiteralPath $shippedCatalogRoot -PathType Container)) {
        $failures.Add("Missing shipped template configuration root: $shippedCatalogRoot") | Out-Null
    }
    elseif (-not (Get-ChildItem -LiteralPath $shippedCatalogRoot -Filter "*.yaml" -File)) {
        $failures.Add("$shippedCatalogRoot ships no template document") | Out-Null
    }

    # The shipped Site store exists and ships empty. M1 ships zero canonical
    # Sites, so a document appearing here would put a Site nobody configured
    # into the operator index and make the first-run empty state a lie.
    if (-not (Test-Path -LiteralPath $shippedSiteRoot -PathType Container)) {
        $failures.Add("Missing shipped site configuration root: $shippedSiteRoot") | Out-Null
    }
    elseif (Get-ChildItem -LiteralPath $shippedSiteRoot -Filter "*.yaml" -File) {
        $failures.Add(("$shippedSiteRoot ships a site document. M1 ships zero " +
            "canonical sites: every site in the product is one a user created.")) | Out-Null
    }

    # The shipped scenario store exists and, unlike the Site store, does NOT
    # ship empty. T017 has no scenario creation flow, so without a tracked
    # definition the catalog would render an empty state on every fresh
    # checkout and the surface would have nothing to inspect. The asymmetry is
    # deliberate and is asserted rather than tolerated.
    if (-not (Test-Path -LiteralPath $shippedScenarioRoot -PathType Container)) {
        $failures.Add("Missing shipped scenario configuration root: $shippedScenarioRoot") | Out-Null
    }
    elseif (-not (Get-ChildItem -LiteralPath $shippedScenarioRoot -Filter "*.yaml" -File)) {
        $failures.Add(("$shippedScenarioRoot ships no scenario definition. The " +
            "product has no scenario creation flow, so a fresh checkout would " +
            "have no scenario to inspect at all.")) | Out-Null
    }

    # Each named reference must be found somewhere, so that adding a shipped
    # root without wiring it in here cannot leave it unprotected.
    $shippedRootReferences = @(
        "site-templates",
        "SHIPPED_SITE_TEMPLATE_ROOT",
        "SHIPPED_SITE_ROOT",
        "SHIPPED_SCENARIO_ROOT"
    )
    $shippedRootReference = ($shippedRootReferences -join "|")
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
    $shippedRootReferencesSeen = @{}
    foreach ($reference in $shippedRootReferences) { $shippedRootReferencesSeen[$reference] = $false }

    foreach ($module in $backendModules) {
        $namesShippedRoot = $false
        foreach ($line in $module.Lines) {
            foreach ($reference in $shippedRootReferences) {
                if ($line -match [regex]::Escape($reference)) {
                    $shippedRootReferencesSeen[$reference] = $true
                    $namesShippedRoot = $true
                }
            }
        }
        if (-not $namesShippedRoot) { continue }

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $writeCapable) {
                if ($line -match $pattern) {
                    $failures.Add(("Write-capable call in a module that resolves a " +
                        "shipped configuration root, $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). Shipped configuration is read-only at runtime.")) | Out-Null
                    break
                }
            }
        }
    }

    foreach ($reference in $shippedRootReferences) {
        if (-not $shippedRootReferencesSeen[$reference]) {
            $failures.Add(("No backend module names '$reference', so the " +
                "shipped-root write check is vacuous for it. Update the check, " +
                "do not delete it.")) | Out-Null
        }
    }

    # 4. Writes go through a user-store adapter and nowhere else.
    #
    #    T006 made the product able to write configuration for the first time.
    #    That is one capability in one module, and this check is what keeps it
    #    that way: a write-capable call anywhere else in the backend is a
    #    second write path that no port, no composition root, and no atomicity
    #    guarantee covers.
    #
    #    The scenario domain has no writer at all, so this rule is also what
    #    holds "T017 cannot write a scenario": a write appearing in any
    #    scenario module fails here, because no scenario module is on the
    #    allowlist.
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
    $writers = @($domains | Where-Object { $null -ne $_.Writer })
    $writerModules = @($writers | ForEach-Object { $_.Writer })
    $writeCallsByWriter = @{}
    foreach ($writer in $writerModules) { $writeCallsByWriter[$writer] = 0 }

    if ($writerModules.Count -eq 0) {
        $failures.Add(("No configuration domain declares a writer module, so the " +
            "single-write-path check has nothing to anchor on. Update the " +
            "check, do not delete it.")) | Out-Null
    }

    foreach ($module in $backendModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $writeCall) {
                if ($line -notmatch $pattern) { continue }

                if ($writerModules -contains $module.Path) {
                    $writeCallsByWriter[$module.Path]++
                    break
                }

                $failures.Add(("Write-capable call outside a user store adapter in " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). " +
                    "Configuration is written only by " +
                    "$($writerModules -join ', '), through its port.")) | Out-Null
                break
            }
        }
    }

    foreach ($writer in $writerModules) {
        if ($writeCallsByWriter[$writer] -eq 0) {
            $failures.Add(("The write-path check found no write-capable call in " +
                "$writer, so it is no longer proving anything. " +
                "Update the check, do not delete it.")) | Out-Null
        }
    }

    # 5. Each writable user store root has exactly one owner.
    #
    #    "Outside the shipped configuration roots" is only checkable if a root
    #    is declared in one place. Two declarations mean two answers to where
    #    user data lives, and the .gitignore check below would then be covering
    #    whichever one it happened to find.
    foreach ($domain in $domains) {
        $userStoreDeclaration = "$($domain.UserRootVar)\s*="
        $userStoreOwners = @()
        $userStoreRootSegment = $null

        foreach ($module in $backendModules) {
            foreach ($line in $module.Lines) {
                if ($line -notmatch $userStoreDeclaration) { continue }
                $userStoreOwners += $module.Path
                if ($line -match "$($domain.UserRootVar)\s*=\s*REPO_ROOT\s*/\s*""([^""]+)""") {
                    $userStoreRootSegment = $Matches[1]
                }
                break
            }
        }

        if ($userStoreOwners.Count -eq 0) {
            $failures.Add(("No backend module declares $($domain.UserRootVar), so the " +
                "writable $($domain.Name) store has no owned configuration point " +
                "and the gitignore check below is vacuous for it.")) | Out-Null
            continue
        }
        elseif ($userStoreOwners.Count -gt 1) {
            $failures.Add(("$($domain.UserRootVar) is declared in " +
                "$($userStoreOwners -join ', '). A writable store root must have " +
                "exactly one owner.")) | Out-Null
        }
        elseif ($userStoreOwners[0] -ne $domain.UserRootOwner) {
            $failures.Add(("$($domain.UserRootVar) is declared in $($userStoreOwners[0]). " +
                "It belongs to $($domain.UserRootOwner), the adapter that owns it.")) | Out-Null
        }

        # 6. The writable user store is outside the shipped roots and
        #    gitignored. User-authored configuration is user data, not shipped
        #    configuration. If it were tracked, a developer's demo site or
        #    scenario would ship to everyone and the shipped/user split would
        #    exist only in the code.
        if ($null -eq $userStoreRootSegment) {
            $failures.Add(("$($domain.UserRootVar) is not declared as a path under the " +
                "repository root, so the gitignore check cannot resolve it.")) | Out-Null
            continue
        }

        if ($userStoreRootSegment -eq "config") {
            $failures.Add(("The writable user $($domain.Name) store resolves inside " +
                "config/, which holds shipped read-only configuration. It must " +
                "live outside every shipped configuration root.")) | Out-Null
        }

        $gitignorePath = ".gitignore"
        if (-not (Test-Path -LiteralPath $gitignorePath -PathType Leaf)) {
            $failures.Add("Missing $gitignorePath") | Out-Null
            continue
        }

        $ignored = @(Get-Content -LiteralPath $gitignorePath |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ -and -not $_.StartsWith("#") })

        if ($ignored.Count -eq 0) {
            $failures.Add("$gitignorePath declares no entries; the coverage check is vacuous") | Out-Null
        }

        $covered = $ignored -contains $userStoreRootSegment -or
            $ignored -contains "$userStoreRootSegment/"
        if (-not $covered) {
            $failures.Add(("$gitignorePath does not cover the writable user " +
                "$($domain.Name) store root '$userStoreRootSegment/'. " +
                "User-authored configuration must not be tracked.")) | Out-Null
        }

        $trackedUserStore = git ls-files -- $userStoreRootSegment
        if ($trackedUserStore) {
            $failures.Add(("$userStoreRootSegment/ holds tracked files. The " +
                "writable user $($domain.Name) store must not be in version control.")) | Out-Null
        }
    }

    return $failures
}
