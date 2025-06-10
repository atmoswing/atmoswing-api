#!/usr/bin/env python
import os
from setuptools import setup

def read_version():
    with open(os.path.join("atmoswing_api", "__version__.py")) as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip("'\"")

if __name__ == "__main__":
    setup(
        name="atmoswing-api",
        version=read_version(),
        author="Pascal Horton",
    )
