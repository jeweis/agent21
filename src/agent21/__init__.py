"""Agent21 project-level AI coding agent configuration manager."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("agent21")
except PackageNotFoundError:
    __version__ = "0.1.5"

__all__ = ["__version__"]
