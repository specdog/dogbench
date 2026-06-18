from setuptools import setup, find_packages
setup(
    name="dogbench",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["telemetry"],
    scripts=["dogbench"],
    install_requires=["pyyaml"],
    extras_require={"dag": []},  # dotdog is an npm dep, see README
)
