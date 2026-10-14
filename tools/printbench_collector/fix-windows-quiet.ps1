param([string]$CollectorPath)
$ErrorActionPreference = 'Stop'
# Update only PRINTBENCH; do not stop unrelated SSH or Python processes.
$running = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^pythonw?\.exe$' -and $_.CommandLine -match 'daemon\.py' -and $_.CommandLine -match 'printbench_collector'
})
if (-not $CollectorPath) {
    $paths = @($running | ForEach-Object {
        if ($_.CommandLine -match '"([^"
]*printbench_collector[\/]daemon\.py)"') {
            Split-Path $Matches[1]
        } elseif ($_.CommandLine -match '(\S*printbench_collector[\/]daemon\.py)') {
            Split-Path $Matches[1]
        }
    } | Select-Object -Unique)
    if ($paths.Count -ne 1) { throw 'Collector nicht eindeutig gefunden. Mit -CollectorPath den vorhandenen Ordner angeben.' }
    $CollectorPath = $paths[0]
}
$CollectorPath = (Resolve-Path -LiteralPath $CollectorPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $CollectorPath 'daemon.py'))) { throw 'daemon.py fehlt im gewaehlten Ordner.' }
$targetProcesses = @($running | Where-Object { $_.CommandLine.IndexOf($CollectorPath, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
$pythonw = $null
foreach ($p in $targetProcesses) {
    if ($p.ExecutablePath) {
        $candidate = Join-Path (Split-Path $p.ExecutablePath) 'pythonw.exe'
        if (Test-Path -LiteralPath $candidate) { $pythonw = $candidate; break }
    }
}
if (-not $pythonw) {
    $command = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($command) { $pythonw = $command.Source }
}
if (-not $pythonw) { throw 'pythonw.exe nicht gefunden. Bestehende Python-Installation pruefen.' }
$files = @(
    @{ Name = 'daemon.py'; Sha256 = 'c63c907181b236dbb368a11ca0dbcf0b1d73743f68056a33645925ce71c9d6a0' }
    @{ Name = 'server_transport.py'; Sha256 = 'e831c6b8e7364d384e177f54aef0abf178802201f791ce3880c127f754433687' }
    @{ Name = 'quiet_process.py'; Sha256 = '87040430218effb9664eca3f1d53bc08e01bc069e72787dc98357d433dba54f3' }
)
$temp = Join-Path ([IO.Path]::GetTempPath()) ('printbench-fix-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    foreach ($file in $files) {
        $dest = Join-Path $temp $file.Name
        Invoke-WebRequest -Uri ('https://raw.githubusercontent.com/jygnw29kms-bit/3d-Files/dde2731/tools/printbench_collector/' + $file.Name) -OutFile $dest
        if ((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash -ne $file.Sha256) { throw ('Pruefsumme falsch: ' + $file.Name) }
    }
    $backup = Join-Path $CollectorPath ('backup-quiet-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backup | Out-Null
    foreach ($file in $files) {
        $original = Join-Path $CollectorPath $file.Name
        if (Test-Path -LiteralPath $original) { Copy-Item -LiteralPath $original -Destination $backup }
    }
    # End only direct children of identified collector processes, then their parents.
    foreach ($p in $targetProcesses) {
        Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $p.ProcessId -and $_.Name -in @('ssh.exe', 'ffmpeg.exe') } | ForEach-Object {
            Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
        }
        Stop-Process -Id $p.ProcessId -ErrorAction SilentlyContinue
    }
    foreach ($file in $files) { Copy-Item -LiteralPath (Join-Path $temp $file.Name) -Destination (Join-Path $CollectorPath $file.Name) -Force }
    $shell = New-Object -ComObject WScript.Shell
    $startup = [Environment]::GetFolderPath('Startup')
    # Rewrite only shortcuts explicitly pointing at this collector.
    foreach ($link in @(Get-ChildItem -LiteralPath $startup -Filter '*.lnk')) {
        $shortcut = $shell.CreateShortcut($link.FullName)
        $text = $shortcut.TargetPath + ' ' + $shortcut.Arguments
        if ($text.IndexOf($CollectorPath, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and $text -match 'daemon\.py') {
            Copy-Item -LiteralPath $link.FullName -Destination $backup
            $shortcut.TargetPath = $pythonw
            $shortcut.Arguments = '"' + (Join-Path $CollectorPath 'daemon.py') + '"'
            $shortcut.WorkingDirectory = $CollectorPath
            $shortcut.WindowStyle = 7
            $shortcut.Save()
        }
    }
    Start-Process -FilePath $pythonw -ArgumentList ('"' + (Join-Path $CollectorPath 'daemon.py') + '"') -WorkingDirectory $CollectorPath -WindowStyle Hidden
    Write-Host 'Collector aktualisiert und unsichtbar neu gestartet. SSH ohne Fenster; keine lokale Kamera-Verarbeitung.'
    Write-Host ('Sicherung: ' + $backup)
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force
}
