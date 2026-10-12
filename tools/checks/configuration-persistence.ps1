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
        @{ Name = $domain.Name; Var = $domain.UserRootVar; Owner = $domain.UserRootOwner }
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
    $assessTables = @('analytic_run', 'analytic_run_evidence', 'assessment_revision', 'analytic_run_assessment', 'analytic_run_selection')
    $assessInserts = $assessTables + @('recompute_job')
    $assessUpdates = @(
        '(?i)\bUPDATE\s+recompute_job\s+SET\s+status\s*=',
        '(?i)\bUPDATE\s+recompute_job\s+SET\s+window_start\s*=\s*:start,\s*window_end\s*=\s*:end\s+WHERE\b')
    $findingWriter = "$backendRoot/analytics/adapters/postgres_finding_store.py"
    $findingTables = @('finding', 'finding_revision', 'finding_revision_assessment', 'finding_revision_evidence',
        'finding_merge')
    $pgWriters = @($pgWriter, $ledgerWriter, $accessWriter, $assessWriter, $findingWriter)
    $sqlWrite = '(?i)\b(?:INSERT\s+INTO|UPDATE\s+[a-z_]+\s+SET|DELETE\s+FROM|TRUNCATE\s+[a-z_]+|CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE)\b'
    $sqlTarget = '(?i)\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|TRUNCATE)\s+([a-z_]+)'
    $dbDriver = '(?:^|\s)(?:import|from)\s+(?:sqlalchemy|psycopg|alembic)(?:[.\s]|$)'
    $pgWritesSeen = @{ $pgWriter = 0; $ledgerWriter = 0; $accessWriter = 0; $assessWriter = 0; $findingWriter = 0 }
    $pgDriverSeen = @{ $pgWriter = $false; $ledgerWriter = $false; $accessWriter = $false; $assessWriter = $false
        $findingWriter = $false }
    foreach ($module in $backendModules) {
        if (-not $module.Path.StartsWith("$backendRoot/")) { continue }
        $isWriter = $pgWriters -contains $module.Path
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -match $sqlWrite) {
                if (-not $isWriter) {
                    $failures.Add(("A second product database writer in $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). Product rows are written only by $($pgWriters -join ' and ').")) | Out-Null
                    continue
                }
                $pgWritesSeen[$module.Path]++
                $target = if ($line -match $sqlTarget) { $Matches[1].ToLowerInvariant() } else { $null }
                if ($module.Path -eq $ledgerWriter -and ($null -eq $target -or $ledgerTables -notcontains $target)) {
                    $failures.Add(("The evidence ledger writes only its own tables ($($ledgerTables -join ', ')); " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
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
                    if (-not ($insertOk -or $updateOk)) {
                        $failures.Add(("The assessment store inserts only $($assessInserts -join ', ') and updates " +
                            "only a recompute job's lease/retry status or a PENDING job's window; " +
                            "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                    }
                }
                if ($module.Path -eq $findingWriter -and -not (
                        $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)' -and $findingTables -contains $Matches[1].ToLowerInvariant())) {
                    $failures.Add(("The Finding store only inserts into $($findingTables -join ', ') (append-only); " +
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
                if ($module.Path -eq $pgWriter -and $null -ne $target -and $ledgerTables -contains $target) {
                    $failures.Add(("The Foundation store must not write ledger table '$target'; " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
            }
            if ($line -match $dbDriver) {
                if ($isWriter) { $pgDriverSeen[$module.Path] = $true }
                else {
                    $failures.Add(("Database driver imported outside $($pgWriters -join ' and ') in " +
                        "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                }
            }
        }
    }
    foreach ($writer in $pgWriters) {
        if ($pgWritesSeen[$writer] -eq 0 -or -not $pgDriverSeen[$writer]) {
            $failures.Add(("The product database writer check found no SQL write or driver import in " +
                "$writer, so it is no longer proving anything. Update the check, do not delete it.")) | Out-Null
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
