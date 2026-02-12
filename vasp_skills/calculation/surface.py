"""Surface model calculation with selective dynamics and adsorption."""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.core.poscar import Poscar
from vasp_skills.core.structure import Structure


class SurfaceCalculation(VaspCalculation):
    """Surface slab relaxation with selective dynamics.

    Provides helpers for:
        - Creating slab from bulk
        - Fixing bottom layers
        - Adding adsorbates
        - Surface energy calculation
    """

    preset_name = "ionic_relaxation"

    def __init__(
        self,
        poscar: Poscar,
        directory: str = "surface",
        fix_bottom_layers: Optional[int] = None,
        fix_below_z: Optional[float] = None,
        **kwargs,
    ):
        """
        Args:
            fix_bottom_layers: Number of bottom layers to fix (approximate).
            fix_below_z: Fix atoms with fractional z below this value.
        """
        if fix_below_z is not None:
            poscar = Structure.set_selective_dynamics(
                poscar, fixed_below_z=fix_below_z
            )
        elif fix_bottom_layers is not None:
            frac_z = poscar.to_direct()[:, 2]
            z_sorted = np.sort(np.unique(np.round(frac_z, 4)))
            if fix_bottom_layers <= len(z_sorted):
                threshold = z_sorted[fix_bottom_layers - 1] + 0.01
                poscar = Structure.set_selective_dynamics(
                    poscar, fixed_below_z=threshold
                )
        super().__init__(poscar, directory, **kwargs)

    def extra_incar_params(self) -> Dict[str, Any]:
        return {
            "ISIF": 2,
            "IDIPOL": 3,
            "LDIPOL": True,
        }

    @classmethod
    def from_bulk(
        cls,
        bulk_poscar: Poscar,
        miller: Tuple[int, int, int] = (0, 0, 1),
        layers: int = 5,
        vacuum: float = 15.0,
        fix_bottom: int = 2,
        directory: str = "surface",
        **kwargs,
    ) -> "SurfaceCalculation":
        """Create surface calculation from bulk structure.

        Args:
            bulk_poscar: Bulk unit cell.
            miller: Miller indices.
            layers: Number of layers.
            vacuum: Vacuum thickness in Angstrom.
            fix_bottom: Number of bottom layers to fix.
        """
        slab = Structure.make_surface(bulk_poscar, miller, layers, vacuum)
        return cls(slab, directory, fix_bottom_layers=fix_bottom, **kwargs)

    @staticmethod
    def add_adsorbate(
        slab: Poscar,
        adsorbate_element: str,
        site: str = "top",
        height: float = 2.0,
        atom_index: int = -1,
    ) -> Poscar:
        """Add an adsorbate atom above the slab surface.

        Args:
            slab: Surface slab Poscar.
            adsorbate_element: Element symbol of adsorbate.
            site: 'top' (atop an atom), 'hollow' (center), 'bridge'.
            height: Height above the surface in Angstrom.
            atom_index: For 'top' site, index of surface atom. -1 = highest z.
        """
        cart = slab.to_cartesian()
        frac = slab.to_direct()

        # Find the topmost atom
        z_max_idx = np.argmax(frac[:, 2])
        if atom_index >= 0:
            z_max_idx = atom_index

        if site == "top":
            ads_cart = cart[z_max_idx].copy()
            ads_cart[2] += height
        elif site == "hollow":
            # Average position of top-layer atoms
            z_vals = frac[:, 2]
            top_z = np.max(z_vals)
            top_mask = z_vals > top_z - 0.01
            ads_cart = np.mean(cart[top_mask], axis=0)
            ads_cart[2] = np.max(cart[top_mask, 2]) + height
        elif site == "bridge":
            z_vals = frac[:, 2]
            top_z = np.max(z_vals)
            top_mask = z_vals > top_z - 0.01
            top_indices = np.where(top_mask)[0]
            if len(top_indices) >= 2:
                ads_cart = (cart[top_indices[0]] + cart[top_indices[1]]) / 2
                ads_cart[2] = np.max(cart[top_indices[:2], 2]) + height
            else:
                ads_cart = cart[top_indices[0]].copy()
                ads_cart[2] += height
        else:
            raise ValueError(f"Unknown site type: {site}")

        return Structure.add_atom(slab, adsorbate_element, list(ads_cart), cartesian=True)
