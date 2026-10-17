from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PANEL=(ROOT/"app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.cpp").read_text(encoding="utf-8")
HEADER=(ROOT/"app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.hpp").read_text(encoding="utf-8")
COLLECTOR=(ROOT/"app/orcaslicer/src/slic3r/GUI/PrintbenchCollector.cpp").read_text(encoding="utf-8")

def test_camera_controls_use_native_machine_commands():
    assert 'command_ipcam_record(!m_machine->camera_recording_when_printing)' in PANEL
    assert 'command_ipcam_timelapse(!m_machine->camera_timelapse)' in PANEL
    assert 'm_machine->printer_type == "N7"' in PANEL
    assert 'command_ipcam_resolution_set(modes[index])' in PANEL

def test_camera_controls_use_explicit_ids_and_central_handler():
    for name in ('ID_PB_CAMERA_RECORD','ID_PB_CAMERA_TIMELAPSE','ID_PB_CAMERA_RESOLUTION'):
        assert name in PANEL
    assert 'void PrintbenchNativePanel::on_camera_action(wxCommandEvent& event)' in PANEL
    assert PANEL.count('Bind(wxEVT_BUTTON, &PrintbenchNativePanel::on_camera_action') == 3
    assert 'on_camera_action(wxCommandEvent& event);' in HEADER

def test_camera_controls_follow_snapshot_state():
    assert 's.camera_recording ? "STOP AUFNAHME" : "AUFNAHME"' in PANEL
    assert 's.camera_timelapse ? "TIMELAPSE AUS" : "TIMELAPSE"' in PANEL
    assert 'camera_resolution_supported.size() > 1' in PANEL

def test_camera_snapshot_uses_ipcam_record_setting():
    assert 'out.camera_recording = machine->camera_recording_when_printing;' in COLLECTOR
    assert 'out.camera_recording = machine->camera_recording;' not in COLLECTOR

def test_camera_controls_exist_as_native_buttons():
    for name in ('m_camera_record','m_camera_timelapse','m_camera_resolution'):
        assert name in HEADER and name in PANEL


def test_p2s_n7_does_not_expose_dead_direct_timelapse_switch():
    collector=(ROOT/'app/orcaslicer/src/slic3r/GUI/PrintbenchCollector.cpp').read_text(encoding='utf-8')
    header=(ROOT/'app/orcaslicer/src/slic3r/GUI/PrintbenchCollector.hpp').read_text(encoding='utf-8')
    assert 'camera_timelapse_control_supported' in header
    assert 'machine->is_support_timelapse && machine->printer_type != "N7"' in collector
    assert 's.camera_timelapse_control_supported' in PANEL
    assert 'P2S-Firmware meldet Timelapse, lehnt direkte LAN-Steuerung jedoch ab' in PANEL
