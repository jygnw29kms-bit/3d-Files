from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = (ROOT / 'app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.cpp').read_text(encoding='utf-8')


def test_final_master_dashboard_fills_device_viewport():
    assert 'root->SetMinSize(wxSize(FromDIP(1640), -1));' not in PANEL
    assert 'shell->Add(root, 1, wxEXPAND);' in PANEL
    assert 'shell->AddStretchSpacer(1);' not in PANEL


def test_final_master_branding_is_native_and_visible():
    assert 'printbench_app_icon_32' in PANEL
    assert 'PRINTBENCH' in PANEL
    assert 'JL1976 Software' in PANEL


def test_final_master_keeps_dominant_p2s_hero():
    assert 'create_scaled_bitmap("printbench_hero_p2s_ams", this, 560)' in PANEL
    assert 'hero->Add(printer_card, 42' in PANEL
