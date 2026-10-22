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
            # S1-01: the YAML user store stays the legacy writer for
            # unimported Sites and Lab; import_files.py writes only the
            # import comparison report (rule 8 confines it). The PostgreSQL
            # adapter is the sole writer for imported product Sites and writes
            # no file, so rule 8, not this list, holds it.
            Writer      = @(
                "$backendRoot/sites/adapters/yaml_user_site_store.py",
                "$backendRoot/sites/adapters/import_files.py"
            )
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
            # T027 (D4): the gated Commit store files sealed artifacts beside
            # runs, in the same domain and adapter layer, with its own single
            # writer and its own owned, gitignored root.
            Writer      = @(
                "$backendRoot/runs/adapters/yaml_run_store.py",
                "$backendRoot/runs/adapters/json_commit_store.py"
            )
            UserRootVar = "RUN_STORE_ROOT"
            UserRootOwner = "$backendRoot/runs/adapters/yaml_run_store.py"
            ExtraUserRoots = @(
                @{
                    Var   = "COMMIT_STORE_ROOT"
                    Owner = "$backendRoot/runs/adapters/json_commit_store.py"
                }
            )
        },
        @{
            # T027: accepted evidence and its immutable configuration/mapping
            # registries. Written only by ingestion through the JSON adapter.
            Name        = "evidence"
            Package     = "$backendRoot/evidence"
            Composition = "$backendRoot/evidence/composition.py"
            # S2-02 phase 2: the gateway upload secret file is the second
            # evidence-domain file writer (written once at issue, owner-only).
            Writer      = @(
                "$backendRoot/evidence/adapters/json_evidence_store.py",
                "$backendRoot/evidence/adapters/gateway_credential_file.py",
                # S2-02 phase 3a: immutable legacy comparison reports (Q14 default).
                "$backendRoot/evidence/adapters/legacy_comparison_file.py"
            )
            UserRootVar = "EVIDENCE_STORE_ROOT"
            UserRootOwner = "$backendRoot/evidence/adapters/json_evidence_store.py"
        },
        @{
            # T028: assessment revision history, derived from accepted evidence
            # but retained (AC13). Written only by the analytics service through
            # the JSON adapter; the memory adapter writes no file.
            Name        = "analytics"
            Package     = "$backendRoot/analytics"
            Composition = "$backendRoot/analytics/composition.py"
            Writer      = "$backendRoot/analytics/adapters/json_assessment_store.py"
            UserRootVar = "ASSESSMENT_STORE_ROOT"
            UserRootOwner = "$backendRoot/analytics/adapters/json_assessment_store.py"
        },
        @{
            # S4-02a: Site financial assumptions. Database-only: no file writer and
            # no writable file root (UserRootVar is null, so the user-root rule
            # skips it); rule 8 confines its PostgreSQL writer. Adapter isolation
            # still applies: only the composition module imports its adapters.
            Name        = "financials"
            Package     = "$backendRoot/financials"
            Composition = "$backendRoot/financials/composition.py"
            Writer      = $null
            UserRootVar = $null
            UserRootOwner = $null
        }
        @{
            # S4-02d: environment and Site schedule state. Database-only; rule 8 confines its PostgreSQL writer
            # (the eighth). Only its composition imports the adapter; callers receive the ScheduleStore port.
            Name        = "scheduling"
            Package     = "$backendRoot/scheduling"
            Composition = "$backendRoot/scheduling/composition.py"
            Writer      = $null
            UserRootVar = $null
            UserRootOwner = $null
        }
        @{
            # S6-01a: Finding-linked Actions, immutable events and Action-owned basis/change rows. Database-only;
            # rule 8 confines its PostgreSQL writer (the ninth). Only its composition imports the adapters.
            Name        = "actions"
            Package     = "$backendRoot/actions"
            Composition = "$backendRoot/actions/composition.py"
            Writer      = $null
            UserRootVar = $null
            UserRootOwner = $null
        }
        @{
            # W3-01 commit 2 (q5 ruling 3): the read-only estate roots. No writer; only its composition imports the
            # estate adapters, whose driver import rule 8 admits through `$pgReaders` (never `$pgWriters`).
            Name        = "estate"
            Package     = "$backendRoot/estate"
            Composition = "$backendRoot/estate/composition.py"
            Writer      = $null
            UserRootVar = $null
            UserRootOwner = $null
        }
        @{
            # W4-01 commit 2: work cases, events, records, plans and OperationalRecords. Database-only; rule 8
            # confines its PostgreSQL writer (the tenth). Only its composition imports the adapters.
            Name        = "work"
            Package     = "$backendRoot/work"
            Composition = "$backendRoot/work/composition.py"
            Writer      = $null
            UserRootVar = $null
            UserRootOwner = $null
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
        # S1-01: database drivers and DDL tooling are storage technology too.
        '(?:^|\s)(?:import|from)\s+(?:sqlalchemy|psycopg|alembic)(?:[.\s]|$)',
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
    #    A domain may own more than one writable root (`ExtraUserRoots`); each
    #    is held to the same single-owner and gitignore rules.
    $userRoots = @(foreach ($domain in $domains) {
        if ($null -ne $domain.UserRootVar) {
            @{ Name = $domain.Name; Var = $domain.UserRootVar; Owner = $domain.UserRootOwner }
        }
        foreach ($extra in @($domain.ExtraUserRoots)) {
            if ($null -eq $extra) { continue }
            @{ Name = "$($domain.Name) ($($extra.Var))"; Var = $extra.Var; Owner = $extra.Owner }
        }
    })
    foreach ($root in $userRoots) {
        $userStoreDeclaration = "$($root.Var)\s*="
        $userStoreOwners = @()
        $userStoreRootSegment = $null

        foreach ($module in $backendModules) {
            foreach ($line in $module.Lines) {
                if ($line -notmatch $userStoreDeclaration) { continue }
                $userStoreOwners += $module.Path
                if ($line -match "$($root.Var)\s*=\s*REPO_ROOT\s*/\s*""([^""]+)""") {
                    $userStoreRootSegment = $Matches[1]
                }
                break
            }
        }

        if ($userStoreOwners.Count -eq 0) {
            $failures.Add(("No backend module declares $($root.Var), so the " +
                "writable $($root.Name) store has no owned configuration point " +
                "and the gitignore check below is vacuous for it.")) | Out-Null
            continue
        }
        elseif ($userStoreOwners.Count -gt 1) {
            $failures.Add(("$($root.Var) is declared in " +
                "$($userStoreOwners -join ', '). A writable store root must have " +
                "exactly one owner.")) | Out-Null
        }
        elseif ($userStoreOwners[0] -ne $root.Owner) {
            $failures.Add(("$($root.Var) is declared in $($userStoreOwners[0]). " +
                "It belongs to $($root.Owner), the adapter that owns it.")) | Out-Null
        }

        # 6. The writable user store is outside the shipped roots and
        #    gitignored. User-authored configuration is user data, not shipped
        #    configuration. If it were tracked, a developer's demo site or
        #    scenario would ship to everyone and the shipped/user split would
        #    exist only in the code.
        if ($null -eq $userStoreRootSegment) {
            $failures.Add(("$($root.Var) is not declared as a path under the " +
                "repository root, so the gitignore check cannot resolve it.")) | Out-Null
            continue
        }

        if ($userStoreRootSegment -eq "config") {
            $failures.Add(("The writable user $($root.Name) store resolves inside " +
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
                "$($root.Name) store root '$userStoreRootSegment/'. " +
                "User-authored configuration must not be tracked.")) | Out-Null
        }

        $trackedUserStore = git ls-files -- $userStoreRootSegment
        if ($trackedUserStore) {
            $failures.Add(("$userStoreRootSegment/ holds tracked files. The " +
                "writable user $($root.Name) store must not be in version control.")) | Out-Null
        }
    }

    # 7. The run store reads with libyaml, at one load point, with no fallback.
    #
    #    T022B, under D-2026-09-29-run-store-libyaml. `CSafeLoader` and the
    #    pure-Python `SafeLoader` accept and refuse different documents, so a
    #    second loader anywhere in the run adapters - a `safe_load`, an
    #    `except ImportError` that picks `SafeLoader`, a branch on
    #    `__with_libyaml__` - would let two installations, or two read paths,
    #    disagree about whether the same bytes are a run. Only the run domain
    #    is held to this: Site, scenario, artifact and stage readers keep their
    #    own loaders by the same decision.
    $runAdapters = "$backendRoot/runs/adapters"
    $runDocuments = "$runAdapters/yaml_run_documents.py"
    $otherLoader = @(
        '\bsafe_load(?:_all)?\s*\(',
        '\b(?:full|unsafe)_load(?:_all)?\s*\(',
        '\bload_all\s*\(',
        'yaml\.(?:Safe|Full|Unsafe|Base)?Loader\b',
        'from\s+yaml\s+import\s+.*\b(?:SafeLoader|FullLoader|UnsafeLoader|BaseLoader|Loader)\b',
        'Loader\s*=\s*(?!CSafeLoader\b)\w',
        'yaml\.load\((?!.*Loader\s*=\s*CSafeLoader\))',
        '__with_libyaml__'
    )
    $cImportSeen = $false
    $cLoadSeen = 0

    foreach ($module in $backendModules) {
        if (-not $module.Path.StartsWith("$runAdapters/")) { continue }

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($module.Path -eq $runDocuments -and $line -match '^\s*from\s+yaml\s+import\s+CSafeLoader\s*$') {
                $cImportSeen = $true
            }
            if ($line -match '=\s*yaml\.load\(.*Loader\s*=\s*CSafeLoader\)') {
                $cLoadSeen++
            }
            foreach ($pattern in $otherLoader) {
                if ($line -notmatch $pattern) { continue }
                $failures.Add(("A second YAML load policy in the run store, " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). Run documents " +
                    "are loaded only by yaml.load(text, Loader=CSafeLoader) in " +
                    "$runDocuments, with no fallback " +
                    "(D-2026-09-29-run-store-libyaml).")) | Out-Null
                break
            }
        }
    }

    if (-not $cImportSeen) {
        $failures.Add(("$runDocuments does not import CSafeLoader from yaml, so the " +
            "run store's libyaml requirement is no longer enforced at import. " +
            "Update the check, do not delete it.")) | Out-Null
    }
    if ($cLoadSeen -ne 1) {
        $failures.Add(("The run adapters hold $cLoadSeen load call(s) of the form " +
            "'= yaml.load(..., Loader=CSafeLoader)'; there must be exactly one, " +
            "the shared load point in $runDocuments.")) | Out-Null
    }

    # 8. S1-01 Foundation-only cutover (D-2026-10-07).
    #
    #    a. The PostgreSQL adapter is the sole writer for imported product
    #       Sites: SQL write statements and database drivers appear in that
    #       one module only (migrations live outside the package).
    #    b. The import report writer writes inside write_import_report only.
    #    c. Routing scan: main.py serves the Sites index through the
    #       tenant-scoped ProductSiteDirectory, and every legacy file-backed
    #       surface (ingestion, Evidence, analytics, Lab) receives the
    #       LegacySiteGate - the raw legacy repository reaches nothing else.
    #    d. Imported-code write refusal: the gate refuses create_site for an
    #       imported code, and each Lab write control calls the import check.
    #
    #    S2-02 adds exactly one more writer, the central evidence ledger
    #    adapter. Each writer is confined to its own tables: the ledger writes
    #    only the ledger tables (migration 0005), and the Foundation store
    #    writes none of them. Every other module stays SQL- and driver-free.
    #
    #    S2-02 phase 2 adds a third, the gateway access store (migration 0006).
    #    It inserts only credential, provisioning-audit and diagnostic rows, and
    #    its only updates are the operator-mutable registration fields listed in
    #    $accessUpdates (credential rotation/revocation and enablement). No other
    #    writer touches its tables.
    #
    #    S3-01 phase 2 adds a fourth, the dispatch assessment store (migration
    #    0007). It inserts only analytic runs, their evidence sets, assessment
    #    revisions and run-to-revision links, plus scheduling rows in the S2
    #    recompute_job table; its only updates are a job's lease/retry status
    #    and the widening of a PENDING job's window. No other writer touches the
    #    assessment tables.
    $pgWriter = "$backendRoot/sites/adapters/postgres_foundation_store.py"
    $ledgerWriter = "$backendRoot/evidence/adapters/postgres_evidence_ledger.py"
    $accessWriter = "$backendRoot/evidence/adapters/postgres_gateway_access.py"
    $ledgerTables = @('ingestion_batch', 'accepted_evidence', 'evidence_rejection',
        'ingestion_disposition', 'batch_refusal', 'recompute_job')
    $accessInserts = @('gateway_credential', 'gateway_access_event', 'gateway_diagnostic',
        'gateway_diagnostic_refusal')
    $accessUpdates = @(
        '(?i)\bUPDATE\s+gateway_credential\s+SET\s+revoked_at\s*=\s*:[a-z_]+\s+WHERE\b',
        '(?i)\bUPDATE\s+gateway\s+SET\s+(?:credential_ref|disabled_at|diagnostic_cadence_seconds)\s*=\s*:[a-z_]+\s+WHERE\b',
        '(?i)\bUPDATE\s+source\s+SET\s+disabled_at\s*=\s*:[a-z_]+\s+WHERE\b')
    $assessWriter = "$backendRoot/analytics/adapters/postgres_assessment_store.py"
    # LR-01 adds source_clock_attestation (migration 0014): INSERT-only events written with their affected-window
    # requeue in one transaction by the assessment store; no other writer touches it and no UPDATE is allowed.
    # W2-03 (D-2026-10-17-w2-02-buildspec, migration 0022) adds the three append-only cold episode tables here, before
    # $assessInserts is derived: the assessment store alone INSERTs them, never UPDATE/DELETE/upsert. The cold
    # worker (analytics/assessment_worker.py) owns the one shared transaction across the assessment and Finding
    # stores and the job completion; it writes no table itself.
    $assessTables = @('analytic_run', 'analytic_run_evidence', 'assessment_revision', 'analytic_run_assessment', 'analytic_run_selection',
        'source_clock_attestation', 'cold_episode', 'cold_episode_revision', 'cold_episode_evidence',
        'ev_session', 'ev_session_revision', 'ev_session_evidence', 'ev_meter_interval')
    $coldEpisodeTables = @('cold_episode', 'cold_episode_revision', 'cold_episode_evidence')
    # W2-06 (D-2026-10-18-w2-06-07-buildspec, migration 0025) adds the four append-only EV session tables the same
    # way: the assessment store alone INSERTs them (never UPDATE/DELETE/upsert); EV Findings stay with the Finding store.
    $evSessionTables = @('ev_session', 'ev_session_revision', 'ev_session_evidence', 'ev_meter_interval')
    $coldTransactionOwner = "$backendRoot/analytics/assessment_worker.py"
    $assessInserts = $assessTables + @('recompute_job')
    # W4-03 closure 4 S2: the one coalescing UPDATE of a PENDING mini_opportunity job, issued only by
    # enqueue_opportunity_job under the study-key advisory lock. Exact text: no other column, domain or status.
    $opportunityCoalesce = ('(?i)^\s*UPDATE\s+recompute_job\s+SET\s+available_at\s*=\s*greatest\(available_at,\s*:at\)' +
        '\s+WHERE\s+id\s*=\s*:pending_id\s+AND\s+domain\s*=\s*''mini_opportunity''\s+AND\s+status\s*=\s*''PENDING''\s*$')
    $opportunityCoalesceSeen = 0
    $assessUpdates = @(
        '(?i)\bUPDATE\s+recompute_job\s+SET\s+status\s*=',
        '(?i)\bUPDATE\s+recompute_job\s+SET\s+window_start\s*=\s*:start,\s*window_end\s*=\s*:end\s+WHERE\b',
        $opportunityCoalesce)
    $findingWriter = "$backendRoot/analytics/adapters/postgres_finding_store.py"
    $findingTables = @('finding', 'finding_revision', 'finding_revision_assessment', 'finding_revision_evidence',
        'finding_merge', 'finding_match_pass')
    # S4-02a adds the sixth writer, the financial assumption store: it inserts its two tables and its only
    # UPDATE closes an assignment's set-once recorded_to. No other module writes either table.
    $assumptionWriter = "$backendRoot/financials/adapters/postgres_assumption_store.py"
    $assumptionTables = @('financial_assumption_revision', 'financial_assumption_assignment')
    $assumptionUpdate = '(?i)\bUPDATE\s+financial_assumption_assignment\s+SET\s+recorded_to\s*=\s*:[a-z_]+\s+WHERE\b'
    # S4-02b adds the seventh writer, the financial consequence store: INSERT-only into the consequence revision,
    # its three link tables and work attempts. Dirty work rows are inserted only by migration triggers (0011:
    # assumption publication and FindingRevision append; 0012, S4-02c: accepted generator-power disposition), so
    # no module may write financial_consequence_work at all.
    $consequenceWriter = "$backendRoot/financials/adapters/postgres_consequence_store.py"
    # W2-04 (D-2026-10-18-w2-04-buildspec, migration 0023): the same store is the sole INSERT-only writer of the
    # three cold consequence tables, registered here before the DML checks. Each of them is also checked as
    # insert-only on its own (no UPDATE/DELETE/TRUNCATE/MERGE/COPY or DO UPDATE from any module). cold_consequence_work
    # is trigger-only like financial_consequence_work: any runtime statement against it fails, and its one migration
    # INSERT must keep the dirty-key DO NOTHING arbiter (checked on the migration text below; rule 8 skips migrations).
    $coldConsequenceTables = @('cold_consequence_revision', 'cold_consequence_evidence', 'cold_consequence_work_attempt')
    $coldConsequenceWork = 'cold_consequence_work'
    $coldConsequenceMigration = 'backend/migrations/versions/0023_w2_cold_consequence.py'
    # W2-07 (D-2026-10-18-w2-06-07-buildspec, migration 0026): the same store is the sole INSERT-only writer of the
    # four EV consequence tables, registered before the DML checks and each insert-only on its own. ev_consequence_work
    # is trigger-only: any runtime statement against it fails, and every INSERT INTO it in 0026 must keep the exact
    # scoped dirty-basis DO NOTHING arbiter (checked on the migration text below).
    $evConsequenceTables = @('ev_consequence_revision', 'ev_consequence_session', 'ev_consequence_evidence',
        'ev_consequence_work_attempt')
    $evConsequenceWork = 'ev_consequence_work'
    $evConsequenceMigration = 'backend/migrations/versions/0026_w2_ev_money.py'
    $consequenceTables = @('financial_consequence_revision', 'financial_consequence_assessment_revision',
        'financial_consequence_assumption_revision', 'financial_consequence_power_interval',
        'financial_consequence_work_attempt') + $coldConsequenceTables + $evConsequenceTables
    # S4-02d adds the eighth writer, the schedule store (D-2026-10-14-s402d-schedule-storage-and-install-gate):
    # the sole runtime writer of the four migration-0013 schedule tables, and it writes no other table. It may
    # INSERT into those tables and UPDATE only the named mutable schedule-state columns below (environment tick
    # claim/lease, start/success/failure, heartbeat, retry due and last counts; Site claim/lease, stage,
    # selected/processed/deferred counts, last failure, retry due and the completed matcher fence/skip state; the
    # fair cursor position; explicit enrolment state). Each of its UPDATEs keeps table, SET list and WHERE on one
    # line so every assigned column is checked; upserts (DO UPDATE), DELETE, TRUNCATE and DDL are refused. No other
    # module writes a schedule table. Migration 0013 owns the DDL; no trigger is ratified. W4-02 q7 ruling 1:
    # migration 0029 replaces the Site stage CHECK (adds MINI) and adds the three mini_* counters, which only the
    # store's token-scoped record_mini assigns. W4-03 migration 0030 adds OPPORTUNITY and the three opportunity_*
    # counters, which only the store's token-scoped record_opportunity assigns.
    $scheduleWriter = "$backendRoot/scheduling/adapters/postgres_schedule_store.py"
    $scheduleTables = @('schedule_tick_head', 'schedule_site_head', 'schedule_cursor', 'schedule_enrolment')
    $scheduleClaim = @('claim_token', 'claim_owner', 'claimed_at', 'lease_until')
    $scheduleUpdates = @{
        'schedule_tick_head' = $scheduleClaim + @('last_started_at', 'last_succeeded_at', 'last_failed_at',
            'last_failure_code', 'last_failure_detail', 'heartbeat_at', 'retry_due_at', 'consecutive_failures',
            'claim_skips', 'last_skipped_at', 'last_sites_selected', 'last_sites_processed', 'last_sites_deferred',
            'last_excluded_with_work', 'last_reconcile_ms')
        'schedule_site_head' = $scheduleClaim + @('stage', 'stage_started_at', 'selected_count', 'last_selected_at',
            'last_completed_at', 's3_processed', 's3_deferred', 'mini_processed', 'mini_deferred', 'mini_failed',
            'opportunity_processed', 'opportunity_deferred', 'opportunity_failed', 'consequence_processed', 'consequence_deferred', 's4_outcome', 's4_outcome_at', 'matched_fence', 'matched_version', 'matched_at', 'fence_moved_streak',
            'last_failure_stage', 'last_failure_code', 'last_failure_detail', 'last_failed_at',
            'consecutive_failures', 'retry_due_at', 'claim_skips', 'last_skipped_at')
        'schedule_cursor' = @('after_tenant_id', 'after_site_id', 'updated_at')
        'schedule_enrolment' = @('enrolled', 'changed_by', 'changed_at')
    }
    # S4-05a (D-2026-10-15-s405-stored-demo-provenance, Architect rule-8 ruling): source provenance extends the
    # existing ledger writer; no new writer. The ledger may only INSERT into the two migration-0017 provenance
    # tables, each statement with its VALUES and no ON CONFLICT (OPS-02 checks the whole extracted statement, so
    # an upsert cannot hide on a continuation line). UPDATE, DELETE, TRUNCATE, upsert and DDL on them are refused here and by the 0017
    # immutability triggers. Anywhere in the ledger, DO UPDATE is refused and ON CONFLICT is allowed only as the
    # three existing DO NOTHING arbiters (batch refusal, external batch slot, accepted message key), which keeps
    # the batch INSERT distinct from an upsert on a binding. No other module writes either table, and no HTTP
    # module (main.py, *_api.py) reaches the designation command.
    $provenanceTables = @('evidence_publication', 'batch_publication_link')
    $ledgerConflictAllowed = "(?i)\bON\s+CONFLICT\s+ON\s+CONSTRAINT\s+(?:batch_refusal_identity|ingestion_batch_external_unique|accepted_evidence_message_unique)\s+DO\s+NOTHING\b"
    $provenanceInsertsSeen = @{ 'evidence_publication' = 0; 'batch_publication_link' = 0 }
    # W2-06 Q12 (migration 0025): `ev_enqueue_configuration`/`ev_enqueue_window` write recompute_job inside the
    # database, so SQL calling them is a recompute_job write. Only the assessment store issues it (through
    # `PostgresAssessmentStore.ev_enqueue_configuration`); other modules call that Python method, never the SQL.
    $evEnqueueSql = '(?i)\b(?:SELECT|PERFORM|CALL)\s+(?:ev_enqueue_[a-z_]+|enqueue_ev_assessment)\s*\('
    $evEnqueueSqlSeen = 0
    # W2-06 q3 P7: the Foundation store's EV publication enqueue is the one other allowed caller, and only of
    # `ev_enqueue_configuration` (SQL function invocation is the guard-compatible allowance; no analytics import).
    $evPublishEnqueueSql = '(?i)\bSELECT\s+ev_enqueue_configuration\s*\('
    $evPublishEnqueueSeen = 0
    # W2-04: per-table owner INSERTs into the cold consequence tables (Q10: each asserted >= 1 below).
    $coldConsequenceInsertsSeen = @{ 'cold_consequence_revision' = 0; 'cold_consequence_evidence' = 0
        'cold_consequence_work_attempt' = 0 }
    # W2-07 (enabled in spec commit 2): per-table owner INSERTs into the EV consequence tables (each asserted >= 1).
    $evConsequenceInsertsSeen = @{ 'ev_consequence_revision' = 0; 'ev_consequence_session' = 0
        'ev_consequence_evidence' = 0; 'ev_consequence_work_attempt' = 0 }
    # W2-00 (D-2026-10-17-w2-00-answers; design section 7): the ledger alone inserts event evidence, rejections and
    # dispositions (recompute_job stays shared with the assessment store). Every INSERT INTO accepted_evidence keeps
    # only the message DO NOTHING arbiter: an event or EV START unique violation is handled by a per-ordinal
    # savepoint and the fixed reread order message, event, session, pinned as one exact `_REREAD_ORDER` line.
    $ledgerOwnedTables = @('ingestion_batch', 'accepted_evidence', 'evidence_rejection', 'ingestion_disposition',
        'batch_refusal')
    $acceptedMessageTarget = '(?i)\bON\s+CONFLICT\s+ON\s+CONSTRAINT\s+accepted_evidence_message_unique\s+DO\s+NOTHING\b'
    $acceptedInsertsSeen = 0
    $rereadOrderExpected = '_REREAD_ORDER = (_REREAD_MESSAGE_SQL, _REREAD_EVENT_SQL, _REREAD_SESSION_SQL)'
    $rereadOrderLines = New-Object System.Collections.Generic.List[string]
    # S6-01a adds the ninth writer, the Action store (D-2026-10-15-s601-action-store-and-ui M1): the sole runtime
    # writer of the migration-0016 Action tables and S6-02a's migration-0019 verification tables, INSERT-only (append-only rows; no UPDATE, DELETE, upsert,
    # TRUNCATE or DDL), and it writes no other table. No other module - explicitly not the Foundation adapter,
    # whose caller-owned-connection publish (phase 2) writes only Foundation and binding rows - writes an Action table.
    $actionWriter = "$backendRoot/actions/adapters/postgres_action_store.py"
    $actionTables = @('action', 'action_basis_assessment', 'action_basis_evidence', 'action_event',
        'action_policy_change', 'action_policy_change_binding', 'verification_plan', 'verification_selection_binding',
        'verification_evaluation_request', 'verification_outcome', 'verification_metric')
    # W4-01 commit 2 (build spec S25, q1 ruling 3) adds the tenth writer, the work store: the sole runtime writer of
    # the eleven migration-0027 work tables, INSERT-only (0027 triggers refuse UPDATE/DELETE; no upsert, TRUNCATE,
    # MERGE, COPY or DDL), and it writes no other table. No other module writes a work table. Each work table must
    # have at least one owner INSERT in the store (per-table anti-vacuity below).
    $workWriter = "$backendRoot/work/adapters/postgres_work_store.py"
    $workTables = @('work_case', 'incident', 'maintenance_work_request', 'work_case_revision', 'work_case_finding_link',
        'work_case_action_link', 'work_case_evidence', 'work_event', 'maintenance_plan', 'maintenance_record',
        'operational_record')
    $workInsertsSeen = @{}
    foreach ($table in $workTables) { $workInsertsSeen[$table] = 0 }
    # W4-02 unit 1 (build spec closure 1 Q25, closure 4 S2) adds the eleventh writer, the mini-depth store: the sole
    # runtime writer of the three migration-0029 tables, INSERT-only (0029 triggers refuse UPDATE/DELETE; no upsert,
    # TRUNCATE, MERGE, COPY or DDL), and it writes no other table. It reads and locks a recompute_job row but never
    # writes one. Each mini table must have at least one owner INSERT in the store (per-table anti-vacuity below).
    $miniWriter = "$backendRoot/mini_depth/store.py"
    $miniTables = @('mini_depth_revision', 'mini_depth_revision_evidence', 'mini_depth_selection')
    $miniInsertsSeen = @{}
    foreach ($table in $miniTables) { $miniInsertsSeen[$table] = 0 }
    # W4-02 q12-6 (final review B-L1): migration 0029 also creates `site_cutover_basis`, the explicit
    # NO_LEGACY_EVIDENCE cutover basis. The Foundation store is its sole writer, INSERT-only (its idempotent
    # ON CONFLICT ... DO NOTHING is not an upsert; no UPDATE, DELETE, DO UPDATE, TRUNCATE, MERGE or COPY from any
    # module), and it must keep at least one owner INSERT (anti-vacuity below).
    $cutoverTable = 'site_cutover_basis'
    $cutoverInsertsSeen = 0
    # W4-03 unit 1 (build spec closure 1 "Rule-8 registers exactly", closure 4 S4): the mini-decision store is the
    # sole runtime writer of the ten migration-0030 tables, INSERT-only (0030 triggers refuse UPDATE/DELETE; no
    # upsert, TRUNCATE, MERGE, COPY or DDL), and it writes no other table (it reads and share-locks a recompute_job
    # row but never writes one). Each table keeps at least one owner INSERT in the store (anti-vacuity below).
    $decisionWriter = "$backendRoot/mini_decisions/store.py"
    $decisionTables = @('mini_scenario', 'mini_scenario_revision', 'mini_alternative_revision',
        'mini_alternative_evidence', 'mini_opportunity', 'mini_opportunity_revision', 'mini_opportunity_evidence',
        'mini_opportunity_selection', 'mini_decision_work_link', 'mini_opportunity_scenario_link')
    $decisionInsertsSeen = @{}
    foreach ($table in $decisionTables) { $decisionInsertsSeen[$table] = 0 }
    # W4-02 closure 2/closure 4 S2: the 0029 enqueue SQL functions write recompute_job inside the database. The
    # Foundation/binding publication store alone calls `mini_enqueue_configuration` (after a successful publish, on
    # its publication connection); `mini_enqueue_hour` and `mini_enqueue_accepted` run only inside the database.
    $miniEnqueueSql = '(?i)\b(?:SELECT|PERFORM|CALL)\s+(?:mini_enqueue_[a-z_]+)\s*\('
    $miniPublishEnqueueSql = '(?i)\bSELECT\s+mini_enqueue_configuration\s*\('
    $miniPublishEnqueueSeen = 0
    $pgWriters = @($pgWriter, $ledgerWriter, $accessWriter, $assessWriter, $findingWriter, $assumptionWriter,
        $consequenceWriter, $scheduleWriter, $actionWriter, $workWriter, $miniWriter, $decisionWriter)
    # W4-01 Run 3 ruling 7: the work read adapter is a named reader (no write; the work store stays the sole writer).
    $pgReaders = @("$backendRoot/estate/adapters/postgres_estate_read.py", "$backendRoot/estate/adapters/postgres_evidence_money_read.py",
        "$backendRoot/work/adapters/postgres_work_read.py",
        # W4-02 unit 5 (closure 1 Q25): the read-only mini-depth reader; the SQL-write refusal still applies to it.
        "$backendRoot/mini_depth/read.py")
    # OPS-02 (S4-02d phase-2 review F-B): the writer policy below applies to SQL statements, not source lines.
    # tools/checks/sql_statements.py parses each backend module with Python's ast and returns every write-shaped
    # clause with its path and line: implicit concatenation, triple-quoted text, escaped newlines and SQL comments
    # are normalised away; `+`, f-string, %/format and join templates keep their dynamic parts as `{?}`; SQLAlchemy
    # Core insert/update/delete calls are synthesised into the equivalent SQL clause. Each clause starts at its write
    # head, so every rule below is anchored at the clause start. The extractor is table-agnostic: a new writer or
    # table is added to the policy tables above, never to the extractor. Proof corpus: tools/writer_guard_probes.py.
    $sqlWrite = '(?i)^(?:INSERT\s+INTO\b|UPDATE\s+\S.*?\bSET\b|DELETE\s+FROM\b|TRUNCATE\b|MERGE\s+INTO\b|COPY\s+[\w."{}?]+\s*(?:\([^)]*\)\s*)?(?:FROM|TO)\b|(?:CREATE|ALTER|DROP)\s+TABLE\b)'
    $sqlTarget = '(?i)^(?:INSERT\s+INTO|UPDATE(?:\s+ONLY)?|DELETE\s+FROM(?:\s+ONLY)?|TRUNCATE(?:\s+TABLE)?(?:\s+ONLY)?|MERGE\s+INTO|COPY)\s+(?:"?[a-z_][a-z0-9_]*"?\.)?"?([a-z_][a-z0-9_]*)"?(?=[\s(;]|$)'
    $sqlDml = '(?i)^(?:INSERT|UPDATE|DELETE|TRUNCATE|MERGE|COPY)\b'
    # A write head with nothing after its target was assembled outside one expression (`sql += ...`).
    $sqlFragment = '^(?:UPDATE \S+|(?:INSERT INTO|DELETE FROM|MERGE INTO)(?: \S+)?)$'
    # The interpreter is found as tools/check-all.ps1 finds it (its -Python override arrives as
    # ASSETOPS_GUARD_PYTHON; default: the repository .venv). A guard that cannot run fails; it never skips.
    $guardPython = $env:ASSETOPS_GUARD_PYTHON
    if (-not $guardPython) {
        foreach ($candidate in @('.venv/Scripts/python.exe', '.venv/bin/python')) {
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { $guardPython = $candidate; break }
        }
    }
    $sqlStatements = @{}
    $extractorRan = $false
    if (-not $guardPython -or -not (Test-Path -LiteralPath $guardPython -PathType Leaf)) {
        $failures.Add(("Rule 8 cannot run its SQL statement extractor: no Python interpreter at '$guardPython' or " +
            ".venv. Create the repository .venv or set ASSETOPS_GUARD_PYTHON; the writer guard never skips.")) | Out-Null
    } else {
        $extractorInput = @($backendModules | Where-Object { $_.Path.StartsWith("$backendRoot/") } |
            ForEach-Object { $_.Path })
        $extractorJson = ($extractorInput -join "`n") | & $guardPython 'tools/checks/sql_statements.py'
        if ($LASTEXITCODE -ne 0) {
            $failures.Add("Rule 8 SQL statement extractor failed (exit $LASTEXITCODE); the writer guard never skips.") | Out-Null
        } else {
            $extractorRan = $true
            # Windows PowerShell's ConvertFrom-Json emits a JSON array as one object; foreach enumerates it.
            $parsedStatements = ($extractorJson -join "`n") | ConvertFrom-Json
            foreach ($statement in $parsedStatements) {
                if (-not $sqlStatements.ContainsKey($statement.path)) { $sqlStatements[$statement.path] = @() }
                $sqlStatements[$statement.path] += $statement
            }
        }
    }
    $dbDriver = '(?:^|\s)(?:import|from)\s+(?:sqlalchemy|psycopg|alembic)(?:[.\s]|$)'
    $pgWritesSeen = @{ $pgWriter = 0; $ledgerWriter = 0; $accessWriter = 0; $assessWriter = 0; $findingWriter = 0
        $assumptionWriter = 0; $consequenceWriter = 0; $scheduleWriter = 0; $actionWriter = 0; $workWriter = 0
        $miniWriter = 0; $decisionWriter = 0 }
    $pgDriverSeen = @{ $pgWriter = $false; $ledgerWriter = $false; $accessWriter = $false; $assessWriter = $false
        $findingWriter = $false; $assumptionWriter = $false; $consequenceWriter = $false; $scheduleWriter = $false
        $actionWriter = $false; $workWriter = $false; $miniWriter = $false; $decisionWriter = $false }
    # S4-05a phase-1 review L1 / fix L1: provenance is insert-only in every module (the ledger included):
    # UPDATE, DELETE FROM or TRUNCATE followed by a provenance table name, schema-qualified or quoted included.
    # The statement loop checks whole clauses; this source-line form is kept as well, so a verb ending one
    # source line with the table name beginning the next is refused wherever it appears, as before OPS-02.
    $provName = '(?:"?[a-z_]+"?\s*\.\s*)?"?(?:evidence_publication|batch_publication_link)"?(?![a-z_])'
    $provVerb = '(?i)\b(?:UPDATE|DELETE\s+FROM|TRUNCATE(?:\s+TABLE)?)(?:\s+ONLY)?'
    $provRefusal = 'Source provenance is insert-only: no UPDATE, DELETE or TRUNCATE in any module (split statements included)'
    # S6-01a: the Action store never mutates or removes a row and runs no DDL. Applied to every source line
    # (SQL-shaped or not) and to every extracted statement clause.
    $actionForbidden = '(?i)\bupdate\s+[a-z_"]+\s+set\b|\bdelete\s+from\b|\btruncate\s+(?:table\s+)?[a-z_"]|\bdo\s+update\b|\bon\s+conflict\b|\bmerge\s+into\b|\b(?:create|alter|drop)\s+(?:table|index|trigger|function|view|sequence)\b|\bgrant\s+\w|\bcopy\s+[a-z_"]+\s+from\b'
    foreach ($module in $backendModules) {
        if (-not $module.Path.StartsWith("$backendRoot/")) { continue }
        $isWriter = $pgWriters -contains $module.Path
        # W3-01 q5 ruling 3: a read-only estate adapter may import the driver; it is never a writer, and the
        # `if (-not $isWriter)` SQL-write refusal below still rejects every extracted write in it.
        $isPgReader = $pgReaders -contains $module.Path
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -match $dbDriver) {
                if ($isWriter) { $pgDriverSeen[$module.Path] = $true }
                elseif (-not $isPgReader) {
                    $failures.Add(("Database driver imported outside $($pgWriters -join ' and ') in " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
            }
            $nextLine = if ($lineNumber -lt $module.Lines.Count) { [string]$module.Lines[$lineNumber] } else { '' }
            if ($line -match "$provVerb\s+$provName" -or
                    ($line -match "$provVerb\s*`$" -and $nextLine -match "(?i)^\s*$provName")) {
                $failures.Add("$provRefusal; $($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
            }
            # Source lines, not extracted clauses: the extractor splits at write heads, and this write is a SELECT.
            if ($line -match $evEnqueueSql) {
                if ($module.Path -eq $assessWriter) { $evEnqueueSqlSeen++ }
                elseif ($module.Path -eq $pgWriter -and $line -match $evPublishEnqueueSql) { $evPublishEnqueueSeen++ }
                else {
                    $failures.Add(("Only $assessWriter calls the 0025 EV enqueue SQL functions (a recompute_job " +
                        "write); call PostgresAssessmentStore.ev_enqueue_configuration instead; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
            }
            if ($module.Path -eq $actionWriter -and $line -match $actionForbidden) {
                $failures.Add("The Action store never updates, deletes, truncates, upserts or runs DDL; " +
                    "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
            }
            if ($module.Path -eq $workWriter -and $line -match $actionForbidden) {
                $failures.Add("The work store never updates, deletes, truncates, upserts or runs DDL; " +
                    "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
            }
            if ($module.Path -eq $miniWriter -and $line -match $actionForbidden) {
                $failures.Add("The mini-depth store never updates, deletes, truncates, upserts or runs DDL; " +
                    "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
            }
            if ($module.Path -eq $decisionWriter -and $line -match $actionForbidden) {
                $failures.Add("The mini-decision store never updates, deletes, truncates, upserts or runs DDL; " +
                    "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
            }
            if ($line -match $miniEnqueueSql) {
                if ($module.Path -eq $pgWriter -and $line -match $miniPublishEnqueueSql) { $miniPublishEnqueueSeen++ }
                else {
                    $failures.Add(("Only $pgWriter calls the 0029 mini enqueue SQL (SELECT mini_enqueue_configuration, " +
                        "a recompute_job write) after a successful publication; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
            }
            if ($module.Path -eq $ledgerWriter -and $line -match '^\s*_REREAD_ORDER\s*=') {
                $rereadOrderLines.Add($line.Trim()) | Out-Null
            }
        }
        $moduleStatements = if ($sqlStatements.ContainsKey($module.Path)) { $sqlStatements[$module.Path] } else { @() }
        foreach ($statement in $moduleStatements) {
            # $line is one SQL clause and $lineNumber the line its Python expression starts on.
            $line = [string]$statement.text
            $lineNumber = [int]$statement.line
            $isDml = $line -match $sqlDml -and $line -match $sqlWrite
            if ($line -match '(?i)^(?:MERGE\s+INTO\b|COPY\s)' -and $line -match $sqlWrite) {
                $failures.Add(("No product writer runs MERGE or COPY; every write is a checked INSERT/UPDATE; " +
                    "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
            }
            if ($isDml -and $line -notmatch $sqlTarget) {
                $failures.Add(("A product write names its target table literally (no format, concatenation or " +
                    "dynamic SQLAlchemy table); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
            }
            if ($line -match $sqlFragment) {
                $failures.Add(("A product write statement ends before its SET, VALUES or WHERE clause (an incomplete statement, " +
                    "or one assembled across expressions); write it as one literal so its table and columns can be checked; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
            }
            if ($line -match $sqlWrite) {
                if (-not $isWriter) {
                    $failures.Add(("A second product database writer in $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). Product rows are written only by $($pgWriters -join ' and ').")) | Out-Null
                    continue
                }
                $pgWritesSeen[$module.Path]++
                $target = if ($line -match $sqlTarget) { $Matches[1].ToLowerInvariant() } else { $null }
                if ($module.Path -eq $ledgerWriter -and ($null -eq $target -or
                        ($ledgerTables -notcontains $target -and $provenanceTables -notcontains $target))) {
                    $failures.Add(("The evidence ledger writes only its own tables ($($ledgerTables -join ', ')) " +
                        "and inserts provenance ($($provenanceTables -join ', ')); " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($null -ne $target -and $provenanceTables -contains $target) {
                    $where = "$($module.Path):${lineNumber}: $($line.Trim())"
                    if ($module.Path -ne $ledgerWriter) {
                        $failures.Add("Only $ledgerWriter writes source provenance table '$target'; $where.") | Out-Null
                    } elseif ($line -notmatch '(?i)\bINSERT\s+INTO\s+(?:evidence_publication|batch_publication_link)\s*\(' -or
                            $line -notmatch '(?i)\bVALUES\s*\(' -or $line -match '(?i)\bON\s+CONFLICT\b') {
                        $failures.Add(("The evidence ledger only INSERTs provenance rows, one literal statement with " +
                            "its VALUES and no ON CONFLICT (no UPDATE, DELETE, TRUNCATE or upsert); $where.")) | Out-Null
                    } else {
                        $provenanceInsertsSeen[$target]++
                    }
                }
                if ($module.Path -eq $accessWriter) {
                    $isInsert = $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)'
                    $insertOk = $isInsert -and $accessInserts -contains $Matches[1].ToLowerInvariant()
                    $updateOk = $false
                    foreach ($allowed in $accessUpdates) { if ($line -match $allowed) { $updateOk = $true } }
                    if (-not ($insertOk -or $updateOk)) {
                        $failures.Add(("The gateway access store inserts only $($accessInserts -join ', ') and " +
                            "updates only credential revocation and gateway/source enablement fields; " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    }
                }
                if ($module.Path -eq $assessWriter) {
                    $isInsert = $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)'
                    $insertOk = $isInsert -and $assessInserts -contains $Matches[1].ToLowerInvariant()
                    $updateOk = $false
                    foreach ($allowed in $assessUpdates) { if ($line -match $allowed) { $updateOk = $true } }
                    if ($line -match $opportunityCoalesce) { $opportunityCoalesceSeen++ }
                    if (-not ($insertOk -or $updateOk)) {
                        $failures.Add(("The assessment store inserts only $($assessInserts -join ', ') and updates " +
                            "only a recompute job's lease/retry status or a PENDING job's window; " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    }
                }
                # LR-01 attestations, S6-01a Action rows and S4-05a provenance are insert-only: a permitted INSERT
                # into one of them must not carry an upsert (ON CONFLICT ... DO UPDATE stays in the INSERT clause).
                if ($null -ne $target -and $line -match '(?i)\bDO\s+UPDATE\b' -and
                        (@('source_clock_attestation', 'finding', 'finding_revision') + $coldEpisodeTables + $evSessionTables +
                            $coldConsequenceTables + $evConsequenceTables + $actionTables + $provenanceTables +
                            $workTables) -contains $target) {
                    $failures.Add(("Insert-only table '$target' is never upserted (no ON CONFLICT DO UPDATE); " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -eq $findingWriter -and -not (
                        $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)' -and $findingTables -contains $Matches[1].ToLowerInvariant())) {
                    $failures.Add(("The Finding store only inserts into $($findingTables -join ', ') (append-only); " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -eq $assumptionWriter -and -not (
                        ($line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)' -and $assumptionTables -contains $Matches[1].ToLowerInvariant()) -or
                        $line -match $assumptionUpdate)) {
                    $failures.Add(("The assumption store only inserts into $($assumptionTables -join ', ') and only " +
                        "sets an assignment's recorded_to; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -eq $consequenceWriter -and -not (
                        $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)' -and $consequenceTables -contains $Matches[1].ToLowerInvariant())) {
                    $failures.Add(("The consequence store only inserts into $($consequenceTables -join ', ') " +
                        "(append-only); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -ne $consequenceWriter -and $null -ne $target -and $consequenceTables -contains $target) {
                    $failures.Add(("Only $consequenceWriter writes consequence table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -eq $actionWriter -and -not (
                        $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)\s*\(' -and $actionTables -contains $Matches[1].ToLowerInvariant())) {
                    $failures.Add(("The Action store only inserts into $($actionTables -join ', ') " +
                        "(append-only); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -ne $actionWriter -and $null -ne $target -and $actionTables -contains $target) {
                    $failures.Add(("Only $actionWriter writes Action table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -eq $workWriter -and -not (
                        $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)\s*\(' -and $workTables -contains $Matches[1].ToLowerInvariant())) {
                    $failures.Add(("The work store only inserts into $($workTables -join ', ') " +
                        "(append-only); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -eq $miniWriter -and -not (
                        $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)\s*\(' -and $miniTables -contains $Matches[1].ToLowerInvariant())) {
                    $failures.Add(("The mini-depth store only inserts into $($miniTables -join ', ') " +
                        "(append-only); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($null -ne $target -and $miniTables -contains $target) {
                    if ($module.Path -ne $miniWriter) {
                        $failures.Add(("Only $miniWriter writes mini-depth table '$target'; " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } elseif ($line -notmatch '(?i)^INSERT\s+INTO\b' -or $line -match '(?i)\bON\s+CONFLICT\b') {
                        $failures.Add(("Mini-depth table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, MERGE, " +
                            "COPY or upsert from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } else {
                        $miniInsertsSeen[$target]++
                    }
                }
                if ($module.Path -eq $decisionWriter -and -not (
                        $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)\s*\(' -and $decisionTables -contains $Matches[1].ToLowerInvariant())) {
                    $failures.Add(("The mini-decision store only inserts into $($decisionTables -join ', ') " +
                        "(append-only); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($null -ne $target -and $decisionTables -contains $target) {
                    if ($module.Path -ne $decisionWriter) {
                        $failures.Add(("Only $decisionWriter writes mini-decision table '$target'; " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } elseif ($line -notmatch '(?i)^INSERT\s+INTO\b' -or $line -match '(?i)\bON\s+CONFLICT\b') {
                        $failures.Add(("Mini-decision table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, " +
                            "MERGE, COPY or upsert from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } else {
                        $decisionInsertsSeen[$target]++
                    }
                }
                if ($null -ne $target -and $target -eq $cutoverTable) {
                    if ($module.Path -ne $pgWriter) {
                        $failures.Add(("Only $pgWriter writes cutover basis table '$target'; " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } elseif ($line -notmatch '(?i)^INSERT\s+INTO\b' -or $line -match '(?i)\bDO\s+UPDATE\b') {
                        $failures.Add(("Cutover basis table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, " +
                            "MERGE, COPY or upsert from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } else {
                        $cutoverInsertsSeen++
                    }
                }
                if ($null -ne $target -and $workTables -contains $target) {
                    if ($module.Path -ne $workWriter) {
                        $failures.Add(("Only $workWriter writes work table '$target'; " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } elseif ($line -notmatch '(?i)^INSERT\s+INTO\b') {
                        $failures.Add(("Work table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, MERGE or " +
                            "COPY from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } else {
                        $workInsertsSeen[$target]++
                    }
                }
                if ($module.Path -ne $scheduleWriter -and $null -ne $target -and $scheduleTables -contains $target) {
                    $failures.Add(("Only $scheduleWriter writes schedule table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($null -ne $target -and $coldConsequenceTables -contains $target) {
                    if ($line -notmatch '(?i)^INSERT\s+INTO\b') {
                        $failures.Add(("Cold consequence table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, " +
                            "MERGE or COPY from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } elseif ($module.Path -eq $consequenceWriter) {
                        $coldConsequenceInsertsSeen[$target]++
                    }
                }
                if ($null -ne $target -and $evConsequenceTables -contains $target) {
                    if ($line -notmatch '(?i)^INSERT\s+INTO\b') {
                        $failures.Add(("EV consequence table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, " +
                            "MERGE or COPY from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } elseif ($module.Path -eq $consequenceWriter) {
                        $evConsequenceInsertsSeen[$target]++
                    }
                }
                if ($target -eq $evConsequenceWork) {
                    $failures.Add(("EV consequence work is written only by the migration 0026 triggers (no runtime " +
                        "INSERT, UPDATE, DELETE, TRUNCATE, MERGE or COPY); $($module.Path):${lineNumber}: " +
                        "$($line.Trim()).")) | Out-Null
                }
                if ($target -eq $coldConsequenceWork) {
                    $failures.Add(("Cold consequence work is written only by the migration 0023 triggers (no runtime " +
                        "INSERT, UPDATE, DELETE, TRUNCATE, MERGE or COPY); $($module.Path):${lineNumber}: " +
                        "$($line.Trim()).")) | Out-Null
                }
                if ($target -eq 'financial_consequence_work') {
                    $failures.Add(("Dirty consequence work is inserted only by the migration 0011/0012 triggers; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -ne $assumptionWriter -and $null -ne $target -and $assumptionTables -contains $target) {
                    $failures.Add(("Only $assumptionWriter writes assumption table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -ne $findingWriter -and $null -ne $target -and $findingTables -contains $target) {
                    $failures.Add(("Only $findingWriter writes Finding table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -ne $assessWriter -and $null -ne $target -and $assessTables -contains $target) {
                    $failures.Add(("Only $assessWriter writes assessment table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -ne $accessWriter -and $null -ne $target -and $accessInserts -contains $target) {
                    $failures.Add(("Only $accessWriter writes gateway access table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -ne $ledgerWriter -and $null -ne $target -and $ledgerOwnedTables -contains $target) {
                    $failures.Add(("Only $ledgerWriter writes ledger table '$target' (event evidence, rejections and " +
                        "dispositions included); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
                if ($module.Path -eq $ledgerWriter -and $target -eq 'accepted_evidence' -and $line -match '(?i)^INSERT\b') {
                    if ($line -notmatch $acceptedMessageTarget) {
                        $failures.Add(("Every INSERT INTO accepted_evidence keeps the accepted_evidence_message_unique " +
                            "DO NOTHING arbiter; event and session collisions use a savepoint and the ordered reread; " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    } else {
                        $acceptedInsertsSeen++
                    }
                }
                if ($module.Path -eq $pgWriter -and $null -ne $target -and $ledgerTables -contains $target) {
                    $failures.Add(("The Foundation store must not write ledger table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
            }
            if ($module.Path -eq $ledgerWriter) {
                $where = "$($module.Path):${lineNumber}: $($line.Trim())"
                if ($line -match '(?i)\bdo\s+update\b' -or
                        ($line -match '(?i)\bon\s+conflict\b' -and $line -notmatch $ledgerConflictAllowed)) {
                    $failures.Add(("The evidence ledger never upserts; ON CONFLICT is allowed only as its three " +
                        "existing DO NOTHING arbiters; $where.")) | Out-Null
                }
                if ($line -match '(?i)\b(?:create|alter|drop)\s+(?:table|index|trigger|function|view)\b|\btruncate\s+(?:table\s+)?[a-z_"]') {
                    $failures.Add("The evidence ledger runs no DDL or TRUNCATE (migrations own DDL); $where.") | Out-Null
                }
            }
            if ($module.Path -ne $ledgerWriter -and $line -match '(?i)\b(?:evidence_publication|batch_publication_link)\b' -and
                    $line -match $sqlWrite) {
                $failures.Add(("Only $ledgerWriter writes source provenance; " +
                    "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
            }
            # The extractor joins split, concatenated and multi-line statements, so the whole clause is checked here
            # (the source-line form of these two rules runs in the driver loop above).
            if ($line -match "$provVerb\s+$provName") {
                $failures.Add("$provRefusal; $($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
            }
            if ($module.Path -eq $workWriter) {
                if ($line -match $actionForbidden) {
                    $failures.Add("The work store never updates, deletes, truncates, upserts or runs DDL; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
                }
                if ($line -match '(?i)\binsert\s+into\s+([a-z_]+)' -and $workTables -notcontains $Matches[1].ToLowerInvariant()) {
                    $failures.Add("The work store only inserts into $($workTables -join ', '); " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
                }
            }
            if ($module.Path -eq $actionWriter) {
                if ($line -match $actionForbidden) {
                    $failures.Add("The Action store never updates, deletes, truncates, upserts or runs DDL; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
                }
                if ($line -match '(?i)\binsert\s+into\s+([a-z_]+)' -and $actionTables -notcontains $Matches[1].ToLowerInvariant()) {
                    $failures.Add("The Action store only inserts into $($actionTables -join ', '); " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
                }
            }
            if ($module.Path -eq $scheduleWriter) {
                # Case-insensitive (phase-1 review F1): lowercase SQL is an ordinary way to write a statement, so
                # every keyword rule here uses (?i); prose is excluded because each rule needs SQL shape.
                $where = "$($module.Path):${lineNumber}: $($line.Trim())"
                if ($line -cmatch '\b(?:DELETE|TRUNCATE|CREATE|ALTER|DROP|GRANT|COPY|MERGE)\b' -or
                        $line -match '(?i)\bdelete\s+from\b|\btruncate\s+(?:table\s+)?[a-z_"]|\bdo\s+update\b|\b(?:create|alter|drop)\s+(?:table|index|trigger|function|view)\b|^merge\s+into\b|^copy\s|\bthen\s+(?:update|delete)\b') {
                    $failures.Add("The schedule store never deletes, truncates, upserts or runs DDL (nor merges or copies); $where.") | Out-Null
                }
                if ($line -match '(?i)\binsert\s+into\b' -and -not (
                        $line -match '(?i)\binsert\s+into\s+([a-z_]+)\s*\(' -and
                        $scheduleTables -contains $Matches[1].ToLowerInvariant())) {
                    $failures.Add(("The schedule store only inserts into $($scheduleTables -join ', '); $where.")) | Out-Null
                }
                if ($line -match '(?i)^update\s+\S+.*\bset\b') {
                    $updTarget = if ($line -match $sqlTarget) { $Matches[1].ToLowerInvariant() } else { $null }
                    if ($null -ne $updTarget -and -not $scheduleUpdates.ContainsKey($updTarget)) {
                        $failures.Add("The schedule store updates only $($scheduleTables -join ', '); $where.") | Out-Null
                    } elseif ($line -match '(?i)^UPDATE\s+([a-z_]+)(?:\s+(?:AS\s+)?(?!SET\b)[a-z_]+)?\s+SET\s+(.+?)\s+WHERE\b') {
                        # An optional table alias is allowed; SET columns are never alias-qualified in PostgreSQL.
                        $updTable = $Matches[1].ToLowerInvariant()
                        $setList = $Matches[2]
                        if (-not $scheduleUpdates.ContainsKey($updTable)) {
                            $failures.Add("The schedule store updates only $($scheduleTables -join ', '); $where.") | Out-Null
                        } elseif ($setList -match '[{}"%`]' -or $setList -match '^\s*\(' -or
                                ($setList.Split('(').Count -ne $setList.Split(')').Count)) {
                            # Braces/format, double quotes (concatenation or quoted identifiers), %-formatting, a
                            # tuple target or unbalanced parentheses (a nested WHERE cut the list short).
                            $failures.Add("A schedule UPDATE names its SET columns literally; $where.") | Out-Null
                        } else {
                            # Split on top-level commas; each item must be `identifier = expression`.
                            $items = New-Object System.Collections.Generic.List[string]
                            $depth = 0; $current = ''
                            foreach ($ch in $setList.ToCharArray()) {
                                if ($ch -eq '(') { $depth++ } elseif ($ch -eq ')') { $depth-- }
                                if ($ch -eq ',' -and $depth -eq 0) { $items.Add($current); $current = '' }
                                else { $current += $ch }
                            }
                            $items.Add($current)
                            foreach ($item in $items) {
                                if ($item -notmatch '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(?![=>])\s*\S') {
                                    $failures.Add("A schedule UPDATE names its SET columns literally; $where.") | Out-Null
                                    continue
                                }
                                $column = $Matches[1]
                                if ($scheduleUpdates[$updTable] -cnotcontains $column) {
                                    $failures.Add(("The schedule store may not update $updTable.$column (not a " +
                                        "named schedule-state column); $where.")) | Out-Null
                                }
                            }
                        }
                    } else {
                        $failures.Add(("Every schedule UPDATE names its table, SET list and WHERE literally in one " +
                            "statement so the guard can check each column; $where.")) | Out-Null
                    }
                }
            }
        }
    }
    foreach ($writer in $pgWriters) {
        if ($extractorRan -and ($pgWritesSeen[$writer] -eq 0 -or -not $pgDriverSeen[$writer])) {
            $failures.Add(("The product database writer check found no SQL write or driver import in " +
                "$writer, so it is no longer proving anything. Update the check, do not delete it.")) | Out-Null
        }
    }

    if ($extractorRan -and $acceptedInsertsSeen -lt 1) {
        $failures.Add(("Rule 8 found no INSERT INTO accepted_evidence with the message DO NOTHING arbiter in " +
            "$ledgerWriter, so the accepted-evidence conflict-target check is vacuous. Update the check.")) | Out-Null
    }
    if ($rereadOrderLines.Count -ne 1 -or $rereadOrderLines[0] -cne $rereadOrderExpected) {
        $failures.Add(("The evidence ledger rereads collisions in the fixed order message, event, session: exactly one " +
            "line '$rereadOrderExpected' in $ledgerWriter (found $($rereadOrderLines.Count): " +
            "$($rereadOrderLines -join ' | ')).")) | Out-Null
    }
    if ($miniPublishEnqueueSeen -lt 1) {
        $failures.Add(("Rule 8 found no mini_enqueue_configuration call in $pgWriter (W4-02 publication enqueue), so " +
            "its allowance is vacuous. Update the check, do not delete it.")) | Out-Null
    }
    if ($extractorRan -and $cutoverInsertsSeen -lt 1) {
        $failures.Add(("Rule 8 found no INSERT INTO $cutoverTable in $pgWriter, so the cutover basis insert-only " +
            "check is vacuous. Update the check, do not delete it.")) | Out-Null
    }
    foreach ($table in $miniTables) {
        if ($extractorRan -and $miniInsertsSeen[$table] -lt 1) {
            $failures.Add(("Rule 8 found no INSERT INTO $table in $miniWriter, so the mini-depth insert-only check " +
                "is vacuous. Update the check, do not delete it.")) | Out-Null
        }
    }
    foreach ($table in $decisionTables) {
        if ($extractorRan -and $decisionInsertsSeen[$table] -lt 1) {
            $failures.Add(("Rule 8 found no INSERT INTO $table in $decisionWriter, so the mini-decision insert-only " +
                "check is vacuous. Update the check, do not delete it.")) | Out-Null
        }
    }
    if ($evPublishEnqueueSeen -lt 1) {
        $failures.Add(("Rule 8 found no ev_enqueue_configuration call in $pgWriter (W2-06 q3 P7 publication " +
            "enqueue), so its allowance is vacuous. Update the check, do not delete it.")) | Out-Null
    }
    if ($opportunityCoalesceSeen -lt 1) {
        $failures.Add(("Rule 8 found no opportunity coalescing UPDATE in $assessWriter (W4-03 closure 4 S2), so its " +
            "allowance is vacuous. Update the check, do not delete it.")) | Out-Null
    }
    if ($evEnqueueSqlSeen -lt 1) {
        $failures.Add(("Rule 8 found no EV enqueue SQL call in $assessWriter, so the sole-caller check is " +
            "vacuous. Update the check, do not delete it.")) | Out-Null
    }
    foreach ($table in $provenanceTables) {
        if ($provenanceInsertsSeen[$table] -lt 1) {
            $failures.Add(("Rule 8 found no ledger INSERT statement into $table in $ledgerWriter, so the " +
                "provenance writer check is vacuous. Update the check, do not delete it.")) | Out-Null
        }
    }
    # W2-04 Q10 (enabled in spec commit 2): the consequence store must really INSERT into each cold consequence
    # table, so the per-table insert-only and sole-owner checks above cannot pass on an empty set.
    foreach ($table in $coldConsequenceTables) {
        if ($coldConsequenceInsertsSeen[$table] -lt 1) {
            $failures.Add(("Rule 8 found no INSERT INTO $table in $consequenceWriter, so the cold consequence " +
                "insert-only check is vacuous. Update the check, do not delete it.")) | Out-Null
        }
    }
    # W4-01 commit 2: the work store must really INSERT into each work table, so the per-table insert-only and
    # sole-owner checks above cannot pass on an empty set.
    foreach ($table in $workTables) {
        if ($extractorRan -and $workInsertsSeen[$table] -lt 1) {
            $failures.Add(("Rule 8 found no INSERT INTO $table in $workWriter, so the work table insert-only check " +
                "is vacuous. Update the check, do not delete it.")) | Out-Null
        }
    }
    # W2-07 (enabled in spec commit 2): the consequence store must really INSERT into each EV consequence table, so
    # the per-table insert-only and sole-owner checks above cannot pass on an empty set.
    foreach ($table in $evConsequenceTables) {
        if ($evConsequenceInsertsSeen[$table] -lt 1) {
            $failures.Add(("Rule 8 found no INSERT INTO $table in $consequenceWriter, so the EV consequence " +
                "insert-only check is vacuous. Update the check, do not delete it.")) | Out-Null
        }
    }
    # W2-03: the cold writer policy fails closed. Each declared owner module must exist, and the rule-8 mutation
    # corpus must keep its pass probe and its foreign-INSERT, UPDATE, DELETE and DO UPDATE fail probes for every cold
    # episode table and for the cold Finding tables, so a removed owner or probe cannot leave the policy unproven.
    foreach ($owner in @($assessWriter, $findingWriter, $coldTransactionOwner)) {
        if (-not (Test-Path -LiteralPath $owner -PathType Leaf)) {
            $failures.Add("Rule 8 declares cold writer owner '$owner', which does not exist; update the check.") | Out-Null
        }
    }
    $probeCorpus = 'tools/writer_guard_probes.py'
    $probeText = if (Test-Path -LiteralPath $probeCorpus -PathType Leaf) { Get-Content -LiteralPath $probeCorpus -Raw } else { '' }
    foreach ($table in ($coldEpisodeTables + @('finding', 'finding_revision'))) {
        foreach ($probeName in @("controls cold $table insert", "cold $table foreign insert", "cold $table update",
                "cold $table delete", "cold $table upsert")) {
            if ($probeText -notmatch [regex]::Escape("(""$probeName""")) {
                $failures.Add(("Rule 8 cold writer probe '$probeName' is missing from tools/writer_guard_probes.py; " +
                    "the cold writer policy is unproven without it.")) | Out-Null
            }
        }
    }
    # W2-06: the EV session tables fail closed the same way, with their own `ev` probe names.
    foreach ($table in $evSessionTables) {
        foreach ($probeName in @("controls ev $table insert", "ev $table foreign insert", "ev $table update",
                "ev $table delete", "ev $table upsert")) {
            if ($probeText -notmatch [regex]::Escape("(""$probeName""")) {
                $failures.Add(("Rule 8 EV writer probe '$probeName' is missing from tools/writer_guard_probes.py; " +
                    "the EV session writer policy is unproven without it.")) | Out-Null
            }
        }
    }
    # W2-04: the cold consequence policy fails closed the same way: its owner and migration must exist, and the
    # rule-8 corpus must keep the owner-INSERT controls and the foreign-INSERT, UPDATE, DELETE and DO UPDATE probes
    # per cold consequence table, the runtime work probes and the migration arbiter probes (Q9/Q10).
    foreach ($owner in @($consequenceWriter, $coldConsequenceMigration)) {
        if (-not (Test-Path -LiteralPath $owner -PathType Leaf)) {
            $failures.Add("Rule 8 declares cold consequence owner '$owner', which does not exist; update the check.") | Out-Null
        }
    }
    $coldProbeNames = @()
    foreach ($table in $coldConsequenceTables) {
        $coldProbeNames += @("controls cold $table insert", "cold $table foreign insert", "cold $table update",
            "cold $table delete", "cold $table upsert")
    }
    foreach ($verb in @('insert', 'update', 'delete', 'truncate', 'merge', 'copy')) {
        $coldProbeNames += "cold $coldConsequenceWork runtime $verb"
    }
    $coldProbeNames += @('controls cold work migration trigger insert', 'cold work migration do update',
        'cold work migration other arbiter', 'cold work migration no arbiter', 'cold work migration no insert',
        'cold work migration second insert without arbiter')
    foreach ($probeName in $coldProbeNames) {
        if ($probeText -notmatch [regex]::Escape("(""$probeName""")) {
            $failures.Add(("Rule 8 cold consequence probe '$probeName' is missing from tools/writer_guard_probes.py; " +
                "the cold consequence writer policy is unproven without it.")) | Out-Null
        }
    }
    # Q9: rule 8 scans runtime modules only, so the one migration that may insert cold_consequence_work is read on
    # its own. Comments and the module docstring are removed first; then there must be at least one
    # INSERT INTO cold_consequence_work, each such statement (to its ';') must carry exactly one ON CONFLICT, the
    # dirty-key DO NOTHING arbiter, and the file has no DO UPDATE at all.
    if (Test-Path -LiteralPath $coldConsequenceMigration -PathType Leaf) {
        $migrationText = (Get-Content -LiteralPath $coldConsequenceMigration -Raw) -replace "`r`n", "`n"
        $migrationText = [regex]::Replace($migrationText, '^\s*(?:\x22\x22\x22[\s\S]*?\x22\x22\x22|\x27\x27\x27[\s\S]*?\x27\x27\x27)', '')
        $migrationText = [regex]::Replace($migrationText, '--[^\n]*', '')
        $migrationText = [regex]::Replace($migrationText, '(?m)^\s*#[^\n]*', '')
        $workInserts = [regex]::Matches($migrationText, '(?i)\bINSERT\s+INTO\s+"?cold_consequence_work"?(?![a-z0-9_])')
        if ($workInserts.Count -lt 1) {
            $failures.Add(("Rule 8 found no INSERT INTO $coldConsequenceWork in $coldConsequenceMigration, so the " +
                "trigger-only dirty-work arbiter check is vacuous. Update the check, do not delete it.")) | Out-Null
        }
        foreach ($insert in $workInserts) {
            $end = $migrationText.IndexOf(';', $insert.Index)
            $statement = if ($end -lt 0) { $migrationText.Substring($insert.Index) } else {
                $migrationText.Substring($insert.Index, $end - $insert.Index + 1) }
            $conflicts = [regex]::Matches($statement, '(?i)\bON\s+CONFLICT\b').Count
            $arbiter = '(?i)\bON\s+CONFLICT\s*\(\s*tenant_id\s*,\s*site_id\s*,\s*dirty_key_sha256\s*\)\s*DO\s+NOTHING\s*;?\s*$'
            if ($conflicts -ne 1 -or $statement -notmatch $arbiter) {
                $failures.Add(("Every INSERT INTO $coldConsequenceWork in $coldConsequenceMigration keeps exactly the " +
                    "ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO NOTHING arbiter; found: " +
                    "$(($statement -replace '\s+', ' ').Trim())")) | Out-Null
            }
        }
        if ($migrationText -match '(?i)\bDO\s+UPDATE\b') {
            $failures.Add(("$coldConsequenceMigration runs no ON CONFLICT DO UPDATE: cold consequence work and " +
                "history are append-only.")) | Out-Null
        }
    }
    # W2-07: the EV consequence policy fails closed the same way: its 0026 migration must exist, and the rule-8
    # corpus must keep the owner-INSERT controls and the foreign-INSERT, UPDATE, DELETE and DO UPDATE probes per EV
    # consequence table, the runtime work probes and the migration arbiter probes.
    if (-not (Test-Path -LiteralPath $evConsequenceMigration -PathType Leaf)) {
        $failures.Add("Rule 8 declares EV consequence migration '$evConsequenceMigration', which does not exist; update the check.") | Out-Null
    }
    $evProbeNames = @()
    foreach ($table in $evConsequenceTables) {
        $evProbeNames += @("controls ev $table insert", "ev $table foreign insert", "ev $table update",
            "ev $table delete", "ev $table upsert", "ev $table owner insert unseen")
    }
    foreach ($verb in @('insert', 'update', 'delete', 'truncate', 'merge', 'copy')) {
        $evProbeNames += "ev $evConsequenceWork runtime $verb"
    }
    $evProbeNames += @('controls ev work migration trigger insert', 'ev work migration do update',
        'ev work migration other arbiter', 'ev work migration unscoped arbiter', 'ev work migration no arbiter',
        'ev work migration no insert', 'ev work migration second insert without arbiter')
    foreach ($probeName in $evProbeNames) {
        if ($probeText -notmatch [regex]::Escape("(""$probeName""")) {
            $failures.Add(("Rule 8 EV consequence probe '$probeName' is missing from tools/writer_guard_probes.py; " +
                "the EV consequence writer policy is unproven without it.")) | Out-Null
        }
    }
    # W4-01 commit 2: the work writer policy fails closed the same way: the rule-8 corpus keeps the owner-INSERT
    # control, the foreign-INSERT, UPDATE, DELETE, DO UPDATE and owner-insert-unseen probes per work table, and the
    # store-level TRUNCATE, MERGE and COPY probes.
    $workProbeNames = @('work truncate', 'work merge', 'work copy')
    foreach ($table in $workTables) {
        $workProbeNames += @("controls work $table insert", "work $table foreign insert", "work $table update",
            "work $table delete", "work $table upsert", "work $table owner insert unseen")
    }
    # W4-02 unit 1: the mini-depth writer policy fails closed the same way.
    foreach ($table in $miniTables) {
        $workProbeNames += @("controls mini $table insert", "mini $table foreign insert", "mini $table update",
            "mini $table delete", "mini $table upsert", "mini $table owner insert unseen")
    }
    $workProbeNames += @('mini truncate', 'mini enqueue foreign call', 'mini enqueue hour from publication')
    # W4-03 unit 1: the mini-decision writer policy fails closed the same way, with a denied-writer probe per table.
    foreach ($table in $decisionTables) {
        $workProbeNames += @("controls decision $table insert", "decision $table foreign insert",
            "decision $table update", "decision $table delete", "decision $table upsert",
            "decision $table owner insert unseen")
    }
    $workProbeNames += @('decision truncate')
    # W4-02 B-L1: the q12-6 cutover basis writer policy fails closed the same way.
    $workProbeNames += @("controls cutover $cutoverTable insert", "cutover $cutoverTable foreign insert",
        "cutover $cutoverTable update", "cutover $cutoverTable delete", "cutover $cutoverTable upsert",
        "cutover $cutoverTable truncate", "cutover $cutoverTable owner insert unseen")
    foreach ($probeName in $workProbeNames) {
        if ($probeText -notmatch [regex]::Escape("(""$probeName""")) {
            $failures.Add(("Rule 8 work probe '$probeName' is missing from tools/writer_guard_probes.py; " +
                "the work writer policy is unproven without it.")) | Out-Null
        }
    }
    # Rule 8 scans runtime modules only, so 0026 is read on its own: comments and the module docstring are removed,
    # then there must be at least one INSERT INTO ev_consequence_work; each such statement (to its ';') carries exactly
    # one ON CONFLICT, the scoped (tenant_id, site_id, window_start, window_end, dirty_basis_sha256) DO NOTHING arbiter
    # that matches the declared unique constraint, and the file has no DO UPDATE at all.
    if (Test-Path -LiteralPath $evConsequenceMigration -PathType Leaf) {
        $migrationText = (Get-Content -LiteralPath $evConsequenceMigration -Raw) -replace "`r`n", "`n"
        $migrationText = [regex]::Replace($migrationText, '^\s*(?:\x22\x22\x22[\s\S]*?\x22\x22\x22|\x27\x27\x27[\s\S]*?\x27\x27\x27)', '')
        $migrationText = [regex]::Replace($migrationText, '--[^\n]*', '')
        $migrationText = [regex]::Replace($migrationText, '(?m)^\s*#[^\n]*', '')
        $workInserts = [regex]::Matches($migrationText, '(?i)\bINSERT\s+INTO\s+"?ev_consequence_work"?(?![a-z0-9_])')
        if ($workInserts.Count -lt 1) {
            $failures.Add(("Rule 8 found no INSERT INTO $evConsequenceWork in $evConsequenceMigration, so the " +
                "trigger-only EV dirty-work arbiter check is vacuous. Update the check, do not delete it.")) | Out-Null
        }
        foreach ($insert in $workInserts) {
            $end = $migrationText.IndexOf(';', $insert.Index)
            $statement = if ($end -lt 0) { $migrationText.Substring($insert.Index) } else {
                $migrationText.Substring($insert.Index, $end - $insert.Index + 1) }
            $conflicts = [regex]::Matches($statement, '(?i)\bON\s+CONFLICT\b').Count
            $arbiter = '(?i)\bON\s+CONFLICT\s*\(\s*tenant_id\s*,\s*site_id\s*,\s*window_start\s*,\s*window_end\s*,\s*dirty_basis_sha256\s*\)\s*DO\s+NOTHING\s*;?\s*$'
            if ($conflicts -ne 1 -or $statement -notmatch $arbiter) {
                $failures.Add(("Every INSERT INTO $evConsequenceWork in $evConsequenceMigration keeps exactly the " +
                    "ON CONFLICT (tenant_id, site_id, window_start, window_end, dirty_basis_sha256) DO NOTHING " +
                    "arbiter; found: $(($statement -replace '\s+', ' ').Trim())")) | Out-Null
            }
        }
        if ($migrationText -match '(?i)\bDO\s+UPDATE\b') {
            $failures.Add(("$evConsequenceMigration runs no ON CONFLICT DO UPDATE: EV consequence work and " +
                "history are append-only.")) | Out-Null
        }
    }
    # S4-05a: designation is a server-side command only. No HTTP module may reach it or its tables.
    $routeModules = @($backendModules | Where-Object {
        $_.Path -eq "$backendRoot/main.py" -or $_.Path -match '_api\.py$' })
    if ($routeModules.Count -lt 2) {
        $failures.Add("Rule 8 scanned $($routeModules.Count) HTTP module(s) for designation routes; update the check.") | Out-Null
    }
    $designation = '(?i)\b(?:register_publication|register_authored|register_run|authored_record|simulation_records|publish_source|evidence_publication|batch_publication_link|run_attestation)\b|evidence\.publication\b|runs\.source_publication\b'
    foreach ($module in $routeModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -match $designation) {
                $failures.Add(("A client route reaches source designation in $($module.Path):${lineNumber}: " +
                    "$($line.Trim()). Publication is a server-side SYSTEM command only.")) | Out-Null
            }
        }
    }

    $reportWriter = "$backendRoot/sites/adapters/import_files.py"
    $reportModule = $backendModules | Where-Object { $_.Path -eq $reportWriter } | Select-Object -First 1
    if ($null -eq $reportModule) {
        $failures.Add("Rule 8 could not find $reportWriter; update the check, do not delete it.") | Out-Null
    } else {
        $currentFunction = $null
        $lineNumber = 0
        foreach ($line in $reportModule.Lines) {
            $lineNumber++
            if ($line -match '^def\s+([A-Za-z_]+)') { $currentFunction = $Matches[1] }
            foreach ($pattern in $writeCall) {
                if ($line -match $pattern -and $currentFunction -ne 'write_import_report') {
                    $failures.Add(("$reportWriter writes outside write_import_report at line ${lineNumber}: " +
                        "$($line.Trim()). It may write only the review report, never a Site document.")) | Out-Null
                }
            }
        }
    }

    $mainPath = "$backendRoot/main.py"
    $mainModule = $backendModules | Where-Object { $_.Path -eq $mainPath } | Select-Object -First 1
    $routingRequired = [ordered]@{
        'product read router built'     = '^\s*product_sites\s*=\s*ProductSiteDirectory\('
        'Sites index served through it' = 'build_sites_router\(product_sites\)'
        'legacy gate built'             = '^\s*repository\s*=\s*LegacySiteGate\(legacy_repository,'
        'Lab write controls gated'      = 'imported_site_check\s*=\s*repository\.refuse_if_imported'
    }
    $legacyAllowed = @(
        '^\s*legacy_repository\s*=',
        '^\s*legacy_repository,\s*$',
        'LegacySiteGate\(legacy_repository,\s*registry\)',
        'build_foundation_router\(registry,\s*legacy_repository\)'
    )
    if ($null -eq $mainModule) {
        $failures.Add("Rule 8 could not find $mainPath; the routing scan would be vacuous.") | Out-Null
    } else {
        foreach ($name in $routingRequired.Keys) {
            if (-not ($mainModule.Lines | Where-Object { $_ -match $routingRequired[$name] })) {
                $failures.Add(("Routing scan: $mainPath no longer shows '$name' " +
                    "($($routingRequired[$name])). Imported Sites must be read through the " +
                    "product router and refused on legacy surfaces.")) | Out-Null
            }
        }
        $legacyLines = 0
        $lineNumber = 0
        foreach ($line in $mainModule.Lines) {
            $lineNumber++
            if ($line -notmatch '\blegacy_repository\b') { continue }
            $legacyLines++
            $allowed = $false
            foreach ($pattern in $legacyAllowed) { if ($line -match $pattern) { $allowed = $true; break } }
            if (-not $allowed) {
                $failures.Add(("Routing scan: the raw legacy Site repository reaches another consumer in " +
                    "${mainPath}:${lineNumber}: $($line.Trim()). Legacy surfaces take the LegacySiteGate.")) | Out-Null
            }
        }
        if ($legacyLines -lt 3) {
            $failures.Add("Routing scan matched only $legacyLines legacy_repository line(s) in $mainPath; update the check.") | Out-Null
        }
    }

    $cutoverPath = "$backendRoot/sites/cutover.py"
    $cutover = $backendModules | Where-Object { $_.Path -eq $cutoverPath } | Select-Object -First 1
    $labPath = "$backendRoot/simulator_lab_api.py"
    $lab = $backendModules | Where-Object { $_.Path -eq $labPath } | Select-Object -First 1
    if ($null -eq $cutover -or $null -eq $lab) {
        $failures.Add("Rule 8 could not find $cutoverPath or $labPath; update the check.") | Out-Null
    } else {
        $text = $cutover.Lines -join "`n"
        if ($text -notmatch '(?s)def create_site\(self[^\n]*\n(?:(?!\n    def ).)*?self\.is_imported\(') {
            $failures.Add("$cutoverPath LegacySiteGate.create_site no longer refuses an imported code.") | Out-Null
        }
        $labText = $lab.Lines -join "`n"
        # S2-01a: every Lab write still passes the one shared boundary. Start,
        # step and run-to-end call it plainly (a registered Draft runs from its
        # frozen basis; a pre-import YAML Draft of an imported code refuses).
        # Commit must call it with commit=True, and the boundary must refuse
        # Commit for a pre-import YAML Draft; a registered run releases (below).
        $guarded = @{
            'RUN_EXECUTION_START_ROUTE' = '_refuse_if_imported\(record\)'
            'RUN_EXECUTION_STEP_ROUTE' = '_refuse_if_imported\(record\)'
            'RUN_EXECUTION_END_ROUTE' = '_refuse_if_imported\(record\)'
            'RUN_COMMIT_ROUTE' = '_refuse_if_imported\(record, commit=True\)'
        }
        foreach ($route in $guarded.Keys) {
            $pattern = '(?s)@router\.post\(' + $route + '\)\n(?:(?!@router\.).)*?' + $guarded[$route]
            if ($labText -notmatch $pattern) {
                $failures.Add(("$labPath POST $route no longer passes the shared imported-Site boundary " +
                    "($($guarded[$route].Replace('\', ''))). Lab writes against an imported code must refuse.")) | Out-Null
            }
        }
        # S2-02 phase 2: a registered run's Commit is a local gateway release.
        # The Commit route must branch on registered_basis first and answer only
        # from port.release_registered, before the file-Stage path; that branch
        # may not seal a file Stage, write the commit store or call ingestion.
        $registeredCommit = '(?s)@router\.post\(RUN_COMMIT_ROUTE\)\n(?:(?!@router\.).)*?' +
            '\n        if record\.registered_basis is not None:\n((?:(?!\n        [^ \n]).)*)' +
            '\n        _refuse_if_imported\(record, commit=True\)'
        if ($labText -notmatch $registeredCommit) {
            $failures.Add(("$labPath POST RUN_COMMIT_ROUTE no longer answers a registered run from " +
                "port.release_registered before the file-Stage path (S2-02 AC5).")) | Out-Null
        } else {
            $branch = $Matches[1]
            if ($branch -notmatch 'port\.release_registered\(record\)') {
                $failures.Add("$labPath registered Commit branch does not call port.release_registered(record).") | Out-Null
            }
            if ($branch -match '_commit_store|_seal\(|\.ingest\(|staged_envelopes') {
                $failures.Add(("$labPath registered Commit branch seals, files or ingests a Stage; a registered " +
                    "run releases only its gateway's sealed batches (S2-02 AC5).")) | Out-Null
            }
        }
    }

    # S2-02 phase 3a: the Evidence cutover gate. Each of the four Site Evidence
    # routes asks imported_scope(site_id) before the legacy site_or_404, the
    # scope asks permits_cutover on the newest comparison record, and the
    # comparison CLI never calls a ledger write path.
    $apiPath = "$backendRoot/evidence_api.py"
    $readsPath = "$backendRoot/evidence/ledger_reads.py"
    $cliPath = "$backendRoot/evidence_migration.py"
    $api = $backendModules | Where-Object { $_.Path -eq $apiPath } | Select-Object -First 1
    $reads = $backendModules | Where-Object { $_.Path -eq $readsPath } | Select-Object -First 1
    $cli = $backendModules | Where-Object { $_.Path -eq $cliPath } | Select-Object -First 1
    if ($null -eq $api -or $null -eq $reads -or $null -eq $cli) {
        $failures.Add("The Evidence cutover check could not find $apiPath, $readsPath or $cliPath; update the check.") | Out-Null
    } else {
        $apiText = $api.Lines -join "`n"
        foreach ($route in @('SITE_EVIDENCE_ROUTE', 'SITE_EVIDENCE_RECORDS_ROUTE', 'SITE_EVIDENCE_RECORD_ROUTE',
                             'SITE_EVIDENCE_REJECTIONS_ROUTE')) {
            $pattern = '(?s)@router\.get\(' + $route + '\)\n    def [a-z_]+\([^\n]*\n        scope = imported_scope\(site_id\)\n'
            if ($apiText -notmatch $pattern) {
                $failures.Add(("$apiPath GET $route no longer asks imported_scope(site_id) first; an imported " +
                    "Site's Evidence reads the ledger only through the comparison gate (S2-02 AC7).")) | Out-Null
            }
        }
        $readsText = $reads.Lines -join "`n"
        if ($readsText -notmatch '(?s)\n    def scope\(self[^\n]*\n(?:(?!\n    def ).)*?permits_cutover\(report') {
            $failures.Add("$readsPath ImportedEvidenceReads.scope no longer asks permits_cutover on the newest report.") | Out-Null
        }
        # S2-02 Q14: the gate recomputes the CURRENT legacy inventory on every
        # read and hands it, with the active environment and the local store-root identity (Q26), to permits_cutover.
        if ($readsText -notmatch '(?s)\n    def scope\(self[^\n]*\n(?:(?!\n    def ).)*?inventory = self\._current_inventory\(code\)(?:(?!\n    def ).)*?permits_cutover\([^)]*environment=self\._environment, inventory=inventory,\s*store_root=self\._current_store_root\(\)\)') {
            $failures.Add(("$readsPath ImportedEvidenceReads.scope no longer recomputes the current legacy inventory, " +
                "environment and store root for permits_cutover; an old PASSED report could authorize a changed or copied store (Q14/Q26).")) | Out-Null
        }
        $lineNumber = 0
        foreach ($line in $cli.Lines) {
            $lineNumber++
            if ($line -match '\.(?:submit|open_batch|decide_chunk|record_refusal|save_site|register_[a-z]+|clear_derived|save_history)\(') {
                $failures.Add(("$cliPath writes through a ledger or legacy store at line ${lineNumber}: " +
                    "$($line.Trim()). The legacy comparison only reads and writes its report.")) | Out-Null
            }
        }
    }

    # S2-02 Q16: the verified unique versioned credential file is the final
    # issued path. Issuance prepares it before the one commit, and neither the
    # CLI nor the file adapter renames or replaces a credential file afterwards
    # (a post-commit file failure would strand a revoked old verifier).
    $issuePath = "$backendRoot/evidence/provision_gateway.py"
    $credentialFilePath = "$backendRoot/evidence/adapters/gateway_credential_file.py"
    $issue = $backendModules | Where-Object { $_.Path -eq $issuePath } | Select-Object -First 1
    $credentialFile = $backendModules | Where-Object { $_.Path -eq $credentialFilePath } | Select-Object -First 1
    if ($null -eq $issue -or $null -eq $credentialFile) {
        $failures.Add("The credential issuance check could not find $issuePath or $credentialFilePath; update the check.") | Out-Null
    } else {
        $issueText = $issue.Lines -join "`n"
        if ($issueText -notmatch '(?s)prepare_gateway_credential_file\(.*?access\.issue_credential\(') {
            $failures.Add("$issuePath no longer prepares the protected versioned file before committing the verifier (Q16).") | Out-Null
        }
        foreach ($module in @($issue, $credentialFile)) {
            $lineNumber = 0
            foreach ($line in $module.Lines) {
                $lineNumber++
                if ($line -match '(?:\bos\.(?:replace|rename)\(|\.rename\(|\.replace\([^)]*Path|\bshutil\.move\(|\bactivate[a-z_]*\()') {
                    $failures.Add(("$($module.Path) renames or replaces a credential file at line ${lineNumber}: " +
                        "$($line.Trim()). The issued versioned file is final; the gateway switches path explicitly (Q16).")) | Out-Null
                }
            }
        }
    }

    return $failures
}
