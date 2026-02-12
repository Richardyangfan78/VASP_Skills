"""Self-consistent field (single-point energy) calculation."""

from typing import Any, Dict

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar


class SCF(VaspCalculation):
    """Single-point energy (SCF) calculation.

    Produces CHGCAR and WAVECAR for subsequent band/DOS calculations.
    """

    preset_name = "scf"

    def __init__(self, poscar: Poscar, directory: str = "scf", **kwargs):
        super().__init__(poscar, directory, **kwargs)

    def extra_incar_params(self) -> Dict[str, Any]:
        return {
            "LWAVE": True,
            "LCHARG": True,
        }
