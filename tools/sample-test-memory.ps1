# PERF-01 (phase 0, R10): memory sampler for a backend test run.
#
# Started by tools/run-backend-suite-in-container.ps1 next to its connection sampler. Every -IntervalSeconds it
# appends one row to -OutFile:
#   win_free_mb        free Windows physical memory
#   vmmem_ws_mb        working set of the Docker/WSL VM process (vmmemWSL / vmmem) as Windows sees it
#   vm_used_mb         memory used inside the VM (MemTotal - MemAvailable, read from the database container)
#   vm_total_mb        the VM's memory size (the .wslconfig cap)
#   runner_mem_mb      the runner container's cgroup memory (pytest workers, gateway children, page cache)
#   pg_mem_mb          the database container's cgroup memory
#   runner_procs       processes with a resident set inside the runner
#   runner_rss_sum_mb  summed resident set of those processes
#   runner_rss_max_mb  the largest single process
# PERF-01 CPU columns (rates over the interval since the previous sample):
#   host_cpu_pct       Windows total processor time (includes the VM)
#   vm_cpu_pct         VM busy share of all its CPUs (/proc/stat, read in the database container: not namespaced)
#   vm_iowait_pct      VM iowait share
#   vm_cpus            CPUs the VM has
#   runner_cpu_cores   runner container CPU use in cores (cgroup cpu.stat usage_usec)
#   pg_cpu_cores       database container CPU use in cores
# The sh scripts hold no double quotes: Windows PowerShell 5.1 strips them from native arguments.
# It reads only; it starts nothing in the containers and changes no setting. It exits when -WatchProcessId exits.
param(
    [Parameter(Mandatory = $true)][string]$OutFile,
    [Parameter(Mandatory = $true)][string]$RunnerContainer,
    [Parameter(Mandatory = $true)][string]$PgContainer,
    [int]$WatchProcessId = 0,
    [int]$IntervalSeconds = 5
)
$ErrorActionPreference = 'Continue'

function Read-Lines([string]$container, [string]$script) {
    $out = & docker exec $container sh -c $script 2>$null
    if ($LASTEXITCODE -ne 0) { return @() }
    return @($out)
}

function To-Mb([string]$bytes) {
    $value = 0L
    if ([long]::TryParse(($bytes -as [string]).Trim(), [ref]$value)) { return [int]($value / 1MB) }
    return ''
}

('utc,win_free_mb,vmmem_ws_mb,vm_used_mb,vm_total_mb,runner_mem_mb,pg_mem_mb,runner_procs,runner_rss_sum_mb,' +
    'runner_rss_max_mb,host_cpu_pct,vm_cpu_pct,vm_iowait_pct,vm_cpus,runner_cpu_cores,pg_cpu_cores') |
    Out-File $OutFile -Encoding ascii

$prev = $null
while ($true) {
    $now = [DateTime]::UtcNow
    if ($WatchProcessId -gt 0 -and -not (Get-Process -Id $WatchProcessId -ErrorAction SilentlyContinue)) { break }

    $os = Get-CimInstance Win32_OperatingSystem
    $winFree = [int]($os.FreePhysicalMemory / 1024)
    $vmmem = Get-Process -Name 'vmmemWSL', 'vmmem' -ErrorAction SilentlyContinue | Select-Object -First 1
    $vmmemWs = if ($vmmem) { [int]($vmmem.WorkingSet64 / 1MB) } else { '' }

    $vmUsed = ''; $vmTotal = ''; $pgMem = ''
    $pg = Read-Lines $PgContainer ('cat /sys/fs/cgroup/memory.current; grep -e ^MemTotal: -e ^MemAvailable: /proc/meminfo; ' +
        'head -1 /proc/stat; grep ^usage_usec /sys/fs/cgroup/cpu.stat; grep -c ^processor /proc/cpuinfo')
    $vmStat = $null; $pgUsage = $null; $vmCpus = ''
    if ($pg.Count -ge 6) {
        $vmStat = @((($pg[3] -split '\s+') | Select-Object -Skip 1) | ForEach-Object { [long]$_ })
        $pgUsage = [long](($pg[4] -split '\s+')[1]); $vmCpus = [int]$pg[5]
    }
    if ($pg.Count -ge 3) {
        $pgMem = To-Mb $pg[0]
        $total = [long](($pg[1] -split '\s+')[1]); $avail = [long](($pg[2] -split '\s+')[1])
        $vmTotal = [int]($total / 1024); $vmUsed = [int](($total - $avail) / 1024)
    }

    $runnerMem = ''; $procs = ''; $rssSum = ''; $rssMax = ''
    $runner = Read-Lines $RunnerContainer ('cat /sys/fs/cgroup/memory.current; grep ^usage_usec /sys/fs/cgroup/cpu.stat; ' +
        'cat /proc/[0-9]*/status 2>/dev/null | grep ^VmRSS:')
    $runnerUsage = $null
    if ($runner.Count -ge 1) {
        $runnerMem = To-Mb $runner[0]
        $usageLine = @($runner | Where-Object { $_ -like 'usage_usec*' }) | Select-Object -First 1
        if ($usageLine) { $runnerUsage = [long](($usageLine -split '\s+')[1]) }
        $rss = @($runner | Where-Object { $_ -like 'VmRSS:*' } | ForEach-Object { [long](($_ -split '\s+')[1]) })
        $procs = $rss.Count
        if ($rss.Count -gt 0) {
            $m = $rss | Measure-Object -Sum -Maximum
            $rssSum = [int]($m.Sum / 1024); $rssMax = [int]($m.Maximum / 1024)
        }
    }

    $hostCpu = ''
    try {
        $hostCpu = (Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'").PercentProcessorTime
    } catch { }
    $vmCpu = ''; $vmIo = ''; $runnerCores = ''; $pgCores = ''
    if ($prev) {
        $seconds = ($now - $prev.Time).TotalSeconds
        if ($vmStat -and $prev.VmStat) {
            $d = @(for ($i = 0; $i -lt [math]::Min($vmStat.Count, 8); $i++) { $vmStat[$i] - $prev.VmStat[$i] })
            $sum = ($d | Measure-Object -Sum).Sum
            if ($sum -gt 0) {
                $vmCpu = [math]::Round(100 * (1 - ($d[3] + $d[4]) / $sum), 1); $vmIo = [math]::Round(100 * $d[4] / $sum, 1)
            }
        }
        if ($seconds -gt 0 -and $null -ne $runnerUsage -and $null -ne $prev.Runner -and $runnerUsage -ge $prev.Runner) {
            $runnerCores = [math]::Round(($runnerUsage - $prev.Runner) / 1e6 / $seconds, 2)
        }
        if ($seconds -gt 0 -and $null -ne $pgUsage -and $null -ne $prev.Pg) {
            $pgCores = [math]::Round(($pgUsage - $prev.Pg) / 1e6 / $seconds, 2)
        }
    }
    $prev = @{ Time = $now; VmStat = $vmStat; Runner = $runnerUsage; Pg = $pgUsage }
    ("$($now.ToString('s')),$winFree,$vmmemWs,$vmUsed,$vmTotal,$runnerMem,$pgMem,$procs,$rssSum,$rssMax," +
        "$hostCpu,$vmCpu,$vmIo,$vmCpus,$runnerCores,$pgCores") | Out-File $OutFile -Append -Encoding ascii
    Start-Sleep -Seconds $IntervalSeconds
}
