import os
from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "Crucible"
APP_AUTHOR = "Crucible"

WORKSPACE_DIR_ENV_VAR = "CRUCIBLE_WORKSPACE_DIR"

def get_workspace_dir() -> Path:
    """Return the root directory under which all Crucible workspace data lives.

    Honors the `CRUCIBLE_WORKSPACE_DIR` environment variable when set (used
    to point at a mounted volume in Docker deployments); otherwise falls
    back to the OS-appropriate application data directory resolved via
    `platformdirs.user_data_dir`, e.g. `%LOCALAPPDATA%\\Crucible\\Crucible`
    on Windows or `~/.local/share/Crucible` on Linux.

    Returns:
        Path: Root directory under which all Crucible workspace data lives.
    """
    override = os.environ.get(WORKSPACE_DIR_ENV_VAR)

    if override:
        return Path(override)

    return Path(user_data_dir(APP_NAME, APP_AUTHOR))

def get_workflows_dir() -> Path:
    """Return the directory where workflow YAML files are stored.

    Returns:
        Path: `<workspace_dir>/workflows`.
    """
    return get_workspace_dir() / "workflows"

def get_runtime_data_dir() -> Path:
    """Return the directory where runtime data (run history, preview cache) is stored.

    Returns:
        Path: `<workspace_dir>/runtime`.
    """
    return get_workspace_dir() / "runtime"
