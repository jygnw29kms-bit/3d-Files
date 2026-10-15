#pragma once

#include <string>

namespace Slic3r {
class AppConfig;

namespace GUI {

inline constexpr const char* PRINTBENCH_NETWORK_VERSION = "02.03.00.99";

// Installs the PRINTBENCH-bundled Bambu LAN networking module into the
// PRINTBENCH user profile before Orca loads any networking DLL.
// Returns true when a bundled package was found and provisioned, or when an
// already provisioned profile is consistent with the bundled version.
bool provision_printbench_network(AppConfig* config, const std::string& data_directory);

} // namespace GUI
} // namespace Slic3r
