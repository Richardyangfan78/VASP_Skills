from setuptools import setup, find_packages

setup(
    name="vasp_skills",
    version="0.1.0",
    description="Comprehensive Python package for VASP calculation management",
    author="VASP Skills Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "matplotlib",
        "pyyaml",
        "lxml",
    ],
    extras_require={
        "pymatgen": ["pymatgen"],
    },
    entry_points={
        "console_scripts": [
            "vasp-skills=vasp_skills.cli:main",
        ],
    },
)
