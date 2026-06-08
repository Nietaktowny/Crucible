from pathlib import Path
import json
import yaml
import logging

from rich.pretty import Pretty

from crucible.models import Workflow

logger = logging.getLogger(__name__)
class WorkflowLoader:
    def load(self, path: str | Path) -> Workflow:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Workflow file does not exist: {path}")

        raw_data = self._read_file(path)
        workflow = Workflow.model_validate(raw_data)
        logger.info(f"Loaded workflow: {workflow.name}")

        logger.debug(
            "Loaded workflow details:\n%s",
            json.dumps(
                workflow.model_dump(),
                indent=2,
                default=str,
            )
        )
        return workflow

    def load_raw(self, path: str | Path) -> dict:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Workflow file does not exist: {path}")

        return self._read_file(path)


    def save_raw(self, raw_data: dict, path: str | Path):
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            path.write_text(
                yaml.safe_dump(
                    raw_data,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            return

        if suffix == ".json":
            path.write_text(
                json.dumps(
                    raw_data,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            return

        raise ValueError(
            f"Unsupported workflow file format: {suffix}. "
            "Supported formats: .yaml, .yml, .json"
        )

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
        
    def save(self, workflow: Workflow, path: str | Path):
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            path.write_text(yaml.safe_dump(workflow.model_dump()), encoding="utf-8")
            return

        if suffix == ".json":
            path.write_text(json.dumps(workflow.model_dump(), indent=2), encoding="utf-8")
            return

        raise ValueError(
            f"Unsupported workflow file format: {suffix}. "
            "Supported formats: .yaml, .yml, .json"
        )