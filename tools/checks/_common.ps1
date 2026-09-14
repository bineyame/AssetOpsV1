# Shared scanning helpers for the architecture check modules in this directory.
#
# Dot-sourced by tools/check-architecture.ps1 before any check module. Every
# check module assumes the current location is the repository root, which the
# runner guarantees.
#
# This file holds scanning mechanics only. It must not hold a seam rule: a
# check that lives here is a check no reviewer reads when they open the module
# for the seam they are changing, which is the whole reason the checks were
# split.

# Directories that are never source. Pruned BEFORE descending, not filtered
# afterwards: Get-ChildItem -Recurse walks every subtree first, so a
# permission-denied cache directory (pytest and npm both create these) aborts
# the whole scan under $ErrorActionPreference = "Stop". A guard that fails for
# reasons unrelated to the seam it protects gets ignored.
$script:IgnoredDirectories = @(
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
                if ($script:IgnoredDirectories -contains $entry.Name) { continue }
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

# Source files under a root as { Path; Lines } records, with repo-relative
# forward-slash paths.
#
# Test directories are excluded by default, and every caller that scans for a
# banned pattern wants that: a test must be able to reach across a boundary, or
# request an unserved URL, in order to prove where the boundary is.
function Get-ScannedModules {
    param(
        [Parameter(Mandatory = $true)] [string] $Root,
        [Parameter(Mandatory = $true)] [string[]] $Extensions,
        [switch] $IncludeTests
    )

    $modules = @()
    foreach ($source in (Get-SourceFiles -Root $Root -Extensions $Extensions)) {
        $relative = (Resolve-Path -LiteralPath $source.FullName -Relative) `
            -replace '^\.[\\/]', '' -replace '\\', '/'

        if (-not $IncludeTests -and $relative -match '(^|/)(tests|__tests__)/') { continue }

        $modules += [pscustomobject]@{
            Path  = $relative
            Lines = @(Get-Content -LiteralPath $source.FullName)
        }
    }
    return $modules
}
