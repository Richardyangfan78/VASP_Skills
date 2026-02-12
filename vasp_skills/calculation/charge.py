"""Charge density analysis (differential charge, Bader)."""

from typing import Any, Dict, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar


class ChargeDensity(VaspCalculation):
    """Charge density calculation for Bader analysis or charge difference.

    Produces CHGCAR and AECCAR0/AECCAR2 for Bader analysis.
    """

    preset_name = "charge"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "charge",
        bader: bool = True,
        **kwargs,
    ):
        """
        Args:
            bader: If True, write all-electron charge (LAECHG=True)
                  needed for Bader charge analysis.
        """
        super().__init__(poscar, directory, **kwargs)
        self.bader = bader

    def extra_incar_params(self) -> Dict[str, Any]:
        params = {
            "LCHARG": True,
            "NSW": 0,
            "IBRION": -1,
        }
        if self.bader:
            params["LAECHG"] = True
            params["PREC"] = "Accurate"
            params["NGXF"] = self._fine_grid_size(0)
            params["NGYF"] = self._fine_grid_size(1)
            params["NGZF"] = self._fine_grid_size(2)
        return params

    def _fine_grid_size(self, axis: int) -> int:
        """Estimate fine FFT grid for Bader analysis."""
        import numpy as np
        length = np.linalg.norm(self.poscar.lattice[axis])
        # ~0.04 A grid spacing
        return int(np.ceil(length / 0.04))
