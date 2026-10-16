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
#include <fstream>
#include <wx/datetime.h>
#include <wx/filename.h>
#include <wx/stdpaths.h>
#include <wx/textfile.h>
#include <wx/dcbuffer.h>
#include <wx/sizer.h>
#include <wx/statline.h>
#include <wx/msgdlg.h>
#include <wx/gauge.h>

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

class PrintbenchProgressBar : public wxPanel
{
public:
    explicit PrintbenchProgressBar(wxWindow* parent)
        : wxPanel(parent, wxID_ANY)
    {
        SetBackgroundStyle(wxBG_STYLE_PAINT);
        SetMinSize(wxSize(-1, FromDIP(10)));
        Bind(wxEVT_PAINT, &PrintbenchProgressBar::on_paint, this);
    }

    void SetValue(int value)
    {
        const int next = std::clamp(value, 0, 100);
        if (next == m_value)
            return;
        m_value = next;
        Refresh(false);
    }

private:
    void on_paint(wxPaintEvent&)
    {
        wxAutoBufferedPaintDC dc(this);
        const wxSize size = GetClientSize();
        dc.SetBackground(wxBrush(PB_CARD));
        dc.Clear();
        if (size.x <= 0 || size.y <= 0)
            return;

        const int radius = std::max(1, FromDIP(3));
        dc.SetPen(*wxTRANSPARENT_PEN);
        dc.SetBrush(wxBrush(PB_BORDER));
        dc.DrawRoundedRectangle(0, 0, size.x, size.y, radius);
        if (m_value <= 0)
            return;

        const int fill_width = std::max(FromDIP(3), (size.x * m_value) / 100);
        dc.SetBrush(wxBrush(PB_ACCENT));
        dc.DrawRoundedRectangle(0, 0, fill_width, size.y, radius);
    }

    int m_value{0};
};

PrintbenchNativePanel::PrintbenchNativePanel(wxWindow* parent)
    : wxScrolledWindow(parent, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxVSCROLL | wxTAB_TRAVERSAL)
{
    SetBackgroundColour(PB_BG);
    SetScrollRate(0, FromDIP(12));

    auto* shell = new wxBoxSizer(wxHORIZONTAL);
    // FINAL-MASTER fills the available desktop viewport edge-to-edge.

    auto* sidebar = new wxPanel(this, wxID_ANY);
    sidebar->SetBackgroundColour(wxColour(4, 14, 24));
    sidebar->SetMinSize(wxSize(FromDIP(180), -1));
    auto* side = new wxBoxSizer(wxVERTICAL);
    auto* brand_row = new wxBoxSizer(wxHORIZONTAL);
    auto brand_icon_bitmap = create_scaled_bitmap("printbench_app_icon_32", sidebar, 18);
    auto* brand_icon = new wxStaticBitmap(sidebar, wxID_ANY, brand_icon_bitmap);
    auto* brand = new wxStaticText(sidebar, wxID_ANY, "PRINTBENCH");
    style_label(brand, 18, true);
    brand_row->Add(brand_icon, 0, wxRIGHT | wxALIGN_CENTER_VERTICAL, FromDIP(8));
    brand_row->Add(brand, 0, wxALIGN_CENTER_VERTICAL);
    side->Add(brand_row, 0, wxLEFT | wxRIGHT | wxTOP, FromDIP(16));
    auto* brand_sub = new wxStaticText(sidebar, wxID_ANY, wxString(L"Studio  \u2022  JL1976 Software"));
    style_label(brand_sub, 9, false, PB_ACCENT);
    side->Add(brand_sub, 0, wxLEFT | wxRIGHT | wxTOP | wxBOTTOM, FromDIP(16));
    const std::array<wxString, 13> nav_items{
        wxString(L"\u00DCbersicht"), L"Live Ansicht", L"Steuerung", L"AMS 2 Pro", L"Material",
        wxString(L"Druckauftr\u00E4ge"), L"Historie", L"Dateien", L"Kamera", wxString(L"Ger\u00E4te-Setup"),
        L"Netzwerk", L"Sicherheit", L"Diagnose"};
    // Reuse Orca's native vector resources so the FINAL-MASTER rail stays crisp
    // at every Windows scaling level instead of falling back to text glyphs.
    const std::array<const char*, 13> nav_icons{
        "monitor", "monitor_camera", "monitor_axis_home_icon", "ams_setting_normal", "filament",
        "print_control_resume", "print_info_time", "topbar_file", "camera_setting", "printer",
        "printer_in_lan", "info", "calib_sf"};
    for (size_t i = 0; i < nav_items.size(); ++i) {
        auto* item = new wxPanel(sidebar, wxID_ANY);
        item->SetBackgroundColour(i == 0 ? wxColour(8, 102, 218) : sidebar->GetBackgroundColour());
        auto* item_sizer = new wxBoxSizer(wxHORIZONTAL);
        auto icon_bitmap = create_scaled_bitmap(nav_icons[i], item, 14);
        auto* icon = new wxStaticBitmap(item, wxID_ANY, icon_bitmap);
        auto* label = new wxStaticText(item, wxID_ANY, nav_items[i]);
        style_label(label, 10, i == 0, i == 0 ? *wxWHITE : PB_TEXT);
        item_sizer->Add(icon, 0, wxLEFT | wxALIGN_CENTER_VERTICAL, FromDIP(9));
        item_sizer->Add(label, 1, wxLEFT | wxRIGHT | wxTOP | wxBOTTOM | wxALIGN_CENTER_VERTICAL,
                        FromDIP(8));
        item->SetSizer(item_sizer);
        side->Add(item, 0, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, FromDIP(3));
    }
    side->AddStretchSpacer();
    auto* side_p2s = new wxStaticText(sidebar, wxID_ANY, wxString(L"\u25CF  Bambu Lab P2S"));
    style_label(side_p2s, 9, true, PB_OK);
    side->Add(side_p2s, 0, wxLEFT | wxRIGHT | wxBOTTOM, FromDIP(16));
    auto* side_ams = new wxStaticText(sidebar, wxID_ANY, wxString(L"\u25CF  AMS 2 Pro"));
    style_label(side_ams, 9, true, PB_OK);
    side->Add(side_ams, 0, wxLEFT | wxRIGHT | wxBOTTOM, FromDIP(16));
    auto* system_item = new wxStaticText(sidebar, wxID_ANY, wxString(L"\u2699  System"));
    style_label(system_item, 11, false, PB_TEXT);
    side->Add(system_item, 0, wxALL, FromDIP(16));
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
        header->Add(label, 0, wxALL | wxALIGN_CENTER_VERTICAL, FromDIP(10));
    }
    header->AddStretchSpacer();
    m_header_status = new wxStaticText(this, wxID_ANY, wxString(L"\u25CF  P2S Offline"));
    style_label(m_header_status, 11, true, PB_MUTED);
    header->Add(m_header_status, 0, wxALL | wxALIGN_CENTER_VERTICAL, FromDIP(10));
    root->Add(header, 0, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(10));
    root->AddSpacer(FromDIP(6));

    auto* hero = new wxBoxSizer(wxHORIZONTAL);
    wxBoxSizer* body = nullptr;

    auto* printer_card = make_card(this, "BAMBU LAB P2S", body);
    printer_card->SetMinSize(wxSize(FromDIP(390), FromDIP(330)));
    m_printer_name = new wxStaticText(printer_card, wxID_ANY, "Bambu Lab P2S");
    style_label(m_printer_name, 20, true);
    body->Add(m_printer_name, 0, wxBOTTOM, FromDIP(4));
    m_ready_banner = new wxStaticText(printer_card, wxID_ANY, wxString(L"\u25CF  Offline"));
    style_label(m_ready_banner, 11, true, PB_MUTED);
    body->Add(m_ready_banner, 0, wxBOTTOM, FromDIP(8));
    auto hero_bitmap = create_scaled_bitmap("printbench_hero_p2s_ams", this, 560);
    auto* hero_image = new wxStaticBitmap(printer_card, wxID_ANY, hero_bitmap);
    body->Add(hero_image, 1, wxALIGN_CENTER_HORIZONTAL | wxTOP | wxBOTTOM, FromDIP(4));
    auto* hero_state = new wxBoxSizer(wxHORIZONTAL);
    m_state = add_value(printer_card, hero_state, "Druckstatus");
    m_online = add_value(printer_card, hero_state, "Verbindung");
    m_wifi = add_value(printer_card, hero_state, "WLAN");
    body->Add(hero_state, 0, wxEXPAND | wxTOP, FromDIP(6));
    hero->Add(printer_card, 42, wxEXPAND | wxRIGHT, FromDIP(8));

    auto* status_card = make_card(this, "DRUCKERSTATUS", body);
    m_status_ready = add_value(status_card, body, "Status");
    m_nozzle = add_value(status_card, body, wxString(L"D\u00FCse"));
    m_bed = add_value(status_card, body, "Druckbett");
    m_chamber = add_value(status_card, body, "Kammer");
    m_speed = add_value(status_card, body, "Geschwindigkeit");
    m_ams_summary = add_value(status_card, body, "AMS 2 Pro");
    status_card->SetMinSize(wxSize(FromDIP(230), FromDIP(330)));
    hero->Add(status_card, 24, wxEXPAND | wxRIGHT, FromDIP(8));

    auto* right_hero = new wxBoxSizer(wxVERTICAL);
    auto* camera_card = make_card(this, "LIVE KAMERA", body);
    camera_card->SetMinSize(wxSize(FromDIP(330), FromDIP(205)));
    m_camera = add_value(camera_card, body, "Kamera");
    m_media_ctrl = new wxMediaCtrl2(camera_card);
    m_media_ctrl->SetMinSize(wxSize(FromDIP(330), FromDIP(155)));
    m_media_ctrl->SetBackgroundColour(*wxBLACK);
    m_media_play_ctrl = new MediaPlayCtrl(camera_card, m_media_ctrl, wxDefaultPosition, wxSize(-1, FromDIP(34)));
    m_media_play_ctrl->SetBackgroundColour(PB_CARD);
    body->Add(m_media_ctrl, 1, wxEXPAND | wxTOP, FromDIP(6));
    body->Add(m_media_play_ctrl, 0, wxEXPAND | wxTOP, FromDIP(4));
    right_hero->Add(camera_card, 1, wxEXPAND | wxBOTTOM, FromDIP(8));

    auto* quick_card = make_card(this, "SCHNELLSTEUERUNG", body);
    auto* controls = new wxBoxSizer(wxHORIZONTAL);
    m_print = new wxButton(quick_card, wxID_ANY, wxString(L"\u25B6\nDRUCKEN"));
    m_pause_resume = new wxButton(quick_card, wxID_ANY, wxString(L"\u2161\nPAUSE"));
    m_stop = new wxButton(quick_card, wxID_ANY, wxString(L"\u25A0\nSTOP"));
    m_light = new wxButton(quick_card, wxID_ANY, wxString(L"\u25CF\nLICHT"));
    for (auto* button : {m_print, m_pause_resume, m_stop, m_light}) {
        button->SetMinSize(wxSize(FromDIP(72), FromDIP(54)));
        wxFont button_font = button->GetFont();
        button_font.SetPointSize(9);
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
    hero->Add(right_hero, 34, wxEXPAND);

    root->Add(hero, 5, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(12));
    root->AddSpacer(FromDIP(8));

    auto* middle = new wxBoxSizer(wxHORIZONTAL);
    auto* print_card = make_card(this, "AKTUELLER DRUCK", body);
    auto* job_row = new wxBoxSizer(wxHORIZONTAL);
    auto job_bitmap = create_scaled_bitmap("menu_obj_cube", print_card, 42);
    auto* job_icon = new wxStaticBitmap(print_card, wxID_ANY, job_bitmap);
    auto* job_text = new wxBoxSizer(wxVERTICAL);
    m_job_name = new wxStaticText(print_card, wxID_ANY, "Kein aktiver Druck");
    style_label(m_job_name, 13, true, PB_TEXT);
    auto* job_meta = new wxStaticText(print_card, wxID_ANY, "Bambu Lab P2S  •  lokaler Druckauftrag");
    style_label(job_meta, 9, false, PB_MUTED);
    job_text->Add(m_job_name, 0, wxBOTTOM, FromDIP(3));
    job_text->Add(job_meta, 0);
    job_row->Add(job_icon, 0, wxRIGHT | wxALIGN_CENTER_VERTICAL, FromDIP(10));
    job_row->Add(job_text, 1, wxALIGN_CENTER_VERTICAL);
    body->Add(job_row, 0, wxEXPAND | wxBOTTOM, FromDIP(10));

    m_progress_gauge = new PrintbenchProgressBar(print_card);
    body->Add(m_progress_gauge, 0, wxEXPAND | wxBOTTOM, FromDIP(10));

    auto* print_metrics = new wxBoxSizer(wxHORIZONTAL);
    auto add_metric = [&](const wxString& caption, wxStaticText*& value) {
        auto* col = new wxBoxSizer(wxVERTICAL);
        auto* name = new wxStaticText(print_card, wxID_ANY, caption);
        style_label(name, 8, true, PB_MUTED);
        value = new wxStaticText(print_card, wxID_ANY, "--");
        style_label(value, 12, true, PB_TEXT);
        col->Add(name, 0, wxBOTTOM, FromDIP(2));
        col->Add(value, 0);
        print_metrics->Add(col, 1, wxRIGHT, FromDIP(8));
    };
    add_metric("FORTSCHRITT", m_progress);
    add_metric("SCHICHTEN", m_layers);
    add_metric("RESTZEIT", m_remaining);
    body->Add(print_metrics, 0, wxEXPAND);
    middle->Add(print_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* temp_card = make_card(this, "TEMPERATUREN (LIVE)", body);
    temp_card->SetMinSize(wxSize(FromDIP(280), FromDIP(190)));
    auto* temp_values = new wxBoxSizer(wxHORIZONTAL);
    const std::array<wxString, 3> temp_names{L"D\u00DCSE", L"BETT", L"KAMMER"};
    const std::array<wxColour, 3> temp_colours{PB_ACCENT, wxColour(210,222,231), wxColour(90,145,165)};
    for (size_t i = 0; i < m_temp_values.size(); ++i) {
        auto* col = new wxBoxSizer(wxVERTICAL);
        auto* name = new wxStaticText(temp_card, wxID_ANY, temp_names[i]);
        style_label(name, 8, true, temp_colours[i]);
        m_temp_values[i] = new wxStaticText(temp_card, wxID_ANY, "-- C");
        style_label(m_temp_values[i], 12, true);
        col->Add(name, 0, wxBOTTOM, FromDIP(2));
        col->Add(m_temp_values[i], 0);
        temp_values->Add(col, 1, wxRIGHT, i + 1 < m_temp_values.size() ? FromDIP(10) : 0);
    }
    body->Add(temp_values, 0, wxEXPAND | wxBOTTOM, FromDIP(8));
    m_temp_chart = new PrintbenchTempChart(temp_card);
    body->Add(m_temp_chart, 1, wxEXPAND | wxTOP, FromDIP(4));
    middle->Add(temp_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* ams_card = make_card(this, "AMS 2 PRO", body);
    ams_card->SetMinSize(wxSize(FromDIP(300), FromDIP(190)));
    m_ams_environment = add_value(ams_card, body, "Environment");
    auto* slot_grid = new wxFlexGridSizer(1, 4, FromDIP(8), FromDIP(8));
    for (int col = 0; col < 4; ++col)
        slot_grid->AddGrowableCol(col, 1);
    for (size_t i = 0; i < m_ams_slots.size(); ++i) {
        m_ams_slots[i] = new wxStaticText(ams_card, wxID_ANY, wxString::Format("SLOT %d  --", static_cast<int>(i + 1)));
        style_label(m_ams_slots[i], 10, true);
        m_ams_slots[i]->SetBackgroundColour(wxColour(8, 22, 33));
        m_ams_slots[i]->SetMinSize(wxSize(FromDIP(72), FromDIP(72)));
        slot_grid->Add(m_ams_slots[i], 1, wxEXPAND | wxALL, FromDIP(6));
    }
    body->Add(slot_grid, 0, wxEXPAND | wxTOP, FromDIP(10));
    middle->Add(ams_card, 1, wxEXPAND);

    root->Add(middle, 3, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(12));
    root->AddSpacer(FromDIP(8));

    auto* bottom = new wxBoxSizer(wxHORIZONTAL);
    auto* device_card = make_card(this, "GERAETESTATUS", body);
    m_device_status = new wxStaticText(device_card, wxID_ANY,
        "LAN: OFFLINE        Transport: Orca LAN\nP2S: Nicht verbunden     Kamera: --\nAMS 2 Pro: --             WLAN: --\nLokalbetrieb: AKTIV       Cloud: NICHT ERFORDERLICH");
    style_label(m_device_status, 10, false, PB_MUTED);
    body->Add(m_device_status, 0, wxTOP, FromDIP(4));
    bottom->Add(device_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* history_card = make_card(this, "LETZTE DRUCKE", body);
    for (size_t i = 0; i < m_history_rows.size(); ++i) {
        m_history_rows[i] = new wxStaticText(history_card, wxID_ANY, i == 0 ? "Noch keine lokalen Druckabschluesse." : "");
        style_label(m_history_rows[i], 9, i == 0, i == 0 ? PB_MUTED : PB_TEXT);
        body->Add(m_history_rows[i], 0, wxEXPAND | wxBOTTOM, FromDIP(5));
    }
    bottom->Add(history_card, 1, wxEXPAND | wxRIGHT, FromDIP(10));

    auto* action_card = make_card(this, "SYSTEM & AKTIONEN", body);
    auto* action_grid = new wxFlexGridSizer(2, 3, FromDIP(6), FromDIP(6));
    for (int col = 0; col < 3; ++col)
        action_grid->AddGrowableCol(col, 1);
    const std::array<wxString, 6> action_names{
        L"Datei senden", L"Kalibrieren", L"Neustart", L"AMS trocknen", L"Firmware", L"Logs anzeigen"};
    std::array<wxButton*, 6> action_buttons{};
    for (size_t i = 0; i < action_buttons.size(); ++i) {
        action_buttons[i] = new wxButton(action_card, wxID_ANY, action_names[i]);
        action_buttons[i]->SetMinSize(wxSize(FromDIP(95), FromDIP(34)));
        action_buttons[i]->SetBackgroundColour(wxColour(8, 37, 55));
        action_buttons[i]->SetForegroundColour(PB_TEXT);
        action_grid->Add(action_buttons[i], 1, wxEXPAND);
    }
    action_buttons[0]->Bind(wxEVT_BUTTON, [](wxCommandEvent&) {
        if (wxGetApp().mainframe)
            wxGetApp().mainframe->select_tab(MainFrame::tp3DEditor);
    });
    action_buttons[5]->Bind(wxEVT_BUTTON, [](wxCommandEvent&) {
        if (wxGetApp().mainframe)
            wxGetApp().mainframe->show_log_window();
    });
    for (size_t i : {size_t(1), size_t(2), size_t(3), size_t(4)}) {
        action_buttons[i]->Enable(false);
        action_buttons[i]->SetToolTip("Noch nicht verfuegbar");
    }
    body->Add(action_grid, 0, wxEXPAND | wxTOP, FromDIP(4));
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

    root->Add(bottom, 2, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, FromDIP(12));
    shell->Add(root, 1, wxEXPAND);
    SetSizer(shell);
    load_history();
    update_history_ui();
    Layout();
}

wxPanel* PrintbenchNativePanel::make_card(wxWindow* parent, const wxString& title, wxBoxSizer*& body)
{
    auto* card = new wxPanel(parent, wxID_ANY);
    card->SetBackgroundColour(PB_CARD);
    auto* outer = new wxBoxSizer(wxVERTICAL);
    auto* heading = new wxStaticText(card, wxID_ANY, title);
    style_label(heading, 11, true, PB_ACCENT);
    outer->Add(heading, 0, wxALL, FromDIP(10));
    auto* line = new wxStaticLine(card, wxID_ANY);
    line->SetForegroundColour(PB_BORDER);
    outer->Add(line, 0, wxEXPAND | wxLEFT | wxRIGHT, FromDIP(10));
    body = new wxBoxSizer(wxVERTICAL);
    outer->Add(body, 1, wxEXPAND | wxALL, FromDIP(10));
    card->SetSizer(outer);
    card->SetMinSize(wxSize(FromDIP(180), FromDIP(120)));
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
    sizer->Add(row, 0, wxEXPAND | wxBOTTOM, FromDIP(6));
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
    observe_history(s);
    // Binding FINAL-MASTER keeps the model name dominant; the live collector
    // still supplies the connection/state data below it.
    m_printer_name->SetLabel("Bambu Lab P2S");
    if (m_header_status) {
        m_header_status->SetLabel(s.online ? wxString(L"\u25CF  P2S Online") : wxString(L"\u25CF  P2S Offline"));
        m_header_status->SetForegroundColour(s.online ? PB_OK : PB_MUTED);
    }
    m_online->SetLabel(s.online ? "ONLINE / LAN" : "OFFLINE");
    m_online->SetForegroundColour(s.online ? PB_OK : PB_MUTED);
    m_state->SetLabel(wxString::FromUTF8(s.print_state));
    const bool ready = s.online && (s.print_state == "IDLE" || s.print_state == "FINISH" || s.print_state == "RUNNING" || s.print_state == "PAUSE");
    if (m_status_ready) {
        m_status_ready->SetLabel(ready ? L"Bereit" : (s.online ? wxString::FromUTF8(s.print_state) : L"Offline"));
        m_status_ready->SetForegroundColour(ready ? PB_OK : (s.online ? PB_TEXT : PB_MUTED));
    }
    if (m_ready_banner) {
        const wxString banner = ready ? wxString(L"\u25CF  Bereit zum Drucken")
                                      : (s.online ? wxString(L"\u25CF  ") + wxString::FromUTF8(s.print_state) : wxString(L"\u25CF  Offline"));
        m_ready_banner->SetLabel(banner);
        m_ready_banner->SetForegroundColour(ready ? PB_OK : (s.online ? PB_TEXT : PB_MUTED));
    }
    m_wifi->SetLabel(s.wifi_signal.empty() ? "--" : wxString::FromUTF8(s.wifi_signal));
    if (m_device_status) {
        const wxString lan = s.online ? "ONLINE" : "OFFLINE";
        const wxString p2s = s.online ? "Verbunden" : "Nicht verbunden";
        const wxString camera_state = s.has_camera ? "READY" : "--";
        const wxString ams_state = s.has_ams ? "VERBUNDEN" : "--";
        const wxString wifi = s.wifi_signal.empty() ? "--" : wxString::FromUTF8(s.wifi_signal);
        m_device_status->SetLabel(wxString::Format(
            "LAN: %s        Transport: Orca LAN\nP2S: %s     Kamera: %s\nAMS 2 Pro: %s             WLAN: %s\nLokalbetrieb: AKTIV       Cloud: NICHT ERFORDERLICH",
            lan, p2s, camera_state, ams_state, wifi));
        m_device_status->SetForegroundColour(s.online ? PB_TEXT : PB_MUTED);
    }

    const bool active_print = s.print_state == "RUNNING" || s.print_state == "PAUSE";
    if (m_job_name)
        m_job_name->SetLabel(active_print ? (s.job_name.empty() ? "Aktiver Druck" : wxString::FromUTF8(s.job_name)) : "Kein aktiver Druck");
    const int progress_value = active_print ? std::clamp(s.progress, 0, 100) : 0;
    if (m_progress_gauge)
        m_progress_gauge->SetValue(progress_value);
    if (active_print) {
        m_progress->SetLabel(wxString::Format("%d %%", progress_value));
        m_progress->SetForegroundColour(PB_OK);
        m_layers->SetLabel(wxString::Format("%d / %d", s.layer_current, s.layer_total));
        const int minutes = std::max(0, s.remaining_seconds / 60);
        if (minutes >= 60)
            m_remaining->SetLabel(wxString::Format("%d h %02d min", minutes / 60, minutes % 60));
        else
            m_remaining->SetLabel(wxString::Format("%d min", minutes));
    } else {
        m_progress->SetLabel("--");
        m_progress->SetForegroundColour(PB_TEXT);
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
    if (m_temp_values[0]) m_temp_values[0]->SetLabel(wxString::Format("%d C", s.nozzle_c));
    if (m_temp_values[1]) m_temp_values[1]->SetLabel(wxString::Format("%d C", s.bed_c));
    if (m_temp_values[2]) m_temp_values[2]->SetLabel(wxString::Format("%.0f C", s.chamber_c));
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
        wxString text = wxString::Format("SLOT %d\n", static_cast<int>(i + 1));
        if (slot.present) {
            text += slot.material.empty() ? "FILAMENT" : wxString::FromUTF8(slot.material);
            if (slot.remain >= 0)
                text += wxString::Format("\n%d %%", slot.remain);
        } else {
            text += "EMPTY\n--";
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

void PrintbenchNativePanel::observe_history(const PrintbenchSnapshot& s)
{
    const bool active = s.print_state == "RUNNING" || s.print_state == "PAUSE";
    const bool was_active = m_previous_print_state == "RUNNING" || m_previous_print_state == "PAUSE";

    if (active && !m_history_tracking) {
        m_history_tracking = true;
        m_history_started = std::chrono::steady_clock::now();
        m_history_job_name = s.job_name.empty() ? "Druckauftrag" : wxString::FromUTF8(s.job_name);
    } else if (active && !s.job_name.empty()) {
        m_history_job_name = wxString::FromUTF8(s.job_name);
    }

    if (m_history_tracking && was_active && !active && s.online) {
        const int observed_seconds = static_cast<int>(std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::steady_clock::now() - m_history_started).count());
        wxString status = "Beendet";
        if (s.print_state == "FINISH")
            status = "Fertig";
        else if (s.print_state == "FAILED" || s.print_state == "ERROR")
            status = "Fehler";
        else if (s.print_state == "CANCEL" || s.print_state == "CANCELLED")
            status = "Abgebrochen";
        append_history(m_history_job_name, status, observed_seconds);
        m_history_tracking = false;
        m_history_job_name.clear();
    }

    // Going offline is not proof that a print ended. Keep tracking and wait for
    // a later online state instead of manufacturing a false history entry.
    if (s.online)
        m_previous_print_state = s.print_state;
}

void PrintbenchNativePanel::append_history(const wxString& job_name, const wxString& status, int observed_seconds)
{
    HistoryEntry entry;
    entry.finished_at = wxDateTime::Now().Format("%d.%m. %H:%M");
    entry.status = status;
    entry.job_name = job_name.empty() ? "Druckauftrag" : job_name;
    entry.observed_seconds = std::max(0, observed_seconds);
    m_history.push_front(entry);
    while (m_history.size() > 20)
        m_history.pop_back();
    save_history();
    update_history_ui();
}

void PrintbenchNativePanel::update_history_ui()
{
    for (auto* row : m_history_rows) {
        if (row) {
            row->SetLabel("");
            row->SetForegroundColour(PB_TEXT);
        }
    }
    if (m_history.empty()) {
        if (m_history_rows[0]) {
            m_history_rows[0]->SetLabel("Noch keine lokalen Druckabschluesse.");
            m_history_rows[0]->SetForegroundColour(PB_MUTED);
        }
        return;
    }

    for (size_t i = 0; i < std::min(m_history_rows.size(), m_history.size()); ++i) {
        const auto& entry = m_history[i];
        const int minutes = entry.observed_seconds / 60;
        wxString duration = minutes >= 60
            ? wxString::Format("%dh %02dm", minutes / 60, minutes % 60)
            : wxString::Format("%dm", minutes);
        const wxString marker = entry.status == "Fertig" ? wxString(L"\u2713") : wxString(L"\u2022");
        m_history_rows[i]->SetLabel(wxString::Format("%s  %s   %s   %s", marker, entry.job_name, entry.finished_at, duration));
        m_history_rows[i]->SetForegroundColour(entry.status == "Fertig" ? PB_OK : PB_TEXT);
    }
}

void PrintbenchNativePanel::load_history()
{
    const wxString dir = wxStandardPaths::Get().GetUserLocalDataDir();
    const wxString path = wxFileName(dir, "printbench-print-history.tsv").GetFullPath();
    if (!wxFileExists(path))
        return;

    wxTextFile file;
    if (!file.Open(path))
        return;
    for (size_t i = 0; i < file.GetLineCount() && m_history.size() < 20; ++i) {
        const wxArrayString fields = wxSplit(file.GetLine(i), '\t', '\0');
        if (fields.size() != 4)
            continue;
        long seconds = 0;
        fields[2].ToLong(&seconds);
        HistoryEntry entry{fields[0], fields[1], fields[3], static_cast<int>(std::max(0L, seconds))};
        m_history.push_back(entry);
    }
    file.Close();
}

void PrintbenchNativePanel::save_history() const
{
    const wxString dir = wxStandardPaths::Get().GetUserLocalDataDir();
    if (!wxDirExists(dir))
        wxFileName::Mkdir(dir, wxS_DIR_DEFAULT, wxPATH_MKDIR_FULL);
    const wxString path = wxFileName(dir, "printbench-print-history.tsv").GetFullPath();
    wxTextFile file;
    if (wxFileExists(path)) {
        if (!file.Open(path))
            return;
        file.Clear();
    } else if (!file.Create(path)) {
        return;
    }

    for (const auto& entry : m_history) {
        wxString safe_name = entry.job_name;
        safe_name.Replace("\t", " ");
        safe_name.Replace("\r", " ");
        safe_name.Replace("\n", " ");
        file.AddLine(wxString::Format("%s\t%s\t%d\t%s", entry.finished_at, entry.status, entry.observed_seconds, safe_name));
    }
    file.Write();
    file.Close();
}

} // namespace GUI
} // namespace Slic3r
