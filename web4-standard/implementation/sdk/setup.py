"""
Web4 Python SDK - Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="web4-sdk",
    version="1.0.0",
    author="Web4 Infrastructure Team",
    author_email="dev@web4.io",
    description="Production-ready Python SDK for Web4 infrastructure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dp-web4/web4",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "PyNaCl>=1.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "examples": [
            "tenacity>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "web4=web4_sdk.cli:main",  # Future CLI tool
        ],
    },
)
