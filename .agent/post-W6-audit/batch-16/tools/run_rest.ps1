# Runs the remaining batch-16 phases sequentially, each against its W504 API port; prints the Vite PIDs started.
param([int]$OldVitePid)
$t = "C:\Users\assef\Bineyame\AssetOpsV1-review5\.agent\post-W6-audit\batch-16\tools"
$prev = $OldVitePid
foreach ($ph in @(@("zero",18602), @("worstcase",18603), @("links",18601), @("forbidden",18606), @("unavailable",18607))) {
  $out = & "$t\run_phase.ps1" -Phase $ph[0] -ApiPort $ph[1] -OldVitePid $prev
  $out
  $prev = [int](($out | Select-String "VITE_PID (\d+)").Matches[0].Groups[1].Value)
}
"LAST_VITE_PID $prev"
