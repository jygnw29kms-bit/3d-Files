from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PANEL=(ROOT/"app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.cpp").read_text(encoding="utf-8")
HEADER=(ROOT/"app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.hpp").read_text(encoding="utf-8")


def test_master_sidebar_rows_are_interactive():
    assert 'std::array<wxPanel*, 13> m_nav_rows' in HEADER
    assert 'hit_target->Bind(wxEVT_LEFT_UP, nav_handler)' in PANEL
    assert 'activate_nav(index);' in PANEL


def test_sidebar_routes_to_real_native_sections():
    for target in ('m_camera_card', 'm_quick_card', 'm_ams_card', 'm_print_card', 'm_history_card'):
        assert f'scroll_to({target})' in PANEL
    assert 'select_tab(MainFrame::tpMultiDevice)' in PANEL
    assert 'show_log_window()' in PANEL


def test_top_master_navigation_is_not_decorative():
    assert 'case 5: wxGetApp().open_preferences();' in PANEL
    assert 'case 2: if (wxGetApp().mainframe) wxGetApp().mainframe->select_tab(MainFrame::tpMultiDevice)' in PANEL
    assert 'case 4: handle_nav(6)' in PANEL
