param(
    [string]$InstallRoot = "$env:LOCALAPPDATA\PRINTBENCH\toolchain\strawberry-perl-5.42.3.1"
)

$ErrorActionPreference = "Stop"
$Version = "5.42.3.1"
$ZipName = "strawberry-perl-$Version-64bit-portable.zip"
$Url = "https://github.com/StrawberryPerl/Perl-Dist-Strawberry/releases/download/SP_54231_64bit/$ZipName"
$TempZip = Join-Path $env:TEMP $ZipName
$PerlExe = Join-Path $InstallRoot "perl\bin\perl.exe"

if (-not (Test-Path $PerlExe)) {
    New-Item -ItemType Directory -Force -Path (Split-Path $InstallRoot) | Out-Null
    & curl.exe -L --fail --retry 3 --output $TempZip $Url
    if ($LASTEXITCODE -ne 0) { throw "Strawberry Perl download failed ($LASTEXITCODE)" }

    if (Test-Path $InstallRoot) { Remove-Item $InstallRoot -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
    & tar.exe -xf $TempZip -C $InstallRoot
    if ($LASTEXITCODE -ne 0) { throw "Strawberry Perl extraction failed ($LASTEXITCODE)" }
    Remove-Item $TempZip -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $PerlExe)) { throw "Native Perl was not installed: $PerlExe" }

$BinPaths = @(
    (Join-Path $InstallRoot "perl\site\bin"),
    (Join-Path $InstallRoot "perl\bin"),
    (Join-Path $InstallRoot "c\bin")
)

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$Parts = @()
if ($UserPath) { $Parts = @($UserPath -split ";" | Where-Object { $_ }) }
foreach ($Bin in $BinPaths) {
    if ($Parts -notcontains $Bin) { $Parts = @($Bin) + $Parts }
}
[Environment]::SetEnvironmentVariable("Path", ($Parts -join ";"), "User")
$env:Path = ($BinPaths -join ";") + ";" + $env:Path

& $PerlExe -V:version -V:osname
if ($LASTEXITCODE -ne 0) { throw "Native Perl validation failed" }

Write-Host "PRINTBENCH Windows toolchain ready."
Write-Host "Perl: $PerlExe"
