# Seam: one shared date range (SR-3; proposal 2026-11-10 "Item 12.5", SR.3 "Consistency and guards"; D-UI.2).
#
# The date range is chosen once, in the shell's top bar (`frontend/src/shell/SharedRangeBar.tsx`), and lives in the
# address. A page must not render its own date range form: two date controls on one page disagree, and a page form
# hides which dates the rest of the app shows. A finer view inside the range (one day, one hour, one event) goes
# through `FocusPicker`, which is exempt like the shell bar.
#
# What counts as a page date form: an `<input type="date">`, or an `<input type="datetime-local">` named `from` or
# `to`, in a non-test `.tsx` file under `frontend/src`.
#
# Ratchet: SR-2 moved the estate and Work pages onto the range. The Site pages listed in `$pending` still carry their
# own forms (SR-2 remaining work, recorded in `.agent/SR-2-packet.md`). Each entry names the number of date inputs the
# file has today; the check fails when a file grows past it, when a file not listed adds one, and when a listed file
# no longer has any (remove the entry, so the list only shrinks).
#
# The self-test at the bottom runs the same scanner over fixed text and fails the seam if it would pass a page form
# or fail an exempt file, so the check cannot silently become vacuous.
#
# Do not weaken this check to make a task pass: move the page onto `useSharedRange` / `FocusPicker` instead.

function Get-PageRangeInputCount {
    param([string]$Text)
    $date = [regex]::Matches($Text, 'type="date"').Count
    $named = [regex]::Matches($Text, '(?s)<input\b[^>]*type="datetime-local"[^>]*name="(from|to)"|<input\b[^>]*name="(from|to)"[^>]*type="datetime-local"').Count
    return $date + $named
}

function Get-PageRangeFormFailures {
    param(
        [hashtable]$Files,      # relative path -> text
        [hashtable]$Pending,    # relative path -> allowed count
        [string[]]$Exempt
    )
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($path in ($Files.Keys | Sort-Object)) {
        if ($Exempt -contains $path) { continue }
        $count = Get-PageRangeInputCount -Text $Files[$path]
        if ($Pending.ContainsKey($path)) {
            $allowed = [int]$Pending[$path]
            if ($count -gt $allowed) {
                $out.Add("$path has $count page date inputs; the SR-2 ratchet allows $allowed. Read the shared range (useSharedRange) or use FocusPicker instead.")
            } elseif ($count -eq 0) {
                $out.Add("$path no longer has a page date form; remove it from the pending list in tools/checks/page-range-forms.ps1.")
            }
        } elseif ($count -gt 0) {
            $out.Add("$path renders its own date range form ($count date inputs). The range is set in the shell's SharedRangeBar; a finer day/hour/event view goes through FocusPicker.")
        }
    }
    foreach ($path in ($Pending.Keys | Sort-Object)) {
        if (-not $Files.ContainsKey($path)) {
            $out.Add("$path is in the pending list of tools/checks/page-range-forms.ps1 but does not exist; remove the entry.")
        }
    }
    return $out
}

function Invoke-PageRangeFormsCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $exempt = @(
        "frontend/src/shell/SharedRangeBar.tsx",
        "frontend/src/shell/FocusPicker.tsx"
    )
    # SR-2 remaining (Site pages); counts are today's, and only shrink.
    $pending = @{
        "frontend/src/sites/LedgerSiteEvidence.tsx"  = 2
        "frontend/src/sites/MiniScenarios.tsx"       = 2
        "frontend/src/sites/SiteFindingIndex.tsx"    = 2
        "frontend/src/sites/SiteWorkActions.tsx"     = 4
        "frontend/src/sites/siteWorkCases.tsx"       = 2
    }

    $root = (Get-Location).Path
    $files = @{}
    Get-ChildItem -LiteralPath (Join-Path $root "frontend/src") -Recurse -Filter "*.tsx" -File |
        Where-Object { $_.FullName -notmatch '[\\/]__tests__[\\/]' -and $_.Name -notmatch '\.test\.tsx$' } |
        ForEach-Object {
            $rel = $_.FullName.Substring($root.Length + 1).Replace('\', '/')
            $files[$rel] = [System.IO.File]::ReadAllText($_.FullName)
        }
    foreach ($f in (Get-PageRangeFormFailures -Files $files -Pending $pending -Exempt $exempt)) { $failures.Add($f) }

    # Self-test: a page form fails; the exempt bar passes; a datetime-local `from` input counts; the ratchet bites.
    $fixtures = @{
        "frontend/src/estate/Fixture.tsx"    = '<input className="v69-chip-control" type="date" value={first} />'
        "frontend/src/shell/SharedRangeBar.tsx" = '<input type="date" /><input type="date" />'
        "frontend/src/sites/Ledger.tsx"      = '<input type="datetime-local" name="from" value={from} />'
        "frontend/src/sites/Pending.tsx"     = '<input type="date" /><input type="date" />'
        "frontend/src/sites/Entry.tsx"       = '<input type="datetime-local" name="effective" />'
    }
    $got = @(Get-PageRangeFormFailures -Files $fixtures -Pending @{ "frontend/src/sites/Pending.tsx" = 1 } -Exempt @("frontend/src/shell/SharedRangeBar.tsx"))
    $expect = @("frontend/src/estate/Fixture.tsx", "frontend/src/sites/Ledger.tsx", "frontend/src/sites/Pending.tsx")
    $flagged = @($got | ForEach-Object { ($_ -split ' ')[0] } | Sort-Object)
    if (($flagged -join ",") -ne ($expect -join ",")) {
        $failures.Add("page-range-forms self-test: expected failures for $($expect -join ', '), got: $($flagged -join ', ')")
    }

    return $failures
}
