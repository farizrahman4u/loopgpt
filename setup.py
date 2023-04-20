from setuptools import setup, find_packages
import os

package_name = "loopgpt"


install_requires = open("requirements.txt", "r").readlines()

if __name__ == "__main__":
    setup(
        install_requires=install_requires,
        packages=find_packages(),
        name=package_name,
        version="0.0.8",
        description="Modular Auto-GPT Framework",
        entry_points={"console_scripts": ["loopgpt = loopgpt.loops.cli:main"]},
    )
