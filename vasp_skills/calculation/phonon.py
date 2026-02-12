"""Phonon calculation via DFPT or finite displacements."""

from typing import Any, Dict, Optional, Tuple

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.kpoints import Kpoints
from vasp_skills.core.poscar import Poscar


class Phonon(VaspCalculation):
    """Phonon calculation using density-functional perturbation theory (DFPT).

    Uses IBRION=8 for DFPT. For finite-displacement method,
    consider using phonopy externally with SCF calculations.
    """

    preset_name = "phonon"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "phonon",
        supercell: Optional[Tuple[int, int, int]] = None,
        method: str = "dfpt",
        **kwargs,
    ):
        """
        Args:
            supercell: If provided, create supercell before phonon calc.
            method: 'dfpt' (IBRION=8) or 'finite_diff' (for phonopy).
        """
        if supercell:
            poscar = poscar.make_supercell(supercell)
        super().__init__(poscar, directory, **kwargs)
        self.method = method

    def extra_incar_params(self) -> Dict[str, Any]:
        if self.method == "dfpt":
            return {
                "IBRION": 8,
                "ADDGRID": True,
            }
        else:
            # For finite displacement (phonopy), just do SCF
            return {
                "IBRION": -1,
                "NSW": 0,
            }
