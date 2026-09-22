# Seam: Run setup inputs nothing may infer, and run identity allocation.
#
# Two rules, and both exist because the same criterion can be defeated by a
# single line somebody thought was helpful.
#
#   - cadence, simulator source identity and gateway publication identity are
#     resolved from the selected versioned profile or the run is BLOCKED. They
#     are never inferred from a site's provenance, from a device's name, or
#     from how a site was created. So the records they live in may be built in
#     one place, and that place cannot see a site at all.
#   - a run identity is allocated, never authored and never derived. So the
#     identity prefix is spelled in one module, and one caller allocates.
#
# Why the ban is on the IMPORT rather than on the words. A scan for
# `display_name` or `source.mode` inside the run package would collide with the
# run's own fields - a run has a lifecycle status too, and a profile has a name
# a screen shows - and a ban with exceptions is a ban somebody widens. What has
# no legitimate use in the modules below is the Site record family itself:
# `assetops_backend.sites.models` is where a name, a source mode, a
# configuration origin, a lifecycle status and a device all live, and a module
# that cannot import it cannot read one however it is spelled.
#
# The run setup service does import that module, and must: it resolves a
# foundation-owned initial value against the declared components. It is
# therefore not on the allowlist below, and cannot build either record.
#
# Test files are exempt, as everywhere else in this directory: a test must be
# able to reach across a boundary in order to prove where it is.
#
# SCOPE, and why it is the whole backend package rather than the run domain.
# The first version of this module scanned `backend/assetops_backend/runs`
# only, while the module it protects claimed the guard covered the product.
# T019's independent review disproved that in the cheapest possible way: a
# function in `simulator_lab_api.py` deriving a cadence from a device's
# display name and building the frozen binding itself passed every test and
# passed this check. A guard scoped to one directory protects one directory,
# and the thing being protected - that a site fact cannot reach a
# profile-resolved run input - is a property of the product, not of a folder.
# So the scan below covers `backend/assetops_backend` and the allowlist is
# two modules. The same widening applies to the run-identity rule: a second
# place that can assemble a run identity is no less a second place for
# sitting outside the run package.
#
# Do not weaken the checks below to make a task pass.

function Invoke-RunSetupCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $backendRoot = "backend/assetops_backend"
    $runsRoot = "$backendRoot/runs"

    if (-not (Test-Path -LiteralPath $runsRoot -PathType Container)) {
        $failures.Add("Missing run domain root: $runsRoot") | Out-Null
        return $failures
    }

    # The whole product package, not the run domain. See SCOPE above.
    $scanned = @(Get-ScannedModules -Root $backendRoot -Extensions @(".py"))

    if ($scanned.Count -eq 0) {
        $failures.Add(("No module was scanned under $backendRoot, so every run " +
            "setup check below is vacuous. Update the check, do not delete it.")) | Out-Null
        return $failures
    }

    # The scan has to reach outside the run domain or it is the guard the
    # review disproved. Asserted rather than assumed: a later change to
    # Get-ScannedModules or to the layout that narrowed it back would
    # otherwise pass silently.
    $outsideTheRunDomain = @($scanned | Where-Object {
        -not $_.Path.StartsWith("$runsRoot/")
    })

    if ($outsideTheRunDomain.Count -eq 0) {
        $failures.Add(("The run setup scan reached no module outside $runsRoot, " +
            "so it is the directory-scoped guard T019's review disproved. " +
            "Update the check, do not delete it.")) | Out-Null
    }

    # --- 1. Profile-resolved inputs are built where no site can reach --------

    # The two records that carry a cadence, a simulator source identity and a
    # gateway identity.
    $resolvedRecords = @("FrozenObservationBinding", "FrozenPublicationIdentity")

    # `profiles.py` RESOLVES them from the selected profile. `parsing.py`
    # reconstructs them when a stored run is read back, which is a round trip
    # of a value some earlier run already resolved rather than a second
    # resolution. Neither may import the Site record family, so neither can
    # read a site fact whatever it is handed.
    $resolvers = @("$runsRoot/profiles.py", "$runsRoot/parsing.py")

    $siteModelImport = 'assetops_backend\.sites\.models'
    $constructionsSeen = 0

    foreach ($module in $scanned) {
        $isResolver = $resolvers -contains $module.Path

        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            foreach ($record in $resolvedRecords) {
                if ($line -notmatch "\b$record\s*\(") { continue }

                if ($isResolver) {
                    $constructionsSeen++
                    continue
                }

                $failures.Add(("$record is constructed in " +
                    "$($module.Path):${lineNumber}: $($line.Trim()). The " +
                    "cadence, the simulator source identity and the gateway " +
                    "identity come from the selected versioned profile or the " +
                    "run is blocked, so nowhere in the product builds the " +
                    "records that carry them except $($resolvers -join ', ') - " +
                    "modules that cannot import a site record and therefore " +
                    "cannot infer one of those values from a site.")) | Out-Null
            }

            if ($isResolver -and $line -match $siteModelImport) {
                $failures.Add(("$($module.Path):${lineNumber} imports the site " +
                    "record family: $($line.Trim()). This module resolves the " +
                    "run inputs that may come only from a versioned profile, " +
                    "so it must not be able to see a site's provenance, its " +
                    "devices, or how it was created.")) | Out-Null
            }
        }
    }

    if ($constructionsSeen -eq 0) {
        $failures.Add(("No $($resolvedRecords -join ' or ') is constructed in " +
            "$($resolvers -join ', '), so the profile-resolution check is " +
            "vacuous. Update the check, do not delete it.")) | Out-Null
    }

    # --- 2. A run identity is allocated in one place -------------------------

    # The prefix every run identity carries. Spelled in the identity module and
    # nowhere else in the package, so no other module can assemble one - from a
    # site ID, from a scenario label, or from anything else.
    $identityModule = "$runsRoot/identity.py"
    $allocator = "$runsRoot/service.py"
    $prefixLiteral = '["'']run-'
    $prefixSightings = 0
    $allocationSightings = 0

    foreach ($module in $scanned) {
        $lineNumber = 0
        foreach ($line in $module.Lines) {
            $lineNumber++

            if ($line -match $prefixLiteral) {
                if ($module.Path -eq $identityModule) {
                    $prefixSightings++
                }
                else {
                    $failures.Add(("The run identity prefix is spelled in " +
                        "$($module.Path):${lineNumber}: $($line.Trim()). A run " +
                        "identity is allocated by $identityModule and nowhere " +
                        "else in the product; a second place that can assemble " +
                        "one is a second answer to what a run is called.")) | Out-Null
                }
            }

            # The definition is not a call. Counting it would let the
            # vacuity check below pass on a tree where nothing allocates at
            # all, which is the shape of hole this project keeps finding.
            if ($line -match '\ballocate_run_id\s*\(' -and $line -notmatch '^\s*def\s') {
                if ($module.Path -eq $allocator) {
                    $allocationSightings++
                }
                else {
                    $failures.Add(("A run identity is allocated in " +
                        "$($module.Path):${lineNumber}: $($line.Trim()). Run " +
                        "setup allocates one, in $allocator. A store, a " +
                        "payload or a parser that allocated one would be " +
                        "creating a run nothing set up.")) | Out-Null
                }
            }
        }
    }

    if ($prefixSightings -eq 0) {
        $failures.Add(("$identityModule no longer spells the run identity " +
            "prefix, so confining it proves nothing. Update the check, do not " +
            "delete it.")) | Out-Null
    }

    if ($allocationSightings -eq 0) {
        $failures.Add(("Nothing calls allocate_run_id, so the allocation " +
            "chokepoint is vacuous. Update the check, do not delete it.")) | Out-Null
    }

    return $failures
}
