"""Hybrid functional (HSE06) calculation."""

import shutil
from typing import Any, Dict, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar


class Hybrid(VaspCalculation):
    """Hybrid functional calculation (HSE06, PBE0, etc.).

    HSE06 is the default with HFSCREEN=0.2.
    """

    preset_name = "hybrid_hse06"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "hybrid",
        functional: str = "hse06",
        scf_dir: Optional[str] = None,
        **kwargs,
    ):
        """
        Args:
            functional: 'hse06', 'pbe0', or 'custom'.
            scf_dir: Prior PBE SCF directory (for WAVECAR to accelerate).
        """
        super().__init__(poscar, directory, **kwargs)
        self.functional = functional
        self.scf_dir = scf_dir

    def extra_incar_params(self) -> Dict[str, Any]:
        params = {
            "LHFCALC": True,
            "ALGO": "Damped",
            "TIME": 0.4,
        }
        if self.functional == "hse06":
            params["HFSCREEN"] = 0.2
            params["AEXX"] = 0.25
        elif self.functional == "pbe0":
            params["HFSCREEN"] = 0.0
            params["AEXX"] = 0.25
        return params

    def write_inputs(self):
        super().write_inputs()
        # Copy WAVECAR from PBE SCF to speed up convergence
        if self.scf_dir:
            for f in ("WAVECAR", "CHGCAR"):
                src = f"{self.scf_dir}/{f}"
                dst = str(self.directory / f)
                try:
                    shutil.copy2(src, dst)
                except FileNotFoundError:
                    pass
