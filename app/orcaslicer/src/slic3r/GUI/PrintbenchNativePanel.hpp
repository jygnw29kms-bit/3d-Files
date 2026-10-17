#pragma once

#include "PrintbenchCollector.hpp"

#include <array>
#include <chrono>
#include <deque>
#include <wx/scrolwin.h>
#include <wx/stattext.h>
#include <wx/button.h>
#include <wx/gauge.h>

class wxMediaCtrl2;

namespace Slic3r {
class MachineObject;

namespace GUI {

class MediaPlayCtrl;
class PrintbenchTempChart;
class PrintbenchProgressBar;
class PrintbenchAmsSlotCard;

class PrintbenchNativePanel : public wxScrolledWindow
{
public:
    explicit PrintbenchNativePanel(wxWindow* parent);
    void refresh_from_machine(MachineObject* machine);

private:
    wxPanel* make_card(wxWindow* parent, const wxString& title, wxBoxSizer*& body);
    wxStaticText* add_value(wxWindow* parent, wxSizer* sizer, const wxString& caption);
    void apply_snapshot(const PrintbenchSnapshot& snapshot);

    struct HistoryEntry
    {
        wxString finished_at;
        wxString status;
        wxString job_name;
        int observed_seconds{0};
    };

    void load_history();
    void save_history() const;
    void update_history_ui();
    void observe_history(const PrintbenchSnapshot& snapshot);
    void append_history(const wxString& job_name, const wxString& status, int observed_seconds);
    void activate_nav(size_t index);
    void handle_nav(size_t index);
    void scroll_to(wxWindow* target);
    void on_camera_action(wxCommandEvent& event);

    PrintbenchCollector m_collector;
    MachineObject* m_machine{nullptr};
    wxMediaCtrl2* m_media_ctrl{nullptr};
    MediaPlayCtrl* m_media_play_ctrl{nullptr};
    PrintbenchTempChart* m_temp_chart{nullptr};
    wxButton* m_print{nullptr};
    wxButton* m_pause_resume{nullptr};
    wxButton* m_stop{nullptr};
    wxButton* m_light{nullptr};
    wxButton* m_camera_record{nullptr};
    wxButton* m_camera_timelapse{nullptr};
    wxButton* m_camera_resolution{nullptr};
    std::array<wxButton*, 4> m_speed_buttons{};
    wxStaticText* m_printer_name{nullptr};
    wxStaticText* m_header_status{nullptr};
    wxStaticText* m_ready_banner{nullptr};
    wxStaticText* m_online{nullptr};
    wxStaticText* m_state{nullptr};
    wxStaticText* m_job_name{nullptr};
    PrintbenchProgressBar* m_progress_gauge{nullptr};
    wxStaticText* m_progress{nullptr};
    wxStaticText* m_layers{nullptr};
    wxStaticText* m_remaining{nullptr};
    wxStaticText* m_nozzle{nullptr};
    wxStaticText* m_bed{nullptr};
    wxStaticText* m_chamber{nullptr};
    wxStaticText* m_status_ready{nullptr};
    wxStaticText* m_speed{nullptr};
    wxStaticText* m_ams_summary{nullptr};
    wxStaticText* m_wifi{nullptr};
    wxStaticText* m_camera{nullptr};
    std::array<wxStaticText*, 6> m_device_status_values{};
    std::array<wxStaticText*, 3> m_history_rows{};
    std::array<wxPanel*, 13> m_nav_rows{};
    std::array<wxStaticText*, 13> m_nav_labels{};
    wxWindow* m_printer_card{nullptr};
    wxWindow* m_camera_card{nullptr};
    wxWindow* m_quick_card{nullptr};
    wxWindow* m_print_card{nullptr};
    wxWindow* m_ams_card{nullptr};
    wxWindow* m_history_card{nullptr};
    std::deque<HistoryEntry> m_history;
    bool m_history_tracking{false};
    wxString m_history_job_name;
    std::chrono::steady_clock::time_point m_history_started{};
    std::string m_previous_print_state;
    std::array<wxStaticText*, 3> m_temp_values{};
    wxStaticText* m_ams_environment{nullptr};
    std::array<PrintbenchAmsSlotCard*, 4> m_ams_slots{};
};

} // namespace GUI
} // namespace Slic3r
