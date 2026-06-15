from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "Crucible"
APP_AUTHOR = "Crucible"

def get_workspace_dir() -> Path:
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))

def get_workflows_dir() -> Path:
    return get_workspace_dir() / "workflows"

def get_runtime_data_dir() -> Path:
    return get_workspace_dir() / "runtime"