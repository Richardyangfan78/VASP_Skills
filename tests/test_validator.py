from vasp_skills.workflow.validator import InputValidator


def test_validate_directory_reports_missing_files(tmp_path):
    validator = InputValidator()
    result = validator.validate_directory(str(tmp_path))

    assert not result.is_valid
    assert any("INCAR not found" in e for e in result.errors)
    assert any("POSCAR not found" in e for e in result.errors)
    assert any("KPOINTS not found" in e for e in result.errors)
    assert any("POTCAR not found" in e for e in result.errors)
