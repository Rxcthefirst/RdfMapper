"""Setup configuration for Semantic Model Data Mapper."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rdfmap",
    version="0.1.0",
    author="Enterprise Data Engineering",
    description="Convert spreadsheet data to RDF triples aligned with ontologies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "rdflib>=7.0.0",
        "polars>=0.19.0",
        "openpyxl>=3.1.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "pyshacl>=0.25.0",
        "typer>=0.9.0",
        "PyYAML>=6.0.1",
        "python-dateutil>=2.8.2",
        "rich>=13.7.0",
        "click>=8.1.7",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "mypy>=1.7.1",
            "black>=23.12.0",
            "ruff>=0.1.8",
            "types-PyYAML>=6.0.12",
            "types-python-dateutil>=2.8.19",
            "psutil>=5.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rdfmap=rdfmap.cli.main:app",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
