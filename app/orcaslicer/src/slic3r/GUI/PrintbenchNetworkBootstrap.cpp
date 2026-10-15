#include "PrintbenchNetworkBootstrap.hpp"

#include "libslic3r/AppConfig.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <map>
#include <sstream>
#include <boost/filesystem.hpp>
#include <boost/log/trivial.hpp>
#include <openssl/sha.h>
#include <wx/stdpaths.h>

namespace Slic3r {
namespace GUI {

namespace fs = boost::filesystem;

namespace {
std::string sha256_file(const fs::path& path)
{
    std::ifstream input(path.string(), std::ios::binary);
    if (!input)
        return {};

    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    std::array<char, 64 * 1024> buffer{};
    while (input.good()) {
        input.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
        const auto count = input.gcount();
        if (count > 0)
            SHA256_Update(&ctx, buffer.data(), static_cast<size_t>(count));
    }
    if (!input.eof())
        return {};

    std::array<unsigned char, SHA256_DIGEST_LENGTH> digest{};
    SHA256_Final(digest.data(), &ctx);
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (const auto byte : digest)
        out << std::setw(2) << static_cast<unsigned int>(byte);
    return out.str();
}

std::map<std::string, std::string> load_manifest(const fs::path& manifest)
{
    std::map<std::string, std::string> expected;
    std::ifstream input(manifest.string());
    std::string hash;
    std::string name;
    while (input >> hash >> name) {
        std::transform(hash.begin(), hash.end(), hash.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        expected[name] = hash;
    }
    return expected;
}

bool verify_file(const fs::path& path, const std::map<std::string, std::string>& manifest)
{
    const auto it = manifest.find(path.filename().string());
    if (it == manifest.end())
        return false;
    const auto actual = sha256_file(path);
    return !actual.empty() && actual == it->second;
}

bool copy_if_needed(const fs::path& source, const fs::path& destination, const std::map<std::string, std::string>& manifest)
{
    if (verify_file(destination, manifest))
        return true;
    if (!verify_file(source, manifest)) {
        BOOST_LOG_TRIVIAL(error) << "PRINTBENCH network bootstrap: SHA-256 verification failed for " << source.string();
        return false;
    }

    boost::system::error_code ec;
    fs::copy_file(source, destination, fs::copy_options::overwrite_existing, ec);
    if (ec) {
        BOOST_LOG_TRIVIAL(error) << "PRINTBENCH network bootstrap: failed to copy "
                                 << source.string() << " -> " << destination.string()
                                 << ": " << ec.message();
        return false;
    }
    return true;
}
} // namespace

bool provision_printbench_network(AppConfig* config, const std::string& data_directory)
{
    if (config == nullptr)
        return false;

    const fs::path executable(wxStandardPaths::Get().GetExecutablePath().ToStdString());
    const fs::path package_dir = executable.parent_path() / "printbench-network";
    const fs::path source_network = package_dir / (std::string("bambu_networking_") + PRINTBENCH_NETWORK_VERSION + ".dll");
    const fs::path source_bambu = package_dir / "BambuSource.dll";
    const fs::path source_live555 = package_dir / "live555.dll";
    const fs::path manifest_path = package_dir / "SHA256SUMS.txt";

    boost::system::error_code ec;
    if (!fs::is_regular_file(source_network, ec) || !fs::is_regular_file(source_bambu, ec)
        || !fs::is_regular_file(source_live555, ec) || !fs::is_regular_file(manifest_path, ec)) {
        const bool already_configured = config->get_bool("installed_networking")
            && config->get_network_plugin_version() == PRINTBENCH_NETWORK_VERSION;
        if (!already_configured) {
            BOOST_LOG_TRIVIAL(warning) << "PRINTBENCH network bootstrap: bundled package missing at " << package_dir.string();
        }
        return already_configured;
    }

    const fs::path destination_dir = fs::path(data_directory) / "plugins";
    fs::create_directories(destination_dir, ec);
    if (ec) {
        BOOST_LOG_TRIVIAL(error) << "PRINTBENCH network bootstrap: cannot create "
                                 << destination_dir.string() << ": " << ec.message();
        return false;
    }

    const auto manifest = load_manifest(manifest_path);
    if (manifest.size() < 3) {
        BOOST_LOG_TRIVIAL(error) << "PRINTBENCH network bootstrap: invalid SHA-256 manifest at " << manifest_path.string();
        return false;
    }

    const fs::path destination_network = destination_dir / source_network.filename();
    const fs::path destination_bambu = destination_dir / source_bambu.filename();
    const fs::path destination_live555 = destination_dir / source_live555.filename();

    if (!copy_if_needed(source_network, destination_network, manifest)
        || !copy_if_needed(source_bambu, destination_bambu, manifest)
        || !copy_if_needed(source_live555, destination_live555, manifest)) {
        return false;
    }

    config->set_bool("installed_networking", true);
    config->set_network_plugin_version(PRINTBENCH_NETWORK_VERSION);
    config->set("network_plugin_remind_later", "true");
    config->set("ignore_module_cert", "1");

    auto skipped = config->get_skipped_network_versions();
    skipped.erase(std::remove(skipped.begin(), skipped.end(), PRINTBENCH_NETWORK_VERSION), skipped.end());
    std::string skipped_joined;
    for (const auto& value : skipped) {
        if (!skipped_joined.empty())
            skipped_joined += ";";
        skipped_joined += value;
    }
    config->set("network_plugin_skipped_versions", skipped_joined);
    config->save();

    BOOST_LOG_TRIVIAL(info) << "PRINTBENCH network bootstrap: provisioned version " << PRINTBENCH_NETWORK_VERSION;
    return true;
}

} // namespace GUI
} // namespace Slic3r
