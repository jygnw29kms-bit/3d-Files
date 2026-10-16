#pragma once

#include <array>
#include <string>

namespace Slic3r {
class MachineObject;

namespace GUI {

struct PrintbenchAmsSlotState
{
    bool        present{false};
    std::string material;
    std::string color;
    int         remain{-1};
};

struct PrintbenchSnapshot
{
    bool        online{false};
    std::string printer_name{"Bambu Lab P2S"};
    std::string print_state{"OFFLINE"};
    std::string job_name;
    int         progress{0};
    int         remaining_seconds{0};
    int         layer_current{0};
    int         layer_total{0};
    int         nozzle_c{0};
    int         nozzle_target_c{0};
    int         bed_c{0};
    int         bed_target_c{0};
    float       chamber_c{0.0f};
    std::string wifi_signal;
    int         speed_level{0};
    bool        has_camera{false};
    bool        camera_recording{false};
    bool        camera_timelapse{false};
    std::string camera_resolution;
    bool        has_ams{false};
    float       ams_temp_c{0.0f};
    int         ams_humidity{-1};
    std::array<PrintbenchAmsSlotState, 4> ams_slots{};
};

class PrintbenchCollector
{
public:
    PrintbenchSnapshot collect(MachineObject* machine) const;
};

} // namespace GUI
} // namespace Slic3r
