# Keeps Windows from idle-sleeping while backend pytest runs are active.
# Uses SetThreadExecutionState (the same request a video player makes); it changes no power settings
# and is released when this script exits. It cannot stop sleep from a closed lid or the power button.
# Exits after -IdleMinutes with no pytest process, or after -MaxHours.
param([int]$IdleMinutes = 20, [int]$MaxHours = 12)

Add-Type -Namespace Win32 -Name Power -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
'@
$ES_CONTINUOUS = [uint32]2147483648
$ES_SYSTEM_REQUIRED = [uint32]1

$deadline = (Get-Date).AddHours($MaxHours)
$lastSeen = Get-Date
try {
    [void][Win32.Power]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED)
    Write-Output "keep-awake on $(Get-Date -Format s)"
    while ((Get-Date) -lt $deadline) {
        $running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -match 'pytest' }
        if ($running) { $lastSeen = Get-Date }
        elseif (((Get-Date) - $lastSeen).TotalMinutes -ge $IdleMinutes) { break }
        Start-Sleep -Seconds 60
    }
} finally {
    [void][Win32.Power]::SetThreadExecutionState($ES_CONTINUOUS)
    Write-Output "keep-awake off $(Get-Date -Format s)"
}
