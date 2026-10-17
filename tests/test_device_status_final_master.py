from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CPP=(ROOT/'app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.cpp').read_text(encoding='utf-8')
HPP=(ROOT/'app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.hpp').read_text(encoding='utf-8')

def test_device_status_is_structured_grid_not_multiline_blob():
    assert 'std::array<wxStaticText*, 6> m_device_status_values' in HPP
    assert 'new wxFlexGridSizer(2, 3' in CPP
    assert 'LAN: OFFLINE        Transport: Orca LAN' not in CPP

def test_device_status_cells_are_live_and_truthful():
    for label in ('P2S','KAMERA','AMS 2 PRO','WLAN','LOKALBETRIEB','CLOUD'):
        assert f'L"{label}"' in CPP
    assert 'device_ok' in CPP
    assert 'SetForegroundColour(device_ok[i] ? PB_OK : PB_MUTED)' in CPP
    assert 'Nicht erforderlich' in CPP
