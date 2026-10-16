from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PANEL=(ROOT/"app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.cpp").read_text(encoding="utf-8")


def test_current_print_card_uses_live_progress_gauge():
    assert 'm_progress_gauge->SetValue(progress_value)' in PANEL
    assert 'std::clamp(s.progress, 0, 100)' in PANEL


def test_current_print_card_has_master_metric_hierarchy():
    for label in ('FORTSCHRITT', 'SCHICHTEN', 'RESTZEIT'):
        assert label in PANEL
    assert 'create_scaled_bitmap("menu_obj_cube", print_card, 42)' in PANEL


def test_remaining_time_formats_hours_when_needed():
    assert 'minutes >= 60' in PANEL
    assert '%d h %02d min' in PANEL
