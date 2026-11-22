# T1: the heavy-tool slot pool, pwsh half (specs/T1-heavy-tool-slot-pool/spec.md §2, §3.1, §5.1).
#
# Dot-sourced by tools/check-all.ps1, tools/heavy-slot.ps1 and the container test runners. Not an architecture
# module: tools/check-architecture.ps1 skips every `_*.ps1` in tools/checks.
#
# The pool is two exclusive flock(2) locks, slot-1.lock and slot-2.lock, in D = <git common dir>/check-all-slots
# (canonical), plus db-job.lock and db-job-b.lock, the two database lanes (T1b, spec-T1b.md §2): a heavy database job
# (-Db) holds both, a focused Postgres test run (-DbLane) the first free one. .NET's FileShare.None open is that flock
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
    $pattern = switch ($Name) { 'db' { '^db-job\.lock$' } 'dbb' { '^db-job-b\.lock$' } 'lane' { '^db-job(-b)?\.lock$' } default { '^slot-[12]\.lock$' } }
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

# T1b §2: exclusive passes when both -Db markers pass; the lane is 'a' (exclusive, or db-job.lock), 'b' or $null.
function Test-HeavyExclusive([string]$SlotDir) {
    return ((Test-HeavyMarker $env:ASSETOPS_HEAVY_DB $SlotDir 'db').Ok -and (Test-HeavyMarker $env:ASSETOPS_HEAVY_DB_B $SlotDir 'dbb').Ok)
}

function Get-HeavyLane([string]$SlotDir) {
    if (Test-HeavyExclusive $SlotDir) { return 'a' }
    if ((Test-HeavyMarker $env:ASSETOPS_HEAVY_DB_LANE $SlotDir 'lane').Ok) {
        if ([IO.Path]::GetFileName($env:ASSETOPS_HEAVY_DB_LANE) -eq 'db-job-b.lock') { return 'b' }
        return 'a'
    }
    return $null
}

function Assert-HeavySlotLocking {
    if ($env:DOTNET_SYSTEM_IO_DISABLEFILELOCKING) {
        [Console]::Error.WriteLine("heavy-slot: refused: DOTNET_SYSTEM_IO_DISABLEFILELOCKING is set; the slot locks would not hold.")
        exit 69
    }
}

# $DbWord: yes (-Db), lane (-DbLane) or no.
function Write-HeavyOwner([string]$LockPath, [string]$Label, [string]$DbWord) {
    $since = [DateTime]::UtcNow.ToString('s') + 'Z'
    $text = "pid=$PID`nlabel=$Label`nsince=$since`ncwd=$($PWD.ProviderPath)`ndb=$DbWord`n"
    try { [IO.File]::WriteAllText((Get-HeavyOwnerPath $LockPath), $text) } catch { }
}

# After the wrapper starts its child: one more owner field (appended, so a reader never sees an empty file).
function Add-HeavyOwnerChild($Handle, [int]$ChildPid) {
    if (-not $Handle -or $Handle.Nested) { return }
    foreach ($lock in @($Handle.SlotPath, $Handle.DbPath, $Handle.DbBPath, $Handle.LanePath)) {
        if ($lock) { try { [IO.File]::AppendAllText((Get-HeavyOwnerPath $lock), "child=$ChildPid`n") } catch { } }
    }
}

function Enter-HeavySlot {
    param(
        [string]$SlotDir,
        [int]$Slots = 2,
        [int]$WaitSeconds,
        [switch]$Db,
        [switch]$DbLane,
        [string]$Label = "",
        [string]$Announce = "",
        # Where -Announce goes: check-all keeps its host line; the wrappers write to stderr.
        [ValidateSet('Host', 'Error')][string]$AnnounceTo = 'Host'
    )
    if ($Db -and $DbLane) { [Console]::Error.WriteLine("heavy-slot: --db and --db-lane are exclusive; give one."); exit 64 }
    if ($Slots -gt 2) { [Console]::Error.WriteLine("heavy-slot: the shared pool has 2 slots (T1)"); exit 64 }
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $marker = $env:ASSETOPS_HEAVY_SLOT
    if ($marker) {
        $test = Test-HeavyMarker $marker $SlotDir 'slot'
        if ($test.Ok) {
            if ($Db -and -not (Test-HeavyExclusive $SlotDir)) {
                [Console]::Error.WriteLine("heavy-slot: refused: --db inside a held slot; put --db on the outermost wrapper.")
                exit 69
            }
            if ($DbLane -and -not (Get-HeavyLane $SlotDir)) {
                [Console]::Error.WriteLine("heavy-slot: refused: --db-lane inside a held slot; put --db-lane on the outermost wrapper.")
                exit 69
            }
            return @{ Nested = $true; SlotPath = $marker; SlotStream = $null
                      DbPath = $(if ($Db) { $env:ASSETOPS_HEAVY_DB } else { $null }); DbStream = $null
                      DbBPath = $(if ($Db) { $env:ASSETOPS_HEAVY_DB_B } else { $null }); DbBStream = $null
                      LanePath = $(if ($DbLane) { $env:ASSETOPS_HEAVY_DB_LANE } else { $null }); LaneStream = $null
                      WaitedSeconds = 0.0 }
        }
        [Console]::Error.WriteLine("heavy-slot: ignoring stale ASSETOPS_HEAVY_SLOT=$marker ($($test.Reason))")
    }
    $dbPath = [IO.Path]::Combine($SlotDir, "db-job.lock")
    $dbbPath = [IO.Path]::Combine($SlotDir, "db-job-b.lock")
    $dbStream = $null
    $dbbStream = $null
    $laneStream = $null
    $lanePath = $null
    $slotStream = $null
    $slotPath = $null
    $saidDb = $false
    $saidDbB = $false
    $saidLanes = $false
    $saidSlot = $false
    while ($true) {
        # Order (T1b §2): -Db takes lane a, then lane b; -DbLane the first free lane; then the lowest free slot.
        if ($Db -and -not $dbStream) {
            try { $dbStream = [IO.File]::Open($dbPath, 'OpenOrCreate', 'ReadWrite', 'None') } catch [System.IO.IOException] { }
        }
        if ($Db -and $dbStream -and -not $dbbStream) {
            try { $dbbStream = [IO.File]::Open($dbbPath, 'OpenOrCreate', 'ReadWrite', 'None') } catch [System.IO.IOException] { }
        }
        if ($DbLane -and -not $laneStream) {
            foreach ($candidate in @($dbPath, $dbbPath)) {
                if ($laneStream) { break }
                try { $laneStream = [IO.File]::Open($candidate, 'OpenOrCreate', 'ReadWrite', 'None'); $lanePath = $candidate }
                catch [System.IO.IOException] { }
            }
        }
        if ((-not $Db -or $dbbStream) -and (-not $DbLane -or $laneStream)) {
            for ($i = 1; $i -le $Slots -and -not $slotStream; $i++) {
                $candidate = [IO.Path]::Combine($SlotDir, "slot-$i.lock")
                try { $slotStream = [IO.File]::Open($candidate, 'OpenOrCreate', 'ReadWrite', 'None'); $slotPath = $candidate }
                catch [System.IO.IOException] { }
            }
        }
        if ($slotStream) { break }
        $left = $WaitSeconds - $clock.Elapsed.TotalSeconds
        if ($left -le 0) {
            foreach ($held in @($dbStream, $dbbStream, $laneStream)) { if ($held) { $held.Dispose() } }
            return $null
        }
        if ($Db -and -not $dbStream) {
            if (-not $saidDb) { [Console]::Error.WriteLine("heavy-slot: another database job holds db-job.lock; waiting up to $WaitSeconds s."); $saidDb = $true }
        } elseif ($Db -and -not $dbbStream) {
            if (-not $saidDbB) { [Console]::Error.WriteLine("heavy-slot: another database job holds db-job-b.lock; waiting up to $WaitSeconds s."); $saidDbB = $true }
        } elseif ($DbLane -and -not $laneStream) {
            if (-not $saidLanes) { [Console]::Error.WriteLine("heavy-slot: both database lanes are busy (tools/heavy-slot.sh --status); waiting up to $WaitSeconds s."); $saidLanes = $true }
        } elseif (-not $saidSlot -and $Announce) {
            if ($AnnounceTo -eq 'Error') { [Console]::Error.WriteLine($Announce) } else { Write-Host $Announce }
            $saidSlot = $true
        }
        Start-Sleep -Milliseconds ([int][Math]::Min(2000, [Math]::Ceiling($left * 1000)))
    }
    $word = if ($Db) { 'yes' } elseif ($DbLane) { 'lane' } else { 'no' }
    Write-HeavyOwner $slotPath $Label $word
    if ($dbStream) { Write-HeavyOwner $dbPath $Label $word; Write-HeavyOwner $dbbPath $Label $word }
    if ($laneStream) { Write-HeavyOwner $lanePath $Label $word }
    return @{ Nested = $false; SlotPath = $slotPath; SlotStream = $slotStream
              DbPath = $(if ($dbStream) { $dbPath } else { $null }); DbStream = $dbStream
              DbBPath = $(if ($dbbStream) { $dbbPath } else { $null }); DbBStream = $dbbStream
              LanePath = $lanePath; LaneStream = $laneStream; WaitedSeconds = $clock.Elapsed.TotalSeconds }
}

function Exit-HeavySlot($Handle) {
    if (-not $Handle) { return }
    foreach ($pair in @(@($Handle.SlotPath, $Handle.SlotStream), @($Handle.DbPath, $Handle.DbStream),
                        @($Handle.DbBPath, $Handle.DbBStream), @($Handle.LanePath, $Handle.LaneStream))) {
        if (-not $pair[1]) { continue }
        $owner = Read-HeavyOwner $pair[0]
        if ($owner['pid'] -eq "$PID") { try { [IO.File]::Delete((Get-HeavyOwnerPath $pair[0])) } catch { } }
        $pair[1].Dispose()
    }
    $Handle.SlotStream = $null
    $Handle.DbStream = $null
    $Handle.DbBStream = $null
    $Handle.LaneStream = $null
}

# $Mode: '' (a slot), 'db' (--db) or 'lane' (--db-lane).
function Get-HeavyRefusal([string]$Tool, [string]$Reason, [string]$Mode) {
    $sh = switch ($Mode) { 'db' { "--db " } 'lane' { "--db-lane " } default { "" } }
    $ps = switch ($Mode) { 'db' { "-Db " } 'lane' { "-DbLane " } default { "" } }
    return "heavy-slot: refused: $Tool runs only inside the heavy-tool slot pool ($Reason).`n" +
        "Run it as: tools/heavy-slot.sh $($sh)-- <your command>   (from frontend/: ../tools/heavy-slot.sh; pwsh: pwsh -NoProfile -File tools/heavy-slot.ps1 $($ps)-- ...)`n" +
        "RULES §7 (T1)."
}

# The pwsh tripwire (spec §5.1). D is resolved with no override: a slot in a private directory never passes.
function Assert-HeavySlotHeld {
    param([string]$Tool, [switch]$Db, [switch]$DbLane)
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
        elseif ($Db -and -not (Test-HeavyExclusive $dir)) { $reason = "a database job needs --db on the outermost wrapper" }
        elseif ($DbLane -and -not (Get-HeavyLane $dir)) { $reason = "a Postgres test run needs --db-lane (or --db) on the outermost wrapper" }
    }
    if ($reason) {
        $mode = if ($Db) { 'db' } elseif ($DbLane) { 'lane' } else { '' }
        [Console]::Error.WriteLine((Get-HeavyRefusal $Tool $reason $mode))
        exit 69
    }
}

# The marker for a container runner: `db` when exclusive passes (both -Db markers, T1b §2), otherwise `slot` (§5.3).
function Get-HeavyContainerMarker {
    $dir = Resolve-HeavySlotDir $PSScriptRoot $false $true
    if (Test-HeavyExclusive $dir) { return 'db' }
    return 'slot'
}

# -Status lines (I12c): slot-1, slot-2, any other slot-N.lock present, then db-job and db-job-b always.
function Get-HeavySlotStatus([string]$SlotDir) {
    $names = [System.Collections.Generic.List[string]]::new()
    foreach ($n in @('slot-1', 'slot-2')) { $names.Add($n) }
    foreach ($f in @(Get-ChildItem -LiteralPath $SlotDir -Filter 'slot-*.lock' -File -ErrorAction SilentlyContinue | Sort-Object Name)) {
        $n = [IO.Path]::GetFileNameWithoutExtension($f.Name)
        if (-not $names.Contains($n)) { $names.Add($n) }
    }
    $names.Add('db-job')
    $names.Add('db-job-b')
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
