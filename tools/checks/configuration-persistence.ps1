# Seams: Configuration persistence port, and Shipped versus user-authored
# configuration.
#
# These exist so that replacing the store stays one new adapter module plus one
# composition change, and so that shipped canonical configuration cannot
# acquire a write path by accident.
#
#   - adapters are imported only by the composition module or each other
#   - no storage technology above the adapter layer
#   - shipped configuration roots hold no write-capable call, and the shipped
#     Site store ships empty
#   - configuration is written only by the user-store adapter
#   - the writable user store root has one owner and is gitignored
#
# Test files are exempt from the scans below for the same reason they are
# exempt elsewhere: a test must be able to reach an adapter directly in order
# to prove what the adapter does.
#
# Do not weaken the checks below to make a task pass.

function Invoke-ConfigurationPersistenceCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $sitesRoot = "backend/assetops_backend/sites"
    $sitesAdaptersRoot = "$sitesRoot/adapters"
    $compositionModule = "$sitesRoot/composition.py"
    $shippedCatalogRoot = "config/site-templates"
    $shippedSiteRoot = "config/sites"
    $userSiteStoreModule = "$sitesAdaptersRoot/yaml_user_site_store.py"

    $backendModules = Get-ScannedModules -Root "backend" -Extensions @(".py")

    if ($backendModules.Count -eq 0) {
        $failures.Add("No backend modules were scanned; the persistence checks would be vacuous") | Out-Null
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

            $failures.Add(("Banned adapter import in $($module.Path):${lineNumber}: " +
                "$($line.Trim()). Only $compositionModule may import " +
                "$sitesAdaptersRoot; every other caller receives the port by injection.")) | Out-Null
        }
    }

    if (-not $adapterImportSeen) {
        $failures.Add(("The adapter-isolation check found no adapter import in " +
            "$compositionModule, so it is no longer proving anything. Update the " +
            "check, do not delete it.")) | Out-Null
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

                $failures.Add(("Storage technology above the adapter layer in " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). Move it into " +
                    "$sitesAdaptersRoot and speak domain records across the port.")) | Out-Null
                break
            }
        }
    }

    if (-not $storageTechnologySeenInAdapters) {
        $failures.Add(("The storage-technology check matched nothing inside " +
            "$sitesAdaptersRoot, so its patterns may no longer match real " +
            "storage code. Update the check, do not delete it.")) | Out-Null
    }

    # 3. The shipped configuration roots are not writable. Shipped canonical
    #    configuration is read-only at runtime, so no module that resolves a
    #    path inside a shipped root may also hold a write-capable call. T006
    #    adds the shipped Site store to the roots this covers; the writable
    #    user store is a separate root, owned by a separate adapter, and is
    #    checked below.
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
                    $failures.Add(("Write-capable call in a module that resolves the " +
                        "shipped catalog root, $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). Shipped configuration is read-only at runtime.")) | Out-Null
                    break
                }
            }
        }
    }

    if ($shippedRootModules -eq 0) {
        $failures.Add(("No backend module resolves $shippedCatalogRoot, so the " +
            "shipped-catalog write check is vacuous. Update the check, do not " +
            "delete it.")) | Out-Null
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

                $failures.Add(("Write-capable call outside the user site store " +
                    "adapter in $($module.Path):${lineNumber}: $($line.Trim()). " +
                    "Configuration is written only by $userSiteStoreModule, " +
                    "through the SiteRepository port.")) | Out-Null
                break
            }
        }
    }

    if ($writeCallsInUserStore -eq 0) {
        $failures.Add(("The write-path check found no write-capable call in " +
            "$userSiteStoreModule, so it is no longer proving anything. " +
            "Update the check, do not delete it.")) | Out-Null
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
        $failures.Add(("No backend module declares USER_SITE_STORE_ROOT, so the " +
            "writable store has no owned configuration point and the " +
            "gitignore check below is vacuous.")) | Out-Null
    }
    elseif ($userStoreOwners.Count -gt 1) {
        $failures.Add(("USER_SITE_STORE_ROOT is declared in " +
            "$($userStoreOwners -join ', '). The writable store root must have " +
            "exactly one owner.")) | Out-Null
    }
    elseif ($userStoreOwners[0] -ne $userSiteStoreModule) {
        $failures.Add(("USER_SITE_STORE_ROOT is declared in $($userStoreOwners[0]). " +
            "It belongs to $userSiteStoreModule, the adapter that writes it.")) | Out-Null
    }

    # 6. The writable user store is outside the shipped roots and gitignored.
    #
    #    User-authored configuration is user data, not shipped configuration.
    #    If it were tracked, a developer's demo site would ship to everyone
    #    and the shipped/user store split would exist only in the code.
    if ($null -eq $userStoreRootSegment) {
        $failures.Add(("USER_SITE_STORE_ROOT is not declared as a path under the " +
            "repository root, so the gitignore check cannot resolve it.")) | Out-Null
    }
    else {
        if ($userStoreRootSegment -eq "config") {
            $failures.Add(("The writable user site store resolves inside config/, " +
                "which holds shipped read-only configuration. It must live " +
                "outside every shipped configuration root.")) | Out-Null
        }

        $gitignorePath = ".gitignore"
        if (-not (Test-Path -LiteralPath $gitignorePath -PathType Leaf)) {
            $failures.Add("Missing $gitignorePath") | Out-Null
        }
        else {
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
                    "site store root '$userStoreRootSegment/'. User-authored " +
                    "configuration must not be tracked.")) | Out-Null
            }

            $trackedUserStore = git ls-files -- $userStoreRootSegment
            if ($trackedUserStore) {
                $failures.Add(("$userStoreRootSegment/ holds tracked files. The " +
                    "writable user site store must not be in version control.")) | Out-Null
            }
        }
    }

    return $failures
}
