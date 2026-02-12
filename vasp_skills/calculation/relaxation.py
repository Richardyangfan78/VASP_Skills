"""Structural relaxation calculation."""

from typing import Any, Dict, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.kpoints import Kpoints
from vasp_skills.core.poscar import Poscar


class Relaxation(VaspCalculation):
    """Structure optimization (ionic + cell relaxation).

    Supports:
        - Full relaxation (ISIF=3): both ions and cell
        - Ionic-only relaxation (ISIF=2): fix cell shape/volume
        - Volume relaxation (ISIF=7): fix shape, relax volume
    """

    preset_name = "relaxation"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "relax",
        isif: int = 3,
        nsw: int = 200,
        ediffg: float = -0.02,
        **kwargs,
    ):
        super().__init__(poscar, directory, **kwargs)
        self.isif = isif
        self.nsw = nsw
        self.ediffg = ediffg

    def extra_incar_params(self) -> Dict[str, Any]:
        return {
            "ISIF": self.isif,
            "NSW": self.nsw,
            "EDIFFG": self.ediffg,
        }

    @classmethod
    def ionic_only(cls, poscar: Poscar, directory: str = "relax", **kwargs):
        """Create ionic-only relaxation (fixed cell)."""
        return cls(poscar, directory, isif=2, **kwargs)

    @classmethod
    def full(cls, poscar: Poscar, directory: str = "relax", **kwargs):
        """Create full relaxation (ions + cell)."""
        return cls(poscar, directory, isif=3, **kwargs)

    @classmethod
    def volume_only(cls, poscar: Poscar, directory: str = "relax", **kwargs):
        """Create volume-only relaxation."""
        return cls(poscar, directory, isif=7, **kwargs)

    def get_relaxed_structure(self) -> Poscar:
        """Read the relaxed structure from CONTCAR."""
        contcar_path = self.directory / "CONTCAR"
        if not contcar_path.exists():
            raise FileNotFoundError(f"CONTCAR not found in {self.directory}")
        return Poscar.read(str(contcar_path))
