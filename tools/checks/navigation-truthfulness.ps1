# Seam: Mockup fidelity versus product honesty (navigation half).
#
# A navigation destination appears only when the route behind it renders a
# truthful surface. A site is addressed by `site_id`, so the parameterless
# `/site-details` and `/site-configuration` placeholders are gone and the
# identified routes replaced them.
#
# Do not weaken the checks below to make a task pass.

function Invoke-NavigationTruthfulnessCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    # These are paired assertions on purpose: a lone "the placeholder is
    # absent" check would also pass on a tree where nothing addresses a site at
    # all, so the identified route has to be found for the absence to mean
    # anything - the route parameter is what is looked for, because the path
    # itself is built from the Sites path constant rather than spelled out.
    #
    # T008 removed `/site-configuration`, so it is banned here the same way.
    # Its identified replacement is looked for as a path built ON the site's
    # own address rather than beside it, which is the invariant worth holding:
    # a configuration that hangs off `${SITE_DETAIL_ROUTE_PATH}` cannot quietly
    # become a parameterless destination again, because it has nowhere to put
    # the identity it would have to drop.
    $identifiedSiteRoutePath = 0
    $identifiedSiteConfigurationRoutePath = 0

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

            if ($line -match '["'']/site-configuration') {
                $failures.Add(("Parameterless site destination at " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). A site is " +
                    "addressed by site_id; a Site Configuration link that names " +
                    "no site is not a destination.")) | Out-Null
            }

            if ($line -match '/:siteId') {
                $identifiedSiteRoutePath++
            }

            if ($line -match '\$\{SITE_DETAIL_ROUTE_PATH\}/configuration') {
                $identifiedSiteConfigurationRoutePath++
            }
        }
    }

    if ($identifiedSiteRoutePath -eq 0) {
        $failures.Add(("No identified site route was found in frontend/src, so " +
            "the navigation-truthfulness check is vacuous. Update the check, " +
            "do not delete it.")) | Out-Null
    }

    if ($identifiedSiteConfigurationRoutePath -eq 0) {
        $failures.Add(("No identified site configuration route was found in " +
            "frontend/src, so banning the parameterless one proves nothing. " +
            "A site's configuration is addressed under that site. Update the " +
            "check, do not delete it.")) | Out-Null
    }

    return $failures
}
