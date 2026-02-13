# VASP Skills

VASP Skills is an agent-oriented toolkit for VASP workflows. It automates the following tasks:

- Generate input files (INCAR/POSCAR/KPOINTS/POTCAR)
- Run and chain multi-step calculation workflows
- Validate inputs and diagnose common runtime errors
- Parse outputs and export/visualize results

---

## 1) Use Cases

- Materials simulation automation (high-throughput DFT)
- LLM agents that need callable, verifiable, and recoverable VASP capabilities
- Standardized skill components for VASP task orchestration

---

## 2) Agent Skill Metadata

This repository provides:

- `agent_skill.yaml`: skill definition, capabilities, input/output contract, and failure policy

Agents can use it for:

- Capability discovery
- Argument validation
- Result interpretation
- Error recovery

---

## 3) Installation

### Production install

```bash
pip install -e .
```

### Development install

```bash
pip install -e .[dev]
```

---

## 4) Quick Start

### 4.1 Generate calculation inputs

```bash
vasp-skills generate relax -p POSCAR -d relax_job
```

### 4.2 Validate inputs

```bash
vasp-skills validate -d relax_job
```

### 4.3 Check runtime errors

```bash
vasp-skills check -d relax_job
```

### 4.4 Parse results

```bash
vasp-skills parse energy -d relax_job
vasp-skills parse forces -d relax_job
vasp-skills parse gap -d relax_job
```

### 4.5 Run a workflow

```bash
vasp-skills workflow bandstructure -p POSCAR -d band_workflow --write-only
```

---

## 5) Input/Output Contract

### Input constraints

- Structure input is POSCAR by default (CIF conversion is supported in some scenarios)
- At minimum, generation requires: `POSCAR`
- Validation requires: `INCAR/POSCAR/KPOINTS/POTCAR`

### Output constraints

- Generation commands produce VASP input files
- Parsing commands produce structured physical metrics (energy, force, band gap, etc.)
- Export commands produce CSV/JSON files

### Failure semantics

- Invalid arguments: command fails fast with a non-zero exit code
- Missing input files: validator returns explicit error list
- Common VASP failures: ErrorHandler returns actionable recovery suggestions

---

## 6) Quality Assurance

- `tests/` provides baseline unit tests
- `.github/workflows/ci.yml` provides minimal CI (install + test)
- `pyproject.toml` provides unified build and test configuration

Run tests:

```bash
pytest -q
```

---

## 7) Project Structure

```text
vasp_skills/
	calculation/   # Calculation templates and execution logic
	core/          # Core INCAR/POSCAR/KPOINTS/POTCAR utilities
	workflow/      # Workflow chaining, validation, and error handling
	postprocess/   # Parsing, exporting, and plotting
```

---

## 8) Notes

- This project does not include the VASP binary; users must have a valid VASP environment and license.
- Default POTCAR path and runtime commands can be configured in `config.yaml`.
- On HPC systems, tune `vasp_cmd` and parallel parameters based on cluster policies.
