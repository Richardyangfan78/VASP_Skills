"""Workflow manager for multi-step VASP calculation chains."""

import shutil
from pathlib import Path
from typing import List, Optional

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.calculation.relaxation import Relaxation
from vasp_skills.calculation.scf import SCF
from vasp_skills.calculation.band import BandStructure
from vasp_skills.calculation.dos import DOS
from vasp_skills.core.poscar import Poscar


class WorkflowStep:
    """A single step in a workflow."""

    def __init__(self, calculation: VaspCalculation, name: str = ""):
        self.calculation = calculation
        self.name = name or calculation.__class__.__name__
        self.completed = False

    def __repr__(self):
        status = "done" if self.completed else "pending"
        return f"WorkflowStep({self.name}, {status})"


class WorkflowManager:
    """Manage multi-step VASP workflows.

    Common workflows:
        - relax -> SCF -> band + DOS
        - relax -> SCF -> hybrid
        - relax -> elastic
        - relax -> phonon

    Usage:
        wf = WorkflowManager.standard_bandstructure(poscar, "my_calc")
        wf.write_all()     # Write all input files
        wf.run_all()       # Run sequentially
    """

    def __init__(self, base_dir: str = "workflow"):
        self.base_dir = Path(base_dir)
        self.steps: List[WorkflowStep] = []

    def add_step(self, calculation: VaspCalculation, name: str = "") -> "WorkflowManager":
        """Add a calculation step (chainable)."""
        self.steps.append(WorkflowStep(calculation, name))
        return self

    def write_all(self):
        """Write input files for all steps."""
        for step in self.steps:
            print(f"Writing inputs for: {step.name}")
            step.calculation.write_inputs()

    def run_all(self, vasp_cmd: Optional[str] = None):
        """Run all steps sequentially, passing results between steps."""
        for i, step in enumerate(self.steps):
            print(f"\n{'='*60}")
            print(f"Running step {i+1}/{len(self.steps)}: {step.name}")
            print(f"Directory: {step.calculation.directory}")
            print(f"{'='*60}")

            step.calculation.write_inputs()
            result = step.calculation.run(vasp_cmd)

            if result.returncode != 0:
                print(f"ERROR in step {step.name}:")
                print(result.stderr[:1000] if result.stderr else "No stderr")
                raise RuntimeError(f"Step '{step.name}' failed")

            step.completed = True

            # If next step needs output from this step, transfer files
            if i + 1 < len(self.steps):
                self._transfer_files(step, self.steps[i + 1])

        print("\nWorkflow completed successfully!")

    def _transfer_files(self, from_step: WorkflowStep, to_step: WorkflowStep):
        """Transfer relevant output files between steps."""
        src_dir = from_step.calculation.directory
        dst_dir = to_step.calculation.directory
        dst_dir.mkdir(parents=True, exist_ok=True)

        # Transfer CONTCAR -> POSCAR for relaxation outputs
        contcar = src_dir / "CONTCAR"
        if contcar.exists():
            to_step.calculation.poscar = Poscar.read(str(contcar))

        # Transfer CHGCAR for band/DOS calculations
        chgcar = src_dir / "CHGCAR"
        if chgcar.exists():
            dst = dst_dir / "CHGCAR"
            if not dst.exists():
                shutil.copy2(str(chgcar), str(dst))

        # Transfer WAVECAR for hybrid calculations
        wavecar = src_dir / "WAVECAR"
        if wavecar.exists():
            dst = dst_dir / "WAVECAR"
            if not dst.exists():
                shutil.copy2(str(wavecar), str(dst))

    def status(self) -> str:
        """Get workflow status summary."""
        lines = [f"Workflow: {self.base_dir}", f"Steps: {len(self.steps)}", ""]
        for i, step in enumerate(self.steps, 1):
            status = "DONE" if step.completed else "PENDING"
            lines.append(f"  {i}. [{status}] {step.name} -> {step.calculation.directory}")
        return "\n".join(lines)

    # ── Pre-built workflows ──────────────────────────────────────────────

    @classmethod
    def standard_bandstructure(
        cls,
        poscar: Poscar,
        base_dir: str = "bandstructure_workflow",
        **kwargs,
    ) -> "WorkflowManager":
        """Standard workflow: relax -> SCF -> band + DOS.

        Args:
            poscar: Input structure.
            base_dir: Base directory for all steps.
        """
        wf = cls(base_dir)

        relax = Relaxation(poscar, directory=f"{base_dir}/01_relax", **kwargs)
        wf.add_step(relax, "Relaxation")

        scf = SCF(poscar, directory=f"{base_dir}/02_scf", **kwargs)
        wf.add_step(scf, "SCF")

        band = BandStructure(
            poscar,
            directory=f"{base_dir}/03_band",
            scf_dir=f"{base_dir}/02_scf",
            **kwargs,
        )
        wf.add_step(band, "Band Structure")

        dos = DOS(
            poscar,
            directory=f"{base_dir}/04_dos",
            scf_dir=f"{base_dir}/02_scf",
            **kwargs,
        )
        wf.add_step(dos, "DOS")

        return wf

    @classmethod
    def relaxation_only(
        cls,
        poscar: Poscar,
        base_dir: str = "relax_workflow",
        **kwargs,
    ) -> "WorkflowManager":
        """Two-step relaxation: coarse -> fine."""
        wf = cls(base_dir)

        coarse = Relaxation(
            poscar,
            directory=f"{base_dir}/01_coarse",
            ediffg=-0.05,
            incar_overrides={"EDIFF": 1e-5, "PREC": "Normal"},
            **kwargs,
        )
        wf.add_step(coarse, "Coarse relaxation")

        fine = Relaxation(
            poscar,
            directory=f"{base_dir}/02_fine",
            ediffg=-0.01,
            incar_overrides={"EDIFF": 1e-7, "PREC": "Accurate"},
            **kwargs,
        )
        wf.add_step(fine, "Fine relaxation")

        return wf

    @classmethod
    def magnetic_calculation(
        cls,
        poscar: Poscar,
        base_dir: str = "magnetic_workflow",
        **kwargs,
    ) -> "WorkflowManager":
        """Magnetic workflow: relax (spin-polarized) -> SCF -> DOS."""
        from vasp_skills.calculation.magnetic import Magnetic

        wf = cls(base_dir)

        mag_relax = Magnetic(
            poscar,
            directory=f"{base_dir}/01_mag_relax",
            incar_overrides={"IBRION": 2, "NSW": 200, "ISIF": 3, "EDIFFG": -0.02},
            **kwargs,
        )
        wf.add_step(mag_relax, "Magnetic relaxation")

        mag_scf = Magnetic(
            poscar,
            directory=f"{base_dir}/02_mag_scf",
            incar_overrides={"IBRION": -1, "NSW": 0, "LWAVE": True, "LCHARG": True},
            **kwargs,
        )
        wf.add_step(mag_scf, "Magnetic SCF")

        dos = DOS(
            poscar,
            directory=f"{base_dir}/03_dos",
            scf_dir=f"{base_dir}/02_mag_scf",
            incar_overrides={"ISPIN": 2},
            **kwargs,
        )
        wf.add_step(dos, "DOS")

        return wf

    def __repr__(self):
        done = sum(1 for s in self.steps if s.completed)
        return f"WorkflowManager({len(self.steps)} steps, {done} completed)"
