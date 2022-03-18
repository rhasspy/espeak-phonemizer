"""Setup file for espeak_phonemizer"""
import os
from pathlib import Path

import setuptools

this_dir = Path(__file__).parent
module_dir = this_dir / "espeak_phonemizer"

# -----------------------------------------------------------------------------

# Load README in as long description
long_description: str = ""
readme_path = this_dir / "README.md"
if readme_path.is_file():
    long_description = readme_path.read_text()

version_path = module_dir / "VERSION"
with open(version_path, "r") as version_file:
    version = version_file.read().strip()

# -----------------------------------------------------------------------------

setuptools.setup(
    name="espeak_phonemizer",
    version=version,
    description="Lightweight International Phonetic Alphabet (IPA) phonemizer that uses libespeak-ng",
    author="Michael Hansen",
    author_email="mike@rhasspy.org",
    url="https://github.com/rhasspy/espeak-phonemizer",
    packages=setuptools.find_packages(),
    package_data={"espeak_phonemizer": ["VERSION", "py.typed"]},
    entry_points={
        "console_scripts": [
            "espeak-phonemizer = espeak_phonemizer.__main__:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
