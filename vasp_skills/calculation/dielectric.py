"""Dielectric properties calculation."""

from typing import Any, Dict

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar


class Dielectric(VaspCalculation):
    """Dielectric properties (Born effective charges, dielectric tensor).

    Uses DFPT (LEPSILON=True) or finite electric field (LCALCEPS).
    """

    preset_name = "dielectric"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "dielectric",
        method: str = "dfpt",
        **kwargs,
    ):
        """
        Args:
            method: 'dfpt' (LEPSILON) or 'finite_field' (LCALCEPS).
        """
        super().__init__(poscar, directory, **kwargs)
        self.method = method

    def extra_incar_params(self) -> Dict[str, Any]:
        if self.method == "dfpt":
            return {
                "LEPSILON": True,
                "IBRION": 8,
            }
        else:
            return {
                "LCALCEPS": True,
                "IBRION": 6,
            }
