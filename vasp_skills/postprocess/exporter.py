"""Data export utilities for VASP results (CSV, JSON)."""

import csv
import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional

from vasp_skills.postprocess.parser import VaspParser


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)


class DataExporter:
    """Export parsed VASP data to CSV and JSON formats."""

    def __init__(self, directory: str = "."):
        self.directory = Path(directory)
        self.parser = VaspParser(directory)

    def export_energy_convergence(self, filepath: str = "energy_convergence.csv"):
        """Export ionic step energies to CSV."""
        data = self.parser.parse_oszicar()
        ionic = data["ionic_steps"]

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            keys = sorted({k for step in ionic for k in step.keys()})
            writer.writerow(["step"] + keys)
            for i, step in enumerate(ionic, 1):
                row = [i] + [step.get(k, "") for k in keys]
                writer.writerow(row)

    def export_dos(self, filepath: str = "dos.csv"):
        """Export total DOS to CSV."""
        data = self.parser.parse_doscar()
        total = data["total_dos"]

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            ncols = total.shape[1]
            if ncols >= 5:
                header = ["energy", "dos_up", "dos_down", "int_up", "int_down"]
            elif ncols >= 3:
                header = ["energy", "dos_up", "dos_down"]
            else:
                header = ["energy", "dos"]
            writer.writerow(header)
            for row in total:
                writer.writerow(row[:len(header)])

    def export_band(self, filepath: str = "band.csv", efermi: float = 0.0):
        """Export band eigenvalues to CSV."""
        data = self.parser.parse_eigenval()
        eigs = data["eigenvalues"]
        kpoints = data["kpoints"]

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            header = ["kx", "ky", "kz"] + [f"band_{i+1}" for i in range(data["nbands"])]
            writer.writerow(header)
            for ik in range(data["nkpts"]):
                row = list(kpoints[ik]) + [eigs[ik, ib, 0] - efermi for ib in range(data["nbands"])]
                writer.writerow(row)

    def export_forces(self, filepath: str = "forces.csv"):
        """Export final forces to CSV."""
        data = self.parser.parse_outcar()
        forces = data.get("forces")
        positions = data.get("positions")

        if forces is None:
            raise ValueError("No force data in OUTCAR")

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["atom", "x", "y", "z", "fx", "fy", "fz", "f_norm"])
            for i in range(len(forces)):
                pos = positions[i] if positions is not None else [0, 0, 0]
                f_norm = np.linalg.norm(forces[i])
                writer.writerow([i] + list(pos) + list(forces[i]) + [f_norm])

    def export_summary(self, filepath: str = "summary.json"):
        """Export a summary of calculation results to JSON."""
        summary: Dict[str, Any] = {}

        try:
            outcar = self.parser.parse_outcar()
            summary["total_energy"] = outcar.get("total_energy")
            summary["fermi_energy"] = outcar.get("fermi_energy")
            summary["converged"] = outcar.get("converged")
            summary["total_magnetization"] = outcar.get("total_magnetization")
            if "stress_kbar" in outcar:
                summary["stress_kbar"] = outcar["stress_kbar"]
            if "elastic_tensor" in outcar:
                summary["elastic_tensor"] = outcar["elastic_tensor"]
            if "dielectric_tensor" in outcar:
                summary["dielectric_tensor"] = outcar["dielectric_tensor"]
        except FileNotFoundError:
            pass

        try:
            gap_info = self.parser.get_band_gap()
            summary["band_gap"] = gap_info
        except FileNotFoundError:
            pass

        try:
            oszicar = self.parser.parse_oszicar()
            summary["n_ionic_steps"] = len(oszicar["ionic_steps"])
        except FileNotFoundError:
            pass

        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2, cls=_NumpyEncoder)

    def export_locpot(self, filepath: str = "locpot.csv", axis: int = 2):
        """Export planar-averaged LOCPOT to CSV."""
        data = self.parser.parse_locpot(axis=axis)

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["position_angstrom", "potential_eV"])
            for pos, pot in zip(data["position"], data["potential"]):
                writer.writerow([pos, pot])
