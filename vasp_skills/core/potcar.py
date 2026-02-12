"""POTCAR file management - auto-assemble from POTCAR library directory."""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path

from vasp_skills.config import Config

# Recommended POTCAR variants for each element
RECOMMENDED_POTCARS: Dict[str, str] = {
    "Li": "Li_sv", "Be": "Be", "B": "B", "C": "C", "N": "N", "O": "O", "F": "F",
    "Na": "Na_pv", "Mg": "Mg", "Al": "Al", "Si": "Si", "P": "P", "S": "S", "Cl": "Cl",
    "K": "K_sv", "Ca": "Ca_sv", "Sc": "Sc_sv", "Ti": "Ti_sv", "V": "V_sv",
    "Cr": "Cr_pv", "Mn": "Mn_pv", "Fe": "Fe", "Co": "Co", "Ni": "Ni",
    "Cu": "Cu", "Zn": "Zn", "Ga": "Ga_d", "Ge": "Ge_d", "As": "As",
    "Se": "Se", "Br": "Br", "Rb": "Rb_sv", "Sr": "Sr_sv", "Y": "Y_sv",
    "Zr": "Zr_sv", "Nb": "Nb_sv", "Mo": "Mo_sv", "Ru": "Ru_pv",
    "Rh": "Rh_pv", "Pd": "Pd", "Ag": "Ag", "Cd": "Cd", "In": "In_d",
    "Sn": "Sn_d", "Sb": "Sb", "Te": "Te", "I": "I",
    "Cs": "Cs_sv", "Ba": "Ba_sv", "La": "La", "Ce": "Ce",
    "Hf": "Hf_pv", "Ta": "Ta_pv", "W": "W_sv", "Re": "Re", "Os": "Os",
    "Ir": "Ir", "Pt": "Pt", "Au": "Au", "Hg": "Hg", "Tl": "Tl_d",
    "Pb": "Pb_d", "Bi": "Bi_d",
    "H": "H", "He": "He",
}


class Potcar:
    """POTCAR file assembler.

    Reads individual element POTCARs from a library directory and
    concatenates them for a given list of elements.
    """

    def __init__(
        self,
        species: List[str],
        potcar_dir: Optional[str] = None,
        variants: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            species: List of element symbols in POSCAR order.
            potcar_dir: Path to POTCAR library. Defaults to config value.
            variants: Dict mapping element -> variant name.
                     e.g. {"Fe": "Fe_pv", "O": "O"}.
                     If not specified, uses recommended defaults.
        """
        self.species = list(species)
        config = Config()
        self.potcar_dir = potcar_dir or config.potcar_dir
        self.variants = variants or {}
        self._content: Optional[str] = None
        self._titles: List[str] = []

    def _get_potcar_path(self, element: str) -> str:
        """Find the POTCAR file path for a given element."""
        # Check explicit variant first
        variant = self.variants.get(element)
        if variant is None:
            variant = RECOMMENDED_POTCARS.get(element, element)

        # Try the variant name as a subdirectory
        candidates = [
            os.path.join(self.potcar_dir, variant, "POTCAR"),
            os.path.join(self.potcar_dir, element, "POTCAR"),
        ]

        for path in candidates:
            if os.path.isfile(path):
                return path

        raise FileNotFoundError(
            f"POTCAR not found for '{element}' (variant='{variant}'). "
            f"Searched in: {self.potcar_dir}. "
            f"Expected: {candidates}"
        )

    def assemble(self) -> str:
        """Assemble POTCAR content by concatenating element POTCARs."""
        if self._content is not None:
            return self._content

        parts = []
        self._titles = []

        for element in self.species:
            path = self._get_potcar_path(element)
            with open(path) as f:
                content = f.read()
            parts.append(content)

            # Extract title from first line
            first_line = content.split("\n")[0].strip()
            self._titles.append(first_line)

        # Ensure each part ends with newline
        self._content = "".join(
            p if p.endswith("\n") else p + "\n" for p in parts
        )
        return self._content

    @property
    def titles(self) -> List[str]:
        """POTCAR title lines for each element."""
        if not self._titles:
            self.assemble()
        return self._titles

    def write(self, filepath: str = "POTCAR"):
        """Write assembled POTCAR to file."""
        content = self.assemble()
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)

    @staticmethod
    def read_titles(filepath: str = "POTCAR") -> List[str]:
        """Read element titles from an existing POTCAR file."""
        titles = []
        with open(filepath) as f:
            for line in f:
                if "PAW_PBE" in line or "PAW_LDA" in line or "US" in line:
                    titles.append(line.strip())
        return titles

    @staticmethod
    def read_elements(filepath: str = "POTCAR") -> List[str]:
        """Extract element names from POTCAR titles."""
        titles = Potcar.read_titles(filepath)
        elements = []
        for title in titles:
            # Title format: "PAW_PBE Si 05Jan2001" or "PAW_PBE Fe_pv 06Sep2000"
            parts = title.split()
            if len(parts) >= 2:
                elem_part = parts[1]
                # Strip variant suffixes
                elem = re.split(r"[_\d]", elem_part)[0]
                if elem:
                    elements.append(elem)
        return elements

    def get_enmax(self) -> Dict[str, float]:
        """Extract ENMAX values from POTCAR files."""
        enmax = {}
        for element in self.species:
            path = self._get_potcar_path(element)
            with open(path) as f:
                for line in f:
                    if "ENMAX" in line:
                        match = re.search(r"ENMAX\s*=\s*([\d.]+)", line)
                        if match:
                            enmax[element] = float(match.group(1))
                        break
        return enmax

    def suggested_encut(self, factor: float = 1.3) -> float:
        """Suggest ENCUT as factor * max(ENMAX)."""
        enmax = self.get_enmax()
        if not enmax:
            return 520.0  # safe default
        return round(max(enmax.values()) * factor)

    def validate_against_poscar(self, species: List[str]) -> List[str]:
        """Validate that POTCAR elements match POSCAR species."""
        errors = []
        if len(self.species) != len(species):
            errors.append(
                f"POTCAR has {len(self.species)} elements but "
                f"POSCAR has {len(species)}"
            )
        for i, (pot, pos) in enumerate(zip(self.species, species)):
            if pot != pos:
                errors.append(
                    f"Element mismatch at position {i}: "
                    f"POTCAR={pot}, POSCAR={pos}"
                )
        return errors

    def __repr__(self) -> str:
        return f"Potcar({', '.join(self.species)})"
