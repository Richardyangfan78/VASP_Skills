"""Crystal structure manipulation - supercells, surfaces, defects."""

import numpy as np
from typing import List, Optional, Tuple

from vasp_skills.core.poscar import Poscar


class Structure:
    """Higher-level structure operations built on Poscar."""

    @staticmethod
    def make_supercell(poscar: Poscar, scaling: Tuple[int, int, int]) -> Poscar:
        """Create a supercell."""
        return poscar.make_supercell(scaling)

    @staticmethod
    def make_surface(
        poscar: Poscar,
        miller: Tuple[int, int, int],
        layers: int = 5,
        vacuum: float = 15.0,
    ) -> Poscar:
        """Create a surface slab from a bulk structure.

        Simple implementation for low-index surfaces of cubic/tetragonal cells.
        For complex surfaces, use pymatgen's SlabGenerator.

        Args:
            poscar: Bulk Poscar structure.
            miller: Miller indices (h, k, l).
            layers: Number of atomic layers.
            vacuum: Vacuum thickness in Angstrom.
        """
        h, k, l = miller

        # For simple (001), (010), (100) surfaces of orthorhombic cells
        if sorted([abs(h), abs(k), abs(l)]) == [0, 0, 1]:
            return Structure._make_simple_surface(poscar, miller, layers, vacuum)

        # For general Miller indices, try pymatgen
        try:
            from pymatgen.core import Structure as PMGStructure
            from pymatgen.core.surface import SlabGenerator

            struct = PMGStructure(
                lattice=poscar.lattice * poscar.scale,
                species=poscar.elements,
                coords=poscar.to_direct(),
            )
            slabgen = SlabGenerator(
                struct,
                miller_index=miller,
                min_slab_size=layers * 2.0,
                min_vacuum_size=vacuum,
                center_slab=True,
            )
            slabs = slabgen.get_slabs()
            if not slabs:
                raise ValueError(f"No slabs generated for Miller index {miller}")

            slab = slabs[0]  # Take the first (most stable) slab
            species = []
            counts = []
            for el in slab.composition.elements:
                species.append(str(el))
                counts.append(int(slab.composition[el]))

            return Poscar(
                lattice=slab.lattice.matrix,
                species=species,
                counts=counts,
                positions=slab.frac_coords,
                comment=f"Surface ({h}{k}{l}) - {layers} layers, {vacuum}A vacuum",
                cartesian=False,
            )
        except ImportError:
            raise ImportError(
                f"pymatgen required for general Miller index {miller}. "
                f"Only (001)/(010)/(100) supported natively."
            )

    @staticmethod
    def _make_simple_surface(
        poscar: Poscar,
        miller: Tuple[int, int, int],
        layers: int,
        vacuum: float,
    ) -> Poscar:
        """Create surface for simple low-index planes of orthorhombic cells."""
        h, k, l = miller

        # Determine which axis is the surface normal
        if abs(l) == 1 and h == 0 and k == 0:
            normal_idx = 2  # c-axis
        elif abs(k) == 1 and h == 0 and l == 0:
            normal_idx = 1  # b-axis
        elif abs(h) == 1 and k == 0 and l == 0:
            normal_idx = 0  # a-axis
        else:
            raise ValueError("Only (100), (010), (001) supported natively.")

        # Replicate along normal direction
        scaling = [1, 1, 1]
        scaling[normal_idx] = layers
        slab = poscar.make_supercell(tuple(scaling))

        # Add vacuum along the normal direction
        new_lattice = slab.lattice.copy()
        normal_length = np.linalg.norm(new_lattice[normal_idx])
        total_length = normal_length + vacuum

        # Scale fractional coords to account for vacuum
        frac = slab.to_direct()
        frac[:, normal_idx] *= normal_length / total_length

        # Extend lattice
        new_lattice[normal_idx] *= total_length / normal_length

        return Poscar(
            lattice=new_lattice,
            species=slab.species,
            counts=slab.counts,
            positions=frac,
            comment=f"Surface ({h}{k}{l}) - {layers} layers, {vacuum}A vacuum",
            cartesian=False,
        )

    @staticmethod
    def create_vacancy(
        poscar: Poscar, atom_index: int
    ) -> Poscar:
        """Remove an atom to create a vacancy.

        Args:
            poscar: Input structure.
            atom_index: 0-based index of atom to remove.
        """
        if atom_index < 0 or atom_index >= poscar.natoms:
            raise IndexError(
                f"atom_index {atom_index} out of range [0, {poscar.natoms})"
            )

        frac = poscar.to_direct()
        elements = poscar.elements
        removed_elem = elements[atom_index]

        new_pos = np.delete(frac, atom_index, axis=0)
        new_elements = elements[:atom_index] + elements[atom_index + 1:]

        # Handle selective dynamics
        new_sd = None
        if poscar.sd_flags is not None:
            new_sd = np.delete(poscar.sd_flags, atom_index, axis=0)

        # Rebuild species/counts
        species = []
        counts = []
        for el in new_elements:
            if not species or species[-1] != el:
                species.append(el)
                counts.append(1)
            else:
                counts[-1] += 1

        return Poscar(
            lattice=poscar.lattice.copy(),
            species=species,
            counts=counts,
            positions=new_pos,
            comment=f"{poscar.comment} - vacancy ({removed_elem} #{atom_index})",
            scale=poscar.scale,
            cartesian=False,
            selective_dynamics=poscar.selective_dynamics,
            sd_flags=new_sd,
        )

    @staticmethod
    def substitution(
        poscar: Poscar, atom_index: int, new_element: str
    ) -> Poscar:
        """Substitute an atom with a different element.

        Args:
            poscar: Input structure.
            atom_index: 0-based index of atom to replace.
            new_element: New element symbol.
        """
        if atom_index < 0 or atom_index >= poscar.natoms:
            raise IndexError(
                f"atom_index {atom_index} out of range [0, {poscar.natoms})"
            )

        frac = poscar.to_direct()
        elements = list(poscar.elements)
        old_elem = elements[atom_index]
        elements[atom_index] = new_element

        sd = poscar.sd_flags.copy() if poscar.sd_flags is not None else None

        # Sort so same species are grouped
        indices = sorted(range(len(elements)), key=lambda i: elements[i])
        sorted_elems = [elements[i] for i in indices]
        sorted_pos = frac[indices]
        sorted_sd = sd[indices] if sd is not None else None

        species = []
        counts = []
        for el in sorted_elems:
            if not species or species[-1] != el:
                species.append(el)
                counts.append(1)
            else:
                counts[-1] += 1

        return Poscar(
            lattice=poscar.lattice.copy(),
            species=species,
            counts=counts,
            positions=sorted_pos,
            comment=f"{poscar.comment} - {old_elem}#{atom_index}->{new_element}",
            scale=poscar.scale,
            cartesian=False,
            selective_dynamics=poscar.selective_dynamics,
            sd_flags=sorted_sd,
        )

    @staticmethod
    def add_atom(
        poscar: Poscar,
        element: str,
        position: List[float],
        cartesian: bool = False,
    ) -> Poscar:
        """Add an interstitial atom."""
        frac = poscar.to_direct()
        if cartesian:
            inv_lat = np.linalg.inv(poscar.lattice * poscar.scale)
            new_frac = np.array(position) @ inv_lat
        else:
            new_frac = np.array(position)

        elements = list(poscar.elements) + [element]
        new_pos = np.vstack([frac, new_frac.reshape(1, 3)])

        sd = None
        if poscar.sd_flags is not None:
            sd = np.vstack([poscar.sd_flags, [["T", "T", "T"]]])

        # Sort
        indices = sorted(range(len(elements)), key=lambda i: elements[i])
        sorted_elems = [elements[i] for i in indices]
        sorted_pos = new_pos[indices]
        sorted_sd = sd[indices] if sd is not None else None

        species = []
        counts = []
        for el in sorted_elems:
            if not species or species[-1] != el:
                species.append(el)
                counts.append(1)
            else:
                counts[-1] += 1

        return Poscar(
            lattice=poscar.lattice.copy(),
            species=species,
            counts=counts,
            positions=sorted_pos,
            comment=f"{poscar.comment} - added {element}",
            scale=poscar.scale,
            cartesian=False,
            selective_dynamics=poscar.selective_dynamics,
            sd_flags=sorted_sd,
        )

    @staticmethod
    def set_selective_dynamics(
        poscar: Poscar,
        fixed_indices: Optional[List[int]] = None,
        fixed_below_z: Optional[float] = None,
    ) -> Poscar:
        """Set selective dynamics flags.

        Args:
            poscar: Input structure.
            fixed_indices: List of atom indices to fix.
            fixed_below_z: Fix atoms with fractional z < this value.
        """
        frac = poscar.to_direct()
        sd_flags = np.full((poscar.natoms, 3), "T", dtype="U1")

        if fixed_indices:
            for idx in fixed_indices:
                sd_flags[idx] = ["F", "F", "F"]

        if fixed_below_z is not None:
            for i in range(poscar.natoms):
                if frac[i, 2] < fixed_below_z:
                    sd_flags[i] = ["F", "F", "F"]

        return Poscar(
            lattice=poscar.lattice.copy(),
            species=poscar.species,
            counts=poscar.counts,
            positions=frac,
            comment=poscar.comment,
            scale=poscar.scale,
            cartesian=False,
            selective_dynamics=True,
            sd_flags=sd_flags,
        )
