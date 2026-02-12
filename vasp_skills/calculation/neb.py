"""Nudged elastic band (NEB) transition state calculation."""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.kpoints import Kpoints
from vasp_skills.core.poscar import Poscar


class NEB(VaspCalculation):
    """Nudged Elastic Band calculation for transition states.

    Supports climbing-image NEB (CI-NEB).
    Requires VTST Tools compiled into VASP.
    """

    preset_name = "neb"

    def __init__(
        self,
        initial: Poscar,
        final: Poscar,
        directory: str = "neb",
        nimages: int = 3,
        climb: bool = True,
        spring: float = -5.0,
        **kwargs,
    ):
        """
        Args:
            initial: Initial state POSCAR.
            final: Final state POSCAR.
            nimages: Number of intermediate images.
            climb: Enable climbing-image NEB.
            spring: Spring constant.
        """
        super().__init__(initial, directory, **kwargs)
        self.initial = initial
        self.final = final
        self.nimages = nimages
        self.climb = climb
        self.spring = spring

    def extra_incar_params(self) -> Dict[str, Any]:
        return {
            "IMAGES": self.nimages,
            "SPRING": self.spring,
            "LCLIMB": self.climb,
            "ICHAIN": 0,
        }

    def interpolate_images(self) -> List[Poscar]:
        """Linear interpolation between initial and final structures."""
        init_frac = self.initial.to_direct()
        final_frac = self.final.to_direct()

        # Handle periodic boundary conditions
        diff = final_frac - init_frac
        diff -= np.round(diff)  # minimum image convention

        images = []
        for i in range(1, self.nimages + 1):
            frac_i = i / (self.nimages + 1)
            positions = init_frac + frac_i * diff
            # Wrap to [0, 1)
            positions %= 1.0

            img = Poscar(
                lattice=self.initial.lattice.copy(),
                species=self.initial.species,
                counts=self.initial.counts,
                positions=positions,
                comment=f"NEB image {i}/{self.nimages}",
                scale=self.initial.scale,
            )
            images.append(img)
        return images

    def write_inputs(self):
        """Write NEB directory structure: 00/, 01/, ..., 0N+1/."""
        self.directory.mkdir(parents=True, exist_ok=True)

        # Write INCAR and KPOINTS to main directory
        incar = self.build_incar()
        incar.write(str(self.directory / "INCAR"))

        kpoints = self.build_kpoints()
        kpoints.write(str(self.directory / "KPOINTS"))

        try:
            potcar = self.build_potcar()
            potcar.write(str(self.directory / "POTCAR"))
        except FileNotFoundError as e:
            print(f"Warning: Could not write POTCAR: {e}")

        # Write initial state (00/)
        dir_00 = self.directory / "00"
        dir_00.mkdir(exist_ok=True)
        self.initial.write(str(dir_00 / "POSCAR"))

        # Write intermediate images
        images = self.interpolate_images()
        for i, img in enumerate(images, start=1):
            dir_i = self.directory / f"{i:02d}"
            dir_i.mkdir(exist_ok=True)
            img.write(str(dir_i / "POSCAR"))

        # Write final state
        dir_final = self.directory / f"{self.nimages + 1:02d}"
        dir_final.mkdir(exist_ok=True)
        self.final.write(str(dir_final / "POSCAR"))
