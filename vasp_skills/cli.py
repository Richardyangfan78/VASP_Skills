"""Command-line interface for VASP Skills."""

import argparse
import sys
from pathlib import Path
import numpy as np


def cmd_generate(args):
    """Generate input files for a calculation type."""
    from vasp_skills.core.poscar import Poscar
    from vasp_skills.calculation.relaxation import Relaxation
    from vasp_skills.calculation.scf import SCF
    from vasp_skills.calculation.band import BandStructure
    from vasp_skills.calculation.dos import DOS
    from vasp_skills.calculation.md import MolecularDynamics
    from vasp_skills.calculation.elastic import Elastic
    from vasp_skills.calculation.phonon import Phonon
    from vasp_skills.calculation.dielectric import Dielectric
    from vasp_skills.calculation.magnetic import Magnetic
    from vasp_skills.calculation.hybrid import Hybrid
    from vasp_skills.calculation.soc import SOC
    from vasp_skills.calculation.charge import ChargeDensity
    from vasp_skills.calculation.workfunction import WorkFunction

    calc_map = {
        "relax": Relaxation,
        "scf": SCF,
        "band": BandStructure,
        "dos": DOS,
        "md": MolecularDynamics,
        "elastic": Elastic,
        "phonon": Phonon,
        "dielectric": Dielectric,
        "magnetic": Magnetic,
        "hybrid": Hybrid,
        "soc": SOC,
        "charge": ChargeDensity,
        "workfunction": WorkFunction,
    }

    calc_type = args.type
    if calc_type not in calc_map:
        print(f"Unknown calculation type: {calc_type}")
        print(f"Available: {', '.join(sorted(calc_map.keys()))}")
        sys.exit(1)

    poscar = Poscar.read(args.poscar)
    outdir = args.directory or calc_type

    kwargs = {}
    if args.encut:
        kwargs["encut"] = args.encut

    calc_cls = calc_map[calc_type]
    calc = calc_cls(poscar, directory=outdir, **kwargs)
    calc.write_inputs()
    print(f"Input files written to: {outdir}/")


def cmd_validate(args):
    """Validate input files."""
    from vasp_skills.workflow.validator import InputValidator

    validator = InputValidator()
    result = validator.validate_directory(args.directory)
    print(result)
    if not result.is_valid:
        sys.exit(1)


def cmd_check_errors(args):
    """Check for errors in calculation output."""
    from vasp_skills.workflow.error_handler import ErrorHandler

    handler = ErrorHandler(args.directory)
    print(handler.report())


def cmd_parse(args):
    """Parse and display calculation results."""
    from vasp_skills.postprocess.parser import VaspParser

    parser = VaspParser(args.directory)

    if args.what == "energy":
        energy = parser.get_energy()
        print(f"Total energy: {energy:.6f} eV")

    elif args.what == "forces":
        forces = parser.get_forces()
        if forces.size > 0:
            max_f = max(float(np.linalg.norm(f)) for f in forces)
            print(f"Max force: {max_f:.6f} eV/A")
            print(f"Atoms: {len(forces)}")
        else:
            print("No force data found")

    elif args.what == "gap":
        gap = parser.get_band_gap()
        gap_type = "direct" if gap["direct"] else "indirect"
        print(f"Band gap: {gap['band_gap']:.4f} eV ({gap_type})")
        print(f"VBM: {gap['vbm']:.4f} eV, CBM: {gap['cbm']:.4f} eV")

    elif args.what == "summary":
        outcar = parser.parse_outcar()
        for key, val in outcar.items():
            if not isinstance(val, (list, dict)) and not hasattr(val, 'shape'):
                print(f"  {key}: {val}")

    else:
        print(f"Unknown parse target: {args.what}")
        print("Available: energy, forces, gap, summary")


def cmd_plot(args):
    """Generate plots from calculation output."""
    from vasp_skills.postprocess.band_plot import BandPlotter
    from vasp_skills.postprocess.dos_plot import DOSPlotter
    from vasp_skills.postprocess.convergence import ConvergencePlotter
    from vasp_skills.postprocess.workfunction_plot import WorkfunctionPlotter

    if args.what == "band":
        plotter = BandPlotter(args.directory)
        plotter.plot(save=args.output or "band.png")
        print(f"Band structure saved to: {args.output or 'band.png'}")

    elif args.what == "dos":
        plotter = DOSPlotter(args.directory)
        plotter.plot_total(save=args.output or "dos.png")
        print(f"DOS plot saved to: {args.output or 'dos.png'}")

    elif args.what == "convergence":
        plotter = ConvergencePlotter(args.directory)
        plotter.plot_energy(save=args.output or "convergence.png")
        print(f"Convergence plot saved to: {args.output or 'convergence.png'}")

    elif args.what == "workfunction":
        plotter = WorkfunctionPlotter(args.directory)
        plotter.plot(save=args.output or "workfunction.png")
        print(f"Work function plot saved to: {args.output or 'workfunction.png'}")

    else:
        print(f"Unknown plot type: {args.what}")
        print("Available: band, dos, convergence, workfunction")


def cmd_export(args):
    """Export data to CSV/JSON."""
    from vasp_skills.postprocess.exporter import DataExporter

    exporter = DataExporter(args.directory)

    if args.what == "summary":
        exporter.export_summary(args.output or "summary.json")
        print(f"Summary exported to: {args.output or 'summary.json'}")

    elif args.what == "dos":
        exporter.export_dos(args.output or "dos.csv")
        print(f"DOS exported to: {args.output or 'dos.csv'}")

    elif args.what == "band":
        exporter.export_band(args.output or "band.csv")
        print(f"Band data exported to: {args.output or 'band.csv'}")

    elif args.what == "energy":
        exporter.export_energy_convergence(args.output or "energy_convergence.csv")
        print(f"Energy data exported to: {args.output or 'energy_convergence.csv'}")

    elif args.what == "forces":
        exporter.export_forces(args.output or "forces.csv")
        print(f"Force data exported to: {args.output or 'forces.csv'}")

    else:
        print(f"Unknown export target: {args.what}")
        print("Available: summary, dos, band, energy, forces")


def cmd_workflow(args):
    """Run pre-built workflows."""
    from vasp_skills.core.poscar import Poscar
    from vasp_skills.workflow.manager import WorkflowManager

    poscar = Poscar.read(args.poscar)

    workflow_map = {
        "bandstructure": WorkflowManager.standard_bandstructure,
        "relax": WorkflowManager.relaxation_only,
        "magnetic": WorkflowManager.magnetic_calculation,
    }

    if args.type not in workflow_map:
        print(f"Unknown workflow: {args.type}")
        print(f"Available: {', '.join(sorted(workflow_map.keys()))}")
        sys.exit(1)

    wf = workflow_map[args.type](poscar, base_dir=args.directory or args.type)

    if args.write_only:
        wf.write_all()
        print(wf.status())
    else:
        wf.run_all()
        print(wf.status())


def main():
    parser = argparse.ArgumentParser(
        prog="vasp-skills",
        description="VASP Skills - VASP calculation management toolkit",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen_parser = subparsers.add_parser("generate", aliases=["gen"],
                                       help="Generate input files")
    gen_parser.add_argument("type", help="Calculation type")
    gen_parser.add_argument("-p", "--poscar", default="POSCAR",
                           help="Input POSCAR file")
    gen_parser.add_argument("-d", "--directory", help="Output directory")
    gen_parser.add_argument("--encut", type=float, help="Override ENCUT")
    gen_parser.set_defaults(func=cmd_generate)

    # validate
    val_parser = subparsers.add_parser("validate", aliases=["val"],
                                       help="Validate input files")
    val_parser.add_argument("-d", "--directory", default=".",
                           help="Directory to validate")
    val_parser.set_defaults(func=cmd_validate)

    # check
    chk_parser = subparsers.add_parser("check", help="Check for errors")
    chk_parser.add_argument("-d", "--directory", default=".",
                           help="Calculation directory")
    chk_parser.set_defaults(func=cmd_check_errors)

    # parse
    parse_parser = subparsers.add_parser("parse", help="Parse results")
    parse_parser.add_argument("what", help="What to parse: energy, forces, gap, summary")
    parse_parser.add_argument("-d", "--directory", default=".",
                             help="Calculation directory")
    parse_parser.set_defaults(func=cmd_parse)

    # plot
    plot_parser = subparsers.add_parser("plot", help="Generate plots")
    plot_parser.add_argument("what", help="What to plot: band, dos, convergence, workfunction")
    plot_parser.add_argument("-d", "--directory", default=".",
                            help="Calculation directory")
    plot_parser.add_argument("-o", "--output", help="Output filename")
    plot_parser.set_defaults(func=cmd_plot)

    # export
    exp_parser = subparsers.add_parser("export", help="Export data")
    exp_parser.add_argument("what", help="What to export: summary, dos, band, energy, forces")
    exp_parser.add_argument("-d", "--directory", default=".",
                           help="Calculation directory")
    exp_parser.add_argument("-o", "--output", help="Output filename")
    exp_parser.set_defaults(func=cmd_export)

    # workflow
    wf_parser = subparsers.add_parser("workflow", aliases=["wf"],
                                      help="Run workflows")
    wf_parser.add_argument("type", help="Workflow type: bandstructure, relax, magnetic")
    wf_parser.add_argument("-p", "--poscar", default="POSCAR",
                          help="Input POSCAR file")
    wf_parser.add_argument("-d", "--directory", help="Base directory")
    wf_parser.add_argument("--write-only", action="store_true",
                          help="Only write inputs, don't run")
    wf_parser.set_defaults(func=cmd_workflow)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
