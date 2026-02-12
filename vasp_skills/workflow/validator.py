"""Input file validation for VASP calculations."""

import os
import numpy as np
from pathlib import Path
from typing import List, Optional

from vasp_skills.core.incar import Incar
from vasp_skills.core.poscar import Poscar
from vasp_skills.core.kpoints import Kpoints


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, msg: str):
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def __str__(self):
        lines = []
        if self.errors:
            lines.append("ERRORS:")
            for e in self.errors:
                lines.append(f"  [ERROR] {e}")
        if self.warnings:
            lines.append("WARNINGS:")
            for w in self.warnings:
                lines.append(f"  [WARN]  {w}")
        if not lines:
            lines.append("All checks passed.")
        return "\n".join(lines)


class InputValidator:
    """Validate VASP input files before submission."""

    def validate_directory(self, directory: str = ".") -> ValidationResult:
        """Validate all input files in a directory."""
        result = ValidationResult()
        d = Path(directory)

        # Check required files exist
        for fname in ("INCAR", "POSCAR", "KPOINTS", "POTCAR"):
            if not (d / fname).exists():
                result.add_error(f"{fname} not found in {directory}")

        if not result.is_valid:
            return result

        # Validate INCAR
        incar = Incar.read(str(d / "INCAR"))
        for w in incar.validate():
            result.add_warning(w)

        # Validate POSCAR
        self._validate_poscar(d / "POSCAR", result)

        # Cross-validate INCAR + POSCAR
        poscar = Poscar.read(str(d / "POSCAR"))
        self._cross_validate(incar, poscar, result)

        return result

    def validate_poscar(self, filepath: str = "POSCAR") -> ValidationResult:
        """Validate a POSCAR file."""
        result = ValidationResult()
        self._validate_poscar(Path(filepath), result)
        return result

    def _validate_poscar(self, filepath: Path, result: ValidationResult):
        """Internal POSCAR validation."""
        try:
            poscar = Poscar.read(str(filepath))
        except Exception as e:
            result.add_error(f"Failed to read POSCAR: {e}")
            return

        if poscar.natoms == 0:
            result.add_error("POSCAR has 0 atoms")

        if not poscar.species:
            result.add_warning("POSCAR missing species names (VASP4 format)")

        # Check lattice
        vol = poscar.volume
        if vol < 1.0:
            result.add_warning(f"Very small cell volume: {vol:.2f} A^3")
        if vol > 100000:
            result.add_warning(f"Very large cell volume: {vol:.2f} A^3")

        # Check for overlapping atoms
        frac = poscar.to_direct()
        for i in range(poscar.natoms):
            for j in range(i + 1, poscar.natoms):
                diff = frac[i] - frac[j]
                diff -= np.round(diff)
                cart_diff = diff @ poscar.lattice
                dist = np.linalg.norm(cart_diff)
                if dist < 0.5:
                    result.add_error(
                        f"Atoms {i} and {j} are too close: {dist:.3f} A"
                    )

        # Check fractional coordinates in [0, 1)
        if not poscar.cartesian:
            if np.any(frac < -0.1) or np.any(frac > 1.1):
                result.add_warning("Some fractional coordinates outside [0, 1)")

    def _cross_validate(
        self, incar: Incar, poscar: Poscar, result: ValidationResult
    ):
        """Cross-validate INCAR against POSCAR."""
        params = incar.params

        # Check MAGMOM count
        magmom = params.get("MAGMOM")
        if isinstance(magmom, str):
            # Parse MAGMOM string
            parts = magmom.split()
            nmag = 0
            for p in parts:
                if "*" in p:
                    nmag += int(p.split("*")[0])
                else:
                    nmag += 1

            ispin = params.get("ISPIN", 1)
            lsorbit = params.get("LSORBIT", False)

            if lsorbit:
                expected = poscar.natoms * 3
            else:
                expected = poscar.natoms

            if nmag != expected:
                result.add_warning(
                    f"MAGMOM has {nmag} values but expected {expected} "
                    f"({poscar.natoms} atoms, LSORBIT={lsorbit})"
                )

        # ENCUT check
        encut = params.get("ENCUT")
        if encut is not None and encut < 200:
            result.add_warning(f"ENCUT={encut} eV seems very low")
        if encut is not None and encut > 1000:
            result.add_warning(f"ENCUT={encut} eV seems very high")

        # EDIFF check
        ediff = params.get("EDIFF")
        if ediff is not None and ediff > 1e-3:
            result.add_warning(f"EDIFF={ediff} is very loose")

        # NSW + IBRION consistency
        nsw = params.get("NSW", 0)
        ibrion = params.get("IBRION", -1)
        if nsw > 0 and ibrion < 0:
            result.add_warning("NSW > 0 but IBRION < 0 (no ionic relaxation)")

        # ISMEAR for metals vs insulators
        ismear = params.get("ISMEAR", 0)
        if ismear == -5 and nsw > 0:
            result.add_error("ISMEAR=-5 (tetrahedron) must not be used with relaxation")

        # LREAL for small systems
        lreal = params.get("LREAL")
        if lreal and str(lreal).upper() not in ("FALSE", ".FALSE.", "F", ".F."):
            if poscar.natoms < 8:
                result.add_warning(
                    "LREAL is set but system has < 8 atoms; consider LREAL=.FALSE."
                )

        # Selective dynamics check
        if poscar.selective_dynamics and ibrion < 0:
            result.add_warning(
                "Selective dynamics enabled but IBRION < 0 (no relaxation)"
            )
