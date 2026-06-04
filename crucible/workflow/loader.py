from pathlib import Path
import json
import yaml

from crucible.models import Workflow


class WorkflowLoader:
    def load(self, path: str | Path) -> Workflow:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Workflow file does not exist: {path}")

        raw_data = self._read_file(path)
        return Workflow.model_validate(raw_data)

    def _read_file(self, path: Path) -> dict:
        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            return yaml.safe_load(path.read_text(encoding="utf-8"))

        if suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))

        raise ValueError(
            f"Unsupported workflow file format: {suffix}. "
            "Supported formats: .yaml, .yml, .json"
        )