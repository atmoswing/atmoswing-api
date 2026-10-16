from importlib.metadata import PackageNotFoundError, version

# The version is defined in pyproject.toml only, and read from the installed package
try:
    __version__ = version("atmoswing-api")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "unknown"
