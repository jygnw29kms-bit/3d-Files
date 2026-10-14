# Windows Orca Build Toolchain

PRINTBENCH/Orca on Windows requires a native Windows Perl for the bundled OpenSSL 1.1.1w dependency.

Use:

```powershell
powershell -ExecutionPolicy Bypass -File tools/setup_windows_build_toolchain.ps1
```

The script installs the official Strawberry Perl portable distribution into the current user's local application data directory, adds its tool directories to the user PATH, and validates that Perl reports `osname='MSWin32'`.

This deliberately avoids an elevated MSI install and therefore does not depend on an unattended UAC approval.

Current validated toolchain:

- Strawberry Perl 5.42.3 (`MSWin32`)
- Visual Studio 18 Community CMake/MSBuild toolchain
- Orca dependency tree under `app/orcaslicer/deps/build`

After setup, continue the OpenSSL dependency build with the Visual Studio CMake executable and then reconfigure `build-printbench-check`. Build artifacts remain local and are not committed.
