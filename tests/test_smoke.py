import tomllib
from pathlib import Path

from qrypt_quickstart import __version__


def test_package_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert __version__ == pyproject["project"]["version"]
