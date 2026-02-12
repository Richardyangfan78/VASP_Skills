"""Ab initio molecular dynamics calculation."""

from typing import Any, Dict, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.kpoints import Kpoints
from vasp_skills.core.poscar import Poscar


class MolecularDynamics(VaspCalculation):
    """Ab initio molecular dynamics (AIMD).

    Supports NVE, NVT (Nose-Hoover), and NVT (Andersen) ensembles.
    """

    preset_name = "md"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "md",
        temperature: float = 300.0,
        temperature_end: Optional[float] = None,
        timestep: float = 1.0,
        nsteps: int = 5000,
        ensemble: str = "nvt_nose",
        **kwargs,
    ):
        """
        Args:
            temperature: Initial temperature in K.
            temperature_end: Final temperature in K (for annealing). Defaults to temperature.
            timestep: Time step in fs.
            nsteps: Number of MD steps.
            ensemble: 'nve', 'nvt_nose' (Nose-Hoover), or 'nvt_andersen'.
        """
        super().__init__(poscar, directory, **kwargs)
        self.temperature = temperature
        self.temperature_end = temperature_end or temperature
        self.timestep = timestep
        self.nsteps = nsteps
        self.ensemble = ensemble

    def default_kpoints(self) -> Kpoints:
        """MD typically uses Gamma-only or sparse mesh."""
        return Kpoints.gamma_only()

    def extra_incar_params(self) -> Dict[str, Any]:
        params = {
            "IBRION": 0,
            "NSW": self.nsteps,
            "POTIM": self.timestep,
            "TEBEG": self.temperature,
            "TEEND": self.temperature_end,
            "ISYM": 0,
        }

        if self.ensemble == "nve":
            params["SMASS"] = -3
            params["MDALGO"] = 0
        elif self.ensemble == "nvt_nose":
            params["SMASS"] = 0
            params["MDALGO"] = 0
        elif self.ensemble == "nvt_andersen":
            params["MDALGO"] = 1

        return params
