# Seam: Shared visual vocabulary (leaf direction, and one system not two).
#
# The primitives module is the single visual vocabulary. Two rules keep it
# from becoming something else:
#
#   - it is a leaf: no shell code, no simulator code, no feature flag, and no
#     Site substrate import. A primitive that could read the gate would be a
#     back door around it, and a primitive that could import the substrate
#     would be a second home for Site presentation.
#   - it is actually shared: both the shell root and the Site substrate render
#     with it. A vocabulary nobody imports is a vocabulary that has been
#     forked.
#
# The complementary rule - that the primitives declare no Site read model, view
# derivation, or presentation component - is already enforced by
# site-substrate.ps1, which flags those definitions anywhere outside
# frontend/src/sites. It is not repeated here.
#
# Test directories are exempt: a test must be able to reach across a boundary
# in order to prove where it is.
#
# Do not weaken the checks below to make a task pass.

function Invoke-UiPrimitivesCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $primitivesRoot = "frontend/src/ui"

    if (-not (Test-Path -LiteralPath $primitivesRoot -PathType Container)) {
        $failures.Add("Missing shared UI primitives root: $primitivesRoot") | Out-Null
        return $failures
    }

    # --- Leaf direction --------------------------------------------------------

    $bannedImports = @(
        @{
            Pattern = 'from\s+["''][^"'']*shell[/"'']'
            Reason  = "shell code"
        },
        @{
            Pattern = 'from\s+["''][^"'']*featureFlags'
            Reason  = "the feature flag"
        },
        @{
            Pattern = 'from\s+["''][^"'']*[Ss]imulator'
            Reason  = "simulator code"
        },
        @{
            Pattern = 'from\s+["''][^"'']*sites[/"'']'
            Reason  = "the Site substrate"
        }
    )

    $primitiveModules = @(Get-ScannedModules -Root $primitivesRoot -Extensions @(".ts", ".tsx"))

    if ($primitiveModules.Count -eq 0) {
        $failures.Add(("No module was scanned under $primitivesRoot, so the " +
            "primitives leaf-direction check is vacuous. Update the check, do " +
            "not delete it.")) | Out-Null
    }

    foreach ($module in $primitiveModules) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++
            foreach ($banned in $bannedImports) {
                if ($line -match $banned.Pattern) {
                    $failures.Add(("The shared UI primitives are a leaf, but " +
                        "$($module.Path):${lineNumber} imports $($banned.Reason): " +
                        "$($line.Trim()). $primitivesRoot supplies vocabulary and " +
                        "must not depend on a shell, the gate, or Site " +
                        "presentation.")) | Out-Null
                    break
                }
            }
        }
    }

    # --- One system, not two ---------------------------------------------------

    # Both shells and the substrate must render with this vocabulary. The check
    # is deliberately coarse: it proves the module is consumed on both sides of
    # the shell/substrate boundary, which is what stops it being quietly
    # replaced by a bespoke table in one of them.
    $consumers = @(
        @{ Root = "frontend/src/shell"; Name = "The shell" },
        @{ Root = "frontend/src/sites"; Name = "The shared Site substrate" }
    )

    $primitivesImport = 'from\s+["''][^"'']*\.\./ui(?:/[^"'']*)?["'']'

    foreach ($consumer in $consumers) {
        $consumerModules = @(Get-ScannedModules -Root $consumer.Root -Extensions @(".ts", ".tsx"))

        if ($consumerModules.Count -eq 0) {
            $failures.Add(("No module was scanned under $($consumer.Root), so " +
                "the shared-vocabulary check is vacuous for it. Update the " +
                "check, do not delete it.")) | Out-Null
            continue
        }

        $importsPrimitives = $false
        foreach ($module in $consumerModules) {
            foreach ($line in $module.Lines) {
                if ($line -match $primitivesImport) {
                    $importsPrimitives = $true
                    break
                }
            }
            if ($importsPrimitives) { break }
        }

        if (-not $importsPrimitives) {
            $failures.Add(("$($consumer.Name) does not import the shared UI " +
                "primitives from $primitivesRoot. One visual vocabulary means " +
                "both shells and the substrate render with it; a surface that " +
                "keeps a bespoke header, rail, table, badge, or panel is a " +
                "second visual system.")) | Out-Null
        }
    }

    return $failures
}
