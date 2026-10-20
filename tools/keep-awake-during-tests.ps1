# Keeps Windows from idle-sleeping while backend pytest runs are active.
# Uses SetThreadExecutionState (the same request a video player makes); it changes no power settings
# and is released when this script exits. It cannot stop sleep from a closed lid or the power button.
# ES_DISPLAY_REQUIRED is needed on Modern Standby machines: ES_SYSTEM_REQUIRED alone does not stop the
# display idle timeout, and display-off enters Modern Standby ("Reason: Idle Timeout", System event 506),
# which throttles the run while wall time advances (main-tick-cost: a 240 s tick budget ran out, 47 min suite).
# Exits after -IdleMinutes with no pytest process, or after -MaxHours.
# -WatchProcessId (OPS-03): also counts as active while that host process lives, because container pytest
# runs no host python.exe. tools/run-backend-suite-in-container.ps1 passes its own PID. Without it the
# behaviour is unchanged.
param([int]$IdleMinutes = 20, [int]$MaxHours = 12, [int]$WatchProcessId = 0)

Add-Type -Namespace Win32 -Name Power -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
'@
$ES_CONTINUOUS = [uint32]2147483648
$ES_SYSTEM_REQUIRED = [uint32]1
$ES_DISPLAY_REQUIRED = [uint32]2

$deadline = (Get-Date).AddHours($MaxHours)
$lastSeen = Get-Date
try {
    [void][Win32.Power]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_DISPLAY_REQUIRED)
    Write-Output "keep-awake on $(Get-Date -Format s)"
    while ((Get-Date) -lt $deadline) {
        $running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -match 'pytest' }
        if (-not $running -and $WatchProcessId -gt 0) {
            $running = Get-Process -Id $WatchProcessId -ErrorAction SilentlyContinue
        }
        if ($running) { $lastSeen = Get-Date }
        elseif (((Get-Date) - $lastSeen).TotalMinutes -ge $IdleMinutes) { break }
        Start-Sleep -Seconds 60
    }
} finally {
    [void][Win32.Power]::SetThreadExecutionState($ES_CONTINUOUS)
    Write-Output "keep-awake off $(Get-Date -Format s)"
}
