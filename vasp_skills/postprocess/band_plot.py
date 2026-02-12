"""Band structure plotting."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vasp_skills.postprocess.parser import VaspParser


class BandPlotter:
    """Plot electronic band structure from VASP output.

    Reads EIGENVAL (and optionally PROCAR for orbital projection)
    along with KPOINTS (line-mode) to produce publication-quality band plots.
    """

    def __init__(self, directory: str = "."):
        self.directory = Path(directory)
        self.parser = VaspParser(directory)

    def plot(
        self,
        efermi: Optional[float] = None,
        ylim: Tuple[float, float] = (-5, 5),
        color: str = "b",
        linewidth: float = 1.0,
        figsize: Tuple[float, float] = (8, 6),
        title: str = "Band Structure",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot band structure.

        Args:
            efermi: Fermi energy. If None, reads from OUTCAR/DOSCAR.
            ylim: Energy range relative to Fermi level.
            color: Line color.
            save: Filepath to save figure. None = show interactively.
        """
        eigenval = self.parser.parse_eigenval()
        kpoints = eigenval["kpoints"]
        eigs = eigenval["eigenvalues"]  # [nkpts, nbands, (energy, occ)]
        nkpts = eigenval["nkpts"]
        nbands = eigenval["nbands"]

        # Get Fermi energy
        if efermi is None:
            try:
                outcar = self.parser.parse_outcar()
                efermi = outcar.get("fermi_energy", 0.0)
            except FileNotFoundError:
                efermi = 0.0

        # Build k-distance for x-axis
        kdist = self._compute_kdist(kpoints)

        # Read k-path labels from KPOINTS
        labels, label_positions = self._read_kpath_labels(kdist)

        fig, ax = plt.subplots(figsize=figsize)

        for ib in range(nbands):
            energies = eigs[:, ib, 0] - efermi
            ax.plot(kdist, energies, color=color, linewidth=linewidth)

        # Fermi level
        ax.axhline(0, color="k", linestyle="--", linewidth=0.5, alpha=0.7)

        # High-symmetry labels
        if label_positions:
            for pos in label_positions:
                ax.axvline(pos, color="gray", linestyle="-", linewidth=0.5, alpha=0.5)
            ax.set_xticks(label_positions)
            ax.set_xticklabels(labels)

        ax.set_xlim(kdist[0], kdist[-1])
        ax.set_ylim(ylim)
        ax.set_ylabel("Energy (eV)")
        ax.set_title(title)

        plt.tight_layout()

        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def plot_projected(
        self,
        atoms: Optional[List[int]] = None,
        orbitals: Optional[List[str]] = None,
        efermi: Optional[float] = None,
        ylim: Tuple[float, float] = (-5, 5),
        figsize: Tuple[float, float] = (8, 6),
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot orbital-projected band structure (fat bands).

        Args:
            atoms: List of atom indices to project onto.
            orbitals: List of orbital names (s, p, d, etc.).
        """
        procar = self.parser.parse_procar()
        eigenval = self.parser.parse_eigenval()
        kpoints = eigenval["kpoints"]
        eigs = eigenval["eigenvalues"]
        nkpts = eigenval["nkpts"]
        nbands = eigenval["nbands"]

        if efermi is None:
            try:
                outcar = self.parser.parse_outcar()
                efermi = outcar.get("fermi_energy", 0.0)
            except FileNotFoundError:
                efermi = 0.0

        kdist = self._compute_kdist(kpoints)

        # Select atoms and orbitals
        all_orbitals = procar["orbitals"]
        proj = procar["projections"]  # [nkpts, nbands, natoms, norb]

        if atoms is None:
            atoms = list(range(procar["natoms"]))
        if orbitals is None:
            orb_indices = list(range(len(all_orbitals)))
        else:
            orb_indices = [all_orbitals.index(o) for o in orbitals if o in all_orbitals]

        # Sum projections
        weights = proj[:, :, :, :][:, :, atoms, :][:, :, :, orb_indices].sum(axis=(2, 3))

        fig, ax = plt.subplots(figsize=figsize)

        for ib in range(nbands):
            energies = eigs[:, ib, 0] - efermi
            w = weights[:, ib]
            w_norm = w / (w.max() + 1e-10)
            ax.scatter(kdist, energies, c=w_norm, s=w_norm * 20, cmap="Reds", alpha=0.8)

        ax.axhline(0, color="k", linestyle="--", linewidth=0.5)
        ax.set_xlim(kdist[0], kdist[-1])
        ax.set_ylim(ylim)
        ax.set_ylabel("Energy (eV)")
        ax.set_title("Projected Band Structure")

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def _compute_kdist(self, kpoints: np.ndarray) -> np.ndarray:
        """Compute cumulative k-distance along the path."""
        dists = [0.0]
        for i in range(1, len(kpoints)):
            dk = np.linalg.norm(kpoints[i] - kpoints[i - 1])
            dists.append(dists[-1] + dk)
        return np.array(dists)

    def _read_kpath_labels(
        self, kdist: np.ndarray
    ) -> Tuple[List[str], List[float]]:
        """Read k-path labels from KPOINTS file."""
        kpoints_file = self.directory / "KPOINTS"
        labels = []
        positions = []

        if not kpoints_file.exists():
            return labels, positions

        with open(kpoints_file) as f:
            lines = f.readlines()

        if len(lines) < 4:
            return labels, positions

        # Check for line-mode
        mode_line = lines[2].strip().lower()
        if not mode_line.startswith("l"):
            return labels, positions

        npoints = int(lines[1].strip())

        # Read label lines
        kpt_labels = []
        for line in lines[4:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split("!")
            if len(parts) >= 2:
                kpt_labels.append(parts[1].strip())
            else:
                kpt_labels.append("")

        # Map labels to k-distances
        # In line-mode, labels come in pairs (start, end of each segment)
        for i in range(0, len(kpt_labels), 2):
            seg_start = (i // 2) * npoints
            seg_end = seg_start + npoints - 1

            if seg_start < len(kdist):
                lbl = kpt_labels[i].replace("GAMMA", "\u0393").replace("G", "\u0393")
                if not labels or positions[-1] != kdist[seg_start]:
                    labels.append(lbl)
                    positions.append(kdist[seg_start])
                else:
                    # Merge labels at same position
                    labels[-1] = f"{labels[-1]}|{lbl}"

            if i + 1 < len(kpt_labels) and seg_end < len(kdist):
                lbl = kpt_labels[i + 1].replace("GAMMA", "\u0393").replace("G", "\u0393")
                labels.append(lbl)
                positions.append(kdist[seg_end])

        return labels, positions
