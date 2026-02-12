"""Base class for all VASP calculation types."""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from vasp_skills.config import Config
from vasp_skills.core.incar import Incar
from vasp_skills.core.poscar import Poscar
from vasp_skills.core.kpoints import Kpoints
from vasp_skills.core.potcar import Potcar


class VaspCalculation:
    """Base class providing common functionality for all calculation types.

    Subclasses should override:
        - preset_name: str - the INCAR preset key
        - default_kpoints() -> Kpoints
        - extra_incar_params() -> dict (optional)
    """

    preset_name: str = "scf"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = ".",
        incar_overrides: Optional[Dict[str, Any]] = None,
        kpoints: Optional[Kpoints] = None,
        potcar_dir: Optional[str] = None,
        potcar_variants: Optional[Dict[str, str]] = None,
        encut: Optional[float] = None,
    ):
        self.poscar = poscar
        self.directory = Path(directory)
        self.incar_overrides = incar_overrides or {}
        self._kpoints = kpoints
        self.potcar_dir = potcar_dir
        self.potcar_variants = potcar_variants
        self.encut = encut
        self.config = Config()

    def extra_incar_params(self) -> Dict[str, Any]:
        """Override in subclasses to add calculation-specific INCAR params."""
        return {}

    def default_kpoints(self) -> Kpoints:
        """Override in subclasses for specific k-point requirements."""
        density = self.config.get("kpoint_density", 40)
        return Kpoints.from_density(self.poscar.lattice, density=density)

    def build_incar(self) -> Incar:
        """Build the INCAR for this calculation."""
        params = {}
        # Start from preset
        incar = Incar.from_preset(self.preset_name)
        params.update(incar.params)

        # Add config defaults
        defaults = self.config.defaults
        if defaults:
            for key in ("NCORE", "KPAR"):
                cfg_key = key.lower()
                if cfg_key in defaults and key not in params:
                    params[key] = defaults[cfg_key]

        # ENCUT
        if self.encut:
            params["ENCUT"] = self.encut
        elif "ENCUT" not in params:
            encut = defaults.get("encut", 520) if defaults else 520
            params["ENCUT"] = encut

        # Subclass-specific params
        params.update(self.extra_incar_params())

        # User overrides (highest priority)
        params.update(self.incar_overrides)

        return Incar(params)

    def build_kpoints(self) -> Kpoints:
        """Build KPOINTS for this calculation."""
        if self._kpoints is not None:
            return self._kpoints
        return self.default_kpoints()

    def build_potcar(self) -> Potcar:
        """Build POTCAR for this calculation."""
        return Potcar(
            species=self.poscar.species,
            potcar_dir=self.potcar_dir,
            variants=self.potcar_variants,
        )

    def write_inputs(self):
        """Write all 4 VASP input files to the directory."""
        self.directory.mkdir(parents=True, exist_ok=True)

        incar = self.build_incar()
        incar.write(str(self.directory / "INCAR"))

        self.poscar.write(str(self.directory / "POSCAR"))

        kpoints = self.build_kpoints()
        kpoints.write(str(self.directory / "KPOINTS"))

        try:
            potcar = self.build_potcar()
            potcar.write(str(self.directory / "POTCAR"))
        except FileNotFoundError as e:
            print(f"Warning: Could not write POTCAR: {e}")
            print("You will need to provide POTCAR manually.")

    def run(self, vasp_cmd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Execute VASP in the calculation directory.

        Args:
            vasp_cmd: VASP command to run. Defaults to config value.
        """
        cmd = vasp_cmd or self.config.vasp_cmd
        self.write_inputs()
        return subprocess.run(
            cmd.split(),
            cwd=str(self.directory),
            capture_output=True,
            text=True,
        )

    def check_convergence(self) -> bool:
        """Check if the calculation converged (basic check via OSZICAR)."""
        oszicar = self.directory / "OSZICAR"
        if not oszicar.exists():
            return False
        with open(oszicar) as f:
            lines = f.readlines()
        if not lines:
            return False
        # For relaxation, check for "reached required accuracy"
        outcar = self.directory / "OUTCAR"
        if outcar.exists():
            with open(outcar) as f:
                content = f.read()
            if "reached required accuracy" in content:
                return True
        return len(lines) > 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(dir={self.directory})"
