"""INCAR file generation and management with presets for all calculation types."""

from typing import Any, Dict, Optional
from pathlib import Path


# Comprehensive INCAR parameter presets for each calculation type
PRESETS: Dict[str, Dict[str, Any]] = {
    "relaxation": {
        "IBRION": 2,
        "ISIF": 3,
        "NSW": 200,
        "EDIFF": 1e-6,
        "EDIFFG": -0.02,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": "Auto",
        "LWAVE": False,
        "LCHARG": False,
        "NELM": 200,
    },
    "ionic_relaxation": {
        "IBRION": 2,
        "ISIF": 2,
        "NSW": 200,
        "EDIFF": 1e-6,
        "EDIFFG": -0.02,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": "Auto",
        "LWAVE": False,
        "LCHARG": False,
    },
    "scf": {
        "IBRION": -1,
        "NSW": 0,
        "EDIFF": 1e-6,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": "Auto",
        "LWAVE": True,
        "LCHARG": True,
    },
    "band": {
        "IBRION": -1,
        "NSW": 0,
        "ICHARG": 11,
        "LORBIT": 11,
        "EDIFF": 1e-6,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": False,
    },
    "dos": {
        "IBRION": -1,
        "NSW": 0,
        "ICHARG": 11,
        "LORBIT": 11,
        "NEDOS": 3001,
        "EDIFF": 1e-6,
        "PREC": "Accurate",
        "ISMEAR": -5,
        "SIGMA": 0.05,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": False,
    },
    "md": {
        "IBRION": 0,
        "NSW": 5000,
        "POTIM": 1.0,
        "SMASS": 0,
        "TEBEG": 300,
        "TEEND": 300,
        "EDIFF": 1e-5,
        "PREC": "Normal",
        "ISMEAR": 0,
        "SIGMA": 0.1,
        "LREAL": "Auto",
        "LWAVE": False,
        "LCHARG": False,
        "ISYM": 0,
    },
    "elastic": {
        "IBRION": 6,
        "ISIF": 3,
        "NSW": 1,
        "EDIFF": 1e-7,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": False,
    },
    "phonon": {
        "IBRION": 8,
        "EDIFF": 1e-8,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": False,
        "ADDGRID": True,
    },
    "neb": {
        "IBRION": 3,
        "POTIM": 0,
        "ICHAIN": 0,
        "IMAGES": 3,
        "SPRING": -5,
        "LCLIMB": True,
        "NSW": 200,
        "EDIFF": 1e-5,
        "EDIFFG": -0.05,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": "Auto",
        "LWAVE": False,
        "LCHARG": False,
    },
    "dielectric": {
        "IBRION": 8,
        "LEPSILON": True,
        "EDIFF": 1e-8,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": False,
    },
    "magnetic": {
        "ISPIN": 2,
        "IBRION": 2,
        "ISIF": 3,
        "NSW": 200,
        "EDIFF": 1e-6,
        "EDIFFG": -0.02,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": "Auto",
        "LWAVE": False,
        "LCHARG": False,
        "LORBIT": 11,
    },
    "hybrid_hse06": {
        "IBRION": -1,
        "NSW": 0,
        "EDIFF": 1e-6,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,
        "LHFCALC": True,
        "HFSCREEN": 0.2,
        "ALGO": "Damped",
        "TIME": 0.4,
        "LWAVE": True,
        "LCHARG": True,
    },
    "soc": {
        "IBRION": -1,
        "NSW": 0,
        "ISPIN": 2,
        "LSORBIT": True,
        "LNONCOLLINEAR": True,
        "EDIFF": 1e-6,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": False,
        "LORBIT": 11,
    },
    "charge": {
        "IBRION": -1,
        "NSW": 0,
        "EDIFF": 1e-6,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": True,
        "LAECHG": True,
    },
    "workfunction": {
        "IBRION": -1,
        "NSW": 0,
        "EDIFF": 1e-6,
        "PREC": "Accurate",
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": True,
        "LVTOT": True,
        "IDIPOL": 3,
        "LDIPOL": True,
    },
}

# Valid INCAR parameters and their expected types for validation
VALID_PARAMS = {
    "SYSTEM", "ISTART", "ICHARG", "ENCUT", "PREC", "ALGO", "NELM", "NELMIN",
    "EDIFF", "EDIFFG", "NSW", "IBRION", "ISIF", "ISPIN", "MAGMOM",
    "ISMEAR", "SIGMA", "LORBIT", "NEDOS", "EMIN", "EMAX",
    "LREAL", "LWAVE", "LCHARG", "LAECHG", "LVTOT", "LVHAR",
    "NCORE", "NPAR", "KPAR", "LPLANE",
    "LHFCALC", "HFSCREEN", "AEXX", "TIME",
    "LSORBIT", "LNONCOLLINEAR", "SAXIS",
    "POTIM", "SMASS", "TEBEG", "TEEND", "MDALGO",
    "ICHAIN", "IMAGES", "SPRING", "LCLIMB",
    "LEPSILON", "LPEAD",
    "ADDGRID", "LASPH", "LMIXTAU",
    "LDIPOL", "IDIPOL", "DIPOL",
    "GGA", "METAGGA", "IVDW",
    "LDAU", "LDAUTYPE", "LDAUL", "LDAUU", "LDAUJ", "LDAUPRINT",
    "ISYM", "SYMPREC", "NBANDS", "NWRITE",
    "LELF", "LPARD", "NBMOD", "EINT",
}


class Incar:
    """INCAR file generator and manager.

    Usage:
        incar = Incar.from_preset("relaxation", ENCUT=520, NCORE=4)
        incar.write("INCAR")
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params: Dict[str, Any] = {}
        if params:
            self.params.update(params)

    @classmethod
    def from_preset(cls, preset_name: str, **overrides) -> "Incar":
        """Create an Incar from a named preset with optional overrides."""
        if preset_name not in PRESETS:
            raise ValueError(
                f"Unknown preset '{preset_name}'. "
                f"Available: {sorted(PRESETS.keys())}"
            )
        params = dict(PRESETS[preset_name])
        params.update(overrides)
        return cls(params)

    def set(self, key: str, value: Any) -> "Incar":
        """Set a parameter (chainable)."""
        self.params[key.upper()] = value
        return self

    def remove(self, key: str) -> "Incar":
        """Remove a parameter (chainable)."""
        self.params.pop(key.upper(), None)
        return self

    def validate(self) -> list:
        """Validate parameters and return list of warnings."""
        warnings = []
        for key in self.params:
            if key.upper() not in VALID_PARAMS:
                warnings.append(f"Unknown INCAR parameter: {key}")

        # Check common issues
        if self.params.get("IBRION", -1) in (1, 2, 3) and self.params.get("NSW", 0) == 0:
            warnings.append("IBRION is set for relaxation but NSW=0")

        if self.params.get("ICHARG") == 11 and not self.params.get("LCHARG"):
            warnings.append("ICHARG=11 requires CHGCAR from previous SCF calculation")

        if self.params.get("LSORBIT") and not self.params.get("ISPIN", 1) == 2:
            warnings.append("LSORBIT=True typically requires ISPIN=2")

        if self.params.get("ISMEAR", 0) == -5 and self.params.get("NSW", 0) > 0:
            warnings.append("ISMEAR=-5 (tetrahedron) should not be used for relaxation")

        return warnings

    def to_string(self) -> str:
        """Generate INCAR file content as a string."""
        lines = []
        # Group parameters logically
        groups = {
            "General": ["SYSTEM", "PREC", "ENCUT", "ALGO", "NELM", "NELMIN",
                        "EDIFF", "EDIFFG", "LREAL", "ADDGRID", "LASPH"],
            "Electronic": ["ISMEAR", "SIGMA", "ISPIN", "MAGMOM", "LORBIT",
                           "NEDOS", "EMIN", "EMAX", "NBANDS"],
            "Ionic": ["NSW", "IBRION", "ISIF", "POTIM", "ISYM"],
            "IO": ["ISTART", "ICHARG", "LWAVE", "LCHARG", "LAECHG",
                    "LVTOT", "LVHAR", "LELF", "NWRITE"],
            "Parallel": ["NCORE", "NPAR", "KPAR", "LPLANE"],
            "Hybrid": ["LHFCALC", "HFSCREEN", "AEXX", "TIME"],
            "SOC": ["LSORBIT", "LNONCOLLINEAR", "SAXIS"],
            "MD": ["SMASS", "TEBEG", "TEEND", "MDALGO"],
            "NEB": ["ICHAIN", "IMAGES", "SPRING", "LCLIMB"],
            "Dielectric": ["LEPSILON", "LPEAD"],
            "Dipole": ["LDIPOL", "IDIPOL", "DIPOL"],
            "DFT+U": ["LDAU", "LDAUTYPE", "LDAUL", "LDAUU", "LDAUJ", "LDAUPRINT"],
            "vdW": ["IVDW"],
            "Functional": ["GGA", "METAGGA", "LMIXTAU"],
        }

        written = set()
        for group_name, keys in groups.items():
            group_lines = []
            for key in keys:
                if key in self.params:
                    group_lines.append(self._format_param(key, self.params[key]))
                    written.add(key)
            if group_lines:
                lines.append(f"# {group_name}")
                lines.extend(group_lines)
                lines.append("")

        # Write remaining parameters not in any group
        remaining = []
        for key, val in self.params.items():
            if key not in written:
                remaining.append(self._format_param(key, val))
        if remaining:
            lines.append("# Other")
            lines.extend(remaining)
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _format_param(key: str, value: Any) -> str:
        if isinstance(value, bool):
            return f"  {key} = .{str(value).upper()}."
        elif isinstance(value, float):
            return f"  {key} = {value}"
        elif isinstance(value, (list, tuple)):
            return f"  {key} = {' '.join(str(v) for v in value)}"
        else:
            return f"  {key} = {value}"

    def write(self, filepath: str = "INCAR"):
        """Write INCAR file to disk."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(self.to_string())

    @classmethod
    def read(cls, filepath: str = "INCAR") -> "Incar":
        """Read an existing INCAR file."""
        params = {}
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("!"):
                    continue
                # Handle inline comments
                for comment_char in ("#", "!"):
                    if comment_char in line:
                        line = line[:line.index(comment_char)]
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip().upper()
                val = val.strip()
                params[key] = cls._parse_value(val)
        return cls(params)

    @staticmethod
    def _parse_value(val: str) -> Any:
        val = val.strip()
        if val.upper() in (".TRUE.", ".T."):
            return True
        if val.upper() in (".FALSE.", ".F."):
            return False
        # Try int
        try:
            return int(val)
        except ValueError:
            pass
        # Try float
        try:
            return float(val.replace("d", "e").replace("D", "E"))
        except ValueError:
            pass
        # Multiple values
        parts = val.split()
        if len(parts) > 1:
            parsed = []
            for p in parts:
                try:
                    parsed.append(int(p))
                except ValueError:
                    try:
                        parsed.append(float(p.replace("d", "e").replace("D", "E")))
                    except ValueError:
                        parsed.append(p)
            return parsed
        return val

    def __repr__(self) -> str:
        return f"Incar({len(self.params)} parameters)"
