#include "PrintbenchCollector.hpp"

#include "DeviceManager.hpp"
#include "DeviceCore/DevBed.h"
#include "DeviceCore/DevExtruderSystem.h"
#include "DeviceCore/DevFilaSystem.h"

namespace Slic3r {
namespace GUI {

PrintbenchSnapshot PrintbenchCollector::collect(MachineObject* machine) const
{
    PrintbenchSnapshot out;
    if (machine == nullptr)
        return out;

    out.online = machine->m_is_online || machine->HasRecentLanMessage();
    if (!machine->get_dev_name().empty())
        out.printer_name = machine->get_dev_name();
    out.print_state = machine->print_status.empty() ? "UNKNOWN" : machine->print_status;
    out.progress = machine->mc_print_percent;
    out.remaining_seconds = machine->mc_left_time;
    out.layer_current = machine->curr_layer;
    out.layer_total = machine->total_layers;
    out.chamber_c = machine->chamber_temp;
    out.wifi_signal = machine->wifi_signal;
    out.speed_level = static_cast<int>(machine->GetPrintingSpeedLevel());

    if (auto* ext = machine->GetExtderSystem()) {
        const int ext_id = ext->GetCurrentExtderId();
        out.nozzle_c = ext->GetNozzleTempCurrent(ext_id);
        out.nozzle_target_c = ext->GetNozzleTempTarget(ext_id);
    }
    if (auto* bed = machine->GetBed()) {
        out.bed_c = static_cast<int>(bed->GetBedTemp());
        out.bed_target_c = static_cast<int>(bed->GetBedTempTarget());
    }

    out.has_camera = machine->has_ipcam;
    out.camera_recording = machine->camera_recording;
    out.camera_timelapse = machine->camera_timelapse;
    out.camera_resolution = machine->camera_resolution;

    if (auto* fila = machine->GetFilaSystem()) {
        out.has_ams = fila->HasAms();
        const auto& ams_list = fila->GetAmsList();
        if (!ams_list.empty() && ams_list.begin()->second != nullptr) {
            const auto* ams = ams_list.begin()->second;
            out.ams_temp_c = ams->GetCurrentTemperature();
            out.ams_humidity = ams->GetHumidityPercent() >= 0 ? ams->GetHumidityPercent() : ams->GetHumidityLevel();
            for (const auto& [tray_id, tray] : ams->GetTrays()) {
                if (tray == nullptr)
                    continue;
                int idx = -1;
                try { idx = std::stoi(tray_id); } catch (...) { idx = -1; }
                if (idx < 0 || idx >= static_cast<int>(out.ams_slots.size()))
                    continue;
                auto& slot = out.ams_slots[static_cast<size_t>(idx)];
                slot.present = tray->is_exists;
                slot.material = tray->get_display_filament_type();
                slot.color = tray->color;
                slot.remain = tray->remain;
            }
        }
    }

    return out;
}

} // namespace GUI
} // namespace Slic3r
