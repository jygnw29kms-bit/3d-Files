#include "PrintbenchNativePanel.hpp"

#include "DeviceManager.hpp"

#include <algorithm>
#include <wx/sizer.h>
#include <wx/statline.h>

namespace Slic3r {
namespace GUI {

namespace {
const wxColour PB_BG(6, 16, 24);
const wxColour PB_CARD(11, 29, 42);
const wxColour PB_BORDER(25, 57, 77);
const wxColour PB_TEXT(226, 238, 247);
const wxColour PB_MUTED(122, 151, 170);
const wxColour PB_ACCENT(0, 188, 230);
const wxColour PB_OK(68, 214, 151);

void style_label(wxStaticText* label, int point_size, bool bold = false, const wxColour& colour = PB_TEXT)
{
    wxFont font = label->GetFont();
    font.SetPointSize(point_size);
    font.SetWeight(bold ? wxFONTWEIGHT_BOLD : wxFONTWEIGHT_NORMAL);
    label->SetFont(font);
    label->SetForegroundColour(colour);
}

wxString format_temp(double value, double target = -1.0)
{
    if (target >= 0.0)
        return wxString::Format("%.0f C  /  %.0f C", value, target);
    return wxString::Format("%.0f C", value);
}
} // namespace

PrintbenchNativePanel::PrintbenchNativePanel(wxWindow* parent)
    : wxScrolledWindow(parent, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxVSCROLL | wxTAB_TRAVERSAL)
{
    SetBackgroundColour(PB_BG);
    SetScrollRate(0, FromDIP(12));

    auto* root = new wxBoxSizer(wxVERTICAL);
    root->AddSpacer(FromDIP(22));

    auto* eyebrow = new wxStaticText(this, wxID_ANY, "PRINTBENCH / LOCAL DEVICE CENTER");
    style_label(eyebrow, 9, true, PB_ACCENT);
    root->Add(eyebrow, 0, wxLEFT | wxRIGHT, FromDIP(28));

    m_printer_name = new wxStaticText(this, wxID_ANY, "Bambu Lab P2S");
    style_label(m_printer_name, 24, true);
    root->Add(m_printer_name, 0, wxLEFT | wxRIGHT | wxTOP, FromDIP(28));

    auto* subtitle = new wxStaticText(this, wxID_ANY, "P2S + AMS 2 Pro  |  Native LAN control  |  No Bambu Studio required");
    style_label(subtitle, 10, false, PB_MUTED);
    root->Add(subtitle, 0, wxLEFT | wxRIGHT | wxTOP, FromDIP(28));
    root->AddSpacer(FromDIP(18));

    auto* hero = new wxBoxSizer(wxHORIZONTAL);
    wxBoxSizer* body = nullptr;

    auto* printer_card = make_card(this, "P2S + AMS 2 PRO", body);
    m_state = add_value(printer_card, body, "Printer state");
    m_online = add_value(printer_card, body, "Connection");
    m_wifi = add_value(printer_card, body, "Wi-Fi");
    hero->Add(printer_card, 2, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* status_card = make_card(this, "DRUCKERSTATUS", body);
    m_nozzle = add_value(status_card, body, "Nozzle");
    m_bed = add_value(status_card, body, "Bed");
    m_chamber = add_value(status_card, body, "Chamber");
    hero->Add(status_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* camera_card = make_card(this, "LIVE KAMERA", body);
    m_camera = add_value(camera_card, body, "Camera");
    auto* camera_note = new wxStaticText(camera_card, wxID_ANY, "Native video surface follows in the next integration step.");
    style_label(camera_note, 9, false, PB_MUTED);
    camera_note->Wrap(FromDIP(280));
    body->Add(camera_note, 0, wxTOP, FromDIP(8));
    hero->Add(camera_card, 1, wxEXPAND);

    root->Add(hero, 0, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(28));
    root->AddSpacer(FromDIP(12));

    auto* middle = new wxBoxSizer(wxHORIZONTAL);
    auto* print_card = make_card(this, "AKTUELLER DRUCK", body);
    m_progress = add_value(print_card, body, "Progress");
    m_layers = add_value(print_card, body, "Layers");
    m_remaining = add_value(print_card, body, "Remaining");
    middle->Add(print_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* temp_card = make_card(this, "TEMPERATUREN (LIVE)", body);
    auto* temp_note = new wxStaticText(temp_card, wxID_ANY, "Native collector reads the live Orca/Bambu machine model directly.");
    style_label(temp_note, 10, false, PB_MUTED);
    temp_note->Wrap(FromDIP(420));
    body->Add(temp_note, 0, wxTOP, FromDIP(8));
    middle->Add(temp_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* ams_card = make_card(this, "AMS 2 PRO", body);
    m_ams_environment = add_value(ams_card, body, "Environment");
    auto* slot_grid = new wxFlexGridSizer(2, 2, FromDIP(8), FromDIP(8));
    slot_grid->AddGrowableCol(0, 1);
    slot_grid->AddGrowableCol(1, 1);
    for (size_t i = 0; i < m_ams_slots.size(); ++i) {
        m_ams_slots[i] = new wxStaticText(ams_card, wxID_ANY, wxString::Format("SLOT %d  --", static_cast<int>(i + 1)));
        style_label(m_ams_slots[i], 10, true);
        m_ams_slots[i]->SetBackgroundColour(wxColour(8, 22, 33));
        m_ams_slots[i]->SetMinSize(wxSize(FromDIP(145), FromDIP(42)));
        slot_grid->Add(m_ams_slots[i], 1, wxEXPAND | wxALL, FromDIP(6));
    }
    body->Add(slot_grid, 0, wxEXPAND | wxTOP, FromDIP(10));
    middle->Add(ams_card, 1, wxEXPAND);

    root->Add(middle, 0, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(28));
    root->AddSpacer(FromDIP(12));

    auto* bottom = new wxBoxSizer(wxHORIZONTAL);
    auto* device_card = make_card(this, "GERAETESTATUS", body);
    auto* device_text = new wxStaticText(device_card, wxID_ANY, "Collector: NATIVE\nTransport: Orca LAN device model\nCloud: not required\nBambu Studio: not required");
    style_label(device_text, 10, false, PB_MUTED);
    body->Add(device_text, 0, wxTOP, FromDIP(4));
    bottom->Add(device_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* history_card = make_card(this, "LETZTE DRUCKE", body);
    auto* history_text = new wxStaticText(history_card, wxID_ANY, "Native session history will use the integrated PRINTBENCH store.");
    style_label(history_text, 10, false, PB_MUTED);
    history_text->Wrap(FromDIP(420));
    body->Add(history_text, 0, wxTOP, FromDIP(4));
    bottom->Add(history_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* action_card = make_card(this, "SYSTEM & AKTIONEN", body);
    auto* action_text = new wxStaticText(action_card, wxID_ANY, "Native control buttons are connected only after capability validation.");
    style_label(action_text, 10, false, PB_MUTED);
    action_text->Wrap(FromDIP(420));
    body->Add(action_text, 0, wxTOP, FromDIP(4));
    bottom->Add(action_card, 1, wxEXPAND);

    root->Add(bottom, 0, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, FromDIP(28));
    SetSizer(root);
    Layout();
}

wxPanel* PrintbenchNativePanel::make_card(wxWindow* parent, const wxString& title, wxBoxSizer*& body)
{
    auto* card = new wxPanel(parent, wxID_ANY);
    card->SetBackgroundColour(PB_CARD);
    auto* outer = new wxBoxSizer(wxVERTICAL);
    auto* heading = new wxStaticText(card, wxID_ANY, title);
    style_label(heading, 9, true, PB_ACCENT);
    outer->Add(heading, 0, wxALL, FromDIP(14));
    auto* line = new wxStaticLine(card, wxID_ANY);
    line->SetForegroundColour(PB_BORDER);
    outer->Add(line, 0, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(14));
    body = new wxBoxSizer(wxVERTICAL);
    outer->Add(body, 1, wxEXPAND | wxALL, FromDIP(14));
    card->SetSizer(outer);
    card->SetMinSize(wxSize(FromDIP(220), FromDIP(150)));
    return card;
}

wxStaticText* PrintbenchNativePanel::add_value(wxWindow* parent, wxSizer* sizer, const wxString& caption)
{
    auto* row = new wxBoxSizer(wxHORIZONTAL);
    auto* name = new wxStaticText(parent, wxID_ANY, caption);
    style_label(name, 9, false, PB_MUTED);
    auto* value = new wxStaticText(parent, wxID_ANY, "--");
    style_label(value, 11, true);
    row->Add(name, 1, wxALIGN_CENTER_VERTICAL);
    row->Add(value, 0, wxALIGN_CENTER_VERTICAL);
    sizer->Add(row, 0, wxEXPAND | wxBOTTOM, FromDIP(7));
    return value;
}

void PrintbenchNativePanel::refresh_from_machine(MachineObject* machine)
{
    apply_snapshot(m_collector.collect(machine));
}

void PrintbenchNativePanel::apply_snapshot(const PrintbenchSnapshot& s)
{
    m_printer_name->SetLabel(wxString::FromUTF8(s.printer_name));
    m_online->SetLabel(s.online ? "ONLINE / LAN" : "OFFLINE");
    m_online->SetForegroundColour(s.online ? PB_OK : PB_MUTED);
    m_state->SetLabel(wxString::FromUTF8(s.print_state));
    m_wifi->SetLabel(s.wifi_signal.empty() ? "--" : wxString::FromUTF8(s.wifi_signal));

    m_progress->SetLabel(wxString::Format("%d %%", std::clamp(s.progress, 0, 100)));
    m_layers->SetLabel(wxString::Format("%d / %d", s.layer_current, s.layer_total));
    const int minutes = std::max(0, s.remaining_seconds / 60);
    m_remaining->SetLabel(wxString::Format("%d min", minutes));

    m_nozzle->SetLabel(format_temp(s.nozzle_c, s.nozzle_target_c));
    m_bed->SetLabel(format_temp(s.bed_c, s.bed_target_c));
    m_chamber->SetLabel(format_temp(s.chamber_c));

    wxString camera = s.has_camera ? "READY" : "NOT AVAILABLE";
    if (s.has_camera && !s.camera_resolution.empty())
        camera += "  " + wxString::FromUTF8(s.camera_resolution);
    if (s.camera_recording)
        camera += "  REC";
    if (s.camera_timelapse)
        camera += "  TL";
    m_camera->SetLabel(camera);

    if (s.has_ams)
        m_ams_environment->SetLabel(wxString::Format("%.1f C  |  Humidity %d", s.ams_temp_c, s.ams_humidity));
    else
        m_ams_environment->SetLabel("NOT CONNECTED");

    for (size_t i = 0; i < m_ams_slots.size(); ++i) {
        const auto& slot = s.ams_slots[i];
        wxString text = wxString::Format("SLOT %d  ", static_cast<int>(i + 1));
        if (slot.present) {
            text += slot.material.empty() ? "FILAMENT" : wxString::FromUTF8(slot.material);
            if (slot.remain >= 0)
                text += wxString::Format("  %d%%", slot.remain);
        } else {
            text += "EMPTY";
        }
        m_ams_slots[i]->SetLabel(text);
        if (slot.present && slot.color.size() >= 6) {
            unsigned long rgb = 0;
            if (wxString::FromUTF8(slot.color.substr(0, 6)).ToULong(&rgb, 16)) {
                const wxColour c((rgb >> 16) & 0xff, (rgb >> 8) & 0xff, rgb & 0xff);
                m_ams_slots[i]->SetForegroundColour(c.GetLuminance() < 0.4 ? *wxWHITE : *wxBLACK);
                m_ams_slots[i]->SetBackgroundColour(c);
            }
        } else {
            m_ams_slots[i]->SetForegroundColour(PB_TEXT);
            m_ams_slots[i]->SetBackgroundColour(wxColour(8, 22, 33));
        }
    }
    Layout();
}

} // namespace GUI
} // namespace Slic3r
