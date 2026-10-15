param(
    [int]$Jobs = 12,
    [switch]$SkipDependencies,
    [switch]$SkipNetwork
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

$Exe = Join-Path $MainBuild 'src\Release\orca-slicer.exe'
$Dll = Join-Path $MainBuild 'src\Release\OrcaSlicer.dll'
$BuildStartedUtc = [DateTime]::UtcNow

Write-Host '== Remove stale PRINTBENCH outputs =='
foreach ($Output in @($Exe, $Dll)) {
    if (Test-Path $Output) {
        try {
            Remove-Item -LiteralPath $Output -Force
        }
        catch {
            throw "Could not remove stale build output '$Output'. Close any running PRINTBENCH/Orca process and retry. $($_.Exception.Message)"
        }
    }
    if (Test-Path $Output) {
        throw "Stale build output still exists after cleanup: $Output"
    }
}

Write-Host '== Build PRINTBENCH Orca GUI =='
& $CMake --build $MainBuild --config Release --target OrcaSlicer_app_gui -- /m:$Jobs
if ($LASTEXITCODE -ne 0) { throw 'PRINTBENCH Orca GUI build failed' }

foreach ($Output in @($Exe, $Dll)) {
    if (-not (Test-Path $Output)) {
        throw "Missing fresh build output: $Output"
    }
    $Item = Get-Item -LiteralPath $Output
    if ($Item.LastWriteTimeUtc -lt $BuildStartedUtc) {
        throw "Build output is stale: $Output ($($Item.LastWriteTimeUtc.ToString('o')) < $($BuildStartedUtc.ToString('o')))"
    }
    if ($Item.Length -le 0) {
        throw "Build output is empty: $Output"
    }
}

if (-not $SkipNetwork) {
    Write-Host '== Build and stage PRINTBENCH native Bambu LAN module =='
    $NetworkScript = Join-Path $PSScriptRoot 'build_printbench_network.ps1'
    $NetworkOutput = Join-Path (Split-Path $Exe) 'printbench-network'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $NetworkScript -OutputDir $NetworkOutput -Jobs $Jobs
    if ($LASTEXITCODE -ne 0) { throw 'PRINTBENCH network package build failed' }
}

$ExeItem = Get-Item -LiteralPath $Exe
$DllItem = Get-Item -LiteralPath $Dll
Write-Host 'PRINTBENCH Orca build complete with fresh outputs.'
Write-Host "EXE: $Exe  $($ExeItem.LastWriteTimeUtc.ToString('o'))  $($ExeItem.Length) bytes"
Write-Host "DLL: $Dll  $($DllItem.LastWriteTimeUtc.ToString('o'))  $($DllItem.Length) bytes"
