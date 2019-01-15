function Copy-BorgRepoFiles {
    param (
        [Parameter(Mandatory = $false)]$configuration,
        [Parameter(Mandatory = $false)][switch]$OnlySum
    )
    if (-not $configuration) {
        $configuration = $Global:configuration
    }
    $maxb = Get-MaxLocalDir -configuration $configuration
    "about to download files from remote: '{0}' to local: '{1}'" -f $configuration.BorgRepoPath, $maxb | Write-Verbose
    Copy-ChangedFiles -RemoteDirectory $configuration.BorgRepoPath -LocalDirectory $maxb -OnlySum:$OnlySum
}