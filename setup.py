#!/usr/bin/env python
import os
from setuptools import setup

def read_version():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, "atmoswing_api", "__version__.py")) as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip("'\"")
        return None


if __name__ == "__main__":
    setup(
        name="atmoswing-api",
        version=read_version(),
        author="Pascal Horton",
    )
