$ErrorActionPreference = 'Stop'
$key = Join-Path $PSScriptRoot 'keys\printbench_pi_ed25519'
if (-not (Test-Path $key)) {
    throw "PRINTBENCH Pi private key not found: $key"
}
ssh.exe -i $key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new printbench@printbench-pi.local
