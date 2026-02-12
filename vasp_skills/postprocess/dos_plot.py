"""Density of states plotting."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vasp_skills.postprocess.parser import VaspParser


class DOSPlotter:
    """Plot density of states from VASP DOSCAR output."""

    # Orbital column mapping for LORBIT=11 (s, p, d decomposition)
    ORBITAL_COLS = {
        "s": 1,
        "py": 2, "pz": 3, "px": 4,
        "dxy": 5, "dyz": 6, "dz2": 7, "dxz": 8, "dx2": 9,
    }
    ORBITAL_GROUPS = {
        "s": [1],
        "p": [2, 3, 4],
        "d": [5, 6, 7, 8, 9],
    }

    def __init__(self, directory: str = "."):
        self.directory = Path(directory)
        self.parser = VaspParser(directory)

    def plot_total(
        self,
        efermi: Optional[float] = None,
        xlim: Tuple[float, float] = (-10, 5),
        figsize: Tuple[float, float] = (8, 5),
        fill: bool = True,
        title: str = "Total DOS",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot total density of states.

        Args:
            efermi: Fermi energy. If None, read from DOSCAR.
            xlim: Energy range relative to Fermi level.
            fill: Fill under DOS curve.
            save: Filepath to save.
        """
        dos_data = self.parser.parse_doscar()
        energy = dos_data["energy"]
        total = dos_data["total_dos"]
        ef = efermi if efermi is not None else dos_data["efermi"]

        fig, ax = plt.subplots(figsize=figsize)

        e_shifted = energy - ef

        is_spin = total.shape[1] >= 3

        if is_spin:
            dos_up = total[:, 1]
            dos_down = -total[:, 2]
            if fill:
                ax.fill_between(e_shifted, dos_up, 0, alpha=0.3, color="blue", label="Spin up")
                ax.fill_between(e_shifted, dos_down, 0, alpha=0.3, color="red", label="Spin down")
            else:
                ax.plot(e_shifted, dos_up, "b-", label="Spin up")
                ax.plot(e_shifted, dos_down, "r-", label="Spin down")
            ax.axhline(0, color="k", linewidth=0.3)
        else:
            dos = total[:, 1]
            if fill:
                ax.fill_between(e_shifted, dos, 0, alpha=0.3, color="blue")
            else:
                ax.plot(e_shifted, dos, "b-")

        ax.axvline(0, color="k", linestyle="--", linewidth=0.5, label="$E_F$")
        ax.set_xlim(xlim)
        ax.set_xlabel("Energy (eV)")
        ax.set_ylabel("DOS (states/eV)")
        ax.set_title(title)
        ax.legend()

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def plot_projected(
        self,
        atoms: Optional[List[int]] = None,
        orbitals: Optional[List[str]] = None,
        efermi: Optional[float] = None,
        xlim: Tuple[float, float] = (-10, 5),
        figsize: Tuple[float, float] = (8, 5),
        title: str = "Projected DOS",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot projected DOS for specific atoms and orbitals.

        Args:
            atoms: List of atom indices (0-based).
            orbitals: List of orbital group names ('s', 'p', 'd').
            efermi: Fermi energy.
        """
        dos_data = self.parser.parse_doscar()
        energy = dos_data["energy"]
        ef = efermi if efermi is not None else dos_data["efermi"]
        pdos = dos_data.get("pdos")

        if pdos is None:
            raise ValueError("No projected DOS data in DOSCAR. Use LORBIT=11.")

        if atoms is None:
            atoms = list(pdos.keys())
        if orbitals is None:
            orbitals = ["s", "p", "d"]

        e_shifted = energy - ef
        colors = {"s": "blue", "p": "red", "d": "green", "f": "orange"}

        fig, ax = plt.subplots(figsize=figsize)

        for orb_name in orbitals:
            cols = self.ORBITAL_GROUPS.get(orb_name)
            if cols is None:
                continue

            total_orb = np.zeros(len(energy))
            for iatom in atoms:
                if iatom in pdos:
                    atom_data = pdos[iatom]
                    for col in cols:
                        if col < atom_data.shape[1]:
                            total_orb += atom_data[:, col]

            color = colors.get(orb_name, "gray")
            ax.fill_between(e_shifted, total_orb, 0, alpha=0.3, color=color, label=orb_name)
            ax.plot(e_shifted, total_orb, color=color, linewidth=0.8)

        ax.axvline(0, color="k", linestyle="--", linewidth=0.5, label="$E_F$")
        ax.set_xlim(xlim)
        ax.set_xlabel("Energy (eV)")
        ax.set_ylabel("DOS (states/eV)")
        ax.set_title(title)
        ax.legend()

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def plot_atom_resolved(
        self,
        atom_groups: Dict[str, List[int]],
        orbital: str = "total",
        efermi: Optional[float] = None,
        xlim: Tuple[float, float] = (-10, 5),
        figsize: Tuple[float, float] = (8, 5),
        title: str = "Atom-Resolved DOS",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot DOS resolved by atom groups.

        Args:
            atom_groups: Dict mapping label -> list of atom indices.
                        e.g. {"Fe": [0,1], "O": [2,3,4]}
            orbital: 'total', 's', 'p', or 'd'.
        """
        dos_data = self.parser.parse_doscar()
        energy = dos_data["energy"]
        ef = efermi if efermi is not None else dos_data["efermi"]
        pdos = dos_data.get("pdos")

        if pdos is None:
            raise ValueError("No projected DOS data in DOSCAR.")

        e_shifted = energy - ef
        fig, ax = plt.subplots(figsize=figsize)

        for label, indices in atom_groups.items():
            total = np.zeros(len(energy))
            for iatom in indices:
                if iatom not in pdos:
                    continue
                atom_data = pdos[iatom]
                if orbital == "total":
                    total += atom_data[:, 1:].sum(axis=1)
                elif orbital in self.ORBITAL_GROUPS:
                    for col in self.ORBITAL_GROUPS[orbital]:
                        if col < atom_data.shape[1]:
                            total += atom_data[:, col]

            ax.fill_between(e_shifted, total, 0, alpha=0.3, label=label)
            ax.plot(e_shifted, total, linewidth=0.8)

        ax.axvline(0, color="k", linestyle="--", linewidth=0.5, label="$E_F$")
        ax.set_xlim(xlim)
        ax.set_xlabel("Energy (eV)")
        ax.set_ylabel("DOS (states/eV)")
        ax.set_title(title)
        ax.legend()

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig
