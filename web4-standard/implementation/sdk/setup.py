"""
Web4 Python SDK - Setup Configuration

Note: pyproject.toml is the canonical source of packaging metadata.
This setup.py exists for backward compatibility with older pip versions.
"""

from setuptools import setup, find_packages

setup(
    name="web4",
    version="0.8.0",
    author="Web4 Infrastructure Team",
    description="Web4 SDK — trust tensors, LCTs, ATP/ADP, federation (SAL), R7 actions, MRH, ACP, security, protocol types",
    packages=find_packages(include=["web4*"]),
    python_requires=">=3.10",
    package_data={"web4": ["py.typed"]},
)
