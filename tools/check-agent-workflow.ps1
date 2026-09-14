$ErrorActionPreference = "Stop"

$failures = New-Object System.Collections.Generic.List[string]

function Add-Failure($message) {
    $failures.Add($message) | Out-Null
}

function Require-File($path) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Add-Failure "Missing required file: $path"
    }
}

$requiredFiles = @(
    "AGENTS.md",
    ".ai/START_HERE.md",
    ".ai/ACTIVE_CONTEXT.md",
    ".ai/CODE_STATE.md",
    ".ai/PROJECT_RULES.md",
    ".ai/WORKFLOW.md",
    ".ai/PRODUCT.md",
    ".ai/ARCHITECTURE.md",
    ".ai/PLANNING_GUIDANCE.md",
    ".ai/ROLE_CONFIG.md",
    ".ai/DECISIONS.md",
    ".ai/ARTIFACT_INDEX.md",
    ".claude/commands/assetops-architect.md",
    ".claude/commands/assetops-planner.md",
    ".claude/commands/assetops-implementer.md",
    ".claude/agents/assetops-architect.md",
    ".claude/agents/assetops-planner.md",
    ".claude/agents/assetops-implementer.md",
    ".claude/skills/assetops-architect/SKILL.md",
    ".claude/skills/assetops-planner/SKILL.md",
    ".claude/skills/assetops-implementer/SKILL.md",
    "tools/check-agent-workflow.ps1"
)

foreach ($file in $requiredFiles) {
    Require-File $file
}

if (Test-Path -LiteralPath "AGENTS.md") {
    $agents = Get-Content -LiteralPath "AGENTS.md" -Raw
    if ($agents -notmatch [regex]::Escape(".ai/START_HERE.md")) {
        Add-Failure "AGENTS.md must point to .ai/START_HERE.md"
    }
}

if (Test-Path -LiteralPath ".ai/START_HERE.md") {
    $start = Get-Content -LiteralPath ".ai/START_HERE.md" -Raw
    if ($start -notmatch "Current milestone:" -or $start -notmatch "Planning status:") {
        Add-Failure ".ai/START_HERE.md must identify an active milestone and planning status"
    }
}

# Every agent reads .ai/ACTIVE_CONTEXT.md in full, so its growth is paid on
# every task. It was trimmed once and grew back to nearly four times the
# trimmed size in six slices, because per-slice records accumulated in it.
# Those belong in .ai/CODE_STATE.md, which is read one entry at a time.
#
# The cap is the file's own stated rule. Raising it is a decision to make
# deliberately, not a way to land a task.
$activeContextLineCap = 200

if (Test-Path -LiteralPath ".ai/ACTIVE_CONTEXT.md") {
    $activeContextLines = @(Get-Content -LiteralPath ".ai/ACTIVE_CONTEXT.md").Count
    if ($activeContextLines -gt $activeContextLineCap) {
        Add-Failure (".ai/ACTIVE_CONTEXT.md is $activeContextLines lines, over " +
            "its $activeContextLineCap-line cap. It is a routing document: move " +
            "per-slice records into .ai/CODE_STATE.md rather than raising the cap.")
    }
}

if (Test-Path -LiteralPath ".ai/PROJECT_RULES.md") {
    $rules = Get-Content -LiteralPath ".ai/PROJECT_RULES.md" -Raw
    foreach ($mode in @("Architect", "Planner", "Implementer", "Reviewer")) {
        if ($rules -notmatch $mode) {
            Add-Failure ".ai/PROJECT_RULES.md must preserve $mode as a default mode"
        }
    }
}

if (Test-Path -LiteralPath ".ai/ROLE_CONFIG.md") {
    $roleConfig = Get-Content -LiteralPath ".ai/ROLE_CONFIG.md" -Raw
    foreach ($required in @("Architect", "Planner", "Implementer", "Codex", "Claude")) {
        if ($roleConfig -notmatch $required) {
            Add-Failure ".ai/ROLE_CONFIG.md must include $required"
        }
    }
}

$claudeCommands = @(
    ".claude/commands/assetops-architect.md",
    ".claude/commands/assetops-planner.md",
    ".claude/commands/assetops-implementer.md"
)

foreach ($command in $claudeCommands) {
    if (Test-Path -LiteralPath $command) {
        $content = Get-Content -LiteralPath $command -Raw
        if ($content -notmatch [regex]::Escape(".ai/ROLE_CONFIG.md")) {
            Add-Failure "$command must read .ai/ROLE_CONFIG.md"
        }
    }
}

if (Test-Path -LiteralPath ".ai/PLANNING_GUIDANCE.md") {
    $planning = Get-Content -LiteralPath ".ai/PLANNING_GUIDANCE.md" -Raw
    if ($planning -notmatch "Feature Versus Task") {
        Add-Failure ".ai/PLANNING_GUIDANCE.md must define Feature Versus Task"
    }
    if ($planning -notmatch "A feature is" -or $planning -notmatch "A task is") {
        Add-Failure ".ai/PLANNING_GUIDANCE.md must distinguish features from tasks"
    }
}

$taskFiles = @()
if (Test-Path -LiteralPath "tasks") {
    $taskFiles = Get-ChildItem -LiteralPath "tasks" -Filter "T*.md" -File
}

$recognizedStates = @("planned", "active", "in_review", "completed", "blocked")
foreach ($task in $taskFiles) {
    $content = Get-Content -LiteralPath $task.FullName -Raw
    if ($content -notmatch "(?m)^Status:\s*(\w+)") {
        Add-Failure "$($task.Name) must declare Status"
    } elseif ($recognizedStates -notcontains $Matches[1]) {
        Add-Failure "$($task.Name) uses unrecognized Status: $($Matches[1])"
    }

    if ($content -notmatch "USER_REVIEW_REQUIRED:\s*(true|false)") {
        Add-Failure "$($task.Name) must declare USER_REVIEW_REQUIRED: true|false"
    }
}

$trackedAgentTask = git ls-files -- ".agent/current-task.yaml"
if ($trackedAgentTask) {
    Add-Failure ".agent/current-task.yaml must not be tracked"
}

$forbiddenFiles = @(
    "PM_GUIDE.md",
    "ARCHITECT_GUIDE.md",
    "IMPLEMENTER_GUIDE.md",
    "REVIEWER_GUIDE.md",
    "SPEC_PARTNER_GUIDE.md",
    "UI_UX_GUIDE.md"
)

foreach ($forbidden in $forbiddenFiles) {
    if (Test-Path -LiteralPath $forbidden) {
        Add-Failure "Unsupported default role guide introduced: $forbidden"
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Agent workflow check failed:"
    foreach ($failure in $failures) {
        Write-Host "- $failure"
    }
    exit 1
}

Write-Host "Agent workflow check passed."
