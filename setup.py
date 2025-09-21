from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ccom",
    version="0.3.2",
    author="Your Name",
    author_email="your.email@example.com",
    description="CCOM v0.3.2 - Claude Code Orchestrator and Memory with Automatic Tool Management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/debashishroy00/ccom",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "ccom=ccom.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ccom": ["templates/*"],
    },
)
