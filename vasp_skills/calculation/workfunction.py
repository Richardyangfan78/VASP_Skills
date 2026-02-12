"""Work function calculation for surface slabs."""

from typing import Any, Dict, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar


class WorkFunction(VaspCalculation):
    """Work function calculation via planar-averaged electrostatic potential.

    Requires a slab model with sufficient vacuum.
    Outputs LOCPOT for planar averaging along the surface normal.
    """

    preset_name = "workfunction"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "workfunction",
        dipol_direction: int = 3,
        dipol_center: Optional[list] = None,
        **kwargs,
    ):
        """
        Args:
            dipol_direction: Direction for dipole correction (1=x, 2=y, 3=z).
            dipol_center: Center of slab in fractional coords [x, y, z].
        """
        super().__init__(poscar, directory, **kwargs)
        self.dipol_direction = dipol_direction
        self.dipol_center = dipol_center

    def extra_incar_params(self) -> Dict[str, Any]:
        params = {
            "LVTOT": True,
            "LDIPOL": True,
            "IDIPOL": self.dipol_direction,
        }
        if self.dipol_center:
            params["DIPOL"] = " ".join(str(d) for d in self.dipol_center)
        return params
