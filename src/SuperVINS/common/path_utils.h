#pragma once

#include <filesystem>
#include <stdexcept>
#include <string>

namespace supervins_paths {
inline std::string absolute(const std::string& path) {
    return std::filesystem::absolute(path).lexically_normal().string();
}

// Every path stored in YAML is relative to that YAML file's directory.
inline std::string resolve(const std::string& config_file, const std::string& path) {
    if (path.empty()) throw std::invalid_argument("Empty path in configuration: " + config_file);
    const auto value = std::filesystem::path(path);
    const auto base = std::filesystem::path(absolute(config_file)).parent_path();
    return (value.is_absolute() ? value : base / value).lexically_normal().string();
}

inline void makeDirectory(const std::string& path) {
    std::filesystem::create_directories(path);
}
}  // namespace supervins_paths
