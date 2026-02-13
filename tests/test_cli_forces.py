from types import SimpleNamespace

import numpy as np

from vasp_skills.cli import cmd_parse
import vasp_skills.postprocess.parser as parser_module


class _DummyParser:
    def __init__(self, directory: str):
        self.directory = directory

    def get_forces(self):
        return np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])


def test_cmd_parse_forces_branch(monkeypatch, capsys):
    monkeypatch.setattr(parser_module, "VaspParser", _DummyParser)
    args = SimpleNamespace(what="forces", directory=".")

    cmd_parse(args)

    out = capsys.readouterr().out
    assert "Max force: 2.000000 eV/A" in out
    assert "Atoms: 2" in out
