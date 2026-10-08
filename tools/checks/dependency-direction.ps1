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
        @{ Root = "gateway";   Extensions = @(".py") },
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

    # --- The gateway is a separate public-side process ------------------------
    #
    # S2-01b. The durable simulated gateway receives public device reports and a
    # frozen registered snapshot from the Lab host and nothing else. It may import
    # the neutral contracts only: an import of the simulator (kernel, world,
    # scenario, oracle), the backend or the composition leaf would let private
    # truth or product state reach the acquisition ledger. Tests are included:
    # the gateway suite restates the snapshot shape rather than importing it.
    $gatewayMayNotImport = @(
        '^\s*(?:from|import)\s+[^\s]*assetops_backend',
        '^\s*(?:from|import)\s+[^\s]*assetops_simulator',
        '^\s*(?:from|import)\s+(?:backend|simulator)(?:\.|\s|$)',
        'import_module\(\s*["''](?:assetops_backend|assetops_simulator)'
    )

    $gatewaySources = Get-SourceFiles -Root "gateway" -Extensions @(".py")

    if ($gatewaySources.Count -eq 0) {
        $failures.Add(("No module was scanned under gateway/, so the gateway " +
            "boundary check below is vacuous. Update the check, do not " +
            "delete it.")) | Out-Null
    }

    foreach ($source in $gatewaySources) {
        $lineNumber = 0
        foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
            $lineNumber++
            foreach ($pattern in $gatewayMayNotImport) {
                if ($line -match $pattern) {
                    $relative = Resolve-Path -LiteralPath $source.FullName -Relative
                    $failures.Add("Banned import in the gateway at ${relative}:${lineNumber}: $($line.Trim()). The gateway process may import the neutral contracts only.") | Out-Null
                    break
                }
            }
        }
    }

    # S2-01b phase 2: the other side of the same process boundary. The Lab host
    # reaches the gateway only through its authenticated channel module
    # (`assetops_gateway.ipc`); importing the service, ledger or snapshot module
    # would let the host write the outbox in-process and skip the channel's
    # authentication. The product never imports the gateway at all. Host tests
    # are exempt: they inspect the ledger to prove what the channel did.
    $hostGatewayImport = '^\s*(?:from|import)\s+assetops_gateway(?:\.(?<module>\w+))?'
    $hostChannelImports = 0
    foreach ($module in @(Get-ScannedModules -Root "host" -Extensions @(".py"))) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -match $hostGatewayImport) {
                if ($Matches['module'] -eq 'ipc') {
                    $hostChannelImports++
                }
                else {
                    $failures.Add(("The Lab host imports the gateway beyond its channel at " +
                        "$($module.Path):${lineNumber}: $($line.Trim()). The host may import " +
                        "assetops_gateway.ipc only.")) | Out-Null
                }
            }
        }
    }
    if ($hostChannelImports -eq 0) {
        $failures.Add(("No host module imports assetops_gateway.ipc, so the host-side " +
            "gateway boundary check is vacuous. Update the check, do not delete it.")) | Out-Null
    }
    foreach ($module in @(Get-ScannedModules -Root "backend" -Extensions @(".py") -IncludeTests)) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            if ($line -match $hostGatewayImport) {
                $failures.Add(("The product imports the gateway at $($module.Path):${lineNumber}: " +
                    "$($line.Trim()). Only the Lab host composes it.")) | Out-Null
            }
        }
    }

    # --- Staged content is not accepted evidence --------------------------------
    #
    # T023. A staged source envelope is what a later Commit would release, not
    # something ingestion accepted, and v4 section 11.3 and `.ai/ARCHITECTURE.md`
    # Evidence Loop Boundaries forbid an operator surface from treating it as
    # evidence. The stage contract is therefore importable in the product only by
    # the gated Lab surface and the port that serves it. An operator module that
    # imported it could render staged content as Site history, and the gate would
    # not see it, because the gate guards URLs rather than imports.
    #
    # The envelope SCHEMA (`source_envelope`) is deliberately not restricted:
    # ingestion (T027) is exactly the product module that must parse it. What is
    # restricted is the stage - staged, unreleased content, and since S2-01b the
    # registered gateway Stage read `gateway_stage` - which nothing but
    # the Lab may read. Tests are exempt, because a test must reach a boundary to
    # prove where it is.
    $stageImport = @(
        '^\s*(?:from|import)\s+assetops_contracts\.(?:source_stage|gateway_stage)(?:\s|$)',
        '^\s*from\s+assetops_contracts\s+import\s+[^#]*\b(?:source_stage|gateway_stage)\b',
        'import_module\(\s*["'']assetops_contracts\.(?:source_stage|gateway_stage)'
    )
    $mayImportStage = @(
        "backend/assetops_backend/simulator_lab_api.py",
        "backend/assetops_backend/runs/execution_ports.py"
    )

    $backendModules = @(Get-ScannedModules -Root "backend/assetops_backend" -Extensions @(".py"))
    $stageImporters = 0
    foreach ($module in $backendModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $stageImport) {
                if ($line -match $pattern) {
                    if ($mayImportStage -contains $module.Path) {
                        $stageImporters++
                    }
                    else {
                        $failures.Add(("Staged content imported outside the gated Lab surface at " +
                            "$($module.Path):${lineNumber}: $($line.Trim()). A staged source " +
                            "envelope is not accepted evidence; only " +
                            "$($mayImportStage -join ' and ') may read the stage contract.")) | Out-Null
                    }
                    break
                }
            }
        }
    }

    # Anti-vacuity: the allowed importers really do import it, so this check is
    # scanning the right tree with a pattern that matches the real spelling.
    if ($stageImporters -lt $mayImportStage.Count) {
        $failures.Add(("The staged-content check matched $stageImporters of the " +
            "$($mayImportStage.Count) modules allowed to import the stage contract, " +
            "so its pattern no longer matches how the stage is imported and the " +
            "check is vacuous. Update the check, do not delete it.")) | Out-Null
    }

    # --- Recorded Lab history is private truth (T025c) --------------------------
    #
    # `D-2026-09-30-lab-cockpit-history`: a run's recorded history - every stock,
    # every resolved interval, every observation attempt - reaches the product
    # only through the gated Lab port, and no operator view consumes it. Same
    # rule and same two importers as the stage above, for the same reason: the
    # gate guards URLs, and an operator module importing the history contract
    # could render private truth as Site history without touching one.
    $historyImport = @(
        '^\s*(?:from|import)\s+assetops_contracts\.lab_history(?:\s|$)',
        '^\s*from\s+assetops_contracts\s+import\s+[^#]*\blab_history\b',
        'import_module\(\s*["'']assetops_contracts\.lab_history'
    )
    $historyImporters = 0
    foreach ($module in $backendModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $historyImport) {
                if ($line -match $pattern) {
                    if ($mayImportStage -contains $module.Path) {
                        $historyImporters++
                    }
                    else {
                        $failures.Add(("Recorded Lab history imported outside the gated Lab " +
                            "surface at $($module.Path):${lineNumber}: $($line.Trim()). Private " +
                            "execution history is not operator evidence; only " +
                            "$($mayImportStage -join ' and ') may read the history contract.")) | Out-Null
                    }
                    break
                }
            }
        }
    }
    if ($historyImporters -lt $mayImportStage.Count) {
        $failures.Add(("The recorded-history check matched $historyImporters of the " +
            "$($mayImportStage.Count) modules allowed to import the history contract, " +
            "so its pattern no longer matches how it is imported and the check is " +
            "vacuous. Update the check, do not delete it.")) | Out-Null
    }

    # --- Accepted evidence reads accepted content only (T027) -----------------
    #
    # `.ai/ARCHITECTURE.md` Evidence Loop Boundaries and T027 AC8/AC15: the
    # evidence package (ingestion, its store and the Site > Evidence read model)
    # and its router derive everything from what ingestion accepted. They may not
    # reach the simulator, the host leaf, the stage, recorded Lab history, the
    # LabProjection, raw observations, the run domain or the Lab surface - any of
    # those would let staged, private or runtime content become operator
    # evidence without crossing ingestion, and would make rebuild-without-the-Lab
    # (AC15) depend on Lab objects.
    #
    # Anti-vacuity: the evidence tree must be scanned and non-empty, and the
    # router module must be found.
    $evidenceMayNotImport = @(
        '^\s*(?:from|import)\s+assetops_simulator(?:[.\s]|$)',
        '^\s*(?:from|import)\s+host(?:[.\s]|$)',
        '^\s*(?:from|import)\s+assetops_contracts\.(?:source_stage|gateway_stage|lab_history|lab_projection|observation)(?:[.\s]|$)',
        '^\s*from\s+assetops_contracts\s+import\s+[^#]*\b(?:source_stage|gateway_stage|lab_history|lab_projection|observation)\b',
        '^\s*(?:from|import)\s+assetops_backend\.(?:runs|simulator_lab_api)(?:[.\s]|$)',
        '^\s*from\s+assetops_backend\s+import\s+[^#]*\b(?:runs|simulator_lab_api)\b',
        # T028: analytics depend on evidence, never the reverse. The Overview
        # receives assessments by injection from the composition root.
        '^\s*(?:from|import)\s+assetops_backend\.(?:analytics|analytics_api)(?:[.\s]|$)',
        '^\s*from\s+assetops_backend\s+import\s+[^#]*\b(?:analytics|analytics_api)\b',
        'import_module\(\s*["''](?:assetops_simulator|host|assetops_contracts\.(?:source_stage|gateway_stage|lab_history|lab_projection|observation)|assetops_backend\.(?:runs|simulator_lab_api))'
    )
    $evidenceModules = @($backendModules | Where-Object {
        $_.Path.StartsWith("backend/assetops_backend/evidence/") -or
        $_.Path -eq "backend/assetops_backend/evidence_api.py"
    })
    $evidencePackageModules = @($evidenceModules | Where-Object {
        $_.Path.StartsWith("backend/assetops_backend/evidence/") -and $_.Path.EndsWith(".py") -and
        -not $_.Path.EndsWith("__init__.py")
    })
    $evidenceRouterScanned = @($evidenceModules | Where-Object {
        $_.Path -eq "backend/assetops_backend/evidence_api.py"
    }).Count -eq 1
    if ($evidencePackageModules.Count -eq 0 -or -not $evidenceRouterScanned) {
        $failures.Add(("No module was scanned under backend/assetops_backend/evidence/ " +
            "(or evidence_api.py is missing), so the accepted-evidence import check " +
            "is vacuous. Update the check, do not delete it.")) | Out-Null
    }
    foreach ($module in $evidenceModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $evidenceMayNotImport) {
                if ($line -match $pattern) {
                    $failures.Add(("Accepted evidence imports a Lab, simulator or runtime " +
                        "module at $($module.Path):${lineNumber}: $($line.Trim()). The " +
                        "evidence package and its router read accepted content only.")) | Out-Null
                    break
                }
            }
        }
    }

    # --- The shared kernel knows no electrical pack (T024) ----------------------
    #
    # v4 section 16: the shared kernel may not import a pack implementation or
    # branch on which model it runs. The daytime mini-grid model reaches the
    # kernel as a `ModelSpec` carrying its controller and resolver, handed over
    # by the composition leaf; the kernel calls what it is handed. The fuel pack
    # is the kernel's historical default model and is the one import this check
    # tolerates (backlog: "kernel imports the fuel pack as its default").
    #
    # Anti-vacuity: the kernel modules must be found, and the leaf must be what
    # imports the electrical pack - so a renamed pack or a moved kernel fails
    # here rather than passing over an empty set.
    $kernelMayNotImport = @(
        '^\s*(?:from|import)\s+assetops_simulator\.packs\.(?!fuel\b)',
        '^\s*from\s+assetops_simulator\.packs\s+import\s+(?!fuel\b)',
        'model_profile_id\s*=='
    )
    $kernelModules = @(Get-ScannedModules -Root "simulator/assetops_simulator/kernel" -Extensions @(".py"))
    if ($kernelModules.Count -eq 0) {
        $failures.Add(("No module was scanned under simulator/assetops_simulator/kernel, " +
            "so the kernel-knows-no-pack check is vacuous. Update the check, do " +
            "not delete it.")) | Out-Null
    }
    foreach ($module in $kernelModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $kernelMayNotImport) {
                if ($line -match $pattern) {
                    $failures.Add(("The shared kernel names a pack or branches on a model at " +
                        "$($module.Path):${lineNumber}: $($line.Trim()). A model reaches " +
                        "the kernel as the ModelSpec the composition leaf hands it.")) | Out-Null
                    break
                }
            }
        }
    }
    $leafImportsElectricalPack = @(Get-ScannedModules -Root "host" -Extensions @(".py") |
        Where-Object { $_.Path -notlike "host/tests/*" } |
        Where-Object { ($_.Lines -join "`n") -match '(?m)^\s*from\s+assetops_simulator\.packs\.minigrid\s+import' })
    if ($leafImportsElectricalPack.Count -eq 0) {
        $failures.Add(("No composition-leaf module imports the electrical pack, so " +
            "the kernel-knows-no-pack check is not observing the path the model " +
            "actually takes. Update the check, do not delete it.")) | Out-Null
    }

    return $failures
}
