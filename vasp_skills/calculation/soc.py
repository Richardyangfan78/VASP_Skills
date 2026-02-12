"""Spin-orbit coupling calculation."""

import shutil
from typing import Any, Dict, List, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar


class SOC(VaspCalculation):
    """Spin-orbit coupling (SOC) calculation.

    Uses non-collinear magnetism (LNONCOLLINEAR=True).
    Requires vasp_ncl executable.
    """

    preset_name = "soc"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "soc",
        saxis: Optional[List[float]] = None,
        magmom: Optional[List[float]] = None,
        scf_dir: Optional[str] = None,
        **kwargs,
    ):
        """
        Args:
            saxis: Spin quantization axis [sx, sy, sz].
            magmom: Non-collinear MAGMOM (3 components per atom).
            scf_dir: Prior collinear SCF directory for WAVECAR.
        """
        super().__init__(poscar, directory, **kwargs)
        self.saxis = saxis or [0, 0, 1]
        self._magmom = magmom
        self.scf_dir = scf_dir

    def _generate_magmom(self) -> str:
        """Generate non-collinear MAGMOM (3 values per atom)."""
        if self._magmom:
            return " ".join(str(m) for m in self._magmom)
        # Default: align along saxis
        natoms = self.poscar.natoms
        moments = []
        for _ in range(natoms):
            moments.extend([0.0, 0.0, 1.0])  # default z-aligned
        return " ".join(str(m) for m in moments)

    def extra_incar_params(self) -> Dict[str, Any]:
        return {
            "ISPIN": 2,
            "LSORBIT": True,
            "LNONCOLLINEAR": True,
            "SAXIS": " ".join(str(s) for s in self.saxis),
            "MAGMOM": self._generate_magmom(),
            "LORBIT": 11,
        }

    def write_inputs(self):
        super().write_inputs()
        if self.scf_dir:
            src = f"{self.scf_dir}/WAVECAR"
            dst = str(self.directory / "WAVECAR")
            try:
                shutil.copy2(src, dst)
            except FileNotFoundError:
                pass
