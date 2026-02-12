"""Band structure calculation."""

import shutil
from typing import Any, Dict, List, Optional, Tuple

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.kpoints import Kpoints
from vasp_skills.core.poscar import Poscar


class BandStructure(VaspCalculation):
    """Band structure calculation along high-symmetry k-path.

    Requires CHGCAR from a prior SCF calculation.
    """

    preset_name = "band"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "band",
        kpath: Optional[List[Tuple[str, List[float]]]] = None,
        npoints: int = 40,
        scf_dir: Optional[str] = None,
        **kwargs,
    ):
        """
        Args:
            poscar: Structure (should match SCF calculation).
            kpath: Explicit k-path as list of (label, [kx,ky,kz]) pairs.
                  If None, auto-generates using pymatgen.
            npoints: Points per k-segment.
            scf_dir: Directory of prior SCF calc (to copy CHGCAR).
        """
        super().__init__(poscar, directory, **kwargs)
        self.kpath = kpath
        self.npoints = npoints
        self.scf_dir = scf_dir

    def default_kpoints(self) -> Kpoints:
        if self.kpath:
            return Kpoints.line_mode(self.kpath, self.npoints)
        return Kpoints.line_mode_auto(self.poscar, self.npoints)

    def extra_incar_params(self) -> Dict[str, Any]:
        return {
            "ICHARG": 11,
            "LORBIT": 11,
        }

    def write_inputs(self):
        super().write_inputs()
        # Copy CHGCAR from SCF directory
        if self.scf_dir:
            src = f"{self.scf_dir}/CHGCAR"
            dst = str(self.directory / "CHGCAR")
            try:
                shutil.copy2(src, dst)
            except FileNotFoundError:
                print(f"Warning: CHGCAR not found at {src}")
