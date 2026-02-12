"""VASP output file parser for OUTCAR, OSZICAR, vasprun.xml, DOSCAR, EIGENVAL, PROCAR, LOCPOT."""

import re
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class VaspParser:
    """Unified parser for VASP output files."""

    def __init__(self, directory: str = "."):
        self.directory = Path(directory)

    # ── OSZICAR ──────────────────────────────────────────────────────────

    def parse_oszicar(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Parse OSZICAR for electronic and ionic step convergence.

        Returns:
            Dict with keys:
                'ionic_steps': list of dicts with E0, dE, mag per ionic step
                'electronic_steps': list of lists of dicts per ionic step
        """
        fp = Path(filepath) if filepath else self.directory / "OSZICAR"
        ionic_steps = []
        electronic_steps = []
        current_electronic = []

        with open(fp) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Electronic step: starts with number and space
                if re.match(r"^\s*\d+\s", line) and "F=" not in line:
                    parts = line.split()
                    step = {"N": int(parts[0])}
                    for i in range(1, len(parts) - 1, 2):
                        try:
                            step[parts[i]] = float(parts[i + 1])
                        except (ValueError, IndexError):
                            pass
                    current_electronic.append(step)
                # Ionic step
                elif "F=" in line or "E0=" in line:
                    parts = line.split()
                    step_data = {}
                    for i, p in enumerate(parts):
                        if p.endswith("=") and i + 1 < len(parts):
                            try:
                                step_data[p.rstrip("=")] = float(parts[i + 1])
                            except ValueError:
                                pass
                    # Try to extract mag
                    if "mag=" in line:
                        mag_match = re.search(r"mag=\s*([-\d.]+)", line)
                        if mag_match:
                            step_data["mag"] = float(mag_match.group(1))
                    ionic_steps.append(step_data)
                    electronic_steps.append(current_electronic)
                    current_electronic = []

        return {
            "ionic_steps": ionic_steps,
            "electronic_steps": electronic_steps,
        }

    # ── OUTCAR ───────────────────────────────────────────────────────────

    def parse_outcar(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Parse OUTCAR for key results.

        Returns dict with: total_energy, forces, stress, fermi_energy,
        band_gap, magnetization, elastic_tensor, born_charges, etc.
        """
        fp = Path(filepath) if filepath else self.directory / "OUTCAR"
        results = {}

        with open(fp) as f:
            content = f.read()

        # Total energy
        energies = re.findall(r"free  energy   TOTEN\s*=\s*([-\d.]+)", content)
        if energies:
            results["total_energy"] = float(energies[-1])

        # Energy without entropy
        e0_matches = re.findall(r"energy  without entropy\s*=\s*([-\d.]+)", content)
        if e0_matches:
            results["energy_without_entropy"] = float(e0_matches[-1])

        # Fermi energy
        ef_match = re.search(r"E-fermi\s*:\s*([-\d.]+)", content)
        if ef_match:
            results["fermi_energy"] = float(ef_match.group(1))

        # Magnetization
        mag_matches = re.findall(
            r"number of electron\s+([-\d.]+)\s+magnetization\s+([-\d.]+)", content
        )
        if mag_matches:
            results["total_electrons"] = float(mag_matches[-1][0])
            results["total_magnetization"] = float(mag_matches[-1][1])

        # Forces on atoms (last set)
        force_block = re.findall(
            r"TOTAL-FORCE.*?\n-+\n(.*?)\n-+",
            content, re.DOTALL
        )
        if force_block:
            lines = force_block[-1].strip().split("\n")
            forces = []
            positions = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    positions.append([float(x) for x in parts[:3]])
                    forces.append([float(x) for x in parts[3:6]])
            results["forces"] = np.array(forces)
            results["positions"] = np.array(positions)

        # Stress tensor (in kBar)
        stress_match = re.findall(
            r"in kB\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)",
            content
        )
        if stress_match:
            vals = [float(x) for x in stress_match[-1]]
            results["stress_kbar"] = vals  # XX YY ZZ XY YZ ZX

        # Elastic tensor
        elastic_match = re.search(
            r"TOTAL ELASTIC MODULI.*?\n-+\n\s*XX.*?\n(.*?)\n\s*-+",
            content, re.DOTALL
        )
        if elastic_match:
            lines = elastic_match.group(1).strip().split("\n")
            tensor = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 7:
                    tensor.append([float(x) for x in parts[1:7]])
            if tensor:
                results["elastic_tensor"] = np.array(tensor)

        # Convergence check
        results["converged"] = "reached required accuracy" in content

        # Dielectric tensor
        diel_match = re.search(
            r"MACROSCOPIC STATIC DIELECTRIC TENSOR.*?\n-+\n"
            r"\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\n"
            r"\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\n"
            r"\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)",
            content
        )
        if diel_match:
            vals = [float(diel_match.group(i)) for i in range(1, 10)]
            results["dielectric_tensor"] = np.array(vals).reshape(3, 3)

        return results

    # ── vasprun.xml ──────────────────────────────────────────────────────

    def parse_vasprun(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Parse vasprun.xml using lxml for detailed results."""
        fp = Path(filepath) if filepath else self.directory / "vasprun.xml"

        try:
            from lxml import etree
        except ImportError:
            raise ImportError("lxml required for vasprun.xml parsing")

        tree = etree.parse(str(fp))
        root = tree.getroot()
        results = {}

        # Parameters
        incar_elem = root.find(".//incar")
        if incar_elem is not None:
            params = {}
            for item in incar_elem:
                name = item.get("name")
                if name:
                    params[name] = item.text.strip() if item.text else ""
            results["parameters"] = params

        # Final energy
        energy_elems = root.findall(".//calculation/energy")
        if energy_elems:
            last_energy = energy_elems[-1]
            for item in last_energy:
                name = item.get("name")
                if name and item.text:
                    results[f"energy_{name}"] = float(item.text.strip())

        # Eigenvalues
        eigenvalues_elem = root.find(
            ".//calculation[last()]/eigenvalues/array/set"
        )
        if eigenvalues_elem is not None:
            results["has_eigenvalues"] = True

        # DOS
        dos_elem = root.find(".//calculation[last()]/dos")
        if dos_elem is not None:
            results["has_dos"] = True
            ef_elem = dos_elem.find("i[@name='efermi']")
            if ef_elem is not None and ef_elem.text:
                results["efermi"] = float(ef_elem.text.strip())

        # Lattice (final)
        struct_elems = root.findall(".//calculation/structure/crystal/varray[@name='basis']")
        if struct_elems:
            last = struct_elems[-1]
            lattice = []
            for v in last.findall("v"):
                lattice.append([float(x) for x in v.text.split()])
            results["final_lattice"] = np.array(lattice)

        # Positions (final)
        pos_elems = root.findall(".//calculation/structure/varray[@name='positions']")
        if pos_elems:
            last = pos_elems[-1]
            positions = []
            for v in last.findall("v"):
                positions.append([float(x) for x in v.text.split()])
            results["final_positions"] = np.array(positions)

        return results

    # ── DOSCAR ───────────────────────────────────────────────────────────

    def parse_doscar(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Parse DOSCAR for total and projected DOS.

        Returns:
            Dict with:
                'energy': array of energies
                'total_dos': array [energy, dos_up, dos_down] or [energy, dos]
                'pdos': dict of atom-index -> orbital-projected DOS
                'efermi': Fermi energy
        """
        fp = Path(filepath) if filepath else self.directory / "DOSCAR"

        with open(fp) as f:
            lines = f.readlines()

        # Header: 6 lines
        natoms = int(lines[0].split()[0])
        header = lines[5].split()
        emax, emin, nedos = float(header[0]), float(header[1]), int(header[2])
        efermi = float(header[3])

        # Total DOS
        total_dos = []
        for i in range(6, 6 + nedos):
            total_dos.append([float(x) for x in lines[i].split()])
        total_dos = np.array(total_dos)

        results = {
            "energy": total_dos[:, 0],
            "total_dos": total_dos,
            "efermi": efermi,
            "nedos": nedos,
        }

        # Projected DOS (if present)
        if len(lines) > 6 + nedos + 1:
            pdos = {}
            offset = 6 + nedos
            for iatom in range(natoms):
                offset += 1  # header line for each atom
                atom_dos = []
                for j in range(nedos):
                    atom_dos.append([float(x) for x in lines[offset + j].split()])
                pdos[iatom] = np.array(atom_dos)
                offset += nedos
            results["pdos"] = pdos

        return results

    # ── EIGENVAL ─────────────────────────────────────────────────────────

    def parse_eigenval(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Parse EIGENVAL for band eigenvalues.

        Returns:
            Dict with:
                'kpoints': array of k-points
                'eigenvalues': array [nkpts, nbands, (energy, occ)]
                'nkpts', 'nbands', 'nelect'
        """
        fp = Path(filepath) if filepath else self.directory / "EIGENVAL"

        with open(fp) as f:
            lines = f.readlines()

        # Header
        nelect, nkpts, nbands = [int(x) for x in lines[5].split()]

        kpoints = []
        eigenvalues = []

        idx = 7
        for ik in range(nkpts):
            parts = lines[idx].split()
            kpoints.append([float(parts[0]), float(parts[1]), float(parts[2])])
            idx += 1

            bands = []
            for ib in range(nbands):
                parts = lines[idx].split()
                bands.append([float(parts[1]), float(parts[2]) if len(parts) > 2 else 0.0])
                idx += 1
            eigenvalues.append(bands)
            idx += 1  # blank line

        return {
            "kpoints": np.array(kpoints),
            "eigenvalues": np.array(eigenvalues),
            "nkpts": nkpts,
            "nbands": nbands,
            "nelect": nelect,
        }

    # ── PROCAR ───────────────────────────────────────────────────────────

    def parse_procar(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Parse PROCAR for orbital-projected band structure.

        Returns:
            Dict with:
                'kpoints': array
                'eigenvalues': [nkpts, nbands]
                'projections': [nkpts, nbands, natoms, norbitals]
                'orbitals': list of orbital names
        """
        fp = Path(filepath) if filepath else self.directory / "PROCAR"

        with open(fp) as f:
            content = f.read()

        # Header
        header_match = re.search(
            r"# of k-points:\s*(\d+)\s*# of bands:\s*(\d+)\s*# of ions:\s*(\d+)",
            content
        )
        if not header_match:
            raise ValueError("Could not parse PROCAR header")

        nkpts = int(header_match.group(1))
        nbands = int(header_match.group(2))
        natoms = int(header_match.group(3))

        # Find orbital names from the first occurrence
        orb_match = re.search(r"ion\s+(.*?)(?:\n|$)", content)
        orbitals = orb_match.group(1).split() if orb_match else []
        if orbitals and orbitals[-1] == "tot":
            orbitals = orbitals[:-1]
        norb = len(orbitals)

        kpoints = []
        eigenvalues = np.zeros((nkpts, nbands))
        projections = np.zeros((nkpts, nbands, natoms, norb))

        # Parse k-point blocks
        kpt_blocks = re.split(r"k-point\s+\d+\s*:", content)[1:]

        for ik, block in enumerate(kpt_blocks[:nkpts]):
            # k-point coordinates
            kpt_match = re.match(r"\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", block)
            if kpt_match:
                kpoints.append([float(kpt_match.group(i)) for i in (1, 2, 3)])

            # Band blocks
            band_blocks = re.split(r"band\s+\d+", block)[1:]

            for ib, bblock in enumerate(band_blocks[:nbands]):
                # Energy
                e_match = re.search(r"energy\s+([-\d.]+)", bblock)
                if e_match:
                    eigenvalues[ik, ib] = float(e_match.group(1))

                # Ion projections
                ion_lines = re.findall(
                    r"^\s*(\d+)\s+([-\d.]+(?:\s+[-\d.]+)*)",
                    bblock, re.MULTILINE
                )
                for ion_line in ion_lines:
                    iatom = int(ion_line[0]) - 1
                    if iatom < natoms:
                        vals = [float(x) for x in ion_line[1].split()]
                        projections[ik, ib, iatom, :len(vals[:norb])] = vals[:norb]

        return {
            "kpoints": np.array(kpoints) if kpoints else np.array([]),
            "eigenvalues": eigenvalues,
            "projections": projections,
            "orbitals": orbitals,
            "nkpts": nkpts,
            "nbands": nbands,
            "natoms": natoms,
        }

    # ── LOCPOT ───────────────────────────────────────────────────────────

    def parse_locpot(
        self, filepath: Optional[str] = None, axis: int = 2
    ) -> Dict[str, Any]:
        """Parse LOCPOT and compute planar average along an axis.

        Args:
            axis: 0=x, 1=y, 2=z (default z for surface normal).

        Returns:
            Dict with 'position' (Angstrom), 'potential' (eV), 'grid_data'.
        """
        fp = Path(filepath) if filepath else self.directory / "LOCPOT"

        with open(fp) as f:
            lines = f.readlines()

        # Read structure header (same as POSCAR format)
        scale = float(lines[1])
        lattice = np.array(
            [[float(x) for x in lines[i].split()] for i in range(2, 5)]
        )
        lattice *= scale

        # Find atom counts
        try:
            counts = [int(x) for x in lines[5].split()]
            data_start = 8  # after species, counts, coord_type, positions
        except ValueError:
            counts = [int(x) for x in lines[6].split()]
            data_start = 9

        natoms = sum(counts)
        data_start += natoms

        # Grid dimensions
        grid_line = lines[data_start].split()
        ngx, ngy, ngz = int(grid_line[0]), int(grid_line[1]), int(grid_line[2])
        data_start += 1

        # Read potential data
        values = []
        for line in lines[data_start:]:
            values.extend([float(x) for x in line.split()])
            if len(values) >= ngx * ngy * ngz:
                break

        data = np.array(values[:ngx * ngy * ngz]).reshape(ngx, ngy, ngz)

        # Planar average along specified axis
        if axis == 0:
            avg = data.mean(axis=(1, 2))
            length = np.linalg.norm(lattice[0])
        elif axis == 1:
            avg = data.mean(axis=(0, 2))
            length = np.linalg.norm(lattice[1])
        else:
            avg = data.mean(axis=(0, 1))
            length = np.linalg.norm(lattice[2])

        npts = len(avg)
        positions = np.linspace(0, length, npts, endpoint=False)

        return {
            "position": positions,
            "potential": avg,
            "grid_data": data,
            "grid_dims": (ngx, ngy, ngz),
        }

    # ── Convenience ──────────────────────────────────────────────────────

    def get_energy(self) -> float:
        """Get the final total energy from OSZICAR."""
        data = self.parse_oszicar()
        if data["ionic_steps"]:
            return data["ionic_steps"][-1].get("E0", float("nan"))
        return float("nan")

    def get_forces(self) -> np.ndarray:
        """Get final forces from OUTCAR."""
        data = self.parse_outcar()
        return data.get("forces", np.array([]))

    def get_band_gap(self) -> Dict[str, float]:
        """Estimate band gap from EIGENVAL."""
        data = self.parse_eigenval()
        eigs = data["eigenvalues"]  # [nkpts, nbands, (energy, occ)]

        occupied = eigs[:, :, 1] > 0.5
        vbm = -np.inf
        cbm = np.inf
        vbm_k = cbm_k = 0

        for ik in range(data["nkpts"]):
            occ_bands = eigs[ik, occupied[ik], 0]
            unocc_bands = eigs[ik, ~occupied[ik], 0]
            if len(occ_bands) > 0 and np.max(occ_bands) > vbm:
                vbm = np.max(occ_bands)
                vbm_k = ik
            if len(unocc_bands) > 0 and np.min(unocc_bands) < cbm:
                cbm = np.min(unocc_bands)
                cbm_k = ik

        gap = max(0.0, cbm - vbm)
        return {
            "band_gap": gap,
            "vbm": vbm,
            "cbm": cbm,
            "direct": vbm_k == cbm_k,
            "vbm_kindex": vbm_k,
            "cbm_kindex": cbm_k,
        }
