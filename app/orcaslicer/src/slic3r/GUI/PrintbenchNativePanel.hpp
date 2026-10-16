#pragma once

#include "PrintbenchCollector.hpp"

#include <array>
#include <wx/scrolwin.h>
#include <wx/stattext.h>
#include <wx/button.h>

class wxMediaCtrl2;

namespace Slic3r {
class MachineObject;

namespace GUI {

class MediaPlayCtrl;
class PrintbenchTempChart;

class PrintbenchNativePanel : public wxScrolledWindow
{
public:
    explicit PrintbenchNativePanel(wxWindow* parent);
    void refresh_from_machine(MachineObject* machine);

private:
    wxPanel* make_card(wxWindow* parent, const wxString& title, wxBoxSizer*& body);
    wxStaticText* add_value(wxWindow* parent, wxSizer* sizer, const wxString& caption);
    void apply_snapshot(const PrintbenchSnapshot& snapshot);

    PrintbenchCollector m_collector;
    MachineObject* m_machine{nullptr};
    wxMediaCtrl2* m_media_ctrl{nullptr};
    MediaPlayCtrl* m_media_play_ctrl{nullptr};
    PrintbenchTempChart* m_temp_chart{nullptr};
    wxButton* m_print{nullptr};
    wxButton* m_pause_resume{nullptr};
    wxButton* m_stop{nullptr};
    wxButton* m_light{nullptr};
    std::array<wxButton*, 4> m_speed_buttons{};
    wxStaticText* m_printer_name{nullptr};
    wxStaticText* m_header_status{nullptr};
    wxStaticText* m_ready_banner{nullptr};
    wxStaticText* m_online{nullptr};
    wxStaticText* m_state{nullptr};
    wxStaticText* m_job_name{nullptr};
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
    wxStaticText* m_ams_environment{nullptr};
    std::array<wxStaticText*, 4> m_ams_slots{};
};

} // namespace GUI
} // namespace Slic3r
