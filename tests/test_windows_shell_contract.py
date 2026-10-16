from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / 'app/orcaslicer/src/slic3r/GUI/MainFrame.cpp').read_text(encoding='utf-8')
GUI_APP = (ROOT / 'app/orcaslicer/src/slic3r/GUI/GUI_App.cpp').read_text(encoding='utf-8')
RC = (ROOT / 'app/orcaslicer/src/dev-utils/platform/msw/OrcaSlicer.rc.in').read_text(encoding='utf-8')
CMAKE = (ROOT / 'app/orcaslicer/CMakeLists.txt').read_text(encoding='utf-8')


def test_windows_shell_keeps_native_window_controls():
    assert '#define BORDERLESS_FRAME_STYLE wxDEFAULT_FRAME_STYLE' in MAIN
    assert 'WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_THICKFRAME' in MAIN
    assert 'return wxFrame::MSWWindowProc(nMsg, wParam, lParam);\n\n#if 0' in MAIN


def test_windows_exe_uses_printbench_icon_resource():
    assert 'PRINTBENCH_AppIcon.ico' in RC
    assert 'images/OrcaSlicer.ico' not in RC
    assert (ROOT / 'assets/branding/PRINTBENCH_AppIcon.ico').is_file()
    assert (ROOT / 'assets/branding/PRINTBENCH_AppIcon_MASTER_1024.png').is_file()


def test_orca_update_advertising_is_not_run_at_printbench_startup():
    startup_marker = '// PRINTBENCH owns its release/update channel; never query or advertise Orca releases on startup.'
    assert startup_marker in GUI_APP
    assert startup_marker + '\n            // this->check_new_version_sf();' in GUI_APP


def test_windows_installer_uses_the_same_printbench_icon():
    assert 'assets/branding/PRINTBENCH_AppIcon.ico' in CMAKE
    assert 'resources/images\\\\OrcaSlicer.ico' not in CMAKE
