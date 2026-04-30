import tomllib
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version


def get_application_version(package_name: str = "ode-solver") -> str:
    """
    Return the application version.

    Priority:
    1. Installed package metadata (works in wheel/container installs)
    2. pyproject.toml fallback (works in local development)
    """

    try:
        return version(package_name)
    except PackageNotFoundError:
        pass

    # Fallback to using pyproject.toml
    project_folder = Path(__file__).parent.parent.parent.parent
    file_path = Path(project_folder) / "pyproject.toml"
    if file_path.exists():
        with file_path.resolve().open("rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]

    return "0+unknown"
