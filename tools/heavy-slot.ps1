# T1: run one heavy command inside the heavy-tool slot pool (specs/T1-heavy-tool-slot-pool/spec.md §3.2).
#
#   pwsh -NoProfile -File tools/heavy-slot.ps1 [-Db] [-SlotWaitSeconds <n>] [-Label <text>] -- <command> [args...]
#   pwsh -NoProfile -File tools/heavy-slot.ps1 -Status
#
# Only the `pwsh -NoProfile -File` form is supported (I3). pwsh splits a `-name:value` argument into two, so give a
# wrapped command `--name=value` forms. Options are read only before the first `--`.
#
# Exit codes: the child's when the command ran; 64 usage; 69 refused; 75 no slot came free. A child that itself exits
# 64, 69 or 75 is told apart only by this wrapper's stderr line (R20).
#
# No param() block on purpose (as tools/run-host-tests.ps1): a plain script gets `--` and every option verbatim.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'checks/_heavy_slot.ps1')

$usage = "usage: pwsh -NoProfile -File tools/heavy-slot.ps1 [-Db] [-SlotWaitSeconds <n>] [-Label <text>] -- <command> [args...]`n" +
         "       pwsh -NoProfile -File tools/heavy-slot.ps1 -Status"
function Exit-Usage([string]$why) {
    if ($why) { [Console]::Error.WriteLine("heavy-slot: $why") }
    [Console]::Error.WriteLine($usage)
    exit 64
}

$db = $false
$wait = 1200
$label = $null
$status = $false
$command = $null
$all = @($args)
for ($i = 0; $i -lt $all.Count; $i++) {
    $a = [string]$all[$i]
    if ($a -eq '--') { $command = @($all | Select-Object -Skip ($i + 1)); break }
    elseif ($a -ieq '-Db') { $db = $true }
    elseif ($a -ieq '-Status') { $status = $true }
    elseif ($a -ieq '-SlotWaitSeconds') {
        $n = 0
        if ($i + 1 -ge $all.Count -or -not [int]::TryParse([string]$all[$i + 1], [ref]$n) -or $n -lt 0) { Exit-Usage "-SlotWaitSeconds needs a whole number of seconds." }
        $wait = $n; $i++
    }
    elseif ($a -ieq '-Label') {
        if ($i + 1 -ge $all.Count) { Exit-Usage "-Label needs a text." }
        $label = [string]$all[++$i]
    }
    else { Exit-Usage "unknown option '$a' (a command goes after --)." }
}

Assert-HeavySlotLocking
$slotDir = Get-HeavySlotDir $PSScriptRoot

if ($status) {
    Get-HeavySlotStatus $slotDir | ForEach-Object { [Console]::Out.WriteLine($_) }
    exit 0
}
if ($null -eq $command) { Exit-Usage "missing -- before the command." }
if ($command.Count -eq 0) { Exit-Usage "no command after --." }
$first = [string]$command[0]
if ($first -eq 'setsid') { Exit-Usage "put setsid/nohup before the wrapper." }

# The label: the first two words of the command, on one line, `=` made a space (I12e).
if (-not $label) { $label = (@($command | Select-Object -First 2) -join ' ') }
$label = ($label -replace "[`r`n=]", ' ').Trim()

# Resolve the child before taking a slot.
$rest = @($command | Select-Object -Skip 1)
if ($first -like '*.ps1' -and (Test-Path -LiteralPath $first -PathType Leaf)) {
    $file = (Get-Process -Id $PID).Path
    $childArgs = @('-NoProfile', '-File', $first) + $rest
} else {
    $found = Get-Command $first -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found) { [Console]::Error.WriteLine("heavy-slot: command not found: $first"); exit 127 }
    $file = $found.Source
    $childArgs = $rest
}

# TERM, HUP and INT: kill the child's tree, drop this process's owner files, exit 128+signal (I12b).
if ($PSVersionTable.PSVersion.Major -ge 7 -and ("System.Runtime.InteropServices.PosixSignalRegistration" -as [type])) {
    if (-not ("HeavySlotReaper" -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
public static class HeavySlotReaper {
    static volatile Process child;
    static string[] owners = new string[0];
    static PosixSignalRegistration term, hup, intr;
    public static void SetChild(Process p) { child = p; }
    public static void SetOwners(string[] paths) { owners = paths ?? new string[0]; }
    static void Collect(int pid, System.Collections.Generic.List<int> acc) {
        acc.Add(pid);
        try {
            foreach (var t in Directory.GetDirectories("/proc/" + pid + "/task")) {
                string f = Path.Combine(t, "children");
                if (!File.Exists(f)) continue;
                foreach (var c in File.ReadAllText(f).Split(new[] { ' ', '\n' }, StringSplitOptions.RemoveEmptyEntries)) {
                    int k; if (int.TryParse(c, out k)) Collect(k, acc);
                }
            }
        } catch { }
    }
    static void Signal(string sig, System.Collections.Generic.List<int> pids) {
        if (pids.Count == 0) return;
        var psi = new ProcessStartInfo("kill");
        psi.ArgumentList.Add("-" + sig);
        foreach (var k in pids) psi.ArgumentList.Add(k.ToString());
        psi.RedirectStandardError = true;
        using (var kp = Process.Start(psi)) { kp.WaitForExit(2000); }
    }
    static bool Alive(int pid) { return Directory.Exists("/proc/" + pid) && !File.ReadAllText("/proc/" + pid + "/stat").Contains(") Z"); }
    static void Stop(PosixSignalContext ctx, int code) {
        ctx.Cancel = true;
        Process p = child;
        // As heavy-slot.sh: TERM the tree, wait up to 5 s, then KILL what is left.
        var tree = new System.Collections.Generic.List<int>();
        try { if (p != null && !p.HasExited) { Collect(p.Id, tree); Signal("TERM", tree); } } catch { }
        try {
            var until = DateTime.UtcNow.AddSeconds(5);
            while (DateTime.UtcNow < until && tree.Exists(x => { try { return Alive(x); } catch { return false; } })) System.Threading.Thread.Sleep(100);
        } catch { }
        try { Signal("KILL", tree.FindAll(x => { try { return Alive(x); } catch { return false; } })); } catch { }
        try { if (p != null && !p.HasExited) p.Kill(true); } catch { }
        foreach (var path in owners) {
            try { if (Array.IndexOf(File.ReadAllLines(path), "pid=" + Environment.ProcessId) >= 0) File.Delete(path); } catch { }
        }
        Environment.Exit(code);
    }
    public static void Register() {
        try { term = PosixSignalRegistration.Create(PosixSignal.SIGTERM, ctx => Stop(ctx, 143)); } catch { }
        try { hup = PosixSignalRegistration.Create(PosixSignal.SIGHUP, ctx => Stop(ctx, 129)); } catch { }
        try { intr = PosixSignalRegistration.Create(PosixSignal.SIGINT, ctx => Stop(ctx, 130)); } catch { }
    }
}
'@
    }
    [HeavySlotReaper]::Register()
    $reaper = $true
} else { $reaper = $false }

$handle = Enter-HeavySlot -SlotDir $slotDir -WaitSeconds $wait -Db:$db -Label $label -AnnounceTo Error `
    -Announce "heavy-slot: both heavy slots are busy (tools/heavy-slot.sh --status); waiting up to $wait s."
if (-not $handle) {
    [Console]::Error.WriteLine("heavy-slot: no slot came free in $wait s (-SlotWaitSeconds).")
    exit 75
}
$code = 1
try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $file
    foreach ($a in $childArgs) { $psi.ArgumentList.Add([string]$a) }
    $psi.UseShellExecute = $false
    $psi.WorkingDirectory = (Get-Location).Path
    if (-not $handle.Nested) {
        # The marker lives in the child's environment only.
        $psi.Environment['ASSETOPS_HEAVY_SLOT'] = $handle.SlotPath
        if ($handle.DbPath) { $psi.Environment['ASSETOPS_HEAVY_DB'] = $handle.DbPath }
        else { [void]$psi.Environment.Remove('ASSETOPS_HEAVY_DB') }
        if ($reaper) {
            [HeavySlotReaper]::SetOwners(@(@($handle.SlotPath, $handle.DbPath) | Where-Object { $_ } | ForEach-Object { Get-HeavyOwnerPath $_ }))
        }
    }
    $child = [System.Diagnostics.Process]::Start($psi)
    if ($reaper) { [HeavySlotReaper]::SetChild($child) }
    Add-HeavyOwnerChild $handle $child.Id
    $child.WaitForExit()
    $code = $child.ExitCode
}
finally {
    Exit-HeavySlot $handle
}
exit $code
