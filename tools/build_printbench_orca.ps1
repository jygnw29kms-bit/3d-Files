param(
    [int]$Jobs = 12,
    [switch]$SkipDependencies
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$OrcaRoot = Join-Path $RepoRoot 'app\orcaslicer'
$DepsRoot = Join-Path $OrcaRoot 'deps'
$DepsBuild = Join-Path $DepsRoot 'build'
$Prefix = Join-Path $DepsBuild 'OrcaSlicer_dep\usr\local'
$MainBuild = Join-Path $OrcaRoot 'build-printbench-check'
$ToolchainSetup = Join-Path $PSScriptRoot 'setup_windows_build_toolchain.ps1'
$CMake = 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'

if (-not (Test-Path $CMake)) {
    throw "Visual Studio CMake not found: $CMake"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ToolchainSetup
if ($LASTEXITCODE -ne 0) { throw 'PRINTBENCH Windows toolchain bootstrap failed' }

$ToolRoot = Join-Path $env:LOCALAPPDATA 'PRINTBENCH\toolchain\strawberry-perl-5.42.3.1'
$env:Path = (Join-Path $ToolRoot 'perl\site\bin') + ';' +
            (Join-Path $ToolRoot 'perl\bin') + ';' +
            (Join-Path $ToolRoot 'c\bin') + ';' + $env:Path

if (-not $SkipDependencies) {
    Write-Host '== Configure Orca dependencies =='
    & $CMake -S $DepsRoot -B $DepsBuild -G 'Visual Studio 18 2026' -A x64 -DCMAKE_BUILD_TYPE=Release
    if ($LASTEXITCODE -ne 0) { throw 'Dependency CMake configure failed' }

    Write-Host '== Build Orca dependencies =='
    & $CMake --build $DepsBuild --config Release -- /m:$Jobs
    if ($LASTEXITCODE -ne 0) { throw 'Dependency build failed' }
}

Write-Host '== Configure PRINTBENCH Orca =='
& $CMake -S $OrcaRoot -B $MainBuild -G 'Visual Studio 18 2026' -A x64 `
    -DDEP_BUILD_DIR="$DepsBuild" `
    -DCMAKE_PREFIX_PATH="$Prefix" `
    -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE -ne 0) { throw 'PRINTBENCH Orca configure failed' }

Write-Host '== Build PRINTBENCH Orca GUI =='
& $CMake --build $MainBuild --config Release --target OrcaSlicer_app_gui -- /m:$Jobs
if ($LASTEXITCODE -ne 0) { throw 'PRINTBENCH Orca GUI build failed' }

$Exe = Join-Path $MainBuild 'src\Release\orca-slicer.exe'
$Dll = Join-Path $MainBuild 'src\Release\OrcaSlicer.dll'
if (-not (Test-Path $Exe)) { throw "Missing build output: $Exe" }
if (-not (Test-Path $Dll)) { throw "Missing build output: $Dll" }

Write-Host 'PRINTBENCH Orca build complete.'
Write-Host "EXE: $Exe"
Write-Host "DLL: $Dll"
