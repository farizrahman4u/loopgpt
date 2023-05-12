from setuptools import setup, find_packages
import os

package_name = "loopgpt"


all_requires = open("requirements.txt", "r").readlines()

install_requires = []
extras_require = {}

for req in all_requires:
    req = req.strip()
    if not req:
        continue
    if req.endswith("]"):
        sp = req.rsplit("[", 1)
        profile = sp[1][:-1]
        package = sp[0]
        if profile not in extras_require:
            extras_require[profile] = []
        extras_require[profile].append(package)
    else:
        install_requires.append(req)


if __name__ == "__main__":
    setup(
        install_requires=install_requires,
        extras_require=extras_require,
        packages=find_packages(),
        name=package_name,
        version="0.0.16",
        description="Modular Auto-GPT Framework",
        entry_points={"console_scripts": ["loopgpt = loopgpt.loops.cli:main"]},
    )
