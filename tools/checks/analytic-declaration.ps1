# Seam: Product analytics declare what they claim, and read accepted evidence only (T028).
#
# `D-2026-10-02-presentation-profile-and-capability-declaration`: the backend owns
# which analytics exist, the Finding type each may emit, the evidence each
# requires and its claim levels, through a capability declaration. This check
# copies the rigour of the simulator model-profile guard (the kernel-knows-no-pack
# block in dependency-direction.ps1), not its data:
#
#   1. Every analytic module (one that sets `ANALYTIC_ID` at module level) is
#      declared: `analytics/declaration.py` imports it, an `AnalyticDeclaration(`
#      block takes its `analytic_id` from it, and that block names every field
#      the decision requires, including its readiness basis (T028 AC20: the
#      Site > Evidence capability row is scored from it, so an analytic without
#      one would have a row the backend cannot score). Verification rules are
#      refused until T034.
#   2. Every declaration is listed in `DECLARATIONS`, so the served read model
#      cannot omit one.
#   3. Product analytics (the analytics package and analytics_api.py) may not
#      import the simulator, the host leaf, the run or scenario domains, the Lab
#      surface, the stage, Lab history, the Lab projection or raw observations,
#      and may not name `EXECUTION_REQUIREMENTS` or `execution_requirement`
#      (defined in `scenarios/models.py`, read by `runs/parsing.py`; the task
#      cites `runs/profiles.py`, whose docstring names it). Those are private
#      or simulator flow; an analytic that reads one is scripted, not inferred.
#
# Anti-vacuity: the package, the declaration module and at least one analytic
# module must be found, and each analytic must be matched to a declaration.
# Tests are exempt, as everywhere in this directory.

function Invoke-AnalyticDeclarationCheck {
    $failures = New-Object System.Collections.Generic.List[string]
    $root = "backend/assetops_backend"
    $modules = @(Get-ScannedModules -Root $root -Extensions @(".py") | Where-Object {
        $_.Path.StartsWith("$root/analytics/") -or $_.Path -eq "$root/analytics_api.py"
    })
    $package = @($modules | Where-Object {
        $_.Path.StartsWith("$root/analytics/") -and $_.Path.EndsWith(".py")
    })
    $declarationModule = $package | Where-Object { $_.Path -eq "$root/analytics/declaration.py" }
    $analyticModules = @($package | Where-Object {
        @($_.Lines | Where-Object { $_ -match '^ANALYTIC_ID\s*=' }).Count -gt 0
    })
    if ($package.Count -eq 0 -or $null -eq $declarationModule -or $analyticModules.Count -eq 0) {
        $failures.Add(("No analytics package, declaration module or analytic module " +
            "(ANALYTIC_ID) was found under $root/analytics/, so the declaration check " +
            "is vacuous. Update the check, do not delete it.")) | Out-Null
        return $failures
    }
    if (@($modules | Where-Object { $_.Path -eq "$root/analytics_api.py" }).Count -ne 1) {
        $failures.Add("$root/analytics_api.py was not scanned; the analytics router is unguarded.") | Out-Null
    }

    # --- 3. no private or simulator flow -----------------------------------------
    $mayNotRead = @(
        '^\s*(?:from|import)\s+assetops_simulator(?:[.\s]|$)',
        '^\s*(?:from|import)\s+host(?:[.\s]|$)',
        '^\s*(?:from|import)\s+(?:lab_execution|source_stages|lab_app|lab_history)(?:[.\s]|$)',
        '^\s*(?:from|import)\s+assetops_contracts\.(?:source_stage|gateway_stage|lab_history|lab_projection|observation|execution_contract)(?:[.\s]|$)',
        '^\s*from\s+assetops_contracts\s+import\s+[^#]*\b(?:source_stage|gateway_stage|lab_history|lab_projection|observation|execution_contract)\b',
        '^\s*(?:from|import)\s+assetops_backend\.(?:runs|scenarios|simulator_lab_api)(?:[.\s]|$)',
        '^\s*from\s+assetops_backend\s+import\s+[^#]*\b(?:runs|scenarios|simulator_lab_api)\b',
        'import_module\(',
        '\bEXECUTION_REQUIREMENTS\b',
        '\bexecution_requirements?\b',
        '\bLabProjection\b'
    )
    foreach ($module in $modules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($pattern in $mayNotRead) {
                if ($line -match $pattern) {
                    $failures.Add(("A product analytic reaches private or simulator flow at " +
                        "$($module.Path):${lineNumber}: $($line.Trim()). Analytics read " +
                        "accepted evidence and the Foundation only.")) | Out-Null
                    break
                }
            }
        }
    }

    # --- 1. and 2. every analytic declared, every declaration complete and listed --
    $required = @("analytic_id", "display_name", "site_types", "finding_type",
        "required_evidence", "optional_evidence", "claim_levels", "model_version",
        "readiness")
    $blocks = @{}
    $current = $null
    $lines = @($declarationModule.Lines)
    foreach ($line in $lines) {
        if ($null -eq $current -and $line -match '^(\w+)\s*=\s*AnalyticDeclaration\(') {
            $current = $Matches[1]
            $blocks[$current] = New-Object System.Collections.Generic.List[string]
            continue
        }
        if ($null -ne $current) {
            if ($line -match '^\)') { $current = $null; continue }
            $blocks[$current].Add($line) | Out-Null
        }
    }
    if ($blocks.Count -eq 0) {
        $failures.Add("No AnalyticDeclaration( block was found in $($declarationModule.Path).") | Out-Null
    }
    $whole = ($lines -join "`n")
    $declaredFrom = @{}
    foreach ($name in $blocks.Keys) {
        $body = $blocks[$name] -join "`n"
        foreach ($field in $required) {
            if ($body -notmatch "(?m)^\s+$field\s*=") {
                $failures.Add(("Analytic declaration $name in $($declarationModule.Path) does " +
                    "not declare '$field'.")) | Out-Null
            }
        }
        if ($body -match '(?i)verification') {
            $failures.Add(("Analytic declaration $name declares verification rules; they " +
                "join at T034 and are not declared yet.")) | Out-Null
        }
        if ($body -match '(?m)^\s+analytic_id\s*=\s*(\w+)\.ANALYTIC_ID') {
            $declaredFrom[$Matches[1]] = $name
        } else {
            $failures.Add(("Analytic declaration $name does not take analytic_id from an " +
                "analytic module's ANALYTIC_ID.")) | Out-Null
        }
        if ($whole -notmatch "(?m)^DECLARATIONS[^=]*=\s*\([^)]*\b$name\b") {
            $failures.Add(("Analytic declaration $name is not listed in DECLARATIONS, so the " +
                "served declaration would omit it.")) | Out-Null
        }
    }
    foreach ($module in $analyticModules) {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($module.Path)
        $imported = @($lines | Where-Object {
            $_ -match "^\s*from\s+assetops_backend\.analytics\s+import\s+[^#]*\b$stem\b"
        }).Count -gt 0
        if (-not $imported -or -not $declaredFrom.ContainsKey($stem)) {
            $failures.Add(("Analytic module $($module.Path) sets ANALYTIC_ID but has no " +
                "declaration in $($declarationModule.Path). Declare its site types, " +
                "Finding type, evidence and claim levels.")) | Out-Null
        }
    }
    return $failures
}
