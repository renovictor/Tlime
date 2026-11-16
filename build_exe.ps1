param(
    [string]$PythonExe = "python",
    [string]$EntryScript = "tlime.py",
    [string]$IconPath = "",
    [switch]$CleanBuild = $true,
    [switch]$SkipPyInstallerInstall
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-Icon {
    param([string]$RequestedIcon)

    if ($RequestedIcon -and (Test-Path -LiteralPath $RequestedIcon)) {
        return (Resolve-Path -LiteralPath $RequestedIcon).Path
    }

    $candidates = @(
        "global_search_international.ico",
        "smithchart.ico",
        "app.ico"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return ""
}

function Ensure-PyInstaller {
    param(
        [string]$PyExe,
        [switch]$SkipInstall
    )

    $originalErrorActionPreference = $ErrorActionPreference
    $probeExitCode = 1
    $ErrorActionPreference = "Continue"
    try {
        & $PyExe -c "import PyInstaller" 2> $null
        $probeExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $originalErrorActionPreference
    }

    if ($probeExitCode -eq 0) {
        return
    }

    if ($SkipInstall) {
        throw "PyInstaller is not installed for '$PyExe'. Install it with: $PyExe -m pip install pyinstaller"
    }

    Write-Host "PyInstaller is not installed. Installing now..."
    & $PyExe -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install PyInstaller. Try: $PyExe -m pip install --upgrade pip pyinstaller"
    }

    $verifyExitCode = 1
    $ErrorActionPreference = "Continue"
    try {
        & $PyExe -c "import PyInstaller" 2> $null
        $verifyExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $originalErrorActionPreference
    }
    if ($verifyExitCode -ne 0) {
        throw "PyInstaller install completed but the module is still not importable."
    }
}

if (-not (Test-Path -LiteralPath $EntryScript)) {
    throw "Entry script not found: $EntryScript"
}

Ensure-PyInstaller -PyExe $PythonExe -SkipInstall:$SkipPyInstallerInstall

$versionRaw = & $PythonExe -c "from version import APP_NAME,__version__;print(f'{APP_NAME}|{__version__}')"
if (-not $versionRaw) {
    throw "Unable to read APP_NAME and __version__ from version.py"
}

$parts = $versionRaw.Trim().Split("|")
if ($parts.Length -ne 2) {
    throw "Unexpected version parse output: $versionRaw"
}

$appName = $parts[0].Trim()
$appVersion = $parts[1].Trim()
$exeName = "{0}_v{1}" -f $appName, $appVersion

$iconResolved = Resolve-Icon -RequestedIcon $IconPath
$hasLogo = Test-Path -LiteralPath "ASM-logo-small.gif"

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name", $exeName
)

if ($CleanBuild) {
    $pyInstallerArgs += "--clean"
}

if ($iconResolved) {
    $pyInstallerArgs += @("--icon", $iconResolved)
}

if ($hasLogo) {
    $pyInstallerArgs += @("--add-data", "ASM-logo-small.gif;.")
}

$pyInstallerArgs += $EntryScript

Write-Host "Building EXE with name: $exeName"
if ($iconResolved) {
    Write-Host "Using icon: $iconResolved"
} else {
    Write-Host "No icon found. EXE will use default icon."
}
if ($hasLogo) {
    Write-Host "Bundling splash asset: ASM-logo-small.gif"
}

& $PythonExe @pyInstallerArgs
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE"
}

$distExe = Join-Path -Path "dist" -ChildPath ($exeName + ".exe")
if (Test-Path -LiteralPath $distExe) {
    Write-Host "Build complete: $distExe"
} else {
    Write-Host "Build finished, but EXE not found at expected path: $distExe"
}
