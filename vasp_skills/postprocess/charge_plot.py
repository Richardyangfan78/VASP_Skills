"""Charge density visualization."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Tuple

from vasp_skills.postprocess.parser import VaspParser


class ChargePlotter:
    """Visualize charge density from CHGCAR or charge difference."""

    def __init__(self, directory: str = "."):
        self.directory = Path(directory)

    def _read_chgcar(self, filepath: str) -> Tuple[np.ndarray, np.ndarray, int, int, int]:
        """Read CHGCAR/PARCHG volumetric data.

        Returns (lattice, data_3d, ngx, ngy, ngz).
        """
        with open(filepath) as f:
            lines = f.readlines()

        scale = float(lines[1])
        lattice = np.array(
            [[float(x) for x in lines[i].split()] for i in range(2, 5)]
        ) * scale

        # Determine data start
        try:
            counts = [int(x) for x in lines[5].split()]
            data_start = 8
        except ValueError:
            counts = [int(x) for x in lines[6].split()]
            data_start = 9

        natoms = sum(counts)
        data_start += natoms

        # Blank line + grid dims
        grid_line = lines[data_start].split()
        ngx, ngy, ngz = int(grid_line[0]), int(grid_line[1]), int(grid_line[2])
        data_start += 1

        values = []
        for line in lines[data_start:]:
            parts = line.split()
            if len(parts) == 0:
                break
            try:
                values.extend([float(x) for x in parts])
            except ValueError:
                break
            if len(values) >= ngx * ngy * ngz:
                break

        data = np.array(values[:ngx * ngy * ngz]).reshape(ngx, ngy, ngz)
        # CHGCAR stores charge * volume
        volume = abs(np.linalg.det(lattice))
        data /= volume

        return lattice, data, ngx, ngy, ngz

    def plot_planar_average(
        self,
        filepath: Optional[str] = None,
        axis: int = 2,
        figsize: Tuple[float, float] = (8, 5),
        title: str = "Planar Average Charge Density",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot planar-averaged charge density along an axis.

        Args:
            filepath: Path to CHGCAR. Defaults to CHGCAR in directory.
            axis: Averaging direction (0=x, 1=y, 2=z).
        """
        fp = filepath or str(self.directory / "CHGCAR")
        lattice, data, ngx, ngy, ngz = self._read_chgcar(fp)

        # Average over the other two axes
        axes_to_avg = tuple(i for i in range(3) if i != axis)
        avg = data.mean(axis=axes_to_avg)
        length = np.linalg.norm(lattice[axis])
        positions = np.linspace(0, length, len(avg), endpoint=False)

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(positions, avg, "b-")
        ax.set_xlabel(f"Position along {'xyz'[axis]} (A)")
        ax.set_ylabel("Charge density (e/A$^3$)")
        ax.set_title(title)

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def plot_slice(
        self,
        filepath: Optional[str] = None,
        axis: int = 2,
        position: float = 0.5,
        figsize: Tuple[float, float] = (6, 6),
        cmap: str = "RdBu_r",
        title: str = "Charge Density Slice",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot a 2D slice of the charge density.

        Args:
            axis: Normal to the slice plane (0=x, 1=y, 2=z).
            position: Fractional position along the axis (0-1).
        """
        fp = filepath or str(self.directory / "CHGCAR")
        lattice, data, ngx, ngy, ngz = self._read_chgcar(fp)

        dims = [ngx, ngy, ngz]
        idx = int(position * dims[axis]) % dims[axis]

        if axis == 0:
            slice_data = data[idx, :, :]
        elif axis == 1:
            slice_data = data[:, idx, :]
        else:
            slice_data = data[:, :, idx]

        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(
            slice_data.T, origin="lower", cmap=cmap, aspect="auto"
        )
        plt.colorbar(im, ax=ax, label="Charge density (e/A$^3$)")
        ax.set_title(f"{title} ({'xyz'[axis]}={position:.2f})")

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig

    def plot_charge_difference(
        self,
        chgcar_total: str,
        chgcar_parts: list,
        axis: int = 2,
        figsize: Tuple[float, float] = (8, 5),
        title: str = "Charge Density Difference",
        save: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Plot charge density difference (total - sum of parts).

        Args:
            chgcar_total: Path to total system CHGCAR.
            chgcar_parts: List of paths to subsystem CHGCARs.
        """
        lat, data_total, _, _, _ = self._read_chgcar(chgcar_total)

        data_sum = np.zeros_like(data_total)
        for part_path in chgcar_parts:
            _, data_part, _, _, _ = self._read_chgcar(part_path)
            data_sum += data_part

        diff = data_total - data_sum

        # Planar average of the difference
        axes_to_avg = tuple(i for i in range(3) if i != axis)
        avg = diff.mean(axis=axes_to_avg)
        length = np.linalg.norm(lat[axis])
        positions = np.linspace(0, length, len(avg), endpoint=False)

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(positions, avg, "b-")
        ax.fill_between(positions, avg, 0, where=avg > 0, alpha=0.3, color="red", label="Accumulation")
        ax.fill_between(positions, avg, 0, where=avg < 0, alpha=0.3, color="blue", label="Depletion")
        ax.axhline(0, color="k", linewidth=0.3)
        ax.set_xlabel(f"Position along {'xyz'[axis]} (A)")
        ax.set_ylabel("$\\Delta\\rho$ (e/A$^3$)")
        ax.set_title(title)
        ax.legend()

        plt.tight_layout()
        if save:
            fig.savefig(save, dpi=dpi, bbox_inches="tight")
        return fig
