# Windows Orca Build Toolchain

PRINTBENCH/Orca on Windows uses the Visual Studio 18 toolchain together with a native Windows Perl/patch environment for bundled dependencies.

## Bootstrap

```powershell
powershell -ExecutionPolicy Bypass -File tools/setup_windows_build_toolchain.ps1
```

The bootstrap installs the official Strawberry Perl portable distribution into the current user's local application data directory. It deliberately avoids an elevated MSI/UAC dependency and provides both native `perl.exe` and GNU `patch.exe`.

Validated local toolchain:

- Strawberry Perl 5.42.3 (`osname='MSWin32'`)
- GNU patch from Strawberry Perl
- Visual Studio 18 Community / MSVC 19.51
- Visual Studio CMake generator `Visual Studio 18 2026`
- Windows SDK 10.0.26100.0
- target Windows 10.0.19045

## Important ExternalProject rule

Dependency sources are extracted below `app/orcaslicer/deps/build`, which itself sits inside the parent Orca Git worktree. `git apply` may therefore treat an extracted dependency as part of the parent repository and silently fail to apply source-relative patches correctly.

For patched third-party dependencies use source-relative GNU patch commands:

```cmake
PATCH_COMMAND patch -p1 -d <SOURCE_DIR> -i <patch-file>
```

This is now verified for OpenCV and OCCT.

## Verified dependency progress

- OpenSSL 1.1.1w: built and installed
- CURL 7.75.0-DEV: built and installed
- OpenCV 4.6.0: VS18 patch applied; rebuilt as `x64/vc18/staticlib`
- OCCT 7.6.0: install-layout patch applied; rebuilt with `bin/occt`, `lib/occt`, `include/occt` layout

The OCCT build is intentionally verbose on current MSVC because its C++17-era sources emit many `std::iterator` deprecation warnings. These warnings are not treated as successful-build proof or failure by themselves; the ExternalProject completion marker and installed artifacts are authoritative.

## One-command build

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_printbench_orca.ps1
```

For an already completed dependency tree, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_printbench_orca.ps1 -SkipDependencies
```

The script bootstraps the local Windows toolchain, configures the dependency and main build trees, builds the Release GUI target, and verifies that both `orca-slicer.exe` and `OrcaSlicer.dll` exist.
## Verified full Orca build

The main OrcaSlicer tree now configures successfully against the local dependency prefix with Visual Studio 18 2026. The following Release targets were built successfully on this machine:

- `OrcaSlicer` -> `build-printbench-check/src/Release/OrcaSlicer.dll`
- `OrcaSlicer_app_gui` -> `build-printbench-check/src/Release/orca-slicer.exe`

This compile includes `libslic3r_gui` and therefore verifies the PRINTBENCH `Monitor.cpp` / embedded Device Center integration at C++ build level.

Generated dependency/build artifacts remain local and are never committed.

## Native P2S LAN module

135er-PRINTBENCH bundles a pinned build of `ClusterM/open-bamboo-networking` so the Windows application can discover and control the P2S over LAN without requiring Bambu Studio. The build entry point is `tools/build_printbench_network.ps1` and the pinned source commit is recorded in that script and in the generated `SOURCE.txt` package metadata.

The external build tree deliberately uses a short `%LOCALAPPDATA%\\PB\\obn\\...` path because Mosquitto/vcpkg create deeply nested MSBuild intermediates that otherwise exceed Windows path limits. Release packaging stages `bambu_networking_<version>.dll`, `BambuSource.dll` and `live555.dll` next to PRINTBENCH under `printbench-network/`.

`SHA256SUMS.txt` is generated during staging. On startup `PrintbenchNetworkBootstrap` verifies the bundled DLLs against that manifest before copying them into the private `PrintbenchStudio/plugins` profile. This integrity pin is required because the private PRINTBENCH network module is not distributed with Bambu's module signature.

Verified on the target Windows PC: PRINTBENCH provisioned network module `02.03.00.99`, loaded it successfully, discovered the P2S directly over LAN, populated AMS 2 Pro slot data, and resolved the native RTSPS camera path without a Raspberry Pi or Bambu Studio process.
