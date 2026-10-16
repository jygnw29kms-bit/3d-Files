#include "PrintbenchNativePanel.hpp"

#include "DeviceManager.hpp"
#include "GUI_App.hpp"
#include "MainFrame.hpp"
#include "DeviceCore/DevLamp.h"
#include "MediaPlayCtrl.h"
#include "wxMediaCtrl2.h"
#include "wxExtensions.hpp"

#include <algorithm>
#include <array>
#include <deque>
#include <wx/dcbuffer.h>
#include <wx/sizer.h>
#include <wx/statline.h>
#include <wx/msgdlg.h>

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

class PrintbenchTempChart : public wxPanel
{
public:
    explicit PrintbenchTempChart(wxWindow* parent)
        : wxPanel(parent, wxID_ANY)
    {
        SetBackgroundStyle(wxBG_STYLE_PAINT);
        SetBackgroundColour(wxColour(7, 21, 31));
        SetMinSize(wxSize(FromDIP(300), FromDIP(115)));
        Bind(wxEVT_PAINT, &PrintbenchTempChart::on_paint, this);
    }

    void push(double nozzle, double bed, double chamber)
    {
        const std::array<double, 3> sample{nozzle, bed, chamber};
        m_samples.push_back(sample);
        while (m_samples.size() > 90)
            m_samples.pop_front();
        Refresh(false);
    }

private:
    void on_paint(wxPaintEvent&)
    {
        wxAutoBufferedPaintDC dc(this);
        const auto size = GetClientSize();
        dc.SetBackground(wxBrush(GetBackgroundColour()));
        dc.Clear();
        if (size.x < 20 || size.y < 20)
            return;

        dc.SetPen(wxPen(wxColour(24, 51, 67), 1));
        for (int i = 1; i < 4; ++i) {
            const int y = (size.y * i) / 4;
            dc.DrawLine(0, y, size.x, y);
        }
        if (m_samples.size() < 2)
            return;

        double max_value = 40.0;
        for (const auto& sample : m_samples)
            max_value = std::max({max_value, sample[0], sample[1], sample[2]});
        max_value = std::min(320.0, max_value + 10.0);

        const std::array<wxColour, 3> colours{
            wxColour(0, 188, 230), wxColour(210, 222, 231), wxColour(90, 145, 165)};
        for (size_t series = 0; series < 3; ++series) {
            dc.SetPen(wxPen(colours[series], series == 0 ? 2 : 1));
            wxPoint previous;
            bool have_previous = false;
            for (size_t i = 0; i < m_samples.size(); ++i) {
                const int x = static_cast<int>((static_cast<double>(i) / (m_samples.size() - 1)) * (size.x - 1));
                const double normalized = std::clamp(m_samples[i][series] / max_value, 0.0, 1.0);
                const int y = size.y - 1 - static_cast<int>(normalized * (size.y - 8));
                const wxPoint point(x, y);
                if (have_previous)
                    dc.DrawLine(previous, point);
                previous = point;
                have_previous = true;
            }
        }
    }

    std::deque<std::array<double, 3>> m_samples;
};

PrintbenchNativePanel::PrintbenchNativePanel(wxWindow* parent)
    : wxScrolledWindow(parent, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxVSCROLL | wxTAB_TRAVERSAL)
{
    SetBackgroundColour(PB_BG);
    SetScrollRate(0, FromDIP(12));

    auto* shell = new wxBoxSizer(wxHORIZONTAL);

    auto* sidebar = new wxPanel(this, wxID_ANY);
    sidebar->SetBackgroundColour(wxColour(4, 14, 24));
    sidebar->SetMinSize(wxSize(FromDIP(238), -1));
    auto* side = new wxBoxSizer(wxVERTICAL);
    auto* brand = new wxStaticText(sidebar, wxID_ANY, "PRINTBENCH");
    style_label(brand, 20, true);
    side->Add(brand, 0, wxLEFT | wxRIGHT | wxTOP, FromDIP(22));
    auto* brand_sub = new wxStaticText(sidebar, wxID_ANY, wxString(L"\u0053tudio  \u2022  Bambu Integration"));
    style_label(brand_sub, 9, false, PB_ACCENT);
    side->Add(brand_sub, 0, wxLEFT | wxRIGHT | wxTOP | wxBOTTOM, FromDIP(22));
    const std::array<wxString, 13> nav_items{
        wxString(L"\u00DCbersicht"), L"Live Ansicht", L"Steuerung", L"AMS 2 Pro", L"Material",
        wxString(L"Druckauftr\u00E4ge"), L"Historie", L"Dateien", L"Kamera", wxString(L"Ger\u00E4te-Setup"),
        L"Netzwerk", L"Sicherheit", L"Diagnose"};
    for (size_t i = 0; i < nav_items.size(); ++i) {
        auto* item = new wxPanel(sidebar, wxID_ANY);
        item->SetBackgroundColour(i == 0 ? wxColour(8, 102, 218) : sidebar->GetBackgroundColour());
        auto* item_sizer = new wxBoxSizer(wxHORIZONTAL);
        auto* label = new wxStaticText(item, wxID_ANY, nav_items[i]);
        style_label(label, 11, i == 0, i == 0 ? *wxWHITE : PB_TEXT);
        item_sizer->Add(label, 1, wxALL | wxALIGN_CENTER_VERTICAL, FromDIP(13));
        item->SetSizer(item_sizer);
        side->Add(item, 0, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, FromDIP(5));
    }
    side->AddStretchSpacer();
    auto* system_item = new wxStaticText(sidebar, wxID_ANY, wxString(L"\u2699  System"));
    style_label(system_item, 11, false, PB_TEXT);
    side->Add(system_item, 0, wxALL, FromDIP(22));
    sidebar->SetSizer(side);
    shell->Add(sidebar, 0, wxEXPAND);

    auto* root = new wxBoxSizer(wxVERTICAL);
    auto* header = new wxBoxSizer(wxHORIZONTAL);
    const std::array<wxString, 6> top_items{L"Drucker", L"Slicer", wxString(L"Ger\u00E4te"), L"Material", L"Historie", L"Einstellungen"};
    for (size_t i = 0; i < top_items.size(); ++i) {
        auto* label = new wxStaticText(this, wxID_ANY, top_items[i]);
        const bool implemented_nav = i == 0 || i == 1;
        style_label(label, 11, i == 0, i == 0 ? PB_ACCENT : (implemented_nav ? PB_TEXT : PB_MUTED));
        if (implemented_nav) {
            label->SetCursor(wxCursor(wxCURSOR_HAND));
            label->Bind(wxEVT_LEFT_UP, [i](wxMouseEvent&) {
                if (!wxGetApp().mainframe)
                    return;
                wxGetApp().mainframe->select_tab(i == 0 ? MainFrame::tpMonitor : MainFrame::tp3DEditor);
            });
        }
        header->Add(label, 0, wxALL | wxALIGN_CENTER_VERTICAL, FromDIP(14));
    }
    header->AddStretchSpacer();
    auto* header_status = new wxStaticText(this, wxID_ANY, wxString(L"\u25CF  P2S Online"));
    style_label(header_status, 11, true, PB_OK);
    header->Add(header_status, 0, wxALL | wxALIGN_CENTER_VERTICAL, FromDIP(14));
    root->Add(header, 0, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(18));
    root->AddSpacer(FromDIP(10));

    auto* hero = new wxBoxSizer(wxHORIZONTAL);
    wxBoxSizer* body = nullptr;

    auto* printer_card = make_card(this, "BAMBU LAB P2S", body);
    printer_card->SetMinSize(wxSize(FromDIP(680), FromDIP(455)));
    m_printer_name = new wxStaticText(printer_card, wxID_ANY, "Bambu Lab P2S");
    style_label(m_printer_name, 24, true);
    body->Add(m_printer_name, 0, wxBOTTOM, FromDIP(4));
    auto* ready_text = new wxStaticText(printer_card, wxID_ANY, wxString(L"\u25CF  Bereit zum Drucken"));
    style_label(ready_text, 11, true, PB_OK);
    body->Add(ready_text, 0, wxBOTTOM, FromDIP(8));
    auto hero_bitmap = create_scaled_bitmap("printbench_hero_p2s_ams", this, 455);
    auto* hero_image = new wxStaticBitmap(printer_card, wxID_ANY, hero_bitmap);
    body->Add(hero_image, 1, wxALIGN_CENTER_HORIZONTAL | wxTOP | wxBOTTOM, FromDIP(4));
    auto* hero_state = new wxBoxSizer(wxHORIZONTAL);
    m_state = add_value(printer_card, hero_state, "Druckstatus");
    m_online = add_value(printer_card, hero_state, "Verbindung");
    m_wifi = add_value(printer_card, hero_state, "WLAN");
    body->Add(hero_state, 0, wxEXPAND | wxTOP, FromDIP(6));
    hero->Add(printer_card, 5, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* status_card = make_card(this, "DRUCKERSTATUS", body);
    m_status_ready = add_value(status_card, body, "Status");
    m_nozzle = add_value(status_card, body, wxString(L"D\u00FCse"));
    m_bed = add_value(status_card, body, "Druckbett");
    m_chamber = add_value(status_card, body, "Kammer");
    m_speed = add_value(status_card, body, "Geschwindigkeit");
    m_ams_summary = add_value(status_card, body, "AMS 2 Pro");
    hero->Add(status_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* right_hero = new wxBoxSizer(wxVERTICAL);
    auto* camera_card = make_card(this, "LIVE KAMERA", body);
    camera_card->SetMinSize(wxSize(FromDIP(440), FromDIP(300)));
    m_camera = add_value(camera_card, body, "Kamera");
    m_media_ctrl = new wxMediaCtrl2(camera_card);
    m_media_ctrl->SetMinSize(wxSize(FromDIP(440), FromDIP(235)));
    m_media_ctrl->SetBackgroundColour(*wxBLACK);
    m_media_play_ctrl = new MediaPlayCtrl(camera_card, m_media_ctrl, wxDefaultPosition, wxSize(-1, FromDIP(34)));
    m_media_play_ctrl->SetBackgroundColour(PB_CARD);
    body->Add(m_media_ctrl, 1, wxEXPAND | wxTOP, FromDIP(6));
    body->Add(m_media_play_ctrl, 0, wxEXPAND | wxTOP, FromDIP(4));
    right_hero->Add(camera_card, 1, wxEXPAND | wxBOTTOM, FromDIP(10));

    auto* quick_card = make_card(this, "SCHNELLSTEUERUNG", body);
    auto* controls = new wxBoxSizer(wxHORIZONTAL);
    m_print = new wxButton(quick_card, wxID_ANY, "DRUCKEN");
    m_pause_resume = new wxButton(quick_card, wxID_ANY, "PAUSE");
    m_stop = new wxButton(quick_card, wxID_ANY, "STOP");
    m_light = new wxButton(quick_card, wxID_ANY, "LICHT");
    for (auto* button : {m_print, m_pause_resume, m_stop, m_light}) {
        button->SetMinSize(wxSize(FromDIP(96), FromDIP(66)));
        wxFont button_font = button->GetFont();
        button_font.SetPointSize(10);
        button_font.SetWeight(wxFONTWEIGHT_BOLD);
        button->SetFont(button_font);
        button->SetForegroundColour(*wxWHITE);
    }
    m_print->SetBackgroundColour(wxColour("#075C46"));
    m_pause_resume->SetBackgroundColour(wxColour("#6A4512"));
    m_stop->SetBackgroundColour(wxColour("#651B2A"));
    m_light->SetBackgroundColour(wxColour("#0A4C92"));
    m_pause_resume->Enable(false);
    m_stop->Enable(false);
    m_light->Enable(false);
    controls->Add(m_print, 1, wxRIGHT, FromDIP(7));
    controls->Add(m_pause_resume, 1, wxRIGHT, FromDIP(7));
    controls->Add(m_stop, 1, wxRIGHT, FromDIP(7));
    controls->Add(m_light, 1);
    body->Add(controls, 0, wxEXPAND | wxBOTTOM, FromDIP(10));
    auto* speed_modes = new wxBoxSizer(wxHORIZONTAL);
    const std::array<wxString, 4> speed_names{L"Leise", L"Standard", L"Sport", L"Ludicrous"};
    for (size_t i = 0; i < m_speed_buttons.size(); ++i) {
        m_speed_buttons[i] = new wxButton(quick_card, wxID_ANY, speed_names[i]);
        m_speed_buttons[i]->SetMinSize(wxSize(FromDIP(76), FromDIP(34)));
        m_speed_buttons[i]->Enable(false);
        const auto level = static_cast<DevPrintingSpeedLevel>(static_cast<int>(i) + 1);
        m_speed_buttons[i]->Bind(wxEVT_BUTTON, [this, level](wxCommandEvent&) {
            if (m_machine != nullptr && m_machine->is_connected())
                m_machine->command_set_printing_speed(level);
        });
        speed_modes->Add(m_speed_buttons[i], 1, i + 1 < m_speed_buttons.size() ? wxRIGHT : 0, FromDIP(6));
    }
    body->Add(speed_modes, 0, wxEXPAND);
    right_hero->Add(quick_card, 0, wxEXPAND);
    hero->Add(right_hero, 3, wxEXPAND);

    root->Add(hero, 5, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(28));
    root->AddSpacer(FromDIP(12));

    auto* middle = new wxBoxSizer(wxHORIZONTAL);
    auto* print_card = make_card(this, "AKTUELLER DRUCK", body);
    m_job_name = add_value(print_card, body, "Datei");
    m_progress = add_value(print_card, body, "Fortschritt");
    m_layers = add_value(print_card, body, "Schichten");
    m_remaining = add_value(print_card, body, "Restzeit");
    middle->Add(print_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* temp_card = make_card(this, "TEMPERATUREN (LIVE)", body);
    temp_card->SetMinSize(wxSize(FromDIP(360), FromDIP(245)));
    m_temp_chart = new PrintbenchTempChart(temp_card);
    body->Add(m_temp_chart, 1, wxEXPAND | wxTOP, FromDIP(4));
    auto* temp_legend = new wxStaticText(temp_card, wxID_ANY, "DUSE  /  BETT  /  KAMMER");
    style_label(temp_legend, 8, true, PB_MUTED);
    body->Add(temp_legend, 0, wxTOP, FromDIP(6));
    middle->Add(temp_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* ams_card = make_card(this, "AMS 2 PRO", body);
    ams_card->SetMinSize(wxSize(FromDIP(390), FromDIP(245)));
    m_ams_environment = add_value(ams_card, body, "Environment");
    auto* slot_grid = new wxFlexGridSizer(2, 2, FromDIP(8), FromDIP(8));
    slot_grid->AddGrowableCol(0, 1);
    slot_grid->AddGrowableCol(1, 1);
    for (size_t i = 0; i < m_ams_slots.size(); ++i) {
        m_ams_slots[i] = new wxStaticText(ams_card, wxID_ANY, wxString::Format("SLOT %d  --", static_cast<int>(i + 1)));
        style_label(m_ams_slots[i], 10, true);
        m_ams_slots[i]->SetBackgroundColour(wxColour(8, 22, 33));
        m_ams_slots[i]->SetMinSize(wxSize(FromDIP(165), FromDIP(58)));
        slot_grid->Add(m_ams_slots[i], 1, wxEXPAND | wxALL, FromDIP(6));
    }
    body->Add(slot_grid, 0, wxEXPAND | wxTOP, FromDIP(10));
    middle->Add(ams_card, 1, wxEXPAND);

    root->Add(middle, 3, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(28));
    root->AddSpacer(FromDIP(12));

    auto* bottom = new wxBoxSizer(wxHORIZONTAL);
    auto* device_card = make_card(this, "GERAETESTATUS", body);
    auto* device_text = new wxStaticText(device_card, wxID_ANY, "Collector: NATIVE        LAN API: DIREKT\nTransport: Orca LAN     Modell: P2S\nCloud: NICHT ERFORDERLICH\nBambu Studio: NICHT ERFORDERLICH");
    style_label(device_text, 10, false, PB_MUTED);
    body->Add(device_text, 0, wxTOP, FromDIP(4));
    bottom->Add(device_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* history_card = make_card(this, "LETZTE DRUCKE", body);
    auto* history_text = new wxStaticText(history_card, wxID_ANY, "Lokale Druckhistorie wird direkt in PRINTBENCH gefuehrt. Noch keine Sitzungseintraege.");
    style_label(history_text, 10, false, PB_MUTED);
    history_text->Wrap(FromDIP(420));
    body->Add(history_text, 0, wxTOP, FromDIP(4));
    bottom->Add(history_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* action_card = make_card(this, "SYSTEM & AKTIONEN", body);
    auto* action_note = new wxStaticText(action_card, wxID_ANY,
        "Datei senden      Drucker kalibrieren\nDrucker neu starten      AMS trocknen\nFirmware pr\u00FCfen      Logs anzeigen");
    style_label(action_note, 9, false, PB_TEXT);
    body->Add(action_note, 0, wxEXPAND | wxTOP, FromDIP(4));
    bottom->Add(action_card, 1, wxEXPAND);

    m_print->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        if (wxGetApp().mainframe)
            wxGetApp().mainframe->select_tab(MainFrame::tp3DEditor);
    });
    m_pause_resume->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        if (m_machine == nullptr || !m_machine->is_connected())
            return;
        if (m_machine->print_status == "PAUSE")
            m_machine->command_task_resume();
        else if (m_machine->print_status == "RUNNING")
            m_machine->command_task_pause();
    });
    m_stop->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        if (m_machine == nullptr || !m_machine->is_connected())
            return;
        if (wxMessageBox("Aktuellen Druck wirklich stoppen?", "PRINTBENCH", wxYES_NO | wxICON_WARNING, this) == wxYES)
            m_machine->command_task_abort();
    });
    m_light->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        if (m_machine == nullptr || !m_machine->is_connected() || m_machine->GetLamp() == nullptr)
            return;
        auto* lamp = m_machine->GetLamp();
        lamp->CtrlSetChamberLight(lamp->IsChamberLightOn() ? DevLamp::LIGHT_EFFECT_OFF : DevLamp::LIGHT_EFFECT_ON);
    });

    root->Add(bottom, 2, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, FromDIP(28));
    shell->Add(root, 1, wxEXPAND);
    SetSizer(shell);
    Layout();
}

wxPanel* PrintbenchNativePanel::make_card(wxWindow* parent, const wxString& title, wxBoxSizer*& body)
{
    auto* card = new wxPanel(parent, wxID_ANY);
    card->SetBackgroundColour(PB_CARD);
    auto* outer = new wxBoxSizer(wxVERTICAL);
    auto* heading = new wxStaticText(card, wxID_ANY, title);
    style_label(heading, 11, true, PB_ACCENT);
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
    style_label(name, 10, false, PB_MUTED);
    auto* value = new wxStaticText(parent, wxID_ANY, "--");
    style_label(value, 12, true);
    row->Add(name, 1, wxALIGN_CENTER_VERTICAL);
    row->Add(value, 0, wxALIGN_CENTER_VERTICAL);
    sizer->Add(row, 0, wxEXPAND | wxBOTTOM, FromDIP(9));
    return value;
}

void PrintbenchNativePanel::refresh_from_machine(MachineObject* machine)
{
    const bool machine_changed = machine != m_machine;
    m_machine = machine;
    if (m_media_play_ctrl) {
        m_media_play_ctrl->SetMachineObject(machine);
        if (machine_changed && machine != nullptr && machine->is_connected())
            m_media_play_ctrl->jump_to_play();
    }
    apply_snapshot(m_collector.collect(machine));
}

void PrintbenchNativePanel::apply_snapshot(const PrintbenchSnapshot& s)
{
    // Binding FINAL-MASTER keeps the model name dominant; the live collector
    // still supplies the connection/state data below it.
    m_printer_name->SetLabel("Bambu Lab P2S");
    m_online->SetLabel(s.online ? "ONLINE / LAN" : "OFFLINE");
    m_online->SetForegroundColour(s.online ? PB_OK : PB_MUTED);
    m_state->SetLabel(wxString::FromUTF8(s.print_state));
    if (m_status_ready) {
        const bool ready = s.online && (s.print_state == "IDLE" || s.print_state == "FINISH" || s.print_state == "RUNNING" || s.print_state == "PAUSE");
        m_status_ready->SetLabel(ready ? L"Bereit" : wxString::FromUTF8(s.print_state));
        m_status_ready->SetForegroundColour(ready ? PB_OK : PB_TEXT);
    }
    m_wifi->SetLabel(s.wifi_signal.empty() ? "--" : wxString::FromUTF8(s.wifi_signal));

    const bool active_print = s.print_state == "RUNNING" || s.print_state == "PAUSE";
    if (m_job_name)
        m_job_name->SetLabel(active_print ? (s.job_name.empty() ? "Aktiver Druck" : wxString::FromUTF8(s.job_name)) : "Kein aktiver Druck");
    if (active_print) {
        m_progress->SetLabel(wxString::Format("%d %%", std::clamp(s.progress, 0, 100)));
        m_layers->SetLabel(wxString::Format("%d / %d", s.layer_current, s.layer_total));
        const int minutes = std::max(0, s.remaining_seconds / 60);
        m_remaining->SetLabel(wxString::Format("%d min", minutes));
    } else {
        m_progress->SetLabel("--");
        m_layers->SetLabel("--");
        m_remaining->SetLabel("--");
    }

    m_nozzle->SetLabel(format_temp(s.nozzle_c, s.nozzle_target_c));
    m_bed->SetLabel(format_temp(s.bed_c, s.bed_target_c));
    m_chamber->SetLabel(format_temp(s.chamber_c));
    static const std::array<wxString, 5> speed_labels{L"--", L"Leise (50 %)", L"Standard (100 %)", L"Sport (124 %)", L"Ludicrous (166 % )"};
    const int speed_idx = std::clamp(s.speed_level, 0, 4);
    if (m_speed) m_speed->SetLabel(speed_labels[static_cast<size_t>(speed_idx)]);
    if (m_ams_summary) {
        int loaded = 0;
        for (const auto& slot : s.ams_slots) loaded += slot.present ? 1 : 0;
        m_ams_summary->SetLabel(s.has_ams ? wxString::Format("%d/4 Slots geladen", loaded) : "Nicht verbunden");
    }
    if (m_temp_chart)
        m_temp_chart->push(s.nozzle_c, s.bed_c, s.chamber_c);

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

    const bool connected = m_machine != nullptr && m_machine->is_connected();
    const bool pausable = connected && (s.print_state == "RUNNING" || s.print_state == "PAUSE");
    if (m_pause_resume) {
        m_pause_resume->Enable(pausable);
        m_pause_resume->SetLabel(s.print_state == "PAUSE" ? "FORTSETZEN" : "PAUSE");
    }
    if (m_stop)
        m_stop->Enable(connected && (s.print_state == "RUNNING" || s.print_state == "PAUSE"));
    for (size_t i = 0; i < m_speed_buttons.size(); ++i) {
        if (!m_speed_buttons[i]) continue;
        const bool active = static_cast<int>(i) + 1 == s.speed_level;
        m_speed_buttons[i]->Enable(connected && (s.print_state == "RUNNING" || s.print_state == "PAUSE"));
        m_speed_buttons[i]->SetBackgroundColour(active ? wxColour("#0A63D8") : wxColour("#0B2639"));
        m_speed_buttons[i]->SetForegroundColour(*wxWHITE);
    }
    if (m_light) {
        auto* lamp = connected && m_machine != nullptr ? m_machine->GetLamp() : nullptr;
        m_light->Enable(lamp != nullptr);
        m_light->SetLabel(lamp != nullptr && lamp->IsChamberLightOn() ? "LICHT AUS" : "LICHT AN");
    }

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
