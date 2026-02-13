import pytest

from vasp_skills.core.incar import Incar


def test_from_known_preset():
    incar = Incar.from_preset("scf")
    assert incar.params["NSW"] == 0
    assert "EDIFF" in incar.params


def test_unknown_preset_raises():
    with pytest.raises(ValueError):
        Incar.from_preset("not_a_preset")
