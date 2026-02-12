"""Elastic constants calculation."""

from typing import Any, Dict

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar


class Elastic(VaspCalculation):
    """Elastic constants calculation using IBRION=6 (finite differences).

    Computes the full elastic tensor Cij.
    """

    preset_name = "elastic"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "elastic",
        **kwargs,
    ):
        super().__init__(poscar, directory, **kwargs)

    def extra_incar_params(self) -> Dict[str, Any]:
        return {
            "IBRION": 6,
            "ISIF": 3,
            "NSW": 1,
        }
