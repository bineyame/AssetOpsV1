# Seam: Mockup fidelity versus product honesty (navigation half).
#
# A navigation destination appears only when the route behind it renders a
# truthful surface. A site is addressed by `site_id`, so the parameterless
# `/site-details` placeholder is gone and the identified route replaced it.
#
# Do not weaken the checks below to make a task pass.

function Invoke-NavigationTruthfulnessCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    # This is a pair of assertions on purpose: a lone "the placeholder is
    # absent" check would also pass on a tree where nothing addresses a site at
    # all, so the identified route has to be found for the absence to mean
    # anything - the route parameter is what is looked for, because the path
    # itself is built from the Sites path constant rather than spelled out.
    #
    # `/site-configuration` is deliberately NOT checked here. It is still a
    # parameterless placeholder and is removed by the slice that gives it an
    # identified replacement; adding it now would fail the build for a route
    # that slice does not replace.
    $identifiedSiteRoutePath = 0

    foreach ($module in (Get-ScannedModules -Root "frontend/src" -Extensions @(".ts", ".tsx"))) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            if ($line -match '["'']/site-details') {
                $failures.Add(("Parameterless site destination at " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). A site is " +
                    "addressed by site_id; a Site Details link that names no " +
                    "site is not a destination.")) | Out-Null
            }

            if ($line -match '/:siteId') {
                $identifiedSiteRoutePath++
            }
        }
    }

    if ($identifiedSiteRoutePath -eq 0) {
        $failures.Add(("No identified site route was found in frontend/src, so " +
            "the navigation-truthfulness check is vacuous. Update the check, " +
            "do not delete it.")) | Out-Null
    }

    return $failures
}
