# Seam: Shared Site presentation substrate.
#
# Two structural checks. They are backstops, not the primary guard: render
# equivalence is, and it needs a second consumer of the substrate to compare
# against, so it ships with the Lab's Site view at causal step 6. These two are
# what can be enforced today.
#
#   - Site presentation is defined only in `frontend/src/sites/`
#   - that substrate is a leaf with no shell, mode, or variant discriminant
#
# Test directories are exempt: a test must be able to reach across a boundary
# in order to prove where it is.
#
# Do not weaken the checks below to make a task pass.

function Invoke-SiteSubstrateCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $substrateRoot = "frontend/src/sites"

    if (-not (Test-Path -LiteralPath $substrateRoot -PathType Container)) {
        $failures.Add("Missing shared Site presentation substrate root: $substrateRoot") | Out-Null
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
        },
        @{
            # The site-configuration components, named separately for the same
            # reason: a definition no pattern reaches is a definition the
            # single-definition check does not protect, and a second shell
            # growing its own opinion of what a foundation looks like is the
            # drift this seam exists to stop.
            #
            # `*Frame` is excluded here too, and for the same reason: a frame
            # supplies the landmark and composes the substrate.
            Name    = "Site configuration presentation component"
            Pattern = 'function\s+SiteConfiguration(?!Frame\b)[A-Za-z]*\s*\('
        }
    )

    $frontendModules = @()
    foreach ($module in (Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))) {
        $frontendModules += [pscustomobject]@{
            Path    = $module.Path
            InSites = $module.Path.StartsWith("$substrateRoot/")
            Lines   = $module.Lines
        }
    }

    if ($frontendModules.Count -eq 0) {
        $failures.Add("No frontend modules were scanned; the substrate checks would be vacuous") | Out-Null
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

                $failures.Add(("$($definition.Name) declared outside the shared " +
                    "substrate in $($module.Path):${lineNumber}: $($line.Trim()). " +
                    "It belongs in $substrateRoot, which both shells compose.")) | Out-Null
            }
        }

        if (-not $seenInSubstrate) {
            $failures.Add(("The single-definition check found no " +
                "$($definition.Name) in $substrateRoot, so it is no longer " +
                "proving anything. Update the check, do not delete it.")) | Out-Null
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
                    $failures.Add(("The shared Site substrate is a leaf, but " +
                        "$($module.Path):${lineNumber} imports out of it: " +
                        "$($line.Trim()). $substrateRoot must not import shell " +
                        "code, simulator code, or the feature flag.")) | Out-Null
                    break
                }
            }

            foreach ($pattern in $substrateBannedDiscriminants) {
                if ($line -match $pattern) {
                    $failures.Add(("Shell, mode, or variant discriminant in the " +
                        "shared Site substrate at $($module.Path):${lineNumber}: " +
                        "$($line.Trim()). Every shell difference must be an " +
                        "addition around the core, never a branch inside it.")) | Out-Null
                    break
                }
            }
        }
    }

    if ($substrateModules -eq 0) {
        $failures.Add(("No module was scanned under $substrateRoot, so the " +
            "leaf-direction check is vacuous. Update the check, do not delete it.")) | Out-Null
    }
    elseif ($substrateImports -eq 0) {
        $failures.Add(("No import was seen under $substrateRoot, so the " +
            "leaf-direction import check is vacuous. Update the check, do not " +
            "delete it.")) | Out-Null
    }

    return $failures
}
