from setuptools import setup, find_packages

setup(
    name="vasp_skills",
    version="0.1.0",
    description="Comprehensive Python package for VASP calculation management",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
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
        "dev": ["pytest>=8.0", "pytest-cov>=5.0"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "vasp-skills=vasp_skills.cli:main",
        ],
    },
)
