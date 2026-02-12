"""Error detection and fix suggestions for VASP calculations."""

import re
from pathlib import Path
from typing import List, Tuple


class ErrorHandler:
    """Detect common VASP errors and suggest fixes.

    Scans OUTCAR, stdout, and stderr for known error patterns.
    """

    # (pattern, error_name, suggestion)
    ERROR_PATTERNS: List[Tuple[str, str, str]] = [
        (
            r"ZBRENT: fatal internal in",
            "ZBRENT error",
            "Try: 1) Reduce POTIM (e.g. 0.1). "
            "2) Switch IBRION=1 to IBRION=2. "
            "3) Use a better starting geometry.",
        ),
        (
            r"VERY BAD NEWS! internal error in subroutine SGRCON",
            "Symmetry error",
            "Try: Set ISYM=0 or SYMPREC=1e-4.",
        ),
        (
            r"Sub-Space-Matrix is not hermitian",
            "Sub-space matrix error",
            "Try: 1) Set ALGO=Normal or ALGO=VeryFast. "
            "2) Increase NBANDS. 3) Set LREAL=.FALSE.",
        ),
        (
            r"EDWAV: internal error, the gradient is not orthogonal",
            "EDWAV gradient error",
            "Try: 1) Set ALGO=Normal. 2) Reduce ENCUT. "
            "3) Increase NBANDS.",
        ),
        (
            r"BRMIX: very serious problems",
            "Charge mixing failure",
            "Try: 1) Set ALGO=All. 2) Use AMIX=0.1, BMIX=0.001. "
            "3) Increase NELM. 4) Try different AMIN.",
        ),
        (
            r"WARNING: DENTET: can't reach specified precision",
            "Tetrahedron precision warning",
            "Usually harmless. If DOS is noisy, increase k-point density.",
        ),
        (
            r"POSCAR, CURRENTK: total number of ions",
            "POTCAR/POSCAR mismatch",
            "Check that POTCAR elements match POSCAR species in order.",
        ),
        (
            r"Found some non-integer stuff",
            "KPOINTS format error",
            "Check KPOINTS file format. Ensure grid values are integers.",
        ),
        (
            r"EDDRMM: call to ZHEGV failed",
            "ZHEGV diagonalization failure",
            "Try: 1) Set ALGO=Normal. 2) Remove WAVECAR and restart. "
            "3) Check for overlapping atoms.",
        ),
        (
            r"LAPACK: Routine ZPOTRF failed",
            "ZPOTRF failure",
            "Try: 1) Check for overlapping atoms. "
            "2) Remove WAVECAR and restart. 3) Set ALGO=Normal.",
        ),
        (
            r"please rerun with smaller EDIFF",
            "EDIFF too large",
            "Reduce EDIFF (e.g., to 1e-6 or 1e-7).",
        ),
        (
            r"NELM reached",
            "Electronic convergence not reached",
            "Try: 1) Increase NELM. 2) Set ALGO=All. "
            "3) Better charge mixing: AMIX=0.1, BMIX=0.001. "
            "4) Use ISTART=1 with WAVECAR from a converged calculation.",
        ),
        (
            r"exceeded limit for .* in NEB",
            "NEB convergence failure",
            "Try: 1) Increase NSW. 2) Adjust SPRING constant. "
            "3) Use more/fewer images. 4) Check initial/final structures.",
        ),
        (
            r"RHOSYG internal error: stars are not ordered",
            "Symmetry/FFT mesh error",
            "Try: Set ISYM=0 or adjust the FFT grid (NGXF, NGYF, NGZF).",
        ),
        (
            r"REAL_OPTLAY: internal error",
            "REAL_OPTLAY error",
            "Set LREAL=.FALSE. for small systems or adjust ROPT.",
        ),
        (
            r"inverse of rotation matrix was not found",
            "Rotation matrix error",
            "Try: Set ISYM=0 or check structure symmetry.",
        ),
    ]

    def __init__(self, directory: str = "."):
        self.directory = Path(directory)

    def check(self) -> List[dict]:
        """Scan for errors in OUTCAR and return findings.

        Returns:
            List of dicts with 'error', 'suggestion', 'line' keys.
        """
        findings = []

        # Check OUTCAR
        outcar = self.directory / "OUTCAR"
        if outcar.exists():
            findings.extend(self._scan_file(outcar))

        # Check stdout if present
        for stdout_name in ("vasp.out", "stdout", "slurm-*.out"):
            for p in self.directory.glob(stdout_name):
                findings.extend(self._scan_file(p))

        # Check for common non-error issues
        findings.extend(self._check_convergence())

        return findings

    def _scan_file(self, filepath: Path) -> List[dict]:
        """Scan a file for known error patterns."""
        findings = []
        try:
            with open(filepath) as f:
                content = f.read()

            for pattern, name, suggestion in self.ERROR_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    findings.append({
                        "error": name,
                        "suggestion": suggestion,
                        "file": str(filepath),
                        "count": len(matches),
                    })
        except (OSError, UnicodeDecodeError):
            pass

        return findings

    def _check_convergence(self) -> List[dict]:
        """Check for convergence issues."""
        findings = []
        outcar = self.directory / "OUTCAR"

        if not outcar.exists():
            findings.append({
                "error": "No OUTCAR found",
                "suggestion": "Calculation may not have started. Check job submission.",
                "file": str(outcar),
                "count": 0,
            })
            return findings

        with open(outcar) as f:
            content = f.read()

        # Check if calculation finished
        if "General timing and accounting" not in content:
            findings.append({
                "error": "Calculation did not finish",
                "suggestion": "Check walltime, memory, or look for crash messages.",
                "file": str(outcar),
                "count": 1,
            })

        # Check for unconverged ionic relaxation
        if "reached required accuracy" not in content:
            # Check if NSW > 0 (relaxation)
            nsw_match = re.search(r"NSW\s*=\s*(\d+)", content)
            if nsw_match and int(nsw_match.group(1)) > 0:
                findings.append({
                    "error": "Ionic relaxation may not have converged",
                    "suggestion": "Increase NSW or loosen EDIFFG. "
                                  "Check that forces are decreasing.",
                    "file": str(outcar),
                    "count": 1,
                })

        return findings

    def report(self) -> str:
        """Generate a human-readable error report."""
        findings = self.check()

        if not findings:
            return "No errors or warnings detected."

        lines = [f"Error Report for: {self.directory}", "=" * 60]

        for f in findings:
            lines.append(f"\n[{f['error']}]")
            lines.append(f"  File: {f['file']}")
            if f.get("count", 0) > 1:
                lines.append(f"  Occurrences: {f['count']}")
            lines.append(f"  Suggestion: {f['suggestion']}")

        return "\n".join(lines)
