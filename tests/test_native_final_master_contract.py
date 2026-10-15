from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'app' / 'orcaslicer' / 'src' / 'slic3r' / 'GUI'
MONITOR = (GUI / 'Monitor.cpp').read_text(encoding='utf-8')
PANEL = (GUI / 'PrintbenchNativePanel.cpp').read_text(encoding='utf-8')
SPEC = (ROOT / 'docs' / 'design' / 'PRINTBENCH_FINAL_MASTER.md').read_text(encoding='utf-8')


def test_printbench_device_surface_is_native():
    assert 'new PrintbenchNativePanel' in MONITOR
    assert 'AddPage(m_printbench_panel' in MONITOR
    assert 'SetSelection(PT_PRINTBENCH)' in MONITOR
    assert 'PrinterWebView' not in PANEL
    assert 'printbench-pi.local' not in PANEL
    assert 'http://' not in PANEL
    assert 'https://' not in PANEL


def test_native_panel_covers_final_master_primary_regions():
    required_labels = [
        'P2S + AMS 2 PRO',
        'DRUCKERSTATUS',
        'LIVE KAMERA',
        'AKTUELLER DRUCK',
        'TEMPERATUREN (LIVE)',
        'AMS 2 PRO',
        'GERAETESTATUS',
        'LETZTE DRUCKE',
        'SYSTEM & AKTIONEN',
    ]
    for label in required_labels:
        assert label in PANEL, label


def test_native_panel_uses_live_machine_state_and_native_media():
    required_tokens = [
        'PrintbenchCollector',
        'MachineObject',
        'wxMediaCtrl2',
        'MediaPlayCtrl',
        'SetMachineObject(machine)',
        'command_task_pause',
        'command_task_resume',
        'CtrlSetChamberLight',
        'PrintbenchTempChart',
    ]
    for token in required_tokens:
        assert token in PANEL, token


def test_final_master_spec_forbids_desktop_bridge_regression():
    assert 'FINAL ist FINAL' in SPEC
    assert 'natives wxWidgets-Panel' in SPEC
    assert 'keine WebView als finale PRINTBENCH-Desktopoberfläche' in SPEC
    assert 'kein Raspberry Pi als Pflicht' in SPEC
    assert 'kein Bambu Studio erforderlich' in SPEC
    assert 'direkt vom PC im LAN' in SPEC
