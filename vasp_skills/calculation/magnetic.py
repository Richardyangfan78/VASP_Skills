"""Magnetic calculations (collinear spin-polarized)."""

from typing import Any, Dict, List, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar


class Magnetic(VaspCalculation):
    """Spin-polarized magnetic calculation.

    Supports ferromagnetic, antiferromagnetic, and custom spin configurations.
    """

    preset_name = "magnetic"

    # Default initial magnetic moments for common elements
    DEFAULT_MAGMOM = {
        "Fe": 5.0, "Co": 3.0, "Ni": 2.0, "Mn": 5.0, "Cr": 5.0,
        "V": 3.0, "Ti": 2.0, "Cu": 1.0, "O": 0.6, "N": 0.6,
    }

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "magnetic",
        magmom: Optional[List[float]] = None,
        configuration: str = "ferro",
        **kwargs,
    ):
        """
        Args:
            magmom: Explicit MAGMOM list (one per atom).
            configuration: 'ferro' (all up), 'afm' (alternating), or 'custom'.
        """
        super().__init__(poscar, directory, **kwargs)
        self._magmom = magmom
        self.configuration = configuration

    def _generate_magmom(self) -> str:
        """Generate MAGMOM string."""
        if self._magmom:
            return " ".join(str(m) for m in self._magmom)

        elements = self.poscar.elements
        moments = []

        for i, elem in enumerate(elements):
            mag = self.DEFAULT_MAGMOM.get(elem, 0.6)
            if self.configuration == "afm" and i % 2 == 1:
                mag = -mag
            moments.append(mag)

        return " ".join(str(m) for m in moments)

    def extra_incar_params(self) -> Dict[str, Any]:
        return {
            "ISPIN": 2,
            "MAGMOM": self._generate_magmom(),
            "LORBIT": 11,
        }
