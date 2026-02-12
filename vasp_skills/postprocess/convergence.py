"""Convergence curve plotting for VASP calculations."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Tuple

from vasp_skills.postprocess.parser import VaspParser


class ConvergencePlotter:
    """Plot convergence of energy, forces, and electronic steps."""

    def __init__(self, directory: str = "."):
        self.directory = Path(directory)
        self.parser = VaspParser(directory)

    def plot_energy(
        self,
        figsize: Tuple[float, float] = (8, 5),
        title: str = "Energy Convergence",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot total energy vs ionic step."""
        data = self.parser.parse_oszicar()
        ionic = data["ionic_steps"]

        energies = [s.get("E0", s.get("F", float("nan"))) for s in ionic]
        steps = list(range(1, len(energies) + 1))

        fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)

        # Absolute energy
        axes[0].plot(steps, energies, "b-o", markersize=3)
        axes[0].set_ylabel("Energy (eV)")
        axes[0].set_title(title)

        # Energy change
        if len(energies) > 1:
            de = np.diff(energies)
            axes[1].plot(steps[1:], np.abs(de), "r-o", markersize=3)
            axes[1].set_yscale("log")
            axes[1].set_ylabel("|dE| (eV)")
            axes[1].set_xlabel("Ionic Step")

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def plot_forces(
        self,
        figsize: Tuple[float, float] = (8, 5),
        title: str = "Force Convergence",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot maximum force vs ionic step from OUTCAR."""
        fp = self.directory / "OUTCAR"
        if not fp.exists():
            raise FileNotFoundError("OUTCAR not found")

        import re
        with open(fp) as f:
            content = f.read()

        # Find all force blocks
        force_blocks = re.findall(
            r"TOTAL-FORCE.*?\n-+\n(.*?)\n-+",
            content, re.DOTALL
        )

        max_forces = []
        rms_forces = []
        for block in force_blocks:
            forces = []
            for line in block.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 6:
                    f_vec = [float(parts[3]), float(parts[4]), float(parts[5])]
                    forces.append(np.linalg.norm(f_vec))
            if forces:
                max_forces.append(max(forces))
                rms_forces.append(np.sqrt(np.mean(np.array(forces) ** 2)))

        steps = list(range(1, len(max_forces) + 1))

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(steps, max_forces, "r-o", markersize=3, label="Max force")
        ax.plot(steps, rms_forces, "b-s", markersize=3, label="RMS force")
        ax.set_yscale("log")
        ax.set_xlabel("Ionic Step")
        ax.set_ylabel("Force (eV/A)")
        ax.set_title(title)
        ax.legend()
        ax.axhline(0.02, color="gray", linestyle="--", linewidth=0.5, label="Threshold")

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def plot_electronic(
        self,
        ionic_step: int = -1,
        figsize: Tuple[float, float] = (8, 5),
        title: str = "Electronic Convergence",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot electronic step convergence for a specific ionic step.

        Args:
            ionic_step: Which ionic step (-1 = last).
        """
        data = self.parser.parse_oszicar()
        e_steps = data["electronic_steps"]

        if not e_steps:
            raise ValueError("No electronic step data found")

        steps = e_steps[ionic_step]
        if not steps:
            raise ValueError(f"No electronic steps for ionic step {ionic_step}")

        energies = [s.get("dE", s.get("rms", 0)) for s in steps]
        ns = list(range(1, len(energies) + 1))

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(ns, [abs(e) for e in energies], "g-o", markersize=3)
        ax.set_yscale("log")
        ax.set_xlabel("Electronic Step")
        ax.set_ylabel("|dE| or RMS")
        ax.set_title(title)

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def plot_magnetization(
        self,
        figsize: Tuple[float, float] = (8, 5),
        title: str = "Magnetization Convergence",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot total magnetization vs ionic step."""
        data = self.parser.parse_oszicar()
        ionic = data["ionic_steps"]

        mags = [s.get("mag", 0.0) for s in ionic]
        steps = list(range(1, len(mags) + 1))

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(steps, mags, "m-o", markersize=3)
        ax.set_xlabel("Ionic Step")
        ax.set_ylabel("Total Magnetization ($\\mu_B$)")
        ax.set_title(title)

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig
