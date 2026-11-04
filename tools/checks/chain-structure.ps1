# Seam: Outcome chain structure (CH-5a2a, build sheet CH-5a §B8, ruling CH5a2-R R6; design §13).
#
# Outside backend/assetops_backend/chain/, no module joins Findings to Actions by importing both a Finding
# store/index and an Action store/index, calls a replaced day/window function, or defines a function the design
# §5.1 "Replaces" column names. The AST walk lives in tools/checks/check_chain_structure.py; today's violations are
# in tools/checks/fixtures/chain_structure_baseline.json, each with its owner slice, and that list only shrinks.
#
# Do not weaken the checks below to make a task pass.

function Invoke-ChainStructureCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    # The interpreter is found as configuration-persistence.ps1 finds it (ASSETOPS_GUARD_PYTHON, else the
    # repository .venv). A guard that cannot run fails; it never skips.
    $guardPython = $env:ASSETOPS_GUARD_PYTHON
    if (-not $guardPython) {
        foreach ($candidate in @('.venv/Scripts/python.exe', '.venv/bin/python')) {
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { $guardPython = $candidate; break }
        }
    }
    if (-not $guardPython -or -not (Test-Path -LiteralPath $guardPython -PathType Leaf)) {
        $failures.Add(("The chain structure guard cannot run: no Python interpreter at '$guardPython' or .venv. " +
            "Create the repository .venv or set ASSETOPS_GUARD_PYTHON; the guard never skips.")) | Out-Null
        return $failures
    }

    $output = @(& $guardPython 'tools/checks/check_chain_structure.py')
    $exitCode = $LASTEXITCODE
    foreach ($line in $output) {
        if ("$line".Trim()) { $failures.Add("$line") | Out-Null }
    }
    if ($exitCode -ne 0 -and $failures.Count -eq 0) {
        $failures.Add("tools/checks/check_chain_structure.py failed (exit $exitCode) with no report.") | Out-Null
    }
    return $failures
}
