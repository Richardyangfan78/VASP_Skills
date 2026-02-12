"""Density of states calculation."""

import shutil
from typing import Any, Dict, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.kpoints import Kpoints
from vasp_skills.core.poscar import Poscar


class DOS(VaspCalculation):
    """Density of states calculation.

    Requires CHGCAR from a prior SCF calculation.
    Uses denser k-mesh and tetrahedron method for accurate DOS.
    """

    preset_name = "dos"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "dos",
        nedos: int = 3001,
        emin: Optional[float] = None,
        emax: Optional[float] = None,
        scf_dir: Optional[str] = None,
        kpoint_density: float = 60.0,
        **kwargs,
    ):
        super().__init__(poscar, directory, **kwargs)
        self.nedos = nedos
        self.emin = emin
        self.emax = emax
        self.scf_dir = scf_dir
        self.kpoint_density = kpoint_density

    def default_kpoints(self) -> Kpoints:
        """Denser k-mesh for DOS."""
        return Kpoints.from_density(
            self.poscar.lattice, density=self.kpoint_density
        )

    def extra_incar_params(self) -> Dict[str, Any]:
        params = {
            "ICHARG": 11,
            "LORBIT": 11,
            "NEDOS": self.nedos,
            "ISMEAR": -5,
        }
        if self.emin is not None:
            params["EMIN"] = self.emin
        if self.emax is not None:
            params["EMAX"] = self.emax
        return params

    def write_inputs(self):
        super().write_inputs()
        if self.scf_dir:
            src = f"{self.scf_dir}/CHGCAR"
            dst = str(self.directory / "CHGCAR")
            try:
                shutil.copy2(src, dst)
            except FileNotFoundError:
                print(f"Warning: CHGCAR not found at {src}")
