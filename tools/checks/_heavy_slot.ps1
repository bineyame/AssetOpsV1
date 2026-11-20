# T1: the heavy-tool slot pool, pwsh half (specs/T1-heavy-tool-slot-pool/spec.md §2, §3.1, §5.1).
#
# Dot-sourced by tools/check-all.ps1, tools/heavy-slot.ps1 and the container test runners. Not an architecture
# module: tools/check-architecture.ps1 skips every `_*.ps1` in tools/checks.
#
# The pool is two exclusive flock(2) locks, slot-1.lock and slot-2.lock, in D = <git common dir>/check-all-slots
# (canonical), plus db-job.lock for the one heavy database job at a time. .NET's FileShare.None open is that flock
# on Linux and is close-on-exec, so a child never inherits it (D-T1.2). The bash wrapper takes the same locks.

$script:HeavyOnWindows = ($PSVersionTable.PSVersion.Major -lt 6) -or $IsWindows

function Get-HeavyCanonicalPath([string]$Path) {
    if (-not $Path) { return $null }
    if ($script:HeavyOnWindows) {
        try { return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/') } catch { return $null }
    }
    $out = & realpath -e -- $Path 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
    return "$out".Trim()
}

function Test-HeavySamePath([string]$A, [string]$B) {
    if (-not $A -or -not $B) { return $false }
    if ($script:HeavyOnWindows) { return [string]::Equals($A, $B, [StringComparison]::OrdinalIgnoreCase) }
    return [string]::Equals($A, $B, [StringComparison]::Ordinal)
}

# `git rev-parse --git-common-dir` with every GIT_* variable removed from git's environment (R3).
function Get-HeavyGitCommonDir([string]$From) {
    if (-not $From) { return $null }
    $saved = @{}
    foreach ($item in @(Get-ChildItem env: | Where-Object { $_.Name -like 'GIT_*' })) {
        $saved[$item.Name] = $item.Value
        Remove-Item -LiteralPath "env:$($item.Name)"
    }
    try {
        $out = & git -C $From rev-parse --path-format=absolute --git-common-dir 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
        return "$out".Trim()
    } catch { return $null }
    finally {
        foreach ($name in $saved.Keys) { Set-Item -LiteralPath "env:$name" -Value $saved[$name] }
    }
}

# D per spec §2. $Override: honour ASSETOPS_HEAVY_SLOT_DIR (wrappers and Enter-HeavySlot only; never a tripwire).
# $Tripwire: on a git failure retry from the current directory, and return $null rather than the temp fallback.
function Resolve-HeavySlotDir([string]$From, [bool]$Override, [bool]$Tripwire) {
    if ($Override -and $env:ASSETOPS_HEAVY_SLOT_DIR) {
        New-Item -ItemType Directory -Force -Path $env:ASSETOPS_HEAVY_SLOT_DIR | Out-Null
        return (Get-HeavyCanonicalPath $env:ASSETOPS_HEAVY_SLOT_DIR)
    }
    $common = Get-HeavyGitCommonDir $From
    if (-not $common -and $Tripwire) { $common = Get-HeavyGitCommonDir (Get-Location).Path }
    if ($common) {
        $canonical = Get-HeavyCanonicalPath $common
        if ($canonical) { return [IO.Path]::Combine($canonical, "check-all-slots") }
    }
    if ($Tripwire) { return $null }
    $temp = Get-HeavyCanonicalPath ([IO.Path]::GetTempPath())
    if (-not $temp) { $temp = [IO.Path]::GetTempPath() }
    return [IO.Path]::Combine($temp, "assetops-check-all-slots")
}

function Get-HeavySlotDir([string]$RepoRoot) {
    $dir = Resolve-HeavySlotDir $RepoRoot $true $false
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

# A probe: never creates the file; a missing file is free (I12d, R8b).
function Test-HeavyLockHeld([string]$Path) {
    if (-not $Path) { return $false }
    try {
        $probe = [IO.File]::Open($Path, 'Open', 'Read', 'None')
        $probe.Dispose()
        return $false
    }
    catch [System.IO.FileNotFoundException] { return $false }
    catch [System.IO.DirectoryNotFoundException] { return $false }
    catch [System.IO.IOException] { return $true }
    catch { return $false }
}

function Get-HeavyOwnerPath([string]$LockPath) {
    return [IO.Path]::Combine([IO.Path]::GetDirectoryName($LockPath), [IO.Path]::GetFileNameWithoutExtension($LockPath) + ".owner")
}

function Read-HeavyOwner([string]$LockPath) {
    $fields = @{}
    try {
        foreach ($line in [IO.File]::ReadAllLines((Get-HeavyOwnerPath $LockPath))) {
            $at = $line.IndexOf('=')
            if ($at -gt 0) { $fields[$line.Substring(0, $at)] = $line.Substring($at + 1) }
        }
    } catch { }
    return $fields
}

function Test-HeavyPidAlive([int]$ProcessId) {
    if ($ProcessId -le 0) { return $false }
    if (-not $script:HeavyOnWindows) {
        try {
            $stat = [IO.File]::ReadAllText("/proc/$ProcessId/stat")
            return ($stat.Substring($stat.LastIndexOf(')') + 2).Split(' ')[0] -ne 'Z')
        } catch { return $false }
    }
    return [bool](Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)
}

# D-T1.14: the holder is the caller itself or an ancestor (4th field of /proc/<pid>/stat, after the last ')').
function Test-HeavyAncestor([int]$HolderPid, [int]$Caller) {
    if ($HolderPid -le 0 -or -not (Test-HeavyPidAlive $HolderPid)) { return $false }
    $p = $Caller
    for ($i = 0; $i -le 64 -and $p -gt 0; $i++) {
        if ($p -eq $HolderPid) { return $true }
        try { $stat = [IO.File]::ReadAllText("/proc/$p/stat") } catch { return $false }
        $p = [int]($stat.Substring($stat.LastIndexOf(')') + 2).Split(' ')[1])
    }
    return $false
}

# The marker test (spec §2), in order: set; in D with the right name; holder is self or an ancestor (Linux); held.
function Test-HeavyMarker([string]$Value, [string]$SlotDir, [string]$Name) {
    if (-not $Value) { return @{ Ok = $false; Reason = "ASSETOPS_HEAVY_SLOT is not set" } }
    $pool = @{ Ok = $false; Reason = "the marker is not a slot of this machine's pool" }
    if (-not $SlotDir) { return $pool }
    $leaf = [IO.Path]::GetFileName($Value)
    $parent = [IO.Path]::GetDirectoryName($Value)
    if (-not $parent) { return $pool }
    $pattern = if ($Name -eq 'db') { '^db-job\.lock$' } else { '^slot-[12]\.lock$' }
    if ($leaf -notmatch $pattern) { return $pool }
    if (-not (Test-HeavySamePath (Get-HeavyCanonicalPath $parent) $SlotDir)) { return $pool }
    $lock = [IO.Path]::Combine($SlotDir, $leaf)
    if (-not $script:HeavyOnWindows) {
        $owner = Read-HeavyOwner $lock
        $holder = 0
        if (-not ($owner.ContainsKey('pid') -and [int]::TryParse($owner['pid'], [ref]$holder) -and (Test-HeavyAncestor $holder $PID))) {
            return @{ Ok = $false; Reason = "the slot's holder is not this process or an ancestor" }
        }
    }
    if (-not (Test-HeavyLockHeld $lock)) { return @{ Ok = $false; Reason = "the slot is not held" } }
    return @{ Ok = $true; Reason = "" }
}

function Assert-HeavySlotLocking {
    if ($env:DOTNET_SYSTEM_IO_DISABLEFILELOCKING) {
        [Console]::Error.WriteLine("heavy-slot: refused: DOTNET_SYSTEM_IO_DISABLEFILELOCKING is set; the slot locks would not hold.")
        exit 69
    }
}

function Write-HeavyOwner([string]$LockPath, [string]$Label, [bool]$Db) {
    $since = [DateTime]::UtcNow.ToString('s') + 'Z'
    $yes = if ($Db) { 'yes' } else { 'no' }
    $text = "pid=$PID`nlabel=$Label`nsince=$since`ncwd=$($PWD.ProviderPath)`ndb=$yes`n"
    try { [IO.File]::WriteAllText((Get-HeavyOwnerPath $LockPath), $text) } catch { }
}

# After the wrapper starts its child: one more owner field (appended, so a reader never sees an empty file).
function Add-HeavyOwnerChild($Handle, [int]$ChildPid) {
    if (-not $Handle -or $Handle.Nested) { return }
    foreach ($lock in @($Handle.SlotPath, $Handle.DbPath)) {
        if ($lock) { try { [IO.File]::AppendAllText((Get-HeavyOwnerPath $lock), "child=$ChildPid`n") } catch { } }
    }
}

function Enter-HeavySlot {
    param(
        [string]$SlotDir,
        [int]$Slots = 2,
        [int]$WaitSeconds,
        [switch]$Db,
        [string]$Label = "",
        [string]$Announce = "",
        # Where -Announce goes: check-all keeps its host line; the wrappers write to stderr.
        [ValidateSet('Host', 'Error')][string]$AnnounceTo = 'Host'
    )
    if ($Slots -gt 2) { [Console]::Error.WriteLine("heavy-slot: the shared pool has 2 slots (T1)"); exit 64 }
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $marker = $env:ASSETOPS_HEAVY_SLOT
    if ($marker) {
        $test = Test-HeavyMarker $marker $SlotDir 'slot'
        if ($test.Ok) {
            if ($Db -and -not (Test-HeavyMarker $env:ASSETOPS_HEAVY_DB $SlotDir 'db').Ok) {
                [Console]::Error.WriteLine("heavy-slot: refused: --db inside a held slot; put --db on the outermost wrapper.")
                exit 69
            }
            return @{ Nested = $true; SlotPath = $marker; SlotStream = $null
                      DbPath = $(if ($Db) { $env:ASSETOPS_HEAVY_DB } else { $null }); DbStream = $null; WaitedSeconds = 0.0 }
        }
        [Console]::Error.WriteLine("heavy-slot: ignoring stale ASSETOPS_HEAVY_SLOT=$marker ($($test.Reason))")
    }
    $dbPath = [IO.Path]::Combine($SlotDir, "db-job.lock")
    $dbStream = $null
    $slotStream = $null
    $slotPath = $null
    $saidDb = $false
    $saidSlot = $false
    while ($true) {
        # Order: the DB lock first, then the lowest free slot (deadlock freedom, spec §2).
        if ($Db -and -not $dbStream) {
            try { $dbStream = [IO.File]::Open($dbPath, 'OpenOrCreate', 'ReadWrite', 'None') } catch [System.IO.IOException] { }
        }
        if (-not $Db -or $dbStream) {
            for ($i = 1; $i -le $Slots -and -not $slotStream; $i++) {
                $candidate = [IO.Path]::Combine($SlotDir, "slot-$i.lock")
                try { $slotStream = [IO.File]::Open($candidate, 'OpenOrCreate', 'ReadWrite', 'None'); $slotPath = $candidate }
                catch [System.IO.IOException] { }
            }
        }
        if ($slotStream) { break }
        $left = $WaitSeconds - $clock.Elapsed.TotalSeconds
        if ($left -le 0) {
            if ($dbStream) { $dbStream.Dispose() }
            return $null
        }
        if ($Db -and -not $dbStream) {
            if (-not $saidDb) { [Console]::Error.WriteLine("heavy-slot: another database job holds db-job.lock; waiting up to $WaitSeconds s."); $saidDb = $true }
        } elseif (-not $saidSlot -and $Announce) {
            if ($AnnounceTo -eq 'Error') { [Console]::Error.WriteLine($Announce) } else { Write-Host $Announce }
            $saidSlot = $true
        }
        Start-Sleep -Milliseconds ([int][Math]::Min(2000, [Math]::Ceiling($left * 1000)))
    }
    Write-HeavyOwner $slotPath $Label $Db.IsPresent
    if ($dbStream) { Write-HeavyOwner $dbPath $Label $true }
    return @{ Nested = $false; SlotPath = $slotPath; SlotStream = $slotStream
              DbPath = $(if ($dbStream) { $dbPath } else { $null }); DbStream = $dbStream; WaitedSeconds = $clock.Elapsed.TotalSeconds }
}

function Exit-HeavySlot($Handle) {
    if (-not $Handle) { return }
    foreach ($pair in @(@($Handle.SlotPath, $Handle.SlotStream), @($Handle.DbPath, $Handle.DbStream))) {
        if (-not $pair[1]) { continue }
        $owner = Read-HeavyOwner $pair[0]
        if ($owner['pid'] -eq "$PID") { try { [IO.File]::Delete((Get-HeavyOwnerPath $pair[0])) } catch { } }
        $pair[1].Dispose()
    }
    $Handle.SlotStream = $null
    $Handle.DbStream = $null
}

function Get-HeavyRefusal([string]$Tool, [string]$Reason, [bool]$Db) {
    $sh = if ($Db) { "--db " } else { "" }
    $ps = if ($Db) { "-Db " } else { "" }
    return "heavy-slot: refused: $Tool runs only inside the heavy-tool slot pool ($Reason).`n" +
        "Run it as: tools/heavy-slot.sh $($sh)-- <your command>   (from frontend/: ../tools/heavy-slot.sh; pwsh: pwsh -NoProfile -File tools/heavy-slot.ps1 $($ps)-- ...)`n" +
        "RULES §7 (T1)."
}

# The pwsh tripwire (spec §5.1). D is resolved with no override: a slot in a private directory never passes.
function Assert-HeavySlotHeld {
    param([string]$Tool, [switch]$Db)
    $reason = ""
    if (-not $script:HeavyOnWindows -and (Test-Path -LiteralPath '/.dockerenv')) {
        $v = $env:ASSETOPS_HEAVY_SLOT_CONTAINER
        if ($v -eq 'db') { }
        elseif ($v -eq 'slot') { if ($Db) { $reason = "a database job needs --db on the outermost wrapper" } }
        else { $reason = "in a container without ASSETOPS_HEAVY_SLOT_CONTAINER" }
    } else {
        $dir = Resolve-HeavySlotDir $PSScriptRoot $false $true
        $test = Test-HeavyMarker $env:ASSETOPS_HEAVY_SLOT $dir 'slot'
        if (-not $test.Ok) { $reason = $test.Reason }
        elseif ($Db -and -not (Test-HeavyMarker $env:ASSETOPS_HEAVY_DB $dir 'db').Ok) { $reason = "a database job needs --db on the outermost wrapper" }
    }
    if ($reason) {
        [Console]::Error.WriteLine((Get-HeavyRefusal $Tool $reason $Db.IsPresent))
        exit 69
    }
}

# The marker for a container runner: `db` when ASSETOPS_HEAVY_DB passes the marker test, otherwise `slot` (§5.3).
function Get-HeavyContainerMarker {
    $dir = Resolve-HeavySlotDir $PSScriptRoot $false $true
    if ((Test-HeavyMarker $env:ASSETOPS_HEAVY_DB $dir 'db').Ok) { return 'db' }
    return 'slot'
}

# -Status lines (I12c): slot-1, slot-2 and db-job always, plus any other slot-N.lock present.
function Get-HeavySlotStatus([string]$SlotDir) {
    $names = [System.Collections.Generic.List[string]]::new()
    foreach ($n in @('slot-1', 'slot-2')) { $names.Add($n) }
    foreach ($f in @(Get-ChildItem -LiteralPath $SlotDir -Filter 'slot-*.lock' -File -ErrorAction SilentlyContinue | Sort-Object Name)) {
        $n = [IO.Path]::GetFileNameWithoutExtension($f.Name)
        if (-not $names.Contains($n)) { $names.Add($n) }
    }
    $names.Add('db-job')
    foreach ($n in $names) {
        $lock = [IO.Path]::Combine($SlotDir, "$n.lock")
        if (-not (Test-HeavyLockHeld $lock)) { "${n}: free"; continue }
        $o = Read-HeavyOwner $lock
        $holder = 0
        if ($o.ContainsKey('pid') -and [int]::TryParse($o['pid'], [ref]$holder) -and (Test-HeavyPidAlive $holder)) {
            "${n}: busy pid=$($o['pid']) child=$($o['child']) label=$($o['label']) since=$($o['since']) cwd=$($o['cwd'])"
        } else {
            "${n}: busy, holder unknown (owner file stale); find it with: fuser -v $lock"
        }
    }
}
