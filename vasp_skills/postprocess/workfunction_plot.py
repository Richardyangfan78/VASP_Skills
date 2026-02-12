"""Work function plotting from LOCPOT data."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Tuple

from vasp_skills.postprocess.parser import VaspParser


class WorkfunctionPlotter:
    """Plot planar-averaged electrostatic potential for work function determination."""

    def __init__(self, directory: str = "."):
        self.directory = Path(directory)
        self.parser = VaspParser(directory)

    def plot(
        self,
        efermi: Optional[float] = None,
        axis: int = 2,
        figsize: Tuple[float, float] = (10, 5),
        title: str = "Work Function",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot planar-averaged potential and compute work function.

        Args:
            efermi: Fermi energy. If None, reads from OUTCAR.
            axis: Surface normal direction (0=x, 1=y, 2=z).
        """
        locpot_data = self.parser.parse_locpot(axis=axis)
        positions = locpot_data["position"]
        potential = locpot_data["potential"]

        if efermi is None:
            try:
                outcar = self.parser.parse_outcar()
                efermi = outcar.get("fermi_energy", 0.0)
            except FileNotFoundError:
                efermi = 0.0

        # Find vacuum level (max potential in vacuum region)
        vacuum_level = np.max(potential)

        # Work function
        work_function = vacuum_level - efermi

        fig, ax = plt.subplots(figsize=figsize)

        ax.plot(positions, potential, "b-", linewidth=1.0, label="Planar avg. potential")
        ax.axhline(efermi, color="r", linestyle="--", linewidth=0.8,
                    label=f"$E_F$ = {efermi:.3f} eV")
        ax.axhline(vacuum_level, color="g", linestyle="--", linewidth=0.8,
                    label=f"$V_{{vac}}$ = {vacuum_level:.3f} eV")

        # Annotate work function
        mid_x = positions[len(positions) // 2]
        ax.annotate(
            f"$\\Phi$ = {work_function:.3f} eV",
            xy=(mid_x, (efermi + vacuum_level) / 2),
            fontsize=12,
            ha="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
        )

        ax.set_xlabel(f"Position along {'xyz'[axis]} (A)")
        ax.set_ylabel("Potential (eV)")
        ax.set_title(title)
        ax.legend()

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def compute_work_function(
        self, efermi: Optional[float] = None, axis: int = 2
    ) -> dict:
        """Compute work function without plotting.

        Returns dict with vacuum_level, fermi_energy, work_function.
        """
        locpot_data = self.parser.parse_locpot(axis=axis)
        potential = locpot_data["potential"]

        if efermi is None:
            try:
                outcar = self.parser.parse_outcar()
                efermi = outcar.get("fermi_energy", 0.0)
            except FileNotFoundError:
                efermi = 0.0

        vacuum_level = np.max(potential)
        work_function = vacuum_level - efermi

        return {
            "vacuum_level": vacuum_level,
            "fermi_energy": efermi,
            "work_function": work_function,
        }
