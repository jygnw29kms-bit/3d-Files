from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATER = (ROOT / "app/orcaslicer/src/slic3r/GUI/Plater.cpp").read_text(encoding="utf-8")


def test_windows_caption_is_stable_printbench_brand():
    assert 'SetTitle(m_project_name + " - 135er-PRINTBENCH")' not in PLATER
    assert 'SetTitle(title + " - 135er-PRINTBENCH")' not in PLATER
    assert PLATER.count('mainframe->SetTitle("135er-PRINTBENCH")') >= 2


def test_project_name_stays_available_in_slicer_topbar():
    assert 'topbar()->SetTitle(m_project_name)' in PLATER
    assert 'topbar()->SetTitle(title)' in PLATER
