from setuptools import setup, find_packages
from gpu_lock.version import version

with open("README.md", "r") as fh:
    long_description: fh.read()

setup_kwargs = {
    "name": "gpu_lock",
    "version": version,
    "author": "Lorenz Hetzel",
    "author_email": "hetzell@student.ethz.ch",
    "description": "File based locking of GPU resources.",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "url": "https://github.com/idsc-frazzoli/gpu_lock",
    "packages": find_packages(),
    "classifiers": [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    "install_requires": [
        "gputil"
    ],
    "python_requires": '>:3.5',
}

setup(**setup_kwargs)