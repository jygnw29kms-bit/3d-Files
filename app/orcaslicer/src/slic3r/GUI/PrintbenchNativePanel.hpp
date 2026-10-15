#pragma once

#include "PrintbenchCollector.hpp"

#include <array>
#include <wx/scrolwin.h>
#include <wx/stattext.h>

namespace Slic3r {
class MachineObject;

namespace GUI {

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
    wxStaticText* m_printer_name{nullptr};
    wxStaticText* m_online{nullptr};
    wxStaticText* m_state{nullptr};
    wxStaticText* m_progress{nullptr};
    wxStaticText* m_layers{nullptr};
    wxStaticText* m_remaining{nullptr};
    wxStaticText* m_nozzle{nullptr};
    wxStaticText* m_bed{nullptr};
    wxStaticText* m_chamber{nullptr};
    wxStaticText* m_wifi{nullptr};
    wxStaticText* m_camera{nullptr};
    wxStaticText* m_ams_environment{nullptr};
    std::array<wxStaticText*, 4> m_ams_slots{};
};

} // namespace GUI
} // namespace Slic3r
