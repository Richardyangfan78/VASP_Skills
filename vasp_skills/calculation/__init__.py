"""Calculation type modules for VASP workflows."""

from vasp_skills.calculation.base import VaspCalculation
from vasp_skills.calculation.relaxation import Relaxation
from vasp_skills.calculation.scf import SCF
from vasp_skills.calculation.band import BandStructure
from vasp_skills.calculation.dos import DOS
from vasp_skills.calculation.md import MolecularDynamics
from vasp_skills.calculation.elastic import Elastic
from vasp_skills.calculation.phonon import Phonon
from vasp_skills.calculation.neb import NEB
from vasp_skills.calculation.dielectric import Dielectric
from vasp_skills.calculation.magnetic import Magnetic
from vasp_skills.calculation.hybrid import Hybrid
from vasp_skills.calculation.soc import SOC
from vasp_skills.calculation.charge import ChargeDensity
from vasp_skills.calculation.workfunction import WorkFunction
from vasp_skills.calculation.surface import SurfaceCalculation
