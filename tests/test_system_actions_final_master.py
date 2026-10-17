from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CPP=(ROOT/'app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.cpp').read_text(encoding='utf-8')

def test_system_actions_have_native_icons_and_master_density():
    assert 'action_icons' in CPP
    assert 'SetBitmap(create_scaled_bitmap(action_icons[i]' in CPP
    assert 'FromDIP(118), FromDIP(42)' in CPP
    assert 'wxFONTWEIGHT_BOLD' in CPP

def test_verified_system_actions_are_wired():
    assert 'select_tab(MainFrame::tp3DEditor)' in CPP
    assert 'select_tab(MainFrame::tpCalibration)' in CPP
    assert 'show_log_window()' in CPP

def test_unverified_device_actions_stay_disabled_with_reason():
    assert 'Kein verifizierter P2S-Neustartbefehl' in CPP
    assert 'AMS-Trocknen benoetigt Material-, Temperatur- und Zeitparameter' in CPP
    assert 'Firmware-Verwaltung wird erst nach verifiziertem P2S-Updatepfad aktiviert' in CPP
