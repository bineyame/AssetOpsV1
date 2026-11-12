# Seam: Site links carry the shared range (SR-4a; architect rev 8 §8.2, D-SR.2).
#
# The shared date range lives in the address. A Site page opened from a link that drops it shows its own day (the
# 2026-11-12 verifier found 0/9 to 0/15 Kobo/Kisiwa tab links carrying it). Every link in the app therefore goes
# through `frontend/src/ui/RangeLink.tsx`, which adds the address's range to every Site target (`carryRange`).
#
# What fails: a non-test `.tsx` under `frontend/src` that imports or re-exports `Link` or `NavLink` (aliased or not,
# either quote style) from `react-router-dom`, or imports the module as a namespace. Import `RangeLink` from `ui/RangeLink` instead (`import { RangeLink as Link } ...` is allowed).
# Exempt: `ui/RangeLink.tsx` itself, and the rail (`ui/NavRail.tsx`, `shell/OperatorShellLayout.tsx`), which already
# carries the range through `railSearch`.
#
# The runtime second guard is `frontend/src/shell/__tests__/siteRangeCarry.test.tsx` (every Site href in the DOM).
# The self-test at the bottom fails the seam if the scanner would pass a violating file or fail an exempt or aliased one.
#
# Do not weaken this check to make a task pass: import RangeLink instead.

function Get-RouterLinkImportCount {
    param([string]$Text)
    $count = 0
    # SR-4ab L-2: double- or single-quoted; `import { ... }` and `export { ... } from` (re-exports); a namespace import
    # (`import * as R`) counts once, since `R.Link` cannot be told from other members cheaply.
    $count += [regex]::Matches($Text, 'import\s*\*\s*as\s+\w+\s+from\s*["'']react-router-dom["'']').Count
    foreach ($m in [regex]::Matches($Text, '(?s)(?:import|export)\s*\{([^}]*)\}\s*from\s*["'']react-router-dom["'']')) {
        foreach ($spec in ($m.Groups[1].Value -split ',')) {
            $name = ($spec.Trim() -split '\s+')[0]
            if ($name -eq 'type') { $name = ($spec.Trim() -split '\s+')[1] }
            if ($name -eq 'Link' -or $name -eq 'NavLink') { $count++ }
        }
    }
    return $count
}

function Get-SiteLinkCarryFailures {
    param(
        [hashtable]$Files,      # relative path -> text
        [string[]]$Exempt
    )
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($path in ($Files.Keys | Sort-Object)) {
        if ($Exempt -contains $path) { continue }
        $count = Get-RouterLinkImportCount -Text $Files[$path]
        if ($count -gt 0) {
            $out.Add("$path imports Link/NavLink from react-router-dom ($count). Import RangeLink from ui/RangeLink (``import { RangeLink as Link } from ""../ui/RangeLink""``) so Site links carry the shared range.")
        }
    }
    return $out
}

function Invoke-SiteLinksCarryRangeCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $exempt = @(
        "frontend/src/ui/RangeLink.tsx",
        "frontend/src/ui/NavRail.tsx",
        "frontend/src/shell/OperatorShellLayout.tsx"
    )

    $root = (Get-Location).Path
    $files = @{}
    Get-ChildItem -LiteralPath (Join-Path $root "frontend/src") -Recurse -Filter "*.tsx" -File |
        Where-Object { $_.FullName -notmatch '[\\/]__tests__[\\/]' -and $_.Name -notmatch '\.test\.tsx$' } |
        ForEach-Object {
            $rel = $_.FullName.Substring($root.Length + 1).Replace('\', '/')
            $files[$rel] = [System.IO.File]::ReadAllText($_.FullName)
        }
    if ($files.Count -eq 0) { $failures.Add("site-links-carry-range: no .tsx files found under frontend/src; the scan is vacuous.") }
    foreach ($f in (Get-SiteLinkCarryFailures -Files $files -Exempt $exempt)) { $failures.Add($f) }

    # Self-test: a plain Link import fails, an aliased router Link fails, a multi-line NavLink import fails; the exempt
    # file passes; `RangeLink as Link` from ui/RangeLink passes; a router import without Link passes.
    $fixtures = @{
        "frontend/src/shell/operatorSiteTabs.tsx" = 'import { Link } from "react-router-dom";'
        "frontend/src/sites/Aliased.tsx"          = 'import { Link as RouterLink, useSearchParams } from "react-router-dom";'
        "frontend/src/sites/Multi.tsx"            = "import {`n  NavLink,`n  useParams,`n} from ""react-router-dom"";"
        "frontend/src/ui/RangeLink.tsx"           = 'import { Link, useSearchParams, type LinkProps } from "react-router-dom";'
        "frontend/src/sites/Carried.tsx"          = "import { useSearchParams } from ""react-router-dom"";`nimport { RangeLink as Link } from ""../ui/RangeLink"";"
        "frontend/src/sites/Single.tsx"           = "import { Link } from 'react-router-dom';"
        "frontend/src/sites/Star.tsx"             = "import * as Router from 'react-router-dom';"
        "frontend/src/sites/ReExport.tsx"         = 'export { NavLink } from "react-router-dom";'
    }
    $got = @(Get-SiteLinkCarryFailures -Files $fixtures -Exempt @("frontend/src/ui/RangeLink.tsx"))
    $expect = @("frontend/src/shell/operatorSiteTabs.tsx", "frontend/src/sites/Aliased.tsx", "frontend/src/sites/Multi.tsx",
        "frontend/src/sites/ReExport.tsx", "frontend/src/sites/Single.tsx", "frontend/src/sites/Star.tsx")
    $flagged = @($got | ForEach-Object { ($_ -split ' ')[0] } | Sort-Object)
    if (($flagged -join ",") -ne ($expect -join ",")) {
        $failures.Add("site-links-carry-range self-test: expected failures for $($expect -join ', '), got: $($flagged -join ', ')")
    }

    return $failures
}
