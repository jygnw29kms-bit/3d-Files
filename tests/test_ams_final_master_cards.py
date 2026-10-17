from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CPP=(ROOT/'app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.cpp').read_text(encoding='utf-8')
HPP=(ROOT/'app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.hpp').read_text(encoding='utf-8')

def test_ams_slots_are_native_visual_cards_not_flat_text_blocks():
    assert 'class PrintbenchAmsSlotCard : public wxPanel' in CPP
    assert 'std::array<PrintbenchAmsSlotCard*, 4> m_ams_slots' in HPP
    assert 'dc.DrawCircle(cx, cy, outer)' in CPP
    assert 'dc.DrawCircle(cx, cy, inner)' in CPP

def test_ams_card_receives_live_material_colour_and_remaining_amount():
    assert 'set_slot(slot.present, material, colour, slot.remain)' in CPP
    assert 'wxString::Format("%d %%", m_remain)' in CPP
    assert 'm_material' in CPP

def test_empty_ams_slot_has_explicit_empty_visual_state():
    assert 'wxPENSTYLE_SHORT_DASH' in CPP
    assert 'Kein Filament' in CPP
