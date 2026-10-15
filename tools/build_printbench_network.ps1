param(
    [string]$OutputDir = '',
    [int]$Jobs = 12,
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$OrcaRoot = Join-Path $RepoRoot 'app\orcaslicer'
$MainBuild = Join-Path $OrcaRoot 'build-printbench-check'
if (-not $OutputDir) {
    $OutputDir = Join-Path $MainBuild 'src\Release\printbench-network'
}

$Version = '02.03.00.99'
$Commit = 'fbf8ff2d63e4717676c9eab8fed7fc62774baa5d'
$Upstream = 'https://github.com/ClusterM/open-bamboo-networking.git'
# Keep this deliberately short: Mosquitto/vcpkg generate very deep MSBuild paths
# and otherwise exceed legacy Windows path limits in intermediate .tlog files.
$DepRoot = Join-Path $env:LOCALAPPDATA 'PB\obn'
$SourceDir = Join-Path $DepRoot $Commit.Substring(0, 8)
$BuildDir = Join-Path $SourceDir 'b'
$CMake = 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$Vcpkg = 'C:\Program Files\Microsoft Visual Studio\18\Community\VC\vcpkg'

if (-not (Test-Path $CMake)) { throw "Visual Studio CMake not found: $CMake" }
if (-not (Test-Path (Join-Path $Vcpkg 'vcpkg.exe'))) { throw "Visual Studio vcpkg not found: $Vcpkg" }

New-Item -ItemType Directory -Force -Path $DepRoot | Out-Null
if (-not (Test-Path (Join-Path $SourceDir '.git'))) {
    Write-Host '== Clone pinned open-bamboo-networking =='
    git clone $Upstream $SourceDir
    if ($LASTEXITCODE -ne 0) { throw 'open-bamboo-networking clone failed' }
}

Push-Location $SourceDir
try {
    git fetch --quiet origin
    if ($LASTEXITCODE -ne 0) { throw 'open-bamboo-networking fetch failed' }
    git checkout --quiet --detach $Commit
    if ($LASTEXITCODE -ne 0) { throw 'open-bamboo-networking checkout failed' }
    $Actual = (git rev-parse HEAD).Trim()
    if ($Actual -ne $Commit) { throw "Pinned network commit mismatch: $Actual" }

    if (-not $SkipBuild) {
        Write-Host "== Configure PRINTBENCH Bambu LAN module $Version =="
        $Configure = @(
            '-S', '.', '-B', $BuildDir,
            '-G', 'Visual Studio 18 2026', '-A', 'x64',
            "-DCMAKE_TOOLCHAIN_FILE=$Vcpkg\scripts\buildsystems\vcpkg.cmake",
            '-DVCPKG_TARGET_TRIPLET=x64-windows-static-md',
            '-DCMAKE_BUILD_TYPE=Release',
            "-DOBN_VERSION=$Version",
            '-DOBN_CLIENT_TYPE=orca_slicer',
            '-DOBN_BUILD_TESTS=ON',
            '-DOBN_PATCH_CLIENT_CONF=OFF',
            '-DOBN_REGISTER_DSHOW_FILTER=OFF'
        )
        & $CMake @Configure
        if ($LASTEXITCODE -ne 0) { throw 'PRINTBENCH network configure failed' }

        Write-Host '== Build PRINTBENCH Bambu LAN module =='
        & $CMake --build $BuildDir --config Release --parallel $Jobs
        if ($LASTEXITCODE -ne 0) { throw 'PRINTBENCH network build failed' }

        Write-Host '== Test PRINTBENCH Bambu LAN module =='
        & (Join-Path (Split-Path $CMake) 'ctest.exe') --test-dir $BuildDir -C Release --output-on-failure
        if ($LASTEXITCODE -ne 0) { throw 'PRINTBENCH network tests failed' }
    }

    $Release = Join-Path $BuildDir 'Release'
    $Required = @('bambu_networking.dll','BambuSource.dll','live555.dll')
    foreach ($Name in $Required) {
        if (-not (Test-Path (Join-Path $Release $Name))) { throw "Missing network artifact: $Name" }
    }

    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    Copy-Item (Join-Path $Release 'bambu_networking.dll') (Join-Path $OutputDir "bambu_networking_$Version.dll") -Force
    Copy-Item (Join-Path $Release 'BambuSource.dll') $OutputDir -Force
    Copy-Item (Join-Path $Release 'live555.dll') $OutputDir -Force
    Set-Content -Path (Join-Path $OutputDir 'SOURCE.txt') -Encoding UTF8 -Value @(
        "open-bamboo-networking commit=$Commit",
        "version=$Version",
        'client=orca_slicer',
        'toolchain=Visual Studio 18 2026 / MSVC v145',
        'triplet=x64-windows-static-md'
    )
    $HashLines = foreach ($Name in @("bambu_networking_$Version.dll", 'BambuSource.dll', 'live555.dll')) {
        $Hash = (Get-FileHash -Algorithm SHA256 -Path (Join-Path $OutputDir $Name)).Hash.ToLowerInvariant()
        "$Hash  $Name"
    }
    Set-Content -Path (Join-Path $OutputDir 'SHA256SUMS.txt') -Encoding ASCII -Value $HashLines
    Write-Host "PRINTBENCH network package staged: $OutputDir"
}
finally {
    Pop-Location
}
