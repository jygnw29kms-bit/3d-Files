from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'printbench_collector'))
import reader_contract


def test_normalize_uid():
    assert reader_contract.normalize_uid('04a1b2c3d4e5f6') == '04:A1:B2:C3:D4:E5:F6'


def test_ams2pro_slot_range():
    obs=reader_contract.TagObservation('reader-1','0','3','04A1B2C3D4E5F6','ntag216',{})
    assert reader_contract.validate(obs).slot_id == '3'
    with pytest.raises(ValueError):
        reader_contract.validate(reader_contract.TagObservation('reader-1','0','4','04A1B2C3D4E5F6','ntag216',{}))


def test_zero_uid_rejected():
    with pytest.raises(ValueError):
        reader_contract.normalize_uid('00000000000000')
