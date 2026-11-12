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
# Ratchet: SR-2 moved the estate and Work pages onto the range and SR-2b the Site pages, so `$pending` is empty and
# any page date input fails. The ratchet branch stays (proved by the self-test) for a future staged migration: an
# entry names a file's allowed count; the check fails when it grows past it or no longer has any.
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

# M2 (SR-2b review): FocusPicker is for a finer view (a day, an hour, an event). A file that uses it AND builds a
# multi-day from/to window (`localDaysWindow(`, or sets the `from`/`to` address params directly) is still a page range
# form, routed through the exempt picker; the first-day-plus-Days form of Renewable was exactly that.
function Get-FocusPickerRangeWriteCount {
    param([string]$Text)
    if ($Text -notmatch '<FocusPicker\b') { return 0 }
    # A write: a days window handed to onApply/navigate/setSearchParams in one statement, or the params set directly.
    # (Building a fixed read window with localDaysWindow, as the Site board does, is not a write.)
    return [regex]::Matches($Text, '(onApply|navigate|setSearchParams)\([^;]*localDaysWindow\(|\.set\(\s*"(from|to)"').Count
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
        $routed = Get-FocusPickerRangeWriteCount -Text $Files[$path]
        if ($routed -gt 0) {
            $out.Add("$path uses FocusPicker and also writes a from/to range ($routed writes). FocusPicker is for one day, hour or event; read the shared range (useSharedRange) instead of a page range form.")
            continue
        }
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
        "frontend/src/ui/FocusPicker.tsx",
        # PR-3 (rev 5 §5.3): the price form's one "Applies from" date is the value recorded on the price, not a range
        # or a day the page shows. Narrow exemption for this one file; pending Architect confirmation (PR-3 packet Q3).
        "frontend/src/sites/SitePriceEntry.tsx"
    )
    # SR-2b emptied this list: every page reads the shared range. Keep it empty; the self-test still proves the ratchet.
    $pending = @{}

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
        "frontend/src/sites/Routed.tsx"      = '<FocusPicker day={d} label="First day" />; onApply(localDaysWindow(tz, first, 3));'
        "frontend/src/sites/Hour.tsx"        = '<FocusPicker day={d} label="Day" />; onApply(localHourWindow(tz, day, 12));'
        "frontend/src/sites/Board.tsx"       = '<FocusPicker day={d} label="Day" />; const day = { ...localDaysWindow(tz, d, 1) };'
    }
    $got = @(Get-PageRangeFormFailures -Files $fixtures -Pending @{ "frontend/src/sites/Pending.tsx" = 1 } -Exempt @("frontend/src/shell/SharedRangeBar.tsx"))
    $expect = @("frontend/src/estate/Fixture.tsx", "frontend/src/sites/Ledger.tsx", "frontend/src/sites/Pending.tsx", "frontend/src/sites/Routed.tsx")
    $flagged = @($got | ForEach-Object { ($_ -split ' ')[0] } | Sort-Object)
    if (($flagged -join ",") -ne ($expect -join ",")) {
        $failures.Add("page-range-forms self-test: expected failures for $($expect -join ', '), got: $($flagged -join ', ')")
    }

    return $failures
}
